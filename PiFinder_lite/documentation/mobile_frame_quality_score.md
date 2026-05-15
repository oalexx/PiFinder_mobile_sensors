# Mobile Frame Quality Score

Issue: #40 Add server-side image quality score for mobile JPEG frames.

Status: implemented as an offline/debug helper.

## Goal

Score uploaded or captured mobile JPEG frames before attempting any diagnostic
plate solve. The score exists to avoid spending solver CPU on frames that look
busy because of noise rather than real stars.

This helper does not invoke Tetra3 solving and does not affect PiFinder's
integrator, live pointing state, or classic camera path.

## Command

Score a stored upload folder:

```powershell
python PiFinder_lite\score_mobile_frame.py --input "$HOME\PiFinder_data\mobile\frames"
```

Score the Phase 2 test set:

```powershell
python PiFinder_lite\score_mobile_frame.py --input "Test cam"
```

Outputs are written locally to:

```text
PiFinder_lite/phase2_camera_analysis/
```

The generated analysis directory is ignored by Git because it can contain local
paths and phone-test artifacts.

Use `--json` when a caller needs the structured result on stdout.

## Metrics

The score includes:

- background mean;
- dark pixel percentage;
- 95th/99th percentiles;
- saturation percentage;
- edge sharpness;
- noise proxy;
- bright point count;
- fast connected-component centroid approximation;
- quality score;
- grade: `HIGH`, `MEDIUM`, or `LOW`;
- `accept_for_diagnostic_solve`;
- explanatory reasons and rejection reasons.

## Phase 2 Rule

The first scoring rule is based on #37:

- prefer dark ISO400/ISO800-style frames with low background mean;
- require enough candidate points, but cap their contribution;
- penalize lifted gray/noisy backgrounds;
- hard-reject frames where many points are likely noise on a bright background;
- do not let ISO3200 frames dominate just because they contain many detected
  points.

## Current Phase 2 Result

Run against `Test cam`:

```text
Frames scored: 324
Accepted for diagnostic solve: 48
HIGH: 30
MEDIUM: 18
LOW: 276
```

All accepted frames came from `iso_sweep` in this run. That matches the #37
finding that baseline ISO400/ISO800 candidates were much more useful than
noisy ISO3200 camera sweep frames.

## Guardrails

This helper must remain diagnostic-only until a later issue explicitly wires it
into an endpoint or workflow.

It must not:

- run plate solving;
- update live pointing;
- feed the integrator;
- alter classic PiFinder camera behavior;
- assume mobile camera solving is reliable under all sky conditions.
