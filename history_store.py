"""Local recent-read history storage.

History is privacy-sensitive and disabled by default. When enabled, entries are
stored only in the user's ReadOut config directory and can be cleared via API.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any

import config


HISTORY_PATH = os.path.join(config.CONFIG_DIR, "history.json")
DEFAULT_HISTORY_LIMIT = 20
MAX_TEXT_CHARS = 500


def _history_path() -> str:
    return os.path.join(config.CONFIG_DIR, "history.json")


def _history_limit(cfg: dict | None = None) -> int:
    cfg = cfg or config.get_config()
    try:
        value = int(cfg.get("history_limit", DEFAULT_HISTORY_LIMIT))
    except (TypeError, ValueError):
        value = DEFAULT_HISTORY_LIMIT
    return max(1, min(value, 100))


def history_enabled(cfg: dict | None = None) -> bool:
    cfg = cfg or config.get_config()
    return bool(cfg.get("history_enabled", False))


def get_history() -> list[dict[str, Any]]:
    path = _history_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def add_read(text: str, *, engine: str, voice: str | None, speed: float | None) -> None:
    cfg = config.get_config()
    if not history_enabled(cfg):
        return

    cleaned = text.strip()
    if not cleaned:
        return

    entry = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engine": engine,
        "voice": voice,
        "speed": speed,
        "text": cleaned[:MAX_TEXT_CHARS],
    }
    history = [entry, *get_history()]
    history = history[:_history_limit(cfg)]

    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    with open(_history_path(), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def clear_history() -> None:
    try:
        os.remove(_history_path())
    except FileNotFoundError:
        pass
