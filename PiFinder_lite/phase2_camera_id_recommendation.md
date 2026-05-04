# Phase 2 Camera ID Recommendation

Issue: [#38 Identify recommended camera ID from successful Camera Sweep solves](https://github.com/oalexx/PiFinder_mobile_sensors/issues/38)

## Summary

The successful Phase 2 Camera Sweep solves came from the Samsung `SM-S948B`
rear `cameraId=2` path.

Recommended path for the next mobile-camera work:

- Device: `samsung SM-S948B`
- Test run: `Test cam/4/pifinder_camera_sweep_20260503_231418/`
- Camera ID: `2`
- Facing: `back`
- Focal length: `[2.2]` mm
- Sensor size: `5.712x4.284` mm
- Hardware level: `LIMITED`
- Manual sensor: `true`
- RAW support: `true`
- Logical multi-camera: `false`
- Capture mode: JPEG, ISO 3200, exposure `176094495 ns`

This should be treated as the first recommended Android camera path for
`Solve Candidate Burst` and future upload/storage tests. It is not yet a final
claim that this is the best physical lens under clear sky; it is the only path
that produced real Tetra3 solves in the current data.

## Successful Frames

Both successful solves were from:

```text
Test cam/4/pifinder_camera_sweep_20260503_231418/
```

| File | Camera ID | ISO | Matches | FOV | Solve Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `pifinder_camera_sweep_20260503_231418_iso3200_003.jpg` | 2 | 3200 | 29 | 16.88 | 3829 ms |
| `pifinder_camera_sweep_20260503_231418_iso3200_004.jpg` | 2 | 3200 | 28 | 24.42 | 931 ms |

The two FOV estimates differ, so follow-up analysis should keep testing
multiple FOV hypotheses until the capture metadata/solver path is tightened.

## Successful Run Metadata

From `pifinder_camera_sweep_20260503_231418_metadata.txt`:

```text
deviceManufacturer=samsung
deviceModel=SM-S948B
androidRelease=16
androidApi=36
cameraId=2
cameraFacing=back
cameraCapabilities=BACKWARD_COMPATIBLE, RAW, cap_9, MANUAL_POST_PROCESSING, PRIVATE_REPROCESSING, READ_SENSOR_SETTINGS, MANUAL_SENSOR, cap_6, cap_7, cap_18, cap_19, cap_20
manualSensor=true
raw=true
logicalMultiCamera=false
hardwareLevel=LIMITED
format=JPEG
size=4080x3060
sensorOrientation=90
jpegOrientation=90
minimumFocusDistanceDiopters=20.0
focalLengthsMm=[2.2]
sensorPhysicalSizeMm=5.712x4.284
exposureRangeNs=[83542, 176094495]
isoRange=[15, 3200]
selectedExposureNs=176094495
selectedMaxIso=3200
```

Actual capture results for the solved frames:

```text
requestExposureNs=176094495
requestIso=3200
requestFocusDiopters=0.0
resultExposureNs=176094495
resultIso=3161
resultFocusDiopters=0.0
resultAfState=0
resultAeState=0
resultAwbState=0
```

## Camera Sweep Comparison

| Block | Run | Camera ID | Focal | Sensor | Hardware | Logical | Solves | Best Centroids | Best Score |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `pifinder_camera_sweep_20260503_230553` | 0 | `[6.5]` | `9.792x7.344` | `LEVEL_3` | true | 0 | 15 | 119.1 |
| 1 | `pifinder_camera_sweep_20260503_230555` | 2 | `[2.2]` | `5.712x4.284` | `LIMITED` | false | 0 | 80 | 177.2 |
| 1 | `pifinder_camera_sweep_20260503_230603` | 0 | `[6.5]` | `9.792x7.344` | `LEVEL_3` | true | 0 | 32 | 161.7 |
| 1 | `pifinder_camera_sweep_20260503_230605` | 2 | `[2.2]` | `5.712x4.284` | `LIMITED` | false | 0 | 80 | 156.9 |
| 2 | `pifinder_camera_sweep_20260503_231203` | 0 | `[6.5]` | `9.792x7.344` | `LEVEL_3` | true | 0 | 10 | 106.5 |
| 2 | `pifinder_camera_sweep_20260503_231205` | 2 | `[2.2]` | `5.712x4.284` | `LIMITED` | false | 0 | 75 | 231.2 |
| 3 | `pifinder_camera_sweep_20260503_231302` | 0 | `[6.5]` | `9.792x7.344` | `LEVEL_3` | true | 0 | 9 | 104.1 |
| 3 | `pifinder_camera_sweep_20260503_231304` | 2 | `[2.2]` | `5.712x4.284` | `LIMITED` | false | 0 | 44 | 168.8 |
| 4 | `pifinder_camera_sweep_20260503_231416` | 0 | `[6.5]` | `9.792x7.344` | `LEVEL_3` | true | 0 | 16 | 121.5 |
| 4 | `pifinder_camera_sweep_20260503_231418` | 2 | `[2.2]` | `5.712x4.284` | `LIMITED` | false | 2 | 80 | 231.2 |

The current data favors `cameraId=2`:

- It produced the only two successful solves.
- Its best candidate scores were consistently stronger than `cameraId=0` in
  the useful blocks.
- It reports a shorter focal length and smaller physical sensor, which matches
  a wider camera path and may make the field easier for Tetra3 to solve from
  handheld, cloudy captures.

`cameraId=0` remains useful as the main/logical high-quality camera path, but
it did not solve in this dataset.

## Metadata Gaps

The current metadata is enough to choose `cameraId=2` for the next tests, but
future captures should add:

- physical camera IDs for logical cameras;
- active physical camera ID when Android reports a logical camera;
- lens aperture if available;
- optical/image stabilization mode and state if available;
- capture target name or sky region when the user can provide it;
- estimated horizontal/vertical FOV derived from focal length and sensor size;
- whether the selected camera ID came from automatic recommendation or manual
  user choice.

These fields will make #39 and #40 easier because the app/server can explain
why a frame is accepted, rejected, or solved under a specific FOV assumption.

## Follow-Up

Recommended next implementation:

1. Use `cameraId=2` as the default recommended camera for Samsung `SM-S948B`
   in the first `Solve Candidate Burst` implementation.
2. Keep a manual camera override in Camera Lab so future phones are not forced
   into this Samsung-specific choice.
3. In #37, test preprocessing and FOV hypotheses against the `cameraId=2`
   frames first, then compare with `cameraId=0`.
4. In #39, capture a bounded ISO 3200 JPEG burst using `cameraId=2`, full
   manual exposure, infinity focus, and rich per-frame metadata.

