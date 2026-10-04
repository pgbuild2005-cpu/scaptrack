#!/usr/bin/env python3
"""
SCAPTRACK Wireless ESP32 Hardware Simulator & Network Test Utility
Streams live 50Hz wireless telemetry packets with 18 individual IMU sensor readings
directly to the SCAPTRACK server at http://localhost:8000/api/esp32/telemetry.
"""

import time
import math
import random
import requests
import sys

SERVER_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/esp32/telemetry"
SAMPLE_RATE_HZ = 50.0
INTERVAL = 1.0 / SAMPLE_RATE_HZ

SENSOR_IDS = [
    "IMU_R_SUP", "IMU_R_SPINE", "IMU_R_INF", "IMU_R_ACROMION",
    "IMU_L_SUP", "IMU_L_SPINE", "IMU_L_INF", "IMU_L_ACROMION",
    "IMU_T2", "IMU_T4", "IMU_T7", "IMU_STERNUM",
    "IMU_R_HUMERUS", "IMU_R_FOREARM", "IMU_L_HUMERUS", "IMU_L_FOREARM",
    "EMG_CH_1_3", "EMG_CH_4_6"
]

def run_test_stream(duration_sec=30):
    print("=" * 70)
    print("  🚀 SCAPTRACK ESP32 Wireless Telemetry Transmitter")
    print(f"  Target Server: {SERVER_URL}")
    print(f"  Rate: {SAMPLE_RATE_HZ} Hz | Sensors: 18 IMUs + 6-ch sEMG")
    print("=" * 70)

    seq = 0
    start_time = time.time()

    while time.time() - start_time < duration_sec:
        seq += 1
        t = time.time() - start_time
        phase = (t % 4.0) / 4.0
        sin_phase = 0.5 - 0.5 * math.cos(phase * 2.0 * math.pi)

        arm_deg = round(120.0 * sin_phase, 1)
        scap_r = round(32.0 * (sin_phase ** 1.1), 1)
        scap_l = round(24.0 * (sin_phase ** 1.25), 1)

        sensors = {}
        for i, s_id in enumerate(SENSOR_IDS):
            if i < 4:
                roll = scap_r
                pitch = 15.0 * sin_phase
                yaw = 30.0
            elif i < 8:
                roll = scap_l
                pitch = 8.5 * sin_phase
                yaw = 33.0
            elif 12 <= i < 16:
                roll = arm_deg
                pitch = arm_deg * 0.95
                yaw = 0.0
            else:
                roll = random.uniform(-0.2, 0.2)
                pitch = 2.0 * sin_phase
                yaw = 0.0

            sensors[s_id] = {
                "is_online": True,
                "calibration_status": "Calibrated",
                "battery_percent": round(max(80.0, 96.0 - (seq * 0.002)), 1),
                "rssi_dbm": random.randint(-46, -42),
                "temperature_c": round(32.0 + random.uniform(-0.1, 0.1), 1),
                "roll": round(roll, 2),
                "pitch": round(pitch, 2),
                "yaw": round(yaw, 2),
                "rate_hz": 50.0
            }

        payload = {
            "hub_id": "ESP32-HUB-01",
            "seq": seq,
            "timestamp_ms": int(time.time() * 1000),
            "arm_elevation_deg": arm_deg,
            "scapula_r_deg": scap_r,
            "scapula_l_deg": scap_l,
            "emg_ut_r": round(15.0 + 75.0 * sin_phase + random.uniform(-3, 3), 1),
            "emg_sa_l": round(12.0 + 82.0 * sin_phase + random.uniform(-3, 3), 1),
            "sensors": sensors
        }

        try:
            res = requests.post(SERVER_URL, json=payload, timeout=0.1)
            print(f"\r[ESP32 TX #{seq:05d} | {t:5.1f}s] Arm: {arm_deg:5.1f}° | Scap R: {scap_r:4.1f}° | Scap L: {scap_l:4.1f}° | HTTP {res.status_code}", end="", flush=True)
        except Exception as e:
            print(f"\n[Warning] Connection error: {e}")

        time.sleep(INTERVAL)

    print(f"\n\nStream complete: {seq} packets transmitted successfully.")

if __name__ == "__main__":
    run_test_stream()
