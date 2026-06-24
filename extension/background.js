// background.js — ReadOut browser extension service worker
// Registers context menus and sends requests to the local ReadOut server.

const READOUT_URL = "http://localhost:7778";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "readout-speak",
    title: "Read aloud",
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "readout-speak-save",
    title: "Read aloud & save WAV",
    contexts: ["selection"],
  });
  chrome.contextMenus.create({
    id: "readout-stop",
    title: "Stop reading",
    contexts: ["all"],
  });
});

// Inject content script on demand if it isn't already loaded
async function ensureContentScript(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, { type: "readout-ping" });
  } catch {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"],
    });
  }
}

async function showToast(tabId, text, error = false) {
  try {
    await ensureContentScript(tabId);
    await chrome.tabs.sendMessage(tabId, { type: "readout-toast", text, error });
  } catch {
    // Tab doesn't support scripting (chrome://, edge://, etc.) — silent fail
  }
}

async function handleContextMenuClick(info, tab = {}) {
  if (info.menuItemId === "readout-stop") {
    await fetch(`${READOUT_URL}/stop`, { method: "POST" }).catch(() => {});
    await showToast(tab.id, "Stopped.");
    return;
  }

  const text = info.selectionText;
  if (!text) return;

  const save = info.menuItemId === "readout-speak-save";

  try {
    const res = await fetch(`${READOUT_URL}/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, save }),
    });

    if (!res.ok) throw new Error("Service error");

    await showToast(tab.id, save ? "Reading & saving..." : "Reading aloud...");
  } catch {
    await showToast(tab.id, "ReadOut not running. Start the desktop app.", true);
  }
}

chrome.contextMenus.onClicked.addListener(handleContextMenuClick);
