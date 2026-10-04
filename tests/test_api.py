import json
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_static_assets_serving():
    """Verify HTML, CSS, and JavaScript files are served correctly."""
    # Index HTML
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert "SCAPTRACK" in res_html.text
    assert "<!DOCTYPE html>" in res_html.text

    # CSS stylesheet
    res_css = client.get("/static/css/styles.css")
    assert res_css.status_code == 200
    assert "--cyan:" in res_css.text

    # App JS
    res_app_js = client.get("/static/js/app.js")
    assert res_app_js.status_code == 200
    assert "SCAPTRACK" in res_app_js.text

    # Live Stream JS
    res_live_js = client.get("/static/js/live_stream.js")
    assert res_live_js.status_code == 200
    assert "renderLiveFrame" in res_live_js.text

def test_dashboard_stats():
    """Verify dashboard metrics calculation."""
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["active_patients"] >= 3
    assert data["today_assessments"] >= 1
    assert data["device_health"] == 98

def test_patient_crud_lifecycle():
    """Verify patient profile creation, update, and retrieval."""
    # 1. Create Patient
    payload = {
        "id": "P-010",
        "name": "K. Patel",
        "age": 31,
        "sex": "Female",
        "dominant_side": "Right",
        "affected_side": "Right",
        "nprs_pain": 5,
        "activity": "CrossFit",
        "prev_injury": "Yes",
        "assessment_type": "Baseline"
    }
    create_res = client.post("/api/patients", json=payload)
    assert create_res.status_code == 200
    assert create_res.json()["id"] == "P-010"

    # 2. Get Patient by ID
    get_res = client.get("/api/patients/P-010")
    assert get_res.status_code == 200
    assert get_res.json()["activity"] == "CrossFit"

    # 3. Update existing patient
    payload["activity"] = "CrossFit / Weightlifting"
    update_res = client.post("/api/patients", json=payload)
    assert update_res.status_code == 200
    assert update_res.json()["activity"] == "CrossFit / Weightlifting"

def test_assessments_and_trials():
    """Verify assessment creation and trial recording."""
    # Create Assessment for P-010
    ass_payload = {
        "patient_id": "P-010",
        "movement": "Arm elevation — abduction",
        "trials_count": 3,
        "range_deg": "0° → 180°",
        "phase": "Elevation + lowering",
        "calibration_quality": 98,
        "status": "In Progress"
    }
    ass_res = client.post("/api/assessments", json=ass_payload)
    assert ass_res.status_code == 200
    ass_id = ass_res.json()["id"]

    # Record Trial for the assessment
    trial_payload = {
        "assessment_id": ass_id,
        "trial_number": 1,
        "arm_elevation_max": 180.0,
        "scapula_r_max": 34.5,
        "scapula_l_max": 33.0,
        "asymmetry_deg": 1.5,
        "symmetry_percent": 95.0,
        "ut_r": 55.0,
        "ut_l": 52.0,
        "mt_r": 30.0,
        "mt_l": 30.0,
        "lt_r": 32.0,
        "lt_l": 31.0,
        "sa_r": 50.0,
        "sa_l": 49.0
    }
    trial_res = client.post("/api/trials", json=trial_payload)
    assert trial_res.status_code == 200
    assert trial_res.json()["trial_number"] == 1

    # Fetch latest assessment
    latest_res = client.get("/api/assessments/latest/P-010")
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == ass_id

def test_clinician_notes():
    """Verify saving and retrieving clinician notes."""
    payload = {
        "patient_id": "P-010",
        "note_text": "Good bilateral symmetry restored after 6 weeks."
    }
    save_res = client.post("/api/notes", json=payload)
    assert save_res.status_code == 200

    get_res = client.get("/api/notes/P-010")
    assert get_res.status_code == 200
    assert "Good bilateral symmetry" in get_res.json()["note_text"]

def test_research_csv_export():
    """Verify research CSV structure and column headers."""
    res = client.get("/api/export/research/P-001")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    
    lines = res.text.strip().split("\n")
    header = lines[0].split(",")
    assert "study_id" in header
    assert "patient_id" in header
    assert "scapula_r_upward_deg" in header
    assert "emg_ut_r_uV" in header
    assert len(lines) > 10  # Ensure time-series data points are present

def test_websocket_stream_frame():
    """Verify WebSocket stream connection and message structure in live mode."""
    with client.websocket_connect("/ws/live") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "live_motion_frame"
        assert data["mode"] == "live"
        assert "arm_elevation" in data
        assert "scapula_r" in data
        assert "scapula_l" in data
        assert "emg_ut" in data
        assert "emg_sa" in data

def test_models_list_and_curves():
    """Verify pre-trained models catalog and kinematic curve generation."""
    # List models
    list_res = client.get("/api/models/list")
    assert list_res.status_code == 200
    models = list_res.json()
    assert len(models) >= 4
    model_ids = [m["id"] for m in models]
    assert "normative" in model_ids
    assert "type2_dyskinesis" in model_ids

    # Fetch curves for Type II Dyskinesis
    curves_res = client.get("/api/models/type2_dyskinesis/curves")
    assert curves_res.status_code == 200
    curves = curves_res.json()
    assert curves["model_id"] == "type2_dyskinesis"
    assert "elevations" in curves
    assert "scapula_r" in curves
    assert "scapula_l" in curves
    assert "normative_band_min" in curves
    assert "normative_band_max" in curves
    assert len(curves["elevations"]) > 10

