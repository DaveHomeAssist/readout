// popup.js — ReadOut extension popup controller

const READOUT_URL = "http://localhost:7778";

// Offline fallback only; the authoritative source is `catalogue`, loaded from
// the server's /voices endpoint (engines = the server-side registry).
const VOICES = {
  kokoro: [
    "af_heart", "af_sky", "af_bella", "af_sarah", "af_nicole",
    "af_jessica", "af_nova", "af_river", "af_kore", "af_aoede",
    "am_adam", "am_echo", "am_michael", "am_fenrir",
    "bf_emma", "bf_isabella", "bm_george", "bm_lewis",
  ],
  openai: ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
  elevenlabs: ["Rachel", "Domi", "Bella", "Antoni", "Elli", "Josh", "Arnold", "Adam", "Sam"],
};

// Per-engine catalogue from /voices: { engine: [{id, label}, ...] }
const catalogue = {};

async function loadVoices() {
  try {
    const res = await fetch(`${READOUT_URL}/voices`, { signal: AbortSignal.timeout(2000) });
    const data = await res.json();
    if (Array.isArray(data.engines)) {
      for (const e of data.engines) {
        catalogue[e.name] = (e.voices || []).map((v) => ({ id: v.id, label: v.label || v.id }));
      }
    }
  } catch { /* keep fallback */ }
}

const els = {
  status: document.getElementById("status"),
  engine: document.getElementById("engine"),
  voice: document.getElementById("voice"),
  speed: document.getElementById("speed"),
  speedVal: document.getElementById("speed-val"),
  btnSpeak: document.getElementById("btn-speak"),
  btnStop: document.getElementById("btn-stop"),
};

// Populate voice dropdown for selected engine (catalogue first, fallback to VOICES)
function updateVoices(engine) {
  const cat = catalogue[engine];
  const list = cat && cat.length ? cat : (VOICES[engine] || []).map((v) => ({ id: v, label: v }));
  els.voice.innerHTML = list.map((v) => `<option value="${v.id}">${v.label}</option>`).join("");
}

// Check server status
async function checkStatus() {
  try {
    const res = await fetch(`${READOUT_URL}/status`, { signal: AbortSignal.timeout(2000) });
    const data = await res.json();
    els.status.textContent = data.status === "ready" ? "READY" : "LOADING";
    els.status.className = "status " + (data.status === "ready" ? "ready" : "loading");

    if (data.engine) els.engine.value = data.engine;
    if (data.voice) {
      updateVoices(data.engine || "kokoro");
      els.voice.value = data.voice;
    }
    if (data.speed) {
      els.speed.value = data.speed;
      els.speedVal.textContent = data.speed + "x";
    }
  } catch {
    els.status.textContent = "OFFLINE";
    els.status.className = "status offline";
  }
}

// Get selected text from the active tab
async function getSelectedText() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.getSelection().toString(),
  });
  return results?.[0]?.result || "";
}

// Speak selected text
els.btnSpeak.addEventListener("click", async () => {
  const text = await getSelectedText();
  if (!text) {
    els.btnSpeak.textContent = "No text selected";
    setTimeout(() => { els.btnSpeak.textContent = "Read Selection"; }, 1500);
    return;
  }

  try {
    els.btnSpeak.textContent = "Reading...";
    await fetch(`${READOUT_URL}/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        voice: els.voice.value,
        speed: parseFloat(els.speed.value),
      }),
    });
    els.btnSpeak.textContent = "Read Selection";
  } catch {
    els.btnSpeak.textContent = "Server offline";
    setTimeout(() => { els.btnSpeak.textContent = "Read Selection"; }, 1500);
  }
});

// Stop
els.btnStop.addEventListener("click", async () => {
  await fetch(`${READOUT_URL}/stop`, { method: "POST" }).catch(() => {});
});

// Engine change → update voices + save to server
els.engine.addEventListener("change", async () => {
  const engine = els.engine.value;
  updateVoices(engine);
  await fetch(`${READOUT_URL}/config`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ engine }),
  }).catch(() => {});
});

// Speed label
els.speed.addEventListener("input", () => {
  els.speedVal.textContent = parseFloat(els.speed.value).toFixed(1) + "x";
});

// ── View tab switching ──
const tabPlayer = document.getElementById("tab-player");
const tabGuide = document.getElementById("tab-guide");
const viewPlayer = document.getElementById("view-player");
const viewGuide = document.getElementById("view-guide");

tabPlayer.addEventListener("click", () => {
  viewPlayer.style.display = "";
  viewGuide.style.display = "none";
  tabPlayer.classList.add("active");
  tabGuide.classList.remove("active");
});

tabGuide.addEventListener("click", () => {
  viewPlayer.style.display = "none";
  viewGuide.style.display = "";
  tabGuide.classList.add("active");
  tabPlayer.classList.remove("active");
});

// Init
updateVoices("kokoro");
loadVoices().then(() => checkStatus());