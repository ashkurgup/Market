(async () => {
  try {
    const response = await fetch("./snapshots/market_phase1.json", {
      cache: "no-store"
    });
    if (!response.ok) throw new Error("JSON fetch failed");

    const d = await response.json();

    /* Small helper: safe box renderer */
    function render(id, cls, html) {
      const el = document.getElementById(id);
      if (!el) return;
      el.className = "card " + cls;
      el.innerHTML = html;
    }

    /* =========================
       NIFTY
    ========================= */
    render(
      "box-nifty",
      "nifty",
      `
      <h3>NIFTY <span class="small">• LIVE</span></h3>
      <div class="value">${Number(d.nifty?.spot ?? 0).toFixed(2)}</div>
      <div class="line green">
        ${d.nifty?.change_points ?? "—"} (${d.nifty?.change_percent ?? "—"}%)
      </div>
      <div class="small">Updated: ${d.meta?.last_updated ?? "--"} IST</div>
    `
    );

    /* =========================
       VOLATILITY (ATR)
    ========================= */
    render(
      "box-volatility",
      "volatility",
      `
      <h3>VOLATILITY (ATR)</h3>
      <div class="value">
        ${d.volatility?.atr ?? "—"}
        <span class="small">(${d.volatility?.sample_status ?? "—"})</span>
      </div>
      <div class="line">
        <strong>Choppiness:</strong>
        ${d.choppiness?.state ?? "—"} — ${d.choppiness?.message ?? "—"}
      </div>
      <div class="small">
        Reliable from ${d.volatility?.reliable_from ?? "--"} IST
      </div>
    `
    );

    /* =========================
       VWAP
    ========================= */
    render(
      "box-vwap",
      "vwap",
      `
      <h3>VWAP</h3>
      <div class="line"><b>Position:</b> ${d.vwap?.position ?? "—"}</div>
      <div class="line"><b>Expansion:</b> ${d.vwap?.expansion_range ?? "—"}</div>
      <div class="line green"><b>Midline:</b> ${d.vwap?.midline ?? "—"}</div>
      <div class="small">
        15‑min candle basis ${d.vwap?.basis_candle_close ?? "--:--"}
      </div>
    `
    );

    /* =========================
       PREVIOUS DAY ANCHORS
    ========================= */
    render(
      "box-anchors",
      "anchors",
      `
      <h3>PREVIOUS DAY ANCHORS</h3>
      <div class="line"><b>PDH:</b> ${d.previous_day?.pdh ?? "—"}</div>
      <div class="line"><b>PDL:</b> ${d.previous_day?.pdl ?? "—"}</div>
      <div class="line"><b>PDC:</b> ${d.previous_day?.pdc ?? "—"}</div>
    `
    );

    /* =========================
       MARKET OPEN (FROZEN)
    ========================= */
    const mo = d.market_open;
render(
  "box-open",
  "open",
  `
  <h3>MARKET OPEN <span class="small">FROZEN</span></h3>
  <div class="line"><b>Gap:</b> ${mo.gap.direction} (${mo.gap.points})</div>
  <div class="small">Frozen at ${mo.gap.frozen_at}</div>

  <div class="line">
    <b>Opening Candle:</b>
    <span class="
      ${mo.opening_candle.color === "GREEN" ? "green" :
        mo.opening_candle.color === "RED" ? "red" : "bold"}
    ">
      ${mo.opening_candle.type}
    </span>
    (${mo.opening_candle.size} pts)
  </div>

  <div class="line">
    O ${mo.opening_candle.ohlc.open}
    | H ${mo.opening_candle.ohlc.high}
  </div>
  <div class="line">
    L ${mo.opening_candle.ohlc.low}
    | C ${mo.opening_candle.ohlc.close}
  </div>
  <div class="line">Range ${mo.opening_candle.range}</div>
`
);

    /* =========================
       TREND ARCHITECT
    ========================= */
    render(
      "box-trend",
      "trend",
      `
      <h3>TREND ARCHITECT <span class="small">FINAL</span></h3>
      <div class="line"><b>Gap Behavior:</b> Closed by 11:05 AM</div>
      <div class="line">
        <b>Major Candle:</b> 32.45 pts |
        <span class="green bold">MARUBOZU</span>
        <span class="small">(Formed: 09:35 AM)</span>
      </div>
      <div class="line">
        <b>Next Candle:</b>
        <span class="red bold">OPPOSING</span>
      </div>
      <div class="line"><b>50‑pt Travel:</b> —</div>
      <div class="line"><b>Choppiness:</b> —</div>
      <div class="small">Effective from 11:00 AM</div>
    `
    );

    /* =========================
       INSTITUTIONAL FLOWS
    ========================= */
    render(
      "box-flows",
      "institutional",
      `
      <h3>INSTITUTIONAL FLOWS (NSE – Cash)</h3>
      <div class="line"><b>FII (Today):</b> —</div>
      <div class="line"><b>DII (Today):</b> —</div>
      <div class="line"><b>FII (Last 4 Days):</b> | — | — | — | —</div>
      <div class="line"><b>DII (Last 4 Days):</b> | — | — | — | —</div>
      <div class="small">Published post‑market</div>
    `
    );

  } catch (err) {
    console.error("APP ERROR:", err);
    document.body.innerHTML =
      "<h2 style='color:red'>Failed to load market data</h2>";
  }
})();
``
