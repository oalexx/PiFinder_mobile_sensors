package io.pifinder.mobile;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
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
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.provider.DocumentsContract;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.TextUtils;
import android.text.style.ForegroundColorSpan;
import android.util.Range;
import android.util.Size;
import android.util.SizeF;
import android.view.Gravity;
import android.view.Surface;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class MainActivity extends Activity implements SensorEventListener, LocationListener {
    private static final int REQUEST_PERMISSIONS = 41;
    private static final int REQUEST_OUTPUT_DIR = 42;
    private static final int BURST_FRAMES = 30;
    private static final int SWEEP_FRAMES_PER_ISO = 8;
    private static final int RAW_BURST_FRAMES = 12;
    private static final int DAY_TEST_FRAMES = 8;
    private static final int COLOR_BG = Color.rgb(3, 5, 10);
    private static final int COLOR_PANEL = Color.rgb(17, 20, 28);
    private static final int COLOR_PANEL_SOFT = Color.rgb(24, 27, 37);
    private static final int COLOR_TEXT = Color.rgb(238, 242, 247);
    private static final int COLOR_MUTED = Color.rgb(127, 136, 153);
    private static final int COLOR_ACCENT = Color.rgb(255, 38, 92);
    private static final int COLOR_ACCENT_DARK = Color.rgb(92, 12, 35);
    private static final int COLOR_PASS = Color.rgb(64, 214, 137);
    private static final int COLOR_WARN = Color.rgb(255, 190, 92);
    private static final int COLOR_FAIL = Color.rgb(255, 74, 107);
    private static final DecimalFormat F3 = new DecimalFormat("0.000");

    private SensorManager sensorManager;
    private LocationManager locationManager;
    private CameraManager cameraManager;

    private TextView deviceReportView;
    private TextView sensorReportView;
    private TextView cameraReportView;
    private TextView compatibilityView;
    private TextView liveView;
    private TextView captureView;
    private Button startImuButton;
    private LinearLayout homeScreen;
    private LinearLayout capabilitiesScreen;
    private LinearLayout cameraScreen;
    private String latestReport = "";
    private boolean compatibilityCheckRun = false;
    private Uri outputTreeUri;

    private final List<Sensor> activeSensors = new ArrayList<>();
    private final StringBuilder liveSensorText = new StringBuilder();
    private Location latestLocation;

    private HandlerThread cameraThread;
    private Handler cameraHandler;
    private CameraDevice captureCamera;
    private CameraCaptureSession captureSession;
    private ImageReader captureReader;
    private int pendingFrames;
    private int savedFrames;
    private int failedFrames;
    private String captureRunPrefix = "";
    private String captureDirDocumentId;
    private String captureTestName = "manual";
    private int captureFormat = 256;
    private int captureJpegOrientation = 0;
    private int captureFrameCount = BURST_FRAMES;
    private List<CaptureRequest> queuedRequests = new ArrayList<>();
    private final List<String> queuedLabels = new ArrayList<>();
    private final StringBuilder captureMetadata = new StringBuilder();
    private final List<String> cameraSweepIds = new ArrayList<>();
    private int cameraSweepIndex = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        cameraManager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);

        setContentView(buildUi());
        requestRuntimePermissions();
        refreshReport();
    }

    @Override
    protected void onPause() {
        super.onPause();
        stopLiveSensors();
        stopLocation();
        closeCaptureCamera();
        stopCameraThread();
    }

    private View buildUi() {
        ScrollView scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(18), dp(18), dp(18));
        root.setBackgroundColor(COLOR_BG);
        scrollView.addView(root);

        TextView title = new TextView(this);
        title.setText("PIFINDER MOBILE");
        title.setTextSize(24);
        title.setTextColor(COLOR_TEXT);
        title.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL));
        title.setLetterSpacing(0.18f);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(56), 0, dp(6));
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("COMPATIBILITY TESTER");
        subtitle.setTextSize(12);
        subtitle.setTextColor(COLOR_ACCENT);
        subtitle.setLetterSpacing(0.24f);
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, 0, 0, dp(34));
        root.addView(subtitle);

        homeScreen = screenContainer();
        root.addView(homeScreen);
        TextView homeIntro = proseText();
        homeIntro.setGravity(Gravity.CENTER);
        homeIntro.setText("Choose a module.");
        homeScreen.addView(homeIntro);
        Button capabilitiesNav = makeHeroButton("01", "CHECK CAPABILITIES", "Sensors, GPS, IMU, and phone readiness");
        capabilitiesNav.setOnClickListener(v -> showScreen("capabilities"));
        homeScreen.addView(capabilitiesNav);
        Button cameraNav = makeHeroButton("02", "CAMERA LAB", "Daylight framing, astro burst, RAW, and lens sweep");
        cameraNav.setOnClickListener(v -> showScreen("camera"));
        homeScreen.addView(cameraNav);

        capabilitiesScreen = screenContainer();
        root.addView(capabilitiesScreen);
        cameraScreen = screenContainer();
        root.addView(cameraScreen);

        addBackRow(capabilitiesScreen);
        addSectionHeader(capabilitiesScreen, "01", "CHECK CAPABILITIES", "Start IMU, stop it after a few seconds, then run the compatibility check.");
        TextView workflow = proseText();
        workflow.setText("1  START IMU\n2  Move the phone gently for a few seconds\n3  STOP\n4  RUN CHECK\n5  COPY REPORT if you want to share it");
        capabilitiesScreen.addView(workflow);
        LinearLayout row1 = buttonRow();
        capabilitiesScreen.addView(row1);
        startImuButton = makeGridButton("Start IMU");
        startImuButton.setOnClickListener(v -> startLiveSensors());
        row1.addView(startImuButton);
        Button stop = makeGridButton("Stop");
        stop.setOnClickListener(v -> {
            stopLiveSensors();
            stopLocation();
        });
        row1.addView(stop);

        LinearLayout row2 = buttonRow();
        capabilitiesScreen.addView(row2);
        Button refresh = makeGridButton("Run Check");
        refresh.setOnClickListener(v -> {
            compatibilityCheckRun = true;
            refreshReport();
        });
        row2.addView(refresh);
        Button copy = makeGridButton("Copy Report");
        copy.setOnClickListener(v -> copyReport());
        row2.addView(copy);

        compatibilityView = sectionText();
        capabilitiesScreen.addView(compatibilityView);

        liveView = sectionText();
        liveView.setText("Live sensors stopped.");
        capabilitiesScreen.addView(liveView);

        addSectionHeader(capabilitiesScreen, "02", "TECHNICAL REPORT", "Detailed sensor and system data for debugging.");
        deviceReportView = sectionText();
        capabilitiesScreen.addView(deviceReportView);
        sensorReportView = sectionText();
        capabilitiesScreen.addView(sensorReportView);

        addBackRow(cameraScreen);
        addSectionHeader(cameraScreen, "01", "CAMERA LAB", "Select a save folder before running any test.");
        TextView cameraGuide = proseText();
        cameraGuide.setText("SAVE FOLDER first.\n\nDay Test checks framing indoors or daylight. Manual Burst, ISO Sweep, RAW Burst and Cam Sweep are for real sky testing.");
        cameraScreen.addView(cameraGuide);

        LinearLayout row3 = buttonRow();
        cameraScreen.addView(row3);
        Button pickFolder = makeGridButton("Save Folder");
        pickFolder.setOnClickListener(v -> pickOutputFolder());
        row3.addView(pickFolder);
        Button dayTest = makeGridButton("Day Test");
        dayTest.setOnClickListener(v -> startCaptureTest("day_test", 256));
        row3.addView(dayTest);

        LinearLayout row4 = buttonRow();
        cameraScreen.addView(row4);
        Button manualBurst = makeGridButton("Manual Burst");
        manualBurst.setOnClickListener(v -> startCaptureTest("manual_burst", 256));
        row4.addView(manualBurst);
        Button isoSweep = makeGridButton("ISO Sweep");
        isoSweep.setOnClickListener(v -> startCaptureTest("iso_sweep", 256));
        row4.addView(isoSweep);

        LinearLayout row5 = buttonRow();
        cameraScreen.addView(row5);
        Button rawBurst = makeGridButton("RAW Burst");
        rawBurst.setOnClickListener(v -> startCaptureTest("raw_burst", 32));
        row5.addView(rawBurst);
        Button cameraSweep = makeGridButton("Cam Sweep");
        cameraSweep.setOnClickListener(v -> startCaptureTest("camera_sweep", 256));
        row5.addView(cameraSweep);

        captureView = sectionText();
        captureView.setText("Capture test: choose a save folder, then run Day Test, Manual Burst, ISO Sweep, RAW Burst, or Cam Sweep.");
        cameraScreen.addView(captureView);

        cameraReportView = sectionText();
        cameraScreen.addView(cameraReportView);

        showScreen("home");

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
        if (homeScreen == null || capabilitiesScreen == null || cameraScreen == null) {
            return;
        }
        homeScreen.setVisibility("home".equals(screenName) ? View.VISIBLE : View.GONE);
        capabilitiesScreen.setVisibility("capabilities".equals(screenName) ? View.VISIBLE : View.GONE);
        cameraScreen.setVisibility("camera".equals(screenName) ? View.VISIBLE : View.GONE);
    }

    private void addBackRow(LinearLayout root) {
        LinearLayout row = buttonRow();
        root.addView(row);
        Button back = makeGridButton("Back");
        back.setOnClickListener(v -> showScreen("home"));
        row.addView(back);
        TextView spacer = new TextView(this);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, 1, 1);
        row.addView(spacer, params);
    }

    private Button makeHeroButton(String title, String subtitle) {
        Button button = new Button(this);
        button.setText(title + "\n" + subtitle);
        button.setAllCaps(false);
        button.setTextSize(15);
        button.setTextColor(COLOR_TEXT);
        button.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL));
        button.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        button.setPadding(dp(18), dp(18), dp(18), dp(18));
        button.setBackground(roundedRect(COLOR_PANEL, COLOR_ACCENT_DARK, 1, 6));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(12), 0, 0);
        button.setLayoutParams(params);
        return button;
    }

    private void addSectionHeader(LinearLayout root, String number, String title, String subtitle) {
        LinearLayout block = new LinearLayout(this);
        block.setOrientation(LinearLayout.VERTICAL);
        block.setPadding(0, dp(18), 0, dp(8));
        root.addView(block);

        LinearLayout titleRow = new LinearLayout(this);
        titleRow.setOrientation(LinearLayout.HORIZONTAL);
        titleRow.setGravity(Gravity.CENTER_VERTICAL);
        block.addView(titleRow);

        TextView index = new TextView(this);
        index.setText(number + ".");
        index.setTextSize(13);
        index.setTextColor(COLOR_ACCENT);
        index.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        index.setLetterSpacing(0.08f);
        LinearLayout.LayoutParams indexParams = new LinearLayout.LayoutParams(
                dp(34),
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        titleRow.addView(index, indexParams);

        TextView heading = new TextView(this);
        heading.setText(title);
        heading.setTextSize(16);
        heading.setTextColor(COLOR_TEXT);
        heading.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL));
        heading.setLetterSpacing(0.18f);
        titleRow.addView(heading);

        TextView caption = new TextView(this);
        caption.setText(subtitle);
        caption.setTextSize(12);
        caption.setTextColor(COLOR_MUTED);
        caption.setLineSpacing(dp(2), 1.0f);
        caption.setPadding(dp(34), dp(4), 0, dp(8));
        block.addView(caption);

        View accent = new View(this);
        accent.setBackgroundColor(COLOR_ACCENT);
        LinearLayout.LayoutParams accentParams = new LinearLayout.LayoutParams(
                dp(56),
                dp(1)
        );
        accentParams.setMargins(dp(34), 0, 0, 0);
        block.addView(accent, accentParams);
    }

    private LinearLayout buttonRow() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.START);
        row.setPadding(0, 0, 0, dp(4));
        return row;
    }

    private Button makeGridButton(String label) {
        Button button = new Button(this);
        button.setText(label.toUpperCase(Locale.US));
        button.setTextSize(11);
        button.setTextColor(COLOR_TEXT);
        button.setTypeface(Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD));
        button.setLetterSpacing(0.08f);
        button.setAllCaps(false);
        button.setSingleLine(false);
        button.setMinHeight(dp(48));
        button.setBackground(roundedRect(COLOR_PANEL_SOFT, COLOR_ACCENT_DARK, 1, 3));
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
        textView.setTextColor(COLOR_TEXT);
        textView.setTypeface(Typeface.MONOSPACE);
        textView.setTextIsSelectable(true);
        textView.setPadding(dp(14), dp(14), dp(14), dp(14));
        textView.setBackground(roundedRect(COLOR_PANEL, Color.rgb(37, 43, 57), 1, 4));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, dp(10), 0, 0);
        textView.setLayoutParams(params);
        return textView;
    }

    private TextView proseText() {
        TextView textView = new TextView(this);
        textView.setTextSize(14);
        textView.setTextColor(COLOR_MUTED);
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

        latestReport = deviceReport.toString()
                + "\n"
                + buildCompatibilityReport()
                + "\n"
                + sensorReport
                + "\n"
                + cameraReport;
        compatibilityView.setText(colorizeCompatibility(buildCompatibilityReport()));
        deviceReportView.setText(deviceReport.toString());
        sensorReportView.setText(sensorReport.toString());
        cameraReportView.setText(cameraReport.toString());
    }

    private SpannableString colorizeCompatibility(String report) {
        SpannableString styled = new SpannableString(report);
        colorToken(styled, report, "PASS", COLOR_PASS);
        colorToken(styled, report, "WARN", COLOR_WARN);
        colorToken(styled, report, "FAIL", COLOR_FAIL);
        colorToken(styled, report, "HIGH", COLOR_PASS);
        colorToken(styled, report, "MEDIUM", COLOR_WARN);
        colorToken(styled, report, "LOW", COLOR_FAIL);
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

    private String buildCompatibilityReport() {
        int score = 0;
        int maxScore = 7;
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

        int percent = Math.round((score * 100f) / maxScore);
        String grade;
        if (percent >= 85) {
            grade = "HIGH";
        } else if (percent >= 60) {
            grade = "MEDIUM";
        } else {
            grade = "LOW";
        }

        StringBuilder report = new StringBuilder();
        report.append("COMPATIBILITY CHECK\n");
        report.append("PiFinder Lite readiness: ").append(grade)
                .append(" (").append(percent).append("%)\n\n");
        for (String line : lines) {
            report.append(line).append("\n");
        }
        report.append("\nRecommendation: ");
        if (percent >= 85) {
            report.append("good candidate for mobile UI, GPS, IMU bridge, and experimental camera bridge.");
        } else if (percent >= 60) {
            report.append("usable as PiFinder companion; validate camera solving before relying on phone camera.");
        } else {
            report.append("usable mainly as UI/GPS companion; dedicated camera or IMU may be needed.");
        }
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
        liveSensorText.setLength(0);
        if (liveView != null) {
            liveView.setText("Live sensors stopped.");
        }
    }

    @SuppressLint("MissingPermission")
    private void startLocation() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
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

    private void stopLocation() {
        try {
            locationManager.removeUpdates(this);
        } catch (SecurityException ignored) {
        }
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
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

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }

    @Override
    public void onLocationChanged(Location location) {
        latestLocation = location;
        refreshReport();
    }

    private void copyReport() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("PiFinder diagnostics", latestReport));
        Toast.makeText(this, "Report copied", Toast.LENGTH_SHORT).show();
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
                captureView.setText("Save folder selected:\n" + outputTreeUri);
            }
        }
    }

    private void startCaptureTest(String testName, int format) {
        if (outputTreeUri == null) {
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
            String cameraId = "camera_sweep".equals(captureTestName)
                    ? cameraSweepIds.get(cameraSweepIndex)
                    : chooseBackCameraId();
            CameraCharacteristics c = cameraManager.getCameraCharacteristics(cameraId);
            captureJpegOrientation = jpegOrientationFor(c);
            Size captureSize = chooseCaptureSize(c, captureFormat);
            if (captureSize == null) {
                captureView.setText("No capture size available for camera " + cameraId + " format " + captureFormat);
                return;
            }

            captureReader = ImageReader.newInstance(
                    captureSize.getWidth(),
                    captureSize.getHeight(),
                    captureFormat,
                    Math.max(BURST_FRAMES, RAW_BURST_FRAMES)
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
            queuedRequests = new ArrayList<>();
            queuedLabels.clear();
            captureMetadata.setLength(0);
            captureMetadata.append("PiFinder capture test\n");
            captureMetadata.append("test=").append(captureTestName).append("\n");
            captureMetadata.append("cameraId=").append(cameraId).append("\n");
            captureMetadata.append("format=").append(captureFormatName(captureFormat)).append("\n");
            captureMetadata.append("size=").append(captureSize.getWidth()).append("x").append(captureSize.getHeight()).append("\n");
            captureMetadata.append("frames=").append(captureFrameCount).append("\n");
            captureMetadata.append("focusDiopters=0.0\n");
            captureMetadata.append("jpegOrientation=").append(captureJpegOrientation).append("\n");

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

            captureMetadata.append("exposureNs=").append(exposureNs).append("\n");
            captureMetadata.append("maxIso=").append(maxIso).append("\n");

            if ("day_test".equals(captureTestName)) {
                for (int i = 0; i < captureFrameCount; i++) {
                    queuedRequests.add(buildAutoDayRequest());
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
                        queuedRequests.add(buildStillRequest(exposureNs, iso));
                        queuedLabels.add("iso" + iso);
                    }
                }
            } else {
                for (int i = 0; i < captureFrameCount; i++) {
                    queuedRequests.add(buildStillRequest(exposureNs, maxIso));
                    queuedLabels.add("iso" + maxIso);
                }
            }

            runOnUiThread(() -> captureView.setText(
                    "Capturing " + captureFrameCount + " frames...\n"
                            + "Test: " + captureTestName + "\n"
                            + ("day_test".equals(captureTestName)
                            ? "Exposure: auto\nISO: auto"
                            : "Exposure: " + (exposureNs / 1_000_000.0) + " ms\nMax ISO: " + maxIso)
            ));

            captureSession.captureBurst(queuedRequests, new CameraCaptureSession.CaptureCallback() {
                @Override
                public void onCaptureCompleted(CameraCaptureSession session, CaptureRequest request, TotalCaptureResult result) {
                    captureMetadata.append("completedFrame\n");
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

    private CaptureRequest buildStillRequest(long exposureNs, int iso) throws CameraAccessException {
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
        captureMetadata.append("request exposureNs=").append(exposureNs)
                .append(" iso=").append(iso)
                .append(" format=").append(captureFormatName(captureFormat))
                .append("\n");
        return request.build();
    }

    private CaptureRequest buildAutoDayRequest() throws CameraAccessException {
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
        captureMetadata.append("request mode=auto_day")
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
            captureMetadata.append("savedFrames=").append(savedFrames).append("\n");
            captureMetadata.append("failedFrames=").append(failedFrames).append("\n");
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
        closeCaptureCamera();
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
