#!/usr/bin/python
# -*- coding:utf-8 -*-
"""Helpers for the optional PiFinder Mobile Bridge API."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PiFinder import utils

API_VERSION = "mobile-bridge-v0"
MOBILE_DATA_DIR = utils.data_dir / "mobile"
PROFILE_LATEST_FILENAME = "profile_latest.json"
GPS_LATEST_FILENAME = "gps_latest.json"
IMU_LATEST_FILENAME = "imu_latest.json"
MAX_IMU_SAMPLES = 512


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
        "device_time_utc": payload.get("device_time_utc"),
        "sample_count": len(normalized_samples),
        "samples": normalized_samples,
        "coordinate_frame_note": (
            "Android sensor coordinate frames are device-relative. This debug "
            "payload is not aligned to the telescope optical axis."
        ),
    }
    if "device" in payload:
        normalized["device"] = payload["device"]
    return normalized, None


def imu_payload(imu_batch: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "received_utc": utc_now_iso(),
        "imu": imu_batch,
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
            "camera_frame": "deferred",
        },
    }


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
