# PiFinder Lite Upstream Change Log

This document tracks every intentional change made to original PiFinder code
while developing PiFinder Lite / Mobile Companion.

The goal is to keep the classic PiFinder behavior intact and make future
upstream review easier. Every core change should explain why it exists, whether
it is required for Lite mode, and whether it should remain when testing on a
real Raspberry Pi.

## Policy

- Prefer new Lite/mobile modules, configuration flags, and documentation over
  changing existing PiFinder behavior.
- Any change under `python/PiFinder/` or the original web UI under
  `python/views/` must be listed here.
- Temporary workstation-only changes should be reverted before merge.
- If a change is only needed because of Windows, missing dependencies, or a
  local test setup, it should not be treated as a PiFinder Lite requirement.
- A change is merge-ready only when it is small, documented, tested, and does
  not alter classic mode behavior.

## Change Records

### 2026-05-02: `keyboard_none.run_keyboard` signature

Files:

- `python/PiFinder/keyboard_none.py`
- `python/tests/test_keyboard_none.py`
- `PiFinder_lite/keyboard_none_validation.md`

Reason:

`python/PiFinder/main.py` starts every keyboard implementation with four
arguments:

```python
keyboard.run_keyboard(
    keyboard_queue,
    shared_state,
    keyboard_logqueue,
    bloom_key_remap,
)
```

`keyboard_none.py` accepted only three arguments, so `--keyboard none` could
fail when the keyboard process was spawned. PiFinder Lite needs
`--keyboard none` so the device can run headless and receive input from the web
remote instead of a physical keypad.

Change:

`keyboard_none.run_keyboard` now accepts the same fourth argument as the other
keyboard implementations:

```python
def run_keyboard(q, shared_state, log_queue, bloom_remap=False):
```

The argument is intentionally ignored because no physical keyboard remapping is
needed in no-keyboard mode.

Classic PiFinder impact:

Low. This only widens the accepted function signature for `keyboard_none`.
Existing physical keyboard modes are not changed.

Validation:

```text
cd python/
.\.conda-py39\python.exe -m pytest tests\test_keyboard_none.py
```

Result:

```text
1 passed
```

A local startup test with `--keyboard none` also stayed alive for 25 seconds
after bypassing a Windows-only logging config issue documented in
`PiFinder_lite/keyboard_none_validation.md`.

Status:

Keep. This looks like a real PiFinder compatibility fix, not just a local PC
workaround.

### 2026-05-02: `tetra3_dir` local validation experiment

Files:

- `python/PiFinder/utils.py`

Reason:

During Windows validation, `python/PiFinder/tetra3` was empty locally and had
to be populated manually from `cedar-solve`. With that local checkout,
`import tetra3` worked when `tetra3_dir` pointed at the package parent rather
than the nested package directory.

Change tried:

```python
tetra3_dir = pifinder_dir / "python/PiFinder/tetra3"
```

instead of:

```python
tetra3_dir = pifinder_dir / "python/PiFinder/tetra3/tetra3"
```

Classic PiFinder impact:

Unknown. This touches shared solver import behavior and may depend on how the
Raspberry Pi install initializes the `tetra3` submodule.

Status:

Reverted. This is treated as a workstation/submodule validation issue, not as a
PiFinder Lite change. Reconsider only if the same import failure appears on the
Raspberry Pi with the official setup.

### 2026-05-02: `/remote` mobile layout

Files:

- `python/views/header.tpl`
- `python/views/remote.tpl`
- `python/views/css/style.css`
- `PiFinder_lite/remote_endpoint_validation.md`

Reason:

PiFinder Lite depends on the existing web remote as the first mobile UI. The
original `/remote` page worked from a phone browser, but used inline layout,
smaller touch targets, and encoded arrow/square glyphs that appeared as mojibake
in the Windows checkout.

Change:

