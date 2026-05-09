# No-Good-Night Field Rehearsal

Purpose: make progress on #52 and Phase 2 even when the sky is cloudy,
bright, or not usable for final evidence.

This rehearsal proves the complete operator workflow:

- Android can reach PiFinder Lite.
- Phone profile, environment, GPS, camera, and IMU data reach Raspberry.
- Camera diagnostic reports and per-phone recommendation profiles can be
  generated.
- Phone-to-telescope calibration batches can be collected, analyzed, and
  documented.
- The telescope mount, phone clamp, repeatability, drift logging, and report
  format are ready for the next clear night.

It does not prove mobile-camera reliability, and it does not promote mobile IMU
or camera data into live pointing.

## Safety Boundaries

- Do not feed mobile camera solves into the live solver or integrator.
- Do not feed mobile IMU into the integrator.
- Keep `/mobile/mount_profile` read-only.
- Treat camera profiles as diagnostic evidence summaries, not runtime config.
- Treat day, indoor, cloudy, or poor-night #52 results as `needs_more_data`.
- Do not commit phone captures, generated analysis output, local paths, or
  precise private GPS coordinates.

## Required Setup

Raspberry:

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

Phone:

- Install the current Android debug APK.
- Put phone and Raspberry on the same network.
- Open PiFinder Mobile.
- Set the PiFinder base URL to the Raspberry.
- Choose a save folder in Camera Lab.

Physical setup:

- Mount the phone in the intended telescope clamp.
- Mark the phone edge, clamp position, and orientation.
- Keep the same phone side, screen direction, and clamp pressure throughout the
  rehearsal.
- Keep magnets, metal tools, speakers, power banks, and steel accessories away
  from the phone.

## Part 1: Connectivity And Runtime Preflight

Run this before attaching the phone to the telescope.

1. Open `PiFinder Remote`.
2. Set the Raspberry base URL.
3. Tap `TEST CONNECTION`.
4. Tap `SEND PROFILE`.
5. Tap `SEND ENV`.
6. Tap `SEND GPS`.
7. Confirm `/remote` opens from the phone browser or WebView.

Pass criteria:

- Connection succeeds.
- Profile/env/GPS sends do not show errors.
- Raspberry keeps running.
- No pointing state is changed by mobile camera or mobile IMU diagnostics.

If this fails, fix network, URL, Android permissions, or Raspberry startup
before doing any telescope work.

## Part 2: Phase 2 Camera Rehearsal

This validates the capture, upload, diagnostic solve, report, and profile flow.
Cloudy or bright frames are allowed, but they are not final camera evidence.

Android:

1. Open `Camera Lab`.
2. Tap `SAVE FOLDER`.
3. Tap `NIGHT TEST WIZARD`.
4. Tap `COPY NIGHT TEST PLAN` and keep the copied plan with local notes.
5. Tap `RUN FULL DIAGNOSTIC`.
6. Wait for candidate ranking, quality score, solve/skipped state, and report
   summary.
7. Tap `MARK REPEAT`.
8. Repeat `RUN FULL DIAGNOSTIC` at least three times:
   - one indoor/day/poor-sky run;
   - one mounted or tripod-fixed run;
   - one repeat after changing nothing.
9. Tap `VIEW REPORTS`.
10. Tap `COPY REPORT SUMMARY`.

Expected poor-night outcomes:

- `solve_ok=false` is acceptable.
- `rejected`, `too_bright`, `too_few_candidates`, or `needs_more_data` are
  acceptable.
- The important result is that reports are persisted and explain why the frame
  was accepted, skipped, solved, or rejected.

Generate a camera recommendation profile on Raspberry:

```bash
python PiFinder_lite/generate_mobile_camera_profile.py \
  --reports-dir "$HOME/PiFinder_data/mobile/camera_solve_reports" \
  --device-model "<phone-model>" \
  --manufacturer "<manufacturer>" \
  --output "$HOME/PiFinder_data/mobile/profiles/mobile_camera_profile.<phone-model>.json" \
  --markdown-output "$HOME/PiFinder_data/mobile/profiles/mobile_camera_profile.<phone-model>.md"
```

Pass criteria:

- Android captures frames.
- `RUN FULL DIAGNOSTIC` completes without app or Raspberry crashes.
- Candidate ranking selects one diagnostic frame.
- `/mobile/camera_reports` returns recent reports.
- A profile file can be generated.
- Profile decision remains conservative unless the reports contain repeated
  clear-sky solves.

Fail/blocker criteria:

- Camera permission or save folder cannot be set.
- Uploads to `/mobile/camera_frame` fail repeatedly.
- `/mobile/camera_solve` or `/mobile/camera_reports` is unreachable.
- Reports are missing selected-candidate, quality, recommendation, or next
  action fields.

## Part 3: #52 IMU Overlay Rehearsal

