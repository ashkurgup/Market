console.log("✅ Phase‑2 JS loaded");

async function loadPhase2() {
  try {
    const url = "snapshots/market_phase2.json?t=" + Date.now();
    const res = await fetch(url, { cache: "no-store" });
    const data = await res.json();

    console.log("✅ Phase‑2 data:", data);

    renderLastUpdated(data.computed_at);
    renderWeeklyLevels(data.weekly_levels);
    renderKeyLevels(data.key_levels);
    renderSessionLevels(data.session_levels);
    renderStructureEvents(data.structure_events);

  } catch (err) {
    console.error("❌ Phase‑2 load failed:", err);
  }
}

/* ================= META ================= */

function renderLastUpdated(ts) {
  const el = document.getElementById("phase2-last-updated");
  if (!el || !ts) return;
  el.innerText = "Last updated: " + new Date(ts).toLocaleString("en-IN");
}

/* ================= WEEKLY LEVELS ================= */

function renderWeeklyLevels(w) {
  const el = document.querySelector("#weekly-levels .content");
  if (!el || !w || w.previous_week_high == null) {
    el.innerHTML = "<em>No data</em>";
    return;
  }

  el.innerHTML = `
    <div><em>High:</em> <strong>${w.previous_week_high.toFixed(2)}</strong></div>
    <div><em>Low:</em> <strong>${w.previous_week_low.toFixed(2)}</strong></div>
    <div><em>(${w.week_start} → ${w.week_end})</em></div>
  `;
}

/* ================= KEY LEVELS ================= */

function renderKeyLevels(k) {
  const el = document.querySelector("#key-levels .content");
  if (!el || !k) {
    el.innerHTML = "<em>No data</em>";
    return;
  }

  const rList = Array.isArray(k.resistance) ? k.resistance : [];
  const sList = Array.isArray(k.support) ? k.support : [];

  const renderList = (label, arr) => {
    if (!arr.length) {
      return `<div><em>${label}:</em> —</div>`;
    }
    return `
      <div><em>${label}:</em></div>
      ${arr.map(v => `<div style="margin-left:12px;"><strong>${v}</strong></div>`).join("")}
    `;
  };

  el.innerHTML = `
    ${renderList("Resistance", rList)}
    ${renderList("Support", sList)}
  `;
}

/* ================= SESSION HIGH / LOW ================= */

function renderSessionLevels(s) {
  const el = document.querySelector("#session-levels .content");
  if (!el || !s || s.high == null || s.low == null) {
    el.innerHTML = "<em>No session data (market closed or not started)</em>";
    return;
  }

  el.innerHTML = `
    <div><em>High:</em> <strong>${s.high.toFixed(2)}</strong></div>
    <div><em>Low:</em> <strong>${s.low.toFixed(2)}</strong></div>
  `;
}

/* ================= STRUCTURE EVENTS ================= */

function renderStructureEvents(events) {
  const el = document.querySelector("#structure-events .content");

  if (!el || !Array.isArray(events) || events.length === 0) {
    el.innerHTML = "<em>No events detected</em>";
    return;
  }

  el.innerHTML = events.map(e => `
    <div style="margin-bottom:8px;">
      <strong>${e.event} ${e.direction}</strong><br>
      Structure: ${e.structure}<br>
      Level: ${e.level}<br>
      Confirmed by: ${e.confirmed_by}<br>
      Time: ${new Date(e.timestamp).toLocaleTimeString("en-IN")}
    </div>
  `).join("<hr>");
}

/* ================= INIT ================= */

document.addEventListener("DOMContentLoaded", loadPhase2);
