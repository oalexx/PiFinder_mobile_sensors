# Mobile Camera Recommendation Profile

This document explains the first mobile camera recommendation profile.

Profile:

```text
PiFinder_lite/configs/mobile_camera_profile.samsung_sm-s948b.example.json
```

## Purpose

The profile captures what the current evidence says about a specific phone
model. It is not a permanent truth and it is not a live runtime config yet.

It is an evidence-backed starting point for:

- Android Camera Lab defaults;
- PiFinder Lite scoring;
- diagnostic solving;
- future per-device recommendation storage.

## Current Device

```text
Samsung SM-S948B
```

Current decision:

```text
PROMISING_TUNE_FIRST
```

## Recommendation

```json
{
  "recommended_camera_id": "2",
  "format": "jpeg",
  "capture_mode": "solve_candidate_burst",
  "recommended_iso_priority": [400, 800],
  "fov_estimate_deg": 74.0,
  "preprocess_order": ["baseline", "background_subtract"],
  "quality_score_required": true,
  "live_solver_ready": false
}
```

## Why

The current evidence says:

- baseline JPEG solves better than aggressive preprocessing;
- ISO400/ISO800 dark-background frames are better first candidates;
- ISO3200 frames with lifted gray backgrounds can produce many false-looking
  points and should not dominate selection;
- score before solve is required;
- diagnostic solve is promising, but live integration is not ready.

## How This Should Evolve

Eventually the app should be able to generate a similar profile for any phone:

```text
Compatibility Tester -> Camera Lab -> Upload -> Score -> Diagnostic Solve -> Profile
```

The final product should use known profiles when available and learn a new one
when a phone model has no existing recommendation.
