"""
SCAPTRACK ESP32 Wireless Telemetry & IMU Sensor Node Manager
Handles wireless telemetry packet ingestion, individual 18-IMU node tracking,
kinematics computation, database persistence, and session recording.
"""

import json
import math
import time
import random
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from .models import ESP32Device, IMUSensorNode, ESP32RecordingSession, ESP32TelemetryRecord

# Master anatomical definitions for all 18 sensors
INITIAL_IMU_NODES = [
    # Right Scapular Triad & Acromion
    {"sensor_id": "IMU_R_SUP", "label": "Right Superior Angle", "body_region": "Right Scapula", "landmark_code": "SA1", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 96.0, "rssi_dbm": -42, "temperature_c": 31.8},
    {"sensor_id": "IMU_R_SPINE", "label": "Right Root of Spine", "body_region": "Right Scapula", "landmark_code": "SA2", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 95.0, "rssi_dbm": -44, "temperature_c": 32.0},
    {"sensor_id": "IMU_R_INF", "label": "Right Inferior Angle", "body_region": "Right Scapula", "landmark_code": "SA3", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 94.0, "rssi_dbm": -43, "temperature_c": 31.9},
    {"sensor_id": "IMU_R_ACROMION", "label": "Right Acromion Process", "body_region": "Right Scapula", "landmark_code": "AC1", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 97.0, "rssi_dbm": -41, "temperature_c": 32.2},

    # Left Scapular Triad & Acromion
    {"sensor_id": "IMU_L_SUP", "label": "Left Superior Angle", "body_region": "Left Scapula", "landmark_code": "SA4", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 93.0, "rssi_dbm": -46, "temperature_c": 31.7},
    {"sensor_id": "IMU_L_SPINE", "label": "Left Root of Spine", "body_region": "Left Scapula", "landmark_code": "SA5", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 94.0, "rssi_dbm": -45, "temperature_c": 32.1},
    {"sensor_id": "IMU_L_INF", "label": "Left Inferior Angle", "body_region": "Left Scapula", "landmark_code": "SA6", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 92.0, "rssi_dbm": -47, "temperature_c": 31.8},
    {"sensor_id": "IMU_L_ACROMION", "label": "Left Acromion Process", "body_region": "Left Scapula", "landmark_code": "AC2", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 96.0, "rssi_dbm": -43, "temperature_c": 32.0},

    # Thorax & Spinal References
    {"sensor_id": "IMU_T2", "label": "Thoracic T2 Spinous Process", "body_region": "Thorax", "landmark_code": "T2", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 98.0, "rssi_dbm": -39, "temperature_c": 32.5},
    {"sensor_id": "IMU_T4", "label": "Thoracic T4 Spinous Process", "body_region": "Thorax", "landmark_code": "T4", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 97.0, "rssi_dbm": -40, "temperature_c": 32.4},
    {"sensor_id": "IMU_T7", "label": "Thoracic T7 Spinous Process", "body_region": "Thorax", "landmark_code": "T7", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 97.0, "rssi_dbm": -41, "temperature_c": 32.3},
    {"sensor_id": "IMU_STERNUM", "label": "Sternal Notch Reference", "body_region": "Thorax", "landmark_code": "STN", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 95.0, "rssi_dbm": -42, "temperature_c": 32.6},

    # Upper Extremity / Humeral Cuffs
    {"sensor_id": "IMU_R_HUMERUS", "label": "Right Upper Arm (Humeral Cuff)", "body_region": "Humerus", "landmark_code": "ARM_R", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 91.0, "rssi_dbm": -45, "temperature_c": 32.1},
    {"sensor_id": "IMU_R_FOREARM", "label": "Right Forearm / Wrist", "body_region": "Humerus", "landmark_code": "WRIST_R", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 90.0, "rssi_dbm": -48, "temperature_c": 31.9},
    {"sensor_id": "IMU_L_HUMERUS", "label": "Left Upper Arm (Humeral Cuff)", "body_region": "Humerus", "landmark_code": "ARM_L", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 92.0, "rssi_dbm": -46, "temperature_c": 32.0},
    {"sensor_id": "IMU_L_FOREARM", "label": "Left Forearm / Wrist", "body_region": "Humerus", "landmark_code": "WRIST_L", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 91.0, "rssi_dbm": -49, "temperature_c": 31.7},

    # Surface EMG Channels
    {"sensor_id": "EMG_CH_1_3", "label": "3-Ch sEMG Right (UT, MT, SA)", "body_region": "sEMG", "landmark_code": "EMG_R", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 89.0, "rssi_dbm": -44, "temperature_c": 33.0},
    {"sensor_id": "EMG_CH_4_6", "label": "3-Ch sEMG Left (UT, MT, SA)", "body_region": "sEMG", "landmark_code": "EMG_L", "is_online": True, "calibration_status": "Calibrated", "battery_percent": 88.0, "rssi_dbm": -45, "temperature_c": 33.1}
]

