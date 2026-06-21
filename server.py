"""
server.py — ReadOut REST API
Endpoints:  POST /speak   POST /stop   GET /status   GET /voices   PATCH /config
CORS restricted to the companion Chrome extension and localhost dev tools.
Config responses redact provider API keys so the server never echoes back
the OpenAI / ElevenLabs credentials a user just stored.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

import tts_engine
import config as cfg_module

app = FastAPI(title="ReadOut TTS", version="1.0.0")

# Cap synthesis input so a huge paste can't pin CPU/RAM (issue 004).
MAX_TEXT_CHARS = 20_000

# Allow Chrome extension origins and local dev origins only. The service
# listens on 127.0.0.1:7778, so the previous wildcard CORS policy let any
# website the user visited drive the local daemon; pinning the origin closes
# that drive-by path. Note: chrome-extension://.* permits any extension, not
# just the companion one — the published extension ID is not pinned yet.
_ALLOWED_ORIGIN_REGEX = (
    r"^(chrome-extension://.*"
    r"|http://localhost(:\d+)?"
    r"|http://127\.0\.0\.1(:\d+)?)$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_ALLOWED_ORIGIN_REGEX,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

# Fields that must never appear in an HTTP response body. Keep this list
# in sync with any new provider credential added to ConfigUpdate below.
_SECRET_FIELDS = frozenset({"openai_api_key", "elevenlabs_api_key"})


def _public_config(cfg: dict) -> dict:
    """Return a copy of cfg safe to send over HTTP (credentials redacted)."""
    return {
        key: ("***" if key in _SECRET_FIELDS and value else value)
        for key, value in cfg.items()
    }


CONTROL_PANEL_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ReadOut Control Panel</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0e0e0e;
      --panel: #161616;
      --panel-2: #1e1e1e;
      --panel-3: #262626;
      --border: #2a2a2a;
      --border-2: #353535;
      --text: #e8e8e8;
      --muted: #8b8b8b;
      --faint: #5f5f5f;
      --accent: #b8f542;
      --accent-soft: rgba(184, 245, 66, 0.12);
      --accent-line: rgba(184, 245, 66, 0.34);
      --danger: #ff5252;
      --warn: #ffaa52;
      --blue: #52a8ff;
      --radius: 14px;
      --radius-sm: 10px;
      --gap: 18px;
    }
    * { box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 18% -10%, rgba(184, 245, 66, 0.10), transparent 32%),
        radial-gradient(circle at 100% 0%, rgba(82, 168, 255, 0.05), transparent 30%),
        linear-gradient(180deg, #111 0%, #090909 100%);
      color: var(--text);
      font-family: "SF Mono", "IBM Plex Mono", "JetBrains Mono", "Courier New", monospace;
      font-size: 14px;
      line-height: 1.5;
    }

    /* ── Layout shell ── */
    .shell {
      width: min(1180px, calc(100vw - 32px));
      margin: 28px auto;
    }
    @media (max-width: 720px) {
      .shell { width: calc(100vw - 20px); margin: 14px auto; }
    }

    /* ── Top app bar ── */
    .appbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 14px;
      padding: 14px 18px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: rgba(22, 22, 22, 0.92);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.32);
    }
    .brand { display: flex; align-items: center; gap: 11px; min-width: 0; }
    .brand-mark {
      width: 30px; height: 30px;
      flex-shrink: 0;
      border-radius: 9px;
      display: grid; place-items: center;
      background: var(--accent-soft);
      border: 1px solid var(--accent-line);
      color: var(--accent);
      font-size: 15px;
    }
    .brand-text { line-height: 1.15; min-width: 0; }
    .brand-name { font-size: 16px; font-weight: 700; letter-spacing: 0.04em; }
    .brand-sub { font-size: 10px; color: var(--faint); letter-spacing: 0.14em; text-transform: uppercase; }

    /* Tab switcher (Speak / Settings) — mirrors the extension's tab pattern */
    .tabs {
      display: flex;
      gap: 4px;
      margin-left: auto;
      padding: 3px;
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 999px;
    }
    .tab {
      appearance: none;
      border: 0;
      background: transparent;
      color: var(--muted);
      font: inherit;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 7px 16px;
      border-radius: 999px;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }
    .tab:hover { color: var(--text); }
    .tab[aria-selected="true"] {
      background: var(--panel-3);
      color: var(--text);
      box-shadow: inset 0 0 0 1px var(--border-2);
    }

    /* Status chip */
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 13px;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
      background: var(--panel-2);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      white-space: nowrap;
    }
    .status .dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: currentColor;
      box-shadow: 0 0 7px currentColor;
    }
    .status[data-state="ready"]   { color: var(--accent); border-color: var(--accent-line); }
    .status[data-state="loading"] { color: var(--warn);   border-color: rgba(255,170,82,0.4); }
    .status[data-state="offline"] { color: var(--danger); border-color: rgba(255,82,82,0.4); }
    .status[data-state="loading"] .dot { animation: pulse 1.1s ease-in-out infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }

    /* ── Main grid: composer + rail ── */
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: var(--gap);
      margin-top: var(--gap);
      align-items: start;
    }
    @media (max-width: 980px) {
      .grid { grid-template-columns: 1fr; }
    }

    .card {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: rgba(22, 22, 22, 0.92);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28);
    }
    .card-pad { padding: 18px; }
    .rail { display: grid; gap: var(--gap); }

    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }
    .section-title {
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--faint);
    }

    /* ── Composer ── */
    .composer-wrap { position: relative; }
    textarea#text {
      width: 100%;
      min-height: 340px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: var(--panel-2);
      color: var(--text);
      padding: 14px 14px 38px;
      font: inherit;
      line-height: 1.65;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    @media (max-width: 980px) { textarea#text { min-height: 220px; } }
    textarea#text::placeholder { color: var(--faint); }
    .char-count {
      position: absolute;
      right: 12px; bottom: 12px;
      font-size: 11px;
      color: var(--faint);
      pointer-events: none;
      background: rgba(22,22,22,0.7);
      padding: 1px 6px;
      border-radius: 6px;
    }
    .char-count.warn { color: var(--warn); }
    .char-count.over { color: var(--danger); }

    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    /* ── Buttons ── */
    button.btn {
      appearance: none;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 11px 16px;
      font: inherit;
      font-size: 13px;
      color: var(--text);
      background: var(--panel-2);
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s, color 0.15s, transform 0.05s;
    }
    button.btn:hover:not(:disabled) { border-color: var(--border-2); background: var(--panel-3); }
    button.btn:active:not(:disabled) { transform: translateY(1px); }
    button.btn:disabled { opacity: 0.4; cursor: not-allowed; }
    button.btn.ghost { background: transparent; color: var(--muted); }
    button.btn.ghost:hover:not(:disabled) { color: var(--text); }
    button.btn.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #0a1400;
      font-weight: 700;
    }
    button.btn.primary:hover:not(:disabled) { background: #c8ff52; border-color: #c8ff52; }
    button.btn.stop { border-color: rgba(255, 82, 82, 0.45); color: var(--danger); }
    button.btn.stop:hover:not(:disabled) { background: rgba(255, 82, 82, 0.10); }

    .transport {
      display: grid;
      grid-template-columns: 2fr 2fr 1fr;
      gap: 8px;
      margin-top: 14px;
    }
    @media (max-width: 460px) { .transport { grid-template-columns: 1fr 1fr; } }

    /* ── Form fields ── */
    .field { display: flex; flex-direction: column; gap: 7px; }
    .field + .field { margin-top: 14px; }
    label {
      color: var(--muted);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }
    .hint { font-size: 11px; color: var(--faint); line-height: 1.45; }

    select, input[type="text"], input[type="password"] {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: var(--panel-2);
      color: var(--text);
      padding: 11px 12px;
      font: inherit;
      font-size: 13px;
    }
    select { appearance: none; cursor: pointer; padding-right: 30px;
      background-image: linear-gradient(45deg, transparent 50%, var(--muted) 50%),
                        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position: calc(100% - 16px) 52%, calc(100% - 11px) 52%;
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
    }
    option { background: var(--panel-2); }

    /* Engine segmented control */
    .engine-seg { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
    .engine-opt {
      position: relative;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: var(--panel-2);
      padding: 10px 6px 9px;
      cursor: pointer;
      text-align: center;
      transition: border-color 0.15s, background 0.15s;
    }
    .engine-opt:hover { border-color: var(--border-2); }
    .engine-opt .e-name { font-size: 12px; color: var(--text); }
    .engine-opt .e-tag {
      display: inline-block;
      margin-top: 4px;
      font-size: 8px;
      letter-spacing: 0.08em;
      padding: 1px 5px;
      border-radius: 3px;
    }
    .engine-opt .e-tag.local { background: var(--accent-soft); color: var(--accent); }
    .engine-opt .e-tag.api   { background: rgba(82,168,255,0.14); color: var(--blue); }
    .engine-opt .e-tag.prem  { background: rgba(255,170,82,0.14); color: var(--warn); }
    .engine-opt input { position: absolute; opacity: 0; pointer-events: none; }
    .engine-opt:has(input:checked) {
      border-color: var(--accent-line);
      background: var(--accent-soft);
      box-shadow: inset 0 0 0 1px var(--accent-line);
    }
    .engine-opt:has(input:checked) .e-name { color: var(--accent); }

    /* Speed slider */
    .speed-row { display: flex; align-items: center; gap: 12px; }
    input[type="range"] {
      flex: 1;
      -webkit-appearance: none;
      appearance: none;
      height: 4px;
      border-radius: 2px;
      background: var(--panel-3);
      cursor: pointer;
    }
    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 16px; height: 16px;
      border-radius: 50%;
      background: var(--accent);
      border: 2px solid #0d0d0d;
      box-shadow: 0 0 8px var(--accent-soft);
    }
    input[type="range"]::-moz-range-thumb {
      width: 14px; height: 14px;
      border-radius: 50%;
      background: var(--accent);
      border: 2px solid #0d0d0d;
    }
    .speed-value {
      min-width: 46px; text-align: right;
      color: var(--accent); font-size: 14px; font-weight: 700;
    }

    /* Toggle (Always Save) */
    .toggle-row {
      display: flex; align-items: center; justify-content: space-between; gap: 12px;
    }
    .toggle-row .toggle-copy { min-width: 0; }
    .toggle-row .toggle-copy .t-title { font-size: 13px; color: var(--text); }
    .switch { position: relative; flex-shrink: 0; width: 42px; height: 24px; }
    .switch input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
    .switch .track {
      position: absolute; inset: 0;
      border-radius: 999px;
      background: var(--panel-3);
      border: 1px solid var(--border);
      transition: background 0.15s, border-color 0.15s;
    }
    .switch .knob {
      position: absolute; top: 3px; left: 3px;
      width: 16px; height: 16px; border-radius: 50%;
      background: var(--muted);
      transition: transform 0.15s, background 0.15s;
    }
    .switch input:checked ~ .track { background: var(--accent-soft); border-color: var(--accent-line); }
    .switch input:checked ~ .knob  { transform: translateX(18px); background: var(--accent); }

    /* Save dir / key indicators */
    .kv {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: var(--panel-2);
      font-size: 12px;
      color: var(--muted);
      word-break: break-all;
    }
    .kv .kv-icon { color: var(--faint); flex-shrink: 0; }
    .badge {
      display: inline-flex; align-items: center; gap: 5px;
      font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase;
      padding: 3px 8px; border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--faint);
      white-space: nowrap;
    }
    .badge.set { color: var(--accent); border-color: var(--accent-line); background: var(--accent-soft); }
    .key-row { display: flex; gap: 8px; align-items: stretch; }
    .key-row input { flex: 1; }

    /* Feedback / meta line (aria-live) */
    .feedback {
      margin-top: 14px;
      padding: 11px 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: var(--panel-2);
      color: var(--muted);
      font-size: 12px;
      min-height: 42px;
      display: flex; align-items: center; gap: 9px;
      transition: border-color 0.2s, color 0.2s;
    }
    .feedback[data-tone="ok"]    { border-color: var(--accent-line); color: var(--accent); }
    .feedback[data-tone="error"] { border-color: rgba(255,82,82,0.45); color: var(--danger); }
    .feedback[data-tone="busy"]  { border-color: rgba(255,170,82,0.4); color: var(--warn); }

    .info-note {
      margin-top: var(--gap);
      padding: 12px 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: rgba(20,20,20,0.7);
      color: var(--muted);
      font-size: 11.5px;
      line-height: 1.6;
    }
    .info-note code { color: var(--accent); }

    [hidden] { display: none !important; }
    .kbd {
      font-size: 10px; color: var(--faint);
      border: 1px solid var(--border); border-radius: 5px;
      padding: 1px 6px;
    }

    /* Accessible focus */
    a:focus-visible, button:focus-visible, select:focus-visible,
    textarea:focus-visible, input:focus-visible, [tabindex]:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
      border-radius: 8px;
    }
    textarea#text:focus-visible, select:focus-visible,
    input[type="text"]:focus-visible, input[type="password"]:focus-visible {
      outline: none;
      border-color: var(--accent-line);
      box-shadow: 0 0 0 2px var(--accent-soft);
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <!-- Top app bar -->
    <header class="appbar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">&#9658;</div>
        <div class="brand-text">
          <div class="brand-name">ReadOut</div>
          <div class="brand-sub">Local TTS Control Panel</div>
        </div>
      </div>
      <div class="tabs" role="tablist" aria-label="Panel views">
        <button class="tab" id="tabSpeakBtn" role="tab" aria-selected="true" aria-controls="view-speak" type="button">Speak</button>
        <button class="tab" id="tabSettingsBtn" role="tab" aria-selected="false" aria-controls="view-settings" type="button">Settings</button>
      </div>
      <div id="status" class="status" data-state="offline" role="status" aria-live="polite">
        <span class="dot" aria-hidden="true"></span><span id="statusLabel">Offline</span>
      </div>
    </header>

    <!-- SPEAK VIEW -->
    <div id="view-speak" role="tabpanel" aria-labelledby="tabSpeakBtn">
      <div class="grid">
        <!-- Composer -->
        <section class="card card-pad" aria-label="Text to speak">
          <div class="section-head">
            <span class="section-title">Compose</span>
            <span class="hint"><span class="kbd">&#8984;/Ctrl + Enter</span> to speak</span>
          </div>
          <div class="composer-wrap">
            <textarea id="text" aria-label="Text to speak"
              placeholder="Paste or type text here, then press Speak. Select text on any web page and use the extension to send it here automatically."></textarea>
            <div class="char-count" id="charCount" aria-hidden="true">0</div>
          </div>
          <div class="toolbar">
            <button class="btn ghost" id="pasteBtn" type="button">Paste</button>
            <button class="btn ghost" id="clearBtn" type="button">Clear</button>
            <span class="hint" id="charLimitHint" style="margin-left:auto;align-self:center;">Limit 20,000 chars</span>
          </div>
          <div class="transport">
            <button class="btn primary" id="speakBtn" type="button">Speak</button>
            <button class="btn" id="saveBtn" type="button">Speak &amp; Save WAV</button>
            <button class="btn stop" id="stopBtn" type="button">Stop</button>
          </div>
          <div class="feedback" id="feedback" role="status" aria-live="polite">Waiting for local server status&#8230;</div>
        </section>

        <!-- Controls rail -->
        <aside class="rail" aria-label="Voice controls">
          <section class="card card-pad">
            <div class="section-head"><span class="section-title">Engine</span></div>
            <div class="engine-seg" id="engineSeg" role="radiogroup" aria-label="TTS engine">
              <label class="engine-opt">
                <input type="radio" name="engine" value="kokoro" checked>
                <div class="e-name">Kokoro</div><div class="e-tag local">Local</div>
              </label>
              <label class="engine-opt">
                <input type="radio" name="engine" value="openai">
                <div class="e-name">OpenAI</div><div class="e-tag api">API</div>
              </label>
              <label class="engine-opt">
                <input type="radio" name="engine" value="elevenlabs">
                <div class="e-name">11Labs</div><div class="e-tag prem">API</div>
              </label>
            </div>
            <div class="field" style="margin-top:14px;">
              <label for="voice">Voice</label>
              <select id="voice" aria-label="Voice"></select>
              <span class="hint" id="voiceHint">Kokoro supports blending, e.g. <code>af_heart:60,am_adam:40</code>.</span>
            </div>
            <div class="field">
              <label for="speed">Speed <span id="speedValue" class="speed-value" style="float:right">1.0&#215;</span></label>
              <div class="speed-row">
                <input id="speed" type="range" min="0.5" max="2.0" step="0.1" value="1.0"
                  aria-label="Speech speed" aria-valuetext="1.0 times">
              </div>
            </div>
          </section>

          <section class="card card-pad">
            <div class="section-head"><span class="section-title">Output</span></div>
            <div class="toggle-row">
              <div class="toggle-copy">
                <div class="t-title">Always save WAV</div>
                <div class="hint">Write every clip to disk automatically.</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="alwaysSave" aria-label="Always save WAV">
                <span class="track" aria-hidden="true"></span><span class="knob" aria-hidden="true"></span>
              </label>
            </div>
            <div class="field" style="margin-top:14px;">
              <label>Save directory</label>
              <div class="kv"><span class="kv-icon" aria-hidden="true">&#128193;</span><span id="saveDir">&#8230;</span></div>
            </div>
          </section>
        </aside>
      </div>
    </div>

    <!-- SETTINGS VIEW -->
    <div id="view-settings" role="tabpanel" aria-labelledby="tabSettingsBtn" hidden>
      <div class="grid">
        <section class="card card-pad" aria-label="API keys">
          <div class="section-head"><span class="section-title">API Keys</span></div>
          <p class="hint" style="margin:-4px 0 16px;">Keys are stored locally in <code>~/.readout/config.json</code> (owner-only) and never sent back to this page. Fields are write-only &#8212; an indicator shows whether a key is set.</p>

          <div class="field" id="openaiField">
            <label for="openaiKey">OpenAI API key <span class="badge" id="openaiBadge" style="float:right;">Not set</span></label>
            <div class="key-row">
              <input type="password" id="openaiKey" autocomplete="off" spellcheck="false" placeholder="sk-&#8230;">
              <button class="btn" id="openaiSave" type="button">Save</button>
            </div>
          </div>

          <div class="field" id="elevenField">
            <label for="elevenKey">ElevenLabs API key <span class="badge" id="elevenBadge" style="float:right;">Not set</span></label>
            <div class="key-row">
              <input type="password" id="elevenKey" autocomplete="off" spellcheck="false" placeholder="&#8230;">
              <button class="btn" id="elevenSave" type="button">Save</button>
            </div>
          </div>
          <div class="feedback" id="settingsFeedback" role="status" aria-live="polite">Manage engine credentials here.</div>
        </section>

        <aside class="rail">
          <section class="card card-pad">
            <div class="section-head"><span class="section-title">Status</span></div>
            <div class="field">
              <label>Active engine</label>
              <div class="kv"><span id="cfgEngine">&#8230;</span></div>
            </div>
            <div class="field">
              <label>Active voice</label>
              <div class="kv"><span id="cfgVoice">&#8230;</span></div>
            </div>
            <div class="field">
              <label>Model</label>
              <div class="kv"><span id="cfgModel">&#8230;</span></div>
            </div>
            <div class="field">
              <label>API endpoint</label>
              <div class="kv"><span id="cfgEndpoint">&#8230;</span></div>
            </div>
            <div class="toolbar" style="margin-top:14px;">
              <button class="btn" id="refreshBtn" type="button">Refresh status</button>
            </div>
          </section>
        </aside>
      </div>
    </div>

    <div class="info-note">
      This web control panel is the primary desktop interface on systems where the native window can&#8217;t start
      (e.g. macOS 26+). The local API runs at <code id="apiBase">http://127.0.0.1:7778</code> and never leaves your machine when using Kokoro.
    </div>
  </main>

  <script>
    const BASE = window.location.origin;
    const MAX_CHARS_DEFAULT = 20000;
    let MAX_CHARS = MAX_CHARS_DEFAULT;

    // Hardcoded fallback voice lists. /voices is authoritative for Kokoro;
    // OpenAI/ElevenLabs have no list endpoint, so these always apply.
    const FALLBACK_VOICES = {
      kokoro: [
        "af_heart", "af_sky", "af_bella", "af_sarah", "af_nicole",
        "af_jessica", "af_nova", "af_river", "af_kore", "af_aoede",
        "am_adam", "am_echo", "am_michael", "am_fenrir",
        "bf_emma", "bf_isabella", "bm_george", "bm_lewis"
      ].map((id) => ({ id, label: id })),
      openai: ["alloy", "echo", "fable", "onyx", "nova", "shimmer"].map((id) => ({ id, label: id })),
      elevenlabs: ["Rachel", "Domi", "Bella", "Antoni", "Elli", "Josh", "Arnold", "Adam", "Sam"].map((id) => ({ id, label: id }))
    };
    let kokoroVoices = FALLBACK_VOICES.kokoro;

    const $ = (id) => document.getElementById(id);
    const els = {
      status: $("status"), statusLabel: $("statusLabel"),
      feedback: $("feedback"), settingsFeedback: $("settingsFeedback"),
      voice: $("voice"), voiceHint: $("voiceHint"),
      text: $("text"), charCount: $("charCount"),
      speed: $("speed"), speedValue: $("speedValue"),
      speakBtn: $("speakBtn"), saveBtn: $("saveBtn"), stopBtn: $("stopBtn"),
      refreshBtn: $("refreshBtn"), pasteBtn: $("pasteBtn"), clearBtn: $("clearBtn"),
      alwaysSave: $("alwaysSave"), saveDir: $("saveDir"),
      openaiKey: $("openaiKey"), elevenKey: $("elevenKey"),
      openaiSave: $("openaiSave"), elevenSave: $("elevenSave"),
      openaiBadge: $("openaiBadge"), elevenBadge: $("elevenBadge"),
      openaiField: $("openaiField"), elevenField: $("elevenField"),
      cfgEngine: $("cfgEngine"), cfgVoice: $("cfgVoice"),
      cfgModel: $("cfgModel"), cfgEndpoint: $("cfgEndpoint"),
      apiBase: $("apiBase")
    };
    let online = false;

    function currentEngine() {
      const checked = document.querySelector('input[name="engine"]:checked');
      return checked ? checked.value : "kokoro";
    }
    function setEngine(engine) {
      const radio = document.querySelector(`input[name="engine"][value="${engine}"]`);
      if (radio) radio.checked = true;
    }

    function voicesFor(engine) {
      return engine === "kokoro" ? kokoroVoices : (FALLBACK_VOICES[engine] || []);
    }

    function updateVoices(engine, selectedVoice) {
      const list = voicesFor(engine);
      els.voice.innerHTML = list.map((v) => {
        const sel = v.id === selectedVoice ? " selected" : "";
        return `<option value="${v.id}"${sel}>${v.label}</option>`;
      }).join("");
      if (selectedVoice && !list.some((v) => v.id === selectedVoice) && /[,:]/.test(selectedVoice)) {
        // Preserve a custom blend string that isn't in the list.
        const opt = document.createElement("option");
        opt.value = selectedVoice; opt.textContent = selectedVoice + " (blend)"; opt.selected = true;
        els.voice.appendChild(opt);
      }
      if (!els.voice.value && list.length) els.voice.value = list[0].id;
      els.voiceHint.hidden = engine !== "kokoro";
    }

    function reflectEngineKeys(engine) {
      // Show the API-key field for the active engine in Settings context.
      els.openaiField.style.opacity = engine === "openai" ? "1" : "0.55";
      els.elevenField.style.opacity = engine === "elevenlabs" ? "1" : "0.55";
    }

    function setStatus(state) {
      const label = state === "ready" ? "Ready" : state === "loading" ? "Loading" : "Offline";
      els.status.dataset.state = state;
      els.statusLabel.textContent = label;
      online = state !== "offline";
      els.speakBtn.disabled = !online;
      els.saveBtn.disabled = !online;
    }

    function setFeedback(target, message, tone) {
      target.textContent = message;
      if (tone) target.dataset.tone = tone; else delete target.dataset.tone;
    }

    function setBadge(badge, isSet) {
      badge.textContent = isSet ? "Key set" : "Not set";
      badge.classList.toggle("set", !!isSet);
    }

    function updateCharCount() {
      const len = els.text.value.length;
      els.charCount.textContent = len.toLocaleString();
      els.charCount.classList.toggle("over", len > MAX_CHARS);
      els.charCount.classList.toggle("warn", len > MAX_CHARS * 0.9 && len <= MAX_CHARS);
    }

    async function patchConfig(payload) {
      try {
        const res = await fetch(`${BASE}/config`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        return await res.json();
      } catch (_e) {
        return null;
      }
    }

    async function loadVoices() {
      try {
        const res = await fetch(`${BASE}/voices`, { signal: AbortSignal.timeout(2500) });
        const data = await res.json();
        if (Array.isArray(data.voices) && data.voices.length) {
          kokoroVoices = data.voices.map((v) =>
            typeof v === "string" ? { id: v, label: v } : { id: v.id, label: v.label || v.id });
        }
      } catch (_e) { /* keep fallback */ }
    }

    async function refreshStatus() {
      try {
        const res = await fetch(`${BASE}/status`, { signal: AbortSignal.timeout(2500) });
        const data = await res.json();
        setStatus(data.status || "offline");

        const engine = data.engine || "kokoro";
        setEngine(engine);
        if (typeof data.max_text_chars === "number") {
          MAX_CHARS = data.max_text_chars;
          $("charLimitHint").textContent = "Limit " + MAX_CHARS.toLocaleString() + " chars";
          updateCharCount();
        }
        updateVoices(engine, data.voice);
        reflectEngineKeys(engine);

        els.speed.value = data.speed || 1.0;
        els.speedValue.textContent = Number(els.speed.value).toFixed(1) + "×";
        els.speed.setAttribute("aria-valuetext", Number(els.speed.value).toFixed(1) + " times");

        if (typeof data.always_save === "boolean") els.alwaysSave.checked = data.always_save;
        els.saveDir.textContent = data.save_dir || "~/Desktop/ReadOut";

        setBadge(els.openaiBadge, data.openai_api_key);
        setBadge(els.elevenBadge, data.elevenlabs_api_key);

        // Settings status mirror
        els.cfgEngine.textContent = engine;
        els.cfgVoice.textContent = data.voice || "—";
        els.cfgModel.textContent = data.model_ready ? "Ready" : (data.status === "loading" ? "Loading…" : "Not loaded");
        els.cfgEndpoint.textContent = BASE;

        if (data.load_error) {
          setFeedback(els.feedback, "Engine error: " + data.load_error, "error");
        } else if (els.feedback.dataset.tone === "error" || !els.feedback.dataset.tone) {
          setFeedback(els.feedback,
            `Ready · ${engine} · ${data.voice || ""} · ${Number(data.speed || 1).toFixed(1)}×`, "");
        }
      } catch (_e) {
        setStatus("offline");
        setFeedback(els.feedback, "The local ReadOut API is not responding. Make sure the app is running.", "error");
        els.cfgModel.textContent = "Offline";
        els.cfgEndpoint.textContent = BASE;
      }
    }

    async function speak(save) {
      const text = els.text.value.trim();
      if (!text) {
        setFeedback(els.feedback, "Enter some text first.", "error");
        els.text.focus();
        return;
      }
      if (text.length > MAX_CHARS) {
        setFeedback(els.feedback, `Text is too long (${text.length.toLocaleString()} / ${MAX_CHARS.toLocaleString()} chars).`, "error");
        return;
      }
      setFeedback(els.feedback, save ? "Synthesizing and saving…" : "Synthesizing…", "busy");
      els.speakBtn.disabled = true; els.saveBtn.disabled = true;
      try {
        const res = await fetch(`${BASE}/speak`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, voice: els.voice.value, speed: Number(els.speed.value), save })
        });
        const data = await res.json();
        if (data.status === "error") {
          setFeedback(els.feedback, data.message || "Synthesis failed.", "error");
        } else if (data.saved_to) {
          setFeedback(els.feedback, "Saved to " + data.saved_to, "ok");
        } else {
          setFeedback(els.feedback, "Playing…", "ok");
        }
      } catch (_e) {
        setFeedback(els.feedback, "Could not reach the local server.", "error");
      } finally {
        els.speakBtn.disabled = !online; els.saveBtn.disabled = !online;
        refreshStatus();
      }
    }

    // ── Tab switching ──
    function showView(which) {
      const speak = which === "speak";
      $("view-speak").hidden = !speak;
      $("view-settings").hidden = speak;
      $("tabSpeakBtn").setAttribute("aria-selected", String(speak));
      $("tabSettingsBtn").setAttribute("aria-selected", String(!speak));
    }
    $("tabSpeakBtn").addEventListener("click", () => showView("speak"));
    $("tabSettingsBtn").addEventListener("click", () => { showView("settings"); refreshStatus(); });

    // ── Wiring ──
    els.text.addEventListener("input", updateCharCount);
    els.text.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); speak(false); }
    });

    document.querySelectorAll('input[name="engine"]').forEach((r) => {
      r.addEventListener("change", async () => {
        const engine = currentEngine();
        updateVoices(engine);
        reflectEngineKeys(engine);
        await patchConfig({ engine, voice: els.voice.value });
        refreshStatus();
      });
    });

    els.voice.addEventListener("change", async () => {
      await patchConfig({ voice: els.voice.value });
    });

    els.speed.addEventListener("input", () => {
      const v = Number(els.speed.value).toFixed(1);
      els.speedValue.textContent = v + "×";
      els.speed.setAttribute("aria-valuetext", v + " times");
    });
    els.speed.addEventListener("change", () => patchConfig({ speed: Number(els.speed.value) }));

    els.alwaysSave.addEventListener("change", async () => {
      await patchConfig({ always_save: els.alwaysSave.checked });
      setFeedback(els.feedback, els.alwaysSave.checked ? "Always-save enabled." : "Always-save disabled.", "ok");
    });

    els.speakBtn.addEventListener("click", () => speak(false));
    els.saveBtn.addEventListener("click", () => speak(true));
    els.stopBtn.addEventListener("click", async () => {
      try { await fetch(`${BASE}/stop`, { method: "POST" }); setFeedback(els.feedback, "Playback stopped.", ""); }
      catch (_e) { setFeedback(els.feedback, "Could not reach the local server.", "error"); }
    });
    els.refreshBtn.addEventListener("click", refreshStatus);

    els.pasteBtn.addEventListener("click", async () => {
      try {
        const t = await navigator.clipboard.readText();
        els.text.value = t; updateCharCount(); els.text.focus();
      } catch (_e) {
        setFeedback(els.feedback, "Clipboard access was blocked. Paste manually with ⌘/Ctrl+V.", "error");
      }
    });
    els.clearBtn.addEventListener("click", () => { els.text.value = ""; updateCharCount(); els.text.focus(); });

    async function saveKey(field, inputEl, badgeEl, name) {
      const val = inputEl.value.trim();
      if (!val) { setFeedback(els.settingsFeedback, "Enter a key first.", "error"); return; }
      const result = await patchConfig({ [field]: val });
      inputEl.value = "";
      const set = result && result.config ? result.config[field] : true;
      setBadge(badgeEl, set);
      setFeedback(els.settingsFeedback, name + " key saved.", "ok");
    }
    els.openaiSave.addEventListener("click", () => saveKey("openai_api_key", els.openaiKey, els.openaiBadge, "OpenAI"));
    els.elevenSave.addEventListener("click", () => saveKey("elevenlabs_api_key", els.elevenKey, els.elevenBadge, "ElevenLabs"));

    // ── Init ──
    els.apiBase.textContent = BASE;
    (async () => {
      await loadVoices();
      updateVoices(currentEngine());
      await refreshStatus();
      setInterval(refreshStatus, 5000);
    })();
  </script>
</body>
</html>
"""


