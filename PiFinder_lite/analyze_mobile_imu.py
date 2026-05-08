"""Analyze Android IMU batches before considering integrator use.

This helper reads the debug payload persisted by `/mobile/imu` and produces a
small confidence report. It intentionally does not feed PiFinder's integrator.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = Path.home() / "PiFinder_data" / "mobile" / "imu_latest.json"


@dataclass
class ImuSensorAnalysis:
    batch_label: str
    sensor: str
    sample_count: int
    duration_ms: float
    median_interval_ms: float | None
    max_interval_ms: float | None
    mean_step_deg: float | None
    max_step_deg: float | None
    total_motion_deg: float | None
    drift_deg_per_s: float | None
    min_accuracy: int | None
    max_accuracy: int | None
    confidence: str
    recommendation: str
    warnings: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to imu_latest.json or a raw IMU batch JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "PiFinder_lite" / "phase4_imu_analysis"),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def load_imu_batch(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "imu" in payload and isinstance(payload["imu"], dict):
        return payload["imu"]
    return payload


def grouped_samples(batch: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for sample in batch.get("samples", []):
        sensor = sample.get("sensor", "unknown")
        groups.setdefault(sensor, []).append(sample)
    for samples in groups.values():
        samples.sort(key=lambda sample: sample.get("t_android_ns", 0))
    return groups


def quaternion_from_rotation_vector(values: list[float]) -> tuple[float, float, float, float] | None:
    if len(values) < 3:
        return None
    x, y, z = float(values[0]), float(values[1]), float(values[2])
    if len(values) >= 4:
        w = float(values[3])
    else:
        remainder = 1.0 - x * x - y * y - z * z
        w = math.sqrt(max(0.0, remainder))
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if norm == 0:
        return None
    return (w / norm, x / norm, y / norm, z / norm)


def angular_distance_deg(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    dot = abs(sum(a * b for a, b in zip(first, second)))
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(2.0 * math.acos(dot))


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def analyze_sensor(
    sensor: str,
    samples: list[dict[str, Any]],
    batch_label: str = "diagnostic",
) -> ImuSensorAnalysis:
    warnings: list[str] = []
    times = [int(sample["t_android_ns"]) for sample in samples if "t_android_ns" in sample]
    duration_ms = 0.0
    intervals_ms: list[float] = []
    if len(times) >= 2:
        duration_ms = (times[-1] - times[0]) / 1_000_000.0
        intervals_ms = [
            (later - earlier) / 1_000_000.0
            for earlier, later in zip(times, times[1:])
            if later >= earlier
        ]

    quaternions = [
        quat
        for sample in samples
        for quat in [quaternion_from_rotation_vector(sample.get("values", []))]
        if quat is not None
    ]
    steps = [
        angular_distance_deg(first, second)
        for first, second in zip(quaternions, quaternions[1:])
    ]

    accuracies = [
        int(sample["accuracy"])
        for sample in samples
        if isinstance(sample.get("accuracy"), int)
    ]
    min_accuracy = min(accuracies) if accuracies else None
    max_accuracy = max(accuracies) if accuracies else None
    median_interval_ms = median(intervals_ms)
    max_interval_ms = max(intervals_ms) if intervals_ms else None
    mean_step_deg = sum(steps) / len(steps) if steps else None
    max_step_deg = max(steps) if steps else None
    total_motion_deg = sum(steps) if steps else None
    duration_s = duration_ms / 1000.0
    drift_deg_per_s = (
        total_motion_deg / duration_s
        if total_motion_deg is not None and duration_s > 0
        else None
    )

    if len(samples) < 8:
        warnings.append("too_few_samples")
    if duration_ms < 500:
        warnings.append("short_capture")
    if max_interval_ms is not None and max_interval_ms > 350:
        warnings.append("sample_gap")
    if max_step_deg is not None and max_step_deg > 20:
        warnings.append("orientation_jump")
    if min_accuracy is not None and min_accuracy <= 0:
        warnings.append("unreliable_accuracy")
    if sensor == "rotation_vector" and min_accuracy is not None and min_accuracy < 2:
        warnings.append("possible_magnetometer_low_confidence")

    if warnings:
        confidence = "LOW" if {"orientation_jump", "too_few_samples"}.intersection(warnings) else "MEDIUM"
    elif drift_deg_per_s is not None and drift_deg_per_s <= 4:
        confidence = "HIGH"
    else:
        confidence = "MEDIUM"

    if confidence == "HIGH":
        recommendation = "candidate_for_mount_calibration_tests"
    elif confidence == "MEDIUM":
        recommendation = "collect_more_stationary_and_motion_batches"
    else:
        recommendation = "do_not_use_for_integrator_yet"

    return ImuSensorAnalysis(
        batch_label=batch_label,
        sensor=sensor,
        sample_count=len(samples),
        duration_ms=round(duration_ms, 3),
        median_interval_ms=round(median_interval_ms, 3) if median_interval_ms is not None else None,
        max_interval_ms=round(max_interval_ms, 3) if max_interval_ms is not None else None,
        mean_step_deg=round(mean_step_deg, 4) if mean_step_deg is not None else None,
        max_step_deg=round(max_step_deg, 4) if max_step_deg is not None else None,
        total_motion_deg=round(total_motion_deg, 4) if total_motion_deg is not None else None,
        drift_deg_per_s=round(drift_deg_per_s, 4) if drift_deg_per_s is not None else None,
        min_accuracy=min_accuracy,
        max_accuracy=max_accuracy,
        confidence=confidence,
        recommendation=recommendation,
        warnings=warnings,
    )


def analyze_batch(batch: dict[str, Any]) -> list[ImuSensorAnalysis]:
    batch_label = str(batch.get("batch_label") or "diagnostic")
    return [
        analyze_sensor(sensor, samples, batch_label=batch_label)
        for sensor, samples in sorted(grouped_samples(batch).items())
    ]


def write_csv(path: Path, analyses: Iterable[ImuSensorAnalysis]) -> None:
    fields = list(ImuSensorAnalysis.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for analysis in analyses:
            row = asdict(analysis)
            row["warnings"] = ";".join(analysis.warnings)
            writer.writerow(row)


def write_markdown(path: Path, analyses: list[ImuSensorAnalysis]) -> None:
    lines = [
        "# Mobile IMU Confidence Analysis",
        "",
        "This report analyzes Android rotation-vector batches before any PiFinder integrator use.",
        "",
        "## Summary",
        "",
        f"- Sensors analyzed: {len(analyses)}",
        "",
        "| batch label | sensor | samples | duration ms | confidence | max step deg | drift deg/s | warnings | recommendation |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | --- | --- |",
    ]
    for analysis in analyses:
        lines.append(
            f"| {analysis.batch_label} | {analysis.sensor} | {analysis.sample_count} | {analysis.duration_ms:.1f} | "
            f"{analysis.confidence} | {analysis.max_step_deg if analysis.max_step_deg is not None else ''} | "
            f"{analysis.drift_deg_per_s if analysis.drift_deg_per_s is not None else ''} | "
            f"{', '.join(analysis.warnings) or 'none'} | {analysis.recommendation} |"
        )
    lines += [
        "",
        "## Guardrails",
        "",
        "- This helper does not feed PiFinder's integrator.",
        "- Android IMU coordinates are device-relative until a mobile-to-telescope calibration exists.",
        "- Run at least one stationary batch and one gentle-motion batch before trusting the recommendation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    analyses = analyze_batch(load_imu_batch(input_path))

    json_path = output_dir / "mobile_imu_confidence.json"
    csv_path = output_dir / "mobile_imu_confidence.csv"
    markdown_path = output_dir / "mobile_imu_confidence.md"
    json_path.write_text(
        json.dumps([asdict(analysis) for analysis in analyses], indent=2),
        encoding="utf-8",
    )
    write_csv(csv_path, analyses)
    write_markdown(markdown_path, analyses)

    if args.json:
        print(json.dumps([asdict(analysis) for analysis in analyses], indent=2))
    else:
        print(f"Analyzed {len(analyses)} IMU sensor groups")
        print(markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
