"""Pluggable TTS engines.

Each engine owns its synthesis, voice catalogue, and capability metadata. The
single extension point is ``engines.registry`` — adding a backend means
implementing ``engines.base.TTSEngine`` and registering it there. See
``engines/base.py`` for the interface.
"""
