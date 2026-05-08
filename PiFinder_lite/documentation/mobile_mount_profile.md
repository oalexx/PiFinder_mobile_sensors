# Mobile Mount Profile

Issue: #45

## Purpose

A mobile mount profile describes how one phone is physically mounted relative to
one telescope optical tube. It is the persistent output of Phase 5 calibration
work.

The profile is diagnostic and inactive by default. Classic PiFinder behavior
must not change unless a future issue explicitly enables a validated profile.

Example profile:

```text
PiFinder_lite/configs/mobile_mount_profile.example.json
```

## Storage

Versioned examples live in the repository:

```text
PiFinder_lite/configs/mobile_mount_profile.example.json
```

Runtime/user profiles should live outside the repository on Raspberry:

```text
~/PiFinder_data/mobile/mount_profiles/
```

PiFinder Lite exposes the latest profile metadata through:

```text
GET /mobile/mount_profile
```

The endpoint is read-only. It summarizes profile status, validation warnings,
offset metadata, runtime flags, and safety state, but it does not activate the
profile or feed the integrator.

Recommended filename:

```text
<phone-model>_<mount-name>_<profile-id>.json
```

Example:

```text
SM-S948B_tube-clamp_20260508T230000Z.json
```

Do not commit user runtime profiles unless they have been sanitized and are
useful as generic examples.

## Status Values

Use one of:

| Status | Meaning |
| --- | --- |
| `uncalibrated` | Placeholder or newly created profile with no offset. |
| `candidate` | Offset exists, but repeatability is not proven. |
| `usable` | Repeatability passed and profile can be considered by later workflows. |
| `invalidated` | Profile was rejected, stale, moved, or no longer matches the mount. |

Even `usable` does not imply integrator access. Runtime use is controlled by
the `runtime` block and the future #49 integration decision.

## Required Top-Level Fields

| Field | Purpose |
| --- | --- |
| `schema` | Must be `pifinder-mobile-mount-profile-v0`. |
| `profile_id` | Stable identifier for this phone/mount calibration. |
| `status` | Calibration lifecycle state. |
| `enabled` | User-facing enable flag; defaults to `false`. |
| `created_utc` / `updated_utc` | Audit timestamps. |
| `device` | Phone/manufacturer/app metadata. |
| `mount` | Physical mount description. |
| `sensor` | Primary/comparison sensor choices and batch limits. |
| `reference` | Known target or pointing used for calibration. |
| `axis_mapping` | Relationship between phone axes and tube axis. |
| `offset` | Phone-to-tube orientation offset. |
| `validation` | Repeatability state, metrics, and warnings. |
| `runtime` | Explicit runtime safety flags. |

## Sensor Policy

Default sensor choices:

```text
primary: game_rotation_vector
comparison: rotation_vector
```

`game_rotation_vector` is preferred first because it avoids magnetometer
dependence. `rotation_vector` is kept for comparison and diagnostics, not as the
default trusted path.

## Runtime Safety

The example profile sets:

```json
{
  "enabled": false,
  "runtime": {
    "allow_integrator_feed": false,
    "allow_guidance_overlay": false,
    "requires_manual_enable": true
  }
}
```

These defaults are intentional. A mount profile must not feed the PiFinder
integrator during Phase 5. The future #49 decision record must choose whether
validated mobile IMU data becomes documentation only, a diagnostic overlay, an
optional guidance aid, or a true integrator input.

## Validation Fields

`validation.state` should use:

- `not_validated`
- `repeatability_pending`
- `passed`
- `failed`

Use warnings instead of silently trusting weak data. Useful warnings include:

- `not_validated`
- `insufficient_samples`
- `batch_too_short`
- `sensor_jump_detected`
- `repeat_error_too_high`
- `magnetic_disagreement`
- `mount_moved_after_calibration`
- `do_not_use_for_runtime_guidance`

## Invalidating A Profile

Set `status` to `invalidated` when:

- The phone was removed and remounted differently.
- The clamp/tube position changed.
- Repeat checks drift beyond the accepted threshold.
- The profile belongs to another phone model.
- The user chooses to recalibrate from scratch.

Keep invalidated profiles as records if useful, but do not load them as active
runtime inputs.

## Upstream Change Log

This schema and example do not change original PiFinder behavior, so no
`upstream_change_log.md` entry is required.

The read-only profile status endpoint is tracked in
`upstream_change_log.md`. Future work must update the upstream change log again
if profile loading changes startup flags, shared runtime state, or classic
PiFinder behavior.
