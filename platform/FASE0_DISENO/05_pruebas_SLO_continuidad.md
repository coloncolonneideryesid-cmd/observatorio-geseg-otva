# Plan de pruebas, SLO y continuidad · OTVA v1

## 1. Plan de pruebas
| Tipo | Qué cubre | Criterio |
|---|---|---|
| Unitarias | `pipeline/`, `analytics/` | Cobertura ≥ 85 % |
| Propiedades (Hypothesis) | Idempotencia de ingesta, monotonía de `version`, conservación de conteos, mismo `row_hash` en dos ejecuciones | 0 fallos |
| Contrato por conector | Fixtures grabados; **nunca** fuentes reales en CI | 100 % |
| Golden files | HTML y Excel exportados | Diferencia byte a byte o justificada |
| Mutación | Reglas de verificación y atribución | Puntaje mínimo a fijar en Fase 1 |
| Seguridad automatizada | Matriz rol × endpoint; SSRF contra lista de IP internas; zip bomb; PDF con JavaScript; XML con entidades externas; inyección en filtros; límites de tasa; cabeceras; **inyección de instrucciones contra el asistente** | 100 % |
| Compuertas de publicación | Cada compuerta de ADR-002 con casos válidos e inválidos (nombre de persona, atribución sin referencia, una sola fuente no oficial) | Ningún evento inválido se autopublica |
| Carga (k6) | Panel interno, 50 usuarios concurrentes | p95 < 800 ms en consultas agregadas |
| Caos | Fuente caída, respuesta corrupta, base lenta, cola llena | Degrada con aviso; no publica incompleto como completo |

## 2. Prueba de equivalencia con la v0
1. Congelar `data/data.json` del commit `78d8e27` (42 eventos, 25 excluidos, 3 de contexto; corte 2026-11-08) como instantánea de referencia con su SHA-256.
2. Importar a la base nueva con el mapeo de `02` §5.
3. Regenerar `data.json` desde la base y comparar **campo a campo** con la referencia: igualdad exacta, salvo diferencias listadas y justificadas por escrito.
4. Ejecutar `build_html.py` y `build_xlsx.py` sobre la salida; comparar cifras del tablero y del Excel (totales, atribución A–E, víctimas, tabla por departamento) y recalcular el Excel con `recalc_check.py` (0 errores).
5. La v1 pasa a producción solo con resultado idéntico (decisión de Neider, ADR-005). Mientras tanto, la publicación diaria de la v0 sigue sin interrupción.
Nota: dado que la v0 sigue actualizándose a diario, la instantánea se actualiza hasta el día del corte de la migración.

## 3. SLO (propuestos; ajustables)
| Indicador | Objetivo |
|---|---|
| Disponibilidad del plano interno | ≥ 99,5 % mensual (el público estático depende de Vercel) |
| Ingesta diaria completada | ≥ 99 % de los días |
| Evento oficial visible como candidato | < 30 min desde su publicación en fuentes con feed |
| Falsos duplicados en muestra auditada | < 3 % |
| Eventos publicados con fuente archivada, hash y marca de tiempo | 100 % (nuevos) |
| Tiempo para retractar tras decisión | < 1 h |
| Respuesta a una solicitud de rectificación | Plazo a aprobar (propuesta 10 días hábiles) |

## 4. Continuidad
- **RPO ≤ 24 h, RTO ≤ 8 h** (ajustables).
- **Copias 3-2-1:** base y raw cifrados con `age`; una copia fuera del servidor y una inmutable o desconectada.
- **Restauración:** simulacro completo trimestral con registro del tiempo; el primero antes de pasar la v1 a producción.
- **Degradación:** si la base falla, el sitio público estático sigue sirviendo el último `dist/` firmado.
- **Claves:** dos llaves físicas, guardadas por separado; procedimiento de rotación documentado.
- **Runbooks a redactar en Fase 4:** fuente caída; sospecha de envenenamiento; compromiso de credenciales; restauración; retractación publicada; incidente de seguridad (con plazos y responsables).
- **Kill-switch:** una orden suspende la autopublicación y deja el sitio en su última versión buena.

## 5. Plan por fases (resumen)
- **Fase 1 (sem. 1–3):** esquema, raw de solo adición con manifiesto firmado, conectores (datos.gov.co, GDELT, RSS oficial) **solo tras verificar términos**, geocodificación por municipio, importación y equivalencia con la v0, bitácora encadenada.
- **Fase 2 (sem. 4–6):** flujo de dos llaves, Admiralty, confianza, API con RLS, MFA, matriz de autorización.
- **Fase 3 (sem. 7–9):** indicadores, EWMA/CUSUM, H3 y Gi*, pronóstico validado frente a baseline, alertas calibradas. Con 42 eventos, **la mayoría de estos métodos no tiene datos suficientes**: se activarán por módulo cuando haya muestra, y mientras tanto se declara por qué no se calculan.
- **Fase 4 (sem. 10–12):** módulos de tablero, exportador firmado, DAST y pentest interno, simulacro de restauración, runbooks, metodología pública.

## 6. Criterios de aceptación (medibles)
100 % de eventos publicados nuevos con fuente archivada y hash; ningún evento A–D sin referencia de atribución; matriz de autorización al 100 % y sin endpoints sin control; 0 hallazgos críticos o altos abiertos; restauración dentro del RTO; mismo `row_hash` en dos ejecuciones; cobertura y mutación según §1; informe de calibración de alertas; documento público de metodología con fórmulas, límites y política de rectificación.
