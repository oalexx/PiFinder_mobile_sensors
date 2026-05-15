# Upstream Release Resync - 2026-05-15

This document records the first experimental resync of the PiFinder Lite/Mobile
fork onto the official `brickbots/PiFinder:release` branch.

## Goal

Keep the fork current with official PiFinder improvements while preserving the
Lite/mobile work as additive functionality.

## Branches

- Official base: `upstream/release` at `651e23f`
- Fork feature base: `main` at `364f876`
- Experimental branch: `codex/upstream-release-resync-20260515`

## Merge Strategy

The histories are unrelated, so this resync is not a normal merge. The
experimental branch starts from `upstream/release` and reintroduces the fork
layers deliberately:

- `AGENTS.md`, `CLAUDE.md`, and project docs from the fork are preserved.
- `PiFinder_lite/` and `mobile/` are restored as additive project areas.
- `python/PiFinder/mobile_bridge.py` is restored as the mobile bridge module.
- Focused Lite/mobile pytest coverage is restored.
- Official PiFinder files receive only the minimal hooks required for the
  mobile bridge and Lite runtime compatibility.

## Safety Boundaries

- Mobile GPS may update PiFinder GPS runtime state through `/mobile/gps`.
- Mobile IMU remains diagnostic/read-only and must not feed the integrator.
- Mobile camera upload and diagnostic solve remain diagnostic-only and must not
  feed runtime pointing.
- Camera recommendation profiles remain evidence summaries, not runtime config.

## Ported Official-File Hooks

- `python/PiFinder/server.py`: adds `/mobile/*` endpoints and imports
  `mobile_bridge`.
- `python/PiFinder/utils.py`: resolves bundled `tetra3` robustly across
  upstream and fork directory layouts.
- `python/PiFinder/keyboard_none.py`: accepts the current keyboard process
  signature and logs as `KeyboardNone`.
- `python/PiFinder/ui/marking_menus.py`: avoids a mutable dataclass default.

## Validation Checklist

Run before considering this branch for `main`:

```bash
python -m pytest python/tests/test_mobile_bridge.py python/tests/test_mobile_camera_profile.py python/tests/test_mobile_imu_analysis.py python/tests/test_mobile_imu_drift_analysis.py python/tests/test_mobile_mount_offset.py python/tests/test_mobile_mount_repeatability.py python/tests/test_lite_runtime_compat.py -q
python -m pytest python/tests/test_mobile_android_camera_solve_ui.py python/tests/test_mobile_android_calibration_ui.py -q
```

Raspberry follow-up:

```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

Then verify:

- `/remote` loads.
- `/mobile/status` returns JSON.
- `/mobile/profile`, `/mobile/gps`, `/mobile/imu`, and
  `/mobile/camera_frame` still accept Android payloads.
- `/mobile/camera_reports` and `/mobile/camera_solve` remain diagnostic-only.

