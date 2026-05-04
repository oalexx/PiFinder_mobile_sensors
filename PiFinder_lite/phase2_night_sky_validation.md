# Phase 2 Night-Sky Camera Validation

Date analyzed: 2026-05-04

Input folder:

```text
Test cam/
```

Conditions reported by tester:

- Partly cloudy sky with intermittent clear patches.
- Phone held by hand with both hands.
- Device: Samsung SM-S948B.
- App: `io.pifinder.mobile` `0.1.0`.

## Dataset

The test folder contains four capture blocks:

| Block | Contents observed |
| --- | --- |
| `1` | manual burst, ISO sweep, raw burst, multiple camera sweep runs |
| `2` | manual burst, ISO sweep, raw burst, camera sweep runs |
| `3` | manual burst, ISO sweep, raw burst, camera sweep runs |
| `4` | manual burst, ISO sweep, raw burst, camera sweep runs |

Files:

- 308 JPEG frames.
- 48 RAW files.
- 22 metadata TXT files.

The generated detailed analysis is stored in:

```text
PiFinder_lite/phase2_camera_analysis/phase2_camera_analysis.md
PiFinder_lite/phase2_camera_analysis/phase2_camera_analysis.csv
```

Analysis script:

```text
PiFinder_lite/analyze_phase2_camera.py
```

## Solver Test

The local Tetra3 database was available at:

```text
python/PiFinder/tetra3/tetra3/data/default_database.npz
```

Local environment note:

- SciPy had to be repaired in `.conda-py39` before Tetra3 could import.
- This was a workstation dependency issue, not a PiFinder code change.

Command used:

```powershell
.\python\.conda-py39\python.exe PiFinder_lite\analyze_phase2_camera.py --max-solve 12
```

Result:

```text
Analyzed 308 JPG frames
Attempted solve on 12 candidates
Successful solves: 2
```

Successful frames:

| Block | Test | Frame | Mode | Matches | FOV | Solve time |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `4` | `camera_sweep` | `pifinder_camera_sweep_20260503_231418_iso3200_003.jpg` | free FOV | 29 | 16.88 deg | 3829 ms |
| `4` | `camera_sweep` | `pifinder_camera_sweep_20260503_231418_iso3200_004.jpg` | free FOV | 28 | 24.42 deg | 931 ms |

## Per-Test Outcome

| Test | Frames analyzed | Best centroids | Successful solves | Outcome |
| --- | ---: | ---: | ---: | --- |
| Camera Sweep | 60 | 80 | 2 | Promising. At least one rear camera/crop path produced solvable JPEGs. |
| ISO Sweep | 128 | 80 | 0 | Stars/candidates detected, but no solve among top tested frames. Needs tuning. |
| Manual Burst | 120 | 18 | 0 | Current handheld burst did not produce enough stable solve candidates. |
| RAW Burst | 48 RAW files | Not solved in this pass | 0 | Keep experimental; JPEG already produced solves, so RAW is not first priority. |

## Decision

Decision: **continue mobile camera path, but tune capture before integrating it
as a primary solver input.**

The mobile camera is not proven stable yet, but it is also not a dead end:
real phone JPEGs from the Camera Sweep block solved successfully with Tetra3
despite clouds and handheld capture.

This is enough evidence to continue with:

- mobile JPEG upload/storage;
- server-side frame quality scoring;
- frame selector for bursts;
- follow-up night testing with clearer sky and fixed phone mounting.

It is not enough evidence yet to:

- feed mobile frames directly into the live PiFinder solver/integrator by default;
- prioritize RAW processing over JPEG;
- assume handheld capture is reliable.

## Recommended Follow-Up Tests

1. Repeat `Camera Sweep` on a clear night and identify which camera ID produced
   `pifinder_camera_sweep_20260503_231418`.
2. Repeat `Manual Burst` with the phone fixed on a tripod or telescope body.
3. Add a shorter list of solve attempts to the app/report: top candidate frame,
   estimated star count, solve success, solve time.
4. Keep ISO 3200 as the current best observed JPEG solve candidate for this
   Samsung SM-S948B dataset.
5. Treat RAW as deferred until JPEG upload + solve path is working end to end.

## Issue Mapping

- #7 Day Test: covered separately in `phase2_day_test_validation.md`; passing.
- #8 Manual Burst: tested; no successful solves in this pass; repeat with fixed mount.
- #9 ISO Sweep: tested; many candidates, but no successful solves in top solve set; tune after camera ID is known.
- #10 Camera Sweep: tested; successful solves found in block `4`; strongest evidence so far.
- #11 RAW Burst: data exists; not prioritized because JPEG already solved.
- #12 Phase 2 decision: continue mobile camera, tune capture first.
- #37 Offline preprocessing/frame selector: new follow-up to improve solve rate from existing data.
- #38 Recommended camera ID: new follow-up to identify the Camera Sweep path that solved.
- #39 Solve Candidate Burst: new Android follow-up after camera ID is known.
- #40 Server-side image quality score: new Phase 4 follow-up before diagnostic solve.
- #41 Diagnostic solve stored JPEG: new Phase 4 follow-up, explicit/debug only.

## Status Snapshot

Resolved or covered by current evidence:

- #8 Manual Burst has enough evidence for this pass: captured and analyzed, but no solve.
- #9 ISO Sweep has enough evidence for this pass: captured and analyzed, but no solve.
- #10 Camera Sweep has positive evidence: 2 successful solves.
- #11 RAW Burst has enough evidence for a decision: defer RAW until JPEG path is stronger.
- #12 Phase 2 decision is documented here.

Still pending:

- #7 Day Test is now covered by `phase2_day_test_validation.md`.
- #37, because preprocessing/candidate selection has not been optimized yet.
- #38, because the successful Camera Sweep run still needs exact camera ID analysis.
- #39, because the app does not yet have a dedicated solve-candidate capture mode.
- #40, because quality scoring exists only in offline prototype form.
- #41, because uploaded/stored frames do not yet have a diagnostic solve path.
