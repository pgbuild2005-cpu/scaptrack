# SCAPTRACK — Full-Stack Clinical Motion Lab

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
│       ├── telemetry.js  # Real-time SSE stream ingestion & recording buffer
│       └── app.js        # UI orchestrator, routing & clinical report generation
├── start.sh              # One-command launcher script
├── test_server.py        # Automated test suite (9 integration tests)
└── README.md
```

---

## Features

1. **Dashboard:** Active patient metrics, readiness status, recent assessments, and a 6-step clinical protocol checklist.
2. **Patient Management:** Create anonymized/coded patient records (HIPAA/GDPR-compliant format), NPRS pain scores, activity levels, and assessment types (Baseline, Follow-up, Research).
3. **Sensor Setup & Anatomical Body Map:** Visual landmark placement on scapula (Superior Angle, Spine, Inferior Angle) and thoracic spine (T2, T4, T7).
4. **Assessment Protocol & Calibration:** Static calibration check and 6-channel sEMG electrode signal verification (Upper/Middle/Lower Trapezius, Serratus Anterior, Infraspinatus, Deltoid).
5. **Live Kinematics & Synchronized EMG:** Real-time 50Hz telemetry streaming arm elevation (0°–120°–0°), Right vs. Left upward rotation, and live multi-channel EMG oscilloscope sweep.
6. **Clinical Reports:** Objective comparison tables, symmetry metrics, muscle activation percentages (%MVIC), clinician notes editor, and one-click PDF/Print layout.
7. **Research Mode:** Direct export of structured time-series datasets to CSV formatted for SPSS, R, MATLAB, and Python analysis.
8. **Device Settings:** Hub status, battery health, and sensor calibration utilities.

---

## Quick Start

### Running the Application:
```bash
cd /home/pg_build/.gemini/antigravity/scratch/scaptrack_app
./start.sh
```
Or directly:
```bash
python3 backend/server.py
```
Open **`http://localhost:8000`** in any modern web browser.

### Running the Test Suite:
```bash
python3 test_server.py
```

---

## REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/patients` | List all registered patients and trial counts |
| `POST` | `/api/patients` | Create a new patient profile |
| `GET` | `/api/patients/{id}` | Get specific patient details and history |
| `POST` | `/api/trials` | Save movement trial data and time-series points |
| `GET` | `/api/reports/{code}` | Retrieve compiled clinical report data |
| `POST` | `/api/notes` | Update clinician notes and treatment recommendations |
| `GET` | `/api/research/export` | Download research-grade CSV dataset |
| `GET` | `/api/sensors/status` | Real-time hardware health and readiness |
| `GET` | `/api/live/stream` | Server-Sent Events (SSE) live kinematic & EMG telemetry |
