"""Generate a conservative per-phone mobile camera recommendation profile.

The generated profile summarizes diagnostic reports only. It is not a runtime
configuration and must not enable mobile camera input for live pointing.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_REPORTS_DIR = Path.home() / "PiFinder_data/mobile/camera_solve_reports"


def _load_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []
    if not reports_dir.exists():
        return reports
    for path in sorted(reports_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            reports.append(payload)
    return reports


def _nested_dict(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _report_device(report: Dict[str, Any]) -> Dict[str, Any]:
    metadata = _nested_dict(report, "metadata")
    device = _nested_dict(metadata, "device")
    nested_metadata = _nested_dict(metadata, "metadata")
    if not device and nested_metadata:
        device = _nested_dict(nested_metadata, "device")
    return device


def _report_metadata(report: Dict[str, Any]) -> Dict[str, Any]:
    metadata = _nested_dict(report, "metadata")
    nested_metadata = _nested_dict(metadata, "metadata")
    if nested_metadata:
        merged = dict(nested_metadata)
        merged.update({key: value for key, value in metadata.items() if key != "metadata"})
        return merged
    return metadata


def _matches_device(report: Dict[str, Any], device_model: str) -> bool:
    if not device_model:
        return True
    model = str(_report_device(report).get("model", "")).strip()
    return not model or model == device_model


def _quality_score(report: Dict[str, Any]) -> Optional[float]:
    summary = _nested_dict(report, "summary")
    score = summary.get("quality_score")
    if score is None:
        score = _nested_dict(report, "score").get("quality_score")
    try:
        return float(score)
    except (TypeError, ValueError):
        return None


def _status(report: Dict[str, Any]) -> str:
    summary = _nested_dict(report, "summary")
    status = str(summary.get("status", "")).strip()
    if status:
        return status
    solve = _nested_dict(report, "solve")
    if solve.get("solve_ok") is True:
        return "solved"
    if solve.get("attempted") is False:
        return "rejected"
    return "unknown"


def _solve_ok(report: Dict[str, Any]) -> bool:
    summary = _nested_dict(report, "summary")
    if summary.get("solve_ok") is True:
        return True
    return _nested_dict(report, "solve").get("solve_ok") is True


def _most_common(values: Iterable[str], default: str = "unknown") -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return default
    return Counter(cleaned).most_common(1)[0][0]


def _confidence(total: int, solved: int, clear_sky_evidence: bool) -> str:
    if total == 0:
        return "UNKNOWN"
    if clear_sky_evidence and solved >= 3 and total >= 6:
        return "HIGH"
    if solved > 0:
        return "MEDIUM"
    return "LOW"


def _caveats(confidence: str, clear_sky_evidence: bool) -> List[str]:
    caveats = [
        "clear_sky_phase2_required",
        "thresholds_not_tuned_until_57",
        "runtime_decision_blocked_until_59",
        "diagnostic_only_no_integrator_feed",
    ]
    if confidence == "HIGH" and clear_sky_evidence:
        caveats.remove("clear_sky_phase2_required")
    return caveats


def generate_mobile_camera_profile(
    reports_dir: Path = DEFAULT_REPORTS_DIR,
    device_model: str = "",
    manufacturer: str = "",
    app_build: str = "",
    clear_sky_evidence: bool = False,
) -> Dict[str, Any]:
    """Build a sanitized recommendation profile from diagnostic report JSON."""

    reports = [
        report
        for report in _load_reports(Path(reports_dir))
        if _matches_device(report, device_model)
    ]
    device_models = [
        str(_report_device(report).get("model", "")).strip() for report in reports
    ]
    manufacturers = [
        str(_report_device(report).get("manufacturer", "")).strip() for report in reports
    ]
    app_builds = [
        str(_report_device(report).get("app_build", "")).strip() for report in reports
    ]
    model = device_model or _most_common(device_models)
    maker = manufacturer or _most_common(manufacturers)
    build = app_build or _most_common(app_builds, "")

    statuses = Counter(_status(report) for report in reports)
    solved_reports = sum(1 for report in reports if _solve_ok(report))
    attempted_reports = sum(
        1
        for report in reports
        if _nested_dict(report, "summary").get("attempted") is True
        or _nested_dict(report, "solve").get("attempted") is True
    )
    scores = [score for report in reports if (score := _quality_score(report)) is not None]
    best_quality_score = max(scores) if scores else None
    camera_ids = []
    capture_modes = []
    formats = []
    for report in reports:
        metadata = _report_metadata(report)
        if _solve_ok(report):
            camera_ids.append(str(metadata.get("camera_id", "")).strip())
            capture_modes.append(str(metadata.get("capture_mode", "")).strip())
            formats.append(str(metadata.get("format", "")).strip())
    if not camera_ids:
        for report in reports:
            metadata = _report_metadata(report)
            camera_ids.append(str(metadata.get("camera_id", "")).strip())
            capture_modes.append(str(metadata.get("capture_mode", "")).strip())
            formats.append(str(metadata.get("format", "")).strip())

    confidence = _confidence(len(reports), solved_reports, clear_sky_evidence)
    recommended_camera_id = _most_common(camera_ids)
    preferred_capture_mode = _most_common(capture_modes, "solve_candidate_burst")
    preferred_format = _most_common(formats, "jpeg")
    raw_status = "unknown"
    if preferred_format == "jpeg":
        raw_status = "not_recommended_until_58"

    return {
        "schema": "pifinder-mobile-camera-profile-v1",
        "status": "diagnostic",
        "decision": "PROMISING_TUNE_FIRST",
        "device": {
            "manufacturer": maker or "unknown",
            "model": model or "unknown",
            "app_build": build or "unknown",
        },
        "recommendation": {
            "recommended_camera_id": recommended_camera_id,
            "preferred_capture_mode": preferred_capture_mode,
            "preferred_format": preferred_format,
            "raw_status": raw_status,
            "confidence": confidence,
            "runtime_support": "diagnostic_only",
            "quality_score_required": True,
            "diagnostic_solve_required": True,
        },
        "evidence": {
            "source": "camera_solve_reports",
            "total_reports": len(reports),
            "attempted_reports": attempted_reports,
            "solved_reports": solved_reports,
            "rejected_reports": statuses.get("rejected", 0),
            "failed_reports": statuses.get("solve_failed", 0)
            + statuses.get("failed", 0),
            "best_quality_score": best_quality_score,
            "clear_sky_evidence": bool(clear_sky_evidence),
            "status_counts": dict(sorted(statuses.items())),
        },
        "caveats": _caveats(confidence, clear_sky_evidence),
    }


def _write_markdown(profile: Dict[str, Any], output: Path) -> None:
    recommendation = profile["recommendation"]
    evidence = profile["evidence"]
    lines = [
        "# Mobile Camera Recommendation Profile",
        "",
        f"Device: `{profile['device']['manufacturer']} {profile['device']['model']}`",
        f"Confidence: `{recommendation['confidence']}`",
        f"Runtime support: `{recommendation['runtime_support']}`",
        "",
        "## Recommendation",
        "",
        f"- Camera ID: `{recommendation['recommended_camera_id']}`",
        f"- Capture mode: `{recommendation['preferred_capture_mode']}`",
        f"- Format: `{recommendation['preferred_format']}`",
        f"- RAW status: `{recommendation['raw_status']}`",
        "",
        "## Evidence",
        "",
        f"- Reports: `{evidence['total_reports']}`",
        f"- Solved: `{evidence['solved_reports']}`",
        f"- Rejected: `{evidence['rejected_reports']}`",
        f"- Best quality score: `{evidence['best_quality_score']}`",
        f"- Clear-sky evidence: `{evidence['clear_sky_evidence']}`",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- `{caveat}`" for caveat in profile["caveats"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--device-model", default="")
    parser.add_argument("--manufacturer", default="")
    parser.add_argument("--app-build", default="")
    parser.add_argument("--clear-sky-evidence", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    profile = generate_mobile_camera_profile(
        reports_dir=args.reports_dir,
        device_model=args.device_model,
        manufacturer=args.manufacturer,
        app_build=args.app_build,
        clear_sky_evidence=args.clear_sky_evidence,
    )
    text = json.dumps(profile, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        _write_markdown(profile, args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
