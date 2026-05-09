import json
from datetime import timezone
from pathlib import Path

from PIL import Image

from PiFinder import mobile_bridge

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "python/PiFinder/server.py"


def test_mobile_gps_queue_fix_maps_payload_to_pifinder_gps_fix():
    gps_fix = {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude_m": 667.5,
        "accuracy_m": 12.3,
        "time_utc": "2026-05-08T00:00:00Z",
        "source": "android",
        "provider": "fused",
    }

    queue_fix = mobile_bridge.mobile_gps_queue_fix(gps_fix)

    assert queue_fix == {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude": 667.5,
        "source": "MOBILE:android",
        "error_in_m": 12.3,
        "lock": True,
        "lock_type": 2,
        "provider": "fused",
        "time_utc": "2026-05-08T00:00:00Z",
    }


def test_mobile_gps_queue_fix_uses_conservative_defaults():
    gps_fix = {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude_m": None,
        "accuracy_m": None,
        "time_utc": "2026-05-08T00:00:00Z",
        "source": "android",
    }

    queue_fix = mobile_bridge.mobile_gps_queue_fix(gps_fix)

    assert queue_fix["altitude"] == 0
    assert queue_fix["error_in_m"] == mobile_bridge.DEFAULT_MOBILE_GPS_ERROR_M
    assert queue_fix["source"] == "MOBILE:android"
    assert queue_fix["lock"] is True


def test_mobile_gps_queue_time_parses_utc_timestamp():
    gps_fix = {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude_m": None,
        "accuracy_m": None,
        "time_utc": "2026-05-08T00:01:02Z",
        "source": "android",
    }

    gps_time = mobile_bridge.mobile_gps_queue_time(gps_fix)

    assert gps_time.year == 2026
    assert gps_time.month == 5
    assert gps_time.day == 8
    assert gps_time.hour == 0
    assert gps_time.minute == 1
    assert gps_time.second == 2
    assert gps_time.tzinfo == timezone.utc


def test_validate_imu_payload_preserves_calibration_label_and_metadata():
    payload = {
        "schema": "pifinder-mobile-imu-batch-v0",
        "batch_label": "mounted_reference",
        "capture_duration_ms": 2000,
        "device_time_utc": "2026-05-08T00:00:00Z",
        "screen_orientation": "portrait",
        "app_version": "debug",
        "device": {
            "manufacturer": "samsung",
            "model": "SM-S948B",
        },
        "samples": [
            {
                "sensor": "game_rotation_vector",
                "t_android_ns": 0,
                "values": [0.0, 0.0, 0.0, 1.0],
                "accuracy": 3,
                "time_utc": "2026-05-08T00:00:00Z",
            }
        ],
    }

    imu_batch, error = mobile_bridge.validate_imu_payload(payload)

    assert error is None
    assert imu_batch["batch_label"] == "mounted_reference"
    assert imu_batch["capture_duration_ms"] == 2000.0
    assert imu_batch["screen_orientation"] == "portrait"
    assert imu_batch["app_version"] == "debug"
    assert imu_batch["device"]["model"] == "SM-S948B"


def test_status_payload_advertises_read_only_mount_profile_loader():
    status = mobile_bridge.status_payload()

    assert status["mobile_bridge"]["mount_profile"] == "implemented_read_only"


def test_status_payload_advertises_diagnostic_camera_solve():
    status = mobile_bridge.status_payload()

    assert status["mobile_bridge"]["camera_solve"] == "implemented_diagnostic_only"


def test_status_payload_advertises_camera_report_history():
    status = mobile_bridge.status_payload()

    assert status["mobile_bridge"]["camera_reports"] == "implemented_read_only"


def test_validate_imu_payload_rejects_unknown_batch_label():
    payload = {
        "batch_label": "surprise_mode",
        "samples": [
            {
                "sensor": "game_rotation_vector",
                "t_android_ns": 0,
                "values": [0.0, 0.0, 0.0, 1.0],
            }
        ],
    }

    imu_batch, error = mobile_bridge.validate_imu_payload(payload)

    assert imu_batch == {}
    assert error == (
        "batch_label must be one of: diagnostic, mounted_reference, "
        "repeat_check, slew, stationary."
    )


