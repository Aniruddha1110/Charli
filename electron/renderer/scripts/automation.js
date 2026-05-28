// automation.js — Automation panel UI logic

let currentVolume  = 50;
let isMuted        = false;
let screenshotData = null;


async function initAutomation() {
  await loadVolumeState();
  await loadClipboard();
  await loadKnownApps();
  lucide.createIcons();
}


// ── Apps ───────────────────────────────────────────────────────────────────

async function loadKnownApps() {
  const data      = await api.getApps();
  const container = document.getElementById("auto-apps-list");
  if (!container) return;

  // Show first 20 popular apps as quick buttons
  const popular = [
    "chrome", "vs code", "spotify", "notepad", "explorer",
    "calculator", "cmd", "powershell", "discord", "whatsapp",
    "telegram", "zoom", "word", "excel", "edge",
  ];

  container.innerHTML = popular.map(app => `
    <button class="auto-app-btn" onclick="launchApp('${app}')">
      ${appIcon(app)}
      <span>${app}</span>
    </button>
  `).join("");
}

async function launchApp(name) {
  const input = document.getElementById("auto-app-input");
  const appName = name || (input ? input.value.trim() : "");
  if (!appName) return;

  showAutoStatus(`Opening ${appName}...`, "info");

  const result = await api.openApp(appName);
  if (result.success) {
    showAutoStatus(`✓ Opened ${appName}`, "success");
    if (input) input.value = "";
  } else {
    showAutoStatus(`✗ Could not open ${appName}: ${result.error}`, "error");
  }
}


// ── Type text ──────────────────────────────────────────────────────────────

async function autoTypeText() {
  const input = document.getElementById("auto-type-input");
  const text  = input.value.trim();
  if (!text) return;

  showAutoStatus("Click your target window — typing in 1 second...", "info");

  const result = await api.typeText(text);
  if (result.success) {
    showAutoStatus(`✓ Typed ${text.length} characters`, "success");
    input.value = "";
  } else {
    showAutoStatus(`✗ Type failed: ${result.error}`, "error");
  }
}

async function autoPressKey() {
  const input = document.getElementById("auto-key-input");
  const key   = input.value.trim();
  if (!key) return;

  const result = await api.pressKey(key);
  if (result.success) {
    showAutoStatus(`✓ Pressed: ${key}`, "success");
    input.value = "";
  } else {
    showAutoStatus(`✗ Key press failed: ${result.error}`, "error");
  }
}


// ── Screenshot ─────────────────────────────────────────────────────────────

async function captureScreen() {
  showAutoStatus("Taking screenshot...", "info");
  const result = await api.takeScreenshot(false);

  if (result.success) {
    screenshotData = result.image;
    const preview  = document.getElementById("auto-screenshot-preview");
    const img      = document.getElementById("auto-screenshot-img");
    img.src        = `data:image/png;base64,${result.image}`;
    preview.classList.remove("hidden");
    showAutoStatus(
      `✓ Screenshot taken (${result.width}×${result.height})`, "success"
    );
  } else {
    showAutoStatus(`✗ Screenshot failed: ${result.error}`, "error");
  }
}

async function saveScreen() {
  const result = await api.takeScreenshot(true);
  if (result.success) {
    showAutoStatus(`✓ Saved to: ${result.path}`, "success");
  } else {
    showAutoStatus(`✗ Save failed: ${result.error}`, "error");
  }
}

function downloadScreenshot() {
  if (!screenshotData) return;
  const link    = document.createElement("a");
  link.href     = `data:image/png;base64,${screenshotData}`;
  link.download = `screenshot_${Date.now()}.png`;
  link.click();
}


// ── Volume ─────────────────────────────────────────────────────────────────

async function loadVolumeState() {
  const data = await api.getVolume();
  if (data.success) {
    currentVolume = data.volume;
    isMuted       = data.muted;
    updateVolumeUI();
  }
}

