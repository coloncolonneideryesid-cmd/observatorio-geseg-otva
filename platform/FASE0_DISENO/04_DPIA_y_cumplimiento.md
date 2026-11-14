# DPIA preliminar y matriz de cumplimiento · OTVA v1

**PENDIENTE de validación jurídica.** No hay abogado designado. Las normas se citan por nombre y número; su alcance exacto en este caso no se ha verificado.

## 1. DPIA preliminar
| Elemento | Contenido |
|---|---|
| Finalidad | Análisis de información pública sobre violencia armada y terrorismo para Congreso, entidades de control, academia y organismos de seguridad |
| Responsable | GESEG – Gestión de la Seguridad S.A.S. (rol: responsable del producto) |
| Datos tratados | Hechos, lugares, fechas, conteos agregados de víctimas, grupos armados como actores colectivos, enlaces y extractos ≤ 280 caracteres |
| Datos que **no** se tratan | Nombres de víctimas, presuntos responsables individuales, menores, valores económicos sin metodología |
| Datos personales residuales | Posibles nombres de funcionarios en la fuente citada (solo si son de interés público); extractos que contengan nombres: se enmascaran antes de guardarse |
| Base legal propuesta | Información pública; Ley 1581 de 2012 y Decreto 1074 de 2015 (habeas data) y Ley 1712 de 2014 (fuentes oficiales): **PENDIENTE de análisis jurídico** |
| Naturaleza del producto y límite | **Análisis estratégico y prospectivo de fuentes abiertas**, no inteligencia ni contrainteligencia. GESEG no es organismo de inteligencia (Ley 1621 de 2013): no recolecta de forma encubierta, no accede a información reservada ni la trata, y no ejerce funciones propias de esos organismos. Solo fuentes abiertas y lícitas |
| Delitos informáticos | Ley 1273 de 2009: toda recolección se revisa contra esta norma; sin evadir autenticación, CAPTCHA ni paywalls |
| Derechos de autor | Solo metadatos, enlace, hash y extracto breve; texto completo únicamente en raw interno |
| Retención propuesta | Eventos agregados: indefinida; extractos ≤ 24 meses; raw cifrado con vencimiento a definir; trazas de analistas ≤ 12 meses |
| Derechos del titular y rectificación | Canal de rectificación con plazo (propuesta: respuesta en 10 días hábiles; **PENDIENTE de aprobar**); retractación con aviso en lo publicado |
| Riesgos principales | Atribución errónea; reidentificación por cruce de celdas pequeñas; difamación; sensibilidad de infraestructura |
| Mitigaciones | Ver ADR-002, modelo de amenazas A1/A9/A11; supresión < 5 víctimas por celda; infraestructura a municipio y semana |
| Evaluación | Riesgo de datos personales **bajo** por diseño (no se guardan nombres); riesgo legal por atribución **medio** hasta revisión jurídica |

Puntos para el abogado: (1) límite con la Ley 1621; (2) política de atribución y difamación; (3) la propia DPIA y el plazo de rectificación.

## 2. Matriz de cumplimiento (borrador)
La numeración de controles ASVS corresponde a los capítulos de la versión 4.0; los códigos finos y el mapeo del MSPI **no se verificaron** y se completan en Fase 1 con apoyo de R13.

| Dominio | OWASP ASVS (capítulo) | ISO/IEC 27001:2022 Anexo A (tema) | MSPI (MinTIC) | Control en el diseño | Fase |
|---|---|---|---|---|---|
| Autenticación | V2 | A.5.17, A.8.5 | PENDIENTE de mapear | WebAuthn, Argon2id, límites 5/usuario+IP y 20/IP en 15 min | 2 |
| Sesiones | V3 | A.8.5 | PENDIENTE | JWT ≤ 15 min, refresh rotativo, cookies HttpOnly/Secure/SameSite=Strict | 2 |
| Control de acceso | V4 | A.5.15, A.5.18, A.8.3 | PENDIENTE | RBAC + RLS por `sensitivity_class`, falla cerrada, matriz probada | 2 |
| Validación y codificación | V5 | A.8.28 | PENDIENTE | Pydantic, allow-lists, sin SQL dinámico, escape de texto externo | 1 |
| Criptografía y datos | V6, V8, V9 | A.8.24, A.8.11 | PENDIENTE | TLS 1.3, age para copias, pgcrypto en campos sensibles | 1 |
| Errores y registro | V7 | A.8.15, A.8.16 | PENDIENTE | RFC 9457, `audit_log` encadenado y firmado | 1 |
| Código malicioso | V10 | A.8.7, A.8.8 | PENDIENTE | SBOM, escaneo de dependencias, firmas | 1 |
| Lógica de negocio | V11 | A.8.28 | PENDIENTE | Compuertas de publicación, estados, límites de transición | 1–2 |
| Archivos | V12 | A.8.7 | PENDIENTE | Magic bytes, cuarentena, sin ejecución | 1 |
| API | V13 | A.8.26 | PENDIENTE | OpenAPI 3.1, cuotas, tipado | 2 |
| Configuración | V14 | A.8.9, A.8.32 | PENDIENTE | Contenedores rootless, IaC, cabeceras, CSP estricta | 1–4 |
| Respaldo y continuidad | — | A.8.13, A.5.30 | PENDIENTE | 3-2-1 cifrado, restauración probada | 1 |
| Proveedores | — | A.5.19–A.5.23 | PENDIENTE | Revisión de términos de Cloudflare, Vercel, proveedor del LLM | 1 |
