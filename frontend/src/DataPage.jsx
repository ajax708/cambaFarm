import { useState } from 'react'
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Cell, ReferenceLine, Legend } from 'recharts'

const C = { rain: '#2f6fb0', tmax: '#c8643b', tmin: '#2f7d4a', ndvi: '#2f7d4a', sm: '#8a5a36', clim: '#b5aa98', nino: '#c8643b', nina: '#2f6fb0', neutral: '#b5aa98' }
const axis = { stroke: '#c9bfae', tick: { fill: '#6f665b', fontSize: 12 }, tickLine: false }
const grid = <CartesianGrid stroke="#ece3d3" vertical={false} />
const tip = { contentStyle: { borderRadius: 12, border: '1px solid #ece3d3', fontSize: 13 }, cursor: { fill: 'rgba(47,125,74,.06)' } }

function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
const toCsv = (rows) => rows.length ? [Object.keys(rows[0]).join(','), ...rows.map((r) => Object.values(r).join(','))].join('\n') : ''

function Status({ state, t }) {
  const label = { ok: t.connected, off: t.offline, wait: t.pending, default: t.fallback }[state]
  return <span className={`status-chip s-${state}`}>{state === 'ok' ? '●' : state === 'wait' ? '◌' : '○'} {label}</span>
}

