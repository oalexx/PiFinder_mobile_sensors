# PiFinder Mobile

Native Android companion app for PiFinder Lite field use, phone diagnostics,
camera checks, GPS/IMU bridge data, calibration evidence, and access to the
existing PiFinder remote.

The current app now covers the Phase 1 tester, the Phase 4 bridge prototype,
and the Phase 5 calibration evidence flow. It checks what the phone actually
exposes through public Android APIs, runs capture tests, loads the existing
PiFinder `/remote` page, and can send GPS, IMU batches, profile data, mount
calibration evidence, and JPEG diagnostic frames to a Raspberry Pi running
PiFinder Lite. It can also send optional environment metadata so camera
reports can show whether ambient light, barometer, battery, and network context
were available during a session. Raspberry tools can turn those diagnostic
reports into conservative per-phone camera recommendation profiles.

Current app/product status:

- Home is organized around `PiFinder Remote` as the primary field action.
- `Phone setup` opens a second menu with Camera Lab, Calibration, and
  Diagnostics.
- `Help` opens in-app instructions for the main workflow and each tool.
- A persistent `Night Vision` mode switches the app to a red, astronomy-friendly
  palette and updates Android system bars where the platform allows it.
- The launcher icon and in-app brand mark use a minimal constellation/phone
  vector logo.
- User-facing labels avoid internal project issue/phase names; development
  gates remain documented here and in `PiFinder_lite/`.

Current validated bridge status:

- `/mobile/status` connection check works.
- `SEND PROFILE` posts the structured phone profile.
- `SEND ENV` stores diagnostic environment metadata without GPS coordinates.
- `SEND GPS` can feed the running PiFinder process.
- `SEND IMU BATCH` stores a short diagnostic batch for confidence analysis.
- `CALIBRATION` stores labeled `stationary`, `mounted_reference`, and
  `repeat_check` IMU batches.
- `UPLOAD LAST JPEG` stores a diagnostic JPEG on the Raspberry.
- `Run full diagnostic` ranks a dynamic subset of burst frames with Raspberry
  diagnostic solve results.
- `View reports` loads `/mobile/camera_reports` and `Copy summary` copies the
  saved diagnostic history/session summary.
- `AI Image Preprocessing` can compare classic/adaptive diagnostic paths and
  records evidence without changing runtime pointing.
- `CALIBRATION` starts the phone-to-telescope evidence flow.

Camera and IMU data are still diagnostic paths. Live mobile camera solving and
mobile IMU integration are intentionally deferred until later phases. The
current calibrated IMU path is read-only overlay/status only.

## Current Screens

### Home And Night Vision

The Home screen is designed for field use:

- `PiFinder Remote` is the primary action.
- `Phone setup` opens a clean tools menu:
  - `Camera Lab`
  - `Calibration`
  - `Diagnostics`
- `Help` opens in-app instructions explaining the recommended procedure and
  what each menu does.
- `Night Vision` is a compact global toggle. It is saved locally and remains
  active when the app is reopened.

Night Vision affects the app palette and Android status/navigation bar colors.
Android does not allow normal apps to recolor the system clock or status icons
directly; the app instead uses dark red bars and forces non-light system icon
flags so the surrounding system chrome is as night-safe as Android permits.

### Diagnostics

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

- `Start IMU` to begin live sensor sampling.
- `Stop` to stop live sensor sampling.
- `Run check` to generate the compatibility result.
- `Copy result`, `Copy tech report`, `Copy profile JSON`, and history actions.

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

- `Run full diagnostic`: captures a solve-candidate JPEG, uploads it, asks
  Raspberry for score/diagnostic solve, and shows the stored report summary.
  For solve-candidate bursts, Android keeps multiple JPEG candidates, uploads a
  dynamic distributed subset, asks Raspberry to score/solve each one, and
  selects the best result by solve success and quality score.
- `Night checklist`: collapsible field checklist for connection,
  profile/environment/GPS, save folder, full diagnostic, repeats, and report
  summary.
- `View reports`: reads `/mobile/camera_reports` and shows recent diagnostic
  reports, session counts, best score, dominant advice, recommendation, and
  next action.
- `Copy night plan`: copies a sanitized field checklist and
  evidence-state summary.
- `Mark repeat run`: increments the local repeat counter after each comparable
  diagnostic attempt.
- `Copy summary`: copies the latest history/session summary from
  `View reports`.

Advanced captures:

- `Day test`: automatic exposure/focus test for indoor or daylight framing.
- `Manual burst`: high ISO, long exposure JPEG burst for sky testing.
- `ISO sweep`: multiple ISO groups for exposure comparison.
- `RAW burst`: raw sensor byte captures for technical experiments.
- `Camera sweep`: tests the available rear camera IDs.
- `Candidate burst`: tuned JPEG capture for PiFinder Lite diagnostics.
- `Upload JPEG`: sends the newest saved JPEG to `/mobile/camera_frame`.
  This remains available as a manual debug path; `Run full diagnostic` uses the
  ranked candidate flow instead.
- `Solve frame`: asks PiFinder to score and diagnostic-solve the uploaded
  frame via `/mobile/camera_solve`.

Diagnostic results include rule-based exposure/capture advice such as
background too bright, noise too high, too few candidates, saturation present,
or solved but collect more evidence. The advice is conservative until more
clear-sky Phase 2 data tunes thresholds.

Camera-frame metadata includes a diagnostic environment snapshot. Missing
light or pressure sensors are recorded as unavailable rather than treated as an
error.

