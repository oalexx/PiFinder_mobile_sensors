# PiFinder Mobile

Native Android companion prototype for exploring whether a phone can be used as
part of a PiFinder Lite setup.

The current app is focused on compatibility testing. It checks what the phone
actually exposes through public Android APIs, then runs capture tests that help
decide whether the phone can provide GPS, IMU/orientation, and experimental
camera data to a Raspberry Pi running PiFinder.

## Current Screens

### Check Capabilities

Checks the phone as a possible PiFinder companion device:

- Android version and model.
- Location/GPS availability.
- Accelerometer, gyroscope, magnetometer, rotation vector, and game rotation
  vector.
- Live IMU stream test.
- GPS sample test.
- Rear camera presence.
- Camera2 manual exposure/ISO support.
- RAW camera support.
- Overall PiFinder Lite readiness: `HIGH`, `MEDIUM`, or `LOW`.

The screen also exposes:

- `START IMU` to begin live sensor sampling.
- `STOP` to stop live sensor sampling.
- `RUN CHECK` to generate the compatibility result.
- `COPY REPORT` to copy the full technical report.

The compatibility result uses:

- `PASS` for confirmed capabilities.
- `WARN` for usable but limited capabilities.
- `FAIL` for missing critical capabilities.
- `NOT TESTED` for checks that need an active live sample.

### Camera Lab

Runs camera capture tests and saves images plus metadata to a user-selected
folder.

Always tap `SAVE FOLDER` before running a test.

Available tests:

- `DAY TEST`: automatic exposure/focus test for indoor or daylight framing.
- `MANUAL BURST`: high ISO, long exposure JPEG burst for sky testing.
- `ISO SWEEP`: multiple ISO groups for exposure comparison.
- `RAW BURST`: raw sensor byte captures for technical experiments.
- `CAM SWEEP`: tests the available rear camera IDs.

Each run creates a dated folder and writes images with descriptive names. The
metadata file is also named after the test run, for example:

```text
pifinder_camera_sweep_20260429_223538_metadata.txt
```

The metadata includes the camera ID, format, size, frame count, orientation,
ISO/exposure settings, saved frame count, and failures.

## Why This Exists

PiFinder already has useful remote/web control primitives:

- `/remote` for a web remote.
- `/image` for the current PiFinder screen.
- `/key_callback` for virtual button presses.
- SkySafari/LX200 support through PiFinder's position server.

The mobile app should not replace that work. The goal is to reuse the existing
PiFinder backend and add the phone-specific pieces that a normal web page cannot
reliably provide:

- Camera2 manual capture.
- RAW/camera diagnostics.
- High-rate Android sensors.
- GPS/time bridge.
- Future mobile-to-Pi sensor bridge.
- Future embedded PiFinder remote WebView.

## Open In Android Studio

Open the `mobile` folder in Android Studio and run the `app` configuration on
the phone.

If Android keeps showing an old launcher icon, uninstall the previous build from
the phone and run again.

## Suggested Test Flow

1. Open the app.
2. Go to `CHECK CAPABILITIES`.
3. Tap `START IMU`.
4. Move the phone gently for a few seconds.
5. Tap `STOP`.
6. Tap `RUN CHECK`.
7. Use `COPY REPORT` if the full diagnostic report is needed.
8. Go to `CAMERA LAB`.
9. Tap `SAVE FOLDER`.
10. Run `DAY TEST` indoors to check framing.
11. Run the sky tests outdoors at night:
    - `MANUAL BURST`
    - `ISO SWEEP`
    - `CAM SWEEP`
    - `RAW BURST`

## Future Direction

The intended long-term architecture is:

```text
Android app
  - Compatibility tester
  - GPS/IMU bridge
  - Camera bridge
  - PiFinder remote WebView
  - Calibration workflow

Raspberry Pi / PiFinder Lite
  - PiFinder backend
  - Catalogs and solver
  - Existing web remote
  - Existing SkySafari/LX200 server
  - New mobile API endpoints
```

The classic PiFinder hardware mode should remain unchanged. Mobile/Lite behavior
should be added as optional modules and configuration.

See [ROADMAP.md](ROADMAP.md) for the phased PiFinder Mobile / PiFinder Lite
development plan.
