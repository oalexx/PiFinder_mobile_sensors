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

Status: completed.

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

Status: still active. Day-test and cloudy/partial-sky evidence exists, but the
remaining decision needs clearer night captures.

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
- Whether the image quality score accepts the frame without being fooled by a
  raised ISO/noise floor.
- Whether the solve-candidate burst produces better frames than the older
  manual burst.

Decision:

- If solving is reliable, continue with the mobile camera path.
- If solving is partial, adjust capture settings and frame selection.
- If solving is unreliable, keep the phone as UI/GPS/IMU and use a dedicated
  USB/ASI/Pi camera for plate solving.

## Phase 3: PiFinder Lite Headless

Goal: run PiFinder without a physical screen or keypad.

Status: completed and Raspberry-validated.

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

Status: completed and Raspberry-validated.

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

- Mobile API module plus a small `server.py` extension.
- Runtime mobile GPS injection through the existing GPS queue.
- IMU batch storage for confidence analysis.
- Storage-only camera frame upload for diagnostics.

Validated behavior:

- `/mobile/status` reports bridge capabilities.
- `/mobile/profile` stores app/device profile data.
- `/mobile/gps` updates the running PiFinder GPS state.
- `/mobile/imu` stores diagnostic rotation-vector batches.
- `/mobile/camera_frame` stores uploaded JPEG frames and metadata.

Deferred from Phase 4:

- Mobile IMU is not yet integrated into the PiFinder integrator.
- Mobile camera frames are not yet integrated into the live solver loop.
- Mobile camera solving remains a diagnostic script flow until Phase 2 validates
  reliable clear-sky frames.

## Phase 5: Phone-To-Telescope Calibration

Goal: when the phone is mounted to the telescope, align the phone axes with the
optical tube axis.

Status: implemented up to diagnostic/read-only overlay. Field validation remains
open in #52 before any optional guidance or integrator-adjacent work.

Input from Phase 4: `game_rotation_vector` produced the best stationary
confidence in the first Raspberry tests, so it should be the first sensor path
considered for calibration experiments. `rotation_vector` remains useful for
comparison but may show more magnetic/noise sensitivity.

Workflow:

1. Mount the phone rigidly.
2. Point to a known star or object.
3. Resolve an image or use a known position.
4. Calculate the offset between phone orientation and optical axis.
5. Save the mount profile.

Recommended first implementation:

- Store labeled IMU batches: `stationary`, `slew`, `mounted_reference`.
- Add a mount-profile JSON editor/export in the Android app.
- Keep calibration output advisory until repeatability is proven.
- Phase 5 decision: calibrated mobile IMU may move next to a diagnostic
  overlay/read-only guidance aid, but must not feed the PiFinder integrator yet.

Implemented in Phase 5:

- Android Calibration workflow for labeled IMU evidence.
- Raspberry scripts for candidate offset calculation and repeatability checks.
- Mount profile schema and disabled-by-default example config.
- `/mobile/mount_profile` read-only profile endpoint.
- Android `CHECK PROFILE` read-only overlay/status view.

Remaining Phase 5 gate:

- #52: Field-validate the calibrated mobile IMU overlay with a real mounted
  session. A cloudy or poor night can validate remount/drift logging and UI
  workflow, but it cannot promote the overlay beyond diagnostic/read-only. A
  clear enough observing session is still needed before optional guidance.

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

Input from Phase 4: upload/storage works, quality scoring works, and diagnostic
solve tooling runs on Raspberry. The missing gate is reliable night-sky evidence
from Phase 2.

Steps:

- Send JPEG frames from the app.
- Save each frame with metadata.
- Pass frames to the solver.
- Measure upload time and solve time.
- Test bursts.
- Automatically choose the best frame.
- Evaluate RAW only if real sky data shows that it adds enough value.

Recommended first implementation after Phase 2 passes:

- Trigger solve only for frames accepted by the quality score.
- Prefer dark background, sufficient centroid count, low saturation, and low
  noise floor.
- Avoid selecting high-ISO frames whose lifted background mimics useful signal.
- Record upload latency, quality-score latency, solve latency, and solve result
  in one per-frame report.

Phase 6 issue plan:

- #54: Add a diagnostic mobile frame solve job endpoint.
- #55: Add an Android guided upload-and-diagnostic-solve workflow.
- #56: Persist mobile camera diagnostic solve reports.
- #57: Tune mobile camera quality thresholds from accepted/rejected night
  frames.
- #58: Evaluate RAW mobile frames for diagnostic solving.
- #59: Decide the mobile camera runtime path after diagnostic solves.

Work that can proceed before a good night:

- Diagnostic endpoint/job scaffolding using existing uploaded frames.
- Android result UI and timeout/error handling.
- Local report persistence and sanitization rules.

Work blocked by Phase 2 clear-sky evidence:

- Quality threshold tuning.
- RAW value decision.
- Any decision to promote mobile camera beyond diagnostic/manual solve.

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

Current AI/process status:

- The first image-quality score is classic image processing, not ML.
- IMU confidence analysis is classic quaternion/statistical analysis.
- Keep ML/ONNX/TFLite experiments behind explicit flags and only after the
  simple metrics fail on real data.

## Recommended Issues

Implemented or closed:

- Polish Android Compatibility Tester UI.
- Add structured compatibility result.
- Add mobile profile JSON export.
- Improve camera test metadata.
- Document existing PiFinder web remote.
- Create PiFinder Lite headless startup mode.
- Add PiFinder Remote WebView to Android app.
- Add mobile connection settings.
- Add mobile GPS bridge endpoint and runtime GPS feed.
- Add mobile IMU bridge endpoint and confidence analysis.
- Add mobile profile endpoint.
- Upload mobile JPEG frames to PiFinder.
- Add image quality score.
- Add burst frame selector / solve-candidate burst.
- Validate SkySafari split-screen workflow.
- Implement phone-to-telescope calibration tooling.
- Add read-only calibrated mobile IMU overlay.

Still open / next:

- Complete Phase 2 night-sky validation.
- Compare Manual Burst, ISO Sweep, Cam Sweep, and RAW Burst under clearer sky.
- Summarize the mobile camera solve decision from real night evidence.
- Field-validate the calibrated mobile IMU overlay (#52).
- Build the Phase 6 diagnostic mobile camera solve workflow (#54-#56).
- Tune/promote mobile camera frames only if Phase 2 evidence supports it
  (#57-#59).
- Add exposure advisor after enough accepted/rejected night frames exist.

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
8. Field-validate calibration as read-only overlay.
9. Add mobile camera diagnostic solve path.
10. Add optional AI helpers after real sky data exists.
