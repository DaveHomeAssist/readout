"""Regression checks for user-facing UI/docs copy."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import ui


ROOT = Path(__file__).resolve().parents[1]


def test_save_copy_says_wav_not_mp3():
    checked = [
        ROOT / "ui.py",
        ROOT / "HOW-TO-USE.md",
        ROOT / "README.md",
        ROOT / "extension" / "popup.html",
        ROOT / "extension" / "background.js",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in checked)

    assert "Save WAV" in combined
    assert "save WAV" in combined
    assert "Preview Voice" in combined
    assert "Save MP3" not in combined
    assert "save MP3" not in combined


def test_desktop_ui_has_only_supported_engine_tabs():
    assert set(ui.ENGINES) == {"kokoro", "openai", "elevenlabs"}
    assert set(ui.VOICES_BY_ENGINE) == {"kokoro", "openai", "elevenlabs"}


def test_desktop_ui_removed_inert_controls():
    source = (ROOT / "ui.py").read_text(encoding="utf-8")
    assert "Auto-read" not in source
    assert "_toggle_auto" not in source
    assert "Download button" not in source


def test_patch_helper_uses_patch_method_and_json(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"status":"updated"}'

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["data"] = req.data
        captured["headers"] = dict(req.header_items())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(ui.urllib.request, "urlopen", fake_urlopen)

    result = ui._patch("/config", {"engine": "openai"})

    assert result == {"status": "updated"}
    assert captured["url"].endswith("/config")
    assert captured["method"] == "PATCH"
    assert captured["data"] == b'{"engine": "openai"}'
    assert captured["headers"]["Content-type"] == "application/json"
    assert captured["timeout"] == 5


def test_desktop_preview_posts_to_preview_endpoint():
    source = (ROOT / "ui.py").read_text(encoding="utf-8")
    assert 'text="Preview Voice"' in source
    assert 'command=self._preview_voice' in source
    assert '_post("/preview"' in source


def test_voice_label_helpers_map_config_ids():
    assert ui._voice_id("af_heart (warm, feminine)") == "af_heart"
    assert ui._voice_label_for_engine("kokoro", "af_heart") == "af_heart (warm, feminine)"
    assert ui._voice_label_for_engine("openai", "nova") == "nova"


def test_voice_catalogue_parser_preserves_ids_for_config_patches():
    parsed = ui._voice_map_from_catalogue(
        {
            "engines": [
                {
                    "name": "kokoro",
                    "voices": [{"id": "af_heart", "label": "Heart - Warm & Gentle"}],
                },
                {
                    "name": "openai",
                    "voices": [{"id": "nova", "label": "Nova"}],
                },
            ]
        }
    )

    assert parsed == {
        "kokoro": ["af_heart (Heart - Warm & Gentle)"],
        "openai": ["nova"],
    }
    assert ui._voice_id(parsed["kokoro"][0]) == "af_heart"


def test_desktop_status_poll_loads_voice_catalogue_once():
    source = (ROOT / "ui.py").read_text(encoding="utf-8")
    assert '_get("/voices")' in source
    assert "_catalogue_loaded" in source


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeWidget:
    def __init__(self):
        self.calls = []

    def configure(self, **kwargs):
        self.calls.append(kwargs)


def test_engine_voice_and_speed_controls_patch_persisted_config():
    captured = []
    shell = SimpleNamespace(
        _engine=FakeVar("kokoro"),
        _voice=FakeVar("nova"),
        _speed=FakeVar(1.75),
        _speed_label=FakeWidget(),
        _engine_btns={
            "kokoro": FakeWidget(),
            "openai": FakeWidget(),
            "elevenlabs": FakeWidget(),
        },
        _model_badge=FakeWidget(),
        _current_voice_id=lambda: "nova",
        _patch_config=lambda payload: captured.append(payload),
    )

    ui.ReadOutApp._select_engine(shell, "openai")
    ui.ReadOutApp._select_voice(shell, "alloy")
    ui.ReadOutApp._on_speed_change(shell)

    assert captured == [
        {"engine": "openai", "voice": "nova"},
        {"voice": "alloy"},
        {"speed": 1.8},
    ]


def test_status_poll_applies_persisted_engine_voice_and_speed_without_repatching():
    captured = []

    def select_engine(engine, persist=True, selected_voice=None):
        captured.append(
            {
                "engine": engine,
                "persist": persist,
                "selected_voice": selected_voice,
            }
        )

    shell = SimpleNamespace(
        _status_dot=FakeWidget(),
        _speed=FakeVar(1.0),
        _speed_label=FakeWidget(),
        _select_engine=select_engine,
        _on_speed_change=lambda persist=True: captured.append({"speed_persist": persist}),
    )

    ui.ReadOutApp._apply_status(
        shell,
        {
            "status": "ready",
            "engine": "elevenlabs",
            "voice": "Rachel",
            "speed": 1.4,
        },
    )

    assert captured == [
        {"engine": "elevenlabs", "persist": False, "selected_voice": "Rachel"},
        {"speed_persist": False},
    ]
    assert shell._speed.get() == 1.4
