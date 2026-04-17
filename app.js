fetch("snapshots/market_phase1.json")
  .then(r => r.json())
  .then(d => {

    /* -------- NIFTY (LOCKED) -------- */
    const now = new Date();
    const isLive =
      (now.getHours() > 9 || (now.getHours() === 9 && now.getMinutes() >= 15)) &&
      (now.getHours() < 15 || (now.getHours() === 15 && now.getMinutes() <= 30));

    const spot = Number(d.nifty?.spot ?? 0).toFixed(2);
    const chg = Number(d.nifty?.change_points ?? 0).toFixed(1);
    const pct = Number(d.nifty?.change_percent ?? 0).toFixed(2);

    document.getElementById("box-nifty").innerHTML = `
      <h2>NIFTY <span class="small">● ${isLive ? "LIVE" : "CLOSED"}</span></h2>
      <div class="value">${spot}</div>
      <div class="line ${chg >= 0 ? "green" : "red"}">${chg} (${pct}%)</div>
      <div class="small">Updated: ${d.meta?.last_updated ?? "--"} IST</div>
    `;

    /* -------- VOLATILITY -------- */
    document.getElementById("box-volatility").innerHTML = `
      <h2>VOLATILITY (ATR)</h2>
      <div class="value">—</div>
      <div class="small">Higher ATR favors continuation over chop</div>
    `;

    /* -------- VWAP -------- */
    document.getElementById("box-vwap").innerHTML = `
      <h2>VWAP</h2>
      <div class="line tight"><b>Position:</b> ${d.vwap?.position ?? "—"}</div>
      <div class="line tight"><b>Expansion:</b> ${d.vwap?.expansion_range ?? "—"}</div>
      <div class="line tight"><b>Midline:</b> ${d.vwap?.midline ?? "—"}</div>
      <div class="small">15‑min candle basis 11:45 AM</div>
    `;

    /* -------- PREVIOUS DAY ANCHORS -------- */
    document.getElementById("box-anchors").innerHTML = `
      <h2>PREVIOUS DAY ANCHORS</h2>
      <div class="line mono"><b>PDH:</b> 24203.25</div>
      <div class="line mono"><b>PDL:</b> 24177.80</div>
      <div class="line mono"><b>PDC:</b> 24188.40</div>
    `;

    /* -------- MARKET OPEN -------- */
    document.getElementById("box-open").innerHTML = `
      <h2>MARKET OPEN <span class="small">FROZEN</span></h2>
      <div class="line"><b>Gap:</b> — (—)</div>
      <div class="small">Frozen at --</div>
      <div class="line"><b>Opening Candle:</b> —</div>
      <div class="line mono">O — | H —<br>L — | C —</div>
      <div class="line">Range —</div>
    `;

    /* -------- TREND ARCHITECT -------- */
    document.getElementById("box-trend").innerHTML = `
      <h2>TREND ARCHITECT <span class="small">FINAL</span></h2>
      <div class="line"><b>Gap Behavior:</b> Closed by 11:05 AM</div>
      <div class="line">
        <b>Major Candle:</b> 32.45 pts |
        <span class="candle-up">MARUBOZU</span>
        (Formed: 09:35 AM)
      </div>
      <div class="line">
        <b>Next Candle:</b>
        <span class="relation-opposing">OPPOSING</span>
      </div>
      <div class="line"><b>50‑pt Travel:</b> —</div>
      <div class="line"><b>Choppiness:</b> —</div>
      <div class="small">Effective from 11:00 AM</div>
    `;

    /* -------- INSTITUTIONAL FLOWS -------- */
    document.getElementById("box-flows").innerHTML = `
      <h2>INSTITUTIONAL FLOWS (NSE – Cash)</h2>
      <div class="line mono"><b>FII (Today):</b> —</div>
      <div class="line mono"><b>DII (Today):</b> —</div>
      <br>
      <div class="line mono"><b>FII (Last 4 Days):</b> | — | — | — | —</div>
      <div class="line mono"><b>DII (Last 4 Days):</b> | — | — | — | —</div>
      <div class="small">Published post‑market</div>
    `;
  });
