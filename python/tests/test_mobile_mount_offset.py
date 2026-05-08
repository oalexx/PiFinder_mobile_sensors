import json
from pathlib import Path

from PiFinder_lite import compute_mobile_mount_offset as mount_offset


def rotation_sample(index: int, values: list[float]) -> dict:
    return {
        "sensor": "game_rotation_vector",
        "t_android_ns": index * 20_000_000,
        "values": values,
        "accuracy": 3,
    }


def test_compute_candidate_profile_from_stable_synthetic_reference(tmp_path: Path):
    imu_batch = {
        "schema": "pifinder-mobile-imu-batch-v0",
        "batch_label": "mounted_reference",
        "device_time_utc": "2026-05-08T00:00:00Z",
        "device": {"manufacturer": "example", "model": "test-phone"},
        "screen_orientation": "portrait",
        "samples": [rotation_sample(index, [0.0, 0.0, 0.0, 1.0]) for index in range(80)],
    }
    reference = {
        "type": "manual_target",
        "target_name": "Synthetic target",
        "q_tube_reference": [0.70710678, 0.0, 0.0, 0.70710678],
    }

    profile = mount_offset.compute_candidate_profile(imu_batch, reference)

    assert profile["schema"] == "pifinder-mobile-mount-profile-v0"
    assert profile["status"] == "candidate"
    assert profile["enabled"] is False
    assert profile["device"]["model"] == "test-phone"
    assert profile["reference"]["target_name"] == "Synthetic target"
    assert profile["offset"]["representation"] == "quaternion"
    assert profile["offset"]["q_phone_to_tube"] == [0.707107, 0.0, 0.0, 0.707107]
    assert profile["offset"]["yaw_deg"] == 90.0
    assert profile["validation"]["state"] == "repeatability_pending"
    assert "do_not_use_for_runtime_guidance" in profile["validation"]["warnings"]


def test_noisy_or_invalid_batch_returns_low_confidence_profile():
    imu_batch = {
        "batch_label": "diagnostic",
        "samples": [
            rotation_sample(0, [0.0, 0.0, 0.0, 1.0]),
            rotation_sample(1, [0.0, 0.0, 1.0, 0.0]),
        ],
    }
    reference = {"q_tube_reference": [1.0, 0.0, 0.0, 0.0]}

    profile = mount_offset.compute_candidate_profile(imu_batch, reference)

    assert profile["status"] == "uncalibrated"
    assert profile["validation"]["state"] == "failed"
    assert "batch_label_not_mounted_reference" in profile["validation"]["warnings"]
    assert "insufficient_samples" in profile["validation"]["warnings"]
    assert "sensor_jump_detected" in profile["validation"]["warnings"]


def test_cli_writes_candidate_profile(tmp_path: Path):
    imu_path = tmp_path / "imu.json"
    reference_path = tmp_path / "reference.json"
    output_path = tmp_path / "profile.json"
    imu_path.write_text(
        json.dumps(
            {
                "imu": {
                    "batch_label": "mounted_reference",
                    "samples": [
                        rotation_sample(index, [0.0, 0.0, 0.0, 1.0])
                        for index in range(80)
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    reference_path.write_text(
        json.dumps({"q_tube_reference": [1.0, 0.0, 0.0, 0.0]}),
        encoding="utf-8-sig",
    )

    exit_code = mount_offset.main(
        [
            "--imu-batch",
            str(imu_path),
            "--reference",
            str(reference_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == "candidate"
