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


def test_validate_gps_payload_rejects_invalid_timestamp_before_queue_update():
    gps_fix, error = mobile_bridge.validate_gps_payload(
        {
            "lat": 40.4168,
            "lon": -3.7038,
            "time_utc": "not-a-date",
            "source": "android",
        }
    )

    assert gps_fix == {}
    assert "time_utc" in error


def test_validate_solve_timeout_ms_rejects_invalid_values():
    timeout, error = mobile_bridge.validate_solve_timeout_ms(
        {"solve_timeout_ms": "bad"},
        default_ms=1000,
    )

    assert timeout is None
    assert "solve_timeout_ms" in error


def test_validate_solve_timeout_ms_accepts_supported_range():
    timeout, error = mobile_bridge.validate_solve_timeout_ms(
        {"solve_timeout_ms": 2500},
        default_ms=1000,
    )

    assert error is None
    assert timeout == 2500


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


def test_status_payload_advertises_optical_boresight_calibration():
    status = mobile_bridge.status_payload()

    assert status["mobile_bridge"]["optical_boresight"] == "implemented_read_only"


def test_status_payload_advertises_mobile_environment_bridge():
    status = mobile_bridge.status_payload()

    assert status["mobile_bridge"]["environment"] == "implemented_diagnostic_only"


def test_validate_environment_payload_preserves_optional_environment_fields():
    payload = {
        "schema": "pifinder-mobile-environment-v0",
        "device_time_utc": "2026-05-09T12:00:00Z",
        "app": {"version_name": "debug"},
        "device": {"manufacturer": "samsung", "model": "SM-S948B"},
        "sensors": {
            "ambient_light": {
                "available": True,
                "lux": 12.3,
                "sensor_name": "Light Sensor",
            },
            "pressure": {"available": False},
        },
        "battery": {"available": True, "percent": 76.0, "charging": True},
        "network": {"available": True, "type": "wifi", "validated": True},
        "device_state": {"screen_orientation": "portrait", "power_save_mode": False},
    }

    environment, error = mobile_bridge.validate_environment_payload(payload)

    assert error is None
    assert environment["sensors"]["ambient_light"]["available"] is True
    assert environment["sensors"]["ambient_light"]["lux"] == 12.3
    assert environment["sensors"]["pressure"]["available"] is False
    assert environment["battery"]["percent"] == 76.0
    assert environment["network"]["type"] == "wifi"


def test_validate_environment_payload_removes_precise_location_fields():
    payload = {
        "device_time_utc": "2026-05-09T12:00:00Z",
        "lat": 42.4,
        "lon": -7.1,
        "location": {"latitude": 42.4, "longitude": -7.1},
        "gps": {"lat": 42.4, "lon": -7.1},
        "sensors": {"ambient_light": {"available": False}},
    }

    environment, error = mobile_bridge.validate_environment_payload(payload)

    assert error is None
    raw = json.dumps(environment)
    assert "42.4" not in raw
    assert "-7.1" not in raw
    assert "location" not in raw
    assert "gps" not in raw


def test_environment_payload_adds_summary_and_received_time():
    environment, error = mobile_bridge.validate_environment_payload(
        {
            "sensors": {
                "ambient_light": {"available": True, "lux": 4.5},
                "pressure": {"available": True, "hpa": 932.1},
            },
            "battery": {"available": True, "percent": 55.0, "charging": False},
            "network": {"available": True, "type": "cellular", "validated": True},
        }
    )
    assert error is None

    payload = mobile_bridge.environment_payload(environment)

    assert payload["received_utc"].endswith("Z")
    assert payload["environment"]["diagnostic_only"] is True
    assert payload["summary"]["ambient_light_available"] is True
    assert payload["summary"]["ambient_light_lux"] == 4.5
    assert payload["summary"]["pressure_available"] is True
    assert payload["summary"]["pressure_hpa"] == 932.1
    assert payload["summary"]["battery_percent"] == 55.0
    assert payload["summary"]["network_type"] == "cellular"


def test_server_exposes_mobile_environment_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/environment", methods=["POST"])' in source
    assert "validate_environment_payload" in source
    assert "ENVIRONMENT_LATEST_FILENAME" in source


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