- Replaced inline remote layout with named CSS classes.
- Kept the same `/key_callback` button codes and JavaScript behavior.
- Increased remote button height and touch target stability.
- Centered and constrained the screen image for phone viewports.
- Used HTML entities for arrows and square symbols so the template stays ASCII.
- Removed one unused JavaScript variable.
- Added a query-string version to `style.css` so phone browsers pick up the
  changed remote layout instead of reusing cached CSS.

Classic PiFinder impact:

Low to medium. This changes the web remote presentation only. Backend routes,
button codes, `/image`, and `/key_callback` behavior remain unchanged.

Validation:

- The endpoint validator still checks `/image`, `/remote`, and `/key_callback`.
- Manual phone validation should be repeated after this layout change.

Status:

Keep if phone validation confirms the layout is more comfortable and desktop
remote use remains acceptable.

### 2026-05-03: `/remote` embedded WebView mode

Files:

- `python/PiFinder/server.py`
- `python/views/remote.tpl`
- `python/views/css/style.css`
- `mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java`

Reason:

When the Android app loads the existing `/remote` page inside a WebView, the
normal PiFinder web header and footer consume vertical space and push the lower
remote buttons out of view. PiFinder Lite needs a focused remote view that gives
priority to the PiFinder screen and keypad.

Change:

- `/remote` now accepts `?embedded=1`.
- `remote.tpl` skips `header.tpl` and `footer.tpl` only when embedded mode is
  requested.
- Embedded mode still emits a minimal HTML document with viewport metadata and
  the same PiFinder CSS assets as the normal page. This is required because
  skipping `header.tpl` also skipped `materialize.css`, `style.css`, and the
  mobile viewport meta tag.
- Embedded mode adds `embedded-remote-body` and `embedded-remote-main` wrapper
  classes so the normal flex body/footer layout does not interfere with the
  Android WebView.
- The Android WebView loads `/remote?embedded=1`.
- The Android app hides its own title/subtitle while the full remote WebView is
  active.
- The Android WebView no longer uses overview/wide viewport scaling and now
  starts at 100% scale, because overview mode made the remote page render tiny
  inside the app even though it looked correct in a phone browser.

Classic PiFinder impact:

Low. Normal `/remote` behavior is unchanged unless `embedded=1` is explicitly
passed.

Validation:

- Android debug build succeeds after the change.
- Authenticated local validation confirms `/remote?embedded=1` includes the
  viewport meta tag, `materialize.css`, the versioned `style.css`, and the
  `remote-shell` markup while omitting the normal navigation header.
- Phone validation should confirm that the app now renders the remote at normal
  mobile scale and that all lower remote buttons are reachable.

Status:

Keep if device validation confirms the embedded view is more usable.

### 2026-05-03: `/mobile/status` endpoint

Files:

- `python/PiFinder/server.py`
- `PiFinder_lite/mobile_bridge_api_v0.md`
- `PiFinder_lite/validate_remote_endpoints.py`

Reason:

The Android companion needs a lightweight way to verify that it is connected to
PiFinder before sending profile/GPS/IMU data. This is the first Mobile Bridge
API endpoint and should not depend on any mobile payloads or hardware.

Change:

- Added `GET /mobile/status`.
- Returns JSON with `ok`, `api`, server UTC time, existing web remote endpoint
  availability, LX200 port, and planned/implemented mobile bridge capability
  flags.
- Extended the local endpoint validator to assert the API version and LX200
  port.

Classic PiFinder impact:

Low. This adds a new read-only endpoint and does not change existing routes,
startup defaults, GPS, solver, UI, or integrator behavior.

Validation:

```text
PASS /mobile/status: api mobile-bridge-v0, server_time <timestamp>
```

Status:

Keep.

### 2026-05-03: Mobile Bridge debug persistence

Files:

- `python/PiFinder/mobile_bridge.py`
- `python/PiFinder/server.py`
- `PiFinder_lite/mobile_bridge_api_v0.md`

Reason:

Phase 4 endpoints need a predictable debug location for the latest mobile
payloads before any data is wired into live GPS, IMU, solver, or integrator
behavior.

Change:

