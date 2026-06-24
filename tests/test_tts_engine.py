"""Tests for tts_engine.py — voice catalogue, model-state flags, audio helpers,
and the Kokoro speak() flow (heavy deps mocked)."""
from __future__ import annotations

import os
import sys
import types
import builtins

import tts_engine


# ── Voice catalogue ───────────────────────────────────────────────────────────

def test_voice_ids_and_labels_are_consistent():
    ids = tts_engine.list_voices()
    labeled = tts_engine.list_voices_labeled()
    assert len(ids) == len(labeled) == 18
    assert [v["id"] for v in labeled] == ids
    assert "af_heart" in ids
    assert len(set(ids)) == len(ids), "voice ids must be unique"


# ── Model-ready flag ──────────────────────────────────────────────────────────

def test_is_first_run_tracks_flag_file(isolated_config):
    assert tts_engine.is_first_run() is True
    tts_engine._mark_model_ready()
    assert tts_engine.is_first_run() is False
    assert os.path.exists(tts_engine.MODEL_READY_FLAG)


# ── Audio helpers ─────────────────────────────────────────────────────────────

def test_play_audio_stops_before_playing(fake_audio):
    tts_engine.play_audio([1, 2, 3], 24000)
    assert fake_audio.sd.stops == 1
    assert fake_audio.sd.played == [([1, 2, 3], 24000)]


def test_read_audio_decodes_via_soundfile(fake_audio):
    fake_audio.sf._decoded = (["pcm"], 16000)
    data, sr = tts_engine.read_audio(b"rawbytes")
    assert data == ["pcm"]
    assert sr == 16000


def test_save_wav_writes_to_configured_dir(isolated_config, fake_audio, monkeypatch):
    import config
    save_dir = os.path.join(os.path.dirname(str(isolated_config)), "out")
    monkeypatch.setattr(config, "DEFAULTS", {**config.DEFAULTS, "save_dir": save_dir})

    path = tts_engine.save_wav([0.1, 0.2], 24000)
    assert path.startswith(save_dir)
    assert path.endswith(".wav")
    assert os.path.exists(path)
    assert fake_audio.sf.writes  # soundfile.write was invoked


def test_stop_audio_is_noop_when_audio_never_loaded(monkeypatch):
    monkeypatch.setattr(tts_engine, "_sd", None)
    tts_engine.stop_audio()  # must not raise


def test_stop_audio_stops_active_device(fake_audio):
    tts_engine.stop_audio()
    assert fake_audio.sd.stops == 1


def test_espeak_loader_is_made_available_before_kokoro_import(monkeypatch):
    calls = {"n": 0}
    fake_loader = types.SimpleNamespace(
        make_library_available=lambda: calls.__setitem__("n", calls["n"] + 1)
    )
    monkeypatch.setitem(sys.modules, "espeakng_loader", fake_loader)
    monkeypatch.setattr(tts_engine, "_espeak_runtime_ready", False)

    tts_engine._ensure_espeak_runtime()
    tts_engine._ensure_espeak_runtime()

    assert calls == {"n": 1}


def test_espeak_loader_absence_falls_back_to_system_runtime(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "espeakng_loader":
            raise ImportError("missing loader")
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "espeakng_loader", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(tts_engine, "_espeak_runtime_ready", False)

    tts_engine._ensure_espeak_runtime()

    assert tts_engine._espeak_runtime_ready is True


# ── speak() ───────────────────────────────────────────────────────────────────

def _patch_pipeline(monkeypatch, chunks):
    """Make get_pipeline() return a fake pipeline yielding the given chunks."""
    def fake_pipeline(text, voice=None, speed=None, split_pattern=None):
        for c in chunks:
            yield ("gs", "ps", c)

    monkeypatch.setattr(tts_engine, "get_pipeline", lambda on_progress=None: fake_pipeline)
    monkeypatch.setattr(tts_engine, "_ensure_imports", lambda: None)


def test_speak_rejects_empty_text(isolated_config, fake_audio, monkeypatch):
    _patch_pipeline(monkeypatch, [[1.0]])
    result = tts_engine.speak("   ")
    assert result["status"] == "error"
    assert "No text" in result["message"]


def test_speak_plays_and_returns_voice_and_speed(isolated_config, fake_audio, monkeypatch):
    _patch_pipeline(monkeypatch, [[0.1], [0.2]])
    result = tts_engine.speak("hello world", voice="am_adam", speed=1.25)
    assert result["status"] == "playing"
    assert result["voice"] == "am_adam"
    assert result["speed"] == 1.25
    # Concatenated chunks were played at Kokoro's fixed 24 kHz.
    assert fake_audio.sd.played[-1] == ([0.1, 0.2], 24000)
    assert "saved_to" not in result


def test_speak_saves_when_requested(isolated_config, fake_audio, monkeypatch):
    save_dir = os.path.join(os.path.dirname(str(isolated_config)), "out")
    import config
    monkeypatch.setattr(config, "DEFAULTS", {**config.DEFAULTS, "save_dir": save_dir})
    _patch_pipeline(monkeypatch, [[0.5]])

    result = tts_engine.speak("save me", save=True)
    assert result["status"] == "playing"
    assert result["saved_to"].endswith(".wav")
    assert os.path.exists(result["saved_to"])


def test_speak_can_ignore_always_save_for_preview(isolated_config, fake_audio, monkeypatch):
    import config

    config.set_config({"always_save": True})
    _patch_pipeline(monkeypatch, [[0.25]])

    result = tts_engine.speak("preview", save=False, allow_always_save=False)

    assert result["status"] == "playing"
    assert "saved_to" not in result


def test_speak_falls_back_to_config_defaults(isolated_config, fake_audio, monkeypatch):
    import config
    config.set_config({"voice": "bf_emma", "speed": 0.75})
    _patch_pipeline(monkeypatch, [[1.0]])
    result = tts_engine.speak("text")
    assert result["voice"] == "bf_emma"
    assert result["speed"] == 0.75
