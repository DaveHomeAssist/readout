"""
tts_engine.py — Kokoro TTS core
Wraps KPipeline, handles playback via sounddevice, optional file save,
and graceful first-run model download.
"""
import os
import queue
import threading
import time

from config import get_config

# Heavy imports (torch, kokoro, numpy, sounddevice) are deferred to first use
# so the server can start immediately without waiting for torch to load.
_np = None
_sd = None
_sf = None
_KPipeline = None
_espeak_runtime_ready = False


def _ensure_espeak_runtime():
    """Expose bundled eSpeak NG libraries before Kokoro imports phonemizer."""
    global _espeak_runtime_ready
    if _espeak_runtime_ready:
        return

    try:
        import espeakng_loader
        espeakng_loader.make_library_available()
    except Exception:
        # Fall back to a system espeak-ng installation if the loader is absent.
        pass
    _espeak_runtime_ready = True


def _ensure_audio():
    """Import the audio stack (numpy/sounddevice/soundfile) without Kokoro.

    The OpenAI / ElevenLabs fallbacks need playback but not the 300 MB model,
    so they can warm up audio without pulling in torch + kokoro.
    """
    global _np, _sd, _sf
    if _sd is None:
        import numpy
        import sounddevice
        import soundfile
        _np = numpy
        _sd = sounddevice
        _sf = soundfile


def _ensure_imports():
    global _KPipeline
    _ensure_audio()
    if _KPipeline is None:
        _ensure_espeak_runtime()
        from kokoro import KPipeline as KP
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
    allow_always_save: bool = True,
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

    want_save = save or (allow_always_save and cfg.get("always_save", False))
    if cfg.get("streaming_playback", False):
        return _speak_streaming(pipeline, text, voice, speed, want_save)

    all_audio = []
    generator = pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+")
    for _i, (_gs, _ps, chunk) in enumerate(generator):
        all_audio.append(chunk)

    if not all_audio:
        return {"status": "error", "message": "No audio generated"}

    full_audio  = _np.concatenate(all_audio)
    sample_rate = 24000   # Kokoro always outputs at 24 kHz

    try:
        play_audio(full_audio, sample_rate)
    except Exception as exc:        # e.g. PortAudioError: no output device / no permission
        return {"status": "error", "message": audio_error_message(exc)}

    result: dict = {"status": "playing", "voice": voice, "speed": speed}

    # Optional file save
    if want_save:
        result["saved_to"] = save_wav(full_audio, sample_rate)

    return result


# ── Streaming playback ───────────────────────────────────────────────────────
# Opt-in via config "streaming_playback". Chunks are played as the generator
# produces them instead of after the whole text is synthesised. See
# docs/BRIEF-streaming-playback.md for scope, exclusions and acceptance.

SAMPLE_RATE = 24000                      # Kokoro always outputs at 24 kHz
STREAM_SPLIT_PATTERN = r"(?<=[.!?])\s+|\n+"   # sentence-aware so the first chunk is short

_stream_player = None
_stream_lock = threading.Lock()


def _to_samples(chunk):
    """Normalise a generator chunk to a 1-D float32 sequence the callback can slice."""
    if hasattr(chunk, "detach"):             # torch tensor (possibly on an accelerator)
        chunk = chunk.detach().cpu().numpy()
    if _np is not None and hasattr(_np, "asarray") and not isinstance(chunk, list):
        chunk = _np.asarray(chunk, dtype="float32")
    return chunk


class StreamPlayer:
    """Feeds synthesised chunks into a sounddevice OutputStream as they arrive.

    Producer side: push(chunk) ... finish(). Consumer side: the PortAudio
    callback drains a queue, zero-fills on underrun, and stops itself once
    finish() was called and the queue is empty. stop() aborts immediately.
    """

    def __init__(self, sd, samplerate: int = SAMPLE_RATE):
        self._sd = sd
        self.samplerate = samplerate
        self._queue: queue.Queue = queue.Queue()
        self._pending = None
        self._pos = 0
        self._done = threading.Event()
        self._finished = threading.Event()   # stream drained or aborted
        self._stream = None
        self.chunks_queued = 0
        self.chunks_played = 0
        self.underruns = 0
        self.error: str | None = None

    # ── producer API ──
    def start(self) -> None:
        self._stream = self._sd.OutputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="float32",
            callback=self._callback,
            finished_callback=self._finished.set,
        )
        self._stream.start()

    def push(self, chunk) -> None:
        self._queue.put(_to_samples(chunk))
        self.chunks_queued += 1

    def finish(self) -> None:
        self._done.set()

    def fail(self, message: str) -> None:
        self.error = message
        self._done.set()

    def stop(self) -> None:
        self._done.set()
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._pending = None
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.abort()
            finally:
                stream.close()
        self._finished.set()

    def wait(self, timeout: float | None = None) -> bool:
        return self._finished.wait(timeout)

    @property
    def active(self) -> bool:
        return self._stream is not None and not self._finished.is_set()

    # ── PortAudio callback ──
    def _callback(self, outdata, frames, _time, status) -> None:
        if status:
            self.underruns += 1
        filled = 0
        while filled < frames:
            if self._pending is None or self._pos >= len(self._pending):
                try:
                    self._pending = self._queue.get_nowait()
                    self._pos = 0
                    self.chunks_played += 1
                except queue.Empty:
                    outdata[filled:] = 0
                    if self._done.is_set():
                        raise self._sd.CallbackStop
                    if filled == 0:
                        self.underruns += 1
                    return
            n = min(frames - filled, len(self._pending) - self._pos)
            outdata[filled:filled + n, 0] = self._pending[self._pos:self._pos + n]
            self._pos += n
            filled += n


