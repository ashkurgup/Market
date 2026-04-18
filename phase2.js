console.log("✅ Phase‑2 JS loaded");

async function loadPhase2() {
  try {
    const res = await fetch("snapshots/market_phase2.json?t=" + Date.now());
    const data = await res.json();

    renderLastUpdated(data.computed_at);
    renderTrendArchitect1300(data.trend_architect_1300);
    renderStructuralBiasFromTA(data.trend_architect_1300);
    renderMomentumEvents(data.momentum_events);
    renderGlobalIndices(data.global_indices);
    renderPreMarketGlobalBias(data.premarket_global_bias);

  } catch (err) {
    console.error("❌ Phase‑2 load failed", err);
  }
}

/* ---------- LAST UPDATED ---------- */

function renderLastUpdated(ts) {
  const el = document.getElementById("phase2-last-updated");
  if (el && ts) el.innerText = "Last updated: " + new Date(ts).toLocaleTimeString("en-IN");
}

/* ---------- TREND ARCHITECT ---------- */

function renderTrendArchitect1300(t) {
  const el = document.querySelector("#trend-architect-1300 .content");
  if (!el || !t) return;
  el.innerHTML = `
    <strong>Major Candle:</strong> ${t.major_candle.range} pts @ ${t.major_candle.time}<br>
    <strong>Distance:</strong> ${t.distance_travelled.points} pts<br>
    <strong>Overlaps:</strong> ${t.distance_travelled.overlaps}<br>
    <strong>Small candles:</strong> ${t.distance_travelled.small_candles}<br>
    <strong>Market Character:</strong> ${t.market_character}
  `;
}

/* ---------- STRUCTURAL BIAS ---------- */

function renderStructuralBiasFromTA(t) {
  const el = document.querySelector("#structural-bias .content");
  if (!el || !t) return;
  let text = "All ⚪ — Stay contextual only";
  if (t.market_character.includes("frequent overlap")) {
    text = "4H 🟢 / 1H 🟢 / 15m ⚪ — Pullback phase";
  } else if (t.market_character.includes("Steady move")) {
    text = "4H 🟢 / 1H 🟢 / 15m 🟢 — Clean trend";
  }
  el.innerHTML = `<strong>${text}</strong>`;
}

/* ---------- MOMENTUM EVENTS ---------- */

function renderMomentumEvents(events = []) {
  const el = document.querySelector("#momentum-events .content");
  if (!el) return;
  if (!events.length) {
    el.innerHTML = "<em>No momentum events detected</em>";
    return;
  }
  el.innerHTML = events.map(e =>
    `<div><strong>${e.description}</strong><br>
     <span>${e.severity} • ${new Date(e.timestamp).toLocaleTimeString("en-IN")}</span></div>`
  ).join("");
}

/* ---------- GLOBAL INDICES ---------- */

function renderGlobalIndices(indices = []) {
  const el = document.querySelector("#global-indices .content");
  if (!el) return;
  if (!indices.length) {
    el.innerHTML = "<em>No data</em>";
    return;
  }
  el.innerHTML = indices.map(i => {
    const sq = i.is_open ? "■" : "■";
    const sqColor = i.is_open ? "green" : "red";
    const pctColor = i.pct_change_30m >= 0 ? "green" : "red";
    return `<div><span style="color:${sqColor}">${sq}</span> ${i.name}
            <span style="color:${pctColor}">${i.pct_change_30m}%</span></div>`;
  }).join("");
}

/* ---------- PRE‑MARKET BIAS ---------- */

function renderPreMarketGlobalBias(value) {
  const el = document.getElementById("premarket-global-bias");
  if (!el || typeof value !== "number") return;
  const color = value > 5 ? "green" : "red";
  el.innerHTML = `
    <strong>Pre‑Market Global Bias</strong>
    <div style="height:10px;background:#eee">
      <div style="width:${value * 10}%;height:100%;background:${color}"></div>
    </div>
    <strong style="color:${color}">${value}</strong>
  `;
}

document.addEventListener("DOMContentLoaded", loadPhase2);
