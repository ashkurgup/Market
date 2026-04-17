(async () => {
  const response = await fetch("./snapshots/market_phase1.json", { cache: "no-store" });
  const marketData = await response.json();

  const render = (id, cls, html) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "card " + cls;
    el.innerHTML = html;
  };

  /* =========================
     NIFTY (FROZEN UI)
  ========================= */
  render("box-nifty", "nifty", `
    <h3>NIFTY <span class="small">• LIVE</span></h3>
    <div class="value">${marketData.nifty.spot.toFixed(2)}</div>
    <div class="line green">
      ${marketData.nifty.change_points} (${marketData.nifty.change_percent}%)
    </div>
    <div class="small">Updated: ${marketData.meta.last_updated} IST</div>
  `);

  /* =========================
     VOLATILITY (FROZEN UI)
  ========================= */
  render("box-volatility", "volatility", `
    <h3>VOLATILITY (ATR)</h3>
    <div class="value">${marketData.volatility.atr}</div>
    <div class="small">${marketData.volatility.sample_status}</div>
    <div class="line">
      <b>Choppiness:</b>
      ${marketData.choppiness.state} — ${marketData.choppiness.message}
    </div>
  `);

  /* =========================
     VWAP (FROZEN UI)
  ========================= */
  render("box-vwap", "vwap", `
    <h3>VWAP</h3>
    <div class="line"><b>Mid:</b> ${marketData.vwap.mid}</div>
    <div class="line"><b>Upper:</b> ${marketData.vwap.upper}</div>
    <div class="line"><b>Lower:</b> ${marketData.vwap.lower}</div>
    <div class="line"><b>Expansion:</b> ${marketData.vwap.expansion}</div>
    <div class="line"><b>Position:</b> ${marketData.vwap.position}</div>
    <div class="line"><b>Midline:</b> ${marketData.vwap.midline}</div>
    <div class="small">
      15‑min candle basis ${marketData.vwap.basis_candle_close}
    </div>
  `);

  /* =========================
     PREVIOUS DAY ANCHORS (FROZEN UI)
  ========================= */
  render("box-anchors", "anchors", `
    <h3>PREVIOUS DAY ANCHORS</h3>
    <div class="line"><b>PDH:</b> ${marketData.previous_day.pdh}</div>
    <div class="line"><b>PDL:</b> ${marketData.previous_day.pdl}</div>
    <div class="line"><b>PDC:</b> ${marketData.previous_day.pdc}</div>
  `);

  /* =========================
     MARKET OPEN (FROZEN UI)
  ========================= */
  const oc = marketData.market_open.opening_candle;
  const gap = marketData.market_open.gap;

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
     TREND ARCHITECT (NEW — ISOLATED, DOES NOT TOUCH OTHERS)
  ========================================================= */
  try {
    const ta = marketData.trend_architect;
    const el = document.getElementById("box-trend");

    el.className = "card trend";
    el.innerHTML = `
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
    `;
  } catch (e) {
    document.getElementById("box-trend").innerHTML =
      "<h3>TREND ARCHITECT</h3><div>Data Awaited</div>";
  }

  /* =========================
     INSTITUTIONAL FLOWS (UNCHANGED)
  ========================= */
  render("box-flows", "institutional", `
    <h3>INSTITUTIONAL FLOWS</h3>
    <div class="line"><b>FII:</b> —</div>
    <div class="line"><b>DII:</b> —</div>
  `);
})();
