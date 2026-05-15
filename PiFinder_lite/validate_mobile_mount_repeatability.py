"""Validate repeatability of diagnostic mobile mount profiles.

This helper compares multiple candidate `q_phone_to_tube` offsets and produces a
conservative report before any live guidance or integrator work is considered.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Any

try:
    from PiFinder_lite.compute_mobile_mount_offset import normalize_quaternion
    from PiFinder_lite.analyze_mobile_imu import angular_distance_deg
except ImportError:  # pragma: no cover - supports direct script execution
    from compute_mobile_mount_offset import normalize_quaternion  # type: ignore
    from analyze_mobile_imu import angular_distance_deg  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "PiFinder_lite" / "phase5_repeatability_analysis"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Profile JSON file(s) or directories containing profile JSON files.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--pass-threshold-deg", type=float, default=1.0)
    parser.add_argument("--reject-threshold-deg", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", help="Print report JSON to stdout.")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def collect_profile_paths(inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.json")))
        else:
            paths.append(path)
    return paths


def profile_quaternion(profile: dict[str, Any]) -> tuple[float, float, float, float] | None:
    offset = profile.get("offset")
    if not isinstance(offset, dict):
        return None
    values = offset.get("q_phone_to_tube")
    if not isinstance(values, list):
        return None
    return normalize_quaternion(values)


def profile_warnings(profile: dict[str, Any]) -> list[str]:
    validation = profile.get("validation")
    if not isinstance(validation, dict):
        return []
    warnings = validation.get("warnings", [])
    if not isinstance(warnings, list):
        return []
    return [str(warning) for warning in warnings]


def pairwise_errors_deg(
    quaternions: list[tuple[float, float, float, float]],
) -> list[float]:
    errors: list[float] = []
    for index, first in enumerate(quaternions):
        for second in quaternions[index + 1 :]:
            errors.append(angular_distance_deg(first, second))
    return errors


def recommendation_from_errors(
    repeat_count: int,
    max_error_deg: float | None,
    warnings: list[str],
    pass_threshold_deg: float,
    reject_threshold_deg: float,
) -> tuple[str, str]:
    if repeat_count < 2:
        return "recalibrate", "repeatability_pending"
    if max_error_deg is None:
        return "reject", "failed"
    if "invalid_profile_offset" in warnings:
        return "reject", "failed"
    if max_error_deg >= reject_threshold_deg:
        return "reject", "failed"
    if max_error_deg <= pass_threshold_deg and not any(
        warning.startswith("source_profile_warning:sensor_jump_detected")
        for warning in warnings
    ):
        return "proceed", "passed"
    return "recalibrate", "repeatability_pending"


def validate_profiles(
    profile_paths: list[Path],
    *,
    pass_threshold_deg: float = 1.0,
    reject_threshold_deg: float = 5.0,
) -> dict[str, Any]:
    profile_entries: list[dict[str, Any]] = []
    quaternions: list[tuple[float, float, float, float]] = []
    warnings: list[str] = []

    for path in profile_paths:
        profile = load_json(path)
        quat = profile_quaternion(profile)
        profile_id = str(profile.get("profile_id") or path.stem)
        entry = {
            "profile_id": profile_id,
            "path": str(path),
            "status": profile.get("status"),
            "validation_state": (
                profile.get("validation", {}).get("state")
                if isinstance(profile.get("validation"), dict)
                else None
            ),
        }
        if quat is None:
            entry["valid_offset"] = False
            warnings.append("invalid_profile_offset")
        else:
            entry["valid_offset"] = True
            entry["q_phone_to_tube"] = [round(value, 6) for value in quat]
            quaternions.append(quat)
        for warning in profile_warnings(profile):
            if warning != "do_not_use_for_runtime_guidance":
                warnings.append(f"source_profile_warning:{warning}")
        profile_entries.append(entry)

    errors = pairwise_errors_deg(quaternions)
    max_error = max(errors) if errors else None
    median_error = median(errors) if errors else None
    if max_error is not None and max_error >= reject_threshold_deg:
        warnings.append("repeat_error_too_high")
    elif max_error is not None and max_error > pass_threshold_deg:
        warnings.append("repeat_error_questionable")
    if len(quaternions) < 2:
        warnings.append("need_at_least_two_repeat_profiles")

    deduped_warnings = sorted(set(warnings))
    recommendation, validation_state = recommendation_from_errors(
        len(quaternions),
        max_error,
        deduped_warnings,
        pass_threshold_deg,
        reject_threshold_deg,
    )

    return {
        "schema": "pifinder-mobile-mount-repeatability-report-v0",
        "repeat_count": len(quaternions),
        "profile_count": len(profile_entries),
        "pass_threshold_deg": pass_threshold_deg,
        "reject_threshold_deg": reject_threshold_deg,
        "max_repeat_error_deg": round(max_error, 6) if max_error is not None else None,
        "median_repeat_error_deg": round(median_error, 6) if median_error is not None else None,
        "recommendation": recommendation,
        "validation_state": validation_state,
        "warnings": deduped_warnings,
        "profiles": profile_entries,
        "field_notes": [
            "Indoor/cloudy tests can validate stability and tooling, not true sky alignment.",
            "Repeat real night captures after remounting before considering a profile usable.",
            "Do not enable runtime guidance from this report during Phase 5.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Mobile Mount Repeatability Report",
        "",
        "This report compares diagnostic phone-to-tube offset profiles before any runtime use.",
        "",
        "## Summary",
        "",
        f"- Recommendation: `{report['recommendation']}`",
        f"- Validation state: `{report['validation_state']}`",
        f"- Repeat profiles: {report['repeat_count']}",
        f"- Max repeat error deg: {report['max_repeat_error_deg']}",
        f"- Median repeat error deg: {report['median_repeat_error_deg']}",
        f"- Warnings: {', '.join(report['warnings']) or 'none'}",
        "",
        "## Profiles",
        "",
        "| profile | status | validation | valid offset |",
        "| --- | --- | --- | --- |",
    ]
    for profile in report["profiles"]:
        lines.append(
            f"| {profile['profile_id']} | {profile.get('status')} | "
            f"{profile.get('validation_state')} | {profile.get('valid_offset')} |"
        )
    lines += [
        "",
        "## Field Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in report["field_notes"])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = validate_profiles(
        collect_profile_paths(args.input),
        pass_threshold_deg=args.pass_threshold_deg,
        reject_threshold_deg=args.reject_threshold_deg,
    )
    json_path = output_dir / "mobile_mount_repeatability.json"
    markdown_path = output_dir / "mobile_mount_repeatability.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(markdown_path, report)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Wrote repeatability report: {markdown_path}")
        print(f"Recommendation: {report['recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
