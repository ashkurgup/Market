(async () => {
  const r = await fetch("./snapshots/market_phase1.json", { cache: "no-store" });
  const d = await r.json();

  /* NIFTY */
  box("box-nifty", "nifty", `
    <h3>NIFTY <span class="small">• LIVE</span></h3>
    <div class="value">${d.nifty.spot.toFixed(2)}</div>
    <div class="line green">${d.nifty.change_points} (${d.nifty.change_percent}%)</div>
    <div class="small">Updated: ${d.meta.last_updated} IST</div>
  `);

  /* ATR + Reliability */
  box("box-volatility", "volatility", `
    <h3>VOLATILITY (ATR)</h3>
    <div class="value">
      ${d.volatility.atr}
      <span class="small">(${d.volatility.sample_status})</span>
    </div>
    <div class="line">
      <strong>Choppiness:</strong>
      ${d.choppiness.state} — ${d.choppiness.message}
    </div>
    <div class="small">Reliable from ${d.volatility.reliable_from} IST</div>
  `);

  /* VWAP */
  box("box-vwap", "vwap", `
    <h3>VWAP</h3>
    <div class="line"><b>Position:</b> ${d.vwap.position}</div>
    <div class="line"><b>Expansion:</b> ${d.vwap.expansion_range}</div>
    <div class="line green"><b>Midline:</b> ${d.vwap.midline}</div>
    <div class="small">15‑min candle basis ${d.vwap.basis_candle_close}</div>
  `);

  /* PREVIOUS DAY */
  box("box-anchors", "anchors", `
    <h3>PREVIOUS DAY ANCHORS</h3>
    <div class="line"><b>PDH:</b> ${d.previous_day.pdh}</div>
    <div class="line"><b>PDL:</b> ${d.previous_day.pdl}</div>
    <div class="line"><b>PDC:</b> ${d.previous_day.pdc}</div>
  `);

  /* MARKET OPEN */
  box("box-open", "open", `
    <h3>MARKET OPEN <span class="small">FROZEN</span></h3>
    <div class="line"><b>Gap:</b> — (—)</div>
    <div class="line"><b>Opening Candle:</b> —</div>
    <div class="line">O — | H —</div>
    <div class="line">L — | C —</div>
    <div class="line">Range —</div>
  `);

  /* TREND ARCHITECT */
  box("box-trend", "trend", `
    <h3>TREND ARCHITECT <span class="small">FINAL</span></h3>
    <div class="line"><b>Gap Behavior:</b> Closed by 11:05 AM</div>
    <div class="line">
      <b>Major Candle:</b> 32.45 pts |
      <span class="green bold">MARUBOZU</span>
      <span class="small">(09:35 AM)</span>
    </div>
    <div class="line"><b>Next Candle:</b> <span class="red bold">OPPOSING</span></div>
    <div class="line"><b>50‑pt Travel:</b> —</div>
    <div class="line"><b>Choppiness:</b> —</div>
    <div class="small">Effective from 11:00 AM</div>
  `);

  /* FLOWS */
  box("box-flows", "institutional", `
    <h3>INSTITUTIONAL FLOWS (NSE – Cash)</h3>
    <div class="line"><b>FII (Today):</b> —</div>
    <div class="line"><b>DII (Today):</b> —</div>
    <div class="line"><b>FII (Last 4 Days):</b> | — | — | — | —</div>
    <div class="line"><b>DII (Last 4 Days):</b> | — | — | — | —</div>
    <div class="small">Published post‑market</div>
  `);

  function box(id, cls, html) {
    const el = document.getElementById(id);
    el.className = "card " + cls;
    el.innerHTML = html;
  }
})();
