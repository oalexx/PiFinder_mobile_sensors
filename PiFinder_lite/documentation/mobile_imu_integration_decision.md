# Mobile IMU Integration Decision

Issue: #49

## Decision

The safest next integration level is:

```text
diagnostic overlay / read-only guidance aid
```

Calibrated mobile IMU data must not feed PiFinder's existing integrator yet.
Phase 5 has enough tooling to collect, label, score, offset, and compare mobile
IMU evidence, but it does not yet prove that a phone remains stable enough over
real observing sessions to participate in live pointing state.

## Options Considered

| Option | Decision | Reason |
| --- | --- | --- |
| Documentation only | Too conservative as the only next step | Useful as fallback, but it does not validate user value in the field. |
| Diagnostic overlay / read-only guidance aid | Chosen next step | Lets users compare calibrated phone orientation against PiFinder/SkySafari without changing pointing state. |
| Optional guidance aid that can drive UI hints | Later | Reasonable after field repeatability passes, but should still avoid integrator coupling first. |
| True integrator input | Rejected for now | Too risky without long-session drift, remount, magnetic, and failure-mode evidence. |

## Evidence Available

Phase 5 now has:

- labeled IMU capture from Android (`diagnostic`, `mounted_reference`,
  `repeat_check`, `stationary`, `slew`);
- a guided Android calibration screen;
- mount profile schema;
- offline offset calculation;
- offline repeatability validation.

This is enough to support a controlled diagnostic overlay. It is not enough to
modify the live PiFinder pointing/integrator state.

## Runtime Boundary

Allowed next:

- load a disabled/candidate/usable mount profile for display;
- show calibrated mobile orientation as a separate diagnostic value;
- compare mobile orientation against PiFinder's solved/integrated position;
- log drift, jumps, confidence, and repeatability without changing telescope
  state;
- keep all controls behind explicit Lite/mobile UI.

Blocked:

- feeding mobile IMU samples into `integrator.py`;
- replacing BNO055 data with Android IMU data;
- changing solver confidence or accepted pointing based on the phone;
- enabling any mobile IMU runtime behavior by default;
- hiding drift/jump warnings from the user.

## Risks

- The phone can move in the clamp after calibration.
- `rotation_vector` can be affected by magnetic contamination.
- `game_rotation_vector` avoids magnetometer issues but can drift over time.
- Android sensor behavior differs by model and OS build.
- A profile can be valid for one orientation and invalid after remounting.
- A read-only overlay could still mislead a user if it looks authoritative.

## Required Guardrails

- Profiles remain `enabled: false` by default.
- `runtime.allow_integrator_feed` remains `false`.
- Diagnostic overlay must show confidence/warnings when available.
- Runtime code must ignore profiles with `status: uncalibrated` or
  `invalidated`.
- Runtime code must reject profiles for a different phone model unless the user
  explicitly overrides in a future workflow.
- Rollback is simple: disable the overlay and continue using classic PiFinder
  camera/solver/integrator behavior.

## Proposed Future Work

1. Add a read-only calibrated IMU overlay/status view.
2. Add a mount profile loader that exposes profile metadata without feeding the
   integrator.
3. Run a real field validation protocol with remount and long-session drift
   checks before considering guidance or integrator work.

## Future Issue Drafts

These follow-up issues stay in Phase 5 because they are the safe continuation
of phone-to-telescope calibration before any later guidance or integrator work.

### Phase 5: Add read-only calibrated mobile IMU overlay (#50)

GitHub: https://github.com/oalexx/PiFinder_mobile_sensors/issues/50

Goal:

Show calibrated mobile IMU orientation as a diagnostic/read-only overlay without
changing PiFinder pointing state.

Acceptance:

- A user can view calibrated mobile IMU diagnostic data when explicitly enabled.
- Classic PiFinder behavior is unchanged by default.
- Profiles with invalid/uncalibrated status are not shown as usable.
- Documentation and `upstream_change_log.md` are updated if original PiFinder
  runtime code changes.

### Phase 5: Add mount profile loader/status endpoint (#51)

GitHub: https://github.com/oalexx/PiFinder_mobile_sensors/issues/51

Goal:

Load mobile mount profile metadata for diagnostics while keeping all runtime
flags disabled by default.

Acceptance:

- Implemented by #51: a profile can be loaded from
  `~/PiFinder_data/mobile/mount_profiles/`.
- Implemented by #51: the loaded profile is exposed through
  `GET /mobile/mount_profile`.
- Profiles for a mismatched phone or invalid state are rejected or clearly
  warned.
- No integrator, solver, GPS, or classic UI behavior changes unless explicitly
  enabled in a later issue.

### Phase 5: Field-validate calibrated mobile IMU overlay (#52)

GitHub: https://github.com/oalexx/PiFinder_mobile_sensors/issues/52

Goal:

Run real mounted observing tests before any guidance or integrator work.

Acceptance:

- Test protocol covers remounting, long-session drift, repeat checks, and
  magnetic/phone-model warnings.
- Results include repeat error and drift metrics without private GPS/capture
  artifacts.
- Decision is updated with whether to stay read-only, progress to optional
  guidance, or reject mobile IMU runtime use.

### Phase 5: Add stationary and repeat-check calibration captures (#53)

GitHub: https://github.com/oalexx/PiFinder_mobile_sensors/issues/53

Goal:

Extend the Android calibration screen beyond the first mounted-reference action
so field validation can collect the complete Phase 5 batch set.

Context:

The initial calibration UI work intentionally used a minimum viable flow to
validate labeled IMU uploads quickly. Field validation needs explicit
`stationary`, `mounted_reference`, and `repeat_check` capture actions so the
operator does not have to rely on generic IMU diagnostics.

Acceptance:

- Implemented by #53: the Calibration screen can send `stationary`,
  `mounted_reference`, and `repeat_check` batches.
- The Raspberry stores the correct label for each uploaded batch.
- The UI reports success/failure clearly for each capture type.
- No integrator or runtime pointing behavior changes.

## Upstream Impact

This decision document makes no original PiFinder runtime change. No
`python/PiFinder/`, `python/views/`, startup flag, shared state, solver, GPS,
IMU, or integrator code is changed by #49.

Future implementation that touches original PiFinder code must update
`PiFinder_lite/documentation/upstream_change_log.md` in the same commit.

## Final State For Phase 5

Phase 5 should close with mobile IMU calibration remaining diagnostic-first:

```text
collect -> label -> compute candidate profile -> validate repeatability
     -> read-only overlay next
     -> integrator input blocked
```
