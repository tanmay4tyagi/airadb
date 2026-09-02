# AirADB Studio PowerShell Launcher
Set-Location -Path $PSScriptRoot
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   🚀 AirADB Studio - Android Wireless Debugging Hub" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python 3 is not installed or not found in PATH." -ForegroundColor Red
    pause
    exit 1
}

python server.py
