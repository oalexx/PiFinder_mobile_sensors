plugins {
    id("com.android.application")
}

android {
    namespace = "io.pifinder.mobile"
    compileSdk = 35

    defaultConfig {
        applicationId = "io.pifinder.mobile"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }
}
