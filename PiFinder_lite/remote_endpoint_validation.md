# Remote Endpoint Validation

Issue: [#15 Validate existing /remote, /image, and /key_callback from phone browser](https://github.com/oalexx/PiFinder_mobile_sensors/issues/15)

## Goal

Confirm that the existing PiFinder web remote can support PiFinder Lite without
changing classic PiFinder behavior.

The relevant existing endpoints are:

- `/remote`: renders the browser remote control.
- `/image`: returns the current PiFinder screen as PNG.
- `/key_callback`: accepts virtual button presses and pushes them into the
  keyboard queue.

## Code Path

`python/PiFinder/server.py` defines the three routes:

```text
/remote -> views/remote.tpl
/image -> shared_state.screen() -> PNG response
/key_callback -> button mapping -> keyboard_queue
```

`/remote` and `/key_callback` are protected by the existing PiFinder web login.
`/image` is currently public and is polled by the remote page.

## Local Automated Validation

The helper script `PiFinder_lite/validate_remote_endpoints.py` starts the real
`PiFinder.server.Server` class on a test port with fake queues and fake shared
state. This avoids starting the full solver/camera stack while still exercising
the actual Bottle routes.

Run from repository root:

```bash
cd python/
.\.conda-py39\python.exe ..\PiFinder_lite\validate_remote_endpoints.py --port 18080
```

The script checks:

- `/image` responds with PNG bytes.
- `/mobile/status` responds with Mobile Bridge API v0 JSON.
- `/mobile/profile` accepts a valid profile JSON object.
- `/mobile/profile` rejects non-object JSON with a clear `400` error.
- `/mobile/gps` accepts a valid GPS JSON payload.
- `/mobile/gps` rejects invalid coordinates with a clear `400` error.
- `/mobile/imu` accepts a bounded IMU sample batch.
- `/mobile/imu` rejects invalid sample values with a clear `400` error.
- `/login` sets an auth cookie.
- `/remote` renders the expected remote HTML.
- `/key_callback` returns success and places a key code on the keyboard queue.

Local result on the development workstation:

```text
PASS /image: 724 bytes, content-type image/png
PASS /mobile/status: api mobile-bridge-v0, server_time 2026-05-03T19:30:39Z
PASS /mobile/profile: stored_as profile_latest.json, received 2026-05-03T19:30:39Z
PASS /mobile/profile invalid: status 400, code invalid_json
PASS /mobile/gps: stored_as gps_latest.json, received 2026-05-03T19:30:39Z
PASS /mobile/gps invalid: status 400, code invalid_gps
PASS /mobile/imu: stored_as imu_latest.json, samples 2
PASS /mobile/imu invalid: status 400, code invalid_imu
PASS /remote: HTML length 7415 chars
PASS /key_callback: response {"message": "success"}, queued key 20
```

The Mobile Bridge calls also write:

```text
~/PiFinder_data/mobile/status.json
~/PiFinder_data/mobile/profile_latest.json
~/PiFinder_data/mobile/gps_latest.json
~/PiFinder_data/mobile/imu_latest.json
```

## Manual Phone Validation

On Raspberry Pi / PiFinder Lite:

```bash
cd python/
python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
```

From a phone on the same network:

```text
http://<pifinder-ip>/remote
```

Fallback:

```text
http://<pifinder-ip>:8080/remote
```

Checks:

1. Login with the PiFinder web password.
2. Confirm the remote screen image appears.
3. Press a direction button and confirm the PiFinder UI changes.
4. Confirm `/image` keeps refreshing without manual reload.
5. Note latency, refresh smoothness, and whether buttons are comfortable on the
   phone screen.

## Findings

The current `/remote` template is simple and usable as a first Lite target:

- The display image is constrained to `max-width: 256px`.
- Buttons use a 4-column grid and fit in a narrow mobile viewport.
- The page polls `/image` every 100 ms.
- Alt and long-press modes are implemented as toggle buttons before the next
  key press.

Phone browser validation from the development PC:

- URL used: `http://192.168.8.167:18080/remote`
- Result: the page loaded from a phone on the same WiFi network.
- The remote screen image appeared.
- Regular buttons were usable from the phone browser.
- `Ent+` and `Long` toggles deactivated after pressing any normal key, not only
  direction keys. This matches the current template behavior: they are
  next-key modifiers.
- Pressing `Ent+` or `Long` again also deactivated the selected modifier.

Known notes for later UX work:

- The button labels in the current file show mojibake in this Windows checkout
  for arrows and square symbols. Verify on Raspberry/browser before changing
  encoding-sensitive template content.
- Polling `/image` every 100 ms is responsive but may be unnecessarily aggressive
  for phone battery/network use.
- The page is functional, but it is not yet optimized for split-screen use with
  SkySafari.

## Upstream Impact

No original PiFinder code changes are required for this validation. The helper
script and notes live under `PiFinder_lite/`.
