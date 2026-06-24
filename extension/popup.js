// popup.js — ReadOut extension popup controller

const READOUT_URL = "http://localhost:7778";

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

const catalogue = {};

const els = {
  status: document.getElementById("status"),
  statusDetail: document.getElementById("status-detail"),
  engine: document.getElementById("engine"),
  voice: document.getElementById("voice"),
  speed: document.getElementById("speed"),
  speedVal: document.getElementById("speed-val"),
  btnSpeak: document.getElementById("btn-speak"),
  btnPreview: document.getElementById("btn-preview"),
  btnStop: document.getElementById("btn-stop"),
};

async function fetchWithTimeout(url, options = {}, timeoutMs = 2000) {
  const controller = new AbortController();
  let timer;
  try {
    return await Promise.race([
      fetch(url, { ...options, signal: controller.signal }),
      new Promise((_, reject) => {
        timer = setTimeout(() => {
          controller.abort();
          reject(new Error("Request timed out"));
        }, timeoutMs);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

async function loadVoices() {
  try {
    const res = await fetchWithTimeout(`${READOUT_URL}/voices`);
    if (!res.ok) throw new Error(`Voices ${res.status}`);
    const data = await res.json();
    if (Array.isArray(data.engines)) {
      for (const engine of data.engines) {
        catalogue[engine.name] = (engine.voices || []).map((voice) => ({
          id: voice.id,
          label: voice.label || voice.id,
        }));
      }
    }
  } catch {
    // Keep static offline fallback voices.
  }
}

function setStatus(state, label, detail) {
  els.status.textContent = label;
  els.status.className = "status " + state;
  els.statusDetail.textContent = detail;
  els.statusDetail.className = "status-detail " + state;
}

function setLastError(message, nextAction) {
  setStatus("error", "ERROR", `Last error: ${message} ${nextAction}`);
}

// Populate voice dropdown for selected engine
function updateVoices(engine) {
  const dynamicList = catalogue[engine];
  const list = dynamicList && dynamicList.length
    ? dynamicList
    : (VOICES[engine] || []).map((voice) => ({ id: voice, label: voice }));
  els.voice.innerHTML = list.map((voice) => `<option value="${voice.id}">${voice.label}</option>`).join("");
}

// Check server status
async function checkStatus() {
  try {
    const res = await fetchWithTimeout(`${READOUT_URL}/status`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    const dependencyIssue = (data.dependency_issues || [])[0];
    const state = dependencyIssue || data.load_error ? "error" : (data.status === "ready" ? "ready" : "loading");
    const label = dependencyIssue || data.load_error ? "ERROR" : (data.status === "ready" ? "READY" : "LOADING");
    const detail = dependencyIssue
      ? `Dependency issue: ${dependencyIssue.message} ${dependencyIssue.fix}`
      : data.load_error
        ? `Server connected, but model failed: ${data.load_error}`
        : data.status === "ready"
          ? `Server connected. Engine: ${data.engine || "unknown"} | Voice: ${data.voice || "unknown"} | Speed: ${data.speed || "1.0"}x`
          : "Server connected. Model is still loading; wait for READY before reading.";
    setStatus(state, label, detail);

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
    setStatus("offline", "OFFLINE", "Server offline. Start the ReadOut desktop app, then reopen this popup.");
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
    setLastError("No text selected.", "Select text on the page, then click Read Selection.");
    setTimeout(() => { els.btnSpeak.textContent = "Read Selection"; }, 1500);
    return;
  }

  try {
    els.btnSpeak.textContent = "Reading...";
    const res = await fetch(`${READOUT_URL}/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        voice: els.voice.value,
        speed: parseFloat(els.speed.value),
      }),
    });
    if (!res.ok) throw new Error(`Speak ${res.status}`);
    const data = await res.json();
    if (data.status === "error") {
      throw new Error(data.message || "ReadOut could not speak the selection.");
    }
    setStatus("ready", "READY", "Selection sent to ReadOut.");
    els.btnSpeak.textContent = "Read Selection";
  } catch (error) {
    const message = error?.message || "ReadOut did not accept the selection.";
    if (message.startsWith("Speak ") || message.includes("Failed to fetch")) {
      setStatus("offline", "OFFLINE", "ReadOut did not accept the selection. Start the desktop app and check the extension origin allowlist.");
    } else {
      setLastError(message, "Check the selected engine, API key, and ReadOut status.");
    }
    els.btnSpeak.textContent = "Server offline";
    setTimeout(() => { els.btnSpeak.textContent = "Read Selection"; }, 1500);
  }
});

// Preview selected voice
els.btnPreview.addEventListener("click", async () => {
  try {
    els.btnPreview.textContent = "Previewing...";
    const res = await fetch(`${READOUT_URL}/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        engine: els.engine.value,
        voice: els.voice.value,
        speed: parseFloat(els.speed.value),
      }),
    });
    if (!res.ok) throw new Error(`Preview ${res.status}`);
    const data = await res.json();
    if (data.status === "error") {
      throw new Error(data.message || "ReadOut could not preview this voice.");
    }
    setStatus("ready", "READY", `Previewing ${els.voice.value}.`);
  } catch (error) {
    const message = error?.message || "Could not preview voice.";
    if (message.startsWith("Preview ") || message.includes("Failed to fetch")) {
      setStatus("offline", "OFFLINE", "Could not preview voice. Start the desktop app and check the extension origin allowlist.");
    } else {
      setLastError(message, "Check the selected engine, API key, and ReadOut status.");
    }
  } finally {
    els.btnPreview.textContent = "Preview";
  }
});

async function stopPlayback() {
  try {
    const res = await fetch(`${READOUT_URL}/stop`, { method: "POST" });
    if (!res.ok) throw new Error(`Stop ${res.status}`);
    setStatus("ready", "READY", "Stop sent to ReadOut.");
  } catch {
    setStatus("offline", "OFFLINE", "Could not stop playback. Start the ReadOut desktop app, then try again.");
  }
}

// Stop
els.btnStop.addEventListener("click", () => {
  stopPlayback();
});

// Engine change → update voices + save to server
els.engine.addEventListener("change", async () => {
  const engine = els.engine.value;
  updateVoices(engine);
  try {
    const res = await fetch(`${READOUT_URL}/config`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engine, voice: els.voice.value }),
    });
    if (!res.ok) throw new Error(`Config ${res.status}`);
    setStatus("ready", "READY", `Engine saved: ${engine}.`);
  } catch {
    setLastError("Could not save engine.", "Check that ReadOut is running and this extension origin is allowed.");
  }
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
checkStatus();
setTimeout(() => checkStatus(), 250);
loadVoices().then(() => {
  updateVoices(els.engine.value || "kokoro");
  checkStatus();
});
