# ADR · Arquitectura y pila tecnológica del OTVA v1

Formato: contexto · decisión · alternativas · consecuencias · excepciones a principios (si las hay). Estado de todos: **propuesto, pendiente de aprobación de Neider**.

## ADR-001 · Arquitectura por niveles: objetivo completo, Fase 1 reducida
**Contexto.** El equipo real es una persona más un asistente. El prompt describe Kubernetes, MinIO con object lock, HSM, WAF y observabilidad completa.
**Decisión.** Se documenta la arquitectura completa como objetivo y se implementa una **Fase 1 reducida** que conserva los controles esenciales.

| Capa | Objetivo documentado | Fase 1 (a construir) |
|---|---|---|
| Cómputo | Kubernetes / Compose | Un servidor, Docker Compose rootless |
| Datos | PostgreSQL 16 + PostGIS 3, RLS | Igual; SQLite + SpatiaLite solo si no hay presupuesto de servidor |
| Raw inmutable | MinIO con object lock, WARC, RFC 3161 | Archivos de solo adición, direccionados por SHA-256, con manifiesto de hashes firmado y versionado en Git; sello RFC 3161 PENDIENTE de elegir autoridad |
| Orquestación | Prefect / Dagster | `systemd timers` (o Tarea Programada si sigue en Windows) con idempotencia estricta |
| Cola | Redis Streams | Tabla de trabajos en la base de datos |
| Borde | WAF + túnel | Cloudflare gratuito (WAF y túnel) delante del plano interno; plano público estático en Vercel |
| Firma | HSM | Llave física (YubiKey) con `age` o `minisign` |
| Observabilidad | OpenTelemetry + Prometheus + Loki + Grafana | Registros estructurados + chequeos de salud + página de estado de fuentes |

**Controles que no se recortan:** MFA (WebAuthn), secretos fuera del repositorio, dependencias fijadas con hash y SBOM, descargas protegidas contra SSRF, bitácora encadenada, copias cifradas con restauración probada, CSP estricta, versiones firmadas.
**Alternativas.** Solo estático como la v0 (descartado: no sostiene verificación, auditoría ni alertas); arquitectura completa desde el día uno (descartada: inviable para una persona).
**Consecuencias.** La seguridad de la raw depende de disciplina y de la firma, no de WORM de hardware. Se declara como riesgo residual R-01.

## ADR-002 · Publicación diaria con compuertas automáticas y revisión posterior
**Contexto.** La v0 publica a diario sin revisión previa (decisión del 21-oct-2026). El prompt pedía aprobación explícita antes de publicar.
**Decisión (Neider, 9-nov).** La «aprobación» pasa a ser una **autorización permanente sobre las reglas**, no sobre cada evento:
- **Se autopublica** solo un evento con **fuente oficial** o con **≥ 2 fuentes independientes** (propietarios editoriales distintos, sin copia verbatim). Lo demás queda en cola interna.
- Todo lo público lleva la etiqueta **«preliminar, sin revisión independiente»**.
- Infraestructura sensible: se degrada a **municipio y semana**.
- **Botón de retractación** (estado `RETRACTADO` que propaga aviso a lo publicado).
- Cambiar las reglas de publicación requiere nueva autorización de Neider, registrada en la bitácora.
**Excepción documentada.** Contradice la primera línea de la sección 1 del prompt («nada se publica sin aprobación explícita del responsable»). Se resuelve por decisión del responsable; el principio de evidencia (§2) se mantiene porque ningún evento sale sin fuente archivada.
**Riesgos.** Una fuente oficial puede errar; un medio puede copiar a otro (mitiga `outlet_group_id`); la difamación por atribución errónea (mitiga: atribución por defecto E, texto «según [fuente]», sin nombres de personas). Riesgos R-02 y R-03.
**Compuertas automáticas mínimas** (todas deben pasar): esquema válido; fuente archivada con hash; sin nombres de personas (detector de entidades + lista de bloqueo); atribución A–D con referencia de apoyo; conteos no negativos y coherentes; coordenadas dentro del municipio; no duplicado; infraestructura sensible degradada; sin instrucciones embebidas detectadas.

## ADR-003 · Verificación de dos llaves y estados
**Decisión.** Claude propone (analista asistente, no decide), Neider revisa. Estados del evento:
`CANDIDATO → PRELIMINAR → VERIFICADO_EQUIPO → VERIFICADO_INDEPENDIENTE`, más `DESCARTADO` y `RETRACTADO`.
- `VERIFICADO_EQUIPO`: revisión de Neider sobre lo que propone Claude. **No es independiente.**
- `VERIFICADO_INDEPENDIENTE`: reservado hasta que exista R13 y un aprobador distinto (regla del programa: R13 = Neider no revisa lo que él mismo redactó; aprueba Omar Rubiano Castro o Fernanda María). El sistema **no permite** asignarlo mientras el rol no esté ocupado por persona distinta del autor.
- Nada público usa «validado», «verificado» ni «independiente» antes de eso; se rotula «preliminar, sin revisión independiente».
- El sistema maneja **roles**, no nombres; los nombres de aprobadores viven solo en registros internos. El administrador del producto no figura en documentos públicos.
**Nota.** `PRELIMINAR` aquí significa «aprobado por compuerta automática, sin revisión humana» y es lo que puede autopublicarse; no entra a indicadores oficiales hasta `VERIFICADO_EQUIPO`.

