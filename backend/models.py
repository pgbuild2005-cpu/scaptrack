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


# ---------------- ESP32 WIRELESS HUB & IMU SENSORS DATA MODELS ----------------

class ESP32Device(Base):
    __tablename__ = "esp32_devices"

    id = Column(String(50), primary_key=True) # e.g. "ESP32-HUB-01"
    name = Column(String(100), default="SCAPTRACK Master Wireless Hub")
    mac_address = Column(String(50), default="24:6F:28:B4:7A:12")
    ip_address = Column(String(50), default="192.168.4.1")
    firmware_version = Column(String(30), default="v2.1.4-BLE5")
    battery_level = Column(Float, default=92.0)
    rssi_dbm = Column(Integer, default=-44)
    status = Column(String(30), default="Online") # "Online", "Streaming", "Disconnected"
    sampling_rate_hz = Column(Float, default=50.0)
    total_packets_received = Column(Integer, default=0)
    last_heartbeat = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)


class IMUSensorNode(Base):
    __tablename__ = "imu_sensor_nodes"

    sensor_id = Column(String(50), primary_key=True) # e.g. "IMU_R_SUP", "IMU_T2", etc.
    label = Column(String(100), nullable=False) # e.g. "Right Superior Angle"
    body_region = Column(String(50), nullable=False) # "Right Scapula", "Left Scapula", "Thorax", "Humerus", "sEMG"
    landmark_code = Column(String(20), default="SA1")
    is_online = Column(Boolean, default=True)
    calibration_status = Column(String(30), default="Calibrated") # "Calibrated", "Calibrating", "Uncalibrated"
    battery_percent = Column(Float, default=95.0)
    rssi_dbm = Column(Integer, default=-46)
    packet_rate_hz = Column(Float, default=50.0)
    temperature_c = Column(Float, default=32.0)
    roll = Column(Float, default=0.0)
    pitch = Column(Float, default=0.0)
    yaw = Column(Float, default=0.0)
    accel_x = Column(Float, default=0.0)
    accel_y = Column(Float, default=0.0)
    accel_z = Column(Float, default=1.0)
    gyro_x = Column(Float, default=0.0)
    gyro_y = Column(Float, default=0.0)
    gyro_z = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=utc_now)


class ESP32RecordingSession(Base):
    __tablename__ = "esp32_recording_sessions"

    session_id = Column(String(50), primary_key=True) # e.g. "SESS-2026-10-05-001"
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)
    movement_plane = Column(String(100), default="Sagittal Flexion")
    status = Column(String(30), default="Active") # "Active", "Completed", "Archived"
    total_packets = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    avg_sample_rate_hz = Column(Float, default=50.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    records = relationship("ESP32TelemetryRecord", back_populates="session", cascade="all, delete-orphan")


class ESP32TelemetryRecord(Base):
    __tablename__ = "esp32_telemetry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("esp32_recording_sessions.session_id"), nullable=False)
    patient_id = Column(String(50), nullable=False)
    seq_number = Column(Integer, default=0)
    timestamp_ms = Column(Integer, default=0)
    arm_elevation_deg = Column(Float, default=0.0)
    scapula_r_upward_deg = Column(Float, default=0.0)
    scapula_l_upward_deg = Column(Float, default=0.0)
    asymmetry_deg = Column(Float, default=0.0)
    scapula_r_tilt_deg = Column(Float, default=0.0)
    scapula_l_tilt_deg = Column(Float, default=0.0)
    scapula_r_pro_deg = Column(Float, default=0.0)
    scapula_l_pro_deg = Column(Float, default=0.0)
    emg_ut_r = Column(Float, default=0.0)
    emg_ut_l = Column(Float, default=0.0)
    emg_sa_r = Column(Float, default=0.0)
    emg_sa_l = Column(Float, default=0.0)
    sensors_payload_json = Column(Text, nullable=True) # Serialized 18-sensor array readings & status
    created_at = Column(DateTime, default=utc_now)

    session = relationship("ESP32RecordingSession", back_populates="records")
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


# ---------------- ESP32 WIRELESS HUB & IMU SENSORS DATA MODELS ----------------

class ESP32Device(Base):
    __tablename__ = "esp32_devices"

    id = Column(String(50), primary_key=True) # e.g. "ESP32-HUB-01"
    name = Column(String(100), default="SCAPTRACK Master Wireless Hub")
    mac_address = Column(String(50), default="24:6F:28:B4:7A:12")
    ip_address = Column(String(50), default="192.168.4.1")
    firmware_version = Column(String(30), default="v2.1.4-BLE5")
    battery_level = Column(Float, default=92.0)
    rssi_dbm = Column(Integer, default=-44)
    status = Column(String(30), default="Online") # "Online", "Streaming", "Disconnected"
    sampling_rate_hz = Column(Float, default=50.0)
    total_packets_received = Column(Integer, default=0)
    last_heartbeat = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)


