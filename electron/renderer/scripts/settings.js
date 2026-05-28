// settings.js — Settings panel logic

let currentSettings = {};

async function initSettings() {
  currentSettings = await api.getSettings();
  renderSettings();
  loadSystemInfo();
  loadMemoryFacts();
}


async function renderSettings() {
  const s = currentSettings;

  // ── Profile ──────────────────────────────────────────────────────────
  document.getElementById("set-name").value   = s.user_name   || "";
  document.getElementById("set-gender").value = s.user_gender || "";
  document.getElementById("set-bot-name").value = s.bot_name || "Charli";

  if (s.user_photo) {
    document.getElementById("set-photo-preview").src = s.user_photo;
    document.getElementById("set-photo-preview").classList.remove("hidden");
    document.getElementById("set-photo-placeholder").classList.add("hidden");
    document.getElementById("set-photo-delete").classList.remove("hidden");
  }

  // ── Theme ────────────────────────────────────────────────────────────
  const theme = s.theme || "dark";
  document.querySelectorAll(".theme-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.theme === theme);
  });
  applyTheme(theme);

  // ── AI Model ─────────────────────────────────────────────────────────
  const modelsData = await api.getAvailableModels();
  const modelSelect = document.getElementById("set-model");
  modelSelect.innerHTML = modelsData.models.map(m =>
    `<option value="${m}" ${m === s.llm_model ? 'selected' : ''}>${m}</option>`
  ).join("");

  // ── Voice speed ───────────────────────────────────────────────────────
  const rate = parseInt(s.tts_rate || "175");
  document.getElementById("set-voice-rate").value = rate;
  document.getElementById("set-voice-rate-label").textContent = `${rate} wpm`;

  // ── Wake word ─────────────────────────────────────────────────────────
  document.getElementById("set-wake-word").value = s.wake_word || "hey charli";
  document.getElementById("set-wake-enabled").checked =
    s.wake_word_enabled === "true";

  // ── Startup ───────────────────────────────────────────────────────────
  document.getElementById("set-startup").checked = s.startup === "true";

  // ── Wake word threshold ────────────────────────────────────────────────
  const threshold = parseFloat(s.wake_word_threshold || "0.5");
  const threshEl  = document.getElementById("set-wake-threshold");
  const threshLbl = document.getElementById("set-wake-threshold-label");
  if (threshEl)  threshEl.value       = threshold;
  if (threshLbl) threshLbl.textContent = threshold.toFixed(2);
}

async function saveBotName() {
  const name = document.getElementById("set-bot-name").value.trim() || "Charli";
  await saveSetting("bot_name", name);

  // Update title bar instantly
  document.querySelector(".app-title").textContent = name;
  document.title = name;

  // Update logo letter
  document.querySelector(".app-logo").textContent = name[0].toUpperCase();
}

// ── Theme ──────────────────────────────────────────────────────────────────

function setTheme(theme, btn) {
  document.querySelectorAll(".theme-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  applyTheme(theme);
  saveSetting("theme", theme);
}

function applyTheme(theme) {
  const root = document.documentElement;

  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    theme = prefersDark ? "dark" : "light";
  }

  if (theme === "light") {
    root.style.setProperty("--bg-app",        "#f8f9fa");
    root.style.setProperty("--bg-sidebar",    "#f0f0f0");
    root.style.setProperty("--bg-chat",       "#ffffff");
    root.style.setProperty("--bg-input",      "#f0f0f0");
    root.style.setProperty("--bg-bubble-ai",  "#f0f0f0");
    root.style.setProperty("--bg-bubble-usr", "#2563eb");
    root.style.setProperty("--bg-titlebar",   "#e8e8e8");
    root.style.setProperty("--text-primary",  "#111111");
    root.style.setProperty("--text-secondary","#555555");
    root.style.setProperty("--text-muted",    "#999999");
  } else {
    root.style.setProperty("--bg-app",        "#0f0f0f");
    root.style.setProperty("--bg-sidebar",    "#161616");
    root.style.setProperty("--bg-chat",       "#111111");
    root.style.setProperty("--bg-input",      "#1a1a1a");
    root.style.setProperty("--bg-bubble-ai",  "#1e1e1e");
    root.style.setProperty("--bg-bubble-usr", "#2563eb");
    root.style.setProperty("--bg-titlebar",   "#0a0a0a");
    root.style.setProperty("--text-primary",  "#f0f0f0");
    root.style.setProperty("--text-secondary","#9ca3af");
    root.style.setProperty("--text-muted",    "#4b5563");
  }
}

// Listen for system theme changes
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (currentSettings.theme === "system") applyTheme("system");
});


// ── Save helpers ───────────────────────────────────────────────────────────

async function saveSetting(key, value) {
  await api.updateSetting(key, String(value));
  currentSettings[key] = String(value);
  showSettingSaved();
}

function showSettingSaved() {
  const el = document.getElementById("settings-saved");
  if (!el) return;
  el.classList.remove("hidden");
  clearTimeout(el._timeout);
  el._timeout = setTimeout(() => el.classList.add("hidden"), 2000);
}


// ── Profile ────────────────────────────────────────────────────────────────

async function saveProfile() {
  const name   = document.getElementById("set-name").value.trim();
  const gender = document.getElementById("set-gender").value;
  await api.updateProfile(name, gender);
  showSettingSaved();
}

function triggerPhotoUpload() {
  document.getElementById("set-photo-input").click();
}

async function handlePhotoUpload(input) {
  const file = input.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64 = e.target.result;
    document.getElementById("set-photo-preview").src = base64;
    document.getElementById("set-photo-preview").classList.remove("hidden");
    document.getElementById("set-photo-placeholder").classList.add("hidden");
    document.getElementById("set-photo-delete").classList.remove("hidden");
    await api.updateProfile(null, null, base64);
    showSettingSaved();
  };
  reader.readAsDataURL(file);
}

