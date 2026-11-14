# OTVA v1 · Fase 0 (diseño) · Borrador para aprobación de Neider

Estado: **Fase 0 aprobada por Neider el 2026-11-09** (las decisiones abiertas A–F siguen pendientes; la Fase 1 no ha empezado). Antes: borrador, sin código. Fecha de elaboración: 2026-11-09. Revisión independiente: **pendiente (R13: Neider; aprobación: Omar Rubiano Castro o Fernanda María)**. La revisión jurídica de la DPIA y de la matriz legal está **PENDIENTE**. Producto de GESEG; no es producto de la DNI ni lleva su respaldo. Rama de trabajo propuesta: `v1`; todo vive bajo `platform/` y no toca `data/`, `src/` ni `dist/` de la v0.

## Naturaleza del producto (precisión de Neider, 9-nov-2026)
El OTVA es **análisis estratégico y prospectivo de fuentes abiertas**. GESEG **no hace inteligencia** ni contrainteligencia. En todo texto, rótulo y documento del producto se evita «inteligencia» y «OSINT» (inteligencia de fuentes abiertas); se usa «fuentes abiertas» y «análisis estratégico». Coherente con el programa (DM-3: «análisis estratégico de fuentes abiertas»).
Consecuencias para el diseño:
- **Alertas tempranas (M6):** se presentan como **señales de seguimiento y alerta temprana analítica** sobre información pública (niveles Seguimiento / Atención / Alerta / Alerta alta, definidos antes de monitorear), no como producto de inteligencia.
- **Prospectiva:** el tablero incorpora escenarios y señales por horizonte (módulo del marco analítico de GESEG). Escalas verbales de probabilidad **sin porcentajes**, salvo que un método lo justifique con validación fuera de muestra. Esto sustituye lo pedido en el prompt (probabilidad calibrada con Brier) hasta que haya datos para justificarlo.
- Los atributos «reservado» y «sin acceso a información reservada» se mantienen como límites.

## Contenido
| Archivo | Qué contiene |
|---|---|
| `01_ADR.md` | Diez decisiones de arquitectura (ADR-001 a ADR-010), con alternativas y excepciones |
| `02_ERD_y_diccionario.md` | ERD, diccionario de datos, taxonomía con definiciones operativas, mapeo v0 → v1 |
| `03_modelo_amenazas.md` | STRIDE + ATT&CK/ATLAS, matriz riesgo × control |
| `04_DPIA_y_cumplimiento.md` | DPIA preliminar y matriz ASVS / ISO 27001 / MSPI (borrador) |
| `05_pruebas_SLO_continuidad.md` | Plan de pruebas, SLO, continuidad, criterios de aceptación |
| `sources/*.yaml` | 17 fichas de fuente; licencias y términos **PENDIENTE de verificar** |

## Hallazgo que corrige el prompt
El prompt dice «26 incidentes». La v0 vigente (`data/data.json`, corte 2026-11-08, commit `78d8e27`) tiene **42 eventos**, **25 excluidos** y **3 de contexto**; la actualización es **diaria**, no semanal. La prueba de equivalencia se hará contra una **instantánea congelada** de ese commit, no contra «26».

## Decisiones de Neider incorporadas (9-nov-2026)
1. Actualización diaria con compuertas automáticas y revisión posterior; autorización permanente sobre las **reglas** de publicación, no sobre cada evento (ADR-002).
2. Dos llaves: Claude propone, Neider revisa; estados `VERIFICADO_EQUIPO` y `VERIFICADO_INDEPENDIENTE` (ADR-003).
3. Versión reducida en servidor único como Fase 1; diseño completo como objetivo (ADR-001, ADR-004).
4. Recolección nacional a nivel municipio; profundidad en departamentos piloto (ADR-008).
5. ACLED y GTD: PENDIENTE, con bandera de licencia por fuente (ADR-007).
6. Claude propone etiquetas sobre texto público; validador determinista (ADR-006).
7. DPIA y matriz legal en borrador, PENDIENTE de validación jurídica.
8. Discrepancias: se conservan siempre; una cifra pública más ícono (ADR-009).
9. Equipo rojo no aplica al contenido diario; sí una revisión adversarial única del modelo de amenazas y los ADR (ADR-010).
10. Ubicación: `platform/` en OTVA 01, rama `v1`; `data.json` sigue como formato de salida (ADR-005).

## Decisiones que siguen abiertas (necesito de Neider)
| # | Decisión | Mi propuesta |
|---|---|---|
| A | Alojamiento y presupuesto del servidor | Un VPS pequeño en Colombia o EE. UU. con disco cifrado; hoy el flujo corre en su equipo Windows |
| B | Departamentos piloto | Ver ADR-008: los datos apuntan a Cesar, Norte de Santander, Chocó, Huila y Valle; Antioquia y Magdalena no están entre los seis primeros |
| C | Presupuesto de licencias (ACLED, GTD) | Ninguno; uso interno y sin redistribución hasta verificar términos |
| D | Confirmar uso de Claude como proveedor externo | Confirmar, tras revisar términos de retención y entrenamiento (PENDIENTE) |
| E | Abogado designado | Ninguno; borrador marcado |
| F | Umbral de discrepancia «material» | ≥ 2 víctimas mortales de diferencia o ≥ 20 % relativo (propuesta) |

## Qué no se hizo
No se verificó ninguna licencia, término de uso, límite de tasa ni norma citada en línea: todo lo marcado PENDIENTE sigue sin comprobar. No se contactó a ninguna fuente ni se escribió código de conectores.
