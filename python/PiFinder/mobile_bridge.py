#!/usr/bin/python
# -*- coding:utf-8 -*-
"""Helpers for the optional PiFinder Mobile Bridge API."""

import hmac
import json
import math
import os
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PiFinder import utils

API_VERSION = "mobile-bridge-v0"
MOBILE_DATA_DIR = utils.data_dir / "mobile"
MOBILE_API_TOKEN_FILENAME = "mobile_api_token.txt"
PROFILE_LATEST_FILENAME = "profile_latest.json"
GPS_LATEST_FILENAME = "gps_latest.json"
IMU_LATEST_FILENAME = "imu_latest.json"
ENVIRONMENT_LATEST_FILENAME = "environment_latest.json"
MOUNT_PROFILES_DIRNAME = "mount_profiles"
OPTICAL_BORESIGHT_PROFILES_DIRNAME = "optical_boresight_profiles"
OPTICAL_BORESIGHT_LATEST_FILENAME = "optical_boresight_latest.json"
MAX_IMU_SAMPLES = 512
IMU_BATCH_LABELS = {
    "diagnostic",
    "mounted_reference",
    "repeat_check",
    "slew",
    "stationary",
}
FRAMES_DIRNAME = "frames"
CAMERA_SOLVE_REPORTS_DIRNAME = "camera_solve_reports"
MAX_CAMERA_FRAME_BYTES = 25 * 1024 * 1024
DEFAULT_MOBILE_GPS_ERROR_M = 9999
MIN_SOLVE_TIMEOUT_MS = 100
MAX_SOLVE_TIMEOUT_MS = 5000
MOUNT_PROFILE_SCHEMA = "pifinder-mobile-mount-profile-v0"
OPTICAL_BORESIGHT_SCHEMA = "pifinder-mobile-optical-boresight-profile-v0"
CAMERA_SOLVE_FRAME_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,96}$")
PRIVATE_LOCATION_KEYS = {
    "gps",
    "location",
    "coordinates",
    "lat",
    "lon",
    "latitude",
    "longitude",
}
MOUNT_PROFILE_STATUSES = {"uncalibrated", "candidate", "usable", "invalidated"}
MOUNT_PROFILE_VALIDATION_STATES = {
    "not_validated",
    "repeatability_pending",
    "passed",
    "failed",
}


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def ensure_mobile_data_dir() -> Path:
    utils.create_path(MOBILE_DATA_DIR)
    return MOBILE_DATA_DIR


def ensure_mobile_frames_dir() -> Path:
    frames_dir = ensure_mobile_data_dir() / FRAMES_DIRNAME
    utils.create_path(frames_dir)
    return frames_dir


def ensure_mobile_mount_profiles_dir() -> Path:
    profiles_dir = ensure_mobile_data_dir() / MOUNT_PROFILES_DIRNAME
    utils.create_path(profiles_dir)
    return profiles_dir


def ensure_mobile_optical_boresight_profiles_dir() -> Path:
    profiles_dir = ensure_mobile_data_dir() / OPTICAL_BORESIGHT_PROFILES_DIRNAME
    utils.create_path(profiles_dir)
    return profiles_dir


def ensure_mobile_camera_solve_reports_dir() -> Path:
    reports_dir = ensure_mobile_data_dir() / CAMERA_SOLVE_REPORTS_DIRNAME
    utils.create_path(reports_dir)
    return reports_dir


def write_debug_json(filename: str, payload: Dict[str, Any]) -> Path:
    """Persist the latest mobile bridge payload for debugging.

    Writes through a temporary file and then replaces the target path so readers
    do not observe partially written JSON.
    """
    data_dir = ensure_mobile_data_dir()
    target = data_dir / filename
    temp = target.with_suffix(target.suffix + ".tmp")
    with open(temp, "w") as output:
        json.dump(payload, output, indent=2, sort_keys=True)
        output.write("\n")
    os.replace(temp, target)
    return target


def profile_payload(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "received_utc": utc_now_iso(),
        "profile": profile,
    }


def validate_environment_payload(
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Normalize mobile environment metadata without accepting GPS coordinates."""
    if not isinstance(payload, dict):
        return {}, "environment payload must be a JSON object."

    sanitized = _strip_private_location_fields(payload)
    sensors = _object_or_empty(sanitized.get("sensors"))
    normalized = {
        "schema": str(sanitized.get("schema") or "pifinder-mobile-environment-v0"),
        "device_time_utc": sanitized.get("device_time_utc"),
        "app": _object_or_empty(sanitized.get("app")),
        "device": _object_or_empty(sanitized.get("device")),
        "sensors": {
            "ambient_light": _environment_sensor_payload(
                sensors.get("ambient_light"),
                value_field="lux",
            ),
            "pressure": _environment_sensor_payload(
                sensors.get("pressure"),
                value_field="hpa",
            ),
        },
        "battery": _object_or_empty(sanitized.get("battery")),
        "network": _object_or_empty(sanitized.get("network")),
        "device_state": _object_or_empty(sanitized.get("device_state")),
        "diagnostic_only": True,
        "integrator_updated": False,
        "runtime_pointing_updated": False,
    }
    normalized["battery"].setdefault("available", bool(normalized["battery"]))
    normalized["network"].setdefault("available", bool(normalized["network"]))
    return normalized, None


def environment_payload(environment: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap normalized environment metadata for storage/debug reports."""
    return {
        "received_utc": utc_now_iso(),
        "environment": environment,
        "summary": environment_summary(environment),
    }


def environment_summary(environment: Dict[str, Any]) -> Dict[str, Any]:
    environment = environment if isinstance(environment, dict) else {}
    sensors = _object_or_empty(environment.get("sensors"))
    light = _object_or_empty(sensors.get("ambient_light"))
    pressure = _object_or_empty(sensors.get("pressure"))
    battery = _object_or_empty(environment.get("battery"))
    network = _object_or_empty(environment.get("network"))
    device_state = _object_or_empty(environment.get("device_state"))
    return {
        "ambient_light_available": bool(light.get("available", False)),
        "ambient_light_lux": _optional_float(light.get("lux")),
        "pressure_available": bool(pressure.get("available", False)),
        "pressure_hpa": _optional_float(
            pressure.get("hpa", pressure.get("pressure_hpa"))
        ),
        "battery_available": bool(battery.get("available", False)),
        "battery_percent": _optional_float(battery.get("percent")),
        "battery_charging": _optional_bool(battery.get("charging")),
        "network_available": bool(network.get("available", False)),
        "network_type": str(network.get("type") or "unknown"),
        "network_validated": _optional_bool(network.get("validated")),
        "screen_orientation": str(device_state.get("screen_orientation") or "unknown"),
        "power_save_mode": _optional_bool(device_state.get("power_save_mode")),
    }


def error_payload(code: str, message: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "api": API_VERSION,
        "error": {
            "code": code,
            "message": message,
        },
    }


def configured_mobile_api_token(data_dir: Optional[Path] = None) -> Optional[str]:
    """Return the configured mobile API token, if one exists.

    Set ``PIFINDER_MOBILE_TOKEN`` for temporary runs, or create
    ``~/PiFinder_data/mobile/mobile_api_token.txt`` for field use.
    """
    env_token = os.environ.get("PIFINDER_MOBILE_TOKEN")
    if isinstance(env_token, str) and env_token.strip():
        return env_token.strip()

    token_path = (data_dir or MOBILE_DATA_DIR) / MOBILE_API_TOKEN_FILENAME
    try:
        token = token_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


def mobile_api_token_matches(
    provided_token: Optional[str],
    configured_token: Optional[str] = None,
) -> bool:
    expected = configured_token or configured_mobile_api_token()
    if not expected or not provided_token:
        return False
    return hmac.compare_digest(str(provided_token).strip(), expected)


def validate_camera_frame_metadata(metadata_text: str) -> Tuple[Dict[str, Any], Optional[str]]:
    if not isinstance(metadata_text, str) or not metadata_text.strip():
        return {}, "Missing required multipart field: metadata."
    try:
        metadata = json.loads(metadata_text)
    except json.JSONDecodeError as exc:
        return {}, f"metadata must be valid JSON: {exc.msg}."
    if not isinstance(metadata, dict):
        return {}, "metadata must be a JSON object."
    return metadata, None


def validate_camera_frame_bytes(frame_bytes: bytes) -> Optional[str]:
    if not frame_bytes:
        return "Missing or empty multipart file field: frame."
    if len(frame_bytes) > MAX_CAMERA_FRAME_BYTES:
        return f"frame must be {MAX_CAMERA_FRAME_BYTES} bytes or smaller."
    if not frame_bytes.startswith(b"\xff\xd8"):
        return "frame must be a JPEG image."
    return None


def _strip_private_location_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _strip_private_location_fields(item)
            for key, item in value.items()
            if str(key).lower() not in PRIVATE_LOCATION_KEYS
        }
    if isinstance(value, list):
        return [_strip_private_location_fields(item) for item in value]
    return value


