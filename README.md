# 🚀 AirADB Studio

> **The modern, cross-device Wireless Android Debugging Assistant & Control Hub.**  
> Pair, connect, manage, mirror, and debug Android devices over Wi-Fi without memorizing terminal commands.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20Android-green.svg)]()
[![WebUSB](https://img.shields.io/badge/WebUSB-Ready-orange.svg)]()

---

## ⚡ Instant 1-Line Quick Start (For Anyone)

Anyone can launch and use AirADB instantly without manual setup:

### 🪟 Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/tanmay4tyagi/airadb/main/install.ps1 | iex
```

### 🍎 macOS & 🐧 Linux (Terminal)
```bash
curl -fsSL https://raw.githubusercontent.com/tanmay4tyagi/airadb/main/install.sh | bash
```

### 🐍 Python Package (pip)
```bash
pip install -e .
airadb
```

### 🐳 Docker (Containerized)
```bash
docker build -t airadb .
docker run -d -p 8765:8765 --net=host airadb
```

---

## 🌟 Key Features

1. **📱 Android 11+ Dual-Port Pairing Wizard**:
   - Matches the official Android "Pair device with pairing code" interface.
   - Enter your Pairing IP:Port and 6-digit Code $\rightarrow$ AirADB handles pairing and connects automatically.
2. **📲 Mobile Companion Mode & 1-Tap Settings**:
   - Open `http://<your-pc-ip>:8765` directly on your phone's browser.
   - 1-Tap shortcuts to instantly launch **Developer Options**, **Wireless Settings**, and **Phone Settings** directly on your phone.
3. **⚡ 1-Click USB-to-Wireless Switch (Android 9 to 15)**:
   - Plug your phone in via USB once $\rightarrow$ AirADB queries its Wi-Fi IP automatically, switches to `adb tcpip 5555`, and connects over Wi-Fi.
   - Unplug your USB cable and enjoy wireless debugging!
4. **🛠️ Connected Devices Studio**:
   - **Live Cards**: Phone Model, Battery Level %, Android OS Version, and IP Address.
   - **Wireless Screen Capture**: Capture live high-res screenshots from your phone to your PC.
   - **Wireless Logcat Streamer**: Live log console with search filter and level selectors (Error, Warn, Info).
   - **Drag-and-Drop APK Installer**: Drop any `.apk` file into your browser to install it wirelessly on your phone.
   - **Remote Navigation Controls**: Home, Back, Recents, Power/Sleep, Volume, Settings, and custom shell command execution.
5. **🌐 Cloud & Remote Hosted Ready (Render / GitHub Pages)**:
   - Deploy the responsive web dashboard to **Render** or **GitHub Pages**.
   - Seamlessly routes commands directly to your local PC or connects via WebUSB.
6. **🔍 Local Network Scanner**:
   - Scans your Wi-Fi subnet for devices broadcasting ADB on port 5555 or mDNS services.
7. **⬇️ Auto-ADB Setup**:
   - If ADB is missing from your system, AirADB automatically downloads and configures Google's official Android Platform-Tools with a single click.

---

## 🌐 Deploying Online (Free Cloud Platforms)

### Deploy to Render (Full Backend + ADB Docker)
1. Fork or push this repository to your GitHub account.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New + > Blueprint** and select your repository.
4. Render automatically detects [`render.yaml`](./render.yaml) and [`Dockerfile`](./Dockerfile) to deploy the cloud container.

### Deploy to GitHub Pages (Static Web App)
1. In your GitHub repository settings, go to **Settings > Pages**.
2. Under **Build and deployment > Source**, select **GitHub Actions**.
3. Push to `main`, and GitHub Actions will automatically deploy the `./public` directory.

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
5. After pairing succeeds, enter the **Connection Port** (e.g. `192.168.1.5:41235`) and click **Connect**.

### Method B: 1-Click USB Switch (Works on all Android versions)
1. Plug your phone into your PC with a USB cable.
2. Allow **USB Debugging** on the phone screen if prompted.
3. In AirADB, open the **"1-Click USB Switch"** tab and click **"Convert to Wireless ADB Now"**.
4. Unplug the USB cable!

---

## 💡 Troubleshooting Tips

- **Same Wi-Fi Network**: Ensure your PC and Android phone are connected to the same Wi-Fi router.
- **AP / Client Isolation**: Some Wi-Fi routers have "AP Isolation" enabled, which blocks devices from communicating with each other. Disable AP isolation in router settings if needed.
- **Remote Access Outside Home Wi-Fi**: To access your home PC's AirADB from anywhere over the internet:
  ```powershell
  npx localtunnel --port 8765
  ```

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
