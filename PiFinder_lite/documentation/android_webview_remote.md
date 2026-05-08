# Android WebView Remote

Issue: [#19 Add Android WebView shell for PiFinder Remote](https://github.com/oalexx/PiFinder_mobile_sensors/issues/19)

## Goal

Add a simple Android entry point that opens the existing PiFinder `/remote` page
inside the mobile app.

This does not add GPS, IMU, camera upload, or new PiFinder backend endpoints.
It only wraps the existing web remote.

## Android Changes

Files changed:

- `mobile/app/src/main/AndroidManifest.xml`
- `mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java`

Manifest changes:

- Added `android.permission.INTERNET`.
- Enabled `android:usesCleartextTraffic="true"` so local PiFinder HTTP URLs such
  as `http://192.168.x.x/remote` can load in WebView.

UI changes:

- Added a `PIFINDER REMOTE` button on the app home screen.
- Added a `PIFINDER REMOTE` screen with:
  - editable PiFinder base URL;
  - persisted URL preference;
  - `Test Connection` action against `/mobile/status`;
  - `Send Profile` action against `/mobile/profile`;
  - `Send GPS` action against `/mobile/gps`;
  - `Send IMU Batch` action against `/mobile/imu`;
  - `Open Remote` action;
  - embedded WebView.
- Opening the remote switches to a dedicated WebView screen so the PiFinder
  controls can use nearly the full display.
- The dedicated WebView screen has a small `Back` / `Reload` toolbar.

WebView behavior:

- Loads `<base-url>/remote?embedded=1`.
- Uses the same persisted base URL as Mobile Bridge actions.
- Enables JavaScript and DOM storage for the existing PiFinder remote page.
- Leaves WebView overview/wide-viewport scaling disabled and starts at 100%
  scale. PiFinder's embedded remote already provides its own mobile viewport,
  and Android overview mode can shrink the whole remote into a tiny desktop-like
  page.
- Shows a clear connection failure status if the main frame cannot load.
- Android back navigation returns from the full-screen WebView to the connection
  screen, or navigates WebView history first if available.
- Hides the app title/subtitle while the full-screen remote is active.
- Gives touch gestures to the WebView while it is being touched, so pages opened
  from the PiFinder header, such as the user guide, can scroll inside the
  WebView instead of dragging the app container.

PiFinder web behavior:

- Normal `/remote` remains unchanged.
- `/remote?embedded=1` skips the PiFinder web header/footer so the Android
  WebView can prioritize the screen image and keypad.
- `/remote?embedded=1` still returns a complete minimal HTML document with the
  mobile viewport meta tag and PiFinder CSS links. This keeps the embedded page
  styled the same way as the browser version while avoiding the full navigation
  chrome.

## Usage

1. Start PiFinder with the web server enabled.
2. Open the Android app.
3. Tap `PIFINDER REMOTE`.
4. Enter the PiFinder base URL, for example:

   ```text
   http://192.168.8.167:8080
   ```

   or:

   ```text
   http://pifinder.local
   ```

5. Tap `Open Remote`.
6. Log in using the PiFinder web password if prompted.

Tap `Test Connection` before opening the remote to verify that the app can reach
PiFinder's Mobile Bridge API:

```text
<base-url>/mobile/status
```

Successful tests show the API version, server UTC time, and current bridge
capability summary. Wrong IP/port/offline cases show an HTTP or network failure
message in the remote status card.

Tap `Send Profile` to POST the current Compatibility Tester profile JSON to
PiFinder:

```text
<base-url>/mobile/profile
```

Successful sends show the stored debug filename and server receive timestamp.
This is an explicit one-shot action; the app does not run continuous background
profile sync.

Tap `Send GPS` to POST one Android location fix to PiFinder:

```text
<base-url>/mobile/gps
```

The app uses the latest cached Android location if available. If no cached fix
exists, it requests a single GPS/network location update and sends the first fix
that arrives. This is an explicit one-shot action; the app does not start a
continuous background GPS bridge.

Tap `Send IMU Batch` to capture a short orientation sample batch and POST it to
PiFinder:

```text
<base-url>/mobile/imu
```

The app captures rotation vector and game rotation vector samples when available
for up to two seconds, then sends the bounded batch. This is diagnostic data for
later drift/confidence analysis; it is not continuous streaming and does not
affect PiFinder pointing.

`Reload` is useful when PiFinder restarts, the phone reconnects to Wi-Fi, or the
web remote gets stuck after a temporary connection failure.

The app appends `/remote` automatically. If the user enters a URL ending in
`/remote`, the app normalizes it back to the base URL before loading.

## Validation

Build command used locally:

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio1\jbr'
.\gradlew.bat :app:assembleDebug
```

Result:

```text
BUILD SUCCESS
```

Gradle printed a deprecation note for existing Android APIs, but compilation
succeeded.

Embedded remote validation:

```text
HasViewport True
HasStyleNew True
HasMaterialize True
HasNav False
HasRemoteShell True
```

## Remaining Device Validation

Install the debug APK and verify on a phone:

1. App opens normally.
2. `PIFINDER REMOTE` appears on the home screen.
3. Base URL is saved after opening.
4. `Test Connection` succeeds against `/mobile/status`.
5. `Send Profile` succeeds against `/mobile/profile`.
6. `Send GPS` succeeds against `/mobile/gps`.
7. `Send IMU Batch` succeeds against `/mobile/imu`.
8. Wrong IP/port/offline state shows a clear failure message.
9. `/remote` loads in WebView on the same Wi-Fi as PiFinder.
10. Login works.
11. Remote buttons work.
12. Back returns from the full-screen WebView to the connection screen.

## Upstream Impact

No PiFinder backend changes are required. This issue only touches the Android
mobile companion app.
