# Observatorio GESEG de terrorismo y violencia armada en Colombia

Instrumento técnico y documentado con fuentes abiertas. Registra presuntos actos terroristas, atentados, ataques armados y otras acciones violentas relevantes desde el **7 de agosto de 2026, 00:00 (UTC−5)** hasta la fecha de corte (`updated` en `data/data.json`).

**Estado:** corte 21-oct-2026 · 30 incidentes · revisión independiente (R13) pendiente de asignación · no publicado.

## Estructura
| Ruta | Qué es |
|---|---|
| `data/data.json` | Base depurada y **fuente única de verdad** (`updated`, `events`, `excluded`, `context`) |
| `data/geo.json` | Contornos simplificados de Colombia y vecinos (generado una sola vez con `src/make_geo.js`) |
| `assets/geseg_logo.svg` | Logo vectorial (`currentColor`); `logo_geseg_azul.png` para el Excel |
| `src/add_events.py` | Agrega eventos nuevos desde un JSON (ids consecutivos, corte, validación con restauración) |
| `vercel.json` | Despliegue estático: sirve `dist/` (`index.html` = tablero; el Excel queda como descarga) |
| `src/validate.py` | Valida esquema, duplicados, fechas, coordenadas, enlaces y atribución; imprime el resumen |
| `src/build_html.py` | Valida e inyecta `__DATA__`, `__GEO__` y `__LOGO__` → `dist/observatorio.html` |
| `src/build_xlsx.py` | Genera el Excel de 7 hojas con indicadores por fórmulas |
| `src/recalc_check.py` | Recalcula el Excel con una instancia propia de Excel (Windows) y cuenta errores |
| `src/build_data.py` | Carga inicial de los 30 registros (documenta cómo se redactó cada uno) |
| `dist/` | Salidas: `observatorio.html` y `Observatorio_Violencia_Armada_Colombia_2026.xlsx` |

## Cómo agregar un evento
1. Lea la nota completa de cada fuente (mínimo dos independientes si existen; una sola fuente queda como información incompleta).
2. Añada el registro a `events` en `data/data.json` (o en `src/build_data.py` y ejecútelo) con el **siguiente id consecutivo** `CO-2026-NNN` (nunca se reutiliza). Todos los campos son obligatorios.
3. Reglas: `fecha` es la de ocurrencia; `lat/lon` es el centroide municipal aproximado; si la autoridad no nombra al autor, `atrib` = `E` y `grupo` = `No determinado`; no infiera autoría por presencia territorial o modalidad; cifras de víctimas = balance oficial más reciente, y las diferencias van en `discrepancia`; sin nombres de víctimas ni valores económicos sin fuente con metodología.
4. Combates, atentados frustrados, hechos fuera del periodo o del territorio y fechas no verificables van a `excluded` con su justificación. Las cifras agregadas oficiales van a `context` y no se suman.
5. Si las fuentes difieren, registre una sola cifra (el balance oficial más reciente); el tablero no muestra discrepancias.

## Validar, construir y publicar
```bash
python src/validate.py        # debe terminar sin errores
python src/build_html.py      # dist/observatorio.html (valida antes)
python src/build_xlsx.py      # dist/Observatorio_Violencia_Armada_Colombia_2026.xlsx
python src/recalc_check.py    # 0 errores de fórmula; compare 2–3 indicadores con validate.py
```
**Publicación:** no se publica sin aprobación expresa de Neider. El HTML es autocontenido (solo carga Chart.js 4.4.1 desde cdnjs y las fuentes de Google Fonts); basta copiarlo a cualquier alojamiento estático. El Excel se entrega como archivo.

## Publicación diaria (GitHub + Vercel)
El repositorio se conecta a Vercel (framework «Other», sin comando de build, directorio de salida `dist`). Cada `git push` a `main` redespliega el tablero. La tarea programada `otva-diario` actualiza la base, reconstruye `dist/` y hace el push (ver `LEEME.md` de la línea).

## Ciclo (diario)
Corte anterior = `updated` → búsqueda de hechos nuevos → actualización de balances de los registros existentes → agregar registros y actualizar `updated` → validar → construir → resumen (hechos nuevos, totales, hechos más graves, correcciones, vacíos). Si no hubo hechos verificables, se dice y no se regeneran los productos. Los textos de periodo, el límite de los filtros y los periodos de los gráficos salen de `updated`; no hay fechas fijas que editar en la plantilla.

## Límites
GESEG no es organismo de inteligencia ni de contrainteligencia (Ley 1621 de 2013). La clase «presunto acto terrorista» es una clasificación analítica provisional, no una calificación jurídica. Los conteos por actor no equivalen a responsabilidad judicial. Una acusación periodística o una atribución oficial no es un hecho judicialmente probado.