# ── Request / response models ─────────────────────────────────────────────────

class SpeakRequest(BaseModel):
    text:  str
    voice: str   | None = None
    speed: float | None = None
    save:  bool         = False


class ConfigUpdate(BaseModel):
    voice:            str   | None = None
    speed:            float | None = None
    always_save:      bool  | None = None
    engine:           str   | None = None
    openai_api_key:   str   | None = None
    elevenlabs_api_key: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/control")


@app.get("/control", response_class=HTMLResponse, include_in_schema=False)
def control_panel():
    return HTMLResponse(CONTROL_PANEL_HTML)

@app.post("/speak")
def speak(req: SpeakRequest):
    """
    Synthesise and play text.
    Routes to the active engine from config.
    """
    if len(req.text) > MAX_TEXT_CHARS:
        return {
            "status": "error",
            "message": f"Text too long ({len(req.text)} chars; max {MAX_TEXT_CHARS}).",
        }

    cfg    = cfg_module.get_config()
    engine = cfg.get("engine", "kokoro")

    if engine == "openai":
        return _speak_openai(req, cfg)
    if engine == "elevenlabs":
        return _speak_elevenlabs(req, cfg)

    # Default: Kokoro local
    return tts_engine.speak(
        text  = req.text,
        voice = req.voice,
        speed = req.speed,
        save  = req.save,
    )


