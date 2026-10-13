# -*- mode: python ; coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath('src'))
from tray_icon import build_ico

os.makedirs('assets', exist_ok=True)
build_ico(os.path.abspath('assets/app_icon.ico'))

a = Analysis(
    ['src/ComputerLock.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'pystray', 'pystray._win32', 'pystray._util.win32'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ComputerLock',
    icon='assets/app_icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
