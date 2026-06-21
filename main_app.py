"""
main_app.py — macOS packaged-app entry point

The packaged macOS app runs as a menu-bar (tray) app whose UI is the web
control panel at /control. It does not auto-open the browser on launch; use
the tray menu's "Open Control Panel" item.
"""
from __future__ import annotations

import os

import main as readout_main


def main() -> None:
    os.environ.setdefault("READOUT_AUTO_OPEN_CONTROL", "0")
    readout_main.main([])


if __name__ == "__main__":
    main()
