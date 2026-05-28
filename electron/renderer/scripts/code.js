let codeLanguage = "python";
let lastResult   = "";


async function initCodePanel() {
  await loadLanguages();
  lucide.createIcons();
}


async function loadLanguages() {
  const data   = await api.getLanguages();
  const select = document.getElementById("code-language-select");
  if (!select) return;

  select.innerHTML = data.languages.map(lang => `
    <option value="${lang}" ${lang === codeLanguage ? "selected" : ""}>
      ${lang.charAt(0).toUpperCase() + lang.slice(1)}
    </option>
  `).join("");
}


function setCodeLanguage(lang) {
  codeLanguage = lang;
  const editor = document.getElementById("code-input");
  if (editor) editor.placeholder = `Write or paste your ${lang} code here…`;
}


async function runCodeAction(action) {
  const code    = document.getElementById("code-input").value;
  const prompt  = document.getElementById("code-prompt").value.trim();
  const output  = document.getElementById("code-output");
  const spinner = document.getElementById("code-spinner");

  if (action !== "write" && !code.trim()) {
    showCodeStatus("Paste your code in the editor first.", "error");
    return;
  }
  if (action === "write" && !prompt) {
    showCodeStatus("Describe what you want to build.", "error");
    return;
  }

  setCodeActionsDisabled(true);
  spinner.classList.remove("hidden");
  output.innerHTML = `
    <div style="color:var(--text-muted); font-size:13px; padding:8px;">
      ${getActionLabel(action)}...
    </div>`;

  try {
    const data = await api.codeAssistant(action, code, prompt, codeLanguage);
    lastResult = data.result;
    renderCodeOutput(data.result, data.language, action);
    showCodeStatus(`✓ ${getActionLabel(action)} complete`, "success");
  } catch (err) {
    output.innerHTML = `
      <div style="color:var(--red); font-size:13px; padding:8px;">
        Error: ${err.message}
      </div>`;
    showCodeStatus("Request failed.", "error");
  }

  setCodeActionsDisabled(false);
  spinner.classList.add("hidden");
}


function renderCodeOutput(result, language, action) {
  const output = document.getElementById("code-output");
  const parts  = parseCodeBlocks(result);
  let   html   = "";

  parts.forEach(part => {
    if (part.type === "code") {
      const lang = part.language || language;
      html += `
        <div class="code-block-wrapper">
          <div class="code-block-header">
            <span class="code-block-lang">${lang}</span>
            <button class="code-copy-btn" onclick="copyCode(this)" data-code="${escapeAttr(part.content)}">
              <i data-lucide="copy" width="12" height="12"></i> Copy
            </button>
            <button class="code-copy-btn" onclick="useCode(this)" data-code="${escapeAttr(part.content)}">
              <i data-lucide="arrow-left" width="12" height="12"></i> Use
            </button>
          </div>
          <pre class="code-block"><code>${highlightCode(part.content, lang)}</code></pre>
        </div>`;
    } else if (part.content.trim()) {
      html += `<div class="code-explanation">${formatExplanation(part.content)}</div>`;
    }
  });

  output.innerHTML = html || `<div class="code-explanation">${formatExplanation(result)}</div>`;
  lucide.createIcons();
}


function parseCodeBlocks(text) {
  const parts   = [];
  const regex   = /```(\w+)?\n?([\s\S]*?)```/g;
  let   lastIdx = 0;
  let   match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push({ type: "text", content: text.slice(lastIdx, match.index) });
    }
    parts.push({ type: "code", language: match[1] || "", content: match[2].trim() });
    lastIdx = regex.lastIndex;
  }

  if (lastIdx < text.length) {
    parts.push({ type: "text", content: text.slice(lastIdx) });
  }

  return parts.length ? parts : [{ type: "text", content: text }];
}


