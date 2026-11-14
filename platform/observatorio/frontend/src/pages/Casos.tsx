import { useEffect, useMemo, useState } from 'react'
import { get, post, put, fecha, SEP } from '../api'
import type { Evento } from '../api'

type Caso = Evento & { event_id: string; creado_por: string; origen_app: boolean }
type Cat = { mods: string[]; grupos: string[]; estados: string[]; prec: string[]; horas: string[]; objetivos: string[]; clases: string[]; municipios: Record<string, Record<string, [number, number]>> }
type Accion = { ts: string; usuario: string; rol: string; accion: string; estado_de: string | null; estado_a: string | null; nota: string | null; version: number }

const ESTADOS = ['CANDIDATO', 'PRELIMINAR', 'VERIFICADO_EQUIPO', 'RETRACTADO', 'DESCARTADO']
const ROT: Record<string, string> = { CANDIDATO: 'Candidato (cola interna)', PRELIMINAR: 'Preliminar (publicable)', VERIFICADO_EQUIPO: 'Verificado por el equipo', RETRACTADO: 'Retractado', DESCARTADO: 'Descartado', VERIFICADO_INDEPENDIENTE: 'Verificado independiente' }
const VACIO = {
  fecha: '', hora: 'Sin dato', depto: '', mpio: '', lugar: '', lat: '', lon: '', prec_coord: 'Municipal aproximada', tipo: '', mod: '', objetivo: 'Fuerza Pública',
  clase: 'Incierto – autoría y finalidad no establecidas', autor: 'No determinado', grupo: 'No determinado', atrib: 'E', evidencia: 'Ninguna autoridad ha atribuido el hecho.',
  m_civ: 0, m_fp: 0, h_civ: 0, h_fp: 0, h_nota: 'No documentado', danos: 'No documentado', eco: 'No cuantificado', desplaz: 'No documentado', servicios: 'No documentado',
  estado: 'Preliminar', discrepancia: '', fuentes: '',
}
type Form = typeof VACIO

const errores = (e: any): string[] => String(e.message || e).split(SEP).filter(Boolean)