function Source({ name, tag, nasa, what, state, t, meta, csv, rows, children }) {
  const [open, setOpen] = useState(false)
  return (
    <section className="src-card">
      <header className="src-head">
        <div>
          <span className={`src-tag ${nasa ? 'nasa' : ''}`}>{tag}</span>
          <h3>{name}</h3>
          <p className="small">{what}</p>
        </div>
        <Status state={state} t={t} />
      </header>
      {meta && <dl className="meta">{meta.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>}
      {children}
      {rows?.length > 0 && (
        <div className="src-actions">
          <button className="link" onClick={() => setOpen(!open)}>{open ? t.hideTable : t.showTable}</button>
          {csv && <button className="link" onClick={() => download(csv, toCsv(rows), 'text/csv')}>{t.downloadCsv}</button>}
        </div>
      )}
      {open && rows?.length > 0 && (
        <div className="table-wrap"><table>
          <thead><tr>{Object.keys(rows[0]).map((k) => <th key={k}>{k}</th>)}</tr></thead>
          <tbody>{rows.map((r, i) => <tr key={i}>{Object.values(r).map((v, j) => <td key={j}>{v == null ? '—' : String(v)}</td>)}</tr>)}</tbody>
        </table></div>
      )}
    </section>
  )
}

export default function DataPage({ data, sat, t, fmt }) {
  const d = data.data
  const p = d.power
  const sd = sat && sat !== 'loading' ? sat.data || {} : {}
  const se = sat && sat !== 'loading' ? sat.errors || {} : {}
  const satState = (k) => sat === 'loading' ? 'wait' : sd[k] && (Array.isArray(sd[k]) ? sd[k].length : true) ? 'ok' : 'off'
  const annual = p.annual.filter((y) => y.complete)
  const imerg = (sd.imerg || []).slice(-36)
  const smap = (sd.smap || []).filter((w) => w.sm != null)
  const ndvi = sd.landsat || []
  const oni = d.enso.recent.map((o) => ({ ...o, label: `${o.season} ${o.year}` }))
  const offMsg = <p className="off-msg">{sat === 'loading' ? t.satPending : t.satOff}</p>

  return (
    <div className="data-page">
      <div className="page-head">
        <div>
          <h1>{t.dataTitle}</h1>
          <p className="lead">{t.dataLead}</p>
        </div>
        <button className="btn soft auto" onClick={() => download('datos-campo.json', JSON.stringify({ point: data.point, data: d, satellite: sat?.data || null }, null, 2), 'application/json')}>{t.downloadAll}</button>
      </div>

      <div className="src-grid">
        <Source name="NASA POWER" tag={t.nasaTag} nasa what={t.power.what} state="ok" t={t} csv="nasa-power-anual.csv" rows={p.annual}
          meta={[[t.query, `${p.query.latitude}, ${p.query.longitude}`], [t.period, `${p.query.start} → ${p.query.end}`],
            [t.days, fmt(p.n_days)]]}>
          <div className="params"><span className="small">{t.params}:</span>{p.parameters.map((x) => <code key={x}>{x}</code>)}</div>
          <h4>{t.power.rain}</h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={annual} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
              {grid}<XAxis dataKey="year" {...axis} interval={4} /><YAxis {...axis} />
              <Tooltip {...tip} formatter={(v) => [`${fmt(v)} mm`, t.power.rain]} />
              <Bar isAnimationActive={false} dataKey="rain_mm" fill={C.rain} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <h4>{t.power.temp}</h4>
          <ResponsiveContainer width="100%" height={170}>
            <LineChart data={annual} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
              {grid}<XAxis dataKey="year" {...axis} interval={4} /><YAxis {...axis} domain={['dataMin - 1', 'dataMax + 1']} />
              <Tooltip {...tip} />
              <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
              <Line isAnimationActive={false} dataKey="tmax_c" name={t.power.tmax} stroke={C.tmax} strokeWidth={2} dot={false} />
              <Line isAnimationActive={false} dataKey="tmin_c" name={t.power.tmin} stroke={C.tmin} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <p className="small src-url">{p.url}</p>
        </Source>

        <Source name="GPM IMERG" tag={t.nasaTag} nasa what={t.imerg.what} state={satState('imerg')} t={t} csv="gpm-imerg-mensual.csv" rows={sd.imerg}
          meta={[['Dataset', 'NASA/GPM_L3/IMERG_MONTHLY_V07']]}>
          {imerg.length ? <>
            <h4>{t.imerg.chart}</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={imerg} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
                {grid}<XAxis dataKey="month" {...axis} interval={5} /><YAxis {...axis} />
                <Tooltip {...tip} formatter={(v) => [`${fmt(v)} mm`, 'GPM']} />
                <Bar isAnimationActive={false} dataKey="rain_mm" fill={C.rain} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer></> : offMsg}
        </Source>

        <Source name="SMAP" tag={t.nasaTag} nasa what={t.smap.what} state={satState('smap')} t={t} csv="smap-semanal.csv" rows={sd.smap}
          meta={[['Dataset', 'NASA/SMAP/SPL4SMGP/008 · sm_surface']]}>
          {smap.length ? <>
            <h4>{t.smap.chart}</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={smap} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
                {grid}<XAxis dataKey="week" {...axis} interval={3} /><YAxis {...axis} domain={['auto', 'auto']} />
                <Tooltip {...tip} />
                <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
                <Line isAnimationActive={false} dataKey="sm" name={t.smap.now} stroke={C.sm} strokeWidth={2} dot={{ r: 3 }} />
                <Line isAnimationActive={false} dataKey="clim" name={t.smap.normal} stroke={C.clim} strokeWidth={2} strokeDasharray="5 4" dot={false} />
              </LineChart>
            </ResponsiveContainer></> : offMsg}
        </Source>

        <Source name="Landsat 8/9" tag={t.nasaTag} nasa what={t.landsat.what} state={satState('landsat')} t={t} csv="landsat-ndvi.csv" rows={sd.landsat}
          meta={[['Dataset', 'LANDSAT/LC08 + LC09 C02 T1_L2']]}>
          {ndvi.length ? <>
            <h4>{t.landsat.chart}</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={ndvi} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
                {grid}<XAxis dataKey="month" {...axis} interval={11} /><YAxis {...axis} domain={[0, 1]} />
                <Tooltip {...tip} />
                <ReferenceLine y={0.35} stroke="#b98557" strokeDasharray="4 4" />
                <Line isAnimationActive={false} dataKey="ndvi" name="NDVI" stroke={C.ndvi} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer></> : offMsg}
        </Source>

        <Source name="SRTM" tag={t.nasaTag} nasa what={t.srtm.what} state={d.terrain.elevation_m != null ? (d.terrain.slope_source === 'default' ? 'default' : 'ok') : 'off'} t={t}
          meta={[[t.srtm.elev, d.terrain.elevation_m != null ? `${fmt(d.terrain.elevation_m)} m` : '—'],
            [t.srtm.slope, `${d.terrain.slope_pct} %${d.terrain.slope_source === 'default' ? ` (${t.fallback.toLowerCase()})` : ''}`],
            ['POWER cell', `${fmt(p.cell_elevation_m)} m`]]} />

        <Source name="SoilGrids" tag={t.partnerTag} what={t.soilgrids.what} state={d.soil.source === 'soilgrids' ? 'ok' : d.soil.source === 'default' ? 'default' : 'ok'} t={t}
          meta={[[t.soilgrids.texture, t.textures[d.soil.texture] || d.soil.texture],
            ...(d.soil.values.sand != null ? [[t.soilgrids.sand, `${d.soil.values.sand} %`], [t.soilgrids.clay, `${d.soil.values.clay} %`], [t.soilgrids.soc, `${d.soil.values.soc} g/kg`]] : [])]} />

        <Source name="NOAA ONI" tag={t.partnerTag} what={t.oni.what} state="ok" t={t} csv="noaa-oni.csv" rows={d.enso.recent}>
          <h4>{t.oni.chart}</h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={oni} margin={{ top: 4, right: 4, left: -12, bottom: 0 }}>
              {grid}<XAxis dataKey="label" {...axis} interval={5} /><YAxis {...axis} />
              <Tooltip {...tip} formatter={(v) => [v, 'ONI']} />
              <ReferenceLine y={0} stroke="#c9bfae" />
              <Bar isAnimationActive={false} dataKey="anom" radius={[3, 3, 3, 3]}>
                {oni.map((o, i) => <Cell key={i} fill={o.anom >= 0.5 ? C.nino : o.anom <= -0.5 ? C.nina : C.neutral} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Source>
      </div>
      {Object.keys(se).length > 0 && sat !== 'loading' && (
        <details className="small"><summary>{t.eeNote}</summary><code>{Object.values(se)[0]}</code></details>
      )}
    </div>
  )
}
