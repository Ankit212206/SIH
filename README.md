DeepGuard AI

AI-Powered Underground Mine Safety, Monitoring and Rescue System

DeepGuard AI is a human-in-the-loop, semi-autonomous underground mine safety and rescue platform designed to reduce the exposure of rescue personnel to hazardous mine environments.

The system combines a rugged ground rover, embedded sensing, AI/ML-based environmental anomaly detection, computer vision, thermal sensing, redundant communication, real-time telemetry, remote control, and data storage.

The core idea is simple:

Send the rover into a dangerous area first, collect reliable information, detect possible hazards and workers, and give rescue personnel better information before they enter.

Table of Contents

Problem

Solution

Objectives

Key Features

System Architecture

Data Flow

Hardware

Software Stack

Communication

Telemetry Format

AI/ML Hazard Detection

Computer Vision and Worker Detection

MongoDB Data Architecture

Real-Time Dashboard

Rover Control

Current Repository Prototype

Project Structure

Installation

Running the System

Prototype Testing

Challenges and Mitigation

Safety and Scope

Future Enhancements

Expected Impact

Problem

Underground coal mines can contain hazardous conditions including:

Toxic or dangerous gases

Excessive dust

High temperature and humidity

Smoke and poor visibility

Flooding

Unstable structures and tunnel collapses

Rubble and inaccessible passages

Unreliable communication after an accident

During an emergency, rescue teams may have limited real-time information about conditions inside inaccessible or unstable areas. Sending people into an unknown hazardous environment for initial reconnaissance can increase risk.

DeepGuard AI addresses this problem by allowing a robotic platform to perform remote reconnaissance and continuously report environmental and visual information.

Solution

DeepGuard AI uses a rugged ground rover equipped with environmental sensors and visual sensing.

The rover collects:

Gas/environmental measurements

Temperature

Humidity

Dust concentration

Motion/orientation information

Obstacle information

RGB/night-vision imagery

Thermal information where available

The collected data is processed and transmitted to a safer surface control station.

AI/ML assists the operator by:

Detecting abnormal environmental patterns

Detecting workers/people in camera frames

Supporting hazard assessment

Supporting worker localization

Providing decision-support information

The system follows a human-in-the-loop approach. Critical rescue decisions remain with the human operator rather than relying on fully autonomous operation.

Objectives

Continuously monitor underground environmental conditions.

Detect abnormal or potentially hazardous conditions using sensor thresholds and AI/ML.

Provide live RGB/night-vision and thermal information where bandwidth permits.

Assist in locating trapped workers.

Enable remote rover control from a safer location.

Provide primary high-bandwidth communication through Wi-Fi/TCP.

Provide LoRa as a low-bandwidth emergency/backup telemetry path.

Store telemetry and mission information for monitoring and later analysis.

Improve rescue-team situational awareness before human entry.

Reduce direct exposure of rescue personnel to hazardous environments.

Key Features

Environmental Monitoring

The rover can monitor:

Gas concentration

Dust concentration

Temperature

Humidity

Other environmental measurements depending on the final sensor configuration

AI Hazard Detection

The environmental AI uses recent sensor readings rather than relying only on one instantaneous value.

The current model pipeline uses:

CO₂

Dust

Temperature

Humidity

A 15-reading sliding window is used for temporal analysis.

Computer Vision

A YOLO-based detector can identify:

People/workers

Relevant objects

OpenCV is used for image/frame processing.

Thermal Worker Localization

Thermal sensing can provide heat signatures that can help identify workers in:

Darkness

Smoke

Poor visibility

RGB and thermal results can be combined as decision support.

Remote Operation

The rover can be remotely controlled by the rescue operator.

Possible commands include:

Forward

Backward

Left

Right

Stop

Emergency/mission commands

Redundant Communication

Wi-Fi/TCP: primary communication path for telemetry and high-bandwidth information.

LoRa: emergency low-bandwidth backup for critical telemetry and commands.

