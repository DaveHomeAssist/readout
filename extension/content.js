// content.js — ReadOut toast notification overlay
// Injected on all pages. Shows a brief toast when the extension triggers playback.

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  // Respond to pings so background.js knows we're loaded
  if (msg.type === "readout-ping") {
    sendResponse({ ok: true });
    return;
  }

  if (msg.type !== "readout-toast") return;

  const existing = document.getElementById("readout-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "readout-toast";
  toast.textContent = msg.text;
  Object.assign(toast.style, {
    position: "fixed",
    bottom: "24px",
    right: "24px",
    background: msg.error ? "#ff5252" : "#b8f542",
    color: "#000",
    padding: "10px 18px",
    borderRadius: "6px",
    fontFamily: "monospace",
    fontSize: "13px",
    fontWeight: "600",
    zIndex: "2147483647",
    boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
    transition: "opacity 0.3s",
    opacity: "1",
  });
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = "0"; }, 2000);
  setTimeout(() => toast.remove(), 2400);
});