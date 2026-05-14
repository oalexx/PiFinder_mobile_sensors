from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_ACTIVITY = ROOT / "mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java"
MANIFEST = ROOT / "mobile/app/src/main/AndroidManifest.xml"
LAUNCHER_ICON = ROOT / "mobile/app/src/main/res/drawable/ic_launcher.xml"
STRINGS = ROOT / "mobile/app/src/main/res/values/strings.xml"


def test_android_camera_lab_exposes_guided_diagnostic_solve_flow():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makePrimaryButton("Run full diagnostic")' in source
    assert "runFullMobileCameraDiagnostic()" in source
    assert "fullDiagnosticRunning" in source
    assert "formatFullDiagnosticResult" in source
    assert 'makeAdvancedButton("Solve frame")' in source
    assert "requestDiagnosticCameraSolve()" in source
    assert '"/mobile/camera_solve"' in source
    assert "lastUploadedFrameId" in source
    assert '"frame_id", frameId' in source
    assert "formatDiagnosticSolveResult" in source
    assert '"quality_score"' in source
    assert '"solve_ok"' in source
    assert '"json_report"' in source
    assert '"summary"' in source
    assert '"advice"' in source
    assert '"message"' in source
    assert '"recommendation"' in source
    assert '"next_action"' in source
    assert 'updateMobileCameraDiagnosticGuide("full_running")' in source
    assert 'updateMobileCameraDiagnosticGuide("solving")' in source
    assert 'updateMobileCameraDiagnosticGuide("solve_complete")' in source
    assert "cameraFieldTestStatusView" in source
    assert "updateCameraFieldTestStatus(\"idle\"" in source
    assert "updateCameraFieldTestStatus(\"running\"" in source
    assert '"complete"' in source
    assert "updateCameraFieldTestStatus(\"failed\"" in source


def test_android_camera_lab_guided_field_test_is_collapsible():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "private boolean cameraDiagnosticGuideExpanded = false;" in source
    assert "addCameraDiagnosticGuideToggle(cameraScreen)" in source
    assert "cameraDiagnosticGuideView.setVisibility(View.GONE)" in source
    assert "toggleCameraDiagnosticGuide()" in source
    assert "updateCameraDiagnosticGuideToggleLabel()" in source
    assert '"▾ Show Guided Field Test"' in source
    assert '"▴ Hide Guided Field Test"' in source
    assert "cameraDiagnosticGuideToggleButton.setTypeface(Typeface.DEFAULT_BOLD)" in source
    assert "This guide explains what the field test does." in source
    assert '"Field test steps\\n"' in source
    assert '"Last action: " + detail' in source
    assert 'cameraFieldTestStatusView.setText(' in source


def test_android_camera_lab_exposes_ai_image_preprocessing_test_mode():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "KEY_AI_IMAGE_PREPROCESSING_ENABLED" in source
    assert '"ai_image_preprocessing_enabled"' in source
    assert "aiImagePreprocessingEnabled" in source
    assert "loadAiImagePreprocessingEnabled()" in source
    assert "saveAiImagePreprocessingEnabled(boolean enabled)" in source
    assert "makeAiImagePreprocessingToggleButton()" in source
    assert 'makeHeaderButton("AI Image Preprocessing: Off")' in source
    assert "toggleAiImagePreprocessing()" in source
    assert 'addAreaTitle(cameraScreen, "Field test")' in source
    assert 'payload.put("ai_image_preprocessing_enabled", aiImagePreprocessingEnabled)' in source
    assert 'payload.put("preprocess_strategy", aiImagePreprocessingEnabled ? "adaptive" : "classic")' in source
    assert 'payload.put("preprocess_modes", aiImagePreprocessingEnabled ? "auto" : "baseline,background_subtract")' in source
    assert "AI Image Preprocessing" in source
    assert "Adaptive preprocessing before diagnostic solve. Diagnostic-only." in source
    assert '"ai_image_preprocessing"' in source
    assert '"verdict"' in source
    assert '"extra_time_ms"' in source