LoRa is not intended for live video.

Real-Time Monitoring

The dashboard can show:

Current environmental values

SAFE/HAZARD status

AI alerts

Battery status

Communication status

Recent telemetry

RGB/night-vision video

Thermal information where available

Worker/target detection

Rover control

System Architecture

                         UNDERGROUND MINE
                                │
                         ┌──────▼──────┐
                         │   ROVER     │
                         │             │
                         │ ESP32       │
                         │ Sensors     │
                         │ Motors      │
                         │ Camera      │
                         │ Thermal     │
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                 Wi-Fi/TCP                 LoRa
              Primary Link            Backup Telemetry
                    │                       │
                    └───────────┬───────────┘
                                │
                                ▼
                       SURFACE CONTROL
                                │
                       ┌────────▼────────┐
                       │ Python Backend  │
                       │                 │
                       │ Receive         │
                       │ Validate        │
                       │ Timestamp       │
                       │ Deduplicate     │
                       │ Process         │
                       └────────┬────────┘
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
                 ▼              ▼              ▼
             MongoDB        AI/ML          WebSocket
                 │          Analysis           │
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                       LIVE DASHBOARD
                                │
                                ▼
                        RESCUE OPERATOR
                                │
                                │ Commands
                                ▼
                              ROVER

Data Flow

Environmental Telemetry

Sensors
   ↓
ESP32
   ↓
JSON telemetry
   ↓
Wi-Fi/TCP
   ↓
Python backend
   ↓
Validation + timestamp + deduplication
   ↓
MongoDB
   ↓
WebSocket
   ↓
Live dashboard

Camera / Vision

Camera
   ↓
Raspberry Pi
   ↓
OpenCV
   ↓
YOLO detection / thermal analysis
   ↓
Worker + hazard information
   ↓
Dashboard / alert layer

Operator Control

Dashboard
   ↓
Python backend
   ↓
TCP/Wi-Fi
   ↓
ESP32
   ↓
Motor driver
   ↓
Geared motors
   ↓
Rover movement

Communication Failure

Wi-Fi/TCP unavailable
        ↓
Critical telemetry prioritized
        ↓
LoRa backup path
        ↓
Control station / gateway
        ↓
Backend

Hardware

The proposed hardware architecture contains:

Component

Purpose

ESP32

Sensor acquisition, Wi-Fi communication, telemetry and control

Raspberry Pi

AI/vision processing and camera handling

Gas sensor(s)

Hazardous atmospheric monitoring

Temperature sensor

Temperature monitoring

Humidity sensor

Humidity monitoring

Dust sensor

Particulate/dust monitoring

IMU

Acceleration/orientation and rover state

Obstacle sensor

Obstacle detection and navigation assistance

RGB/night-vision camera

Visual inspection in low-light environments

Thermal camera/sensor

Heat-signature detection and worker localization

LoRa module

Emergency low-bandwidth telemetry

Motor driver

Motor control

Geared motors

Rover movement and traction

Battery/power system

Powers sensing, computation, communication and mobility

The exact gas and thermal sensor models depend on the final prototype.

Software Stack

Embedded

ESP32

C/C++

Arduino/ESP32 ecosystem

ArduinoJson

PlatformIO

Backend

Python

FastAPI / Python networking services

Python sockets

PyMongo

PySerial

AI/ML

TensorFlow/Keras

Scikit-learn

NumPy

Pandas

Joblib

PyKalman

Computer Vision

OpenCV

Ultralytics YOLO

Database

MongoDB

Real-Time UI

Flask-based web interface in the current repository

WebSocket architecture for real-time updates

HTML/CSS/JavaScript

Packet Analysis / Networking Experiments

Scapy

Scapy is intended primarily for packet inspection, debugging and controlled networking experiments. Normal TCP socket APIs are simpler for the actual telemetry endpoint.

Communication

Wi-Fi + TCP

