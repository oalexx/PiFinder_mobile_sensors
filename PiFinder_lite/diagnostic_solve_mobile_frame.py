"""Run explicit diagnostic solves for scored mobile JPEG frames.

This helper is intentionally outside the PiFinder runtime path. It reads one
JPEG or a directory of JPEGs, scores them with `score_mobile_frame.py`, and
attempts Tetra3 solving only for frames accepted by the quality score.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

import score_mobile_frame


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = REPO_ROOT / "python"
TETRA3_PACKAGE_PARENT = PYTHON_DIR / "PiFinder" / "tetra3"
TETRA3_PACKAGE_DIR = TETRA3_PACKAGE_PARENT / "tetra3"
TETRA3_DB = TETRA3_PACKAGE_PARENT / "tetra3" / "data" / "default_database.npz"

if not hasattr(np, "math"):
    np.math = math
sys.path.insert(0, str(TETRA3_PACKAGE_PARENT))
sys.path.insert(0, str(TETRA3_PACKAGE_DIR))
import tetra3  # noqa: E402


@dataclass
class DiagnosticSolveResult:
    path: str
    candidate_rank: int
    grade: str
    quality_score: float
    accepted_by_score: bool
    attempted: bool
    solve_ok: bool
    preprocess_mode: str = ""
    fov_mode: str = ""
    solve_ra: float | None = None
    solve_dec: float | None = None
    solve_fov: float | None = None
    solve_roll: float | None = None
    solve_matches: int | None = None
    solve_time_ms: float | None = None
    solve_error: str = ""
    rejection_reasons: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="JPEG file or directory containing stored/captured mobile JPEGs.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "PiFinder_lite" / "phase2_camera_analysis"),
    )
    parser.add_argument("--max-frames", type=int, default=12)
    parser.add_argument("--solve-timeout-ms", type=int, default=1000)
    parser.add_argument(
        "--min-grade",
        choices=("HIGH", "MEDIUM", "LOW"),
        default="MEDIUM",
        help="Minimum score grade to attempt. LOW means attempt all accepted/low frames.",
    )
    parser.add_argument(
        "--preprocess-modes",
        default="baseline,background_subtract",
        help="Comma-separated modes: baseline,background_subtract.",
    )
    parser.add_argument(
        "--continue-after-solve",
        action="store_true",
        help="Continue trying modes after the first successful solve.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def grade_rank(grade: str) -> int:
    return {"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get(grade, 0)


def parse_metadata_text(run_dir: Path) -> dict[str, str]:
    metadata_files = list(run_dir.glob("*_metadata.txt"))
    if not metadata_files:
        return {}
    metadata: dict[str, str] = {}
    for line in metadata_files[0].read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def read_sidecar_metadata(frame_path: Path) -> dict[str, Any]:
    sidecar = frame_path.with_suffix(".json")
    if not sidecar.exists():
        return {}
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(payload, dict):
        nested = payload.get("metadata")
        if isinstance(nested, dict):
            merged = dict(payload)
            merged.update(nested)
            return merged
        return payload
    return {}


def fov_from_metadata(metadata: dict[str, Any]) -> float | None:
    focal_text = str(metadata.get("focalLengthsMm", ""))
    sensor_text = str(metadata.get("sensorPhysicalSizeMm", ""))
    focal_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", focal_text)
    sensor_match = re.search(r"([0-9]+(?:\.[0-9]+)?)x", sensor_text)
    if not focal_match or not sensor_match:
        return None
    focal_mm = float(focal_match.group(1))
    sensor_width_mm = float(sensor_match.group(1))
    if focal_mm <= 0:
        return None
    return math.degrees(2 * math.atan(sensor_width_mm / (2 * focal_mm)))


def fov_modes(frame_path: Path) -> list[tuple[str, dict[str, float | int | bool | None]]]:
    metadata = parse_metadata_text(frame_path.parent)
    metadata.update(read_sidecar_metadata(frame_path))
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
    return modes


def background_subtract(gray: Image.Image) -> Image.Image:
    background = gray.filter(ImageFilter.MedianFilter(size=31))
    return ImageChops.subtract(gray, background, scale=1.0, offset=18)


def percentile_stretch(gray: Image.Image, low_pct: float = 1.0, high_pct: float = 99.8) -> Image.Image:
    histogram = gray.histogram()
    total = sum(histogram)
    if total <= 0:
        return gray.copy()

    def percentile_value(percentile: float) -> int:
        target = total * percentile / 100.0
        cumulative = 0
        for value, count in enumerate(histogram):
            cumulative += count
            if cumulative >= target:
                return value
        return 255

    lo = percentile_value(low_pct)
    hi = percentile_value(high_pct)
    if hi <= lo:
        return gray.copy()
    scale = 255.0 / float(hi - lo)
    lut = [max(0, min(255, int((value - lo) * scale))) for value in range(256)]
    return gray.point(lut)


def denoise_stretch(gray: Image.Image) -> Image.Image:
    denoised = gray.filter(ImageFilter.MedianFilter(size=3))
    stretched = percentile_stretch(denoised, low_pct=1.0, high_pct=99.7)
    return ImageEnhance.Contrast(stretched).enhance(1.25)


def hot_pixel_suppression(gray: Image.Image) -> Image.Image:
    median = gray.filter(ImageFilter.MedianFilter(size=3))
    softened = ImageChops.darker(gray, median)
    return percentile_stretch(softened, low_pct=1.0, high_pct=99.8)


def local_contrast(gray: Image.Image) -> Image.Image:
    stretched = percentile_stretch(gray, low_pct=1.0, high_pct=99.8)
    enhanced = ImageOps.autocontrast(stretched)
    return enhanced.filter(ImageFilter.UnsharpMask(radius=1.0, percent=70, threshold=4))


def center_crop(gray: Image.Image, fraction: float = 0.78) -> Image.Image:
    width, height = gray.size
    crop_width = max(1, int(width * fraction))
    crop_height = max(1, int(height * fraction))
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    return gray.crop((left, top, left + crop_width, top + crop_height))


def preprocess_variants(gray: Image.Image, modes: list[str]) -> list[tuple[str, Image.Image]]:
    variants: list[tuple[str, Image.Image]] = []
    for mode in modes:
        if mode == "baseline":
            variants.append((mode, gray.copy()))
        elif mode == "background_subtract":
            variants.append((mode, background_subtract(gray)))
        elif mode == "percentile_stretch":
            variants.append((mode, percentile_stretch(gray)))
        elif mode == "denoise_stretch":
            variants.append((mode, denoise_stretch(gray)))
        elif mode == "hot_pixel_suppression":
            variants.append((mode, hot_pixel_suppression(gray)))
        elif mode == "local_contrast":
            variants.append((mode, local_contrast(gray)))
        elif mode == "center_crop":
            variants.append((mode, center_crop(gray)))
        else:
            raise ValueError(f"Unknown preprocess mode: {mode}")
    return variants


def solve_one(
    t3: tetra3.Tetra3,
    frame_path: Path,
    score: score_mobile_frame.MobileFrameScore,
    candidate_rank: int,
    preprocess_modes: list[str],
    solve_timeout_ms: int,
    continue_after_solve: bool,
) -> list[DiagnosticSolveResult]:
    results: list[DiagnosticSolveResult] = []
    with Image.open(frame_path) as image:
        gray = image.convert("L")
        gray.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        for preprocess_name, processed in preprocess_variants(gray, preprocess_modes):
            for fov_mode, kwargs in fov_modes(frame_path):
                result_row = DiagnosticSolveResult(
                    path=str(frame_path),
                    candidate_rank=candidate_rank,
                    grade=score.grade,
                    quality_score=score.quality_score,
                    accepted_by_score=score.accept_for_diagnostic_solve,
                    attempted=True,
                    solve_ok=False,
                    preprocess_mode=preprocess_name,
                    fov_mode=fov_mode,
                    rejection_reasons=";".join(score.rejection_reasons),
                )
                try:
                    t0 = time.perf_counter()
                    solve = t3.solve_from_image(
                        processed,
                        solve_timeout=solve_timeout_ms,
                        return_matches=True,
                        pattern_checking_stars=12,
                        **kwargs,
                    )
                    result_row.solve_time_ms = round((time.perf_counter() - t0) * 1000, 1)
                    if solve and solve.get("RA") is not None:
                        result_row.solve_ok = True
                        result_row.solve_ra = float(solve.get("RA"))
                        result_row.solve_dec = float(solve.get("Dec"))
                        result_row.solve_fov = float(solve.get("FOV"))
                        result_row.solve_roll = float(solve.get("Roll"))
                        result_row.solve_matches = int(solve.get("Matches", 0))
                except Exception as exc:
                    result_row.solve_error = f"{exc.__class__.__name__}: {exc}"
                results.append(result_row)
                if result_row.solve_ok and not continue_after_solve:
                    return results
    return results


def skipped_result(
    frame_path: Path,
    score: score_mobile_frame.MobileFrameScore,
    candidate_rank: int,
) -> DiagnosticSolveResult:
    return DiagnosticSolveResult(
        path=str(frame_path),
        candidate_rank=candidate_rank,
        grade=score.grade,
        quality_score=score.quality_score,
        accepted_by_score=score.accept_for_diagnostic_solve,
        attempted=False,
        solve_ok=False,
        rejection_reasons=";".join(score.rejection_reasons),
    )


def write_csv(path: Path, results: list[DiagnosticSolveResult]) -> None:
    fields = list(DiagnosticSolveResult.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def write_markdown(path: Path, results: list[DiagnosticSolveResult]) -> None:
    attempted = [result for result in results if result.attempted]
    solved = [result for result in attempted if result.solve_ok]
    unique_attempted = {result.path for result in attempted}
    unique_solved = {result.path for result in solved}
    lines = [
        "# Mobile Frame Diagnostic Solves",
        "",
        "This report contains explicit diagnostic solves for mobile JPEG frames.",
        "",
        "## Summary",
        "",
        f"- Result rows: {len(results)}",
        f"- Unique frames attempted: {len(unique_attempted)}",
        f"- Unique frames solved: {len(unique_solved)}",
        f"- Successful solve rows: {len(solved)}",
        "",
        "## Successful Solves",
        "",
        "| rank | grade | score | file | preprocess | fov mode | matches | fov | solve ms | RA | Dec |",
        "| ---: | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in solved:
        lines.append(
            f"| {result.candidate_rank} | {result.grade} | {result.quality_score:.1f} | "
            f"`{Path(result.path).name}` | {result.preprocess_mode} | {result.fov_mode} | "
            f"{result.solve_matches} | {result.solve_fov:.2f} | {result.solve_time_ms:.0f} | "
            f"{result.solve_ra:.4f} | {result.solve_dec:.4f} |"
        )
    if not solved:
        lines.append("| | | | no solves | | | | | | | |")
    lines += [
        "",
        "## Guardrails",
        "",
        "- This helper does not update PiFinder live pointing.",
        "- This helper does not feed the integrator.",
        "- This helper does not change classic PiFinder solver behavior.",
        "- Results are evidence for the later mobile-camera path decision only.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    preprocess_modes = [mode.strip() for mode in args.preprocess_modes.split(",") if mode.strip()]
    min_grade = grade_rank(args.min_grade)

    scores, invalid_frames = score_mobile_frame.score_valid_frames(
        score_mobile_frame.iter_jpegs(input_path)
    )
    scores.sort(key=lambda item: item.quality_score, reverse=True)

    t3 = tetra3.Tetra3(str(TETRA3_DB))
    results: list[DiagnosticSolveResult] = []
    attempted_frames = 0
    for candidate_rank, score in enumerate(scores, 1):
        frame_path = Path(score.path)
        should_attempt = (
            score.accept_for_diagnostic_solve
            and grade_rank(score.grade) >= min_grade
            and attempted_frames < args.max_frames
        )
        if not should_attempt:
            results.append(skipped_result(frame_path, score, candidate_rank))
            continue
        attempted_frames += 1
        results.extend(
            solve_one(
                t3=t3,
                frame_path=frame_path,
                score=score,
                candidate_rank=candidate_rank,
                preprocess_modes=preprocess_modes,
                solve_timeout_ms=args.solve_timeout_ms,
                continue_after_solve=args.continue_after_solve,
            )
        )

    json_path = output_dir / "mobile_frame_diagnostic_solves.json"
    csv_path = output_dir / "mobile_frame_diagnostic_solves.csv"
    markdown_path = output_dir / "mobile_frame_diagnostic_solves.md"
    payload = [asdict(result) for result in results]
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(csv_path, results)
    write_markdown(markdown_path, results)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        solved = {result.path for result in results if result.solve_ok}
        print(f"Scored {len(scores)} JPEG frames")
        print(f"Skipped invalid frames: {len(invalid_frames)}")
        print(f"Attempted diagnostic solve on {attempted_frames} frames")
        print(f"Solved {len(solved)} unique frames")
        print(markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
