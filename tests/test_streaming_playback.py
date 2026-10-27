"""Tests for the opt-in streaming playback path (docs/BRIEF-streaming-playback.md).

The real sounddevice OutputStream and numpy are never imported; a fake stream
lets the tests drive the PortAudio callback by hand.
"""
from __future__ import annotations

import os
import threading
import time
import types

import pytest

import config
import tts_engine


# ── Fakes ─────────────────────────────────────────────────────────────────────

class CallbackStop(Exception):
    pass


class FakeOutputStream:
    def __init__(self, samplerate, channels, dtype, callback, finished_callback):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.callback = callback
        self.finished_callback = finished_callback
        self.started = False
        self.aborted = False
        self.closed = False

    def start(self):
        self.started = True

    def abort(self):
        self.aborted = True

    def close(self):
        self.closed = True


class FakeStreamingSoundDevice:
    CallbackStop = CallbackStop

    def __init__(self):
        self.streams: list[FakeOutputStream] = []
        self.stops = 0
        self.played = []

    def OutputStream(self, **kwargs):  # noqa: N802 (mirrors sounddevice)
        stream = FakeOutputStream(**kwargs)
        self.streams.append(stream)
        return stream

    def stop(self):
        self.stops += 1

    def play(self, data, samplerate=None):
        self.played.append((data, samplerate))


class FakeOutData:
    """Records what the callback writes: outdata[a:b, 0] = seq and outdata[a:] = 0."""

    def __init__(self, frames):
        self.values = [None] * frames

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            sl = key[0]
            for i, v in zip(range(*sl.indices(len(self.values))), value):
                self.values[i] = v
        else:
            for i in range(*key.indices(len(self.values))):
                self.values[i] = value


def pump(stream: FakeOutputStream, frames: int):
    """Run one callback tick; return (values, stopped)."""
    out = FakeOutData(frames)
    try:
        stream.callback(out, frames, None, None)
        return out.values, False
    except CallbackStop:
        return out.values, True


@pytest.fixture
def streaming_audio(monkeypatch, isolated_config):
    sd = FakeStreamingSoundDevice()
    monkeypatch.setattr(tts_engine, "_sd", sd)
    monkeypatch.setattr(tts_engine, "_sf", None)
    monkeypatch.setattr(tts_engine, "_np", None)
    monkeypatch.setattr(tts_engine, "_ensure_audio", lambda: None)
    monkeypatch.setattr(tts_engine, "_ensure_imports", lambda: None)
    monkeypatch.setattr(tts_engine, "_stream_player", None)
    config.set_config({"streaming_playback": True})
    yield sd
    tts_engine._stop_stream_player()


def _patch_pipeline(monkeypatch, chunks, *, gate: threading.Event | None = None, seen: dict | None = None):
    """Fake pipeline yielding `chunks`; waits on `gate` before every chunk after the first."""
    def fake_pipeline(text, voice=None, speed=None, split_pattern=None):
        if seen is not None:
            seen["split_pattern"] = split_pattern
        for i, c in enumerate(chunks):
            if gate is not None and i > 0:
                gate.wait(timeout=5)
            yield ("gs", "ps", c)

    monkeypatch.setattr(tts_engine, "get_pipeline", lambda on_progress=None: fake_pipeline)


# ── StreamPlayer unit behaviour ───────────────────────────────────────────────

def test_callback_fills_across_chunks_and_zero_fills_then_stops():
    sd = FakeStreamingSoundDevice()
    player = tts_engine.StreamPlayer(sd, 24000)
    player.start()
    player.push([1, 2, 3])
    player.push([4, 5])
    stream = sd.streams[0]

    values, stopped = pump(stream, 4)
    assert values == [1, 2, 3, 4] and not stopped

    # Queue runs dry with the producer still working: zero-fill, one gap event.
    values, stopped = pump(stream, 3)
    assert values == [5, 0, 0] and not stopped
    assert player.underruns == 1
    values, stopped = pump(stream, 2)
    assert values == [0, 0] and not stopped
    assert player.underruns == 1            # same gap, not a new one
    assert player.starved_frames == 4

    # Data arrives, plays, runs dry again: a second gap.
    player.push([6])
    values, _ = pump(stream, 2)
    assert values == [6, 0]
    assert player.underruns == 2

    player.finish()
    values, stopped = pump(stream, 2)
    assert values == [0, 0] and stopped
    assert player.chunks_played == 3
    assert player.underruns == 2            # draining after finish() is not a gap


