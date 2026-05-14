package io.pifinder.mobile;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraExtensionCharacteristics;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureFailure;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.Image;
import android.media.ImageReader;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.Uri;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.DocumentsContract;
import android.text.InputType;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.TextUtils;
import android.text.style.ForegroundColorSpan;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
import android.util.Range;
import android.util.Size;
import android.util.SizeF;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.IOException;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.TimeZone;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public class MainActivity extends Activity implements SensorEventListener, LocationListener {
    private static final int REQUEST_PERMISSIONS = 41;
    private static final int REQUEST_OUTPUT_DIR = 42;
    private static final int BURST_FRAMES = 30;
    private static final int SOLVE_CANDIDATE_FRAMES = 30;
    private static final int SOLVE_CANDIDATE_ISO = 3200;
    private static final String RECOMMENDED_SOLVE_DEVICE = "SM-S948B";
    private static final String RECOMMENDED_SOLVE_CAMERA_ID = "2";
    private static final int SWEEP_FRAMES_PER_ISO = 8;
    private static final int RAW_BURST_FRAMES = 12;
    private static final int DAY_TEST_FRAMES = 8;
    private static final int IMU_BATCH_MAX_SAMPLES = 256;
    private static final int IMU_BATCH_CAPTURE_MS = 2000;
    private static final int COLOR_BG = Color.rgb(3, 5, 10);
    private static final int COLOR_PANEL = Color.rgb(17, 20, 28);
    private static final int COLOR_PANEL_SOFT = Color.rgb(24, 27, 37);
    private static final int COLOR_TEXT = Color.rgb(238, 242, 247);
    private static final int COLOR_MUTED = Color.rgb(127, 136, 153);
    private static final int COLOR_ACCENT = Color.rgb(255, 38, 92);
    private static final int COLOR_ACCENT_DARK = Color.rgb(92, 12, 35);
    private static final int COLOR_PRIMARY = Color.rgb(255, 76, 121);
    private static final int COLOR_PRIMARY_TEXT = Color.rgb(29, 4, 13);
    private static final int COLOR_SECONDARY = Color.rgb(42, 49, 65);
    private static final int COLOR_SECONDARY_STROKE = Color.rgb(75, 86, 108);
    private static final int COLOR_ADVANCED = Color.rgb(13, 16, 24);
    private static final int COLOR_ADVANCED_STROKE = Color.rgb(49, 56, 72);
    private static final int COLOR_PASS = Color.rgb(64, 214, 137);
    private static final int COLOR_WARN = Color.rgb(255, 190, 92);
    private static final int COLOR_FAIL = Color.rgb(255, 74, 107);
    private static final DecimalFormat F3 = new DecimalFormat("0.000");
    private static final String PREFS_NAME = "pifinder_mobile";
    private static final String KEY_CHECK_HISTORY = "check_history";
    private static final String KEY_REMOTE_BASE_URL = "remote_base_url";
    private static final String KEY_NIGHT_VISION_ENABLED = "night_vision_enabled";
    private static final String KEY_PENDING_SCREEN_AFTER_THEME_TOGGLE = "pending_screen_after_theme_toggle";
    private static final String KEY_PENDING_REMOTE_WEB_URL_AFTER_THEME_TOGGLE = "pending_remote_web_url_after_theme_toggle";
    private static final String KEY_AI_IMAGE_PREPROCESSING_ENABLED = "ai_image_preprocessing_enabled";
    private static final int MAX_HISTORY_RECORDS = 20;

    private SensorManager sensorManager;
    private LocationManager locationManager;
    private CameraManager cameraManager;

    private TextView deviceReportView;
    private TextView sensorReportView;
    private TextView cameraReportView;
    private TextView compatibilityView;
    private TextView readinessBadgeView;
    private TextView homeStatusView;
    private TextView capabilityActionView;
    private TextView cameraFolderStatusView;
    private TextView historyView;
    private TextView liveView;
    private TextView captureView;
    private TextView cameraDiagnosticGuideView;
    private TextView cameraFieldTestStatusView;
    private TextView aiImagePreprocessingStatusView;
    private TextView phase2NightTestWizardView;
    private TextView calibrationChecklistView;
    private TextView aiImuDriftSessionView;
    private Button calibrationChecklistToggleButton;
    private Button cameraDiagnosticGuideToggleButton;
    private Button aiImagePreprocessingToggleButton;
    private Button startImuButton;
    private LinearLayout homeActionsRow;
    private LinearLayout homeScreen;
    private LinearLayout setupScreen;
    private LinearLayout helpScreen;
    private LinearLayout capabilitiesScreen;
    private LinearLayout cameraScreen;
    private LinearLayout historyScreen;
    private LinearLayout remoteScreen;
    private LinearLayout calibrationScreen;
    private LinearLayout remoteWebScreen;
    private LinearLayout rootLayout;
    private TextView titleView;
    private TextView subtitleView;
    private Button nightVisionToggleButton;
    private EditText remoteUrlInput;
    private TextView remoteStatusView;
    private TextView calibrationStatusView;
    private EditText calibrationTargetInput;
    private WebView remoteWebView;
    private String latestCheckResult = "";
    private String latestProfileJson = "";
    private String latestHistoryJson = "";
    private String latestCalibrationEvidenceJson = "";
    private String latestAiImuDriftAnalysisJson = "";
    private String latestCameraReportSummary = "";
    private String latestReport = "";
    private String latestReadinessGrade = "NOT RUN";
    private int latestReadinessPercent = -1;
    private boolean compatibilityCheckRun = false;
    private boolean nightVisionEnabled = false;
    private boolean aiImagePreprocessingEnabled = false;
    private boolean calibrationChecklistExpanded = false;
    private boolean cameraDiagnosticGuideExpanded = false;
    private boolean liveImuStarted = false;
    private boolean liveImuSampleReceived = false;
    private boolean liveImuEverSampleReceived = false;
    private Uri outputTreeUri;
    private String currentScreenName = "home";
    private String pendingGpsBaseUrl = "";
    private boolean imuBatchCaptureActive = false;
    private String pendingImuBaseUrl = "";
    private String pendingImuBatchLabel = "diagnostic";
    private String pendingEnvironmentBaseUrl = "";
    private boolean environmentCaptureActive = false;
    private Float latestAmbientLightLux;
    private long latestAmbientLightAtMs = 0L;
    private Float latestPressureHpa;
    private long latestPressureAtMs = 0L;
    private String lastUploadedFrameId = "";
    private boolean fullDiagnosticRunning = false;
    private boolean aiImuDriftSolveRunning = false;
    private String aiImuDriftSolveRole = "";
    private JSONObject aiImuDriftInitialSolveAltAz;
    private float[] aiImuDriftMoveStartOrientation;
    private float[] aiImuDriftMoveEndOrientation;
    private long aiImuDriftMoveStartMs = 0L;
    private int aiImuDriftCycleCounter = 0;
    private final JSONArray aiImuDriftCycles = new JSONArray();
    private float[] latestDeviceOrientationDeg;
    private int phase2NightTestRepeatCount = 0;
    private SolveCandidateFrame selectedSolveCandidateFrame;
    private String latestSolveCandidateRankingSummary = "";

    private final List<Sensor> activeSensors = new ArrayList<>();
    private final List<Sensor> imuBatchSensors = new ArrayList<>();
    private final List<Sensor> environmentSensors = new ArrayList<>();
    private final List<SolveCandidateFrame> solveCandidateFrames = new ArrayList<>();
    private final JSONArray imuBatchSamples = new JSONArray();
    private final StringBuilder liveSensorText = new StringBuilder();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private Location latestLocation;

    private HandlerThread cameraThread;
    private Handler cameraHandler;
    private CameraDevice captureCamera;
    private CameraCaptureSession captureSession;
    private ImageReader captureReader;
    private int pendingFrames;
    private int savedFrames;
    private int failedFrames;
    private int completedFrames;
    private String captureRunPrefix = "";
    private String captureDirDocumentId;
    private String captureTestName = "manual";
    private String activeCaptureCameraId = "";
    private Size activeCaptureSize;
    private int captureFormat = 256;
    private int captureJpegOrientation = 0;
    private int captureFrameCount = BURST_FRAMES;
    private String captureCameraSelection = "default";
    private byte[] lastCapturedJpegBytes;
    private String lastCapturedJpegName = "";
    private String lastCapturedJpegMetadataJson = "";
    private List<CaptureRequest> queuedRequests = new ArrayList<>();
    private final List<String> queuedLabels = new ArrayList<>();
    private final StringBuilder captureMetadata = new StringBuilder();
    private final List<String> cameraSweepIds = new ArrayList<>();
    private int cameraSweepIndex = 0;

    private static class SolveCandidateFrame {
        final int burstIndex;
        final int totalFrames;
        final String filename;
        final String label;
        final byte[] bytes;
        final String selectionReason;

        SolveCandidateFrame(
                int burstIndex,
                int totalFrames,
                String filename,
                String label,
                byte[] bytes,
                String selectionReason
        ) {
            this.burstIndex = burstIndex;
            this.totalFrames = totalFrames;
            this.filename = filename;
            this.label = label;
            this.bytes = bytes;
            this.selectionReason = selectionReason;
        }
    }

    private static class SolveCandidateResult {
        final SolveCandidateFrame candidate;
        final String frameId;
        final String uploadMessage;
        final String solveMessage;
        final boolean uploadOk;
        final boolean solveOk;
        final double qualityScore;
        final String grade;

        SolveCandidateResult(
                SolveCandidateFrame candidate,
                String frameId,
                String uploadMessage,
                String solveMessage,
                boolean uploadOk,
                boolean solveOk,
                double qualityScore,
                String grade
        ) {
            this.candidate = candidate;
            this.frameId = frameId;
            this.uploadMessage = uploadMessage;
            this.solveMessage = solveMessage;
            this.uploadOk = uploadOk;
            this.solveOk = solveOk;
            this.qualityScore = qualityScore;
            this.grade = grade;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        cameraManager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);

        nightVisionEnabled = loadNightVisionEnabled();
        aiImagePreprocessingEnabled = loadAiImagePreprocessingEnabled();
        applySystemBars();
        setContentView(buildUi());
        requestRuntimePermissions();
        refreshReport();
    }

    @Override
    protected void onPause() {
        super.onPause();
        stopImuBatchCapture();
        stopEnvironmentCapture();
        stopLiveSensors();
        stopLocation();
        if (remoteWebView != null) {
            remoteWebView.onPause();
        }
        closeCaptureCamera();
        stopCameraThread();
    }

    @Override
    protected void onResume() {
        super.onResume();
        applySystemBars();
        if (remoteWebView != null) {
            remoteWebView.onResume();
        }
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        resizeRemoteWebView();
        showScreen(currentScreenName);
    }

    @Override
    public void onBackPressed() {
        if (remoteWebScreen != null && remoteWebScreen.getVisibility() == View.VISIBLE) {
            if (remoteWebView != null && remoteWebView.canGoBack()) {
                remoteWebView.goBack();
            } else {
                showScreen("remote");
            }
            return;
        }
        if (!"home".equals(currentScreenName)) {
            showScreen(parentScreenFor(currentScreenName));
            return;
        }
        super.onBackPressed();
    }

    private View buildUi() {
        ScrollView scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);

        LinearLayout root = new LinearLayout(this);
        rootLayout = root;
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(64), dp(18), dp(18));
        root.setBackgroundColor(themeBg());
        scrollView.addView(root);

        titleView = new TextView(this);
        titleView.setText("PiFinder Mobile");
        titleView.setTextSize(25);
        titleView.setTextColor(themeText());
        titleView.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        titleView.setLetterSpacing(0.0f);
        titleView.setGravity(Gravity.CENTER);
        titleView.setPadding(0, dp(4), 0, dp(6));
        root.addView(titleView);

        subtitleView = new TextView(this);
        subtitleView.setText("Plate solving connection app");
        subtitleView.setTextSize(13);
        subtitleView.setTextColor(themeAccent());
        subtitleView.setLetterSpacing(0.0f);
        subtitleView.setGravity(Gravity.CENTER);
        subtitleView.setPadding(0, 0, 0, dp(14));
        root.addView(subtitleView);

        homeActionsRow = buttonRow();
        homeActionsRow.setGravity(Gravity.CENTER);
        root.addView(homeActionsRow);
        Button helpButton = makeHeaderButton("Help");
        helpButton.setOnClickListener(v -> showScreen("help"));
        homeActionsRow.addView(helpButton);
        nightVisionToggleButton = makeNightVisionToggleButton();
        homeActionsRow.addView(nightVisionToggleButton);

        homeScreen = screenContainer();
        root.addView(homeScreen);
        homeStatusView = statusCard();
        homeScreen.addView(homeStatusView);
        Button remoteNav = makeHeroButton("PiFinder Remote", "Connect with PiFinder Remote on this phone", true);
        remoteNav.setOnClickListener(v -> showScreen("remote"));
        homeScreen.addView(remoteNav);
        Button setupNav = makeHeroButton("Phone setup", "Camera, calibration, diagnostics, and checks", false);
        setupNav.setOnClickListener(v -> showScreen("setup"));
        homeScreen.addView(setupNav);

        setupScreen = screenContainer();
        root.addView(setupScreen);
        helpScreen = screenContainer();
        root.addView(helpScreen);
        capabilitiesScreen = screenContainer();
        root.addView(capabilitiesScreen);
        cameraScreen = screenContainer();
        root.addView(cameraScreen);
        historyScreen = screenContainer();
        root.addView(historyScreen);
        remoteScreen = screenContainer();
        root.addView(remoteScreen);
        calibrationScreen = screenContainer();
        root.addView(calibrationScreen);
        remoteWebScreen = screenContainer();
        root.addView(remoteWebScreen);

        addBackRow(setupScreen);
        addPlainSectionHeader(setupScreen, "Phone setup", "Tools for preparing and checking the phone.");
        Button cameraNav = makeHeroButton("Camera Lab", "Capture and review phone camera diagnostics", false);
        cameraNav.setOnClickListener(v -> showScreen("camera"));
        setupScreen.addView(cameraNav);
        Button calibrationNav = makeHeroButton("Calibration", "Calibrate and check the phone mount", false);
        calibrationNav.setOnClickListener(v -> showScreen("calibration"));
        setupScreen.addView(calibrationNav);
        Button capabilitiesNav = makeHeroButton("Diagnostics", "Check phone sensors, GPS, camera, and readiness", false);
        capabilitiesNav.setOnClickListener(v -> showScreen("capabilities"));
        setupScreen.addView(capabilitiesNav);

        addBackRow(helpScreen);
        addPlainSectionHeader(helpScreen, "Instructions", "How to use PiFinder Mobile in the field.");
        TextView helpTextView = statusCard();
        helpTextView.setText(helpTextStyled());
        helpScreen.addView(helpTextView);

        addBackRow(capabilitiesScreen, "setup");
        addSectionHeader(capabilitiesScreen, "01", "Diagnostics", "Sensor, GPS, camera, and readiness checks.");
        capabilityActionView = statusCard();
        capabilitiesScreen.addView(capabilityActionView);
        LinearLayout row1 = buttonRow();
        capabilitiesScreen.addView(row1);
        startImuButton = makeSecondaryButton("Start IMU");
        startImuButton.setOnClickListener(v -> startLiveSensors());
        row1.addView(startImuButton);
        Button stop = makeAdvancedButton("Stop");
        stop.setOnClickListener(v -> {
            stopLiveSensors();
            stopLocation();
        });
        row1.addView(stop);

        LinearLayout row2 = buttonRow();
        capabilitiesScreen.addView(row2);
        Button refresh = makePrimaryButton("Run check");
        refresh.setOnClickListener(v -> {
            compatibilityCheckRun = true;
            refreshReport();
            saveCheckHistoryRecord();
            updateHistoryView();
            updateCapabilityAction("Review the readiness result and copy the report if needed.");
        });
        row2.addView(refresh);
        Button copyCheck = makeSecondaryButton("Copy result");
        copyCheck.setOnClickListener(v -> copyCheckResult());
        row2.addView(copyCheck);

        LinearLayout rowCopy = buttonRow();
        capabilitiesScreen.addView(rowCopy);
        Button copyTech = makeAdvancedButton("Copy tech report");
        copyTech.setOnClickListener(v -> copyTechReport());
        rowCopy.addView(copyTech);
        Button copyProfile = makeAdvancedButton("Copy profile JSON");
        copyProfile.setOnClickListener(v -> copyProfileJson());
        rowCopy.addView(copyProfile);

        LinearLayout rowHistory = buttonRow();
        capabilitiesScreen.addView(rowHistory);
        Button viewHistory = makeSecondaryButton("View history");
        viewHistory.setOnClickListener(v -> {
            updateHistoryView();
            showScreen("history");
        });
        rowHistory.addView(viewHistory);
        Button copyHistory = makeAdvancedButton("Copy history");
        copyHistory.setOnClickListener(v -> copyHistoryJson());
        rowHistory.addView(copyHistory);

        addAreaTitle(capabilitiesScreen, "Readiness");
        readinessBadgeView = readinessBadge();
        capabilitiesScreen.addView(readinessBadgeView);

        addAreaTitle(capabilitiesScreen, "Check details");
        compatibilityView = sectionText();
        capabilitiesScreen.addView(compatibilityView);

        liveView = sectionText();
        liveView.setText("Live sensors stopped.");
        capabilitiesScreen.addView(liveView);

        addSectionHeader(capabilitiesScreen, "02", "Technical report", "Detailed sensor and system data for debugging.");
        deviceReportView = sectionText();
        capabilitiesScreen.addView(deviceReportView);
        sensorReportView = sectionText();
        capabilitiesScreen.addView(sensorReportView);

        addBackRow(historyScreen, "capabilities");
        addPlainSectionHeader(historyScreen, "Recent check history", "Saved locally on this device.");
        historyView = sectionText();
        historyScreen.addView(historyView);

        addBackRow(remoteScreen);
        addPlainSectionHeader(remoteScreen, "PiFinder Remote", "Loads the existing /remote page from your PiFinder.");
        remoteStatusView = statusCard();
        remoteScreen.addView(remoteStatusView);
        remoteUrlInput = makeUrlInput();
        remoteScreen.addView(remoteUrlInput);
        LinearLayout remoteRow = buttonRow();
        remoteScreen.addView(remoteRow);
        Button openRemote = makePrimaryButton("Open remote");
        openRemote.setOnClickListener(v -> openRemoteWebView());
        remoteRow.addView(openRemote);
        Button testConnection = makeSecondaryButton("Test connection");
        testConnection.setOnClickListener(v -> testPiFinderConnection());
        remoteRow.addView(testConnection);
        LinearLayout remoteBridgeRow = buttonRow();
        remoteScreen.addView(remoteBridgeRow);
        Button sendProfile = makeSecondaryButton("Send profile");
        sendProfile.setOnClickListener(v -> sendProfileToPiFinder());
        remoteBridgeRow.addView(sendProfile);
        Button sendGps = makeSecondaryButton("Send GPS");
        sendGps.setOnClickListener(v -> sendGpsToPiFinder());
        remoteBridgeRow.addView(sendGps);
        Button sendEnvironment = makeSecondaryButton("Send env");
        sendEnvironment.setOnClickListener(v -> sendEnvironmentToPiFinder());
        remoteBridgeRow.addView(sendEnvironment);
        LinearLayout remoteImuRow = buttonRow();
        remoteScreen.addView(remoteImuRow);
        Button sendImu = makeAdvancedButton("Send IMU batch");
        sendImu.setOnClickListener(v -> sendImuBatchToPiFinder("diagnostic"));
        remoteImuRow.addView(sendImu);
        Button sendMountReferenceImu = makeAdvancedButton("Mount ref IMU");
        sendMountReferenceImu.setOnClickListener(v -> sendImuBatchToPiFinder("mounted_reference"));
        remoteImuRow.addView(sendMountReferenceImu);

        addBackRow(calibrationScreen, "setup");
        addPlainSectionHeader(calibrationScreen, "Calibration", "Step through phone mount checks.");
        addCalibrationChecklistToggle(calibrationScreen);
        calibrationStatusView = statusCard();
        calibrationScreen.addView(calibrationStatusView);
        calibrationTargetInput = makeTextInput("Reference target or note");
        calibrationScreen.addView(calibrationTargetInput);
        LinearLayout calibrationConnectionRow = buttonRow();
        calibrationScreen.addView(calibrationConnectionRow);
        Button calibrationTestConnection = makePrimaryButton("Test connection");
        calibrationTestConnection.setOnClickListener(v -> testPiFinderConnection());
        calibrationConnectionRow.addView(calibrationTestConnection);
        Button calibrationProfile = makeSecondaryButton("Send profile");
        calibrationProfile.setOnClickListener(v -> sendProfileToPiFinder());
        calibrationConnectionRow.addView(calibrationProfile);
        Button calibrationCheckProfile = makeSecondaryButton("Check profile");
        calibrationCheckProfile.setOnClickListener(v -> checkMobileMountProfile());
        calibrationConnectionRow.addView(calibrationCheckProfile);
        LinearLayout calibrationDataRow = buttonRow();
        calibrationScreen.addView(calibrationDataRow);
        Button calibrationGps = makeSecondaryButton("Send GPS");
        calibrationGps.setOnClickListener(v -> sendGpsToPiFinder());
        calibrationDataRow.addView(calibrationGps);
        Button calibrationStationary = makePrimaryButton("Stationary");
        calibrationStationary.setOnClickListener(v -> sendCalibrationImuBatch("stationary"));
        calibrationDataRow.addView(calibrationStationary);
        LinearLayout calibrationBatchRow = buttonRow();
        calibrationScreen.addView(calibrationBatchRow);
        Button calibrationMountReference = makePrimaryButton("Mount ref");
        calibrationMountReference.setOnClickListener(v -> sendCalibrationImuBatch("mounted_reference"));
        calibrationBatchRow.addView(calibrationMountReference);
        Button calibrationRepeatCheck = makePrimaryButton("Repeat check");
        calibrationRepeatCheck.setOnClickListener(v -> sendCalibrationImuBatch("repeat_check"));
        calibrationBatchRow.addView(calibrationRepeatCheck);
        LinearLayout calibrationEvidenceRow = buttonRow();
        calibrationScreen.addView(calibrationEvidenceRow);
        Button copyCalibrationEvidence = makeSecondaryButton("Copy evidence");
        copyCalibrationEvidence.setOnClickListener(v -> copyCalibrationEvidence());
        calibrationEvidenceRow.addView(copyCalibrationEvidence);
        Button aiImuDrift = makeSecondaryButton("AI IMU drift");
        aiImuDrift.setOnClickListener(v -> showAiImuDriftAnalysisGuide());
        calibrationEvidenceRow.addView(aiImuDrift);
        LinearLayout aiImuDriftRow1 = buttonRow();
        calibrationScreen.addView(aiImuDriftRow1);
        Button startAiSession = makeSecondaryButton("Start AI session");
        startAiSession.setOnClickListener(v -> startAiImuDriftSession());
        aiImuDriftRow1.addView(startAiSession);
        Button initialSolve = makeSecondaryButton("Initial solve");
        initialSolve.setOnClickListener(v -> captureAiImuDriftInitialSolve());
        aiImuDriftRow1.addView(initialSolve);
        LinearLayout aiImuDriftRow2 = buttonRow();
        calibrationScreen.addView(aiImuDriftRow2);
        Button startMove = makeSecondaryButton("Start move");
        startMove.setOnClickListener(v -> startAiImuDriftMove());
        aiImuDriftRow2.addView(startMove);
        Button finishCycle = makeSecondaryButton("Finish cycle");
        finishCycle.setOnClickListener(v -> finishAiImuDriftCycle());
        aiImuDriftRow2.addView(finishCycle);
        LinearLayout aiImuDriftRow3 = buttonRow();
        calibrationScreen.addView(aiImuDriftRow3);
        Button analyzeDrift = makeSecondaryButton("Analyze drift");
        analyzeDrift.setOnClickListener(v -> analyzeAiImuDriftSession());
        aiImuDriftRow3.addView(analyzeDrift);
        aiImuDriftSessionView = sectionText();
        aiImuDriftSessionView.setText("AI IMU Drift Session\nStart session, capture an initial solve, move, finish cycle, then analyze.");
        calibrationScreen.addView(aiImuDriftSessionView);

        addRemoteWebToolbar(remoteWebScreen);
        remoteWebView = makeRemoteWebView();
        remoteWebScreen.addView(remoteWebView);

        addBackRow(cameraScreen, "setup");
        addPlainSectionHeader(cameraScreen, "Camera Lab", "Capture, upload, and review camera diagnostics.");
        cameraFolderStatusView = statusCard();
        cameraScreen.addView(cameraFolderStatusView);

        addAreaTitle(cameraScreen, "Field test");
        addCameraDiagnosticGuideToggle(cameraScreen);
        cameraFieldTestStatusView = statusCard();
        cameraScreen.addView(cameraFieldTestStatusView);
        updateCameraFieldTestStatus("idle", "Ready", "Run full diagnostic when PiFinder is reachable.");

        LinearLayout aiPreprocessingRow = buttonRow();
        cameraScreen.addView(aiPreprocessingRow);
        aiImagePreprocessingToggleButton = makeAiImagePreprocessingToggleButton();
        aiPreprocessingRow.addView(aiImagePreprocessingToggleButton);
        aiImagePreprocessingStatusView = sectionText();
        cameraScreen.addView(aiImagePreprocessingStatusView);
        updateAiImagePreprocessingStatus();

        LinearLayout row3 = buttonRow();
        cameraScreen.addView(row3);
        Button pickFolder = makeSecondaryButton("Save folder");
        pickFolder.setOnClickListener(v -> pickOutputFolder());
        row3.addView(pickFolder);
        Button phase2Wizard = makeSecondaryButton("Night wizard");
        phase2Wizard.setOnClickListener(v -> showPhase2NightTestWizard());
        row3.addView(phase2Wizard);

        LinearLayout fullDiagnosticRow = buttonRow();
        cameraScreen.addView(fullDiagnosticRow);
        Button fullDiagnostic = makePrimaryButton("Run full diagnostic");
        fullDiagnostic.setOnClickListener(v -> runFullMobileCameraDiagnostic());
        fullDiagnosticRow.addView(fullDiagnostic);

        LinearLayout reportRow = buttonRow();
        cameraScreen.addView(reportRow);
        Button viewReports = makeSecondaryButton("View reports");
        viewReports.setOnClickListener(v -> requestCameraDiagnosticReports());
        reportRow.addView(viewReports);
        Button copyReportSummary = makeSecondaryButton("Copy summary");
        copyReportSummary.setOnClickListener(v -> copyCameraReportSummary());
        reportRow.addView(copyReportSummary);
        Button markPhase2Repeat = makeSecondaryButton("Mark repeat run");
        markPhase2Repeat.setOnClickListener(v -> markPhase2NightTestRepeat());
        reportRow.addView(markPhase2Repeat);

        addAreaTitle(cameraScreen, "Night checklist");
        phase2NightTestWizardView = statusCard();
        updatePhase2NightTestWizard("ready");
        cameraScreen.addView(phase2NightTestWizardView);
        LinearLayout phase2WizardRow = buttonRow();
        cameraScreen.addView(phase2WizardRow);
        Button copyPhase2Plan = makeSecondaryButton("Copy night plan");
        copyPhase2Plan.setOnClickListener(v -> copyPhase2NightTestPlan());
        phase2WizardRow.addView(copyPhase2Plan);

        LinearLayout diagnosticToolsRow = buttonRow();
        cameraScreen.addView(diagnosticToolsRow);
        Button copyDiagnosticPlan = makeAdvancedButton("Copy diagnostic plan");
        copyDiagnosticPlan.setOnClickListener(v -> copyMobileCameraDiagnosticPlan());
        diagnosticToolsRow.addView(copyDiagnosticPlan);

        addAreaTitle(cameraScreen, "Advanced captures");
        LinearLayout diagnosticRow = buttonRow();
        cameraScreen.addView(diagnosticRow);
        Button guidedDiagnostic = makeAdvancedButton("Diagnostic burst");
        guidedDiagnostic.setOnClickListener(v -> startMobileCameraDiagnostic());
        diagnosticRow.addView(guidedDiagnostic);
        Button dayTest = makeAdvancedButton("Day test");
        dayTest.setOnClickListener(v -> startCaptureTest("day_test", 256));
        diagnosticRow.addView(dayTest);

        LinearLayout row4 = buttonRow();
        cameraScreen.addView(row4);
        Button manualBurst = makeAdvancedButton("Manual burst");
        manualBurst.setOnClickListener(v -> startCaptureTest("manual_burst", 256));
        row4.addView(manualBurst);
        Button isoSweep = makeAdvancedButton("ISO sweep");
        isoSweep.setOnClickListener(v -> startCaptureTest("iso_sweep", 256));
        row4.addView(isoSweep);

        LinearLayout row5 = buttonRow();
        cameraScreen.addView(row5);
        Button rawBurst = makeAdvancedButton("RAW burst");
        rawBurst.setOnClickListener(v -> startCaptureTest("raw_burst", 32));
        row5.addView(rawBurst);
        Button cameraSweep = makeAdvancedButton("Camera sweep");
        cameraSweep.setOnClickListener(v -> startCaptureTest("camera_sweep", 256));
        row5.addView(cameraSweep);

        LinearLayout row6 = buttonRow();
        cameraScreen.addView(row6);
        Button solveCandidateBurst = makeAdvancedButton("Candidate burst");
        solveCandidateBurst.setOnClickListener(v -> startCaptureTest("solve_candidate_burst", 256));
        row6.addView(solveCandidateBurst);
        Button uploadLastJpeg = makeAdvancedButton("Upload JPEG");
        uploadLastJpeg.setOnClickListener(v -> uploadLastCapturedJpeg());
        row6.addView(uploadLastJpeg);
        Button diagnosticSolve = makeAdvancedButton("Solve frame");
        diagnosticSolve.setOnClickListener(v -> requestDiagnosticCameraSolve());
        row6.addView(diagnosticSolve);

        captureView = sectionText();
        captureView.setText("Capture test: waiting for a save folder.");
        cameraScreen.addView(captureView);

        cameraReportView = sectionText();
        cameraScreen.addView(cameraReportView);

        String initialScreen = resolveInitialScreen();
        showScreen(initialScreen);
        if ("remoteWeb".equals(initialScreen)) {
            restoreRemoteWebUrlAfterThemeToggle();
        }
        updateCapabilityAction("Run check first. Use live IMU only when you need sensor debugging.");
        updateCameraFolderStatus();
        updateHomeStatus();
        updateHistoryView();
        updateRemoteStatus("Enter the PiFinder base URL, test the connection, then open the remote.");
        updateCalibrationStatus(
                "Start with Test connection, then capture Stationary, Mount ref, and Repeat check."
        );

        return scrollView;
    }

    private Button makeButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, 0, dp(8), dp(8));
        button.setLayoutParams(params);
        return button;
    }

    private LinearLayout screenContainer() {
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setVisibility(View.GONE);
        return screen;
    }

    private void showScreen(String screenName) {
        if (homeScreen == null || setupScreen == null || helpScreen == null
                || capabilitiesScreen == null || cameraScreen == null
                || historyScreen == null || remoteScreen == null || calibrationScreen == null
                || remoteWebScreen == null) {
            return;
        }
        currentScreenName = screenName;
        homeScreen.setVisibility("home".equals(screenName) ? View.VISIBLE : View.GONE);
        setupScreen.setVisibility("setup".equals(screenName) ? View.VISIBLE : View.GONE);
        helpScreen.setVisibility("help".equals(screenName) ? View.VISIBLE : View.GONE);
        capabilitiesScreen.setVisibility("capabilities".equals(screenName) ? View.VISIBLE : View.GONE);
        cameraScreen.setVisibility("camera".equals(screenName) ? View.VISIBLE : View.GONE);
        historyScreen.setVisibility("history".equals(screenName) ? View.VISIBLE : View.GONE);
        remoteScreen.setVisibility("remote".equals(screenName) ? View.VISIBLE : View.GONE);
        calibrationScreen.setVisibility("calibration".equals(screenName) ? View.VISIBLE : View.GONE);
        remoteWebScreen.setVisibility("remoteWeb".equals(screenName) ? View.VISIBLE : View.GONE);
        boolean home = "home".equals(screenName);
        boolean fullRemote = "remoteWeb".equals(screenName);
        titleView.setVisibility(home ? View.VISIBLE : View.GONE);
        subtitleView.setVisibility(home ? View.VISIBLE : View.GONE);
        if (homeActionsRow != null) {
            homeActionsRow.setVisibility(home ? View.VISIBLE : View.GONE);
        }
        if (nightVisionToggleButton != null) {
            nightVisionToggleButton.setVisibility(home ? View.VISIBLE : View.GONE);
        }
        if (rootLayout != null) {
            if (fullRemote) {
                rootLayout.setPadding(0, dp(64), 0, 0);
            } else {
                rootLayout.setPadding(dp(18), dp(64), dp(18), dp(18));
            }
        }
        resizeRemoteWebView();
    }

    private String parentScreenFor(String screenName) {
        switch (screenName) {
            case "camera":
            case "calibration":
            case "capabilities":
                return "setup";
            case "history":
                return "capabilities";
            case "remote":
            case "setup":
            case "help":
                return "home";
            default:
                return "home";
        }
    }

    private void addBackRow(LinearLayout root) {
        addBackRow(root, "home");
    }

    private void addBackRow(LinearLayout root, String targetScreen) {
        LinearLayout row = buttonRow();
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(8), 0, dp(8));
        root.addView(row);
        Button back = makeHeaderButton("Back");
        back.setOnClickListener(v -> showScreen(targetScreen));
        row.addView(back);
        TextView spacer = new TextView(this);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, 1, 1);
        row.addView(spacer, params);
        row.addView(makeNightVisionToggleButton());
    }

    private void addCalibrationChecklistToggle(LinearLayout root) {
        calibrationChecklistToggleButton = makeHeaderButton("Phone mount checklist");
        calibrationChecklistToggleButton.setTypeface(Typeface.DEFAULT_BOLD);
        calibrationChecklistToggleButton.setOnClickListener(v -> toggleCalibrationChecklist());
        root.addView(calibrationChecklistToggleButton);

        calibrationChecklistView = statusCard();
        calibrationChecklistView.setText(calibrationChecklistText());
        calibrationChecklistView.setVisibility(View.GONE);
        root.addView(calibrationChecklistView);
        updateCalibrationChecklistToggleLabel();
    }

    private void toggleCalibrationChecklist() {
        calibrationChecklistExpanded = !calibrationChecklistExpanded;
        if (calibrationChecklistView != null) {
            calibrationChecklistView.setVisibility(calibrationChecklistExpanded ? View.VISIBLE : View.GONE);
        }
        updateCalibrationChecklistToggleLabel();
    }

    private void updateCalibrationChecklistToggleLabel() {
        if (calibrationChecklistToggleButton != null) {
            calibrationChecklistToggleButton.setText(
                    calibrationChecklistExpanded ? "▴ Hide Phone Mount Checklist" : "▾ Show Phone Mount Checklist"
            );
        }
    }

    private void addCameraDiagnosticGuideToggle(LinearLayout root) {
        cameraDiagnosticGuideToggleButton = makeHeaderButton("Guided field test");
        cameraDiagnosticGuideToggleButton.setTypeface(Typeface.DEFAULT_BOLD);
        cameraDiagnosticGuideToggleButton.setOnClickListener(v -> toggleCameraDiagnosticGuide());
        root.addView(cameraDiagnosticGuideToggleButton);

        cameraDiagnosticGuideView = statusCard();
        updateMobileCameraDiagnosticGuide("ready");
        cameraDiagnosticGuideView.setVisibility(View.GONE);
        root.addView(cameraDiagnosticGuideView);
        updateCameraDiagnosticGuideToggleLabel();
    }

    private void toggleCameraDiagnosticGuide() {
        cameraDiagnosticGuideExpanded = !cameraDiagnosticGuideExpanded;
        if (cameraDiagnosticGuideView != null) {
            cameraDiagnosticGuideView.setVisibility(cameraDiagnosticGuideExpanded ? View.VISIBLE : View.GONE);
        }
        updateCameraDiagnosticGuideToggleLabel();
    }

    private void updateCameraDiagnosticGuideToggleLabel() {
        if (cameraDiagnosticGuideToggleButton != null) {
            cameraDiagnosticGuideToggleButton.setText(
                    cameraDiagnosticGuideExpanded ? "▴ Hide Guided Field Test" : "▾ Show Guided Field Test"
            );
        }
    }

    private void addRemoteWebToolbar(LinearLayout root) {
        LinearLayout row = buttonRow();
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(12), dp(8), dp(12), dp(8));
        root.addView(row);
        Button back = makeHeaderButton("Back");
        back.setOnClickListener(v -> showScreen("remote"));
        row.addView(back);
        TextView spacer = new TextView(this);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, 1, 1);
        row.addView(spacer, params);
        row.addView(makeNightVisionToggleButton());
    }

    private Button makeHeroButton(String title, String subtitle, boolean primary) {
        Button button = new Button(this);
        String text = title + "\n" + subtitle;
        SpannableString styledText = new SpannableString(text);
        styledText.setSpan(
                new StyleSpan(Typeface.BOLD),
                0,
                title.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        );
        styledText.setSpan(
                new RelativeSizeSpan(1.12f),
                0,
                title.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        );
        styledText.setSpan(
                new StyleSpan(Typeface.NORMAL),
                title.length() + 1,
                text.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        );
        styledText.setSpan(
                new RelativeSizeSpan(0.76f),
                title.length() + 1,
                text.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        );
        styledText.setSpan(
                new ForegroundColorSpan(primary ? themePrimarySupportText() : themeMuted()),
                title.length() + 1,
                text.length(),
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
        );
        button.setText(styledText);
        button.setAllCaps(false);
        button.setTextSize(16);
        button.setTextColor(primary ? themePrimaryText() : themeText());
        button.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL));
        button.setGravity(Gravity.CENTER);
        button.setLetterSpacing(0.0f);
        button.setMinHeight(dp(112));
        button.setPadding(dp(18), dp(18), dp(18), dp(18));
        button.setBackground(primary
                ? roundedRect(themePrimary(), themePrimary(), 1, 28)
                : roundedRect(themePanel(), themeSecondaryStroke(), 1, 18));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(16), 0, 0);
        button.setLayoutParams(params);
        return button;
    }

    private Button makeSmallButton(String label) {
        return makeHeaderButton(label);
    }

    private Button makeHeaderButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(12);
        button.setTextColor(themeMuted());
        button.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        button.setLetterSpacing(0.0f);
        button.setAllCaps(false);
        button.setMinHeight(dp(48));
        button.setMinWidth(dp(88));
        button.setPadding(dp(14), 0, dp(14), 0);
        button.setBackground(roundedRect(themeBg(), themeHairline(), 1, 18));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                dp(48)
        );
        params.setMargins(0, dp(6), dp(8), dp(10));
        button.setLayoutParams(params);
        return button;
    }

    private void addSectionHeader(LinearLayout root, String number, String title, String subtitle) {
        addSectionHeader(root, number, title, subtitle, true);
    }

    private void addPlainSectionHeader(LinearLayout root, String title, String subtitle) {
        addSectionHeader(root, "", title, subtitle, false);
    }

    private void addSectionHeader(
            LinearLayout root,
            String number,
            String title,
            String subtitle,
            boolean numbered
    ) {
        LinearLayout block = new LinearLayout(this);
        block.setOrientation(LinearLayout.VERTICAL);
        block.setPadding(0, dp(18), 0, dp(8));
        root.addView(block);

        LinearLayout titleRow = new LinearLayout(this);
        titleRow.setOrientation(LinearLayout.HORIZONTAL);
        titleRow.setGravity(Gravity.CENTER_VERTICAL);
        block.addView(titleRow);

        int textOffset = 0;
        if (numbered) {
            TextView index = new TextView(this);
            index.setText(number + ".");
            index.setTextSize(13);
            index.setTextColor(themeAccent());
            index.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
            index.setLetterSpacing(0.0f);
            LinearLayout.LayoutParams indexParams = new LinearLayout.LayoutParams(
                    dp(34),
                    LinearLayout.LayoutParams.WRAP_CONTENT
            );
            titleRow.addView(index, indexParams);
            textOffset = dp(34);
        }

        TextView heading = new TextView(this);
        heading.setText(title);
        heading.setTextSize(18);
        heading.setTextColor(themeText());
        heading.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        heading.setLetterSpacing(0.0f);
        titleRow.addView(heading);

        TextView caption = new TextView(this);
        caption.setText(subtitle);
        caption.setTextSize(12);
        caption.setTextColor(themeMuted());
        caption.setLineSpacing(dp(2), 1.0f);
        caption.setPadding(textOffset, dp(4), 0, dp(8));
        block.addView(caption);

        View accent = new View(this);
        accent.setBackgroundColor(themeAccent());
        LinearLayout.LayoutParams accentParams = new LinearLayout.LayoutParams(
                dp(56),
                dp(1)
        );
        accentParams.setMargins(textOffset, 0, 0, 0);
        block.addView(accent, accentParams);
    }

    private void addAreaTitle(LinearLayout root, String title) {
        LinearLayout block = new LinearLayout(this);
        block.setOrientation(LinearLayout.VERTICAL);
        block.setPadding(0, dp(18), 0, dp(4));
        root.addView(block);

        TextView heading = new TextView(this);
        heading.setText(title);
        heading.setTextSize(15);
        heading.setTextColor(themeText());
        heading.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        heading.setLetterSpacing(0.0f);
        heading.setGravity(Gravity.START);
        block.addView(heading);

        View underline = new View(this);
        underline.setBackgroundColor(themeAccent());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                dp(92),
                dp(2)
        );
        params.setMargins(0, dp(7), 0, dp(8));
        block.addView(underline, params);
    }

    private LinearLayout buttonRow() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.START);
        row.setClipToPadding(false);
        row.setPadding(0, dp(8), 0, dp(8));
        return row;
    }

    private Button makeGridButton(String label) {
        return makeSecondaryButton(label);
    }

    private Button makePrimaryButton(String label) {
        return makeActionButton(label, themePrimary(), themePrimary(), themePrimaryText(), 56, 24);
    }

    private Button makeSecondaryButton(String label) {
        return makeActionButton(label, themeSecondary(), themeSecondaryStroke(), themeText(), 52, 18);
    }

    private Button makeAdvancedButton(String label) {
        return makeActionButton(label, themeAdvanced(), themeAdvancedStroke(), themeMuted(), 50, 14);
    }

    private Button makeNightVisionToggleButton() {
        Button button = makeHeaderButton("Night Vision");
        button.setTextColor(nightVisionEnabled ? themePrimaryText() : themeMuted());
        button.setBackground(roundedRect(
                nightVisionEnabled ? themePrimary() : themeAdvanced(),
                nightVisionEnabled ? themePrimary() : themeAdvancedStroke(),
                1,
                18
        ));
        button.setOnClickListener(v -> toggleNightVision());
        return button;
    }

    private Button makeAiImagePreprocessingToggleButton() {
        Button button = makeHeaderButton("AI Image Preprocessing: Off");
        button.setOnClickListener(v -> toggleAiImagePreprocessing());
        return button;
    }

    private void updateAiImagePreprocessingStatus() {
        if (aiImagePreprocessingToggleButton != null) {
            aiImagePreprocessingToggleButton.setText("AI Image Preprocessing: "
                    + (aiImagePreprocessingEnabled ? "On" : "Off"));
            aiImagePreprocessingToggleButton.setTextColor(
                    aiImagePreprocessingEnabled ? themePrimaryText() : themeMuted()
            );
            aiImagePreprocessingToggleButton.setBackground(roundedRect(
                    aiImagePreprocessingEnabled ? themePrimary() : themeAdvanced(),
                    aiImagePreprocessingEnabled ? themePrimary() : themeAdvancedStroke(),
                    1,
                    18
            ));
        }
        if (aiImagePreprocessingStatusView != null) {
            aiImagePreprocessingStatusView.setText(
                    "Adaptive preprocessing before diagnostic solve. Diagnostic-only."
            );
        }
    }

    private Button makeActionButton(
            String label,
            int fill,
            int stroke,
            int textColor,
            int minHeightDp,
            int radiusDp
    ) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(13);
        button.setTextColor(textColor);
        button.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        button.setLetterSpacing(0.0f);
        button.setAllCaps(false);
        button.setSingleLine(false);
        button.setMinHeight(dp(minHeightDp));
        button.setPadding(dp(12), 0, dp(12), 0);
        button.setBackground(roundedRect(fill, stroke, 1, radiusDp));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1
        );
        params.setMargins(0, 0, dp(8), dp(8));
        button.setLayoutParams(params);
        return button;
    }

    private TextView sectionText() {
        TextView textView = new TextView(this);
        textView.setTextSize(13);
        textView.setTextColor(themeText());
        textView.setTypeface(Typeface.MONOSPACE);
        textView.setTextIsSelectable(true);
        textView.setPadding(dp(14), dp(14), dp(14), dp(14));
        textView.setBackground(roundedRect(themePanel(), themeHairline(), 1, 10));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(10), 0, 0);
        textView.setLayoutParams(params);
        return textView;
    }

    private TextView statusCard() {
        TextView textView = new TextView(this);
        textView.setTextSize(14);
        textView.setTextColor(themeText());
        textView.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL));
        textView.setLineSpacing(dp(4), 1.0f);
        textView.setPadding(dp(18), dp(16), dp(18), dp(16));
        textView.setBackground(roundedRect(themePanel(), themeHairline(), 1, 18));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(10), 0, dp(8));
        textView.setLayoutParams(params);
        return textView;
    }

    private EditText makeUrlInput() {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setText(loadRemoteBaseUrl());
        input.setTextColor(themeText());
        input.setHintTextColor(themeMuted());
        input.setHint("http://pifinder.local or http://192.168.8.167:8080");
        input.setTextSize(14);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        input.setSelectAllOnFocus(false);
        input.setPadding(dp(14), 0, dp(14), 0);
        input.setBackground(roundedRect(themePanel(), themeHairline(), 1, 16));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(52)
        );
        params.setMargins(0, dp(10), 0, dp(10));
        input.setLayoutParams(params);
        return input;
    }

    private EditText makeTextInput(String hint) {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setTextColor(themeText());
        input.setHintTextColor(themeMuted());
        input.setHint(hint);
        input.setTextSize(14);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        input.setPadding(dp(14), 0, dp(14), 0);
        input.setBackground(roundedRect(themePanel(), themeHairline(), 1, 16));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(52)
        );
        params.setMargins(0, dp(10), 0, dp(10));
        input.setLayoutParams(params);
        return input;
    }

    @SuppressLint("SetJavaScriptEnabled")
    private WebView makeRemoteWebView() {
        WebView webView = new WebView(this);
        webView.setBackgroundColor(Color.BLACK);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setTextZoom(100);
        webView.setInitialScale(100);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                updateRemoteStatus("Loaded\n" + url);
                applyRemoteWebNightVision();
            }

            @Override
            public void onReceivedError(
                    WebView view,
                    WebResourceRequest request,
                    WebResourceError error
            ) {
                if (request != null && request.isForMainFrame()) {
                    updateRemoteStatus("Connection failed\nCheck PiFinder IP, port, and Wi-Fi.");
                }
            }
        });
        webView.setOnTouchListener((view, event) -> {
            if (event.getAction() == MotionEvent.ACTION_DOWN
                    || event.getAction() == MotionEvent.ACTION_MOVE) {
                view.getParent().requestDisallowInterceptTouchEvent(true);
            }
            if (event.getAction() == MotionEvent.ACTION_UP
                    || event.getAction() == MotionEvent.ACTION_CANCEL) {
                view.getParent().requestDisallowInterceptTouchEvent(false);
            }
            return false;
        });
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                remoteWebViewHeight()
        );
        params.setMargins(0, 0, 0, 0);
        webView.setLayoutParams(params);
        return webView;
    }

    private int remoteWebViewHeight() {
        int screenHeight = getResources().getDisplayMetrics().heightPixels;
        int toolbarAllowance = getResources().getConfiguration().orientation
                == Configuration.ORIENTATION_LANDSCAPE ? dp(60) : dp(72);
        return Math.max(dp(260), screenHeight - toolbarAllowance);
    }

    private void resizeRemoteWebView() {
        if (remoteWebView == null) {
            return;
        }
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                remoteWebViewHeight()
        );
        params.setMargins(0, 0, 0, 0);
        remoteWebView.setLayoutParams(params);
        remoteWebView.requestLayout();
    }

    private void openRemoteWebView() {
        if (remoteUrlInput == null || remoteWebView == null) {
            return;
        }
        String baseUrl = saveRemoteBaseUrlFromInput();
        if (baseUrl.length() == 0) {
            updateRemoteStatus("Connection missing\nEnter a PiFinder base URL.");
            return;
        }
        String remoteUrl = baseUrl + "/remote?embedded=1";
        updateRemoteStatus("Loading\n" + remoteUrl);
        showScreen("remoteWeb");
        remoteWebView.clearCache(true);
        remoteWebView.loadUrl(remoteUrl);
    }

    private void testPiFinderConnection() {
        if (remoteUrlInput == null) {
            return;
        }
        String baseUrl = saveRemoteBaseUrlFromInput();
        if (baseUrl.length() == 0) {
            updateRemoteStatus("Connection missing\nEnter a PiFinder base URL.");
            return;
        }
        updateRemoteStatus("Testing\n" + baseUrl + "/mobile/status");
        new Thread(() -> {
            String message = runPiFinderStatusCheck(baseUrl);
            runOnUiThread(() -> updateRemoteStatus(message));
        }).start();
    }

    private void sendProfileToPiFinder() {
        if (remoteUrlInput == null) {
            return;
        }
        String baseUrl = saveRemoteBaseUrlFromInput();
        if (baseUrl.length() == 0) {
            updateRemoteStatus("Connection missing\nEnter a PiFinder base URL.");
            return;
        }
        if (latestProfileJson == null || latestProfileJson.trim().length() == 0) {
            latestProfileJson = buildProfileJson();
        }
        updateRemoteStatus("Sending profile\n" + baseUrl + "/mobile/profile");
        new Thread(() -> {
            String message = postMobileProfile(baseUrl, latestProfileJson);
            runOnUiThread(() -> updateRemoteStatus(message));
        }).start();
    }

    private void checkMobileMountProfile() {
        if (remoteUrlInput == null) {
            return;
        }
        String baseUrl = saveRemoteBaseUrlFromInput();
        if (baseUrl.length() == 0) {
            updateCalibrationStatus("Connection missing\nEnter a PiFinder base URL.");
            return;
        }
        updateCalibrationStatus("Checking mount profile\n" + baseUrl + "/mobile/mount_profile");
        new Thread(() -> {
            String message = getMobileMountProfile(baseUrl);
            runOnUiThread(() -> updateCalibrationStatus(message));
        }).start();
    }

    private void sendGpsToPiFinder() {
        if (remoteUrlInput == null) {
            return;
        }
        String baseUrl = saveRemoteBaseUrlFromInput();
        if (baseUrl.length() == 0) {
            updateRemoteStatus("Connection missing\nEnter a PiFinder base URL.");
            return;
        }
        if (!hasLocationPermission()) {
            requestRuntimePermissions();
            updateRemoteStatus("GPS permission missing\nGrant location permission, then tap Send GPS again.");
            return;
        }
        Location location = bestAvailableLocation();
        if (location != null) {
            postLocationToPiFinder(baseUrl, location);
            return;
        }
        pendingGpsBaseUrl = baseUrl;
        if (requestSingleLocationForSend()) {
            updateRemoteStatus("Waiting for GPS\nKeep the app open until Android returns one location fix.");
        } else {
            pendingGpsBaseUrl = "";
            updateRemoteStatus("GPS unavailable\nNo enabled Android location provider returned a fix.");
        }
    }

    private void sendEnvironmentToPiFinder() {
        if (remoteUrlInput == null) {
            return;
        }
        String baseUrl = saveRemoteBaseUrlFromInput();
        if (baseUrl.length() == 0) {
            updateRemoteStatus("Connection missing\nEnter a PiFinder base URL.");
            return;
        }
        pendingEnvironmentBaseUrl = baseUrl;
        stopEnvironmentCapture();
        boolean registered = registerEnvironmentSensor(Sensor.TYPE_LIGHT);
        registered = registerEnvironmentSensor(Sensor.TYPE_PRESSURE) || registered;
        environmentCaptureActive = registered;
        if (registered) {
            updateRemoteStatus("Sampling environment\nLight/pressure sensors are optional.");
            mainHandler.postDelayed(() -> finishEnvironmentCapture("sampled"), 700);
        } else {
            finishEnvironmentCapture("no_optional_sensors");
        }
    }

    private boolean registerEnvironmentSensor(int type) {
        if (sensorManager == null) {
            return false;
        }
        Sensor sensor = sensorManager.getDefaultSensor(type);
        if (sensor == null) {
            return false;
        }
        boolean registered = sensorManager.registerListener(
                this,
                sensor,
                SensorManager.SENSOR_DELAY_NORMAL
        );
        if (registered && !environmentSensors.contains(sensor)) {
            environmentSensors.add(sensor);
        }
        return registered;
    }

    private void finishEnvironmentCapture(String reason) {
        String baseUrl = pendingEnvironmentBaseUrl;
        pendingEnvironmentBaseUrl = "";
        stopEnvironmentCapture();
        if (baseUrl == null || baseUrl.length() == 0) {
            return;
        }
        String environmentJson;
        try {
            environmentJson = buildEnvironmentPayloadJson();
        } catch (JSONException e) {
            updateRemoteStatus("Environment send failed\nCould not build environment JSON.");
            return;
        }
        updateRemoteStatus("Sending environment\n" + reason + "\n" + baseUrl + "/mobile/environment");
        new Thread(() -> {
            String message = postMobileEnvironment(baseUrl, environmentJson);
            runOnUiThread(() -> updateRemoteStatus(message));
        }).start();
    }

    private void stopEnvironmentCapture() {
        if (sensorManager != null) {
            for (Sensor sensor : environmentSensors) {
                sensorManager.unregisterListener(this, sensor);
            }
        }
        environmentSensors.clear();
        environmentCaptureActive = false;
    }

    private void sendImuBatchToPiFinder(String batchLabel) {
        if (remoteUrlInput == null) {
            return;
        }
        String baseUrl = saveRemoteBaseUrlFromInput();
        if (baseUrl.length() == 0) {
            updateRemoteStatus("Connection missing\nEnter a PiFinder base URL.");
            return;
        }
        if (sensorManager == null) {
            updateRemoteStatus("IMU unavailable\nAndroid sensor service is not available.");
            return;
        }
        pendingImuBaseUrl = baseUrl;
        pendingImuBatchLabel = batchLabel;
        clearImuBatchSamples();
        stopImuBatchCapture();
        boolean registered = false;
        if (liveImuStarted) {
            registered = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR) != null
                    || sensorManager.getDefaultSensor(Sensor.TYPE_GAME_ROTATION_VECTOR) != null;
        } else {
            registered = registerImuBatchSensor(Sensor.TYPE_ROTATION_VECTOR) || registered;
            registered = registerImuBatchSensor(Sensor.TYPE_GAME_ROTATION_VECTOR) || registered;
        }
        if (!registered) {
            pendingImuBaseUrl = "";
            pendingImuBatchLabel = "diagnostic";
            updateRemoteStatus("IMU unavailable\nNo rotation vector sensors are available.");
            return;
        }
        imuBatchCaptureActive = true;
        if ("mounted_reference".equals(batchLabel)) {
            updateRemoteStatus("Capturing mount reference IMU\nKeep the phone and tube still for two seconds.");
        } else {
            updateRemoteStatus("Capturing IMU\nMove the phone gently for two seconds.");
        }
        mainHandler.postDelayed(() -> finishImuBatchCapture("timeout"), IMU_BATCH_CAPTURE_MS);
    }

    private void sendCalibrationImuBatch(String batchLabel) {
        updateCalibrationEvidenceJson(batchLabel);
        updateCalibrationStatus(calibrationCaptureStatus(batchLabel));
        sendImuBatchToPiFinder(batchLabel);
    }

    private String calibrationCaptureStatus(String batchLabel) {
        if ("stationary".equals(batchLabel)) {
            return "Capturing stationary baseline\nKeep the mounted phone and telescope tube still.";
        }
        if ("repeat_check".equals(batchLabel)) {
            return "Capturing repeat check\nReturn to the same reference and keep the tube still.";
        }
        return "Capturing mounted reference\nKeep the phone and telescope tube still.";
    }

    private String saveRemoteBaseUrlFromInput() {
        String baseUrl = normalizeRemoteBaseUrl(remoteUrlInput.getText().toString());
        if (baseUrl.length() > 0) {
            prefs().edit().putString(KEY_REMOTE_BASE_URL, baseUrl).apply();
            remoteUrlInput.setText(baseUrl);
        }
        return baseUrl;
    }

    private String runPiFinderStatusCheck(String baseUrl) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(baseUrl + "/mobile/status");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(4000);
            connection.setReadTimeout(4000);
            connection.setRequestProperty("Accept", "application/json");
            int status = connection.getResponseCode();
            String body = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                return "Connection failed\nHTTP " + status + "\nCheck PiFinder IP, port, and Wi-Fi.";
            }
            JSONObject json = new JSONObject(body);
            boolean ok = json.optBoolean("ok", false);
            String api = json.optString("api", "unknown");
            String serverTime = json.optString("server_time_utc", "unknown time");
            JSONObject bridge = json.optJSONObject("mobile_bridge");
            String profile = bridge != null
                    ? bridge.optString("profile", "unknown")
                    : "unknown";
            if (!ok) {
                return "Connection failed\n/mobile/status returned ok=false.";
            }
            return "Connection OK\nAPI: " + api
                    + "\nServer: " + serverTime
                    + "\nProfile bridge: " + profile;
        } catch (Exception e) {
            return "Connection failed\n" + shortError(e)
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private String getMobileMountProfile(String baseUrl) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(baseUrl + "/mobile/mount_profile");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(4000);
            connection.setReadTimeout(4000);
            connection.setRequestProperty("Accept", "application/json");
            int status = connection.getResponseCode();
            String body = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                if (status == 404) {
                    return "Mount profile endpoint not available"
                            + "\nUpdate the PiFinder Lite backend or continue without profile overlay.";
                }
                return "Mount profile check failed\nHTTP " + status + "\n" + responseErrorSummary(body);
            }
            JSONObject json = new JSONObject(body);
            if (!json.optBoolean("ok", false)) {
                return "Mount profile check failed\n/mobile/mount_profile returned ok=false.";
            }
            return formatMountProfileOverlay(json);
        } catch (Exception e) {
            return "Mount profile check failed\n" + shortError(e)
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private String formatMountProfileOverlay(JSONObject json) {
        JSONArray warnings = json.optJSONArray("warnings");
        if (!json.optBoolean("profile_available", false)) {
            return "Mount profile overlay\nNo profile available"
                    + "\nWarnings: " + formatJsonStringArray(warnings)
                    + "\nRead-only: true"
                    + "\nIntegrator: blocked";
        }

        JSONObject profile = json.optJSONObject("profile");
        if (profile == null) {
            return "Mount profile overlay\nProfile payload missing"
                    + "\nWarnings: " + formatJsonStringArray(warnings)
                    + "\nRead-only: true"
                    + "\nIntegrator: blocked";
        }

        JSONObject safety = profile.optJSONObject("safety");
        JSONObject runtime = profile.optJSONObject("runtime");
        JSONObject validation = profile.optJSONObject("validation");
        boolean overlayCandidate = safety != null && safety.optBoolean("overlay_candidate", false);
        boolean runtimeUsable = safety != null && safety.optBoolean("runtime_usable", false);
        boolean readOnly = safety == null || safety.optBoolean("read_only", true);
        boolean integratorBlocked = safety == null || safety.optBoolean("integrator_blocked", true);

        StringBuilder builder = new StringBuilder();
        builder.append("Mount profile overlay\n");
        builder.append("Profile: ").append(profile.optString("profile_id", "unknown")).append("\n");
        builder.append("Status: ").append(profile.optString("status", "unknown")).append("\n");
        builder.append("Phone: ").append(profile.optString("device_model", "unknown")).append("\n");
        builder.append("Overlay candidate: ").append(overlayCandidate).append("\n");
        builder.append("Runtime usable: ").append(runtimeUsable).append("\n");
        builder.append("Read-only: ").append(readOnly).append("\n");
        builder.append("Integrator blocked: ").append(integratorBlocked);
        if (validation != null) {
            builder.append("\nValidation: ").append(validation.optString("state", "unknown"));
            if (!validation.isNull("max_repeat_error_deg")) {
                builder.append("\nMax repeat error: ")
                        .append(format(validation.optDouble("max_repeat_error_deg")))
                        .append(" deg");
            }
        }
        if (runtime != null) {
            builder.append("\nGuidance flag: ")
                    .append(runtime.optBoolean("allow_guidance_overlay", false));
        }
        builder.append("\nWarnings: ").append(formatJsonStringArray(warnings));
        return builder.toString();
    }

    private String postMobileProfile(String baseUrl, String profileJson) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(baseUrl + "/mobile/profile");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(4000);
            connection.setReadTimeout(6000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");

            byte[] bodyBytes = profileJson.getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(bodyBytes.length);
            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(bodyBytes);
            }

            int status = connection.getResponseCode();
            String body = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                return "Profile send failed\nHTTP " + status + "\n" + responseErrorSummary(body);
            }
            JSONObject json = new JSONObject(body);
            if (!json.optBoolean("ok", false)) {
                return "Profile send failed\nServer returned ok=false.";
            }
            return "Profile sent\nStored: " + json.optString("stored_as", "unknown")
                    + "\nReceived: " + json.optString("received_utc", "unknown time");
        } catch (Exception e) {
            return "Profile send failed\n" + shortError(e)
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private void postLocationToPiFinder(String baseUrl, Location location) {
        latestLocation = location;
        String gpsJson;
        try {
            gpsJson = buildGpsPayloadJson(location);
        } catch (JSONException e) {
            updateRemoteStatus("GPS send failed\nCould not build GPS JSON.");
            return;
        }
        updateRemoteStatus("Sending GPS\n" + baseUrl + "/mobile/gps");
        new Thread(() -> {
            String message = postMobileGps(baseUrl, gpsJson);
            runOnUiThread(() -> updateRemoteStatus(message));
        }).start();
    }

    private String postMobileGps(String baseUrl, String gpsJson) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(baseUrl + "/mobile/gps");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(4000);
            connection.setReadTimeout(6000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");

            byte[] bodyBytes = gpsJson.getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(bodyBytes.length);
            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(bodyBytes);
            }

            int status = connection.getResponseCode();
            String body = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                return "GPS send failed\nHTTP " + status + "\n" + responseErrorSummary(body);
            }
            JSONObject json = new JSONObject(body);
            if (!json.optBoolean("ok", false)) {
                return "GPS send failed\nServer returned ok=false.";
            }
            return "GPS sent\nStored: " + json.optString("stored_as", "unknown")
                    + "\nReceived: " + json.optString("received_utc", "unknown time");
        } catch (Exception e) {
            return "GPS send failed\n" + shortError(e)
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private String postMobileEnvironment(String baseUrl, String environmentJson) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(baseUrl + "/mobile/environment");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(4000);
            connection.setReadTimeout(6000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");

            byte[] bodyBytes = environmentJson.getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(bodyBytes.length);
            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(bodyBytes);
            }

            int status = connection.getResponseCode();
            String body = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                return "Environment send failed\nHTTP " + status + "\n" + responseErrorSummary(body);
            }
            JSONObject json = new JSONObject(body);
            if (!json.optBoolean("ok", false)) {
                return "Environment send failed\nServer returned ok=false.";
            }
            JSONObject summary = json.optJSONObject("summary");
            return "Environment sent\nStored: " + json.optString("stored_as", "unknown")
                    + "\nReceived: " + json.optString("received_utc", "unknown time")
                    + "\n" + formatEnvironmentSummary(summary);
        } catch (Exception e) {
            return "Environment send failed\n" + shortError(e)
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private String formatEnvironmentSummary(JSONObject summary) {
        if (summary == null) {
            return "Environment: unavailable";
        }
        StringBuilder builder = new StringBuilder();
        builder.append("Light: ");
        if (summary.optBoolean("ambient_light_available", false)) {
            builder.append(format(summary.optDouble("ambient_light_lux", 0.0))).append(" lux");
        } else {
            builder.append("unavailable");
        }
        builder.append("\nPressure: ");
        if (summary.optBoolean("pressure_available", false)) {
            builder.append(format(summary.optDouble("pressure_hpa", 0.0))).append(" hPa");
        } else {
            builder.append("unavailable");
        }
        builder.append("\nBattery: ");
        if (summary.optBoolean("battery_available", false)) {
            builder.append(format(summary.optDouble("battery_percent", 0.0))).append("%");
        } else {
            builder.append("unavailable");
        }
        builder.append("\nNetwork: ").append(summary.optString("network_type", "unknown"));
        return builder.toString();
    }

    private String buildGpsPayloadJson(Location location) throws JSONException {
        JSONObject gps = new JSONObject();
        gps.put("lat", location.getLatitude());
        gps.put("lon", location.getLongitude());
        if (location.hasAltitude()) {
            gps.put("altitude_m", location.getAltitude());
        }
        if (location.hasAccuracy()) {
            gps.put("accuracy_m", location.getAccuracy());
        }
        gps.put("time_utc", utcIso(location.getTime()));
        gps.put("source", "android-gps");
        gps.put("provider", location.getProvider());
        gps.put("phone_time_utc", utcIso(System.currentTimeMillis()));
        return gps.toString();
    }

    private String buildEnvironmentPayloadJson() throws JSONException {
        JSONObject environment = new JSONObject();
        environment.put("schema", "pifinder-mobile-environment-v0");
        environment.put("device_time_utc", utcIso(System.currentTimeMillis()));
        environment.put("app", appJson());
        environment.put("device", deviceJson());
        environment.put("sensors", environmentSensorsJson());
        environment.put("battery", batteryJson());
        environment.put("network", networkJson());
        environment.put("device_state", deviceStateJson());
        environment.put("diagnostic_only", true);
        return environment.toString();
    }

    private JSONObject environmentSensorsJson() throws JSONException {
        JSONObject sensors = new JSONObject();
        sensors.put("ambient_light", environmentSensorJson(
                Sensor.TYPE_LIGHT,
                "lux",
                latestAmbientLightLux,
                latestAmbientLightAtMs
        ));
        sensors.put("pressure", environmentSensorJson(
                Sensor.TYPE_PRESSURE,
                "hpa",
                latestPressureHpa,
                latestPressureAtMs
        ));
        return sensors;
    }

    private JSONObject environmentSensorJson(
            int type,
            String valueName,
            Float latestValue,
            long latestAtMs
    ) throws JSONException {
        JSONObject json = sensorJson(type);
        json.put("sensor_name", json.optString("name", ""));
        if (latestValue != null) {
            json.put(valueName, latestValue);
            json.put("sample_age_ms", Math.max(0, System.currentTimeMillis() - latestAtMs));
        }
        return json;
    }

    private JSONObject batteryJson() throws JSONException {
        JSONObject battery = new JSONObject();
        BatteryManager batteryManager = (BatteryManager) getSystemService(Context.BATTERY_SERVICE);
        battery.put("available", batteryManager != null);
        if (batteryManager != null) {
            int percent = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
            if (percent >= 0) {
                battery.put("percent", percent);
            }
            int chargingStatus = batteryManager.getIntProperty(
                    BatteryManager.BATTERY_PROPERTY_STATUS
            );
            battery.put("charging", chargingStatus == BatteryManager.BATTERY_STATUS_CHARGING
                    || chargingStatus == BatteryManager.BATTERY_STATUS_FULL);
        }
        return battery;
    }

    private JSONObject networkJson() throws JSONException {
        JSONObject network = new JSONObject();
        network.put("available", false);
        network.put("type", "unknown");
        try {
            ConnectivityManager manager = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
            if (manager == null) {
                return network;
            }
            Network activeNetwork = manager.getActiveNetwork();
            NetworkCapabilities capabilities = manager.getNetworkCapabilities(activeNetwork);
            if (capabilities == null) {
                return network;
            }
            network.put("available", true);
            network.put("internet", capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET));
            network.put("validated", capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED));
            if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
                network.put("type", "wifi");
            } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) {
                network.put("type", "cellular");
            } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)) {
                network.put("type", "ethernet");
            } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) {
                network.put("type", "vpn");
            }
        } catch (SecurityException ignored) {
            network.put("available", false);
        }
        return network;
    }

    private JSONObject deviceStateJson() throws JSONException {
        JSONObject state = new JSONObject();
        state.put("screen_orientation", screenOrientationName());
        PowerManager powerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
        if (powerManager != null) {
            state.put("power_save_mode", powerManager.isPowerSaveMode());
            state.put("interactive", powerManager.isInteractive());
        }
        return state;
    }

    private void postImuBatchToPiFinder(String baseUrl, String imuJson, String batchLabel) {
        String sendingMessage = "Sending IMU batch\nLabel: " + batchLabel + "\n" + baseUrl + "/mobile/imu";
        updateRemoteStatus(sendingMessage);
        if (isCalibrationBatchLabel(batchLabel)) {
            updateCalibrationStatus(sendingMessage);
        }
        new Thread(() -> {
            String message = postMobileImu(baseUrl, imuJson);
            runOnUiThread(() -> {
                updateRemoteStatus(message);
                if (isCalibrationBatchLabel(batchLabel)) {
                    updateCalibrationStatus(message);
                }
            });
        }).start();
    }

    private boolean isCalibrationBatchLabel(String batchLabel) {
        return "stationary".equals(batchLabel)
                || "mounted_reference".equals(batchLabel)
                || "repeat_check".equals(batchLabel);
    }

    private String postMobileImu(String baseUrl, String imuJson) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(baseUrl + "/mobile/imu");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(4000);
            connection.setReadTimeout(6000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");

            byte[] bodyBytes = imuJson.getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(bodyBytes.length);
            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(bodyBytes);
            }

            int status = connection.getResponseCode();
            String body = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                return "IMU send failed\nHTTP " + status + "\n" + responseErrorSummary(body);
            }
            JSONObject json = new JSONObject(body);
            if (!json.optBoolean("ok", false)) {
                return "IMU send failed\nServer returned ok=false.";
            }
            return "IMU batch sent\nLabel: " + json.optString("batch_label", "diagnostic")
                    + "\nStored: " + json.optString("stored_as", "unknown")
                    + "\nSamples: " + json.optInt("sample_count", -1)
                    + "\nReceived: " + json.optString("received_utc", "unknown time");
        } catch (Exception e) {
            return "IMU send failed\n" + shortError(e)
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private String buildImuBatchJson(JSONArray samples, String batchLabel) throws JSONException {
        JSONObject batch = new JSONObject();
        batch.put("schema", "pifinder-mobile-imu-batch-v0");
        batch.put("batch_label", batchLabel);
        batch.put("device_time_utc", utcIso(System.currentTimeMillis()));
        batch.put("capture_duration_ms", IMU_BATCH_CAPTURE_MS);
        batch.put("screen_orientation", screenOrientationName());
        batch.put("samples", samples);
        batch.put("app_version", appJson());
        JSONObject device = new JSONObject();
        device.put("manufacturer", android.os.Build.MANUFACTURER);
        device.put("model", android.os.Build.MODEL);
        device.put("brand", android.os.Build.BRAND);
        device.put("device", android.os.Build.DEVICE);
        device.put("android_release", android.os.Build.VERSION.RELEASE);
        device.put("android_api", android.os.Build.VERSION.SDK_INT);
        batch.put("device", device);
        return batch.toString();
    }

    private String screenOrientationName() {
        int orientation = getResources().getConfiguration().orientation;
        if (orientation == Configuration.ORIENTATION_LANDSCAPE) {
            return "landscape";
        }
        if (orientation == Configuration.ORIENTATION_PORTRAIT) {
            return "portrait";
        }
        return "unknown";
    }

    private void uploadLastCapturedJpeg() {
        if (lastCapturedJpegBytes == null || lastCapturedJpegBytes.length == 0) {
            captureView.setText("No JPEG ready to upload.\nRun Solve Candidate Burst or another JPEG capture first.");
            updateMobileCameraDiagnosticGuide("capture_needed");
            return;
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.length() == 0) {
            captureView.setText("PiFinder URL missing.\nSet it in PiFinder Remote first.");
            updateMobileCameraDiagnosticGuide("remote_needed");
            return;
        }
        byte[] frameBytes = Arrays.copyOf(lastCapturedJpegBytes, lastCapturedJpegBytes.length);
        String filename = lastCapturedJpegName;
        String metadataJson = lastCapturedJpegMetadataJson;
        lastUploadedFrameId = "";
        captureView.setText("Uploading last JPEG...\n" + filename + "\n" + baseUrl + "/mobile/camera_frame");
        updateMobileCameraDiagnosticGuide("uploading");
        new Thread(() -> {
            String message = postMobileCameraFrame(baseUrl, filename, frameBytes, metadataJson);
            runOnUiThread(() -> {
                captureView.setText(message);
                if (message.startsWith("Camera frame uploaded")) {
                    updateMobileCameraDiagnosticGuide("uploaded");
                } else {
                    updateMobileCameraDiagnosticGuide("upload_failed");
                }
            });
        }).start();
    }

    private void startMobileCameraDiagnostic() {
        updateMobileCameraDiagnosticGuide("capturing");
        startCaptureTest("solve_candidate_burst", 256);
    }

    private void runFullMobileCameraDiagnostic() {
        if (fullDiagnosticRunning) {
            captureView.setText("Full diagnostic already running.\nWait for the current report.");
            updateCameraFieldTestStatus("running", "Already running", "Wait for the current diagnostic report.");
            return;
        }
        if (outputTreeUri == null) {
            updateCameraFolderStatus();
            captureView.setText("Full diagnostic needs a save folder.\nChoose Save Folder first.");
            updateMobileCameraDiagnosticGuide("capture_needed");
            updateCameraFieldTestStatus("failed", "Save folder needed", "Choose Save folder before running the diagnostic.");
            pickOutputFolder();
            return;
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestRuntimePermissions();
            return;
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.length() == 0) {
            captureView.setText("PiFinder URL missing.\nSet it in PiFinder Remote first.");
            updateMobileCameraDiagnosticGuide("remote_needed");
            updateCameraFieldTestStatus("failed", "PiFinder URL missing", "Set the base URL in PiFinder Remote.");
            return;
        }
        fullDiagnosticRunning = true;
        lastUploadedFrameId = "";
        updateMobileCameraDiagnosticGuide("full_running");
        updateCameraFieldTestStatus("running", "Capturing frames", "Run full diagnostic started.");
        captureView.setText("Full diagnostic running...\n1. Capturing solve-candidate JPEG burst.");
        startCaptureTest("solve_candidate_burst", 256);
    }

    private void continueFullMobileCameraDiagnostic() {
        if (!fullDiagnosticRunning) {
            return;
        }
        List<SolveCandidateFrame> candidates = selectSolveCandidateFramesForUpload();
        if (candidates.isEmpty() && (lastCapturedJpegBytes == null || lastCapturedJpegBytes.length == 0)) {
            fullDiagnosticRunning = false;
            captureView.setText("Full diagnostic failed.\nNo JPEG was captured.");
            updateMobileCameraDiagnosticGuide("capture_needed");
            updateCameraFieldTestStatus("failed", "No frames captured", "Run full diagnostic again after checking camera permission and save folder.");
            return;
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.length() == 0) {
            fullDiagnosticRunning = false;
            captureView.setText("Full diagnostic failed.\nPiFinder URL missing.");
            updateMobileCameraDiagnosticGuide("remote_needed");
            updateCameraFieldTestStatus("failed", "PiFinder URL missing", "Set the base URL in PiFinder Remote.");
            return;
        }
        if (candidates.isEmpty()) {
            candidates.add(new SolveCandidateFrame(
                    1,
                    1,
                    lastCapturedJpegName,
                    "manual_debug",
                    Arrays.copyOf(lastCapturedJpegBytes, lastCapturedJpegBytes.length),
                    "fallback manual debug latest JPEG"
            ));
        }
        captureView.setText("Full diagnostic running...\n2. Uploading "
                + candidates.size() + " distributed candidate(s).");
        updateMobileCameraDiagnosticGuide("uploading");
        updateCameraFieldTestStatus("running", "Uploading candidates", "Sending selected frames to PiFinder.");
        new Thread(() -> {
            List<SolveCandidateResult> results = new ArrayList<>();
            int total = candidates.size();
            for (int i = 0; i < total; i++) {
                SolveCandidateFrame candidate = candidates.get(i);
                int displayIndex = i + 1;
                runOnUiThread(() -> {
                    captureView.setText("Full diagnostic running...\n"
                            + "Candidate " + displayIndex + "/" + total
                            + "\n" + candidate.filename);
                    updateMobileCameraDiagnosticGuide("solving");
                    updateCameraFieldTestStatus("running", "Solving candidate " + displayIndex + "/" + total, candidate.filename);
                });
                String metadataJson = buildCameraFrameMetadataJson(
                        candidate.filename,
                        candidate.bytes.length,
                        candidate,
                        latestSolveCandidateRankingSummary
                );
                String uploadMessage = postMobileCameraFrame(
                        baseUrl,
                        candidate.filename,
                        Arrays.copyOf(candidate.bytes, candidate.bytes.length),
                        metadataJson
                );
                String frameId = lastUploadedFrameId == null ? "" : lastUploadedFrameId.trim();
                String solveMessage = "";
                if (uploadMessage.startsWith("Camera frame uploaded") && frameId.length() > 0) {
                    solveMessage = postDiagnosticCameraSolve(baseUrl, frameId);
                }
                results.add(new SolveCandidateResult(
                        candidate,
                        frameId,
                        uploadMessage,
                        solveMessage,
                        uploadMessage.startsWith("Camera frame uploaded"),
                        solveMessage.contains("Solve OK: true"),
                        parseDiagnosticQualityScore(solveMessage),
                        parseDiagnosticGrade(solveMessage)
                ));
            }
            rankSolveCandidateResults(results);
            SolveCandidateResult selected = results.isEmpty() ? null : results.get(0);
            if (selected != null) {
                selectedSolveCandidateFrame = selected.candidate;
                lastUploadedFrameId = selected.frameId;
                lastCapturedJpegBytes = Arrays.copyOf(selected.candidate.bytes, selected.candidate.bytes.length);
                lastCapturedJpegName = selected.candidate.filename;
                lastCapturedJpegMetadataJson = buildCameraFrameMetadataJson(
                        selected.candidate.filename,
                        selected.candidate.bytes.length,
                        selected.candidate,
                        formatSolveCandidateRanking(results)
                );
            }
            String finalMessage = formatFullDiagnosticResult(results);
            boolean success = selected != null && selected.uploadOk
                    && selected.solveMessage.startsWith("Diagnostic solve complete");
            runOnUiThread(() -> {
                fullDiagnosticRunning = false;
                latestCameraReportSummary = "Latest full diagnostic\n" + finalMessage;
                captureView.setText(finalMessage);
                updateMobileCameraDiagnosticGuide(success ? "solve_complete" : "solve_failed");
                updateCameraFieldTestStatus(
                        success ? "complete" : "failed",
                        success ? "Diagnostic complete" : "Diagnostic finished with issues",
                        success ? "Review reports and mark repeat if this run should count." : "Review the result, then retry when ready."
                );
                updatePhase2NightTestWizard(success ? "review" : "ready");
            });
        }).start();
    }

    private void requestCameraDiagnosticReports() {
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.length() == 0) {
            cameraReportView.setText("Camera reports unavailable\nSet the PiFinder URL in PiFinder Remote first.");
            updateMobileCameraDiagnosticGuide("remote_needed");
            updateCameraFieldTestStatus("failed", "Reports unavailable", "Set the PiFinder URL in PiFinder Remote.");
            return;
        }
        cameraReportView.setText("Loading camera diagnostic reports...\n" + baseUrl + "/mobile/camera_reports?limit=20");
        updateCameraFieldTestStatus("running", "Loading reports", "Requesting saved camera reports from PiFinder.");
        new Thread(() -> {
            String message = getCameraDiagnosticReports(baseUrl);
            runOnUiThread(() -> {
                cameraReportView.setText(message);
                boolean loaded = message.startsWith("Camera diagnostic history");
                if (!loaded && latestCameraReportSummary.length() == 0) {
                    latestCameraReportSummary = message;
                }
                updateMobileCameraDiagnosticGuide(loaded ? "reports_loaded" : "solve_failed");
                updateCameraFieldTestStatus(
                        loaded ? "complete" : "failed",
                        loaded ? "Reports loaded" : "Reports failed",
                        loaded ? "Use Copy summary for your notes." : "Check PiFinder connection and try again."
                );
                updatePhase2NightTestWizard(loaded ? "reports_loaded" : "ready");
            });
        }).start();
    }

    private String getCameraDiagnosticReports(String baseUrl) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(baseUrl + "/mobile/camera_reports?limit=20");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(20000);
            connection.setRequestProperty("Accept", "application/json");

            int status = connection.getResponseCode();
            String responseBody = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                if (status == 404) {
                    return "Camera reports endpoint not available"
                            + "\nUpdate the PiFinder Lite backend or continue with the latest local diagnostic summary.";
                }
                return "Camera reports failed\nHTTP " + status + "\n" + responseErrorSummary(responseBody);
            }
            JSONObject json = new JSONObject(responseBody);
            if (!json.optBoolean("ok", false)) {
                return "Camera reports failed\nServer returned ok=false.";
            }
            return formatCameraReports(json);
        } catch (Exception e) {
            return "Camera reports failed\n" + shortError(e)
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private void updateMobileCameraDiagnosticGuide(String stage) {
        if (cameraDiagnosticGuideView == null) {
            return;
        }
        String text = "Guided field test\n"
                + "This guide explains what the field test does.\n"
                + "Use the Current field test card for live progress.\n\n"
                + "Field test steps\n"
                + "1. Send GPS from Calibration.\n"
                + "2. Run full diagnostic.\n"
                + "3. View reports.\n"
                + "4. Mark repeat run when repeating the same setup.\n\n"
                + "Advanced captures below are for troubleshooting individual camera steps.\n\n";
        if ("capturing".equals(stage)) {
            text += "Status: capturing a solve-targeted JPEG burst.";
        } else if ("full_running".equals(stage)) {
            text += "Status: full diagnostic running. Capture, upload, score, and report will run in sequence.";
        } else if ("capture_ready".equals(stage)) {
            text += "Status: capture complete. Upload Last JPEG when PiFinder is reachable.";
        } else if ("capture_needed".equals(stage)) {
            text += "Status: no JPEG is ready. Use Run full diagnostic, or Diagnostic burst in Advanced captures.";
        } else if ("remote_needed".equals(stage)) {
            text += "Status: PiFinder URL missing. Set it in PiFinder Remote.";
        } else if ("uploading".equals(stage)) {
            text += "Status: uploading the latest JPEG to PiFinder.";
        } else if ("uploaded".equals(stage)) {
            text += "Status: uploaded. Tap Diagnostic Solve to score and solve on PiFinder.";
        } else if ("solving".equals(stage)) {
            text += "Status: PiFinder is scoring and running diagnostic solve.";
        } else if ("solve_complete".equals(stage)) {
            text += "Status: diagnostic solve complete. Review score, solve result, and report path.";
        } else if ("reports_loaded".equals(stage)) {
            text += "Status: report history loaded. Use it to compare recent score/solve results.";
        } else if ("solve_failed".equals(stage)) {
            text += "Status: diagnostic solve request failed. Check PiFinder status and frame id.";
        } else if ("upload_failed".equals(stage)) {
            text += "Status: upload failed. Check PiFinder IP, Wi-Fi, and /mobile/status.";
        } else {
            text += "Status: ready. Use this for night testing or camera checks.";
        }
        cameraDiagnosticGuideView.setText(text);
    }

    private void updateCameraFieldTestStatus(String status, String step, String detail) {
        if (cameraFieldTestStatusView == null) {
            return;
        }
        cameraFieldTestStatusView.setText(
                "Current field test\n"
                        + "Status: " + status + "\n"
                        + "Step: " + step + "\n"
                        + "Last action: " + detail
        );
    }

    private String mobileCameraDiagnosticPlanText() {
        return "PiFinder Lite mobile camera diagnostic\n"
                + "1. Start PiFinder Lite on Raspberry.\n"
                + "2. Set the PiFinder base URL in the Android app.\n"
                + "3. Camera Lab -> Save Folder.\n"
                + "4. Calibration -> Send GPS.\n"
                + "5. Tap Run full diagnostic.\n"
                + "6. Review uploaded frame ID, quality score, solve/skipped state, and stored report.\n"
                + "7. Use Advanced captures only when debugging individual steps.\n";
    }

    private void showPhase2NightTestWizard() {
        updatePhase2NightTestWizard("review");
        if (cameraReportView != null) {
            cameraReportView.setText(phase2NightTestPlanText());
        }
    }

    private void markPhase2NightTestRepeat() {
        phase2NightTestRepeatCount += 1;
        updatePhase2NightTestWizard("repeat_marked");
        updateCameraFieldTestStatus("idle", "Repeat run marked", "Run full diagnostic again under the same setup.");
        if (cameraReportView != null) {
            cameraReportView.setText("Repeat run marked\nCount: " + phase2NightTestRepeatCount
                    + "\nRun full diagnostic again under the same setup.");
        }
        Toast.makeText(this, "Night test repeat marked", Toast.LENGTH_SHORT).show();
    }

    private void updatePhase2NightTestWizard(String stage) {
        if (phase2NightTestWizardView == null) {
            return;
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        String folderStatus = outputTreeUri == null ? "missing" : "selected";
        String reportStatus = latestCameraReportSummary == null
                || latestCameraReportSummary.trim().length() == 0
                ? "not loaded"
                : "loaded";
        String text = "Night checklist\n"
                + "Goal: collect clear, comparable camera diagnostics without changing telescope pointing.\n"
                + "Status: " + phase2NightTestWizardStatus(stage) + "\n\n"
                + "Checklist\n"
                + "1. PiFinder URL: " + (baseUrl.length() == 0 ? "missing" : baseUrl) + "\n"
                + "2. In Calibration: SEND GPS.\n"
                + "3. Save folder: " + folderStatus + "\n"
                + "4. In Camera Lab: Run full diagnostic.\n"
                + "5. Use View reports, then Copy summary for sanitized notes.\n"
                + "6. Repeat count marked here: " + phase2NightTestRepeatCount + "\n"
                + "7. Report summary: " + reportStatus + "\n\n"
                + "Decision boundary: test completed means the workflow ran. Camera reliability needs repeated clear-sky results.\n"
                + "Safety: diagnostic-only; no mobile camera solve updates pointing or the integrator.";
        phase2NightTestWizardView.setText(text);
    }

    private String phase2NightTestWizardStatus(String stage) {
        if ("repeat_marked".equals(stage)) {
            return "repeat marked; run another full diagnostic or load reports.";
        }
        if ("reports_loaded".equals(stage)) {
            return "reports loaded; copy the summary for your notes.";
        }
        if ("review".equals(stage)) {
            return "review the checklist and run each field step deliberately.";
        }
        return "ready; use this before a clear-sky or partial-night run.";
    }

    private String phase2NightTestPlanText() {
        String summary = latestCameraReportSummary == null ? "" : latestCameraReportSummary.trim();
        return "Night Test Wizard\n"
                + "Purpose: collect repeatable phone-camera diagnostics.\n"
                + "This records a completed test session. Camera reliability still needs repeated clear-sky results.\n\n"
                + "Field steps\n"
                + "1. Start PiFinder Lite on Raspberry.\n"
                + "2. Set Android PiFinder base URL and run TEST CONNECTION.\n"
                + "3. In Calibration, SEND GPS.\n"
                + "4. Camera Lab -> SAVE FOLDER.\n"
                + "5. Run Full Diagnostic.\n"
                + "6. View Reports and copy the sanitized report summary.\n"
                + "7. Mark Repeat after each completed diagnostic attempt.\n\n"
                + "Evidence state\n"
                + "- Repeat count marked in app: " + phase2NightTestRepeatCount + "\n"
                + "- Save folder selected: " + (outputTreeUri == null ? "no" : "yes") + "\n"
                + "- Latest uploaded frame ID: " + safeEvidenceText(lastUploadedFrameId, "none") + "\n"
                + "- Latest report summary loaded: " + (summary.length() == 0 ? "no" : "yes") + "\n\n"
                + "Decision boundary\n"
                + "- test completed: checklist ran and report summary was captured.\n"
                + "- reliable camera use: requires repeated clear-sky results.\n"
                + "- diagnostic-only: do not feed mobile solves into pointing or the integrator.\n";
    }

    private String safeEvidenceText(String value, String fallback) {
        if (value == null || value.trim().length() == 0) {
            return fallback;
        }
        return value.replace("\n", " ").replace("\r", " ").trim();
    }

    private void copyPhase2NightTestPlan() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder night test plan", phase2NightTestPlanText()));
        Toast.makeText(this, "Night test plan copied", Toast.LENGTH_SHORT).show();
    }

    private void copyMobileCameraDiagnosticPlan() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder mobile diagnostic plan", mobileCameraDiagnosticPlanText()));
        Toast.makeText(this, "Diagnostic plan copied", Toast.LENGTH_SHORT).show();
    }

    private void copyCameraReportSummary() {
        String summary = latestCameraReportSummary == null ? "" : latestCameraReportSummary.trim();
        if (summary.length() == 0) {
            summary = "No camera diagnostic report summary loaded.\nTap View Reports first.";
        }
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder camera report summary", summary));
        Toast.makeText(this, "Camera report summary copied", Toast.LENGTH_SHORT).show();
    }

    private String postMobileCameraFrame(
            String baseUrl,
            String filename,
            byte[] frameBytes,
            String metadataJson
    ) {
        HttpURLConnection connection = null;
        String boundary = "PiFinderMobileBoundary" + System.currentTimeMillis();
        try {
            byte[] multipartBody = buildCameraFrameMultipartBody(
                    boundary,
                    filename,
                    frameBytes,
                    metadataJson
            );
            URL url = new URL(baseUrl + "/mobile/camera_frame");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(30000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            connection.setFixedLengthStreamingMode(multipartBody.length);

            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(multipartBody);
            }

            int status = connection.getResponseCode();
            String body = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                return "Camera frame upload failed\nHTTP " + status + "\n" + responseErrorSummary(body);
            }
            JSONObject json = new JSONObject(body);
            if (!json.optBoolean("ok", false)) {
                return "Camera frame upload failed\nServer returned ok=false.";
            }
            lastUploadedFrameId = json.optString("frame_id", "");
            return "Camera frame uploaded\nFrame ID: " + json.optString("frame_id", "unknown")
                    + "\nBytes: " + json.optLong("bytes", frameBytes.length)
                    + "\nElapsed: " + json.optInt("elapsed_ms", -1) + " ms";
        } catch (Exception e) {
            return "Camera frame upload failed\n" + shortError(e)
                    + "\nJPEG bytes: " + frameBytes.length
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private void requestDiagnosticCameraSolve() {
        String frameId = lastUploadedFrameId == null ? "" : lastUploadedFrameId.trim();
        if (frameId.length() == 0) {
            captureView.setText("No uploaded frame ID ready.\nUpload Last JPEG before Diagnostic Solve.");
            updateMobileCameraDiagnosticGuide("capture_needed");
            return;
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.length() == 0) {
            captureView.setText("PiFinder URL missing.\nSet it in PiFinder Remote first.");
            updateMobileCameraDiagnosticGuide("remote_needed");
            return;
        }
        captureView.setText("Requesting diagnostic solve...\nFrame ID: " + frameId
                + "\n" + baseUrl + "/mobile/camera_solve");
        updateMobileCameraDiagnosticGuide("solving");
        new Thread(() -> {
            String message = postDiagnosticCameraSolve(baseUrl, frameId);
            runOnUiThread(() -> {
                captureView.setText(message);
                if (message.startsWith("Diagnostic solve complete")) {
                    updateMobileCameraDiagnosticGuide("solve_complete");
                } else {
                    updateMobileCameraDiagnosticGuide("solve_failed");
                }
            });
        }).start();
    }

    private String postDiagnosticCameraSolve(String baseUrl, String frameId) {
        try {
            return formatDiagnosticSolveResult(postDiagnosticCameraSolveJson(baseUrl, frameId));
        } catch (Exception e) {
            return "Diagnostic solve failed\n" + shortError(e)
                    + "\nFrame ID: " + frameId
                    + "\nCheck PiFinder IP, port, and Wi-Fi.";
        }
    }

    private JSONObject postDiagnosticCameraSolveJson(String baseUrl, String frameId) throws Exception {
        HttpURLConnection connection = null;
        try {
            JSONObject payload = new JSONObject();
            payload.put("frame_id", frameId);
            payload.put("solve_timeout_ms", 1000);
            payload.put("ai_image_preprocessing_enabled", aiImagePreprocessingEnabled);
            payload.put("preprocess_strategy", aiImagePreprocessingEnabled ? "adaptive" : "classic");
            payload.put("preprocess_modes", aiImagePreprocessingEnabled ? "auto" : "baseline,background_subtract");
            byte[] body = payload.toString().getBytes(StandardCharsets.UTF_8);
            URL url = new URL(baseUrl + "/mobile/camera_solve");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(45000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }

            int status = connection.getResponseCode();
            String responseBody = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                if (status == 404) {
                    throw new IOException("Diagnostic solve endpoint not available. Update the PiFinder Lite backend before camera solve tests.");
                }
                throw new IOException("HTTP " + status + ": " + responseErrorSummary(responseBody));
            }
            JSONObject json = new JSONObject(responseBody);
            if (!json.optBoolean("ok", false)) {
                throw new JSONException("Server returned ok=false.");
            }
            return json;
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private String formatDiagnosticSolveResult(JSONObject json) {
        JSONObject score = json.optJSONObject("score");
        JSONObject solve = json.optJSONObject("solve");
        JSONObject report = json.optJSONObject("report");
        JSONObject summary = json.optJSONObject("summary");
        JSONObject advice = json.optJSONObject("advice");
        String grade = score == null ? "unknown" : score.optString("grade", "unknown");
        double qualityScore = score == null ? -1.0 : score.optDouble("quality_score", -1.0);
        boolean attempted = solve != null && solve.optBoolean("attempted", false);
        boolean solveOk = solve != null && solve.optBoolean("solve_ok", false);
        String skippedReason = solve == null ? "" : solve.optString("skipped_reason", "");
        JSONObject aiPreprocessing = solve == null ? null : solve.optJSONObject("ai_image_preprocessing");
        boolean aiEnabled = aiPreprocessing != null && aiPreprocessing.optBoolean("enabled", false);
        String aiVerdict = aiPreprocessing == null ? "" : aiPreprocessing.optString("verdict", "");
        double aiExtraTimeMs = aiPreprocessing == null ? -1.0 : aiPreprocessing.optDouble("extra_time_ms", -1.0);
        String aiWinningVariant = aiPreprocessing == null ? "" : aiPreprocessing.optString("winning_variant", "");
        String reportPath = report == null ? "not stored" : report.optString("json_report", "not stored");
        String summaryLabel = summary == null ? "" : summary.optString("label", "");
        String adviceLabel = advice == null ? "" : advice.optString("label", "");
        String adviceMessage = advice == null ? "" : advice.optString("message", "");
        String adviceNext = advice == null ? "" : advice.optString("next_action", "");
        String recommendation = json.optString("recommendation", "");
        String nextAction = json.optString("next_action", "");
        return "Diagnostic solve complete\nFrame ID: " + json.optString("frame_id", "unknown")
                + (summaryLabel.length() > 0 ? "\nSummary: " + summaryLabel : "")
                + "\nGrade: " + grade
                + "\nScore: " + qualityScore
                + "\nAttempted: " + attempted
                + "\nSolve OK: " + solveOk
                + (skippedReason.length() > 0 ? "\nSkipped: " + skippedReason : "")
                + (aiPreprocessing != null ? "\nAI Image Preprocessing: " + (aiEnabled ? "enabled" : "disabled") : "")
                + (aiVerdict.length() > 0 ? "\nAI verdict: " + aiVerdict : "")
                + (aiExtraTimeMs >= 0 ? "\nAI extra time ms: " + aiExtraTimeMs : "")
                + (aiWinningVariant.length() > 0 ? "\nAI winning variant: " + aiWinningVariant : "")
                + (adviceLabel.length() > 0 ? "\nAdvice: " + adviceLabel : "")
                + (adviceMessage.length() > 0 ? "\nWhy: " + adviceMessage : "")
                + (adviceNext.length() > 0 ? "\nTry: " + adviceNext : "")
                + (recommendation.length() > 0 ? "\nRecommendation: " + recommendation : "")
                + (nextAction.length() > 0 ? "\nNext: " + nextAction : "")
                + "\nReport: " + reportPath
                + "\nDiagnostic only: " + json.optBoolean("diagnostic_only", true);
    }

    private String formatFullDiagnosticResult(String uploadMessage, String solveMessage) {
        StringBuilder result = new StringBuilder();
        result.append("Full diagnostic report\n\nUpload\n").append(uploadMessage);
        if (solveMessage == null || solveMessage.length() == 0) {
            result.append("\n\nDiagnostic solve\nNot requested because upload did not return a frame ID.");
            return result.toString();
        }
        result.append("\n\nDiagnostic solve\n").append(solveMessage);
        return result.toString();
    }

    private String formatFullDiagnosticResult(List<SolveCandidateResult> results) {
        StringBuilder result = new StringBuilder();
        result.append("Full diagnostic report\n");
        if (results == null || results.isEmpty()) {
            result.append("\nNo candidate frames were available.");
            return result.toString();
        }
        result.append("\nCandidate ranking\n").append(formatSolveCandidateRanking(results));
        SolveCandidateResult selected = results.get(0);
        result.append("\n\nSelected frame\n")
                .append(selected.candidate.filename)
                .append("\nReason: selected by Raspberry score from ")
                .append(results.size())
                .append(" candidate(s) distributed across burst.")
                .append("\nFrame ID: ")
                .append(selected.frameId.length() > 0 ? selected.frameId : "not uploaded")
                .append("\nQuality score: ")
                .append(selected.qualityScore)
                .append("\nSolve OK: ")
                .append(selected.solveOk)
                .append("\n\nSelected upload\n")
                .append(selected.uploadMessage);
        if (selected.solveMessage == null || selected.solveMessage.length() == 0) {
            result.append("\n\nSelected diagnostic solve\nNot requested because upload did not return a frame ID.");
        } else {
            result.append("\n\nSelected diagnostic solve\n").append(selected.solveMessage);
        }
        return result.toString();
    }

    private void recordSolveCandidateFrame(String filename, String label, byte[] bytes, int burstIndex) {
        solveCandidateFrames.add(new SolveCandidateFrame(
                burstIndex,
                captureFrameCount,
                filename,
                label,
                Arrays.copyOf(bytes, bytes.length),
                "eligible solve-candidate JPEG"
        ));
    }

    private int candidateUploadLimitForBurst(int count) {
        if (count <= 3) {
            return count;
        }
        if (count <= 12) {
            return 3;
        }
        if (count <= 24) {
            return 5;
        }
        return 7;
    }

    private List<SolveCandidateFrame> selectSolveCandidateFramesForUpload() {
        List<SolveCandidateFrame> selected = new ArrayList<>();
        int count = solveCandidateFrames.size();
        int limit = candidateUploadLimitForBurst(count);
        if (limit <= 0) {
            return selected;
        }
        if (count <= limit) {
            selected.addAll(solveCandidateFrames);
        } else {
            int start = count > limit + 2 ? 1 : 0;
            int end = count > limit + 2 ? count - 2 : count - 1;
            for (int i = 0; i < limit; i++) {
                int index = limit == 1
                        ? count / 2
                        : Math.round(start + (i * (end - start) / (float) (limit - 1)));
                SolveCandidateFrame candidate = solveCandidateFrames.get(index);
                if (!selected.contains(candidate)) {
                    selected.add(candidate);
                }
            }
            for (SolveCandidateFrame candidate : solveCandidateFrames) {
                if (selected.size() >= limit) {
                    break;
                }
                if (!selected.contains(candidate)) {
                    selected.add(candidate);
                }
            }
        }
        latestSolveCandidateRankingSummary = "Android preselected " + selected.size()
                + "/" + count + " candidates distributed across burst for Raspberry scoring.";
        captureMetadata.append("solve_candidate_selector=").append(latestSolveCandidateRankingSummary).append("\n");
        return selected;
    }

    private void rankSolveCandidateResults(List<SolveCandidateResult> results) {
        Collections.sort(results, (left, right) -> Double.compare(
                scoreSolveCandidateResult(right),
                scoreSolveCandidateResult(left)
        ));
    }

    private double scoreSolveCandidateResult(SolveCandidateResult result) {
        double score = result.qualityScore >= 0.0 ? result.qualityScore : 0.0;
        if (result.solveOk) {
            score += 10000.0;
        }
        if (result.uploadOk) {
            score += 1000.0;
        }
        score += Math.min(result.candidate.bytes.length / 100000.0, 99.0);
        return score;
    }

    private String formatSolveCandidateRanking(List<SolveCandidateResult> results) {
        StringBuilder ranking = new StringBuilder();
        ranking.append("selected by Raspberry score; candidates distributed across burst");
        for (int i = 0; i < results.size(); i++) {
            SolveCandidateResult item = results.get(i);
            ranking.append("\n")
                    .append(i + 1)
                    .append(". ")
                    .append(item.candidate.filename)
                    .append(" frame ")
                    .append(item.candidate.burstIndex)
                    .append("/")
                    .append(item.candidate.totalFrames)
                    .append(" score ")
                    .append(item.qualityScore)
                    .append(" grade ")
                    .append(item.grade)
                    .append(" solve_ok ")
                    .append(item.solveOk)
                    .append(" frame_id ")
                    .append(item.frameId.length() > 0 ? item.frameId : "none");
        }
        latestSolveCandidateRankingSummary = ranking.toString();
        return latestSolveCandidateRankingSummary;
    }

    private double parseDiagnosticQualityScore(String solveMessage) {
        return parseDoubleAfterLabel(solveMessage, "Score: ");
    }

    private String parseDiagnosticGrade(String solveMessage) {
        if (solveMessage == null) {
            return "unknown";
        }
        for (String line : solveMessage.split("\n")) {
            if (line.startsWith("Grade: ")) {
                return line.substring("Grade: ".length()).trim();
            }
        }
        return "unknown";
    }

    private double parseDoubleAfterLabel(String text, String label) {
        if (text == null) {
            return -1.0;
        }
        int start = text.indexOf(label);
        if (start < 0) {
            return -1.0;
        }
        start += label.length();
        int end = text.indexOf("\n", start);
        String value = (end >= 0 ? text.substring(start, end) : text.substring(start)).trim();
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            return -1.0;
        }
    }

    private String formatCameraReports(JSONObject json) {
        JSONObject sessionSummary = json.optJSONObject("session_summary");
        JSONArray reports = json.optJSONArray("reports");
        JSONObject statusCounts = sessionSummary == null ? null : sessionSummary.optJSONObject("status_counts");
        JSONObject dominantAdvice = sessionSummary == null ? null : sessionSummary.optJSONObject("dominant_advice");
        StringBuilder result = new StringBuilder();
        result.append("Camera diagnostic history\n");
        if (sessionSummary != null) {
            JSONObject environment = sessionSummary.optJSONObject("environment");
            result.append("Reports: ")
                    .append(sessionSummary.optInt("returned_reports", 0))
                    .append("/")
                    .append(sessionSummary.optInt("total_reports", 0))
                    .append("\nSolved: ")
                    .append(sessionSummary.optInt("solved_count", 0))
                    .append("\nRejected: ")
                    .append(sessionSummary.optInt("rejected_count", 0));
            String bestFrame = sessionSummary.optString("best_frame_id", "");
            if (bestFrame.length() > 0 && !"null".equals(bestFrame)) {
                result.append("\nBest frame: ").append(bestFrame)
                        .append(" score ")
                        .append(sessionSummary.optDouble("best_quality_score", -1.0));
            }
            String recommendation = sessionSummary.optString("recommendation", "");
            String nextAction = sessionSummary.optString("next_action", "");
            if (statusCounts != null) {
                result.append("\nStatus counts: ").append(statusCounts.toString());
            }
            if (dominantAdvice != null) {
                String adviceLabel = dominantAdvice.optString("label", "");
                String adviceNext = dominantAdvice.optString("next_action", "");
                if (adviceLabel.length() > 0) {
                    result.append("\nMain advice: ").append(adviceLabel);
                }
                if (adviceNext.length() > 0) {
                    result.append("\nTry: ").append(adviceNext);
                }
            }
            if (environment != null) {
                result.append("\nEnv reports: ")
                        .append(environment.optInt("reports_with_environment", 0));
                JSONObject latestEnvironment = environment.optJSONObject("latest");
                if (latestEnvironment != null) {
                    result.append("\nLatest env: ")
                            .append(formatEnvironmentSummary(latestEnvironment));
                }
            }
            if (recommendation.length() > 0) {
                result.append("\nRecommendation: ").append(recommendation);
            }
            if (nextAction.length() > 0) {
                result.append("\nNext: ").append(nextAction);
            }
        }
        int malformedReports = json.optInt("malformed_reports", 0);
        if (malformedReports > 0) {
            result.append("\nWarnings: ").append(malformedReports).append(" malformed report(s) skipped");
        }
        result.append("\n\nRecent reports");
        if (reports == null || reports.length() == 0) {
            result.append("\nNo reports available yet. Run full diagnostic first.");
            latestCameraReportSummary = result.toString();
            return latestCameraReportSummary;
        }
        int count = Math.min(reports.length(), 5);
        for (int i = 0; i < count; i++) {
            JSONObject report = reports.optJSONObject(i);
            if (report == null) {
                continue;
            }
            JSONObject summary = report.optJSONObject("summary");
            JSONObject advice = report.optJSONObject("advice");
            JSONObject score = report.optJSONObject("score");
            JSONObject solve = report.optJSONObject("solve");
            JSONObject environment = report.optJSONObject("environment");
            String status = summary == null ? "unknown" : summary.optString("status", "unknown");
            String label = summary == null ? "" : summary.optString("label", "");
            String grade = summary == null ? "unknown" : summary.optString("grade", "unknown");
            double qualityScore = summary == null ? -1.0 : summary.optDouble("quality_score", -1.0);
            boolean attempted = solve != null && solve.optBoolean("attempted", false);
            boolean solveOk = solve != null && solve.optBoolean("solve_ok", false);
            String skippedReason = solve == null ? "" : solve.optString("skipped_reason", "");
            String adviceLabel = advice == null ? "" : advice.optString("label", "");
            String adviceNext = advice == null ? "" : advice.optString("next_action", "");
            if (score != null && qualityScore < 0) {
                qualityScore = score.optDouble("quality_score", -1.0);
            }
            result.append("\n\n")
                    .append(i + 1)
                    .append(". ")
                    .append(report.optString("frame_id", "unknown"))
                    .append("\nStatus: ")
                    .append(status)
                    .append(label.length() > 0 ? " (" + label + ")" : "")
                    .append("\nGrade: ")
                    .append(grade)
                    .append(" score ")
                    .append(qualityScore)
                    .append("\nAttempted: ")
                    .append(attempted)
                    .append(" solve_ok: ")
                    .append(solveOk);
            if (skippedReason.length() > 0) {
                result.append("\nSkipped: ").append(skippedReason);
            }
            if (adviceLabel.length() > 0) {
                result.append("\nAdvice: ").append(adviceLabel);
            }
            if (adviceNext.length() > 0) {
                result.append("\nTry: ").append(adviceNext);
            }
            if (environment != null) {
                result.append("\nEnvironment: ")
                        .append(environment.optBoolean("available", false) ? "available" : "missing");
            }
            result.append("\nReport: ").append(report.optString("report_file", "unknown"));
        }
        latestCameraReportSummary = result.toString();
        return latestCameraReportSummary;
    }

    private byte[] buildCameraFrameMultipartBody(
            String boundary,
            String filename,
            byte[] frameBytes,
            String metadataJson
    ) throws IOException {
        ByteArrayOutputStream body = new ByteArrayOutputStream(frameBytes.length + metadataJson.length() + 1024);
        writeMultipartText(body, boundary, "metadata", metadataJson);
        writeMultipartFile(body, boundary, "frame", filename, "image/jpeg", frameBytes);
        body.write(("--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
        return body.toByteArray();
    }

    private void writeMultipartText(
            OutputStream outputStream,
            String boundary,
            String name,
            String value
    ) throws IOException {
        outputStream.write(("--" + boundary + "\r\n").getBytes(StandardCharsets.UTF_8));
        outputStream.write(("Content-Disposition: form-data; name=\"" + name + "\"\r\n").getBytes(StandardCharsets.UTF_8));
        outputStream.write("Content-Type: application/json; charset=utf-8\r\n\r\n".getBytes(StandardCharsets.UTF_8));
        outputStream.write(value.getBytes(StandardCharsets.UTF_8));
        outputStream.write("\r\n".getBytes(StandardCharsets.UTF_8));
    }

    private void writeMultipartFile(
            OutputStream outputStream,
            String boundary,
            String name,
            String filename,
            String contentType,
            byte[] bytes
    ) throws IOException {
        outputStream.write(("--" + boundary + "\r\n").getBytes(StandardCharsets.UTF_8));
        outputStream.write((
                "Content-Disposition: form-data; name=\"" + name + "\"; filename=\""
                        + safeMultipartFilename(filename) + "\"\r\n"
        ).getBytes(StandardCharsets.UTF_8));
        outputStream.write(("Content-Type: " + contentType + "\r\n\r\n").getBytes(StandardCharsets.UTF_8));
        outputStream.write(bytes);
        outputStream.write("\r\n".getBytes(StandardCharsets.UTF_8));
    }

    private String safeMultipartFilename(String filename) {
        if (filename == null || filename.trim().length() == 0) {
            return "frame.jpg";
        }
        return filename.replace("\\", "_").replace("/", "_").replace("\"", "_");
    }

    private String buildCameraFrameMetadataJson(String filename, int byteCount) {
        return buildCameraFrameMetadataJson(filename, byteCount, selectedSolveCandidateFrame, latestSolveCandidateRankingSummary);
    }

    private String buildCameraFrameMetadataJson(
            String filename,
            int byteCount,
            SolveCandidateFrame selectedCandidate,
            String rankingSummary
    ) {
        try {
            JSONObject metadata = new JSONObject();
            metadata.put("schema", "pifinder-mobile-camera-frame-v0");
            metadata.put("created_utc", utcIso(System.currentTimeMillis()));
            JSONObject device = new JSONObject();
            device.put("manufacturer", android.os.Build.MANUFACTURER);
            device.put("model", android.os.Build.MODEL);
            device.put("android_api", android.os.Build.VERSION.SDK_INT);
            metadata.put("device", device);
            metadata.put("camera_id", activeCaptureCameraId);
            metadata.put("camera_selection", captureCameraSelection);
            metadata.put("capture_mode", captureTestName);
            metadata.put("source_file", filename);
            metadata.put("format", "jpeg");
            metadata.put("bytes", byteCount);
            metadata.put("orientation_degrees", captureJpegOrientation);
            if (activeCaptureSize != null) {
                metadata.put("width", activeCaptureSize.getWidth());
                metadata.put("height", activeCaptureSize.getHeight());
            }
            metadata.put("storage_only", true);
            metadata.put("solver_requested", false);
            if (selectedCandidate != null) {
                JSONObject selector = new JSONObject();
                selector.put("strategy", "dynamic_distributed_raspberry_score");
                selector.put("reason", selectedCandidate.selectionReason);
                selector.put("ranking_summary", rankingSummary == null ? "" : rankingSummary);
                JSONObject selected = new JSONObject();
                selected.put("filename", selectedCandidate.filename);
                selected.put("burst_index", selectedCandidate.burstIndex);
                selected.put("total_frames", selectedCandidate.totalFrames);
                selected.put("label", selectedCandidate.label);
                selector.put("selected_candidate", selected);
                metadata.put("solve_candidate_selector", selector);
            }
            metadata.put("environment", new JSONObject(buildEnvironmentPayloadJson()));
            return metadata.toString();
        } catch (JSONException e) {
            return "{\"schema\":\"pifinder-mobile-camera-frame-v0\",\"storage_only\":true}";
        }
    }

    private String responseErrorSummary(String body) {
        if (body == null || body.trim().length() == 0) {
            return "No error body returned.";
        }
        try {
            JSONObject json = new JSONObject(body);
            JSONObject error = json.optJSONObject("error");
            if (error != null) {
                return error.optString("code", "error")
                        + "\n" + error.optString("message", body);
            }
            return json.optString("message", body);
        } catch (JSONException e) {
            return body.length() > 160 ? body.substring(0, 160) : body;
        }
    }

    private String formatJsonStringArray(JSONArray array) {
        if (array == null || array.length() == 0) {
            return "none";
        }
        List<String> values = new ArrayList<>();
        for (int i = 0; i < array.length(); i++) {
            String value = array.optString(i, "").trim();
            if (value.length() > 0) {
                values.add(value);
            }
        }
        if (values.isEmpty()) {
            return "none";
        }
        return TextUtils.join(", ", values);
    }

    private String readHttpBody(HttpURLConnection connection, int status) throws IOException {
        InputStream stream = status >= 200 && status < 400
                ? connection.getInputStream()
                : connection.getErrorStream();
        if (stream == null) {
            return "";
        }
        StringBuilder body = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
            String line;
            while ((line = reader.readLine()) != null) {
                body.append(line);
            }
        }
        return body.toString();
    }

    private String shortError(Exception e) {
        String message = e.getMessage();
        if (message == null || message.trim().length() == 0) {
            return e.getClass().getSimpleName();
        }
        return message;
    }

    private String loadRemoteBaseUrl() {
        return prefs().getString(KEY_REMOTE_BASE_URL, "http://pifinder.local");
    }

    private String normalizeRemoteBaseUrl(String value) {
        if (value == null) {
            return "";
        }
        String url = value.trim();
        if (url.length() == 0) {
            return "";
        }
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://" + url;
        }
        int queryIndex = url.indexOf("?");
        if (queryIndex >= 0) {
            url = url.substring(0, queryIndex);
        }
        int fragmentIndex = url.indexOf("#");
        if (fragmentIndex >= 0) {
            url = url.substring(0, fragmentIndex);
        }
        while (url.endsWith("/")) {
            url = url.substring(0, url.length() - 1);
        }
        if (url.endsWith("/remote")) {
            url = url.substring(0, url.length() - "/remote".length());
        }
        return url;
    }

    private void updateRemoteStatus(String message) {
        if (remoteStatusView != null) {
            remoteStatusView.setText("Remote\n" + message);
        }
        if (calibrationStatusView != null && "calibration".equals(currentScreenName)) {
            updateCalibrationStatus(message);
        }
    }

    private void updateCalibrationStatus(String message) {
        if (calibrationStatusView != null) {
            calibrationStatusView.setText("Current step\n" + message
                    + "\n\nBoundary: read-only diagnostic overlay. Poor-night/day runs remain needs_more_data.");
        }
    }

    private String calibrationChecklistText() {
        return "Phone mount checklist\n"
                + "1. Test connection.\n"
                + "2. Send profile and GPS.\n"
                + "3. Capture Stationary with the tube untouched.\n"
                + "4. Point at a repeatable reference and capture Mount ref.\n"
                + "5. Capture Repeat check without moving the phone.\n"
                + "6. Remount the phone and repeat Mount ref + Repeat check.\n"
                + "7. Wait 5 minutes, capture one final Repeat check.\n"
                + "8. Copy evidence for your calibration notes.";
    }

    private String aiImuDriftAnalysisGuideText() {
        return "AI IMU Drift Analysis\n"
                + "Collect solve-to-solve residual cycles before any correction profile.\n\n"
                + "Cycle\n"
                + "1. Start from a confirmed solve.\n"
                + "2. Record phone IMU orientation at the solve.\n"
                + "3. Move the telescope while the IMU predicts the path.\n"
                + "4. Stop and solve again.\n"
                + "5. Compare predicted final Alt/Az with solved final Alt/Az.\n\n"
                + "Raspberry endpoint\n"
                + "/mobile/imu_drift_analysis\n\n"
                + "Boundary\n"
                + "diagnostic_only=true; no integrator update; no runtime pointing update.";
    }

    private void showAiImuDriftAnalysisGuide() {
        updateCalibrationStatus(aiImuDriftAnalysisGuideText()
                + "\n\nCopy evidence to capture the JSON template.");
        copyAiImuDriftAnalysisEvidence();
    }

    private void startAiImuDriftSession() {
        while (aiImuDriftCycles.length() > 0) {
            aiImuDriftCycles.remove(0);
        }
        aiImuDriftInitialSolveAltAz = null;
        aiImuDriftMoveStartOrientation = null;
        aiImuDriftMoveEndOrientation = null;
        aiImuDriftMoveStartMs = 0L;
        aiImuDriftCycleCounter = 0;
        latestAiImuDriftAnalysisJson = "";
        updateAiImuDriftSessionView("AI IMU Drift Session\nReady.\n1. Send GPS.\n2. Initial solve.\n3. Start move.\n4. Finish cycle.\n5. Repeat 3+ cycles, then Analyze drift.");
    }

    private void captureAiImuDriftInitialSolve() {
        runAiImuDriftSolve("initial");
    }

    private void startAiImuDriftMove() {
        if (aiImuDriftInitialSolveAltAz == null
                || !aiImuDriftInitialSolveAltAz.optBoolean("available", false)) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nInitial solve required before Start move.");
            return;
        }
        if (!liveImuStarted) {
            startLiveSensors();
        }
        if (latestDeviceOrientationDeg == null) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nWaiting for rotation vector sample. Keep the app open, move the phone gently, then tap Start move again.");
            return;
        }
        aiImuDriftMoveStartOrientation = Arrays.copyOf(latestDeviceOrientationDeg, latestDeviceOrientationDeg.length);
        aiImuDriftMoveEndOrientation = null;
        aiImuDriftMoveStartMs = System.currentTimeMillis();
        updateAiImuDriftSessionView("AI IMU Drift Session\nMove started.\nMove the telescope, stop, then tap Finish cycle.");
    }

    private void finishAiImuDriftCycle() {
        if (aiImuDriftMoveStartOrientation == null || aiImuDriftMoveStartMs <= 0L) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nStart move before Finish cycle.");
            return;
        }
        if (latestDeviceOrientationDeg == null) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nNo final IMU orientation sample yet.");
            return;
        }
        aiImuDriftMoveEndOrientation = Arrays.copyOf(latestDeviceOrientationDeg, latestDeviceOrientationDeg.length);
        runAiImuDriftSolve("final");
    }

    private void analyzeAiImuDriftSession() {
        if (aiImuDriftCycles.length() == 0) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nNo cycles yet. Finish at least one cycle before analysis.");
            return;
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.length() == 0) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nPiFinder URL missing.");
            return;
        }
        updateAiImuDriftSessionView("AI IMU Drift Session\nAnalyzing " + aiImuDriftCycles.length() + " cycle(s)...");
        String payload = aiImuDriftSessionPayloadJson();
        new Thread(() -> {
            String message = postAiImuDriftAnalysis(baseUrl, payload);
            runOnUiThread(() -> updateAiImuDriftSessionView(message));
        }).start();
    }

    private void updateAiImuDriftSessionView(String message) {
        if (aiImuDriftSessionView != null) {
            aiImuDriftSessionView.setText(message);
        }
        updateCalibrationStatus(message);
    }

    private void runAiImuDriftSolve(String role) {
        if (aiImuDriftSolveRunning || fullDiagnosticRunning) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nA solve is already running.");
            return;
        }
        if (outputTreeUri == null) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nChoose Camera Lab Save folder before automated solves.");
            pickOutputFolder();
            return;
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestRuntimePermissions();
            return;
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.length() == 0) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nPiFinder URL missing.");
            return;
        }
        aiImuDriftSolveRunning = true;
        aiImuDriftSolveRole = role;
        updateAiImuDriftSessionView("AI IMU Drift Session\nCapturing " + role + " solve...");
        startCaptureTest("solve_candidate_burst", 256);
    }

    private void continueAiImuDriftSolve() {
        if (!aiImuDriftSolveRunning) {
            return;
        }
        List<SolveCandidateFrame> candidates = selectSolveCandidateFramesForUpload();
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (candidates.isEmpty() || baseUrl.length() == 0) {
            aiImuDriftSolveRunning = false;
            updateAiImuDriftSessionView("AI IMU Drift Session\nSolve failed before upload. Capture candidates or PiFinder URL missing.");
            return;
        }
        String role = aiImuDriftSolveRole;
        updateAiImuDriftSessionView("AI IMU Drift Session\nUploading " + candidates.size() + " candidate(s) for " + role + " solve.");
        new Thread(() -> {
            JSONObject selectedSolve = null;
            String lastError = "";
            for (SolveCandidateFrame candidate : candidates) {
                String metadataJson = buildCameraFrameMetadataJson(candidate.filename, candidate.bytes.length, candidate, latestSolveCandidateRankingSummary);
                String uploadMessage = postMobileCameraFrame(baseUrl, candidate.filename, Arrays.copyOf(candidate.bytes, candidate.bytes.length), metadataJson);
                String frameId = lastUploadedFrameId == null ? "" : lastUploadedFrameId.trim();
                if (!uploadMessage.startsWith("Camera frame uploaded") || frameId.length() == 0) {
                    lastError = uploadMessage;
                    continue;
                }
                try {
                    JSONObject solveJson = postDiagnosticCameraSolveJson(baseUrl, frameId);
                    JSONObject altAz = solveJson.optJSONObject("solve_altaz");
                    if (altAz != null && altAz.optBoolean("available", false)) {
                        selectedSolve = solveJson;
                        break;
                    }
                    lastError = formatDiagnosticSolveResult(solveJson);
                } catch (Exception e) {
                    lastError = shortError(e);
                }
            }
            JSONObject finalSelectedSolve = selectedSolve;
            String finalLastError = lastError;
            runOnUiThread(() -> completeAiImuDriftSolve(role, finalSelectedSolve, finalLastError));
        }).start();
    }

    private void completeAiImuDriftSolve(String role, JSONObject solveJson, String lastError) {
        aiImuDriftSolveRunning = false;
        aiImuDriftSolveRole = "";
        if (solveJson == null) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nNo solved Alt/Az available.\n" + lastError);
            return;
        }
        JSONObject altAz = solveJson.optJSONObject("solve_altaz");
        if ("initial".equals(role)) {
            aiImuDriftInitialSolveAltAz = altAz;
            updateAiImuDriftSessionView("AI IMU Drift Session\nInitial solve captured.\nAlt: "
                    + format(altAz.optDouble("alt_deg")) + "\nAz: " + format(altAz.optDouble("az_deg"))
                    + "\nNow tap Start move.");
            return;
        }
        addAiImuDriftCycle(altAz);
    }

    private void addAiImuDriftCycle(JSONObject finalSolveAltAz) {
        try {
            aiImuDriftCycleCounter++;
            JSONObject cycle = new JSONObject();
            cycle.put("cycle_id", "cycle_" + aiImuDriftCycleCounter);
            cycle.put("remount_id", "mount_a");
            cycle.put("duration_s", Math.max(0, Math.round((System.currentTimeMillis() - aiImuDriftMoveStartMs) / 1000.0)));
            cycle.put("predicted_final", predictedAiImuFinalAltAz());
            cycle.put("solve_final", altAzPointJson(finalSolveAltAz));
            aiImuDriftCycles.put(cycle);
            aiImuDriftInitialSolveAltAz = finalSolveAltAz;
            aiImuDriftMoveStartOrientation = null;
            aiImuDriftMoveEndOrientation = null;
            aiImuDriftMoveStartMs = 0L;
            updateAiImuDriftSessionView("AI IMU Drift Session\nCycle added: " + cycle.optString("cycle_id")
                    + "\nCycles ready: " + aiImuDriftCycles.length()
                    + "\nRepeat Start move / Finish cycle, or Analyze drift.");
        } catch (JSONException e) {
            updateAiImuDriftSessionView("AI IMU Drift Session\nCould not build cycle JSON: " + e.getMessage());
        }
    }

    private JSONObject predictedAiImuFinalAltAz() throws JSONException {
        double initialAlt = aiImuDriftInitialSolveAltAz.optDouble("alt_deg");
        double initialAz = aiImuDriftInitialSolveAltAz.optDouble("az_deg");
        double deltaAz = angleDeltaDeg(aiImuDriftMoveEndOrientation[0], aiImuDriftMoveStartOrientation[0]);
        double deltaAlt = aiImuDriftMoveEndOrientation[1] - aiImuDriftMoveStartOrientation[1];
        JSONObject predicted = new JSONObject();
        predicted.put("alt_deg", clamp(initialAlt + deltaAlt, -90.0, 90.0));
        predicted.put("az_deg", wrap360(initialAz + deltaAz));
        return predicted;
    }

    private JSONObject altAzPointJson(JSONObject source) throws JSONException {
        JSONObject point = new JSONObject();
        point.put("alt_deg", source.optDouble("alt_deg"));
        point.put("az_deg", source.optDouble("az_deg"));
        return point;
    }

    private double angleDeltaDeg(double end, double start) {
        double delta = end - start;
        while (delta > 180.0) {
            delta -= 360.0;
        }
        while (delta < -180.0) {
            delta += 360.0;
        }
        return delta;
    }

    private double wrap360(double value) {
        double wrapped = value % 360.0;
        return wrapped < 0 ? wrapped + 360.0 : wrapped;
    }

    private double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }

    private String helpText() {
        return "GET STARTED\n"
                + "1. Start PiFinder on the Raspberry Pi.\n"
                + "2. Connect this phone to the same network.\n"
                + "3. Open PiFinder Remote and set the Raspberry URL.\n"
                + "4. Run Test connection before sending data.\n"
                + "5. Use Night Vision when observing in the dark.\n\n"
                + "NORMAL FIELD USE\n"
                + "- PiFinder Remote is the main screen for telescope control.\n"
                + "- Open remote loads the regular PiFinder remote interface.\n"
                + "- Send profile, env, GPS, and IMU only when you want phone data available on the Raspberry.\n\n"
                + "PHONE SETUP\n"
                + "- Camera Lab checks whether this phone can capture useful night images.\n"
                + "- Calibration collects phone mount evidence when the phone is attached to the telescope.\n"
                + "- Diagnostics checks sensors, GPS, camera support, and readiness.\n\n"
                + "CAMERA LAB\n"
                + "1. Choose Save folder.\n"
                + "2. Use Night wizard for the checklist.\n"
                + "3. Run full diagnostic.\n"
                + "4. View reports and copy summary for your notes.\n"
                + "5. Use Advanced captures only for troubleshooting.\n\n"
                + "CALIBRATION\n"
                + "1. Mount the phone firmly.\n"
                + "2. Test connection and send profile/GPS.\n"
                + "3. Capture Stationary, Mount ref, and Repeat check.\n"
                + "4. Copy evidence for your notes.\n"
                + "These checks are diagnostic and do not change telescope pointing.\n\n"
                + "DIAGNOSTICS\n"
                + "- Run check grades the phone readiness.\n"
                + "- Start IMU shows live sensor updates.\n"
                + "- Copy result is the short shareable summary.\n"
                + "- Copy tech report is for debugging.";
    }

    private SpannableString helpTextStyled() {
        String text = helpText();
        SpannableString styledText = new SpannableString(text);
        boldHelpHeading(styledText, text, "GET STARTED");
        boldHelpHeading(styledText, text, "NORMAL FIELD USE");
        boldHelpHeading(styledText, text, "PHONE SETUP");
        boldHelpHeading(styledText, text, "CAMERA LAB");
        boldHelpHeading(styledText, text, "CALIBRATION");
        boldHelpHeading(styledText, text, "DIAGNOSTICS");
        return styledText;
    }

    private void boldHelpHeading(SpannableString styledText, String text, String heading) {
        int start = text.indexOf(heading);
        if (start < 0) {
            return;
        }
        int end = start + heading.length();
        styledText.setSpan(new StyleSpan(Typeface.BOLD), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        styledText.setSpan(new ForegroundColorSpan(themeText()), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
    }

    private TextView readinessBadge() {
        TextView textView = statusCard();
        textView.setTextSize(18);
        textView.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        textView.setGravity(Gravity.CENTER);
        textView.setMinHeight(dp(104));
        return textView;
    }

    private TextView proseText() {
        TextView textView = new TextView(this);
        textView.setTextSize(14);
        textView.setTextColor(themeMuted());
        textView.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL));
        textView.setLineSpacing(dp(4), 1.0f);
        textView.setPadding(dp(2), dp(8), dp(2), dp(8));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(4), 0, dp(8));
        textView.setLayoutParams(params);
        return textView;
    }

    private GradientDrawable roundedRect(int fill, int stroke, int strokeWidthDp, int radiusDp) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(radiusDp));
        drawable.setStroke(dp(strokeWidthDp), stroke);
        return drawable;
    }

    private int themeBg() {
        return nightVisionEnabled ? Color.rgb(4, 0, 0) : COLOR_BG;
    }

    private int themePanel() {
        return nightVisionEnabled ? Color.rgb(18, 2, 3) : COLOR_PANEL;
    }

    private int themeText() {
        return nightVisionEnabled ? Color.rgb(255, 88, 88) : COLOR_TEXT;
    }

    private int themeMuted() {
        return nightVisionEnabled ? Color.rgb(148, 45, 45) : COLOR_MUTED;
    }

    private int themeAccent() {
        return nightVisionEnabled ? Color.rgb(255, 48, 48) : COLOR_ACCENT;
    }

    private int themePrimary() {
        return nightVisionEnabled ? Color.rgb(156, 20, 22) : COLOR_PRIMARY;
    }

    private int themePrimaryText() {
        return nightVisionEnabled ? Color.rgb(255, 180, 172) : COLOR_PRIMARY_TEXT;
    }

    private int themePrimarySupportText() {
        return nightVisionEnabled ? Color.rgb(255, 132, 124) : Color.rgb(80, 14, 35);
    }

    private int themeSecondary() {
        return nightVisionEnabled ? Color.rgb(34, 6, 7) : COLOR_SECONDARY;
    }

    private int themeSecondaryStroke() {
        return nightVisionEnabled ? Color.rgb(90, 20, 22) : COLOR_SECONDARY_STROKE;
    }

    private int themeAdvanced() {
        return nightVisionEnabled ? Color.rgb(10, 0, 0) : COLOR_ADVANCED;
    }

    private int themeAdvancedStroke() {
        return nightVisionEnabled ? Color.rgb(54, 10, 11) : COLOR_ADVANCED_STROKE;
    }

    private int themeHairline() {
        return nightVisionEnabled ? Color.rgb(58, 11, 12) : Color.rgb(37, 43, 57);
    }

    private int themePass() {
        return nightVisionEnabled ? Color.rgb(255, 104, 96) : COLOR_PASS;
    }

    private int themeWarn() {
        return nightVisionEnabled ? Color.rgb(255, 126, 70) : COLOR_WARN;
    }

    private int themeFail() {
        return nightVisionEnabled ? Color.rgb(255, 48, 60) : COLOR_FAIL;
    }

    private boolean loadNightVisionEnabled() {
        return getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .getBoolean(KEY_NIGHT_VISION_ENABLED, false);
    }

    private void saveNightVisionEnabled(boolean enabled) {
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_NIGHT_VISION_ENABLED, enabled)
                .apply();
    }

    private boolean loadAiImagePreprocessingEnabled() {
        return getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .getBoolean(KEY_AI_IMAGE_PREPROCESSING_ENABLED, false);
    }

    private void saveAiImagePreprocessingEnabled(boolean enabled) {
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_AI_IMAGE_PREPROCESSING_ENABLED, enabled)
                .apply();
    }

    private void toggleAiImagePreprocessing() {
        aiImagePreprocessingEnabled = !aiImagePreprocessingEnabled;
        saveAiImagePreprocessingEnabled(aiImagePreprocessingEnabled);
        updateAiImagePreprocessingStatus();
    }

    private String resolveInitialScreen() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String pendingScreen = prefs.getString(KEY_PENDING_SCREEN_AFTER_THEME_TOGGLE, "home");
        prefs.edit().remove(KEY_PENDING_SCREEN_AFTER_THEME_TOGGLE).apply();
        if ("remoteWeb".equals(pendingScreen)) {
            return "remoteWeb";
        }
        if (isKnownScreen(pendingScreen)) {
            return pendingScreen;
        }
        return "home";
    }

    private boolean isKnownScreen(String screenName) {
        return "home".equals(screenName)
                || "setup".equals(screenName)
                || "help".equals(screenName)
                || "capabilities".equals(screenName)
                || "camera".equals(screenName)
                || "history".equals(screenName)
                || "remote".equals(screenName)
                || "calibration".equals(screenName)
                || "remoteWeb".equals(screenName);
    }

    private void toggleNightVision() {
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_NIGHT_VISION_ENABLED, !nightVisionEnabled)
                .putString(KEY_PENDING_SCREEN_AFTER_THEME_TOGGLE, currentScreenName)
                .putString(KEY_PENDING_REMOTE_WEB_URL_AFTER_THEME_TOGGLE, currentRemoteWebUrl())
                .apply();
        recreate();
    }

    private String currentRemoteWebUrl() {
        if (remoteWebView != null && remoteWebView.getUrl() != null && !remoteWebView.getUrl().isEmpty()) {
            return remoteWebView.getUrl();
        }
        String baseUrl = normalizeRemoteBaseUrl(loadRemoteBaseUrl());
        if (baseUrl.isEmpty()) {
            return "";
        }
        return baseUrl + "/remote";
    }

    private void restoreRemoteWebUrlAfterThemeToggle() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String remoteWebUrl = prefs.getString(KEY_PENDING_REMOTE_WEB_URL_AFTER_THEME_TOGGLE, "");
        prefs.edit().remove(KEY_PENDING_REMOTE_WEB_URL_AFTER_THEME_TOGGLE).apply();
        if (remoteWebView != null && remoteWebUrl != null && !remoteWebUrl.isEmpty()) {
            remoteWebView.loadUrl(remoteWebUrl);
        }
    }

    private void applyRemoteWebNightVision() {
        if (remoteWebView == null) {
            return;
        }
        String script = "(function(){"
                + "var id='pifinder-mobile-night-vision-style';"
                + "var existing=document.getElementById(id);"
                + (nightVisionEnabled
                ? "if(!existing){"
                + "var style=document.createElement('style');"
                + "style.id=id;"
                + "style.textContent='html{background:#000!important;"
                + "filter:grayscale(1) sepia(1) saturate(7) hue-rotate(315deg) "
                + "brightness(.72) contrast(1.08)!important;}body{background:#000!important;}';"
                + "document.head.appendChild(style);"
                + "}"
                : "if(existing){existing.remove();}")
                + "})();";
        remoteWebView.evaluateJavascript(script, null);
    }

    private void applySystemBars() {
        getWindow().setStatusBarColor(nightVisionEnabled ? themePanel() : themeBg());
        getWindow().setNavigationBarColor(nightVisionEnabled ? themePanel() : themeBg());
        int flags = getWindow().getDecorView().getSystemUiVisibility();
        flags &= ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        if (android.os.Build.VERSION.SDK_INT >= 26) {
            flags &= ~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        }
        getWindow().getDecorView().setSystemUiVisibility(flags);
    }

    private void requestRuntimePermissions() {
        List<String> permissions = new ArrayList<>();
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.CAMERA);
        }
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION);
        }
        if (!permissions.isEmpty()) {
            requestPermissions(permissions.toArray(new String[0]), REQUEST_PERMISSIONS);
        }
    }

    private void refreshReport() {
        StringBuilder deviceReport = new StringBuilder();
        deviceReport.append("DEVICE\n");
        deviceReport.append("Android: ").append(android.os.Build.VERSION.RELEASE)
                .append(" (API ").append(android.os.Build.VERSION.SDK_INT).append(")\n");
        deviceReport.append("Model: ").append(android.os.Build.MANUFACTURER)
                .append(" ").append(android.os.Build.MODEL).append("\n\n");
        appendLocationReport(deviceReport);

        StringBuilder sensorReport = new StringBuilder();
        appendSensorReport(sensorReport);

        StringBuilder cameraReport = new StringBuilder();
        appendCameraReport(cameraReport);

        String compatibilityReport = compatibilityCheckRun
                ? buildCompatibilityReport()
                : buildCompatibilityPlaceholder();

        latestCheckResult = buildCheckResult(compatibilityReport);
        latestProfileJson = buildProfileJson();
        latestReport = deviceReport.toString()
                + "\n"
                + "COMPATIBILITY CHECK\n"
                + compatibilityReport
                + "\n"
                + sensorReport
                + "\n"
                + cameraReport;
        compatibilityView.setText(colorizeCompatibility(compatibilityReport));
        deviceReportView.setText(deviceReport.toString());
        sensorReportView.setText(sensorReport.toString());
        cameraReportView.setText(cameraReport.toString());
        updateReadinessBadge();
        updateHomeStatus();
    }

    private String buildCheckResult(String compatibilityReport) {
        StringBuilder result = new StringBuilder();
        result.append("PiFinder Lite check result\n");
        result.append("Device: ").append(deviceLabel()).append("\n");
        result.append("Readiness: ").append(latestReadinessGrade);
        if (latestReadinessPercent >= 0) {
            result.append(" (").append(latestReadinessPercent).append("%)");
        }
        result.append("\n");

        if (!compatibilityCheckRun) {
            result.append("Status: NOT RUN\n");
            result.append("Next: Start IMU, move the phone, stop it, then run the check.\n");
            return result.toString();
        }

        result.append("PASS: ").append(countPrefixedLines(compatibilityReport, "PASS")).append("\n");
        result.append("WARN: ").append(countPrefixedLines(compatibilityReport, "WARN")).append("\n");
        result.append("FAIL: ").append(countPrefixedLines(compatibilityReport, "FAIL")).append("\n");
        result.append("NOT TESTED: ").append(countPrefixedLines(compatibilityReport, "NOT TESTED")).append("\n");
        result.append("Recommendation: ").append(recommendationText()).append("\n");
        return result.toString();
    }

    private String deviceLabel() {
        return android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL
                + " / Android " + android.os.Build.VERSION.RELEASE
                + " API " + android.os.Build.VERSION.SDK_INT;
    }

    private int countPrefixedLines(String text, String prefix) {
        int count = 0;
        String[] lines = text.split("\\n");
        for (String line : lines) {
            if (line.startsWith(prefix)) {
                count++;
            }
        }
        return count;
    }

    private String recommendationText() {
        if ("HIGH".equals(latestReadinessGrade)) {
            return "good candidate for mobile UI, GPS, IMU bridge, and experimental camera bridge.";
        }
        if ("MEDIUM".equals(latestReadinessGrade)) {
            return "usable as PiFinder companion; validate camera solving before relying on phone camera.";
        }
        if ("LOW".equals(latestReadinessGrade)) {
            return "usable mainly as UI/GPS companion; dedicated camera or IMU may be needed.";
        }
        return "run the compatibility check before sharing results.";
    }

    private String buildProfileJson() {
        try {
            JSONObject profile = new JSONObject();
            profile.put("schema", "io.pifinder.mobile.profile.v1");
            profile.put("app", appJson());
            profile.put("device", deviceJson());
            profile.put("readiness", readinessJson());
            profile.put("location", locationJson());
            profile.put("sensors", sensorsJson());
            profile.put("camera", cameraProfileJson());
            return profile.toString(2);
        } catch (JSONException e) {
            return "{\"error\":\"profile_json_failed\",\"message\":\"" + e.getMessage() + "\"}";
        }
    }

    private JSONObject appJson() throws JSONException {
        JSONObject app = new JSONObject();
        app.put("package", getPackageName());
        app.put("version_name", appVersionName());
        app.put("version_code", appVersionCode());
        return app;
    }

    private String appVersionName() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
        } catch (PackageManager.NameNotFoundException e) {
            return "unknown";
        }
    }

    private long appVersionCode() {
        try {
            if (android.os.Build.VERSION.SDK_INT >= 28) {
                return getPackageManager().getPackageInfo(getPackageName(), 0).getLongVersionCode();
            }
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionCode;
        } catch (PackageManager.NameNotFoundException e) {
            return -1;
        }
    }

    private JSONObject deviceJson() throws JSONException {
        JSONObject device = new JSONObject();
        device.put("manufacturer", android.os.Build.MANUFACTURER);
        device.put("model", android.os.Build.MODEL);
        device.put("brand", android.os.Build.BRAND);
        device.put("device", android.os.Build.DEVICE);
        device.put("android_release", android.os.Build.VERSION.RELEASE);
        device.put("android_api", android.os.Build.VERSION.SDK_INT);
        return device;
    }

    private String buildCalibrationEvidenceJson(String batchLabel) {
        try {
            JSONObject evidence = new JSONObject();
            evidence.put("schema", "pifinder-mobile-calibration-evidence-v0");
            evidence.put("created_utc", utcIso(System.currentTimeMillis()));
            evidence.put("reference_target", calibrationReferenceText());
            evidence.put("batch_label", batchLabel);
            evidence.put("expected_imu_endpoint", "/mobile/imu");
            evidence.put("remote_base_url", normalizeRemoteBaseUrl(loadRemoteBaseUrl()));
            evidence.put("app", appJson());
            evidence.put("device", deviceJson());
            evidence.put("readiness", readinessJson());
            if (latestLocation != null) {
                evidence.put("location", locationJson());
            }
            evidence.put("screen_orientation", screenOrientationName());
            return evidence.toString(2);
        } catch (JSONException e) {
            return "{\"error\":\"calibration_evidence_failed\",\"message\":\""
                    + e.getMessage() + "\"}";
        }
    }

    private String aiImuDriftAnalysisEvidenceJson() {
        try {
            JSONObject evidence = new JSONObject();
            evidence.put("schema", "pifinder-mobile-ai-imu-drift-evidence-v0");
            evidence.put("created_utc", utcIso(System.currentTimeMillis()));
            evidence.put("analysis_name", "AI IMU Drift Analysis");
            evidence.put("description", "solve-to-solve residual evidence template");
            evidence.put("expected_endpoint", "/mobile/imu_drift_analysis");
            evidence.put("diagnostic_only", true);
            evidence.put("integrator_updated", false);
            evidence.put("runtime_pointing_updated", false);
            evidence.put("remote_base_url", normalizeRemoteBaseUrl(loadRemoteBaseUrl()));
            evidence.put("reference_target", calibrationReferenceText());
            evidence.put("app", appJson());
            evidence.put("device", deviceJson());
            JSONArray cycles = new JSONArray();
            JSONObject cycle = new JSONObject();
            cycle.put("cycle_id", "cycle_1");
            cycle.put("remount_id", "mount_a");
            cycle.put("duration_s", JSONObject.NULL);
            cycle.put("predicted_final", altAzTemplateJson());
            cycle.put("solve_final", altAzTemplateJson());
            cycles.put(cycle);
            evidence.put("cycles", cycles);
            return evidence.toString(2);
        } catch (JSONException e) {
            return "{\"error\":\"ai_imu_drift_evidence_failed\",\"message\":\""
                    + e.getMessage() + "\"}";
        }
    }

    private String aiImuDriftSessionPayloadJson() {
        try {
            JSONObject payload = new JSONObject();
            payload.put("schema", "pifinder-mobile-ai-imu-drift-session-v0");
            payload.put("created_utc", utcIso(System.currentTimeMillis()));
            payload.put("diagnostic_only", true);
            payload.put("integrator_updated", false);
            payload.put("runtime_pointing_updated", false);
            payload.put("remote_base_url", normalizeRemoteBaseUrl(loadRemoteBaseUrl()));
            payload.put("reference_target", calibrationReferenceText());
            payload.put("app", appJson());
            payload.put("device", deviceJson());
            payload.put("cycles", aiImuDriftCycles);
            return payload.toString(2);
        } catch (JSONException e) {
            return "{\"error\":\"ai_imu_drift_session_failed\",\"message\":\""
                    + e.getMessage() + "\"}";
        }
    }

    private String postAiImuDriftAnalysis(String baseUrl, String payloadJson) {
        HttpURLConnection connection = null;
        try {
            byte[] body = payloadJson.getBytes(StandardCharsets.UTF_8);
            URL url = new URL(baseUrl + "/mobile/imu_drift_analysis");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(30000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }
            int status = connection.getResponseCode();
            String responseBody = readHttpBody(connection, status);
            if (status < 200 || status >= 300) {
                return "AI IMU Drift Analysis failed\nHTTP " + status + "\n" + responseErrorSummary(responseBody);
            }
            latestAiImuDriftAnalysisJson = responseBody;
            JSONObject json = new JSONObject(responseBody);
            return "AI IMU Drift Analysis\nVerdict: " + json.optString("verdict", "unknown")
                    + "\nConfidence: " + json.optString("confidence", "unknown")
                    + "\nCycles: " + json.optInt("cycle_count", 0)
                    + "\nMean error deg: " + json.optDouble("mean_error_deg", -1)
                    + "\nRecommendation: " + json.optString("recommendation", "");
        } catch (Exception e) {
            return "AI IMU Drift Analysis failed\n" + shortError(e);
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private JSONObject altAzTemplateJson() throws JSONException {
        JSONObject value = new JSONObject();
        value.put("alt_deg", JSONObject.NULL);
        value.put("az_deg", JSONObject.NULL);
        return value;
    }

    private String calibrationReferenceText() {
        if (calibrationTargetInput == null) {
            return "";
        }
        return calibrationTargetInput.getText().toString().trim();
    }

    private void updateCalibrationEvidenceJson(String batchLabel) {
        latestCalibrationEvidenceJson = buildCalibrationEvidenceJson(batchLabel);
    }

    private JSONObject readinessJson() throws JSONException {
        JSONObject readiness = new JSONObject();
        readiness.put("check_run", compatibilityCheckRun);
        readiness.put("level", latestReadinessGrade);
        readiness.put("percent", latestReadinessPercent >= 0 ? latestReadinessPercent : JSONObject.NULL);
        readiness.put("recommendation", recommendationText());
        return readiness;
    }

    private JSONObject locationJson() throws JSONException {
        JSONObject location = new JSONObject();
        location.put("service_available", locationManager != null);
        location.put("fine_permission", checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED);
        location.put("coarse_permission", checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                == PackageManager.PERMISSION_GRANTED);
        location.put("sample_available", latestLocation != null);
        if (latestLocation != null) {
            location.put("provider", latestLocation.getProvider());
            location.put("latitude", latestLocation.getLatitude());
            location.put("longitude", latestLocation.getLongitude());
            location.put("altitude_m", latestLocation.getAltitude());
            location.put("accuracy_m", latestLocation.getAccuracy());
            location.put("time_ms", latestLocation.getTime());
        }
        return location;
    }

    private JSONObject sensorsJson() throws JSONException {
        JSONObject sensors = new JSONObject();
        sensors.put("live_imu_started", liveImuStarted);
        sensors.put("live_sample_received", liveImuSampleReceived);
        sensors.put("accelerometer", sensorJson(Sensor.TYPE_ACCELEROMETER));
        sensors.put("gyroscope", sensorJson(Sensor.TYPE_GYROSCOPE));
        sensors.put("magnetometer", sensorJson(Sensor.TYPE_MAGNETIC_FIELD));
        sensors.put("rotation_vector", sensorJson(Sensor.TYPE_ROTATION_VECTOR));
        sensors.put("game_rotation_vector", sensorJson(Sensor.TYPE_GAME_ROTATION_VECTOR));
        sensors.put("gravity", sensorJson(Sensor.TYPE_GRAVITY));
        sensors.put("linear_acceleration", sensorJson(Sensor.TYPE_LINEAR_ACCELERATION));
        sensors.put("all_sensor_count", sensorManager.getSensorList(Sensor.TYPE_ALL).size());
        return sensors;
    }

    private JSONObject sensorJson(int type) throws JSONException {
        JSONObject json = new JSONObject();
        Sensor sensor = sensorManager.getDefaultSensor(type);
        json.put("available", sensor != null);
        if (sensor != null) {
            json.put("name", sensor.getName());
            json.put("vendor", sensor.getVendor());
            json.put("type", sensor.getType());
            json.put("min_delay_us", sensor.getMinDelay());
            json.put("resolution", sensor.getResolution());
            json.put("max_range", sensor.getMaximumRange());
        }
        return json;
    }

    private JSONObject cameraProfileJson() throws JSONException {
        JSONObject camera = new JSONObject();
        camera.put("camera_permission", checkSelfPermission(Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED);
        camera.put("back_camera_available", hasBackCamera());
        camera.put("manual_back_camera_available", hasManualBackCamera());
        camera.put("raw_back_camera_available", hasRawBackCamera());

        JSONArray cameras = new JSONArray();
        try {
            for (String cameraId : cameraManager.getCameraIdList()) {
                cameras.put(cameraIdProfileJson(cameraId));
            }
        } catch (CameraAccessException | SecurityException e) {
            camera.put("error", e.getMessage());
        }
        camera.put("cameras", cameras);
        return camera;
    }

    private JSONObject cameraIdProfileJson(String cameraId) throws CameraAccessException, JSONException {
        CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
        JSONObject camera = new JSONObject();
        Integer lensFacing = c.get(CameraCharacteristics.LENS_FACING);
        int[] caps = c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
        camera.put("id", cameraId);
        camera.put("facing", lensFacingName(lensFacing));
        camera.put("manual_sensor", hasCapability(caps,
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR));
        camera.put("raw", hasCapability(caps,
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW));
        camera.put("logical_multi_camera", hasCapability(caps,
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_LOGICAL_MULTI_CAMERA));
        camera.put("capabilities", intArrayJson(caps));

        Range<Long> exposureRange = c.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        if (exposureRange != null) {
            JSONObject exposure = new JSONObject();
            exposure.put("min_ns", exposureRange.getLower());
            exposure.put("max_ns", exposureRange.getUpper());
            camera.put("exposure_time_range", exposure);
        }

        Range<Integer> isoRange = c.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        if (isoRange != null) {
            JSONObject iso = new JSONObject();
            iso.put("min", isoRange.getLower());
            iso.put("max", isoRange.getUpper());
            camera.put("iso_range", iso);
        }

        Float minFocus = c.get(CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE);
        camera.put("minimum_focus_distance_diopters", minFocus != null ? minFocus : JSONObject.NULL);
        camera.put("focal_lengths_mm", floatArrayJson(c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS)));

        SizeF sensorSize = c.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
        if (sensorSize != null) {
            JSONObject size = new JSONObject();
            size.put("width_mm", sensorSize.getWidth());
            size.put("height_mm", sensorSize.getHeight());
            camera.put("sensor_physical_size", size);
        }

        StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        if (map != null) {
            JSONObject outputs = new JSONObject();
            outputs.put("jpeg", sizeArrayJson(map.getOutputSizes(256)));
            outputs.put("raw_sensor", sizeArrayJson(map.getOutputSizes(32)));
            outputs.put("yuv_420_888", sizeArrayJson(map.getOutputSizes(35)));
            camera.put("output_sizes", outputs);
        }
        camera.put("hardware_level", hardwareLevelName(valueOrMinusOne(
                c.get(CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL))));
        return camera;
    }

    private JSONArray intArrayJson(int[] values) {
        JSONArray array = new JSONArray();
        if (values != null) {
            for (int value : values) {
                array.put(value);
            }
        }
        return array;
    }

    private JSONArray floatArrayJson(float[] values) {
        JSONArray array = new JSONArray();
        if (values != null) {
            for (float value : values) {
                try {
                    array.put(value);
                } catch (JSONException ignored) {
                }
            }
        }
        return array;
    }

    private JSONArray sizeArrayJson(Size[] sizes) throws JSONException {
        JSONArray array = new JSONArray();
        if (sizes != null) {
            for (Size size : sizes) {
                JSONObject item = new JSONObject();
                item.put("width", size.getWidth());
                item.put("height", size.getHeight());
                array.put(item);
            }
        }
        return array;
    }

    private void saveCheckHistoryRecord() {
        try {
            JSONArray history = loadCheckHistory();
            JSONArray updated = new JSONArray();
            updated.put(checkHistoryRecordJson());
            for (int i = 0; i < history.length() && updated.length() < MAX_HISTORY_RECORDS; i++) {
                updated.put(history.getJSONObject(i));
            }
            prefs().edit().putString(KEY_CHECK_HISTORY, updated.toString()).apply();
            latestHistoryJson = updated.toString(2);
        } catch (JSONException e) {
            Toast.makeText(this, "Could not save check history", Toast.LENGTH_SHORT).show();
        }
    }

    private JSONObject checkHistoryRecordJson() throws JSONException {
        JSONObject record = new JSONObject();
        record.put("timestamp_ms", System.currentTimeMillis());
        record.put("timestamp_local", new SimpleDateFormat(
                "yyyy-MM-dd HH:mm:ss",
                Locale.US
        ).format(new java.util.Date()));
        record.put("app", appJson());
        record.put("device", deviceJson());
        record.put("readiness", readinessJson());
        record.put("check_result", latestCheckResult);
        record.put("profile", new JSONObject(latestProfileJson));
        return record;
    }

    private JSONArray loadCheckHistory() {
        String raw = prefs().getString(KEY_CHECK_HISTORY, "[]");
        try {
            return new JSONArray(raw);
        } catch (JSONException e) {
            return new JSONArray();
        }
    }

    private SharedPreferences prefs() {
        return getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
    }

    private void updateHistoryView() {
        JSONArray history = loadCheckHistory();
        latestHistoryJson = history.toString();
        if (historyView == null) {
            return;
        }
        if (history.length() == 0) {
            historyView.setText("No saved checks yet.\nRun Check to save the first history record.");
            return;
        }

        StringBuilder text = new StringBuilder();
        text.append("Saved checks: ").append(history.length()).append("\n\n");
        int shown = Math.min(history.length(), 5);
        for (int i = 0; i < shown; i++) {
            JSONObject record = history.optJSONObject(i);
            if (record == null) {
                continue;
            }
            JSONObject readiness = record.optJSONObject("readiness");
            JSONObject device = record.optJSONObject("device");
            text.append(record.optString("timestamp_local", "unknown time")).append("\n");
            if (readiness != null) {
                text.append("Readiness: ")
                        .append(readiness.optString("level", "unknown"))
                        .append(" (")
                        .append(readiness.optString("percent", "n/a"))
                        .append("%)\n");
            }
            if (device != null) {
                text.append("Device: ")
                        .append(device.optString("manufacturer", "unknown"))
                        .append(" ")
                        .append(device.optString("model", "unknown"))
                        .append("\n");
            }
            if (i < shown - 1) {
                text.append("\n");
            }
        }
        historyView.setText(text.toString());
    }

    private String buildCompatibilityPlaceholder() {
        latestReadinessGrade = "NOT RUN";
        latestReadinessPercent = -1;
        return "Status: NOT RUN\n\n"
                + "Start IMU, move the phone gently, press STOP, then RUN CHECK.";
    }

    private SpannableString colorizeCompatibility(String report) {
        SpannableString styled = new SpannableString(report);
        colorToken(styled, report, "PASS", themePass());
        colorToken(styled, report, "WARN", themeWarn());
        colorToken(styled, report, "FAIL", themeFail());
        colorToken(styled, report, "HIGH", themePass());
        colorToken(styled, report, "MEDIUM", themeWarn());
        colorToken(styled, report, "LOW", themeFail());
        colorToken(styled, report, "NOT RUN", themeMuted());
        colorToken(styled, report, "NOT TESTED", themeMuted());
        colorToken(styled, report, "RECOMMENDATION", themeAccent());
        boldToken(styled, report, "RECOMMENDATION");
        return styled;
    }

    private void colorToken(SpannableString styled, String text, String token, int color) {
        int start = text.indexOf(token);
        while (start >= 0) {
            styled.setSpan(
                    new ForegroundColorSpan(color),
                    start,
                    start + token.length(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
            start = text.indexOf(token, start + token.length());
        }
    }

    private void boldToken(SpannableString styled, String text, String token) {
        int start = text.indexOf(token);
        while (start >= 0) {
            styled.setSpan(
                    new StyleSpan(Typeface.BOLD),
                    start,
                    start + token.length(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
            start = text.indexOf(token, start + token.length());
        }
    }

    private void updateReadinessBadge() {
        if (readinessBadgeView == null) {
            return;
        }
        if (!compatibilityCheckRun) {
            readinessBadgeView.setText("NOT RUN\nReady for first check");
            readinessBadgeView.setTextColor(themeMuted());
            readinessBadgeView.setBackground(roundedRect(themePanel(), themeHairline(), 1, 18));
            return;
        }

        int color = readinessColor();
        String detail;
        if ("HIGH".equals(latestReadinessGrade)) {
            detail = "Strong PiFinder Lite candidate";
        } else if ("MEDIUM".equals(latestReadinessGrade)) {
            detail = "Usable companion; validate camera at night";
        } else {
            detail = "Best as UI/GPS companion for now";
        }
        readinessBadgeView.setText(
                latestReadinessGrade + "\n"
                        + latestReadinessPercent + "%\n"
                        + detail
        );
        readinessBadgeView.setTextColor(themeText());
        readinessBadgeView.setBackground(roundedRect(themePanel(), color, 2, 18));
    }

    private void updateHomeStatus() {
        if (homeStatusView == null) {
            return;
        }
        if (!compatibilityCheckRun) {
            homeStatusView.setText("Ready for field setup\nStart with PiFinder Remote if the Raspberry is running, or use Phone setup for camera and calibration tools.");
            homeStatusView.setTextColor(themeMuted());
            homeStatusView.setBackground(roundedRect(themePanel(), themeHairline(), 1, 18));
            return;
        }
        homeStatusView.setText(
                "Readiness: " + latestReadinessGrade + " (" + latestReadinessPercent + "%)\n"
                        + "Next: open PiFinder Remote, Camera Lab, or Calibration."
        );
        homeStatusView.setTextColor(themeText());
        homeStatusView.setBackground(roundedRect(themePanel(), readinessColor(), 1, 18));
    }

    private int readinessColor() {
        if ("HIGH".equals(latestReadinessGrade)) {
            return themePass();
        }
        if ("MEDIUM".equals(latestReadinessGrade)) {
            return themeWarn();
        }
        if ("LOW".equals(latestReadinessGrade)) {
            return themeFail();
        }
        return themeMuted();
    }

    private void updateCapabilityAction(String text) {
        if (capabilityActionView != null) {
            capabilityActionView.setText("Next action\n" + text);
        }
    }

    private void updateCameraFolderStatus() {
        if (cameraFolderStatusView == null) {
            return;
        }
        if (outputTreeUri == null) {
            cameraFolderStatusView.setText("Save folder: not selected\nChoose a folder before running the field diagnostic.");
            cameraFolderStatusView.setTextColor(themeWarn());
            cameraFolderStatusView.setBackground(roundedRect(themePanel(), themeWarn(), 1, 18));
            return;
        }
        cameraFolderStatusView.setText("Save folder: selected\n" + outputTreeUri);
        cameraFolderStatusView.setTextColor(themeText());
        cameraFolderStatusView.setBackground(roundedRect(themePanel(), themePass(), 1, 18));
    }

    private String buildCompatibilityReport() {
        int score = 0;
        int maxScore = 9;
        List<String> lines = new ArrayList<>();

        Sensor accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        Sensor gyroscope = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        Sensor magnetometer = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
        Sensor rotationVector = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
        Sensor gameRotationVector = sensorManager.getDefaultSensor(Sensor.TYPE_GAME_ROTATION_VECTOR);

        if (accelerometer != null && gyroscope != null) {
            score++;
            lines.add("PASS  Motion core: accelerometer + gyroscope available");
        } else {
            lines.add("FAIL  Motion core: accelerometer/gyroscope incomplete");
        }

        if (rotationVector != null || gameRotationVector != null) {
            score++;
            lines.add("PASS  Orientation: rotation vector available");
        } else {
            lines.add("WARN  Orientation: no Android fused rotation vector");
        }

        if (magnetometer != null) {
            score++;
            lines.add("PASS  Compass: magnetometer available");
        } else {
            lines.add("WARN  Compass: magnetometer unavailable");
        }

        if (hasBackCamera()) {
            score++;
            lines.add("PASS  Camera: rear camera available");
        } else {
            lines.add("FAIL  Camera: no rear camera exposed");
        }

        if (hasManualBackCamera()) {
            score++;
            lines.add("PASS  Camera2 manual: exposure/ISO control exposed");
        } else {
            lines.add("WARN  Camera2 manual: limited manual controls");
        }

        if (hasRawBackCamera()) {
            score++;
            lines.add("PASS  RAW: raw capture exposed");
        } else {
            lines.add("WARN  RAW: no raw capture exposed");
        }

        if (locationManager != null) {
            score++;
            lines.add("PASS  Location: Android location service available");
        } else {
            lines.add("WARN  Location: Android location service unavailable");
        }

        if (!liveImuStarted && !liveImuEverSampleReceived) {
            lines.add("NOT TESTED  Live IMU stream: press START IMU before checking dynamic sensor behavior");
        } else if (liveImuSampleReceived || liveImuEverSampleReceived) {
            score++;
            lines.add("PASS  Live IMU stream: sensor samples received");
        } else {
            lines.add("FAIL  Live IMU stream: no live sensor samples received");
        }

        if (latestLocation != null) {
            score++;
            lines.add("PASS  GPS sample: live or cached location available");
        } else {
            lines.add("NOT TESTED  GPS sample: no location sample yet");
        }

        int percent = Math.round((score * 100f) / maxScore);
        String grade;
        if (percent >= 85) {
            grade = "HIGH";
        } else if (percent >= 60) {
            grade = "MEDIUM";
        } else {
            grade = "LOW";
        }
        latestReadinessGrade = grade;
        latestReadinessPercent = percent;

        StringBuilder report = new StringBuilder();
        report.append("PiFinder Lite readiness: ").append(grade)
                .append(" (").append(percent).append("%)\n\n");
        for (String line : lines) {
            report.append(line).append("\n");
        }
        report.append("\nRECOMMENDATION\n");
        report.append(recommendationText());
        return report.toString();
    }

    private void appendSensorReport(StringBuilder report) {
        report.append("SENSORS\n");
        appendSensorSummary(report, Sensor.TYPE_ACCELEROMETER, "Accelerometer");
        appendSensorSummary(report, Sensor.TYPE_GYROSCOPE, "Gyroscope");
        appendSensorSummary(report, Sensor.TYPE_MAGNETIC_FIELD, "Magnetometer");
        appendSensorSummary(report, Sensor.TYPE_ROTATION_VECTOR, "Rotation vector");
        appendSensorSummary(report, Sensor.TYPE_GAME_ROTATION_VECTOR, "Game rotation vector");
        appendSensorSummary(report, Sensor.TYPE_GRAVITY, "Gravity");
        appendSensorSummary(report, Sensor.TYPE_LINEAR_ACCELERATION, "Linear acceleration");

        report.append("\nAll sensors exposed: ").append(sensorManager.getSensorList(Sensor.TYPE_ALL).size()).append("\n");
        for (Sensor sensor : sensorManager.getSensorList(Sensor.TYPE_ALL)) {
            report.append("- ").append(sensor.getName())
                    .append(" | type=").append(sensor.getType())
                    .append(" | vendor=").append(sensor.getVendor())
                    .append(" | minDelayUs=").append(sensor.getMinDelay())
                    .append(" | resolution=").append(sensor.getResolution())
                    .append(" | maxRange=").append(sensor.getMaximumRange())
                    .append("\n");
        }
        report.append("\n");
    }

    private void appendSensorSummary(StringBuilder report, int type, String label) {
        Sensor sensor = sensorManager.getDefaultSensor(type);
        report.append(label).append(": ");
        if (sensor == null) {
            report.append("not available\n");
            return;
        }
        report.append(sensor.getName())
                .append(" | minDelayUs=").append(sensor.getMinDelay())
                .append(" | maxRateHz~=").append(sensor.getMinDelay() > 0 ? 1_000_000 / sensor.getMinDelay() : "on-change")
                .append("\n");
    }

    private void appendLocationReport(StringBuilder report) {
        report.append("LOCATION\n");
        if (latestLocation == null) {
            report.append("No live location sample yet. Tap Start IMU and grant location permission.\n\n");
            return;
        }
        report.append("Provider: ").append(latestLocation.getProvider()).append("\n");
        report.append("Lat/Lon: ").append(format(latestLocation.getLatitude()))
                .append(", ").append(format(latestLocation.getLongitude())).append("\n");
        report.append("Altitude: ").append(format(latestLocation.getAltitude())).append(" m\n");
        report.append("Accuracy: ").append(format(latestLocation.getAccuracy())).append(" m\n\n");
    }

    private void appendCameraReport(StringBuilder report) {
        report.append("CAMERA2\n");
        try {
            for (String cameraId : cameraManager.getCameraIdList()) {
                CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
                report.append("Camera ").append(cameraId).append("\n");

                Integer lensFacing = c.get(CameraCharacteristics.LENS_FACING);
                report.append("  Facing: ").append(lensFacingName(lensFacing)).append("\n");

                int[] caps = c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
                report.append("  Capabilities: ").append(capabilityNames(caps)).append("\n");
                report.append("  Manual sensor: ").append(hasCapability(caps, CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR)).append("\n");
                report.append("  RAW: ").append(hasCapability(caps, CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW)).append("\n");
                report.append("  Logical multi-camera: ").append(hasCapability(caps, CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_LOGICAL_MULTI_CAMERA)).append("\n");

                Range<Long> exposureRange = c.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
                report.append("  Exposure ns: ").append(exposureRange != null ? exposureRange : "unknown").append("\n");

                Range<Integer> isoRange = c.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
                report.append("  ISO range: ").append(isoRange != null ? isoRange : "unknown").append("\n");

                Float minFocus = c.get(CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE);
                report.append("  Minimum focus distance diopters: ").append(minFocus != null ? minFocus : "unknown").append("\n");
                report.append("  Infinity focus value: 0.0 diopters when manual focus is supported\n");

                float[] focalLengths = c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
                report.append("  Focal lengths mm: ").append(focalLengths != null ? Arrays.toString(focalLengths) : "unknown").append("\n");

                SizeF sensorSize = c.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
                report.append("  Sensor physical size mm: ").append(sensorSize != null ? sensorSize : "unknown").append("\n");

                StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
                if (map != null) {
                    report.append("  Output formats: ").append(Arrays.toString(map.getOutputFormats())).append("\n");
                    appendSizes(report, "RAW_SENSOR sizes", map.getOutputSizes(32));
                    appendSizes(report, "RAW10 sizes", map.getOutputSizes(37));
                    appendSizes(report, "RAW12 sizes", map.getOutputSizes(38));
                    appendSizes(report, "JPEG sizes", map.getOutputSizes(256));
                    appendSizes(report, "YUV_420_888 sizes", map.getOutputSizes(35));
                }

                Range<Integer>[] fpsRanges = c.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES);
                report.append("  AE target FPS ranges: ").append(fpsRanges != null ? Arrays.toString(fpsRanges) : "unknown").append("\n");

                int[] aeModes = c.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_MODES);
                report.append("  AE modes: ").append(aeModeNames(aeModes)).append("\n");

                int[] afModes = c.get(CameraCharacteristics.CONTROL_AF_AVAILABLE_MODES);
                report.append("  AF modes: ").append(afModeNames(afModes)).append("\n");

                int[] sceneModes = c.get(CameraCharacteristics.CONTROL_AVAILABLE_SCENE_MODES);
                report.append("  Scene modes: ").append(sceneModeNames(sceneModes)).append("\n");

                int[] effects = c.get(CameraCharacteristics.CONTROL_AVAILABLE_EFFECTS);
                report.append("  Effects: ").append(Arrays.toString(effects != null ? effects : new int[0])).append("\n");

                int[] videoStabModes = c.get(CameraCharacteristics.CONTROL_AVAILABLE_VIDEO_STABILIZATION_MODES);
                report.append("  Video stabilization modes: ").append(Arrays.toString(videoStabModes != null ? videoStabModes : new int[0])).append("\n");

                int[] opticalStabModes = c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION);
                report.append("  Optical stabilization modes: ").append(Arrays.toString(opticalStabModes != null ? opticalStabModes : new int[0])).append("\n");

                int[] hardwareLevel = new int[] {
                        valueOrMinusOne(c.get(CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL))
                };
                report.append("  Hardware level: ").append(hardwareLevelName(hardwareLevel[0])).append("\n");

                appendKeyNames(report, "Available capture request keys", c.getAvailableCaptureRequestKeys());
                appendKeyNames(report, "Available capture result keys", c.getAvailableCaptureResultKeys());
                appendKeyNames(report, "Available session keys", c.getAvailableSessionKeys());
                appendExtensionReport(report, cameraId);
                appendPhysicalCameraReport(report, c);
                report.append("\n");
            }
        } catch (CameraAccessException | SecurityException e) {
            report.append("Camera report failed: ").append(e.getMessage()).append("\n\n");
        }
    }

    private void startLiveSensors() {
        stopLiveSensors();
        registerLiveSensor(Sensor.TYPE_ACCELEROMETER);
        registerLiveSensor(Sensor.TYPE_GYROSCOPE);
        registerLiveSensor(Sensor.TYPE_MAGNETIC_FIELD);
        registerLiveSensor(Sensor.TYPE_ROTATION_VECTOR);
        registerLiveSensor(Sensor.TYPE_GAME_ROTATION_VECTOR);
        startLocation();
        liveImuStarted = true;
        liveImuSampleReceived = false;
        if (startImuButton != null) {
            startImuButton.setText("IMU RUNNING");
            startImuButton.setBackground(roundedRect(themePrimary(), themeAccent(), 1, 18));
        }
        updateCapabilityAction("IMU is running. Move the phone gently, then stop and run the check.");
        liveView.setText("Live sensors started. Move the phone slowly to inspect updates.");
    }

    private void registerLiveSensor(int type) {
        Sensor sensor = sensorManager.getDefaultSensor(type);
        if (sensor == null) {
            return;
        }
        sensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
        activeSensors.add(sensor);
    }

    private void stopLiveSensors() {
        sensorManager.unregisterListener(this);
        activeSensors.clear();
        liveImuStarted = false;
        liveSensorText.setLength(0);
        if (startImuButton != null) {
            startImuButton.setText("Start IMU");
            startImuButton.setBackground(roundedRect(themeSecondary(), themeSecondaryStroke(), 1, 18));
        }
        if (liveView != null) {
            liveView.setText("Live sensors stopped.");
        }
        if (capabilityActionView != null) {
            updateCapabilityAction("Run the check to calculate readiness.");
        }
    }

    @SuppressLint("MissingPermission")
    private void startLocation() {
        if (!hasLocationPermission()) {
            return;
        }
        try {
            locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 0, this);
            Location last = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            if (last != null) {
                latestLocation = last;
            }
        } catch (IllegalArgumentException | SecurityException ignored) {
        }
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @SuppressLint("MissingPermission")
    private Location bestAvailableLocation() {
        Location best = latestLocation;
        if (!hasLocationPermission() || locationManager == null) {
            return best;
        }
        best = newerLocation(best, lastKnownLocation(LocationManager.GPS_PROVIDER));
        best = newerLocation(best, lastKnownLocation(LocationManager.NETWORK_PROVIDER));
        return best;
    }

    @SuppressLint("MissingPermission")
    private boolean requestSingleLocationForSend() {
        if (!hasLocationPermission() || locationManager == null) {
            return false;
        }
        boolean requested = false;
        requested = requestSingleLocationProvider(LocationManager.GPS_PROVIDER) || requested;
        requested = requestSingleLocationProvider(LocationManager.NETWORK_PROVIDER) || requested;
        return requested;
    }

    @SuppressLint("MissingPermission")
    private Location lastKnownLocation(String provider) {
        try {
            if (!locationManager.isProviderEnabled(provider)) {
                return null;
            }
            return locationManager.getLastKnownLocation(provider);
        } catch (IllegalArgumentException | SecurityException e) {
            return null;
        }
    }

    @SuppressLint("MissingPermission")
    private boolean requestSingleLocationProvider(String provider) {
        try {
            if (!locationManager.isProviderEnabled(provider)) {
                return false;
            }
            locationManager.requestSingleUpdate(provider, this, null);
            return true;
        } catch (IllegalArgumentException | SecurityException e) {
            return false;
        }
    }

    private Location newerLocation(Location current, Location candidate) {
        if (candidate == null) {
            return current;
        }
        if (current == null || candidate.getTime() > current.getTime()) {
            return candidate;
        }
        return current;
    }

    private String utcIso(long timeMs) {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US);
        formatter.setTimeZone(TimeZone.getTimeZone("UTC"));
        return formatter.format(new Date(timeMs));
    }

    private boolean registerImuBatchSensor(int type) {
        Sensor sensor = sensorManager.getDefaultSensor(type);
        if (sensor == null) {
            return false;
        }
        sensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
        imuBatchSensors.add(sensor);
        return true;
    }

    private void stopImuBatchCapture() {
        for (Sensor sensor : imuBatchSensors) {
            sensorManager.unregisterListener(this, sensor);
        }
        imuBatchSensors.clear();
        imuBatchCaptureActive = false;
    }

    private void clearImuBatchSamples() {
        while (imuBatchSamples.length() > 0) {
            imuBatchSamples.remove(0);
        }
    }

    private void maybeCaptureImuSample(SensorEvent event) {
        if (!imuBatchCaptureActive) {
            return;
        }
        int type = event.sensor.getType();
        if (type != Sensor.TYPE_ROTATION_VECTOR
                && type != Sensor.TYPE_GAME_ROTATION_VECTOR) {
            return;
        }
        try {
            JSONObject sample = new JSONObject();
            sample.put("sensor", sensorNameForPayload(type));
            sample.put("t_android_ns", event.timestamp);
            sample.put("accuracy", event.accuracy);
            sample.put("time_utc", utcIso(System.currentTimeMillis()));
            JSONArray values = new JSONArray();
            for (float value : event.values) {
                values.put(value);
            }
            sample.put("values", values);
            imuBatchSamples.put(sample);
        } catch (JSONException ignored) {
        }
        if (imuBatchSamples.length() >= IMU_BATCH_MAX_SAMPLES) {
            finishImuBatchCapture("max_samples");
        }
    }

    private void finishImuBatchCapture(String reason) {
        if (!imuBatchCaptureActive) {
            return;
        }
        stopImuBatchCapture();
        if (pendingImuBaseUrl == null || pendingImuBaseUrl.length() == 0) {
            return;
        }
        if (imuBatchSamples.length() == 0) {
            String failedLabel = pendingImuBatchLabel;
            pendingImuBaseUrl = "";
            pendingImuBatchLabel = "diagnostic";
            String message = "IMU unavailable\nNo orientation samples arrived.";
            updateRemoteStatus(message);
            if (isCalibrationBatchLabel(failedLabel)) {
                updateCalibrationStatus(message);
            }
            return;
        }
        String baseUrl = pendingImuBaseUrl;
        String batchLabel = pendingImuBatchLabel;
        pendingImuBaseUrl = "";
        pendingImuBatchLabel = "diagnostic";
        try {
            String imuJson = buildImuBatchJson(imuBatchSamples, batchLabel);
            updateRemoteStatus(
                    "Captured IMU batch\nLabel: " + batchLabel
                            + "\nSamples: " + imuBatchSamples.length()
                            + "\nReason: " + reason
            );
            postImuBatchToPiFinder(baseUrl, imuJson, batchLabel);
        } catch (JSONException e) {
            String message = "IMU send failed\nCould not build IMU JSON.";
            updateRemoteStatus(message);
            if (isCalibrationBatchLabel(batchLabel)) {
                updateCalibrationStatus(message);
            }
        } finally {
            clearImuBatchSamples();
        }
    }

    private String sensorNameForPayload(int type) {
        if (type == Sensor.TYPE_ROTATION_VECTOR) {
            return "rotation_vector";
        }
        if (type == Sensor.TYPE_GAME_ROTATION_VECTOR) {
            return "game_rotation_vector";
        }
        return "sensor_" + type;
    }

    private void stopLocation() {
        try {
            locationManager.removeUpdates(this);
        } catch (SecurityException ignored) {
        }
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        rememberEnvironmentSensorSample(event);
        liveImuSampleReceived = true;
        liveImuEverSampleReceived = true;
        maybeCaptureImuSample(event);
        liveSensorText.setLength(0);
        liveSensorText.append("LIVE SENSOR SAMPLE\n");
        liveSensorText.append(sensorName(event.sensor.getType())).append(": ");
        liveSensorText.append(formatValues(event.values)).append("\n");
        liveSensorText.append("Timestamp ns: ").append(event.timestamp).append("\n");
        if (event.sensor.getType() == Sensor.TYPE_ROTATION_VECTOR
                || event.sensor.getType() == Sensor.TYPE_GAME_ROTATION_VECTOR) {
            float[] quat = new float[4];
            SensorManager.getQuaternionFromVector(quat, event.values);
            liveSensorText.append("Quaternion [w,x,y,z]: ").append(formatValues(quat)).append("\n");
            rememberDeviceOrientation(event.values);
        }
        if (latestLocation != null) {
            liveSensorText.append("GPS: ")
                    .append(format(latestLocation.getLatitude())).append(", ")
                    .append(format(latestLocation.getLongitude())).append(" +/- ")
                    .append(format(latestLocation.getAccuracy())).append(" m\n");
        }
        liveSensorText.append("\nActive sensors: ").append(activeSensors.size());
        liveView.setText(liveSensorText.toString());
    }

    private void rememberDeviceOrientation(float[] rotationVector) {
        try {
            float[] rotationMatrix = new float[9];
            float[] orientation = new float[3];
            SensorManager.getRotationMatrixFromVector(rotationMatrix, rotationVector);
            SensorManager.getOrientation(rotationMatrix, orientation);
            latestDeviceOrientationDeg = new float[]{
                    (float) Math.toDegrees(orientation[0]),
                    (float) Math.toDegrees(orientation[1]),
                    (float) Math.toDegrees(orientation[2])
            };
        } catch (RuntimeException ignored) {
        }
    }

    private void rememberEnvironmentSensorSample(SensorEvent event) {
        if (event.values == null || event.values.length == 0) {
            return;
        }
        int type = event.sensor.getType();
        if (type == Sensor.TYPE_LIGHT) {
            latestAmbientLightLux = event.values[0];
            latestAmbientLightAtMs = System.currentTimeMillis();
        } else if (type == Sensor.TYPE_PRESSURE) {
            latestPressureHpa = event.values[0];
            latestPressureAtMs = System.currentTimeMillis();
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }

    @Override
    public void onLocationChanged(Location location) {
        latestLocation = location;
        if (pendingGpsBaseUrl != null && pendingGpsBaseUrl.length() > 0) {
            String baseUrl = pendingGpsBaseUrl;
            pendingGpsBaseUrl = "";
            postLocationToPiFinder(baseUrl, location);
        }
        refreshReport();
    }

    private void copyCheckResult() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder check result", latestCheckResult));
        Toast.makeText(this, "Check result copied", Toast.LENGTH_SHORT).show();
    }

    private void copyTechReport() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder tech report", latestReport));
        Toast.makeText(this, "Tech report copied", Toast.LENGTH_SHORT).show();
    }

    private void copyProfileJson() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder mobile profile JSON", latestProfileJson));
        Toast.makeText(this, "Profile JSON copied", Toast.LENGTH_SHORT).show();
    }

    private void copyHistoryJson() {
        updateHistoryView();
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder check history JSON", latestHistoryJson));
        Toast.makeText(this, "Check history copied", Toast.LENGTH_SHORT).show();
    }

    private void copyCalibrationEvidence() {
        updateCalibrationEvidenceJson("mounted_reference");
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText(
                "PiFinder calibration evidence JSON",
                latestCalibrationEvidenceJson
        ));
        updateCalibrationStatus("Evidence copied\nReference: " + calibrationReferenceText());
        Toast.makeText(this, "Calibration evidence copied", Toast.LENGTH_SHORT).show();
    }

    private void copyAiImuDriftAnalysisEvidence() {
        String text = aiImuDriftCycles.length() > 0 ? aiImuDriftSessionPayloadJson() : aiImuDriftAnalysisEvidenceJson();
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText(
                "PiFinder AI IMU Drift Analysis evidence JSON",
                text
        ));
        Toast.makeText(this, "AI IMU drift evidence copied", Toast.LENGTH_SHORT).show();
    }

    private void pickOutputFolder() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        startActivityForResult(intent, REQUEST_OUTPUT_DIR);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_OUTPUT_DIR && resultCode == RESULT_OK && data != null) {
            outputTreeUri = data.getData();
            int flags = data.getFlags()
                    & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            if (outputTreeUri != null) {
                getContentResolver().takePersistableUriPermission(outputTreeUri, flags);
                updateCameraFolderStatus();
                updatePhase2NightTestWizard("review");
                captureView.setText("Save folder selected:\n" + outputTreeUri);
            }
        }
    }

    private void startCaptureTest(String testName, int format) {
        if (outputTreeUri == null) {
            updateCameraFolderStatus();
            Toast.makeText(this, "Choose a save folder first", Toast.LENGTH_SHORT).show();
            pickOutputFolder();
            return;
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestRuntimePermissions();
            return;
        }
        captureTestName = testName;
        captureFormat = format;
        captureView.setText("Preparing " + testName + "...");
        startCameraThread();
        if ("camera_sweep".equals(testName)) {
            try {
                cameraSweepIds.clear();
                cameraSweepIds.addAll(backCameraIds());
                cameraSweepIndex = 0;
                if (cameraSweepIds.isEmpty()) {
                    captureView.setText("No back cameras found.");
                    return;
                }
            } catch (CameraAccessException e) {
                captureView.setText("Camera sweep setup failed: " + e.getMessage());
                return;
            }
        }
        openCaptureCamera();
    }

    private void startCameraThread() {
        if (cameraThread != null) {
            return;
        }
        cameraThread = new HandlerThread("PiFinderCapture");
        cameraThread.start();
        cameraHandler = new Handler(cameraThread.getLooper());
    }

    private void stopCameraThread() {
        if (cameraThread == null) {
            return;
        }
        cameraThread.quitSafely();
        try {
            cameraThread.join();
        } catch (InterruptedException ignored) {
        }
        cameraThread = null;
        cameraHandler = null;
    }

    @SuppressLint("MissingPermission")
    private void openCaptureCamera() {
        try {
            String cameraId = chooseCaptureCameraId();
            CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
            activeCaptureCameraId = cameraId;
            captureJpegOrientation = jpegOrientationFor(c);
            Size captureSize = chooseCaptureSize(c, captureFormat);
            if (captureSize == null) {
                captureView.setText("No capture size available for camera " + cameraId + " format " + captureFormat);
                return;
            }
            activeCaptureSize = captureSize;

            captureReader = ImageReader.newInstance(
                    captureSize.getWidth(),
                    captureSize.getHeight(),
                    captureFormat,
                    Math.max(Math.max(BURST_FRAMES, RAW_BURST_FRAMES), SOLVE_CANDIDATE_FRAMES)
            );
            captureReader.setOnImageAvailableListener(reader -> saveNextImage(reader), cameraHandler);

            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new java.util.Date());
            captureRunPrefix = "pifinder_" + captureTestName + "_" + timestamp;
            try {
                captureDirDocumentId = createRunDirectory(captureRunPrefix);
            } catch (IOException e) {
                captureView.setText("Could not create output folder: " + e.getMessage());
                return;
            }
            captureFrameCount = frameCountForTest(captureTestName);
            pendingFrames = captureFrameCount;
            savedFrames = 0;
            failedFrames = 0;
            completedFrames = 0;
            queuedRequests = new ArrayList<>();
            queuedLabels.clear();
            solveCandidateFrames.clear();
            selectedSolveCandidateFrame = null;
            latestSolveCandidateRankingSummary = "";
            captureMetadata.setLength(0);
            appendCaptureMetadataHeader(cameraId, c, captureSize, timestamp);

            cameraManager.openCamera(cameraId, new CameraDevice.StateCallback() {
                @Override
                public void onOpened(CameraDevice camera) {
                    captureCamera = camera;
                    createCaptureSession(camera, c);
                }

                @Override
                public void onDisconnected(CameraDevice camera) {
                    camera.close();
                    runOnUiThread(() -> captureView.setText("Camera disconnected."));
                }

                @Override
                public void onError(CameraDevice camera, int error) {
                    camera.close();
                    runOnUiThread(() -> captureView.setText("Camera error: " + error));
                }
            }, cameraHandler);
        } catch (CameraAccessException | SecurityException e) {
            captureView.setText("Open camera failed: " + e.getMessage());
        }
    }

    private String chooseCaptureCameraId() throws CameraAccessException {
        if ("camera_sweep".equals(captureTestName)) {
            captureCameraSelection = "camera_sweep_index_" + cameraSweepIndex;
            return cameraSweepIds.get(cameraSweepIndex);
        }
        if ("solve_candidate_burst".equals(captureTestName)) {
            return chooseSolveCandidateCameraId();
        }
        captureCameraSelection = "default_back_camera";
        return chooseBackCameraId();
    }

    private String chooseSolveCandidateCameraId() throws CameraAccessException {
        if (RECOMMENDED_SOLVE_DEVICE.equalsIgnoreCase(android.os.Build.MODEL)
                && isBackCamera(RECOMMENDED_SOLVE_CAMERA_ID)) {
            captureCameraSelection = "recommended_" + RECOMMENDED_SOLVE_DEVICE
                    + "_camera_" + RECOMMENDED_SOLVE_CAMERA_ID;
            return RECOMMENDED_SOLVE_CAMERA_ID;
        }
        String fallback = chooseBackCameraId();
        captureCameraSelection = "recommended_camera_unavailable_fallback_" + fallback;
        return fallback;
    }

    private boolean isBackCamera(String cameraId) throws CameraAccessException {
        for (String availableCameraId : cameraManager.getCameraIdList()) {
            if (!availableCameraId.equals(cameraId)) {
                continue;
            }
            CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
            Integer facing = c.get(CameraCharacteristics.LENS_FACING);
            return facing != null && facing == CameraCharacteristics.LENS_FACING_BACK;
        }
        return false;
    }

    private String chooseBackCameraId() throws CameraAccessException {
        String fallback = cameraManager.getCameraIdList()[0];
        for (String cameraId : cameraManager.getCameraIdList()) {
            CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
            Integer facing = c.get(CameraCharacteristics.LENS_FACING);
            if (facing != null
                    && facing == CameraCharacteristics.LENS_FACING_BACK
                    && hasCapability(c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES),
                    CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_LOGICAL_MULTI_CAMERA)) {
                return cameraId;
            }
        }
        for (String cameraId : cameraManager.getCameraIdList()) {
            CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
            Integer facing = c.get(CameraCharacteristics.LENS_FACING);
            if (facing != null && facing == CameraCharacteristics.LENS_FACING_BACK) {
                return cameraId;
            }
        }
        return fallback;
    }

    private List<String> backCameraIds() throws CameraAccessException {
        List<String> ids = new ArrayList<>();
        for (String cameraId : cameraManager.getCameraIdList()) {
            CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
            Integer facing = c.get(CameraCharacteristics.LENS_FACING);
            if (facing != null && facing == CameraCharacteristics.LENS_FACING_BACK) {
                ids.add(cameraId);
            }
        }
        return ids;
    }

    private boolean hasBackCamera() {
        try {
            return !backCameraIds().isEmpty();
        } catch (CameraAccessException | SecurityException e) {
            return false;
        }
    }

    private boolean hasManualBackCamera() {
        try {
            for (String cameraId : backCameraIds()) {
                CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
                if (hasCapability(
                        c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES),
                        CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR
                )) {
                    return true;
                }
            }
        } catch (CameraAccessException | SecurityException e) {
            return false;
        }
        return false;
    }

    private boolean hasRawBackCamera() {
        try {
            for (String cameraId : backCameraIds()) {
                CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
                if (hasCapability(
                        c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES),
                        CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW
                )) {
                    return true;
                }
            }
        } catch (CameraAccessException | SecurityException e) {
            return false;
        }
        return false;
    }

    private int frameCountForTest(String testName) {
        if ("iso_sweep".equals(testName)) {
            return SWEEP_FRAMES_PER_ISO * 4;
        }
        if ("raw_burst".equals(testName)) {
            return RAW_BURST_FRAMES;
        }
        if ("solve_candidate_burst".equals(testName)) {
            return SOLVE_CANDIDATE_FRAMES;
        }
        if ("camera_sweep".equals(testName)) {
            return 6;
        }
        if ("day_test".equals(testName)) {
            return DAY_TEST_FRAMES;
        }
        return BURST_FRAMES;
    }

    private Size chooseCaptureSize(CameraCharacteristics c, int format) {
        StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        if (map == null) {
            return null;
        }
        Size[] sizes = map.getOutputSizes(format);
        if (sizes == null || sizes.length == 0) {
            return null;
        }
        List<Size> sorted = new ArrayList<>(Arrays.asList(sizes));
        Collections.sort(sorted, Comparator.comparingLong(s -> (long) s.getWidth() * s.getHeight()));
        return sorted.get(sorted.size() - 1);
    }

    private void appendCaptureMetadataHeader(
            String cameraId,
            CameraCharacteristics c,
            Size captureSize,
            String timestamp
    ) {
        Integer lensFacing = c.get(CameraCharacteristics.LENS_FACING);
        Integer sensorOrientation = c.get(CameraCharacteristics.SENSOR_ORIENTATION);
        int deviceRotation = getWindowManager().getDefaultDisplay().getRotation();
        int[] caps = c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
        Range<Long> exposureRange = c.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        Range<Integer> isoRange = c.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        Float minFocus = c.get(CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE);
        float[] focalLengths = c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
        SizeF sensorSize = c.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);

        captureMetadata.append("PiFinder capture test\n");
        captureMetadata.append("metadataVersion=2\n");
        captureMetadata.append("runPrefix=").append(captureRunPrefix).append("\n");
        captureMetadata.append("timestamp=").append(timestamp).append("\n");
        captureMetadata.append("timestampMs=").append(System.currentTimeMillis()).append("\n");
        captureMetadata.append("appPackage=").append(getPackageName()).append("\n");
        captureMetadata.append("appVersionName=").append(appVersionName()).append("\n");
        captureMetadata.append("appVersionCode=").append(appVersionCode()).append("\n");
        captureMetadata.append("deviceManufacturer=").append(android.os.Build.MANUFACTURER).append("\n");
        captureMetadata.append("deviceModel=").append(android.os.Build.MODEL).append("\n");
        captureMetadata.append("androidRelease=").append(android.os.Build.VERSION.RELEASE).append("\n");
        captureMetadata.append("androidApi=").append(android.os.Build.VERSION.SDK_INT).append("\n");
        captureMetadata.append("test=").append(captureTestName).append("\n");
        captureMetadata.append("cameraId=").append(cameraId).append("\n");
        captureMetadata.append("cameraSelection=").append(captureCameraSelection).append("\n");
        captureMetadata.append("recommendedSolveDevice=").append(RECOMMENDED_SOLVE_DEVICE).append("\n");
        captureMetadata.append("recommendedSolveCameraId=").append(RECOMMENDED_SOLVE_CAMERA_ID).append("\n");
        captureMetadata.append("cameraFacing=").append(lensFacingName(lensFacing)).append("\n");
        captureMetadata.append("cameraCapabilities=").append(capabilityNames(caps)).append("\n");
        captureMetadata.append("manualSensor=").append(hasCapability(
                caps,
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR
        )).append("\n");
        captureMetadata.append("raw=").append(hasCapability(
                caps,
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW
        )).append("\n");
        captureMetadata.append("logicalMultiCamera=").append(hasCapability(
                caps,
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_LOGICAL_MULTI_CAMERA
        )).append("\n");
        captureMetadata.append("hardwareLevel=").append(hardwareLevelName(valueOrMinusOne(
                c.get(CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL)
        ))).append("\n");
        captureMetadata.append("format=").append(captureFormatName(captureFormat)).append("\n");
        captureMetadata.append("size=").append(captureSize.getWidth()).append("x")
                .append(captureSize.getHeight()).append("\n");
        captureMetadata.append("frames=").append(captureFrameCount).append("\n");
        captureMetadata.append("sensorOrientation=").append(sensorOrientation != null ? sensorOrientation : "unknown")
                .append("\n");
        captureMetadata.append("deviceRotation=").append(deviceRotationName(deviceRotation)).append("\n");
        captureMetadata.append("jpegOrientation=").append(captureJpegOrientation).append("\n");
        captureMetadata.append("minimumFocusDistanceDiopters=").append(minFocus != null ? minFocus : "unknown")
                .append("\n");
        captureMetadata.append("focalLengthsMm=").append(focalLengths != null ? Arrays.toString(focalLengths) : "unknown")
                .append("\n");
        captureMetadata.append("sensorPhysicalSizeMm=").append(sensorSize != null ? sensorSize : "unknown")
                .append("\n");
        captureMetadata.append("exposureRangeNs=").append(exposureRange != null ? exposureRange : "unknown")
                .append("\n");
        captureMetadata.append("isoRange=").append(isoRange != null ? isoRange : "unknown").append("\n");
        captureMetadata.append("outputTreeUri=").append(outputTreeUri != null ? outputTreeUri : "none").append("\n");
        captureMetadata.append("\nREQUESTS\n");
    }

    private void createCaptureSession(CameraDevice camera, CameraCharacteristics c) {
        try {
            Surface surface = captureReader.getSurface();
            camera.createCaptureSession(
                    Collections.singletonList(surface),
                    new CameraCaptureSession.StateCallback() {
                        @Override
                        public void onConfigured(CameraCaptureSession session) {
                            captureSession = session;
                            runCaptureTest(c);
                        }

                        @Override
                        public void onConfigureFailed(CameraCaptureSession session) {
                            runOnUiThread(() -> captureView.setText("Capture session configuration failed."));
                        }
                    },
                    cameraHandler
            );
        } catch (CameraAccessException e) {
            captureView.setText("Create session failed: " + e.getMessage());
        }
    }

    private void runCaptureTest(CameraCharacteristics c) {
        try {
            Range<Long> exposureRange = c.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
            Range<Integer> isoRange = c.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
            long exposureNs = exposureRange != null ? exposureRange.getUpper() : 200_000_000L;
            int maxIso = isoRange != null ? isoRange.getUpper() : 3200;
            int solveIso = clampIso(SOLVE_CANDIDATE_ISO, isoRange);

            captureMetadata.append("selectedExposureNs=").append(exposureNs).append("\n");
            captureMetadata.append("selectedMaxIso=").append(maxIso).append("\n");
            captureMetadata.append("selectedSolveCandidateIso=").append(solveIso).append("\n");

            if ("day_test".equals(captureTestName)) {
                for (int i = 0; i < captureFrameCount; i++) {
                    queuedRequests.add(buildAutoDayRequest(i + 1));
                    queuedLabels.add("auto_day");
                }
            } else if ("iso_sweep".equals(captureTestName)) {
                int[] isoValues = new int[] {
                        clampIso(400, isoRange),
                        clampIso(800, isoRange),
                        clampIso(1600, isoRange),
                        clampIso(maxIso, isoRange)
                };
                for (int iso : isoValues) {
                    for (int i = 0; i < SWEEP_FRAMES_PER_ISO; i++) {
                        queuedRequests.add(buildStillRequest(exposureNs, iso, queuedRequests.size() + 1));
                        queuedLabels.add("iso" + iso);
                    }
                }
            } else if ("solve_candidate_burst".equals(captureTestName)) {
                for (int i = 0; i < captureFrameCount; i++) {
                    queuedRequests.add(buildStillRequest(exposureNs, solveIso, i + 1));
                    queuedLabels.add("solve_iso" + solveIso);
                }
            } else {
                for (int i = 0; i < captureFrameCount; i++) {
                    queuedRequests.add(buildStillRequest(exposureNs, maxIso, i + 1));
                    queuedLabels.add("iso" + maxIso);
                }
            }

            runOnUiThread(() -> captureView.setText(
                    "Capturing " + captureFrameCount + " frames...\n"
                            + "Test: " + captureTestName + "\n"
                            + ("day_test".equals(captureTestName)
                            ? "Exposure: auto\nISO: auto"
                            : "Exposure: " + (exposureNs / 1_000_000.0) + " ms\nISO: "
                                    + ("solve_candidate_burst".equals(captureTestName) ? solveIso : maxIso))
            ));

            captureSession.captureBurst(queuedRequests, new CameraCaptureSession.CaptureCallback() {
                @Override
                public void onCaptureCompleted(CameraCaptureSession session, CaptureRequest request, TotalCaptureResult result) {
                    completedFrames++;
                    appendCaptureResultMetadata(completedFrames, request, result);
                }

                @Override
                public void onCaptureFailed(CameraCaptureSession session, CaptureRequest request, CaptureFailure failure) {
                    failedFrames++;
                    checkCaptureDone();
                }
            }, cameraHandler);
        } catch (CameraAccessException | IllegalArgumentException e) {
            captureView.setText("Capture test failed: " + e.getMessage());
        }
    }

    private CaptureRequest buildStillRequest(long exposureNs, int iso, int frameNumber) throws CameraAccessException {
        CaptureRequest.Builder request = captureCamera.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
        request.addTarget(captureReader.getSurface());
        request.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_OFF);
        request.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
        request.set(CaptureRequest.SENSOR_EXPOSURE_TIME, exposureNs);
        request.set(CaptureRequest.SENSOR_SENSITIVITY, iso);
        request.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF);
        request.set(CaptureRequest.LENS_FOCUS_DISTANCE, 0.0f);
        if (captureFormat == 256) {
            request.set(CaptureRequest.JPEG_QUALITY, (byte) 95);
            request.set(CaptureRequest.JPEG_ORIENTATION, captureJpegOrientation);
        }
        captureMetadata.append("requestFrame=").append(frameNumber)
                .append(" mode=manual")
                .append(" exposureNs=").append(exposureNs)
                .append(" iso=").append(iso)
                .append(" focusDiopters=0.0")
                .append(" jpegOrientation=").append(captureJpegOrientation)
                .append(" format=").append(captureFormatName(captureFormat))
                .append("\n");
        return request.build();
    }

    private CaptureRequest buildAutoDayRequest(int frameNumber) throws CameraAccessException {
        CaptureRequest.Builder request = captureCamera.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
        request.addTarget(captureReader.getSurface());
        request.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO);
        request.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON);
        request.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
        request.set(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO);
        if (captureFormat == 256) {
            request.set(CaptureRequest.JPEG_QUALITY, (byte) 95);
            request.set(CaptureRequest.JPEG_ORIENTATION, captureJpegOrientation);
        }
        captureMetadata.append("requestFrame=").append(frameNumber)
                .append(" mode=auto_day")
                .append(" jpegOrientation=").append(captureJpegOrientation)
                .append(" format=").append(captureFormatName(captureFormat))
                .append("\n");
        return request.build();
    }

    private int clampIso(int value, Range<Integer> range) {
        if (range == null) {
            return value;
        }
        return Math.max(range.getLower(), Math.min(range.getUpper(), value));
    }

    private void appendCaptureResultMetadata(
            int frameNumber,
            CaptureRequest request,
            TotalCaptureResult result
    ) {
        captureMetadata.append("completedFrame=").append(frameNumber);
        appendRequestValue(captureMetadata, " requestExposureNs", request.get(CaptureRequest.SENSOR_EXPOSURE_TIME));
        appendRequestValue(captureMetadata, " requestIso", request.get(CaptureRequest.SENSOR_SENSITIVITY));
        appendRequestValue(captureMetadata, " requestFocusDiopters", request.get(CaptureRequest.LENS_FOCUS_DISTANCE));
        appendRequestValue(captureMetadata, " resultExposureNs", result.get(CaptureResult.SENSOR_EXPOSURE_TIME));
        appendRequestValue(captureMetadata, " resultIso", result.get(CaptureResult.SENSOR_SENSITIVITY));
        appendRequestValue(captureMetadata, " resultFocusDiopters", result.get(CaptureResult.LENS_FOCUS_DISTANCE));
        appendRequestValue(captureMetadata, " resultAfState", result.get(CaptureResult.CONTROL_AF_STATE));
        appendRequestValue(captureMetadata, " resultAeState", result.get(CaptureResult.CONTROL_AE_STATE));
        appendRequestValue(captureMetadata, " resultAwbState", result.get(CaptureResult.CONTROL_AWB_STATE));
        captureMetadata.append("\n");
    }

    private void appendRequestValue(StringBuilder builder, String label, Object value) {
        builder.append(label).append("=").append(value != null ? value : "unknown");
    }

    private int jpegOrientationFor(CameraCharacteristics c) {
        Integer sensorOrientation = c.get(CameraCharacteristics.SENSOR_ORIENTATION);
        Integer lensFacing = c.get(CameraCharacteristics.LENS_FACING);
        int deviceRotation = getWindowManager().getDefaultDisplay().getRotation();
        int deviceDegrees;
        switch (deviceRotation) {
            case Surface.ROTATION_90:
                deviceDegrees = 90;
                break;
            case Surface.ROTATION_180:
                deviceDegrees = 180;
                break;
            case Surface.ROTATION_270:
                deviceDegrees = 270;
                break;
            case Surface.ROTATION_0:
            default:
                deviceDegrees = 0;
                break;
        }
        if (sensorOrientation == null) {
            return deviceDegrees;
        }
        if (lensFacing != null && lensFacing == CameraCharacteristics.LENS_FACING_FRONT) {
            return (sensorOrientation + deviceDegrees) % 360;
        }
        return (sensorOrientation - deviceDegrees + 360) % 360;
    }

    private String deviceRotationName(int rotation) {
        switch (rotation) {
            case Surface.ROTATION_90:
                return "ROTATION_90";
            case Surface.ROTATION_180:
                return "ROTATION_180";
            case Surface.ROTATION_270:
                return "ROTATION_270";
            case Surface.ROTATION_0:
            default:
                return "ROTATION_0";
        }
    }

    private void saveNextImage(ImageReader reader) {
        Image image = null;
        try {
            image = reader.acquireNextImage();
            if (image == null) {
                failedFrames++;
                checkCaptureDone();
                return;
            }
            ByteBuffer buffer = image.getPlanes()[0].getBuffer();
            byte[] bytes = new byte[buffer.remaining()];
            buffer.get(bytes);
            String label = savedFrames < queuedLabels.size() ? queuedLabels.get(savedFrames) : "frame";
            String extension = captureFormat == 32 ? ".raw" : ".jpg";
            String mimeType = captureFormat == 32 ? "application/octet-stream" : "image/jpeg";
            String name = captureRunPrefix + "_" + label + "_" + String.format(Locale.US, "%03d", savedFrames + 1) + extension;
            writeDocument(name, mimeType, bytes);
            if (captureFormat == 256 && bytes.length > 0) {
                lastCapturedJpegBytes = Arrays.copyOf(bytes, bytes.length);
                lastCapturedJpegName = name;
                lastCapturedJpegMetadataJson = buildCameraFrameMetadataJson(name, bytes.length);
                if ("solve_candidate_burst".equals(captureTestName)) {
                    recordSolveCandidateFrame(name, label, bytes, savedFrames + 1);
                }
            }
            captureMetadata.append("savedFile=").append(name)
                    .append(" label=").append(label)
                    .append(" bytes=").append(bytes.length)
                    .append(" mimeType=").append(mimeType)
                    .append("\n");
            savedFrames++;
            runOnUiThread(() -> captureView.setText(
                    "Saving " + captureTestName + "...\nSaved: " + savedFrames + "/" + captureFrameCount
                            + "\nFailed: " + failedFrames
            ));
        } catch (Exception e) {
            failedFrames++;
            runOnUiThread(() -> captureView.setText("Save image failed: " + e.getMessage()));
        } finally {
            if (image != null) {
                image.close();
            }
            checkCaptureDone();
        }
    }

    private void checkCaptureDone() {
        pendingFrames--;
        if (pendingFrames > 0) {
            return;
        }
        try {
            captureMetadata.append("\nSUMMARY\n");
            captureMetadata.append("savedFrames=").append(savedFrames).append("\n");
            captureMetadata.append("failedFrames=").append(failedFrames).append("\n");
            captureMetadata.append("completedFrames=").append(completedFrames).append("\n");
            writeDocument(
                    captureRunPrefix + "_metadata.txt",
                    "text/plain",
                    captureMetadata.toString().getBytes()
            );
        } catch (Exception ignored) {
        }
        runOnUiThread(() -> captureView.setText(
                "Capture test complete.\nTest: " + captureTestName
                        + "\nSaved: " + savedFrames
                        + "\nFailed: " + failedFrames
                        + "\nFolder: " + captureRunPrefix
        ));
        if ("solve_candidate_burst".equals(captureTestName)) {
            runOnUiThread(() -> updateMobileCameraDiagnosticGuide("capture_ready"));
        }
        closeCaptureCamera();
        if ("solve_candidate_burst".equals(captureTestName) && fullDiagnosticRunning) {
            runOnUiThread(() -> continueFullMobileCameraDiagnostic());
        }
        if ("solve_candidate_burst".equals(captureTestName) && aiImuDriftSolveRunning) {
            runOnUiThread(() -> continueAiImuDriftSolve());
        }
        if ("camera_sweep".equals(captureTestName)) {
            cameraSweepIndex++;
            if (cameraSweepIndex < cameraSweepIds.size()) {
                runOnUiThread(() -> captureView.setText(
                        "Camera sweep continuing...\nCompleted camera "
                                + cameraSweepIds.get(cameraSweepIndex - 1)
                                + "\nNext camera: " + cameraSweepIds.get(cameraSweepIndex)
                ));
                openCaptureCamera();
            } else {
                runOnUiThread(() -> captureView.setText(
                        "Camera sweep complete.\nCameras tested: "
                                + TextUtils.join(", ", cameraSweepIds)
                ));
            }
        }
    }

    private void writeDocument(String fileName, String mimeType, byte[] bytes) throws IOException {
        if (outputTreeUri == null) {
            throw new IOException("No output folder selected");
        }
        String parentDocumentId = captureDirDocumentId != null
                ? captureDirDocumentId
                : DocumentsContract.getTreeDocumentId(outputTreeUri);
        Uri docUri = DocumentsContract.buildDocumentUriUsingTree(
                outputTreeUri,
                parentDocumentId
        );
        Uri fileUri = DocumentsContract.createDocument(getContentResolver(), docUri, mimeType, fileName);
        if (fileUri == null) {
            throw new IOException("Could not create " + fileName);
        }
        try (OutputStream outputStream = getContentResolver().openOutputStream(fileUri)) {
            if (outputStream == null) {
                throw new IOException("Could not open " + fileName);
            }
            outputStream.write(bytes);
        }
    }

    private String createRunDirectory(String folderName) throws IOException {
        if (outputTreeUri == null) {
            throw new IOException("No output folder selected");
        }
        String parentId = DocumentsContract.getTreeDocumentId(outputTreeUri);
        Uri parentUri = DocumentsContract.buildDocumentUriUsingTree(outputTreeUri, parentId);
        Uri folderUri = DocumentsContract.createDocument(
                getContentResolver(),
                parentUri,
                DocumentsContract.Document.MIME_TYPE_DIR,
                folderName
        );
        if (folderUri == null) {
            throw new IOException("Could not create folder " + folderName);
        }
        return DocumentsContract.getDocumentId(folderUri);
    }

    private String captureFormatName(int format) {
        if (format == 256) {
            return "JPEG";
        }
        if (format == 32) {
            return "RAW_SENSOR";
        }
        if (format == 37) {
            return "RAW10";
        }
        if (format == 35) {
            return "YUV_420_888";
        }
        return "format_" + format;
    }

    private void closeCaptureCamera() {
        if (captureSession != null) {
            captureSession.close();
            captureSession = null;
        }
        if (captureCamera != null) {
            captureCamera.close();
            captureCamera = null;
        }
        if (captureReader != null) {
            captureReader.close();
            captureReader = null;
        }
    }

    private boolean hasCapability(int[] caps, int capability) {
        if (caps == null) {
            return false;
        }
        for (int cap : caps) {
            if (cap == capability) {
                return true;
            }
        }
        return false;
    }

    private String capabilityNames(int[] caps) {
        if (caps == null || caps.length == 0) {
            return "none";
        }
        List<String> names = new ArrayList<>();
        for (int cap : caps) {
            switch (cap) {
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_BACKWARD_COMPATIBLE:
                    names.add("BACKWARD_COMPATIBLE");
                    break;
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR:
                    names.add("MANUAL_SENSOR");
                    break;
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_POST_PROCESSING:
                    names.add("MANUAL_POST_PROCESSING");
                    break;
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW:
                    names.add("RAW");
                    break;
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_LOGICAL_MULTI_CAMERA:
                    names.add("LOGICAL_MULTI_CAMERA");
                    break;
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_PRIVATE_REPROCESSING:
                    names.add("PRIVATE_REPROCESSING");
                    break;
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_READ_SENSOR_SETTINGS:
                    names.add("READ_SENSOR_SETTINGS");
                    break;
                case CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_ULTRA_HIGH_RESOLUTION_SENSOR:
                    names.add("ULTRA_HIGH_RESOLUTION_SENSOR");
                    break;
                default:
                    names.add("cap_" + cap);
            }
        }
        return TextUtils.join(", ", names);
    }

    private void appendSizes(StringBuilder report, String label, Size[] sizes) {
        report.append("  ").append(label).append(": ");
        if (sizes == null || sizes.length == 0) {
            report.append("none\n");
            return;
        }
        report.append(firstSizes(sizes, 10)).append("\n");
    }

    private String firstSizes(Size[] sizes, int limit) {
        List<String> values = new ArrayList<>();
        for (int i = 0; i < sizes.length && i < limit; i++) {
            values.add(sizes[i].getWidth() + "x" + sizes[i].getHeight());
        }
        if (sizes.length > limit) {
            values.add("... +" + (sizes.length - limit) + " more");
        }
        return TextUtils.join(", ", values);
    }

    private String aeModeNames(int[] modes) {
        if (modes == null || modes.length == 0) {
            return "none";
        }
        List<String> names = new ArrayList<>();
        for (int mode : modes) {
            switch (mode) {
                case CameraCharacteristics.CONTROL_AE_MODE_OFF:
                    names.add("OFF");
                    break;
                case CameraCharacteristics.CONTROL_AE_MODE_ON:
                    names.add("ON");
                    break;
                case CameraCharacteristics.CONTROL_AE_MODE_ON_ALWAYS_FLASH:
                    names.add("ON_ALWAYS_FLASH");
                    break;
                case CameraCharacteristics.CONTROL_AE_MODE_ON_AUTO_FLASH:
                    names.add("ON_AUTO_FLASH");
                    break;
                case CameraCharacteristics.CONTROL_AE_MODE_ON_AUTO_FLASH_REDEYE:
                    names.add("ON_AUTO_FLASH_REDEYE");
                    break;
                case CameraCharacteristics.CONTROL_AE_MODE_ON_EXTERNAL_FLASH:
                    names.add("ON_EXTERNAL_FLASH");
                    break;
                default:
                    names.add("AE_" + mode);
            }
        }
        return TextUtils.join(", ", names);
    }

    private String afModeNames(int[] modes) {
        if (modes == null || modes.length == 0) {
            return "none";
        }
        List<String> names = new ArrayList<>();
        for (int mode : modes) {
            switch (mode) {
                case CameraCharacteristics.CONTROL_AF_MODE_OFF:
                    names.add("OFF");
                    break;
                case CameraCharacteristics.CONTROL_AF_MODE_AUTO:
                    names.add("AUTO");
                    break;
                case CameraCharacteristics.CONTROL_AF_MODE_CONTINUOUS_PICTURE:
                    names.add("CONTINUOUS_PICTURE");
                    break;
                case CameraCharacteristics.CONTROL_AF_MODE_CONTINUOUS_VIDEO:
                    names.add("CONTINUOUS_VIDEO");
                    break;
                case CameraCharacteristics.CONTROL_AF_MODE_EDOF:
                    names.add("EDOF");
                    break;
                case CameraCharacteristics.CONTROL_AF_MODE_MACRO:
                    names.add("MACRO");
                    break;
                default:
                    names.add("AF_" + mode);
            }
        }
        return TextUtils.join(", ", names);
    }

    private String sceneModeNames(int[] modes) {
        if (modes == null || modes.length == 0) {
            return "none";
        }
        List<String> names = new ArrayList<>();
        for (int mode : modes) {
            switch (mode) {
                case CameraCharacteristics.CONTROL_SCENE_MODE_DISABLED:
                    names.add("DISABLED");
                    break;
                case CameraCharacteristics.CONTROL_SCENE_MODE_NIGHT:
                    names.add("NIGHT");
                    break;
                case CameraCharacteristics.CONTROL_SCENE_MODE_NIGHT_PORTRAIT:
                    names.add("NIGHT_PORTRAIT");
                    break;
                case CameraCharacteristics.CONTROL_SCENE_MODE_ACTION:
                    names.add("ACTION");
                    break;
                case CameraCharacteristics.CONTROL_SCENE_MODE_HDR:
                    names.add("HDR");
                    break;
                default:
                    names.add("SCENE_" + mode);
            }
        }
        return TextUtils.join(", ", names);
    }

    private String hardwareLevelName(int level) {
        switch (level) {
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_LEGACY:
                return "LEGACY";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_LIMITED:
                return "LIMITED";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_FULL:
                return "FULL";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_3:
                return "LEVEL_3";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_EXTERNAL:
                return "EXTERNAL";
            default:
                return "unknown(" + level + ")";
        }
    }

    private int valueOrMinusOne(Integer value) {
        return value == null ? -1 : value;
    }

    private void appendKeyNames(StringBuilder report, String label, List<?> keys) {
        report.append("  ").append(label).append(": ");
        if (keys == null || keys.isEmpty()) {
            report.append("none\n");
            return;
        }
        List<String> names = new ArrayList<>();
        for (Object key : keys) {
            if (key instanceof CaptureRequest.Key<?>) {
                names.add(((CaptureRequest.Key<?>) key).getName());
            } else if (key instanceof CaptureResult.Key<?>) {
                names.add(((CaptureResult.Key<?>) key).getName());
            } else {
                names.add(String.valueOf(key));
            }
        }
        report.append(compactList(names, 24)).append("\n");
    }

    private String compactList(List<String> values, int limit) {
        List<String> out = new ArrayList<>();
        for (int i = 0; i < values.size() && i < limit; i++) {
            out.add(values.get(i));
        }
        if (values.size() > limit) {
            out.add("... +" + (values.size() - limit) + " more");
        }
        return TextUtils.join(", ", out);
    }

    private void appendExtensionReport(StringBuilder report, String cameraId) {
        if (android.os.Build.VERSION.SDK_INT < 31) {
            report.append("  Camera extensions: unavailable below API 31\n");
            return;
        }
        try {
            CameraExtensionCharacteristics ext = cameraManager.getCameraExtensionCharacteristics(cameraId);
            List<Integer> supported = ext.getSupportedExtensions();
            report.append("  Camera extensions: ");
            if (supported == null || supported.isEmpty()) {
                report.append("none\n");
                return;
            }
            List<String> names = new ArrayList<>();
            for (Integer extension : supported) {
                names.add(extensionName(extension));
            }
            report.append(TextUtils.join(", ", names)).append("\n");
        } catch (CameraAccessException | IllegalArgumentException e) {
            report.append("  Camera extensions: unavailable (")
                    .append(e.getMessage()).append(")\n");
        }
    }

    private String extensionName(int extension) {
        if (android.os.Build.VERSION.SDK_INT < 31) {
            return "EXT_" + extension;
        }
        switch (extension) {
            case CameraExtensionCharacteristics.EXTENSION_AUTOMATIC:
                return "AUTOMATIC";
            case CameraExtensionCharacteristics.EXTENSION_BOKEH:
                return "BOKEH";
            case CameraExtensionCharacteristics.EXTENSION_FACE_RETOUCH:
                return "FACE_RETOUCH";
            case CameraExtensionCharacteristics.EXTENSION_HDR:
                return "HDR";
            case CameraExtensionCharacteristics.EXTENSION_NIGHT:
                return "NIGHT";
            default:
                return "EXT_" + extension;
        }
    }

    private void appendPhysicalCameraReport(StringBuilder report, CameraCharacteristics c) {
        Set<String> physicalIds = c.getPhysicalCameraIds();
        report.append("  Physical camera IDs: ");
        if (physicalIds == null || physicalIds.isEmpty()) {
            report.append("none\n");
            return;
        }
        report.append(TextUtils.join(", ", physicalIds)).append("\n");
        for (String physicalId : physicalIds) {
            try {
                CameraCharacteristics pc = cameraManager.getCameraCharacteristics(physicalId);
                Range<Long> exp = pc.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
                Range<Integer> iso = pc.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
                float[] focal = pc.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
                SizeF size = pc.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
                report.append("    Physical ").append(physicalId)
                        .append(" exp=").append(exp != null ? exp : "unknown")
                        .append(" iso=").append(iso != null ? iso : "unknown")
                        .append(" focal=").append(focal != null ? Arrays.toString(focal) : "unknown")
                        .append(" sensor=").append(size != null ? size : "unknown")
                        .append("\n");
            } catch (CameraAccessException | IllegalArgumentException e) {
                report.append("    Physical ").append(physicalId)
                        .append(" unavailable: ").append(e.getMessage()).append("\n");
            }
        }
    }

    private String lensFacingName(Integer value) {
        if (value == null) {
            return "unknown";
        }
        switch (value) {
            case CameraCharacteristics.LENS_FACING_BACK:
                return "back";
            case CameraCharacteristics.LENS_FACING_FRONT:
                return "front";
            case CameraCharacteristics.LENS_FACING_EXTERNAL:
                return "external";
            default:
                return "unknown(" + value + ")";
        }
    }

    private String sensorName(int type) {
        switch (type) {
            case Sensor.TYPE_ACCELEROMETER:
                return "accelerometer";
            case Sensor.TYPE_GYROSCOPE:
                return "gyroscope";
            case Sensor.TYPE_MAGNETIC_FIELD:
                return "magnetometer";
            case Sensor.TYPE_ROTATION_VECTOR:
                return "rotation vector";
            case Sensor.TYPE_GAME_ROTATION_VECTOR:
                return "game rotation vector";
            default:
                return "sensor " + type;
        }
    }

    private String formatValues(float[] values) {
        List<String> parts = new ArrayList<>();
        for (float value : values) {
            parts.add(format(value));
        }
        return "[" + TextUtils.join(", ", parts) + "]";
    }

    private String format(double value) {
        return String.format(Locale.US, "%s", F3.format(value));
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density);
    }
}
