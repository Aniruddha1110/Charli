// tasks.js — Tasks panel logic

async function loadTasks() {
  const tasks = await api.getTasks(currentFilter === "all" ? null : currentFilter);
  renderTasks(tasks);
}

function renderTasks(tasks) {
  const container = document.getElementById("tasks-list");
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = `<div class="empty-state">No tasks yet. Add one below.</div>`;
    return;
  }

  container.innerHTML = tasks.map(task => `
    <div class="task-item ${task.status === 'done' ? 'done' : ''}" data-id="${task.id}">
      <div class="task-check" onclick="toggleTask(${task.id})">
        ${task.status === 'done'
          ? '<i data-lucide="check-circle-2" width="18" height="18" style="color:var(--green)"></i>'
          : '<i data-lucide="circle" width="18" height="18" style="color:var(--text-muted)"></i>'}
      </div>
      <div class="task-body">
        <div class="task-title">${escapeHtmlTask(task.title)}</div>
        ${task.description
          ? `<div class="task-desc">${escapeHtmlTask(task.description)}</div>` : ''}
        <div class="task-meta">
          <span class="priority ${task.priority}">${task.priority}</span>
          ${task.due_date ? `<span class="due">${task.due_date}</span>` : ''}
          <span class="task-date">${formatDateTask(task.created_at)}</span>
        </div>
      </div>
      <button class="task-delete" onclick="deleteTask(${task.id})" title="Delete">
        <i data-lucide="trash-2" width="14" height="14"></i>
      </button>
    </div>
  `).join("");

  lucide.createIcons();
}

async function toggleTask(id) {
  await api.completeTask(id);
  loadTasks();
}

async function deleteTask(id) {
  await api.deleteTask(id);
  loadTasks();
}

async function addTask() {
  const input    = document.getElementById("task-input");
  const title    = input.value.trim();
  if (!title) return;
  const priority = document.getElementById("task-priority").value;
  await api.createTask(title, "", priority);
  input.value = "";
  loadTasks();
}

function escapeHtmlTask(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function formatDateTask(dateStr) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString();
}