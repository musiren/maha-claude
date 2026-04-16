# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for maha-client
#
# Build:
#   cd client && python -m PyInstaller maha-client.spec
#
# Output: client/dist/maha-client  (Linux/macOS)
#         client/dist/maha-client.exe  (Windows)
#
# config.json is bundled as a default but the exe also checks
# for a config.json placed next to it at runtime (takes priority).

a = Analysis(
    ["web_main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("web/index.html", "web"),
        ("config.json", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "email", "html", "http"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="maha-client",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
