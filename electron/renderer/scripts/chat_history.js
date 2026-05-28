// chat_history.js — Chat session sidebar logic

let activeChatId  = null;
let allChats      = [];
let renamingChatId = null;


// ── Load and render all chats ──────────────────────────────────────────────

async function loadChatHistory() {
  allChats = await api.getAllChats();
  renderChatHistory();
}

function renderChatHistory() {
  const container = document.getElementById("chat-history-list");
  if (!container) return;

  if (!allChats.length) {
    container.innerHTML = `
      <div style="font-size:11px; color:var(--text-muted);
                  padding:8px 10px;">No chats yet.</div>`;
    return;
  }

  container.innerHTML = allChats.map(chat => `
    <div class="chat-history-item ${chat.id === activeChatId ? 'active' : ''}"
         id="chat-item-${chat.id}"
         onclick="switchToChat(${chat.id})">

      <i data-lucide="message-circle" width="13" height="13"
         style="flex-shrink:0; color:var(--text-muted);"></i>

      <span class="chat-history-name"
            id="chat-name-${chat.id}"
            ondblclick="startRenameChat(${chat.id}, event)">
        ${escCHH(chat.name)}
      </span>

      <div class="chat-history-actions">
        <button onclick="startRenameChat(${chat.id}, event)" title="Rename"
          style="background:transparent; border:none; color:var(--text-muted);
                 cursor:pointer; padding:2px; border-radius:3px;">
          <i data-lucide="pencil" width="11" height="11"></i>
        </button>
        <button onclick="deleteChatItem(${chat.id}, event)" title="Delete"
          style="background:transparent; border:none; color:var(--text-muted);
                 cursor:pointer; padding:2px; border-radius:3px;">
          <i data-lucide="trash-2" width="11" height="11"></i>
        </button>
      </div>
    </div>
  `).join("");

  lucide.createIcons();
}


// ── Switch to a chat ───────────────────────────────────────────────────────

async function switchToChat(chatId) {
  if (chatId === activeChatId) return;

  // Activate in backend
  await api.activateChat(chatId);
  activeChatId = chatId;

  // Load messages
  await loadChatMessages(chatId);

  // Update sidebar highlight
  document.querySelectorAll(".chat-history-item").forEach(el => {
    el.classList.toggle("active", el.id === `chat-item-${chatId}`);
  });

  // Make sure chat panel is visible
  showPanel("chat", document.querySelector(".nav-btn.active"));
}

async function loadChatMessages(chatId) {
  const messages = await api.getChatMessages(chatId);

  // Clear current chat
  messagesEl.innerHTML = "";
  conversationHistory = [];

  if (!messages.length) {
    const botName = window._botName || "Charli";
    appendMessage("assistant",
      `Hey! I'm ${botName}. How can I help you today?`);
    return;
  }

  // Render all messages
  messages.forEach(msg => {
    if (msg.role === "user") {
      appendMessage("user", msg.content);
    } else if (msg.role === "assistant") {
      appendMessage("assistant", msg.content);
    }
    conversationHistory.push({
      role:    msg.role,
      content: msg.content,
    });
  });

  scrollToBottom();
}


// ── New chat ───────────────────────────────────────────────────────────────

async function startNewChat() {
  const chat   = await api.createNewChat();
  activeChatId = chat.id;

  // Clear messages UI
  messagesEl.innerHTML = "";
  conversationHistory  = [];

  const botName = window._botName || "Charli";
  appendMessage("assistant",
    `Hey! I'm ${botName}. What can I help you with?`);

  // Reload sidebar
  await loadChatHistory();

  // Make sure chat panel is shown
  document.querySelectorAll(".chat-area").forEach(p => p.classList.add("hidden"));
  document.getElementById("panel-chat").classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelector("[onclick=\"showPanel('chat', this)\"]")
    ?.classList.add("active");

  inputEl.focus();
}


// ── Rename chat ────────────────────────────────────────────────────────────

function startRenameChat(chatId, event) {
  event.stopPropagation();
  renamingChatId = chatId;

  const nameEl = document.getElementById(`chat-name-${chatId}`);
  if (!nameEl) return;

  const current = nameEl.textContent.trim();
  const input   = document.createElement("input");

  input.type      = "text";
  input.value     = current;
  input.className = "chat-rename-input";

  input.onblur = () => finishRenameChat(chatId, input.value);
  input.onkeydown = (e) => {
    if (e.key === "Enter")  { e.preventDefault(); input.blur(); }
    if (e.key === "Escape") { input.value = current; input.blur(); }
    e.stopPropagation();
  };

  nameEl.innerHTML = "";
  nameEl.appendChild(input);
  input.focus();
  input.select();
}

async function finishRenameChat(chatId, newName) {
  const name   = newName.trim() || "New Chat";
  await api.renameChat(chatId, name);

  // Update in local array
  const chat = allChats.find(c => c.id === chatId);
  if (chat) chat.name = name;

  renderChatHistory();
}


// ── Delete chat ────────────────────────────────────────────────────────────

async function deleteChatItem(chatId, event) {
  event.stopPropagation();

  if (!confirm("Delete this chat? This cannot be undone.")) return;

  await api.deleteChat(chatId);

  // If we deleted the active chat, start fresh
  if (chatId === activeChatId) {
    await startNewChat();
  } else {
    await loadChatHistory();
  }
}


// ── Init ───────────────────────────────────────────────────────────────────

async function initChatHistory() {
  // Get active chat from backend
  const active = await api.getActiveChat();
  activeChatId = active.id;

  // Load its messages
  await loadChatMessages(active.id);

  // Load sidebar
  await loadChatHistory();

  // Poll for auto-name updates every 3 seconds for the first 30s
  let polls = 0;
  const poll = setInterval(async () => {
    polls++;
    await loadChatHistory();
    if (polls >= 10) clearInterval(poll);
  }, 3000);
}


// ── Helper ─────────────────────────────────────────────────────────────────

function escCHH(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}