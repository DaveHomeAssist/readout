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

import os
import sys
import threading
import time

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

def _launch_ui():
    """Launch Tkinter UI. Disabled on macOS 26+ where Tk crashes when
    combined with pystray's NSApplication (macOSVersion selector missing)."""
    global _ui_app
    if sys.platform == "darwin":
        try:
            import platform
            ver = tuple(int(x) for x in platform.mac_ver()[0].split(".")[:2])
            if ver >= (26, 0):
                import logging
                logging.warning(
                    "Tkinter UI disabled on macOS %s (Tk/NSApplication conflict). "
                    "Use the tray icon or Chrome extension.", platform.mac_ver()[0]
                )
                return
        except Exception:
            pass
    from ui import ReadOutApp
    _ui_app = ReadOutApp()
    _ui_app.mainloop()


# ── Tray menu actions ─────────────────────────────────────────────────────────

def _on_show_window(icon, item):
    global _ui_app
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

    voice_items = [
        pystray.MenuItem(v, _voice_setter(v))
        for v in voices
    ]

    menu = pystray.Menu(
        pystray.MenuItem("ReadOut — Running", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Show Window", _on_show_window),
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
    )

    return pystray.Icon("ReadOut", img, "ReadOut TTS", menu)


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def _setup(icon: pystray.Icon):
    """Runs in a background thread once the tray is ready."""
    icon.visible = True

    # 1. Start FastAPI server
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    # 2. Warm up Kokoro model
    def _warmup():
        try:
            def _progress(msg: str):
                if msg == "loading_model":
                    icon.notify("Downloading voice model (~300 MB). One-time only…",
                                "ReadOut")
                elif msg == "ready":
                    icon.notify("Voice model ready.", "ReadOut")
            tts_engine.get_pipeline(on_progress=_progress)
        except Exception as exc:
            icon.notify(f"Model error: {exc}", "ReadOut")

    warmup_thread = threading.Thread(target=_warmup, daemon=True)
    warmup_thread.start()

    # 3. Launch the UI window
    _launch_ui()


def main():
    # On macOS M1-M4, enable Metal fallback for PyTorch
    if sys.platform == "darwin":
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    icon = _build_tray()
    # pystray.Icon.run() MUST be on the main thread on macOS.
    # setup= runs in a background thread once the runloop is ready.
    icon.run(setup=_setup)


if __name__ == "__main__":
    main()
