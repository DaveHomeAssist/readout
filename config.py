"""
config.py — ReadOut settings
Flat JSON at ~/.readout/config.json. Reloaded on every request, so
changes from the UI take effect without a restart.
"""
import json
import os
import sys

CONFIG_DIR  = os.path.expanduser("~/.readout")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# ── Resolve asset path whether running from source or PyInstaller bundle ──
def _asset(name: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)

DEFAULTS: dict = {
    "voice":             "af_heart",
    "speed":             1.0,
    "lang_code":         "a",          # 'a' = American EN, 'b' = British EN
    "always_save":       False,
    "save_dir":          os.path.expanduser("~/Desktop/ReadOut"),
    "port":              7778,          # 7777 reserved for DaveLLM Router
    "openai_api_key":    "",
    "elevenlabs_api_key": "",
    "engine":            "kokoro",      # kokoro | openai | elevenlabs
    "window_visible":    True,          # show main window on launch
    "allowed_origins":   [],            # extra exact browser origins, e.g. the Chrome extension ID
    "history_enabled":   False,         # local recent-read history is off by default
    "history_limit":     20,
}


def get_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                user = json.load(f)
            return {**DEFAULTS, **user}
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULTS.copy()


def set_config(updates: dict) -> None:
    current = get_config()
    current.update(updates)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        os.chmod(CONFIG_DIR, 0o700)
    except OSError:
        pass
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def asset_path(name: str) -> str:
    return _asset(name)
