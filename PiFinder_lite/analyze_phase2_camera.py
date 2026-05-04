"""Analyze Phase 2 Camera Lab captures and try Tetra3 solving.

This script is intentionally outside the PiFinder core. It reads the Android
Camera Lab output folder, scores JPG frames, tries Tetra3 plate solving on the
best candidates, and writes reproducible CSV/Markdown results.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageFilter, ImageStat


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
TETRA3_PACKAGE_PARENT = PYTHON_DIR / "PiFinder" / "tetra3"
TETRA3_DB = TETRA3_PACKAGE_PARENT / "tetra3" / "data" / "default_database.npz"

sys.path.insert(0, str(TETRA3_PACKAGE_PARENT))
import tetra3  # noqa: E402


@dataclass
class FrameMetrics:
    path: Path
    block: str
    run: str
    test: str
    iso_label: str
    width: int
    height: int
    mean: float
    p95: float
    p99: float
    saturation_pct: float
    dark_pct: float
    sharpness: float
    bright_points: int
    centroids: int
    quality_score: float
    solve_ok: bool = False
    solve_ra: float | None = None
    solve_dec: float | None = None
    solve_fov: float | None = None
    solve_roll: float | None = None
    solve_matches: int | None = None
    solve_time_ms: float | None = None
    solve_mode: str = ""
    solve_error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(REPO_ROOT / "Test cam"))
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "PiFinder_lite" / "phase2_camera_analysis"),
    )
    parser.add_argument("--max-solve", type=int, default=36)
    return parser.parse_args()


def parse_metadata(run_dir: Path) -> dict[str, str]:
    metadata_files = list(run_dir.glob("*_metadata.txt"))
    if not metadata_files:
        return {}
    metadata: dict[str, str] = {}
    for line in metadata_files[0].read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def fov_from_metadata(metadata: dict[str, str]) -> float | None:
    focal_text = metadata.get("focalLengthsMm", "")
    sensor_text = metadata.get("sensorPhysicalSizeMm", "")
    focal_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", focal_text)
    sensor_match = re.search(r"([0-9]+(?:\.[0-9]+)?)x", sensor_text)
    if not focal_match or not sensor_match:
        return None
    focal_mm = float(focal_match.group(1))
    sensor_width_mm = float(sensor_match.group(1))
    if focal_mm <= 0:
        return None
    return math.degrees(2 * math.atan(sensor_width_mm / (2 * focal_mm)))


def iter_jpgs(root: Path) -> Iterable[tuple[Path, dict[str, str]]]:
    for run_dir in sorted(path for path in root.rglob("*") if path.is_dir()):
        jpgs = sorted(run_dir.glob("*.jpg"))
        if not jpgs:
            continue
        metadata = parse_metadata(run_dir)
        for jpg in jpgs:
            yield jpg, metadata


def iso_label(path: Path) -> str:
    match = re.search(r"iso([0-9]+)", path.name, flags=re.IGNORECASE)
    return match.group(0).lower() if match else ""


def block_name(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).parts[0]
    except Exception:
        return ""


def downscaled_luma(path: Path, max_side: int = 900) -> tuple[Image.Image, np.ndarray]:
    with Image.open(path) as image:
        gray = image.convert("L")
        gray.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        arr = np.asarray(gray, dtype=np.float32)
        return gray.copy(), arr


def approximate_bright_points(arr: np.ndarray) -> int:
    if arr.size == 0:
        return 0
    threshold = max(float(np.percentile(arr, 99.85)), float(arr.mean() + 4.0 * arr.std()))
    mask = arr >= threshold
    if not mask.any():
        return 0
    # Cheap connected-component approximation without scipy/cv2.
    visited = np.zeros(mask.shape, dtype=bool)
    count = 0
    height, width = mask.shape
    ys, xs = np.nonzero(mask)
    for start_y, start_x in zip(ys, xs):
        if visited[start_y, start_x] or not mask[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        area = 0
        while stack:
            y, x = stack.pop()
            area += 1
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    if not visited[ny, nx] and mask[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
        if 1 <= area <= 80:
            count += 1
    return count


def quality_metrics(path: Path, root: Path, metadata: dict[str, str]) -> FrameMetrics:
    gray, arr = downscaled_luma(path)
    stat = ImageStat.Stat(gray)
    mean = float(stat.mean[0])
    percentiles = np.percentile(arr, [95, 99])
    saturation_pct = float(np.mean(arr >= 252) * 100)
    dark_pct = float(np.mean(arr <= 3) * 100)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    sharpness = float(ImageStat.Stat(edges).var[0])
    bright_points = approximate_bright_points(arr)
    centroids = 0
    try:
        centroids = len(
            tetra3.get_centroids_from_image(
                gray,
                sigma=2,
                filtsize=25,
                max_area=120,
                min_area=2,
                max_returned=80,
            )
        )
    except Exception:
        centroids = 0
    score = (
        min(centroids, 60) * 2.5
        + min(bright_points, 80) * 1.0
        + min(sharpness / 10.0, 40)
        - saturation_pct * 5
        - max(0.0, dark_pct - 70) * 0.8
    )
    return FrameMetrics(
        path=path,
        block=block_name(path, root),
        run=path.parent.name,
        test=metadata.get("test", ""),
        iso_label=iso_label(path),
        width=Image.open(path).size[0],
        height=Image.open(path).size[1],
        mean=mean,
        p95=float(percentiles[0]),
        p99=float(percentiles[1]),
        saturation_pct=saturation_pct,
        dark_pct=dark_pct,
        sharpness=sharpness,
        bright_points=bright_points,
        centroids=centroids,
        quality_score=score,
    )


def solve_frame(
    t3: tetra3.Tetra3,
    frame: FrameMetrics,
    metadata_by_run: dict[str, dict[str, str]],
) -> None:
    metadata = metadata_by_run.get(frame.run, {})
    fov = fov_from_metadata(metadata)
    modes: list[tuple[str, dict[str, float | int | bool | None]]] = []
    if fov is not None:
        modes.append(
            (
                f"metadata_fov_{fov:.1f}",
                {
                    "fov_estimate": fov,
                    "fov_max_error": max(8.0, fov * 0.25),
                    "match_max_error": 0.01,
                },
            )
        )
    modes.append(
        (
            "free_fov",
            {
                "fov_estimate": None,
                "fov_max_error": None,
                "match_max_error": 0.01,
            },
        )
    )
    with Image.open(frame.path) as image:
        gray = image.convert("L")
        gray.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        for mode_name, kwargs in modes:
            try:
                t0 = time.perf_counter()
                result = t3.solve_from_image(
                    gray,
                    solve_timeout=5000,
                    return_matches=True,
                    pattern_checking_stars=12,
                    **kwargs,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                if result and result.get("RA") is not None:
                    frame.solve_ok = True
                    frame.solve_ra = float(result.get("RA"))
                    frame.solve_dec = float(result.get("Dec"))
                    frame.solve_fov = float(result.get("FOV"))
                    frame.solve_roll = float(result.get("Roll"))
                    frame.solve_matches = int(result.get("Matches", 0))
                    frame.solve_time_ms = elapsed_ms
                    frame.solve_mode = mode_name
                    return
                frame.solve_time_ms = elapsed_ms
                frame.solve_mode = mode_name
            except Exception as exc:
                frame.solve_error = f"{exc.__class__.__name__}: {exc}"


def write_csv(path: Path, frames: list[FrameMetrics]) -> None:
    fields = list(FrameMetrics.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for frame in frames:
            row = {field: getattr(frame, field) for field in fields}
            row["path"] = str(frame.path)
            writer.writerow(row)


def write_markdown(path: Path, frames: list[FrameMetrics], solved: list[FrameMetrics]) -> None:
    by_test: dict[str, list[FrameMetrics]] = {}
    for frame in frames:
        by_test.setdefault(frame.test or "unknown", []).append(frame)
    lines = [
        "# Phase 2 Camera Lab Analysis",
        "",
        "Input: `Test cam`",
        "",
        "## Summary",
        "",
        f"- JPG frames analyzed: {len(frames)}",
        f"- Frames attempted with Tetra3: {sum(1 for f in frames if f.solve_mode)}",
        f"- Successful solves: {len(solved)}",
        "",
    ]
    if solved:
        lines += [
            "## Successful Solves",
            "",
            "| block | test | file | mode | matches | fov | solve ms |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
        for frame in solved:
            lines.append(
                f"| {frame.block} | {frame.test} | `{frame.path.name}` | {frame.solve_mode} | "
                f"{frame.solve_matches} | {frame.solve_fov:.2f} | {frame.solve_time_ms:.0f} |"
            )
        lines.append("")
    lines += [
        "## Best Quality Candidates",
        "",
        "| rank | block | test | file | ISO | centroids | bright pts | mean | sat % | score | solved |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for idx, frame in enumerate(sorted(frames, key=lambda f: f.quality_score, reverse=True)[:30], 1):
        lines.append(
            f"| {idx} | {frame.block} | {frame.test} | `{frame.path.name}` | {frame.iso_label} | "
            f"{frame.centroids} | {frame.bright_points} | {frame.mean:.1f} | "
            f"{frame.saturation_pct:.2f} | {frame.quality_score:.1f} | "
            f"{'yes' if frame.solve_ok else 'no'} |"
        )
    lines += ["", "## Per-Test Counts", ""]
    lines += ["| test | frames | best score | best centroids | solves |", "| --- | ---: | ---: | ---: | ---: |"]
    for test, test_frames in sorted(by_test.items()):
        lines.append(
            f"| {test} | {len(test_frames)} | "
            f"{max(f.quality_score for f in test_frames):.1f} | "
            f"{max(f.centroids for f in test_frames)} | "
            f"{sum(1 for f in test_frames if f.solve_ok)} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- A successful Tetra3 solve is the strongest signal that the phone camera can work as a PiFinder image source.",
        "- If no frames solve, the supporting metrics indicate whether the blocker is likely cloud cover, motion/blur, low star count, or field-of-view/database mismatch.",
        "- These results are from handheld captures under partly cloudy conditions, so a failed solve should be treated as a conservative first pass rather than a final rejection.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_by_run: dict[str, dict[str, str]] = {}
    frames: list[FrameMetrics] = []
    for jpg, metadata in iter_jpgs(root):
        metadata_by_run[jpg.parent.name] = metadata
        frames.append(quality_metrics(jpg, root, metadata))

    t3 = tetra3.Tetra3(str(TETRA3_DB))
    candidates = sorted(frames, key=lambda f: f.quality_score, reverse=True)[: args.max_solve]
    for candidate in candidates:
        solve_frame(t3, candidate, metadata_by_run)

    solved = [frame for frame in frames if frame.solve_ok]
    write_csv(output_dir / "phase2_camera_analysis.csv", frames)
    write_markdown(output_dir / "phase2_camera_analysis.md", frames, solved)
    print(f"Analyzed {len(frames)} JPG frames")
    print(f"Attempted solve on {len(candidates)} candidates")
    print(f"Successful solves: {len(solved)}")
    print(output_dir / "phase2_camera_analysis.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
