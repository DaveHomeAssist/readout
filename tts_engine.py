"""
tts_engine.py — Kokoro TTS core
Wraps KPipeline, handles playback via sounddevice, optional file save,
and graceful first-run model download.
"""
import os
import threading
import time

from config import get_config

# Heavy imports (torch, kokoro, numpy, sounddevice) are deferred to first use
# so the server can start immediately without waiting for torch to load.
_np = None
_sd = None
_sf = None
_KPipeline = None


def _ensure_imports():
    global _np, _sd, _sf, _KPipeline
    if _np is None:
        import numpy
        import sounddevice
        import soundfile
        from kokoro import KPipeline as KP
        _np = numpy
        _sd = sounddevice
        _sf = soundfile
        _KPipeline = KP

# ── Model state ──────────────────────────────────────────────────────────────
_pipeline      = None
_pipeline_lock = threading.Lock()
_loading       = False          # True while model is initialising
_load_error    = None           # set if KPipeline() raises

MODEL_READY_FLAG = os.path.expanduser("~/.readout/.model_ready")


def is_first_run() -> bool:
    return not os.path.exists(MODEL_READY_FLAG)


def _mark_model_ready() -> None:
    os.makedirs(os.path.dirname(MODEL_READY_FLAG), exist_ok=True)
    open(MODEL_READY_FLAG, "w").close()


def get_pipeline(on_progress=None):
    """
    Load the KPipeline singleton.  Thread-safe, loads once.
    on_progress(msg: str) — optional callback for status updates.
    """
    global _pipeline, _loading, _load_error

    if _pipeline is not None:
        return _pipeline

    with _pipeline_lock:
        if _pipeline is not None:
            return _pipeline

        _loading = True
        try:
            _ensure_imports()
            if on_progress:
                on_progress("loading_model")

            cfg = get_config()
            _pipeline = _KPipeline(lang_code=cfg.get("lang_code", "a"))
            _mark_model_ready()

            if on_progress:
                on_progress("ready")

        except Exception as exc:
            _load_error = str(exc)
            if on_progress:
                on_progress(f"error:{exc}")
            raise
        finally:
            _loading = False

    return _pipeline


def is_loading() -> bool:
    return _loading


def get_load_error():
    return _load_error


# ── Playback ─────────────────────────────────────────────────────────────────

def speak(
    text: str,
    voice: str  = None,
    speed: float = None,
    save: bool   = False,
    on_progress=None,
) -> dict:
    """
    Synthesise text → audio → play.
    Returns {"status": "playing"|"error", "voice", "speed", "saved_to"?}
    """
    cfg   = get_config()
    voice = voice or cfg.get("voice", "af_heart")
    speed = speed or cfg.get("speed", 1.0)

    try:
        pipeline = get_pipeline(on_progress=on_progress)
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    if not text.strip():
        return {"status": "error", "message": "No text provided"}

    _ensure_imports()

    all_audio = []
    generator = pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+")
    for _i, (_gs, _ps, chunk) in enumerate(generator):
        all_audio.append(chunk)

    if not all_audio:
        return {"status": "error", "message": "No audio generated"}

    full_audio  = _np.concatenate(all_audio)
    sample_rate = 24000   # Kokoro always outputs at 24 kHz

    # Non-blocking playback
    _sd.stop()
    _sd.play(full_audio, samplerate=sample_rate)

    result: dict = {"status": "playing", "voice": voice, "speed": speed}

    # Optional file save
    if save or cfg.get("always_save", False):
        save_dir = cfg.get("save_dir", os.path.expanduser("~/Desktop/ReadOut"))
        os.makedirs(save_dir, exist_ok=True)
        filename = f"readout_{int(time.time())}.wav"
        filepath = os.path.join(save_dir, filename)
        _sf.write(filepath, full_audio, sample_rate)
        result["saved_to"] = filepath

    return result


def stop_audio() -> None:
    """Immediately stop any playing audio."""
    if _sd is not None:
        _sd.stop()


# ── Voice catalogue ───────────────────────────────────────────────────────────

VOICES: list[dict] = [
    {"id": "af_heart",    "label": "af_heart (warm, feminine)"},
    {"id": "af_sky",      "label": "af_sky (bright, clear)"},
    {"id": "af_bella",    "label": "af_bella (expressive)"},
    {"id": "af_sarah",    "label": "af_sarah (natural)"},
    {"id": "af_nicole",   "label": "af_nicole (soft)"},
    {"id": "af_jessica",  "label": "af_jessica (conversational)"},
    {"id": "af_nova",     "label": "af_nova (energetic)"},
    {"id": "af_river",    "label": "af_river (smooth)"},
    {"id": "af_kore",     "label": "af_kore (precise)"},
    {"id": "af_aoede",    "label": "af_aoede (melodic)"},
    {"id": "am_adam",     "label": "am_adam (deep, neutral)"},
    {"id": "am_echo",     "label": "am_echo (casual, male)"},
    {"id": "am_michael",  "label": "am_michael (warm, male)"},
    {"id": "am_fenrir",   "label": "am_fenrir (strong, male)"},
    {"id": "bf_emma",     "label": "bf_emma (British, feminine)"},
    {"id": "bf_isabella", "label": "bf_isabella (British, warm)"},
    {"id": "bm_george",   "label": "bm_george (British, authoritative)"},
    {"id": "bm_lewis",    "label": "bm_lewis (British, conversational)"},
]


def list_voices() -> list[str]:
    return [v["id"] for v in VOICES]


def list_voices_labeled() -> list[dict]:
    return VOICES
