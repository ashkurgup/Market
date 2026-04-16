fetch("snapshots/market_phase1.json")
  .then(res => {
    if (!res.ok) throw new Error("JSON not found");
    return res.json();
  })
  .then(data => {

    // LAST UPDATED
    document.getElementById("lastUpdated").innerText =
      `Last Updated: ${data.meta?.last_updated ?? "--"} IST`;

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
    (data.global_markets ?? []).forEach(m => {
      const li = document.createElement("li");
      li.innerText = `${m.name} | ${m.value}`;
      globalList.appendChild(li);
    });

    // ATR
    document.getElementById("atrValue").innerText =
      data.volatility?.atr ?? "—";

    // VWAP
    document.getElementById("vwapPosition").innerText =
      data.vwap?.position ?? "—";
    document.getElementById("vwapRange").innerText =
      data.vwap?.expansion_range ?? "—";
    document.getElementById("vwapMid").innerText =
      data.vwap?.midline ?? "—";

    // GAP & OPEN
    document.getElementById("gapStatus").innerText =
      data.market_open?.gap_status?.type ?? "Data Awaited";

    document.getElementById("openingCandle").innerText =
      data.market_open?.opening_candle?.type ?? "Data Awaited";

    // TREND ARCHITECT
    document.getElementById("trendBlock").innerText =
      data.trend_architect?.market_character ?? "Data Awaited";

    // ANCHORS
    document.getElementById("anchorsValue").innerText =
      data.previous_day
        ? `PDH ${data.previous_day.pdh} | PDL ${data.previous_day.pdl} | PDC ${data.previous_day.pdc}`
        : "—";

    // FII / DII
    document.getElementById("fiiDiiValue").innerText =
      data.institutional_flows?.status ?? "Awaiting institutional data";
  })
  .catch(err => {
    console.warn("Market data unavailable:", err.message);
  });