def test_status_flags_count_as_xruns_not_gaps():
    sd = FakeStreamingSoundDevice()
    player = tts_engine.StreamPlayer(sd, 24000)
    player.start()
    player.push([1, 2])
    out = FakeOutData(2)
    sd.streams[0].callback(out, 2, None, "output underflow")
    assert player.xruns == 1 and player.underruns == 0


def test_stream_chunks_merge_short_sentences():
    text = "Paragraph 1. " + "A" * 60 + ". " + "B" * 60 + ".\n\nParagraph 2. Short. End."
    chunks = tts_engine.stream_chunks(text, min_chars=100)
    assert chunks[0].startswith("Paragraph 1. AAAA")
    assert all(len(c) >= 50 for c in chunks)
    # No sentence is lost or split.
    assert " ".join(chunks).replace("  ", " ") == " ".join(
        s for s in text.replace("\n\n", " ").split(" ") if s
    )


def test_stream_chunks_keeps_short_text_whole():
    assert tts_engine.stream_chunks("Hi.") == ["Hi."]
    assert tts_engine.stream_chunks("") == []


def test_stop_drains_queue_and_aborts_stream():
    sd = FakeStreamingSoundDevice()
    player = tts_engine.StreamPlayer(sd, 24000)
    player.start()
    player.push([1, 2])
    player.stop()
    assert sd.streams[0].aborted and sd.streams[0].closed
    assert player.active is False
    assert player.wait(0) is True


def test_stalled_device_aborts_and_reports_error(monkeypatch):
    from fastapi.testclient import TestClient
    import server

    sd = FakeStreamingSoundDevice()
    player = tts_engine.StreamPlayer(sd, callback_timeout=0.05)
    monkeypatch.setattr(tts_engine, "_stream_player", player)
    player.push([1, 2])
    player.start()

    assert player.wait(2)
    assert sd.streams[0].aborted and sd.streams[0].closed
    assert tts_engine.playback_state()["state"] == "error"
    assert "stopped responding" in tts_engine.playback_state()["error"]
    monkeypatch.setattr(server, "check_dependencies", lambda: [])
    monkeypatch.setattr(tts_engine, "get_load_error", lambda: None)
    client = TestClient(server.app)
    assert client.get("/status").json()["playback"]["state"] == "error"
    assert "data.playback.error" in client.get("/control").text


def test_callbacks_prevent_timeout_and_normal_finish_stays_idle(monkeypatch):
    sd = FakeStreamingSoundDevice()
    player = tts_engine.StreamPlayer(sd, callback_timeout=0.25)
    monkeypatch.setattr(tts_engine, "_stream_player", player)
    player.start()
    player.push([1] * 20)
    for _ in range(8):
        pump(sd.streams[0], 1)
        time.sleep(0.05)
    assert player.active and player.error is None
    player.finish()
    _, stopped = pump(sd.streams[0], 30)
    assert stopped
    sd.streams[0].finished_callback()
    assert player.wait(1)
    assert tts_engine.playback_state()["state"] == "idle"
    player.stop()


def test_stream_opened_with_kokoro_format():
    sd = FakeStreamingSoundDevice()
    player = tts_engine.StreamPlayer(sd)
    player.start()
    s = sd.streams[0]
    assert (s.samplerate, s.channels, s.dtype, s.started) == (24000, 1, "float32", True)


# ── speak() in streaming mode ─────────────────────────────────────────────────

