from flask import Flask, render_template, jsonify, Response
from pymongo import MongoClient
from ultralytics import YOLO
import numpy as np
import os
import sys
import subprocess
import cv2
import time

# Import hazard detector
from Model.abnormality_analysis import MineHazardDetector

current_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- MongoDB Setup ---
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client['NASA']
collection = db['astronauts']

# --- AI Models Setup ---
print("Loading YOLO models...")
coco_model = YOLO("CV/yolov10n.pt") 
miner_model = YOLO("CV/best.pt")     
clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

print("Loading Hazard Detector...")
hazard_detector = MineHazardDetector(
    model_path="Model/model.keras.zip",
    scaler_path="Model/scaler.joblib",
    threshold_path="Model/threshold.joblib",
    window_size=15
)

current_detections = {"persons": 0, "miners": 0}

# Reject very dark, nearly uniform frames (for example, a covered lens) before
# sending them to YOLO.  Such frames can otherwise produce false positives.
MIN_FRAME_BRIGHTNESS = 18
MIN_FRAME_CONTRAST = 10
MIN_DETECTION_AREA_RATIO = 0.01
CONFIRMATION_FRAMES = 2
person_detection_streak = 0


def is_usable_camera_frame(frame):
    """Return False for a black/covered camera feed."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Both light and detail are needed.  A uniformly bright cover should be
    # rejected just like a black cover.
    return gray.mean() >= MIN_FRAME_BRIGHTNESS and gray.std() >= MIN_FRAME_CONTRAST


def valid_boxes(result, frame_shape):
    """Keep only detections large enough to be meaningful in this frame."""
    if result.boxes is None:
        return []

    frame_area = frame_shape[0] * frame_shape[1]
    boxes = []
    for box in result.boxes.data.cpu().numpy():
        x1, y1, x2, y2 = map(int, box[:4])
        if max(0, x2 - x1) * max(0, y2 - y1) >= frame_area * MIN_DETECTION_AREA_RATIO:
            boxes.append((x1, y1, x2, y2, float(box[4])))
    return boxes

# --- Webcam Setup ---
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def generate_frames():
    global current_detections, person_detection_streak
    
    while True:
        success, frame = camera.read()
        if not success:
            break
            
        display_frame = frame.copy()
        p_count = 0
        m_count = 0

        if is_usable_camera_frame(frame):
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l_enhanced = clahe.apply(l)
            enhanced_frame = cv2.cvtColor(cv2.merge((l_enhanced, a, b)), cv2.COLOR_LAB2BGR)

            coco_res = coco_model(enhanced_frame, classes=[0], conf=0.55, imgsz=480, device="cpu", verbose=False)[0]
            miner_res = miner_model(enhanced_frame, conf=0.50, imgsz=480, device="cpu", verbose=False)[0]
            person_boxes = valid_boxes(coco_res, frame.shape)
            miner_boxes = valid_boxes(miner_res, frame.shape)

            if person_boxes or miner_boxes:
                person_detection_streak += 1
            else:
                person_detection_streak = 0

            # Do not alert on a single false-positive frame.
            if person_detection_streak >= CONFIRMATION_FRAMES:
                p_count = len(person_boxes)
                m_count = len(miner_boxes)

            for x1, y1, x2, y2, conf in person_boxes:
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display_frame, f"Person {conf:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            person_detection_streak = 0
            cv2.putText(display_frame, "CAMERA COVERED / NO USABLE IMAGE", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        current_detections["persons"] = p_count
        current_detections["miners"] = m_count

        ret, buffer = cv2.imencode('.jpg', display_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/data')
def get_data():
    try:
        # Fetch the last 15 documents and reverse them into chronological order
        cursor = collection.find({}, sort=[('_id', -1)]).limit(15)
        docs = list(cursor)
        docs.reverse()
        
        if not docs:
            return jsonify({"error": "No database entries found"}), 404
            
        latest_doc = docs[-1]
        latest_doc['_id'] = str(latest_doc['_id'])
        
        hazard_result = None
        
        # Feed the 15 chronological readings into the sliding window
        for doc in docs:
            temp = doc.get('temp', doc.get('Temp', 30))
            humid = doc.get('humid', doc.get('Humid', 40))
            gas = doc.get('gas', 700)
            dust = doc.get('dust', 650)
            
            # Format: [CO2, Dust, Temp, Humidity] matching your detector script
            reading = [gas+730, dust, temp, humid]
            time.sleep(1)
            hazard_result = hazard_detector.process_reading(reading)
            
        # Append YOLO counts
        latest_doc['persons'] = current_detections['persons']
        latest_doc['miners'] = current_detections['miners']
        
        # Append Hazard Data
        if hazard_result:
            latest_doc['hazard_status'] = hazard_result.get('status', 'SAFE')
            latest_doc['anomalies'] = hazard_result.get('anomalies', [])
        else:
            latest_doc['hazard_status'] = 'WARMING UP'
            latest_doc['anomalies'] = []
            
        return jsonify(latest_doc)
        
    except Exception as e:
        print(f"Database/Model error: {e}")
        return jsonify({"error": "Failed to fetch data"}), 500

if __name__ == '__main__':
    db_receive_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dbReceive.py')
    print("[*] Starting (USB Serial listener)...")
    db_process = subprocess.Popen(
        [sys.executable, db_receive_path]
    )
    print(f"[*] dbReceive.py started with PID: {db_process.pid}")

    try:
        print("Web server running at http://127.0.0.1:8080")
        # Flask's debug reloader starts this module twice.  Disable it so the
        # serial listener is launched once and is not immediately terminated.
        app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
    finally:
        print("[*] Shutting down dbReceive.py...")
        if db_process.poll() is None:
            db_process.terminate()
            db_process.wait()
