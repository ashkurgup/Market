(async function () {
  try {
    // ✅ THIS PATH IS CRITICAL
    const resp = await fetch("./snapshots/market_phase1.json", { cache: "no-store" });
    if (!resp.ok) throw new Error("JSON fetch failed");
    const d = await resp.json();

    /* ---------- NIFTY ---------- */
    document.getElementById("box-nifty").innerHTML = `
      <h2>NIFTY <span class="small">● LIVE</span></h2>
      <div class="value">${d.nifty.spot.toFixed(2)}</div>
      <div class="line green">${d.nifty.change_points} (${d.nifty.change_percent}%)</div>
      <div class="small">Updated: ${d.meta.last_updated} IST</div>
    `;

    /* ---------- VOLATILITY ---------- */
    document.getElementById("box-volatility").innerHTML = `
      <h2>VOLATILITY (ATR)</h2>
      <div class="value">${d.volatility?.atr ?? "—"}</div>
      <div class="small">Higher ATR favors continuation over chop</div>
    `;

    /* ---------- VWAP ---------- */
    document.getElementById("box-vwap").innerHTML = `
      <h2>VWAP</h2>
      <div class="line"><b>Position:</b> ${d.vwap.position}</div>
      <div class="line"><b>Expansion:</b> ${d.vwap.expansion_range}</div>
      <div class="line"><b>Midline:</b> ${d.vwap.midline}</div>
      <div class="small">15‑min candle basis</div>
    `;

    /* ---------- PREVIOUS DAY ---------- */
    document.getElementById("box-anchors").innerHTML = `
      <h2>PREVIOUS DAY ANCHORS</h2>
      <div class="line mono"><b>PDH:</b> ${d.previous_day.pdh}</div>
      <div class="line mono"><b>PDL:</b> ${d.previous_day.pdl}</div>
      <div class="line mono"><b>PDC:</b> ${d.previous_day.pdc}</div>
    `;

    /* ---------- MARKET OPEN ---------- */
    document.getElementById("box-open").innerHTML = `
      <h2>MARKET OPEN <span class="small">FROZEN</span></h2>
      <div class="line">Gap: — (—)</div>
      <div class="small">Frozen at --</div>
      <div class="line">Opening Candle: —</div>
      <div class="line mono">O — | H —<br>L — | C —</div>
      <div class="line">Range —</div>
    `;

    /* ---------- TREND ARCHITECT ---------- */
    document.getElementById("box-trend").innerHTML = `
      <h2>TREND ARCHITECT <span class="small">FINAL</span></h2>
      <div class="line">Gap Behavior: Closed by 11:05 AM</div>
      <div class="line">Major Candle: 32.45 pts | <span class="green">MARUBOZU</span> (09:35 AM)</div>
      <div class="line">Next Candle: <span class="red">OPPOSING</span></div>
      <div class="line">50‑pt Travel: —</div>
      <div class="line">Choppiness: —</div>
    `;

    /* ---------- FLOWS ---------- */
    document.getElementById("box-flows").innerHTML = `
      <h2>INSTITUTIONAL FLOWS</h2>
      <div class="line mono"><b>FII (Today):</b> —</div>
      <div class="line mono"><b>DII (Today):</b> —</div>
      <div class="line mono"><b>FII (Last 4 Days):</b> | — | — | — | —</div>
      <div class="line mono"><b>DII (Last 4 Days):</b> | — | — | — | —</div>
    `;

  } catch (e) {
    console.error(e);
    document.body.innerHTML = "<h2 style='color:red'>Failed to load market data</h2>";
  }
})();