async function removePhoto() {
  document.getElementById("set-photo-preview").src = "";
  document.getElementById("set-photo-preview").classList.add("hidden");
  document.getElementById("set-photo-placeholder").classList.remove("hidden");
  document.getElementById("set-photo-delete").classList.add("hidden");
  document.getElementById("set-photo-input").value = "";
  await api.updateProfile(null, null, "");
  showSettingSaved();
}


// ── Voice speed ────────────────────────────────────────────────────────────

function updateVoiceRate(val) {
  document.getElementById("set-voice-rate-label").textContent = `${val} wpm`;
}

async function saveVoiceRate() {
  const val = document.getElementById("set-voice-rate").value;
  await saveSetting("tts_rate", val);
}


// ── Model ──────────────────────────────────────────────────────────────────

async function saveModel() {
  const val = document.getElementById("set-model").value;
  await saveSetting("llm_model", val);
}


// ── Wake word ──────────────────────────────────────────────────────────────

async function saveWakeWord() {
  const word      = document.getElementById("set-wake-word").value.trim();
  const enabled   = document.getElementById("set-wake-enabled").checked;
  const threshold = 0.5;

  await saveSetting("wake_word",         word    || "hey charli");
  await saveSetting("wake_word_enabled", String(enabled));
  await saveSetting("wake_word_threshold", String(threshold));

  // Tell Electron to start/stop wake word
  if (window.charli) {
    if (enabled) {
      window.charli.startWakeWord(threshold);
      showSettingSaved();
    } else {
      window.charli.stopWakeWord();
      showSettingSaved();
    }
  }
}


// ── Startup ────────────────────────────────────────────────────────────────

async function toggleStartup(checkbox) {
  await saveSetting("startup", String(checkbox.checked));
  // Tell Electron main process to set/unset login item
  if (window.charli && window.charli.setStartup) {
    window.charli.setStartup(checkbox.checked);
  }
}

// ── Memory ────────────────────────────────────────────────────────────────

async function loadMemoryFacts() {
  const container = document.getElementById("memory-facts-list");
  if (!container) return;

  container.innerHTML = `<div class="empty-state" style="margin-top:8px;">
    Loading...</div>`;

  const data  = await api.getMemoryFacts();
  const facts = data.facts || [];

  if (!facts.length) {
    container.innerHTML = `<div class="empty-state" style="margin-top:8px;">
      No memories yet. Start chatting and Charli will learn about you.</div>`;
    return;
  }

  // Group by category
  const grouped = {};
  facts.forEach(f => {
    if (!grouped[f.category]) grouped[f.category] = [];
    grouped[f.category].push(f);
  });

  const catColors = {
    personal:   "#3b82f6",
    work:       "#22c55e",
    preference: "#f59e0b",
    project:    "#a855f7",
  };

  let html = "";
  for (const [cat, items] of Object.entries(grouped)) {
    const color = catColors[cat] || "var(--accent)";
    html += `
      <div style="margin-bottom:8px;">
        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.8px;
                    color:${color}; font-weight:600; margin-bottom:4px;">
          ${cat}
        </div>
        ${items.map(f => `
          <div style="display:flex; align-items:center; gap:8px;
                      background:var(--bg-input); border:1px solid #2a2a2a;
                      border-radius:6px; padding:7px 10px; margin-bottom:4px;">
            <span style="flex:1; font-size:12px; color:var(--text-primary);">
              ${escMemHtml(f.fact)}
            </span>
            <button onclick="deleteMemoryFact(${f.id})"
              style="background:transparent; border:none; color:var(--text-muted);
                     cursor:pointer; padding:2px; border-radius:3px; flex-shrink:0;"
              onmouseover="this.style.color='var(--red)'"
              onmouseout="this.style.color='var(--text-muted)'">
              <i data-lucide="x" width="12" height="12"></i>
            </button>
          </div>
        `).join("")}
      </div>`;
  }

  container.innerHTML = html;
  lucide.createIcons();
}

async function deleteMemoryFact(id) {
  await api.deleteMemoryFact(id);
  await loadMemoryFacts();
  showSettingSaved();
}

async function clearAllMemory() {
  if (!confirm("Clear all of Charli's memories about you? This cannot be undone.")) return;
  await api.clearAllMemory();
  await loadMemoryFacts();
  showSettingSaved();
}

async function clearChatHistory() {
  if (!confirm("Clear all conversation history? Charli won't remember past chats.")) return;
  await api.clearChatHistory();
  showSettingSaved();
}

function escMemHtml(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}


// ── System info ────────────────────────────────────────────────────────────

async function loadSystemInfo() {
  const info = await api.getSystemInfo();
  const el   = document.getElementById("set-system-info");
  if (!el) return;

  el.innerHTML = `
    <div class="about-grid">
      <div class="about-item">
        <span class="about-label">Charli Version</span>
        <span class="about-value">v${info.app_version}</span>
      </div>
      <div class="about-item">
        <span class="about-label">Platform</span>
        <span class="about-value">${info.platform}</span>
      </div>
      <div class="about-item">
        <span class="about-label">Python</span>
        <span class="about-value">${info.python_version}</span>
      </div>
      <div class="about-item">
        <span class="about-label">CPU Usage</span>
        <span class="about-value">${info.cpu_usage || "—"}</span>
      </div>
      <div class="about-item">
        <span class="about-label">RAM</span>
        <span class="about-value">${info.ram_used || "—"} / ${info.ram_total || "—"}</span>
      </div>
      <div class="about-item">
        <span class="about-label">Disk Free</span>
        <span class="about-value">${info.disk_free || "—"}</span>
      </div>
    </div>`;
}