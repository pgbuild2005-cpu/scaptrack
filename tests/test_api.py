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
    """Verify WebSocket stream connection and message structure."""
    with client.websocket_connect("/ws/live") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "live_motion_frame"
        assert "arm_elevation" in data
        assert "scapula_r" in data
        assert "scapula_l" in data
        assert "emg_ut" in data
        assert "emg_sa" in data
