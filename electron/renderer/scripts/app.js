// app.js — Main frontend logic for Charli

// ── State ──────────────────────────────────────────────────────────────────
let conversationHistory = [];
let isWaiting           = false;
let isListening         = false;
let currentFilter       = "all";

// ── DOM refs ───────────────────────────────────────────────────────────────
const messagesEl   = document.getElementById("messages");
const inputEl      = document.getElementById("user-input");
const sendBtn      = document.getElementById("send-btn");
const statusDotEl  = document.getElementById("status-dot");
const statusTextEl = document.getElementById("status-text");
const modelLabelEl = document.getElementById("model-label");
const voiceBtn     = document.getElementById("voice-btn");

// ── Apply saved settings on startup ───────────────────────────────────────
(async () => {
  try {
    const s = await api.getSettings();
    if (s.theme) applyTheme(s.theme);

    if (s.bot_name) {
      // FIX 1: .app-logo does not exist — the element is <img class="app-logo-img">
      // You cannot set textContent on an <img>. Update the title text only.
      const titleEl = document.querySelector(".app-title");
      if (titleEl) titleEl.textContent = s.bot_name;
      document.title = s.bot_name;
    }

    if (s.user_name) window._userName = s.user_name.split(" ")[0];
    window._botName = s.bot_name || "Charli";
  } catch (err) {
    console.warn("[Charli] Failed to load settings:", err);
  }
})();


// ── Init ───────────────────────────────────────────────────────────────────
async function init() {
  checkBackendHealth();
  inputEl.focus();
  // Load chat history — this also loads the active chat messages
  await initChatHistory();
}

// ── Wake word handler ──────────────────────────────────────────────────────
if (window.charli && window.charli.onWakeWord) {
  window.charli.onWakeWord(() => {
    // Wake word detected — auto-click the mic button
    if (!isListening && !isWaiting) {
      // Show notification
      appendMessage(
        "assistant",
        `Wake word detected! Listening…`
      );
      // Trigger voice chat after short delay
      setTimeout(() => {
        voiceBtn.click();
      }, 500);
    }
  });
}


// ── Backend health check ───────────────────────────────────────────────────
async function checkBackendHealth() {
  for (let i = 0; i < 15; i++) {
    try {
      const data = await api.health();
      if (data.ollama_running) {
        setStatus("online", `Connected — ${data.current_model}`);
        modelLabelEl.textContent = data.current_model;
      } else {
        setStatus("warn", "Ollama not running — start Ollama first");
      }
      return;
    } catch {
      setStatus("offline", `Connecting… (attempt ${i + 1})`);
      await new Promise(r => setTimeout(r, 2000));
    }
  }
  setStatus("offline", "Backend offline — run python main.py");
}

function setStatus(state, text) {
  statusDotEl.className    = `status-dot ${state}`;
  statusTextEl.textContent = text;
}


// ── Send message ───────────────────────────────────────────────────────────
async function sendMessage() {
  if (isWaiting) return;

  const text = inputEl.value.trim();
  if (!text) return;

  appendMessage("user", text);
  inputEl.value = "";
  conversationHistory.push({ role: "user", content: text });

  isWaiting        = true;
  sendBtn.disabled = true;
  const typingId   = showTyping();

  try {
    // FIX 2: activeChatId comes from chat_history.js global scope.
    // Guard against it being undefined on first load.
    const chatId = (typeof activeChatId !== "undefined") ? activeChatId : null;

    const res = await fetch("http://127.0.0.1:8000/chat/", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        message:    text,
        chat_id:    chatId,
        use_memory: true,
      }),
    });

    const data = await res.json();
    removeTyping(typingId);
    appendMessage("assistant", data.reply);
    conversationHistory.push({ role: "assistant", content: data.reply });

    // Update active chat ID in case a new one was created by the backend
    if (data.chat_id && typeof activeChatId !== "undefined") {
      activeChatId = data.chat_id;
    }

    // Refresh sidebar after a delay (for auto-naming)
    setTimeout(loadChatHistory, 4000);

    // Keep history bounded to last 40 turns
    if (conversationHistory.length > 40) {
      conversationHistory = conversationHistory.slice(-40);
    }
  } catch (err) {
    removeTyping(typingId);
    appendMessage("error", `Connection error: ${err.message}`);
  }

  isWaiting        = false;
  sendBtn.disabled = false;
  inputEl.focus();
}


// ── Message rendering ──────────────────────────────────────────────────────
function appendMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = formatText(text);

  const time = document.createElement("span");
  time.className   = "timestamp";
  time.textContent = now();

  wrapper.appendChild(bubble);
  wrapper.appendChild(time);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  lucide.createIcons();
}

