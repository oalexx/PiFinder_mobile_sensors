from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_ACTIVITY = ROOT / "mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java"


def test_android_calibration_workflow_is_reachable_and_actionable():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeHeroButton("CALIBRATION"' in source
    assert 'showScreen("calibration")' in source
    assert 'addSectionHeader(calibrationScreen, "01", "CALIBRATION"' in source
    assert 'makeGridButton("Mount Ref")' in source
    assert 'sendCalibrationImuBatch("mounted_reference")' in source
    assert 'copyCalibrationEvidence()' in source
    assert 'updateCalibrationEvidenceJson("mounted_reference")' in source
    assert '"batch_label", batchLabel' in source


def test_android_calibration_screen_exposes_all_phase5_batch_labels():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'sendCalibrationImuBatch("stationary")' in source
    assert 'sendCalibrationImuBatch("mounted_reference")' in source
    assert 'sendCalibrationImuBatch("repeat_check")' in source
    assert 'makeGridButton("Stationary")' in source
    assert 'makeGridButton("Mount Ref")' in source
    assert 'makeGridButton("Repeat Check")' in source
    assert "private boolean isCalibrationBatchLabel(String batchLabel)" in source
    assert "updateCalibrationStatus(message)" in source