- Added `PiFinder.mobile_bridge` helper module.
- Added `~/PiFinder_data/mobile/` as the Mobile Bridge debug data directory.
- Added atomic-ish JSON writes via temp file + replace.
- Moved the `/mobile/status` JSON construction into `mobile_bridge.status_payload`.
- `/mobile/status` now also writes `status.json` for debugging.

Classic PiFinder impact:

Low. This only writes debug JSON when the new `/mobile/status` endpoint is
called. It does not affect classic startup, solver, GPS, IMU, or integrator
behavior.

Validation:

```text
PASS /mobile/status: api mobile-bridge-v0, server_time <timestamp>
```

Status:

Keep.

### 2026-05-03: `/mobile/profile` endpoint

Files:

- `python/PiFinder/server.py`
- `python/PiFinder/mobile_bridge.py`
- `PiFinder_lite/mobile_bridge_api_v0.md`
- `PiFinder_lite/validate_remote_endpoints.py`

Reason:

The Android Compatibility Tester needs a way to send its structured device,
sensor, camera, and readiness profile to PiFinder Lite before any GPS/IMU/camera
runtime integration is attempted.

Change:

- Added `POST /mobile/profile`.
- Accepts JSON objects and rejects invalid or non-object JSON with `400`.
- Stores the latest accepted payload under
  `~/PiFinder_data/mobile/profile_latest.json`.
- Marks the profile capability as implemented in `/mobile/status`.

Classic PiFinder impact:

Low. The endpoint only runs when called explicitly by a mobile client. The
stored profile is debug/validation data only and does not alter startup, solver,
GPS, IMU, integrator, camera, or classic UI behavior.

Validation:

```text
PASS /mobile/profile: stored_as profile_latest.json, received <timestamp>
PASS /mobile/profile invalid: status 400, code invalid_json
```

Status:

Keep.

### 2026-05-04: `/mobile/gps` endpoint

Files:

- `python/PiFinder/server.py`
- `python/PiFinder/mobile_bridge.py`
- `PiFinder_lite/mobile_bridge_api_v0.md`
- `PiFinder_lite/validate_remote_endpoints.py`

Reason:

The Android companion needs a first GPS handoff path so PiFinder Lite can
receive and inspect phone GPS fixes before any live GPS source replacement is
considered.

Change:

- Added `POST /mobile/gps`.
- Validates JSON object payloads with required `lat`, `lon`, `time_utc`, and
  `source` fields.
- Validates latitude/longitude ranges and non-negative GPS accuracy.
- Stores the latest accepted fix under `~/PiFinder_data/mobile/gps_latest.json`.
- Marks the GPS bridge capability as implemented in `/mobile/status`.

Classic PiFinder impact:

Low. This endpoint only persists debug GPS data when called explicitly. It does
not feed the GPS queue and does not affect GPSD, UBlox, fake GPS, solver,
integrator, camera, startup, or classic UI behavior.

Validation:

```text
PASS /mobile/gps: stored_as gps_latest.json, received <timestamp>
PASS /mobile/gps invalid: status 400, code invalid_gps
```

Status:

Keep.

### 2026-05-04: `/mobile/imu` debug endpoint

Files:

- `python/PiFinder/server.py`
- `python/PiFinder/mobile_bridge.py`
- `PiFinder_lite/mobile_bridge_api_v0.md`
- `PiFinder_lite/validate_remote_endpoints.py`

Reason:

The Android companion needs a safe way to send bounded orientation/IMU samples
for offline drift and confidence analysis before any mobile IMU pointing work is
considered.

Change:

- Added `POST /mobile/imu`.
- Accepts either `samples` batch payloads or a single `sample` object.
- Validates sample count, sensor names, Android timestamps, and numeric value
  arrays.
- Stores the latest accepted batch under
  `~/PiFinder_data/mobile/imu_latest.json`.
- Marks the IMU bridge capability as `implemented_debug_only` in
  `/mobile/status`.

Classic PiFinder impact:

Low. This endpoint only persists debug IMU data when called explicitly. It does
not feed PiFinder's integrator, does not alter pointing state, and does not
change GPS, solver, camera, startup, or classic UI behavior.

