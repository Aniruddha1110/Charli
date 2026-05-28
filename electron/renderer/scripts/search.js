// search.js — Web Search UI logic

let searchMode = "web";   // "web" or "news"

async function runSearch() {
  const input = document.getElementById("search-input");
  const query = input.value.trim();
  if (!query) return;

  // Show loading state
  document.getElementById("search-summary").innerHTML = `
    <div class="search-summary-box loading">
      <div class="bubble typing" style="display:inline-flex; gap:4px; padding:8px 12px">
        <span></span><span></span><span></span>
      </div>
      Searching for "${query}"...
    </div>`;
  document.getElementById("search-results").innerHTML = "";

  try {
    let data;
    if (searchMode === "news") {
      data = await api.searchNews(query);
      renderResults(data.results, false);
      document.getElementById("search-summary").innerHTML = "";
    } else {
      data = await api.search(query, 5, true);
      renderSummary(data.summary, query);
      renderResults(data.results, true);
    }
  } catch (err) {
    document.getElementById("search-summary").innerHTML =
      `<div class="search-summary-box error">Search failed: ${err.message}</div>`;
  }
}

function renderSummary(summary, query) {
  const el = document.getElementById("search-summary");
  if (!summary) {
    el.innerHTML = "";
    return;
  }

  el.innerHTML = `
    <div class="search-summary-box">
      <div class="search-summary-header">
        <i data-lucide="sparkles" width="14" height="14"></i>
        Charli's summary for "${query}"
      </div>
      <div class="search-summary-text">${escSH(summary)}</div>
    </div>`;

  lucide.createIcons();
}

function renderResults(results, showNumber = true) {
  const container = document.getElementById("search-results");

  if (!results || results.length === 0) {
    container.innerHTML = `<div class="empty-state">No results found.</div>`;
    return;
  }

  container.innerHTML = results.map((r, i) => `
    <div class="search-result-item">
      <div class="search-result-header">
        ${showNumber ? `<span class="result-num">${i + 1}</span>` : ""}
        <div class="result-title-block">
          <a class="result-title" href="#" onclick="openUrl('${escSP(r.url)}')">${escSH(r.title)}</a>
          <span class="result-url">${escSH(shortUrl(r.url))}</span>
        </div>
        <button class="result-open-btn" onclick="openUrl('${escSP(r.url)}')" title="Open in browser">
          <i data-lucide="external-link" width="13" height="13"></i>
        </button>
      </div>
      <div class="result-snippet">${escSH(r.snippet || "")}</div>
      ${r.source ? `<div class="result-source">${escSH(r.source)} · ${escSH(r.date || "")}</div>` : ""}
    </div>
  `).join("");

  lucide.createIcons();
}

function setSearchMode(mode, btn) {
  searchMode = mode;
  document.querySelectorAll(".search-mode-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  // Clear results when switching mode
  document.getElementById("search-summary").innerHTML = "";
  document.getElementById("search-results").innerHTML = "";
}

async function openUrl(url) {
  // Use Electron shell to open in default browser
  const { shell } = require("electron");
  // Since we can't use require in renderer, call backend instead
  await fetch(`http://127.0.0.1:8000/search/open`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ url }),
  }).catch(() => {
    // Fallback — open via window
    window.open(url, "_blank");
  });
}

// ── Helpers ────────────────────────────────────────────────────────────────
function shortUrl(url) {
  try {
    const u = new URL(url);
    return u.hostname.replace("www.", "");
  } catch {
    return url;
  }
}

function escSH(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escSP(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'");
}