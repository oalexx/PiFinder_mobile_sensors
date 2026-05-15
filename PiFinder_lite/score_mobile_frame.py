"""Score mobile JPEG frames before diagnostic solving.

This is an offline / debug helper for PiFinder Lite. It intentionally does not
invoke the solver. The score is derived from the Phase 2 finding that dark
ISO400/ISO800 frames solved better than noisy ISO3200 frames with lifted gray
backgrounds.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class MobileFrameScore:
    path: str
    width: int
    height: int
    mean: float
    p95: float
    p99: float
    dark_pct: float
    saturation_pct: float
    sharpness: float
    noise_proxy: float
    bright_points: int
    centroids: int
    quality_score: float
    grade: str
    accept_for_diagnostic_solve: bool
    reasons: list[str]
    rejection_reasons: list[str]


@dataclass
class InvalidMobileFrame:
    path: str
    error: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="JPEG file or directory containing JPEG frames.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "PiFinder_lite" / "phase2_camera_analysis"),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def iter_jpegs(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    patterns = ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG")
    seen: set[Path] = set()
    for pattern in patterns:
        for candidate in sorted(path.rglob(pattern)):
            if candidate not in seen:
                seen.add(candidate)
                yield candidate


def downscaled_luma(path: Path, max_side: int = 900) -> tuple[Image.Image, np.ndarray, tuple[int, int]]:
    with Image.open(path) as image:
        width, height = image.size
        gray = image.convert("L")
        gray.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        arr = np.asarray(gray, dtype=np.float32)
        return gray.copy(), arr, (width, height)


def connected_points(arr: np.ndarray, percentile: float, sigma_multiplier: float) -> int:
    if arr.size == 0:
        return 0
    threshold = max(
        float(np.percentile(arr, percentile)),
        float(arr.mean() + sigma_multiplier * arr.std()),
    )
    mask = arr >= threshold
    if not mask.any():
        return 0
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


def approximate_bright_points(arr: np.ndarray) -> int:
    return connected_points(arr, percentile=99.85, sigma_multiplier=4.0)


def approximate_centroids(arr: np.ndarray) -> int:
    return connected_points(arr, percentile=99.55, sigma_multiplier=3.2)


def noise_proxy(gray: Image.Image) -> float:
    background = gray.filter(ImageFilter.MedianFilter(size=9))
    arr = np.asarray(gray, dtype=np.float32)
    bg = np.asarray(background, dtype=np.float32)
    residual = arr - bg
    return float(np.std(residual))


def score_metrics(
    mean: float,
    dark_pct: float,
    saturation_pct: float,
    sharpness: float,
    noise: float,
    bright_points: int,
    centroids: int,
) -> tuple[float, list[str], list[str]]:
    score = 0.0
    reasons: list[str] = []
    rejection_reasons: list[str] = []

    if dark_pct >= 92:
        score += 32
        reasons.append("dark_background_good")
    elif dark_pct >= 75:
        score += 20
        reasons.append("background_usable")
    elif dark_pct >= 45:
        score += 5
        rejection_reasons.append("background_not_dark_enough")
    else:
        score -= 45
        rejection_reasons.append("too_bright_background")

    if mean <= 2.8:
        score += 28
        reasons.append("low_background_mean")
    elif mean <= 4.5:
        score += 16
        reasons.append("background_mean_usable")
    elif mean <= 6.5:
        score += 4
        rejection_reasons.append("background_mean_high")
    else:
        score -= min(70, (mean - 6.5) * 12)
        rejection_reasons.append("lifted_gray_background")

    if 18 <= centroids <= 90:
        score += min(centroids, 80) * 0.8
        reasons.append("enough_centroids")
    elif centroids > 90:
        score += 32
        reasons.append("many_centroids_capped")
    else:
        score += centroids * 0.6
        rejection_reasons.append("low_star_candidates")

    if 25 <= bright_points <= 800:
        score += min(bright_points, 250) * 0.08
        reasons.append("bright_points_reasonable")
    elif bright_points > 800:
        score += 8
        rejection_reasons.append("too_many_bright_points_possible_noise")
    else:
        score += bright_points * 0.08

    score += min(sharpness / 5.0, 18.0)
    if sharpness >= 3.0:
        reasons.append("sharpness_usable")
    else:
        rejection_reasons.append("low_sharpness_or_low_signal")

    if saturation_pct > 0.5:
        score -= saturation_pct * 12
        rejection_reasons.append("saturation_present")
    else:
        reasons.append("low_saturation")

    if noise > 9.0:
        score -= min(35, (noise - 9.0) * 3)
        rejection_reasons.append("noise_proxy_high")

    if mean > 5.0 and (centroids >= 60 or bright_points >= 120):
        score -= 55
        rejection_reasons.append("possible_noise_overrank_lifted_background")

    return round(score, 2), reasons, rejection_reasons


def grade_for(score: float, rejection_reasons: list[str]) -> tuple[str, bool]:
    hard_rejections = {
        "too_bright_background",
        "lifted_gray_background",
        "possible_noise_overrank_lifted_background",
    }
    if hard_rejections.intersection(rejection_reasons):
        return "LOW", False
    if score >= 100:
        return "HIGH", True
    if score >= 72:
        return "MEDIUM", True
    return "LOW", False


def score_frame(path: Path) -> MobileFrameScore:
    gray, arr, original_size = downscaled_luma(path)
    stat = ImageStat.Stat(gray)
    mean = float(stat.mean[0])
    p95, p99 = np.percentile(arr, [95, 99])
    saturation_pct = float(np.mean(arr >= 252) * 100)
    dark_pct = float(np.mean(arr <= 3) * 100)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    sharpness = float(ImageStat.Stat(edges).var[0])
    bright_points = approximate_bright_points(arr)
    centroids = approximate_centroids(arr)
    noise = noise_proxy(gray)
    score, reasons, rejection_reasons = score_metrics(
        mean=mean,
        dark_pct=dark_pct,
        saturation_pct=saturation_pct,
        sharpness=sharpness,
        noise=noise,
        bright_points=bright_points,
        centroids=centroids,
    )
    grade, accept = grade_for(score, rejection_reasons)
    return MobileFrameScore(
        path=str(path),
        width=original_size[0],
        height=original_size[1],
        mean=round(mean, 3),
        p95=round(float(p95), 3),
        p99=round(float(p99), 3),
        dark_pct=round(dark_pct, 3),
        saturation_pct=round(saturation_pct, 3),
        sharpness=round(sharpness, 3),
        noise_proxy=round(noise, 3),
        bright_points=bright_points,
        centroids=centroids,
        quality_score=score,
        grade=grade,
        accept_for_diagnostic_solve=accept,
        reasons=reasons,
        rejection_reasons=rejection_reasons,
    )


def score_valid_frames(paths: Iterable[Path]) -> tuple[list[MobileFrameScore], list[InvalidMobileFrame]]:
    scores: list[MobileFrameScore] = []
    invalid_frames: list[InvalidMobileFrame] = []
    for path in paths:
        try:
            scores.append(score_frame(path))
        except (OSError, UnidentifiedImageError) as exc:
            invalid_frames.append(
                InvalidMobileFrame(
                    path=str(path),
                    error=f"{exc.__class__.__name__}: {exc}",
                )
            )
    return scores, invalid_frames


def write_csv(path: Path, scores: list[MobileFrameScore]) -> None:
    fields = list(MobileFrameScore.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for score in scores:
            row = asdict(score)
            row["reasons"] = ";".join(score.reasons)
            row["rejection_reasons"] = ";".join(score.rejection_reasons)
            writer.writerow(row)


def write_markdown(
    path: Path,
    scores: list[MobileFrameScore],
    invalid_frames: list[InvalidMobileFrame] | None = None,
) -> None:
    invalid_frames = invalid_frames or []
    accepted = [score for score in scores if score.accept_for_diagnostic_solve]
    by_grade = {grade: sum(1 for score in scores if score.grade == grade) for grade in ("HIGH", "MEDIUM", "LOW")}
    lines = [
        "# Mobile Frame Quality Scores",
        "",
        "This report scores mobile JPEGs before any diagnostic solve attempt.",
        "",
        "## Summary",
        "",
        f"- Frames scored: {len(scores)}",
        f"- Invalid frames skipped: {len(invalid_frames)}",
        f"- Accepted for diagnostic solve: {len(accepted)}",
        f"- HIGH: {by_grade['HIGH']}",
        f"- MEDIUM: {by_grade['MEDIUM']}",
        f"- LOW: {by_grade['LOW']}",
        "",
        "## Top Candidates",
        "",
        "| rank | grade | accepted | score | file | mean | dark % | centroids | bright pts | sharpness | rejection reasons |",
        "| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, score in enumerate(sorted(scores, key=lambda item: item.quality_score, reverse=True)[:30], 1):
        lines.append(
            f"| {rank} | {score.grade} | {'yes' if score.accept_for_diagnostic_solve else 'no'} | "
            f"{score.quality_score:.1f} | `{Path(score.path).name}` | {score.mean:.1f} | "
            f"{score.dark_pct:.1f} | {score.centroids} | {score.bright_points} | "
            f"{score.sharpness:.1f} | {', '.join(score.rejection_reasons)} |"
        )
    lines += [
        "",
        "## Invalid Frames",
        "",
    ]
    if invalid_frames:
        lines.extend(
            f"- `{Path(frame.path).name}`: {frame.error}"
            for frame in invalid_frames
        )
    else:
        lines.append("- none")
    lines += [
        "",
        "## Scoring Notes",
        "",
        "- The score intentionally prefers a dark background and low mean brightness.",
        "- Many centroid or bright-point detections are capped so noisy ISO3200 frames do not dominate.",
        "- Lifted gray backgrounds are hard-rejected even when they contain many detected points.",
        "- `centroids` is a fast connected-component approximation, not a Tetra3 solve.",
        "- This helper does not invoke Tetra3 solving; it only decides whether a diagnostic solve is worth trying.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scores, invalid_frames = score_valid_frames(iter_jpegs(input_path))
    scores.sort(key=lambda item: item.quality_score, reverse=True)

    csv_path = output_dir / "mobile_frame_quality_scores.csv"
    json_path = output_dir / "mobile_frame_quality_scores.json"
    invalid_json_path = output_dir / "mobile_frame_quality_invalid.json"
    markdown_path = output_dir / "mobile_frame_quality_scores.md"
    write_csv(csv_path, scores)
    json_path.write_text(
        json.dumps([asdict(score) for score in scores], indent=2),
        encoding="utf-8",
    )
    invalid_json_path.write_text(
        json.dumps([asdict(frame) for frame in invalid_frames], indent=2),
        encoding="utf-8",
    )
    write_markdown(markdown_path, scores, invalid_frames)

    if args.json:
        print(
            json.dumps(
                {
                    "scores": [asdict(score) for score in scores],
                    "invalid_frames": [asdict(frame) for frame in invalid_frames],
                },
                indent=2,
            )
        )
    else:
        accepted = sum(1 for score in scores if score.accept_for_diagnostic_solve)
        print(f"Scored {len(scores)} JPEG frames")
        print(f"Skipped invalid frames: {len(invalid_frames)}")
        print(f"Accepted for diagnostic solve: {accepted}")
        print(markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