The intended primary telemetry path is:

ESP32
   ↓
Wi-Fi
   ↓
Laptop TCP Server
   ↓
Python Backend

The ESP32 acts as a TCP client.

The laptop acts as a TCP server.

The laptop server can bind to:

0.0.0.0:5000

0.0.0.0 means the server listens on all local network interfaces. The ESP32 must connect to the laptop's actual LAN IPv4 address, for example:

172.18.117.25

Persistent TCP Connection

The rover should establish the TCP connection once and continuously send telemetry while the connection remains active.

The system should implement:

Persistent connection

Automatic reconnection

Packet IDs

Timestamps

Message framing

Buffering

Duplicate detection

TCP Message Framing

TCP is a byte stream, not a message-based protocol.

Therefore, telemetry messages need application-level framing.

A simple approach is newline-delimited JSON:

{"type":"telemetry","packet_id":1,...}\n
{"type":"telemetry","packet_id":2,...}\n
{"type":"telemetry","packet_id":3,...}\n

The backend maintains a buffer and separates complete JSON records using the newline delimiter.

LoRa Communication

LoRa is used as a low-bandwidth emergency/backup channel.

Suitable LoRa information includes:

Gas alerts

Hazard status

Rover status

Battery status

Emergency messages

Basic commands

Other critical telemetry

LoRa should not be used for live RGB or thermal video because its bandwidth is much lower than Wi-Fi.

A LoRa receiver/gateway can forward the received telemetry into the same backend processing pipeline where appropriate.

Telemetry Format

A common JSON structure keeps telemetry consistent across communication paths.

Example:

{
  "type": "telemetry",
  "rover_id": "DG01",
  "packet_id": 16,
  "timestamp": "2026-08-30T14:00:00Z",
  "temperature": 31.4,
  "humidity": 52,
  "co2": 700,
  "dust": 35,
  "battery": 87
}

Why packet_id is important

It helps identify:

Duplicate packets

Missing packets

Stale packets

Ordering problems

Why timestamp is important

It allows telemetry to be associated with a precise point in time and supports:

Historical analysis

Incident investigation

Trend visualization

AI analysis

AI/ML Hazard Detection

The environmental anomaly pipeline is designed to detect unusual patterns in sensor data.

Current model inputs

CO₂
Dust
Temperature
Humidity

Processing pipeline

Incoming sensor reading
        ↓
15-reading sliding window
        ↓
Kalman filtering
        ↓
Standard scaling
        ↓
Keras model
        ↓
Reconstruction / prediction
        ↓
Mean Squared Error (MSE)
        ↓
Sensor-specific thresholds
        ↓
SAFE / HAZARD

15-reading sliding window

Instead of looking at only the current reading, the system considers the most recent 15 readings.

This allows the model to consider recent temporal behavior.

Kalman filtering

Sensor measurements can contain noise.

A Kalman filter is used to smooth noisy measurements before model inference.

Anomaly score

The model compares the processed input with its reconstruction/prediction.

The difference is measured using Mean Squared Error (MSE).

Large reconstruction error can indicate abnormal behavior.

Final decision

Sensor-specific errors are compared against predefined thresholds.

The result is converted into an operator-friendly state:

SAFE

or

HAZARD

Critical decisions should remain subject to human confirmation.

The supplied repository contains trained-model inference assets. Training a robust model for real mine deployment is a separate task and requires representative normal and abnormal mine data.

Computer Vision and Worker Detection

The vision pipeline uses:

OpenCV

YOLO-based object detection

RGB/night-vision camera

Thermal sensing where available

The current repository contains YOLO model assets:

CV/yolov10n.pt
CV/best.pt

The system can use:

A general person detector

A mine/worker-specific detector

The dashboard can display a worker/person detection state.

Thermal + RGB fusion

Thermal imagery can provide an additional signal when:

The mine is dark

Visibility is poor

Smoke is present

