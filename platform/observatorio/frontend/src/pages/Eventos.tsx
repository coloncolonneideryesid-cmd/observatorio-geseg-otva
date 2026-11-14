import { useEffect, useMemo, useState } from 'react'
import { get, fecha } from '../api'
import type { Evento } from '../api'

type K = 'id' | 'fecha' | 'depto' | 'mpio' | 'mod' | 'grupo' | 'atrib' | 'estado'
const COLS: [K, string][] = [['id', 'Id'], ['fecha', 'Fecha'], ['depto', 'Departamento'], ['mpio', 'Municipio'], ['mod', 'Modalidad'], ['grupo', 'Atribuido a'], ['atrib', 'Nivel'], ['estado', 'Estado']]

export default function Eventos() {
  const [ev, setEv] = useState<Evento[]>([])
  const [q, setQ] = useState('')
  const [atr, setAtr] = useState('')
  const [ord, setOrd] = useState<{ k: K; d: 1 | -1 }>({ k: 'fecha', d: -1 })
  const [sel, setSel] = useState<string | null>(null)
  useEffect(() => { get<Evento[]>('/api/eventos').then(setEv) }, [])

  const filas = useMemo(() => {
    const t = q.trim().toLowerCase()
    return ev.filter(e => (!atr || e.atrib === atr) && (!t || (e.mpio + e.depto + e.tipo + e.id).toLowerCase().includes(t)))
      .sort((a, b) => String(a[ord.k]).localeCompare(String(b[ord.k])) * ord.d || a.id.localeCompare(b.id))
  }, [ev, q, atr, ord])
  const e = ev.find(x => x.id === sel)

  const csv = () => {
    const f = ['id', 'fecha', 'depto', 'mpio', 'mod', 'grupo', 'atrib', 'estado', 'm_civ', 'm_fp', 'h_civ', 'h_fp', 'fuentes'] as const
    const qt = (v: unknown) => '"' + String(Array.isArray(v) ? v.join(' | ') : v).replace(/"/g, '""') + '"'
    const blob = new Blob(['﻿' + [f.join(','), ...filas.map(x => f.map(k => qt(x[k])).join(','))].join('\n')], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'otva_eventos.csv'; a.click()
  }

  return (
    <>
      <h2>Base de eventos</h2>
      <p className="lead">{filas.length} de {ev.length} incidentes. Haga clic en un encabezado para ordenar y en una fila para ver el detalle.</p>
      <div className="filtros">
        <input placeholder="Buscar municipio, departamento o hecho" value={q} onChange={x => setQ(x.target.value)} aria-label="Buscar" />
        <select value={atr} onChange={x => setAtr(x.target.value)} aria-label="Nivel de atribución"><option value="">Todos los niveles</option>{'ABCDE'.split('').map(l => <option key={l}>{l}</option>)}</select>
        <button className="btn" onClick={csv}>Descargar CSV</button>
      </div>
      <div className="grid g2">
        <div className="card" style={{ overflow: 'auto', maxHeight: 560 }}>
          <table><thead><tr>{COLS.map(([k, l]) => <th key={k} onClick={() => setOrd(o => ({ k, d: o.k === k ? (-o.d as 1 | -1) : 1 }))}>{l}{ord.k === k ? (ord.d > 0 ? ' ▲' : ' ▼') : ''}</th>)}</tr></thead>
            <tbody>{filas.map(x => <tr key={x.id} className={x.id === sel ? 'sel' : ''} onClick={() => setSel(x.id)}>
              <td>{x.id}</td><td>{fecha(x.fecha)}</td><td>{x.depto}</td><td>{x.mpio}</td><td>{x.mod}</td><td>{x.grupo}</td><td><span className="chip">{x.atrib}</span></td><td>{x.estado}</td></tr>)}</tbody></table>
        </div>
        <div className="card">{!e ? <p className="lead">Seleccione una fila.</p> : (
          <><h3>{e.id} · {e.mpio}, {e.depto}</h3>
            <dl><dt>Hecho</dt><dd>{e.tipo}</dd><dt>Lugar</dt><dd>{e.lugar}</dd><dt>Objetivo</dt><dd>{e.objetivo}</dd><dt>Clase</dt><dd>{e.clase}</dd>
              <dt>Presunto autor</dt><dd>{e.autor}</dd><dt>Base</dt><dd>{e.evidencia}</dd>
              <dt>Víctimas</dt><dd>{e.m_civ} civiles y {e.m_fp} de fuerza pública fallecidos · {e.h_civ} y {e.h_fp} heridos. {e.h_nota}</dd>
              <dt>Daños</dt><dd>{e.danos}</dd>{e.discrepancia && <><dt>Versiones distintas</dt><dd>⚠ {e.discrepancia}</dd></>}
              <dt>Coordenada</dt><dd>{e.prec_coord}</dd><dt>Actualizado</dt><dd>{fecha(e.actualizacion)}</dd>
              <dt>Fuentes</dt><dd>{e.fuentes.map((u, i) => <div key={u}><a href={u} target="_blank" rel="noopener noreferrer">[{i + 1}] {new URL(u).hostname.replace('www.', '')}</a></div>)}</dd></dl></>)}</div>
      </div>
    </>
  )
}
