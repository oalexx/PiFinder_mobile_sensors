# Phase 2 Camera Lab Analysis

Input: `Test cam`

## Summary

- JPG frames analyzed: 308
- Frames attempted with Tetra3: 12
- Successful solves: 2

## Successful Solves

| block | test | file | mode | matches | fov | solve ms |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_003.jpg` | free_fov | 29 | 16.88 | 3829 |
| 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_004.jpg` | free_fov | 28 | 24.42 | 931 |

## Best Quality Candidates

| rank | block | test | file | ISO | centroids | bright pts | mean | sat % | score | solved |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_005.jpg` | iso3200 | 78 | 213 | 8.2 | 0.00 | 231.2 | no |
| 2 | 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_003.jpg` | iso3200 | 77 | 86 | 8.3 | 0.00 | 231.2 | yes |
| 3 | 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_006.jpg` | iso3200 | 74 | 200 | 8.1 | 0.00 | 231.2 | no |
| 4 | 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_004.jpg` | iso3200 | 64 | 208 | 8.2 | 0.00 | 231.2 | yes |
| 5 | 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_001.jpg` | iso3200 | 80 | 106 | 7.7 | 0.00 | 231.2 | no |
| 6 | 2 | camera_sweep | `pifinder_camera_sweep_20260503_231205_iso3200_001.jpg` | iso3200 | 75 | 155 | 8.0 | 0.00 | 231.2 | no |
| 7 | 2 | camera_sweep | `pifinder_camera_sweep_20260503_231205_iso3200_002.jpg` | iso3200 | 71 | 113 | 7.8 | 0.00 | 231.2 | no |
| 8 | 2 | camera_sweep | `pifinder_camera_sweep_20260503_231205_iso3200_006.jpg` | iso3200 | 75 | 132 | 7.9 | 0.00 | 231.2 | no |
| 9 | 2 | camera_sweep | `pifinder_camera_sweep_20260503_231205_iso3200_005.jpg` | iso3200 | 71 | 131 | 7.9 | 0.00 | 231.2 | no |
| 10 | 2 | camera_sweep | `pifinder_camera_sweep_20260503_231205_iso3200_003.jpg` | iso3200 | 67 | 147 | 7.9 | 0.00 | 231.2 | no |
| 11 | 2 | camera_sweep | `pifinder_camera_sweep_20260503_231205_iso3200_004.jpg` | iso3200 | 67 | 300 | 7.8 | 0.00 | 231.1 | no |
| 12 | 4 | camera_sweep | `pifinder_camera_sweep_20260503_231418_iso3200_002.jpg` | iso3200 | 64 | 79 | 8.2 | 0.00 | 230.2 | no |
| 13 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_003.jpg` | iso400 | 80 | 630 | 2.4 | 0.00 | 209.9 | no |
| 14 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_004.jpg` | iso400 | 80 | 609 | 2.3 | 0.00 | 209.6 | no |
| 15 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_002.jpg` | iso400 | 80 | 578 | 2.4 | 0.00 | 209.5 | no |
| 16 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_005.jpg` | iso400 | 80 | 488 | 2.3 | 0.00 | 209.4 | no |
| 17 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_008.jpg` | iso400 | 80 | 568 | 2.3 | 0.00 | 209.4 | no |
| 18 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_007.jpg` | iso400 | 80 | 527 | 2.3 | 0.00 | 209.2 | no |
| 19 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_006.jpg` | iso400 | 80 | 553 | 2.3 | 0.00 | 209.2 | no |
| 20 | 1 | iso_sweep | `pifinder_iso_sweep_20260503_230541_iso400_001.jpg` | iso400 | 80 | 442 | 2.2 | 0.00 | 208.6 | no |
| 21 | 4 | iso_sweep | `pifinder_iso_sweep_20260503_231403_iso400_002.jpg` | iso400 | 80 | 200 | 1.9 | 0.00 | 207.5 | no |
| 22 | 2 | iso_sweep | `pifinder_iso_sweep_20260503_231151_iso400_003.jpg` | iso400 | 63 | 190 | 1.8 | 0.00 | 207.4 | no |
| 23 | 2 | iso_sweep | `pifinder_iso_sweep_20260503_231151_iso400_001.jpg` | iso400 | 60 | 178 | 1.8 | 0.00 | 207.4 | no |
| 24 | 4 | iso_sweep | `pifinder_iso_sweep_20260503_231403_iso400_001.jpg` | iso400 | 80 | 182 | 2.1 | 0.00 | 207.3 | no |
| 25 | 2 | iso_sweep | `pifinder_iso_sweep_20260503_231151_iso400_002.jpg` | iso400 | 80 | 142 | 1.8 | 0.00 | 207.3 | no |
| 26 | 2 | iso_sweep | `pifinder_iso_sweep_20260503_231151_iso400_005.jpg` | iso400 | 77 | 140 | 1.7 | 0.00 | 207.2 | no |
| 27 | 2 | iso_sweep | `pifinder_iso_sweep_20260503_231151_iso400_004.jpg` | iso400 | 67 | 172 | 1.8 | 0.00 | 207.2 | no |
| 28 | 2 | iso_sweep | `pifinder_iso_sweep_20260503_231151_iso400_007.jpg` | iso400 | 67 | 130 | 1.7 | 0.00 | 207.2 | no |
| 29 | 2 | iso_sweep | `pifinder_iso_sweep_20260503_231151_iso400_008.jpg` | iso400 | 80 | 140 | 1.7 | 0.00 | 207.2 | no |
| 30 | 4 | iso_sweep | `pifinder_iso_sweep_20260503_231403_iso400_007.jpg` | iso400 | 80 | 158 | 2.0 | 0.00 | 207.2 | no |

## Per-Test Counts

| test | frames | best score | best centroids | solves |
| --- | ---: | ---: | ---: | ---: |
| camera_sweep | 60 | 231.2 | 80 | 2 |
| iso_sweep | 128 | 209.9 | 80 | 0 |
| manual_burst | 120 | 126.5 | 18 | 0 |

## Interpretation

- A successful Tetra3 solve is the strongest signal that the phone camera can work as a PiFinder image source.
- If no frames solve, the supporting metrics indicate whether the blocker is likely cloud cover, motion/blur, low star count, or field-of-view/database mismatch.
- These results are from handheld captures under partly cloudy conditions, so a failed solve should be treated as a conservative first pass rather than a final rejection.
