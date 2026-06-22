"""Engine interface — the single contract every TTS backend implements.

An engine owns three things so the rest of the app never branches on engine
name: its synthesis, its voice catalogue, and its capability metadata (local vs
cloud, whether it needs an API key, whether it supports voice blending).
"""
from __future__ import annotations


class EngineError(Exception):
    """Raised when an engine cannot synthesize (auth, network, decode)."""


class TTSEngine:
    """Base class for TTS engines. Subclasses set the class attributes and
    implement ``list_voices`` and ``synthesize``."""

    name: str = ""
    label: str = ""
    is_local: bool = False
    requires_key: str | None = None   # config key holding the credential, or None
    supports_blend: bool = False

    def list_voices(self) -> list[dict]:
        """Return this engine's voice catalogue as ``[{'id', 'label'}, ...]``."""
        raise NotImplementedError

    def synthesize(self, req, cfg: dict) -> dict:
        """Synthesize ``req.text`` and play it; return a result dict.

        Success: ``{'status': 'playing', 'engine': name, 'saved_to'?: path}``
        (the Kokoro engine additionally returns ``voice``/``speed`` for
        backward compatibility). Failure: ``{'status': 'error', 'message': str}``.
        """
        raise NotImplementedError

    def describe(self) -> dict:
        """Capability + catalogue snapshot for the ``/voices`` response."""
        return {
            "name": self.name,
            "label": self.label,
            "is_local": self.is_local,
            "requires_key": self.requires_key,
            "supports_blend": self.supports_blend,
            "voices": self.list_voices(),
        }