Validation:

```text
PASS /mobile/imu: stored_as imu_latest.json, samples 2
PASS /mobile/imu invalid: status 400, code invalid_imu
```

Status:

Keep.

### 2026-05-04: `/mobile/camera_frame` contract

Files:

- `python/PiFinder/server.py`
- `python/PiFinder/mobile_bridge.py`
- `PiFinder_lite/mobile_bridge_api_v0.md`
- `PiFinder_lite/validate_remote_endpoints.py`

Reason:

The Android companion now has a solve-targeted JPEG burst mode, so PiFinder
Lite needs a stable upload path. The first step was an API contract and a safe
placeholder; #33 then replaced the temporary `501` behavior with storage-only
upload.

Change:

- Added `POST /mobile/camera_frame`.
- The API contract chooses multipart form upload with a JPEG `frame` part and a
  UTF-8 JSON `metadata` part.
- The endpoint does not solve or apply any camera frame data.

Classic PiFinder impact:

Low. This adds a new endpoint only. It does not change classic startup, camera,
solver, GPS, IMU, integrator, web remote, or pointing behavior.

Validation:

The endpoint validator exercises the storage-only upload from #33.

Status:

Keep. This is the stable v0 contract used by the storage-only implementation.

### 2026-05-04: Storage-only mobile JPEG upload

Files:

- `python/PiFinder/server.py`
- `python/PiFinder/mobile_bridge.py`
- `mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java`
- `PiFinder_lite/mobile_bridge_api_v0.md`
- `PiFinder_lite/mobile_camera_frame_upload.md`
- `PiFinder_lite/validate_remote_endpoints.py`

Why:

Phase 2 produced at least some mobile JPEG frames that solved offline, and the
next safe step is to move one Android Camera Lab frame to PiFinder for evidence
collection. This must remain storage/debug only until quality scoring and
diagnostic solve work are explicit.

Change:

- `POST /mobile/camera_frame` now accepts multipart form data.
- Required parts are `metadata` as a JSON object and `frame` as a JPEG file.
- JPEG uploads are limited to 25 MiB and must start with JPEG magic bytes.
- PiFinder stores the upload under `~/PiFinder_data/mobile/frames/` as:
  - `<frame_id>.jpg`
  - `<frame_id>.json`
- The JSON sidecar records received time, original filename, content type,
  byte count, stored paths, and Android metadata.
- `/mobile/status` reports `camera_frame` as `implemented_storage_only`.
- Android Camera Lab keeps the latest captured JPEG in memory and adds
  `Upload Last JPEG` to send it to the configured PiFinder base URL.

Classic PiFinder impact:

Low. This adds one optional mobile endpoint path and one Android debug action.
It does not change classic startup, camera selection, solving, GPS, IMU,
integrator, web remote controls, or pointing behavior.

Validation:

- Python syntax check for `server.py`, `mobile_bridge.py`, and the endpoint
  validator.
- Direct helper test writes a sample JPEG and JSON sidecar to a temporary test
  mobile data directory.
- Full endpoint validator is still blocked in the PC environment by missing
  PiFinder runtime dependency `pydeepskylog`; use it on the Pi or after the
  Python environment is complete.
- Android terminal build remains blocked without a usable JDK in this shell;
  build/install from Android Studio.

Status:

Keep. This is required evidence plumbing for #40 image quality scoring and #41
diagnostic solving, while preserving classic PiFinder behavior.

### 2026-05-05: Phase 2 preprocessing and frame-selector analysis

Files:

- `PiFinder_lite/analyze_phase2_camera.py`
- `PiFinder_lite/phase4_dependency_map.md`

Generated local output:

- `PiFinder_lite/phase2_camera_analysis/`

The generated analysis directory is intentionally ignored by Git because it can
contain local paths, phone-test filenames, CSV/JSON reports, and other test-run
artifacts.

Why:

The first Phase 2 solve pass proved mobile JPEGs can solve, but candidate
selection was too naive: high-ISO noisy frames ranked above darker ISO 400/800
frames that actually solved.

