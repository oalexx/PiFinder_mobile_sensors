# PiFinder Lite Headless Startup

This document describes the first PiFinder Lite / Mobile Companion startup mode:
run the existing PiFinder backend without relying on the physical keypad as the
primary user interface, then control it from a phone, tablet, or browser through
the existing web remote.

The goal is not to replace classic PiFinder. Classic hardware startup should
remain unchanged. PiFinder Lite should be an optional way to reuse the current
backend, solver, catalogs, web remote, and SkySafari/LX200 support.

Phase 4 mobile bridge endpoints are specified separately in
`PiFinder_lite/mobile_bridge_api_v0.md`. The recommended Phase 4 order and
dependency gates are tracked in `PiFinder_lite/phase4_dependency_map.md`.

## Current Status

The current codebase already has most of the pieces needed for a first headless
workflow:

- `python/PiFinder/main.py` starts the normal multiprocess PiFinder backend.
- `--keyboard none` selects `keyboard_none.py`, which keeps the keyboard process
  alive without reading physical keys.
- The web server starts automatically from `main.py`.
- `/remote` exposes the existing browser remote.
- `/image` returns the current PiFinder screen as a PNG.
- `/key_callback` accepts virtual key presses from the web remote.
- `pos_server.py` starts the SkySafari/LX200-compatible position server on port
  `4030`.

This means Phase 3 can start by documenting and validating the existing behavior
before adding any new mobile bridge endpoints.

## Recommended Development Startup

Use this on a development machine or Raspberry Pi when you want to test the
Lite/headless flow without relying on real GPS/IMU hardware:

```bash
cd python/
python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
```

What each flag does:

- `-fh` / `--fakehardware`: uses fake IMU and fake GPS modules.
- `--camera debug`: uses the debug camera module instead of Pi camera hardware.
- `--keyboard none`: starts the no-op keyboard process.
- `-x` / `--verbose`: enables debug logging.

This is the safest first command for validating the web remote because it avoids
physical hardware dependencies while keeping the normal PiFinder process model.

## Recommended Raspberry Pi Startup

For a Raspberry Pi with real PiFinder camera/display stack but no physical keypad
workflow, start with:

```bash
cd python/
python3.9 -m PiFinder.main --keyboard none -x
```

For a Raspberry Pi where you want to avoid camera hardware during early headless
testing:

```bash
cd python/
python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
```

For a Raspberry Pi where GPS hardware is not ready but the rest of the system is
being tested:

```bash
cd python/
python3.9 -m PiFinder.main --gps fake --keyboard none -x
```

`main.py` currently supports:

- `--camera pi`
- `--camera asi`
- `--camera debug`
- `--camera none`
- `--gps pi`
- `--gps fake`
- `--keyboard pi`
- `--keyboard local`
- `--keyboard none`
- `--display <hardware>`

The default classic behavior remains `--camera pi --gps pi --keyboard pi`.

## Accessing The Web Remote

When PiFinder starts, the web server binds to all interfaces:

```text
0.0.0.0:80
```

If port `80` is unavailable, it falls back to:

```text
0.0.0.0:8080
```

From a phone or browser on the same network, open one of:

```text
http://<pifinder-ip>/remote
http://<pifinder-ip>:8080/remote
```

Useful endpoints:

```text
/remote        Browser remote UI
/image         Current PiFinder screen as PNG
/key_callback  POST endpoint used by the remote for virtual keys
/              Main web interface
/gps           Web GPS/location page
/network       Network settings page
/equipment     Telescope/eyepiece settings page
/logs          Log viewer
```

Important: `/remote` is protected by the existing web authentication flow. If
prompted, log in using the configured PiFinder web password.

## SkySafari / LX200

`pos_server.py` binds a socket server on port:

```text
4030
```

This server implements a lightweight LX200-style protocol used by SkySafari and
similar clients.

SkySafari configuration target:

```text
Host: <pifinder-ip>
Port: 4030
Protocol: LX200 / Meade-compatible telescope
```

The intended Lite workflow is:

```text
SkySafari -> LX200 port 4030 -> PiFinder
PiFinder -> /remote and /image -> phone browser or Android WebView
Phone browser -> /key_callback -> PiFinder UI queue
```

## Validation Checklist

Use this checklist for issue #13/#14/#15 validation.

1. Start PiFinder with:

   ```bash
   cd python/
   python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
   ```

2. Confirm the process reaches the main UI loop without physical keypad input.

3. Find the Raspberry Pi IP address.

4. Open the web UI from another device:

   ```text
   http://<pifinder-ip>/
   ```

5. Open the remote:

   ```text
   http://<pifinder-ip>/remote
   ```

   If port `80` is unavailable, use:

   ```text
   http://<pifinder-ip>:8080/remote
   ```

6. Confirm `/image` returns a PNG:

   ```text
   http://<pifinder-ip>/image
   ```

7. Press remote buttons and confirm the PiFinder UI responds.

8. Open SkySafari and connect to:

   ```text
   <pifinder-ip>:4030
   ```

9. Record:

   - Startup command used.
   - PiFinder IP address.
   - Whether the web server used port `80` or `8080`.
   - Whether `/remote` loaded.
   - Whether `/image` updated.
   - Whether virtual buttons worked.
   - Whether SkySafari connected to port `4030`.
   - Any crashes, permission issues, or missing hardware assumptions.

## Known Limitations

This is a first headless workflow, not a finished Lite mode.

- The main process still starts the normal display/UI stack.
- `--keyboard none` disables physical key input, but it does not remove the UI
  loop.
- The web remote UI may need mobile layout improvements.
- The web remote depends on the current `/image` polling approach.
- GPS/IMU are still PiFinder-side modules unless fake hardware is selected.
- Android GPS/IMU/camera bridge endpoints do not exist yet.
- The mobile app WebView shell is a separate Phase 3 issue.

## What This Phase Should Not Do Yet

Keep Phase 3 narrow:

- Do not add `/mobile/gps`, `/mobile/imu`, or `/mobile/camera_frame` yet.
- Do not replace the existing solver/integrator.
- Do not change default classic PiFinder startup.
- Do not make phone camera solving decisions before Phase 2 night tests.

## Follow-Up Work

The next Phase 3 tasks are:

- Validate `keyboard none` / no physical keypad workflow.
- Validate `/remote`, `/image`, and `/key_callback` from a phone browser.
- Improve the `/remote` mobile layout.
- Validate SkySafari plus PiFinder Remote split-screen usage.
- Add/use the recommended PiFinder Lite config profile in
  `PiFinder_lite/lite_config_profile.md`.
- Add an Android WebView shell that opens the existing `/remote` page.

The next Phase 4 tasks are:

- Define Mobile Bridge API v0.
- Add `/mobile/status`.
- Add `/mobile/profile`.
- Add `/mobile/gps`.
- Add Android connection/profile/GPS actions.
- Defer IMU/camera/integrator work until validation data exists.