def test_optical_boresight_calibration_persists_read_only_offset(tmp_path, monkeypatch):
    def fake_diagnostic_camera_solve(**kwargs):
        return {
            "ok": True,
            "frame_id": kwargs["frame_id"],
            "diagnostic_only": True,
            "integrator_updated": False,
            "runtime_pointing_updated": False,
            "summary": {"status": "solved", "solve_ok": True},
            "solve": {
                "attempted": True,
                "solve_ok": True,
                "best": {
                    "solve_ok": True,
                    "solve_ra": 120.0,
                    "solve_dec": 22.5,
                },
            },
            "report": {"json_report": str(tmp_path / "report.json")},
        }

    monkeypatch.setattr(mobile_bridge, "diagnostic_camera_solve", fake_diagnostic_camera_solve)

    result = mobile_bridge.optical_boresight_calibration(
        {
            "frame_id": "20260516T000000Z_frame",
            "reference_target": "Vega centered in eyepiece",
            "reference_ra_deg": 121.0,
            "reference_dec_deg": 22.0,
            "device": {"model": "SM-S948B"},
        },
        profiles_dir=tmp_path / "optical_profiles",
    )

    assert result["ok"] is True
    assert result["calibration_ok"] is True
    assert result["diagnostic_only"] is True
    assert result["integrator_updated"] is False
    assert result["runtime_pointing_updated"] is False
    assert result["profile"]["status"] == "ok"
    assert result["profile"]["offset"]["available"] is True
    assert result["profile"]["offset"]["ra_deg"] == 1.0
    assert result["profile"]["offset"]["dec_deg"] == -0.5
    assert Path(result["stored_as"]).exists()

    status = mobile_bridge.optical_boresight_status(tmp_path / "optical_profiles")
    assert status["profile_available"] is True
    assert status["profile"]["integrator_blocked"] is True
    assert status["profile"]["runtime_pointing_blocked"] is True


def test_optical_boresight_calibration_needs_reference_coordinates(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mobile_bridge,
        "diagnostic_camera_solve",
        lambda **kwargs: {
            "ok": True,
            "summary": {"status": "solved"},
            "solve": {
                "attempted": True,
                "solve_ok": True,
                "best": {"solve_ra": 120.0, "solve_dec": 22.5},
            },
        },
    )

    result = mobile_bridge.optical_boresight_calibration(
        {"frame_id": "20260516T000000Z_frame"},
        profiles_dir=tmp_path / "optical_profiles",
    )

    assert result["ok"] is True
    assert result["calibration_ok"] is False
    assert result["profile"]["status"] == "needs_reference_coordinates"
    assert "reference_ra_dec_required" in result["profile"]["warnings"]


