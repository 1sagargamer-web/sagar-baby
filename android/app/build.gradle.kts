plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.sagar.videodownloader"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.sagar.videodownloader"
        minSdk = 26
        targetSdk = 35
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = "2.0." + (System.getenv("GITHUB_RUN_NUMBER") ?: "0")

        // Owner panel / remote config ke liye
        buildConfigField("String", "REPO_OWNER", "\"1sagargamer-web\"")
        buildConfigField("String", "REPO_NAME", "\"sagar-baby\"")
        buildConfigField("String", "CONFIG_BRANCH", "\"main\"")
        buildConfigField("String", "CONFIG_PATH", "\"config/sagar-saver.json\"")
    }

    // Fixed key GitHub Secrets se aati hai (repo me kabhi commit mat karna).
    // Secret na ho to debug key se sign hota hai.
    val ksPath = System.getenv("SIGNING_KEYSTORE_PATH")
    signingConfigs {
        if (ksPath != null) {
            create("sagar") {
                storeFile = file(ksPath)
                storePassword = System.getenv("SIGNING_STORE_PASSWORD")
                keyAlias = System.getenv("SIGNING_KEY_ALIAS")
                keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
            }
        }
    }

    // Har phone type ke liye alag (chhota) APK banega
    splits {
        abi {
            isEnable = true
            reset()
            include("arm64-v8a", "armeabi-v7a")
            isUniversalApk = false
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName(if (ksPath != null) "sagar" else "debug")
        }
    }

    // youtubedl-android ko native libs extract karni padti hain
    packaging {
        jniLibs { useLegacyPackaging = true }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    buildFeatures {
        viewBinding = true
        buildConfig = true
    }
}

dependencies {
    implementation("io.github.junkfood02.youtubedl-android:library:0.18.1")
    implementation("io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1")

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("androidx.work:work-runtime-ktx:2.9.1")
}
