# PiFinder Mobile / PiFinder Lite Roadmap

This document turns the mobile companion idea into an implementation roadmap.
The guiding principle is to keep classic PiFinder behavior unchanged and add
mobile/lite behavior through optional modules, flags, and configuration.

## Goal

Create an extended PiFinder mode where an Android phone can act as a display,
GPS source, IMU source, experimental camera, and configuration companion.

The recommended strategy is to reuse the existing PiFinder backend instead of
rewriting it:

- Web server and `/remote`.
- `/image` and `/key_callback`.
- SkySafari/LX200 position server.
- Existing solver, catalogs, integrator, and multiprocessing architecture.

## Proposed Architecture

```text
Android app
  - Compatibility tester
  - Camera lab
  - GPS / IMU bridge
  - PiFinder remote WebView
  - Calibration workflow
  - Future camera frame uploader

Raspberry Pi / PiFinder Lite
  - Original PiFinder backend
  - Solver, catalogs, and integrator
  - Existing web remote
  - Existing SkySafari/LX200 server
  - New mobile API endpoints
```

Classic PiFinder should continue to run exactly as it does today. Mobile
features should enter through explicit choices such as:

```bash
python -m PiFinder.main --keyboard none --gps mobile --imu mobile --camera mobile
```

or later:

```bash
python -m PiFinder.main --mode mobile-lite
```

## Phase 1: Finish The Mobile Tester

Goal: make the current Android app a reliable compatibility tester.

Tasks:

- Polish the current Home, Check Capabilities, and Camera Lab UI.
- Separate `Copy Check Result` from `Copy Tech Report`.
- Export a structured phone profile as JSON.
- Store historical compatibility check results.
- Improve capture metadata.
- Add app version and build version to reports.
- Validate launcher icon, permissions, JPEG orientation, and saved output.

Expected result: a user installs the app, runs the checks, and gets a clear
PiFinder Lite readiness result: `HIGH`, `MEDIUM`, or `LOW`.

## Phase 2: Night Sky Validation

Goal: determine whether phone camera frames are actually useful for plate
solving.

Tests:

- `DAY TEST`: framing and focus.
- `MANUAL BURST`: real sky JPEG captures.
- `ISO SWEEP`: sensitivity and noise comparison.
- `CAM SWEEP`: choose the best rear camera.
- `RAW BURST`: evaluate whether RAW adds value.

Validation criteria:

- Visible star count.
- Saturation.
- Noise.
- Stability.
- Whether Tetra3/PiFinder can solve the frame.
- Solve time.

Decision:

- If solving is reliable, continue with the mobile camera path.
- If solving is partial, adjust capture settings and frame selection.
- If solving is unreliable, keep the phone as UI/GPS/IMU and use a dedicated
  USB/ASI/Pi camera for plate solving.

## Phase 3: PiFinder Lite Headless

Goal: run PiFinder without a physical screen or keypad.

Reuse existing pieces:

- `keyboard_none.py`.
- Web server.
- `/remote`.
- `/image`.
- `/key_callback`.
- `pos_server.py` for SkySafari/LX200.

Tasks:

- Document the headless startup mode.
- Create a recommended configuration.
- Test mobile browser access to `/remote`.
- Improve the web remote UX for phones.
- Validate split-screen usage with SkySafari and PiFinder Mobile.

Expected flow:

```text
SkySafari -> LX200 -> PiFinder
PiFinder -> /remote /image -> Android app
Android app -> GPS/IMU/camera -> PiFinder
```

## Phase 4: Mobile Bridge

Goal: allow the Android app to send phone data to PiFinder.

Suggested endpoints:

```text
/mobile/profile
/mobile/gps
/mobile/imu
/mobile/camera_frame
/mobile/status
```

Phone data:

- GPS and time.
- Phone model.
- Sensor profile.
- Rotation vector and game rotation vector.
- Battery state.
- Screen orientation.
- Recommended camera.

PiFinder implementation candidates:

