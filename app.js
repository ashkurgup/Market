fetch("snapshots/market_phase1.json")
  .then(r => r.json())
  .then(d => {

    // Last updated
    document.getElementById("lastUpdated").innerText =
      "Last Updated: " + d.meta.last_updated + " IST";

    // NIFTY
    const n = d.nifty;
    document.getElementById("niftyValue").innerHTML =
      `${n.spot.toFixed(2)} (${n.change_points.toFixed(2)} / ${n.change_percent.toFixed(2)}%)`;

    // ATR
    if (d.volatility?.atr !== undefined) {
      document.getElementById("atrValue").innerText =
        d.volatility.atr.toFixed(1);
    }

    // VWAP
    const v = d.vwap;
    document.getElementById("vwapPosition").innerText = v.position;
    document.getElementById("vwapRange").innerText =
      Number(v.expansion_range).toFixed(1);
    document.getElementById("vwapMid").innerText = v.midline;

    // Market Open
    const mo = d.market_open;
    if (mo) {
      document.getElementById("gapStatus").innerText =
        `${mo.gap_status.type} (${mo.gap_status.points.toFixed(2)})`;

      const oc = mo.opening_candle;
      document.getElementById("openingCandle").innerText =
        `${oc.type} | O ${oc.ohlc.open} H ${oc.ohlc.high} L ${oc.ohlc.low} C ${oc.ohlc.close}`;
    }

    // Trend Architect
    if (d.trend_architect) {
      document.getElementById("trendBlock").innerText =
        d.trend_architect.market_character;
    }

    // Anchors
    const a = d.previous_day;
    document.getElementById("anchorsValue").innerText =
      `PDH ${a.pdh.toFixed(2)} | PDL ${a.pdl.toFixed(2)} | PDC ${a.pdc.toFixed(2)}`;

    // Institutional flows
    document.getElementById("fiiDiiValue").innerText =
      d.institutional_flows.status;
  });
