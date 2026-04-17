(async () => {
  try {
    const response = await fetch("./snapshots/market_phase1.json", {
      cache: "no-store"
    });
    if (!response.ok) throw new Error("JSON fetch failed");

    const d = await response.json();

    /* =========================
       NIFTY (LIVE)
    ========================= */
    const niftyBox = document.getElementById("box-nifty");
    niftyBox.className = "card nifty";
    niftyBox.innerHTML = `
      <h3>NIFTY <span class="small">• LIVE</span></h3>
      <div class="value">${Number(d.nifty.spot).toFixed(2)}</div>
      <div class="line green">
        ${d.nifty.change_points} (${d.nifty.change_percent}%)
      </div>
      <div class="small">Updated: ${d.meta.last_updated} IST</div>
    `;

    /* =========================
       VOLATILITY (ATR)
    ========================= */
    const volBox = document.getElementById("box-volatility");
    volBox.className = "card volatility";
    volBox.innerHTML = `
      <h3>VOLATILITY (ATR)</h3>
      <div class="value">${d.volatility?.atr ?? "—"}</div>
      <div class="small">Higher ATR favors continuation over chop</div>
    `;

    /* =========================
       VWAP
    ========================= */
    const vwapBox = document.getElementById("box-vwap");
    vwapBox.className = "card vwap";
    vwapBox.innerHTML = `
      <h3>VWAP</h3>
      <div class="line"><span class="bold">Position:</span> ${d.vwap.position}</div>
      <div class="line"><span class="bold">Expansion:</span> ${d.vwap.expansion_range}</div>
      <div class="line green"><span class="bold">Midline:</span> ${d.vwap.midline}</div>
      <div class="small">15‑min candle basis 11:45 AM</div>
    `;

    /* =========================
       PREVIOUS DAY ANCHORS (LOCKED)
    ========================= */
    const anchorsBox = document.getElementById("box-anchors");
    anchorsBox.className = "card anchors";
    anchorsBox.innerHTML = `
      <h3>PREVIOUS DAY ANCHORS</h3>
      <div class="line"><span class="bold">PDH:</span> ${d.previous_day.pdh}</div>
      <div class="line"><span class="bold">PDL:</span> ${d.previous_day.pdl}</div>
      <div class="line"><span class="bold">PDC:</span> ${d.previous_day.pdc}</div>
    `;

    /* =========================
       MARKET OPEN (FROZEN)
    ========================= */
    const openBox = document.getElementById("box-open");
    openBox.className = "card open";
    openBox.innerHTML = `
      <h3>MARKET OPEN <span class="small">FROZEN</span></h3>
      <div class="line"><span class="bold">Gap:</span> — (—)</div>
      <div class="small">Frozen at —</div>
      <div class="line"><span class="bold">Opening Candle:</span> —</div>
      <div class="line">O — | H —</div>
      <div class="line">L — | C —</div>
      <div class="line">Range —</div>
    `;

    /* =========================
       TREND ARCHITECT (FINAL)
    ========================= */
    const trendBox = document.getElementById("box-trend");
    trendBox.className = "card trend";
    trendBox.innerHTML = `
      <h3>TREND ARCHITECT <span class="small">FINAL</span></h3>
      <div class="line">
        <span class="bold">Gap Behavior:</span> Closed by 11:05 AM
      </div>
      <div class="line">
        <span class="bold">Major Candle:</span>
        32.45 pts |
        <span class="green bold">MARUBOZU</span>
        <span class="small">(Formed: 09:35 AM)</span>
      </div>
      <div class="line">
        <span class="bold">Next Candle:</span>
        <span class="red bold">OPPOSING</span>
      </div>
      <div class="line"><span class="bold">50‑pt Travel:</span> —</div>
      <div class="line"><span class="bold">Choppiness:</span> —</div>
      <div class="small">Effective from 11:00 AM</div>
    `;

    /* =========================
       INSTITUTIONAL FLOWS
    ========================= */
    const flowsBox = document.getElementById("box-flows");
    flowsBox.className = "card institutional";
    flowsBox.innerHTML = `
      <h3>INSTITUTIONAL FLOWS (NSE – Cash)</h3>
      <div class="line"><span class="bold">FII (Today):</span> —</div>
      <div class="line"><span class="bold">DII (Today):</span> —</div>
      <br>
      <div class="line"><span class="bold">FII (Last 4 Days):</span> | — | — | — | —</div>
      <div class="line"><span class="bold">DII (Last 4 Days):</span> | — | — | — | —</div>
      <div class="small">Published post‑market</div>
    `;

  } catch (err) {
    console.error("APP ERROR:", err);
    document.body.innerHTML =
      "<h2 style='color:red'>Failed to load market data</h2>";
  }
})();
``