function highlightCode(code, language) {
  let html = code
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const lang = (language || "").toLowerCase();

  const keywords = {
    python:     /\b(def|class|import|from|return|if|elif|else|for|while|in|not|and|or|try|except|finally|with|as|pass|break|continue|lambda|yield|raise|True|False|None|async|await)\b/g,
    javascript: /\b(const|let|var|function|return|if|else|for|while|class|import|export|default|from|async|await|try|catch|finally|throw|new|this|typeof|instanceof|true|false|null|undefined)\b/g,
    typescript: /\b(const|let|var|function|return|if|else|for|while|class|import|export|default|from|async|await|try|catch|interface|type|enum|implements|extends|true|false|null|undefined)\b/g,
    java:       /\b(public|private|protected|class|interface|extends|implements|import|return|if|else|for|while|new|this|static|final|void|int|String|boolean|true|false|null)\b/g,
    cpp:        /\b(int|float|double|char|bool|void|class|struct|public|private|protected|return|if|else|for|while|include|using|namespace|new|delete|true|false|nullptr)\b/g,
    sql:        /\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|DROP|TABLE|INDEX|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|LIKE|ORDER|BY|GROUP|HAVING|LIMIT|AS|NULL|PRIMARY|KEY)\b/gi,
  };

  const kw = keywords[lang] || keywords.python;

  html = html
    .replace(kw, '<span class="hl-keyword">$&</span>')
    .replace(/(["'`])(?:(?!\1)[^\\]|\\.)*\1/g, '<span class="hl-string">$&</span>')
    .replace(/(\/\/.*$|#.*$)/gm, '<span class="hl-comment">$&</span>')
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="hl-number">$&</span>')
    .replace(/\b([a-zA-Z_]\w*)\s*(?=\()/g, '<span class="hl-function">$1</span>');

  return html;
}


function copyCode(btn) {
  navigator.clipboard.writeText(btn.dataset.code).then(() => {
    btn.innerHTML = `<i data-lucide="check" width="12" height="12"></i> Copied`;
    lucide.createIcons();
    setTimeout(() => {
      btn.innerHTML = `<i data-lucide="copy" width="12" height="12"></i> Copy`;
      lucide.createIcons();
    }, 2000);
  });
}

function useCode(btn) {
  const editor = document.getElementById("code-input");
  if (editor) {
    editor.value = btn.dataset.code;
    showCodeStatus("Code moved to editor.", "success");
  }
}

function copyAllOutput() {
  if (!lastResult) return;
  navigator.clipboard.writeText(lastResult).then(() => {
    showCodeStatus("✓ Output copied to clipboard", "success");
  });
}

function clearCodePanel() {
  document.getElementById("code-input").value  = "";
  document.getElementById("code-prompt").value = "";
  document.getElementById("code-output").innerHTML = `
    <div class="code-output-placeholder">
      <i data-lucide="code-2" width="32" height="32"></i>
      <p>Output will appear here</p>
    </div>`;
  lastResult = "";
  lucide.createIcons();
}


function getActionLabel(action) {
  const labels = {
    write:    "Writing code",
    debug:    "Debugging",
    explain:  "Explaining",
    review:   "Reviewing",
    optimize: "Optimizing",
    complete: "Completing",
    convert:  "Converting",
    test:     "Writing tests",
  };
  return labels[action] || action;
}

function setCodeActionsDisabled(disabled) {
  document.querySelectorAll(".code-action-btn").forEach(btn => {
    btn.disabled = disabled;
  });
}

function showCodeStatus(msg, type = "info") {
  const el = document.getElementById("code-status");
  if (!el) return;
  const colors = {
    info:    "var(--text-secondary)",
    success: "var(--green)",
    error:   "var(--red)",
  };
  el.textContent = msg;
  el.style.color = colors[type];
  el.classList.remove("hidden");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), 3000);
}

function formatExplanation(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, '<code style="background:#0a0a0a; padding:1px 5px; border-radius:3px; color:#93c5fd; font-family:var(--font-mono); font-size:12px;">$1</code>')
    .replace(/\n/g, "<br>");
}

function escapeAttr(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const style = document.createElement("style");
style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
document.head.appendChild(style);