Change:

- Added preprocessing variants to the offline analyzer:
  - baseline;
  - autocontrast;
  - percentile stretch;
  - background subtraction;
  - denoise plus stretch;
  - center crop.
- Added per-attempt CSV output for preprocessing/FOV combinations.
- Added `solve_preprocess` to the frame-level CSV/Markdown result.
- Added CLI controls for preprocessing modes, solve timeout, max candidates,
  and whether to continue after a candidate solves.
- Adjusted candidate scoring to penalize lifted gray/noisy backgrounds and
  high mean brightness before spending solver CPU.
- Re-ran the analysis over 30 ranked candidates using baseline,
  percentile-stretch, and background-subtract variants.

Result:

- 324 JPG frames analyzed.
- 30 ranked candidates attempted.
- 75 solve attempts across preprocessing/FOV variants.
- 22 successful solves.
- Baseline JPEG solving was strongest: 21 solves.
- Background subtraction rescued 1 extra frame.
- Percentile stretch did not solve any frame in this run.

Classic PiFinder impact:

None. This is an offline analysis script and generated report only. No runtime
solver, camera, integrator, GPS, IMU, or web remote behavior changes.

Status:

Keep. These findings should feed #40's server-side image quality score:
baseline first, dark-background preference, and ISO 400/800 candidates before
noisy ISO 3200 candidates for the tested Samsung run.

### 2026-05-05: Mobile JPEG image quality score

Files:

- `PiFinder_lite/score_mobile_frame.py`
- `PiFinder_lite/mobile_frame_quality_score.md`
- `PiFinder_lite/phase4_dependency_map.md`

Generated local output:

- `PiFinder_lite/phase2_camera_analysis/`

The generated analysis directory is intentionally ignored by Git because it can
contain local paths, phone-test filenames, CSV/JSON reports, and other test-run
artifacts.

Why:

Before adding diagnostic solving for uploaded mobile frames, PiFinder Lite needs
a cheap filter that rejects frames likely to waste solver CPU. #37 showed that
dark ISO400/ISO800 frames solved better than noisy ISO3200 frames with lifted
gray backgrounds.

Change:

- Added `score_mobile_frame.py`, an offline/debug scorer for JPEG files or
  directories.
- The scorer returns structured metrics:
  - background mean;
  - dark percentage;
  - saturation percentage;
  - sharpness;
  - noise proxy;
  - bright points;
  - fast connected-component centroid approximation;
  - score, grade, acceptance flag, reasons, and rejection reasons.
- The score hard-penalizes lifted gray backgrounds and caps the contribution
  from many detected points so high-ISO noise does not dominate.
- Generated CSV, JSON, and Markdown reports for the Phase 2 `Test cam` data.

Result:

- 324 JPEG frames scored.
- 48 accepted for diagnostic solving.
- 30 `HIGH`, 18 `MEDIUM`, 276 `LOW`.
- All accepted frames came from `iso_sweep`, matching #37's evidence.

Classic PiFinder impact:

None. This is a standalone Lite helper and generated report. It does not run
the solver, update pointing, feed the integrator, or change classic runtime
behavior.

Status:

Keep. #41 should use this scorer to choose stored mobile JPEGs for explicit
diagnostic solving.

### 2026-05-05: Diagnostic solve for scored mobile JPEGs

Files:

- `PiFinder_lite/diagnostic_solve_mobile_frame.py`
- `PiFinder_lite/mobile_frame_diagnostic_solve.md`
- `PiFinder_lite/phase4_dependency_map.md`

Generated local output:

- `PiFinder_lite/phase2_camera_analysis/`

The generated analysis directory is intentionally ignored by Git because it can
contain local paths, phone-test filenames, CSV/JSON reports, and other test-run
artifacts.

Why:

After #33 storage and #40 scoring, PiFinder Lite needs an explicit diagnostic
solve path to prove whether accepted mobile JPEGs actually solve before any
live/runtime integration is considered.

Change:

