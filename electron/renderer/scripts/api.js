// api.js — All FastAPI calls for Charli

const API_BASE = "http://127.0.0.1:8000";

const api = {

  // ── Health ─────────────────────────────────────────────────────────────
  async health() {
    const res = await fetch(`${API_BASE}/chat/health`);
    return res.json();
  },

  // ── Chat ───────────────────────────────────────────────────────────────
  async chat(message, history = []) {
    const res = await fetch(`${API_BASE}/chat/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ message, history }),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Chat API error ${res.status}: ${err}`);
    }
    return res.json();
  },

  // ── Tasks ──────────────────────────────────────────────────────────────
  async getTasks(status = null) {
    const url = status
      ? `${API_BASE}/tasks/?status=${status}`
      : `${API_BASE}/tasks/`;
    const res = await fetch(url);
    return res.json();
  },

  async createTask(title, description = "", priority = "normal", due_date = null) {
    const res = await fetch(`${API_BASE}/tasks/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ title, description, priority, due_date }),
    });
    return res.json();
  },

  async completeTask(id) {
    const res = await fetch(`${API_BASE}/tasks/${id}/complete`, { method: "PATCH" });
    return res.json();
  },

  async deleteTask(id) {
    const res = await fetch(`${API_BASE}/tasks/${id}`, { method: "DELETE" });
    return res.json();
  },

  // ── Notes ──────────────────────────────────────────────────────────────
  async getNotes() {
    const res = await fetch(`${API_BASE}/notes/`);
    return res.json();
  },

  async createNote(content, title = "", tags = "") {
    const res = await fetch(`${API_BASE}/notes/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ content, title, tags }),
    });
    return res.json();
  },

  async deleteNote(id) {
    const res = await fetch(`${API_BASE}/notes/${id}`, { method: "DELETE" });
    return res.json();
  },

  // ── Files ─────────────────────────────────────────────────────────────
  async searchFiles(query, max_results = 20) {
    const res = await fetch(
      `${API_BASE}/files/search?q=${encodeURIComponent(query)}&max_results=${max_results}`
    );
    return res.json();
  },

  async listDirectory(path) {
    const res = await fetch(
      `${API_BASE}/files/list?path=${encodeURIComponent(path)}`
    );
    return res.json();
  },

  async openFile(path) {
    const res = await fetch(`${API_BASE}/files/open`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ path }),
    });
    return res.json();
  },

  async renameFile(path, new_name) {
    const res = await fetch(`${API_BASE}/files/rename`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ path, new_name }),
    });
    return res.json();
  },

  async moveFile(path, destination) {
    const res = await fetch(`${API_BASE}/files/move`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ path, destination }),
    });
    return res.json();
  },

  async deleteFile(path, trash = true) {
    const res = await fetch(`${API_BASE}/files/delete`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ path, trash }),
    });
    return res.json();
  },

  async getQuickFolders() {
    const res = await fetch(`${API_BASE}/files/quick`);
    return res.json();
  },

  // ── Search ────────────────────────────────────────────────────────────
  async search(query, max_results = 5, summarise = true) {
    const res = await fetch(`${API_BASE}/search/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ query, max_results, summarise }),
    });
    return res.json();
  },

  async searchNews(query, max_results = 5) {
    const res = await fetch(
      `${API_BASE}/search/news?q=${encodeURIComponent(query)}&max_results=${max_results}`
    );
    return res.json();
  },

  // ── Calendar ──────────────────────────────────────────────────────────
  async getMonthEvents(year, month) {
    const res = await fetch(
      `${API_BASE}/calendar/month?year=${year}&month=${month}`
    );
    return res.json();
  },

  async getDayEvents(date) {
    const res = await fetch(
      `${API_BASE}/calendar/day?date=${date}`
    );
    return res.json();
  },

  async getUpcomingEvents(limit = 5) {
    const res = await fetch(`${API_BASE}/calendar/upcoming?limit=${limit}`);
    return res.json();
  },

  async createEvent(title, start_time, end_time = null,
                    description = "", location = "") {
    const res = await fetch(`${API_BASE}/calendar/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        title, start_time, end_time, description, location
      }),
    });
    return res.json();
  },

  async deleteEvent(id) {
    const res = await fetch(`${API_BASE}/calendar/${id}`, {
      method: "DELETE"
    });
    return res.json();
  },

  // ── Settings ──────────────────────────────────────────────────────────
  async getSettings() {
    const res = await fetch(`${API_BASE}/settings/`);
    return res.json();
  },

  async updateSetting(key, value) {
    const res = await fetch(`${API_BASE}/settings/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ key, value }),
    });
    return res.json();
  },

  async updateProfile(name, gender, photo = null) {
    const res = await fetch(`${API_BASE}/settings/profile`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name, gender, photo }),
    });
    return res.json();
  },

  async getAvailableModels() {
    const res = await fetch(`${API_BASE}/settings/models`);
    return res.json();
  },

  async getSystemInfo() {
    const res = await fetch(`${API_BASE}/settings/system`);
    return res.json();
  },

  // ── Automation ────────────────────────────────────────────────────────
  async getApps() {
    const res = await fetch(`${API_BASE}/automation/apps`);
    return res.json();
  },

  async openApp(app_name) {
    const res = await fetch(`${API_BASE}/automation/open`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ app_name }),
    });
    return res.json();
  },

  async typeText(text, delay = 0.05) {
    const res = await fetch(`${API_BASE}/automation/type`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text, delay }),
    });
    return res.json();
  },

  async pressKey(key) {
    const res = await fetch(`${API_BASE}/automation/key`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ key }),
    });
    return res.json();
  },

  async takeScreenshot(save = false, path = null) {
    const res = await fetch(`${API_BASE}/automation/screenshot`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ save, path }),
    });
    return res.json();
  },

  async getVolume() {
    const res = await fetch(`${API_BASE}/automation/volume`);
    return res.json();
  },

  async setVolume(level) {
    const res = await fetch(`${API_BASE}/automation/volume`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ level }),
    });
    return res.json();
  },

  async muteVolume(mute) {
    const res = await fetch(`${API_BASE}/automation/volume/mute`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ mute }),
    });
    return res.json();
  },

  async getClipboard() {
    const res = await fetch(`${API_BASE}/automation/clipboard`);
    return res.json();
  },

  async setClipboard(text) {
    const res = await fetch(`${API_BASE}/automation/clipboard`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text }),
    });
    return res.json();
  },

  async runCommand(command, timeout = 30) {
    const res = await fetch(`${API_BASE}/automation/command`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ command, timeout }),
    });
    return res.json();
  },

  async getProcesses(filter = "") {
    const res = await fetch(
      `${API_BASE}/automation/processes?filter=${encodeURIComponent(filter)}`
    );
    return res.json();
  },

  // ── Memory ────────────────────────────────────────────────────────────
  async getMemoryFacts() {
    const res = await fetch(`${API_BASE}/memory/facts`);
    return res.json();
  },

  async deleteMemoryFact(id) {
    const res = await fetch(`${API_BASE}/memory/facts/${id}`, {
      method: "DELETE"
    });
    return res.json();
  },

  async clearAllMemory() {
    const res = await fetch(`${API_BASE}/memory/facts`, {
      method: "DELETE"
    });
    return res.json();
  },

  async clearChatHistory(session_id = "default") {
    const res = await fetch(
      `${API_BASE}/chat/memory?session_id=${session_id}`,
      { method: "DELETE" }
    );
    return res.json();
  },

  // ── Reminders ─────────────────────────────────────────────────────────
  async getReminders(include_sent = false) {
    const res = await fetch(
      `${API_BASE}/reminders/?include_sent=${include_sent}`
    );
    return res.json();
  },

  async createReminder(title, remind_at, notes = "") {
    const res = await fetch(`${API_BASE}/reminders/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ title, remind_at, notes }),
    });
    return res.json();
  },

  async createNaturalReminder(text) {
    const res = await fetch(`${API_BASE}/reminders/natural`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text }),
    });
    return res.json();
  },

  async deleteReminder(id) {
    const res = await fetch(`${API_BASE}/reminders/${id}`, {
      method: "DELETE"
    });
    return res.json();
  },

  async codeAssistant(action, code = "", prompt = "", language = "python") {
    const res = await fetch(`${API_BASE}/code/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ action, code, prompt, language }),
    });
    return res.json();
  },

  async getLanguages() {
    const res = await fetch(`${API_BASE}/code/languages`);
    return res.json();
  },

  // ── Chat Sessions ─────────────────────────────────────────────────────
  async getAllChats() {
    const res = await fetch(`${API_BASE}/chats/`);
    return res.json();
  },

  async createNewChat() {
    const res = await fetch(`${API_BASE}/chats/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name: "New Chat" }),
    });
    return res.json();
  },

  async getActiveChat() {
    const res = await fetch(`${API_BASE}/chats/active`);
    return res.json();
  },

  async activateChat(id) {
    const res = await fetch(`${API_BASE}/chats/${id}/activate`, {
      method: "POST"
    });
    return res.json();
  },

  async renameChat(id, name) {
    const res = await fetch(`${API_BASE}/chats/${id}/rename`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name }),
    });
    return res.json();
  },

  async deleteChat(id) {
    const res = await fetch(`${API_BASE}/chats/${id}`, {
      method: "DELETE"
    });
    return res.json();
  },

  async getChatMessages(id) {
    const res = await fetch(`${API_BASE}/chats/${id}/messages`);
    return res.json();
  },

  // ── Translator ────────────────────────────────────────────────────────
  async translate(text, source_lang, target_lang, formal = true) {
    const res = await fetch(`${API_BASE}/translator/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text, source_lang, target_lang, formal }),
    });
    return res.json();
  },

  async detectLanguage(text) {
    const res = await fetch(`${API_BASE}/translator/detect`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text }),
    });
    return res.json();
  },

  async translateAndSpeak(text, source_lang, target_lang, formal = true) {
    const res = await fetch(`${API_BASE}/translator/speak`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text, source_lang, target_lang, formal }),
    });
    return res.json();
  },

  async getSupportedLanguages() {
    const res = await fetch(`${API_BASE}/translator/languages`);
    return res.json();
  },

};