def test_optical_boresight_calibration_rejects_invalid_timeout_before_solving(
    tmp_path,
    monkeypatch,
):
    solve_called = False

    def fake_diagnostic_camera_solve(**kwargs):
        nonlocal solve_called
        solve_called = True
        return {"ok": True}

    monkeypatch.setattr(mobile_bridge, "diagnostic_camera_solve", fake_diagnostic_camera_solve)

    result = mobile_bridge.optical_boresight_calibration(
        {
            "frame_id": "20260516T000000Z_frame",
            "reference_ra_deg": 120.0,
            "reference_dec_deg": 22.5,
            "solve_timeout_ms": "bad",
        },
        profiles_dir=tmp_path / "optical_profiles",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_solve_timeout"
    assert solve_called is False


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


def test_diagnostic_camera_solve_includes_latest_environment_summary(tmp_path):
    frame_id = "20260508T000000Z_frame"
    frame_path = tmp_path / f"{frame_id}.jpg"
    Image.new("RGB", (64, 64), color=(0, 0, 0)).save(frame_path)
    (tmp_path / f"{frame_id}.json").write_text(
        json.dumps({"schema": "pifinder-mobile-camera-frame-v0"}),
        encoding="utf-8",
    )
    environment, error = mobile_bridge.validate_environment_payload(
        {
            "sensors": {"ambient_light": {"available": True, "lux": 0.8}},
            "battery": {"available": True, "percent": 91.0},
            "network": {"available": True, "type": "wifi"},
            "location": {"latitude": 42.4, "longitude": -7.1},
        }
    )
    assert error is None
    environment_path = tmp_path / "environment_latest.json"
    environment_path.write_text(
        json.dumps(mobile_bridge.environment_payload(environment)),
        encoding="utf-8",
    )

    result = mobile_bridge.diagnostic_camera_solve(
        frame_id,
        frames_dir=tmp_path,
        reports_dir=tmp_path / "reports",
        environment_path=environment_path,
    )

    assert result["ok"] is True
    assert result["environment"]["available"] is True
    assert result["environment"]["summary"]["ambient_light_lux"] == 0.8
    report_file = Path(result["report"]["json_report"])
    report_payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert report_payload["environment"]["summary"]["battery_percent"] == 91.0
    assert "42.4" not in json.dumps(report_payload)


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


def test_diagnostic_camera_solve_ai_preprocessing_reports_comparison(tmp_path, monkeypatch):
    frame_id = "20260508T000000Z_ai"
    frame_path = tmp_path / f"{frame_id}.jpg"
    Image.new("RGB", (128, 128), color=(4, 4, 4)).save(frame_path)
    (tmp_path / f"{frame_id}.json").write_text(
        json.dumps({"frame_id": frame_id}),
        encoding="utf-8",
    )

    def fake_select(frame_path, score):
        return {
            "strategy": "adaptive",
            "selected_modes": ["percentile_stretch", "hot_pixel_suppression"],
            "selection_reason": "dark_low_contrast_frame",
            "image_metrics": {
                "mean": 4.0,
                "noise_proxy": 2.0,
                "saturation_pct": 0.0,
                "bright_points": 20,
            },
            "image_analysis_ms": 7,
        }

    def fake_attempt(frame_path, score, solve_timeout_ms, preprocess_modes):
        rows = [
            {
                "preprocess_mode": preprocess_modes[-1],
                "solve_ok": "hot_pixel_suppression" in preprocess_modes,
                "solve_matches": 18 if "hot_pixel_suppression" in preprocess_modes else 0,
                "solve_time_ms": 120.0 if "hot_pixel_suppression" in preprocess_modes else 80.0,
            }
        ]
        solved = rows[0]["solve_ok"]
        return {
            "attempted": True,
            "solve_ok": solved,
            "rows": rows,
            "best": rows[0],
        }

    monkeypatch.setattr(mobile_bridge, "_select_ai_preprocessing_modes", fake_select)
    monkeypatch.setattr(mobile_bridge, "_attempt_diagnostic_solve", fake_attempt)

    result = mobile_bridge.diagnostic_camera_solve(
        frame_id,
        frames_dir=tmp_path,
        reports_dir=tmp_path / "reports",
        force_attempt=True,
        ai_image_preprocessing_enabled=True,
        preprocess_strategy="adaptive",
    )

    assert result["ok"] is True
    assert result["diagnostic_only"] is True
    assert result["integrator_updated"] is False
    assert result["runtime_pointing_updated"] is False
    assert result["solve"]["solve_ok"] is True
    ai = result["solve"]["ai_image_preprocessing"]
    assert ai["enabled"] is True
    assert ai["strategy"] == "adaptive"
    assert ai["selected_modes"] == ["percentile_stretch", "hot_pixel_suppression"]
    assert ai["selection_reason"] == "dark_low_contrast_frame"
    assert ai["baseline_result"]["solve_ok"] is False
    assert ai["adaptive_result"]["solve_ok"] is True
    assert ai["winning_variant"] == "hot_pixel_suppression"
    assert ai["matches"] == 18
    assert ai["verdict"] == "helped"
    assert "image_analysis_ms" in ai
    assert "preprocessing_ms" in ai
    assert "baseline_solve_ms" in ai
    assert "adaptive_solve_ms" in ai
    assert "total_ai_path_ms" in ai
    assert "extra_time_ms" in ai
    report_payload = json.loads(Path(result["report"]["json_report"]).read_text(encoding="utf-8"))
    assert report_payload["solve"]["ai_image_preprocessing"]["verdict"] == "helped"


def test_diagnostic_camera_solve_ai_preprocessing_disabled_keeps_classic_modes(tmp_path, monkeypatch):
    frame_id = "20260508T000000Z_classic"
    frame_path = tmp_path / f"{frame_id}.jpg"
    Image.new("RGB", (128, 128), color=(4, 4, 4)).save(frame_path)

    calls = []

    def fake_attempt(frame_path, score, solve_timeout_ms, preprocess_modes):
        calls.append(preprocess_modes)
        return {
            "attempted": True,
            "solve_ok": False,
            "rows": [],
            "best": None,
        }

    monkeypatch.setattr(mobile_bridge, "_attempt_diagnostic_solve", fake_attempt)

    result = mobile_bridge.diagnostic_camera_solve(
        frame_id,
        frames_dir=tmp_path,
        force_attempt=True,
        ai_image_preprocessing_enabled=False,
    )

    assert result["ok"] is True
    assert calls == [["baseline", "background_subtract"]]
    assert result["solve"]["ai_image_preprocessing"]["enabled"] is False
    assert result["solve"]["ai_image_preprocessing"]["strategy"] == "classic"
    assert result["solve"]["ai_image_preprocessing"]["verdict"] == "disabled"


def test_diagnostic_camera_solve_adds_solve_altaz_from_latest_mobile_gps(tmp_path, monkeypatch):
    frame_id = "20260514T000000Z_solved_altaz"
    frame_path = tmp_path / f"{frame_id}.jpg"
    Image.new("RGB", (128, 128), color=(4, 4, 4)).save(frame_path)
    gps_path = tmp_path / "gps_latest.json"
    gps_path.write_text(
        json.dumps(
            {
                "gps": {
                    "lat": 42.38,
                    "lon": -7.13,
                    "altitude_m": 600,
                    "time_utc": "2026-05-14T22:00:00Z",
                    "source": "android-gps",
                }
            }
        ),
        encoding="utf-8",
    )

    def fake_attempt(frame_path, score, solve_timeout_ms, preprocess_modes):
        return {
            "attempted": True,
            "solve_ok": True,
            "rows": [],
            "best": {
                "solve_ok": True,
                "solve_ra": 120.0,
                "solve_dec": 22.5,
                "solve_matches": 16,
            },
        }

    monkeypatch.setattr(mobile_bridge, "_attempt_diagnostic_solve", fake_attempt)
    monkeypatch.setattr(
        mobile_bridge,
        "_radec_to_altaz_for_gps",
        lambda ra, dec, gps: (37.25, 181.75),
    )

    result = mobile_bridge.diagnostic_camera_solve(
        frame_id,
        frames_dir=tmp_path,
        reports_dir=tmp_path / "reports",
        gps_path=gps_path,
        force_attempt=True,
    )

    assert result["ok"] is True
    assert result["solve"]["solve_ok"] is True
    assert result["solve_altaz"] == {
        "available": True,
        "alt_deg": 37.25,
        "az_deg": 181.75,
        "source": "mobile_gps_latest",
    }
    report_payload = json.loads(Path(result["report"]["json_report"]).read_text(encoding="utf-8"))
    assert report_payload["solve_altaz"]["available"] is True


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


def test_server_exposes_optical_boresight_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/optical_boresight")' in source
    assert '@app.route("/mobile/optical_boresight", methods=["POST"])' in source
    assert "mobile_bridge.optical_boresight_status(" in source
    assert "mobile_bridge.optical_boresight_calibration(" in source


def test_server_exposes_diagnostic_camera_solve_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/camera_solve", methods=["POST"])' in source
    assert "mobile_bridge.diagnostic_camera_solve(" in source
    assert '"ai_image_preprocessing_enabled"' in source
    assert '"preprocess_strategy", "classic"' in source


def test_server_mobile_mutating_and_report_endpoints_require_mobile_auth():
    source = SERVER.read_text(encoding="utf-8")

    for route in (
        '@app.route("/mobile/mount_profile")',
        '@app.route("/mobile/optical_boresight")',
        '@app.route("/mobile/profile", methods=["POST"])',
        '@app.route("/mobile/environment", methods=["POST"])',
        '@app.route("/mobile/gps", methods=["POST"])',
        '@app.route("/mobile/imu", methods=["POST"])',
        '@app.route("/mobile/imu_drift_analysis", methods=["POST"])',
        '@app.route("/mobile/camera_frame", methods=["POST"])',
        '@app.route("/mobile/camera_reports")',
        '@app.route("/mobile/camera_solve", methods=["POST"])',
        '@app.route("/mobile/optical_boresight", methods=["POST"])',
    ):
        route_index = source.index(route)
        decorator_lines = source[route_index:].splitlines()[:3]
        assert any("@mobile_auth_required" in line for line in decorator_lines)


def test_server_mobile_camera_solve_validates_timeout_before_solving():
    source = SERVER.read_text(encoding="utf-8")

    assert "mobile_bridge.validate_solve_timeout_ms(" in source
    assert "invalid_solve_timeout" in source


def test_server_exposes_camera_report_history_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/camera_reports")' in source
    assert "mobile_bridge.camera_report_history(" in source


def test_mobile_bridge_exposes_ai_imu_drift_analysis():
    payload = {
        "cycles": [
            {
                "cycle_id": "cycle_1",
                "duration_s": 60,
                "predicted_final": {"alt_deg": 30.0, "az_deg": 120.0},
                "solve_final": {"alt_deg": 30.8, "az_deg": 119.6},
            },
            {
                "cycle_id": "cycle_2",
                "duration_s": 60,
                "predicted_final": {"alt_deg": 35.0, "az_deg": 125.0},
                "solve_final": {"alt_deg": 35.9, "az_deg": 124.5},
            },
            {
                "cycle_id": "cycle_3",
                "duration_s": 60,
                "predicted_final": {"alt_deg": 40.0, "az_deg": 130.0},
                "solve_final": {"alt_deg": 40.8, "az_deg": 129.4},
            },
        ]
    }

    result = mobile_bridge.ai_imu_drift_analysis(payload)

    assert result["ok"] is True
    assert result["diagnostic_only"] is True
    assert result["integrator_updated"] is False
    assert result["runtime_pointing_updated"] is False
    assert result["verdict"] == "pattern_found"
    assert result["suggested_correction"]["status"] == "diagnostic_only"


def test_server_exposes_ai_imu_drift_analysis_endpoint():
    source = SERVER.read_text(encoding="utf-8")

    assert '@app.route("/mobile/imu_drift_analysis", methods=["POST"])' in source
    assert "mobile_bridge.ai_imu_drift_analysis(" in source
