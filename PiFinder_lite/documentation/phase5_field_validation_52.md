# Phase 5 Field Validation Protocol (#52)

Issue: #52

## Purpose

Validate the calibrated mobile IMU overlay as a mounted-phone diagnostic aid
before any guidance or integrator-adjacent work.

This protocol has two levels:

- **Day / poor-night validation**: proves the physical mount, Android workflow,
  Raspberry tools, drift logging, remount behavior, and report format.
- **Clear-night validation**: repeats the same workflow against a real sky
  reference and is required before the overlay can progress beyond read-only
  diagnostic status.

Passing the day / poor-night level does not make the phone IMU a runtime
pointing input.

## Safety Boundaries

- Do not feed mobile IMU values into `integrator.py`.
- Do not change PiFinder pointing state from a mobile mount profile.
- Keep `/mobile/mount_profile` read-only.
- Treat every generated mount profile as diagnostic evidence until #52 has a
  clear-night result.
- Do not commit raw IMU batches, phone captures, local paths, or precise private
  GPS coordinates.

## Required Setup

Raspberry:

```bash
cd ~/PiFinder_mobile_sensors
source python/.venv/bin/activate
python -m PiFinder.main -fh --camera debug --keyboard none -x
```

Android:

1. Open PiFinder Mobile.
2. Confirm the PiFinder base URL points to the Raspberry.
3. Use `PiFinder Remote` -> `TEST CONNECTION`.
4. Use the Calibration screen for labeled IMU captures.

Physical setup:

- Attach the phone rigidly to the telescope or a telescope-like fixed tube.
- Mark the phone and clamp position so remounts can be repeated.
- Avoid magnetic accessories, power banks, steel tools, and speaker magnets
  near the phone.
- Keep the screen orientation and phone side consistent across captures.

## Day / Poor-Night Validation

This level can be run indoors, during the day, or under clouds. It validates the
workflow and short-term stability only.

1. Start PiFinder Lite and confirm `/mobile/status` is reachable.
2. Mount the phone in the intended clamp.
3. Capture one `stationary` batch with the tube untouched.
4. Capture one `mounted_reference` batch while the tube points at a repeatable
   physical reference, such as a distant roof edge or wall mark.
5. Capture one `repeat_check` batch without changing the mount.
6. Remove and remount the phone using the same marks.
7. Capture a second `mounted_reference` batch.
8. Capture a second `repeat_check` batch.
9. Leave the phone mounted for a drift interval of at least 5 minutes, then
   capture a final `repeat_check` batch.

Useful Raspberry checks:

```bash
python PiFinder_lite/analyze_mobile_imu.py \
  --input "$HOME/PiFinder_data/mobile/imu_latest.json" \
  --json
```

Create candidate profiles from each mounted reference. The reference file must
contain `q_tube_reference` in `[w, x, y, z]` order. For day validation, use a
clearly named manual reference and mark it as non-sky evidence.

```bash
python PiFinder_lite/compute_mobile_mount_offset.py \
  --imu-batch "$HOME/PiFinder_data/mobile/imu_latest.json" \
  --reference "$HOME/PiFinder_data/mobile/reference_target_day.json" \
  --sensor game_rotation_vector \
  --mount-name "day-validation-remount-1" \
  --output "$HOME/PiFinder_data/mobile/mount_profiles/day-remount-1.json"
```

Compare two or more candidate profiles:

```bash
python PiFinder_lite/validate_mobile_mount_repeatability.py \
  --input "$HOME/PiFinder_data/mobile/mount_profiles" \
  --output-dir "$HOME/PiFinder_data/mobile/repeatability" \
  --json
```

Day / poor-night success means:

- Android sends each labeled batch successfully.
- The Raspberry stores and analyzes the latest batch.
- `game_rotation_vector` remains stable enough to be the first candidate
  sensor, unless the report shows warnings.
- Remount repeatability produces a clear `proceed`, `recalibrate`, or `reject`
  recommendation.
- The operator can complete the workflow without editing JSON by hand except for
  the explicit reference file.

Day / poor-night success still leaves the final decision as
`needs_more_data`.

## Clear-Night Validation

This level is required before deciding whether the calibrated overlay can move
toward optional guidance in a future issue.

Repeat the day / poor-night workflow, but replace the physical reference with a
real sky reference:

1. Mount the phone using the marked position.
2. Point the telescope at a known star/object.
3. Confirm the reference with a PiFinder solve, a trusted manual alignment, or a
   clearly documented known target.
4. Capture `stationary`, `mounted_reference`, and `repeat_check`.
5. Slew away and return to the same target.
6. Capture another `repeat_check`.
7. Remount the phone and repeat the target capture.
8. Run offset and repeatability analysis.
9. Record whether the overlay remains stable enough for read-only use.

Clear-night success means:

- Repeat error is low enough to continue testing.
- Drift over the observing interval is acceptable for read-only overlay use.
- Warnings do not indicate magnetic contamination, phone movement, mismatched
  phone model, or invalid profile status.
- The decision can be updated from `needs_more_data` to either
  `read_only_ok`, `reject_for_guidance`, or `candidate_for_future_guidance`.

## Report Template

Copy this template into a local report under
`~/PiFinder_data/mobile/field_validation/` or into a sanitized issue comment.

```markdown
# Phase 5 Field Validation Report (#52)

Date:
Observer:
Phone model:
Android app build:
PiFinder branch/commit:
Raspberry model / OS:

## Session Type

- [ ] Day / poor-night validation
- [ ] Clear-night validation

## Mount

Mount description:
Phone orientation:
Clamp/marking method:
Remount count:
Known magnetic risks:

## Captures

Stationary batches:
Mounted reference batches:
Repeat check batches:
Longest drift interval:
Reference target/source:

## IMU Analysis

Preferred sensor:
Sample count:
Duration:
Mean step deg:
Max step deg:
Drift deg/s:
Warnings:

## Offset / Repeatability

Candidate profile files:
Max repeat error deg:
Median repeat error deg:
Tool recommendation:
Profile status:
Safety flags:

## Decision

Decision:

- [ ] needs_more_data
- [ ] read_only_ok
- [ ] reject_for_guidance
- [ ] candidate_for_future_guidance

Reason:
Next action:

## Privacy Check

- [ ] No raw IMU batches attached.
- [ ] No phone captures attached.
- [ ] No precise private GPS coordinates.
- [ ] No local absolute paths in shared output.
```

## Decision Rules

Use these labels consistently:

| Decision | Meaning |
| --- | --- |
| `needs_more_data` | Workflow ran, but evidence is day-only, cloudy, unstable, incomplete, or not repeatable enough. |
| `read_only_ok` | Clear-night evidence supports a diagnostic overlay only. No integrator feed. |
| `reject_for_guidance` | Drift, remount error, warnings, or mount instability make guidance unsafe. |
| `candidate_for_future_guidance` | Clear-night evidence is strong enough to create a later optional guidance issue, still not integrator input. |

## Completion Criteria For #52

#52 can be considered complete only when:

- the day / poor-night workflow has been run at least once;
- a mounted clear-night session has been run or explicitly documented as still
  pending;
- repeatability and drift metrics are recorded;
- the report uses one of the four decision labels;
- the decision document is updated with the outcome;
- runtime pointing and integrator behavior remain unchanged.
