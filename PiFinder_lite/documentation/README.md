# PiFinder Lite Documentation

This folder keeps the longer PiFinder Lite notes, validation records, and
decision documents out of the active tool/runtime folder.

The parent `PiFinder_lite/README.md` is the main entry point. Start there for
the current status, Raspberry launch commands, and active diagnostic tools.

## Setup And Runtime Notes

| Document | Purpose |
| --- | --- |
| `lite_config_profile.md` | Optional Lite config profile and startup flags. |
| `keyboard_none_validation.md` | No-keyboard/headless validation notes. |
| `remote_endpoint_validation.md` | `/remote`, `/image`, `/key_callback` validation. |
| `android_webview_remote.md` | Android WebView remote behavior. |
| `mobile_remote_layout.md` | Mobile-friendly `/remote` layout notes. |
| `skysafari_split_screen_validation.md` | SkySafari split-screen workflow. |

## Mobile Bridge

| Document | Purpose |
| --- | --- |
| `mobile_bridge_api_v0.md` | API contract for `/mobile/*` endpoints. |
| `mobile_camera_frame_upload.md` | Storage-only JPEG upload flow. |
| `phase4_dependency_map.md` | Phase 4 issue dependency order and gates. |
| `upstream_change_log.md` | Changes to original PiFinder and why. |

## Camera Evidence And Decisions

| Document | Purpose |
| --- | --- |
| `phase2_night_sky_validation.md` | Phase 2 night-sky evidence summary. |
| `phase2_day_test_validation.md` | Day Test validation notes. |
| `phase2_camera_id_recommendation.md` | Camera ID recommendation evidence. |
| `solve_candidate_burst.md` | Android burst mode tuned for solving. |
| `mobile_frame_quality_score.md` | Quality score rules and usage. |
| `mobile_frame_diagnostic_solve.md` | Diagnostic solve workflow. |
| `mobile_camera_solver_path_decision.md` | Product/technical decision for solver path. |
| `mobile_camera_profile.md` | Per-device recommendation profile format. |

## Phase 5 Calibration

| Document | Purpose |
| --- | --- |
| `phase5_mobile_telescope_calibration_design.md` | Mobile-to-telescope calibration design and runtime boundaries. |
| `mobile_mount_profile.md` | Mount profile schema, storage path, lifecycle, and safety flags. |
| `mobile_mount_offset_tool.md` | Offline tool for computing a candidate phone-to-tube orientation offset. |
| `mobile_mount_repeatability.md` | Offline repeatability validation for candidate mount profiles. |
| `mobile_imu_integration_decision.md` | Decision record for the safe next mobile IMU integration level. |
| `phase5_field_validation_52.md` | Guided day/poor-night and clear-night protocol for #52. |
