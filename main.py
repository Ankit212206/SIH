from collections import deque
import os
import subprocess
import sys
import threading

import cv2
from flask import Flask, Response, jsonify, render_template
from pymongo import MongoClient
from ultralytics import YOLO

from Model.abnormality_analysis import MineHazardDetector


current_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(current_dir, "templates")
static_dir = os.path.join(current_dir, "static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# --- Terminal log history ---
terminal_logs = deque(maxlen=300)
terminal_logs_lock = threading.Lock()


def save_terminal_log(message):
    message = str(message).rstrip()
    if not message:
        return
    with terminal_logs_lock:
        terminal_logs.append(message)


def get_terminal_logs():
    with terminal_logs_lock:
        return list(terminal_logs)


class TerminalAndDashboard:
    """Mirror print output to the terminal and to the dashboard log buffer."""

    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.buffer = ""
        self.buffer_lock = threading.Lock()

    def write(self, text):
        self.original_stream.write(text)
        self.original_stream.flush()

        completed_lines = []
        with self.buffer_lock:
            self.buffer += text
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                completed_lines.append(line)

        for line in completed_lines:
            save_terminal_log(line)
        return len(text)

    def flush(self):
        self.original_stream.flush()

    def __getattr__(self, name):
        return getattr(self.original_stream, name)


sys.stdout = TerminalAndDashboard(sys.stdout)
sys.stderr = TerminalAndDashboard(sys.stderr)


# --- Database ---
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["NASA"]
collection = db["astronauts"]


# --- Runtime state ---
# Models are intentionally loaded only after the Start button calls /api/start.
coco_model = None
miner_model = None
hazard_detector = None
clahe = None
camera = None
system_running = False

state_lock = threading.RLock()
model_lock = threading.Lock()
camera_lock = threading.Lock()
analysis_lock = threading.Lock()
detections_lock = threading.Lock()

current_detections = {"persons": 0, "miners": 0}
last_processed_document_id = None
latest_hazard_result = None


def is_system_running():
    with state_lock:
        return system_running


def load_models():
    """Load the CV and hazard-analysis models once, on the first Start."""
    global coco_model, miner_model, hazard_detector, clahe

    with model_lock:
        if all((coco_model, miner_model, hazard_detector, clahe)):
            return

        print("[*] Loading CV models...")
        loaded_coco_model = YOLO("CV/yolov10n.pt")
        loaded_miner_model = YOLO("CV/best.pt")

        print("[*] Loading hazard-analysis model...")
        loaded_hazard_detector = MineHazardDetector(
            model_path="Model/model (1).keras.zip",
            scaler_path="Model/scaler (1).joblib",
            threshold_path="Model/threshold (1).joblib",
            window_size=15,
        )

        coco_model = loaded_coco_model
        miner_model = loaded_miner_model
        hazard_detector = loaded_hazard_detector
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        print("[*] Models are ready.")


def start_system():
    """Start camera capture and enable model inference/database processing."""
    global camera, system_running, last_processed_document_id, latest_hazard_result

    with state_lock:
        if system_running:
            return True, "System is already running."

        try:
            load_models()

            opened_camera = cv2.VideoCapture(0)
            opened_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            opened_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            opened_camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not opened_camera.isOpened():
                opened_camera.release()
                raise RuntimeError("Camera 0 could not be opened.")

            with camera_lock:
                camera = opened_camera

            last_processed_document_id = None
            latest_hazard_result = None
            with detections_lock:
                current_detections["persons"] = 0
                current_detections["miners"] = 0

            system_running = True
            print("[*] System started: camera, CV, hazard analysis, and database polling enabled.")
            return True, "System started."
        except Exception as error:
            print(f"[!] Failed to start system: {error}")
            return False, str(error)


def stop_system():
    """Stop inference/database processing and release the camera device."""
    global camera, system_running, last_processed_document_id, latest_hazard_result

    with state_lock:
        if not system_running:
            return True, "System is already stopped."

        system_running = False
        last_processed_document_id = None
        latest_hazard_result = None
        with detections_lock:
            current_detections["persons"] = 0
            current_detections["miners"] = 0

        with camera_lock:
            active_camera = camera
            camera = None

    if active_camera is not None:
        active_camera.release()

    print("[*] System stopped: camera released and model/database processing paused.")
    return True, "System stopped."


def sensor_reading_from(document):
    return [
        document.get("gas", 30),
        document.get("dust", 650),
        document.get("temp", document.get("Temp", 30)),
        document.get("humid", document.get("Humid", 40)),
    ]


def update_hazard_result(documents):
    """Seed the detector once, then analyse only newly inserted Mongo records."""
    global last_processed_document_id, latest_hazard_result

    latest_id = str(documents[-1]["_id"])
    with analysis_lock:
        if last_processed_document_id is None:
            # A detector needs 15 readings. Seed it with the available recent
            # history only once, not again on every browser refresh.
            for document in documents:
                latest_hazard_result = hazard_detector.process_reading(
                    sensor_reading_from(document)
                )
            last_processed_document_id = latest_id
        elif last_processed_document_id != latest_id:
            latest_hazard_result = hazard_detector.process_reading(
                sensor_reading_from(documents[-1])
            )
            last_processed_document_id = latest_id

        return latest_hazard_result


def generate_frames():
    frame_counter = 0
    last_boxes = []

    while is_system_running():
        # Holding this lock during read prevents stop_system from releasing the
        # OpenCV capture object while a frame is being read.
        with camera_lock:
            active_camera = camera
            if active_camera is None:
                break
            success, frame = active_camera.read()

        if not success:
            print("[!] Camera frame could not be read.")
            break

        if not is_system_running():
            break

        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lightness, channel_a, channel_b = cv2.split(lab)
        enhanced_lightness = clahe.apply(lightness)
        enhanced_frame = cv2.cvtColor(
            cv2.merge((enhanced_lightness, channel_a, channel_b)),
            cv2.COLOR_LAB2BGR,
        )
        display_frame = enhanced_frame.copy()
        frame_counter += 1

        if frame_counter % 3 == 0:
            try:
                coco_result = coco_model(
                    enhanced_frame,
                    classes=[0],
                    conf=0.35,
                    imgsz=320,
                    device="cpu",
                    verbose=False,
                )[0]
                miner_result = miner_model(
                    enhanced_frame,
                    conf=0.25,
                    imgsz=320,
                    device="cpu",
                    verbose=False,
                )[0]
            except Exception as error:
                print(f"[!] CV inference error: {error}")
                break

            person_count = 0
            miner_count = 0
            last_boxes.clear()

            if coco_result.boxes is not None:
                for box in coco_result.boxes.data.cpu().numpy():
                    x1, y1, x2, y2 = map(int, box[:4])
                    confidence = float(box[4]) if len(box) > 4 else 0.0
                    last_boxes.append((x1, y1, x2, y2, confidence))
                    person_count += 1

            if miner_result.boxes is not None:
                miner_count = len(miner_result.boxes)

            with detections_lock:
                current_detections["persons"] = person_count
                current_detections["miners"] = miner_count

        for x1, y1, x2, y2, confidence in last_boxes:
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                display_frame,
                f"Person {confidence:.2f}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        encoded, buffer = cv2.imencode(".jpg", display_frame)
        if not encoded:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video-feed")
def video_feed():
    if not is_system_running():
        return jsonify({"error": "System is stopped. Press Start first."}), 409
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/api/start", methods=["POST"])
def start_api():
    started, message = start_system()
    status_code = 200 if started else 500
    return jsonify({
        "running": started and is_system_running(),
        "message": message,
        "logs": get_terminal_logs(),
    }), status_code


@app.route("/api/stop", methods=["POST"])
def stop_api():
    stopped, message = stop_system()
    status_code = 200 if stopped else 500
    return jsonify({
        "running": is_system_running(),
        "message": message,
        "logs": get_terminal_logs(),
    }), status_code


@app.route("/api/data")
def get_data():
    if not is_system_running():
        return jsonify({
            "running": False,
            "message": "System is stopped. Press Start to fetch MongoDB data.",
            "logs": get_terminal_logs(),
        })

    try:
        # _id is monotonically generated by MongoDB in normal inserts, so the
        # first item from this descending query is the newest document.
        documents = list(collection.find({}, sort=[("_id", -1)]).limit(15))
        documents.reverse()

        if not documents:
            return jsonify({
                "running": True,
                "error": "No database entries found.",
                "logs": get_terminal_logs(),
            }), 404

        latest_document = documents[-1].copy()
        history = []
        for document in documents:
            history.append({
                "timestamp": document.get("timestamp"),
                "temp": document.get("temp", document.get("Temp")),
                "humid": document.get("humid", document.get("Humid")),
                "gas": document.get("gas"),
                "dust": document.get("dust"),
            })
        hazard_result = update_hazard_result(documents)
        latest_document["_id"] = str(latest_document["_id"])

        with detections_lock:
            latest_document["persons"] = current_detections["persons"]
            latest_document["miners"] = current_detections["miners"]

        if hazard_result:
            latest_document["hazard_status"] = hazard_result.get("status", "SAFE")
            latest_document["anomalies"] = hazard_result.get("anomalies", [])
        else:
            latest_document["hazard_status"] = "WARMING UP"
            latest_document["anomalies"] = []

        latest_document["running"] = True
        latest_document["history"] = history
        latest_document["logs"] = get_terminal_logs()
        return jsonify(latest_document)
    except Exception as error:
        print(f"[!] Database/model error: {error}")
        return jsonify({
            "running": is_system_running(),
            "error": "Failed to fetch the latest database data.",
            "logs": get_terminal_logs(),
        }), 500


if __name__ == "__main__":
    db_receive_path = os.path.join(current_dir, "dbReceive.py")
    print("[*] Starting USB serial listener...")
    db_process = subprocess.Popen(
        [sys.executable, "-u", db_receive_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def forward_db_receive_logs():
        if db_process.stdout is None:
            return
        for line in db_process.stdout:
            print(f"[dbReceive] {line.rstrip()}")

    threading.Thread(target=forward_db_receive_logs, daemon=True).start()
    print(f"[*] dbReceive.py started with PID: {db_process.pid}")

    try:
        print("Web server running at http://127.0.0.1:8080")
        app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
    finally:
        stop_system()
        print("[*] Shutting down dbReceive.py...")
        if db_process.poll() is None:
            db_process.terminate()
            db_process.wait()
