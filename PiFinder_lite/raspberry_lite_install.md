# Raspberry PiFinder Lite Install

This document is the practical install/run checklist for PiFinder Lite and the
Android mobile companion bridge.

It keeps classic PiFinder intact: all Lite behavior is optional and should be
started explicitly.

Validated on:

```text
Raspberry Pi OS Trixie
Python 3.13.5
PiFinder branch: phase4-mobile-camera-diagnostic
Startup command: python -m PiFinder.main -fh --camera debug --keyboard none -x
Validated web URL: http://<raspberry-ip>:8080/remote
```

PiFinder upstream was originally developed against an older Python/runtime
stack. On Trixie/Python 3.13, use the compatibility notes below instead of
blindly installing the pinned upstream `requirements.txt`.

## 1. Prepare The Raspberry

Install system packages:

```bash
sudo apt update
xargs -a PiFinder_lite/apt-packages-trixie-py313.txt \
  sudo apt -o Acquire::ForceIPv4=true install -y
```

Create a venv that can use the Raspberry OS packages:

```bash
cd ~/PiFinder_mobile_sensors/python
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

Install PiFinder Lite runtime packages that were validated on Trixie:

```bash
pip install -r ../PiFinder_lite/requirements-trixie-py313.txt
```

Do not install the pinned `timezonefinder==6.1.9` on Trixie. It pulls an older
`h3` build path that failed during validation. The Lite/Trixie requirements use
`timezonefinder==8.2.4`, which supports the modern `h3` 4.x API. They also pin
`flatbuffers==25.12.19`, because piwheels can otherwise provide an old
date-versioned `flatbuffers` build that imports Python's removed `imp` module.

## 2. Initialize Tetra3/Cedar Solve

Initialize the solver submodule with a shallow checkout:

```bash
cd ~/PiFinder_mobile_sensors
git submodule update --init --recursive --depth 1 python/PiFinder/tetra3
```

Install it without dependencies, because NumPy/Pillow are supplied by the
Raspberry OS packages:

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
pip install -e PiFinder/tetra3 --no-deps
python -c "import tetra3; print('tetra3 ok')"
```

## 3. Download External Star Data

`astro_data/hip_main.dat` is intentionally ignored by Git. PiFinder needs it to
render the chart module.

```bash
cd ~/PiFinder_mobile_sensors
wget -O astro_data/hip_main.dat \
  https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat
ls -lh astro_data/hip_main.dat
```

Expected size is about 51 MiB.

## 4. Python 3.13 Compatibility

This branch includes the two source-level compatibility fixes found during the
first Trixie validation:

- Tetra3 import path resolution now prefers the package parent
  `python/PiFinder/tetra3` when the submodule has a package layout, with a
  fallback for the legacy nested layout.
- `MarkingMenu.up` uses `field(default_factory=...)`, which avoids the Python
  3.13 dataclass mutable-default import error.

Timezone lookup should use `timezonefinder==8.2.4` plus
`flatbuffers==25.12.19` from the Lite/Trixie requirements. The first manual
validation used a temporary UTC shim before this dependency strategy was tested.

## 5. Validate Imports

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -c "from google.protobuf import runtime_version; print('protobuf ok')"
python -c "import grpc; print(grpc.__version__)"
python -c "import skyfield, numpy; print('skyfield/numpy ok', numpy.__version__)"
python -c "import luma.core.device, luma.oled.device, luma.lcd.device; print('luma ok')"
python -c "import PiFinder.main; print('main import ok')"
```

## 6. Optional Lite Config

Back up the current PiFinder user config first:

```bash
mkdir -p ~/PiFinder_data
cp ~/PiFinder_data/config.json ~/PiFinder_data/config.before_lite.json
```

Copy the optional Lite profile:

```bash
cp ../PiFinder_lite/configs/pifinder_lite_config.example.json ~/PiFinder_data/config.json
```

This does not change `default_config.json`; it only changes the local user
config if you choose to copy it.

## 7. Start Headless/Lite

Hardware-light validation:

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

Raspberry with normal camera/GPS stack but no keypad workflow:

```bash
cd python
source .venv/bin/activate
python -m PiFinder.main --keyboard none -x
```

If GPS hardware is unavailable:

```bash
python -m PiFinder.main --gps fake --keyboard none -x
```

Successful validation reaches:

```text
Web Interface on port 8080
SkySafari server started and listening
Event Loop
```

## 8. Connect From Android

Find the Raspberry IP address:

```bash
hostname -I
```

In the Android app:

```text
PiFinder Remote -> Base URL -> http://<raspberry-ip>:8080
```

Use port `80` if PiFinder bound to port 80. Use `8080` if it fell back.

Check:

```text
Test Connection
Open Remote
```

Browser validation:

```text
http://<raspberry-ip>:8080/remote
http://<raspberry-ip>:8080/mobile/status
```

## 9. Validate Mobile Camera Diagnostic

On Android:

```text
Camera Lab -> Save Folder
Camera Lab -> Run Diagnostic Burst
Camera Lab -> Upload Last JPEG
```

On Raspberry:

```bash
python PiFinder_lite/score_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames"
python PiFinder_lite/diagnostic_solve_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames" --max-frames 12 --solve-timeout-ms 1000 --preprocess-modes baseline,background_subtract
```

Expected stored files:

```text
~/PiFinder_data/mobile/frames/<frame_id>.jpg
~/PiFinder_data/mobile/frames/<frame_id>.json
```

## 6. Record Results

For issue #42, record:

- Android model and app build.
- PiFinder commit/branch.
- startup command;
- Pi IP and selected port;
- upload success/failure;
- stored frame path;
- score grade;
- diagnostic solve result;
- matches, FOV, solve time;
- sky conditions.

## Guardrails

This install path must not:

- feed mobile camera solves into live pointing;
- feed mobile IMU into the integrator;
- replace classic PiFinder startup defaults;
- require a user to change upstream PiFinder behavior permanently.
