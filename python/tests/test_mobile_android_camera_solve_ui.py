from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_ACTIVITY = ROOT / "mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java"


def test_android_camera_lab_exposes_guided_diagnostic_solve_flow():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeGridButton("Run Full Diagnostic")' in source
    assert "runFullMobileCameraDiagnostic()" in source
    assert "fullDiagnosticRunning" in source
    assert "formatFullDiagnosticResult" in source
    assert 'makeGridButton("Diagnostic Solve")' in source
    assert "requestDiagnosticCameraSolve()" in source
    assert '"/mobile/camera_solve"' in source
    assert "lastUploadedFrameId" in source
    assert '"frame_id", frameId' in source
    assert "formatDiagnosticSolveResult" in source
    assert '"quality_score"' in source
    assert '"solve_ok"' in source
    assert '"json_report"' in source
    assert '"summary"' in source
    assert '"recommendation"' in source
    assert '"next_action"' in source
    assert 'updateMobileCameraDiagnosticGuide("full_running")' in source
    assert 'updateMobileCameraDiagnosticGuide("solving")' in source
    assert 'updateMobileCameraDiagnosticGuide("solve_complete")' in source
