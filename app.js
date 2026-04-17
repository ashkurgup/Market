(async () => {
  const r = await fetch("./snapshots/market_phase1.json", { cache: "no-store" });
  const d = await r.json();

  const box = (id, cls, html) => {
    const el = document.getElementById(id);
    el.className = "card " + cls;
    el.innerHTML = html;
  };

  box("box-vwap", "vwap", `
    <h3>VWAP</h3>
    <div class="line"><b>Mid:</b> ${d.vwap.mid}</div>
    <div class="line"><b>Upper:</b> ${d.vwap.upper}</div>
    <div class="line"><b>Lower:</b> ${d.vwap.lower}</div>
    <div class="line"><b>Expansion:</b> ${d.vwap.expansion}</div>
    <div class="line"><b>Position:</b> ${d.vwap.position}</div>
    <div class="line"><b>Midline:</b> ${d.vwap.midline}</div>
    <div class="small">15‑min candle basis ${d.vwap.basis_candle_close}</div>
  `);

  const oc = d.market_open.opening_candle;
  box("box-open", "open", `
    <h3>MARKET OPEN <span class="small">FROZEN</span></h3>
    <div class="line">
      Opening Candle:
      <span class="${oc.color === "GREEN" ? "green" : "red"}">
        ${oc.type}
      </span>
      (Size ${oc.size} pts | Body ${oc.body_pct}%)
    </div>
    <div class="line">
      O ${oc.ohlc.open} | H ${oc.ohlc.high}
    </div>
    <div class="line">
      L ${oc.ohlc.low} | C ${oc.ohlc.close}
    </div>
    <div class="line">Range ${oc.range}</div>
  `);
})();
