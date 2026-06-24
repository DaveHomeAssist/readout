"""Regression checks for the Chrome extension popup surface."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POPUP_HTML = ROOT / "extension" / "popup.html"
POPUP_JS = ROOT / "extension" / "popup.js"


def test_popup_has_status_detail_region():
    html = POPUP_HTML.read_text(encoding="utf-8")
    assert 'id="status-detail"' in html
    assert 'role="status"' in html
    assert 'id="btn-preview"' in html
    assert ">Preview<" in html
    assert ".status-detail.ready" in html
    assert ".status-detail.offline" in html
    assert ".status-detail.error" in html


def test_manifest_uses_least_privilege_permissions():
    manifest = (ROOT / "extension" / "manifest.json").read_text(encoding="utf-8")
    assert '"storage"' not in manifest
    assert '"version": "1.3"' in manifest


def test_popup_status_paths_include_next_actions():
    js = POPUP_JS.read_text(encoding="utf-8")
    assert "function setStatus" in js
    assert "function setLastError" in js
    assert "async function fetchWithTimeout" in js
    assert "function loadVoices" in js
    assert "`${READOUT_URL}/voices`" in js
    assert "`${READOUT_URL}/status`" in js
    assert "data.engines" in js
    assert "checkStatus();" in js
    assert "setTimeout(() => checkStatus(), 250)" in js
    assert "Server offline. Start the ReadOut desktop app" in js
    assert "Dependency issue:" in js
    assert "Select text on the page, then click Read Selection" in js
    assert "check the extension origin allowlist" in js
    assert "Could not save engine" in js
    assert "Server connected, but model failed" in js


def test_popup_preview_posts_selected_voice():
    js = POPUP_JS.read_text(encoding="utf-8")
    assert "btnPreview" in js
    assert "Previewing..." in js
    assert "`${READOUT_URL}/preview`" in js
    assert "voice: els.voice.value" in js
    assert "speed: parseFloat(els.speed.value)" in js
    assert "Could not preview voice" in js


def test_popup_stop_uses_shared_stop_handler():
    js = POPUP_JS.read_text(encoding="utf-8")
    assert "async function stopPlayback" in js
    assert "`${READOUT_URL}/stop`" in js
    assert 'setStatus("ready", "READY", "Stop sent to ReadOut.")' in js
    assert 'els.btnStop.addEventListener("click", () => {' in js
    assert "stopPlayback();" in js
