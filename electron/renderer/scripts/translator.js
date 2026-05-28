// translator.js — Translator panel logic
// Uses Unicode flag emojis — no external CSS needed, works on all platforms

const LANGUAGES = [
  { key: "afrikaans",             label: "Afrikaans",              flag: "🇿🇦" },
  { key: "albanian",              label: "Albanian",               flag: "🇦🇱" },
  { key: "amharic",               label: "Amharic",                flag: "🇪🇹" },
  { key: "arabic",                label: "Arabic",                 flag: "🇸🇦" },
  { key: "armenian",              label: "Armenian",               flag: "🇦🇲" },
  { key: "assamese",              label: "Assamese",               flag: "🇮🇳" },
  { key: "aymara",                label: "Aymara",                 flag: "🇧🇴" },
  { key: "azerbaijani",           label: "Azerbaijani",            flag: "🇦🇿" },
  { key: "bambara",               label: "Bambara",                flag: "🇲🇱" },
  { key: "basque",                label: "Basque",                 flag: "🇪🇸" },
  { key: "belarusian",            label: "Belarusian",             flag: "🇧🇾" },
  { key: "bengali",               label: "Bengali",                flag: "🇧🇩" },
  { key: "bhojpuri",              label: "Bhojpuri",               flag: "🇮🇳" },
  { key: "bosnian",               label: "Bosnian",                flag: "🇧🇦" },
  { key: "bulgarian",             label: "Bulgarian",              flag: "🇧🇬" },
  { key: "catalan",               label: "Catalan",                flag: "🇪🇸" },
  { key: "cebuano",               label: "Cebuano",                flag: "🇵🇭" },
  { key: "chichewa",              label: "Chichewa",               flag: "🇲🇼" },
  { key: "chinese_simplified",    label: "Chinese (Simplified)",   flag: "🇨🇳" },
  { key: "chinese_traditional",   label: "Chinese (Traditional)",  flag: "🇹🇼" },
  { key: "corsican",              label: "Corsican",               flag: "🇫🇷" },
  { key: "croatian",              label: "Croatian",               flag: "🇭🇷" },
  { key: "czech",                 label: "Czech",                  flag: "🇨🇿" },
  { key: "danish",                label: "Danish",                 flag: "🇩🇰" },
  { key: "dhivehi",               label: "Dhivehi",                flag: "🇲🇻" },
  { key: "dogri",                 label: "Dogri",                  flag: "🇮🇳" },
  { key: "dutch",                 label: "Dutch",                  flag: "🇳🇱" },
  { key: "english",               label: "English",                flag: "🇬🇧" },
  { key: "esperanto",             label: "Esperanto",              flag: "🏳️" },
  { key: "estonian",              label: "Estonian",               flag: "🇪🇪" },
  { key: "ewe",                   label: "Ewe",                    flag: "🇬🇭" },
  { key: "filipino",              label: "Filipino",               flag: "🇵🇭" },
  { key: "finnish",               label: "Finnish",                flag: "🇫🇮" },
  { key: "french",                label: "French",                 flag: "🇫🇷" },
  { key: "frisian",               label: "Frisian",                flag: "🇳🇱" },
  { key: "galician",              label: "Galician",               flag: "🇪🇸" },
  { key: "georgian",              label: "Georgian",               flag: "🇬🇪" },
  { key: "german",                label: "German",                 flag: "🇩🇪" },
  { key: "greek",                 label: "Greek",                  flag: "🇬🇷" },
  { key: "guarani",               label: "Guarani",                flag: "🇵🇾" },
  { key: "gujarati",              label: "Gujarati",               flag: "🇮🇳" },
  { key: "haitian_creole",        label: "Haitian Creole",         flag: "🇭🇹" },
  { key: "hausa",                 label: "Hausa",                  flag: "🇳🇬" },
  { key: "hawaiian",              label: "Hawaiian",               flag: "🇺🇸" },
  { key: "hebrew",                label: "Hebrew",                 flag: "🇮🇱" },
  { key: "hindi",                 label: "Hindi",                  flag: "🇮🇳" },
  { key: "hmong",                 label: "Hmong",                  flag: "🇱🇦" },
  { key: "hungarian",             label: "Hungarian",              flag: "🇭🇺" },
  { key: "icelandic",             label: "Icelandic",              flag: "🇮🇸" },
  { key: "igbo",                  label: "Igbo",                   flag: "🇳🇬" },
  { key: "ilocano",               label: "Ilocano",                flag: "🇵🇭" },
  { key: "indonesian",            label: "Indonesian",             flag: "🇮🇩" },
  { key: "irish",                 label: "Irish",                  flag: "🇮🇪" },
  { key: "italian",               label: "Italian",                flag: "🇮🇹" },
  { key: "japanese",              label: "Japanese",               flag: "🇯🇵" },
  { key: "javanese",              label: "Javanese",               flag: "🇮🇩" },
  { key: "kannada",               label: "Kannada",                flag: "🇮🇳" },
  { key: "kazakh",                label: "Kazakh",                 flag: "🇰🇿" },
  { key: "khmer",                 label: "Khmer",                  flag: "🇰🇭" },
  { key: "kinyarwanda",           label: "Kinyarwanda",            flag: "🇷🇼" },
  { key: "konkani",               label: "Konkani",                flag: "🇮🇳" },
  { key: "korean",                label: "Korean",                 flag: "🇰🇷" },
  { key: "krio",                  label: "Krio",                   flag: "🇸🇱" },
  { key: "kurdish_kurmanji",      label: "Kurdish (Kurmanji)",     flag: "🇮🇶" },
  { key: "kurdish_sorani",        label: "Kurdish (Sorani)",       flag: "🇮🇶" },
  { key: "kyrgyz",                label: "Kyrgyz",                 flag: "🇰🇬" },
  { key: "lao",                   label: "Lao",                    flag: "🇱🇦" },
  { key: "latin",                 label: "Latin",                  flag: "🇻🇦" },
  { key: "latvian",               label: "Latvian",                flag: "🇱🇻" },
  { key: "lingala",               label: "Lingala",                flag: "🇨🇩" },
  { key: "lithuanian",            label: "Lithuanian",             flag: "🇱🇹" },
  { key: "luganda",               label: "Luganda",                flag: "🇺🇬" },
  { key: "luxembourgish",         label: "Luxembourgish",          flag: "🇱🇺" },
  { key: "macedonian",            label: "Macedonian",             flag: "🇲🇰" },
  { key: "maithili",              label: "Maithili",               flag: "🇮🇳" },
  { key: "malagasy",              label: "Malagasy",               flag: "🇲🇬" },
  { key: "malay",                 label: "Malay",                  flag: "🇲🇾" },
  { key: "malayalam",             label: "Malayalam",              flag: "🇮🇳" },
  { key: "maltese",               label: "Maltese",                flag: "🇲🇹" },
  { key: "maori",                 label: "Maori",                  flag: "🇳🇿" },
  { key: "marathi",               label: "Marathi",                flag: "🇮🇳" },
  { key: "meitei",                label: "Meitei (Manipuri)",      flag: "🇮🇳" },
  { key: "mizo",                  label: "Mizo",                   flag: "🇮🇳" },
  { key: "mongolian",             label: "Mongolian",              flag: "🇲🇳" },
  { key: "myanmar",               label: "Myanmar (Burmese)",      flag: "🇲🇲" },
  { key: "nepali",                label: "Nepali",                 flag: "🇳🇵" },
  { key: "norwegian",             label: "Norwegian",              flag: "🇳🇴" },
  { key: "odia",                  label: "Odia (Oriya)",           flag: "🇮🇳" },
  { key: "oromo",                 label: "Oromo",                  flag: "🇪🇹" },
  { key: "pashto",                label: "Pashto",                 flag: "🇦🇫" },
  { key: "persian",               label: "Persian",                flag: "🇮🇷" },
  { key: "polish",                label: "Polish",                 flag: "🇵🇱" },
  { key: "portuguese",            label: "Portuguese",             flag: "🇵🇹" },
  { key: "punjabi",               label: "Punjabi",                flag: "🇮🇳" },
  { key: "quechua",               label: "Quechua",                flag: "🇵🇪" },
  { key: "romanian",              label: "Romanian",               flag: "🇷🇴" },
  { key: "russian",               label: "Russian",                flag: "🇷🇺" },
  { key: "samoan",                label: "Samoan",                 flag: "🇼🇸" },
  { key: "sanskrit",              label: "Sanskrit",               flag: "🇮🇳" },
  { key: "scots_gaelic",          label: "Scots Gaelic",           flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿" },
  { key: "sepedi",                label: "Sepedi",                 flag: "🇿🇦" },
  { key: "serbian",               label: "Serbian",                flag: "🇷🇸" },
  { key: "sesotho",               label: "Sesotho",                flag: "🇱🇸" },
  { key: "shona",                 label: "Shona",                  flag: "🇿🇼" },
  { key: "sindhi",                label: "Sindhi",                 flag: "🇵🇰" },
  { key: "sinhala",               label: "Sinhala",                flag: "🇱🇰" },
  { key: "slovak",                label: "Slovak",                 flag: "🇸🇰" },
  { key: "slovenian",             label: "Slovenian",              flag: "🇸🇮" },
  { key: "somali",                label: "Somali",                 flag: "🇸🇴" },
  { key: "spanish",               label: "Spanish",                flag: "🇪🇸" },
  { key: "sundanese",             label: "Sundanese",              flag: "🇮🇩" },
  { key: "swahili",               label: "Swahili",                flag: "🇰🇪" },
  { key: "swedish",               label: "Swedish",                flag: "🇸🇪" },
  { key: "tajik",                 label: "Tajik",                  flag: "🇹🇯" },
  { key: "tamil",                 label: "Tamil",                  flag: "🇮🇳" },
  { key: "tatar",                 label: "Tatar",                  flag: "🇷🇺" },
  { key: "telugu",                label: "Telugu",                 flag: "🇮🇳" },
  { key: "thai",                  label: "Thai",                   flag: "🇹🇭" },
  { key: "tigrinya",              label: "Tigrinya",               flag: "🇪🇷" },
  { key: "tsonga",                label: "Tsonga",                 flag: "🇿🇦" },
  { key: "turkish",               label: "Turkish",                flag: "🇹🇷" },
  { key: "turkmen",               label: "Turkmen",                flag: "🇹🇲" },
  { key: "twi",                   label: "Twi",                    flag: "🇬🇭" },
  { key: "ukrainian",             label: "Ukrainian",              flag: "🇺🇦" },
  { key: "urdu",                  label: "Urdu",                   flag: "🇵🇰" },
  { key: "uyghur",                label: "Uyghur",                 flag: "🇨🇳" },
  { key: "uzbek",                 label: "Uzbek",                  flag: "🇺🇿" },
  { key: "vietnamese",            label: "Vietnamese",             flag: "🇻🇳" },
  { key: "welsh",                 label: "Welsh",                  flag: "🏴󠁧󠁢󠁷󠁬󠁳󠁿" },
  { key: "xhosa",                 label: "Xhosa",                  flag: "🇿🇦" },
  { key: "yiddish",               label: "Yiddish",                flag: "🇮🇱" },
  { key: "yoruba",                label: "Yoruba",                 flag: "🇳🇬" },
  { key: "zulu",                  label: "Zulu",                   flag: "🇿🇦" },
];

let translatorListening   = false;
let translatorInitialised = false;

async function initTranslator() {
  if (translatorInitialised) return;
  renderLanguageSelects();
  buildCustomDropdowns();
  lucide.createIcons();
  translatorInitialised = true;
}

function reinitTranslator() {
  translatorInitialised = false;
  initTranslator();
}

function renderLanguageSelects() {
  const sorted = [...LANGUAGES].sort((a, b) => a.label.localeCompare(b.label));
  const opts   = sorted.map(l => `<option value="${l.key}">${l.label}</option>`).join("");
  ["trans-source-lang", "trans-target-lang"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts;
  });
  const savedSrc = localStorage.getItem("charli_trans_src") || "english";
  const savedTgt = localStorage.getItem("charli_trans_tgt") || "hindi";
  document.getElementById("trans-source-lang").value = savedSrc;
  document.getElementById("trans-target-lang").value = savedTgt;
}

