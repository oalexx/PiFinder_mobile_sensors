# PiFinder Lite / Mobile Companion

PiFinder Lite is an additive/mobile companion path for PiFinder. The goal is to
reuse the original backend, solver, catalogs, web remote, and SkySafari/LX200
support while adding optional phone-based UI, GPS, IMU, camera diagnostics, and
configuration workflows.

Classic PiFinder should remain unchanged unless a Lite feature is explicitly
enabled.

## Current Status

Phase 4 is implemented and validated on Raspberry Pi OS Trixie/Python 3.13.
The Android app can talk to PiFinder Lite through the mobile bridge, upload a
JPEG frame, send GPS into the running PiFinder process, and send IMU diagnostic
batches for confidence analysis.

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

Still intentionally diagnostic-only:

- Mobile camera frames are not fed into the live solver/integrator loop.
- Mobile IMU is not fed into the integrator.
- RAW is not promoted until Phase 2 night evidence shows value.

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
PiFinder_lite/mobile_camera_solver_path_decision.md
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
Camera Lab -> Run Diagnostic Burst
Camera Lab -> Upload Last JPEG
```

Then on Raspberry:

```bash
python PiFinder_lite/score_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames"
python PiFinder_lite/diagnostic_solve_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames" --max-frames 12 --solve-timeout-ms 1000 --preprocess-modes baseline,background_subtract
```

## Documentation Map

### Setup And Runtime

| Document | Purpose |
| --- | --- |
| `raspberry_lite_install.md` | End-to-end Raspberry install/run checklist. |
| `raspberry_validation_runbook.md` | Step-by-step #42 validation manual. |
| `apt-packages-trixie-py313.txt` | Raspberry Pi OS Trixie system packages for Lite validation. |
| `requirements-trixie-py313.txt` | Pip requirements for the Trixie/Python 3.13 Lite venv. |
| `lite_config_profile.md` | Optional Lite config profile and startup flags. |
| `keyboard_none_validation.md` | No-keyboard/headless validation notes. |
| `remote_endpoint_validation.md` | `/remote`, `/image`, `/key_callback` validation. |
| `android_webview_remote.md` | Android WebView remote behavior. |
| `mobile_remote_layout.md` | Mobile-friendly `/remote` layout notes. |
| `skysafari_split_screen_validation.md` | SkySafari split-screen workflow. |

### Mobile Bridge

| Document | Purpose |
| --- | --- |
| `mobile_bridge_api_v0.md` | API contract for `/mobile/*` endpoints. |
| `mobile_camera_frame_upload.md` | Storage-only JPEG upload flow. |
| `phase4_dependency_map.md` | Issue dependency order and current gates. |
| `upstream_change_log.md` | Changes to original PiFinder and why. |
| `phase4_imu_analysis/mobile_imu_confidence.md` | Generated local IMU analysis output. |

### Camera Evidence

| Document | Purpose |
| --- | --- |
| `phase2_night_sky_validation.md` | Phase 2 night-sky evidence summary. |
| `phase2_day_test_validation.md` | Day Test validation notes. |
| `phase2_camera_id_recommendation.md` | Camera ID recommendation evidence. |
| `solve_candidate_burst.md` | Android burst mode tuned for solving. |
| `mobile_frame_quality_score.md` | Quality score rules and usage. |
| `mobile_frame_diagnostic_solve.md` | Diagnostic solve workflow. |
| `mobile_camera_solver_path_decision.md` | Product/technical decision for solver path. |
| `mobile_camera_profile.md` | Per-device recommendation profile format. |

### Tools

| Tool | Purpose |
| --- | --- |
| `analyze_phase2_camera.py` | Offline Phase 2 frame analysis and Tetra3 attempts. |
| `score_mobile_frame.py` | Score JPEGs before diagnostic solving. |
| `diagnostic_solve_mobile_frame.py` | Explicit diagnostic solve of scored JPEGs. |
| `analyze_mobile_imu.py` | Analyze stored `/mobile/imu` batches. |
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

## Next Hardware Gate

Phase 4 hardware validation has passed. The next real gate is Phase 2 clear-sky
camera validation:

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
