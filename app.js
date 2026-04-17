(async () => {
  const safe = (fn) => {
    try { return fn(); } catch (e) { return "—"; }
  };

  const render = (id, cls, html) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "card " + cls;
    el.innerHTML = html;
  };

  /* =========================
     ALWAYS FILL ALL BOXES FIRST (DEBUG GUARD)
  ========================= */
  render("box-nifty", "nifty", "<h3>NIFTY</h3><div>Loading…</div>");
  render("box-volatility", "volatility", "<h3>VOLATILITY</h3><div>Loading…</div>");
  render("box-vwap", "vwap", "<h3>VWAP</h3><div>Loading…</div>");
  render("box-anchors", "anchors", "<h3>PREVIOUS DAY</h3><div>Loading…</div>");
  render("box-open", "open", "<h3>MARKET OPEN</h3><div>Loading…</div>");
  render("box-trend", "trend", "<h3>TREND ARCHITECT</h3><div>Loading…</div>");
  render("box-flows", "institutional", "<h3>INSTITUTIONAL FLOWS</h3><div>Loading…</div>");

  /* =========================
     DATA LOAD
  ========================= */
  const response = await fetch("./snapshots/market_phase1.json", { cache: "no-store" });
  const d = await response.json();

  /* =========================
     NIFTY
  ========================= */
  render("box-nifty", "nifty", `
    <h3>NIFTY <span class="small">• LIVE</span></h3>
    <div class="value">${safe(() => d.nifty.spot.toFixed(2))}</div>
    <div class="line green">
      ${safe(() => d.nifty.change_points)} (${safe(() => d.nifty.change_percent)}%)
    </div>
    <div class="small">Updated: ${safe(() => d.meta.last_updated)} IST</div>
  `);

  /* =========================
     VOLATILITY
  ========================= */
  render("box-volatility", "volatility", `
    <h3>VOLATILITY (ATR)</h3>
    <div class="value">${safe(() => d.volatility.atr)}</div>
    <div class="line">${safe(() => d.choppiness.state)} — ${safe(() => d.choppiness.message)}</div>
  `);

  /* =========================
     VWAP
  ========================= */
  render("box-vwap", "vwap", `
    <h3>VWAP</h3>
    <div class="line">Mid: ${safe(() => d.vwap.mid)}</div>
    <div class="line">Upper: ${safe(() => d.vwap.upper)}</div>
    <div class="line">Lower: ${safe(() => d.vwap.lower)}</div>
    <div class="line">Expansion: ${safe(() => d.vwap.expansion)}</div>
    <div class="line">Position: ${safe(() => d.vwap.position)}</div>
  `);

  /* =========================
     PREVIOUS DAY ANCHORS
  ========================= */
  render("box-anchors", "anchors", `
    <h3>PREVIOUS DAY ANCHORS</h3>
    <div class="line">PDH: ${safe(() => d.previous_day.pdh)}</div>
    <div class="line">PDL: ${safe(() => d.previous_day.pdl)}</div>
    <div class="line">PDC: ${safe(() => d.previous_day.pdc)}</div>
  `);

  /* =========================
     MARKET OPEN
  ========================= */
  render("box-open", "open", `
    <h3>MARKET OPEN (FROZEN)</h3>
    <div class="line">Gap: ${safe(() => d.market_open.gap.direction)} (${safe(() => d.market_open.gap.points)})</div>
    <div class="line">
      Opening Candle:
      ${safe(() => d.market_open.opening_candle.type)}
      (${safe(() => d.market_open.opening_candle.size)} pts | ${safe(() => d.market_open.opening_candle.body_pct)}%)
    </div>
  `);

  /* =========================
     TREND ARCHITECT
  ========================= */
  render("box-trend", "trend", `
    <h3>TREND ARCHITECT</h3>
    <div class="line">Gap: ${safe(() => d.trend_architect.gap_behavior.status)}</div>
    <div class="line">Major Candle: ${safe(() => d.trend_architect.major_candle.type)} @ ${safe(() => d.trend_architect.major_candle.time)}</div>
    <div class="line">Next: ${safe(() => d.trend_architect.next_candle.relation)}</div>
    <div class="line">${safe(() => d.trend_architect.market_character)}</div>
  `);

  /* =========================
     INSTITUTIONAL FLOWS
  ========================= */
  render("box-flows", "institutional", `
    <h3>INSTITUTIONAL FLOWS</h3>
    <div class="line">FII: —</div>
    <div class="line">DII: —</div>
  `);
})();