- `gps_mobile.py`.
- `imu_mobile.py`.
- `camera_mobile.py`.
- New mobile API module or a small extension to `server.py`.

## Phase 5: Phone-To-Telescope Calibration

Goal: when the phone is mounted to the telescope, align the phone axes with the
optical tube axis.

Workflow:

1. Mount the phone rigidly.
2. Point to a known star or object.
3. Resolve an image or use a known position.
4. Calculate the offset between phone orientation and optical axis.
5. Save the mount profile.

Persisted data example:

```json
{
  "mount_profile": {
    "phone_model": "samsung SM-S948B",
    "axis_mapping": "...",
    "yaw_offset": 0.0,
    "pitch_offset": 0.0,
    "roll_offset": 0.0
  }
}
```

## Phase 6: Phone Camera As A Sensor

Goal: send Android frames to the Raspberry Pi and solve them with the existing
PiFinder solver path.

Steps:

- Send JPEG frames from the app.
- Save each frame with metadata.
- Pass frames to the solver.
- Measure upload time and solve time.
- Test bursts.
- Automatically choose the best frame.
- Evaluate RAW only if real sky data shows that it adds enough value.

## Optional AI Layer

AI should be an optional helper layer, not a replacement for the current solver
and integrator.

```text
Image capture
  -> optional AI preprocessor
  -> existing solver
  -> existing integrator
```

Priority use cases:

1. Image quality score: visible stars, blur, saturation, noise, clouds.
2. Frame selector: choose the best frames from a burst before solving.
3. Exposure advisor: suggest ISO/exposure from detected stars.
4. Star candidate detection: improve noisy phone images.
5. Cloud / obstruction detection: clouds, branches, roof, lamps, burned frame.
6. IMU confidence filter: detect jumps, drift, magnetic interference, and
   inconsistent data.
7. Solver failure predictor: estimate whether a solve attempt is worth the CPU.
8. Calibration assistant: detect phone mount drift or bad alignment.

Initial software preference:

- Start with classic OpenCV.
- Use NumPy and scikit-image metrics when helpful.
- Consider lightweight ONNX/TFLite models only if classic image processing is
  insufficient.
- Avoid heavy models early.

Suggested configuration:

```json
{
  "ai": {
    "enabled": false,
    "image_quality_filter": true,
    "frame_selector": true,
    "exposure_advisor": true,
    "imu_confidence_filter": true,
    "star_detector": false
  }
}
```

## Recommended Issues

1. Polish Android Compatibility Tester UI.
2. Add structured compatibility result.
3. Add mobile profile JSON export.
4. Improve camera test metadata.
5. Run night sky validation.
6. Document existing PiFinder web remote.
7. Create PiFinder Lite headless startup mode.
8. Add PiFinder Remote WebView to Android app.
9. Add mobile connection settings.
10. Add mobile GPS bridge endpoint.
11. Add mobile IMU bridge endpoint.
12. Add mobile profile endpoint.
13. Implement mobile-to-telescope calibration.
14. Upload mobile JPEG frames to PiFinder.
15. Run plate solve on mobile camera frames.
16. Add image quality score.
17. Add burst frame selector.
18. Add exposure advisor.
19. Add IMU confidence filter.
20. Validate SkySafari split-screen workflow.

## Main Risks

- The phone camera may not solve reliably.
- Public Camera2 APIs may expose less than Samsung or other OEM camera apps use.
- Phone IMU data may drift or suffer magnetic interference.
- Integrating phone IMU data into the existing integrator is delicate.
- The existing web remote works but needs a better phone UX.
- RAW capture may be expensive without adding enough solve value.

## Execution Order

1. Stabilize the tester.
2. Run night sky tests.
3. Build PiFinder headless plus web remote workflow.
4. Add the WebView to the Android app.
5. Add the GPS bridge.
6. Add the IMU bridge.
7. Add calibration.
8. Add mobile camera frame upload and solve path.
9. Add optional AI helpers after real sky data exists.
