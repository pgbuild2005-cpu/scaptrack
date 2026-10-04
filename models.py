import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(50), primary_key=True, index=True) # e.g. P-001
    name = Column(String(100), nullable=False)
    age = Column(Integer, default=25)
    sex = Column(String(20), default="Female")
    dominant_side = Column(String(20), default="Right")
    affected_side = Column(String(20), default="Left")
    nprs_pain = Column(Integer, default=4)
    activity = Column(String(100), nullable=True)
    prev_injury = Column(String(20), default="No")
    assessment_type = Column(String(50), default="Baseline")
    created_at = Column(DateTime, default=utc_now)

    assessments = relationship("Assessment", back_populates="patient", cascade="all, delete-orphan")
    notes = relationship("ClinicianNote", back_populates="patient", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)
    movement = Column(String(100), default="Arm elevation — flexion")
    trials_count = Column(Integer, default=3)
    range_deg = Column(String(50), default="0° → 120°")
    phase = Column(String(50), default="Elevation + lowering")
    calibration_quality = Column(Integer, default=96)
    status = Column(String(30), default="Complete") # "Complete", "Pending", "In Progress"
    created_at = Column(DateTime, default=utc_now)

    patient = relationship("Patient", back_populates="assessments")
    trials = relationship("Trial", back_populates="assessment", cascade="all, delete-orphan")


class Trial(Base):
    __tablename__ = "trials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    trial_number = Column(Integer, default=1)
    arm_elevation_max = Column(Float, default=120.0)
    scapula_r_max = Column(Float, default=32.0)
    scapula_l_max = Column(Float, default=24.0)
    asymmetry_deg = Column(Float, default=8.0)
    symmetry_percent = Column(Float, default=75.0)
    
    # Muscle activation percentage summary (%MVIC)
    ut_r = Column(Float, default=60.0)
    ut_l = Column(Float, default=45.0)
    mt_r = Column(Float, default=35.0)
    mt_l = Column(Float, default=20.0)
    lt_r = Column(Float, default=35.0)
    lt_l = Column(Float, default=20.0)
    sa_r = Column(Float, default=42.0)
    sa_l = Column(Float, default=62.0)

    # Serialized detailed time series dataset (for research export)
    time_series_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    assessment = relationship("Assessment", back_populates="trials")


class ClinicianNote(Base):
    __tablename__ = "clinician_notes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    note_text = Column(Text, default="")
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    patient = relationship("Patient", back_populates="notes")
