import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { get, fecha } from '../api'
import type { Evento } from '../api'

const COLOR: Record<string, string> = { A: '#0D1F3C', B: '#0053BB', C: '#3b6fb8', D: '#7a8fb3', E: '#C0392B' }

/** Mapa: la coordenada de la v0 es el centroide municipal, así que se dibuja un círculo de ~8 km (no un punto exacto). */
export default function Mapa() {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<L.Map | null>(null)
  const capa = useRef<L.LayerGroup | null>(null)
  const base = useRef<L.TileLayer | null>(null)
  const [ev, setEv] = useState<Evento[]>([])
  const [sel, setSel] = useState<Evento | null>(null)
  const [conBase, setConBase] = useState(true)
  const [dep, setDep] = useState('')
  const [err, setErr] = useState('')

  useEffect(() => { get<Evento[]>('/api/eventos').then(setEv).catch(e => setErr(e.message)) }, [])
  useEffect(() => {
    if (!el.current || map.current) return
    map.current = L.map(el.current, { center: [4.6, -74.1], zoom: 6, zoomControl: true })
    capa.current = L.layerGroup().addTo(map.current)
    return () => { map.current?.remove(); map.current = null }
  }, [])
  useEffect(() => {
    if (!map.current) return
    base.current?.remove()
    if (conBase) base.current = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 12, attribution: '© OpenStreetMap' }).addTo(map.current)
  }, [conBase])
  useEffect(() => {
    if (!capa.current) return
    capa.current.clearLayers()
    ev.filter(e => !dep || e.depto === dep).forEach(e => {
      L.circle([e.lat, e.lon], { radius: 8000, color: COLOR[e.atrib], weight: 1, fillColor: COLOR[e.atrib], fillOpacity: 0.35 })
        .on('click', () => setSel(e)).bindTooltip(`${e.mpio} · ${e.id}`).addTo(capa.current!)
    })
  }, [ev, dep])

  const deptos = [...new Set(ev.map(e => e.depto))].sort()
  return (
    <>
      <h2>Mapa</h2>
      <p className="lead">Cada círculo es el área aproximada del municipio, no el lugar exacto. Color = nivel de atribución según las fuentes.</p>
      <div className="filtros">
        <select value={dep} onChange={e => setDep(e.target.value)} aria-label="Departamento"><option value="">Todos los departamentos</option>{deptos.map(d => <option key={d}>{d}</option>)}</select>
        <label><input type="checkbox" checked={conBase} onChange={e => setConBase(e.target.checked)} /> Mapa base (OpenStreetMap, requiere internet)</label>
      </div>
      {err && <p className="err">{err}</p>}
      <div className="grid g2">
        <div className="map" ref={el} aria-label="Mapa de incidentes" />
        <div className="card">
          {!sel ? <p className="lead">Seleccione un círculo para ver la ficha.</p> : (
            <><h3>{sel.id} · {sel.mpio}, {sel.depto}</h3>
              <dl><dt>Fecha</dt><dd>{fecha(sel.fecha)} · {sel.hora}</dd><dt>Hecho</dt><dd>{sel.tipo}</dd><dt>Modalidad</dt><dd>{sel.mod}</dd>
                <dt>Presunto autor</dt><dd>{sel.autor} <span className="chip">{sel.atrib}</span></dd><dt>Base</dt><dd>{sel.evidencia}</dd>
                <dt>Víctimas</dt><dd>{sel.m_civ + sel.m_fp} fallecidos · {sel.h_civ + sel.h_fp} heridos</dd>
                {sel.discrepancia && <><dt>Versiones distintas</dt><dd>⚠ {sel.discrepancia}</dd></>}
                <dt>Estado</dt><dd>{sel.estado} · v1: {sel.estado_v1}</dd>
                <dt>Fuentes</dt><dd>{sel.fuentes.map((u, i) => <div key={u}><a href={u} target="_blank" rel="noopener noreferrer">[{i + 1}] {new URL(u).hostname.replace('www.', '')}</a></div>)}</dd></dl></>)}
        </div>
      </div>
    </>
  )
}