Combining RGB and thermal evidence can improve decision support.

AI detections should be treated as assistance to rescue personnel, not as an unquestionable ground truth.

MongoDB Data Architecture

MongoDB is used because rover telemetry is naturally represented as flexible JSON-like documents and the prototype requires frequent writes and quick retrieval.

Recommended collections

MongoDB
│
├── telemetry_history
├── telemetry_latest
├── alerts
├── missions
└── commands

telemetry_history

Stores complete telemetry history.

Example:

{
  "rover_id": "DG01",
  "packet_id": 742,
  "timestamp": "2026-08-30T14:10:22Z",
  "temperature": 31.2,
  "humidity": 54,
  "co2": 720,
  "dust": 38,
  "battery": 81
}

This collection should preserve historical data for:

Incident analysis

Trend analysis

Future AI improvement

Mission review

telemetry_latest

Maintains only the newest 15 telemetry readings for fast live visualization.

Behavior:

Reading 1  → [1]
Reading 2  → [1,2]
...
Reading 15 → [1,...,15]

Reading 16 arrives
       ↓
Remove reading 1
       ↓
Insert reading 16

Result:
[2,3,4,...,15,16]

Historical telemetry should not be deleted merely to maintain the latest-15 window.

alerts

Stores important events such as:

Environmental anomaly

High gas level

Worker detection

Communication failure

Low battery

Other emergency events

Example:

{
  "type": "alert",
  "rover_id": "DG01",
  "severity": "HIGH",
  "hazard": "ENVIRONMENTAL_ANOMALY",
  "timestamp": "2026-08-30T14:15:00Z"
}

missions

Stores:

Mission ID

Rover ID

Start time

End time

Mission status

commands

Stores operator commands and acknowledgements for auditability.

Real-Time Dashboard

The dashboard provides the rescue operator with a single view of the rover.

It can display:

Environmental

Temperature

Humidity

Gas

Dust

Other available telemetry

AI

SAFE / HAZARD

Detected anomalies

MSE/anomaly information where appropriate

Vision

Person/worker detection

RGB/night-vision feed

Thermal information where available

Rover

Battery

Communication status

Mission state

Controls

Movement commands

Stop/emergency commands

Recent telemetry

The dashboard can display trends from the latest 15 readings.

WebSocket updates are preferred for live changes so the dashboard does not need to repeatedly poll the database for every update.

Rover Control

The system is designed for human-in-the-loop semi-autonomous control.

The operator can send commands to the rover while the AI provides assistance.

Example command:

{
  "type": "command",
  "command": "STOP"
}

Another example:

{
  "type": "command",
  "command": "MOVE",
  "direction": "FORWARD",
  "speed": 100
}

The rover should always support a manual emergency stop/override mechanism.

Current Repository Prototype

The repository contains a working prototype with several communication and processing components.

Current embedded implementation

The current rover firmware in:

src/rover/rover_main.cpp

uses:

ESP32-S3

DHT11 temperature/humidity sensing

MPU6050 IMU

Analog gas/smoke input

Servo-mounted distance scanning

Ultrasonic distance measurement

ArduinoJson

ESP-NOW broadcast telemetry

The rover currently generates a JSON telemetry record containing:

id
gas
dust
temp
humid
scan

The current dust values are simulated/randomized in the prototype firmware rather than measured by a physical dust sensor.

Current base-station implementation

The receiver firmware in:

src/receiver/receiver_main.cpp

uses an ESP32-C3 as an ESP-NOW-to-USB serial bridge.

It:

Receives ESP-NOW packets.

Parses the JSON.

Displays selected values on an OLED.

Prints the received JSON to USB serial.

The Python dbReceive.py process can then read the USB serial stream and insert JSON telemetry into MongoDB.

Current web/AI prototype

The repository also contains:

main.py
Model/abnormality_analysis.py
CV/
templates/
static/

The current Flask application:

Serves the dashboard.

Provides a video feed.