// ── Custom flag dropdown ───────────────────────────────────────────────────

function buildCustomDropdowns() {
  buildOneDropdown("trans-source-lang", "trans-source-custom");
  buildOneDropdown("trans-target-lang", "trans-target-custom");
}

function getLangByKey(key) {
  return LANGUAGES.find(l => l.key === key) || { key, label: key, flag: "🌐" };
}

// FIX: Use Unicode emoji flags — no external CSS or CDN required
function flagHTML(lang) {
  return `<span class="lang-flag" aria-hidden="true">${lang.flag}</span>`;
}

function buildOneDropdown(selectId, customId) {
  const select    = document.getElementById(selectId);
  const container = document.getElementById(customId);
  if (!select || !container) return;

  const sorted     = [...LANGUAGES].sort((a, b) => a.label.localeCompare(b.label));
  const currentKey = select.value || "english";
  const current    = getLangByKey(currentKey);

  container.innerHTML = `
    <div class="cdd-trigger" onclick="toggleDropdown('${customId}')">
      ${flagHTML(current)}
      <span class="cdd-label">${current.label}</span>
      <i data-lucide="chevron-down" width="14" height="14" style="margin-left:auto;color:var(--text-muted);flex-shrink:0;"></i>
    </div>
    <div class="cdd-panel hidden" id="${customId}-panel">
      <div class="cdd-search-wrap">
        <i data-lucide="search" width="13" height="13" style="color:var(--text-muted);flex-shrink:0;"></i>
        <input class="cdd-search" placeholder="Search language…"
               oninput="filterDropdown('${customId}', this.value)" />
      </div>
      <div class="cdd-list" id="${customId}-list">
        ${sorted.map(l => `
          <div class="cdd-option ${l.key === currentKey ? 'selected' : ''}"
               data-key="${l.key}"
               data-label="${l.label.toLowerCase()}"
               onclick="selectLang('${selectId}','${customId}','${l.key}')">
            ${flagHTML(l)}
            <span>${l.label}</span>
          </div>`).join("")}
      </div>
    </div>`;
  lucide.createIcons();
}

