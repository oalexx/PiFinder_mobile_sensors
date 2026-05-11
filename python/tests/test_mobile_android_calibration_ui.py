from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_ACTIVITY = ROOT / "mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java"


def test_android_calibration_workflow_is_reachable_and_actionable():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeHeroButton("Calibration"' in source
    assert 'showScreen("calibration")' in source
    assert 'addPlainSectionHeader(calibrationScreen, "Calibration"' in source
    assert 'makePrimaryButton("Mount ref")' in source
    assert 'sendCalibrationImuBatch("mounted_reference")' in source
    assert 'copyCalibrationEvidence()' in source
    assert 'updateCalibrationEvidenceJson("mounted_reference")' in source
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


def test_android_calibration_screen_exposes_ai_imu_drift_analysis_evidence():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("AI IMU drift")' in source
    assert "showAiImuDriftAnalysisGuide()" in source
    assert "copyAiImuDriftAnalysisEvidence()" in source
    assert "aiImuDriftAnalysisEvidenceJson()" in source
    assert "AI IMU Drift Analysis" in source
    assert "solve-to-solve residual" in source
    assert '"/mobile/imu_drift_analysis"' in source
    assert '"diagnostic_only", true' in source
    assert '"integrator_updated", false' in source
    assert '"runtime_pointing_updated", false' in source