def _object_or_empty(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _optional_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _optional_bool(value: Any) -> Optional[bool]:
    return value if isinstance(value, bool) else None


def _parse_utc_timestamp(value: str) -> Tuple[Optional[datetime], Optional[str]]:
    time_utc = str(value).strip()
    if not time_utc:
        return None, "time_utc must be a non-empty string."
    if time_utc.endswith("Z"):
        time_utc = time_utc[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(time_utc)
    except ValueError:
        return None, "time_utc must be an ISO-8601 timestamp."
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc), None


def _environment_sensor_payload(value: Any, value_field: str) -> Dict[str, Any]:
    source = _object_or_empty(value)
    payload = dict(source)
    payload["available"] = bool(source.get("available", False))
    if value_field in source:
        numeric_value = _optional_float(source.get(value_field))
        if numeric_value is not None:
            payload[value_field] = numeric_value
    return payload


def store_camera_frame(
    frame_bytes: bytes,
    metadata: Dict[str, Any],
    original_filename: str,
    content_type: str,
) -> Dict[str, Any]:
    received_utc = utc_now_iso()
    frame_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{os.urandom(4).hex()}"
    frames_dir = ensure_mobile_frames_dir()
    frame_filename = f"{frame_id}.jpg"
    metadata_filename = f"{frame_id}.json"
    frame_path = frames_dir / frame_filename
    metadata_path = frames_dir / metadata_filename

    temp_frame_path = frame_path.with_suffix(".jpg.tmp")
    with open(temp_frame_path, "wb") as output:
        output.write(frame_bytes)
    os.replace(temp_frame_path, frame_path)

    stored_metadata = {
        "received_utc": received_utc,
        "frame_id": frame_id,
        "storage_only": True,
        "solver_invoked": False,
        "original_filename": original_filename,
        "content_type": content_type,
        "bytes": len(frame_bytes),
        "frame_file": str(frame_path),
        "metadata_file": str(metadata_path),
        "metadata": metadata,
    }
    temp_metadata_path = metadata_path.with_suffix(".json.tmp")
    with open(temp_metadata_path, "w") as output:
        json.dump(stored_metadata, output, indent=2, sort_keys=True)
        output.write("\n")
    os.replace(temp_metadata_path, metadata_path)
    return stored_metadata


def diagnostic_camera_solve(
    frame_id: str,
    frames_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
    environment_path: Optional[Path] = None,
    gps_path: Optional[Path] = None,
    solve_timeout_ms: int = 1000,
    preprocess_modes: Optional[List[str]] = None,
    force_attempt: bool = False,
    ai_image_preprocessing_enabled: bool = False,
    preprocess_strategy: str = "classic",
) -> Dict[str, Any]:
    """Score and optionally diagnostic-solve one stored mobile frame.

    This is intentionally diagnostic-only. It never updates PiFinder live
    pointing, solver state, or the integrator.
    """
    start_time = time.perf_counter()
    if not isinstance(frame_id, str) or not CAMERA_SOLVE_FRAME_ID_RE.match(frame_id):
        return error_payload(
            "invalid_frame_id",
            "frame_id must contain only letters, numbers, underscores, or hyphens.",
        )

    frame_root = frames_dir or ensure_mobile_frames_dir()
    frame_path = frame_root / f"{frame_id}.jpg"
    metadata_path = frame_root / f"{frame_id}.json"
    if not frame_path.exists() or not frame_path.is_file():
        return error_payload(
            "frame_not_found",
            f"No stored mobile frame exists for frame_id: {frame_id}.",
        )

    metadata = _load_optional_json(metadata_path)
    environment = _latest_environment_for_report(environment_path)
    try:
        score_mobile_frame = _import_lite_module("score_mobile_frame")
        score = score_mobile_frame.score_frame(frame_path)
        score_payload = asdict(score)
    except Exception as exc:
        payload = {
            "ok": True,
            "api": API_VERSION,
            "frame_id": frame_id,
            "diagnostic_only": True,
            "integrator_updated": False,
            "runtime_pointing_updated": False,
            "metadata": metadata,
            "environment": environment,
            "score": None,
            "solve": {
                "attempted": False,
                "solve_ok": False,
                "skipped_reason": "quality_score_error",
                "error": f"{exc.__class__.__name__}: {exc}",
            },
            "solve_altaz": {"available": False, "reason": "solve_not_ok"},
            "elapsed_ms": _elapsed_ms(start_time),
        }
        return _with_diagnostic_report(_with_diagnostic_summary(payload), reports_dir)

    should_attempt = bool(score.accept_for_diagnostic_solve or force_attempt)
    if not should_attempt:
        payload = {
            "ok": True,
            "api": API_VERSION,
            "frame_id": frame_id,
            "diagnostic_only": True,
            "integrator_updated": False,
            "runtime_pointing_updated": False,
            "metadata": metadata,
            "environment": environment,
            "score": score_payload,
            "solve": {
                "attempted": False,
                "solve_ok": False,
                "skipped_reason": "quality_score_rejected",
                "rejection_reasons": score.rejection_reasons,
            },
            "solve_altaz": {"available": False, "reason": "solve_not_ok"},
            "elapsed_ms": _elapsed_ms(start_time),
        }
        return _with_diagnostic_report(_with_diagnostic_summary(payload), reports_dir)

    if ai_image_preprocessing_enabled:
        solve_payload = _attempt_ai_image_preprocessing_solve(
            frame_path=frame_path,
            score=score,
            solve_timeout_ms=solve_timeout_ms,
            preprocess_strategy=preprocess_strategy,
        )
    else:
        solve_payload = _attempt_diagnostic_solve(
            frame_path=frame_path,
            score=score,
            solve_timeout_ms=solve_timeout_ms,
            preprocess_modes=preprocess_modes or ["baseline", "background_subtract"],
        )
        solve_payload["ai_image_preprocessing"] = _disabled_ai_image_preprocessing_payload()
    payload = {
        "ok": True,
        "api": API_VERSION,
        "frame_id": frame_id,
        "diagnostic_only": True,
        "integrator_updated": False,
        "runtime_pointing_updated": False,
        "metadata": metadata,
        "environment": environment,
        "score": score_payload,
        "solve": solve_payload,
        "solve_altaz": _solve_altaz_payload(solve_payload, gps_path),
        "elapsed_ms": _elapsed_ms(start_time),
    }
    return _with_diagnostic_report(_with_diagnostic_summary(payload), reports_dir)


def camera_report_history(
    reports_dir: Optional[Path] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Return recent mobile camera diagnostic reports and a session summary.

    This is read-only diagnostic data. It intentionally returns sanitized,
    compact report objects rather than raw files so mobile clients do not need
    to understand every internal score/solve field.
    """
    target_dir = reports_dir or ensure_mobile_camera_solve_reports_dir()
    safe_limit = max(1, min(int(limit), 100))
    report_files = _camera_report_files(target_dir)
    reports: List[Dict[str, Any]] = []
    warnings: List[str] = []
    malformed_reports = 0

    for report_file in report_files:
        payload, error = _load_camera_report(report_file)
        if error:
            malformed_reports += 1
            warnings.append(error)
            continue
        reports.append(_camera_report_summary(report_file, payload))
        if len(reports) >= safe_limit:
            break

    return {
        "ok": True,
        "api": API_VERSION,
        "report_dir": CAMERA_SOLVE_REPORTS_DIRNAME,
        "limit": safe_limit,
        "total_report_files": len(report_files),
        "malformed_reports": malformed_reports,
        "session_summary": _camera_session_summary(
            reports=reports,
            total_reports=max(0, len(report_files) - malformed_reports),
        ),
        "reports": reports,
        "warnings": warnings,
    }


def optical_boresight_status(
    profiles_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Return the latest phone-camera-to-telescope optical offset profile."""
    target_dir = profiles_dir or ensure_mobile_optical_boresight_profiles_dir()
    latest_path = target_dir / OPTICAL_BORESIGHT_LATEST_FILENAME
    if not latest_path.exists():
        return {
            "ok": True,
            "api": API_VERSION,
            "profile_available": False,
            "profile": None,
            "warnings": ["no_optical_boresight_profile_found"],
            "profiles_dir": str(target_dir),
            "diagnostic_only": True,
            "integrator_updated": False,
            "runtime_pointing_updated": False,
        }

    profile, load_error = _load_json_object(latest_path)
    if load_error:
        return {
            "ok": True,
            "api": API_VERSION,
            "profile_available": False,
            "profile": None,
            "warnings": [load_error],
            "profiles_dir": str(target_dir),
            "selected_profile": str(latest_path),
            "diagnostic_only": True,
            "integrator_updated": False,
            "runtime_pointing_updated": False,
        }

    warnings: List[str] = []
    if profile.get("schema") != OPTICAL_BORESIGHT_SCHEMA:
        warnings.append("invalid_optical_boresight_schema")
    if profile.get("status") != "ok":
        warnings.append(f"profile_status_{profile.get('status', 'unknown')}")

    return {
        "ok": True,
        "api": API_VERSION,
        "profile_available": profile.get("schema") == OPTICAL_BORESIGHT_SCHEMA,
        "profile": _optical_boresight_summary(profile),
        "warnings": warnings,
        "profiles_dir": str(target_dir),
        "selected_profile": str(latest_path),
        "diagnostic_only": True,
        "integrator_updated": False,
        "runtime_pointing_updated": False,
    }


def optical_boresight_calibration(
    payload: Dict[str, Any],
    profiles_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Create a repeatable read-only optical boresight calibration profile.

    The profile describes the angular offset between the latest solved mobile
    camera frame and a target manually centered in the telescope eyepiece. It
    is evidence only: no live solver, integrator, or pointing state is changed.
    """
    if not isinstance(payload, dict):
        return error_payload(
            "invalid_json",
            "Request body must be a JSON object.",
        )

    frame_id = str(payload.get("frame_id") or "").strip()
    if not CAMERA_SOLVE_FRAME_ID_RE.match(frame_id):
        return error_payload(
            "invalid_frame_id",
            "Run Full Diagnostic first so an uploaded frame_id is available.",
        )

    reference_ra_deg, ra_error = _optional_number_field(payload, "reference_ra_deg")
    reference_dec_deg, dec_error = _optional_number_field(payload, "reference_dec_deg")
    if ra_error or dec_error:
        return error_payload(
            "invalid_reference_coordinates",
            ra_error or dec_error or "Invalid reference coordinates.",
        )

    solve_timeout_ms, timeout_error = validate_solve_timeout_ms(
        payload,
        default_ms=1500,
    )
    if timeout_error:
        return error_payload("invalid_solve_timeout", timeout_error)
    assert solve_timeout_ms is not None
    solve_result = diagnostic_camera_solve(
        frame_id=frame_id,
        reports_dir=reports_dir,
        solve_timeout_ms=solve_timeout_ms,
        force_attempt=True,
        ai_image_preprocessing_enabled=bool(
            payload.get("ai_image_preprocessing_enabled", False)
        ),
        preprocess_strategy=str(payload.get("preprocess_strategy", "classic")),
    )
    if not bool(solve_result.get("ok", False)):
        return solve_result

    profile = _build_optical_boresight_profile(
        payload=payload,
        frame_id=frame_id,
        reference_ra_deg=reference_ra_deg,
        reference_dec_deg=reference_dec_deg,
        solve_result=solve_result,
    )
    stored = _write_optical_boresight_profile(profile, profiles_dir)
    return {
        "ok": True,
        "api": API_VERSION,
        "message": (
            "optical boresight calibration saved"
            if profile["status"] == "ok"
            else "optical boresight calibration needs more data"
        ),
        "calibration_ok": profile["status"] == "ok",
        "profile": _optical_boresight_summary(profile),
        "stored_as": stored["latest_profile"],
        "archived_as": stored["profile"],
        "diagnostic_solve_report": (
            solve_result.get("report", {}).get("json_report")
            if isinstance(solve_result.get("report"), dict)
            else None
        ),
        "diagnostic_only": True,
        "integrator_updated": False,
        "runtime_pointing_updated": False,
    }


def camera_exposure_advice(
    score: Optional[Dict[str, Any]],
    solve: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    """Map camera quality/solve diagnostics to short field advice.

    Thresholds are intentionally conservative until clear-sky Phase 2 evidence
    tunes them. The advice is diagnostic-only and never affects runtime state.
    """
    score = score if isinstance(score, dict) else {}
    solve = solve if isinstance(solve, dict) else {}
    rejection_reasons = {
        str(reason)
        for reason in score.get("rejection_reasons", [])
        if isinstance(reason, str)
    }

    if bool(solve.get("solve_ok")):
        return _advice(
            code="solved_collect_more",
            label="Solved",
            message=(
                "Diagnostic solve succeeded; keep it as evidence, but this "
                "is not final support."
            ),
            next_action=(
                "Repeat Run Full Diagnostic on more clear-sky frames before "
                "changing runtime pointing."
            ),
            severity="success",
        )

    if (
        {"too_bright_background", "lifted_gray_background", "background_mean_high"}
        & rejection_reasons
        or _score_number(score, "mean") > 6.5
        or 0 <= _score_number(score, "dark_pct") < 45
    ):
        return _advice(
            code="background_too_bright",
            label="Background too bright",
            message="The sky/background is too bright for reliable solving.",
            next_action=(
                "Try lower ISO/exposure, avoid clouds/moon/light pollution, "
                "or wait for darker sky."
            ),
            severity="warning",
        )

    if (
        {
            "noise_proxy_high",
            "too_many_bright_points_possible_noise",
            "possible_noise_overrank_lifted_background",
        }
        & rejection_reasons
        or _score_number(score, "noise_proxy") > 9.0
    ):
        return _advice(
            code="noise_too_high",
            label="Noise too high",
            message=(
                "Noise looks too high; ISO3200-style frames can mimic star "
                "candidates."
            ),
            next_action=(
                "Prefer ISO400/ISO800, steadier support, and a darker frame "
                "before solving."
            ),
            severity="warning",
        )

    if "saturation_present" in rejection_reasons or _score_number(score, "saturation_pct") > 0.5:
        return _advice(
            code="saturation_present",
            label="Saturation present",
            message="Some pixels are saturated, which can confuse star detection.",
            next_action="Reduce exposure/ISO and avoid bright lights in the frame.",
            severity="warning",
        )

    if "low_star_candidates" in rejection_reasons or _score_number(score, "centroids") < 18:
        return _advice(
            code="too_few_star_candidates",
            label="Too few candidates",
            message="The frame has too few star-like candidates to solve reliably.",
            next_action=(
                "Point at a richer star field, increase exposure slightly, or "
                "wait for clearer sky."
            ),
            severity="warning",
        )

    if "low_sharpness_or_low_signal" in rejection_reasons:
        return _advice(
            code="low_sharpness_or_signal",
            label="Low sharpness or signal",
            message="The frame appears soft or has too little usable signal.",
            next_action="Hold the phone steadier, refocus, and retry the same capture mode.",
            severity="warning",
        )

    if bool(solve.get("attempted")):
        return _advice(
            code="solve_failed_collect_better_frame",
            label="Solve failed",
            message="The frame was good enough to try, but Tetra3 did not solve it.",
            next_action=(
                "Retry with a steadier clear-sky frame and compare the report "
                "history."
            ),
            severity="info",
        )

    return _advice(
        code="inspect_quality_report",
        label="Inspect quality report",
        message="The frame did not produce a specific exposure diagnosis.",
        next_action="Run Full Diagnostic again and compare the report history.",
        severity="info",
    )


def validate_gps_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    required_fields = ("lat", "lon", "time_utc", "source")
    for field in required_fields:
        if field not in payload:
            return {}, f"Missing required field: {field}"

    lat, lat_error = _number_field(payload, "lat")
    if lat_error:
        return {}, lat_error
    lon, lon_error = _number_field(payload, "lon")
    if lon_error:
        return {}, lon_error
    altitude_m, altitude_error = _optional_number_field(payload, "altitude_m")
    if altitude_error:
        return {}, altitude_error
    accuracy_m, accuracy_error = _optional_number_field(payload, "accuracy_m")
    if accuracy_error:
        return {}, accuracy_error

    if not -90.0 <= lat <= 90.0:
        return {}, "lat must be between -90 and 90."
    if not -180.0 <= lon <= 180.0:
        return {}, "lon must be between -180 and 180."
    if accuracy_m is not None and accuracy_m < 0:
        return {}, "accuracy_m must be zero or greater."

    time_utc = payload.get("time_utc")
    if not isinstance(time_utc, str) or not time_utc.strip():
        return {}, "time_utc must be a non-empty string."
    parsed_time, time_error = _parse_utc_timestamp(time_utc)
    if time_error:
        return {}, time_error
    assert parsed_time is not None
    source = payload.get("source")
    if not isinstance(source, str) or not source.strip():
        return {}, "source must be a non-empty string."

    normalized = {
        "lat": lat,
        "lon": lon,
        "altitude_m": altitude_m,
        "accuracy_m": accuracy_m,
        "time_utc": parsed_time.isoformat().replace("+00:00", "Z"),
        "source": source,
    }
    if "provider" in payload:
        normalized["provider"] = payload["provider"]
    if "phone_time_utc" in payload:
        normalized["phone_time_utc"] = payload["phone_time_utc"]
    return normalized, None


def gps_payload(gps_fix: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "received_utc": utc_now_iso(),
        "gps": gps_fix,
    }


def mobile_gps_queue_fix(gps_fix: Dict[str, Any]) -> Dict[str, Any]:
    source = str(gps_fix.get("source") or "mobile").strip() or "mobile"
    altitude = gps_fix.get("altitude_m")
    accuracy = gps_fix.get("accuracy_m")
    queue_fix = {
        "lat": gps_fix["lat"],
        "lon": gps_fix["lon"],
        "altitude": 0 if altitude is None else altitude,
        "source": f"MOBILE:{source}",
        "error_in_m": DEFAULT_MOBILE_GPS_ERROR_M if accuracy is None else accuracy,
        "lock": True,
        "lock_type": 2,
        "time_utc": gps_fix["time_utc"],
    }
    if "provider" in gps_fix:
        queue_fix["provider"] = gps_fix["provider"]
    return queue_fix


def mobile_gps_queue_time(gps_fix: Dict[str, Any]) -> datetime:
    gps_time, error_message = _parse_utc_timestamp(str(gps_fix["time_utc"]))
    if error_message:
        raise ValueError(error_message)
    assert gps_time is not None
    return gps_time


def validate_solve_timeout_ms(
    payload: Dict[str, Any],
    default_ms: int,
    min_ms: int = MIN_SOLVE_TIMEOUT_MS,
    max_ms: int = MAX_SOLVE_TIMEOUT_MS,
) -> Tuple[Optional[int], Optional[str]]:
    raw_timeout = payload.get("solve_timeout_ms", default_ms)
    if isinstance(raw_timeout, bool):
        return None, "solve_timeout_ms must be an integer."
    try:
        timeout_ms = int(raw_timeout)
    except (TypeError, ValueError):
        return None, "solve_timeout_ms must be an integer."
    if timeout_ms < min_ms or timeout_ms > max_ms:
        return None, f"solve_timeout_ms must be between {min_ms} and {max_ms}."
    return timeout_ms, None


def validate_imu_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    if "samples" in payload:
        samples = payload["samples"]
    elif "sample" in payload:
        samples = [payload["sample"]]
    else:
        return {}, "Missing required field: samples."

    if not isinstance(samples, list) or not samples:
        return {}, "samples must be a non-empty list."
    if len(samples) > MAX_IMU_SAMPLES:
        return {}, f"samples must contain {MAX_IMU_SAMPLES} items or fewer."

    batch_label = str(payload.get("batch_label") or "diagnostic").strip()
    if batch_label not in IMU_BATCH_LABELS:
        labels = ", ".join(sorted(IMU_BATCH_LABELS))
        return {}, f"batch_label must be one of: {labels}."

    capture_duration_ms, duration_error = _optional_number_field(
        payload,
        "capture_duration_ms",
    )
    if duration_error:
        return {}, duration_error
    if capture_duration_ms is not None and capture_duration_ms < 0:
        return {}, "capture_duration_ms must be zero or greater."

    normalized_samples = []
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            return {}, f"samples[{index}] must be an object."
        normalized_sample, error_message = _validate_imu_sample(sample, index)
        if error_message:
            return {}, error_message
        normalized_samples.append(normalized_sample)

    normalized = {
        "schema": payload.get("schema", "pifinder-mobile-imu-batch-v0"),
        "batch_label": batch_label,
        "device_time_utc": payload.get("device_time_utc"),
        "capture_duration_ms": capture_duration_ms,
        "sample_count": len(normalized_samples),
        "samples": normalized_samples,
        "coordinate_frame_note": (
            "Android sensor coordinate frames are device-relative. This debug "
            "payload is not aligned to the telescope optical axis."
        ),
    }
    if "device" in payload:
        normalized["device"] = payload["device"]
    if "screen_orientation" in payload:
        normalized["screen_orientation"] = payload["screen_orientation"]
    if "app_version" in payload:
        normalized["app_version"] = payload["app_version"]
    return normalized, None


def imu_payload(imu_batch: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "received_utc": utc_now_iso(),
        "imu": imu_batch,
    }


def ai_imu_drift_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze solve-to-solve mobile IMU residual cycles.

    This is diagnostic-only. It never updates PiFinder live pointing or the
    integrator.
    """
    if not isinstance(payload, dict):
        return error_payload(
            "invalid_json",
            "Request body must be a JSON object.",
        )
    try:
        analyzer = _import_lite_module("analyze_mobile_imu_drift")
        report = analyzer.analyze_payload(payload)
    except Exception as exc:
        return error_payload(
            "invalid_imu_drift_analysis",
            f"{exc.__class__.__name__}: {exc}",
        )
    report["ok"] = True
    report["api"] = API_VERSION
    report["diagnostic_only"] = True
    report["integrator_updated"] = False
    report["runtime_pointing_updated"] = False
    return report


def mount_profile_status(
    profiles_dir: Optional[Path] = None,
    mobile_profile_path: Optional[Path] = None,
) -> Dict[str, Any]:
    profiles_path = profiles_dir or ensure_mobile_mount_profiles_dir()
    warnings: List[str] = []
    profile_files = _mount_profile_files(profiles_path)
    if not profile_files:
        return {
            "ok": True,
            "api": API_VERSION,
            "profile_available": False,
            "profile": None,
            "warnings": ["no_mount_profiles_found"],
            "profiles_dir": str(profiles_path),
        }

    selected_path = profile_files[0]
    profile, load_error = _load_json_object(selected_path)
    if load_error:
        return {
            "ok": True,
            "api": API_VERSION,
            "profile_available": False,
            "profile": None,
            "warnings": [load_error],
            "profiles_dir": str(profiles_path),
            "selected_profile": str(selected_path),
        }

    expected_device_model = (
        _latest_mobile_device_model(mobile_profile_path)
        if mobile_profile_path is not None
        else None
    )
    summary, validation_warnings = _summarize_mount_profile(
        profile,
        selected_path,
        expected_device_model,
    )
    warnings.extend(validation_warnings)
    return {
        "ok": True,
        "api": API_VERSION,
        "profile_available": summary is not None,
        "profile": summary,
        "warnings": warnings,
        "profiles_dir": str(profiles_path),
        "selected_profile": str(selected_path),
    }


def status_payload() -> Dict[str, Any]:
    return {
        "ok": True,
        "api": API_VERSION,
        "server_time_utc": utc_now_iso(),
        "pifinder": {
            "web_remote": True,
            "image_endpoint": True,
            "key_callback": True,
            "lx200_port": 4030,
        },
        "mobile_bridge": {
            "status": "implemented",
            "profile": "implemented",
            "gps": "implemented",
            "environment": "implemented_diagnostic_only",
            "imu": "implemented_debug_only",
            "camera_frame": "implemented_storage_only",
            "camera_solve": "implemented_diagnostic_only",
            "camera_reports": "implemented_read_only",
            "mount_profile": "implemented_read_only",
            "optical_boresight": "implemented_read_only",
        },
    }


def _elapsed_ms(start_time: float) -> int:
    return int((time.perf_counter() - start_time) * 1000)


def _advice(
    code: str,
    label: str,
    message: str,
    next_action: str,
    severity: str,
) -> Dict[str, str]:
    return {
        "code": code,
        "label": label,
        "message": message,
        "next_action": next_action,
        "severity": severity,
    }


def _score_number(score: Dict[str, Any], key: str) -> float:
    value = score.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _import_lite_module(module_name: str):
    lite_dir = _repo_root() / "PiFinder_lite"
    lite_path = str(lite_dir)
    if lite_path not in sys.path:
        sys.path.insert(0, lite_path)
    return __import__(module_name)


def _load_optional_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path) as input_file:
            payload = json.load(input_file)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_utc_datetime(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _radec_to_altaz_for_gps(
    ra_deg: float,
    dec_deg: float,
    gps_fix: Dict[str, Any],
) -> Tuple[float, float]:
    from PiFinder import calc_utils

    observer = calc_utils.sf_utils(
        lat=float(gps_fix["lat"]),
        lon=float(gps_fix["lon"]),
        altitude=float(gps_fix.get("altitude_m") or 0.0),
    )
    return observer.radec_to_altaz(
        float(ra_deg),
        float(dec_deg),
        _parse_utc_datetime(gps_fix.get("time_utc")),
    )


def _solve_altaz_payload(
    solve_payload: Dict[str, Any],
    gps_path: Optional[Path],
) -> Dict[str, Any]:
    if not bool(solve_payload.get("solve_ok")):
        return {"available": False, "reason": "solve_not_ok"}
    best = solve_payload.get("best")
    if not isinstance(best, dict):
        return {"available": False, "reason": "missing_best_solve"}
    ra = best.get("solve_ra")
    dec = best.get("solve_dec")
    if ra is None or dec is None:
        return {"available": False, "reason": "missing_ra_dec"}
    path = gps_path or (ensure_mobile_data_dir() / GPS_LATEST_FILENAME)
    gps_payload = _load_optional_json(path)
    gps_fix = gps_payload.get("gps") if isinstance(gps_payload, dict) else None
    if not isinstance(gps_fix, dict):
        return {"available": False, "reason": "mobile_gps_missing"}
    try:
        alt_deg, az_deg = _radec_to_altaz_for_gps(float(ra), float(dec), gps_fix)
    except Exception as exc:
        return {
            "available": False,
            "reason": "altaz_conversion_failed",
            "error": f"{exc.__class__.__name__}: {exc}",
        }
    return {
        "available": True,
        "alt_deg": round(float(alt_deg), 6),
        "az_deg": round(float(az_deg), 6),
        "source": "mobile_gps_latest",
    }


def _attempt_diagnostic_solve(
    frame_path: Path,
    score: Any,
    solve_timeout_ms: int,
    preprocess_modes: List[str],
) -> Dict[str, Any]:
    try:
        diagnostic_solve = _import_lite_module("diagnostic_solve_mobile_frame")
        t3 = diagnostic_solve.tetra3.Tetra3(str(diagnostic_solve.TETRA3_DB))
        results = diagnostic_solve.solve_one(
            t3=t3,
            frame_path=frame_path,
            score=score,
            candidate_rank=1,
            preprocess_modes=preprocess_modes,
            solve_timeout_ms=solve_timeout_ms,
            continue_after_solve=False,
        )
    except Exception as exc:
        return {
            "attempted": True,
            "solve_ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
        }

    rows = [asdict(result) for result in results]
    solved_rows = [row for row in rows if row.get("solve_ok")]
    return {
        "attempted": True,
        "solve_ok": bool(solved_rows),
        "rows": rows,
        "best": solved_rows[0] if solved_rows else (rows[0] if rows else None),
    }


def _disabled_ai_image_preprocessing_payload() -> Dict[str, Any]:
    return {
        "enabled": False,
        "strategy": "classic",
        "verdict": "disabled",
    }


def _score_attr(score: Any, name: str, default: float = 0.0) -> float:
    value = getattr(score, name, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _select_ai_preprocessing_modes(frame_path: Path, score: Any) -> Dict[str, Any]:
    start_time = time.perf_counter()
    mean = _score_attr(score, "mean")
    dark_pct = _score_attr(score, "dark_pct")
    saturation_pct = _score_attr(score, "saturation_pct")
    sharpness = _score_attr(score, "sharpness")
    noise_proxy = _score_attr(score, "noise_proxy")
    bright_points = int(_score_attr(score, "bright_points"))
    centroids = int(_score_attr(score, "centroids"))

    modes: List[str] = []
    reasons: List[str] = []
    if mean > 6.0 or dark_pct < 75.0:
        modes.extend(["background_subtract", "percentile_stretch"])
        reasons.append("bright_or_lifted_background")
    if noise_proxy > 10.0 or bright_points > 350:
        modes.extend(["hot_pixel_suppression", "denoise_stretch"])
        reasons.append("noise_or_hot_pixels")
    if centroids < 18 or bright_points < 12:
        modes.extend(["percentile_stretch", "local_contrast"])
        reasons.append("few_candidate_stars")
    if sharpness < 3.0:
        modes.append("center_crop")
        reasons.append("soft_or_edge_degraded_frame")
    if not modes:
        modes.extend(["percentile_stretch", "background_subtract"])
        reasons.append("balanced_frame_probe")

    selected_modes: List[str] = []
    for mode in modes:
        if mode not in selected_modes:
            selected_modes.append(mode)
        if len(selected_modes) >= 2:
            break

    return {
        "strategy": "adaptive",
        "selected_modes": selected_modes,
        "selection_reason": ",".join(reasons),
        "image_metrics": {
            "mean": mean,
            "dark_pct": dark_pct,
            "saturation_pct": saturation_pct,
            "sharpness": sharpness,
            "noise_proxy": noise_proxy,
            "bright_points": bright_points,
            "centroids": centroids,
        },
        "image_analysis_ms": _elapsed_ms(start_time),
    }


def _solve_time_ms(solve_payload: Dict[str, Any]) -> float:
    total = 0.0
    for row in solve_payload.get("rows") or []:
        value = row.get("solve_time_ms") if isinstance(row, dict) else None
        if isinstance(value, (int, float)):
            total += float(value)
    return round(total, 1)


def _solve_matches(solve_payload: Dict[str, Any]) -> int:
    best = solve_payload.get("best")
    if not isinstance(best, dict):
        return 0
    value = best.get("solve_matches")
    return int(value) if isinstance(value, (int, float)) else 0


def _solve_result_summary(solve_payload: Dict[str, Any]) -> Dict[str, Any]:
    best = solve_payload.get("best")
    return {
        "attempted": bool(solve_payload.get("attempted")),
        "solve_ok": bool(solve_payload.get("solve_ok")),
        "matches": _solve_matches(solve_payload),
        "best_preprocess_mode": (
            best.get("preprocess_mode") if isinstance(best, dict) else ""
        ),
    }


def _ai_preprocessing_verdict(
    baseline: Dict[str, Any],
    adaptive: Dict[str, Any],
    extra_time_ms: float,
) -> str:
    baseline_ok = bool(baseline.get("solve_ok"))
    adaptive_ok = bool(adaptive.get("solve_ok"))
    baseline_matches = _solve_matches(baseline)
    adaptive_matches = _solve_matches(adaptive)
    if adaptive_ok and not baseline_ok:
        return "helped"
    if adaptive_ok and baseline_ok and adaptive_matches > baseline_matches:
        return "helped"
    if extra_time_ms > 1000 and not adaptive_ok:
        return "too_slow"
    if baseline_ok and not adaptive_ok:
        return "not_needed"
    if baseline_ok and adaptive_ok:
        return "not_needed"
    if not baseline_ok and not adaptive_ok:
        return "not_useful"
    return "inconclusive"


def _solve_consistency(baseline: Dict[str, Any], adaptive: Dict[str, Any]) -> str:
    baseline_ok = bool(baseline.get("solve_ok"))
    adaptive_ok = bool(adaptive.get("solve_ok"))
    if baseline_ok and adaptive_ok:
        return "both_solved"
    if adaptive_ok:
        return "adaptive_only"
    if baseline_ok:
        return "baseline_only"
    return "none_solved"


def _attempt_ai_image_preprocessing_solve(
    frame_path: Path,
    score: Any,
    solve_timeout_ms: int,
    preprocess_strategy: str,
) -> Dict[str, Any]:
    start_time = time.perf_counter()
    selector = _select_ai_preprocessing_modes(frame_path, score)
    selected_modes = selector.get("selected_modes") or ["percentile_stretch"]
    baseline_modes = ["baseline", "background_subtract"]

    baseline_solve = _attempt_diagnostic_solve(
        frame_path=frame_path,
        score=score,
        solve_timeout_ms=solve_timeout_ms,
        preprocess_modes=baseline_modes,
    )
    adaptive_solve = _attempt_diagnostic_solve(
        frame_path=frame_path,
        score=score,
        solve_timeout_ms=solve_timeout_ms,
        preprocess_modes=list(selected_modes),
    )

    baseline_solve_ms = _solve_time_ms(baseline_solve)
    adaptive_solve_ms = _solve_time_ms(adaptive_solve)
    image_analysis_ms = int(selector.get("image_analysis_ms") or 0)
    total_ai_path_ms = _elapsed_ms(start_time)
    preprocessing_ms = max(
        0.0,
        round(total_ai_path_ms - baseline_solve_ms - adaptive_solve_ms - image_analysis_ms, 1),
    )
    extra_time_ms = round(image_analysis_ms + preprocessing_ms + adaptive_solve_ms, 1)
    verdict = _ai_preprocessing_verdict(baseline_solve, adaptive_solve, extra_time_ms)
    adaptive_helped = verdict == "helped"
    winning_solve = adaptive_solve if adaptive_helped else baseline_solve
    if not winning_solve.get("solve_ok") and adaptive_solve.get("solve_ok"):
        winning_solve = adaptive_solve

    rows: List[Dict[str, Any]] = []
    for source_name, solve_payload in (
        ("baseline", baseline_solve),
        ("adaptive", adaptive_solve),
    ):
        for row in solve_payload.get("rows") or []:
            if isinstance(row, dict):
                annotated = dict(row)
                annotated["ai_path"] = source_name
                rows.append(annotated)

    best = winning_solve.get("best")
    winning_variant = best.get("preprocess_mode") if isinstance(best, dict) else ""
    solve_ok = bool(baseline_solve.get("solve_ok") or adaptive_solve.get("solve_ok"))
    return {
        "attempted": True,
        "solve_ok": solve_ok,
        "rows": rows,
        "best": best if isinstance(best, dict) else (rows[0] if rows else None),
        "ai_image_preprocessing": {
            "enabled": True,
            "strategy": preprocess_strategy or "adaptive",
            "image_analysis_ms": image_analysis_ms,
            "preprocessing_ms": preprocessing_ms,
            "baseline_solve_ms": baseline_solve_ms,
            "adaptive_solve_ms": adaptive_solve_ms,
            "total_ai_path_ms": total_ai_path_ms,
            "extra_time_ms": extra_time_ms,
            "selected_modes": list(selected_modes),
            "variants_tried": baseline_modes + list(selected_modes),
            "selection_reason": selector.get("selection_reason", ""),
            "image_metrics": selector.get("image_metrics", {}),
            "winning_variant": winning_variant,
            "baseline_result": _solve_result_summary(baseline_solve),
            "adaptive_result": _solve_result_summary(adaptive_solve),
            "matches": _solve_matches(winning_solve),
            "solve_consistency": _solve_consistency(baseline_solve, adaptive_solve),
            "verdict": verdict,
        },
    }


def _with_diagnostic_report(
    payload: Dict[str, Any],
    reports_dir: Optional[Path],
) -> Dict[str, Any]:
    report_info = _write_diagnostic_report(payload, reports_dir)
    payload["report"] = report_info
    return payload


def _camera_report_files(reports_dir: Path) -> List[Path]:
    if not reports_dir.exists() or not reports_dir.is_dir():
        return []
    return sorted(
        [path for path in reports_dir.glob("*.json") if path.is_file()],
        key=lambda path: (path.name, path.stat().st_mtime),
        reverse=True,
    )


def _load_camera_report(path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        with open(path) as input_file:
            payload = json.load(input_file)
    except json.JSONDecodeError:
        return {}, f"malformed_report:{path.name}"
    except OSError as exc:
        return {}, f"malformed_report:{path.name}:{exc}"
    if not isinstance(payload, dict):
        return {}, f"malformed_report:{path.name}:expected_object"
    return _sanitize_diagnostic_report(payload), None


def _latest_environment_for_report(
    environment_path: Optional[Path] = None,
) -> Dict[str, Any]:
    path = environment_path or (MOBILE_DATA_DIR / ENVIRONMENT_LATEST_FILENAME)
    latest = _load_optional_json(path)
    if not isinstance(latest, dict) or not latest:
        return {
            "available": False,
            "summary": environment_summary({}),
            "warnings": ["no_environment_payload_found"],
        }

    environment = latest.get("environment")
    if not isinstance(environment, dict):
        environment, error = validate_environment_payload(latest)
        if error:
            return {
                "available": False,
                "summary": environment_summary({}),
                "warnings": [error],
            }

    summary = latest.get("summary")
    if not isinstance(summary, dict):
        summary = environment_summary(environment)

    return {
        "available": True,
        "received_utc": latest.get("received_utc"),
        "summary": summary,
    }


def _camera_report_summary(report_file: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    score = payload.get("score") if isinstance(payload.get("score"), dict) else {}
    solve = payload.get("solve") if isinstance(payload.get("solve"), dict) else {}
    environment = (
        payload.get("environment") if isinstance(payload.get("environment"), dict) else {}
    )
    advice = payload.get("advice") if isinstance(payload.get("advice"), dict) else None
    if advice is None:
        advice = camera_exposure_advice(score, solve)
    report_mtime_utc = (
        datetime.fromtimestamp(report_file.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "report_file": report_file.name,
        "report_mtime_utc": report_mtime_utc,
        "frame_id": str(payload.get("frame_id") or "unknown"),
        "diagnostic_only": bool(payload.get("diagnostic_only", True)),
        "summary": summary,
        "advice": advice,
        "score": {
            "path": score.get("path"),
            "grade": summary.get("grade", score.get("grade", "unknown")),
            "quality_score": summary.get(
                "quality_score",
                score.get("quality_score"),
            ),
            "accepted_for_diagnostic_solve": score.get(
                "accepted_for_diagnostic_solve"
            ),
            "rejection_reasons": score.get("rejection_reasons", []),
        },
        "solve": {
            "attempted": bool(summary.get("attempted", solve.get("attempted"))),
            "solve_ok": bool(summary.get("solve_ok", solve.get("solve_ok"))),
            "skipped_reason": summary.get(
                "skipped_reason",
                solve.get("skipped_reason", ""),
            ),
            "best": solve.get("best"),
        },
        "recommendation": str(payload.get("recommendation") or ""),
        "next_action": str(payload.get("next_action") or ""),
        "environment": _camera_environment_summary(environment),
        "elapsed_ms": payload.get("elapsed_ms"),
    }


def _camera_environment_summary(environment: Dict[str, Any]) -> Dict[str, Any]:
    summary = environment.get("summary") if isinstance(environment, dict) else {}
    if not isinstance(summary, dict):
        summary = {}
    return {
        "available": bool(environment.get("available", False))
        if isinstance(environment, dict)
        else False,
        "received_utc": environment.get("received_utc") if isinstance(environment, dict) else None,
        "summary": summary or environment_summary({}),
        "warnings": environment.get("warnings", []) if isinstance(environment, dict) else [],
    }


def _camera_session_summary(
    reports: List[Dict[str, Any]],
    total_reports: int,
) -> Dict[str, Any]:
    status_counts: Dict[str, int] = {}
    advice_counts: Dict[str, int] = {}
    best_frame_id = None
    best_quality_score = None
    best_solved_frame_id = None
    dominant_advice = None
    environment_counts = {
        "reports_with_environment": 0,
        "ambient_light_available": 0,
        "pressure_available": 0,
        "battery_available": 0,
        "network_available": 0,
    }
    latest_environment_summary = None

    for report in reports:
        summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        advice = report.get("advice") if isinstance(report.get("advice"), dict) else {}
        status = str(summary.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        advice_code = str(advice.get("code") or "unknown")
        advice_counts[advice_code] = advice_counts.get(advice_code, 0) + 1
        if dominant_advice is None or advice_counts[advice_code] > advice_counts.get(
            str(dominant_advice.get("code") or "unknown"),
            0,
        ):
            dominant_advice = advice
        quality_score = summary.get("quality_score")
        if isinstance(quality_score, (int, float)) and (
            best_quality_score is None or quality_score > best_quality_score
        ):
            best_quality_score = quality_score
            best_frame_id = report.get("frame_id")
        if bool(summary.get("solve_ok")) and best_solved_frame_id is None:
            best_solved_frame_id = report.get("frame_id")
        environment = (
            report.get("environment")
            if isinstance(report.get("environment"), dict)
            else {}
        )
        if bool(environment.get("available", False)):
            environment_counts["reports_with_environment"] += 1
            env_summary = (
                environment.get("summary")
                if isinstance(environment.get("summary"), dict)
                else {}
            )
            if latest_environment_summary is None:
                latest_environment_summary = env_summary
            for key in (
                "ambient_light_available",
                "pressure_available",
                "battery_available",
                "network_available",
            ):
                if bool(env_summary.get(key, False)):
                    environment_counts[key] += 1

    solved_count = status_counts.get("solved", 0)
    returned_reports = len(reports)
    if returned_reports == 0:
        recommendation = "run_full_diagnostic"
        next_action = "Run Full Diagnostic from Camera Lab to create the first report."
    elif solved_count > 0:
        recommendation = "collect_clear_sky_evidence"
        next_action = (
            "Keep this solved report and repeat with more clear-sky frames "
            "before changing runtime pointing."
        )
    else:
        recommendation = "capture_better_frames"
        next_action = (
            "Run Full Diagnostic again with darker sky, steadier framing, or "
            "different camera settings."
        )

    return {
        "total_reports": total_reports,
        "returned_reports": returned_reports,
        "status_counts": status_counts,
        "advice_counts": advice_counts,
        "dominant_advice": dominant_advice,
        "solved_count": solved_count,
        "rejected_count": status_counts.get("rejected", 0),
        "best_frame_id": best_frame_id,
        "best_solved_frame_id": best_solved_frame_id,
        "best_quality_score": best_quality_score,
        "environment": {
            **environment_counts,
            "latest": latest_environment_summary,
        },
        "recommendation": recommendation,
        "next_action": next_action,
    }


def _with_diagnostic_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    solve = payload.get("solve") if isinstance(payload.get("solve"), dict) else {}
    score = payload.get("score") if isinstance(payload.get("score"), dict) else {}
    attempted = bool(solve.get("attempted"))
    solve_ok = bool(solve.get("solve_ok"))
    skipped_reason = str(solve.get("skipped_reason") or "")
    grade = str(score.get("grade") or "unknown")
    quality_score = score.get("quality_score")

    if skipped_reason == "quality_score_rejected":
        status = "rejected"
        label = "Rejected by quality score"
        recommendation = "capture_better_frame"
        next_action = (
            "Run Full Diagnostic again with a darker, steadier frame or wait "
            "for clearer sky."
        )
    elif skipped_reason == "quality_score_error":
        status = "score_error"
        label = "Quality score failed"
        recommendation = "check_frame_or_server_logs"
        next_action = "Check the stored JPEG/report and retry Run Full Diagnostic."
    elif attempted and solve_ok:
        status = "solved"
        label = "Diagnostic solve succeeded"
        recommendation = "keep_collecting_clear_sky_evidence"
        next_action = (
            "Save this report as evidence and repeat Run Full Diagnostic across "
            "more clear-sky frames."
        )
    elif attempted:
        status = "solve_failed"
        label = "Diagnostic solve attempted but failed"
        recommendation = "capture_better_frame_or_tune_thresholds"
        next_action = (
            "Run Full Diagnostic again with steadier capture and compare the "
            "stored reports."
        )
    else:
        status = "not_attempted"
        label = "Diagnostic solve not attempted"
        recommendation = "inspect_report"
        next_action = "Inspect the stored report and retry Run Full Diagnostic."

    payload["summary"] = {
        "status": status,
        "label": label,
        "grade": grade,
        "quality_score": quality_score,
        "attempted": attempted,
        "solve_ok": solve_ok,
        "skipped_reason": skipped_reason,
    }
    payload["advice"] = camera_exposure_advice(score, solve)
    payload["recommendation"] = recommendation
    payload["next_action"] = next_action
    return payload


def _write_diagnostic_report(
    payload: Dict[str, Any],
    reports_dir: Optional[Path],
) -> Dict[str, Any]:
    target_dir = reports_dir or ensure_mobile_camera_solve_reports_dir()
    utils.create_path(target_dir)
    frame_id = str(payload.get("frame_id") or "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = target_dir / f"{timestamp}_{frame_id}.json"
    report_payload = _sanitize_diagnostic_report(payload)
    temp_path = report_path.with_suffix(".json.tmp")
    with open(temp_path, "w") as output:
        json.dump(report_payload, output, indent=2, sort_keys=True)
        output.write("\n")
    os.replace(temp_path, report_path)
    return {
        "stored": True,
        "json_report": str(report_path),
    }


def _sanitize_diagnostic_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = json.loads(json.dumps(payload, default=str))
    sanitized = _strip_private_location_fields(sanitized)
    metadata = sanitized.get("metadata")
    if isinstance(metadata, dict):
        metadata.pop("frame_file", None)
        metadata.pop("metadata_file", None)
        nested = metadata.get("metadata")
        if isinstance(nested, dict):
            for key in ("location", "gps", "lat", "lon", "latitude", "longitude"):
                nested.pop(key, None)
        for key in ("location", "gps", "lat", "lon", "latitude", "longitude"):
            metadata.pop(key, None)
    score = sanitized.get("score")
    if isinstance(score, dict):
        score["path"] = Path(str(score.get("path", ""))).name
    solve = sanitized.get("solve")
    if isinstance(solve, dict):
        for row in solve.get("rows") or []:
            if isinstance(row, dict) and "path" in row:
                row["path"] = Path(str(row["path"])).name
        best = solve.get("best")
        if isinstance(best, dict) and "path" in best:
            best["path"] = Path(str(best["path"])).name
    sanitized.pop("report", None)
    return sanitized


def _build_optical_boresight_profile(
    payload: Dict[str, Any],
    frame_id: str,
    reference_ra_deg: Optional[float],
    reference_dec_deg: Optional[float],
    solve_result: Dict[str, Any],
) -> Dict[str, Any]:
    timestamp = utc_now_iso()
    profile_id = f"optical_boresight_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    solve = solve_result.get("solve") if isinstance(solve_result.get("solve"), dict) else {}
    best = solve.get("best") if isinstance(solve.get("best"), dict) else {}
    camera_ra = _optional_float(best.get("solve_ra"))
    camera_dec = _optional_float(best.get("solve_dec"))
    solve_ok = bool(solve.get("solve_ok")) and camera_ra is not None and camera_dec is not None

    warnings: List[str] = []
    status = "ok"
    if reference_ra_deg is None or reference_dec_deg is None:
        status = "needs_reference_coordinates"
        warnings.append("reference_ra_dec_required")
    if not solve_ok:
        status = "solve_failed"
        warnings.append("diagnostic_solve_not_available")

    offset: Dict[str, Any] = {"available": False}
    if status == "ok" and camera_ra is not None and camera_dec is not None:
        ra_offset = _normalize_degrees_signed(float(reference_ra_deg) - camera_ra)
        dec_offset = float(reference_dec_deg) - camera_dec
        mean_dec_rad = math.radians((float(reference_dec_deg) + camera_dec) / 2.0)
        angular_offset = math.sqrt(
            (ra_offset * math.cos(mean_dec_rad)) ** 2 + dec_offset**2
        )
        offset = {
            "available": True,
            "ra_deg": round(ra_offset, 6),
            "dec_deg": round(dec_offset, 6),
            "angular_deg": round(angular_offset, 6),
            "interpretation": (
                "reference_center_minus_mobile_camera_center; diagnostic-only"
            ),
        }

    return {
        "schema": OPTICAL_BORESIGHT_SCHEMA,
        "profile_id": profile_id,
        "created_utc": timestamp,
        "status": status,
        "reference": {
            "target": str(payload.get("reference_target") or "").strip(),
            "ra_deg": reference_ra_deg,
            "dec_deg": reference_dec_deg,
        },
        "camera_center": {
            "frame_id": frame_id,
            "ra_deg": camera_ra,
            "dec_deg": camera_dec,
            "solve_ok": solve_ok,
            "solve_summary": solve_result.get("summary"),
        },
        "offset": offset,
        "app": _object_or_empty(payload.get("app")),
        "device": _object_or_empty(payload.get("device")),
        "diagnostic_only": True,
        "read_only": True,
        "integrator_updated": False,
        "runtime_pointing_updated": False,
        "runtime": {
            "allow_integrator_feed": False,
            "allow_runtime_pointing_update": False,
            "requires_manual_recalibration_after_remount": True,
        },
        "warnings": warnings,
    }


def _write_optical_boresight_profile(
    profile: Dict[str, Any],
    profiles_dir: Optional[Path],
) -> Dict[str, str]:
    target_dir = profiles_dir or ensure_mobile_optical_boresight_profiles_dir()
    utils.create_path(target_dir)
    profile_id = str(profile.get("profile_id") or "optical_boresight")
    archive_path = target_dir / f"{profile_id}.json"
    latest_path = target_dir / OPTICAL_BORESIGHT_LATEST_FILENAME
    sanitized = _strip_private_location_fields(json.loads(json.dumps(profile, default=str)))
    for path in (archive_path, latest_path):
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with open(temp_path, "w") as output:
            json.dump(sanitized, output, indent=2, sort_keys=True)
            output.write("\n")
        os.replace(temp_path, path)
    return {
        "profile": str(archive_path),
        "latest_profile": str(latest_path),
    }


def _optical_boresight_summary(profile: Dict[str, Any]) -> Dict[str, Any]:
    reference = profile.get("reference") if isinstance(profile.get("reference"), dict) else {}
    camera_center = (
        profile.get("camera_center")
        if isinstance(profile.get("camera_center"), dict)
        else {}
    )
    offset = profile.get("offset") if isinstance(profile.get("offset"), dict) else {}
    runtime = profile.get("runtime") if isinstance(profile.get("runtime"), dict) else {}
    return {
        "profile_id": profile.get("profile_id"),
        "created_utc": profile.get("created_utc"),
        "status": profile.get("status", "unknown"),
        "reference": reference,
        "camera_center": camera_center,
        "offset": offset,
        "read_only": bool(profile.get("read_only", True)),
        "diagnostic_only": bool(profile.get("diagnostic_only", True)),
        "integrator_blocked": not bool(runtime.get("allow_integrator_feed", False)),
        "runtime_pointing_blocked": not bool(
            runtime.get("allow_runtime_pointing_update", False)
        ),
        "warnings": profile.get("warnings", []),
    }


def _normalize_degrees_signed(value: float) -> float:
    wrapped = (float(value) + 180.0) % 360.0 - 180.0
    if wrapped == -180.0:
        return 180.0
    return wrapped


def _mount_profile_files(profiles_dir: Path) -> List[Path]:
    if not profiles_dir.exists() or not profiles_dir.is_dir():
        return []
    return sorted(
        [path for path in profiles_dir.glob("*.json") if path.is_file()],
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )


def _load_json_object(path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        with open(path) as input_file:
            payload = json.load(input_file)
    except json.JSONDecodeError as exc:
        return {}, f"invalid_mount_profile_json:{path.name}:{exc.msg}"
    except OSError as exc:
        return {}, f"mount_profile_read_failed:{path.name}:{exc}"
    if not isinstance(payload, dict):
        return {}, f"invalid_mount_profile_json:{path.name}:expected_object"
    return payload, None


def _latest_mobile_device_model(mobile_profile_path: Optional[Path]) -> Optional[str]:
    if mobile_profile_path is None:
        return None
    profile_path = mobile_profile_path
    if not profile_path.exists():
        return None
    payload, error = _load_json_object(profile_path)
    if error:
        return None
    profile = payload.get("profile")
    if not isinstance(profile, dict):
        return None
    device = profile.get("device")
    if not isinstance(device, dict):
        return None
    model = device.get("model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return None


def _summarize_mount_profile(
    profile: Dict[str, Any],
    path: Path,
    expected_device_model: Optional[str],
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    if profile.get("schema") != MOUNT_PROFILE_SCHEMA:
        return None, ["invalid_mount_profile_schema"]

    profile_id = _string_value(profile, "profile_id")
    if not profile_id:
        warnings.append("missing_profile_id")

    status = _string_value(profile, "status") or "unknown"
    if status not in MOUNT_PROFILE_STATUSES:
        warnings.append("invalid_status")
    if status in {"uncalibrated", "invalidated"}:
        warnings.append(f"profile_status_{status}")

    device = profile.get("device") if isinstance(profile.get("device"), dict) else {}
    device_model = str(device.get("model") or "").strip()
    if not device_model:
        warnings.append("missing_device_model")
    if (
        expected_device_model
        and device_model
        and device_model != expected_device_model
    ):
        warnings.append("phone_model_mismatch")

    validation = (
        profile.get("validation")
        if isinstance(profile.get("validation"), dict)
        else {}
    )
    validation_state = str(validation.get("state") or "unknown").strip()
    if validation_state not in MOUNT_PROFILE_VALIDATION_STATES:
        warnings.append("invalid_validation_state")
    if validation_state != "passed":
        warnings.append("profile_not_repeatability_validated")
    for warning in validation.get("warnings") or []:
        if isinstance(warning, str) and warning.strip():
            warnings.append(warning.strip())

    offset = profile.get("offset") if isinstance(profile.get("offset"), dict) else {}
    q_phone_to_tube = offset.get("q_phone_to_tube")
    has_offset = (
        isinstance(q_phone_to_tube, list)
        and len(q_phone_to_tube) == 4
        and all(isinstance(value, (int, float)) for value in q_phone_to_tube)
    )
    if not has_offset:
        warnings.append("missing_valid_offset")

    runtime = profile.get("runtime") if isinstance(profile.get("runtime"), dict) else {}
    allow_integrator_feed = bool(runtime.get("allow_integrator_feed", False))
    allow_guidance_overlay = bool(runtime.get("allow_guidance_overlay", False))
    requires_manual_enable = bool(runtime.get("requires_manual_enable", True))
    if allow_integrator_feed:
        warnings.append("integrator_feed_requested_but_blocked")
    if not requires_manual_enable:
        warnings.append("manual_enable_required_missing")

    overlay_candidate = (
        status == "usable"
        and validation_state == "passed"
        and has_offset
        and not allow_integrator_feed
        and requires_manual_enable
    )
    summary = {
        "profile_id": profile_id,
        "path": str(path),
        "status": status,
        "enabled": bool(profile.get("enabled", False)),
        "device_model": device_model or None,
        "mount_name": _nested_string(profile, "mount", "name"),
        "sensor_primary": _nested_string(profile, "sensor", "primary"),
        "reference": profile.get("reference", {}),
        "axis_mapping_confidence": _nested_string(
            profile,
            "axis_mapping",
            "confidence",
        ),
        "offset": {
            "representation": offset.get("representation"),
            "q_phone_to_tube": q_phone_to_tube if has_offset else None,
            "yaw_deg": offset.get("yaw_deg"),
            "pitch_deg": offset.get("pitch_deg"),
            "roll_deg": offset.get("roll_deg"),
        },
        "validation": {
            "state": validation_state,
            "max_repeat_error_deg": validation.get("max_repeat_error_deg"),
            "median_repeat_error_deg": validation.get("median_repeat_error_deg"),
            "warnings": validation.get("warnings") or [],
        },
        "runtime": {
            "allow_integrator_feed": False,
            "allow_guidance_overlay": allow_guidance_overlay,
            "requires_manual_enable": requires_manual_enable,
        },
        "safety": {
            "integrator_blocked": True,
            "runtime_usable": False,
            "overlay_candidate": overlay_candidate,
            "read_only": True,
        },
    }
    return summary, sorted(set(warnings))


def _string_value(payload: Dict[str, Any], field: str) -> Optional[str]:
    value = payload.get(field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _nested_string(
    payload: Dict[str, Any],
    parent: str,
    child: str,
) -> Optional[str]:
    nested = payload.get(parent)
    if not isinstance(nested, dict):
        return None
    value = nested.get(child)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _number_field(payload: Dict[str, Any], field: str) -> Tuple[float, Optional[str]]:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0, f"{field} must be a number."
    return float(value), None


def _optional_number_field(
    payload: Dict[str, Any],
    field: str,
) -> Tuple[Optional[float], Optional[str]]:
    if field not in payload or payload[field] is None:
        return None, None
    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"{field} must be a number."
    return float(value), None


def _validate_imu_sample(
    sample: Dict[str, Any],
    index: int,
) -> Tuple[Dict[str, Any], Optional[str]]:
    sensor = sample.get("sensor")
    if not isinstance(sensor, str) or not sensor.strip():
        return {}, f"samples[{index}].sensor must be a non-empty string."

    t_android_ns, time_error = _number_field(sample, "t_android_ns")
    if time_error:
        return {}, f"samples[{index}].{time_error}"
    if t_android_ns < 0:
        return {}, f"samples[{index}].t_android_ns must be zero or greater."

    values = sample.get("values")
    if not isinstance(values, list) or not 3 <= len(values) <= 5:
        return {}, f"samples[{index}].values must contain 3 to 5 numbers."
    normalized_values = []
    for value_index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return {}, (
                f"samples[{index}].values[{value_index}] must be a number."
            )
        normalized_values.append(float(value))

    normalized = {
        "sensor": sensor,
        "t_android_ns": int(t_android_ns),
        "values": normalized_values,
    }
    if "accuracy" in sample:
        normalized["accuracy"] = sample["accuracy"]
    if "time_utc" in sample:
        normalized["time_utc"] = sample["time_utc"]
    return normalized, None
