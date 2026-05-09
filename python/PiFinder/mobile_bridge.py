#!/usr/bin/python
# -*- coding:utf-8 -*-
"""Helpers for the optional PiFinder Mobile Bridge API."""

import json
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
PROFILE_LATEST_FILENAME = "profile_latest.json"
GPS_LATEST_FILENAME = "gps_latest.json"
IMU_LATEST_FILENAME = "imu_latest.json"
MOUNT_PROFILES_DIRNAME = "mount_profiles"
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
MOUNT_PROFILE_SCHEMA = "pifinder-mobile-mount-profile-v0"
CAMERA_SOLVE_FRAME_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,96}$")
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


def error_payload(code: str, message: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "api": API_VERSION,
        "error": {
            "code": code,
            "message": message,
        },
    }


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
    solve_timeout_ms: int = 1000,
    preprocess_modes: Optional[List[str]] = None,
    force_attempt: bool = False,
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
            "score": None,
            "solve": {
                "attempted": False,
                "solve_ok": False,
                "skipped_reason": "quality_score_error",
                "error": f"{exc.__class__.__name__}: {exc}",
            },
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
            "score": score_payload,
            "solve": {
                "attempted": False,
                "solve_ok": False,
                "skipped_reason": "quality_score_rejected",
                "rejection_reasons": score.rejection_reasons,
            },
            "elapsed_ms": _elapsed_ms(start_time),
        }
        return _with_diagnostic_report(_with_diagnostic_summary(payload), reports_dir)

    solve_payload = _attempt_diagnostic_solve(
        frame_path=frame_path,
        score=score,
        solve_timeout_ms=solve_timeout_ms,
        preprocess_modes=preprocess_modes or ["baseline", "background_subtract"],
    )
    payload = {
        "ok": True,
        "api": API_VERSION,
        "frame_id": frame_id,
        "diagnostic_only": True,
        "integrator_updated": False,
        "runtime_pointing_updated": False,
        "metadata": metadata,
        "score": score_payload,
        "solve": solve_payload,
        "elapsed_ms": _elapsed_ms(start_time),
    }
    return _with_diagnostic_report(_with_diagnostic_summary(payload), reports_dir)


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
    source = payload.get("source")
    if not isinstance(source, str) or not source.strip():
        return {}, "source must be a non-empty string."

    normalized = {
        "lat": lat,
        "lon": lon,
        "altitude_m": altitude_m,
        "accuracy_m": accuracy_m,
        "time_utc": time_utc,
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
    time_utc = str(gps_fix["time_utc"]).strip()
    if time_utc.endswith("Z"):
        time_utc = time_utc[:-1] + "+00:00"
    gps_time = datetime.fromisoformat(time_utc)
    if gps_time.tzinfo is None:
        gps_time = gps_time.replace(tzinfo=timezone.utc)
    return gps_time.astimezone(timezone.utc)


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
            "imu": "implemented_debug_only",
            "camera_frame": "implemented_storage_only",
            "camera_solve": "implemented_diagnostic_only",
            "mount_profile": "implemented_read_only",
        },
    }


def _elapsed_ms(start_time: float) -> int:
    return int((time.perf_counter() - start_time) * 1000)


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


def _with_diagnostic_report(
    payload: Dict[str, Any],
    reports_dir: Optional[Path],
) -> Dict[str, Any]:
    report_info = _write_diagnostic_report(payload, reports_dir)
    payload["report"] = report_info
    return payload


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
