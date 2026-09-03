# AirADB Studio - Android Companion App

This folder contains the native Android application source code for **AirADB Studio**.

## 📱 Features of the Android App
- **Real-Time IP Display**: Detects and displays your phone's active Wi-Fi IP address.
- **1-Tap Developer Options**: Instantly opens `Settings > Developer Options` on your phone without digging through menus.
- **1-Tap Wireless Debugging**: Jumps directly to `Settings > System > Wireless debugging`.
- **Integrated Companion UI**: Embedded full-featured AirADB dashboard with zero browser URL bar or clutter.

## 🛠️ How to Build the APK

### Method 1: Android Studio (Easiest)
1. Open **Android Studio**.
2. Click **Open Project** and select this `android/` directory.
3. Click **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
4. Your APK will be generated at `app/build/outputs/apk/debug/app-debug.apk`.
5. Transfer and install it on any Android phone!

### Method 2: Command Line (Gradle)
If you have Android SDK and Gradle installed:
```bash
cd android
./gradlew assembleDebug
```
The APK will be generated in `app/build/outputs/apk/debug/`.
