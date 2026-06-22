"""Engine registry — the single place that knows which engines exist.

Routing (`/speak`), the voice catalogue (`/voices`), and any future tray/UI
that enumerates engines all consult this module instead of branching on engine
name. Adding an engine = implement TTSEngine and add one line here.
"""
from __future__ import annotations

from engines.base import TTSEngine
from engines.kokoro import KokoroEngine
from engines.openai import OpenAIEngine
from engines.elevenlabs import ElevenLabsEngine

DEFAULT_ENGINE = "kokoro"

_ENGINES: dict[str, TTSEngine] = {
    e.name: e for e in (KokoroEngine(), OpenAIEngine(), ElevenLabsEngine())
}


def get(name: str | None) -> TTSEngine:
    """Resolve an engine by name, falling back to the local default."""
    return _ENGINES.get(name or DEFAULT_ENGINE, _ENGINES[DEFAULT_ENGINE])


def names() -> list[str]:
    return list(_ENGINES)


def catalogue() -> list[dict]:
    """Per-engine capability + voice snapshot for the /voices response."""
    return [engine.describe() for engine in _ENGINES.values()]
