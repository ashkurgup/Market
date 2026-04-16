fetch("snapshots/market_phase1.json")
  .then(res => res.json())
  .then(data => {

    // Last Updated
    document.getElementById("lastUpdated").innerText =
      `Last Updated: ${data.meta.last_updated} IST`;

    // NIFTY
    if (data.nifty && data.nifty.spot !== undefined) {
      const cls = data.nifty.change_points >= 0 ? "up" : "down";
      document.getElementById("niftyValue").innerHTML =
        `<span class="${cls}">
          ${data.nifty.spot}
          (${data.nifty.change_points.toFixed(1)} / ${data.nifty.change_percent.toFixed(2)}%)
         </span>`;
    }

    // ATR
    if (data.volatility && data.volatility.atr !== undefined) {
      document.getElementById("atrValue").innerText =
        data.volatility.atr;
    }

    // VWAP
    if (data.vwap && data.vwap.position) {
      document.getElementById("vwapValue").innerText =
        data.vwap.position;
    }

  })
  .catch(() => {
    document.body.innerHTML = "Unable to load market data.";
  });
