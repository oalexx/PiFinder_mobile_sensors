# PiFinder Mobile

Native Android companion prototype for exploring whether a phone can be used as
part of a PiFinder Lite setup.

The current app now covers the Phase 1 tester, the Phase 4 bridge prototype,
and the Phase 5 calibration evidence flow. It checks what the phone actually
exposes through public Android APIs, runs capture tests, loads the existing
PiFinder `/remote` page, and can send GPS, IMU batches, profile data, mount
calibration evidence, and JPEG diagnostic frames to a Raspberry Pi running
PiFinder Lite.

Current validated bridge status:

- `/mobile/status` connection check works.
- `SEND PROFILE` posts the structured phone profile.
- `SEND GPS` can feed the running PiFinder process.
- `SEND IMU BATCH` stores a short diagnostic batch for confidence analysis.
- `CALIBRATION` stores labeled `stationary`, `mounted_reference`, and
  `repeat_check` IMU batches.
- `UPLOAD LAST JPEG` stores a diagnostic JPEG on the Raspberry.
- `CALIBRATION` starts the Phase 5 phone-to-telescope evidence flow.

Camera and IMU data are still diagnostic paths. Live mobile camera solving and
mobile IMU integration are intentionally deferred until later phases. The
current calibrated IMU path is read-only overlay/status only.

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
- `SOLVE CANDIDATE BURST`: tuned JPEG capture for PiFinder Lite diagnostics.
- `UPLOAD LAST JPEG`: sends the newest saved JPEG to `/mobile/camera_frame`.
- `DIAGNOSTIC SOLVE`: asks PiFinder to score and diagnostic-solve the uploaded
  frame via `/mobile/camera_solve`.

Each run creates a dated folder and writes images with descriptive names. The
metadata file is also named after the test run, for example:

```text
pifinder_camera_sweep_20260429_223538_metadata.txt
```

The metadata includes the camera ID, format, size, frame count, orientation,
ISO/exposure settings, saved frame count, and failures.

### PiFinder Remote

Connects the app to a Raspberry/PiFinder Lite instance.

Available actions:

- `TEST CONNECTION`: checks `/mobile/status`.
- `OPEN REMOTE`: opens the existing PiFinder `/remote` page full-screen.
- `SEND PROFILE`: sends the phone capability/profile JSON.
- `SEND GPS`: posts the current Android location to PiFinder.
- `SEND IMU BATCH`: captures and uploads a short rotation-vector batch.
- `MOUNT REF IMU`: captures a still phone/tube reference batch for Phase 5
  calibration experiments from the remote tools screen.

The embedded remote is a wrapper around the existing PiFinder web UI. If layout
issues appear, compare it with the same URL in a normal browser before changing
PiFinder server-side CSS.

### Calibration

Collects Phase 5 phone-to-telescope evidence without enabling mobile IMU
pointing.

Available actions:

- `TEST CONNECTION`: checks the saved PiFinder base URL.
- `SEND PROFILE`: uploads the current phone capability profile.
- `CHECK PROFILE`: reads `GET /mobile/mount_profile` and shows the mounted
  profile as a read-only overlay/status card.
- `SEND GPS`: uploads the current Android location.
- `STATIONARY`: uploads a labeled `stationary` IMU batch while the mounted
  phone and tube remain still.
- `MOUNT REF`: uploads a labeled `mounted_reference` IMU batch against the
  selected reference target/note.
- `REPEAT CHECK`: uploads a labeled `repeat_check` IMU batch after returning
  to the same reference.
- `COPY EVIDENCE`: copies a calibration evidence JSON with the reference note,
  app/device metadata, readiness, optional location, and expected batch label.

Use the reference field for the star/object/manual pointing note used during
the capture. The flow is intentionally manual and diagnostic-only; the uploaded
batches do not feed PiFinder pointing or the integrator.

`CHECK PROFILE` is also diagnostic-only. It can show whether the loaded mount
profile is an overlay candidate, but `runtime_usable` remains false during
Phase 5 and the integrator stays blocked.

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

Android Studio may suggest an Android Gradle Plugin upgrade. Leave that alone
unless the task is specifically to upgrade the build tooling; the current build
has been validated as-is.

Command-line debug APK build:

```powershell
cd mobile
.\gradlew.bat assembleDebug
```

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
11. Go to `PIFINDER REMOTE`, set the Raspberry base URL, then run:
    - `TEST CONNECTION`
    - `SEND PROFILE`
    - `SEND GPS`
    - `SEND IMU BATCH`
12. Go back to `CAMERA LAB`, run `SOLVE CANDIDATE BURST`, then tap
    `UPLOAD LAST JPEG`.
13. Tap `DIAGNOSTIC SOLVE` to display quality score, solve/skipped state, and
    the Raspberry report path.
14. Run the sky tests outdoors at night when conditions allow:
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
  - Diagnostic camera bridge
  - PiFinder remote WebView
  - Calibration workflow

Raspberry Pi / PiFinder Lite
  - PiFinder backend
  - Catalogs and solver
  - Existing web remote
  - Existing SkySafari/LX200 server
  - Mobile API endpoints
```

The classic PiFinder hardware mode should remain unchanged. Mobile/Lite behavior
should be added as optional modules and configuration.

Next gates:

- Complete Phase 2 clear-sky camera validation.
- Field-validate the Phase 5 calibrated IMU overlay (#52). Poor/cloudy nights
  can still validate remount, drift, and workflow logging, but cannot promote
  the overlay beyond read-only. Use
  `../PiFinder_lite/documentation/phase5_field_validation_52.md` for the guided
  day/poor-night and clear-night protocol.
- Build Phase 6 as a diagnostic mobile-camera solve workflow first.
- Keep uploaded frames diagnostic until mobile captures solve reliably under
  Phase 2 evidence.

See [ROADMAP.md](ROADMAP.md) for the phased PiFinder Mobile / PiFinder Lite
development plan.
