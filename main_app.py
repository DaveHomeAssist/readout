"""
main_app.py — macOS packaged-app entry point

For the packaged macOS app, force the tray + browser control panel flow and
disable the Tk desktop window path, which is unstable with Homebrew Tk 9.
"""
from __future__ import annotations

import os

import main as readout_main


def main() -> None:
    os.environ.setdefault("READOUT_DISABLE_UI", "1")
    os.environ.setdefault("READOUT_AUTO_OPEN_CONTROL", "0")
    readout_main.main([])


if __name__ == "__main__":
    main()