def test_model_prediction_endpoint():
    """Verify model inference API prediction."""
    payload = {"model_id": "type1_dyskinesis"}
    res = client.post("/api/models/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["model_id"] == "type1_dyskinesis"
    assert "classification" in data
    assert "confidence" in data
    assert data["dyskinesis_risk_percent"] > 50

def test_websocket_pretrained_mode_and_toggling():
    """Verify WebSocket streaming in pre-trained mode and dynamic message toggling."""
    # 1. Connect with pre-trained mode query parameter
    with client.websocket_connect("/ws/live?mode=pretrained&model=type2_dyskinesis") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "model_prediction_frame"
        assert data["mode"] == "pretrained"
        assert data["model_id"] == "type2_dyskinesis"
        assert "classification" in data
        assert "confidence" in data
        assert "normative_band_min" in data

        # 2. Dynamically send toggle message back to live mode over WebSocket
        websocket.send_text(json.dumps({"action": "set_mode", "mode": "live"}))
        
        # Read next frames until live frame arrives
        received_live = False
        for _ in range(5):
            next_data = websocket.receive_json()
            if next_data.get("mode") == "live":
                received_live = True
                assert next_data["type"] == "live_motion_frame"
                assert "sensors" in next_data
                break
        assert received_live is True

def test_esp32_hardware_status_and_18_sensors():
    """Verify live status of ESP32 hub and all 18 individual IMU sensors."""
    res = client.get("/api/esp32/status")
    assert res.status_code == 200
    data = res.json()
    assert "hub" in data
    assert data["hub"]["status"] in ["Online", "Connected"]
    assert "sensors_summary" in data
    assert data["sensors_summary"]["total"] == 18
    assert "sensor_nodes" in data
    assert len(data["sensor_nodes"]) == 18

    # Verify individual IMU attributes
    sensor_ids = [s["sensor_id"] for s in data["sensor_nodes"]]
    assert "IMU_R_SUP" in sensor_ids
    assert "IMU_L_INF" in sensor_ids
    assert "IMU_T2" in sensor_ids
    assert "IMU_R_HUMERUS" in sensor_ids
    assert "EMG_CH_1_3" in sensor_ids

    # Check that each sensor specifies live status, battery, and signal
    for node in data["sensor_nodes"]:
        assert "calibration_status" in node
        assert "battery_percent" in node
        assert "rssi_dbm" in node
        assert "temperature_c" in node
        assert "roll" in node
        assert "pitch" in node
        assert "yaw" in node

def test_esp32_session_recording_and_database_persistence():
    """Verify starting, ingesting live telemetry packets, stopping, and retrieving database records."""
    # 1. Start a persistent recording session
    start_payload = {
        "patient_id": "P-001",
        "movement_plane": "Sagittal Flexion"
    }
    start_res = client.post("/api/esp32/session/start", json=start_payload)
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["status"] == "recording_started"
    session_id = start_data["session_id"]
    assert session_id.startswith("SESS-")

    # 2. Ingest 5 wireless telemetry packets from simulated ESP32
    for i in range(1, 6):
        pkt = {
            "hub_id": "ESP32-HUB-01",
            "seq": i,
            "timestamp_ms": 1000 + i * 20,
            "arm_elevation_deg": 60.0 + i * 5,
            "scapula_r_deg": 18.0 + i,
            "scapula_l_deg": 14.0 + i,
            "emg_ut_r": 45.0,
            "emg_sa_l": 50.0,
            "sensors": {
                "IMU_R_SUP": {"roll": 18.0, "pitch": 5.0, "yaw": 30.0, "battery_percent": 96.0, "rssi_dbm": -42},
                "IMU_L_INF": {"roll": 14.0, "pitch": 4.0, "yaw": 33.0, "battery_percent": 93.0, "rssi_dbm": -45}
            }
        }
        ingest_res = client.post("/api/esp32/telemetry", json=pkt)
        assert ingest_res.status_code == 200
        assert ingest_res.json()["status"] == "ack"
        assert ingest_res.json()["is_recording"] is True

    # 3. Stop recording session
    stop_res = client.post("/api/esp32/session/stop")
    assert stop_res.status_code == 200
    stop_data = stop_res.json()
    assert stop_data["status"] == "recording_stopped"
    assert stop_data["session_id"] == session_id

    # 4. Verify historical sessions list includes the saved session
    list_res = client.get("/api/esp32/sessions")
    assert list_res.status_code == 200
    sessions = list_res.json()
    matched = [s for s in sessions if s["session_id"] == session_id]
    assert len(matched) == 1
    assert matched[0]["total_packets"] >= 5

    # 5. Retrieve saved telemetry data points for the session
    data_res = client.get(f"/api/esp32/sessions/{session_id}")
    assert data_res.status_code == 200
    session_records = data_res.json()
    assert session_records["session_id"] == session_id
    assert len(session_records["records"]) >= 5

    # 6. Test CSV Export of the saved session
    export_res = client.get(f"/api/esp32/sessions/{session_id}/export")
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    assert f"{session_id}_esp32_raw_telemetry.csv" in export_res.headers["content-disposition"]
    csv_lines = export_res.text.strip().split("\n")
    assert len(csv_lines) >= 6 # Header + 5 records
    assert "session_id,patient_id,seq_number" in csv_lines[0]

