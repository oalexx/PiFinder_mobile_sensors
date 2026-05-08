# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current Project Context

This fork is adding PiFinder Lite / Mobile Companion capabilities while keeping
classic PiFinder behavior intact by default. Treat mobile work as additive:
new endpoints, optional flows, diagnostics, and documented runtime profiles
should not disturb the original hardware mode unless explicitly requested.

Current status:

- Phase 1 Android compatibility tester is implemented.
- Phase 3 PiFinder Lite headless/web remote workflow is implemented.
- Phase 4 mobile bridge is implemented and Raspberry-validated.
- Phase 2 night-sky camera validation remains the active evidence gate.

Validated Phase 4 capabilities:

- `/mobile/status`, `/mobile/profile`, `/mobile/gps`, `/mobile/imu`, and
  `/mobile/camera_frame` exist.
- Mobile GPS can feed PiFinder runtime state when the Android app sends GPS.
- Mobile IMU batches are stored for diagnostics and confidence analysis.
- Mobile JPEG upload is storage/diagnostic-only, with quality scoring and
  diagnostic solve tooling.

Guardrails:

- Do not feed mobile camera solves into the integrator yet.
- Do not feed mobile IMU into the integrator yet.
- Keep mobile camera work diagnostic until Phase 2 produces reliable clear-sky
  evidence.
- Do not commit phone captures, generated analysis output, local paths, or
  precise private GPS coordinates.

## Development Commands

**Development workflow uses Nox for task automation:**
```bash
nox -s lint          # Code linting with Ruff (auto-fixes issues)
nox -s format        # Code formatting with Ruff
nox -s type_hints    # Type checking with MyPy
nox -s smoke_tests   # Quick functionality validation
nox -s unit_tests    # Full unit test suite
nox -s babel         # I18n message extraction and compilation
```

**Direct testing with pytest:**
```bash
pytest -m smoke      # Smoke tests for core functionality
pytest -m unit       # Unit tests for isolated components
pytest -m integration # End-to-end integration tests
```

**Development setup:**
```bash
cd python/
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_dev.txt
```
If the .venv dir already exists, you can directly source it and run the app.


**Running the application:**
Development setup has to have run and you should be in .venv virtual environment
```bash
cd python/
python -m PiFinder.main [options]
```
Usual startup:

```bash
python3.9 -m PiFinder.main -fh --camera debug --keyboard local -x
```

**PiFinder Lite Raspberry validation startup:**
```bash
cd ~/PiFinder_mobile_sensors/python
source .venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

For Raspberry Pi OS Trixie / Python 3.13, use the Lite-specific install files:

- `PiFinder_lite/raspberry_lite_install.md`
- `PiFinder_lite/apt-packages-trixie-py313.txt`
- `PiFinder_lite/requirements-trixie-py313.txt`

**Android app:**
```powershell
cd mobile
.\gradlew.bat assembleDebug
```

Opening the `mobile` folder in Android Studio is also supported. Do not run the
Android Gradle Plugin upgrade assistant unless the task is specifically about
upgrading the Android build.

**Focused Lite/mobile tests:**
```powershell
.\python\.venv\Scripts\python.exe -m pytest python\tests\test_mobile_bridge.py python\tests\test_mobile_imu_analysis.py python\tests\test_lite_runtime_compat.py -q
```

## Architecture Overview

**Multi-Process Design:** PiFinder uses a process-based architecture where each major subsystem runs in its own process, communicating via queues and shared state objects:

- **Main Process** (`main.py`) - UI event loop, menu system, user interaction
- **Camera Process** - Image capture from various camera types (Pi, ASI, debug)
- **Solver Process** - Plate solving using Tetra3/Cedar libraries for star pattern recognition
- **GPS Process** - Location/time via GPSD or UBlox direct interface
- **IMU Process** - Motion tracking with BNO055 sensor
- **Integrator Process** - Combines solver + IMU data for real-time positioning
- **Web Server Process** - Web interface and SkySafari telescope control integration
- **Position Server Process** - External protocol support

**State Management:**
- `SharedStateObj` - Process-shared state using multiprocessing managers
- `UIState` - UI-specific state management
- Real-time synchronization of telescope position, GPS coordinates, and solved sky coordinates

**Database Layer:**
- SQLite backend (`astro_data/pifinder_objects.db`)
- `ObjectsDatabase` - Astronomical catalog management (NGC, Messier, etc.)
- `ObservationsDatabase` - Session logging and observation tracking
- Modular catalog import system supporting multiple astronomical databases

**Hardware Abstraction:**
- Camera interface supporting IMX296 (global shutter), IMX290/462, HQ cameras
- Display system for SSD1351 OLED and ST7789 LCD with red-light preservation
- Hardware keypad with PWM brightness control
- GPS integration via GPSD or direct UBlox protocol
- IMU sensor integration for motion detection and telescope orientation

## Key Directories

- `python/PiFinder/` - Core application modules
- `python/PiFinder/ui/` - User interface components (menus, screens, charts)
- `python/PiFinder/db/` - Database abstraction layer
- `astro_data/` - Astronomical catalogs and object databases
- `python/tests/` - Test suite (smoke, unit, integration markers)
- `case/` - 3D printable enclosure files
- `docs/` - Documentation and build guides
- `PiFinder_lite/` - Lite setup, validation runbooks, mobile camera/IMU tools
- `mobile/` - Android companion app

## Configuration

**Config Files:**
- `default_config.json` - System defaults
- `~/PiFinder_data/config.json` - User settings
- Equipment profiles for telescopes and eyepieces
- Display, camera, GPS, and solver parameters

**Hardware Configuration:**
- Camera selection: Pi Camera, ASI cameras, debug mode
- Display type: OLED vs LCD with brightness/orientation settings
- Input method: hardware keypad, local keyboard, web interface
- GPS receiver: GPSD daemon vs direct UBlox protocol

**PiFinder Lite Runtime Notes:**
- Use `--keyboard none` for headless/mobile tests.
- `/remote` remains the primary phone UI surface.
- `/mobile/gps` is live runtime input once posted by the app.
- `/mobile/imu` is currently diagnostic/confidence data only.
- `/mobile/camera_frame` stores JPEGs for analysis; live solving is not wired
  into the main runtime yet.

## Testing Strategy

Tests use pytest with custom markers for different test types. The smoke tests provide quick validation while unit tests cover isolated functionality. Integration tests validate end-to-end workflows including the multi-process architecture.

**Key test areas:**
- Calculation utilities and coordinate transformations
- Catalog data validation and import processes
- Menu structure and navigation logic
- Multi-process logging and communication
- Hardware interface abstractions
- Mobile bridge endpoint behavior and storage
- Raspberry/Python 3.13 Lite compatibility shims
- Mobile IMU confidence analysis

**Useful Raspberry diagnostics:**
```bash
python PiFinder_lite/score_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames"
python PiFinder_lite/diagnostic_solve_mobile_frame.py --input "$HOME/PiFinder_data/mobile/frames" --max-frames 12 --solve-timeout-ms 1000 --preprocess-modes baseline,background_subtract
python PiFinder_lite/analyze_mobile_imu.py --input "$HOME/PiFinder_data/mobile/imu_latest.json"
```

## Code Quality

- **Linting:** Ruff with Python 3.9 target, Black-compatible formatting
- **Type Checking:** MyPy with gradual typing adoption
- **Code Style:** 88-character line length, double quotes, space indentation
- **I18n Support:** Babel integration for multi-language UI

The codebase follows modern Python practices with type hints, comprehensive testing, and automated code quality checks integrated into the development workflow.
