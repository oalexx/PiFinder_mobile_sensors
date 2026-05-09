from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_ACTIVITY = ROOT / "mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java"


def test_android_camera_lab_exposes_guided_diagnostic_solve_flow():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makePrimaryButton("Run full diagnostic")' in source
    assert "runFullMobileCameraDiagnostic()" in source
    assert "fullDiagnosticRunning" in source
    assert "formatFullDiagnosticResult" in source
    assert 'makeAdvancedButton("Solve frame")' in source
    assert "requestDiagnosticCameraSolve()" in source
    assert '"/mobile/camera_solve"' in source
    assert "lastUploadedFrameId" in source
    assert '"frame_id", frameId' in source
    assert "formatDiagnosticSolveResult" in source
    assert '"quality_score"' in source
    assert '"solve_ok"' in source
    assert '"json_report"' in source
    assert '"summary"' in source
    assert '"advice"' in source
    assert '"message"' in source
    assert '"recommendation"' in source
    assert '"next_action"' in source
    assert 'updateMobileCameraDiagnosticGuide("full_running")' in source
    assert 'updateMobileCameraDiagnosticGuide("solving")' in source
    assert 'updateMobileCameraDiagnosticGuide("solve_complete")' in source


def test_android_camera_lab_exposes_diagnostic_report_history():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("View reports")' in source
    assert "requestCameraDiagnosticReports()" in source
    assert '"/mobile/camera_reports?limit=20"' in source
    assert "formatCameraReports" in source
    assert "latestCameraReportSummary" in source
    assert 'makeSecondaryButton("Copy summary")' in source
    assert "copyCameraReportSummary()" in source
    assert '"session_summary"' in source
    assert '"status_counts"' in source
    assert '"dominant_advice"' in source


def test_android_exposes_mobile_environment_metadata_bridge():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("Send env")' in source
    assert "sendEnvironmentToPiFinder()" in source
    assert "buildEnvironmentPayloadJson()" in source
    assert "postMobileEnvironment" in source
    assert '"/mobile/environment"' in source
    assert "Sensor.TYPE_LIGHT" in source
    assert "Sensor.TYPE_PRESSURE" in source
    assert '"ambient_light"' in source
    assert '"pressure"' in source
    assert '"battery"' in source
    assert '"network"' in source
    assert '"device_state"' in source
    assert "ConnectivityManager" in source
    assert "BatteryManager" in source


def test_android_camera_lab_exposes_phase2_night_test_wizard():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "phase2NightTestWizardView" in source
    assert 'addAreaTitle(cameraScreen, "Phase 2 checklist")' in source
    assert 'makeSecondaryButton("Night wizard")' in source
    assert "showPhase2NightTestWizard()" in source
    assert 'makeSecondaryButton("Copy night plan")' in source
    assert "copyPhase2NightTestPlan()" in source
    assert 'makeSecondaryButton("Mark repeat")' in source
    assert "markPhase2NightTestRepeat()" in source
    assert "phase2NightTestRepeatCount" in source
    assert "updatePhase2NightTestWizard" in source
    assert "phase2NightTestPlanText" in source
    assert "Phase 2 Night Test Wizard" in source
    assert "test completed" in source
    assert "camera proven reliable" in source
    assert "clear-sky evidence" in source
    assert "diagnostic-only" in source
    assert "SEND PROFILE" in source
    assert "SEND ENV" in source
    assert "SEND GPS" in source
    assert "Run full diagnostic" in source
    assert "View reports" in source


def test_android_full_diagnostic_ranks_dynamic_burst_candidates():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "SolveCandidateFrame" in source
    assert "SolveCandidateResult" in source
    assert "solveCandidateFrames" in source
    assert "recordSolveCandidateFrame" in source
    assert "candidateUploadLimitForBurst" in source
    assert "selectSolveCandidateFramesForUpload" in source
    assert "scoreSolveCandidateResult" in source
    assert "rankSolveCandidateResults" in source
    assert "formatSolveCandidateRanking" in source
    assert "selected by Raspberry score" in source
    assert "distributed across burst" in source
    assert "Run full diagnostic" in source
    assert "postMobileCameraFrame(" in source
    assert "candidate.filename" in source
    assert "postDiagnosticCameraSolve(baseUrl, frameId)" in source
    assert '"solve_candidate_selector"' in source
    assert '"ranking_summary"' in source
    assert '"selected_candidate"' in source
    assert "Upload JPEG" in source
    assert "manual debug" in source
