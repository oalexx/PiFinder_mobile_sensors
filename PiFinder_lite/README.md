# PiFinder Lite / Mobile Companion

PiFinder Lite is an additive/mobile companion path for PiFinder. The goal is to
reuse the original backend, solver, catalogs, web remote, and SkySafari/LX200
support while adding optional phone-based UI, GPS, IMU, camera diagnostics, and
configuration workflows.

Classic PiFinder should remain unchanged unless a Lite feature is explicitly
enabled.

## Current Status

Phase 4 is implemented and validated on Raspberry Pi OS Trixie/Python 3.13.
Phase 5 is implemented up to calibrated mobile IMU read-only overlay/status.
The Android app can talk to PiFinder Lite through the mobile bridge, upload a
JPEG frame, send GPS into the running PiFinder process, send IMU diagnostic
batches for confidence analysis, collect phone-to-telescope calibration
evidence, and display the loaded mount profile as diagnostic read-only status.

Validated chain:

```text
Android app -> PiFinder /mobile/* endpoints -> Raspberry storage/runtime state
```

Validated capabilities:

- Headless PiFinder startup with `--keyboard none`.
- Phone access to `/remote`.
- SkySafari/LX200 server startup alongside the web remote.
- `/mobile/status`, `/mobile/profile`, `/mobile/gps`, `/mobile/imu`, and
  `/mobile/camera_frame`.
- Runtime GPS updates from Android GPS.
- IMU batch capture and confidence scoring.
- Mobile JPEG upload, quality scoring, and diagnostic solve tooling.
- Diagnostic `/mobile/camera_solve` endpoint for uploaded frames.
- Local diagnostic solve reports under
  `~/PiFinder_data/mobile/camera_solve_reports/`.
- Read-only `/mobile/camera_reports` history/session summary for recent
  diagnostic reports.

Still intentionally diagnostic-only:

- Mobile camera frames are not fed into the live solver/integrator loop.
- Mobile IMU is not fed into the integrator.
- Calibrated mobile mount profiles are shown read-only and do not change
  pointing state.
- RAW is not promoted until Phase 2 night evidence shows value.

Phase 5 decision:

```text
calibrated mobile IMU -> diagnostic overlay/read-only guidance aid next
calibrated mobile IMU -> integrator input blocked
```

## Current Camera Decision

Mobile camera path:

```text
PROMISING_TUNE_FIRST
```

Meaning:

- continue mobile-camera work;
- keep it diagnostic-only for now;
- use quality scoring before solving;
- validate on Raspberry before live integration;
- do not feed mobile solves into the integrator yet.

Decision record:

```text
PiFinder_lite/documentation/mobile_camera_solver_path_decision.md
```

## Quick Start On Raspberry

Install/run checklist:

```text
PiFinder_lite/raspberry_lite_install.md
```

The Raspberry Pi OS Trixie / Python 3.13 path needs the compatibility notes in
that checklist. Do not assume the original pinned `requirements.txt` is enough
on a fresh Trixie image.

Minimal headless/dev startup:

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

Open from phone:

```text
http://<raspberry-ip>:8080/remote
```

## Android Diagnostic Flow

In the Android app:

```text
PiFinder Remote -> set base URL
PiFinder Remote -> Test Connection
PiFinder Remote -> Send Profile / Send GPS / Send IMU Batch
Camera Lab -> Save Folder
Camera Lab -> Run Full Diagnostic
```

`Run Full Diagnostic` captures a solve-candidate JPEG, uploads it to
`/mobile/camera_frame`, calls `/mobile/camera_solve`, and displays upload,
quality score, solve/skipped state, next action, and the persisted report path.
It also shows a conservative exposure/capture advice line, for example
background too bright, noise too high, too few candidates, saturation present,
or solved but collect more evidence. `View Reports` then reads
`/mobile/camera_reports` and shows the recent report history, solved/rejected
counts, best score, dominant advice, recommendation, and next action. `Copy
Report Summary` copies that human-readable summary. The separate
burst/upload/solve buttons remain available for debugging.

The exposure advisor is rule-based and diagnostic-only. Its thresholds are
intentionally conservative until more Phase 2 clear-sky evidence tunes them.

Optional Raspberry-side batch checks:

```bash
python PiFinder_lite/score_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames"
python PiFinder_lite/diagnostic_solve_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames" --max-frames 12 --solve-timeout-ms 1000 --preprocess-modes baseline,background_subtract
```

The Android diagnostic actions remain diagnostic-only and do not update live
pointing or feed the integrator.

## Documentation Map

The root of `PiFinder_lite/` is kept for active setup files and executable
diagnostic tools. Longer design notes, validation history, and decision records
live under `documentation/`.

### Setup And Runtime

