# Android Solve Candidate Burst

Issue: [#39 Android Camera Lab: Add Solve Candidate Burst mode](https://github.com/oalexx/PiFinder_mobile_sensors/issues/39)

## Goal

Add a Camera Lab mode that captures JPEG frames specifically intended for
offline plate-solving analysis.

This mode does not upload frames, run a solver on Android, or feed PiFinder's
live solver/integrator. It only produces a clearly named capture folder with
rich metadata.

## Android Behavior

Camera Lab now includes:

```text
Solve Candidate Burst
```

The mode runs:

- test name: `solve_candidate_burst`
- output folder prefix: `pifinder_solve_candidate_burst_<timestamp>`
- format: JPEG
- frame count: 30
- requested ISO: 3200, clamped to the selected camera range
- exposure: maximum available Camera2 exposure for the selected camera
- focus: manual infinity, `0.0` diopters
- JPEG quality: 95

For Samsung `SM-S948B`, the app prefers rear `cameraId=2`, based on the
successful Phase 2 solves documented in
`PiFinder_lite/phase2_camera_id_recommendation.md`.

If that camera ID is not available or is not rear-facing, the app falls back to
the existing best rear-camera selection.

## Metadata

The existing metadata file is reused and extended with:

```text
test=solve_candidate_burst
cameraSelection=<selection reason>
recommendedSolveDevice=SM-S948B
recommendedSolveCameraId=2
selectedSolveCandidateIso=<actual requested ISO after clamping>
```

Each request still records:

```text
requestFrame=<n> mode=manual exposureNs=<value> iso=<value> focusDiopters=0.0
```

Each completed frame still records the actual Camera2 result values:

```text
completedFrame=<n> requestExposureNs=<value> requestIso=<value> resultExposureNs=<value> resultIso=<value>
```

This preserves enough information for offline ranking, upload experiments, and
future quality scoring.

## Expected Output

Example folder:

```text
pifinder_solve_candidate_burst_20260504_224500/
```

Example files:

```text
pifinder_solve_candidate_burst_20260504_224500_solve_iso3200_001.jpg
pifinder_solve_candidate_burst_20260504_224500_solve_iso3200_002.jpg
...
pifinder_solve_candidate_burst_20260504_224500_metadata.txt
```

## Follow-Up

Use this mode for the next clear-sky or partly-clear test instead of generic
Manual Burst. Then run the offline Phase 2 analyzer against the new folder and
compare solve rate, star candidates, blur, and saturation against the previous
Camera Sweep results.