- Added `diagnostic_solve_mobile_frame.py`.
- The helper scores frames first using `score_mobile_frame.py`.
- It attempts Tetra3 only for frames accepted by the quality score and above
  the selected grade.
- It records structured solve results:
  - success/failure;
  - RA/Dec;
  - FOV;
  - roll;
  - matches;
  - solve time;
  - preprocessing mode;
  - FOV mode;
  - quality score and grade.
- It supports baseline and background-subtract diagnostic modes.
- It reads metadata/FOV hints from Camera Lab metadata files or JSON sidecars
  when available.

Result:

Run against `Test cam` with 12 top scored candidates:

```text
Scored 324 JPEG frames
Attempted diagnostic solve on 12 frames
Solved 9 unique frames
```

All successful solves used baseline preprocessing and `metadata_fov_74.0`.
Successful ISO400 frames typically solved in roughly 90-155 ms, with one around
239 ms.

Classic PiFinder impact:

None. This is an offline diagnostic helper. It does not update pointing, feed
the integrator, start a live solver loop, or change classic PiFinder runtime
behavior.

Status:

Keep. These results provide the evidence needed for #34's mobile camera solver
path decision.

### 2026-05-05: Mobile camera solver path decision

Files:

- `PiFinder_lite/mobile_camera_solver_path_decision.md`
- `PiFinder_lite/phase4_dependency_map.md`
- `PiFinder_lite/upstream_change_log.md`

Why:

#37, #40, and #41 provide enough evidence to decide whether the mobile camera
path should continue and what guardrails it needs.

Decision:

```text
PROMISING_TUNE_FIRST
```

Meaning:

- Continue mobile-camera development.
- Keep the path diagnostic-only for now.
- Use quality scoring before diagnostic solving.
- Prefer baseline JPEG solving first.
- Prefer metadata/FOV-assisted solve when available.
- Validate on Raspberry and repeat clearer/fixed-mount captures before any
  live solver/integrator path is considered.

Evidence:

- Phase 2 analysis: 22 successful solves from 30 ranked candidates.
- Quality score: 48 accepted candidates from 324 JPEGs.
- Diagnostic solve: 9 solved frames from 12 top scored candidates.
- Successful diagnostic solves used baseline preprocessing and
  `metadata_fov_74.0`.

Classic PiFinder impact:

None. This is a documentation/decision record only.

Status:

Keep. This decision should guide the next mobile-camera milestone:
capture -> upload -> score -> explicit diagnostic solve.

### 2026-05-05: Guided diagnostic UX and Lite documentation cleanup

Files:

- `mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java`
- `PiFinder_lite/README.md`
- `PiFinder_lite/raspberry_lite_install.md`
- `PiFinder_lite/mobile_camera_profile.md`
- `PiFinder_lite/configs/mobile_camera_profile.samsung_sm-s948b.example.json`
- `PiFinder_lite/upstream_change_log.md`

Why:

The camera evidence now supports a diagnostic workflow, but the app and docs
needed a clearer path for a user validating PiFinder Lite on real hardware.

Change:

- Added a `Mobile camera diagnostic` guide card in Android Camera Lab.
- Added `Run Diagnostic Burst` as a guided entry point for
  `solve_candidate_burst`.
- Added `Copy Diagnostic Plan` so the Raspberry-side commands can be copied from
  the app.
- The guide state updates after capture, upload, upload failure, or missing
  PiFinder URL.
- Added a Raspberry install/run checklist.
- Added a first Samsung `SM-S948B` camera recommendation profile JSON.
- Added a profile-format explainer.
- Replaced `PiFinder_lite/README.md` with a documentation map and current
  decision summary.

Classic PiFinder impact:

None. Android UX and Lite docs only. No classic PiFinder runtime behavior
changes.

Status:

Keep. This prepares issue #42 validation and future guided diagnostic workflow
work.

### 2026-05-07: Raspberry Pi OS Trixie Lite validation

Files:

