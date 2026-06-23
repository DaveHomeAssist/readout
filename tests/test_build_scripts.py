"""Static checks for packaging preflight scripts."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_build_resolves_supported_python_before_build():
    text = (ROOT / "build_windows.ps1").read_text(encoding="utf-8")

    assert "Python Launcher 3.12" in text
    assert "Python Launcher 3.11" in text
    assert "Python Launcher 3.10" in text
    assert "Test-SupportedPython" in text
    assert "python --version 2>&1" not in text
    assert "Python 3.10-3.12 is required for Kokoro" in text
    assert "Get-Command espeak-ng" in text
    assert "-m PyInstaller" in text


def test_mac_build_checks_supported_python_and_espeak_before_build():
    text = (ROOT / "build_mac.sh").read_text(encoding="utf-8")

    assert "is_supported_python" in text
    assert "python3.12" in text
    assert "python3.11" in text
    assert "python3.10" in text
    assert "Existing .venv is not Python 3.10" in text
    assert "command -v espeak-ng" in text
    assert "brew install espeak-ng" in text
    assert ".venv/bin/python -m PyInstaller ReadOut.spec" in text


def test_pyinstaller_spec_includes_engine_modules():
    text = (ROOT / "ReadOut.spec").read_text(encoding="utf-8")

    assert "entry_script = 'main_app.py' if sys.platform == 'darwin' else 'main.py'" in text
    assert "(\"tkinter\" if sys.platform == 'darwin'" in text or '(["tkinter"] if sys.platform == \'darwin\'' in text

    for module in [
        "engines.registry",
        "engines.kokoro",
        "engines.openai",
        "engines.elevenlabs",
    ]:
        assert module in text