function formatText(text) {
  // Escape HTML first, then selectively re-allow our own formatting
  return text
    .replace(/```(\w+)?\n?([\s\S]*?)```/g,
      (_, lang, code) =>
        `<pre><code class="lang-${lang || ''}">${escHtml(code.trim())}</code></pre>`)
    .replace(/`([^`]+)`/g, (_, code) => `<code>${escHtml(code)}</code>`)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function showTyping() {
  const id      = "typing-" + Date.now();
  const wrapper = document.createElement("div");
  wrapper.className = "message assistant typing-wrapper";
  wrapper.id        = id;
  wrapper.innerHTML = `
    <div class="bubble typing">
      <span></span><span></span><span></span>
    </div>`;
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function now() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit", minute: "2-digit"
  });
}


// ── Input events ───────────────────────────────────────────────────────────
sendBtn.addEventListener("click", sendMessage);

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});


// ── Clear chat ─────────────────────────────────────────────────────────────
document.getElementById("clear-btn").addEventListener("click", async () => {
  const chatId = (typeof activeChatId !== "undefined") ? activeChatId : null;
  if (!chatId) return;

  try {
    await fetch(`http://127.0.0.1:8000/chats/${chatId}/messages`, {
      method: "DELETE",
    });
  } catch (err) {
    console.warn("[Charli] Could not clear messages on backend:", err);
  }

  messagesEl.innerHTML = "";
  conversationHistory  = [];

  // FIX 4: botName was declared but never used in the string — fixed now
  const botName = window._botName || "Charli";
  appendMessage("assistant", `Chat cleared. What can I help you with, ${window._userName || "there"}?`);
});


// ── Window controls ────────────────────────────────────────────────────────
document.getElementById("btn-minimize").onclick = () => window.charli?.minimize();
document.getElementById("btn-maximize").onclick = () => window.charli?.maximize();
document.getElementById("btn-close").onclick    = () => window.charli?.close();


// ── Voice button ───────────────────────────────────────────────────────────
voiceBtn.addEventListener("click", async () => {
  if (isWaiting || isListening) return;

  isListening = true;
  voiceBtn.classList.add("listening");
  voiceBtn.innerHTML = `<i data-lucide="ear" width="16" height="16"></i>`;
  lucide.createIcons();

  appendMessage("assistant", "Listening… speak now, I'll stop when you pause.");
  const typingId = showTyping();

  try {
    const res = await fetch("http://127.0.0.1:8000/voice/chat", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        history:    conversationHistory.slice(-20),
        use_intent: true,
      }),
    });

    const data = await res.json();
    removeTyping(typingId);

    // FIX 6: Use a dedicated function to render the voice message so we can
    // safely inject the SVG mic icon without passing raw HTML through
    // appendMessage (which would expose it to the formatText pipeline).
    if (data.heard) {
      appendVoiceMessage(data.heard);
      conversationHistory.push({ role: "user", content: data.heard });
    }

    // FIX 5: Backend may return null, not the string "none" — guard both
    const intent = data.intent;
    if (intent && intent !== "chat" && intent !== "none" && intent !== null) {
      appendIntentBadge(intent);
    }

    // Show screenshot inline if captured
    if (intent === "screenshot" && data.data?.image) {
      appendScreenshot(data.data.image);
    }

    // Always append the reply
    if (data.reply) {
      appendMessage("assistant", data.reply);
      conversationHistory.push({ role: "assistant", content: data.reply });
    }

  } catch (err) {
    removeTyping(typingId);
    appendMessage("error", `Voice error: ${err.message}`);
  }

  isListening = false;
  voiceBtn.classList.remove("listening");
  voiceBtn.innerHTML = `<i data-lucide="mic" width="16" height="16"></i>`;
  lucide.createIcons();
});


// ── Intent badge ───────────────────────────────────────────────────────────
function appendIntentBadge(intent) {
  const labels = {
    open_app:       "Opening app",
    screenshot:     "Screenshot",
    set_volume:     "Volume",
    volume_up:      "Volume up",
    volume_down:    "Volume down",
    mute:           "Mute",
    type_text:      "Typing",
    press_key:      "Key press",
    clipboard_read: "Clipboard",
    run_command:    "Terminal",
    search_web:     "Web search",
    search_files:   "File search",
    create_task:    "Task created",
    create_note:    "Note saved",
  };

  const icons = {
    open_app:       "app-window",
    screenshot:     "camera",
    set_volume:     "volume-2",
    volume_up:      "volume-2",
    volume_down:    "volume-1",
    mute:           "volume-x",
    type_text:      "keyboard",
    press_key:      "command",
    clipboard_read: "clipboard",
    run_command:    "terminal",
    search_web:     "search",
    search_files:   "folder-search",
    create_task:    "check-square",
    create_note:    "file-text",
  };

  const label = labels[intent] || intent;
  const icon  = icons[intent]  || "zap";

  const badge = document.createElement("div");
  badge.style.cssText = `
    display: inline-flex; align-items: center; gap: 5px;
    background: #1e3a8a22; border: 1px solid #1e3a8a44;
    color: var(--accent); border-radius: 6px;
    padding: 3px 10px; font-size: 11px; font-weight: 600;
    margin: 0 0 4px 0; align-self: flex-start;
  `;
  badge.innerHTML = `<i data-lucide="${icon}" width="11" height="11"></i> ${escHtml(label)}`;
  messagesEl.appendChild(badge);
  lucide.createIcons();
  scrollToBottom();
}


