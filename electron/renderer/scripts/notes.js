// notes.js — Notes panel logic

async function loadNotes() {
  const notes = await api.getNotes();
  renderNotes(notes);
}

function renderNotes(notes) {
  const container = document.getElementById("notes-list");
  if (!container) return;

  if (notes.length === 0) {
    container.innerHTML = `<div class="empty-state">No notes yet. Write one below.</div>`;
    return;
  }

  container.innerHTML = notes.map(note => `
    <div class="note-item" data-id="${note.id}">
      <div class="note-body">
        ${note.title
          ? `<div class="note-title">${escapeHtmlNote(note.title)}</div>` : ''}
        <div class="note-content">${escapeHtmlNote(note.content)}</div>
        ${note.tags
          ? `<div class="note-tags">${note.tags.split(',').map(t =>
              `<span class="tag">${t.trim()}</span>`).join('')}</div>` : ''}
        <div class="note-date">${formatDateNote(note.created_at)}</div>
      </div>
      <button class="note-delete" onclick="deleteNote(${note.id})" title="Delete">
        <i data-lucide="trash-2" width="14" height="14"></i>
      </button>
    </div>
  `).join("");

  lucide.createIcons();
}

async function addNote() {
  const contentEl = document.getElementById("note-input");
  const content   = contentEl.value.trim();
  if (!content) return;
  const title = document.getElementById("note-title").value.trim();
  const tags  = document.getElementById("note-tags").value.trim();
  await api.createNote(content, title, tags);
  contentEl.value = "";
  document.getElementById("note-title").value = "";
  document.getElementById("note-tags").value  = "";
  loadNotes();
}

async function deleteNote(id) {
  await api.deleteNote(id);
  loadNotes();
}

function escapeHtmlNote(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function formatDateNote(dateStr) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString();
}