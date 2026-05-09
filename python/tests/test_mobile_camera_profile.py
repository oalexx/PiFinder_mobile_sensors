import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE_TOOL = ROOT / "PiFinder_lite/generate_mobile_camera_profile.py"


def load_profile_tool():
    spec = importlib.util.spec_from_file_location("generate_mobile_camera_profile", PROFILE_TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_report(path, frame_id, model, camera_id, status, grade, score, solve_ok):
    payload = {
        "frame_id": frame_id,
        "diagnostic_only": True,
        "metadata": {
            "device": {
                "manufacturer": "samsung",
                "model": model,
                "app_build": "debug-local",
            },
            "camera_id": camera_id,
            "capture_mode": "solve_candidate_burst",
            "format": "jpeg",
            "source_file": f"{frame_id}.jpg",
        },
        "score": {
            "grade": grade,
            "quality_score": score,
            "path": f"/home/pi/private/{frame_id}.jpg",
        },
        "solve": {
            "attempted": True,
            "solve_ok": solve_ok,
        },
        "summary": {
            "status": status,
            "grade": grade,
            "quality_score": score,
            "attempted": True,
            "solve_ok": solve_ok,
        },
        "advice": {
            "code": "solved_collect_more" if solve_ok else "background_too_bright",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_profile_generator_summarizes_per_phone_diagnostics(tmp_path):
    tool = load_profile_tool()
    write_report(tmp_path / "001.json", "bad", "SM-S948B", "0", "rejected", "LOW", 0.12, False)
    write_report(tmp_path / "002.json", "good", "SM-S948B", "2", "solved", "HIGH", 0.91, True)

    profile = tool.generate_mobile_camera_profile(
        reports_dir=tmp_path,
        device_model="SM-S948B",
        manufacturer="samsung",
        app_build="debug-local",
    )

    assert profile["schema"] == "pifinder-mobile-camera-profile-v1"
    assert profile["device"]["model"] == "SM-S948B"
    assert profile["recommendation"]["recommended_camera_id"] == "2"
    assert profile["recommendation"]["preferred_capture_mode"] == "solve_candidate_burst"
    assert profile["recommendation"]["preferred_format"] == "jpeg"
    assert profile["recommendation"]["runtime_support"] == "diagnostic_only"
    assert profile["recommendation"]["confidence"] == "MEDIUM"
    assert profile["evidence"]["total_reports"] == 2
    assert profile["evidence"]["solved_reports"] == 1
    assert profile["evidence"]["rejected_reports"] == 1
    assert profile["evidence"]["best_quality_score"] == 0.91
    assert profile["evidence"]["clear_sky_evidence"] is False
    assert "runtime_decision_blocked_until_59" in profile["caveats"]
    assert "thresholds_not_tuned_until_57" in profile["caveats"]
    raw = json.dumps(profile)
    assert "/home/pi/private" not in raw


def test_profile_generator_keeps_unknown_low_confidence_without_reports(tmp_path):
    tool = load_profile_tool()

    profile = tool.generate_mobile_camera_profile(
        reports_dir=tmp_path,
        device_model="UnknownPhone",
        manufacturer="unknown",
    )

    assert profile["recommendation"]["recommended_camera_id"] == "unknown"
    assert profile["recommendation"]["confidence"] == "UNKNOWN"
    assert profile["evidence"]["total_reports"] == 0
    assert profile["recommendation"]["runtime_support"] == "diagnostic_only"
    assert "clear_sky_phase2_required" in profile["caveats"]
