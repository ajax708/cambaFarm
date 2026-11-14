import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Polygon, Polyline, useMap, useMapEvents } from 'react-leaflet'
import { T } from './i18n.jsx'
import { PROFILES, TODAY_OPTIONS, winterCrop, isTwoYear, summary, tags, areaHa, median } from './logic.js'
import DataPage from './DataPage.jsx'

const API = import.meta.env.DEV ? '/api' : ''
const PILOT = { lat: -17.4, lon: -63.2 }

/* ---------- small building blocks ---------- */
const Icon = ({ id, size }) => <svg width={size} height={size} aria-hidden="true"><use href={`#${id}`} /></svg>

function Hero() {
  return (
    <svg className="hero" viewBox="0 0 480 360" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#cfe6f2" /><stop offset="1" stopColor="#fbf6ec" /></linearGradient></defs>
      <rect width="480" height="360" fill="url(#sky)" />
      <circle cx="370" cy="80" r="38" fill="#f2b33d" /><circle cx="370" cy="80" r="56" fill="#f2b33d" opacity=".18" />
      <path d="M0 200c90-50 190-56 300-30s130 12 180-8v198H0z" fill="#8fc27f" />
      <path d="M0 238c120-36 250-34 480-4v126H0z" fill="#b98557" />
      <g stroke="#8a5a36" strokeWidth="3" opacity=".55">{[[-30, 180], [60, 220], [160, 270], [260, 315], [360, 350], [470, 390]].map(([x1, x2], i) => <path key={i} d={`M${x1} 360L${x2} 238`} />)}</g>
      {[[90, 262, .7], [210, 284, 1], [330, 268, .8], [140, 318, 1.2], [380, 312, 1.3]].map(([x, y, k], i) =>
        <g key={i} transform={`translate(${x} ${y}) scale(${k})`}><use href="#sprout" width="24" height="24" /></g>)}
    </svg>
  )
}

function MapClicks({ mode, onPoint, onVertex }) {
  useMapEvents({ click: (e) => { const p = { lat: +e.latlng.lat.toFixed(5), lon: +e.latlng.lng.toFixed(5) }; mode === 'draw' ? onVertex(p) : onPoint(p) } })
  return null
}
function Recenter({ to }) {
  const map = useMap()
  useEffect(() => { if (to) map.flyTo([to.lat, to.lon], 15) }, [to, map])
  return null
}

