import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "PiFinder_lite" / "analyze_mobile_imu.py"
spec = importlib.util.spec_from_file_location("analyze_mobile_imu", SCRIPT_PATH)
analyze_mobile_imu = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["analyze_mobile_imu"] = analyze_mobile_imu
spec.loader.exec_module(analyze_mobile_imu)


def rotation_sample(index, values, sensor="game_rotation_vector", accuracy=3):
    return {
        "sensor": sensor,
        "t_android_ns": index * 100_000_000,
        "values": values,
        "accuracy": accuracy,
        "time_utc": "2026-05-08T00:00:00Z",
    }


def test_stable_game_rotation_vector_is_candidate_for_calibration():
    samples = [
        rotation_sample(index, [0.0, 0.0, 0.001 * index, 0.999999])
        for index in range(12)
    ]

    analysis = analyze_mobile_imu.analyze_sensor("game_rotation_vector", samples)

    assert analysis.confidence == "HIGH"
    assert analysis.recommendation == "candidate_for_mount_calibration_tests"
    assert analysis.warnings == []


def test_large_orientation_jump_is_rejected_for_integrator():
    samples = [
        rotation_sample(0, [0.0, 0.0, 0.0, 1.0]),
        rotation_sample(1, [0.0, 0.0, 0.01, 0.99995]),
        rotation_sample(2, [0.0, 0.0, 0.8, 0.6]),
        rotation_sample(3, [0.0, 0.0, 0.81, 0.58643]),
        rotation_sample(4, [0.0, 0.0, 0.82, 0.57236]),
        rotation_sample(5, [0.0, 0.0, 0.83, 0.55776]),
        rotation_sample(6, [0.0, 0.0, 0.84, 0.54259]),
        rotation_sample(7, [0.0, 0.0, 0.85, 0.52678]),
    ]

    analysis = analyze_mobile_imu.analyze_sensor("game_rotation_vector", samples)

    assert analysis.confidence == "LOW"
    assert analysis.recommendation == "do_not_use_for_integrator_yet"
    assert "orientation_jump" in analysis.warnings


def test_analyze_batch_reports_calibration_batch_label():
    batch = {
        "batch_label": "mounted_reference",
        "samples": [
            rotation_sample(index, [0.0, 0.0, 0.001 * index, 0.999999])
            for index in range(12)
        ],
    }

    analyses = analyze_mobile_imu.analyze_batch(batch)

    assert len(analyses) == 1
    assert analyses[0].batch_label == "mounted_reference"
