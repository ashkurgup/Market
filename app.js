(async () => {
  const response = await fetch("./snapshots/market_phase1.json", { cache: "no-store" });
  const d = await response.json();

  const safe = (v, fb = "—") => (v === undefined || v === null ? fb : v);

  const render = (id, cls, html) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "card " + cls;
    el.innerHTML = html;
  };

  /* =======================
     NIFTY
  ======================= */
  render("box-nifty", "nifty", `
    <h3>NIFTY <span class="small">• LIVE</span></h3>
    <div class="value">${d.nifty.spot.toFixed(2)}</div>
    <div class="line green">${d.nifty.change_points} (${d.nifty.change_percent}%)</div>
    <div class="small">Updated: ${d.meta.last_updated} IST</div>
  `);

  /* =======================
     VOLATILITY + CHOPPINESS
  ======================= */
  render("box-volatility", "volatility", `
    <h3>VOLATILITY (ATR)</h3>
    <div class="value">${safe(d.volatility?.atr)}</div>
    <div class="small">${safe(d.volatility?.sample_status)}</div>
    <div class="line">
      <b>Choppiness:</b> ${safe(d.choppiness?.state)} — ${safe(d.choppiness?.message)}
    </div>
  `);

  /* =======================
     VWAP
  ======================= */
  render("box-vwap", "vwap", `
    <h3>VWAP</h3>
    <div class="line"><b>Mid:</b> ${safe(d.vwap?.mid)}</div>
    <div class="line"><b>Upper:</b> ${safe(d.vwap?.upper)}</div>
    <div class="line"><b>Lower:</b> ${safe(d.vwap?.lower)}</div>
    <div class="line"><b>Expansion:</b> ${safe(d.vwap?.expansion)}</div>
    <div class="line"><b>Position:</b> ${safe(d.vwap?.position)}</div>
    <div class="line"><b>Midline:</b> ${safe(d.vwap?.midline)}</div>
    <div class="small">15‑min candle basis ${safe(d.vwap?.basis_candle_close)}</div>
  `);

  /* =======================
     PREVIOUS DAY
  ======================= */
  render("box-anchors", "anchors", `
    <h3>PREVIOUS DAY ANCHORS</h3>
    <div class="line"><b>PDH:</b> ${safe(d.previous_day?.pdh)}</div>
    <div class="line"><b>PDL:</b> ${safe(d.previous_day?.pdl)}</div>
    <div class="line"><b>PDC:</b> ${safe(d.previous_day?.pdc)}</div>
  `);

  /* =======================
     MARKET OPEN
  ======================= */
  const gap = d.market_open?.gap ?? {};
  const oc = d.market_open?.opening_candle ?? {};

  render("box-open", "open", `
    <h3>MARKET OPEN <span class="small">FROZEN</span></h3>
    <div class="line"><b>Gap:</b> ${safe(gap.direction)} (${safe(gap.points)})</div>
    <div class="small">Frozen at ${safe(gap.frozen_at)}</div>
    <div class="line">
      <b>Opening Candle:</b>
      <span class="${oc.color === "GREEN" ? "green" : "red"}">${safe(oc.type)}</span>
      (Size ${safe(oc.size)} pts | Body ${safe(oc.body_pct)}%)
    </div>
  `);

  /* =======================
     TREND ARCHITECT
  ======================= */
  const ta = d.trend_architect ?? {};

  render("box-trend", "trend", `
    <h3>TREND ARCHITECT <span class="small">(MOST IMPORTANT)</span></h3>
    <div class="line"><b>Gap Behavior:</b> ${safe(ta.gap_behavior?.status)}</div>
    <div class="small">Frozen at ${safe(ta.gap_behavior?.frozen_at)}</div>

    <div class="line">
      <b>Major Candle:</b>
      ${safe(ta.major_candle?.range)} pts
      (<span class="${ta.major_candle?.color === "GREEN" ? "green" : "red"}">
        ${safe(ta.major_candle?.type)}
      </span>)
      @ ${safe(ta.major_candle?.time)}
    </div>

    <div class="line"><b>Next Candle:</b> ${safe(ta.next_candle?.relation)}</div>

    <div class="line">
      <b>Total Distance:</b> ${safe(ta.distance_travelled?.points)} pts |
      <b>Overlaps:</b> ${safe(ta.distance_travelled?.overlaps)} |
      <b>Small candles:</b> ${safe(ta.distance_travelled?.small_candles)}
    </div>

    <div class="line"><b>Market Character:</b> ${safe(ta.market_character)}</div>
  `);

  /* =======================
     INSTITUTIONAL FLOWS
  ======================= */
  const flows = d.institutional_flows ?? {};

  const fmt = v =>
    v > 0 ? `<span class="green">+${v}</span>` :
    v < 0 ? `<span class="red">${v}</span>` : "0";

  const hist = (arr = []) =>
    arr.map(x => `${x.day}: ${fmt(x.value)}`).join(" | ");

  render("box-flows", "institutional", `
    <h3>INSTITUTIONAL FLOWS</h3>

    <div class="line">
      <b>Today (${safe(flows.as_of)}):</b>
      FII ${fmt(flows.today?.fii)} |
      DII ${fmt(flows.today?.dii)}
    </div>

    <div class="small">
      <b>FII (Last 4):</b> ${hist(flows.history_4d?.fii)}
    </div>

    <div class="small">
      <b>DII (Last 4):</b> ${hist(flows.history_4d?.dii)}
    </div>
  `);
})();
``
