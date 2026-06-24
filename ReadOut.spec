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

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

block_cipher = None
entry_script = 'main_app.py' if sys.platform == 'darwin' else 'main.py'
extra_datas = [
    *collect_data_files('kokoro', include_py_files=True),
    *collect_data_files('en_core_web_sm', include_py_files=True),
    *copy_metadata('en_core_web_sm'),
    *collect_data_files('misaki'),
    *collect_data_files('espeakng_loader'),
    *collect_data_files('language_tags'),
]
extra_binaries = collect_dynamic_libs('espeakng_loader')
tk_hiddenimports = []
if sys.platform != 'darwin':
    tk_hiddenimports = [
        'tkinter',
        'tkinter.ttk',
        'tkinter.font',
    ]

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
        'en_core_web_sm',
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

        # ReadOut pluggable engines
        'engines',
        'engines.base',
        'engines.registry',
        'engines.kokoro',
        'engines.openai',
        'engines.elevenlabs',

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

if sys.platform == 'win32':
    system32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
    runtime_overrides = {
        name: os.path.join(system32, name)
        for name in ('msvcp140.dll', 'ucrtbase.dll', 'vcruntime140.dll')
    }

    def _override_windows_runtime(entry):
        dest_name, source_name, typecode = entry
        source_override = runtime_overrides.get(os.path.basename(dest_name).lower())
        if source_override and os.path.exists(source_override):
            return dest_name, source_override, typecode
        return entry

    a.binaries = [_override_windows_runtime(entry) for entry in a.binaries]

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
