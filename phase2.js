async function loadPhase2() {
  const res = await fetch('snapshots/market_phase2.json')
  const data = await res.json()

  // For now, we only verify wiring
  console.log('Phase‑2 loaded:', data)
}

document.addEventListener('DOMContentLoaded', loadPhase2)
