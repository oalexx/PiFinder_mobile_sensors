# Mobile Mount Offset Tool

Issue: #47

## Purpose

`PiFinder_lite/compute_mobile_mount_offset.py` creates a diagnostic candidate
mount profile from:

- one labeled Android IMU batch, normally `mounted_reference`;
- one known telescope tube reference orientation.

The output follows the `pifinder-mobile-mount-profile-v0` schema and stays
disabled for runtime use. It is evidence for Phase 5, not an integrator input.

## Reference Input

The first implementation expects the known reference orientation as a quaternion
named `q_tube_reference` in `[w, x, y, z]` order:

```json
{
  "type": "manual_target",
  "target_name": "Vega",
  "source": "manual_or_pifinder_solve",
  "q_tube_reference": [1.0, 0.0, 0.0, 0.0]
}
```

Example file:

```text
PiFinder_lite/configs/mobile_mount_reference.example.json
```

This keeps the offset math explicit while Phase 5 is still diagnostic. Later
work can add helpers that derive this quaternion from a solved PiFinder pointing
or a selected reference object.

## Command

```bash
cd ~/PiFinder_mobile_sensors
source python/.venv/bin/activate

python PiFinder_lite/compute_mobile_mount_offset.py \
  --imu-batch "$HOME/PiFinder_data/mobile/imu_latest.json" \
  --reference "$HOME/PiFinder_data/mobile/reference_target.json" \
  --output "$HOME/PiFinder_data/mobile/mount_profiles/candidate.json"
```

## Output

The profile contains:

- `status: candidate` when the batch is stable enough for repeatability tests;
- `status: uncalibrated` plus warnings when input is weak or invalid;
- `offset.q_phone_to_tube` as the primary quaternion offset;
- yaw/pitch/roll degrees only as a human-readable projection;
- runtime flags that keep integrator and guidance use disabled.

Warnings are intentionally conservative. A profile with
`do_not_use_for_runtime_guidance` is expected during Phase 5.
