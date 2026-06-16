import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "PiFinder_lite" / "analyze_mobile_imu_drift.py"
spec = importlib.util.spec_from_file_location("analyze_mobile_imu_drift", SCRIPT_PATH)
analyze_mobile_imu_drift = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["analyze_mobile_imu_drift"] = analyze_mobile_imu_drift
spec.loader.exec_module(analyze_mobile_imu_drift)


def cycle(index, predicted_alt, predicted_az, actual_alt, actual_az, remount_id="mount_a"):
    return {
        "cycle_id": f"cycle_{index}",
        "remount_id": remount_id,
        "duration_s": 60,
        "predicted_final": {"alt_deg": predicted_alt, "az_deg": predicted_az},
        "solve_final": {"alt_deg": actual_alt, "az_deg": actual_az},
    }


def test_clear_repeatable_residual_produces_pattern_found():
    payload = {
        "cycles": [
            cycle(1, 30.0, 120.0, 30.9, 119.5),
            cycle(2, 35.0, 125.0, 35.8, 124.6),
            cycle(3, 40.0, 130.0, 40.9, 129.4),
        ]
    }

    report = analyze_mobile_imu_drift.analyze_payload(payload)

    assert report["diagnostic_only"] is True
    assert report["integrator_updated"] is False
    assert report["runtime_pointing_updated"] is False
    assert report["verdict"] == "pattern_found"
    assert report["confidence"] == "MEDIUM"
    assert report["suggested_correction"]["alt_bias_deg"] > 0.7
    assert report["suggested_correction"]["az_bias_deg"] < -0.3
    assert report["recommendation"] == "candidate_for_future_correction_profile"


def test_few_cycles_need_more_data():
    report = analyze_mobile_imu_drift.analyze_payload({"cycles": [cycle(1, 30, 120, 31, 119)]})

    assert report["verdict"] == "needs_more_data"
    assert report["recommendation"] == "repeat_solve_to_solve_cycles"
    assert "too_few_cycles" in report["warnings"]


def test_remount_shift_is_marked_unstable():
    payload = {
        "cycles": [
            cycle(1, 30, 120, 31, 119, remount_id="mount_a"),
            cycle(2, 35, 125, 36, 124, remount_id="mount_a"),
            cycle(3, 30, 120, 36, 126, remount_id="mount_b"),
            cycle(4, 35, 125, 41, 131, remount_id="mount_b"),
        ]
    }

    report = analyze_mobile_imu_drift.analyze_payload(payload)

    assert report["verdict"] == "unstable_mount"
    assert report["recommendation"] == "recalibrate_or_remount_phone"
    assert "remount_shift" in report["warnings"]


def test_high_inconsistent_error_rejects_imu_reliability():
    payload = {
        "cycles": [
            cycle(1, 30, 120, 40, 100),
            cycle(2, 35, 125, 20, 145),
            cycle(3, 40, 130, 51, 151),
        ]
    }

    report = analyze_mobile_imu_drift.analyze_payload(payload)

    assert report["verdict"] == "imu_not_reliable"
    assert report["confidence"] == "LOW"
    assert report["recommendation"] == "keep_read_only_and_collect_better_cycles"


def test_error_metric_weights_azimuth_by_cos_altitude():
    # Near the zenith a 10-deg azimuth residual subtends a much smaller on-sky
    # angle: at alt=80 the true separation is ~10 * cos(80) = 1.7365 deg, not 10.
    payload = {"cycles": [cycle(1, 80.0, 100.0, 80.0, 110.0)]}

    report = analyze_mobile_imu_drift.analyze_payload(payload)
    cycle_result = report["cycles"][0]

    # Raw azimuth residual is preserved for traceability.
    assert cycle_result["residual_az_deg"] == 10.0
    # error_deg is the cos(altitude)-weighted on-sky separation.
    assert abs(cycle_result["error_deg"] - 1.7365) < 0.01
