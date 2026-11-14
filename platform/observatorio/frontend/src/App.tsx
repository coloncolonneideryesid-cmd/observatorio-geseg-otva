import { useEffect, useState } from 'react'
import { get, post, setToken, hayToken } from './api'
import Panorama from './pages/Panorama'
import Mapa from './pages/Mapa'
import Eventos from './pages/Eventos'
import Fuentes from './pages/Fuentes'
import Casos from './pages/Casos'

const MODULOS: { id: string; n: string; t: string; C: any; solo?: string[] }[] = [
  { id: 'panorama', n: '01', t: 'Panorama general', C: Panorama },
  { id: 'mapa', n: '02', t: 'Mapa', C: Mapa },
  { id: 'eventos', n: '03', t: 'Base de eventos', C: Eventos },
  { id: 'fuentes', n: '04', t: 'Fuentes y calidad', C: Fuentes },
  { id: 'casos', n: '05', t: 'Casos: registro y revisión', C: Casos, solo: ['editor', 'admin'] },
]

function Ingreso({ onOk }: { onOk: (cambiar: boolean, u: string) => void }) {
  const [u, setU] = useState('admin')
  const [c, setC] = useState('')
  const [err, setErr] = useState('')
  const entrar = async (ev: React.FormEvent) => {
    ev.preventDefault(); setErr('')
    try { const r = await post<{ token: string; cambiar_clave: boolean; usuario: string }>('/api/login', { usuario: u, clave: c }); setToken(r.token); onOk(r.cambiar_clave, r.usuario) }
    catch (e: any) { setErr(e.message) }
  }
  return (
    <form className="login card" onSubmit={entrar}>
      <h2>Observatorio OTVA</h2><p className="lead">Análisis estratégico de violencia armada con fuentes abiertas · GESEG</p>
      <label>Usuario<input value={u} onChange={e => setU(e.target.value)} autoComplete="username" /></label>
      <label>Clave<input type="password" value={c} onChange={e => setC(e.target.value)} autoComplete="current-password" /></label>
      <div className="err" role="alert">{err}</div><button className="btn">Ingresar</button>
    </form>)
}

function CambioClave({ onOk }: { onOk: () => void }) {
  const [a, setA] = useState(''); const [b, setB] = useState(''); const [err, setErr] = useState('')
  const enviar = async (ev: React.FormEvent) => {
    ev.preventDefault()
    if (a !== b) return setErr('Las claves no coinciden')
    try { const r = await post<{ token: string }>('/api/clave', { nueva: a }); setToken(r.token); onOk() } catch (e: any) { setErr(e.message) }
  }
  return (
    <form className="login card" onSubmit={enviar}>
      <h2>Cree su clave personal</h2><p className="lead">Por seguridad debe cambiar la clave inicial (mínimo 10 caracteres).</p>
      <label>Nueva clave<input type="password" value={a} onChange={e => setA(e.target.value)} autoComplete="new-password" /></label>
      <label>Repita la clave<input type="password" value={b} onChange={e => setB(e.target.value)} autoComplete="new-password" /></label>
      <div className="err" role="alert">{err}</div><button className="btn">Guardar</button>
    </form>)
}

export default function App() {
  const [estado, setEstado] = useState<'ingreso' | 'cambio' | 'app'>(hayToken() ? 'app' : 'ingreso')
  const [mod, setMod] = useState('panorama')
  const [usuario, setUsuario] = useState('')
  const [rol, setRol] = useState('lector')
  const [tema, setTema] = useState<string>(() => { try { return localStorage.getItem('otva_tema') || 'light' } catch { return 'light' } })
  useEffect(() => { document.documentElement.dataset.theme = tema; try { localStorage.setItem('otva_tema', tema) } catch { /* ignorar */ } }, [tema])
  useEffect(() => { if (estado === 'app') get<{ usuario: string; rol: string }>('/api/yo').then(r => { setUsuario(r.usuario); setRol(r.rol) }).catch(() => { setToken(null); setEstado('ingreso') }) }, [estado])

  if (estado === 'ingreso') return <Ingreso onOk={(c, u) => { setUsuario(u); setEstado(c ? 'cambio' : 'app') }} />
  if (estado === 'cambio') return <CambioClave onOk={() => setEstado('app')} />
  const visibles = MODULOS.filter(m => !m.solo || m.solo.includes(rol))
  const M = (visibles.find(m => m.id === mod) || visibles[0]).C
  return (
    <>
      <header className="top"><b>OBSERVATORIO OTVA</b><span>Terrorismo y violencia armada · GESEG</span><span className="sp" />
        <span>{usuario} · {rol}</span>
        <button onClick={() => setTema(t => t === 'light' ? 'dark' : 'light')}>{tema === 'light' ? 'Tema oscuro' : 'Tema claro'}</button>
        <button onClick={() => { setToken(null); setEstado('ingreso') }}>Salir</button></header>
      <div className="banner" role="note"><strong>Preliminar, sin revisión independiente.</strong> Las atribuciones son las de las fuentes citadas, no hechos probados. Análisis estratégico de fuentes abiertas; no es producto de inteligencia.</div>
      <nav className="tabs" aria-label="Módulos">{visibles.map(m => <button key={m.id} className={m.id === mod ? 'on' : ''} onClick={() => setMod(m.id)}>{m.n} · {m.t}</button>)}</nav>
      <main><M rol={rol} usuario={usuario} /></main>
    </>)
}
