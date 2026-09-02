#!/usr/bin/env bash
# ==============================================================================
# AirADB Studio - 1-Line Universal macOS / Linux Installer & Launcher
# Usage: curl -fsSL https://raw.githubusercontent.com/tanmay4tyagi/airadb/main/install.sh | bash
# ==============================================================================

set -e

echo ""
echo "=========================================================="
echo "            AirADB Studio - Instant Setup                 "
echo "      Cross-Device Wireless Android Debugging Assistant   "
echo "=========================================================="
echo ""

INSTALL_DIR="$HOME/.airadb"
mkdir -p "$INSTALL_DIR"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3 is required. Please install python3 (e.g. brew install python or sudo apt install python3)."
    exit 1
fi

echo "[+] Python 3 detected: $(python3 --version)"

# Download latest AirADB
echo "[*] Downloading latest AirADB..."
ZIP_URL="https://github.com/tanmay4tyagi/airadb/archive/refs/heads/main.zip"
curl -fsSL "$ZIP_URL" -o "$INSTALL_DIR/airadb-latest.zip" || true

if [ -f "$INSTALL_DIR/airadb-latest.zip" ]; then
    unzip -q -o "$INSTALL_DIR/airadb-latest.zip" -d "$INSTALL_DIR"
    cp -rf "$INSTALL_DIR/airadb-main/"* "$INSTALL_DIR/" 2>/dev/null || true
    rm -rf "$INSTALL_DIR/airadb-main" "$INSTALL_DIR/airadb-latest.zip"
fi

echo "[🚀] Starting AirADB Studio..."
cd "$INSTALL_DIR"
python3 server.py
