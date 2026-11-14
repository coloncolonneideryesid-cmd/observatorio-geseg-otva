# Observatorio OTVA (plano interno)

Plataforma local de GESEG para consultar, analizar y controlar la calidad de los registros de violencia armada documentados con fuentes abiertas. Es **análisis estratégico de fuentes abiertas**, no inteligencia. Replica la estructura y el arranque del Observatorio de referencia (backend FastAPI, frontend React compilado, ETL, SQLite). Todo lo que muestra es «Preliminar, sin revisión independiente».

## Cómo iniciarlo (Windows, Python 3.11+)
```bash
cd platform/observatorio
pip install -r requirements.txt
python -m etl.cargar inicial            # una sola vez: carga la v0 viva (data/data.json de OTVA 01)
python run.py --abrir                   # http://127.0.0.1:8000
```
También: `instalar.bat` e `iniciar.bat`. Node **no** hace falta para usarlo (la interfaz ya está compilada en `backend/static`); solo para modificarla: `cd frontend && npm install && npm run build`.

Primer ingreso: usuario `admin`; la clave inicial queda en `data/db/CREDENCIALES_INICIALES.txt`. El sistema obliga a cambiarla y borra el archivo.

## Estructura
```
run.py, iniciar.bat, instalar.bat, requirements.txt
backend/    main.py (API), db.py (usuarios, claves, tokens, bitácora de acceso), almacen.py (consultas), config.py
frontend/   React + TypeScript + Vite + ECharts + Leaflet  ->  compila a backend/static
etl/        cargar.py (carga inicial desde la v0), sincronizar.py (trae lo nuevo de la v0 viva); usan el núcleo ../otva
data/db/    otva.db (eventos, historia inmutable, bitácora encadenada), usuarios.db, secret.key   [no se versionan]
tests/      prueba_integral.py (API, autenticación, límites, ciclo de casos)
tools/      respaldo.py
```
El núcleo de datos (`../otva/core.py`) y su esquema (`../migrations/`) son los mismos de la Fase 1; el ciclo de casos está en `../otva/ciclo.py` y sus pruebas en `../tests/test_ciclo.py`.

## Módulos actuales
01 Panorama general · 02 Mapa (círculos municipales, no puntos exactos) · 03 Base de eventos (filtros, orden, CSV) · 04 Fuentes y calidad · **05 Casos: registro y revisión** (solo editor y admin). Pendientes (Fases 2–4): sala de situación, línea de tiempo con control estadístico, actores y territorios, perfil territorial, alertas, reportes, administración.

## Ciclo de casos (módulo 05)
Un caso nuevo nace **CANDIDATO** (no es público). Pasa a **PRELIMINAR** (público) solo si cumple las compuertas: fuente oficial (.gov.co, .mil.co) o 2 fuentes de propietarios editoriales distintos, atribución A–D con base, sin instrucciones embebidas, sin duplicado y sin nombres de personas (si el filtro heurístico sospecha uno, solo un admin puede continuar, con motivo). **VERIFICADO_EQUIPO** lo asigna un admin distinto de quien creó o editó el caso (dos llaves). **RETRACTADO** y **DESCARTADO** exigen motivo y sacan el caso de lo público. **VERIFICADO_INDEPENDIENTE** está reservado a R13 y el sistema no lo asigna. Cada cambio crea una versión nueva (la historia es inmutable) y queda en el historial del caso y en la bitácora encadenada. Editar un caso verificado lo devuelve a preliminar. Los casos nuevos de la aplicación usan la misma numeración `CO-2026-NNN`.

Régimen transitorio: todavía no hay captura automática de las fuentes, así que no se exige archivo (hash) para pasar a preliminar; los casos quedan marcados como sin archivar.

## Sincronizar con la v0 y exportar
- `python -m etl.sincronizar` (o el botón «Sincronizar con la v0», admin): trae a la base los eventos nuevos y editados del `data.json` vivo, y los excluidos y el contexto. No pisa casos creados en la aplicación; si la v0 usa un id que la aplicación ya tomó, informa el conflicto. Es idempotente.
- Botón «Exportar data.json publicable» (admin): genera `data/export/data.json` solo con lo publicable, validado con las reglas de la v0, con su SHA-256 registrado. **No toca el `data.json` vivo ni publica nada**: llevarlo al tablero público sigue siendo un paso manual.

## Seguridad actual
PBKDF2 (200 000 iteraciones), roles lector/editor/admin, tokens firmados de 8 h, cambio obligatorio de la clave inicial, claves de al menos 10 caracteres, 5 fallos por usuario+IP y 20 por IP en 15 minutos, CSP estricta y demás cabeceras, API sin documentación pública, bitácora de accesos. Escucha solo en 127.0.0.1; si se expone fuera del equipo, ponerlo detrás de HTTPS y de un control de acceso (ver la guía de publicación de la referencia).

## Pruebas
`python tests/prueba_integral.py` (usa una carpeta temporal; no toca `data/`).
