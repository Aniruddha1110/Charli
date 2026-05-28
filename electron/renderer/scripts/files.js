// files.js — File Manager UI logic

let currentPath = "";

async function initFileManager() {
  await loadQuickFolders();
}

// ── Quick folders ──────────────────────────────────────────────────────────
async function loadQuickFolders() {
  const data = await api.getQuickFolders();
  const container = document.getElementById("quick-folders");
  if (!container) return;

  container.innerHTML = data.folders.map(f => `
    <button class="quick-folder-btn" onclick="browseFolder('${escFP(f.path)}')">
      ${folderIcon(f.name)} ${f.name}
    </button>
  `).join("");

  lucide.createIcons();
}

// ── Browse folder ──────────────────────────────────────────────────────────
async function browseFolder(path) {
  currentPath = path;
  const data  = await api.listDirectory(path);

  if (data.error) {
    showFileError(data.error);
    return;
  }

  document.getElementById("file-current-path").textContent = path;
  renderDirectory(data);
}

function renderDirectory(data) {
  const container = document.getElementById("file-list");
  if (!container) return;

  let html = "";

  // Back button
  const parent = getParentPath(currentPath);
  if (parent) {
    html += `
      <div class="file-item folder" onclick="browseFolder('${escFP(parent)}')">
        <span class="file-icon">⬆️</span>
        <span class="file-name">..</span>
        <span class="file-meta">Up one level</span>
      </div>`;
  }

  // Folders first
  data.folders.forEach(f => {
    html += `
      <div class="file-item folder" ondblclick="browseFolder('${escFP(f.path)}')">
        <span class="file-icon">📁</span>
        <span class="file-name">${escFH(f.name)}</span>
        <span class="file-meta">${formatModified(f.modified)}</span>
        <div class="file-actions">
          <button onclick="openItem('${escFP(f.path)}')" title="Open">↗</button>
          <button onclick="startRename('${escFP(f.path)}', '${escFH(f.name)}')" title="Rename">✏️</button>
          <button onclick="deleteItem('${escFP(f.path)}')" title="Delete" class="danger">🗑</button>
        </div>
      </div>`;
  });

  // Files
  data.files.forEach(f => {
    html += `
      <div class="file-item" ondblclick="openItem('${escFP(f.path)}')">
        <span class="file-icon">${fileIcon(f.type)}</span>
        <span class="file-name">${escFH(f.name)}</span>
        <span class="file-meta">${f.size_str} · ${formatModified(f.modified)}</span>
        <div class="file-actions">
          <button onclick="openItem('${escFP(f.path)}')" title="Open">↗</button>
          <button onclick="startRename('${escFP(f.path)}', '${escFH(f.name)}')" title="Rename">✏️</button>
          <button onclick="deleteItem('${escFP(f.path)}')" title="Delete" class="danger">🗑</button>
        </div>
      </div>`;
  });

  if (!data.folders.length && !data.files.length) {
    html = `<div class="empty-state">This folder is empty.</div>`;
  }

  container.innerHTML = html;

  lucide.createIcons();
}

// ── Search ─────────────────────────────────────────────────────────────────
async function searchFiles() {
  const input = document.getElementById("file-search-input");
  const query = input.value.trim();
  if (!query) return;

  document.getElementById("file-current-path").textContent = `Search: "${query}"`;
  document.getElementById("file-list").innerHTML =
    `<div class="empty-state">Searching...</div>`;

  const data = await api.searchFiles(query);
  const container = document.getElementById("file-list");

  if (!data.results || data.results.length === 0) {
    container.innerHTML = `<div class="empty-state">No files found for "${query}"</div>`;
    return;
  }

  container.innerHTML = data.results.map(f => `
    <div class="file-item" ondblclick="openItem('${escFP(f.path)}')">
      <span class="file-icon">${fileIcon(f.type)}</span>
      <div class="file-name-block">
        <span class="file-name">${escFH(f.name)}</span>
        <span class="file-path-small">${escFH(f.folder)}</span>
      </div>
      <span class="file-meta">${f.size_str}</span>
      <div class="file-actions">
        <button onclick="openItem('${escFP(f.path)}')" title="Open">↗</button>
        <button onclick="openItem('${escFP(f.folder)}')" title="Open folder">📁</button>
        <button onclick="deleteItem('${escFP(f.path)}')" title="Delete" class="danger">🗑</button>
      </div>
    </div>
  `).join("");

  lucide.createIcons();
}

// ── File actions ───────────────────────────────────────────────────────────
async function openItem(path) {
  await api.openFile(path);
}

async function deleteItem(path) {
  if (!confirm(`Send to recycle bin?\n${path}`)) return;
  const result = await api.deleteFile(path, true);
  if (result.success) {
    if (currentPath) browseFolder(currentPath);
  } else {
    showFileError(result.error || "Delete failed");
  }
}

async function startRename(path, currentName) {
  const newName = prompt(`Rename "${currentName}" to:`, currentName);
  if (!newName || newName === currentName) return;

  const result = await api.renameFile(path, newName);
  if (result.success) {
    if (currentPath) browseFolder(currentPath);
  } else {
    showFileError(result.error || "Rename failed");
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function showFileError(msg) {
  const container = document.getElementById("file-list");
  if (container) {
    container.innerHTML = `<div class="empty-state" style="color:var(--red)">${msg}</div>`;
  }
}

function getParentPath(path) {
  if (!path) return null;
  const parts = path.replace(/\\/g, "/").split("/");
  if (parts.length <= 1) return null;
  parts.pop();
  return parts.join("\\");
}

function escFH(str) {
  if (!str) return "";
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function escFP(str) {
  if (!str) return "";
  return str.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

function formatModified(ts) {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleDateString();
}

function fileIcon(type) {
  const icons = {
    "PDF":        "file-text",
    "Word":       "file-text",
    "Excel":      "file-spreadsheet",
    "PowerPoint": "presentation",
    "Text":       "file-text",
    "Markdown":   "file-text",
    "Python":     "code-2",
    "JavaScript": "code-2",
    "TypeScript": "code-2",
    "HTML":       "globe",
    "JSON":       "braces",
    "Image":      "image",
    "GIF":        "image",
    "SVG":        "image",
    "Video":      "video",
    "Audio":      "music",
    "Archive":    "archive",
    "App":        "settings",
    "Installer":  "package",
    "Script":     "terminal",
  };
  const name = icons[type] || "file";
  return `<i data-lucide="${name}" width="16" height="16"></i>`;
}

function folderIcon(name) {
  const icons = {
    "Desktop":   "monitor",
    "Documents": "folder-open",
    "Downloads": "download",
    "Pictures":  "image",
    "Music":     "music",
    "Videos":    "video",
  };
  const icon = icons[name] || "folder";
  return `<i data-lucide="${icon}" width="14" height="14"></i>`;
}