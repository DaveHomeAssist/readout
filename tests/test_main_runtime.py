"""Tests for startup/runtime UI routing decisions."""
from __future__ import annotations

import main
import main_app


def _reset_runtime(monkeypatch, platform: str):
    monkeypatch.setattr(main, "_ui_runtime", None)
    monkeypatch.setattr(main.sys, "platform", platform)
    monkeypatch.delenv("READOUT_FORCE_TK", raising=False)
    monkeypatch.delenv("READOUT_DISABLE_UI", raising=False)


def test_macos_uses_control_panel_as_primary_ui(monkeypatch):
    _reset_runtime(monkeypatch, "darwin")

    ui_ok, reason = main._get_ui_runtime()

    assert ui_ok is False
    assert "browser control panel" in reason


def test_force_tk_overrides_macos_control_panel_default(monkeypatch):
    _reset_runtime(monkeypatch, "darwin")
    monkeypatch.setenv("READOUT_FORCE_TK", "1")

    assert main._get_ui_runtime() == (True, "")


def test_non_macos_uses_tk_ui_by_default(monkeypatch):
    _reset_runtime(monkeypatch, "win32")

    assert main._get_ui_runtime() == (True, "")


def test_model_warmup_waits_for_server_before_heavy_import(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "_wait_for_server", lambda port: calls.append(("wait", port)) or True)
    monkeypatch.setattr(main.tts_engine, "get_pipeline", lambda on_progress=None: calls.append(("pipeline", None)))
    monkeypatch.setattr(main, "get_config", lambda: {"port": 7778})

    main._warmup_model()

    assert calls == [("wait", 7778), ("pipeline", None)]


def test_packaged_macos_entry_forces_tray_control_panel_flow(monkeypatch):
    calls = []
    monkeypatch.delenv("READOUT_DISABLE_UI", raising=False)
    monkeypatch.delenv("READOUT_AUTO_OPEN_CONTROL", raising=False)
    monkeypatch.setattr(main_app.readout_main, "main", lambda argv: calls.append(argv))

    main_app.main()

    assert calls == [[]]
    assert main_app.os.environ["READOUT_DISABLE_UI"] == "1"
    assert main_app.os.environ["READOUT_AUTO_OPEN_CONTROL"] == "0"