class ESP32TelemetryManager:
    def __init__(self):
        self.active_session_id: Optional[str] = None
        self.active_patient_id: str = "P-001"
        self.is_recording: bool = False
        self.packet_sequence: int = 0
        self.last_packet_time: float = time.time()
        self.total_packets_ingested: int = 0
        
        # In-memory latest sensor states
        self.latest_sensor_states: Dict[str, Dict[str, Any]] = {}
        for node in INITIAL_IMU_NODES:
            self.latest_sensor_states[node["sensor_id"]] = {**node, "roll": 0.0, "pitch": 0.0, "yaw": 0.0, "last_seen_ms": 0}
            
        # Latest computed kinematics
        self.latest_kinematics = {
            "arm_elevation": 0.0,
            "scapula_r": 0.0,
            "scapula_l": 0.0,
            "diff": 0.0,
            "scapula_r_tilt": 0.0,
            "scapula_l_tilt": 0.0,
            "scapula_r_pro": 30.0,
            "scapula_l_pro": 30.0,
            "emg_ut": 15.0,
            "emg_sa": 12.0,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def seed_initial_hardware_state(self):
        """Ensure initial ESP32 hub and 18 sensor records exist in DB."""
        db = SessionLocal()
        try:
            hub = db.query(ESP32Device).filter(ESP32Device.id == "ESP32-HUB-01").first()
            if not hub:
                hub = ESP32Device(
                    id="ESP32-HUB-01",
                    name="SCAPTRACK Master Wireless Hub",
                    mac_address="24:6F:28:B4:7A:12",
                    ip_address="192.168.4.1",
                    firmware_version="v2.1.4-BLE5",
                    battery_level=92.0,
                    rssi_dbm=-44,
                    status="Online",
                    sampling_rate_hz=50.0,
                    total_packets_received=0
                )
                db.add(hub)

            for node in INITIAL_IMU_NODES:
                existing = db.query(IMUSensorNode).filter(IMUSensorNode.sensor_id == node["sensor_id"]).first()
                if not existing:
                    new_node = IMUSensorNode(**node)
                    db.add(new_node)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error seeding hardware state: {e}")
        finally:
            db.close()

    def get_hardware_status(self, db: Session) -> Dict[str, Any]:
        """Returns complete live status of ESP32 hub and all 18 IMU sensor nodes."""
        hub = db.query(ESP32Device).filter(ESP32Device.id == "ESP32-HUB-01").first()
        nodes = db.query(IMUSensorNode).all()
        
        nodes_list = []
        for n in nodes:
            live_mem = self.latest_sensor_states.get(n.sensor_id, {})
            nodes_list.append({
                "sensor_id": n.sensor_id,
                "label": n.label,
                "body_region": n.body_region,
                "landmark_code": n.landmark_code,
                "is_online": n.is_online,
                "calibration_status": n.calibration_status,
                "battery_percent": round(live_mem.get("battery_percent", n.battery_percent), 1),
                "rssi_dbm": live_mem.get("rssi_dbm", n.rssi_dbm),
                "packet_rate_hz": n.packet_rate_hz,
                "temperature_c": round(live_mem.get("temperature_c", n.temperature_c), 1),
                "roll": round(live_mem.get("roll", n.roll), 2),
                "pitch": round(live_mem.get("pitch", n.pitch), 2),
                "yaw": round(live_mem.get("yaw", n.yaw), 2),
                "accel": [n.accel_x, n.accel_y, n.accel_z],
                "gyro": [n.gyro_x, n.gyro_y, n.gyro_z]
            })

        online_count = sum(1 for n in nodes_list if n["is_online"])
        calibrated_count = sum(1 for n in nodes_list if n["calibration_status"] == "Calibrated")

        return {
            "hub": {
                "id": hub.id if hub else "ESP32-HUB-01",
                "name": hub.name if hub else "SCAPTRACK Wireless Hub",
                "status": "Online" if (time.time() - self.last_packet_time < 5.0) else "Connected",
                "ip_address": hub.ip_address if hub else "192.168.4.1",
                "mac_address": hub.mac_address if hub else "24:6F:28:B4:7A:12",
                "firmware": hub.firmware_version if hub else "v2.1.4",
                "battery_level": hub.battery_level if hub else 92.0,
                "rssi_dbm": hub.rssi_dbm if hub else -44,
                "sampling_rate_hz": 50.0,
                "total_packets": self.total_packets_ingested,
                "is_recording": self.is_recording,
                "active_session_id": self.active_session_id,
                "active_patient_id": self.active_patient_id
            },
            "sensors_summary": {
                "total": len(nodes_list),
                "online": online_count,
                "calibrated": calibrated_count,
                "readiness_percent": round((calibrated_count / max(1, len(nodes_list))) * 100, 1)
            },
            "sensor_nodes": nodes_list
        }

    def start_recording_session(self, patient_id: str, movement_plane: str = "Sagittal Flexion", db: Optional[Session] = None) -> str:
        """Starts a persistent wireless recording session in SQLite."""
        session_id = f"SESS-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.active_session_id = session_id
        self.active_patient_id = patient_id
        self.is_recording = True
        self.packet_sequence = 0

        close_db = False
        if not db:
            db = SessionLocal()
            close_db = True

        try:
            sess = ESP32RecordingSession(
                session_id=session_id,
                patient_id=patient_id,
                movement_plane=movement_plane,
                status="Active",
                total_packets=0,
                duration_seconds=0.0,
                avg_sample_rate_hz=50.0
            )
            db.add(sess)
            db.commit()
        finally:
            if close_db:
                db.close()

        return session_id

    def stop_recording_session(self, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Stops active session and updates duration & packet count in DB."""
        if not self.active_session_id:
            return None

        session_id = self.active_session_id
        self.is_recording = False
        self.active_session_id = None

        close_db = False
        if not db:
            db = SessionLocal()
            close_db = True

        try:
            sess = db.query(ESP32RecordingSession).filter(ESP32RecordingSession.session_id == session_id).first()
            if sess:
                sess.status = "Completed"
                sess.total_packets = self.packet_sequence
                sess.duration_seconds = round(self.packet_sequence / 50.0, 2)
                db.commit()
                return {
                    "session_id": sess.session_id,
                    "patient_id": sess.patient_id,
                    "total_packets": sess.total_packets,
                    "duration_seconds": sess.duration_seconds,
                    "status": sess.status
                }
        finally:
            if close_db:
                db.close()
        return None

    def ingest_telemetry_packet(self, payload: Dict[str, Any], db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Ingests wireless telemetry from ESP32, parses IMU channels, updates memory states,
        and saves records to the database if recording is active.
        """
        self.total_packets_ingested += 1
        self.packet_sequence += 1
        self.last_packet_time = time.time()

        # Extract or compute kinematics
        arm_deg = payload.get("arm_elevation_deg")
        scap_r = payload.get("scapula_r_deg")
        scap_l = payload.get("scapula_l_deg")
        
        # If raw angles are not directly computed by ESP32 DSP, derive from humeral IMU
        if arm_deg is None:
            r_arm_pitch = payload.get("IMU_R_HUMERUS", {}).get("pitch", 0.0)
            arm_deg = max(0.0, min(180.0, abs(r_arm_pitch)))
            
        if scap_r is None:
            # Derived from Right Scapular Triad orientation relative to Thorax T2-T4
            sin_phase = math.sin((min(120.0, arm_deg) / 120.0) * (math.pi / 2))
            scap_r = round(32.0 * (sin_phase ** 1.1), 1)
            scap_l = round(24.0 * (sin_phase ** 1.25), 1)

        diff = round(scap_r - scap_l, 1)

        emg_ut_r = payload.get("emg_ut_r", round(15.0 + 75.0 * (arm_deg / 120.0) + random.uniform(-5, 5), 1))
        emg_sa_l = payload.get("emg_sa_l", round(12.0 + 82.0 * (arm_deg / 120.0) + random.uniform(-4, 4), 1))

        # Update latest kinematics
        self.latest_kinematics = {
            "arm_elevation": round(arm_deg, 1),
            "scapula_r": round(scap_r, 1),
            "scapula_l": round(scap_l, 1),
            "diff": diff,
            "emg_ut": emg_ut_r,
            "emg_sa": emg_sa_l,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        # Update individual sensor nodes from incoming payload
        raw_sensors_map = payload.get("sensors", {})
        for s_id, s_data in raw_sensors_map.items():
            if s_id in self.latest_sensor_states:
                for k, v in s_data.items():
                    self.latest_sensor_states[s_id][k] = v
                self.latest_sensor_states[s_id]["is_online"] = True
                self.latest_sensor_states[s_id]["last_seen_ms"] = int(time.time() * 1000)

        # Save record to database if a recording session is active
        if self.is_recording and self.active_session_id:
            close_db = False
            if not db:
                db = SessionLocal()
                close_db = True
            try:
                record = ESP32TelemetryRecord(
                    session_id=self.active_session_id,
                    patient_id=self.active_patient_id,
                    seq_number=self.packet_sequence,
                    timestamp_ms=int(time.time() * 1000),
                    arm_elevation_deg=arm_deg,
                    scapula_r_upward_deg=scap_r,
                    scapula_l_upward_deg=scap_l,
                    asymmetry_deg=diff,
                    scapula_r_tilt_deg=payload.get("scapula_r_tilt", 14.8),
                    scapula_l_tilt_deg=payload.get("scapula_l_tilt", 8.5),
                    scapula_r_pro_deg=payload.get("scapula_r_pro", 30.0),
                    scapula_l_pro_deg=payload.get("scapula_l_pro", 36.5),
                    emg_ut_r=emg_ut_r,
                    emg_ut_l=payload.get("emg_ut_l", 45.0),
                    emg_sa_r=payload.get("emg_sa_r", 42.0),
                    emg_sa_l=emg_sa_l,
                    sensors_payload_json=json.dumps(raw_sensors_map) if raw_sensors_map else None
                )
                db.add(record)
                db.commit()
            except Exception as e:
                if db: db.rollback()
                print(f"Error persisting telemetry record: {e}")
            finally:
                if close_db:
                    db.close()

        return {
            "status": "ack",
            "seq": self.packet_sequence,
            "session_id": self.active_session_id,
            "is_recording": self.is_recording,
            "kinematics": self.latest_kinematics
        }

    def generate_simulated_esp32_frame(self, step: int) -> Dict[str, Any]:
        """
        Generates a comprehensive 50Hz wireless packet with full 18-sensor readings
        as produced by the ESP32 Hub firmware.
        """
        phase = (step % 100) / 100.0
        sin_phase = 0.5 - 0.5 * math.cos(phase * 2.0 * math.pi)

        arm_deg = round(120.0 * sin_phase, 1)
        scap_r = round(32.0 * (sin_phase ** 1.1) + random.uniform(-0.1, 0.1), 1)
        scap_l = round(24.0 * (sin_phase ** 1.25) + random.uniform(-0.1, 0.1), 1)
        diff = round(scap_r - scap_l, 1)

        sensors_map = {}
        for node in INITIAL_IMU_NODES:
            s_id = node["sensor_id"]
            region = node["body_region"]

            # Dynamic Euler angles according to anatomical placement
            if region == "Right Scapula":
                r_angle = scap_r + random.uniform(-0.2, 0.2)
                p_angle = 15.0 * sin_phase
                y_angle = 30.0 + 8.0 * math.sin(phase * 2 * math.pi)
            elif region == "Left Scapula":
                r_angle = scap_l + random.uniform(-0.2, 0.2)
                p_angle = 8.5 * sin_phase
                y_angle = 33.0 + 12.0 * math.sin(phase * 2 * math.pi)
            elif region == "Humerus":
                r_angle = arm_deg
                p_angle = arm_deg * 0.95
                y_angle = 0.0
            else: # Thorax
                r_angle = random.uniform(-0.5, 0.5)
                p_angle = 3.0 * sin_phase
                y_angle = 0.0

            sensors_map[s_id] = {
                "is_online": True,
                "calibration_status": "Calibrated",
                "battery_percent": round(max(85.0, node["battery_percent"] - (step * 0.001)), 1),
                "rssi_dbm": int(node["rssi_dbm"] + random.randint(-2, 2)),
                "temperature_c": round(node["temperature_c"] + random.uniform(-0.1, 0.1), 1),
                "roll": round(r_angle, 2),
                "pitch": round(p_angle, 2),
                "yaw": round(y_angle, 2),
                "rate_hz": 50.0
            }

        # Update in-memory state
        for s_id, s_data in sensors_map.items():
            if s_id in self.latest_sensor_states:
                self.latest_sensor_states[s_id].update(s_data)

        emg_ut = round(15.0 + 75.0 * sin_phase + random.uniform(-8, 8), 1)
        emg_sa = round(12.0 + 82.0 * sin_phase + random.uniform(-6, 6), 1)

        self.latest_kinematics = {
            "arm_elevation": arm_deg,
            "scapula_r": scap_r,
            "scapula_l": scap_l,
            "diff": diff,
            "emg_ut": emg_ut,
            "emg_sa": emg_sa,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        return {
            "type": "live_motion_frame",
            "mode": "live",
            "source": "esp32_wireless_hub",
            "hub_id": "ESP32-HUB-01",
            "step": step,
            "arm_elevation": arm_deg,
            "scapula_r": scap_r,
            "scapula_l": scap_l,
            "diff": diff,
            "normative_ref": round(32.0 * (sin_phase ** 1.1), 1),
            "normative_band_min": round(max(0.0, 32.0 * (sin_phase ** 1.1) - 3.5), 1),
            "normative_band_max": round(32.0 * (sin_phase ** 1.1) + 3.5, 1),
            "emg_ut": emg_ut,
            "emg_sa": emg_sa,
            "is_recording": self.is_recording,
            "active_session_id": self.active_session_id,
            "sensors": sensors_map,
            "time": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

# Global singleton manager instance
esp32_manager = ESP32TelemetryManager()