@app.post("/stop")
def stop():
    tts_engine.stop_audio()
    return {"status": "stopped"}


@app.get("/status")
def status():
    cfg = cfg_module.get_config()
    return {
        "status":        "loading" if tts_engine.is_loading() else "ready",
        "engine":        cfg.get("engine"),
        "voice":         cfg.get("voice"),
        "speed":         cfg.get("speed"),
        "always_save":   cfg.get("always_save"),
        "save_dir":      cfg.get("save_dir"),
        # API keys are never echoed — only a presence flag, mirroring _public_config().
        "openai_api_key":     bool(cfg.get("openai_api_key")),
        "elevenlabs_api_key": bool(cfg.get("elevenlabs_api_key")),
        "model_ready":   not tts_engine.is_first_run(),
        "load_error":    tts_engine.get_load_error(),
        "max_text_chars": MAX_TEXT_CHARS,
        "version":       "1.0.0",
    }


@app.get("/voices")
def voices():
    return {"voices": tts_engine.list_voices_labeled()}


@app.patch("/config")
def update_config(update: ConfigUpdate):
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    cfg_module.set_config(updates)
    # Never echo provider API keys back in an HTTP response. The client
    # just sent them; it does not need them returned, and logs or XSS
    # elsewhere in the browser could surface the response body.
    return {"status": "updated", "config": _public_config(cfg_module.get_config())}


