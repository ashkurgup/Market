fetch("snapshots/market_phase1.json")
  .then(response => {
    if (!response.ok) {
      throw new Error("HTTP error " + response.status);
    }
    return response.json();
  })
  .then(data => {

    // Last Updated
    document.getElementById("lastUpdated").innerText =
      `Last Updated: ${data.meta.last_updated} IST`;

    // NIFTY
    const nifty = data.nifty;
    if (nifty) {
      const cls = nifty.change_points >= 0 ? "up" : "down";
      document.getElementById("niftyValue").innerHTML =
        `<span class="${cls}">
          ${nifty.spot} (${nifty.change_points} / ${nifty.change_percent}%)
        </span>`;
    }

    // ATR
    document.getElementById("atrValue").innerText =
      data.volatility?.atr ?? "Data Awaited";

    // VWAP
    document.getElementById("vwapValue").innerText =
      data.vwap?.position ?? "Data Awaited";
  })
  .catch(error => {
    console.error(error);
    alert("Failed to load market data. Check console.");
  });
