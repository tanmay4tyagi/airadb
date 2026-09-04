# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('public/app.html', 'public'),
        ('public/app.js', 'public'),
        ('public/style.css', 'public'),
        ('public/index.html', 'public'),
        ('public/landing.css', 'public'),
        ('public/icon.jpg', 'public'),
        ('public/icon.svg', 'public'),
        ('public/manifest.json', 'public'),
        ('public/qrcode.min.js', 'public'),
    ],
    hiddenimports=['zeroconf', 'psutil', 'PyQt6', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['webview', 'clr', 'pythonnet', 'clr_loader'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AirADB-Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AirADB-Studio',
)