def _mount_profile(profile_id="profile-ok", **overrides):
    profile = {
        "schema": "pifinder-mobile-mount-profile-v0",
        "profile_id": profile_id,
        "status": "usable",
        "enabled": False,
        "created_utc": "2026-05-08T00:00:00Z",
        "updated_utc": "2026-05-08T00:00:00Z",
        "device": {
            "manufacturer": "samsung",
            "model": "SM-S948B",
            "app_version": "debug",
        },
        "mount": {
            "name": "tube clamp",
        },
        "sensor": {
            "primary": "game_rotation_vector",
        },
        "reference": {
            "type": "manual_target",
            "target_name": "Vega",
        },
        "axis_mapping": {
            "confidence": "MEDIUM",
        },
        "offset": {
            "representation": "quaternion",
            "q_phone_to_tube": [1.0, 0.0, 0.0, 0.0],
        },
        "validation": {
            "state": "passed",
            "max_repeat_error_deg": 0.8,
            "warnings": [],
        },
        "runtime": {
            "allow_integrator_feed": False,
            "allow_guidance_overlay": False,
            "requires_manual_enable": True,
        },
    }
    profile.update(overrides)
    return profile


def test_mount_profile_status_reports_latest_profile_without_runtime_enable(tmp_path):
    profiles_dir = tmp_path / "mount_profiles"
    profiles_dir.mkdir()
    profile_path = profiles_dir / "profile-ok.json"
    profile_path.write_text(json.dumps(_mount_profile()), encoding="utf-8")

    status = mobile_bridge.mount_profile_status(profiles_dir)

    assert status["ok"] is True
    assert status["profile_available"] is True
    assert status["profile"]["profile_id"] == "profile-ok"
    assert status["profile"]["status"] == "usable"
    assert status["profile"]["device_model"] == "SM-S948B"
    assert status["profile"]["runtime"]["allow_integrator_feed"] is False
    assert status["profile"]["runtime"]["allow_guidance_overlay"] is False
    assert status["profile"]["safety"]["integrator_blocked"] is True
    assert status["profile"]["safety"]["runtime_usable"] is False
    assert status["warnings"] == []


def test_mount_profile_status_blocks_integrator_feed_flag(tmp_path):
    profiles_dir = tmp_path / "mount_profiles"
    profiles_dir.mkdir()
    profile = _mount_profile(
        runtime={
            "allow_integrator_feed": True,
            "allow_guidance_overlay": True,
            "requires_manual_enable": False,
        }
    )
    (profiles_dir / "unsafe.json").write_text(json.dumps(profile), encoding="utf-8")

    status = mobile_bridge.mount_profile_status(profiles_dir)

    assert status["ok"] is True
    assert status["profile_available"] is True
    assert status["profile"]["safety"]["integrator_blocked"] is True
    assert status["profile"]["safety"]["runtime_usable"] is False
    assert "integrator_feed_requested_but_blocked" in status["warnings"]
    assert "manual_enable_required_missing" in status["warnings"]


def test_mount_profile_status_handles_missing_profiles(tmp_path):
    status = mobile_bridge.mount_profile_status(tmp_path / "missing")

    assert status["ok"] is True
    assert status["profile_available"] is False
    assert status["profile"] is None
    assert status["warnings"] == ["no_mount_profiles_found"]


