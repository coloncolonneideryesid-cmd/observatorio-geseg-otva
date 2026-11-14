# Sistema de Fuentes Abiertas – 07 Observatorio de Terrorismo y Violencia Armada (OTVA)

Repositorio estructurado de fuentes abiertas (OSINT) para identificar, clasificar, consultar y verificar información sobre terrorismo, violencia armada, grupos armados organizados, afectaciones a la población civil y orden público en Colombia.

> **Estado al 2026-11-14.** El sistema está **configurado y validado**, pero **no hay monitoreo automatizado en producción**. Cuatro conceptos se distinguen siempre:
>
> | Concepto | Significado | Cifra actual |
> |---|---|---|
> | Fuente **identificada** | Registrada en un JSON con entidad, territorio y URL o cuenta | 197 |
> | Fuente **verificada** (`estado: activa`) | Su `url_principal` respondió HTTP 2xx/3xx desde el dominio registrado, sin reto anti-bots ni redirección a otro dominio, en una ejecución real registrada | 146 |
> | Fuente **consultable** por máquina | RSS válido comprobado o API pública con respuesta comprobada | 61 RSS + 9 conjuntos de datos (API SODA) |
> | Fuente **automatizada** | Ingesta programada en ejecución, con registro de publicaciones | **0** |
>
> La verificación técnica **no certifica la titularidad institucional** de un dominio ni la veracidad de su contenido. Las cuentas de redes sociales siguen todas en `pendiente_verificacion`.

---

## 1. Estructura

```
07_OTVA/fuentes_abiertas/
├── fuentes_maestras.json                  # DERIVADO: directorio consolidado + índices (no editar a mano)
├── fuentes_institucionales.json           # OTVA-INS-*  Policía, FF.MM., Fiscalía, ministerios, gobernaciones, alcaldías
├── fuentes_medios_nacionales.json         # OTVA-MNA-*  Medios de cobertura nacional
├── fuentes_medios_regionales.json         # OTVA-MRE-*  Medios departamentales, regionales y municipales
├── fuentes_redes_sociales.json            # OTVA-RSO-*  Cuentas oficiales y públicas
├── fuentes_internacionales_academicas.json# OTVA-INT-*  ONU, OEA, CICR, ACLED, GDELT, ONG y centros de pensamiento (archivo adicional)
├── categorias_monitoreo.json              # Taxonomía: temas, actores, niveles, corroboración, geografía DIVIPOLA
├── parametros_consulta.json               # Frecuencias, filtros, palabras clave, deduplicación, APIs comprobadas
├── esquema_validacion.json                # JSON Schema 2020-12 + reglas de integridad
├── verificador_fuentes.py                 # Validación, comprobación de URLs, descubrimiento y reportes
├── pruebas/test_verificador.py            # 19 pruebas unitarias (sin red)
└── reportes/
    ├── reporte_calidad.md / .json         # Último informe de calidad
    ├── fuentes_pendientes.json            # Fuentes pendientes y su motivo
    └── registro_ejecuciones.jsonl         # Historial append-only de TODAS las ejecuciones
```

`fuentes_internacionales_academicas.json` no estaba en la lista original. Se agregó porque el sistema debe distinguir la información de organismos internacionales y no correspondía mezclarla con las entidades del Estado colombiano.

## 2. Modelo de datos de una fuente

Todos los campos del prompt maestro son obligatorios: si no aplican o se desconocen, van en `null`, nunca vacíos ni inventados.

| Campo | Notas |
|---|---|
| `id_fuente` | `OTVA-{INS|MNA|MRE|RSO|INT}-NNN`; el prefijo coincide con el archivo. Gobernaciones: 101–133; alcaldías: 201+. |
| `categoria` | `institucional`, `gubernamental`, `periodistica`, `red_social`, `organismo_internacional`, `centro_investigacion` |
| `nivel_cobertura` | `nacional`, `departamental`, `regional`, `municipal`, `internacional` |
| `departamento` | Nombre normalizado (sin tildes) de `categorias_monitoreo.json#/normalizacion_geografica` |
| `estado` | `activa`, `inactiva`, `pendiente_verificacion` (ver §5) |
| `metodo_consulta` | `rss`, `api_publica`, `api_con_registro`, `api_con_registro_nombre_app`, `api_oficial_de_pago`, `html_publico`, `manual`, `no_automatizable` |
| `frecuencia_actualizacion` | Frecuencia **programada** de consulta, en formato ISO 8601 (`PT30M`, `PT1H`, `P1D`). No significa que se haya consultado. |
| `fecha_verificacion` | Última comprobación técnica **exitosa** real. |
| `fecha_ultima_consulta` | Última comprobación **intentada**, con cualquier resultado. |
| `confiabilidad_fuente` | `N1_fuente_primaria` … `N4_fuente_complementaria` |

