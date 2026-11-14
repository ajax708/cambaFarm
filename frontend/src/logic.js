// Turns the engine's response into the few plain facts the farmer sees.

export const PROFILES = {
  balanced: { income: 0.3, stability: 0.25, soil: 0.25, water: 0.1, pests: 0.1 },
  money: { income: 0.7, stability: 0.1, soil: 0.1, water: 0.05, pests: 0.05 },
  risk: { income: 0.15, stability: 0.45, soil: 0.1, water: 0.25, pests: 0.05 },
  soil: { income: 0.15, stability: 0.1, soil: 0.6, water: 0.05, pests: 0.1 },
}

// Winter options the farmer can say they do today (all after soy).
export const TODAY_OPTIONS = [
  { crop: 'barbecho', strategy: 'A' },
  { crop: 'trigo', strategy: 'B' },
  { crop: 'sorgo', strategy: 'C' },
  { crop: 'girasol', strategy: 'D' },
  { crop: 'cobertura', strategy: 'E' },
]

/** Main winter crop of a strategy (first cycle year). */
export function winterCrop(s) {
  const first = Array.isArray(s.cycle[0]) ? s.cycle[0] : s.cycle
  return first[1]
}
export const isTwoYear = (s) => Array.isArray(s.cycle[0]) && s.cycle.length > 1

function status(w) {
  if (!w || w.class === 'fallow') return 'rest'
  if (w.class === 'good' || w.class === 'fair') return 'ok'
  if (w.class === 'not_sown') return 'miss'
  return 'bad'
}

/** Campaign-by-campaign winters, compared to the current strategy. */
export function winters(s, current) {
  const cur = current.phases[0].campaigns
  return s.phases[0].campaigns.map((c, i) => ({
    year: c.campaign + 1,
    crop: c.winter?.crop,
    status: status(c.winter),
    rain: c.winter?.rain_mm,
    enso: c.enso,
    gain: c.margin - (cur[i]?.margin ?? c.margin),
  }))
}

export function summary(s, current, phase) {
  const ws = winters(s, current)
  const planted = ws.filter((w) => w.status !== 'rest')
  const same = ws.filter((w) => w.enso === phase)
  const samePlanted = same.filter((w) => w.status !== 'rest')
  return {
    ws,
    n: planted.length,
    ok: planted.filter((w) => w.status === 'ok').length,
    worse: s.id === current.id ? 0 : ws.filter((w) => w.gain < -1).length,
    gainYear: s.indicators.margin.value - current.indicators.margin.value,
    gainTotal: ws.reduce((a, w) => a + w.gain, 0),
    bareMonths: Math.round(s.indicators.bare_days.value / 30.4),
    curBareMonths: Math.round(current.indicators.bare_days.value / 30.4),
    ensoN: same.length,
    ensoFails: samePlanted.filter((w) => w.status !== 'ok').length,
  }
}

/** Short "personality" tag per option, among the options that are not today's. */
export function tags(strats, currentId) {
  const pool = strats.filter((s) => !s.excluded?.length && s.id !== currentId)
  const out = {}
  const pick = (key, best) => { if (best && !out[best.id]) out[best.id] = key }
  pick('best', pool.find((s) => s.rank === Math.min(...pool.map((p) => p.rank))))
  pick('money', [...pool].sort((a, b) => b.indicators.margin.value - a.indicators.margin.value)[0])
  pick('safe', [...pool].sort((a, b) => a.indicators.loss_share.value - b.indicators.loss_share.value
    || a.indicators.bad_summer_share.value - b.indicators.bad_summer_share.value
    || b.indicators.margin_p10.value - a.indicators.margin_p10.value)[0])
  pick('soil', [...pool].sort((a, b) => a.indicators.bare_days.value - b.indicators.bare_days.value)[0])
  out[currentId] = 'today'
  return out
}

/** Hectares of a lat/lon polygon (small-area approximation). */
export function areaHa(poly) {
  if (!poly || poly.length < 3) return null
  const lat0 = (poly.reduce((a, p) => a + p.lat, 0) / poly.length) * Math.PI / 180
  const pts = poly.map((p) => [p.lon * 111320 * Math.cos(lat0), p.lat * 110540])
  let a = 0
  for (let i = 0; i < pts.length; i++) {
    const [x1, y1] = pts[i]
    const [x2, y2] = pts[(i + 1) % pts.length]
    a += x1 * y2 - x2 * y1
  }
  return Math.abs(a) / 2 / 10000
}

export function median(xs) {
  const v = xs.filter((x) => x != null).sort((a, b) => a - b)
  return v.length ? v[Math.floor(v.length / 2)] : null
}