Runs YOLO-based person/miner detection.

Reads telemetry from MongoDB.

Runs the environmental anomaly detector.

Exposes data through /api/data.

Target communication architecture

The broader DeepGuard architecture is designed to evolve toward:

ESP32 Rover
   ↓
Wi-Fi/TCP
   ↓
Python Backend
   ↓
MongoDB + WebSocket

with:

LoRa
   ↓
Emergency/backup telemetry

The current ESP-NOW + USB bridge is therefore a prototype communication path, while Wi-Fi/TCP + LoRa provides the intended scalable communication architecture.

Project Structure

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
├── reciever.py
├── sockreceive.py
├── platformio.ini
├── pyproject.toml
├── requirment.txt
└── README.md

Installation

Requirements

The project specifies:

Python 3.12

The repository includes Python dependencies for:

Flask

MongoDB/PyMongo

TensorFlow

OpenCV

Ultralytics

Scikit-learn

NumPy

Pandas

PyKalman

Joblib

PySerial

Scapy

PyAudio

ElevenLabs

Install dependencies using the project's dependency configuration or:

pip install -r requirment.txt

MongoDB

The prototype expects a local MongoDB server:

mongodb://localhost:27017/

Make sure MongoDB is running before starting the backend/database components.

ESP32

The embedded project uses PlatformIO.

The platformio.ini defines:

rover_s3
receiver_c3

The rover environment targets:

ESP32-S3 DevKitC-1

The receiver environment targets:

ESP32-C3 DevKitM-1

Running the System

Web/AI backend

From the project directory:

python main.py

The current Flask application runs on:

http://127.0.0.1:8080

The application also starts the serial database receiver process configured in main.py.

Current serial receiver

The current dbReceive.py is configured for:

COM5
115200 baud

Change the serial port to match the base-station ESP32 on your machine.

TCP telemetry prototype

For the target Wi-Fi/TCP architecture:

Laptop:
TCP server → port 5000

ESP32:
TCP client → laptop LAN IP:5000

Do not use 0.0.0.0 as the ESP32 destination. The ESP32 must connect to the laptop's actual LAN IPv4 address.

Prototype Testing

Testing should be performed progressively.

Stage 1 — Embedded sensing

Test each sensor independently.

Verify sensor values.

Calibrate sensors.

Check sensor drift.

Stage 2 — Rover communication

Confirm telemetry generation.

Verify packet IDs.

Verify JSON formatting.

Check continuous transmission.

Stage 3 — TCP

Start the laptop TCP server.

Connect the ESP32.

Keep the connection open.

Send continuous telemetry.

Test automatic reconnection.

Test bidirectional commands.

Stage 4 — Database

Verify:

JSON validation

Timestamp insertion

Duplicate handling

Complete history storage

Latest-15 rolling collection

Stage 5 — Dashboard

Verify:

Real-time telemetry

Hazard status

Worker detection

Battery status

Communication status

Recent telemetry trends

Stage 6 — LoRa

Test emergency telemetry separately.

Verify that critical information can still be delivered when the primary Wi-Fi path is unavailable.

Stage 7 — AI

Test the anomaly detector using:

Normal sequences

Abnormal sequences

Sensor noise

Gradual changes

Sudden changes

Stage 8 — Vision

Test worker detection under:

Darkness

Low visibility

Smoke/dust simulation

Different distances

Different worker poses

Stage 9 — Integrated mock mine

Evaluate:

End-to-end latency

Packet loss

Detection performance

Battery life

Rover mobility

Communication reliability

Hazard response

Operator usability

Challenges and Mitigation

Challenge

Mitigation

Wi-Fi attenuation underground

Use relay/mesh architecture and LoRa backup

TCP connection loss

Persistent connection + automatic reconnection

Duplicate telemetry

Packet IDs + deduplication

TCP stream fragmentation

Newline-delimited JSON or another framing method

LoRa low bandwidth

