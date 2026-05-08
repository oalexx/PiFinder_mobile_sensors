# Keyboard None Validation

Issue: [#14 Validate keyboard none / no physical keypad workflow](https://github.com/oalexx/PiFinder_mobile_sensors/issues/14)

## Goal

Confirm that PiFinder Lite can start without a physical keypad process reading
hardware, while still allowing remote key presses to control the UI through the
existing web remote.

## Code Path

Startup selection happens in `python/PiFinder/main.py`:

```text
--keyboard none -> PiFinder.keyboard_none
```

The main process always starts a keyboard process with:

```text
keyboard.run_keyboard(keyboard_queue, shared_state, keyboard_logqueue, bloom_key_remap)
```

`keyboard_none.py` must therefore accept the same process arguments as the other
keyboard implementations, even if it ignores `bloom_key_remap`.

## Fix Applied

`python/PiFinder/keyboard_none.py` now exposes:

```python
def run_keyboard(q, shared_state, log_queue, bloom_remap=False):
```

This matches the call shape used by `main.py` and prevents the no-keyboard child
process from failing immediately with an argument mismatch.

The implementation intentionally does not read any physical input. It only keeps
the keyboard process alive:

```text
while True:
    time.sleep(1)
```

## Remote Key Flow

The no-keyboard mode still supports UI input because remote button presses do not
come from `keyboard_none.py`. They enter through the existing web server:

```text
/remote -> /key_callback -> Server.key_callback -> keyboard_queue -> main UI loop
```

In `python/PiFinder/server.py`, `/key_callback` maps button names to
`KeyboardInterface` key codes and pushes them into `keyboard_queue`.

In `python/PiFinder/main.py`, the UI loop consumes `keyboard_queue` and dispatches
the key code to `menu_manager.key_*` handlers. This is the same queue consumed
when using the physical keypad.

## Recommended Validation Command

For development or Raspberry testing without hardware dependencies:

```bash
cd python/
python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
```

Expected behavior:

- PiFinder starts with fake GPS and fake IMU.
- Debug camera is used.
- No physical keypad is required.
- The keyboard process stays alive.
- The web server starts on port `80`, or falls back to `8080`.
- `/remote` can send virtual key presses through `/key_callback`.

## Browser Validation

From a phone or browser on the same network:

```text
http://<pifinder-ip>/remote
```

Fallback if port `80` is unavailable:

```text
http://<pifinder-ip>:8080/remote
```

Minimum checks:

1. Open `/remote`.
2. Press a direction button.
3. Confirm the PiFinder screen changes through `/image`.
4. Press numeric or square controls if available.
5. Confirm there is no physical keypad dependency.

## Automated Check

`python/tests/test_keyboard_none.py` verifies that `keyboard_none.run_keyboard`
accepts the same argument shape that `main.py` uses when spawning the keyboard
process.

Run:

```bash
cd python/
pytest tests/test_keyboard_none.py
```

Local result on the development workstation:

```text
tests/test_keyboard_none.py . [100%]
1 passed
```

## Dependency Setup Used For Local Validation

The first attempt used a Python 3.13 virtual environment, but the pinned
`numpy==1.26.2` dependency does not provide a Python 3.13 wheel and tried to
build from source on Windows. For a closer match to the PiFinder target runtime,
the validation was moved to a Python 3.9 conda environment at:

```text
python/.conda-py39
```

The repository dependency install needed these local Windows adjustments:

- `sh==1.14.3` was excluded from `requirements.txt` because it imports `fcntl`,
  which is not available on Windows.
- `requirements_dev.txt` installed successfully after the runtime dependencies.
- `python/PiFinder/tetra3` was empty locally, so `cedar-solve` had to be cloned
  into that path before PiFinder could import `tetra3`.
- The current `cedar-solve` master generated code required newer runtime
  packages than the repository pins:
  - `protobuf>=5.26,<6`
  - `grpcio>=1.71,<2`
- `cedar-solve` attempted to downgrade Pillow below the version PiFinder needs
  for `ImageFont.Layout`; Pillow was restored to `10.4.0`.

These steps are local validation notes, not a recommended Raspberry deployment
recipe.

## Startup Validation

```bash
cd python/
.\.conda-py39\python.exe -m PiFinder.main -fh --camera debug --keyboard none -x --display pg_128
```

Initial full-process startup then reached the logging configuration step and
failed because `python/pifinder_logconf.json` contains the literal text:

```text
logconf_default.json
```

On Windows this was read as JSON5 content and raised:

```text
ValueError: <string>:1 Unexpected "l" at column 1
```

For validation only, `logconf_default.json` was temporarily copied over
`pifinder_logconf.json`, the startup command was run, and the original file
content was restored immediately afterward.

With that temporary logging workaround, the command stayed alive until the
25-second validation timeout. That confirms the application gets past the
`--keyboard none` process startup and does not hit the previous keyboard
argument mismatch.

## Local Result

The issue #14 code path is validated at two levels:

- the unit test confirms the keyboard process signature matches `main.py`;
- the full PiFinder command starts far enough to remain running under
  `--keyboard none` when the local Windows logging-file quirk is bypassed.

The remaining validation should happen on Raspberry Pi or the real Lite target,
where Linux symlink-style config behavior and hardware assumptions are closer to
production.

## Remaining Raspberry Validation

This code-level fix should be validated on a Raspberry Pi with the full runtime:

- run the recommended startup command;
- open `/remote`;
- press virtual keys;
- confirm UI navigation works;
- record whether web server uses port `80` or `8080`;
- record any hardware assumptions still present outside the keyboard path.
