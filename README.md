# SCAPTRACK — Clinical Biomechanics & Kinematics Lab

**SCAPTRACK** is a full-stack clinical biomechanics and wearable sensor platform engineered for assessing 3D scapulothoracic kinematics (upward rotation, posterior tilt, protraction) synchronized with 6-channel periscapular surface electromyography (sEMG).

The platform features real-time wireless telemetry ingestion from multi-node **ESP32 WROOM-32D / ESP32-S3** hardware hubs, database persistence with historical session recording, granular live health diagnostics for **18 anatomical IMU landmarks**, and a toggleable suite of **pre-trained DeepKinematics™ AI models**.

---

## 🌟 Key Features

### 1. Dual-Mode Stream Engine (Live Hardware vs Pre-trained AI Model)
* **Global Mode Switcher**: Toggle dynamically between **Live Sensor Stream** (50Hz Real-Time Hardware Feed) and **Pre-trained AI Models** (DeepKinematics™ Biomechanical Priors & Dyskinesis Classifier) from both the top navigation bar and the Live Analysis view.
* **Pre-trained Clinical AI Models**:
  * **DeepKinematics™ Normative Baseline**: Gold-standard asymptomatic 2:1 scapulohumeral rhythm (32° peak upward rotation, balanced periscapular sEMG recruitment, 98.7% accuracy).
  * **Type II Scapular Dyskinesis (Medial Border Winging)**: 8.0° upward rotation lag, lower trapezius deficit, 94.2% dyskinesis risk.
  * **Type I Dyskinesis (Subacromial Impingement)**: Inferior angle tilt, anterior tilt excess, delayed Serratus Anterior activation.
  * **Type III Dyskinesis (Rotator Cuff Compensation)**: Early shoulder shrug, Upper Trapezius hyperactivity.
  * **Overhead Throwing Athlete**: High-velocity scaption adaptation with dominant upward rotation bias (36°).
* **Normative 95% Confidence Shaded Band**: Shaded reference band rendered on the kinematics chart to visually benchmark live patient movement or model predictions against healthy physiological bounds.
* **Real-time AI Diagnostics**: Displays neural architecture (`BiLSTM-Transformer v2.4`), inference latency (`~10ms`), Kibler clinical classification, dyskinesis risk score, and model confidence in real time.

---

### 2. ESP32 Wireless Telemetry & Hardware Hub Integration
* **High-Frequency Wireless Ingestion**: Ingests 50Hz wireless telemetry packets over WiFi / HTTP REST (`POST /api/esp32/telemetry`) and WebSockets (`ws://localhost:8000/ws/live`).
* **Arduino / ESP32 C++ Master Firmware**: Ready-to-flash sketch located at `main_esp32_hub/esp32_scaptrack_imu_hub.ino`.
* **Wireless Network Simulator**: Built-in Python test transmitter script (`esp32_wireless_tester.py`) to stream 50Hz wireless frames during testing.
* **Master Hub Telemetry**: Monitors hub IP address, MAC, WiFi signal RSSI (dBm), battery level, and packet throughput.

---

### 3. Granular Live Status for 18 IMU Sensor Landmarks
Each of the 18 individual IMU sensor nodes is tracked and displayed with live telemetry:
* **Right Scapular Triad & Acromion**: Superior Angle (`SA1`), Root of Spine (`SA2`), Inferior Angle (`SA3`), Acromion (`AC1`)
* **Left Scapular Triad & Acromion**: Superior Angle (`SA4`), Root of Spine (`SA5`), Inferior Angle (`SA6`), Acromion (`AC2`)
* **Thoracic Spine References**: T2 (`T2`), T4 (`T4`), T7 (`T7`), Sternal Notch (`STN`)
* **Bilateral Upper Extremity**: Right Upper Arm (`ARM_R`), Right Forearm (`WRIST_R`), Left Upper Arm (`ARM_L`), Left Forearm (`WRIST_L`)
* **Periscapular sEMG Units**: Right 3-Ch sEMG (`EMG_R`), Left 3-Ch sEMG (`EMG_L`)
* **Individual Monitored Metrics**:
  * 🟢 **Live Status & Calibration State** (`Calibrated`, `Calibrating`, `Offline`)
  * 🔋 **Battery Level** (e.g., `96%`)
  * 📶 **Wireless RF Signal Strength** (e.g., `-42 dBm`)
  * 🌡 **Operating Temperature** (e.g., `32.1°C`)
  * 📐 **Real-Time 3D Orientation Readout** (Roll, Pitch, Yaw in degrees)

---

### 4. Database Persistence & Historical Session Recording (SQLite)
* **One-Click Session Recording**: Start and stop persistent wireless recording sessions directly from the dashboard (`🔴 Record to Database` / `⏹ Stop & Save Session`).
* **Database Models (`backend/models.py`)**:
  * `ESP32Device`: Master wireless hub state, IP, MAC, battery, and firmware version.
  * `IMUSensorNode`: 18 individual sensor records with calibration, battery, and orientation.
  * `ESP32RecordingSession`: Historical recorded trial sessions with total packet counts, durations, and protocol metadata.
  * `ESP32TelemetryRecord`: Time-series kinematic curves and full 18-sensor payload JSON.
