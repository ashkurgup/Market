(async () => {
  try {
    const response = await fetch("./snapshots/market_phase1.json", {
      cache: "no-store"
    });

    if (!response.ok) throw new Error("404 JSON not found");

    const d = await response.json();

    // NIFTY
    document.getElementById("box-nifty").innerHTML = `
      <h3>NIFTY</h3>
      <div>${d.nifty.spot.toFixed(2)}</div>
      <div>${d.nifty.change_points} (${d.nifty.change_percent}%)</div>
    `;

    // ATR
    document.getElementById("box-volatility").innerHTML = `
      <h3>Volatility (ATR)</h3>
      <div>${d.volatility?.atr ?? "—"}</div>
    `;

    // VWAP
    document.getElementById("box-vwap").innerHTML = `
      <h3>VWAP</h3>
      <div>Position: ${d.vwap.position}</div>
      <div>Expansion: ${d.vwap.expansion_range}</div>
      <div>Midline: ${d.vwap.midline}</div>
    `;

    // Previous Day Anchors (LOCKED)
    document.getElementById("box-anchors").innerHTML = `
      <h3>Previous Day</h3>
      <div>PDH: ${d.previous_day.pdh}</div>
      <div>PDL: ${d.previous_day.pdl}</div>
      <div>PDC: ${d.previous_day.pdc}</div>
    `;

    // Market Open
    const mo = d.market_open;
    document.getElementById("box-open").innerHTML = mo
      ? `<h3>Market Open</h3>
         <div>Gap: ${mo.gap.direction} (${mo.gap.points})</div>
         <div>Opening Candle: ${mo.opening_candle.type}</div>`
      : `<h3>Market Open</h3><div>—</div>`;

    // Trend Architect
    document.getElementById("box-trend").innerHTML = `
      <h3>Trend Architect</h3>
      <div>Major Candle: ${d.trend_architect.major_candle.type}</div>
      <div>Next Candle: ${d.trend_architect.next_candle_relation}</div>
    `;

    // Flows
    document.getElementById("box-flows").innerHTML = `
      <h3>Institutional Flows</h3>
      <div>FII Today: —</div>
      <div>DII Today: —</div>
      <div>FII (Last 4): — | — | — | —</div>
      <div>DII (Last 4): — | — | — | —</div>
    `;

  } catch (e) {
    console.error(e);
    document.body.innerHTML =
      "<h2 style='color:red'>Failed to load market data</h2>";
  }
})();