def test_android_camera_lab_exposes_diagnostic_report_history():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("View reports")' in source
    assert "requestCameraDiagnosticReports()" in source
    assert 'updateCameraFieldTestStatus("running", "Loading reports", "Requesting saved camera reports from PiFinder.")' in source
    assert '"/mobile/camera_reports?limit=20"' in source
    assert "formatCameraReports" in source
    assert "No reports available yet. Run full diagnostic first." in source
    assert "Camera reports endpoint not available" in source
    assert "latestCameraReportSummary" in source
    assert 'latestCameraReportSummary = "Latest full diagnostic\\n" + finalMessage' in source
    assert "latestCameraReportSummary.length() == 0" in source
    assert 'makeSecondaryButton("Copy summary")' in source
    assert "copyCameraReportSummary()" in source
    assert '"session_summary"' in source
    assert '"status_counts"' in source
    assert '"dominant_advice"' in source


def test_android_exposes_mobile_environment_metadata_bridge():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'makeSecondaryButton("Send env")' in source
    assert "sendEnvironmentToPiFinder()" in source
    assert "buildEnvironmentPayloadJson()" in source
    assert "postMobileEnvironment" in source
    assert '"/mobile/environment"' in source
    assert "Sensor.TYPE_LIGHT" in source
    assert "Sensor.TYPE_PRESSURE" in source
    assert '"ambient_light"' in source
    assert '"pressure"' in source
    assert '"battery"' in source
    assert '"network"' in source
    assert '"device_state"' in source
    assert "ConnectivityManager" in source
    assert "BatteryManager" in source


def test_android_camera_lab_exposes_phase2_night_test_wizard():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "phase2NightTestWizardView" in source
    assert 'addAreaTitle(cameraScreen, "Night checklist")' in source
    assert 'makeSecondaryButton("Night wizard")' in source
    assert "showPhase2NightTestWizard()" in source
    assert 'makeSecondaryButton("Copy night plan")' in source
    assert "copyPhase2NightTestPlan()" in source
    assert 'makeSecondaryButton("Mark repeat run")' in source
    assert "markPhase2NightTestRepeat()" in source
    assert 'updateCameraFieldTestStatus("idle", "Repeat run marked", "Run full diagnostic again under the same setup.")' in source
    assert "phase2NightTestRepeatCount" in source
    assert "updatePhase2NightTestWizard" in source
    assert "phase2NightTestPlanText" in source
    assert "Night Test Wizard" in source
    assert "test completed" in source
    assert "reliable camera use" in source
    assert "clear-sky results" in source
    assert "diagnostic-only" in source
    assert "SEND GPS" in source
    assert "Run full diagnostic" in source
    assert "View reports" in source


def test_android_full_diagnostic_ranks_dynamic_burst_candidates():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "SolveCandidateFrame" in source
    assert "SolveCandidateResult" in source
    assert "solveCandidateFrames" in source
    assert "recordSolveCandidateFrame" in source
    assert "candidateUploadLimitForBurst" in source
    assert "selectSolveCandidateFramesForUpload" in source
    assert "scoreSolveCandidateResult" in source
    assert "rankSolveCandidateResults" in source
    assert "formatSolveCandidateRanking" in source
    assert "selected by Raspberry score" in source
    assert "distributed across burst" in source
    assert "Run full diagnostic" in source
    assert "postMobileCameraFrame(" in source
    assert "candidate.filename" in source
    assert "postDiagnosticCameraSolve(baseUrl, frameId)" in source
    assert "Diagnostic solve endpoint not available" in source
    assert '"solve_candidate_selector"' in source
    assert '"ranking_summary"' in source
    assert '"selected_candidate"' in source
    assert "Upload JPEG" in source
    assert "manual debug" in source