function toggleDropdown(customId) {
  const panel = document.getElementById(`${customId}-panel`);
  if (!panel) return;
  // Close any other open dropdowns
  document.querySelectorAll(".cdd-panel:not(.hidden)").forEach(p => {
    if (p.id !== `${customId}-panel`) p.classList.add("hidden");
  });
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) {
    const s = panel.querySelector(".cdd-search");
    if (s) setTimeout(() => s.focus(), 50);
  }
}

function filterDropdown(customId, query) {
  const list = document.getElementById(`${customId}-list`);
  if (!list) return;
  const q = query.toLowerCase();
  list.querySelectorAll(".cdd-option").forEach(opt => {
    const matches = opt.dataset.label.includes(q) || opt.dataset.key.includes(q);
    opt.style.display = matches ? "" : "none";
  });
}

function selectLang(selectId, customId, key) {
  const select = document.getElementById(selectId);
  if (select) select.value = key;

  const storageKey = selectId === "trans-source-lang" ? "charli_trans_src" : "charli_trans_tgt";
  localStorage.setItem(storageKey, key);

  const lang      = getLangByKey(key);
  const container = document.getElementById(customId);
  const trigger   = container && container.querySelector(".cdd-trigger");
  if (trigger) {
    trigger.innerHTML = `
      ${flagHTML(lang)}
      <span class="cdd-label">${lang.label}</span>
      <i data-lucide="chevron-down" width="14" height="14" style="margin-left:auto;color:var(--text-muted);flex-shrink:0;"></i>`;
    lucide.createIcons();
  }

  const list = document.getElementById(`${customId}-list`);
  if (list) {
    list.querySelectorAll(".cdd-option").forEach(opt =>
      opt.classList.toggle("selected", opt.dataset.key === key)
    );
  }

  const panel = document.getElementById(`${customId}-panel`);
  if (panel) panel.classList.add("hidden");
}

