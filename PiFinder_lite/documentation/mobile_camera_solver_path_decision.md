# Mobile Camera Solver Path Decision

Issue: #34 Decide whether mobile camera frames should enter PiFinder solver path.

Date: 2026-05-05.

Decision: **continue the mobile camera path, but keep it diagnostic-only until
Raspberry/upload validation and a clearer repeat capture confirm stability.**

## Short Version

The phone camera path is no longer speculative. The Samsung test data contains
mobile JPEG frames that Tetra3 can solve quickly when the frame is selected
well.

However, the evidence is not yet strong enough to put mobile frames into the
live PiFinder solver/integrator path. The next implementation step should be a
Lite diagnostic workflow:

```text
capture burst -> upload/store -> quality score -> explicit diagnostic solve
```

Only after that works reliably on the Raspberry should we design a live
mobile-camera solving mode.

## Evidence Used

### Phase 2 Offline Analysis

Source:

```text
PiFinder_lite/phase2_camera_analysis/phase2_camera_analysis.md
```

Result:

```text
JPG frames analyzed: 324
Frames attempted with Tetra3: 30
Solve attempts across preprocessing/FOV variants: 75
Successful solves: 22
```

Important finding:

- Baseline JPEG solving was strongest.
- `baseline`: 21 successful solves.
- `background_subtract`: 1 additional successful solve.
- `percentile_stretch`: 0 successful solves.

Interpretation:

Aggressive preprocessing is not the first path. The best current path is to
choose good frames, then try baseline solve first.

### Quality Score

Source:

```text
PiFinder_lite/phase2_camera_analysis/mobile_frame_quality_scores.md
```

Result:

```text
Frames scored: 324
Accepted for diagnostic solve: 48
HIGH: 30
MEDIUM: 18
LOW: 276
```

Important finding:

All accepted frames came from `iso_sweep` in this run. This matches the solve
evidence: dark ISO400/ISO800-style frames are more useful than noisy ISO3200
frames with lifted gray backgrounds.

Interpretation:

The scoring rule should prefer:

- low background mean;
- high dark-pixel percentage;
- enough candidate points, with capped contribution;
- low saturation;
- usable sharpness;
- rejection of lifted/noisy backgrounds even when many points are detected.

### Diagnostic Solves

Source:

```text
PiFinder_lite/phase2_camera_analysis/mobile_frame_diagnostic_solves.md
```

Result:

```text
JPG frames scored: 324
Frames attempted: 12
Unique frames solved: 9
Successful solve rows: 9
```

Important finding:

All successful solves used:

```text
preprocess: baseline
fov mode: metadata_fov_74.0
```

Typical solve times for successful ISO400 frames were around 90-155 ms, with
one slower frame around 239 ms.

Interpretation:

The quality score is useful: top accepted frames are not just visually busy,
they actually solve in diagnostic mode.

## Current Recommended Mobile Camera Path

For the tested Samsung device:

```json
{
  "mobile_camera_path": "continue_diagnostic",
  "recommended_format": "jpeg",
  "recommended_preprocess_first": "baseline",
  "fallback_preprocess": "background_subtract",
  "recommended_fov_mode": "metadata_fov",
  "recommended_iso_priority": [400, 800],
  "avoid_first": ["iso3200_lifted_background", "aggressive_percentile_stretch"],
  "quality_gate_required": true,
  "live_solver_ready": false
}
```

This does not mean ISO3200 is impossible. It means the tested ISO3200 frames
were poor first candidates because the background was lifted/noisy.

## What Should Happen Next

1. Validate #33, #40, and #41 on Raspberry with real Android uploads.
2. Run another clear-sky or fixed-mount capture if possible.
3. Store the selected phone profile:
   - device model;
   - camera ID;
   - capture mode;
   - ISO/exposure preference;
   - FOV estimate;
   - quality score thresholds.
4. Build a guided diagnostic workflow in the app/PiFinder Lite.
5. Only then consider a live mobile-camera solver mode.

## What Should Not Happen Yet

Do not yet:

- feed mobile solves into the integrator;
- update live telescope pointing from mobile frames;
- solve every uploaded frame automatically;
- assume all phones are valid because this Samsung data solved;
- prioritize RAW before JPEG evidence says it helps.

## Product Decision

The mobile camera should remain in the roadmap as a promising PiFinder Lite
sensor. The next milestone is not “replace the original PiFinder camera”; it is
“make the mobile diagnostic workflow reliable and repeatable.”

Decision label:

```text
PROMISING_TUNE_FIRST
```

Meaning:

- Continue mobile-camera development.
- Use quality scoring before solving.
- Use diagnostic solve before live integration.
- Require Raspberry and clearer repeat validation before claiming production
  parity with the original PiFinder camera.
