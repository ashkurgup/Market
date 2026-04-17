fetch("snapshots/market_phase1.json")
  .then(r => r.json())
  .then(d => {

    document.getElementById("lastUpdated").innerText =
      `Last Updated: ${d.meta.last_updated} IST`;

    const n = d.nifty;
    document.getElementById("niftyValue").innerHTML =
      `${n.spot.toFixed(2)} (${n.change_points.toFixed(2)} / ${n.change_percent.toFixed(2)}%)`;

    document.getElementById("atrValue").innerText =
      d.volatility.atr.toFixed(1);

    document.getElementById("vwapPosition").innerText = d.vwap.position;
    document.getElementById("vwapRange").innerText = d.vwap.expansion_range;
    document.getElementById("vwapMid").innerText = d.vwap.midline;

    const mo = d.market_open;
    if (mo) {
      document.getElementById("gapStatus").innerText =
        `${mo.gap_status.type} (${mo.gap_status.points})`;

      const oc = mo.opening_candle;
      document.getElementById("openingCandle").innerText =
        `${oc.type} | O ${oc.ohlc.open} H ${oc.ohlc.high} L ${oc.ohlc.low} C ${oc.ohlc.close}`;
    }

    const t = d.trend_architect;
    if (t) {
      document.getElementById("trendBlock").innerText =
        `${t.market_character} | ${t.gap_behavior}`;
    }

    const a = d.previous_day;
    document.getElementById("anchorsValue").innerText =
      `PDH ${a.pdh} | PDL ${a.pdl} | PDC ${a.pdc}`;

    document.getElementById("fiiDiiValue").innerText =
      d.institutional_flows.status;
  });
