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
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps, ImageStat


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
    solve_preprocess: str = ""
    solve_mode: str = ""
    solve_error: str = ""


@dataclass
class SolveAttempt:
    path: Path
    block: str
    test: str
    file: str
    candidate_rank: int
    preprocess_mode: str
    fov_mode: str
    ok: bool
    solve_ra: float | None = None
    solve_dec: float | None = None
    solve_fov: float | None = None
    solve_roll: float | None = None
    solve_matches: int | None = None
    solve_time_ms: float | None = None
    solve_error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(REPO_ROOT / "Test cam"))
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "PiFinder_lite" / "phase2_camera_analysis"),
    )
    parser.add_argument("--max-solve", type=int, default=30)
    parser.add_argument("--solve-timeout-ms", type=int, default=2500)
    parser.add_argument(
        "--preprocess-modes",
        default="baseline,percentile_stretch,background_subtract,denoise_stretch,center_crop",
        help="Comma-separated preprocessing modes, or 'all'.",
    )
    parser.add_argument(
        "--continue-after-solve",
        action="store_true",
        help="Try all preprocessing/FOV variants even after a candidate solves.",
    )
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


def percentile_stretch(gray: Image.Image, low: float = 1.0, high: float = 99.8) -> Image.Image:
    arr = np.asarray(gray, dtype=np.float32)
    lo, hi = np.percentile(arr, [low, high])
    if hi <= lo:
        return gray.copy()
    stretched = np.clip((arr - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
    return Image.fromarray(stretched, mode="L")


def background_subtract(gray: Image.Image) -> Image.Image:
    background = gray.filter(ImageFilter.MedianFilter(size=31))
    flattened = ImageChops.subtract(gray, background, scale=1.0, offset=18)
    return percentile_stretch(flattened, low=2.0, high=99.9)


def denoise_stretch(gray: Image.Image) -> Image.Image:
    denoised = gray.filter(ImageFilter.MedianFilter(size=3))
    stretched = percentile_stretch(denoised, low=1.0, high=99.7)
    return ImageEnhance.Contrast(stretched).enhance(1.35)


def center_crop(gray: Image.Image, fraction: float = 0.78) -> Image.Image:
    width, height = gray.size
    crop_width = max(1, int(width * fraction))
    crop_height = max(1, int(height * fraction))
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    return gray.crop((left, top, left + crop_width, top + crop_height))


def preprocessing_variants(gray: Image.Image, requested_modes: list[str]) -> list[tuple[str, Image.Image]]:
    available = {
        "baseline": lambda image: image.copy(),
        "autocontrast": ImageOps.autocontrast,
        "percentile_stretch": percentile_stretch,
        "background_subtract": background_subtract,
        "denoise_stretch": denoise_stretch,
        "center_crop": center_crop,
    }
    if requested_modes == ["all"]:
        requested_modes = list(available.keys())
    variants: list[tuple[str, Image.Image]] = []
    for mode in requested_modes:
        factory = available.get(mode)
        if factory is None:
            raise ValueError(f"Unknown preprocessing mode: {mode}")
        variants.append((mode, factory(gray)))
    return variants


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
        - max(0.0, 45.0 - dark_pct) * 2.4
        - max(0.0, mean - 5.0) * 12.0
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
    candidate_rank: int,
    preprocess_modes: list[str],
    solve_timeout_ms: int,
    continue_after_solve: bool,
) -> list[SolveAttempt]:
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
    attempts: list[SolveAttempt] = []
    with Image.open(frame.path) as image:
        gray = image.convert("L")
        gray.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        variants = preprocessing_variants(gray, preprocess_modes)
        for preprocess_name, processed in variants:
            for mode_name, kwargs in modes:
                attempt = SolveAttempt(
                    path=frame.path,
                    block=frame.block,
                    test=frame.test,
                    file=frame.path.name,
                    candidate_rank=candidate_rank,
                    preprocess_mode=preprocess_name,
                    fov_mode=mode_name,
                    ok=False,
                )
                try:
                    t0 = time.perf_counter()
                    result = t3.solve_from_image(
                        processed,
                        solve_timeout=solve_timeout_ms,
                        return_matches=True,
                        pattern_checking_stars=12,
                        **kwargs,
                    )
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    attempt.solve_time_ms = elapsed_ms
                    if result and result.get("RA") is not None:
                        attempt.ok = True
                        attempt.solve_ra = float(result.get("RA"))
                        attempt.solve_dec = float(result.get("Dec"))
                        attempt.solve_fov = float(result.get("FOV"))
                        attempt.solve_roll = float(result.get("Roll"))
                        attempt.solve_matches = int(result.get("Matches", 0))
                        if not frame.solve_ok:
                            frame.solve_ok = True
                            frame.solve_ra = attempt.solve_ra
                            frame.solve_dec = attempt.solve_dec
                            frame.solve_fov = attempt.solve_fov
                            frame.solve_roll = attempt.solve_roll
                            frame.solve_matches = attempt.solve_matches
                            frame.solve_time_ms = elapsed_ms
                            frame.solve_preprocess = preprocess_name
                            frame.solve_mode = mode_name
                    elif not frame.solve_ok:
                        frame.solve_time_ms = elapsed_ms
                        frame.solve_preprocess = preprocess_name
                        frame.solve_mode = mode_name
                except Exception as exc:
                    attempt.solve_error = f"{exc.__class__.__name__}: {exc}"
                    if not frame.solve_ok:
                        frame.solve_error = attempt.solve_error
                attempts.append(attempt)
                if attempt.ok and not continue_after_solve:
                    return attempts
    return attempts


def write_csv(path: Path, frames: list[FrameMetrics]) -> None:
    fields = list(FrameMetrics.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for frame in frames:
            row = {field: getattr(frame, field) for field in fields}
            row["path"] = str(frame.path)
            writer.writerow(row)


def write_attempts_csv(path: Path, attempts: list[SolveAttempt]) -> None:
    fields = list(SolveAttempt.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for attempt in attempts:
            row = {field: getattr(attempt, field) for field in fields}
            row["path"] = str(attempt.path)
            writer.writerow(row)


def write_markdown(
    path: Path,
    frames: list[FrameMetrics],
    solved: list[FrameMetrics],
    attempts: list[SolveAttempt],
    continue_after_solve: bool,
) -> None:
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
        f"- Solve attempts across preprocessing/FOV variants: {len(attempts)}",
        f"- Successful solves: {len(solved)}",
        "",
    ]
    if attempts:
        lines += [
            "## Preprocessing Outcomes",
            "",
            "| preprocess | attempts | solved attempts | unique solved frames | median solve ms |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for mode in sorted({attempt.preprocess_mode for attempt in attempts}):
            mode_attempts = [attempt for attempt in attempts if attempt.preprocess_mode == mode]
            ok_attempts = [attempt for attempt in mode_attempts if attempt.ok]
            times = sorted(
                attempt.solve_time_ms
                for attempt in mode_attempts
                if attempt.solve_time_ms is not None
            )
            median_ms = times[len(times) // 2] if times else 0
            lines.append(
                f"| {mode} | {len(mode_attempts)} | {len(ok_attempts)} | "
                f"{len({attempt.path for attempt in ok_attempts})} | {median_ms:.0f} |"
            )
        lines += [
            "",
            "Note: by default the script stops trying variants for a candidate after "
            "the first successful solve. Use `--continue-after-solve` for a fuller "
            "mode-by-mode comparison at higher runtime cost."
            if not continue_after_solve
            else "Note: this run used `--continue-after-solve`, so all requested variants were attempted for each candidate.",
            "",
        ]
    if solved:
        lines += [
            "## Successful Solves",
            "",
            "| block | test | file | preprocess | fov mode | matches | fov | solve ms |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
        for frame in solved:
            lines.append(
                f"| {frame.block} | {frame.test} | `{frame.path.name}` | "
                f"{frame.solve_preprocess} | {frame.solve_mode} | "
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
        "## Recommendation For Next Steps",
        "",
        "- Prefer baseline JPEG solving first; in this run, percentile stretching did not help and background subtraction only helped one frame after baseline failed.",
        "- Rank uploaded frames by a dark-background score, centroid count, bright point count, sharpness, and saturation. Penalize lifted gray/noisy backgrounds before spending solver CPU.",
        "- Use ISO 400/800 candidates from the tested Samsung run before ISO 3200 candidates unless a later clear-sky run proves otherwise.",
        "- Feed these metrics into #40 as the first server-side image quality score, then use #41 for explicit diagnostic solving of stored uploads.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    preprocess_modes = [
        mode.strip()
        for mode in args.preprocess_modes.split(",")
        if mode.strip()
    ]

    metadata_by_run: dict[str, dict[str, str]] = {}
    frames: list[FrameMetrics] = []
    for jpg, metadata in iter_jpgs(root):
        metadata_by_run[jpg.parent.name] = metadata
        frames.append(quality_metrics(jpg, root, metadata))

    t3 = tetra3.Tetra3(str(TETRA3_DB))
    candidates = sorted(frames, key=lambda f: f.quality_score, reverse=True)[: args.max_solve]
    attempts: list[SolveAttempt] = []
    for rank, candidate in enumerate(candidates, 1):
        attempts.extend(
            solve_frame(
                t3,
                candidate,
                metadata_by_run,
                candidate_rank=rank,
                preprocess_modes=preprocess_modes,
                solve_timeout_ms=args.solve_timeout_ms,
                continue_after_solve=args.continue_after_solve,
            )
        )

    solved = [frame for frame in frames if frame.solve_ok]
    write_csv(output_dir / "phase2_camera_analysis.csv", frames)
    write_attempts_csv(output_dir / "phase2_camera_solve_attempts.csv", attempts)
    write_markdown(
        output_dir / "phase2_camera_analysis.md",
        frames,
        solved,
        attempts,
        args.continue_after_solve,
    )
    print(f"Analyzed {len(frames)} JPG frames")
    print(f"Attempted solve on {len(candidates)} candidates")
    print(f"Solve attempts: {len(attempts)}")
    print(f"Successful solves: {len(solved)}")
    print(output_dir / "phase2_camera_analysis.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
