import { useEffect, useState } from 'react'
import { get } from '../api'
import type { Calidad } from '../api'

export default function Fuentes() {
  const [c, setC] = useState<Calidad | null>(null)
  useEffect(() => { get<Calidad>('/api/calidad').then(setC) }, [])
  if (!c) return <p>Cargando…</p>
  const fila = (k: string, v: number | string) => <tr key={k}><td>{k}</td><td>{v}</td></tr>
  return (
    <>
      <h2>Fuentes y calidad</h2>
      <p className="lead">Estado real de la evidencia y del proceso de verificación.</p>
      <div className="grid g2">
        <div className="card"><h3>Archivo de la evidencia</h3><table><tbody>
          {fila('Documentos de fuente vinculados', c.documentos)}{fila('Con captura archivada (hash y fecha)', c.documentos_archivados)}
          {fila('Eventos sin archivar (históricos)', `${c.sin_archivar} de ${c.eventos}`)}{fila('Registros en la bitácora de datos', c.registros_bitacora)}</tbody></table>
          <p className="lead" style={{ marginTop: 8 }}>Los eventos de la v0 se registraron antes de existir el archivo de capturas; se archivarán mientras la fuente siga disponible.</p></div>
        <div className="card"><h3>Estado de verificación (v1)</h3><table><tbody>{Object.entries(c.estados).map(([k, v]) => fila(k, v))}</tbody></table>
          <p className="lead" style={{ marginTop: 8 }}>Ningún evento tiene revisión independiente. VERIFICADO_INDEPENDIENTE está reservado hasta que exista el revisor (R13) y un aprobador distinto.</p></div>
        <div className="card"><h3>Estado según la v0</h3><table><tbody>{Object.entries(c.estado_v0).map(([k, v]) => fila(k, v))}</tbody></table></div>
        <div className="card"><h3>Fuentes por registro</h3><table><tbody>{Object.entries(c.por_n_fuentes).sort().map(([k, v]) => fila(`${k} fuente(s)`, v))}</tbody></table>
          <p className="lead" style={{ marginTop: 8 }}>Los registros con una sola fuente se cuentan como información incompleta.</p></div>
        <div className="card" style={{ gridColumn: '1 / -1' }}><h3>Medios y entidades citados</h3><table><tbody>{c.dominios.map(([d, n]) => fila(d, n))}</tbody></table></div>
      </div>
    </>
  )
}
