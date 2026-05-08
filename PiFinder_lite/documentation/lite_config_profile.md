# PiFinder Lite Config Profile

Issue: [#18 Add recommended PiFinder Lite config profile](https://github.com/oalexx/PiFinder_mobile_sensors/issues/18)

## Goal

Provide an optional PiFinder Lite configuration profile without changing classic
PiFinder defaults.

PiFinder currently uses two different kinds of startup settings:

- persistent user config in `~/PiFinder_data/config.json`;
- command-line flags passed to `python -m PiFinder.main`.

The Lite profile therefore has two parts: a JSON config example and recommended
startup commands.

## Config File

Example profile:

```text
PiFinder_lite/configs/pifinder_lite_config.example.json
```

This file is a user config example, not a replacement for `default_config.json`.
To try it on a Raspberry Pi:

```bash
mkdir -p ~/PiFinder_data
cp PiFinder_lite/configs/pifinder_lite_config.example.json ~/PiFinder_data/config.json
```

If a real `~/PiFinder_data/config.json` already exists, back it up first:

```bash
cp ~/PiFinder_data/config.json ~/PiFinder_data/config.before_lite.json
```

## Included Options

The profile only uses options that already exist in PiFinder:

```json
{
    "display_brightness": 32,
    "keypad_brightness": "0",
    "menu_anim_speed": 0.0,
    "text_scroll_speed": "Med",
    "sleep_timeout": "Off",
    "screen_off_timeout": "Off",
    "hint_timeout": "4s",
    "screen_direction": "right",
    "mount_type": "Alt/Az",
    "gps_type": "ublox",
    "gps_baud_rate": 9600,
    "solver_debug": 0
}
```

Why these values:

- `display_brightness`: low but visible for diagnostics; `/remote` still uses
  `/image`, so the normal UI remains active.
- `keypad_brightness`: off, because Lite mode should not rely on physical keypad
  feedback.
- `menu_anim_speed`: zero, to make remote navigation feel snappier.
- `sleep_timeout` and `screen_off_timeout`: off, to avoid the remote UI going
  quiet during a phone-controlled session.
- `hint_timeout`: short, so hints do not dominate the small remote screen.
- `gps_type` and `gps_baud_rate`: kept compatible with the current PiFinder GPS
  options. Mobile GPS is a later phase and does not exist yet.

## Startup Flags Still Required

The following Lite choices are not currently stored in `config.json`; they are
selected through command-line flags:

- camera module;
- keyboard module;
- fake hardware mode;
- display hardware override;
- fake GPS override.

Recommended development command:

```bash
cd python/
python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
```

Recommended Raspberry command when real camera/GPS/IMU are available but keypad
is not used:

```bash
cd python/
python3.9 -m PiFinder.main --keyboard none -x
```

Raspberry command when GPS hardware is not ready:

```bash
cd python/
python3.9 -m PiFinder.main --gps fake --keyboard none -x
```

Raspberry/development command when camera hardware is not ready:

```bash
cd python/
python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
```

## Current Limitation

PiFinder Lite is not yet a true `--mode mobile-lite` startup. The existing
application still starts the normal UI/display process model, web server, camera
process, solver, integrator, and SkySafari position server.

That is intentional for Phase 3: reuse the proven PiFinder backend first, then
add smaller optional Lite/mobile pieces later.

## Future Config Keys

Do not add these to `config.json` yet; they are proposed future work:

```json
{
    "mobile_lite": {
        "enabled": true,
        "gps_source": "mobile",
        "imu_source": "mobile",
        "camera_source": "pifinder",
        "remote_refresh_ms": 250
    }
}
```

These keys should only become real after the corresponding mobile bridge
endpoints and backend modules exist.

## Validation Checklist

1. Back up any existing `~/PiFinder_data/config.json`.
2. Copy the Lite example config into `~/PiFinder_data/config.json`.
3. Start PiFinder with one of the recommended commands above.
4. Open `/remote` from a phone browser.
5. Confirm the UI remains awake during navigation.
6. Confirm physical keypad brightness is not required.
7. Confirm classic startup still works after restoring the original config.

## Upstream Impact

No original PiFinder defaults are changed. This issue adds an optional example
profile and documentation under `PiFinder_lite/`.