// Close dropdowns when clicking outside
document.addEventListener("click", e => {
  if (!e.target.closest(".cdd-wrapper")) {
    document.querySelectorAll(".cdd-panel:not(.hidden)").forEach(p =>
      p.classList.add("hidden")
    );
  }
});

// ── Swap languages ─────────────────────────────────────────────────────────
function swapLanguages() {
  const src    = document.getElementById("trans-source-lang");
  const tgt    = document.getElementById("trans-target-lang");
  const input  = document.getElementById("trans-input");
  const output = document.getElementById("trans-output");

  const tmpKey  = src.value;
  src.value     = tgt.value;
  tgt.value     = tmpKey;

  const tmpText = input.value;
  input.value   = output.value;
  output.value  = tmpText;

  buildOneDropdown("trans-source-lang", "trans-source-custom");
  buildOneDropdown("trans-target-lang", "trans-target-custom");
  lucide.createIcons();

  localStorage.setItem("charli_trans_src", src.value);
  localStorage.setItem("charli_trans_tgt", tgt.value);
}

// ── Translation actions ────────────────────────────────────────────────────
async function runTranslation() {
  const text       = document.getElementById("trans-input").value.trim();
  const sourceLang = document.getElementById("trans-source-lang").value;
  const targetLang = document.getElementById("trans-target-lang").value;
  const formal     = document.getElementById("trans-formal").checked;

  if (!text) {
    showTransStatus("Please enter text to translate.", "error");
    return;
  }
  if (sourceLang === targetLang) {
    showTransStatus("Source and target languages are the same.", "error");
    return;
  }

  setTransLoading(true);
  try {
    const result = await api.translate(text, sourceLang, targetLang, formal);
    if (result.success) {
      document.getElementById("trans-output").value = result.translation;
      showTransStatus(`✓ Translated from ${result.source} to ${result.target}`, "success");
    } else {
      showTransStatus(`✗ Translation failed: ${result.error}`, "error");
    }
  } catch (err) {
    showTransStatus(`✗ Error: ${err.message}`, "error");
  }
  setTransLoading(false);
}

