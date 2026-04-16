fetch("snapshots/market_phase1.json")
  .then(res => res.json())
  .then(data => {

    // Last Updated
    document.getElementById("lastUpdated").innerText =
      `Last Updated: ${data.meta.last_updated} IST`;

    // NIFTY
    if (data.nifty) {
      const cls = data.nifty.change_points >= 0 ? "up" : "down";
      document.getElementById("niftyValue").innerHTML =
        `<span class="${cls}">
          ${data.nifty.spot}
          (${data.nifty.change_points} / ${data.nifty.change_percent}%)
        </span>`;
    }

    // GLOBAL INDICES
    const globalList = document.getElementById("globalList");
    globalList.innerHTML = "";

    data.global_markets.forEach(m => {
      const cls = m.direction === "UP" ? "up" : "down";
      const li = document.createElement("li");
      li.innerHTML = `<span class="${cls}">
        ${m.name} | ${m.value}
      </span>`;
      globalList.appendChild(li);
    });

    // ATR
    document.getElementById("atrValue").innerText =
      data.volatility.atr;

    // VWAP
    document.getElementById("vwapValue").innerText =
      data.vwap.position;

   // ===== GAP STATUS
const gap = data.market_open?.gap_status;
if (gap) {
  document.getElementById("gapStatus").innerHTML =
    `Gap Status: ${gap.type} (${gap.points}) | Frozen @ ${gap.frozen_at}`;
}

// ===== OPENING CANDLE
const oc = data.market_open?.opening_candle;
if (oc) {
  document.getElementById("openingCandle").innerHTML =
    `Opening Candle: ${oc.type}<br>
     O: ${oc.ohlc.open} |
     H: ${oc.ohlc.high} |
     L: ${oc.ohlc.low} |
     C: ${oc.ohlc.close}<br>
     Range: ${oc.range} | Frozen @ ${oc.frozen_at}`;
}
    
    // TREND ARCHITECT
    const ta = data.trend_architect;
    document.getElementById("trendBlock").innerHTML = `
      Gap Behavior: ${ta.gap_behavior}<br>
      Major Candle: ${ta.major_candle.size}
      (${ta.major_candle.type}) @ ${ta.major_candle.time}<br>
      Next Candle: ${ta.next_candle_relation}<br>
      Velocity: ${ta.velocity}<br>
      Character: ${ta.market_character}<br>
      Effective: ${ta.effective_time}
    `;
  })
  .catch(err => {
    console.error(err);
    alert("Failed to load market data");
  });
