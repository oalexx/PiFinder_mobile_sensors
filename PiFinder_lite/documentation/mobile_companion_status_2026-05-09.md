# Mobile Companion Status - 2026-05-09

This is the current inflection-point summary for the PiFinder Lite / Mobile
Companion fork.

## What Works Now

- Android compatibility tester and profile export.
- PiFinder Lite headless startup with `--keyboard none`.
- Phone access to the existing PiFinder `/remote` UI.
- Mobile bridge endpoints:
  - `/mobile/status`
  - `/mobile/profile`
  - `/mobile/gps`
  - `/mobile/imu`
  - `/mobile/environment`
  - `/mobile/camera_frame`
  - `/mobile/camera_solve`
  - `/mobile/camera_reports`
  - `/mobile/mount_profile`
- Android GPS can update PiFinder runtime GPS state.
- Android IMU batches are stored and analyzed for diagnostics.
- Android calibration flow can collect `stationary`, `mounted_reference`, and
  `repeat_check` batches.
- Raspberry tools can compute candidate phone-to-tube mount offsets and compare
  repeatability.
- Android can display the loaded mobile mount profile as read-only overlay
  metadata.
- Android Camera Lab can capture solve-candidate bursts, upload frames, request
  diagnostic solves, view report history, copy summaries, and run a Phase 2
  night-test wizard.
- `Run Full Diagnostic` ranks a dynamic distributed subset of burst frames by
  Raspberry diagnostic solve results instead of blindly using the last JPEG.
- Raspberry can generate conservative per-phone camera recommendation profiles
  from diagnostic reports.

## Validated On Raspberry

Phase 4 mobile bridge validation passed on Raspberry Pi OS Trixie/Python 3.13.
The mobile bridge, GPS update path, IMU storage path, camera upload path, quality
score, and diagnostic solve tooling have been exercised as additive diagnostic
flows.

## Still Diagnostic-Only

- Mobile camera solves do not update pointing.
- Mobile camera solves do not feed the integrator.
- Mobile IMU does not feed the integrator.
- Mobile mount profiles are read-only and cannot make runtime pointing changes.
- Per-phone camera profiles are evidence summaries, not runtime configs.
- RAW remains experimental until #58.

## Open Evidence Gates

- Phase 2 clear-sky camera validation remains the main camera gate.
- #52 field validation remains the mounted/real-sky gate for calibrated mobile
  IMU overlay confidence.
- #57 must tune quality thresholds from accepted/rejected real night frames.
- #58 must decide whether RAW adds value over JPEG.
- #59 must decide whether mobile camera can move beyond diagnostic solving.

## Distance To A Usable Product

The companion is already useful as a PiFinder Lite field diagnostic and remote
workflow aid. It is not yet a replacement for the original PiFinder camera or
IMU runtime loop.

Practical next milestone:

```text
Use Android wizard -> collect clear-sky burst diagnostics -> generate per-phone
profile -> tune thresholds -> make #59 runtime-path decision.
```

After one or two good clear-sky sessions, the project should be able to decide
whether the mobile camera is:

- diagnostic-only;
- useful as a manual solve aid;
- worth designing as a future live mobile-camera solver path;
- or not worth pursuing beyond UI/GPS/IMU support.

The calibrated mobile IMU path needs its own #52 field evidence before it can
move from read-only overlay toward any optional guidance issue.