Campos adicionales: `region`, `codigo_divipola`, `fuente_relacionada` (relaciones; por ejemplo, DIJIN → Policía, o una cuenta de X → su institución), `resultado_ultima_comprobacion`, `fallos_consecutivos`, `fecha_primer_fallo`.

Los nombres se guardan sin tildes para que las comparaciones sean deterministas. El nombre oficial con tildes y los alias están en la tabla geográfica.

## 3. Metodología de verificación de la información

| Nivel | Tipo | Ejemplos |
|---|---|---|
| N1 | Fuente primaria | Comunicados de Policía, FF.MM., Fiscalía, Defensoría; ONU |
| N2 | Fuente secundaria | Medios nacionales y diarios regionales reconocidos; ACLED |
| N3 | Fuente digital verificada | Cuentas públicas con titularidad comprobada |
| N4 | Fuente complementaria | Medios locales, ONG, agregadores (GDELT) |

Cada publicación capturada (esquema `esquema_validacion.json#/$defs/publicacion`) lleva **un** estado de corroboración: `confirmado_oficial`, `reportado_medios`, `declaracion_atribuida`, `en_desarrollo`, `no_corroborado` o `desmentido_rectificado`. Reglas clave (`categorias_monitoreo.json#/reglas_corroboracion`):

- Nada pasa a `confirmado_oficial` sin una fuente N1 que **afirme** el hecho.
- Las réplicas de una misma nota o agencia no cuentan como fuentes independientes.
- Un desmentido cambia el estado y conserva la traza en `historial_estado`; no borra el registro.

## 4. Búsqueda, clasificación y deduplicación

`parametros_consulta.json#/filtros_busqueda` define 14 dimensiones: departamento, municipio (DIVIPOLA), región, subregión, institución, actor armado, tipo de hecho, fecha de publicación, fecha de ocurrencia, palabra clave, medio, plataforma, categoría de información y estado de corroboración. `fuentes_maestras.json#/indices` trae índices precalculados por departamento, categoría, plataforma, nivel, región y confiabilidad.

Deduplicación (`#/deduplicacion`):

- **URL canónica:** sin esquema, sin `www`, sin parámetros `utm_`, `fbclid` ni `gclid`.
- **Títulos:** Jaccard sobre shingles. Umbral 0,85 para duplicado y 0,5 para publicación relacionada.
- **Agrupación en `id_evento`:** por municipio, tipo de hecho y fecha (±1 día).
- **Detección de cambios:** hash SHA-256 del contenido normalizado.

La normalización geográfica usa `normalizar_texto()` (minúsculas, sin tildes ni signos) más alias; por ejemplo, "Bogotá", "Bogota" y "Distrito Capital" → `Bogota D.C.`.

## 5. Ciclo de estados de una fuente

| Resultado de la comprobación | Efecto |
|---|---|
| `ok` (2xx/3xx en el mismo dominio) | `activa`, `fecha_verificacion` = ahora, contador de fallos a 0 |
| `redireccion_otro_dominio` | Queda `pendiente_verificacion` hasta que una persona acepte el nuevo dominio |
| `bloqueado_o_restringido` (401/403/429 o página de reto anti-bots, aunque responda 200) | Queda `pendiente_verificacion`; requiere comprobación manual en navegador, **nunca evasión** |
| `sin_respuesta`, `enlace_roto`, `error_servidor` | Suma un fallo. Pasa a `inactiva` solo con **3 fallos consecutivos que abarquen ≥ 72 h** |

## 6. Uso del verificador

Requisitos: Python ≥ 3.9. Usa solo la biblioteca estándar; `jsonschema` es opcional y activa la validación completa del esquema.

```bash
python3 verificador_fuentes.py --construir-maestro
```

```bash
python3 verificador_fuentes.py --comprobar-urls --descubrir
```

```bash
python3 verificador_fuentes.py --comprobar-urls --actualizar
```

```bash
python3 verificador_fuentes.py --comprobar-urls --solo OTVA-INS-009,OTVA-MNA-005
```

```bash
python3 -m unittest discover -s pruebas -v
```

Códigos de salida: `0` = válido, `1` = hay errores de validación, `2` = la ejecución falló. Cada ejecución, exitosa o no, se añade a `reportes/registro_ejecuciones.jsonl`. `--descubrir` lista RSS y enlaces de prensa candidatos **sin escribirlos**: una persona decide si se registran.

