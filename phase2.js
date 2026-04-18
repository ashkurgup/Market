console.log("✅ Phase‑2 JS loaded");

async function loadPhase2() {
  try {
    const url = "snapshots/market_phase2.json?t=" + Date.now();
    const res = await fetch(url, { cache: "no-store" });
    const data = await res.json();

    console.log("✅ Phase‑2 data:", data);

    renderLastUpdated(data.computed_at);

    renderTrendArchitect1300(data.trend_architect_1300);
    renderStructuralBiasFromTA(data.trend_architect_1300);

    renderMomentumEvents(data.momentum_events);

    renderGlobalIndices(data.global_indices);

    renderPreMarketGlobalBias(data.premarket_global_bias);

  } catch (err) {
    console.error("❌ Phase‑2 load failed:", err);
  }
}

/* ================= LAST UPDATED ================= */

function renderLastUpdated(ts) {
  const el = document.getElementById("phase2-last-updated");
  if (!el || !ts) return;
  el.innerText = "Last updated: " + new Date(ts).toLocaleTimeString("en-IN");
}

/* ================= TREND ARCHITECT ================= */

function renderTrendArchitect1300(t) {
  const el = document.querySelector("#trend-architect-1300 .content");
  if (!el) return;

  if (!t) {
    el.innerHTML = "<em>No data</em>";
    return;
  }

  el.innerHTML = `
    <div><strong>Major Candle:</strong> ${t.major_candle.range} pts @ ${t.major_candle.time}</div>
    <div><strong>Distance:</strong> ${t.distance_travelled.points} pts</div>
    <div><strong>Overlaps:</strong> ${t.distance_travelled.overlaps}</div>
    <div><strong>Small candles:</strong> ${t.distance_travelled.small_candles}</div>
    <div><strong>Market Character:</strong> ${t.market_character}</div>
  `;
}

/* ================= STRUCTURAL BIAS ================= */

function renderStructuralBiasFromTA(t) {
  const el = document.querySelector("#structural-bias .content");
  if (!el || !t) return;

  let value = "All ⚪ — Stay contextual only";

  if (t.market_character.includes("frequent overlap")) {
    value = "4H 🟢 / 1H 🟢 / 15m ⚪ — Pullback phase";
  } else if (t.market_character.includes("Steady move")) {
    value = "4H 🟢 / 1H 🟢 / 15m 🟢 — Clean trend";
  }

  el.innerHTML = `<strong style="color:#000;">${value}</strong>`;
}

/* ================= MOMENTUM EVENTS ================= */

function renderMomentumEvents(events) {
  const el = document.querySelector("#momentum-events .content");
  if (!el || !Array.isArray(events) || events.length === 0) {
    el.innerHTML = "<em>No momentum events detected</em>";
    return;
  }

  el.innerHTML = events.map(e => {
    let color = "#999";
    if (e.severity === "High") color = "#e74c3c";
    if (e.severity === "Medium") color = "#f39c12";
    if (e.severity === "Low") color = "#2ecc71";

    return `
      <div style="margin-bottom:6px;">
        <strong>${e.description}</strong><br>
        <span style="color:${color}; font-size:11px;">
          ${e.severity} • ${new Date(e.timestamp).toLocaleTimeString("en-IN")}
        </span>
      </div>
    `;
  }).join("");
}

/* ================= GLOBAL INDICES ================= */

function renderGlobalIndices(indices) {
  const el = document.querySelector("#global-indices .content");
  if (!el || !Array.isArray(indices) || indices.length === 0) {
    el.innerHTML = "<em>No data</em>";
    return;
  }

  el.innerHTML = indices.map(i => {
    const pctColor = i.pct_change_30m >= 0 ? "#2ecc71" : "#e74c3c";
    const sign = i.pct_change_30m >= 0 ? "+" : "";
    const square = i.is_open
      ? "<span style='color:#2ecc71;'>■</span>"
      : "<span style='color:#e74c3c;'>■</span>";

    return `
      <div style="margin-bottom:6px;">
        ${square}
        <strong style="margin-left:6px;">${i.name}</strong>
        <span style="color:${pctColor}; margin-left:6px;">
          ${sign}${i.pct_change_30m}%
        </span>
      </div>
    `;
  }).join("");
}

/* ================= PRE‑MARKET GLOBAL BIAS ================= */

function renderPreMarketGlobalBias(value) {
  const el = document.getElementById("premarket-global-bias");
  if (!el || typeof value !== "number") return;

  let color = "#999";
  if (value <= 2) color = "#e74c3c";
  else if (value <= 4) color = "#f39c12";
  else if (value <= 7) color = "#2ecc71";
  else color = "#27ae60";

  el.innerHTML = `
    <div style="font-size:12px;color:#777;margin-bottom:4px;">
      Pre‑Market Global Bias
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
      <div style="flex:1;height:10px;background:#eee;border-radius:5px;">
        <