// ── Inline screenshot ──────────────────────────────────────────────────────
function appendScreenshot(base64img) {
  const wrapper = document.createElement("div");
  wrapper.style.cssText = "align-self:flex-start; max-width:75%; margin-bottom:4px;";

  const img     = document.createElement("img");
  img.src       = `data:image/png;base64,${base64img}`;
  img.style.cssText = `
    max-width: 100%; border-radius: 8px;
    border: 1px solid #2a2a2a; cursor: pointer;
  `;
  img.onclick = () => window.open(img.src, "_blank");
  img.title   = "Click to open full size";

  wrapper.appendChild(img);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
}


// ── Voice heard message (SVG mic icon + transcript text) ──────────────────
function appendVoiceMessage(text) {
  const wrapper = document.createElement("div");
  wrapper.className = "message user";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  // Build content with SVG mic icon — created via DOM, never via innerHTML,
  // so the user transcript text is always treated as plain text (no XSS risk)
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  icon.setAttribute("width", "13");
  icon.setAttribute("height", "13");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("fill", "none");
  icon.setAttribute("stroke", "currentColor");
  icon.setAttribute("stroke-width", "2");
  icon.setAttribute("stroke-linecap", "round");
  icon.setAttribute("stroke-linejoin", "round");
  icon.style.cssText = "display:inline-block; vertical-align:middle; margin-right:5px; flex-shrink:0; opacity:0.85;";

  // Mic SVG paths (matches Lucide "mic" icon exactly)
  const path1 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  path1.setAttribute("width", "8");
  path1.setAttribute("height", "14");
  path1.setAttribute("x", "8");
  path1.setAttribute("y", "1");
  path1.setAttribute("rx", "4");

  const path2 = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path2.setAttribute("d", "M4 11a8 8 0 0 0 16 0");

  const path3 = document.createElementNS("http://www.w3.org/2000/svg", "line");
  path3.setAttribute("x1", "12");
  path3.setAttribute("x2", "12");
  path3.setAttribute("y1", "19");
  path3.setAttribute("y2", "23");

  const path4 = document.createElementNS("http://www.w3.org/2000/svg", "line");
  path4.setAttribute("x1", "8");
  path4.setAttribute("x2", "16");
  path4.setAttribute("y1", "23");
  path4.setAttribute("y2", "23");

  icon.appendChild(path1);
  icon.appendChild(path2);
  icon.appendChild(path3);
  icon.appendChild(path4);

  // Text node — plain text, never innerHTML, so XSS-safe
  const textNode = document.createTextNode(text);

  bubble.style.cssText = "display:flex; align-items:center; flex-wrap:wrap;";
  bubble.appendChild(icon);
  bubble.appendChild(textNode);

  const time = document.createElement("span");
  time.className   = "timestamp";
  time.textContent = now();

  wrapper.appendChild(bubble);
  wrapper.appendChild(time);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
}


// ── Panel switching ────────────────────────────────────────────────────────
function showPanel(name, btn) {
  document.querySelectorAll(".chat-area").forEach(p => p.classList.add("hidden"));
  document.getElementById(`panel-${name}`)?.classList.remove("hidden");

  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  // Panel-specific init calls
  if (name === "tasks")      loadTasks();
  if (name === "notes")      loadNotes();
  if (name === "files")      initFileManager();
  if (name === "search")     lucide.createIcons();
  if (name === "calendar")   initCalendar();
  if (name === "settings")   initSettings();
  if (name === "automation") initAutomation();
  if (name === "reminders")  loadReminders();
  if (name === "code")       initCodePanel();

  // FIX 3: Use initTranslator() (idempotent via flag) instead of
  // reinitTranslator() which unnecessarily destroys and rebuilds the dropdowns
  // every time the panel is shown, causing a visible flicker.
  if (name === "translator") initTranslator();
}

function setFilter(filter, btn) {
  currentFilter = filter;
  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  loadTasks();
}

// ── Tray event handlers ────────────────────────────────────────────────────
if (window.charli) {
  // Tray → New Chat
  window.charli.onTrayNewChat && window.charli.onTrayNewChat(() => {
    startNewChat();
  });

  // Tray → Start Voice
  window.charli.onTrayStartVoice && window.charli.onTrayStartVoice(() => {
    showPanel("chat", document.querySelector("[onclick=\"showPanel('chat', this)\"]"));
    setTimeout(() => voiceBtn.click(), 300);
  });

  // Tray → Open Settings
  window.charli.onTrayOpenSettings && window.charli.onTrayOpenSettings(() => {
    const btn = document.querySelector("[onclick=\"showPanel('settings', this)\"]");
    showPanel("settings", btn);
  });

  // Wake word handler
  window.charli.onWakeWord && window.charli.onWakeWord(() => {
    if (!isListening && !isWaiting) {
      showPanel("chat", document.querySelector("[onclick=\"showPanel('chat', this)\"]"));
      appendMessage("assistant", "Wake word detected! Listening…");
      setTimeout(() => voiceBtn.click(), 500);
    }
  });
}

// ── Start ──────────────────────────────────────────────────────────────────
init();