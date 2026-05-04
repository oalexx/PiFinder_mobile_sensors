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
