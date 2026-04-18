console.log("✅ Phase‑2 JS loaded");

async function loadPhase2() {
  try {
    const url = "snapshots/market_phase2.json?t=" + Date.now();
    const res = await fetch(url, { cache: "no-store" });
    const data = await res.json();

    console.log("✅ Phase‑2 data:", data);

    renderLastUpdated(data.computed_at);
    renderKeyLevels(data.key_levels);
    renderSessionLevels(data.session_levels);
    renderStructureEvents(data.structure_events);
    renderTrendArchitect1300(data.trend_architect_1300);

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

/* ================= TREND ARCHITECT ================= */

function renderTrendArchitect1300(t) {
  const el = document.querySelector("#trend-architect-1300 .content");

  if (!el) return;

  // 🔒 Defensive guard: ensure object with expected fields
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