export default function Casos({ rol, usuario }: { rol: string; usuario: string }) {
  const [lista, setLista] = useState<Caso[]>([])
  const [cat, setCat] = useState<Cat | null>(null)
  const [filtro, setFiltro] = useState('CANDIDATO')
  const [sel, setSel] = useState<string | null>(null)
  const [hist, setHist] = useState<Accion[]>([])
  const [form, setForm] = useState<{ modo: 'nuevo' | 'editar'; v: Form } | null>(null)
  const [msg, setMsg] = useState<{ ok: boolean; t: string[] } | null>(null)
  const admin = rol === 'admin'

  const cargar = () => get<Caso[]>('/api/casos').then(setLista).catch(e => setMsg({ ok: false, t: errores(e) }))
  useEffect(() => { cargar(); get<Cat>('/api/catalogos').then(setCat) }, [])
  const c = lista.find(x => x.id === sel) || null
  useEffect(() => { if (c) get<Accion[]>(`/api/casos/${c.id}/historial`).then(setHist); else setHist([]) }, [sel, lista])

  const cuenta = useMemo(() => Object.fromEntries(ESTADOS.map(s => [s, lista.filter(x => x.estado_v1 === s).length])), [lista])
  const filas = lista.filter(x => !filtro || x.estado_v1 === filtro).slice().reverse()

  const actuar = async (fn: () => Promise<any>, ok: string) => {
    setMsg(null)
    try { await fn(); await cargar(); setMsg({ ok: true, t: [ok] }) } catch (e: any) { setMsg({ ok: false, t: errores(e) }) }
  }
  const trans = (a: string, pedirMotivo: boolean) => {
    const motivo = pedirMotivo ? (window.prompt('Indique el motivo (mínimo 10 caracteres):') || '') : ''
    if (pedirMotivo && !motivo) return
    actuar(() => post(`/api/casos/${c!.id}/transicion`, { a, motivo }), `Caso ${c!.id}: ${ROT[a]}`)
  }

  const guardar = async () => {
    if (!form) return
    const f = form.v
    const reg: any = { ...f, lat: Number(f.lat), lon: Number(f.lon), m_civ: Number(f.m_civ), m_fp: Number(f.m_fp), h_civ: Number(f.h_civ), h_fp: Number(f.h_fp),
      fuentes: f.fuentes.split('\n').map(s => s.trim()).filter(Boolean) }
    setMsg(null)
    try {
      if (form.modo === 'nuevo') { const r = await post<{ id: string }>('/api/casos', reg); setSel(r.id); setFiltro('CANDIDATO'); setMsg({ ok: true, t: [`Caso ${r.id} creado como candidato. Aún no es público.`] }) }
      else {
        const cambios: any = {}
        const orig: any = { ...c, fuentes: c!.fuentes }
        for (const k of Object.keys(reg)) if (JSON.stringify(reg[k]) !== JSON.stringify(orig[k])) cambios[k] = reg[k]
        await put(`/api/casos/${c!.id}`, { cambios, nota: 'Edición desde el tablero' })
        setMsg({ ok: true, t: [`Caso ${c!.id} actualizado (nueva versión).`] })
      }
      setForm(null); await cargar()
    } catch (e: any) { setMsg({ ok: false, t: errores(e) }) }
  }

  const editar = () => c && setForm({ modo: 'editar', v: { ...(c as any), lat: String(c.lat), lon: String(c.lon), fuentes: c.fuentes.join('\n') } })
  const set = (k: keyof Form, v: string | number) => setForm(f => {
    if (!f) return f
    const n = { ...f.v, [k]: v } as Form
    const ll = cat?.municipios[n.depto]?.[n.mpio]
    if ((k === 'mpio' || k === 'depto') && ll) { n.lat = String(ll[0]); n.lon = String(ll[1]) }
    if (k === 'atrib' && v === 'E') n.grupo = 'No determinado'
    return { ...f, v: n }
  })

  const sync = () => actuar(async () => { const r: any = await post('/api/sincronizar', {}); setMsg({ ok: true, t: [`Sincronizado: ${r.nuevos.length} nuevos, ${r.editados.length} editados${r.conflictos.length ? `; CONFLICTOS: ${r.conflictos.join(', ')}` : ''}`] }) }, 'Sincronizado')
  const exportar = () => actuar(async () => { const r: any = await post('/api/exportar', {}); setMsg({ ok: true, t: [`Exportados ${r.eventos} casos publicables (corte ${r.corte}). Archivo: ${r.ruta} · SHA-256 ${r.sha256.slice(0, 16)}…`] }) }, 'Exportado')

  const inp = (k: keyof Form, tipo = 'text') => <input type={tipo} value={String(form!.v[k])} onChange={e => set(k, e.target.value)} />
  const sel1 = (k: keyof Form, op: string[]) => <select value={String(form!.v[k])} onChange={e => set(k, e.target.value)}>{op.map(o => <option key={o}>{o}</option>)}</select>

  return (
    <>
      <h2>Casos: registro y revisión</h2>
      <p className="lead">Aquí se registran, revisan y retractan los casos. Un caso nuevo nace como <b>candidato</b> (no es público) y solo pasa a preliminar si cumple las compuertas: fuente oficial o dos fuentes independientes, atribución con base y sin datos de personas.</p>
      <div className="filtros">
        <button className="btn" onClick={() => setForm({ modo: 'nuevo', v: { ...VACIO } })}>+ Nuevo caso</button>
        {admin && <><button className="btn" onClick={sync}>Sincronizar con la v0</button><button className="btn" onClick={exportar}>Exportar data.json publicable</button></>}
        {ESTADOS.map(s => <button key={s} className={`chip${filtro === s ? ' on' : ''}`} style={{ cursor: 'pointer', background: filtro === s ? 'var(--blue)' : undefined, color: filtro === s ? '#fff' : undefined }} onClick={() => setFiltro(filtro === s ? '' : s)}>{ROT[s]} · {cuenta[s]}</button>)}
      </div>
      {msg && <div className="note" role="status" style={{ borderLeftColor: msg.ok ? 'var(--blue)' : 'var(--alert)' }}>{msg.t.map((t, i) => <div key={i}>{t}</div>)}</div>}

      {form && <div className="card" style={{ marginBottom: 14 }}>
        <h3>{form.modo === 'nuevo' ? 'Nuevo caso (candidato)' : `Editar ${c!.id}`}</h3>
        <div className="grid g2" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))' }}>
          <label>Fecha del hecho{inp('fecha', 'date')}</label><label>Hora{sel1('hora', cat?.horas || [])}</label>
          <label>Departamento<input list="deptos" value={form.v.depto} onChange={e => set('depto', e.target.value)} /></label>
          <label>Municipio<input list="mpios" value={form.v.mpio} onChange={e => set('mpio', e.target.value)} /></label>
          <datalist id="deptos">{Object.keys(cat?.municipios || {}).map(d => <option key={d} value={d} />)}</datalist>
          <datalist id="mpios">{Object.keys(cat?.municipios[form.v.depto] || {}).map(d => <option key={d} value={d} />)}</datalist>
          <label>Latitud (centroide municipal){inp('lat', 'number')}</label><label>Longitud{inp('lon', 'number')}</label>
          <label>Lugar{inp('lugar')}</label><label>Modalidad{sel1('mod', ['', ...(cat?.mods || [])])}</label>
          <label style={{ gridColumn: '1 / -1' }}>Qué ocurrió (según las fuentes){inp('tipo')}</label>
          <label>Objetivo<input list="objs" value={form.v.objetivo} onChange={e => set('objetivo', e.target.value)} /></label>
          <datalist id="objs">{(cat?.objetivos || []).map(o => <option key={o} value={o} />)}</datalist>
          <label>Nivel de atribución{sel1('atrib', ['A', 'B', 'C', 'D', 'E'])}</label>
          <label>Atribuido a{sel1('grupo', cat?.grupos || [])}</label><label>Texto de la fuente sobre el autor{inp('autor')}</label>
          <label style={{ gridColumn: '1 / -1' }}>Base de la atribución (quién atribuye y con qué acto){inp('evidencia')}</label>
          <label>Fallecidos civiles{inp('m_civ', 'number')}</label><label>Fallecidos Fuerza Pública{inp('m_fp', 'number')}</label>
          <label>Heridos civiles{inp('h_civ', 'number')}</label><label>Heridos Fuerza Pública{inp('h_fp', 'number')}</label>
          <label style={{ gridColumn: '1 / -1' }}>Nota sobre heridos{inp('h_nota')}</label><label>Daños{inp('danos')}</label><label>Estado de la información{sel1('estado', cat?.estados || [])}</label>
          <label style={{ gridColumn: '1 / -1' }}>Versiones distintas entre fuentes (si las hay){inp('discrepancia')}</label>
          <label style={{ gridColumn: '1 / -1' }}>Fuentes: un enlace https:// por línea (máximo 3). Sin nombres de víctimas.
            <textarea rows={3} value={form.v.fuentes} onChange={e => set('fuentes', e.target.value)} style={{ width: '100%' }} /></label>
        </div>
        <p className="lead">La coordenada se completa sola si el municipio ya existe; es el centro del municipio, no el lugar exacto.</p>
        <button className="btn" onClick={guardar}>Guardar</button> <button className="btn" style={{ background: 'var(--mute)' }} onClick={() => setForm(null)}>Cancelar</button>
      </div>}

      <div className="grid g2">
        <div className="card" style={{ overflow: 'auto', maxHeight: 520 }}>
          <table><thead><tr><th>Id</th><th>Fecha</th><th>Municipio</th><th>Modalidad</th><th>Estado</th><th>Creó</th></tr></thead>
            <tbody>{filas.map(x => <tr key={x.id} className={x.id === sel ? 'sel' : ''} onClick={() => setSel(x.id)}><td>{x.id}</td><td>{fecha(x.fecha)}</td><td>{x.mpio}</td><td>{x.mod}</td><td>{ROT[x.estado_v1]}</td><td>{x.creado_por}</td></tr>)}</tbody></table>
          {!filas.length && <p className="lead">No hay casos en este estado.</p>}
        </div>
        <div className="card">{!c ? <p className="lead">Seleccione un caso.</p> : <>
          <h3>{c.id} · {c.mpio}, {c.depto} <span className="chip">{ROT[c.estado_v1]}</span></h3>
          <dl><dt>Hecho</dt><dd>{c.tipo}</dd><dt>Modalidad</dt><dd>{c.mod}</dd><dt>Atribución</dt><dd>{c.grupo} · nivel {c.atrib} · {c.evidencia}</dd>
            <dt>Víctimas</dt><dd>{c.m_civ + c.m_fp} fallecidos · {c.h_civ + c.h_fp} heridos</dd>
            <dt>Fuentes</dt><dd>{c.fuentes.map((u, i) => <div key={u}><a href={u} target="_blank" rel="noopener noreferrer">[{i + 1}] {new URL(u).hostname.replace('www.', '')}</a></div>)}</dd>
            <dt>Versión</dt><dd>{c.version}</dd></dl>
          <div className="filtros" style={{ marginTop: 12 }}>
            {!['RETRACTADO', 'DESCARTADO'].includes(c.estado_v1) && <button className="btn" onClick={editar}>Editar</button>}
            {c.estado_v1 === 'CANDIDATO' && <><button className="btn" onClick={() => trans('PRELIMINAR', false)}>Pasar a preliminar (publicable)</button><button className="btn" style={{ background: 'var(--mute)' }} onClick={() => trans('DESCARTADO', true)}>Descartar</button></>}
            {admin && c.estado_v1 === 'PRELIMINAR' && <button className="btn" disabled={c.creado_por === usuario} title={c.creado_por === usuario ? 'Dos llaves: lo debe verificar otra persona' : ''} onClick={() => trans('VERIFICADO_EQUIPO', false)}>Verificar (equipo)</button>}
            {admin && ['PRELIMINAR', 'VERIFICADO_EQUIPO'].includes(c.estado_v1) && <button className="btn" style={{ background: 'var(--alert)' }} onClick={() => trans('RETRACTADO', true)}>Retractar</button>}
          </div>
          <p className="lead">La verificación independiente (R13) está reservada y no se puede asignar hasta que exista ese rol.</p>
          <h3>Historial</h3>
          <table><tbody>{hist.map((h, i) => <tr key={i}><td>{h.ts.replace('T', ' ').slice(0, 16)}</td><td>{h.usuario} ({h.rol})</td><td>{h.accion}{h.estado_a ? ` → ${h.estado_a}` : ''}</td><td>{h.nota}</td></tr>)}</tbody></table>
        </>}</div>
      </div>
    </>
  )
}
