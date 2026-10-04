import os
import json
import io
import csv
import math
import random
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import engine, Base, get_db, SessionLocal
from backend.models import Patient, Assessment, Trial, ClinicianNote
from backend.schemas import (
    PatientCreate, PatientOut,
    AssessmentCreate, AssessmentOut,
    TrialCreate, TrialOut,
    ClinicianNoteCreate, ClinicianNoteOut,
    DashboardStats
)
from backend.simulation import generate_trial_time_series

# Initialize DB tables
Base.metadata.create_all(bind=engine)

def seed_initial_data():
    db = SessionLocal()
    try:
        p1_check = db.query(Patient).filter(Patient.id == "P-001").first()
        if not p1_check:
            p1 = Patient(
                id="P-001", name="A. Mehta", age=28, sex="Female",
                dominant_side="Right", affected_side="Left",
                nprs_pain=4, activity="Badminton / Desk work", prev_injury="Yes",
                assessment_type="Baseline"
            )
            p2 = Patient(
                id="P-002", name="R. Shah", age=34, sex="Male",
                dominant_side="Right", affected_side="Right",
                nprs_pain=6, activity="Gym / Overhead lifting", prev_injury="No",
                assessment_type="Follow-up"
            )
            p3 = Patient(
                id="P-003", name="S. Jain", age=22, sex="Female",
                dominant_side="Left", affected_side="Left",
                nprs_pain=2, activity="Swimming", prev_injury="No",
                assessment_type="Research visit"
            )
            db.add_all([p1, p2, p3])
            db.commit()

            # Seed an assessment and trial for P-001
            a1 = Assessment(
                patient_id="P-001",
                movement="Arm elevation — flexion",
                trials_count=3,
                range_deg="0° → 120°",
                phase="Elevation + lowering",
                calibration_quality=96,
                status="Complete"
            )
            db.add(a1)
            db.commit()
            db.refresh(a1)

            t1_data = generate_trial_time_series("Flexion", 4.0, 50)
            t1 = Trial(
                assessment_id=a1.id,
                trial_number=1,
                arm_elevation_max=120.0,
                scapula_r_max=32.0,
                scapula_l_max=24.0,
                asymmetry_deg=8.0,
                symmetry_percent=75.0,
                ut_r=60.0,
                ut_l=45.0,
                mt_r=35.0,
                mt_l=20.0,
                lt_r=35.0,
                lt_l=20.0,
                sa_r=42.0,
                sa_l=62.0,
                time_series_json=json.dumps(t1_data)
            )
            db.add(t1)

            note1 = ClinicianNote(
                patient_id="P-001",
                assessment_id=a1.id,
                note_text="Patient demonstrates 8° left scapular upward rotation deficit at 120° arm elevation. Serratus anterior activation is delayed on the affected left side. Recommended scapular stabilization and serratus punches 3x/week."
            )
            db.add(note1)
            db.commit()
    finally:
        db.close()

# Ensure database is seeded
seed_initial_data()

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_initial_data()
    yield