- `PiFinder_lite/apt-packages-trixie-py313.txt`
- `PiFinder_lite/raspberry_lite_install.md`
- `PiFinder_lite/raspberry_validation_runbook.md`
- `PiFinder_lite/requirements-trixie-py313.txt`
- `python/PiFinder/utils.py`
- `python/PiFinder/ui/marking_menus.py`
- `python/tests/test_lite_runtime_compat.py`

Why:

The first real Raspberry validation of PiFinder Lite used a fresh Raspberry Pi
OS Trixie install with Python 3.13.5. This is newer than the classic PiFinder
runtime assumptions, so several dependency and Python compatibility issues had
to be resolved before the web remote could run.

Validated result:

```text
PiFinder reached Event Loop
Web Interface on port 8080
SkySafari server started and listening
Mobile browser loaded /remote successfully
```

Validated startup command:

```bash
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

Environment changes:

- Used `python3 -m venv --system-site-packages .venv` so the venv can reuse
  Raspberry OS packages for NumPy, SciPy, pandas, Pillow, scikit-learn, Bottle,
  Cheroot, and related heavy dependencies.
- Installed `protobuf>=5.27` because current `cedar-solve` generated protobuf
  code imports `google.protobuf.runtime_version`.
- Installed `grpcio>=1.71.0` from a binary wheel because current
  `cedar-solve` generated gRPC code requires a newer runtime than
  `python3-grpcio` from apt.
- Installed `skyfield>=1.53` because `skyfield==1.45` imports `numpy.float_`,
  which is no longer available in NumPy 2.x.
- Installed `luma.core`, `luma.oled`, `luma.lcd`, and `luma.emulator` so the
  existing PiFinder display imports can load even in debug/headless validation.
- Installed `tetra3` with `pip install -e PiFinder/tetra3 --no-deps` after a
  shallow submodule checkout.
- Downloaded `astro_data/hip_main.dat`, which is intentionally ignored by Git
  but required by the chart preload path.

Integrated compatibility changes:

- `python/PiFinder/utils.py`: added `resolve_tetra3_dir(...)`, which prefers the
  package parent `python/PiFinder/tetra3` when the bundled submodule has a
  package `tetra3/__init__.py`, and falls back to the legacy nested
  `python/PiFinder/tetra3/tetra3` layout when needed. This avoids treating
  `tetra3.py` as a standalone module on the validated Trixie setup while keeping
  a compatibility path for older layouts.
- `python/PiFinder/ui/marking_menus.py`: changed the `MarkingMenu.up` dataclass
  default to use `field(default_factory=...)`, because Python 3.13 rejects a
  mutable dataclass default of type `MarkingMenuOption`.
- Replaced the temporary local `timezonefinder` UTC shim recommendation with
  `timezonefinder==8.2.4` in the Lite/Trixie requirements. The PC venv verified
  `TimezoneFinder().timezone_at(...)` returns `Europe/Madrid` for Madrid
  coordinates on Python 3.13.

Classic PiFinder impact:

The runtime dependency changes are installation concerns only. The two Python
source changes are intentionally small compatibility fixes:

- `resolve_tetra3_dir(...)` only affects how the bundled Tetra3 path is added to
  `sys.path`.
- `field(default_factory=...)` preserves the existing default HELP option while
  preventing shared mutable state and Python 3.13 import failure.

They still need normal validation against the classic supported Raspberry
image/runtime before an upstream PR.

Status:

Keep with follow-up validation.

- Keep the documentation and install recipe.
- Validate `timezonefinder==8.2.4` on the Raspberry Trixie venv before GPS
  bridge work depends on local timezone calculation.
- Re-run classic PiFinder startup/tests on the original supported runtime before
  proposing these changes upstream.

## Pre-Merge Checklist

Before merging Lite work back into a branch intended for upstream PiFinder:

- Review this file and remove or revert any record marked temporary.
- Confirm each remaining `python/PiFinder/` change has a test or manual
  validation note.
- Confirm classic startup still works with the normal keyboard/display/camera
  configuration.
- Confirm Lite startup works with the documented headless command.
- Keep Android/mobile code and PiFinder core code separated unless a bridge
  endpoint or interface change is explicitly required.