The night checklist is a checklist, not a runtime promotion. A completed test
means the workflow ran and produced notes; reliable camera use still requires
repeated clear-sky results and the project decision summary. The checklist
remains diagnostic-only and does not feed mobile solves into pointing or the
integrator.
For cloudy, bright, or rehearsal sessions, use
  `../PiFinder_lite/documentation/no_good_night_rehearsal.md` to combine the
  Camera Lab workflow with mounted IMU overlay checks.

The burst frame selector is also diagnostic-only. Android only chooses a
bounded, distributed subset from the burst so field uploads stay practical:
small bursts upload all frames, medium bursts upload three to five, and large
bursts upload up to seven. Raspberry remains the source of truth for quality:
the selected frame is chosen from Raspberry diagnostic solve results, preferring
`solve_ok`, then higher quality score, with JPEG size only as a fallback.

After reports are collected, Raspberry can generate a per-phone recommendation
profile with `PiFinder_lite/generate_mobile_camera_profile.py`. That profile
summarizes recommended camera ID, capture mode, JPEG/RAW status, confidence,
evidence counts, and caveats. It remains diagnostic-only until the Phase 2/#57
/#59 evidence chain supports any runtime decision.

Each run creates a dated folder and writes images with descriptive names. The
metadata file is also named after the test run, for example:

```text
pifinder_camera_sweep_20260429_223538_metadata.txt
```

The metadata includes the camera ID, format, size, frame count, orientation,
ISO/exposure settings, saved frame count, and failures.

### PiFinder Remote

Connects the app to a Raspberry/PiFinder Lite instance.

Field connectivity away from a home router is tracked in issue #75. The
preferred mode to validate first is phone hotspot/tethering with the Raspberry
Pi as Wi-Fi client. Fallbacks are Pi hotspot/access point, USB tethering, and a
small travel router. These tests are about transport reliability only; they do
not change camera/IMU diagnostic-only boundaries.

Available actions:

- `Test connection`: checks `/mobile/status`.
- `Open remote`: opens the existing PiFinder `/remote` page full-screen.
- `Send profile`: sends the phone capability/profile JSON.
- `Send env`: sends ambient-light/barometer availability, battery, network,
  app/device time, and coarse device state to `/mobile/environment`.
- `Send GPS`: posts the current Android location to PiFinder.
- `Send IMU batch`: captures and uploads a short rotation-vector batch.
- `Mount ref IMU`: captures a still phone/tube reference batch for Phase 5
  calibration experiments from the remote tools screen.

The embedded remote is a wrapper around the existing PiFinder web UI. If layout
issues appear, compare it with the same URL in a normal browser before changing
PiFinder server-side CSS.

### Calibration

Collects Phase 5 phone-to-telescope evidence without enabling mobile IMU
pointing.

Available actions:

- `Test connection`: checks the saved PiFinder base URL.
- `Send profile`: uploads the current phone capability profile.
- `Check profile`: reads `GET /mobile/mount_profile` and shows the mounted
  profile as a read-only overlay/status card.
- `Send GPS`: uploads the current Android location.
- `Stationary`: uploads a labeled `stationary` IMU batch while the mounted
  phone and tube remain still.
- `Mount ref`: uploads a labeled `mounted_reference` IMU batch against the
  selected reference target/note.
- `Repeat check`: uploads a labeled `repeat_check` IMU batch after returning
  to the same reference.
- `Copy evidence`: copies a calibration evidence JSON with the reference note,
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
2. Use `Night Vision` if observing conditions require red-light mode.
3. Open `Help` if you need the in-app procedure overview.
4. Open `PiFinder Remote` for normal field control, or go to `Phone setup`.
5. In `Phone setup`, open `Diagnostics`.
6. Tap `Start IMU`.
7. Move the phone gently for a few seconds.
8. Tap `Stop`.
9. Tap `Run check`.
10. Use `Copy result` or `Copy tech report` if needed.
11. Go back to `Phone setup`, then open `Camera Lab`.
12. Tap `Save folder`.
13. Run `Day test` indoors to check framing.
14. Go to `PiFinder Remote`, set the Raspberry base URL, then run:
    - `Test connection`
    - `Send profile`
    - `Send env`
    - `Send GPS`
    - `Send IMU batch`
15. Go back to `Phone setup`, open `Camera Lab`, tap `Night checklist`, then
    `Copy night plan` if you want a field checklist.
16. Tap `Run full diagnostic` to capture a solve-candidate burst, upload a
    dynamic distributed subset, score/diagnostic-solve candidates on Raspberry,
    and summarize the selected frame plus ranking.
17. Tap `Mark repeat run` after each completed attempt, even if the frame is
    rejected or solve fails.
18. Tap `View reports` to compare recent diagnostic reports and copy the
    session summary when needed.
19. Run broader sky tests outdoors at night when conditions allow:
    - `Manual burst`
    - `ISO sweep`
    - `Camera sweep`
    - `RAW burst`

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
  day/poor-night and clear-night protocol, or
  `../PiFinder_lite/documentation/no_good_night_rehearsal.md` when combining
  #52 with a Phase 2 camera shakedown.
- Build Phase 6 as a diagnostic mobile-camera solve workflow first.
- Keep uploaded frames diagnostic until mobile captures solve reliably under
  Phase 2 evidence.

See [ROADMAP.md](ROADMAP.md) for the phased PiFinder Mobile / PiFinder Lite
development plan.