app = FastAPI(title="SCAPTRACK API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- API ENDPOINTS ----------------

@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    active_count = db.query(Patient).count()
    assessments_count = db.query(Assessment).count()
    pending_count = db.query(Assessment).filter(Assessment.status != "Complete").count()
    return {
        "active_patients": active_count,
        "today_assessments": max(1, assessments_count),
        "reports_pending": pending_count if pending_count > 0 else 2,
        "device_health": 98
    }

@app.get("/api/patients", response_model=List[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).order_by(Patient.created_at.desc()).all()

@app.get("/api/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p

@app.post("/api/patients", response_model=PatientOut)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.id == payload.id).first()
    if existing:
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing
    new_patient = Patient(**payload.model_dump())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@app.get("/api/assessments/latest/{patient_id}", response_model=Optional[AssessmentOut])
def get_latest_assessment(patient_id: str, db: Session = Depends(get_db)):
    ass = db.query(Assessment).filter(Assessment.patient_id == patient_id).order_by(Assessment.created_at.desc()).first()
    return ass

@app.post("/api/assessments", response_model=AssessmentOut)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    ass = Assessment(**payload.model_dump())
    db.add(ass)
    db.commit()
    db.refresh(ass)
    return ass

@app.post("/api/trials", response_model=TrialOut)
def record_trial(payload: TrialCreate, db: Session = Depends(get_db)):
    trial = Trial(**payload.model_dump())
    if not trial.time_series_json:
        ts_data = generate_trial_time_series("Flexion", 4.0, 50)
        trial.time_series_json = json.dumps(ts_data)
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial

@app.get("/api/notes/{patient_id}", response_model=Optional[ClinicianNoteOut])
def get_notes(patient_id: str, db: Session = Depends(get_db)):
    note = db.query(ClinicianNote).filter(ClinicianNote.patient_id == patient_id).order_by(ClinicianNote.updated_at.desc()).first()
    return note

@app.post("/api/notes", response_model=ClinicianNoteOut)
def save_notes(payload: ClinicianNoteCreate, db: Session = Depends(get_db)):
    note = db.query(ClinicianNote).filter(ClinicianNote.patient_id == payload.patient_id).first()
    if note:
        note.note_text = payload.note_text
        note.updated_at = datetime.now(timezone.utc)
    else:
        note = ClinicianNote(**payload.model_dump())
        db.add(note)
    db.commit()
    db.refresh(note)
    return note

@app.get("/api/export/research/{patient_id}")
def export_research_csv(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    assessments = db.query(Assessment).filter(Assessment.patient_id == patient_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "study_id", "patient_id", "age", "sex", "dominant_side", "affected_side",
        "nprs_pain", "assessment_type", "assessment_id", "trial_id", "timestamp_s",
        "arm_elevation_deg", "scapula_r_upward_deg", "scapula_l_upward_deg",
        "scapula_r_tilt_deg", "scapula_l_tilt_deg", "scapula_r_protraction_deg", "scapula_l_protraction_deg",
        "emg_ut_r_uV", "emg_ut_l_uV", "emg_sa_r_uV", "emg_sa_l_uV", "emg_mt_uV", "emg_lt_uV"
    ])

    for a in assessments:
        for t in a.trials:
            if t.time_series_json:
                points = json.loads(t.time_series_json)
                for pt in points:
                    writer.writerow([
                        "SCAP-001", patient.id, patient.age, patient.sex, patient.dominant_side, patient.affected_side,
                        patient.nprs_pain, patient.assessment_type, a.id, t.id, pt.get("timestamp_s", 0),
                        pt.get("arm_elevation_deg", 0), pt.get("scapula_r_upward_deg", 0), pt.get("scapula_l_upward_deg", 0),
                        pt.get("scapula_r_tilt_deg", 0), pt.get("scapula_l_tilt_deg", 0),
                        pt.get("scapula_r_protraction_deg", 0), pt.get("scapula_l_protraction_deg", 0),
                        pt.get("emg_ut_r_uV", 0), pt.get("emg_ut_l_uV", 0), pt.get("emg_sa_r_uV", 0), pt.get("emg_sa_l_uV", 0),
                        pt.get("emg_mt_uV", 0), pt.get("emg_lt_uV", 0)
                    ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={patient_id}_scaptrack_research.csv"}
    )


# ---------------- PRE-TRAINED MODELS API ----------------
from backend.models_pretrained import (
    list_pretrained_models,
    get_pretrained_model,
    generate_model_frame,
    generate_model_curves
)

@app.get("/api/models/list")
def get_models_list():
    """Returns list of pre-trained clinical biomechanical models and AI classifiers."""
    return list_pretrained_models()

@app.get("/api/models/{model_id}")
def get_model_details(model_id: str):
    """Returns full metadata and biomechanical parameters of a pre-trained model."""
    model = get_pretrained_model(model_id)
    return model

@app.get("/api/models/{model_id}/curves")
def get_model_kinematic_curves(model_id: str):
    """Returns full kinematic trajectory curves & normative 95% confidence bands."""
    return generate_model_curves(model_id)

@app.post("/api/models/predict")
def run_model_inference(payload: dict):
    """
    Runs pre-trained model inference on custom angles or returns model diagnostic evaluation.
    """
    model_id = payload.get("model_id", "type2_dyskinesis")
    model = get_pretrained_model(model_id)
    curves = generate_model_curves(model_id)
    return {
        "status": "success",
        "model_id": model_id,
        "model_name": model["name"],
        "architecture": model["architecture"],
        "classification": model["classification"],
        "confidence": model["confidence"],
        "dyskinesis_risk_percent": model["dyskinesis_risk_percent"],
        "inference_latency_ms": model["inference_latency_ms"],
        "curves": curves,
        "recommendation": "Prescribe Serratus Anterior activation and Lower Trapezius neuromuscular re-education." if "type" in model_id else "Maintain balanced athletic conditioning."
    }


# ---------------- WEBSOCKET STREAM (LIVE & PRE-TRAINED TOGGLE) ----------------

@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket, mode: str = "live", model: str = "type2_dyskinesis"):
    await websocket.accept()
    
    current_mode = mode
    current_model = model
    step = 0

    async def message_receiver():
        nonlocal current_mode, current_model
        try:
            while True:
                msg_text = await websocket.receive_text()
                try:
                    data = json.loads(msg_text)
                    if data.get("action") == "set_mode":
                        if "mode" in data:
                            current_mode = data["mode"]
                        if "model_id" in data:
                            current_model = data["model_id"]
                    elif data.get("action") == "set_model":
                        if "model_id" in data:
                            current_model = data["model_id"]
                except Exception:
                    pass
        except Exception:
            pass

    receiver_task = asyncio.create_task(message_receiver())

    try:
        while True:
            step = (step + 1) % 100
            
            if current_mode == "pretrained":
                packet = generate_model_frame(current_model, step)
                packet["time"] = datetime.now(timezone.utc).isoformat()
            else:
                phase = step / 100.0
                sin_phase = 0.5 - 0.5 * math.cos(phase * 2.0 * math.pi)
                
                arm_deg = round(120.0 * sin_phase, 1)
                scap_r = round(32.0 * (sin_phase ** 1.1) + random.uniform(-0.15, 0.15), 1)
                scap_l = round(24.0 * (sin_phase ** 1.25) + random.uniform(-0.15, 0.15), 1)
                
                emg_ut = round(15.0 + 75.0 * sin_phase + random.uniform(-8, 8), 1)
                emg_sa = round(12.0 + 82.0 * sin_phase + random.uniform(-6, 6), 1)

                packet = {
                    "type": "live_motion_frame",
                    "mode": "live",
                    "step": step,
                    "arm_elevation": arm_deg,
                    "scapula_r": scap_r,
                    "scapula_l": scap_l,
                    "diff": round(scap_r - scap_l, 1),
                    "normative_ref": round(32.0 * (sin_phase ** 1.1), 1),
                    "normative_band_min": round(max(0.0, 32.0 * (sin_phase ** 1.1) - 3.5), 1),
                    "normative_band_max": round(32.0 * (sin_phase ** 1.1) + 3.5, 1),
                    "emg_ut": emg_ut,
                    "emg_sa": emg_sa,
                    "time": datetime.now(timezone.utc).isoformat()
                }

            await websocket.send_json(packet)
            await asyncio.sleep(0.04)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        receiver_task.cancel()


# ---------------- STATIC ASSETS ----------------
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def get_root_page():
    index_file = os.path.join(STATIC_DIR, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