Detrás de un proxy con certificado propio, exporte `SSL_CERT_FILE` con la ruta del bundle de CA.

## 7. Cómo agregar o actualizar fuentes

1. Elija el archivo por categoría y el siguiente `id_fuente` libre con su prefijo.
2. Copie un registro existente y complete **solo** lo comprobado; lo demás va en `null`. Use `estado: "pendiente_verificacion"`, `fecha_verificacion: null` y `fallos_consecutivos: 0`.
3. Use un departamento de la tabla normalizada y temas de la taxonomía.
4. Ejecute `--construir-maestro` y luego `--comprobar-urls --actualizar --solo <id>`.
5. **Redes sociales:** solo registre una cuenta si el sitio oficial de la entidad la enlaza. No se marca `activa` sin verificación de titularidad documentada en `observaciones`. Para funcionarios o actores políticos, confirme el cargo en una fuente oficial y no lo asuma.
6. **Cambio de dominio:** actualice `url_principal` y explique en `observaciones` de dónde a dónde redirigía y la fecha.

## 8. Integraciones comprobadas (configuradas, no automatizadas)

| Integración | Estado comprobado el 2026-11-13 |
|---|---|
| datos.gov.co (Socrata SODA) | 9 conjuntos de datos oficiales respondieron con datos: homicidio, secuestro, terrorismo, voladuras y masacres (MinDefensa); terrorismo (Policía); SIEVCAC (CNMH); presuntos homicidios (Medicina Legal); minas antipersonal. Ver `parametros_consulta.json#/integraciones_api` |
| RSS | 61 feeds declarados por las propias fuentes y validados como RSS/Atom |
| GDELT DOC 2.0 | Responde, pero limita a 1 solicitud cada 5 s por IP (HTTP 429 observado) |
| ReliefWeb | La API v1 está dada de baja (410); la v2 exige un `appname` aprobado (403 sin él) |
| ACLED | Requiere registro; no probado |
| X, Facebook, Instagram, TikTok, Threads | Sin acceso autorizado gratuito para monitoreo de terceros (ver `#/integraciones_api/redes_sociales`) |

## 9. Seguridad y privacidad

Solo información pública, sin credenciales ni cuentas privadas y sin evadir bloqueos (el verificador se identifica con un User-Agent propio). No se hace vigilancia individual ni se perfila a personas no públicas. No se registran ubicaciones operativas, movimientos de unidades ni vulnerabilidades. Los alias de actores armados son términos de búsqueda, no atribuciones. Se prioriza el análisis agregado.

## 10. Brechas conocidas

- **Cobertura regional (2026-11-14):** 32 de 33 entidades territoriales tienen al menos un medio registrado. Sucre se cubre solo de forma parcial, con El Meridiano (registrado en Córdoba).
- **Ampliación del 2026-11-14:** se agregaron 18 medios (OTVA-MRE-052 a 069) para Caquetá, Cundinamarca, Amazonas, Guainía, Guaviare, Vaupés y Vichada. Cada uno se comprobó en vivo (HTTP y feed RSS) y la fecha de su último ítem RSS consta en `observaciones`.
- **Cobertura débil:** en Vaupés no se halló ningún medio digital propio. Solo están la sección regional de Radio Nacional y Consonante, que tiene un único ítem de 2025. En Guaviare el único medio local con sitio web es Guaviare Estéreo, cuya afiliación con Caracol Radio está por confirmar. Amazonas News Radio no publica en RSS desde mayo de 2026.
- **Descartados por no responder (2026-11-14):** caqueta.extra.com.co (Extra Caquetá), diariocaqueteno.com, cundinamarques.com y juventudfm.com (Juventud Estéreo, Guaviare). Las emisoras sin sitio web encontrado (Ondas del Amazonas, Fantástica Estéreo, Yuruparí Estéreo, La Voz del Guaviare) no se registraron.
- **Redes sociales:** 18 cuentas de X con handle registrado, sin verificación de titularidad posible desde aquí. Faltan Facebook, Instagram, YouTube, TikTok y Telegram (no se registraron cuentas no comprobadas). La cuenta de Vicepresidencia, las embajadas y los funcionarios quedan como marcadores sin cuenta.
- **Gobernaciones y alcaldías:** las URL siguen el patrón `<entidad>.gov.co`. Las que respondieron se verificaron técnicamente; 10 siguen pendientes (7 gobernaciones y 3 alcaldías).
- **Subsecciones:** sala de prensa, comunicados y alertas tempranas de la mayoría de las instituciones están en `null`. Use `--descubrir` y revise los candidatos de `reporte_calidad.md`.
