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
     VOLATILITY
  ======================= */
  render("box-volatility", "volatility", `
    <h3>VOLATILITY (ATR)</h3>
    <div class="value">${safe(d.volatility?.atr)}</div>
    <div class="small">${safe(d.volatility?.sample_status)}</div>
    <div class="line">
      <b>Choppiness:</b>
      ${safe(d.choppiness?.state)} — ${safe(d.choppiness?.message)}
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
     PREVIOUS DAY ANCHORS
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
const ohlc = oc.ohlc ?? {};

render("box-open", "open", `
  <h3>MARKET OPEN <span class="small">FROZEN</span></h3>

  <div class="line">
    <b>Gap:</b> ${safe(gap.direction)} (${safe(gap.points)})
  </div>
  <div class="small">Frozen at ${safe(gap.frozen_at)}</div>

  <div class="line">
    <b>Opening Candle:</b>
    <span class="${oc.color === "GREEN" ? "green" : "red"}">${safe(oc.type)}</span>
    (Size ${safe(oc.size)} pts | Body ${safe(oc.body_pct)}%)
  </div>

  <div class="line">
    <b>O:</b> ${safe(ohlc.open)} |
    <b>H:</b> ${safe(ohlc.high)}
  </div>
  <div class="line">
    <b>L:</b> ${safe(ohlc.low)} |
    <b>C:</b> ${safe(ohlc.close)}
  </div>
  <div class="line">
    <b>Range:</b> ${safe(oc.range)} pts
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
   INSTITUTIONAL FLOWS (MANUAL)
======================= */
const flows = d.institutional_flows ?? {};

render("box-flows", "institutional manual", `
  <h3>INSTITUTIONAL FLOWS <span class="small">(Manual)</span></h3>

  <div class="line">
    <b>As of ${safe(flows.as_of)}:</b>
    FII ${safe(flows.today?.fii)} | DII ${safe(flows.today?.dii)}
  </div>

  <div class="small">
    <b>FII (Last 4):</b>
    ${flows.history_4d?.fii?.map(x => x.value).join(" | ") ?? "—"}
  </div>

  <div class="small">
    <b>DII (Last 4):</b>
    ${flows.history_4d?.dii?.map(x => x.value).join(" | ") ?? "—"}
  </div>
`);

/* =======================
   PCR (MANUAL + INTERPRETATION)
======================= */
const pcrVal = d.pcr?.value;

let pcrText = "—";
if (typeof pcrVal === "number") {
  if (pcrVal < 0.8) {
    pcrText = "Bearish options positioning (excess calls writing)";
  } else if (pcrVal <= 1.1) {
    pcrText = "Balanced to mildly bullish options positioning";
  } else {
    pcrText = "Bullish options positioning (excess puts writing)";
  }
}

render("box-pcr", "pcr manual", `
  <h3>PCR (OPTIONS) <span class="small">(Manual)</span></h3>

  <div class="value">${safe(pcrVal)}</div>

  <div class="small">
    As of ${safe(d.pcr?.as_of)}
  </div>

  <div class="line">
    <b>Interpretation:</b> ${pcrText}
  </div>
`);
})();
