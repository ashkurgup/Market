async function loadPhase2() {
  try {
    const res = await fetch('snapshots/market_phase2.json', { cache: 'no-store' })
    const data = await res.json()

    renderPhase2Meta(data)
    renderWeeklyLevels(data.weekly_levels)
    renderKeyLevels(data.key_levels)
    renderSessionLevels(data.session_levels)
    renderStructureEvents(data.structure_events)
    renderMomentumEvents(data.momentum_events)
    renderGlobalIndices(data.global_indices)
    renderStructuralBias(data.bias)

  } catch (err) {
    console.error('Phase‑2 load failed:', err)
  }
}

/* ================== META ================== */

function renderPhase2Meta(data) {
  const el = document.getElementById('phase2-last-updated')
  if (!el || !data.computed_at) return

  const dt = new Date(data.computed_at)
  el.innerText = 'Last updated: ' + dt.toLocaleString('en-IN')
}

/* ================== WEEKLY LEVELS ================== */

function renderWeeklyLevels(w) {
  const el = document.querySelector('#weekly-levels .content')
  if (!el || !w || w.previous_week_high === null) {
    el.innerText = 'No data'
    return
  }

  el.innerHTML = `
    High: <strong>${w.previous_week_high}</strong><br/>
    Low: <strong>${w.previous_week_low}</strong><br/>
    (${w.week_start} → ${w.week_end})
  `
}

/* ================== KEY LEVELS ================== */

function renderKeyLevels(k) {
  const el = document.querySelector('#key-levels .content')
  if (!el || !k || (k.nearest_support === null && k.nearest_resistance === null)) {
    el.innerText = 'No data'
    return
  }

  el.innerHTML = `
    Resistance: ${k.nearest_resistance ?? '—'}<br/>
    Support: ${k.nearest_support ?? '—'}
  `
}

/* ================== SESSION LEVELS ================== */

function renderSessionLevels(s) {
  const el = document.querySelector('#session-levels .content')
  if (!el || !s || s.high === null) {
    el.innerText = 'No data'
    return
  }

  el.innerHTML = `
    High: <strong>${s.high}</strong><br/>
    Low: <strong>${s.low}</strong><br/>
    (${s.based_on_timeframe}, close‑based)
  `
}

/* ================== STRUCTURE EVENTS ================== */

function renderStructureEvents(events) {
  const el = document.querySelector('#structure-events .content')
  if (!el || !events || events.length === 0) {
    el.innerText = 'No events detected'
    return
  }

  el.innerHTML = events.map(e => `
    ${e.type} (${e.direction}) @ ${e.price}
    <br/><small>${formatTime(e.time)}</small>
  `).join('<hr/>')
}

/* ================== MOMENTUM EVENTS ================== */

function renderMomentumEvents(events) {
  const el = document.querySelector('#momentum-events .content')
  if (!el || !events || events.length === 0) {
    el.innerText = 'No events detected'
    return
  }

  el.innerHTML = events.map(e => `
    ${e.type} (${e.direction})
    <br/><small>${formatTime(e.time)}</small>
  `).join('<hr/>')
}

/* ================== GLOBAL INDICES ================== */

function renderGlobalIndices(g) {
  const el = document.querySelector('#global-indices .content')
  if (!el || !g || !g.indices || g.indices.length === 0) {
    el.innerText = 'No data'
    return
  }

  el.innerHTML = g.indices.map(i => `
    ${i.name}: ${i.percent_change ?? '—'}%
  `).join('<br/>')
}

/* ================== STRUCTURAL BIAS ================== */

function renderStructuralBias(b) {
  const el = document.querySelector('#structural-bias .content')
  if (!el || !b || (!b.day && !b.h4 && !b.h1)) {
    el.innerText = 'Not evaluated'
    return
  }

  el.innerHTML = `
    Day: ${b.day ?? '—'}<br/>
    4H: ${b.h4 ?? '—'}<br/>
    1H: ${b.h1 ?? '—'}
  `
}

/* ================== HELPERS ================== */

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('en-IN')
}

/* ================== INIT ================== */

document.addEventListener('DOMContentLoaded', loadPhase2)
