import math
import random
import time
from typing import Dict, Any, List

def generate_trial_time_series(movement: str = "Flexion", duration_sec: float = 4.0, hz: int = 50) -> List[Dict[str, Any]]:
    """
    Generates a high-frequency biomechanical dataset simulating arm elevation and lowering.
    Includes right and left scapular upward rotation, tilt, protraction, and 6-channel sEMG.
    """
    total_samples = int(duration_sec * hz)
    dataset = []

    for i in range(total_samples):
        t = i / hz
        phase = t / duration_sec # 0.0 to 1.0
        
        # Arm elevation cycle: 0 -> 120 -> 0 degrees (bell/sinusoidal curve)
        sin_phase = math.sin(phase * math.pi)
        arm_elevation = 120.0 * sin_phase

        # Scapular upward rotation (Normal ~ 32 deg max on unaffected Right, ~ 24 deg on affected Left)
        # Non-linear scapulohumeral rhythm
        scap_r_upward = 32.0 * (sin_phase ** 1.1) + random.uniform(-0.2, 0.2)
        scap_l_upward = 24.0 * (sin_phase ** 1.25) + random.uniform(-0.2, 0.2)

        # Scapular posterior tilt (-5 deg resting to +15 deg elevated)
        scap_r_tilt = -5.0 + 20.0 * sin_phase + random.uniform(-0.1, 0.1)
        scap_l_tilt = -5.0 + 14.0 * sin_phase + random.uniform(-0.1, 0.1)

        # Scapular internal rotation / protraction
        scap_r_pro = 30.0 + 8.0 * math.sin(phase * 2 * math.pi) + random.uniform(-0.1, 0.1)
        scap_l_pro = 33.0 + 12.0 * math.sin(phase * 2 * math.pi) + random.uniform(-0.1, 0.1)

        # Surface EMG bursts (modulated by elevation velocity & amplitude + Gaussian noise)
        emg_ut_base = 15.0 + 75.0 * sin_phase
        emg_sa_base = 12.0 + 82.0 * (sin_phase ** 1.3)

        emg_ut_r = max(0.0, emg_ut_base + random.gauss(0, 8.0))
        emg_ut_l = max(0.0, (emg_ut_base * 0.75) + random.gauss(0, 6.0))
        emg_sa_r = max(0.0, (emg_sa_base * 0.65) + random.gauss(0, 6.0))
        emg_sa_l = max(0.0, (emg_sa_base * 0.95) + random.gauss(0, 9.0))
        emg_mt = max(0.0, 10.0 + 25.0 * sin_phase + random.gauss(0, 4.0))
        emg_lt = max(0.0, 8.0 + 30.0 * sin_phase + random.gauss(0, 4.0))

        dataset.append({
            "timestamp_s": round(t, 3),
            "arm_elevation_deg": round(arm_elevation, 2),
            "scapula_r_upward_deg": round(scap_r_upward, 2),
            "scapula_l_upward_deg": round(scap_l_upward, 2),
            "scapula_r_tilt_deg": round(scap_r_tilt, 2),
            "scapula_l_tilt_deg": round(scap_l_tilt, 2),
            "scapula_r_protraction_deg": round(scap_r_pro, 2),
            "scapula_l_protraction_deg": round(scap_l_pro, 2),
            "emg_ut_r_uV": round(emg_ut_r, 2),
            "emg_ut_l_uV": round(emg_ut_l, 2),
            "emg_sa_r_uV": round(emg_sa_r, 2),
            "emg_sa_l_uV": round(emg_sa_l, 2),
            "emg_mt_uV": round(emg_mt, 2),
            "emg_lt_uV": round(emg_lt, 2),
        })

    return dataset
