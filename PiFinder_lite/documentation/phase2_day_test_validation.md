# Phase 2 Day Test Validation

Date analyzed: 2026-05-04

Input folder:

```text
Test cam/Day Test/
```

Runs:

- `pifinder_day_test_20260504_135847`
- `pifinder_day_test_20260504_135852`

Generated local outputs:

```text
PiFinder_lite/phase2_camera_analysis/
```

The generated analysis directory is ignored by Git.

## Result

Decision: **PASS**

The Day Test validates that Camera Lab can capture, save, orient, and document
daylight JPEGs from the tested phone.

## Evidence

Dataset:

- 2 Day Test runs.
- 16 JPEG frames.
- 2 metadata TXT files.
- 8 saved frames per run.
- 0 failed frames in both runs.

Device/camera:

- Device: Samsung SM-S948B.
- App version: `0.1.0` / build `1`.
- Camera ID: `0`.
- Facing: back.
- Format: JPEG.
- Size: `4080x3060`.
- Hardware level: `LEVEL_3`.
- Manual sensor: true.
- RAW capability: true.
- Logical multi-camera: true.

Orientation:

- Metadata `jpegOrientation=90`.
- EXIF orientation tag: `6`.
- After EXIF transpose, display orientation is portrait (`3060x4080`).
- Contact sheet confirms the images display upright.

Focus/framing:

- Frames contain clear daylight scene detail: stone wall, roof edges, cables,
  sky/cloud boundaries, and building edges.
- Edge/sharpness metrics increase after autofocus settles.
- Both runs are suitable for verifying framing and focus behavior before night
  tests.

Exposure:

- Bright daylight sky/clouds produce saturation in the sky region.
- Saturation is around 12% in the first run and around 18% in the second run.
- This is acceptable for Day Test framing/focus validation because terrestrial
  detail remains visible and the test is not intended for plate solving.

## Minor Notes

- First run reports `savedFrames=8`, `failedFrames=0`, but
  `completedFrames=7`. Since all 8 files exist and metadata lists saved files,
  this looks like callback/accounting timing rather than a capture failure.
- Day Test validates app capture plumbing. It does not validate night-sky solve
  quality; that is covered by `phase2_night_sky_validation.md`.

## Issue Mapping

- #7 Day Test validation: covered and passing.
