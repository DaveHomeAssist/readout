"""
main.py — ReadOut entry point

Thread layout
─────────────
main thread   → pystray tray icon (macOS REQUIRES tray on main thread)
daemon thread → uvicorn FastAPI server
daemon thread → Kokoro model warm-up
daemon thread → Tkinter UI window (launched via tray setup callback)

Quitting the tray icon stops the process; all daemon threads die with it.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
import webbrowser

import pystray
from PIL import Image, ImageDraw
import uvicorn

from config import get_config, set_config, asset_path
import tts_engine


# ── Tray icon image (generated if icon.png not found) ────────────────────────

def _make_icon_image() -> Image.Image:
    icon_path = asset_path("icon.png")
    if os.path.exists(icon_path):
        return Image.open(icon_path).resize((64, 64))

    # Fallback: draw a simple soundwave icon programmatically
    img = Image.new("RGBA", (64, 64), (14, 14, 14, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = 32, 32
    heights = [6, 12, 22, 30, 22, 12, 6]
    n = len(heights)
    for i, h in enumerate(heights):
        x = cx - (n // 2) * 7 + i * 7
        draw.rectangle([x, cy - h, x + 4, cy + h],
                       fill=(184, 245, 66, 255))
    return img


# ── Server ────────────────────────────────────────────────────────────────────

def _run_server():
    cfg  = get_config()
    port = cfg.get("port", 7778)
    from server import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


# ── UI window ─────────────────────────────────────────────────────────────────

_ui_app = None
_ui_runtime = None


def _parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="ReadOut desktop TTS")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the local API + browser control panel without tray or Tk UI.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the browser control panel in headless mode.",
    )
    return parser.parse_args(argv)


def _get_control_url() -> str:
    cfg = get_config()
    return f"http://127.0.0.1:{cfg.get('port', 7778)}/control"


def _should_auto_open_control_panel() -> bool:
    value = os.getenv("READOUT_AUTO_OPEN_CONTROL", "").strip().lower()
    if value in {"0", "false", "no", "off"}:
        return False
    if value in {"1", "true", "yes", "on"}:
        return True
    return True


def _open_control_panel(delay: float = 0.0) -> None:
    def _open():
        if delay > 0:
            time.sleep(delay)
        webbrowser.open(_get_control_url())

    threading.Thread(target=_open, daemon=True).start()


def _get_ui_runtime():
    global _ui_runtime
    if _ui_runtime is not None:
        return _ui_runtime

    if os.getenv("READOUT_FORCE_TK", "").lower() in {"1", "true", "yes"}:
        _ui_runtime = (True, "")
        return _ui_runtime

    if os.getenv("READOUT_DISABLE_UI", "").lower() in {"1", "true", "yes"}:
        _ui_runtime = (False, "Desktop UI disabled via READOUT_DISABLE_UI.")
        return _ui_runtime

    if sys.platform != "darwin":
        _ui_runtime = (True, "")
        return _ui_runtime

    try:
        import _tkinter
        linked = subprocess.run(
            ["otool", "-L", _tkinter.__file__],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        if "libtcl9tk9.0.dylib" in linked or "libtcl9.0.dylib" in linked:
            _ui_runtime = (
                False,
                "Homebrew Tk 9 is linked into this Python build. Using browser control panel instead.",
            )
            return _ui_runtime
    except Exception:
        # If inspection fails, prefer attempting the UI rather than disabling it.
        pass

    _ui_runtime = (True, "")
    return _ui_runtime

def _launch_ui():
    global _ui_app
    from ui import ReadOutApp
    _ui_app = ReadOutApp()
    _ui_app.mainloop()


def _launch_ui_or_fallback(icon: pystray.Icon | None = None, *, open_browser: bool | None = None) -> bool:
    ui_ok, reason = _get_ui_runtime()
    if not ui_ok:
        should_open_browser = _should_auto_open_control_panel() if open_browser is None else open_browser
        if icon is not None:
            icon.notify(reason, "ReadOut")
        if should_open_browser:
            _open_control_panel(delay=1.0)
        return False

    _launch_ui()
    return True


def _warmup_model(icon: pystray.Icon | None = None) -> None:
    try:
        def _progress(msg: str):
            if icon is None:
                return
            if msg == "loading_model":
                icon.notify("Downloading voice model (~300 MB). One-time only…", "ReadOut")
            elif msg == "ready":
                icon.notify("Voice model ready.", "ReadOut")

        tts_engine.get_pipeline(on_progress=_progress)
    except Exception as exc:
        if icon is not None:
            icon.notify(f"Model error: {exc}", "ReadOut")


# ── Tray menu actions ─────────────────────────────────────────────────────────

def _on_show_window(icon, item):
    global _ui_app
    ui_ok, _reason = _get_ui_runtime()
    if not ui_ok:
        _open_control_panel()
        return

    if _ui_app is None or not _ui_app.winfo_exists():
        t = threading.Thread(target=_launch_ui, daemon=True)
        t.start()
    else:
        try:
            _ui_app.deiconify()
            _ui_app.lift()
            _ui_app.focus_force()
        except Exception:
            pass


def _on_stop_audio(icon, item):
    tts_engine.stop_audio()


def _on_open_control_panel(icon, item):
    _open_control_panel()


def _on_quit(icon, item):
    tts_engine.stop_audio()
    icon.stop()


def _voice_setter(voice_id: str):
    def _set(icon, item):
        set_config({"voice": voice_id})
    return _set


def _engine_setter(engine: str):
    def _set(icon, item):
        set_config({"engine": engine})
    return _set


# ── Tray ──────────────────────────────────────────────────────────────────────

def _build_tray() -> pystray.Icon:
    img   = _make_icon_image()
    voices = tts_engine.list_voices()
    ui_ok, _reason = _get_ui_runtime()

    voice_items = [
        pystray.MenuItem(v, _voice_setter(v))
        for v in voices
    ]

    menu_items = [
        pystray.MenuItem("ReadOut — Running", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Show Window" if ui_ok else "Open Control Panel", _on_show_window),
    ]
    if ui_ok:
        menu_items.append(pystray.MenuItem("Open Control Panel", _on_open_control_panel))
    menu_items.extend([
        pystray.MenuItem("Stop Audio",  _on_stop_audio),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Voice",  pystray.Menu(*voice_items)),
        pystray.MenuItem("Engine", pystray.Menu(
            pystray.MenuItem("Kokoro (local)", _engine_setter("kokoro")),
            pystray.MenuItem("OpenAI TTS",     _engine_setter("openai")),
            pystray.MenuItem("ElevenLabs",      _engine_setter("elevenlabs")),
        )),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", _on_quit),
    ])

    menu = pystray.Menu(*menu_items)

    return pystray.Icon("ReadOut", img, "ReadOut TTS", menu)


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def _setup(icon: pystray.Icon):
    """Runs in a background thread once the tray is ready."""
    icon.visible = True

    # 1. Start FastAPI server
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    # 2. Warm up Kokoro model
    warmup_thread = threading.Thread(target=lambda: _warmup_model(icon), daemon=True)
    warmup_thread.start()

    # 3. Launch the UI window
    cfg = get_config()
    if cfg.get("window_visible", True):
        launched = _launch_ui_or_fallback(icon, open_browser=None)
        if not launched and not _should_auto_open_control_panel():
            icon.notify(
                f"ReadOut is running at {_get_control_url()}. Use the tray menu to open the control panel.",
                "ReadOut",
            )


def _run_headless(open_browser: bool = True):
    warmup_thread = threading.Thread(target=_warmup_model, daemon=True)
    warmup_thread.start()
    if open_browser:
        _open_control_panel(delay=1.0)
    _run_server()


def main(argv: list[str] | None = None):
    # On macOS M1-M4, enable Metal fallback for PyTorch
    if sys.platform == "darwin":
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    args = _parse_args(argv)
    if args.headless or os.getenv("READOUT_HEADLESS", "").lower() in {"1", "true", "yes"}:
        _run_headless(open_browser=not args.no_browser)
        return

    icon = _build_tray()
    # pystray.Icon.run() MUST be on the main thread on macOS.
    # setup= runs in a background thread once the runloop is ready.
    icon.run(setup=_setup)


if __name__ == "__main__":
    main()
