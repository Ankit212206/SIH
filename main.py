from flask import Flask, render_template, jsonify, Response
from pymongo import MongoClient
from ultralytics import YOLO
import numpy as np
import os
import sys
import subprocess
import cv2

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

# --- Webcam Setup ---
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1) 

def generate_frames():
    global current_detections
    
    frame_counter = 0
    last_boxes = []  
    
    while True:
        success, frame = camera.read()
        if not success:
            break
            
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_enhanced = clahe.apply(l)
        enhanced_frame = cv2.cvtColor(cv2.merge((l_enhanced, a, b)), cv2.COLOR_LAB2BGR)
        
        display_frame = enhanced_frame.copy()
        frame_counter += 1
        
        if frame_counter % 3 == 0:
            # ANTI-LAG: Reduced imgsz to 320 for much faster CPU processing
            coco_res = coco_model(enhanced_frame, classes=[0], conf=0.35, imgsz=320, device="cpu", verbose=False)[0]
            miner_res = miner_model(enhanced_frame, conf=0.25, imgsz=320, device="cpu", verbose=False)[0]

            p_count = 0
            m_count = 0
            last_boxes.clear() # Clear old memory

            if coco_res.boxes is not None:
                for b in coco_res.boxes.data.cpu().numpy():
                    x1, y1, x2, y2 = map(int, b[:4])
                    conf = float(b[4]) if len(b) > 4 else 0.0
                    # Save the box coordinates to draw them smoothly
                    last_boxes.append((x1, y1, x2, y2, conf))
                    p_count += 1

            if miner_res.boxes is not None:
                for b in miner_res.boxes.data.cpu().numpy():
                    m_count += 1 # We just count the miner, we don't draw their box

            current_detections["persons"] = p_count
            current_detections["miners"] = m_count

        # Draw the person boxes (this runs on EVERY frame so video looks smooth)
        for (x1, y1, x2, y2, conf) in last_boxes:
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(display_frame, f"Person {conf:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

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
        cursor = collection.find({}, sort=[('_id', -1)]).limit(15)
        docs = list(cursor)
        docs.reverse()
        
        if not docs:
            return jsonify({"error": "No database entries found"}), 404
            
        latest_doc = docs[-1]
        latest_doc['_id'] = str(latest_doc['_id'])
        
        hazard_result = None
        
        for doc in docs:
            temp = doc.get('temp', doc.get('Temp', 30))
            humid = doc.get('humid', doc.get('Humid', 40))
            gas = doc.get('gas', 30)
            dust = doc.get('dust', 650)
            
            reading = [gas+730, dust, temp, humid]
            hazard_result = hazard_detector.process_reading(reading)
            
        latest_doc['persons'] = current_detections['persons']
        latest_doc['miners'] = current_detections['miners']
        
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
        app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
    finally:
        print("[*] Shutting down dbReceive.py...")
        if db_process.poll() is None:
            db_process.terminate()
            db_process.wait()