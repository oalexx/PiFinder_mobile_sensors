from datetime import timezone

from PiFinder import mobile_bridge


def test_mobile_gps_queue_fix_maps_payload_to_pifinder_gps_fix():
    gps_fix = {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude_m": 667.5,
        "accuracy_m": 12.3,
        "time_utc": "2026-05-08T00:00:00Z",
        "source": "android",
        "provider": "fused",
    }

    queue_fix = mobile_bridge.mobile_gps_queue_fix(gps_fix)

    assert queue_fix == {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude": 667.5,
        "source": "MOBILE:android",
        "error_in_m": 12.3,
        "lock": True,
        "lock_type": 2,
        "provider": "fused",
        "time_utc": "2026-05-08T00:00:00Z",
    }


def test_mobile_gps_queue_fix_uses_conservative_defaults():
    gps_fix = {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude_m": None,
        "accuracy_m": None,
        "time_utc": "2026-05-08T00:00:00Z",
        "source": "android",
    }

    queue_fix = mobile_bridge.mobile_gps_queue_fix(gps_fix)

    assert queue_fix["altitude"] == 0
    assert queue_fix["error_in_m"] == mobile_bridge.DEFAULT_MOBILE_GPS_ERROR_M
    assert queue_fix["source"] == "MOBILE:android"
    assert queue_fix["lock"] is True


def test_mobile_gps_queue_time_parses_utc_timestamp():
    gps_fix = {
        "lat": 40.4168,
        "lon": -3.7038,
        "altitude_m": None,
        "accuracy_m": None,
        "time_utc": "2026-05-08T00:01:02Z",
        "source": "android",
    }

    gps_time = mobile_bridge.mobile_gps_queue_time(gps_fix)

    assert gps_time.year == 2026
    assert gps_time.month == 5
    assert gps_time.day == 8
    assert gps_time.hour == 0
    assert gps_time.minute == 1
    assert gps_time.second == 2
    assert gps_time.tzinfo == timezone.utc


def test_validate_imu_payload_preserves_calibration_label_and_metadata():
    payload = {
        "schema": "pifinder-mobile-imu-batch-v0",
        "batch_label": "mounted_reference",
        "capture_duration_ms": 2000,
        "device_time_utc": "2026-05-08T00:00:00Z",
        "screen_orientation": "portrait",
        "app_version": "debug",
        "device": {
            "manufacturer": "samsung",
            "model": "SM-S948B",
        },
        "samples": [
            {
                "sensor": "game_rotation_vector",
                "t_android_ns": 0,
                "values": [0.0, 0.0, 0.0, 1.0],
                "accuracy": 3,
                "time_utc": "2026-05-08T00:00:00Z",
            }
        ],
    }

    imu_batch, error = mobile_bridge.validate_imu_payload(payload)

    assert error is None
    assert imu_batch["batch_label"] == "mounted_reference"
    assert imu_batch["capture_duration_ms"] == 2000.0
    assert imu_batch["screen_orientation"] == "portrait"
    assert imu_batch["app_version"] == "debug"
    assert imu_batch["device"]["model"] == "SM-S948B"


def test_validate_imu_payload_rejects_unknown_batch_label():
    payload = {
        "batch_label": "surprise_mode",
        "samples": [
            {
                "sensor": "game_rotation_vector",
                "t_android_ns": 0,
                "values": [0.0, 0.0, 0.0, 1.0],
            }
        ],
    }

    imu_batch, error = mobile_bridge.validate_imu_payload(payload)

    assert imu_batch == {}
    assert error == (
        "batch_label must be one of: diagnostic, mounted_reference, "
        "repeat_check, slew, stationary."
    )
