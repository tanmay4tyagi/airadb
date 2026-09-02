# ==============================================================================
# AirADB Studio - 1-Line Universal Windows Installer & Launcher
# Usage: irm https://raw.githubusercontent.com/tanmay4tyagi/airadb/main/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "            AirADB Studio - Instant Setup                 " -ForegroundColor Green
Write-Host "      Cross-Device Wireless Android Debugging Assistant   " -ForegroundColor DarkCyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Target install directory
$InstallDir = Join-Path $HOME ".airadb"

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Check for Python
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
}

if (-not $PythonCmd) {
    Write-Host "[!] Python 3 not detected. Attempting to install via winget..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.11 --exact --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $PythonCmd = "python"
    } else {
        Write-Host "[-] Please install Python 3 from https://python.org and rerun this script." -ForegroundColor Red
        Exit 1
    }
}

Write-Host "[+] Python detected: $(& $PythonCmd --version)" -ForegroundColor Green

# Download or Update Repository
Write-Host "[*] Downloading latest AirADB files..." -ForegroundColor Cyan
$ZipUrl = "https://github.com/tanmay4tyagi/airadb/archive/refs/heads/main.zip"
$ZipPath = Join-Path $InstallDir "airadb-latest.zip"

try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
    Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
    $ExtractedFolder = Join-Path $InstallDir "airadb-main"
    Get-ChildItem -Path $ExtractedFolder | Move-Item -Destination $InstallDir -Force
    Remove-Item -Path $ExtractedFolder -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $ZipPath -Force -ErrorAction SilentlyContinue
} catch {
    Write-Host "[!] Note: GitHub repo download will activate once repository is pushed." -ForegroundColor Yellow
}

# Create Desktop Shortcut
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "AirADB Studio.bat"
$LauncherContent = @"
@echo off
title AirADB Studio
cd /d "$InstallDir"
$PythonCmd server.py
pause
"@
Set-Content -Path $ShortcutPath -Value $LauncherContent -Force
Write-Host "[+] Created Desktop shortcut: AirADB Studio.bat" -ForegroundColor Green

# Launch AirADB
Write-Host ""
Write-Host "[🚀] Starting AirADB Studio..." -ForegroundColor Green
Set-Location -Path $InstallDir
& $PythonCmd server.py
