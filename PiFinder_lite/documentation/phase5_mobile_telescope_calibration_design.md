# Phase 5 Mobile-To-Telescope Calibration Design

Issue: #43

## Goal

Phase 5 defines how PiFinder Lite can calibrate a rigidly mounted Android phone
against the telescope optical axis. The phone can then become a useful
orientation reference, but only after repeatability is proven.

This phase is diagnostic-first. It must not feed mobile IMU data into the
PiFinder integrator until a mount profile is stable, repeatable, and explicitly
enabled.

## Non-Goals

- Do not replace PiFinder's existing camera/solver/integrator loop.
- Do not enable mobile IMU guidance by default.
- Do not assume magnetometer-based orientation is reliable.
- Do not require clear-sky plate solving for the first implementation.
- Do not store private captures or exact user locations in the repository.

## Starting Evidence

Phase 4 showed that Android can send IMU batches to the Raspberry and that
`game_rotation_vector` can be stable when the phone is stationary. The first
stationary Raspberry test rated `game_rotation_vector` higher than
`rotation_vector`, while `rotation_vector` may still be useful for comparison.

Recommended first sensor path:

```text
primary: game_rotation_vector
comparison: rotation_vector
```

Reasoning:

- `game_rotation_vector` avoids magnetometer dependence and is less exposed to
  magnetic contamination near telescope hardware.
- `rotation_vector` can include absolute heading information, but that is also
  where magnetic interference can enter.
- A calibration profile can work from relative orientation if the reference
  observation defines the optical-axis relationship.

## User Workflow

1. Mount the phone rigidly on the telescope tube.
2. Open the Android calibration flow.
3. Connect to PiFinder Lite through the existing base URL setting.
4. Capture a `stationary` batch with the tube not moving.
5. Point the telescope at a known reference target.
6. Capture a `mounted_reference` batch while the tube is still.
7. Optionally capture a `repeat_check` batch after moving away and returning to
   the same target.
8. Generate a candidate mount profile on Raspberry or in the app.
9. Validate repeatability before using the profile for any runtime behavior.

Reference target options:

- Known bright star selected manually in SkySafari/PiFinder.
- Existing PiFinder solved position from the original camera path.
- Manual altitude/azimuth or RA/Dec reference during early diagnostics.

The first version should allow manual reference entry so Phase 5 can progress
without depending on mobile camera solves.

## Data Flow

```text
Android calibration UI
  -> labeled IMU batch
  -> /mobile/imu
  -> ~/PiFinder_data/mobile/imu_latest.json
  -> calibration analysis tool
  -> candidate mount profile JSON
  -> repeatability validation
  -> optional saved mount profile
```

Existing generic IMU uploads should keep working. Labeled calibration batches
extend the payload; they do not replace the Phase 4 diagnostic endpoint.

Implementation note:

- Android `SEND IMU BATCH` sends `batch_label: diagnostic`.
- Android `MOUNT REF IMU` sends `batch_label: mounted_reference` and should be
  captured while the mounted phone and telescope tube are still.
- Android `CALIBRATION` provides the first guided collection screen with
  connection check, profile/GPS upload, manual reference note, mounted-reference
  capture, and copied evidence JSON.
- PiFinder stores the accepted label in
  `~/PiFinder_data/mobile/imu_latest.json`, and `analyze_mobile_imu.py`
  includes the label in its report.
- `compute_mobile_mount_offset.py` consumes that IMU batch plus an explicit
  `q_tube_reference` quaternion and writes a disabled candidate mount profile
  with `q_phone_to_tube`, confidence, and warnings.

## Inputs

Required:

- Phone model and Android build/app version.
- Sensor source: `game_rotation_vector` first, `rotation_vector` for
  comparison.
- Timestamped quaternion or rotation-vector samples.
- Batch label: `stationary`, `mounted_reference`, `repeat_check`, or `slew`.
- Screen orientation.
- Reference target or reference pointing.

Useful optional inputs:

- GPS location and time.
- Phone battery state.
- Sensor accuracy when available.
- Telescope/mount notes.
- Physical mount notes such as phone side, camera orientation, and clamp style.

## Outputs

Primary output:

```json
{
  "schema": "pifinder-mobile-mount-profile-v0",
  "status": "candidate",
  "phone_model": "example",
  "sensor_source": "game_rotation_vector",
  "axis_mapping": {
    "phone_forward": "unknown",
    "phone_up": "unknown",
    "tube_axis": "optical_axis"
  },
  "offset": {
    "representation": "quaternion",
    "q": [1.0, 0.0, 0.0, 0.0],
    "yaw_deg": 0.0,
    "pitch_deg": 0.0,
    "roll_deg": 0.0
  },
  "confidence": "LOW",
  "created_utc": "2026-05-08T00:00:00Z",
  "validation": {
    "repeat_count": 0,
    "max_repeat_error_deg": null,
    "warnings": ["not_validated"]
  }
}
```

The schema above is intentionally a design sketch. Issue #45 should turn it
into the canonical JSON example and storage rule.

Canonical schema documentation and example:

```text
PiFinder_lite/documentation/mobile_mount_profile.md
PiFinder_lite/configs/mobile_mount_profile.example.json
```

## Failure Modes

- Phone is not rigidly mounted.
- The phone is moved after calibration.
- Magnetic interference affects `rotation_vector`.
- The user captures while the telescope is still moving.
- Batch duration is too short or sample count is too low.
- Orientation changes because Android screen orientation changed unexpectedly.
- Reference target/position is wrong.
- Repeat checks disagree beyond the allowed threshold.
- The mount profile is applied to a different phone or different physical mount.

The system should reject or warn on these conditions instead of silently saving
a trusted profile.

## Validation Criteria

A mount profile can only move from `candidate` to `usable` after repeatability
checks pass.

Suggested initial thresholds:

- At least two `mounted_reference` or `repeat_check` captures.
- At least 1.5 seconds of IMU data per batch.
- At least 50 samples per primary sensor batch.
- No large discontinuity or jump in the primary sensor stream.
- `game_rotation_vector` repeat error below a small field-tested threshold.
- Any `rotation_vector` disagreement is reported, not ignored.

The exact repeat-error threshold should be tuned after real mounted tests. Until
then, profiles should remain `candidate` or `diagnostic`.

## Implementation Issues

The current Phase 5 issue set is sufficient:

- #44: labeled IMU calibration batch capture.
- #45: mount profile JSON schema and storage.
- #46: Android calibration workflow UI.
- #47: orientation offset calculation.
- #48: repeatability and drift validation.
- #49: integration decision record.

No extra issues are required yet. Create new issues only if implementation
reveals a missing dependency, for example reference-target selection or a
profile-management screen that is larger than expected.

## Runtime Boundary

The first Phase 5 implementation must stop at diagnostics:

```text
allowed: collect -> analyze -> candidate profile -> repeatability report
blocked: candidate profile -> live integrator input
```

Only #49 should decide whether calibrated mobile IMU data becomes documentation
only, a diagnostic overlay, an optional guidance aid, or a true integrator
input.

## Upstream Change Log Rule

This design document does not change original PiFinder behavior and does not
need an `upstream_change_log.md` entry.

Future Phase 5 work must update
`PiFinder_lite/documentation/upstream_change_log.md` when it changes files under
`python/PiFinder/`, `python/views/`, shared runtime state, startup flags, or any
behavior that could affect classic PiFinder mode.
