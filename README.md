# 🚀 AirADB Studio — Android Wireless Debugging Assistant & Control Hub

An intuitive, modern, zero-dependency desktop & web application for Windows designed to effortlessly pair, connect, manage, and debug your Android device over Wi-Fi without memorizing terminal commands.

---

## 🌟 Key Features

1. **📱 Android 11+ Dual-Port Pairing Wizard**:
   - Matches the official Android "Pair device with pairing code" interface.
   - Enter your Pairing IP:Port and 6-digit Code -> AirADB handles pairing and connects automatically.
2. **⚡ 1-Click USB-to-Wireless Switch (Android 9/10/11/12/13/14/15)**:
   - Plug your phone in via USB once -> AirADB queries its Wi-Fi IP automatically, switches to `adb tcpip 5555`, and connects over Wi-Fi.
   - Unplug your USB cable and enjoy wireless debugging!
3. **🛠️ Connected Devices Studio**:
   - **Live Cards**: Phone Model, Battery Level %, Android OS Version, and IP Address.
   - **Wireless Screen Capture**: Capture live high-res screenshots from your phone to your PC.
   - **Wireless Logcat Streamer**: Live log console with search filter and level selectors (Error, Warn, Info).
   - **Drag-and-Drop APK Installer**: Drop any `.apk` file into your browser to install it wirelessly on your phone.
   - **Remote Navigation Controls**: Home, Back, Recents, Power/Sleep, Volume, Settings, and custom shell command execution.
4. **🔍 Local Network Scanner**:
   - Scans your Wi-Fi subnet for devices broadcasting ADB on port 5555 or mDNS services.
5. **⬇️ Auto-ADB Setup**:
   - If ADB is missing from your system, AirADB will download and configure official Google Android Platform-Tools with a single click.
6. **💻 Interactive Terminal CLI**:
   - Includes a standalone terminal wizard (`python cli.py`) for quick command-line use.

---

## 🚀 How to Run

### Option 1: Web GUI Dashboard (Recommended)
Double-click `start.bat` (or run `python server.py` in PowerShell/Terminal).
Your browser will automatically open:
```
http://localhost:8765
```

### Option 2: Interactive Terminal CLI
Run:
```powershell
python cli.py
```

---

## 📖 Step-by-Step Wireless Debugging Guide

### Method A: Android 11+ (No USB cable needed)
1. **Enable Developer Options**: Go to phone **Settings > About Phone** and tap **Build Number** 7 times.
2. **Enable Wireless Debugging**: Go to **Settings > System > Developer Options > Wireless debugging** and toggle it **ON**.
3. **Open Pairing Dialog**: Tap on **"Pair device with pairing code"**.
4. In AirADB:
   - Enter the **IP & Pairing Port** shown in the popup (e.g. `192.168.1.5:37123`).
   - Enter the **6-digit pairing code** (e.g. `482194`).
   - Click **Pair Device**.
5. After pairing succeeds, look at the main Wireless Debugging screen on your phone for the **Connection Port** (e.g. `192.168.1.5:41235`), enter it into AirADB, and click **Connect**.

### Method B: 1-Click USB Switch (Works on all Android versions)
1. Plug your phone into your PC with a USB cable.
2. Allow **USB Debugging** on the phone screen if prompted.
3. In AirADB, open the **"1-Click USB Switch"** tab and click **"Convert to Wireless ADB Now"**.
4. Unplug the USB cable!

---

## 💡 Troubleshooting Tips

- **Same Wi-Fi Network**: Ensure your PC and Android phone are connected to the same Wi-Fi router.
- **AP / Client Isolation**: Some Wi-Fi routers have "AP Isolation" or "Guest Network" enabled, which blocks devices from communicating with each other. Disable AP isolation in your router settings.
- **Firewall Prompt**: If Windows Firewall asks for permission for ADB or Python, select "Allow on Private Networks".