# ── Engine fallbacks ──────────────────────────────────────────────────────────

def _speak_openai(req: SpeakRequest, cfg: dict) -> dict:
    try:
        import openai

        client   = openai.OpenAI(api_key=cfg["openai_api_key"])
        response = client.audio.speech.create(
            model           = "tts-1",
            voice           = req.voice or "alloy",
            input           = req.text,
            speed           = req.speed or 1.0,
            response_format = "wav",   # WAV decodes reliably via soundfile
        )
        data, sr = tts_engine.read_audio(response.content)
        tts_engine.play_audio(data, sr)
        result = {"status": "playing", "engine": "openai"}
        if req.save or cfg.get("always_save", False):
            result["saved_to"] = tts_engine.save_wav(data, sr)
        return result
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _speak_elevenlabs(req: SpeakRequest, cfg: dict) -> dict:
    try:
        import requests

        vid     = req.voice or "21m00Tcm4TlvDq8ikWAM"   # Rachel default
        url     = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/stream"
        headers = {
            "xi-api-key":    cfg["elevenlabs_api_key"],
            "Content-Type":  "application/json",
        }
        r    = requests.post(
            url,
            json    = {"text": req.text, "model_id": "eleven_monolingual_v1"},
            headers = headers,
            timeout = 30,
        )
        if not r.ok:
            # ElevenLabs returns a JSON error body on failure; surface it
            # instead of letting soundfile choke on non-audio bytes.
            return {"status": "error", "message": f"ElevenLabs API {r.status_code}: {r.text[:200]}"}

        # This endpoint streams MP3 by default and offers no WAV option (unlike
        # the OpenAI path's response_format="wav"), so decoding relies on a
        # soundfile/libsndfile build with MPEG support (libsndfile >= 1.1).
        data, sr = tts_engine.read_audio(r.content)
        tts_engine.play_audio(data, sr)
        result = {"status": "playing", "engine": "elevenlabs"}
        if req.save or cfg.get("always_save", False):
            result["saved_to"] = tts_engine.save_wav(data, sr)
        return result
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