/* ---------- app ---------- */
export default function App() {
  const [lang, setLang] = useState('es')
  const t = T[lang]
  const fmt = (n) => new Intl.NumberFormat(t.locale, { maximumFractionDigits: 0 }).format(n)

  const [screen, setScreen] = useState('home')
  const [mode, setMode] = useState('point')
  const [point, setPoint] = useState(PILOT)
  const [poly, setPoly] = useState([])
  const [flyTo, setFlyTo] = useState(null)
  const [locating, setLocating] = useState(false)
  const [current, setCurrent] = useState('A')
  const [profile, setProfile] = useState('balanced')
  const [data, setData] = useState(null)
  const [sat, setSat] = useState(null)
  const [busy, setBusy] = useState(false)
  const [tick, setTick] = useState(0)
  const [sel, setSel] = useState(null)

  const polygon = poly.length >= 3 ? poly.map((p) => [p.lat, p.lon]) : null
  const center = polygon ? { lat: poly.reduce((a, p) => a + p.lat, 0) / poly.length, lon: poly.reduce((a, p) => a + p.lon, 0) / poly.length } : point
  const ha = areaHa(polygon ? poly : null)

  useEffect(() => { window.scrollTo(0, 0) }, [screen])
  useEffect(() => {
    if (screen !== 'loading') return
    setTick(0)
    const ids = [setTimeout(() => setTick(1), 1200), setTimeout(() => setTick(2), 2600)]
    return () => ids.forEach(clearTimeout)
  }, [screen])

  async function run(prof = profile, l = lang, keepScreen = false) {
    if (!keepScreen) setScreen('loading')
    setBusy(true)
    const body = { lat: center.lat, lon: center.lon, polygon, lang: l, current, weights: PROFILES[prof] }
    try {
      const r = await fetch(`${API}/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      if (!r.ok) throw new Error(r.statusText)
      setData(await r.json())
      setSel(null)
      if (!keepScreen) setScreen('result')
    } catch {
      if (!keepScreen) setScreen('error')
    } finally {
      setBusy(false)
    }
    if (!keepScreen) {
      setSat('loading')
      fetch(`${API}/satellite`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ lat: center.lat, lon: center.lon, polygon }) })
        .then((r) => r.json()).then(setSat).catch(() => setSat({ data: {}, errors: { all: 'network' } }))
    }
  }

  function switchLang(l) {
    setLang(l)
    if (data) run(profile, l, true)
  }

  function locate() {
    if (!navigator.geolocation) return
    setLocating(true)
    navigator.geolocation.getCurrentPosition((pos) => {
      const p = { lat: +pos.coords.latitude.toFixed(5), lon: +pos.coords.longitude.toFixed(5) }
      setMode('point'); setPoly([]); setPoint(p); setFlyTo(p); setLocating(false)
    }, () => setLocating(false), { timeout: 10000 })
  }

  /* ----- derived view model ----- */
  const vm = useMemo(() => {
    if (!data) return null
    const strats = data.strategies
    const cur = strats.find((s) => s.is_current) || strats.find((s) => s.id === current)
    const pool = strats.filter((s) => !s.excluded?.length && s.id !== cur.id).sort((a, b) => a.rank - b.rank)
    const best = pool[0]
    const chosen = strats.find((s) => s.id === sel) || best
    const phase = data.outlook?.phase || 'neutral'
    return { strats, cur, pool, best, chosen, phase, oni: data.outlook?.oni ?? 0, tags: tags(strats, cur.id), sum: summary(chosen, cur, phase), alreadyBest: cur.rank === 1 }
  }, [data, sel, current])

  /* ----- top navigation ----- */
  const nav = (
    <nav className="nav">
      <div className="nav-in">
        <button className="brand" onClick={() => setScreen('home')}><Icon id="leaf" size={22} />{t.brand}</button>
        <div className="nav-links">
          <button className={screen === 'setup' ? 'on' : ''} onClick={() => setScreen('setup')}>{t.navField}</button>
          <button className={screen === 'result' ? 'on' : ''} disabled={!data} onClick={() => setScreen('result')}>{t.navResult}</button>
          <button className={screen === 'data' ? 'on' : ''} disabled={!data} onClick={() => setScreen('data')}>{t.navData}</button>
        </div>
        <div className="lang" role="group" aria-label="language">
          {['es', 'en'].map((l) => <button key={l} className={l === lang ? 'on' : ''} onClick={() => switchLang(l)}>{l.toUpperCase()}</button>)}
        </div>
      </div>
    </nav>
  )
  const page = (cls, children) => <div className="site">{nav}<main className={`wrap ${cls}`}>{children}</main><footer className="foot small">{t.sources} · {t.disclaimer}</footer></div>

  /* ----- screens ----- */
  if (screen === 'home') return page('home', <>
    <section className="landing">
      <div className="landing-text">
        <span className="tag">{t.landingTag}</span>
        <h1 className="display">{t.heroTitle}</h1>
        <p className="lead big">{t.heroLead}</p>
        <button className="btn go auto" onClick={() => setScreen('setup')}>{t.start}</button>
      </div>
      <div className="landing-art"><Hero /></div>
    </section>
    <section>
      <h2 className="section-h">{t.howTitle}</h2>
      <div className="how">
        {[[t.how1, 'barbecho'], [t.how2, 'soya'], [t.how3, 'sprout']].map(([[h, p], ic], i) => (
          <div key={i} className="how-card"><span className="how-n">{i + 1}</span><Icon id={ic} size={56} /><b>{h}</b><p>{p}</p></div>
        ))}
      </div>
    </section>
    <p className="powered">{t.poweredBy} <b>NASA POWER</b> · <b>GPM IMERG</b> · <b>SMAP</b> · <b>Landsat</b> · <b>SRTM</b></p>
  </>)

  if (screen === 'setup') return page('setup', <>
    <div className="page-head"><div><h1>{t.setupTitle}</h1><p className="lead">{t.setupLead}</p></div></div>
    <div className="setup-grid">
      <div className="map">
        <MapContainer center={[center.lat, center.lon]} zoom={12} scrollWheelZoom style={{ height: '100%', width: '100%' }} attributionControl={false}>
          <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" />
          {polygon ? <Polygon positions={polygon} pathOptions={{ color: '#f2b33d', weight: 3, dashArray: '7 5', fillOpacity: 0.25 }} />
            : poly.length > 1 ? <Polyline positions={poly.map((p) => [p.lat, p.lon])} pathOptions={{ color: '#f2b33d', weight: 3 }} /> : null}
          {mode === 'point' && <CircleMarker center={[point.lat, point.lon]} radius={10} pathOptions={{ color: '#fff', weight: 3, fillColor: '#2f7d4a', fillOpacity: 1 }} />}
          {mode === 'draw' && poly.map((p, i) => <CircleMarker key={i} center={[p.lat, p.lon]} radius={6} pathOptions={{ color: '#f2b33d', weight: 3, fillColor: '#fff', fillOpacity: 1 }} />)}
          <MapClicks mode={mode} onPoint={setPoint} onVertex={(p) => setPoly([...poly, p])} />
          <Recenter to={flyTo} />
        </MapContainer>
        <div className="map-chip">
          {mode === 'point' ? <>{t.chipPoint}<span>{t.chipPointHelp}</span></>
            : ha ? <>{t.chipLot(fmt(ha))}<span>{t.chipLotHelp}</span></>
              : <>{t.chipDrawing}<span>{t.chipDrawingHelp}</span></>}
        </div>
        {mode === 'draw' && poly.length > 0 && <button className="map-clear" onClick={() => setPoly([])}>{t.clear}</button>}
      </div>
      <aside className="panel setup-side">
        <p className="q"><span className="num">1</span>{t.whereTitle}</p>
        <div className="seg">
          <button className={mode === 'point' ? 'on' : ''} onClick={() => { setMode('point'); setPoly([]) }}>{t.usePoint}</button>
          <button className={mode === 'draw' ? 'on' : ''} onClick={() => { setMode('draw'); setPoly([]) }}>{t.drawLot}</button>
        </div>
        <button className="locate" onClick={locate} disabled={locating}>
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="currentColor" /><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="2" /><path d="M12 1v4M12 19v4M1 12h4M19 12h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
          {locating ? t.locating : t.myLocation}
        </button>
        <p className="q"><span className="num">2</span>{t.todayQ}</p>
        <div className="tiles">
          {TODAY_OPTIONS.map((o) => (
            <button key={o.strategy} className={`tile ${current === o.strategy ? 'on' : ''}`} onClick={() => setCurrent(o.strategy)}>
              <Icon id={o.crop} size={50} />{t.crops[o.crop]}
            </button>
          ))}
        </div>
        <button className="btn go" disabled={mode === 'draw' && !polygon} onClick={() => run()}>{t.see}</button>
      </aside>
    </div>
  </>)

  if (screen === 'loading') return page('loading', (
    <div className="panel loading-card">
      <svg width="200" height="200" viewBox="0 0 220 220" aria-hidden="true">
        <circle cx="110" cy="130" r="70" fill="#d6ebf5" />
        <path d="M48 150c20-14 40-12 62-4s44 6 64-6c-6 32-34 54-64 54s-56-18-62-44z" fill="#8fc27f" />
        <circle className="orbit" cx="110" cy="130" r="70" fill="none" stroke="#2f7d4a" strokeWidth="3" strokeDasharray="4 8" />
        <g className="sat"><g transform="translate(150 34) rotate(25)">
          <rect x="-10" y="-8" width="20" height="16" rx="3" fill="#6f665b" />
          <rect x="-38" y="-6" width="24" height="12" fill="#2a78d6" /><rect x="14" y="-6" width="24" height="12" fill="#2a78d6" />
        </g></g>
        <path className="beam" d="M140 52l-24 64" stroke="#f2b33d" strokeWidth="3" strokeDasharray="5 5" />
        <circle cx="114" cy="122" r="6" fill="#f2b33d" />
      </svg>
      <h1>{t.loadingTitle}</h1>
      <div className="checks">
        {t.checks.map((c, i) => <div key={i} className={`check ${i <= tick ? '' : 'wait'}`}><span className="ic">{i <= tick ? '✓' : '…'}</span>{c}</div>)}
      </div>
      <p className="small center">{t.slowNote}</p>
    </div>
  ))

  if (screen === 'error' || !vm) return page('loading', (
    <div className="panel loading-card">
      <Icon id="barbecho" size={140} />
      <h1>{t.errorTitle}</h1>
      <button className="btn go auto" onClick={() => run()}>{t.retry}</button>
    </div>
  ))

  if (screen === 'data') return page('data', <DataPage data={data} sat={sat} t={t} fmt={fmt} />)

  /* ----- result (one rich page on web) ----- */
  const { chosen, cur, sum, phase, oni } = vm
  const crop = winterCrop(chosen)
  const headline = isTwoYear(chosen) ? chosen.name : t.plant[crop]
  const more = sum.gainYear >= 0
  const statuses = ['ok', 'bad', 'miss', 'rest'].filter((k) => sum.ws.some((w) => w.status === k))
  const rains = sum.ws.filter((w) => w.status === 'ok' || w.status === 'bad').map((w) => w.rain).filter((r) => r > 0)
  const sd = sat && sat !== 'loading' ? sat.data || {} : null
  const years = {}
  ;(sd?.imerg || []).forEach((m) => { const y = m.month.slice(0, 4); (years[y] ||= []).push(m.rain_mm) })
  const full = Object.values(years).filter((v) => v.length === 12).map((v) => v.reduce((a, b) => a + b, 0))
  const gpm = full.length ? Math.round(full.reduce((a, b) => a + b, 0) / full.length / 10) * 10 : null
  const bareSat = sd?.bare_month_share ? sd.bare_month_share.filter((x) => x != null && x >= 0.5).length : null
  const anom = sd?.smap_anomaly
  const satMsg = sat === 'loading' ? t.satPending : t.satOff

  return page(`result ${busy ? 'fading' : ''}`, <>
    <section className="verdict-head">
      <div className="crop-hero">
        <div className="circle"><Icon id={crop} size={72} /></div>
        <div>
          <span className="tag">{t.bestTag}</span>
          <h1 className="display sm">{headline}</h1>
          {vm.alreadyBest && !sel && <p className="note">{t.alreadyBest}</p>}
        </div>
      </div>
      <div className="profiles">
        <p className="q">{t.priority}</p>
        <div className="chips">
          {Object.keys(PROFILES).map((p) => (
            <button key={p} className={`chip ${profile === p ? 'on' : ''}`} disabled={busy}
              onClick={() => { setProfile(p); run(p, lang, true) }}>{t.profiles[p]}</button>
          ))}
        </div>
      </div>
    </section>

    <div className="result-grid">
      <div className="col">
        <div className={`money ${more ? '' : 'less'}`}>
          <div className="big">{more ? '+' : '−'} USD {fmt(Math.abs(sum.gainYear))}</div>
          <p className="m-sub">{t.perHa} · {t.vsToday}</p>
          {ha && <p className="m-lot">{(more ? t.onYourLot : t.onYourLotLess)(fmt(ha), fmt(Math.round(Math.abs(sum.gainYear) * ha / 100) * 100))}</p>}
        </div>
        <div className="facts">
          {sum.n > 0 && (
            <div className="fact"><span className="ic" style={{ background: 'var(--leaf-l)' }}><Icon id="sprout" size={24} /></span>
              <div><b>{t.workedTitle(sum.ok, sum.n)}</b>{sum.worse === 0 ? t.neverWorse : t.sometimesWorse(sum.worse)}</div></div>
          )}
          <div className="fact"><span className="ic" style={{ background: 'var(--soil-l)' }}><Icon id="barbecho" size={26} /></span>
            <div><b>{sum.bareMonths <= sum.curBareMonths ? t.soilTitle : t.soilTitleWorse}</b>{t.soilText(sum.bareMonths, sum.curBareMonths)}</div></div>
          {sum.ensoN > 0 && (
            <div className="fact"><span className="ic" style={{ background: 'var(--sun-l)' }}><Icon id="sun" size={24} /></span>
              <div><b>{Math.abs(oni) >= 1.5 && t.ensoStrong[phase] ? t.ensoStrong[phase] : t.ensoTitle[phase]}</b>{t.ensoText(sum.ensoFails, sum.ensoN)}</div></div>
          )}
        </div>
        {chosen.card?.risks?.length > 0 && <p className="risk"><b>{t.risksTitle}</b> {chosen.card.risks[0].replace(/^[^:]+:\s*/, '')}</p>}
      </div>

      <div className="col">
        <h2 className="section-h">{t.optionsShort}</h2>
        {[...vm.pool, cur].map((s) => {
          const c = winterCrop(s)
          const g = s.indicators.margin.value - cur.indicators.margin.value
          const tag = vm.tags[s.id]
          const isCur = s.id === cur.id
          return (
            <button key={s.id} className={`opt ${s.id === chosen.id ? 'best' : ''} ${isCur ? 'cur' : ''}`} onClick={() => { if (!isCur) setSel(s.id) }}>
              <span className={`pic bg-${c}`}><Icon id={c} size={40} /></span>
              <span className="opt-main"><span className="name">{isTwoYear(s) ? s.name : t.crops[c]}</span>
                {tag && <span className={`chip-s t-${tag}`}>{t.tags[tag]}</span>}</span>
              <span className={`val ${isCur ? '' : g >= 0 ? 'up' : 'down'}`}>
                {isCur ? '0' : `${g >= 0 ? '+' : '−'}${fmt(Math.abs(g))}`}<small>{isCur ? t.startPoint : t.perYear}</small></span>
            </button>
          )
        })}
        <p className="small">{t.optionsNote}</p>
      </div>
    </div>

    <section className="panel">
      <div className="h-row"><h2 className="section-h">{t.wintersShort}</h2>
        <div className="legend">{statuses.map((k) => <span key={k}><i className={`w-${k}`} />{t.legend[k]}</span>)}</div></div>
      <p className="lead">{t.wintersLead}</p>
      <div className="winters">
        {sum.ws.map((w) => (
          <span key={w.year} className={`w-${w.status}`} title={`${t.winterOf(w.year)}: ${t.legend[w.status]}`}>
            <Icon id={w.status === 'ok' ? 'sprout' : w.status === 'rest' ? 'dot' : 'cross'} />
            <em>{String(w.year).slice(2)}</em>
          </span>
        ))}
      </div>
      {chosen.id !== cur.id && (
        <div className="total">{t.totalMore} <b>{t.totalPerHa(fmt(Math.abs(sum.gainTotal)), sum.gainTotal >= 0)}</b> {t.totalVs}</div>
      )}
    </section>

    <section>
      <div className="h-row"><h2 className="section-h">{t.whyTitle}</h2>
        <button className="btn soft auto" onClick={() => setScreen('data')}>{t.seeData} →</button></div>
      <div className="why-grid">
        <div className="why"><span className="pic" style={{ background: 'var(--sky)' }}><Icon id="rain" size={30} /></span>
          <div><b>{t.rainTitle}</b><p>{rains.length ? t.rainText(fmt(Math.min(...rains)), fmt(median(rains))) : ''}{gpm ? t.gpmText(fmt(gpm)) : ''}</p>
            <span className="src">NASA POWER{gpm ? ' · GPM IMERG' : ''}</span></div></div>
        <div className="why"><span className="pic" style={{ background: 'var(--leaf-l)' }}><Icon id="sprout" size={30} /></span>
          <div><b>{t.greenTitle}</b><p>{bareSat != null ? t.greenSat(bareSat) : t.greenModel(sum.curBareMonths)}</p>
            <span className="src">{bareSat != null ? 'Landsat 8/9' : 'NASA POWER'}</span></div></div>
        <div className="why"><span className="pic" style={{ background: 'var(--soil-l)' }}><Icon id="drop" size={30} /></span>
          <div><b>{t.waterTitle}</b>
            <p>{anom == null ? satMsg : Math.abs(anom) < 0.1 ? t.waterSame : t.waterText(Math.round(Math.abs(anom) * 100), anom > 0)}</p>
            <span className="src">SMAP</span></div></div>
      </div>
      <div className="unknown"><b>{t.unknownTitle}</b> {t.unknownText}</div>
    </section>
  </>)
}