| Document | Purpose |
| --- | --- |
| `raspberry_lite_install.md` | End-to-end Raspberry install/run checklist. |
| `raspberry_validation_runbook.md` | Step-by-step #42 validation manual. |
| `apt-packages-trixie-py313.txt` | Raspberry Pi OS Trixie system packages for Lite validation. |
| `requirements-trixie-py313.txt` | Pip requirements for the Trixie/Python 3.13 Lite venv. |
| `documentation/lite_config_profile.md` | Optional Lite config profile and startup flags. |
| `documentation/keyboard_none_validation.md` | No-keyboard/headless validation notes. |
| `documentation/remote_endpoint_validation.md` | `/remote`, `/image`, `/key_callback` validation. |
| `documentation/android_webview_remote.md` | Android WebView remote behavior. |
| `documentation/mobile_remote_layout.md` | Mobile-friendly `/remote` layout notes. |
| `documentation/skysafari_split_screen_validation.md` | SkySafari split-screen workflow. |

### Mobile Bridge

| Document | Purpose |
| --- | --- |
| `documentation/mobile_bridge_api_v0.md` | API contract for `/mobile/*` endpoints. |
| `documentation/mobile_camera_frame_upload.md` | Storage-only JPEG upload flow. |
| `documentation/phase4_dependency_map.md` | Issue dependency order and current gates. |
| `documentation/upstream_change_log.md` | Changes to original PiFinder and why. |
| `phase4_imu_analysis/mobile_imu_confidence.md` | Generated local IMU analysis output. |

### Camera Evidence

| Document | Purpose |
| --- | --- |
| `documentation/phase2_night_sky_validation.md` | Phase 2 night-sky evidence summary. |
| `documentation/phase2_day_test_validation.md` | Day Test validation notes. |
| `documentation/phase2_camera_id_recommendation.md` | Camera ID recommendation evidence. |
| `documentation/solve_candidate_burst.md` | Android burst mode tuned for solving. |
| `documentation/mobile_frame_quality_score.md` | Quality score rules and usage. |
| `documentation/mobile_frame_diagnostic_solve.md` | Diagnostic solve workflow. |
| `documentation/mobile_camera_solver_path_decision.md` | Product/technical decision for solver path. |
| `documentation/mobile_camera_profile.md` | Per-device recommendation profile format. |

### Tools

| Tool | Purpose |
| --- | --- |
| `analyze_phase2_camera.py` | Offline Phase 2 frame analysis and Tetra3 attempts. |
| `score_mobile_frame.py` | Score JPEGs before diagnostic solving. |
| `diagnostic_solve_mobile_frame.py` | Explicit diagnostic solve of scored JPEGs. |
| `analyze_mobile_imu.py` | Analyze stored `/mobile/imu` batches. |
| `compute_mobile_mount_offset.py` | Compute a diagnostic candidate phone-to-tube offset profile. |
| `validate_mobile_mount_repeatability.py` | Compare candidate offsets and recommend proceed/recalibrate/reject. |
| `validate_remote_endpoints.py` | Local validation of web/mobile endpoints. |
| `validate_lx200_server.py` | LX200/SkySafari server validation. |

### Generated Reports

Generated Phase 2 reports are intentionally ignored by Git:

```text
PiFinder_lite/phase2_camera_analysis/
```

Keep local CSV/JSON/Markdown analysis output there when needed, but do not
commit phone-test artifacts or local filesystem paths.

## Config Examples

| File | Purpose |
| --- | --- |
| `configs/pifinder_lite_config.example.json` | Optional PiFinder Lite user config example. |
| `configs/mobile_camera_profile.samsung_sm-s948b.example.json` | First phone camera recommendation profile. |
| `configs/mobile_mount_profile.example.json` | Disabled mobile mount profile schema example. |
| `configs/mobile_mount_reference.example.json` | Reference quaternion input example for offset calculation. |

## Next Hardware Gate

Phase 4 hardware validation has passed. Phase 5 tooling is ready, but #52 still
needs mounted field evidence before any guidance beyond read-only overlay.
Use `documentation/phase5_field_validation_52.md` to run a day/poor-night
workflow now and repeat the same protocol under clear sky later.

The next camera gate remains Phase 2 clear-sky camera validation:

```text
Manual Burst / ISO Sweep / Cam Sweep / RAW Burst under clearer sky.
```

Required evidence:

```text
dark sky frame -> enough star-like centroids -> accepted quality score -> diagnostic solve attempt
```

Until that evidence is reliable, mobile camera remains diagnostic-only and
PiFinder Lite should continue to use the original PiFinder camera path for live
solving.

Phase 6 has been split into issues #54-#59. Endpoint/UI/report scaffolding can
be built with existing uploaded frames, but threshold tuning, RAW decisions, and
any runtime promotion remain blocked by Phase 2 evidence.