def test_speak_streams_first_chunk_before_synthesis_finishes(streaming_audio, monkeypatch):
    gate = threading.Event()
    seen = {}
    _patch_pipeline(monkeypatch, [[0.1], [0.2], [0.3]], gate=gate, seen=seen)

    result = tts_engine.speak("One.\nTwo.\nThree.")

    # Returned while the producer is still blocked on chunk two.
    assert result["status"] == "playing"
    assert result["streaming"] is True
    assert "saved_to" not in result
    assert seen["split_pattern"] == tts_engine.STREAM_SPLIT_PATTERN
    stream = streaming_audio.streams[0]
    assert stream.started
    player = tts_engine._stream_player
    assert player.chunks_queued == 1
    assert tts_engine.playback_state()["state"] == "playing"

    gate.set()
    deadline = threading.Event()
    for _ in range(200):
        if player._done.is_set():
            break
        deadline.wait(0.01)
    assert player.chunks_queued == 3
    assert player.error is None


def test_speak_streaming_saves_full_audio_after_synthesis(streaming_audio, monkeypatch):
    writes = []
    fake_np = types.SimpleNamespace(concatenate=lambda chunks: [x for c in chunks for x in c])
    monkeypatch.setattr(tts_engine, "_np", fake_np)
    monkeypatch.setattr(tts_engine, "save_wav", lambda data, sr: writes.append((data, sr)) or "/tmp/fake.wav")
    _patch_pipeline(monkeypatch, [[0.1], [0.2], [0.3]])

    result = tts_engine.speak("a. b. c.", save=True)

    assert result["saved_to"] == "/tmp/fake.wav"
    assert writes == [([0.1, 0.2, 0.3], 24000)]


def test_speak_streaming_empty_generator_returns_error_without_stream(streaming_audio, monkeypatch):
    _patch_pipeline(monkeypatch, [])
    result = tts_engine.speak("text")
    assert result["status"] == "error"
    assert "No audio" in result["message"]
    assert streaming_audio.streams == []


def test_speak_streaming_generator_failure_before_first_chunk(streaming_audio, monkeypatch):
    def broken(text, voice=None, speed=None, split_pattern=None):
        raise RuntimeError("phonemizer exploded")
        yield  # pragma: no cover

    monkeypatch.setattr(tts_engine, "get_pipeline", lambda on_progress=None: broken)
    result = tts_engine.speak("text")
    assert result == {"status": "error", "message": "phonemizer exploded"}
    assert streaming_audio.streams == []


def test_speak_streaming_producer_failure_is_recorded(streaming_audio, monkeypatch):
    def flaky(text, voice=None, speed=None, split_pattern=None):
        yield ("gs", "ps", [0.1])
        raise RuntimeError("mid-stream failure")

    monkeypatch.setattr(tts_engine, "get_pipeline", lambda on_progress=None: flaky)
    fake_np = types.SimpleNamespace(concatenate=lambda chunks: [x for c in chunks for x in c])
    monkeypatch.setattr(tts_engine, "_np", fake_np)

    result = tts_engine.speak("text", save=True)   # save=True waits for the producer

    assert result["status"] == "playing"
    assert result["save_error"] == "mid-stream failure"
    assert "saved_to" not in result
    assert tts_engine.playback_state()["error"] == "mid-stream failure"


def test_new_streaming_request_replaces_previous_stream(streaming_audio, monkeypatch):
    _patch_pipeline(monkeypatch, [[0.1]])
    tts_engine.speak("first")
    first = streaming_audio.streams[0]
    tts_engine.speak("second")
    assert first.aborted and first.closed
    assert len(streaming_audio.streams) == 2
    assert streaming_audio.stops >= 2        # sd.stop() guards buffered cloud playback too


def test_stop_audio_halts_live_stream(streaming_audio, monkeypatch):
    _patch_pipeline(monkeypatch, [[0.1]])
    tts_engine.speak("text")
    stream = streaming_audio.streams[0]
    tts_engine.stop_audio()
    assert stream.aborted
    assert tts_engine.playback_state() == {"state": "idle", "streaming": False}


def test_cloud_play_audio_stops_live_stream(streaming_audio, monkeypatch):
    _patch_pipeline(monkeypatch, [[0.1]])
    tts_engine.speak("text")
    stream = streaming_audio.streams[0]
    tts_engine.play_audio([0.5], 16000)
    assert stream.aborted
    assert streaming_audio.played == [([0.5], 16000)]