def test_android_exposes_persistent_night_vision_theme_toggle():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "KEY_NIGHT_VISION_ENABLED" in source
    assert "KEY_PENDING_SCREEN_AFTER_THEME_TOGGLE" in source
    assert "KEY_PENDING_REMOTE_WEB_URL_AFTER_THEME_TOGGLE" in source
    assert '"night_vision_enabled"' in source
    assert "nightVisionEnabled" in source
    assert "makeNightVisionToggleButton()" in source
    assert 'makeHeaderButton("Night Vision")' in source
    assert "toggleNightVision()" in source
    assert "loadNightVisionEnabled()" in source
    assert "saveNightVisionEnabled(boolean enabled)" in source
    assert "resolveInitialScreen()" in source
    assert ".putString(KEY_PENDING_SCREEN_AFTER_THEME_TOGGLE, currentScreenName)" in source
    assert ".putString(KEY_PENDING_REMOTE_WEB_URL_AFTER_THEME_TOGGLE, currentRemoteWebUrl())" in source
    assert "restoreRemoteWebUrlAfterThemeToggle()" in source
    assert "applyRemoteWebNightVision()" in source
    assert "pifinder-mobile-night-vision-style" in source
    assert "remoteWebView.evaluateJavascript(script, null)" in source
    assert "String initialScreen = resolveInitialScreen()" in source
    assert "showScreen(initialScreen)" in source
    assert 'return "remoteWeb";' in source
    assert "getSharedPreferences(PREFS_NAME, MODE_PRIVATE)" in source
    assert "recreate()" in source
    assert "applySystemBars()" in source
    assert "setStatusBarColor(nightVisionEnabled ? themePanel() : themeBg())" in source
    assert "setNavigationBarColor(nightVisionEnabled ? themePanel() : themeBg())" in source
    assert "SYSTEM_UI_FLAG_LIGHT_STATUS_BAR" in source
    assert "SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR" in source


def test_android_home_routes_setup_and_help_without_global_brand_on_submenus():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert "setupScreen" in source
    assert "helpScreen" in source
    assert 'makeHeroButton("Phone setup"' in source
    assert 'setupNav.setOnClickListener(v -> showScreen("setup"))' in source
    assert 'helpButton.setOnClickListener(v -> showScreen("help"))' in source
    assert 'makeHeroButton("Camera Lab"' in source
    assert 'makeHeroButton("Calibration"' in source
    assert 'makeHeroButton("Diagnostics"' in source
    assert 'addPlainSectionHeader(helpScreen, "Instructions"' in source
    assert "How to use PiFinder Mobile" in source
    assert "GET STARTED" in source
    assert "NORMAL FIELD USE" in source
    assert "PHONE SETUP" in source
    assert "helpTextStyled()" in source
    assert "boldHelpHeading" in source
    assert 'subtitleView.setText("Plate solving connection app")' in source
    assert 'makeHeroButton("PiFinder Remote", "Connect with PiFinder Remote on this phone", true)' in source
    assert "button.setMinHeight(dp(112))" in source
    assert "row.setPadding(0, dp(8), 0, dp(8))" in source
    assert "params.setMargins(0, dp(6), dp(8), dp(10))" in source
    assert "homeActionsRow" in source
    assert 'titleView.setVisibility(home ? View.VISIBLE : View.GONE)' in source
    assert 'subtitleView.setVisibility(home ? View.VISIBLE : View.GONE)' in source
    assert 'homeActionsRow.setVisibility(home ? View.VISIBLE : View.GONE)' in source
    assert 'row.addView(makeNightVisionToggleButton())' in source


def test_android_submenu_navigation_keeps_expected_parent_screens():
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'addBackRow(cameraScreen, "setup")' in source
    assert 'addBackRow(calibrationScreen, "setup")' in source
    assert 'addBackRow(capabilitiesScreen, "setup")' in source
    assert 'addBackRow(historyScreen, "capabilities")' in source
    assert 'showScreen(parentScreenFor(currentScreenName))' in source
    assert 'case "camera":' in source
    assert 'case "calibration":' in source
    assert 'case "capabilities":' in source
    assert 'return "setup";' in source
    assert 'case "history":' in source
    assert 'return "capabilities";' in source
    assert 'case "remote":' in source
    assert 'return "home";' in source


def test_android_launcher_branding_is_pifinder_mobile():
    manifest = MANIFEST.read_text(encoding="utf-8")
    icon = LAUNCHER_ICON.read_text(encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")

    assert 'android:icon="@drawable/ic_launcher"' in manifest
    assert 'android:roundIcon="@drawable/ic_launcher"' in manifest
    assert "<string name=\"app_name\">PiFinder Mobile</string>" in strings
    assert "logoView" not in source
    assert 'android:pathData="M20,54 H88"' in icon
    assert 'android:pathData="M54,20 V88"' in icon
    assert "#FF1F2D" in icon
    assert "M21,78 L42,57 L59,74 L38,95 Z" in icon
