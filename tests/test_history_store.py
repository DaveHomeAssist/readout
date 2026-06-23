"""Tests for local recent-read history storage."""
from __future__ import annotations

import os

import config
import history_store


def test_history_is_disabled_by_default(isolated_config):
    history_store.add_read("hello", engine="kokoro", voice="af_heart", speed=1.0)
    assert history_store.get_history() == []
    assert not os.path.exists(os.path.join(config.CONFIG_DIR, "history.json"))


def test_history_records_when_enabled_and_respects_limit(isolated_config):
    config.set_config({"history_enabled": True, "history_limit": 2})

    history_store.add_read("first", engine="kokoro", voice="af_heart", speed=1.0)
    history_store.add_read("second", engine="openai", voice="nova", speed=1.1)
    history_store.add_read("third", engine="elevenlabs", voice="Rachel", speed=1.2)

    history = history_store.get_history()
    assert [item["text"] for item in history] == ["third", "second"]
    assert history[0]["engine"] == "elevenlabs"
    assert history[0]["voice"] == "Rachel"
    assert history[0]["speed"] == 1.2
    assert "created_at" in history[0]


def test_clear_history_removes_file(isolated_config):
    config.set_config({"history_enabled": True})
    history_store.add_read("delete me", engine="kokoro", voice="af_heart", speed=1.0)
    assert history_store.get_history()

    history_store.clear_history()

    assert history_store.get_history() == []
