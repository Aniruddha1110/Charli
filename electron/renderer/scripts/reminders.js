// reminders.js — Reminders UI logic

async function loadReminders() {
  const reminders = await api.getReminders(false);
  renderReminders(reminders);
}

function renderReminders(reminders) {
  const container = document.getElementById("reminders-list");
  if (!container) return;

  if (!reminders.length) {
    container.innerHTML = `
      <div class="empty-state">
        No upcoming reminders. Add one below.
      </div>`;
    return;
  }

  container.innerHTML = reminders.map(r => `
    <div class="reminder-item ${isPast(r.remind_at) ? 'past' : ''}">
      <div class="reminder-icon">
        <i data-lucide="bell" width="16" height="16"></i>
      </div>
      <div class="reminder-body">
        <div class="reminder-title">${escRH(r.title)}</div>
        <div class="reminder-time">
          <i data-lucide="clock" width="11" height="11"></i>
          ${formatReminderTime(r.remind_at)}
          ${isPast(r.remind_at)
            ? '<span class="reminder-badge past">Past</span>'
            : timeUntil(r.remind_at)
              ? `<span class="reminder-badge upcoming">${timeUntil(r.remind_at)}</span>`
              : ''}
        </div>
      </div>
      <button class="reminder-delete" onclick="deleteReminderItem(${r.id})"
        title="Delete">
        <i data-lucide="trash-2" width="13" height="13"></i>
      </button>
    </div>
  `).join("");

  lucide.createIcons();
}

async function addReminderNatural() {
  const input = document.getElementById("reminder-natural-input");
  const text  = input.value.trim();
  if (!text) return;

  const btn = document.getElementById("reminder-natural-btn");
  btn.disabled    = true;
  btn.textContent = "Processing...";

  try {
    const result = await api.createNaturalReminder(text);
    input.value  = "";
    showReminderStatus(
      `✓ Reminder set for ${formatReminderTime(result.reminder.remind_at)}`,
      "success"
    );
    await loadReminders();
  } catch (err) {
    showReminderStatus(`✗ Failed: ${err.message}`, "error");
  }

  btn.disabled    = false;
  btn.innerHTML   = `<i data-lucide="plus" width="13" height="13"></i> Set`;
  lucide.createIcons();
}

async function addReminderManual() {
  const titleEl = document.getElementById("reminder-title-input");
  const dateEl  = document.getElementById("reminder-date-input");
  const timeEl  = document.getElementById("reminder-time-input");

  const title = titleEl.value.trim();
  const date  = dateEl.value;
  const time  = timeEl.value;

  if (!title || !date || !time) {
    showReminderStatus("Please fill in title, date and time.", "error");
    return;
  }

  const remind_at = `${date}T${time}:00`;
  await api.createReminder(title, remind_at);

  titleEl.value = "";
  showReminderStatus(`✓ Reminder set for ${date} at ${time}`, "success");
  await loadReminders();
}

async function deleteReminderItem(id) {
  await api.deleteReminder(id);
  await loadReminders();
}

function showReminderStatus(msg, type = "info") {
  const el = document.getElementById("reminder-status");
  if (!el) return;
  const colors = { info: "var(--text-secondary)", success: "var(--green)", error: "var(--red)" };
  el.textContent = msg;
  el.style.color = colors[type];
  el.classList.remove("hidden");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), 4000);
}

// ── Helpers ────────────────────────────────────────────────────────────────

function isPast(dateStr) {
  return new Date(dateStr) < new Date();
}

function formatReminderTime(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleString("en-US", {
    weekday: "short", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function timeUntil(dateStr) {
  const diff = new Date(dateStr) - new Date();
  if (diff <= 0) return null;

  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days  = Math.floor(hours / 24);

  if (days > 0)  return `in ${days}d`;
  if (hours > 0) return `in ${hours}h`;
  if (mins > 0)  return `in ${mins}m`;
  return "soon";
}

function escRH(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}