def test_diagnostic_camera_solve_rejects_unsafe_frame_id(tmp_path):
    result = mobile_bridge.diagnostic_camera_solve(
        "../escape",
        frames_dir=tmp_path,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_frame_id"


def test_diagnostic_camera_solve_reports_missing_frame(tmp_path):
    result = mobile_bridge.diagnostic_camera_solve(
        "20260508T000000Z_missing",
        frames_dir=tmp_path,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "frame_not_found"


def test_diagnostic_camera_solve_skips_low_quality_frame_without_runtime_effect(tmp_path):
    frame_id = "20260508T000000Z_low"
    frame_path = tmp_path / f"{frame_id}.jpg"
    Image.new("RGB", (128, 128), color=(200, 200, 200)).save(frame_path)
    (tmp_path / f"{frame_id}.json").write_text(
        json.dumps({"frame_id": frame_id, "metadata": {"test": True}}),
        encoding="utf-8",
    )

    result = mobile_bridge.diagnostic_camera_solve(
        frame_id,
        frames_dir=tmp_path,
    )

    assert result["ok"] is True
    assert result["frame_id"] == frame_id
    assert result["diagnostic_only"] is True
    assert result["integrator_updated"] is False
    assert result["runtime_pointing_updated"] is False
    assert result["score"]["grade"] == "LOW"
    assert result["solve"]["attempted"] is False
    assert result["solve"]["skipped_reason"] == "quality_score_rejected"
    assert result["summary"]["status"] == "rejected"
    assert result["summary"]["label"] == "Rejected by quality score"
    assert result["recommendation"] == "capture_better_frame"
    assert "Run Full Diagnostic" in result["next_action"]
    assert result["advice"]["code"] == "background_too_bright"
    assert "lower ISO" in result["advice"]["next_action"]


def test_camera_exposure_advice_flags_noisy_rejected_frame():
    advice = mobile_bridge.camera_exposure_advice(
        score={
            "grade": "LOW",
            "mean": 5.8,
            "dark_pct": 55.0,
            "noise_proxy": 13.2,
            "bright_points": 950,
            "centroids": 80,
            "rejection_reasons": [
                "noise_proxy_high",
                "too_many_bright_points_possible_noise",
            ],
        },
        solve={
            "attempted": False,
            "solve_ok": False,
            "skipped_reason": "quality_score_rejected",
        },
    )

    assert advice["code"] == "noise_too_high"
    assert advice["severity"] == "warning"
    assert "ISO3200" in advice["message"]
    assert "ISO400/ISO800" in advice["next_action"]


def test_camera_exposure_advice_for_solved_frame_collects_more_evidence():
    advice = mobile_bridge.camera_exposure_advice(
        score={
            "grade": "HIGH",
            "quality_score": 121.5,
            "rejection_reasons": [],
        },
        solve={
            "attempted": True,
            "solve_ok": True,
        },
    )

    assert advice["code"] == "solved_collect_more"
    assert advice["severity"] == "success"
    assert "not final support" in advice["message"]
    assert "clear-sky frames" in advice["next_action"]


def test_diagnostic_camera_solve_persists_sanitized_report(tmp_path):
    frames_dir = tmp_path / "frames"
    reports_dir = tmp_path / "reports"
    frames_dir.mkdir()
    frame_id = "20260508T000000Z_report"
    frame_path = frames_dir / f"{frame_id}.jpg"
    Image.new("RGB", (128, 128), color=(200, 200, 200)).save(frame_path)
    (frames_dir / f"{frame_id}.json").write_text(
        json.dumps(
            {
                "frame_id": frame_id,
                "frame_file": "C:/private/local/path/frame.jpg",
                "metadata": {
                    "device": {"model": "SM-S948B"},
                    "location": {"lat": 42.40404584, "lon": -7.1594411},
                },
            }
        ),
        encoding="utf-8",
    )

    result = mobile_bridge.diagnostic_camera_solve(
        frame_id,
        frames_dir=frames_dir,
        reports_dir=reports_dir,
    )

    assert result["report"]["stored"] is True
    report_path = Path(result["report"]["json_report"])
    assert report_path.exists()
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_payload["frame_id"] == frame_id
    assert report_payload["diagnostic_only"] is True
    assert report_payload["integrator_updated"] is False
    assert report_payload["summary"]["status"] == "rejected"
    assert report_payload["recommendation"] == "capture_better_frame"
    assert report_payload["advice"]["code"] == "background_too_bright"
    assert "Run Full Diagnostic" in report_payload["next_action"]
    assert "C:/private" not in report_path.read_text(encoding="utf-8")
    assert "42.40404584" not in report_path.read_text(encoding="utf-8")


def test_camera_report_history_returns_empty_session_summary(tmp_path):
    result = mobile_bridge.camera_report_history(reports_dir=tmp_path)

    assert result["ok"] is True
    assert result["reports"] == []
    assert result["session_summary"]["total_reports"] == 0
    assert result["session_summary"]["returned_reports"] == 0
    assert result["session_summary"]["recommendation"] == "run_full_diagnostic"
    assert result["session_summary"]["next_action"].startswith("Run Full Diagnostic")


def test_camera_report_history_lists_sanitized_reports_and_session_summary(tmp_path):
    private_path = "C:/Users/aleja/private/frame.jpg"
    old_report = {
        "frame_id": "frame_rejected",
        "diagnostic_only": True,
        "metadata": {
            "device": {"model": "SM-S948B"},
            "location": {"lat": 42.40404584, "lon": -7.1594411},
        },
        "score": {
            "path": private_path,
            "grade": "LOW",
            "quality_score": 0.12,
        },
        "solve": {
            "attempted": False,
            "solve_ok": False,
            "skipped_reason": "quality_score_rejected",
        },
        "summary": {
            "status": "rejected",
            "label": "Rejected by quality score",
            "grade": "LOW",
            "quality_score": 0.12,
            "attempted": False,
            "solve_ok": False,
            "skipped_reason": "quality_score_rejected",
        },
        "recommendation": "capture_better_frame",
        "next_action": "Run Full Diagnostic again.",
        "advice": {
            "code": "background_too_bright",
            "label": "Background too bright",
            "message": "The sky/background is too bright for reliable solving.",
            "next_action": "Try lower ISO/exposure.",
            "severity": "warning",
        },
        "elapsed_ms": 14,
    }
    new_report = {
        "frame_id": "frame_solved",
        "diagnostic_only": True,
        "metadata": {
            "metadata": {
                "gps": {"lat": 42.40404584, "lon": -7.1594411},
            },
        },
        "score": {
            "path": "/home/pi/PiFinder_data/mobile/frames/frame_solved.jpg",
            "grade": "HIGH",
            "quality_score": 0.91,
        },
        "solve": {
            "attempted": True,
            "solve_ok": True,
            "best": {"path": "/home/pi/private/preprocessed.jpg"},
        },
        "summary": {
            "status": "solved",
            "label": "Diagnostic solve succeeded",
            "grade": "HIGH",
            "quality_score": 0.91,
            "attempted": True,
            "solve_ok": True,
            "skipped_reason": "",
        },
        "recommendation": "keep_collecting_clear_sky_evidence",
        "next_action": "Save this report as evidence.",
        "advice": {
            "code": "solved_collect_more",
            "label": "Solved",
            "message": "Solved. Keep collecting evidence; this is not final support.",
            "next_action": "Repeat with more clear-sky frames.",
            "severity": "success",
        },
        "elapsed_ms": 101,
    }
    (tmp_path / "20260508T000000Z_frame_rejected.json").write_text(
        json.dumps(old_report),
        encoding="utf-8",
    )
    (tmp_path / "20260508T000001Z_frame_solved.json").write_text(
        json.dumps(new_report),
        encoding="utf-8",
    )

    result = mobile_bridge.camera_report_history(reports_dir=tmp_path, limit=10)

    assert result["ok"] is True
    assert result["malformed_reports"] == 0
    assert result["session_summary"]["total_reports"] == 2
    assert result["session_summary"]["returned_reports"] == 2
    assert result["session_summary"]["status_counts"]["solved"] == 1
    assert result["session_summary"]["status_counts"]["rejected"] == 1
    assert result["session_summary"]["best_frame_id"] == "frame_solved"
    assert result["session_summary"]["best_quality_score"] == 0.91
    assert result["session_summary"]["recommendation"] == "collect_clear_sky_evidence"
    assert result["session_summary"]["advice_counts"]["solved_collect_more"] == 1
    assert result["session_summary"]["dominant_advice"]["code"] == "solved_collect_more"
    assert result["reports"][0]["frame_id"] == "frame_solved"
    assert result["reports"][0]["advice"]["code"] == "solved_collect_more"
    assert result["reports"][0]["report_file"] == "20260508T000001Z_frame_solved.json"
    assert result["reports"][0]["score"]["path"] == "frame_solved.jpg"
    assert result["reports"][0]["solve"]["best"]["path"] == "preprocessed.jpg"
    serialized = json.dumps(result)
    assert private_path not in serialized
    assert "42.40404584" not in serialized
    assert "/home/pi/PiFinder_data" not in serialized


def test_camera_report_history_skips_malformed_json(tmp_path):
    (tmp_path / "broken.json").write_text("{not-json", encoding="utf-8")

    result = mobile_bridge.camera_report_history(reports_dir=tmp_path)

    assert result["ok"] is True
    assert result["reports"] == []
    assert result["malformed_reports"] == 1
    assert "malformed_report:broken.json" in result["warnings"]


def test_server_exposes_read_only_mount_profile_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/mount_profile")' in source
    assert "mobile_bridge.mount_profile_status(" in source


def test_server_exposes_diagnostic_camera_solve_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/camera_solve", method="POST")' in source
    assert "mobile_bridge.diagnostic_camera_solve(" in source


def test_server_exposes_camera_report_history_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/camera_reports")' in source
    assert "mobile_bridge.camera_report_history(" in source
