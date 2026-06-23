"""Tests for config.py — defaults, merge, corruption recovery, persistence."""
from __future__ import annotations

import json

import config


def test_defaults_when_no_file(isolated_config):
    cfg = config.get_config()
    assert cfg["engine"] == "kokoro"
    assert cfg["voice"] == "af_heart"
    assert cfg["port"] == 7778
    assert cfg["speed"] == 1.0
    assert cfg["history_enabled"] is False
    assert cfg["history_limit"] == 20
    # Returned dict must be a copy — mutating it must not poison DEFAULTS.
    cfg["voice"] = "mutated"
    assert config.DEFAULTS["voice"] == "af_heart"


def test_user_values_override_defaults(isolated_config):
    config.set_config({"voice": "am_adam", "speed": 1.5})
    cfg = config.get_config()
    assert cfg["voice"] == "am_adam"
    assert cfg["speed"] == 1.5
    # Untouched keys still fall back to defaults.
    assert cfg["port"] == 7778
    assert cfg["engine"] == "kokoro"


def test_malformed_json_falls_back_to_defaults(isolated_config):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text("{not valid json", encoding="utf-8")
    cfg = config.get_config()
    assert cfg == config.DEFAULTS or cfg["engine"] == "kokoro"
    assert cfg["port"] == 7778


def test_set_config_is_persistent_and_merges(isolated_config):
    config.set_config({"engine": "openai"})
    config.set_config({"speed": 2.0})
    on_disk = json.loads(isolated_config.read_text(encoding="utf-8"))
    # Second write must not clobber the first.
    assert on_disk["engine"] == "openai"
    assert on_disk["speed"] == 2.0


def test_secret_fields_persist_to_disk(isolated_config):
    config.set_config({"openai_api_key": "sk-secret"})
    on_disk = json.loads(isolated_config.read_text(encoding="utf-8"))
    assert on_disk["openai_api_key"] == "sk-secret"


def test_asset_path_points_into_assets_dir():
    p = config.asset_path("icon.png")
    assert p.endswith(("assets/icon.png", "assets\\icon.png"))
