from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_ACTIVITY = ROOT / "mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java"


def test_android_calibration_workflow_is_reachable_and_actionable():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeHeroButton("Calibration"' in source
    assert 'showScreen("calibration")' in source
    assert 'addPlainSectionHeader(calibrationScreen, "Calibration"' in source
    assert 'addCalibrationChecklistToggle(calibrationScreen)' in source
    assert 'makePrimaryButton("Mount ref")' in source
    assert 'sendCalibrationImuBatch("mounted_reference")' in source
    assert 'copyCalibrationEvidence()' in source
    assert "latestCalibrationBatchLabel" in source
    assert "updateCalibrationEvidenceJson(latestCalibrationBatchLabel)" in source
    assert '"batch_label", batchLabel' in source


def test_android_calibration_screen_exposes_all_phase5_batch_labels():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'sendCalibrationImuBatch("stationary")' in source
    assert 'sendCalibrationImuBatch("mounted_reference")' in source
    assert 'sendCalibrationImuBatch("repeat_check")' in source
    assert 'makePrimaryButton("Stationary")' in source
    assert 'makePrimaryButton("Mount ref")' in source
    assert 'makePrimaryButton("Repeat check")' in source
    assert "private boolean isCalibrationBatchLabel(String batchLabel)" in source
    assert "updateCalibrationStatus(message)" in source


def test_android_calibration_screen_exposes_read_only_mount_profile_overlay():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("Check profile")' in source
    assert "checkMobileMountProfile()" in source
    assert '"/mobile/mount_profile"' in source
    assert "formatMountProfileOverlay" in source
    assert '"overlay_candidate"' in source
    assert '"runtime_usable"' in source
    assert '"read_only"' in source
    assert "updateCalibrationStatus(message)" in source
    assert "Mount profile endpoint not available" in source
    assert "Update the PiFinder Lite backend or continue without profile overlay." in source


def test_android_calibration_screen_exposes_optical_boresight_recalibration():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("Optical guide")' in source
    assert 'makePrimaryButton("Optical align")' in source
    assert 'makeSecondaryButton("Check optical")' in source
    assert "runOpticalBoresightCalibration()" in source
    assert "checkOpticalBoresightProfile()" in source
    assert "buildOpticalBoresightPayloadJson()" in source
    assert '"/mobile/optical_boresight"' in source
    assert '"pifinder-mobile-optical-boresight-calibration-v0"' in source
    assert '"reference_ra_deg"' in source
    assert '"reference_dec_deg"' in source
    assert "Optical boresight OK" in source
    assert "Offset RA" in source
    assert "Offset Dec" in source
    assert "Angular offset" in source
    assert '"diagnostic_only", true' in source
    assert '"integrator_updated", false' in source
    assert '"runtime_pointing_updated", false' in source


def test_android_optical_boresight_uses_dedicated_full_diagnostic_frame():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "private String opticalBoresightFrameId = \"\";" in source
    assert "opticalBoresightFrameId = \"\";" in source
    assert "opticalBoresightFrameId = selected.frameId;" in source
    assert "lastUploadedFrameId = json.optString(\"frame_id\", \"\");" in source
    assert "String frameId = opticalBoresightFrameId == null ? \"\" : opticalBoresightFrameId.trim();" in source
    assert 'payload.put("frame_id", frameId);' in source
    assert 'payload.put("frame_source", "full_diagnostic_selected_candidate");' in source


def test_android_calibration_screen_exposes_ai_imu_drift_analysis_evidence():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("AI IMU drift")' in source
    assert 'makeSecondaryButton("Start AI session")' in source
    assert 'makeSecondaryButton("Initial solve")' in source
    assert 'makeSecondaryButton("Start move")' in source
    assert 'makeSecondaryButton("Finish cycle")' in source
    assert 'makeSecondaryButton("Analyze drift")' in source
    assert "startAiImuDriftSession()" in source
    assert "captureAiImuDriftInitialSolve()" in source
    assert "startAiImuDriftMove()" in source
    assert "finishAiImuDriftCycle()" in source
    assert "analyzeAiImuDriftSession()" in source
    assert "showAiImuDriftAnalysisGuide()" in source
    assert "copyAiImuDriftAnalysisEvidence()" in source
    assert "aiImuDriftAnalysisEvidenceJson()" in source
    assert "aiImuDriftSessionPayloadJson()" in source
    assert "postAiImuDriftAnalysis(" in source
    assert "aiImuDriftCycles" in source
    assert "aiImuDriftInitialSolveAltAz" in source
    assert "aiImuDriftMoveStartOrientation" in source
    assert "AI IMU Drift Analysis" in source
    assert "solve-to-solve residual" in source
    assert '"/mobile/imu_drift_analysis"' in source
    assert '"/mobile/camera_solve"' in source
    assert '"diagnostic_only", true' in source
    assert '"integrator_updated", false' in source
    assert '"runtime_pointing_updated", false' in source


def test_android_calibration_phone_mount_checklist_is_collapsed_before_status():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "private boolean calibrationChecklistExpanded = false;" in source
    assert "addCalibrationChecklistToggle(LinearLayout root)" in source
    assert 'makeHeaderButton("Phone mount checklist")' in source
    assert "toggleCalibrationChecklist()" in source
    assert "calibrationChecklistView.setVisibility(View.GONE)" in source
    assert "calibrationChecklistView.setVisibility(calibrationChecklistExpanded ? View.VISIBLE : View.GONE)" in source
    assert "updateCalibrationChecklistToggleLabel()" in source
    assert '"▾ Show Phone Mount Checklist"' in source
    assert '"▴ Hide Phone Mount Checklist"' in source
    assert "calibrationChecklistToggleButton.setTypeface(Typeface.DEFAULT_BOLD)" in source

    checklist_index = source.index("addCalibrationChecklistToggle(calibrationScreen)")
    status_index = source.index("calibrationStatusView = statusCard()")
    assert checklist_index < status_index


def test_android_diagnostics_remembers_successful_live_imu_after_stop():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "private boolean liveImuEverSampleReceived = false;" in source
    assert "liveImuEverSampleReceived = true;" in source
    assert "if (!liveImuStarted && !liveImuEverSampleReceived)" in source
    assert "PASS  Live IMU stream: sensor samples received" in source