class IMUSensorNode(Base):
    __tablename__ = "imu_sensor_nodes"

    sensor_id = Column(String(50), primary_key=True) # e.g. "IMU_R_SUP", "IMU_T2", etc.
    label = Column(String(100), nullable=False) # e.g. "Right Superior Angle"
    body_region = Column(String(50), nullable=False) # "Right Scapula", "Left Scapula", "Thorax", "Humerus", "sEMG"
    landmark_code = Column(String(20), default="SA1")
    is_online = Column(Boolean, default=True)
    calibration_status = Column(String(30), default="Calibrated") # "Calibrated", "Calibrating", "Uncalibrated"
    battery_percent = Column(Float, default=95.0)
    rssi_dbm = Column(Integer, default=-46)
    packet_rate_hz = Column(Float, default=50.0)
    temperature_c = Column(Float, default=32.0)
    roll = Column(Float, default=0.0)
    pitch = Column(Float, default=0.0)
    yaw = Column(Float, default=0.0)
    accel_x = Column(Float, default=0.0)
    accel_y = Column(Float, default=0.0)
    accel_z = Column(Float, default=1.0)
    gyro_x = Column(Float, default=0.0)
    gyro_y = Column(Float, default=0.0)
    gyro_z = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=utc_now)


class ESP32RecordingSession(Base):
    __tablename__ = "esp32_recording_sessions"

    session_id = Column(String(50), primary_key=True) # e.g. "SESS-2026-10-05-001"
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)
    movement_plane = Column(String(100), default="Sagittal Flexion")
    status = Column(String(30), default="Active") # "Active", "Completed", "Archived"
    total_packets = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    avg_sample_rate_hz = Column(Float, default=50.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    records = relationship("ESP32TelemetryRecord", back_populates="session", cascade="all, delete-orphan")


class ESP32TelemetryRecord(Base):
    __tablename__ = "esp32_telemetry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("esp32_recording_sessions.session_id"), nullable=False)
    patient_id = Column(String(50), nullable=False)
    seq_number = Column(Integer, default=0)
    timestamp_ms = Column(Integer, default=0)
    arm_elevation_deg = Column(Float, default=0.0)
    scapula_r_upward_deg = Column(Float, default=0.0)
    scapula_l_upward_deg = Column(Float, default=0.0)
    asymmetry_deg = Column(Float, default=0.0)
    scapula_r_tilt_deg = Column(Float, default=0.0)
    scapula_l_tilt_deg = Column(Float, default=0.0)
    scapula_r_pro_deg = Column(Float, default=0.0)
    scapula_l_pro_deg = Column(Float, default=0.0)
    emg_ut_r = Column(Float, default=0.0)
    emg_ut_l = Column(Float, default=0.0)
    emg_sa_r = Column(Float, default=0.0)
    emg_sa_l = Column(Float, default=0.0)
    sensors_payload_json = Column(Text, nullable=True) # Serialized 18-sensor array readings & status
    created_at = Column(DateTime, default=utc_now)

    session = relationship("ESP32RecordingSession", back_populates="records")
