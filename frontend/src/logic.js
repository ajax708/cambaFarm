// Turns the engine's response into the few plain facts the farmer sees.

// Ranking weights per priority profile (see backend Weights).
export const PROFILES = {
  balanced: { success: 0.45, summer: 0.2, soil: 0.25, pests: 0.1 },
  risk: { success: 0.65, summer: 0.3, soil: 0.05, pests: 0 },
  soil: { success: 0.3, summer: 0.1, soil: 0.6, pests: 0 },
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

/** Campaign-by-campaign winters (45 of them), with the success-rule outcome. */
export function winters(s) {
  return s.phases[0].campaigns.map((c) => ({
    year: c.campaign + 1,
    crop: c.winter?.crop,
    outcome: c.winter_outcome || 'rest', // ok | no_sow | late_sow | water | frost | heat | late | rest
    summer: c.summer_outcome,
    rain: c.winter?.rain_mm,
    ratio: c.winter?.water_ratio,
    enso: c.enso,
  }))
}

const count = (xs, f) => xs.filter(f).length

export function summary(s, current, phase) {
  const ws = winters(s)
  const planted = ws.filter((w) => w.outcome !== 'rest')
  const fails = planted.filter((w) => w.outcome !== 'ok')
  const causes = {}
  fails.forEach((w) => { causes[w.outcome] = (causes[w.outcome] || 0) + 1 })
  const same = planted.filter((w) => w.enso === phase)
  const curWs = winters(current)
  return {
    ws,
    n: planted.length,
    ok: count(planted, (w) => w.outcome === 'ok'),
    sown: count(planted, (w) => w.outcome !== 'no_sow' && w.outcome !== 'late_sow'),
    share: planted.length ? count(planted, (w) => w.outcome === 'ok') / planted.length : 0,
    mainCause: Object.keys(causes).sort((a, b) => causes[b] - causes[a])[0] || null,
    causes,
    summerOk: count(ws, (w) => w.summer === 'ok'),
    curSummerOk: count(curWs, (w) => w.summer === 'ok'),
    bareMonths: Math.round(s.indicators.bare_days.value / 30.4),
    curBareMonths: Math.round(current.indicators.bare_days.value / 30.4),
    ensoN: same.length,
    ensoOk: count(same, (w) => w.outcome === 'ok'),
  }
}

/** "8 of every 10" style rounding. */
export const outOfTen = (share) => Math.round(share * 10)

/** Short "personality" tag per option, among the options that are not today's. */
export function tags(strats, currentId) {
  const pool = strats.filter((s) => !s.excluded?.length && s.id !== currentId)
  const out = {}
  const pick = (key, best) => { if (best && !out[best.id]) out[best.id] = key }
  const succ = (s) => s.indicators.winter_success.value || 0
  pick('best', pool.find((s) => s.rank === Math.min(...pool.map((p) => p.rank))))
  pick('safe', [...pool].sort((a, b) => succ(b) - succ(a))[0])
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

/** Optional money estimate from the farmer's own numbers. A failed winter counts as no harvest. */
export function expectedMoney(sum, yieldKg, price, cost) {
  if (!(yieldKg > 0 && price > 0 && cost >= 0) || !sum.n) return null
  return (sum.ok / sum.n) * yieldKg * price - (sum.sown / sum.n) * cost
}
