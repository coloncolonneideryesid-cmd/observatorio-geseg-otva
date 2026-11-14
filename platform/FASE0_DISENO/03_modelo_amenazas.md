# Modelo de amenazas · OTVA v1

Metodología: STRIDE sobre los límites de confianza del diagrama de arquitectura, con referencia a técnicas MITRE ATT&CK/ATLAS **por nombre de táctica** (los identificadores de técnica se asignan en la revisión adversarial; no se citan de memoria). Probabilidad e impacto: B/M/A (juicio del autor, sin datos históricos). Estado: **borrador sin revisión independiente**.

## Activos y límites de confianza
Activos: base de eventos y su historia; raw archivado; claves de firma; credenciales de Neider y del asistente; lista de fuentes y términos vigilados (INTERNO); reputación (atribuciones). Límites: Internet → recolector; recolector → raw; raw → procesamiento; procesamiento → base; base → publicación estática; usuario → plano interno; asistente (Claude) → validador.

## Matriz riesgo × control

| ID | Amenaza (STRIDE) | P | I | Controles Fase 1 | Controles objetivo | Riesgo residual |
|---|---|---|---|---|---|---|
| A1 | Envenenamiento/desinformación coordinada (T, R) | M | A | Compuerta ADR-002 (oficial o ≥ 2 fuentes independientes); `outlet_group_id`; detección de ráfagas idénticas; tope de peso por origen; atribución E por defecto; botón de retractación | Reconstrucción histórica reproducible desde raw; revisión de dos personas | **Medio**: una fuente oficial errónea se autopublica (R-02) |
| A2 | SSRF/RCE/DoS por conectores y parsers (T, E, D) | M | A | DNS fijado, bloqueo de IP privadas/metadatos, ≤ 3 redirecciones, límite de tamaño, TLS obligatorio, magic bytes, sin ejecutar JS, parseo en contenedor sin red | ClamAV en cuarentena, seccomp/AppArmor, límite de ratio de descompresión | Bajo |
| A3 | Inyección de instrucciones en el LLM (T, E) | A | M | Texto como dato delimitado; salida solo JSON validado; Claude sin herramientas, red ni acceso a DB; no cambia `status` ni `attribution_level`; validador determinista | Modelo local; conjunto de pruebas adversarias | Bajo-medio |
| A4 | Cadena de suministro (T, E) | M | A | Dependencias con hash, `npm ci`/lockfile, sin `latest`, SBOM CycloneDX, escaneo OSV/pip-audit, acciones de CI fijadas por SHA, commits firmados | SLSA 3, cosign, builds reproducibles | Medio |
| A5 | Robo de credenciales/phishing (S, E) | M | A | WebAuthn (llave física), sesiones cortas, secretos fuera del repo (SOPS+age), gitleaks | OIDC institucional, detección de anomalías | Bajo-medio |
| A6 | Abuso interno / filtración (I, E) | B | M | Mínimo privilegio por rol; registro de exportaciones; marca de agua en Excel interno | RLS completa, alertas de volumen | Bajo (equipo de una persona) |
| A7 | Exfiltración por API, exportes o copias (I) | B | A | Exportes con checksum; copias cifradas con age; cuotas; plano interno tras Cloudflare Access | DLP básico, egreso restringido | Bajo |
| A8 | Manipulación de la bitácora o historial (T, R) | B | A | `audit_log` encadenado; manifiesto de hashes firmado y versionado en Git; réplica semanal en destino aparte | Almacén de solo escritura separado | Bajo |
| A9 | Exposición legal (difamación, datos personales) (I, R) | M | A | Sin nombres de víctimas ni presuntos responsables; «según [fuente]»; atribución por defecto E; etiqueta «preliminar, sin revisión independiente»; retractación con plazo; revisión jurídica de DPIA (PENDIENTE) | Rectificación pública con plazo definido | **Medio** (R-03) |
| A10 | Doxxing de analistas y de intereses (I) | B | M | Un único perfil de egreso con User-Agent honesto; lista de fuentes y términos INTERNO; sin cuentas personales; sin interacción con actores armados | VM desechable para verificación | Bajo |
| A11 | Divulgación de vulnerabilidades de infraestructura (I) | M | A | `infra_sensitive` ⇒ municipio y semana; alertas internas por defecto; revisión de redacción | Rezago configurable | Medio |
| A12 | Fuente caída o corrupta; datos incompletos presentados como completos (D, T) | A | M | Estado de fuentes visible; ingestas fallidas bloquean promoción; rezago marcado y excluido de comparaciones | Caos controlado trimestral | Bajo |
| A13 | Pérdida de la clave de firma o del servidor (D) | B | A | Dos llaves físicas (principal y respaldo) guardadas por separado; copia cifrada 3-2-1 | HSM | Medio |
| A14 | Uso de datos con licencia restringida en el plano público (R) | M | M | `public_redistribution` por fuente; el exportador filtra | Prueba automática de exportación | Bajo |

## Riesgos residuales abiertos
- **R-01** Raw sin WORM de hardware: la inmutabilidad depende de firma y disciplina.
- **R-02** Autopublicación de un evento con fuente oficial equivocada: se cubre con retractación, pero el error es visible mientras tanto.
- **R-03** Exposición legal por atribución o fraseo: depende de la revisión jurídica pendiente.
- **R-04** Alojamiento no decidido: sin él no se puede cerrar el diseño de red.
- **R-05** Sello de tiempo RFC 3161: autoridad no elegida.

## Revisión adversarial (ADR-010)
Una sesión de escenarios con Neider sobre A1, A3, A9 y A11, más pruebas automáticas descritas en `05`. No bloquea la publicación diaria.
