# Mobile Frame Diagnostic Solve

Issue: #41 Add diagnostic solve path for stored mobile JPEG frames.

Status: implemented as an offline/debug helper.

## Goal

Explicitly solve selected stored or captured mobile JPEG frames for diagnosis,
without feeding the result into PiFinder's live pointing state.

This is the bridge between:

1. uploaded/stored mobile frames;
2. image quality scoring;
3. a future decision about whether mobile camera frames can enter a real solver
   path.

## Command

Solve stored uploads:

```powershell
python PiFinder_lite\diagnostic_solve_mobile_frame.py --input "$HOME\PiFinder_data\mobile\frames"
```

Solve the Phase 2 test set:

```powershell
python PiFinder_lite\diagnostic_solve_mobile_frame.py --input "Test cam" --max-frames 12 --solve-timeout-ms 1000 --preprocess-modes baseline,background_subtract
```

Outputs:

```text
PiFinder_lite/phase2_camera_analysis/mobile_frame_diagnostic_solves.csv
PiFinder_lite/phase2_camera_analysis/mobile_frame_diagnostic_solves.json
PiFinder_lite/phase2_camera_analysis/mobile_frame_diagnostic_solves.md
```

## Flow

1. Score all JPEG frames with `score_mobile_frame.py`.
2. Sort by quality score.
3. Attempt only frames accepted by the score and above the selected grade.
4. Try baseline first.
5. Optionally try `background_subtract` as a rescue mode.
6. Persist solve success/failure, RA, Dec, FOV, roll, matches, solve time,
   preprocessing mode, and quality score.

## Current Validation Result

Command:

```powershell
python PiFinder_lite\diagnostic_solve_mobile_frame.py --input "Test cam" --max-frames 12 --solve-timeout-ms 1000 --preprocess-modes baseline,background_subtract
```

Result:

```text
JPG frames scored: 324
Frames attempted: 12
Unique frames solved: 9
Successful solve rows: 9
```

All successful solves used:

```text
preprocess: baseline
fov mode: metadata_fov_74.0
```

Typical solve time was around 90-155 ms for the successful ISO400 frames, with
one slower frame around 239 ms.

## Interpretation

This confirms the #40 score is useful: the top accepted frames are not merely
visually busy, they are actually solvable by Tetra3 in diagnostic mode.

The current evidence favors:

- JPEG baseline first;
- metadata/FOV-assisted solving when available;
- ISO400/ISO800-style dark frames before noisy ISO3200 candidates;
- scoring before solving.

## Guardrails

This helper must not:

- update PiFinder live pointing;
- feed the integrator;
- change classic PiFinder solver behavior;
- automatically solve every uploaded mobile frame;
- assume mobile solving is production-ready.

It is diagnostic evidence only. A later issue must explicitly decide whether and
how mobile frames can enter a real PiFinder Lite solver workflow.