def test_flag_off_keeps_batch_behaviour(isolated_config, fake_audio, monkeypatch):
    config.set_config({"streaming_playback": False})
    seen = {}
    _patch_pipeline(monkeypatch, [[0.1], [0.2]], seen=seen)
    monkeypatch.setattr(tts_engine, "_ensure_imports", lambda: None)
    result = tts_engine.speak("a. b.")
    assert "streaming" not in result
    assert seen["split_pattern"] == r"\n+"
    assert fake_audio.sd.played[-1] == ([0.1, 0.2], 24000)


# ── Config default and HTTP surface ───────────────────────────────────────────

def test_streaming_playback_defaults_on(isolated_config):
    # SP-1 answered C (on everywhere) on 2026-10-26 after the real-audio run.
    assert config.get_config()["streaming_playback"] is True


def test_status_and_config_expose_streaming_flag(isolated_config, monkeypatch):
    from fastapi.testclient import TestClient
    import server

    monkeypatch.setattr(tts_engine, "is_loading", lambda: False)
    monkeypatch.setattr(tts_engine, "get_load_error", lambda: None)
    monkeypatch.setattr(server, "check_dependencies", lambda: [])
    monkeypatch.setattr(tts_engine, "_stream_player", None)
    client = TestClient(server.app)

    status = client.get("/status").json()
    assert status["streaming_playback"] is True
    assert status["playback"] == {"state": "idle", "streaming": False}

    r = client.patch("/config", json={"streaming_playback": False})
    assert r.status_code == 200
    assert r.json()["config"]["streaming_playback"] is False
    assert client.get("/status").json()["streaming_playback"] is False


def test_control_panel_has_streaming_switch(isolated_config):
    from fastapi.testclient import TestClient
    import server

    html = TestClient(server.app).get("/control").text
    assert 'id="streamingPlayback"' in html
    assert "streaming_playback" in html


# ── Audio device failures return a clean error, not a 500 ─────────────────────

class _NoDeviceError(Exception):
    pass


def test_streaming_start_failure_returns_error_and_leaves_no_player(streaming_audio, monkeypatch):
    def boom(**_kwargs):
        raise _NoDeviceError("Error querying device -1")

    monkeypatch.setattr(streaming_audio, "OutputStream", boom)
    _patch_pipeline(monkeypatch, [[0.1], [0.2]])

    result = tts_engine.speak("text")

    assert result["status"] == "error"
    assert "Audio output unavailable" in result["message"]
    assert "device -1" in result["message"]
    assert tts_engine.playback_state() == {"state": "idle", "streaming": False}


def test_batch_play_failure_returns_error(isolated_config, fake_audio, monkeypatch):
    config.set_config({"streaming_playback": False})
    _patch_pipeline(monkeypatch, [[0.1]])
    monkeypatch.setattr(tts_engine, "_ensure_imports", lambda: None)

    def boom(data, samplerate=None):
        raise _NoDeviceError("Error querying device -1")

    monkeypatch.setattr(fake_audio.sd, "play", boom)
    result = tts_engine.speak("text")
    assert result["status"] == "error"
    assert "Audio output unavailable" in result["message"]


def test_speak_endpoint_maps_audio_failure_to_503_json(isolated_config, monkeypatch):
    from fastapi.testclient import TestClient
    import server

    monkeypatch.setattr(
        tts_engine, "speak",
        lambda **_kw: {"status": "error", "message": tts_engine.audio_error_message(_NoDeviceError("x"))},
    )
    r = TestClient(server.app).post("/speak", json={"text": "hi"})
    assert r.status_code == 503
    assert r.json()["status"] == "error"


def test_speak_streaming_feeds_coalesced_chunks(streaming_audio, monkeypatch):
    seen = {}

    def capture(text, voice=None, speed=None, split_pattern=None):
        seen["text"] = text
        yield ("gs", "ps", [0.1])

    monkeypatch.setattr(tts_engine, "get_pipeline", lambda on_progress=None: capture)
    tts_engine.speak("Paragraph 1. " + "word " * 30 + ".")
    first_line = seen["text"].split("\n")[0]
    assert first_line.startswith("Paragraph 1. word")
