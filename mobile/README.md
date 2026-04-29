# PiFinder Mobile Diagnostics

Small native Android app for checking whether a phone can act as a PiFinder
sensor/camera companion.

The app reports:

- Motion/orientation sensors exposed by Android.
- Live accelerometer, gyroscope, rotation vector, and game rotation vector data.
- GPS/location sample.
- Camera2 capabilities for each camera ID, including manual sensor controls,
  RAW support, exposure range, ISO range, focus distance, focal lengths, sensor
  size, and output formats.

## Open

Open the `mobile` folder in Android Studio and run the `app` configuration on
the phone.

## Why this exists

Before building the PiFinder mobile bridge, we need to know what the specific
phone exposes through public Android APIs. Samsung's own camera apps may have
private access that third-party apps do not, so this diagnostic app checks the
real Camera2 and SensorManager surface available to us.
