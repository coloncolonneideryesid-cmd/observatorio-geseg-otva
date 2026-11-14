export const SEP = '||'   // separa los mensajes de error múltiples del servidor
const KEY = 'otva_token'
let token: string | null = null
try { token = sessionStorage.getItem(KEY) } catch { /* sin almacenamiento */ }

export const setToken = (t: string | null) => {
  token = t
  try { t ? sessionStorage.setItem(KEY, t) : sessionStorage.removeItem(KEY) } catch { /* ignorar */ }
}
export const hayToken = () => !!token

async function call<T>(method: string, url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) {
    let d = r.statusText
    try { d = (await r.json()).detail ?? d } catch { /* sin cuerpo */ }
    throw Object.assign(new Error(Array.isArray(d) ? d.join(SEP) : String(d)), { status: r.status })
  }
  return r.json()
}
export const get = <T,>(u: string) => call<T>('GET', u)
export const post = <T,>(u: string, b: unknown) => call<T>('POST', u, b)
export const put = <T,>(u: string, b: unknown) => call<T>('PUT', u, b)

export const fmt = (n: number) => n.toLocaleString('es-CO')
export const fecha = (s: string) => {
  const [y, m, d] = s.split('-')
  return `${d}/${m}/${y}`
}

export type Evento = {
  id: string; fecha: string; hora: string; depto: string; mpio: string; lugar: string; lat: number; lon: number
  prec_coord: string; tipo: string; mod: string; objetivo: string; clase: string; autor: string; grupo: string
  atrib: 'A' | 'B' | 'C' | 'D' | 'E'; evidencia: string; m_civ: number; m_fp: number; h_civ: number; h_fp: number
  h_nota: string; danos: string; estado: string; discrepancia: string; fuentes: string[]; actualizacion: string
  estado_v1: string; archivo: string; version: number
}
export type Resumen = {
  corte: string; excluidos: number; contexto: number; total: number; fallecidos: number; heridos: number
  fuente_unica: number; incompleto: number; por_depto: [string, number][]; por_atrib: [string, number, string][]
  por_mes: [string, number][]; por_grupo: [string, number][]; por_mod: [string, number][]
}
export type Calidad = {
  eventos: number; documentos: number; documentos_archivados: number; sin_archivar: number
  estados: Record<string, number>; estado_v0: Record<string, number>; por_n_fuentes: Record<string, number>
  dominios: [string, number][]; registros_bitacora: number
}