async function speakTranslation() {
  const text       = document.getElementById("trans-input").value.trim();
  const sourceLang = document.getElementById("trans-source-lang").value;
  const targetLang = document.getElementById("trans-target-lang").value;
  const formal     = document.getElementById("trans-formal").checked;

  if (!text) { showTransStatus("Enter text first.", "error"); return; }
  showTransStatus("Translating and speaking...", "info");
  setTransLoading(true);
  try {
    const result = await api.translateAndSpeak(text, sourceLang, targetLang, formal);
    if (result.success) {
      document.getElementById("trans-output").value = result.translation;
      showTransStatus("✓ Speaking translation...", "success");
    }
  } catch (err) {
    showTransStatus(`✗ Error: ${err.message}`, "error");
  }
  setTransLoading(false);
}

async function speakOutput() {
  const text = document.getElementById("trans-output").value.trim();
  if (!text) return;
  await fetch("http://127.0.0.1:8000/voice/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  showTransStatus("Speaking...", "info");
}

async function listenForTranslation() {
  if (translatorListening) return;
  translatorListening = true;
  const btn = document.getElementById("trans-listen-btn");
  btn.innerHTML = `<i data-lucide="ear" width="14" height="14"></i> Listening...`;
  btn.style.color = "var(--red)";
  lucide.createIcons();
  showTransStatus("Speak now — I'll auto-detect your language...", "info");
  try {
    const res  = await fetch("http://127.0.0.1:8000/voice/listen", { method: "POST" });
    const data = await res.json();
    if (data.text) {
      document.getElementById("trans-input").value = data.text;
      showTransStatus(`✓ Heard: "${data.text}"`, "success");
      await runTranslation();
    } else {
      showTransStatus("Didn't catch that. Try again.", "error");
    }
  } catch (err) {
    showTransStatus(`✗ ${err.message}`, "error");
  }
  translatorListening = false;
  btn.innerHTML = `<i data-lucide="mic" width="14" height="14"></i> Speak`;
  btn.style.color = "";
  lucide.createIcons();
}

async function copyTranslation() {
  const text = document.getElementById("trans-output").value;
  if (!text) return;
  await navigator.clipboard.writeText(text);
  showTransStatus("✓ Copied to clipboard", "success");
}

async function detectInputLanguage() {
  const text = document.getElementById("trans-input").value.trim();
  if (!text) return;
  const result = await api.detectLanguage(text);
  showTransStatus(`Detected: ${result.language}`, "info");
  if (result.key) selectLang("trans-source-lang", "trans-source-custom", result.key);
}

// ── Helpers ────────────────────────────────────────────────────────────────
function setTransLoading(loading) {
  const btn = document.getElementById("trans-btn");
  const spk = document.getElementById("trans-speak-btn");
  btn.disabled = loading;
  spk.disabled = loading;
  btn.innerHTML = loading
    ? `<i data-lucide="loader" width="14" height="14" style="animation:spin 1s linear infinite;"></i> Translating...`
    : `<i data-lucide="languages" width="14" height="14"></i> Translate`;
  lucide.createIcons();
}

function showTransStatus(msg, type = "info") {
  const el = document.getElementById("trans-status");
  if (!el) return;
  el.textContent = msg;
  el.style.color = {
    info:    "var(--text-secondary)",
    success: "var(--green)",
    error:   "var(--red)"
  }[type] || "var(--text-secondary)";
  el.classList.remove("hidden");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), 4000);
}

document.addEventListener("DOMContentLoaded", () => initTranslator());