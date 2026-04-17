fetch("snapshots/market_phase1.json")
  .then(r => r.json())
  .then(d => {
fetch("snapshots/market_phase1.json")
  .then(r => r.json())
  .then(d => {

    /* BOX 1 — NIFTY */
    const live = d.meta.session_status === "OPEN" ? "LIVE" : "CLOSED";
    document.getElementById("box-nifty").innerHTML = `
      <h2>NIFTY <span class="small">● ${live}</span></h2>
      <div class="value">${d.nifty.spot}</div>
      <div class="line ${d.nifty.change_points >= 0 ? 'green' : 'red'}">
        ${d.nifty.change_points} (${d.nifty.change_percent}%)
      </div>
      <div class="small">Updated: ${d.meta.last_updated} IST</div>
    `;

    /* BOX 2 — VOLATILITY */
    document.getElementById("box-volatility").innerHTML = `
      <h2>VOLATILITY (ATR)</h2>
      <div class="value">${d.volatility.atr}</div>
      <div class="small">Higher ATR favors continuation over chop</div>
    `;

    /* BOX 3 — VWAP */
    document.getElementById("box-vwap").innerHTML = `
      <h2>VWAP</h2>
      <div class="line"><b>Position:</b> ${d.vwap.position}</div>
      <div class="line"><b>Expansion:</b> ${d.vwap.expansion_range}</div>
      <div class="line"><b>Midline:</b> ${d.vwap.midline}</div>
      <div class="small">15‑min candle basis</div>
    `;

    /* BOX 4 — MARKET OPEN */
    const mo = d.market_open;
    document.getElementById("box-open").innerHTML = `
      <h2>MARKET OPEN <span class="small">FROZEN</span></h2>
      <div class="line"><b>Gap:</b> ${mo.gap_status.type} (${mo.gap_status.points})</div>
      <div class="small">Frozen at ${mo.gap_status.frozen_at}</div>

      <div class="line"><b>Opening Candle:</b> ${mo.opening_candle.type}</div>
      <div class="line mono">
        O ${mo.opening_candle.ohlc.open} |
        H ${mo.opening_candle.ohlc.high}<br>
        L ${mo.opening_candle.ohlc.low} |
        C ${mo.opening_candle.ohlc.close}
      </div>
      <div class="small">Range ${mo.opening_candle.range} | Frozen at ${mo.opening_candle.frozen_at}</div>
    `;

    /* BOX 5 — TREND ARCHITECT */
    const ta = d.trend_architect;
    document.getElementById("box-trend").innerHTML = `
      <h2>TREND ARCHITECT <span class="small">FINAL</span></h2>
      <div class="line"><b>Gap Behavior:</b> ${ta.gap_behavior}</div>
      <div class="line"><b>Major Candle:</b> ${ta.major_candle.size} pts | ${ta.major_candle.type}</div>
      <div class="small">Time ${ta.major_candle.time}</div>
      <div class="line"><b>Next Candle:</b> ${ta.next_candle_relation}</div>
      <div class="line"><b>50‑pt Travel:</b> ${ta.travel}</div>
      <div class="line"><b>Choppiness:</b> ${ta.choppiness}</div>
      <div class="small">Effective from ${ta.effective_time}</div>
    `;

    /* BOX 6 — PDH */
    document.getElementById("box-pdh").innerHTML = `
      <h2>PREVIOUS DAY ANCHORS</h2>
      <div class="line mono">PDH: ${d.previous_day.pdh}</div>
      <div class="line mono">PDL: ${d.previous_day.pdl}</div>
      <div class="line mono">PDC: ${d.previous_day.pdc}</div>
    `;

    /* BOX 7 — FLOWS */
    const f = d.institutional_flows;
    document.getElementById("box-flows").innerHTML = `
      <h2>INSTITUTIONAL FLOWS (NSE – Cash)</h2>
      <div class="line mono">FII (Today): ${f.fii_today}</div>
      <div class="line mono">DII (Today): ${f.dii_today}</div>
      <br>
      <div class="line mono">FII (Last 5 Days): | ${f.fii_minus.join(" | ")}</div>
      <div class="line mono">DII (Last 5 Days): | ${f.dii_minus.join(" | ")}</div>
      <div class="small">Published post‑market</div>
    `;
  })
  .catch(e => {
    document.body.innerHTML = "<h2 style='color:red'>Failed to load market data</h2>";
    console.error(e);
  });
    /* BOX 1 — NIFTY */
    const live = d.meta.session_status === "OPEN" ? "LIVE" : "CLOSED";
    document.getElementById("box-nifty").innerHTML = `
      <h2>NIFTY <span class="small">● ${live}</span></h2>
      <div class="value">${d.nifty.spot}</div>
      <div class="line ${d.nifty.change_points >= 0 ? 'green' : 'red'}">
        ${d.nifty.change_points} (${d.nifty.change_percent}%)
      </div>
      <div class="small">Updated: ${d.meta.last_updated} IST</div>
    `;

    /* BOX 2 — VOLATILITY */
    document.getElementById("box-volatility").innerHTML = `
      <h2>VOLATILITY (ATR)</h2>
      <div class="value">${d.volatility.atr}</div>
      <div class="small">Higher ATR favors continuation over chop</div>
    `;

    /* BOX 3 — VWAP */
    document.getElementById("box-vwap").innerHTML = `
      <h2>VWAP</h2>
      <div class="line"><b>Position:</b> ${d.vwap.position}</div>
      <div class="line"><b>Expansion:</b> ${d.vwap.expansion_range}</div>
      <div class="line"><b>Midline:</b> ${d.vwap.midline}</div>
      <div class="small">15‑min candle basis</div>
    `;

    /* BOX 4 — MARKET OPEN */
    const mo = d.market_open;
    document.getElementById("box-open").innerHTML = `
      <h2>MARKET OPEN <span class="small">FROZEN</span></h2>
      <div class="line"><b>Gap:</b> ${mo.gap_status.type} (${mo.gap_status.points})</div>
      <div class="small">Frozen at ${mo.gap_status.frozen_at}</div>

      <div class="line"><b>Opening Candle:</b> ${mo.opening_candle.type}</div>
      <div class="line mono">
        O ${mo.opening_candle.ohlc.open} |
        H ${mo.opening_candle.ohlc.high}<br>
        L ${mo.opening_candle.ohlc.low} |
        C ${mo.opening_candle.ohlc.close}
      </div>
      <div class="small">Range ${mo.opening_candle.range} | Frozen at ${mo.opening_candle.frozen_at}</div>
    `;

    /* BOX 5 — TREND ARCHITECT */
    const ta = d.trend_architect;
    document.getElementById("box-trend").innerHTML = `
      <h2>TREND ARCHITECT <span class="small">FINAL</span></h2>
      <div class="line"><b>Gap Behavior:</b> ${ta.gap_behavior}</div>
      <div class="line"><b>Major Candle:</b> ${ta.major_candle.size} pts | ${ta.major_candle.type}</div>
      <div class="small">Time ${ta.major_candle.time}</div>
      <div class="line"><b>Next Candle:</b> ${ta.next_candle_relation}</div>
      <div class="line"><b>50‑pt Travel:</b> ${ta.travel}</div>
      <div class="line"><b>Choppiness:</b> ${ta.choppiness}</div>
      <div class="small">Effective from ${ta.effective_time}</div>
    `;

    /* BOX 6 — PDH LOCKED */
    document.getElementById("box-pdh").innerHTML = `
      <h2>PREVIOUS DAY ANCHORS</h2>
      <div class="line mono">PDH: ${d.previous_day.pdh}</div>
      <div class="line mono">PDL: ${d.previous_day.pdl}</div>
      <div class="line mono">PDC: ${d.previous_day.pdc}</div>
    `;

    /* BOX 7 — FLOWS FINAL FORMAT */
    const f = d.institutional_flows;
    document.getElementById("box-flows").innerHTML = `
      <h2>INSTITUTIONAL FLOWS (NSE – Cash)</h2>
      <div class="line mono">FII (Today): ${f.fii_today}</div>
      <div class="line mono">DII (Today): ${f.dii_today}</div>
      <br>
      <div class="line mono">FII (Last 5 Days): | ${f.fii_minus.join(" | ")}</div>
      <div class="line mono">DII (Last 5 Days): | ${f.dii_minus.join(" | ")}</div>
      <div class="small">Published post‑market</div>
    `;
  });