This validates the mounted-phone calibration workflow. It can be run indoors,
in daylight, or on a cloudy night by using a repeatable physical reference.

Android:

1. Open the Calibration screen.
2. Confirm `TEST CONNECTION` succeeds.
3. Send profile/GPS again if the session has been idle.
4. Mount the phone using the marked clamp position.
5. Capture one `stationary` batch with the tube untouched.
6. Point the telescope tube at a repeatable physical reference:
   - distant roof edge;
   - wall mark;
   - fixed landscape feature;
   - artificial target across the room.
7. Capture one `mounted_reference` batch.
8. Capture one `repeat_check` batch without changing the mount.
9. Remove and remount the phone using the same marks.
10. Capture another `mounted_reference` batch.
11. Capture another `repeat_check` batch.
12. Leave the phone mounted for at least 5 minutes.
13. Capture one final `repeat_check` batch.

Analyze the latest IMU batch on Raspberry:

```bash
python PiFinder_lite/analyze_mobile_imu.py \
  --input "$HOME/PiFinder_data/mobile/imu_latest.json" \
  --json
```

Create candidate offset profiles. For poor-night/day rehearsal, the reference
file must be clearly named as non-sky evidence and contain `q_tube_reference`
in `[w, x, y, z]` order.

```bash
python PiFinder_lite/compute_mobile_mount_offset.py \
  --imu-batch "$HOME/PiFinder_data/mobile/imu_latest.json" \
  --reference "$HOME/PiFinder_data/mobile/reference_target_day.json" \
  --sensor game_rotation_vector \
  --mount-name "day-validation-remount-1" \
  --output "$HOME/PiFinder_data/mobile/mount_profiles/day-remount-1.json"
```

Compare candidate profiles:

```bash
python PiFinder_lite/validate_mobile_mount_repeatability.py \
  --input "$HOME/PiFinder_data/mobile/mount_profiles" \
  --output-dir "$HOME/PiFinder_data/mobile/repeatability" \
  --json
```

Pass criteria:

- All labeled batches send successfully.
- Raspberry can analyze the latest IMU batch.
- At least two candidate profiles can be compared.
- Repeatability tool returns `proceed`, `recalibrate`, or `reject`.
- The report can clearly explain mount stability, remount behavior, and drift.

Poor-night success still means:

```text
Decision: needs_more_data
```

It can close workflow risks, but it cannot prove real-sky overlay accuracy.

## Evidence To Keep Locally

Keep these under `~/PiFinder_data/mobile/` or another private local folder:

```text
camera_solve_reports/
profiles/
imu_latest.json
mount_profiles/
repeatability/
field_validation/
```

For a sanitized issue update or project note, copy only summaries:

- Android copied night-test plan.
- Android copied camera report summary.
- Generated camera profile Markdown summary.
- IMU analysis summary.
- Repeatability recommendation.
- Decision label.
- Next blocker.

Before sharing anything, remove:

- raw phone images;
- raw IMU batches;
- local absolute paths;
- exact private GPS coordinates.

## Rehearsal Report Template

Copy this into a local note under
`~/PiFinder_data/mobile/field_validation/`.

```markdown
# No-Good-Night Rehearsal Report

Date:
Observer:
Phone model:
Android app build:
PiFinder branch/commit:
Raspberry model / OS:

## Session Type

- [ ] Indoor/day
- [ ] Cloudy/poor night
- [ ] Mounted telescope
- [ ] Tripod or fixed support only

## Connectivity

Base URL:
Remote reachable:
Profile sent:
Environment sent:
GPS sent:

## Camera Rehearsal

Runs completed:
Candidate frames uploaded:
Reports generated:
Best quality score:
Successful diagnostic solves:
Dominant advice:
Generated profile:
Profile decision:

## #52 IMU Rehearsal

Mount description:
Phone orientation:
Reference target:
Stationary batches:
Mounted reference batches:
Repeat check batches:
Longest drift interval:
Preferred sensor:
Warnings:
Repeatability recommendation:

## Decision

Decision:

- [ ] needs_more_data

Reason:
What is ready for the next clear night:
What still needs fixing before the next clear night:

## Privacy Check

- [ ] No raw images attached.
- [ ] No raw IMU batches attached.
- [ ] No precise private GPS coordinates.
- [ ] No local absolute paths in shared output.
```

## What This Unlocks

After a good rehearsal, the next clear night should be a validation session, not
a debugging session.

You can continue immediately with:

- fixing Android permissions, UX text, or connection failures;
- improving report readability;
- validating Raspberry startup and storage paths;
- practicing #52 remount and drift capture;
- generating conservative per-phone camera profiles from existing reports.

You should still wait for clear sky before:

- tuning #57 thresholds;
- deciding #58 RAW value;
- making #59 runtime-path decisions;
- changing mobile IMU from read-only overlay;
- treating mobile camera frames as reliable live pointing input.
