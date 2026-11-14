import { useEffect, useMemo, useState } from 'react'
import { get, fmt, fecha } from '../api'
import type { Resumen } from '../api'
import Chart from '../components/Chart'

export default function Panorama() {
  const [r, setR] = useState<Resumen | null>(null)
  const [err, setErr] = useState('')
  useEffect(() => { get<Resumen>('/api/resumen').then(setR).catch(e => setErr(e.message)) }, [])

  const dep = useMemo(() => r && ({
    grid: { left: 130, right: 20, top: 10, bottom: 20 }, tooltip: {},
    xAxis: { type: 'value' }, yAxis: { type: 'category', inverse: true, data: r.por_depto.slice(0, 10).map(x => x[0]) },
    series: [{ type: 'bar', data: r.por_depto.slice(0, 10).map(x => x[1]), label: { show: true, position: 'right' } }],
  }), [r])
  const mes = useMemo(() => r && ({
    grid: { left: 40, right: 20, top: 20, bottom: 30 }, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: r.por_mes.map(x => x[0]) }, yAxis: { type: 'value' },
    series: [{ type: 'bar', data: r.por_mes.map(x => x[1]), label: { show: true, position: 'top' } }],
  }), [r])
  const atr = useMemo(() => r && ({
    tooltip: { trigger: 'item' }, legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['40%', '68%'], data: r.por_atrib.filter(x => x[1] > 0).map(x => ({ name: `${x[0]} · ${x[2]}`, value: x[1] })), label: { formatter: '{c}' } }],
  }), [r])

  if (err) return <p className="err">{err}</p>
  if (!r) return <p>Cargando…</p>
  const sinAutor = r.por_atrib.find(x => x[0] === 'E')?.[1] ?? 0
  return (
    <>
      <h2>Panorama general</h2>
      <p className="lead">Corte {fecha(r.corte)} · {r.total} incidentes documentados con fuentes abiertas desde el 7 de agosto de 2026.</p>
      <div className="grid k4">
        <div className="card kpi"><b>{fmt(r.total)}</b><span>Incidentes registrados</span></div>
        <div className="card kpi"><b>{fmt(r.fallecidos)}</b><span>Fallecidos (balance oficial más reciente)</span></div>
        <div className="card kpi"><b>{fmt(r.heridos)}</b><span>Heridos</span></div>
        <div className="card kpi"><b>{Math.round(100 * sinAutor / r.total)} %</b><span>Sin autoría atribuida (nivel E): {sinAutor} de {r.total}</span></div>
        <div className="card kpi"><b>{Math.round(100 * r.incompleto / r.total)} %</b><span>Información incompleta (fuente única o no confirmado)</span></div>
      </div>
      <div className="note">La base es una muestra documentada con fuentes abiertas, no el universo de los hechos violentos del país. Las variaciones pueden reflejar la cobertura de las fuentes y no solo cambios en la violencia.</div>
      <div className="grid g2">
        <div className="card"><h3>{r.por_depto.slice(0, 3).map(x => x[0]).join(', ')} concentran {Math.round(100 * r.por_depto.slice(0, 3).reduce((a, x) => a + x[1], 0) / r.total)} % de los registros</h3>{dep && <Chart option={dep} label="Incidentes por departamento" />}</div>
        <div className="card"><h3>Incidentes por mes de ocurrencia</h3>{mes && <Chart option={mes} label="Incidentes por mes" />}</div>
        <div className="card"><h3>Atribución según las fuentes (A–E)</h3>{atr && <Chart option={atr} label="Niveles de atribución" />}</div>
        <div className="card"><h3>Presuntos responsables según las fuentes</h3>
          <table><tbody>{r.por_grupo.map(([g, n]) => <tr key={g}><td>{g}</td><td>{n}</td></tr>)}</tbody></table>
          <p className="lead" style={{ marginTop: 8 }}>La atribución es la que hace cada fuente; no se infiere por presencia territorial ni por modalidad.</p></div>
      </div>
    </>
  )
}