def audio_error_message(exc: Exception) -> str:
    """Turn a PortAudio failure into an actionable message for /speak callers."""
    return (
        f"Audio output unavailable: {exc}. Check that an output device exists and "
        "that this user can open it (on Linux: membership of the 'audio' group or a "
        "running PipeWire/PulseAudio session)."
    )


def _stop_stream_player() -> None:
    global _stream_player
    with _stream_lock:
        player, _stream_player = _stream_player, None
    if player is not None:
        player.stop()


def playback_state() -> dict:
    """Snapshot for /status: whether a live stream is playing and its counters."""
    player = _stream_player
    if player is None:
        return {"state": "idle", "streaming": False}
    return {
        "state": "playing" if player.active else "idle",
        "streaming": True,
        "chunks_queued": player.chunks_queued,
        "chunks_played": player.chunks_played,
        "underruns": player.underruns,
        "error": player.error,
    }


def _speak_streaming(pipeline, text: str, voice: str, speed: float, want_save: bool) -> dict:
    global _stream_player

    generator = pipeline(text, voice=voice, speed=speed, split_pattern=STREAM_SPLIT_PATTERN)

    # First chunk synchronously: an empty or failing generator must surface an
    # error before any stream is opened or any "playing" result is returned.
    try:
        _gs, _ps, first = next(generator)
    except StopIteration:
        return {"status": "error", "message": "No audio generated"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    _ensure_audio()
    _stop_stream_player()
    _sd.stop()                      # halt any buffered sd.play() from a cloud engine

    player = StreamPlayer(_sd, SAMPLE_RATE)
    player.push(first)
    try:
        player.start()
    except Exception as exc:        # e.g. PortAudioError: no output device / no permission
        return {"status": "error", "message": audio_error_message(exc)}
    with _stream_lock:
        _stream_player = player

    collected = [first] if want_save else None
    synthesis_done = threading.Event()

    def _produce():
        try:
            for _gs, _ps, chunk in generator:
                if player._done.is_set():
                    break
                if collected is not None:
                    collected.append(chunk)
                player.push(chunk)
            player.finish()
        except Exception as exc:       # keep the stream alive to drain what was queued
            player.fail(str(exc))
        finally:
            synthesis_done.set()

    threading.Thread(target=_produce, name="readout-stream-producer", daemon=True).start()

    result: dict = {"status": "playing", "voice": voice, "speed": speed, "streaming": True}
    if want_save:
        # Playback is already audible; wait for synthesis so saved_to is complete.
        synthesis_done.wait()
        if player.error:
            result["save_error"] = player.error
        else:
            result["saved_to"] = save_wav(_np.concatenate(collected), SAMPLE_RATE)
    return result


def play_audio(data, samplerate) -> None:
    """Stop any current playback and play `data` non-blocking.

    Shared by Kokoro and the OpenAI / ElevenLabs fallbacks so a new request
    always replaces the previous one and stop_audio() can halt any of them.
    """
    _ensure_audio()
    _stop_stream_player()
    _sd.stop()
    _sd.play(data, samplerate=samplerate)


def read_audio(raw: bytes):
    """Decode raw audio bytes (e.g. an API response body) → (data, samplerate)."""
    import io
    _ensure_audio()
    return _sf.read(io.BytesIO(raw))


def save_wav(data, samplerate) -> str:
    """Write `data` to the configured save_dir as a timestamped WAV; return path."""
    cfg = get_config()
    save_dir = cfg.get("save_dir", os.path.expanduser("~/Desktop/ReadOut"))
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, f"readout_{int(time.time())}.wav")
    _ensure_audio()
    _sf.write(filepath, data, samplerate)
    return filepath


def stop_audio() -> None:
    """Immediately stop any playing audio (Kokoro batch, streaming, or API fallback)."""
    _stop_stream_player()
    if _sd is not None:
        _sd.stop()


# ── Voice catalogue ───────────────────────────────────────────────────────────

VOICES: list[dict] = [
    {"id": "af_heart",    "label": "Heart - Warm & Gentle"},
    {"id": "af_sky",      "label": "Sky - Bright & Clear"},
    {"id": "af_bella",    "label": "Bella - Expressive & Rich"},
    {"id": "af_sarah",    "label": "Sarah - Natural & Balanced"},
    {"id": "af_nicole",   "label": "Nicole - Soft & Calm"},
    {"id": "af_jessica",  "label": "Jessica - Conversational"},
    {"id": "af_nova",     "label": "Nova - Energetic & Upbeat"},
    {"id": "af_river",    "label": "River - Smooth & Steady"},
    {"id": "af_kore",     "label": "Kore - Precise & Crisp"},
    {"id": "af_aoede",    "label": "Aoede - Melodic & Lyrical"},
    {"id": "am_adam",     "label": "Adam - Deep & Neutral"},
    {"id": "am_echo",     "label": "Echo - Casual & Relaxed"},
    {"id": "am_michael",  "label": "Michael - Warm & Grounded"},
    {"id": "am_fenrir",   "label": "Fenrir - Strong & Commanding"},
    {"id": "bf_emma",     "label": "bf_emma (British, feminine)"},
    {"id": "bf_isabella", "label": "bf_isabella (British, warm)"},
    {"id": "bm_george",   "label": "bm_george (British, authoritative)"},
    {"id": "bm_lewis",    "label": "bm_lewis (British, conversational)"},
]


def list_voices() -> list[str]:
    return [v["id"] for v in VOICES]


def list_voices_labeled() -> list[dict]:
    return VOICES
