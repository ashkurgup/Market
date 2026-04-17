(async () => {
  const response = await fetch("./snapshots/market_phase1.json", {
    cache: "no-store"
  });
  const d = await response.json();

  const render = (id, cls, html) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "card " + cls;
    el.innerHTML = html;
  };

  /* =========================
     NIFTY — FROZEN
  ========================= */
  render("box-nifty", "nifty", `
    <h3>NIFTY <span class="small">• LIVE</span></h3>
    <div class="value">${d.nifty.spot.toFixed(2)}</div>
    <div class="line green">
      ${d.nifty.change_points} (${d.nifty.change_percent}%)
    </div>
    <div class="small">Updated: ${d.meta.last_updated} IST</div>
  `);

  /* =========================
     VOLATILITY — FROZEN
  ========================= */
  render("box-volatility", "volatility", `
    <h3>VOLATILITY (ATR)</h3>
    <div class="value">${d.volatility.atr}</div>
    <div class="small">${d.volatility.sample_status}</div>
    <div class="line">
      <b>Choppiness:</b>
      ${d.choppiness.state} — ${d.choppiness.message}
    </div>
  `);

  /* =========================
     VWAP — FROZEN
  ========================= */
  render("box-vwap", "vwap", `
    <h3>VWAP</h3>
    <div class="line"><b>Mid:</b> ${d.vwap.mid}</div>
    <div class="line"><b>Upper:</b> ${d.vwap.upper}</div>
    <div class="line"><b>Lower:</b> ${d.vwap.lower}</div>
    <div class="line"><b>Expansion:</b> ${d.vwap.expansion}</div>
    <div class="line"><b>Position:</b> ${d.vwap.position}</div>
    <div class="line"><b>Midline:</b> ${d.vwap.midline}</div>
    <div class="small">
      15‑min candle basis ${d.vwap.basis_candle_close}
    </div>
  `);

  /* =========================
     PREVIOUS DAY — FROZEN
  ========================= */
  render("box-anchors", "anchors", `
    <h3>PREVIOUS DAY ANCHORS</h3>
    <div class="line"><b>PDH:</b> ${d.previous_day.pdh}</div>
    <div class="line"><b>PDL:</b> ${d.previous_day.pdl}</div>
    <div class="line"><b>PDC:</b> ${d.previous_day.pdc}</div>
  `);

  /* =========================
     MARKET OPEN — FROZEN
  ========================= */
  const oc = d.market_open.opening_candle;
  const gap = d.market_open.gap;

  render("box-open", "open", `
    <h3>MARKET OPEN <span class="small">FROZEN</span></h3>

    <div class="line"><b>Gap:</b> ${gap.direction} (${gap.points})</div>
    <div class="small">Frozen at ${gap.frozen_at}</div>

    <div class="line">
      <b>Opening Candle:</b>
      <span class="${oc.color === "GREEN" ? "green" : "red"}">
        ${oc.type}
      </span>
      (Size ${oc.size} pts | Body ${oc.body_pct}%)
    </div>

    <div class="line">
      <b>O</b> ${oc.ohlc.open} | <b>H</b> ${oc.ohlc.high}
    </div>
    <div class="line">
      <b>L</b> ${oc.ohlc.low} | <b>C</b> ${oc.ohlc.close}
    </div>

    <div class="line"><b>Range</b> ${oc.range}</div>
  `);

  /* =========================================================
     TREND ARCHITECT — NEW, ISOLATED, DOES NOT TOUCH FROZEN UI
  ========================================================= */
  try {
    const ta = d.trend_architect;

    render("box-trend", "trend", `
      <h3>TREND ARCHITECT <span class="small">(MOST IMPORTANT)</span></h3>

      <div class="line">
        <b>Gap Behavior:</b> ${ta.gap_behavior.status}
      </div>
      <div class="small">Frozen at ${ta.gap_behavior.frozen_at}</div>

      <div class="line">
        <b>Major Candle:</b>
        ${ta.major_candle.range} pts
        (<span class="${ta.major_candle.color === "GREEN" ? "green" : "red"}">
          ${ta.major_candle.type}
        </span>)
        @ ${ta.major_candle.time}
      </div>

      <div class="line">
        <b>Next Candle:</b>
        <span class="${ta.next_candle.color === "GREEN" ? "green" : "red"}">
          ${ta.next_candle.relation}
        </span>
      </div>

      <div class="line">
        <b>Total Distance Travelled (09:30–11:05):</b>
        <span class="${ta.distance_travelled.direction === "UP" ? "green" : "red"}">
          ${ta.distance_travelled.points} pts
        </span>
        &nbsp;|&nbsp;
        <b>Overlapping Candles:</b> ${ta.distance_travelled.overlaps}
      </div>

      <div class="line">
        <b>Market Character:</b> ${ta.market_character}
      </div>
    `);
  } catch (e) {
    render("box-trend", "trend", `
      <h3>TREND ARCHITECT</h3>
      <div class="line">Data Awaited</div>
    `);
  }

  /* =========================
     INSTITUTIONAL FLOWS — UNCHANGED
  ========================= */
  render("box-flows", "institutional", `
    <h3>INSTITUTIONAL FLOWS</h3>
    <div class="line"><b>FII:</b> —</div>
    <div class="line"><b>DII:</b> —</div>
  `);
})();
