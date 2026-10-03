# SCAPTRACK — Clinical Biomechanics & Kinematics Lab

Full-stack clinical web application for assessing scapular kinematics (upward rotation, posterior tilt, protraction) synchronized with 6-channel surface electromyography (sEMG).

---

## Features
- **Dashboard**# SCAPTRACK — Full-Stack Clinical Motion Lab

An integrated clinical biomechanics and surface electromyography (sEMG) application for assessing scapular dyskinesis, shoulder kinematics, and neuromuscular coordination.

---

## Architecture Overview

```
scaptrack_app/
├── backend/
│   ├── database.py       # SQLite database schema, connection pool & seed data
│   ├── server.py         # Multi-threaded HTTP server, REST APIs & SSE live telemetry
│   └── scaptrack.db      # SQLite persistent clinical database
├── frontend/
│   ├── index.html        # Semantic HTML5 Single Page Application
│   ├── css/
│   │   └── styles.css    # Clinical design system, tokens, responsive & print media
│   └── js/
│       ├── api.js        # REST API client (Fetch / Promise-based)
│       ├── charts.js     # Kinematics SVG chart & Canvas EMG oscilloscope
: System readiness, live sensor telemetry (18 online BLE channels), quick patient review.
- **Patient Management**: Coded patient demographics, NPRS pain scale (0–10), affected side, baseline/follow-up tracking.
- **Sensor Setup & Body Landmark Map**: Interactive visual body guide for scapular (1–3), thoracic (T2, T4, T7), and humeral sensors.
- **Assessment Protocol**: Static zero-calibration verification, SENIAM EMG impedance diagnostics, and customizable trial parameters.
- **Live Biomechanical Analysis**: Real-time kinematic curves (SVG), dynamic angle readouts, 3D posture visualizer, and 50Hz/1kHz live sEMG oscilloscope feed via WebSockets (`/ws/live`).
- **Automated Clinical Reports**: Side-by-side range-of-motion comparison, asymmetry calculations, %MVIC muscle activation tables, and persistent clinician note editor with print-to-PDF formatting.
- **Research Data Export**: Export synchronized high-frequency motion and sEMG datasets as CSV for SPSS, R, Python, and MATLAB.

---

## Quick Start

### 1. Launch the Server
```bash
./start.sh
```
Or manually:
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Open the Web Application
Open your browser and navigate to:
```
http://localhost:8000
```

### 3. Interactive API Documentation
Access Swagger UI at:
```
http://localhost:8000/docs
```

---

## Automated Tests
To run the automated API and endpoint tests:
```bash
PYTHONPATH=. ./venv/bin/pytest tests/test_api.py -v
```
