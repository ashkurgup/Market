fetch("snapshots/market_phase1.json")
  .then(res => res.json())
  .then(data => {

    document.getElementById("updated").innerText =
      `Last Updated: ${data.meta.last_updated} IST`;

    if (data.nifty?.spot) {
      document.getElementById("nifty").innerHTML =
        `${data.nifty.spot} (${data.nifty.change_points.toFixed(1)} / ${data.nifty.change_percent.toFixed(2)}%)`;
    } else {
      document.getElementById("nifty").innerText = "Data Awaited";
    }

    document.getElementById("atr").innerText =
      data.volatility?.atr ?? "Data Awaited";

    document.getElementById("vwap").innerText =
      data.vwap?.position ?? "Data Awaited";

  })
  .catch(err => {
    console.error(err);
    document.body.innerHTML = "Failed to load market data.";
  });
