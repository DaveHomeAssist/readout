"""
ui.py — ReadOut main window
Matches the screenshot exactly: dark bg, acid-green accent, traffic lights,
voice engine tabs, text area, voice/speed controls, waveform, playback bar,
recent queue. Talks to the local FastAPI server at localhost:7778.
"""
from __future__ import annotations

import os
import sys
import json
import threading
import time
import math
import tkinter as tk
from tkinter import ttk, font as tkfont
import urllib.request
import urllib.error
import urllib.parse

# ── Constants ─────────────────────────────────────────────────────────────────
PORT       = 7778
BASE_URL   = f"http://localhost:{PORT}"

# Colours — lifted straight from the screenshot
C_BG       = "#0e0e0e"
C_SURFACE  = "#161616"
C_SURFACE2 = "#1e1e1e"
C_SURFACE3 = "#262626"
C_BORDER   = "#2a2a2a"
C_ACCENT   = "#b8f542"      # acid green
C_TEXT     = "#e8e8e8"
C_MUTED    = "#666666"
C_DIM      = "#999999"
C_RED      = "#ff5252"
C_ORANGE   = "#ffaa52"
C_BLUE     = "#52a8ff"

# Engine configs
ENGINES = {
    "kokoro":     {"label": "Kokoro",     "badge": "LOCAL",  "badge_fg": C_ACCENT, "badge_bg": "#1a2a0a"},
    "openai":     {"label": "OpenAI",     "badge": "API",    "badge_fg": C_BLUE,   "badge_bg": "#0a1a2a"},
    "elevenlabs": {"label": "ElevenLabs", "badge": "API",    "badge_fg": C_ORANGE, "badge_bg": "#2a1a0a"},
}

VOICES_BY_ENGINE = {
    "kokoro": [
        "af_heart (warm, feminine)", "af_sky (bright, clear)", "af_bella (expressive)",
        "af_sarah (natural)", "af_nicole (soft)", "af_jessica (conversational)",
        "af_nova (energetic)", "af_river (smooth)", "af_kore (precise)",
        "am_adam (deep, neutral)", "am_echo (casual, male)", "am_michael (warm, male)",
        "am_fenrir (strong, male)", "bf_emma (British, feminine)", "bf_isabella (British, warm)",
        "bm_george (British, authoritative)", "bm_lewis (British, conversational)",
    ],
    "openai":     ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
    "elevenlabs": ["Rachel", "Domi", "Bella", "Antoni", "Elli", "Josh", "Arnold", "Adam", "Sam"],
}

NUM_BARS = 52


