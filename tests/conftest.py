"""Shared pytest fixtures for the ReadOut test suite.

The suite never imports the heavy runtime stack (torch / kokoro / sounddevice).
`tts_engine` defers those imports to first use, so tests inject lightweight
fakes into the module globals instead of installing the real packages.
"""
from __future__ import annotations

import os
import sys
import types

import pytest

# Make the project root importable regardless of where pytest is invoked from.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point config + model-ready flag at a temp dir so tests never touch ~/.readout."""
    import config
    import tts_engine

    cfg_dir = tmp_path / ".readout"
    cfg_path = cfg_dir / "config.json"
    monkeypatch.setattr(config, "CONFIG_DIR", str(cfg_dir))
    monkeypatch.setattr(config, "CONFIG_PATH", str(cfg_path))
    monkeypatch.setattr(tts_engine, "MODEL_READY_FLAG", str(cfg_dir / ".model_ready"))
    return cfg_path


class FakeSoundDevice:
    """Records play/stop calls in place of the real sounddevice module."""

    def __init__(self):
        self.played = []
        self.stops = 0

    def play(self, data, samplerate=None):
        self.played.append((data, samplerate))

    def stop(self):
        self.stops += 1


class FakeSoundFile:
    """Stand-in for soundfile: records writes, returns a canned decode."""

    def __init__(self, decoded=None):
        self.writes = []
        self._decoded = decoded if decoded is not None else ([0.0], 24000)

    def write(self, path, data, samplerate):
        self.writes.append((path, data, samplerate))
        # Mimic soundfile actually creating a file on disk.
        with open(path, "wb") as fh:
            fh.write(b"RIFFFAKEWAVE")

    def read(self, buf):
        return self._decoded


class FakeNumpy:
    """Minimal numpy stand-in exposing only what tts_engine.speak uses."""

    @staticmethod
    def concatenate(chunks):
        flat = []
        for c in chunks:
            flat.extend(c)
        return flat


@pytest.fixture
def fake_audio(monkeypatch):
    """Inject fake numpy/sounddevice/soundfile into tts_engine and return them."""
    import tts_engine

    sd = FakeSoundDevice()
    sf = FakeSoundFile()
    np = FakeNumpy()
    monkeypatch.setattr(tts_engine, "_sd", sd)
    monkeypatch.setattr(tts_engine, "_sf", sf)
    monkeypatch.setattr(tts_engine, "_np", np)
    # _ensure_audio() is a no-op now that the globals are populated, but make
    # the intent explicit so an accidental real import can never happen.
    monkeypatch.setattr(tts_engine, "_ensure_audio", lambda: None)
    return types.SimpleNamespace(sd=sd, sf=sf, np=np)
