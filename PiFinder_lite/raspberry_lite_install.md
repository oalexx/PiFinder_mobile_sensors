# Raspberry PiFinder Lite Install

This document is the practical install/run checklist for PiFinder Lite and the
Android mobile companion bridge.

It keeps classic PiFinder intact: all Lite behavior is optional and should be
started explicitly.

## 1. Prepare The Raspberry

Start from a working PiFinder checkout on the Raspberry.

Recommended Python environment follows the upstream PiFinder setup:

```bash
cd python
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If the environment already exists:

```bash
cd python
source .venv/bin/activate
```

## 2. Optional Lite Config

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

## 3. Start Headless/Lite

Hardware-light validation:

```bash
cd python
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

## 4. Connect From Android

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

## 5. Validate Mobile Camera Diagnostic

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