def _request_json(endpoint: str, method: str, payload: dict | None = None, timeout: int = 10) -> dict:
    url  = BASE_URL + endpoint
    data = json.dumps(payload or {}).encode()
    req  = urllib.request.Request(url, data=data,
                                   headers={"Content-Type": "application/json"},
                                   method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _post(endpoint: str, payload: dict | None = None, timeout: int = 120) -> dict:
    return _request_json(endpoint, "POST", payload, timeout=timeout)


def _patch(endpoint: str, payload: dict | None = None) -> dict:
    return _request_json(endpoint, "PATCH", payload, timeout=5)


def _get(endpoint: str) -> dict:
    try:
        with urllib.request.urlopen(BASE_URL + endpoint, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def _voice_id(label: str) -> str:
    return label.split(" ")[0] if label else ""


def _voice_label_for_engine(engine: str, voice_id: str | None) -> str | None:
    if not voice_id:
        return None
    for label in VOICES_BY_ENGINE.get(engine, []):
        if _voice_id(label) == voice_id:
            return label
    return voice_id


def _catalogue_voice_label(voice: dict) -> str | None:
    voice_id = str(voice.get("id", "")).strip()
    label = str(voice.get("label", "")).strip()
    if not voice_id:
        return None
    if not label or label.lower() == voice_id.lower():
        return voice_id
    if label.startswith(voice_id):
        return label
    return f"{voice_id} ({label})"


def _voice_map_from_catalogue(data: dict) -> dict[str, list[str]]:
    engines = data.get("engines") if isinstance(data, dict) else None
    if not isinstance(engines, list):
        return {}

    voice_map: dict[str, list[str]] = {}
    for engine in engines:
        if not isinstance(engine, dict):
            continue
        name = str(engine.get("name", "")).strip()
        voices = engine.get("voices", [])
        if not name or not isinstance(voices, list):
            continue
        labels = [
            label
            for voice in voices
            if isinstance(voice, dict)
            for label in [_catalogue_voice_label(voice)]
            if label
        ]
        if labels:
            voice_map[name] = labels
    return voice_map


class WaveformCanvas(tk.Canvas):
    """Animated waveform bar display."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=C_SURFACE2, highlightthickness=0, **kwargs)
        self._bars:   list[float] = []
        self._targets: list[float] = []
        self._playing = False
        self._anim_id = None
        self._label_id = None
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, _event=None):
        self.after(10, self._draw)

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        # Status label
        label = "PLAYING" if self._playing else "READY"
        self._label_id = self.create_text(
            w - 12, h // 2, text=label, anchor="e",
            fill=C_MUTED, font=("Courier", 8))

        bar_w   = 2
        gap     = 2
        total_w = bar_w + gap
        n       = min(NUM_BARS, (w - 40) // total_w)
        x_start = (w - n * total_w) // 2

        # Initialise bars
        if len(self._bars) != n:
            import random
            self._bars    = [4 + random.random() * 6 for _ in range(n)]
            self._targets = list(self._bars)

        color = C_ACCENT if self._playing else C_BORDER
        for i, bar_h in enumerate(self._bars):
            x  = x_start + i * total_w
            y0 = (h - bar_h) // 2
            y1 = y0 + bar_h
            self.create_rectangle(x, y0, x + bar_w, y1, fill=color, outline="")

    def set_playing(self, playing: bool):
        self._playing = playing
        if playing:
            self._animate()
        else:
            if self._anim_id:
                self.after_cancel(self._anim_id)
                self._anim_id = None
            import random
            self._bars = [4 + random.random() * 6 for _ in range(len(self._bars))]
            self._draw()

    def _animate(self):
        import random
        for i in range(len(self._bars)):
            self._targets[i] = 4 + random.random() * 28
        for i in range(len(self._bars)):
            diff = self._targets[i] - self._bars[i]
            self._bars[i] += diff * 0.35
        self._draw()
        self._anim_id = self.after(80, self._animate)


class ReadOutApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ReadOut — Text to Speech")
        self.configure(bg=C_BG)
        self.resizable(False, False)
        self.geometry("560x680")

        # Try to remove default title bar decorations (macOS/Linux)
        try:
            self.overrideredirect(False)
        except Exception:
            pass

        self._engine  = tk.StringVar(value="kokoro")
        self._voice   = tk.StringVar(value="af_heart (warm, feminine)")
        self._speed   = tk.DoubleVar(value=1.0)
        self._playing = False
        self._queue:  list[dict] = []
        self._status_text = tk.StringVar(value="READY")
        self._catalogue_loaded = False

        self._build_ui()
        self._poll_status()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer container with 1px border illusion
        outer = tk.Frame(self, bg=C_BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True, padx=24, pady=24)

        inner = tk.Frame(outer, bg=C_SURFACE)
        inner.pack(fill="both", expand=True)

        self._build_titlebar(inner)
        self._build_body(inner)

    def _build_titlebar(self, parent):
        bar = tk.Frame(parent, bg=C_SURFACE2, height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Traffic lights
        lights = tk.Frame(bar, bg=C_SURFACE2)
        lights.pack(side="left", padx=14, pady=0)
        for color in ("#ff5f57", "#febc2e", "#28c840"):
            dot = tk.Label(lights, bg=color, width=1, height=1,
                           relief="flat", bd=0)
            dot.pack(side="left", padx=3, pady=12, ipadx=5, ipady=5)
            dot.configure(cursor="arrow")

        # Title
        tk.Label(bar, text="ReadOut — Text to Speech",
                 bg=C_SURFACE2, fg=C_MUTED,
                 font=("Courier", 10)).pack(expand=True)

        # Status dot
        self._status_dot = tk.Label(bar, text="●", fg=C_ACCENT,
                                     bg=C_SURFACE2, font=("Helvetica", 9))
        self._status_dot.pack(side="right", padx=14)

    def _build_body(self, parent):
        body = tk.Frame(parent, bg=C_SURFACE, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        # ── Top-level view tabs: Player / Guide ──
        self._view_tab_bar = tk.Frame(body, bg=C_SURFACE)
        self._view_tab_bar.pack(fill="x", pady=(0, 10))

        self._view_btns: dict[str, tk.Button] = {}
        for label in ("Player", "Guide"):
            btn = tk.Button(
                self._view_tab_bar, text=label,
                bg=C_SURFACE2, fg=C_MUTED,
                relief="flat", bd=0, padx=14, pady=5,
                font=("Courier", 10, "bold"),
                cursor="hand2",
                command=lambda v=label.lower(): self._switch_view(v),
            )
            btn.pack(side="left", padx=(0, 4))
            self._view_btns[label.lower()] = btn

        # ── Player view (main controls) ──
        self._player_frame = tk.Frame(body, bg=C_SURFACE)
        self._player_frame.pack(fill="both", expand=True)

        self._build_engine_tabs(self._player_frame)
        self._build_text_input(self._player_frame)
        self._build_voice_speed(self._player_frame)
        self._build_waveform(self._player_frame)
        self._build_playback_bar(self._player_frame)
        self._select_engine(self._engine.get(), persist=False)
        self._build_queue(self._player_frame)

        # ── Guide view (how to use) ──
        self._guide_frame = tk.Frame(body, bg=C_SURFACE)
        self._build_guide(self._guide_frame)

        # Start on Player
        self._switch_view("player")

    def _switch_view(self, view: str):
        self._current_view = view
        if view == "player":
            self._guide_frame.pack_forget()
            self._player_frame.pack(fill="both", expand=True)
        else:
            self._player_frame.pack_forget()
            self._guide_frame.pack(fill="both", expand=True)
        for k, btn in self._view_btns.items():
            if k == view:
                btn.configure(bg=C_SURFACE3, fg=C_TEXT)
            else:
                btn.configure(bg=C_SURFACE2, fg=C_MUTED)

    def _build_guide(self, parent):
        """Scrollable how-to-use guide built into the app."""
        canvas = tk.Canvas(parent, bg=C_SURFACE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=C_SURFACE)

        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120 or (-1 if event.num == 5 else 1)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Guide content ──
        sections = [
            ("QUICK START", [
                "1. Run the desktop app:  python main.py",
                "2. A tray icon appears in your menu bar",
                "3. First launch downloads the voice model (~300 MB)",
                "4. The UI window opens automatically",
            ]),
            ("BROWSER EXTENSION", [
                "1. Open Chrome → chrome://extensions",
                "2. Enable Developer mode (top-right)",
                "3. Click Load unpacked → select extension/ folder",
                "4. Select text on any page → right-click → Read aloud",
                "5. Click the ReadOut toolbar icon for quick controls",
            ]),
            ("VOICES", [
                "18 built-in Kokoro voices — change from:",
                "  • Desktop UI voice dropdown",
                "  • Extension popup dropdown",
                "  • System tray → Voice menu",
                "  • Preview Voice plays a short sample",
                "",
                "Voice blending supported:",
                "  af_heart:60,am_adam:40  (60/40 mix)",
            ]),
            ("ENGINES", [
                "Kokoro (default) — local, no API key needed",
                "OpenAI TTS — set openai_api_key in config",
                "ElevenLabs — set elevenlabs_api_key in config",
                "",
                "Switch from the Engine tabs, popup, or tray.",
                "Desktop changes persist to config instantly.",
            ]),
            ("SAVING AUDIO", [
                "• Click Save WAV in the desktop UI",
                "• Right-click → Read aloud & save WAV",
                "• Files save to ~/Desktop/ReadOut/",
                "• Set always_save: true for auto-save",
            ]),
            ("CONFIG FILE", [
                "~/.readout/config.json",
                "Edits take effect instantly — no restart.",
                "",
                "  voice:       af_heart",
                "  speed:       1.0",
                "  engine:      kokoro",
                "  port:        7778",
                "  always_save: false",
                "  save_dir:    ~/Desktop/ReadOut",
            ]),
            ("API (LOCALHOST:7778)", [
                "POST /speak   {text, voice?, speed?, save?}",
                "POST /preview {engine?, voice?, speed?}",
                "POST /stop    Stop playback",
                "GET  /status  Health check + config",
                "GET  /voices  Voice catalogue",
                "PATCH /config {voice?, speed?, engine?}",
            ]),
            ("TROUBLESHOOTING", [
                "No audio: check system output + espeak-ng",
                "Extension silent: reload the page first",
                "Orange dot: model still loading",
                "Port conflict: change in config.json",
                "Python: requires 3.10–3.12 (not 3.13+)",
            ]),
        ]

        for i, (heading, lines) in enumerate(sections):
            # Section heading
            tk.Label(scroll_frame, text=heading, bg=C_SURFACE,
                     fg=C_ACCENT, font=("Courier", 9, "bold"),
                     anchor="w").pack(fill="x", padx=4,
                     pady=(14 if i > 0 else 4, 4))

            # Section body
            block = tk.Frame(scroll_frame, bg=C_SURFACE2)
            block.pack(fill="x", padx=4, pady=(0, 2))

            for line in lines:
                tk.Label(block, text=line or " ", bg=C_SURFACE2,
                         fg=C_DIM if line.startswith("  ") else C_TEXT,
                         font=("Courier", 10),
                         anchor="w", justify="left").pack(
                    fill="x", padx=10, pady=1)

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, bg=C_SURFACE,
                 fg=C_MUTED, font=("Courier", 8),
                 anchor="w").pack(fill="x", pady=(12, 4))

    def _build_engine_tabs(self, parent):
        self._section_label(parent, "VOICE ENGINE")

        tab_frame = tk.Frame(parent, bg=C_SURFACE2, relief="flat", bd=0)
        tab_frame.pack(fill="x", pady=(0, 8))

        self._engine_btns: dict[str, tk.Button] = {}
        for key, cfg in ENGINES.items():
            btn = tk.Button(
                tab_frame,
                text=f"{cfg['label']}  {cfg['badge']}",
                bg=C_SURFACE2, fg=C_MUTED,
                relief="flat", bd=0, padx=10, pady=6,
                font=("Courier", 9),
                cursor="hand2",
                command=lambda k=key: self._select_engine(k),
            )
            btn.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            self._engine_btns[key] = btn

    def _select_engine(self, key: str, persist: bool = True, selected_voice: str | None = None):
        if key not in ENGINES:
            return

        self._engine.set(key)
        for k, btn in self._engine_btns.items():
            if k == key:
                btn.configure(bg=C_SURFACE3, fg=C_TEXT)
            else:
                btn.configure(bg=C_SURFACE2, fg=C_MUTED)

        # Update voice dropdown
        voices = VOICES_BY_ENGINE.get(key, [])
        if hasattr(self, "_voice_menu"):
            menu = self._voice_menu["menu"]
            menu.delete(0, "end")
            for v in voices:
                menu.add_command(label=v, command=lambda val=v: self._select_voice(val))

            target_voice = _voice_label_for_engine(key, selected_voice)
            valid_voice_ids = {_voice_id(v) for v in voices}
            if target_voice and (_voice_id(target_voice) in valid_voice_ids or target_voice in voices):
                self._voice.set(target_voice)
            elif voices and _voice_id(self._voice.get()) not in valid_voice_ids:
                self._voice.set(voices[0])

        # Update model badge
        e_cfg = ENGINES[key]
        if hasattr(self, "_model_badge"):
            self._model_badge.configure(
                text=e_cfg["label"].upper(),
                fg=e_cfg["badge_fg"],
                bg=C_SURFACE,
            )

        if persist:
            payload = {"engine": key}
            voice_id = self._current_voice_id()
            if voice_id:
                payload["voice"] = voice_id
            self._patch_config(payload)

    def _select_voice(self, label: str, persist: bool = True):
        self._voice.set(label)
        if persist:
            voice_id = _voice_id(label)
            if voice_id:
                self._patch_config({"voice": voice_id})

    def _current_voice_id(self) -> str:
        return _voice_id(self._voice.get())

    def _patch_config(self, payload: dict):
        def _worker():
            _patch("/config", payload)

        threading.Thread(target=_worker, daemon=True).start()

    def _build_text_input(self, parent):
        frame = tk.Frame(parent, bg=C_SURFACE2, relief="flat")
        frame.pack(fill="x", pady=(0, 8))

        self._text_input = tk.Text(
            frame, bg=C_SURFACE2, fg=C_TEXT,
            insertbackground=C_ACCENT,
            relief="flat", bd=0, padx=12, pady=10,
            height=5, font=("Helvetica", 12),
            wrap="word",
        )
        self._text_input.pack(fill="both", padx=1, pady=1)
        self._text_input.insert("1.0",
            "Paste text here, or select text on any page and hit the extension button...")
        self._text_input.configure(fg=C_MUTED)

        def _clear_placeholder(event):
            if self._text_input.get("1.0", "end-1c") == \
               "Paste text here, or select text on any page and hit the extension button...":
                self._text_input.delete("1.0", "end")
                self._text_input.configure(fg=C_TEXT)
        self._text_input.bind("<FocusIn>", _clear_placeholder)

        # Bottom bar: paste / clear / char count
        bottom = tk.Frame(frame, bg=C_SURFACE2)
        bottom.pack(fill="x", padx=8, pady=(0, 6))

        for label, cmd in [("paste", self._paste), ("clear", self._clear_text)]:
            tk.Button(bottom, text=label, bg=C_SURFACE2, fg=C_MUTED,
                      relief="flat", bd=0, font=("Courier", 9),
                      cursor="hand2", padx=6, pady=2,
                      highlightthickness=1, highlightbackground=C_BORDER,
                      command=cmd).pack(side="left", padx=(0, 4))

        self._char_label = tk.Label(bottom, text="0", bg=C_SURFACE2,
                                     fg=C_MUTED, font=("Courier", 9))
        self._char_label.pack(side="right")

        self._text_input.bind("<KeyRelease>", self._update_char_count)

    def _update_char_count(self, _=None):
        n = len(self._text_input.get("1.0", "end-1c"))
        self._char_label.configure(
            text=str(n),
            fg=C_ORANGE if n > 2000 else C_MUTED,
        )

    def _paste(self):
        try:
            txt = self.clipboard_get()
            self._text_input.delete("1.0", "end")
            self._text_input.insert("1.0", txt)
            self._text_input.configure(fg=C_TEXT)
            self._update_char_count()
        except Exception:
            pass

    def _clear_text(self):
        self._text_input.delete("1.0", "end")
        self._char_label.configure(text="0")
        self._stop()

    def _build_voice_speed(self, parent):
        row = tk.Frame(parent, bg=C_SURFACE)
        row.pack(fill="x", pady=(0, 8))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        # Voice
        v_frame = tk.Frame(row, bg=C_SURFACE)
        v_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(v_frame, text="VOICE", bg=C_SURFACE, fg=C_MUTED,
                 font=("Courier", 8), anchor="w").pack(fill="x", pady=(0, 4))

        self._voice_menu = tk.OptionMenu(v_frame, self._voice, "af_heart (warm, feminine)")
        self._voice_menu.configure(
            bg=C_SURFACE2, fg=C_TEXT, relief="flat", bd=0,
            activebackground=C_SURFACE3, activeforeground=C_TEXT,
            font=("Helvetica", 11), highlightthickness=1,
            highlightbackground=C_BORDER, indicatoron=True,
        )
        self._voice_menu["menu"].configure(bg=C_SURFACE2, fg=C_TEXT,
                                            activebackground=C_SURFACE3)
        self._voice_menu.pack(fill="x")

        self._preview_btn = tk.Button(
            v_frame, text="Preview Voice",
            bg=C_SURFACE2, fg=C_DIM,
            relief="flat", bd=0,
            font=("Courier", 9),
            cursor="hand2",
            highlightthickness=1, highlightbackground=C_BORDER,
            command=self._preview_voice,
        )
        self._preview_btn.pack(fill="x", pady=(6, 0), ipady=4)

        # Speed
        s_frame = tk.Frame(row, bg=C_SURFACE)
        s_frame.grid(row=0, column=1, sticky="ew")
        tk.Label(s_frame, text="SPEED", bg=C_SURFACE, fg=C_MUTED,
                 font=("Courier", 8), anchor="w").pack(fill="x", pady=(0, 4))

        speed_row = tk.Frame(s_frame, bg=C_SURFACE)
        speed_row.pack(fill="x")

        self._speed_label = tk.Label(speed_row, text="1.0×", bg=C_SURFACE,
                                      fg=C_ACCENT, font=("Courier", 11), width=4)
        self._speed_label.pack(side="right")

        slider = ttk.Scale(speed_row, from_=0.5, to=2.0,
                           variable=self._speed, orient="horizontal",
                           command=self._on_speed_change)
        slider.pack(side="left", fill="x", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TScale",
                         background=C_SURFACE,
                         troughcolor=C_BORDER,
                         slidercolor=C_ACCENT)

    def _on_speed_change(self, _=None, persist: bool = True):
        v = round(self._speed.get(), 1)
        self._speed_label.configure(text=f"{v}×")
        if persist:
            self._patch_config({"speed": v})

    def _build_waveform(self, parent):
        self._wave = WaveformCanvas(parent, height=54)
        self._wave.pack(fill="x", pady=(0, 8))

    def _build_playback_bar(self, parent):
        bar = tk.Frame(parent, bg=C_SURFACE)
        bar.pack(fill="x", pady=(0, 8))

        # Play/Stop button
        self._play_btn = tk.Button(
            bar, text="▶",
            bg=C_ACCENT, fg="#000000",
            relief="flat", bd=0,
            font=("Helvetica", 14, "bold"),
            width=3, height=1,
            cursor="hand2",
            command=self._toggle_play,
        )
        self._play_btn.pack(side="left", padx=(0, 8), ipady=6)

        # Save WAV
        self._save_btn = tk.Button(
            bar, text="⬇  Save WAV",
            bg=C_SURFACE2, fg=C_DIM,
            relief="flat", bd=0,
            font=("Courier", 9),
            cursor="hand2",
            highlightthickness=1, highlightbackground=C_BORDER,
            command=self._save_audio,
        )
        self._save_btn.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=7)

        # Model badge
        self._model_badge = tk.Label(
            bar, text="KOKORO",
            bg=C_SURFACE, fg=C_ACCENT,
            font=("Courier", 9, "bold"),
            padx=8, pady=4,
        )
        self._model_badge.pack(side="right")

    def _build_queue(self, parent):
        self._section_label(parent, "RECENT / QUEUE")

        self._queue_frame = tk.Frame(parent, bg=C_SURFACE)
        self._queue_frame.pack(fill="x")

    # ── Playback logic ────────────────────────────────────────────────────────

    def _get_text(self) -> str:
        txt = self._text_input.get("1.0", "end-1c").strip()
        if txt == "Paste text here, or select text on any page and hit the extension button...":
            return ""
        return txt

    def _toggle_play(self):
        if self._playing:
            self._stop()
        else:
            self._play()

    def _play(self):
        text = self._get_text()
        if not text:
            return

        voice_id    = self._current_voice_id()
        speed       = round(self._speed.get(), 1)
        engine      = self._engine.get()

        self._set_playing(True)

        def _worker():
            if engine == "kokoro":
                result = _post("/speak", {
                    "text":  text,
                    "voice": voice_id,
                    "speed": speed,
                    "save":  False,
                })
            else:
                result = _post("/speak", {"text": text, "voice": voice_id, "speed": speed})

            self.after(0, lambda: self._on_speak_done(result, text, speed))

        threading.Thread(target=_worker, daemon=True).start()

        # Add to queue display
        self._add_to_queue(text, voice_id)

    def _on_speak_done(self, result: dict, text: str, speed: float):
        if result.get("status") == "error":
            self._set_playing(False)
            self._status_text.set("ERROR")

    def _preview_voice(self):
        voice_id = self._current_voice_id()
        if not voice_id:
            return

        engine = self._engine.get()
        speed = round(self._speed.get(), 1)
        self._preview_btn.configure(text="Previewing...", fg=C_ACCENT)

        def _worker():
            result = _post("/preview", {
                "engine": engine,
                "voice": voice_id,
                "speed": speed,
            })
            self.after(0, lambda: self._on_preview_done(result))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_preview_done(self, result: dict):
        if result.get("status") == "error":
            self._status_text.set("ERROR")
        self._preview_btn.configure(text="Preview Voice", fg=C_DIM)

    def _stop(self):
        def _worker():
            _post("/stop", timeout=10)
        threading.Thread(target=_worker, daemon=True).start()
        self._set_playing(False)

    def _set_playing(self, playing: bool):
        self._playing = playing
        self._wave.set_playing(playing)
        if playing:
            self._play_btn.configure(text="⏸", bg=C_RED)
        else:
            self._play_btn.configure(text="▶", bg=C_ACCENT)

    def _save_audio(self):
        text     = self._get_text()
        voice_id = self._current_voice_id()
        speed    = round(self._speed.get(), 1)

        if not text:
            return

        orig_text = self._save_btn.cget("text")
        self._save_btn.configure(text="⬇  Saving...", fg=C_ACCENT)

        def _worker():
            result = _post("/speak", {"text": text, "voice": voice_id,
                                       "speed": speed, "save": True})
            saved  = result.get("saved_to", "")
            self.after(0, lambda: self._on_saved(saved))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_saved(self, path: str):
        if path:
            self._save_btn.configure(text="✓  Saved", fg=C_ACCENT)
        else:
            self._save_btn.configure(text="⬇  Save WAV", fg=C_DIM)
        self.after(2000, lambda: self._save_btn.configure(
            text="⬇  Save WAV", fg=C_DIM))

    # ── Queue display ─────────────────────────────────────────────────────────

    def _add_to_queue(self, text: str, voice: str):
        # Estimate duration: ~150 wpm ≈ 12.5 chars/sec
        dur_s   = max(1, int(len(text) / 12.5))
        dur_str = f"0:{dur_s:02d}" if dur_s < 60 else f"{dur_s//60}:{dur_s%60:02d}"
        entry   = {"text": text[:80], "voice": voice, "duration": dur_str}
        self._queue.insert(0, entry)
        if len(self._queue) > 5:
            self._queue = self._queue[:5]
        self._render_queue()

    def _render_queue(self):
        for w in self._queue_frame.winfo_children():
            w.destroy()

        for i, item in enumerate(self._queue):
            row = tk.Frame(self._queue_frame, bg=C_SURFACE2 if i > 0 else "#1a2a0a",
                           relief="flat")
            row.pack(fill="x", pady=(0, 3))

            # Index / playing indicator
            idx_text = "▶" if i == 0 else str(i + 1)
            idx_color = C_ACCENT if i == 0 else C_MUTED
            tk.Label(row, text=idx_text, bg=row["bg"], fg=idx_color,
                     font=("Courier", 9), width=2, pady=6).pack(side="left", padx=(8, 4))

            # Text
            tk.Label(row, text=item["text"] + ("..." if len(item["text"]) >= 80 else ""),
                     bg=row["bg"],
                     fg=C_ACCENT if i == 0 else C_DIM,
                     font=("Helvetica", 11), anchor="w").pack(side="left", fill="x",
                                                               expand=True, padx=4)

            # Duration
            tk.Label(row, text=item["duration"], bg=row["bg"], fg=C_MUTED,
                     font=("Courier", 9), pady=6).pack(side="right", padx=4)

    # ── Status polling ────────────────────────────────────────────────────────

    def _poll_status(self):
        def _worker():
            catalogue = {}
            if not self._catalogue_loaded:
                catalogue = _get("/voices")
            result = _get("/status")
            self.after(0, lambda: self._apply_status(result, catalogue))

        threading.Thread(target=_worker, daemon=True).start()
        self.after(3000, self._poll_status)

    def _apply_voice_catalogue(self, data: dict):
        voice_map = _voice_map_from_catalogue(data)
        if not voice_map:
            return

        VOICES_BY_ENGINE.update(voice_map)
        self._catalogue_loaded = True

    def _apply_status(self, result: dict, catalogue: dict | None = None):
        if catalogue:
            self._apply_voice_catalogue(catalogue)

        status = result.get("status", "")
        if status == "ready":
            self._status_dot.configure(fg=C_ACCENT)
        elif status == "loading":
            self._status_dot.configure(fg=C_ORANGE)
        else:
            self._status_dot.configure(fg=C_RED)

        engine = result.get("engine")
        if engine in ENGINES:
            self._select_engine(engine, persist=False, selected_voice=result.get("voice"))

        speed = result.get("speed")
        if isinstance(speed, (int, float)):
            self._speed.set(float(speed))
            self._on_speed_change(persist=False)