## ADR-004 · Pila tecnológica
Python 3.12 (pydantic v2, SQLAlchemy 2 Core, Alembic, httpx, polars, shapely 2, pyproj, h3, statsmodels, scipy, ruptures, scikit-learn). FastAPI con OpenAPI 3.1 para el plano interno. Frontend: **la v0 sigue siendo HTML autocontenido**; el tablero React + TypeScript + ECharts + MapLibre es Fase 4 y solo si Neider lo aprueba. Contenedores rootless con sistema de ficheros de solo lectura. IaC con OpenTofu en Fase 4 (en Fase 1 basta Compose versionado).
**Desviaciones respecto al prompt:** sin Redis/RabbitMQ, sin Prefect/Dagster, sin Kubernetes y sin MinIO en Fase 1 (ADR-001). Autenticación: OIDC si hay proveedor; si no, Argon2id propio + WebAuthn.
**Verificación pendiente.** No se comprobaron versiones ni vigencia de paquetes; se fijarán con hash al iniciar la Fase 1.

## ADR-005 · Ubicación y compatibilidad con la v0
**Decisión.** Todo dentro de `OTVA 01`, rama `v1`, subdirectorio `platform/`. `data/data.json` sigue siendo el **formato de salida**, generado desde la base de datos, para que `src/build_html.py` y `src/build_xlsx.py` no cambien. La publicación diaria no se interrumpe: la v1 se despliega primero en una **vista previa** y pasa a producción cuando la prueba de equivalencia con la v0 dé idéntico (plan en `05`).
**Consecuencia.** Los campos de la v0 que no encajan en el modelo nuevo se guardan en `legacy_payload` para viaje de ida y vuelta sin pérdida.

## ADR-006 · Uso de Claude como asistente de extracción y clasificación
**Decisión.** Claude propone etiquetas **solo sobre texto público de notas leídas**. Nunca recibe listas de fuentes o términos vigilados (INTERNO), información reservada ni credenciales. No puede cambiar `attribution_level` ni `status`. Un **validador determinista** revisa toda propuesta (esquema JSON, vocabulario cerrado, atribución sin salto de nivel, límites de longitud) antes de guardarla.
**Prompt injection.** El texto externo va en un bloque de datos delimitado, nunca en el prompt del sistema; filtro de instrucciones embebidas; salida solo estructurada; sin herramientas ni red en la llamada; se registra el hash de entradas y salidas.
**Pendiente.** Revisar términos del proveedor sobre retención y entrenamiento; un modelo local queda como opción futura. Hay conjunto de oro y métricas (F1, kappa) desde Fase 1 con anotación humana de Neider.

## ADR-007 · Licencias de fuentes como dato
**Decisión.** Cada ficha lleva `license_status` (`VERIFIED`/`PENDING`/`RESTRICTED`) y `public_redistribution` (`yes`/`no`/`pending`). El exportador público **excluye** cualquier dato cuya fuente no tenga `public_redistribution: yes`. ACLED y GTD quedan `PENDING`, solo uso interno de contexto y validación. GESEG es S.A.S. (uso comercial posible); sus términos pueden exigir licencia: **no verificado**.

## ADR-008 · Cobertura territorial
**Decisión.** Recolección **nacional a nivel de municipio** (DIVIPOLA) y verificación profunda con gazetteer de veredas en departamentos piloto.
**Datos de la v0 (42 eventos, corte 2026-11-08):** Cesar 7, Norte de Santander 6, Chocó 6, Huila 5, Valle del Cauca 5, Cauca 4, Arauca 2, Nariño 2; los 5 restantes están repartidos en otros departamentos (Antioquia y Magdalena no superan 2 cada uno). **Propuesta de pilotos:** Cesar, Norte de Santander, Chocó y Huila, o Cauca si Neider prefiere criterio estratégico sobre el de conteo. **Decisión de Neider pendiente.** Nota: el conteo refleja la cobertura de lo que se ha leído, no el riesgo real.

## ADR-009 · Discrepancias entre fuentes
**Decisión.** Siempre se conservan en datos (claim registry). En el plano público: **una sola cifra principal** (la más reciente del balance oficial, regla de la v0) más ícono «versiones distintas» que muestra rango y fuentes **solo si la diferencia es material**. Umbral propuesto: ≥ 2 muertos de diferencia o ≥ 20 % relativo (PENDIENTE de Neider). Detalle completo en el plano interno.

## ADR-010 · Revisión adversarial y equipo rojo
**Decisión.** El equipo rojo no revisa el contenido diario de eventos (sigue valiendo NG-OTVA-01/02). Una **sola** revisión adversarial ligera del modelo de amenazas y de los ADR (sesión de escenarios con Neider + pruebas automáticas de SSRF, archivos maliciosos e inyección de instrucciones). No bloquea la publicación diaria. Se formaliza cuando exista R13. Cualquier nota con conclusiones sí puede ir al equipo rojo (regla del programa).
