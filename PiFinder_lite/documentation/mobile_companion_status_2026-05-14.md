# Mobile Companion Status - 2026-05-14

## Summary

The 2026-05-14 field rehearsal validated the Android-to-Raspberry workflow but
did not satisfy the Phase 2 clear-sky evidence gate.

Validated:

- PiFinder Lite startup with debug camera and no keyboard.
- `/mobile/status`, `/mobile/profile`, `/mobile/gps`, `/mobile/mount_profile`,
  `/mobile/camera_frame`, `/mobile/camera_solve`, and `/mobile/camera_reports`.
- Android Calibration profile/GPS flow.
- Camera Lab full diagnostic upload, candidate ranking, diagnostic solve
  request, persisted report, report history, and copied summary.
- AI Image Preprocessing toggle and diagnostic-only report evidence.

Still open:

- Phase 2 clear-sky camera validation.
- #52 mounted real-sky field validation.
- Phase 6 threshold tuning (#57), RAW decision (#58), and runtime-path decision
  (#59).

## Camera Evidence

Observed report history:

- Reports: 11
- Solved: 0
- Rejected: 11
- Best observed score: about `-963`
- Dominant advice: `Background too bright`
- Recommendation: `capture_better_frames`

Interpretation:

- This is a successful workflow rehearsal, not a successful camera validation.
- The diagnostic solve endpoint and report history work.
- AI preprocessing did not break the flow and may slightly improve quality
  score, but the evidence is inconclusive because every frame was rejected
  before solving.
- No mobile camera result should affect pointing or integrator state.

## First Clear-Sky Run

Use this when conditions improve:

1. Start PiFinder Lite on the Raspberry.
2. Confirm Android `Test connection`.
3. In Calibration, send GPS and profile.
4. In Camera Lab, choose the save folder.
5. Open `Night checklist` for the visible run steps.
6. Run `Run full diagnostic` with AI Image Preprocessing off.
7. Tap `View reports`, then `Copy summary`.
8. Toggle AI Image Preprocessing on.
9. Run `Run full diagnostic` again without moving the telescope.
10. Tap `Mark repeat run` only for comparable repeat attempts.
11. Repeat at least three times if the sky and mount remain stable.

Required result before changing thresholds or runtime decisions:

- At least one clear-sky report must reach an attempted solve.
- Useful evidence should show whether frames are accepted, solved, or rejected
  for sky/camera reasons rather than workflow or endpoint failures.
- Keep all captures and reports local; do not commit phone images, precise GPS,
  or generated private evidence.

## UI Notes

`Night checklist` is not an execution tool. It is an operator checklist for
collecting comparable camera diagnostics. `Mark repeat run` increments the
repeat counter after a completed diagnostic attempt under the same setup, so the
copied summary can explain how many comparable attempts were made.
