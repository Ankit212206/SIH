
## AI-Powered Underground Mine Safety, Monitoring and Rescue System

DeepGuard AI is a human-in-the-loop robotic mine safety and rescue system designed to reduce the exposure of rescue personnel to hazardous underground environments.

The system combines a rugged ground rover, ESP32-based sensing and control, Raspberry Pi-based AI and computer vision, thermal sensing, Wi-Fi/TCP communication, LoRa backup communication, MongoDB telemetry storage, and a real-time monitoring dashboard.

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

DeepGuard AI addresses this problem by using a robotic rover to perform remote reconnaissance and provide real-time environmental and visual information to rescue personnel.

---

## 💡 Proposed Solution

DeepGuard AI uses a rugged ground rover equipped with environmental sensors, cameras, thermal sensing, wireless communication, obstacle detection, and motor control.

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
                       │     Thermal     │
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
## Environmental Telemetry
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


##Computer Vision

RGB / Night-Vision Camera
          ↓
      Raspberry Pi
          ↓
     OpenCV + YOLO
          ↓
 Worker / Object Detection
          ↓
    Alerts / Dashboard



##Thermal Detection

Thermal Camera / Sensor
          ↓
   Thermal Processing
          ↓
Possible Human Heat Signature
          ↓
    Rescue Operator



##Rover Control

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
