"""Compute a diagnostic phone-to-telescope mount offset.

This helper consumes a labeled Android IMU batch plus a known reference tube
orientation and writes a candidate mobile mount profile. It intentionally does
not feed PiFinder's runtime integrator.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PiFinder_lite import analyze_mobile_imu
except ImportError:  # pragma: no cover - supports direct script execution
    import analyze_mobile_imu  # type: ignore


DEFAULT_INPUT = Path.home() / "PiFinder_data" / "mobile" / "imu_latest.json"
DEFAULT_OUTPUT_DIR = Path.home() / "PiFinder_data" / "mobile" / "mount_profiles"
MINIMUM_SAMPLE_COUNT = 50
MINIMUM_BATCH_DURATION_MS = 1500.0

Quat = tuple[float, float, float, float]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--imu-batch",
        default=str(DEFAULT_INPUT),
        help="Path to imu_latest.json or a raw IMU batch JSON file.",
    )
    parser.add_argument(
        "--reference",
        required=True,
        help="Reference JSON containing q_tube_reference as [w, x, y, z].",
    )
    parser.add_argument(
        "--sensor",
        default="game_rotation_vector",
        help="Sensor group to use from the IMU batch.",
    )
    parser.add_argument(
        "--mount-name",
        default="mobile-phone-tube-mount",
        help="Human-readable mount name for the generated profile.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output profile path. Defaults to ~/PiFinder_data/mobile/mount_profiles/...",
    )
    parser.add_argument("--json", action="store_true", help="Print profile JSON to stdout.")
    return parser.parse_args(argv)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_quaternion(values: list[float] | tuple[float, ...]) -> Quat | None:
    if len(values) != 4:
        return None
    w, x, y, z = (float(value) for value in values)
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if norm == 0:
        return None
    return (w / norm, x / norm, y / norm, z / norm)


def quaternion_inverse(quat: Quat) -> Quat:
    w, x, y, z = quat
    return (w, -x, -y, -z)


def quaternion_multiply(first: Quat, second: Quat) -> Quat:
    aw, ax, ay, az = first
    bw, bx, by, bz = second
    return normalize_quaternion(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ]
    ) or (1.0, 0.0, 0.0, 0.0)


def average_quaternion(quaternions: list[Quat]) -> Quat | None:
    if not quaternions:
        return None
    base = quaternions[0]
    sums = [0.0, 0.0, 0.0, 0.0]
    for quat in quaternions:
        aligned = quat
        if sum(a * b for a, b in zip(base, quat)) < 0:
            aligned = tuple(-value for value in quat)  # type: ignore[assignment]
        for index, value in enumerate(aligned):
            sums[index] += value
    return normalize_quaternion(tuple(sums))


def quaternion_to_yaw_pitch_roll_deg(quat: Quat) -> tuple[float, float, float]:
    w, x, y, z = quat

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)

    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    return (
        round(math.degrees(yaw), 6),
        round(math.degrees(pitch), 6),
        round(math.degrees(roll), 6),
    )


def rounded_quaternion(quat: Quat) -> list[float]:
    return [round(value, 6) for value in quat]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def selected_sensor_samples(batch: dict[str, Any], sensor: str) -> list[dict[str, Any]]:
    return analyze_mobile_imu.grouped_samples(batch).get(sensor, [])


def reference_quaternion(reference: dict[str, Any]) -> Quat | None:
    values = reference.get("q_tube_reference")
    if not isinstance(values, list):
        return None
    return normalize_quaternion(values)


def reference_block(reference: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": reference.get("type", "manual_target"),
        "target_name": reference.get("target_name"),
        "ra_hours": reference.get("ra_hours"),
        "dec_degrees": reference.get("dec_degrees"),
        "alt_degrees": reference.get("alt_degrees"),
        "az_degrees": reference.get("az_degrees"),
        "source": reference.get("source", "manual_or_pifinder_solve"),
        "q_tube_reference": reference.get("q_tube_reference"),
    }


def confidence_warnings(
    batch: dict[str, Any],
    analysis: analyze_mobile_imu.ImuSensorAnalysis | None,
    phone_quaternion: Quat | None,
    tube_quaternion: Quat | None,
) -> list[str]:
    warnings: list[str] = []
    if batch.get("batch_label") != "mounted_reference":
        warnings.append("batch_label_not_mounted_reference")
    if analysis is None or analysis.sample_count < MINIMUM_SAMPLE_COUNT:
        warnings.append("insufficient_samples")
    if analysis is None or analysis.duration_ms < MINIMUM_BATCH_DURATION_MS:
        warnings.append("batch_too_short")
    if analysis and "orientation_jump" in analysis.warnings:
        warnings.append("sensor_jump_detected")
    if phone_quaternion is None:
        warnings.append("no_valid_phone_quaternion")
    if tube_quaternion is None:
        warnings.append("missing_reference_quaternion")
    warnings.append("do_not_use_for_runtime_guidance")
    return warnings


def profile_status_from_warnings(warnings: list[str]) -> tuple[str, str, str]:
    blockers = {
        "insufficient_samples",
        "batch_too_short",
        "sensor_jump_detected",
        "no_valid_phone_quaternion",
        "missing_reference_quaternion",
    }
    if blockers.intersection(warnings):
        return "uncalibrated", "failed", "LOW"
    return "candidate", "repeatability_pending", "MEDIUM"


def compute_candidate_profile(
    imu_payload: dict[str, Any],
    reference: dict[str, Any],
    *,
    sensor: str = "game_rotation_vector",
    mount_name: str = "mobile-phone-tube-mount",
) -> dict[str, Any]:
    batch = imu_payload.get("imu") if isinstance(imu_payload.get("imu"), dict) else imu_payload
    samples = selected_sensor_samples(batch, sensor)
    analysis = (
        analyze_mobile_imu.analyze_sensor(
            sensor,
            samples,
            batch.get("batch_label", "diagnostic"),
        )
        if samples
        else None
    )
    phone_quaternion = average_quaternion(
        [
            quat
            for sample in samples
            for quat in [analyze_mobile_imu.quaternion_from_rotation_vector(sample.get("values", []))]
            if quat is not None
        ]
    )
    tube_quaternion = reference_quaternion(reference)
    warnings = confidence_warnings(batch, analysis, phone_quaternion, tube_quaternion)
    status, validation_state, axis_confidence = profile_status_from_warnings(warnings)
    if phone_quaternion is not None and tube_quaternion is not None:
        offset = quaternion_multiply(tube_quaternion, quaternion_inverse(phone_quaternion))
    else:
        offset = (1.0, 0.0, 0.0, 0.0)
    yaw, pitch, roll = quaternion_to_yaw_pitch_roll_deg(offset)
    now = utc_now_iso()
    device = batch.get("device", {}) if isinstance(batch.get("device"), dict) else {}
    if "app_version" in batch and "app_version" not in device:
        device = {**device, "app_version": batch["app_version"]}

    return {
        "schema": "pifinder-mobile-mount-profile-v0",
        "profile_id": f"candidate-{now.replace(':', '').replace('-', '')}",
        "status": status,
        "enabled": False,
        "created_utc": now,
        "updated_utc": now,
        "device": device,
        "mount": {
            "name": mount_name,
            "attachment": "rigid_clamp",
            "phone_side": "unknown",
            "screen_orientation": batch.get("screen_orientation", "unknown"),
            "notes": "Generated by diagnostic offset tool; validate repeatability before use.",
        },
        "sensor": {
            "primary": sensor,
            "comparison": "rotation_vector" if sensor != "rotation_vector" else "game_rotation_vector",
            "sample_rate_hz": None,
            "minimum_batch_duration_ms": MINIMUM_BATCH_DURATION_MS,
            "minimum_sample_count": MINIMUM_SAMPLE_COUNT,
        },
        "reference": reference_block(reference),
        "axis_mapping": {
            "phone_forward": "unknown",
            "phone_up": "unknown",
            "tube_axis": "optical_axis",
            "confidence": axis_confidence,
        },
        "offset": {
            "representation": "quaternion",
            "q_phone_to_tube": rounded_quaternion(offset),
            "yaw_deg": yaw,
            "pitch_deg": pitch,
            "roll_deg": roll,
            "source_batch_id": batch.get("batch_id") or batch.get("device_time_utc"),
        },
        "validation": {
            "state": validation_state,
            "repeat_count": 0,
            "max_repeat_error_deg": None,
            "median_repeat_error_deg": None,
            "last_validated_utc": None,
            "warnings": warnings,
        },
        "runtime": {
            "allow_integrator_feed": False,
            "allow_guidance_overlay": False,
            "requires_manual_enable": True,
        },
    }


def default_output_path(profile: dict[str, Any]) -> Path:
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_OUTPUT_DIR / f"{profile['profile_id']}.json"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    imu_payload = load_json(Path(args.imu_batch))
    reference = load_json(Path(args.reference))
    profile = compute_candidate_profile(
        imu_payload,
        reference,
        sensor=args.sensor,
        mount_name=args.mount_name,
    )
    output_path = Path(args.output) if args.output else default_output_path(profile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(profile, indent=2))
    else:
        print(f"Wrote candidate mount profile: {output_path}")
        print(f"Status: {profile['status']} ({profile['validation']['state']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
