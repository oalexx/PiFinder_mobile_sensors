# SkySafari Split-Screen Validation

Issue: [#17 Validate SkySafari + PiFinder Remote split-screen workflow](https://github.com/oalexx/PiFinder_mobile_sensors/issues/17)

## Goal

Validate the intended PiFinder Lite observing workflow:

```text
SkySafari -> LX200/TCP -> PiFinder position server
Phone browser -> /remote + /image + /key_callback -> PiFinder web server
```

## Existing PiFinder Path

The SkySafari server is implemented in `python/PiFinder/pos_server.py`.

Main startup launches it as the `SkySafariServer` process:

```text
pos_server.run_server(shared_state, ui_queue, posserver_logqueue)
```

The server listens on TCP port `4030` and implements a small LX200-compatible
command set, including:

- `:GR#`: get telescope RA;
- `:GD#`: get telescope Dec;
- `:GVP#`: get product name;
- `:Sr...#` + `:Sd...#`: set target coordinates and push a new object into the
  PiFinder UI flow.

## Local Automated Validation

The helper script `PiFinder_lite/validate_lx200_server.py` starts the existing
`PiFinder.pos_server` with fake shared state and checks the socket protocol.

Run from repository root:

```bash
cd python/
.\.conda-py39\python.exe ..\PiFinder_lite\validate_lx200_server.py
```

The script checks:

- TCP connection to port `4030`;
- product response reports `PiFinder`;
- RA and Dec commands return LX200-style values;
- a push-to target sequence queues `push_object`.

On Windows, the helper bypasses PiFinder's multiprocessing logging config inside
the test child process because this checkout stores `pifinder_logconf.json` as a
literal pointer-like file. This does not affect Raspberry validation or the
original PiFinder code.

Local result on the development workstation:

```text
PASS product: :GVP# -> 'PiFinder#'
PASS ra: :GR# -> '05:36:08#'
PASS dec: :GD# -> "+22*02'04#"
PASS pushto: :Sr# -> '1', :Sd# -> '1', ui_queue -> 'push_object'
```

## SkySafari Settings To Test On Phone/Tablet

In SkySafari, configure a telescope connection similar to:

```text
Scope Type: Meade LX200 Classic / LX200 compatible
Mount Type: Alt-Az GoTo
Communication: Connect via Wi-Fi / TCP
IP Address: <pifinder-ip>
Port: 4030
```

Exact labels vary between SkySafari versions.

## Split-Screen Workflow

1. Start PiFinder Lite/headless:

   ```bash
   cd python/
   python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
   ```

2. Open PiFinder Remote from the phone browser:

   ```text
   http://<pifinder-ip>/remote
   ```

   Fallback:

   ```text
   http://<pifinder-ip>:8080/remote
   ```

3. Open SkySafari and connect to PiFinder at port `4030`.
4. Use split screen if the device supports it. Otherwise, switch between
   SkySafari and the browser.
5. Confirm PiFinder Remote remains reachable while SkySafari is connected.
6. Confirm SkySafari can query the telescope position.
7. Select a target in SkySafari and issue a GoTo/PushTo command.
8. Confirm PiFinder receives the pushed target.

## Notes From Current Validation

- `/remote` has already been validated from an Android phone browser using the
  development PC server.
- The mobile remote layout has been improved and documented in
  `PiFinder_lite/documentation/mobile_remote_layout.md`.
- This issue still needs a real SkySafari app validation because the app itself
  is not available in the local automation environment.

## Expected Follow-Ups

Create follow-up issues if validation shows:

- SkySafari cannot connect to TCP port `4030`;
- Android split-screen is too cramped;
- browser backgrounding interrupts `/image` refresh;
- SkySafari push-to commands reach PiFinder but do not surface cleanly in the UI;
- the position server should expose its port/config in Lite documentation.
