import json
from pathlib import Path

from PiFinder_lite import validate_mobile_mount_repeatability as repeatability


def profile(path: Path, name: str, quat: list[float], warnings: list[str] | None = None) -> Path:
    payload = {
        "schema": "pifinder-mobile-mount-profile-v0",
        "profile_id": name,
        "status": "candidate",
        "offset": {
            "representation": "quaternion",
            "q_phone_to_tube": quat,
        },
        "validation": {
            "state": "repeatability_pending",
            "warnings": warnings or ["do_not_use_for_runtime_guidance"],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_repeatability_passes_for_tight_offsets(tmp_path: Path):
    paths = [
        profile(tmp_path / "a.json", "a", [1.0, 0.0, 0.0, 0.0]),
        profile(tmp_path / "b.json", "b", [0.999999, 0.0, 0.0, 0.001]),
        profile(tmp_path / "c.json", "c", [0.999998, 0.0, 0.0, -0.0015]),
    ]

    report = repeatability.validate_profiles(paths, pass_threshold_deg=1.0, reject_threshold_deg=5.0)

    assert report["recommendation"] == "proceed"
    assert report["repeat_count"] == 3
    assert report["max_repeat_error_deg"] < 1.0
    assert report["validation_state"] == "passed"


def test_repeatability_rejects_large_spread_and_source_warnings(tmp_path: Path):
    paths = [
        profile(tmp_path / "a.json", "a", [1.0, 0.0, 0.0, 0.0]),
        profile(tmp_path / "b.json", "b", [0.70710678, 0.0, 0.0, 0.70710678]),
        profile(
            tmp_path / "c.json",
            "c",
            [0.999999, 0.0, 0.0, 0.001],
            warnings=["sensor_jump_detected", "do_not_use_for_runtime_guidance"],
        ),
    ]

    report = repeatability.validate_profiles(paths, pass_threshold_deg=1.0, reject_threshold_deg=5.0)

    assert report["recommendation"] == "reject"
    assert report["validation_state"] == "failed"
    assert report["max_repeat_error_deg"] > 5.0
    assert "repeat_error_too_high" in report["warnings"]
    assert "source_profile_warning:sensor_jump_detected" in report["warnings"]


def test_cli_writes_json_and_markdown_report(tmp_path: Path):
    profile(tmp_path / "a.json", "a", [1.0, 0.0, 0.0, 0.0])
    profile(tmp_path / "b.json", "b", [0.999999, 0.0, 0.0, 0.001])
    output_dir = tmp_path / "report"

    exit_code = repeatability.main(
        [
            "--input",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
            "--pass-threshold-deg",
            "1.0",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "mobile_mount_repeatability.json").exists()
    assert (output_dir / "mobile_mount_repeatability.md").exists()
