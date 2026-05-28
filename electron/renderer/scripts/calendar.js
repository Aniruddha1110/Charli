// calendar.js — Calendar UI logic

let calYear  = new Date().getFullYear();
let calMonth = new Date().getMonth() + 1;  // 1-based
let calEvents = [];
let selectedDate = null;

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

const DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];


async function initCalendar() {
  await loadMonth(calYear, calMonth);
}


async function loadMonth(year, month) {
  calYear  = year;
  calMonth = month;
  calEvents = await api.getMonthEvents(year, month);
  renderCalendar();
  renderUpcoming();
}


function renderCalendar() {
  // Update header
  document.getElementById("cal-month-label").textContent =
    `${MONTHS[calMonth - 1]} ${calYear}`;

  const grid = document.getElementById("cal-grid");

  // First day of month and total days
  const firstDay  = new Date(calYear, calMonth - 1, 1).getDay();
  const totalDays = new Date(calYear, calMonth, 0).getDate();
  const today     = new Date();

  let html = "";

  // Day headers
  DAYS.forEach(d => {
    html += `<div class="cal-day-header">${d}</div>`;
  });

  // Empty cells before first day
  for (let i = 0; i < firstDay; i++) {
    html += `<div class="cal-cell empty"></div>`;
  }

  // Day cells
  for (let day = 1; day <= totalDays; day++) {
    const dateStr  = `${calYear}-${String(calMonth).padStart(2,"0")}-${String(day).padStart(2,"0")}`;
    const isToday  = (
      day === today.getDate() &&
      calMonth === today.getMonth() + 1 &&
      calYear  === today.getFullYear()
    );
    const dayEvents = calEvents.filter(e => e.start_time.startsWith(dateStr));
    const isSelected = dateStr === selectedDate;

    html += `
      <div class="cal-cell ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}"
           onclick="selectDate('${dateStr}')">
        <span class="cal-day-num">${day}</span>
        ${dayEvents.slice(0, 2).map(e => `
          <div class="cal-event-dot" title="${escCH(e.title)}">
            ${escCH(e.title)}
          </div>
        `).join("")}
        ${dayEvents.length > 2
          ? `<div class="cal-more">+${dayEvents.length - 2} more</div>`
          : ""}
      </div>`;
  }

  grid.innerHTML = html;
}


async function renderUpcoming() {
  const events  = await api.getUpcomingEvents(5);
  const container = document.getElementById("cal-upcoming");

  if (!events.length) {
    container.innerHTML = `<div class="empty-state" style="margin-top:16px">
      No upcoming events.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="cal-upcoming-title">Upcoming</div>
    ${events.map(e => `
      <div class="cal-upcoming-item">
        <div class="cal-upcoming-date">${formatEventDate(e.start_time)}</div>
        <div class="cal-upcoming-name">${escCH(e.title)}</div>
        ${e.location
          ? `<div class="cal-upcoming-loc">
               <i data-lucide="map-pin" width="11" height="11"></i>
               ${escCH(e.location)}
             </div>`
          : ""}
        <button class="cal-delete-btn" onclick="deleteCalEvent(${e.id})">
          <i data-lucide="trash-2" width="12" height="12"></i>
        </button>
      </div>
    `).join("")}`;

  lucide.createIcons();
}


function selectDate(dateStr) {
  selectedDate = dateStr;
  renderCalendar();

  // Show events for this day
  const dayEvents = calEvents.filter(e => e.start_time.startsWith(dateStr));
  const panel     = document.getElementById("cal-day-panel");
  const title     = document.getElementById("cal-day-title");
  const list      = document.getElementById("cal-day-events");

  // Format date nicely
  const d = new Date(dateStr + "T00:00:00");
  title.textContent = d.toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric"
  });

  if (!dayEvents.length) {
    list.innerHTML = `<div style="color:var(--text-muted); font-size:13px;
      padding:8px 0">No events. Add one below.</div>`;
  } else {
    list.innerHTML = dayEvents.map(e => `
      <div class="cal-day-event-item">
        <div class="cal-day-event-time">${formatTime(e.start_time)}</div>
        <div class="cal-day-event-info">
          <div class="cal-day-event-title">${escCH(e.title)}</div>
          ${e.description
            ? `<div class="cal-day-event-desc">${escCH(e.description)}</div>`
            : ""}
          ${e.location
            ? `<div class="cal-day-event-desc">
                 <i data-lucide="map-pin" width="11" height="11"></i>
                 ${escCH(e.location)}
               </div>`
            : ""}
        </div>
        <button class="cal-delete-btn" onclick="deleteCalEvent(${e.id})">
          <i data-lucide="trash-2" width="12" height="12"></i>
        </button>
      </div>
    `).join("");
  }

  panel.classList.remove("hidden");
  lucide.createIcons();
}


async function addCalEvent() {
  const titleEl = document.getElementById("cal-event-title");
  const timeEl  = document.getElementById("cal-event-time");
  const endEl   = document.getElementById("cal-event-end");
  const locEl   = document.getElementById("cal-event-location");
  const descEl  = document.getElementById("cal-event-desc");

  const title = titleEl.value.trim();
  if (!title) return;

  // Use selected date or today
  const date      = selectedDate || new Date().toISOString().split("T")[0];
  const time      = timeEl.value  || "00:00";
  const start_time = `${date}T${time}`;
  const end_time   = endEl.value  ? `${date}T${endEl.value}` : null;
  const location   = locEl.value.trim();
  const description = descEl.value.trim();

  await api.createEvent(title, start_time, end_time, description, location);

  // Clear inputs
  titleEl.value = "";
  timeEl.value  = "";
  endEl.value   = "";
  locEl.value   = "";
  descEl.value  = "";

  // Reload
  await loadMonth(calYear, calMonth);
  if (selectedDate) selectDate(selectedDate);
}


async function deleteCalEvent(id) {
  await api.deleteEvent(id);
  await loadMonth(calYear, calMonth);
  if (selectedDate) selectDate(selectedDate);
}


function prevMonth() {
  if (calMonth === 1) { calYear--;  calMonth = 12; }
  else                { calMonth--; }
  loadMonth(calYear, calMonth);
}

function nextMonth() {
  if (calMonth === 12) { calYear++;  calMonth = 1; }
  else                 { calMonth++; }
  loadMonth(calYear, calMonth);
}


// ── Helpers ────────────────────────────────────────────────────────────────
function formatEventDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
  });
}

function formatTime(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d)) return "";
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

function escCH(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}