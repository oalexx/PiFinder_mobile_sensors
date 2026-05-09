# Mobile Camera Recommendation Profile

This document defines the per-phone mobile camera recommendation profile used
by Phase 6 diagnostics.

The profile is an evidence summary, not a runtime config. It must not enable
mobile camera solves as live PiFinder pointing input.

## Generator

Use the Raspberry-side tool after one or more Android `Run Full Diagnostic`
sessions:

```bash
python PiFinder_lite/generate_mobile_camera_profile.py \
  --reports-dir "$HOME/PiFinder_data/mobile/camera_solve_reports" \
  --manufacturer samsung \
  --device-model SM-S948B \
  --output "$HOME/PiFinder_data/mobile/profiles/mobile_camera_profile.SM-S948B.json" \
  --markdown-output "$HOME/PiFinder_data/mobile/profiles/mobile_camera_profile.SM-S948B.md"
```

Generated output under `~/PiFinder_data/mobile/` is local evidence. Do not
commit generated profiles unless they have been sanitized and intentionally
turned into examples.

## Schema V1

```json
{
  "schema": "pifinder-mobile-camera-profile-v1",
  "status": "diagnostic",
  "decision": "PROMISING_TUNE_FIRST",
  "device": {
    "manufacturer": "samsung",
    "model": "SM-S948B",
    "app_build": "debug-local"
  },
  "recommendation": {
    "recommended_camera_id": "2",
    "preferred_capture_mode": "solve_candidate_burst",
    "preferred_format": "jpeg",
    "raw_status": "not_recommended_until_58",
    "confidence": "MEDIUM",
    "runtime_support": "diagnostic_only",
    "quality_score_required": true,
    "diagnostic_solve_required": true
  },
  "evidence": {
    "source": "camera_solve_reports",
    "total_reports": 2,
    "attempted_reports": 2,
    "solved_reports": 1,
    "rejected_reports": 1,
    "failed_reports": 0,
    "best_quality_score": 0.91,
    "clear_sky_evidence": false,
    "status_counts": {
      "rejected": 1,
      "solved": 1
    }
  },
  "caveats": [
    "clear_sky_phase2_required",
    "thresholds_not_tuned_until_57",
    "runtime_decision_blocked_until_59",
    "diagnostic_only_no_integrator_feed"
  ]
}
```

## Confidence Rules

Use confidence conservatively:

| Confidence | Meaning |
| --- | --- |
| `UNKNOWN` | No useful diagnostic reports for this phone. |
| `LOW` | Reports exist, but no diagnostic solves succeeded yet. |
| `MEDIUM` | At least one diagnostic solve succeeded, but Phase 2 clear-sky evidence and #57 tuning are not complete. |
| `HIGH` | Reserved for repeated clear-sky evidence after threshold tuning and runtime decision work. Not expected before #57/#59. |

`HIGH` must not imply runtime support. Runtime support remains
`diagnostic_only` until #59 explicitly changes the product decision.

## Recommendation Rules

The generator prefers solved diagnostic reports when choosing camera ID, capture
mode, and format. If no report solved, it falls back to the most common
available metadata.

Current defaults remain intentionally conservative:

- preferred capture mode: `solve_candidate_burst`;
- preferred format: `jpeg`;
- RAW status: `not_recommended_until_58` when JPEG is the preferred format;
- quality score and diagnostic solve remain required.

## Privacy And Commit Safety

Generated profiles must not include:

- raw frame paths;
- local absolute paths;
- precise GPS coordinates;
- phone captures or generated analysis artifacts.

The committed Samsung example is a schema/example profile, not proof that this
phone is runtime-ready.