function updateVolumeUI() {
  const slider = document.getElementById("auto-volume-slider");
  const label  = document.getElementById("auto-volume-label");
  const muteBtn = document.getElementById("auto-mute-btn");

  if (slider) slider.value = currentVolume;
  if (label)  label.textContent = isMuted ? "Muted" : `${currentVolume}%`;
  if (muteBtn) {
    muteBtn.innerHTML = isMuted
      ? `<i data-lucide="volume-x" width="16" height="16"></i>`
      : `<i data-lucide="volume-2" width="16" height="16"></i>`;
    muteBtn.classList.toggle("active", isMuted);
    lucide.createIcons();
  }
}

async function changeVolume(val) {
  currentVolume = parseInt(val);
  document.getElementById("auto-volume-label").textContent = `${currentVolume}%`;
  await api.setVolume(currentVolume);
}

async function toggleMute() {
  isMuted = !isMuted;
  await api.muteVolume(isMuted);
  updateVolumeUI();
  showAutoStatus(isMuted ? "Muted" : "Unmuted", "info");
}

async function setVolumeLevel(level) {
  currentVolume = level;
  await api.setVolume(level);
  updateVolumeUI();
  showAutoStatus(`Volume set to ${level}%`, "success");
}


// ── Clipboard ──────────────────────────────────────────────────────────────

async function loadClipboard() {
  const data = await api.getClipboard();
  const el   = document.getElementById("auto-clipboard-content");
  if (el && data.success) {
    el.value = data.content || "";
  }
}

async function copyToClipboard() {
  const text = document.getElementById("auto-clipboard-content").value;
  if (!text) return;
  const result = await api.setClipboard(text);
  if (result.success) {
    showAutoStatus("✓ Copied to clipboard", "success");
  }
}

async function refreshClipboard() {
  await loadClipboard();
  showAutoStatus("✓ Clipboard refreshed", "success");
}


// ── Run command ────────────────────────────────────────────────────────────

async function executeCommand() {
  const input   = document.getElementById("auto-cmd-input");
  const output  = document.getElementById("auto-cmd-output");
  const command = input.value.trim();
  if (!command) return;

  output.textContent = `> ${command}\nRunning...`;
  output.classList.remove("hidden");

  const result = await api.runCommand(command);

  let text = `> ${command}\n`;
  if (result.stdout) text += result.stdout + "\n";
  if (result.stderr) text += `[stderr] ${result.stderr}\n`;
  text += `\n[exit code: ${result.return_code ?? (result.success ? 0 : 1)}]`;

  output.textContent = text;
  output.scrollTop   = output.scrollHeight;

  if (!result.success && result.error) {
    showAutoStatus(`✗ ${result.error}`, "error");
  }
}


// ── Helpers ────────────────────────────────────────────────────────────────

function showAutoStatus(msg, type = "info") {
  const el = document.getElementById("auto-status");
  if (!el) return;

  const colors = {
    info:    "var(--text-secondary)",
    success: "var(--green)",
    error:   "var(--red)",
  };

  el.textContent  = msg;
  el.style.color  = colors[type] || colors.info;
  el.classList.remove("hidden");

  clearTimeout(el._timeout);
  if (type !== "error") {
    el._timeout = setTimeout(() => el.classList.add("hidden"), 3000);
  }
}

function appIcon(name) {
  const icons = {
    "chrome":      "chrome",
    "vs code":     "code-2",
    "vscode":      "code-2",
    "spotify":     "music",
    "notepad":     "file-text",
    "explorer":    "folder-open",
    "calculator":  "calculator",
    "cmd":         "terminal",
    "powershell":  "terminal",
    "discord":     "message-circle",
    "whatsapp":    "message-circle",
    "telegram":    "send",
    "zoom":        "video",
    "word":        "file-text",
    "excel":       "file-spreadsheet",
    "edge":        "globe",
  };
  const icon = icons[name] || "app-window";
  return `<i data-lucide="${icon}" width="18" height="18"></i>`;
}