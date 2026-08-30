from flask import Flask, render_template, jsonify, Response
from pymongo import MongoClient
from ultralytics import YOLO
import numpy as np
import os
import cv2

# Ensure Flask looks in the correct directories based on your structure
current_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- MongoDB Setup ---
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client['SIH']
collection = db['data']

# --- YOLO Setup ---
print("Loading YOLO models...")
# Paths point inside the CV folder according to your directory structure
coco_model = YOLO("CV/yolov10n.pt") 
miner_model = YOLO("CV/best.pt")     
clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

# Global dictionary to share detection counts between the camera thread and API
current_detections = {"persons": 0, "miners": 0}

# --- Webcam Setup ---
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def generate_frames():
    global current_detections
    
    while True:
        success, frame = camera.read()
        if not success:
            break
            
        # Image Enhancement
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_enhanced = clahe.apply(l)
        enhanced_frame = cv2.cvtColor(cv2.merge((l_enhanced, a, b)), cv2.COLOR_LAB2BGR)

        # Run YOLO Inference
        coco_res = coco_model(enhanced_frame, classes=[0], conf=0.35, imgsz=480, device="cpu", verbose=False)[0]
        miner_res = miner_model(enhanced_frame, conf=0.25, imgsz=480, device="cpu", verbose=False)[0]

        display_frame = enhanced_frame.copy()
        p_count = 0
        m_count = 0

        # Draw Person Boxes (Green)
        if coco_res.boxes is not None:
            for b in coco_res.boxes.data.cpu().numpy():
                x1, y1, x2, y2 = map(int, b[:4])
                conf = float(b[4]) if len(b) > 4 else 0.0
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display_frame, f"Person {conf:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                p_count += 1

        # Draw Miner Boxes (Orange)
        if miner_res.boxes is not None:
            for b in miner_res.boxes.data.cpu().numpy():
                # x1, y1, x2, y2 = map(int, b[:4])
                # conf = float(b[4]) if len(b) > 4 else 0.0
                # cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                # cv2.putText(display_frame, f"Miner {conf:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
                m_count += 1

        # Update global state
        current_detections["persons"] = p_count
        current_detections["miners"] = m_count

        # Compress and send to web
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
        latest_doc = collection.find_one({}, sort=[('id', -1)])
        
        if not latest_doc:
            latest_doc = {}
        else:
            latest_doc['_id'] = str(latest_doc['_id'])
            
        # Inject live counts from the YOLO detection
        latest_doc['persons'] = current_detections['persons']
        latest_doc['miners'] = current_detections['miners']
        
        return jsonify(latest_doc)
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to fetch data"}), 500

if __name__ == '__main__':
    print("Web server running at http://127.0.0.1:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)