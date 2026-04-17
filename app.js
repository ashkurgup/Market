(async function () {
  try {
    // ✅ Correct path for GitHub Pages PROJECT repository
    const response = await fetch("./snapshots/market_phase1.json", {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error("JSON fetch failed: " + response.status);
    }

    const d = await response.json();

    /* =========================
       NIFTY (LOCKED)
    ========================= */
    const nifty = d.nifty || {};
    const meta = d.meta || {};

    document.getElementById("box-nifty").innerHTML = `
      <h2>NIFTY <span class="small">● LIVE</span></h2>
      <div class="value">${(nifty.spot ?? "—").toFixed?.(2) ?? nifty.spot}</div>
      <div class="line ${nifty.change_points >= 0 ? "green" : "red"}">
        ${nifty.change_points ?? "—"} (${nifty.change_percent ?? "—"}%)
      </div>
      <div class="small">Updated: ${meta.last_updated ?? "--"} IST</div>
    `;

    /* =========================
       VOLATILITY (ATR)
    ========================= */
    document.getElementById("box-volatility").innerHTML = `
      <h2>VOLATILITY (ATR)</h2>
      <div class="value">${d.volatility?.atr ?? "—"}</div>
      <div class="small">Higher ATR favors continuation over chop</div>
    `;

    /* =========================
       VWAP
    ========================= */
    const vwap = d.vwap || {};
    document.getElementById("box-vwap").innerHTML = `
      <h2>VWAP</h2>
      <div class="line tight"><b>Position:</b> ${vwap.position ?? "—"}</div>
      <div class="line tight"><b>Expansion:</b> ${vwap.expansion_range ?? "—"}</div>
      <div class="line tight"><b>Midline:</b> ${vwap.midline ?? "—"}</div>
      <div class="small">15‑min candle basis</div>
    `;

    /* =========================
       PREVIOUS DAY ANCHORS (LOCKED)
    ========================= */
    const prev = d.previous_day || {};
    document.getElementById("box-anchors").innerHTML = `
      <h2>PREVIOUS DAY ANCHORS</h2>
      <div class="line mono"><b>PDH:</b> ${prev.pdh ?? "—"}</div>
      <div class="line mono"><b>PDL:</b> ${prev.pdl ?? "—"}</div>
      <div class="line mono"><b>PDC:</b> ${prev.pdc ?? "—"}</div>
    `;

    /* =========================
       MARKET OPEN (FROZEN)
    ========================= */
    const mo = d.market_open;

    if (mo && mo.gap && mo.opening_candle) {
      document.getElementById("box-open").innerHTML = `
        <h2>MARKET OPEN <span class="small">FROZEN</span></h2>

        <div class="line">
          <b>Gap:</b> ${mo.gap.direction} ${mo.gap.points}
        </div>
        <div class="small">Frozen at ${mo.gap.frozen_at}</div>

        <div class="line"><b>Opening Candle:</b> ${mo.opening_candle.type}</div>
        <div class="line mono">
          O ${mo.opening_candle.ohlc.open} | H ${mo.opening_candle.ohlc.high}<br>
          L ${mo.opening_candle.ohlc.low}  | C ${mo.opening_candle.ohlc.close}
        </div>
        <div class="line">Range ${mo.opening_candle.range}</div>
      `;
    } else {
      document.getElementById("box-open").innerHTML = `
        <h2>MARKET OPEN <span class="small">FROZEN</span></h2>
        <div class="line">Gap: — (—)</div>
        <div class="small">Frozen at --</div>
        <div class="line">Opening Candle: —</div>
        <div class="line mono">O — | H —<br>L — | C —</div>
        <div class="line">Range —</div>
      `;
    }

    /* =========================
       TREND ARCHITECT
    ========================= */
    const ta = d.trend_architect || {};

    document.getElementById("box-trend").innerHTML = `
      <h2>TREND ARCHITECT <span class="small">FINAL</span></h2>

      <div class="line"><b>Gap Behavior:</b> Closed by 11:05 AM</div>

      <div class="line">
        <b>Major Candle:</b>
        ${ta.major_candle?.size ?? "—"} pts |
        <span class="${ta.major_candle?.direction === "UP" ? "green" : "red"}">
          ${ta.major_candle?.type ?? "—"}
        </span>
        (Formed: ${ta.major_candle?.time ?? "--"} AM)
      </div>

      <div class="line">
        <b>Next Candle:</b>
        <span class="${ta.next_candle_relation === "OPPOSING" ? "red" : "green"}">
          ${ta.next_candle_relation ?? "—"}
        </span>
      </div>

      <div class="line"><b>50‑pt Travel:</b> —</div>
      <div class="line"><b>Choppiness:</b> —</div>

      <div class="small">Effective from 11:00 AM</div>
    `;

    /* =========================
       INSTITUTIONAL FLOWS
    ========================= */
    document.getElementById("box-flows").innerHTML = `
      <h2>INSTITUTIONAL FLOWS (NSE – Cash)</h2>
      <div class="line mono"><b>FII (Today):</b> —</div>
      <div class="line mono"><b>DII (Today):</b> —</div>
      <br>
      <div class="line mono"><b>FII (Last 4 Days):</b> | — | — | — | —</div>
      <div class="line mono"><b>DII (Last 4 Days):</b> | — | — | — | —</div>
    `;

  } catch (err) {
    console.error("APP ERROR:", err);
    document.body.innerHTML =
      "<h2 style='color:red'>Failed to load market data</h2>";
  }
})();
