
## AI-Powered Underground Mine Safety, Monitoring and Rescue System


 AI is a human-in-the-loop robotic mine safety and rescue system designed to reduce the exposure of rescue personnel to hazardous underground environments.

The system combines a rugged ground rover, ESP32-based sensing and control, Raspberry Pi-based AI and computer vision, low light sensing, Wi-Fi/TCP communication, LoRa backup communication, MongoDB telemetry storage, and a real-time monitoring dashboard.

> **Sense. Analyze. Locate. Rescue.**

---

##  Problem Statement

Underground coal mines can contain dangerous and unpredictable conditions such as:

- Toxic and hazardous gases
- Excessive dust
- High temperature and humidity
- Smoke and poor visibility
- Flooding
- Tunnel collapse and unstable structures
- Rubble and blocked passages
- Trapped or injured workers
- Communication failures during emergencies

During a mine accident, rescue teams may have limited information about the conditions inside inaccessible or unstable areas. Sending human rescuers into an unknown hazardous environment for initial inspection can increase their risk.

Ai addresses this problem by using a robotic rover to perform remote reconnaissance and provide real-time environmental and visual information to rescue personnel.

---

## 💡 Proposed Solution

AI uses a rugged ground rover equipped with environmental sensors, cameras, low light sensing, wireless communication, obstacle detection, and motor control.

The rover continuously collects information from its surroundings and transmits telemetry to a surface control station.

The surface system:

1. Receives rover telemetry.
2. Validates and processes the data.
3. Stores telemetry in MongoDB.
4. Performs AI/ML-based environmental analysis.
5. Performs computer vision analysis.
6. Generates alerts when required.
7. Displays information on a real-time dashboard.
8. Allows the rescue operator to control the rover.

The system follows a **human-in-the-loop approach**, where AI assists the operator but critical rescue decisions remain under human control.

---

## 🏗️ System Architecture

```text
                         UNDERGROUND MINE
                                │
                                ▼
                       ┌─────────────────┐
                       │      ROVER      │
                       │                 │
                       │     ESP32       │
                       │     Sensors     │
                       │     Motors      │
                       │     Camera      │
                       │     low light     │
                       └────────┬────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
               Wi-Fi / TCP                 LoRa
             Primary Channel          Backup Channel
                    │                       │
                    └───────────┬───────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Python Backend  │
                       │                 │
                       │ Data Receiver   │
                       │ Validation      │
                       │ Processing      │
                       │ AI/ML           │
                       └────────┬────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
             MongoDB          AI/ML         Dashboard
                │               │               │
                └───────────────┼───────────────┘
                                │
                                ▼
                        RESCUE OPERATOR
                                │
                                │ Commands
                                ▼
                              ROVER


```
## 🌡️ Environmental Telemetry

```text
Environmental Sensors
        ↓
      ESP32
        ↓
   JSON Telemetry
        ↓
    Wi-Fi / TCP
        ↓
  Python Backend
        ↓
Validation + Timestamp + Processing
        ↓
     MongoDB
        ↓
 WebSocket / API
        ↓
 Real-Time Dashboard
        ↓
 Rescue Operator
```

## Computer Vision
```text


RGB / Night-Vision Camera
          ↓
      Raspberry Pi
          ↓
     OpenCV + YOLO
          ↓
 Worker / Object Detection
          ↓
    Alerts / Dashboard

```

## low light Detection

```text


low light Camera / Sensor
          ↓
   low light Processing
          ↓
Possible Human Heat Signature
          ↓
    Rescue Operator



## Rover Control

Rescue Operator
       ↓
    Dashboard
       ↓
 Python Backend
       ↓
   Wi-Fi / TCP
       ↓
      ESP32
       ↓
  Motor Driver
       ↓
     Motors
       ↓
      Rover

```

## AI/ML Pipeline
```text


The environmental AI system uses CO₂, dust, temperature and humidity.

Sensor Data
    ↓
15-Reading Window
    ↓
Kalman Filter
    ↓
Scaling
    ↓
Keras Model
    ↓
MSE / Reconstruction Error
    ↓
Threshold
    ↓
SAFE / HAZARD

AI is used as decision support and does not replace human decisions during rescue operations.


```
## Communication
Wi-Fi / TCP
```text

Wi-Fi/TCP is the primary communication channel for continuous telemetry and rover control.

ESP32 ←──── TCP Connection ────→ Laptop

Telemetry is sent as newline-delimited JSON.

Example:

{
  "type": "telemetry",
  "rover_id": "DG01",
  "packet_id": 16,
  "temperature": 31.4,
  "humidity": 52,
  "co2": 700,
  "dust": 35,
  "battery": 87
}



LoRa acts as a low-bandwidth backup channel for critical information such as:
Hazard alerts
Gas warnings
Battery status
Emergency messages

LoRa is not intended for live video transmission.

```
## MongoDB
```text

MongoDB is used for telemetry and system data.

Project
├── telemetry_history
├── telemetry_latest
├── alerts
├── missions
└── commands

telemetry_history stores complete historical data.

telemetry_latest maintains only the latest 15 readings for fast dashboard access.

[1,2,3,...,15]

16 arrives
↓
Delete 1
↓
[2,3,4,...,16]

The deleted reading remains available in telemetry_history.

```

