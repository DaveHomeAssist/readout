# ReadOut.spec
# PyInstaller spec file for ReadOut TTS
#
# Usage:
#   macOS:   pyinstaller ReadOut.spec
#   Windows: pyinstaller ReadOut.spec
#
# The spec handles:
#   - Bundling all assets (icon.png)
#   - Hidden imports PyInstaller misses for kokoro/sounddevice/pystray
#   - macOS .app bundle with correct plist entries
#   - Windows windowed exe (no console)

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None
entry_script = 'main_app.py' if sys.platform == 'darwin' else 'main.py'
extra_datas = [
    *collect_data_files('misaki'),
    *collect_data_files('espeakng_loader'),
    *collect_data_files('language_tags'),
]
extra_binaries = collect_dynamic_libs('espeakng_loader')
# Tk was retired (the desktop UI is the web control panel); no tkinter imports.
tk_hiddenimports = []

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [entry_script],
    pathex=['.'],
    binaries=[
        *extra_binaries,
    ],
    datas=[
        # Bundle the assets folder
        ('assets', 'assets'),
        *extra_datas,
    ],
    hiddenimports=[
        # kokoro / torch
        'kokoro',
        'misaki',
        'misaki.en',
        'espeakng_loader',
        'language_tags',
        'phonemizer',
        'phonemizer.backend',
        'phonemizer.backend.espeak.wrapper',
        'torch',
        'torch.nn',
        'torchaudio',

        # sounddevice needs these at runtime
        'sounddevice',
        'soundfile',
        'cffi',
        '_cffi_backend',

        # FastAPI / uvicorn internals
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'pydantic',
        'anyio',
        'anyio._backends._asyncio',
        'starlette',
        'starlette.routing',

        # pystray backends
        'pystray._darwin',   # macOS
        'pystray._win32',    # Windows
        'pystray._xorg',     # Linux fallback

        # Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',

        # stdlib
        'json',
        'threading',
        'urllib.request',
        'urllib.error',
        *tk_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim unused large packages
        'matplotlib',
        'notebook',
        'IPython',
        'scipy',
        'pandas',
        'sklearn',
        'cv2',
        *(["tkinter"] if sys.platform == 'darwin' else []),
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── PYZ ───────────────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ReadOut',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No terminal window
    windowed=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,       # None = native arch
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.icns' if sys.platform == 'darwin' else 'assets/icon.ico',
)

# ── COLLECT ───────────────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ReadOut',
)

# ── macOS .app BUNDLE ─────────────────────────────────────────────────────────
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='ReadOut.app',
        icon='assets/icon.icns',
        bundle_identifier='dev.digitalfootprints.readout',
        info_plist={
            'NSPrincipalClass':               'NSApplication',
            'NSAppleScriptEnabled':           False,
            'NSHighResolutionCapable':        True,
            'LSUIElement':                    True,   # Tray-only: no Dock icon
            'NSMicrophoneUsageDescription':   'ReadOut does not use the microphone.',
            'CFBundleShortVersionString':     '1.0.0',
            'CFBundleVersion':               '1',
            'CFBundleName':                  'ReadOut',
            'CFBundleDisplayName':           'ReadOut',
            'NSHumanReadableCopyright':      '© 2026 Digital Footprints LLC',
        },
    )
