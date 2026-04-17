fetch("snapshots/market_phase1.json")
  .then(r => r.json())
  .then(d => {

    /* ---------- TIME BASED LIVE / CLOSED ---------- */
    const now = new Date();
    const istHour = now.getHours();
    const istMin = now.getMinutes();
    const isLive =
      (istHour > 9 || (istHour === 9 && istMin >= 15)) &&
      (istHour < 15 || (istHour === 15 && istMin <= 30));

    const liveStatus = isLive ? "LIVE" : "CLOSED";

    /* ---------- BOX 1 : NIFTY ---------- */
    const spot = Number(d.nifty?.spot ?? 0).toFixed(2);
    const chg = Number(d.nifty?.change_points ?? 0).toFixed(1);
    const pct = Number(d.nifty?.change_percent ?? 0).toFixed(2);
    const chgClass = chg >= 0 ? "green" : "red";

    document.getElementById("box-nifty").innerHTML = `
      <h2>NIFTY <span class="small">● ${liveStatus}</span></h2>
      <div class="value">${spot}</div>
      <div class="line ${chgClass}">${chg} (${pct}%)</div>
      <div class="small">Updated: ${d.meta?.last_updated ?? "--"} IST</div>
    `;

    /* ---------- BOX 2 : VOLATILITY ---------- */
    document.getElementById("box-volatility").innerHTML = `
      <h2>VOLATILITY (ATR)</h2>
      <div class="value">${d.volatility?.atr ?? "—"}</div>
      <div class="small">Higher ATR favors continuation over chop</div>
    `;

    /* ---------- BOX 3 : VWAP (TIGHT SPACING) ---------- */
    document.getElementById("box-vwap").innerHTML = `
      <h2>VWAP</h2>
      <div class="line tight"><b>Position:</b> ${d.vwap?.position ?? "—"}</div>
      <div class="line tight"><b>Expansion:</b> ${d.vwap?.expansion_range ?? "—"}</div>
      <div class="line tight"><b>Midline:</b> ${d.vwap?.midline ?? "—"}</div>
      <div class="small">15‑min candle basis</div>
    `;

    /* ---------- BOX 4 : MARKET OPEN ---------- */
    const mo = d.market_open ?? {};
    document.getElementById("box-open").innerHTML = `
      <h2>MARKET OPEN <span class="small">FROZEN</span></h2>
      <div class="line"><b>Gap:</b> ${mo.gap_status?.type ?? "—"} (${mo.gap_status?.points ?? "—"})</div>
      <div class="small">Frozen at ${mo.gap_status?.frozen_at ?? "--"}</div>

      <div class="line"><b>Opening Candle:</b> ${mo.opening_candle?.type ?? "—"}</div>
      <div class="line mono">
        O ${mo.opening_candle?.ohlc?.open ?? "—"} |
        H ${mo.opening_candle?.ohlc?.high ?? "—"}<br>
        L ${mo.opening_candle?.ohlc?.low ?? "—"} |
        C ${mo.opening_candle?.ohlc?.close ?? "—"}
      </div>
      <div class="small">Range ${mo.opening_candle?.range ?? "—"}</div>
    `;

    /* ---------- BOX 5 : TREND ARCHITECT ---------- */
    const ta = d.trend_architect ?? {};
    document.getElementById("box-trend").innerHTML = `
      <h2>TREND ARCHITECT <span class="small">FINAL</span></h2>
      <div class="line"><b>Gap Behavior:</b> ${ta.gap_behavior ?? "—"}</div>
      <div class="line"><b>Major Candle:</b> ${ta.major_candle?.size ?? "—"} pts | ${ta.major_candle?.type ?? "—"}</div>
      <div class="small">Time ${ta.major_candle?.time ?? "--"}</div>
      <div class="line"><b>Next Candle:</b> ${ta.next_candle_relation ?? "—"}</div>
      <div class="line"><b>50‑pt Travel:</b> ${ta.travel ?? "—"}</div>
      <div class="line"><b>Choppiness:</b> ${ta.choppiness ?? "—"}</div>
      <div class="small">Effective from ${ta.effective_time ?? "--"}</div>
    `;

    /* ---------- BOX 6 : PDH / PDL / PDC ---------- */
    document.getElementById("box-pdh").innerHTML = `
      <h2>PREVIOUS DAY ANCHORS</h2>
      <div class="line mono">PDH: ${Number(d.previous_day?.pdh ?? 0).toFixed(2)}</div>
      <div class="line mono">PDL: ${Number(d.previous_day?.pdl ?? 0).toFixed(2)}</div>
      <div class="line mono">PDC: ${Number(d.previous_day?.pdc ?? 0).toFixed(2)}</div>
    `;

    /* ---------- BOX 7 : INSTITUTIONAL FLOWS ---------- */
    const f = d.institutional_flows ?? {};
    document.getElementById("box-flows").innerHTML = `
      <h2>INSTITUTIONAL FLOWS (NSE – Cash)</h2>
      <div class="line mono">FII (Today): ${f.fii_today ?? "—"}</div>
      <div class="line mono">DII (Today): ${f.dii_today ?? "—"}</div>
      <br>
      <div class="line mono">FII (Last 5 Days): | ${(f.fii_minus ?? ["—","—","—","—"]).join(" | ")}</div>
      <div class="line mono">DII (Last 5 Days): | ${(f.dii_minus ?? ["—","—","—","—"]).join(" | ")}</div>
      <div class="small">Published post‑market</div>
    `;
  });