Send only critical telemetry/alerts

Dust/smoke affecting cameras

Combine RGB/night vision with thermal sensing

Sensor noise

Calibration + Kalman filtering

AI false positives/negatives

Combine model output with engineering thresholds and operator confirmation

Uneven terrain

Obstacle detection + controlled speed + manual override

Battery limitations

Continuous battery monitoring

Rover immobilization

Rugged mobility design and manual recovery

Underground positioning

Future SLAM/localization improvements

Communication infrastructure damage

Redundant communication paths

Hazardous atmosphere

Appropriate hardware selection and safety validation

Fully autonomous navigation

Use human-in-the-loop semi-autonomy for the prototype

Safety and Scope

DeepGuard AI is a prototype/proof-of-concept system.

A real underground mine deployment is safety-critical and requires substantially more engineering validation than a hackathon prototype.

Real deployment would require, as applicable:

Ruggedization

Environmental testing

Electrical safety validation

Explosion/intrinsic-safety assessment

Mine-specific certification

Reliable communication engineering

Sensor calibration and validation

Fail-safe control

Extensive field testing

The prototype should therefore be tested first in a controlled/mock-mine environment.

AI output must be treated as decision support, especially for critical rescue actions.

Future Enhancements

Potential future extensions include:

Advanced autonomy

SLAM

LiDAR-based mapping

Autonomous path planning

Dynamic obstacle avoidance

Multi-agent rescue

Ground Rover → Inspection
Aerial Drone → Difficult-area exploration
Relay Unit   → Communication extension

Multiple robots could cooperate during large rescue missions.

Communication relays

Deployable relay nodes could create an ad-hoc communication network deeper inside the mine.

Better localization

Future versions can integrate:

LiDAR

IMU

UWB

Visual odometry

SLAM

to improve GPS-denied localization.

Predictive maintenance

AI could monitor rover motors, battery, and other equipment for early failure detection.

Digital mine map

A future version could maintain a 2D/3D representation of the mine and show:

Rover position

Worker locations

Hazard zones

Environmental readings

Safe/unsafe routes

Expected Impact

DeepGuard AI aims to provide:

Safer reconnaissance of hazardous mine areas

Earlier awareness of dangerous atmospheric conditions

Better rescue-team situational awareness

Assisted trapped-worker localization

Reduced direct exposure of rescue personnel

Continuous environmental monitoring

Remote operation

Redundant emergency communication

Faster and more informed rescue decisions

Structured telemetry data for future AI improvement

A modular foundation for multi-rover rescue systems

Innovation

DeepGuard AI combines multiple technologies into one rescue platform:

Environmental sensing

AI/ML anomaly detection

RGB/night-vision computer vision

Thermal worker localization

Rover robotics

Human-in-the-loop semi-autonomy

Wi-Fi/TCP communication

LoRa emergency redundancy

Real-time telemetry

MongoDB historical storage

Latest-15 telemetry visualization

Remote rover control

The combination is designed around the practical constraints of underground rescue rather than treating AI or robotics as isolated components.

Conclusion

DeepGuard AI is a modular, human-in-the-loop underground mine safety and rescue platform.

The rover collects environmental and visual information and transmits it to a safer control station. AI/ML assists with environmental anomaly detection and computer vision assists with worker and hazard detection. Wi-Fi/TCP provides the primary communication path, while LoRa provides a low-bandwidth emergency backup. MongoDB provides telemetry storage, and the dashboard gives rescue personnel real-time situational awareness and remote control.

The system is intentionally designed so that automation assists rescue personnel rather than replacing critical human decisions.

The prototype can be progressively extended toward:

stronger autonomous navigation,

improved underground localization,

communication relays,

multi-rover coordination,

richer mine mapping,

and more advanced AI-based rescue assistance.

DeepGuard AI

Sense. Analyze. Locate. Rescue.

AI-powered intelligence for safer underground mine reconnaissance and rescue.
