console.log("✅ Phase‑2 JS loaded");

async function loadPhase2() {
  try {
    const url = "snapshots/market_phase2.json?t=" + Date.now();
    const res = await fetch(url, { cache: "no-store" });
    const data = await res.json();

    console.log("✅ Phase‑2 data (raw):", data);
    console.log("✅ Phase‑2 keys:", Object.keys(data));

    /* ===== Header ===== */
    if (data.computed_at) {
      renderLastUpdated(data.computed_at);
    }

    /* ===== Phase‑2 Boxes ===== */
    renderKeyLevels(data.key_levels || null);
    renderSessionLevels(data.session_levels || null);
    renderStructureEvents(data.structure_events || []);

    /* ===== Trend Architect (13:00 Snapshot) ===== */
    const ta1300 =
      data.trend_architect_1300 ||
      data.trendArchitect1300 ||
      data.trend_architect ||
      null;

    console.log("✅ Bound Trend Architect @13:00:", ta1300);

    renderTrendArchitect1300(ta1300);

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

/* ================= KEY LEVELS ================= */

function renderKeyLevels(k) {
  const el = document.querySelector("#key-levels .content");
  if (!el || !k) {
    el.innerHTML = "<em>No data</em>";
    return;
  }

  const r = k.resistance || [];
  const s = k.support || [];

  let html = "";

  html += "<div class='line'><em>Resistance:</em></div>";
  if (r.length) {
    r.forEach(v => {
      html += `<div style="margin-left:12px;"><strong>${v}</strong></div>`;
    });
  } else {
    html += "<div style='margin-left:12px;'>—</div>";
  }

  html += "<div class='line' style='margin-top:6px;'><em>Support:</em></div>";
  if (s.length) {
    s.forEach(v => {
      html += `<div style="margin-left:12px;"><strong>${v}</strong></div>`;
    });
  } else {
    html += "<div style='margin-left:12px;'>—</div>";
  }

  el.innerHTML = html;
}

/* ================= SESSION LEVELS ================= */

function renderSessionLevels(s) {
  const el = document.querySelector("#session-levels .content");
  if (!el || !s || s.high == null || s.low == null) {
    el.innerHTML = "<em>No data</em>";
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

/* ================= TREND ARCHITECT ================= */

function renderTrendArchitect1300(t) {
  const el = document.querySelector("#trend-architect-1300 .content");
  if (!el) return;

  if (!t || !t.major_candle || !t.distance_travelled) {
    console.warn("⚠️ Trend Architect data missing or malformed:", t);
    el.innerHTML = "<em>Waiting for Trend Architect snapshot…</em>";
    return;
  }

  el.innerHTML = `
    <div class="trend-row">
      <span class="trend-label">Major Candle:</span>
      <span class="trend-value">
        ${t.major_candle.range} pts (${t.major_candle.type}) @ ${t.major_candle.time}
      </span>
    </div>

    <div class="trend-row">
      <span class="trend-label">Next Candle:</span>
      <span class="trend-value">${t.next_candle.relation}</span>
    </div>

    <div class="trend-row">
      <span class="trend-label">Total Distance:</span>
      <span class="trend-value">
        ${t.distance_travelled.points} pts |
        Overlaps: ${t.distance_travelled.overlaps} |
        Small candles: ${t.distance_travelled.small_candles}
      </span>
    </div>

    <div class="trend-row">
      <span class="trend-label">Market Character:</span>
      <span class="trend-value">${t.market_character}</span>
    </div>
  `;
}

/* ================= INIT ================= */

document.addEventListener("DOMContentLoaded", loadPhase2);