* **Historical Sessions Explorer**: View past saved trials in the database and export raw time-series datasets as CSV (`/api/esp32/sessions/{session_id}/export`).

---

### 5. Clinical Reports & Research Data Export
* **Objective Findings & Bilateral Comparison**: Range of motion tables, asymmetry deficits, and %MVIC muscle activation ratios.
* **Clinician Notes**: Persistent notes editor with database backing and print-to-PDF formatting.
* **Research CSV Export**: Export synchronized high-frequency kinematic and sEMG datasets formatted for SPSS, R, Python, and MATLAB.

---

## 🌐 Live Public Access (Online)

The platform is hosted and accessible globally on the internet:

* 🔗 **Live Web Dashboard**: **[https://clearing-arrivals-softball-dame.trycloudflare.com](https://clearing-arrivals-softball-dame.trycloudflare.com)**
* 📚 **Interactive Swagger API Docs**: **[https://clearing-arrivals-softball-dame.trycloudflare.com/docs](https://clearing-arrivals-softball-dame.trycloudflare.com/docs)**
* 📡 **Live WebSocket Feed**: `wss://clearing-arrivals-softball-dame.trycloudflare.com/ws/live`
* 🔌 **ESP32 Ingestion URL**: `https://clearing-arrivals-softball-dame.trycloudflare.com/api/esp32/telemetry`

---

## 🚀 Quick Start

### 1. Launch the Application Server
```bash
./start.sh
```
Or manually using the virtual environment:
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Open the Web Dashboard
Navigate to:
```
http://localhost:8000
```

### 3. Interactive API Documentation
Access Swagger UI at:
```
http://localhost:8000/docs
```

---

## 📡 Wireless ESP32 Testing

### Stream Simulated 50Hz Wireless Telemetry
To test wireless packet ingestion without physical hardware, run the test transmitter:
```bash
python3 esp32_wireless_tester.py http://localhost:8000/api/esp32/telemetry
```

### Flash ESP32 Firmware
Open `main_esp32_hub/esp32_scaptrack_imu_hub.ino` in the Arduino IDE or PlatformIO, configure your WiFi credentials and server IP, and flash onto your ESP32 board.

---

## 📚 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web Application Dashboard |
| `GET` | `/api/dashboard/stats` | High-level clinical statistics |
| `GET` | `/api/patients` | List all registered patient profiles |
| `POST` | `/api/patients` | Create or update patient profile |
| `GET` | `/api/models/list` | List all pre-trained AI biomechanical models |
| `GET` | `/api/models/{id}/curves` | Get kinematic trajectories & 95% CI normative bands |
| `POST` | `/api/models/predict` | Run AI dyskinesis classification inference |
| `POST` | `/api/esp32/telemetry` | Ingest live 50Hz wireless packet from ESP32 |
| `GET` | `/api/esp32/status` | Live status of ESP32 hub and all 18 IMU sensors |
| `POST` | `/api/esp32/session/start` | Start persistent database recording session |
| `POST` | `/api/esp32/session/stop` | Stop active recording session |
| `GET` | `/api/esp32/sessions` | List all historical recorded sessions |
| `GET` | `/api/esp32/sessions/{id}` | Get time-series records for a session |
| `GET` | `/api/esp32/sessions/{id}/export` | Download session telemetry as CSV |
| `WS` | `/ws/live` | WebSocket real-time live motion feed |

---

## 🧪 Running Automated Tests

Run the complete test suite (12 unit and integration tests):
```bash
PYTHONPATH=. ./venv/bin/pytest tests/test_api.py -v
```

---

## 📁 Project Structure

```
scaptrack/
├── backend/
│   ├── database.py              # SQLite database connection & session setup
│   ├── models.py                # SQLAlchemy ORM models (Patients, ESP32, IMUs, Sessions)
│   ├── schemas.py               # Pydantic schemas for validation
│   ├── simulation.py            # High-frequency biomechanical trajectory simulator
│   ├── models_pretrained.py     # Pre-trained DeepKinematics™ AI models & normative bounds
│   └── esp32_manager.py         # ESP32 wireless ingestion & 18-IMU node manager
├── static/
│   ├── css/
│   │   └── styles.css           # Modern clinical UI theme, gauges & mode switchers
│   ├── js/
│   │   ├── app.js               # Application state, patient forms & notes controller
│   │   └── live_stream.js       # WebSocket engine, ESP32 recording & 18-IMU matrix
│   └── index.html               # Multi-view clinical dashboard & live motion lab
├── tests/
│   └── test_api.py              # Comprehensive test suite for APIs & WebSockets
├── main_esp32_hub/
│   └── esp32_scaptrack_imu_hub.ino # ESP32 C++/Arduino wireless transmitter firmware
├── esp32_wireless_tester.py     # Standalone 50Hz Python wireless transmitter utility
├── main.py                      # FastAPI application entrypoint & REST/WS endpoints
├── requirements.txt             # Python dependencies
├── scaptrack.db                 # SQLite persistent database
└── start.sh                     # Automated startup script
```