## Computer Vision

The computer vision subsystem uses:

OpenCV
YOLO
RGB camera
Night-vision camera
low light sensing where available

The system can assist in detecting:

Workers
People
Relevant objects
Potential rescue targets

YOLO model files are stored under:
```text
CV/
├── best.pt
└── yolov10n.pt
```
The computer vision system provides additional situational awareness to the rescue operator.



## Low light Worker Detection

Low light sensing provides an additional method of detecting people in difficult visual conditions.

It can be useful in:

Darkness
Poor visibility
Smoke
Dust
Low-light environments

The proposed RGB + low light approach is:
```text

RGB Camera
     │
     ├──────────────┐
     │              │
     ▼              ▼
Visual Detection   low light Detection
     │              │
     └──────┬───────┘
            ▼
      Decision Support
            │
            ▼
      Rescue Operator
```
low light and RGB information are complementary sources of information and should not be treated as absolute confirmation.



## Communication System

 AI uses a redundant communication architecture consisting of:
```text
                    ROVER
                      │
             ┌────────┴────────┐
             │                 │
             ▼                 ▼
          Wi-Fi/TCP           LoRa
           Primary           Backup
             │                 │
             └────────┬────────┘
                      ▼
                Surface System
```
Wi-Fi / TCP

Wi-Fi/TCP is the primary communication channel for:

Continuous telemetry
Rover control
Higher-bandwidth information
Communication between ESP32 and laptop

The ESP32 acts as the TCP client.

The laptop acts as the TCP server.



## Bidirectional Communication

The TCP connection can be used in both directions.

ESP32 → Laptop
```text

The ESP32 sends telemetry:
{
  "type": "telemetry",
  "rover_id": "DG01",
  "packet_id": 16,
  "temperature": 31.4,
  "humidity": 52,
  "methane": 42,
  "battery": 87
}
```
Laptop → ESP32
```
The laptop can send commands:
{
  "type": "command",
  "command": "STOP"
}
```
Movement command:
```text

{
  "type": "command",
  "command": "MOVE",
  "direction": "FORWARD",
  "speed": 100
}
```
Possible commands include:
```text
FORWARD
BACKWARD
LEFT
RIGHT
STOP
```
An emergency stop/override should remain available independently of AI decisions.



## MongoDB Database

MongoDB is used to store rover telemetry, alerts, missions and commands.

The recommended database structure is:
```text
Project
│
├── telemetry_history
├── telemetry_latest
├── alerts
├── missions
└── commands
```


## Latest 15 Telemetry Readings

A separate telemetry_latest collection maintains only the latest 15 telemetry readings for fast dashboard visualization.

```text
Reading 1
→ [1]

Reading 2
→ [1,2]

...

Reading 15
→ [1,2,3,...,15]

Reading 16 arrives
→ Delete reading 1
→ Insert reading 16

Result:
[2,3,4,...,15,16]
```
The old telemetry should only be removed from telemetry_latest.

It remains stored in: telemetry_history

This allows the dashboard to work with a small recent-data window without losing historical mission data.



## Real-Time Dashboard

The dashboard provides the rescue operator with a centralized view of the rover.

Environmental Information
```text

Temperature
Humidity
Gas levels
CO₂
Dust
```
AI Information
```text
SAFE / HAZARD status
Environmental anomaly information
AI detection results
```
Vision
```text
RGB video
Night-vision video
Worker detection
low light information
```
Rover Status
```text
Battery
Communication status
Mission status
```
Telemetry
```text
Latest 15 readings
Sensor trends
Historical information
```
Control
```text
Forward
Backward
Left
Right
Stop
Emergency stop
```


## Project Structure
```text
SIH-main/
│
├── CV/
│   ├── best.pt
│   ├── yolov10n.pt
│   ├── main.ipynb
│   └── maine.ipynb
│
├── Model/
│   ├── abnormality_analysis.py
│   ├── model.keras.zip
│   ├── scaler.joblib
│   └── threshold.joblib
│
├── src/
│   ├── rover/
│   │   └── rover_main.cpp
│   │
│   ├── receiver/
│   │   └── receiver_main.cpp
│   │
│   └── sih/
│       └── __init__.py
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html
│
├── main.py
├── dbReceive.py
├── sender.py
├── rec.py
├── receiver.py
├── sockreceive.py
├── tempCodeRunnerFile.py
├── platformio.ini
├── pyproject.toml
├── requirment.txt
├── uv.lock
└── README.md
```
