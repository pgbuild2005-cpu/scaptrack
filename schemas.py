from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PatientBase(BaseModel):
    id: str = Field(..., description="Coded Patient ID", json_schema_extra={"example": "P-004"})
    name: str = Field(..., description="Patient Name", json_schema_extra={"example": "A. Mehta"})
    age: int = Field(25, json_schema_extra={"example": 25})
    sex: str = Field("Female", json_schema_extra={"example": "Female"})
    dominant_side: str = Field("Right", json_schema_extra={"example": "Right"})
    affected_side: str = Field("Left", json_schema_extra={"example": "Left"})
    nprs_pain: int = Field(4, ge=0, le=10, json_schema_extra={"example": 4})
    activity: Optional[str] = Field("", json_schema_extra={"example": "Tennis / Badminton"})
    prev_injury: str = Field("No", json_schema_extra={"example": "No"})
    assessment_type: str = Field("Baseline", json_schema_extra={"example": "Baseline"})

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TrialCreate(BaseModel):
    assessment_id: int
    trial_number: int = 1
    arm_elevation_max: float = 120.0
    scapula_r_max: float = 32.0
    scapula_l_max: float = 24.0
    asymmetry_deg: float = 8.0
    symmetry_percent: float = 75.0
    ut_r: float = 60.0
    ut_l: float = 45.0
    mt_r: float = 35.0
    mt_l: float = 20.0
    lt_r: float = 35.0
    lt_l: float = 20.0
    sa_r: float = 42.0
    sa_l: float = 62.0
    time_series_json: Optional[str] = None

class TrialOut(TrialCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AssessmentCreate(BaseModel):
    patient_id: str
    movement: str = "Arm elevation — flexion"
    trials_count: int = 3
    range_deg: str = "0° → 120°"
    phase: str = "Elevation + lowering"
    calibration_quality: int = 96
    status: str = "Complete"

class AssessmentOut(AssessmentCreate):
    id: int
    created_at: datetime
    trials: List[TrialOut] = []
    model_config = ConfigDict(from_attributes=True)

class ClinicianNoteCreate(BaseModel):
    patient_id: str
    assessment_id: Optional[int] = None
    note_text: str

class ClinicianNoteOut(ClinicianNoteCreate):
    id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DashboardStats(BaseModel):
    active_patients: int
    today_assessments: int
    reports_pending: int
    device_health: int
  
