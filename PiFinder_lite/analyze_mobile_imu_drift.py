"""Analyze solve-to-solve mobile IMU residuals.

This helper is diagnostic-only. It compares where the phone IMU predicted the
telescope would end a movement against the next plate-solve confirmed position.
It does not feed PiFinder pointing state or the integrator.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "PiFinder_lite" / "phase5_imu_drift_analysis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON file with solve-to-solve cycles.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for JSON and Markdown reports.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def wrap_delta_deg(value: float) -> float:
    return (float(value) + 180.0) % 360.0 - 180.0


def mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def stddev(values: Iterable[float]) -> float:
    items = list(values)
    if len(items) < 2:
        return 0.0
    avg = mean(items)
    return math.sqrt(sum((item - avg) ** 2 for item in items) / len(items))


def _point(cycle: dict[str, Any], key: str) -> dict[str, float]:
    point = cycle.get(key)
    if not isinstance(point, dict):
        raise ValueError(f"{key} must be an object.")
    return {
        "alt_deg": float(point["alt_deg"]),
        "az_deg": float(point["az_deg"]),
    }


def _cycle_result(cycle: dict[str, Any], index: int) -> dict[str, Any]:
    predicted = _point(cycle, "predicted_final")
    solved = _point(cycle, "solve_final")
    residual_alt = wrap_delta_deg(solved["alt_deg"] - predicted["alt_deg"])
    residual_az = wrap_delta_deg(solved["az_deg"] - predicted["az_deg"])
    # Azimuth residuals are not metric on the sphere: a given delta-az subtends a
    # smaller on-sky angle near the zenith. Weight by cos(mean altitude) so
    # error_deg is the true angular separation (same cos(dec) convention the
    # optical boresight offset uses). residual_az_deg below stays raw for trace.
    mean_alt_rad = math.radians((solved["alt_deg"] + predicted["alt_deg"]) / 2.0)
    error_deg = math.hypot(residual_alt, residual_az * math.cos(mean_alt_rad))
    duration_s = max(0.0, float(cycle.get("duration_s") or 0.0))
    drift_deg_per_min = (error_deg / duration_s * 60.0) if duration_s > 0 else None
    return {
        "cycle_id": str(cycle.get("cycle_id") or f"cycle_{index + 1}"),
        "remount_id": str(cycle.get("remount_id") or "default"),
        "duration_s": round(duration_s, 3),
        "predicted_final": predicted,
        "solve_final": solved,
        "residual_alt_deg": round(residual_alt, 4),
        "residual_az_deg": round(residual_az, 4),
        "error_deg": round(error_deg, 4),
        "drift_deg_per_min": round(drift_deg_per_min, 4) if drift_deg_per_min is not None else None,
    }


def _remount_shift(cycles: list[dict[str, Any]]) -> float:
    groups: dict[str, list[dict[str, Any]]] = {}
    for cycle in cycles:
        groups.setdefault(cycle["remount_id"], []).append(cycle)
    if len(groups) < 2:
        return 0.0
    centroids = []
    for group_cycles in groups.values():
        centroids.append(
            (
                mean(cycle["residual_alt_deg"] for cycle in group_cycles),
                mean(cycle["residual_az_deg"] for cycle in group_cycles),
            )
        )
    max_shift = 0.0
    for left_index, left in enumerate(centroids):
        for right in centroids[left_index + 1 :]:
            max_shift = max(max_shift, math.hypot(left[0] - right[0], left[1] - right[1]))
    return max_shift


def _verdict(
    cycle_count: int,
    mean_error_deg: float,
    max_error_deg: float,
    residual_std_deg: float,
    remount_shift_deg: float,
) -> tuple[str, str, list[str], str]:
    warnings: list[str] = []
    if cycle_count < 3:
        warnings.append("too_few_cycles")
        return "needs_more_data", "LOW", warnings, "repeat_solve_to_solve_cycles"
    if remount_shift_deg > 3.0:
        warnings.append("remount_shift")
        return "unstable_mount", "LOW", warnings, "recalibrate_or_remount_phone"
    if max_error_deg > 12.0 or residual_std_deg > 6.0:
        warnings.append("residuals_not_repeatable")
        return "imu_not_reliable", "LOW", warnings, "keep_read_only_and_collect_better_cycles"
    if mean_error_deg <= 2.0 and max_error_deg <= 4.0 and residual_std_deg <= 1.5:
        return "pattern_found", "MEDIUM", warnings, "candidate_for_future_correction_profile"
    warnings.append("weak_or_partial_pattern")
    return "inconclusive", "LOW", warnings, "collect_more_cycles_before_correction_profile"


def analyze_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cycles_input = payload.get("cycles")
    if not isinstance(cycles_input, list):
        raise ValueError("cycles must be a list.")
    cycles = [_cycle_result(cycle, index) for index, cycle in enumerate(cycles_input)]
    errors = [cycle["error_deg"] for cycle in cycles]
    residual_alt_values = [cycle["residual_alt_deg"] for cycle in cycles]
    residual_az_values = [cycle["residual_az_deg"] for cycle in cycles]
    mean_error_deg = mean(errors)
    max_error_deg = max(errors) if errors else 0.0
    residual_std_deg = math.hypot(stddev(residual_alt_values), stddev(residual_az_values))
    remount_shift_deg = _remount_shift(cycles)
    verdict, confidence, warnings, recommendation = _verdict(
        len(cycles),
        mean_error_deg,
        max_error_deg,
        residual_std_deg,
        remount_shift_deg,
    )
    alt_bias = mean(residual_alt_values)
    az_bias = mean(residual_az_values)
    drift_values = [
        cycle["drift_deg_per_min"]
        for cycle in cycles
        if cycle.get("drift_deg_per_min") is not None
    ]
    return {
        "ok": True,
        "schema": "pifinder-mobile-ai-imu-drift-analysis-v0",
        "diagnostic_only": True,
        "integrator_updated": False,
        "runtime_pointing_updated": False,
        "cycle_count": len(cycles),
        "cycles": cycles,
        "mean_error_deg": round(mean_error_deg, 4),
        "max_error_deg": round(max_error_deg, 4),
        "residual_std_deg": round(residual_std_deg, 4),
        "estimated_drift_deg_per_min": round(mean(drift_values), 4) if drift_values else None,
        "remount_shift_deg": round(remount_shift_deg, 4),
        "suggested_correction": {
            "status": "diagnostic_only",
            "alt_bias_deg": round(alt_bias, 4),
            "az_bias_deg": round(az_bias, 4),
            "apply_to_pointing": False,
        },
        "confidence": confidence,
        "verdict": verdict,
        "warnings": warnings,
        "recommendation": recommendation,
    }


def write_reports(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "ai_imu_drift_analysis.json"
    markdown_path = output_dir / "ai_imu_drift_analysis.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# AI IMU Drift Analysis",
        "",
        f"- Verdict: `{report['verdict']}`",
        f"- Confidence: `{report['confidence']}`",
        f"- Cycles: `{report['cycle_count']}`",
        f"- Mean error deg: `{report['mean_error_deg']}`",
        f"- Max error deg: `{report['max_error_deg']}`",
        f"- Remount shift deg: `{report['remount_shift_deg']}`",
        f"- Recommendation: `{report['recommendation']}`",
        "",
        "Diagnostic-only. Do not feed this correction into pointing or the integrator.",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = analyze_payload(payload)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        json_path, markdown_path = write_reports(report, Path(args.output_dir))
        print(f"Wrote AI IMU drift report: {json_path}")
        print(f"Wrote AI IMU drift summary: {markdown_path}")
        print(f"Verdict: {report['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
