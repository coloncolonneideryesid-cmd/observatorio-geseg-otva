# Observatorio GESEG de terrorismo y violencia armada en Colombia

Instrumento técnico y documentado con fuentes abiertas. Registra presuntos actos terroristas, atentados, ataques armados y otras acciones violentas relevantes desde el **7 de agosto de 2026, 00:00 (UTC−5)** hasta la fecha de corte (`updated` en `data/data.json`).

**Estado:** se actualiza a diario; el corte vigente y los totales están en `data/data.json` (`updated`) y en la tabla de ediciones del `LEEME.md` de la línea (al 14-nov-2026: corte 12-nov, 43 incidentes). Publicado en GitHub y Vercel. Revisión independiente pendiente (R13: Neider; aprobación: Omar Rubiano Castro o Fernanda María). La plataforma v1 (`platform/`) vive en la rama `v1` y es local: no se publica.

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
| `fuentes_abiertas/` | Directorio de fuentes abiertas del OTVA (extraído de `OTVA_fuentes_abiertas.zip`, que se conserva): 197 fuentes, verificador y reportes de calidad. Guía: `fuentes_abiertas/README_FUENTES_OTVA.md`. `build_html.py` lee `fuentes_maestras.json` y alimenta la sección «Red de fuentes» del tablero (solo campos descriptivos: no publica palabras clave, parámetros de consulta ni observaciones). Si el zip se actualiza, se vuelve a extraer aquí y se reconstruye el tablero |
| `src/recolectar_rss.py` | Consulta los canales RSS verificados del directorio, filtra desde el corte por términos de violencia armada, agrupa duplicados y deja candidatos en `%TEMP%\otva_rss\` (fuera del repositorio). Son pistas: cada nota se lee completa antes de registrar. Lo usa `otva-diario` (paso 1 bis) |
| `src/briefing.py` | Briefing de situación en PDF (2 páginas) a partir de `data.json`; salida en `briefing/` (fuera de git, no se publica) |
| `platform/` | OTVA v1: diseño (Fase 0), núcleo de datos, ciclo de casos y observatorio local (FastAPI + React). Rama `v1`; uso interno |
| `equipo_rojo/` | Paquetes y memos del equipo rojo sobre productos con conclusiones del OTVA (p. ej., ER-0023) |

## Cómo agregar un evento
1. Lea la nota completa de cada fuente (mínimo dos independientes si existen; una sola fuente queda como información incompleta).
2. Añada el registro a `events` en `data/data.json` (o en `src/build_data.py` y ejecútelo) con el **siguiente id consecutivo** `CO-2026-NNN` (nunca se reutiliza). Todos los campos son obligatorios.
3. Reglas: `fecha` es la de ocurrencia; `lat/lon` es el centroide municipal aproximado; si la autoridad no nombra al autor, `atrib` = `E` y `grupo` = `No determinado`; no infiera autoría por presencia territorial o modalidad; cifras de víctimas = balance oficial más reciente, y las diferencias van en `discrepancia`; sin nombres de víctimas ni valores económicos sin fuente con metodología.
   - `clase` es lista controlada; se escribe **exactamente** una de: `Presunto acto terrorista (clasificación analítica provisional)` · `Ataque armado contra Fuerza Pública (clasificación analítica provisional)` · `Incierto – autoría y finalidad no establecidas` (con raya corta «–»). `validate.py` rechaza cualquier otra variante.
   - Si no hay daño material documentado, `danos` empieza por «No informados», «No descritos», «No documentados» o «No se reportan…»; el tablero no cuenta esos registros como daño documentado.
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
Corte anterior = `updated` → candidatos de los RSS de la red de fuentes (`src/recolectar_rss.py`) → búsqueda de hechos nuevos → actualización de balances de los registros existentes → agregar registros y actualizar `updated` → validar → construir → resumen (hechos nuevos, totales, hechos más graves, correcciones, vacíos). Si no hubo hechos verificables, se dice y no se regeneran los productos. Los textos de periodo, el límite de los filtros y los periodos de los gráficos salen de `updated`; no hay fechas fijas que editar en la plantilla.

## Límites
GESEG no es organismo de inteligencia ni de contrainteligencia (Ley 1621 de 2013). La clase «presunto acto terrorista» es una clasificación analítica provisional, no una calificación jurídica. Los conteos por actor no equivalen a responsabilidad judicial. Una acusación periodística o una atribución oficial no es un hecho judicialmente probado.
