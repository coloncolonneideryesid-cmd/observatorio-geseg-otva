# Memo de equipo rojo · Hoja ejecutiva OTVA «Terrorismo y violencia armada en Colombia: situación al 10 de noviembre de 2026» · 2026-11-10

**ID de registro:** ER-0023 · **Revisores:** agente rojo (IA); arbitraje de R13 pendiente · experto externo: no
**Rótulo:** Control automatizado de equipo rojo (IA). Revisión independiente pendiente. El producto lo redactó GESEG con Claude, no Neider; por eso puede arbitrar como R13.

## 1. Memo del agente rojo
Íntegro y sin editar: `2026-11-10_memo_agente_rojo.md`. Notas del autor: (a) el premortem menciona el «14 de noviembre», fecha posterior al corte (error del agente); (b) H4 parte de una línea del encabezado del paquete («no declara escala»), escrita por el autor del paquete; es cierta de todos modos: el PDF no gradúa sus juicios; (c) el agente no abrió ningún enlace.

## 2. Respuesta del autor
Comprobado por el autor: las sumas, los porcentajes (56%, 66%, 55%, 41%), la clasificación de brechas por departamento y la aritmética de ventanas cuadran. Limitación: el `data.json` local del OTVA tiene 42 hechos (corte 8-nov), no los 99 del PDF; no se pudo contrastar con la base de origen.

| Hallazgo | Decisión | Razón | Cambio propuesto |
|---|---|---|---|
| H1 estable vs. señales que suben | Acepta | «Estable» (8 vs 8) convive con VBIED 5 vs 1 y civiles 38 vs 12. La última semana puede estar incompleta (PDF generado a media mañana del 10-nov) y la verificación tiene rezago | Reformular «estable» como «hechos estables; daño a civiles y vehículos con explosivos al alza»; explicar ventanas; nota de rezago |
| H2 «Extremo» / «en expansión» | Acepta | Criterios circulares; no hay serie de expansión | Quitar «en expansión» o añadir serie mensual por departamento; definir umbrales; evaluar «Muy alto» |
| H3 brecha / judicialización | Acepta | Dos muestras con selección distinta; «operación vinculada a atentado» no es judicialización; rezago judicial en hechos recientes | Renombrar «operaciones registradas en la base»; retirar o fundar «poca judicialización»; confianza baja |
| H4 sin escala ni confianza | Acepta en parte | Válido para los juicios de «Lo esencial» y el riesgo; el OTVA no está obligado por el §9, pero el producto promete «hacia dónde va la tendencia» | Graduar los juicios principales o quitar la promesa |
| H5 dos cifras «38» | Acepta | 144−106=38 civiles por drones; la coincidencia con los 38 civiles de 14 días no se pudo verificar | Rotular periodos y verificar en la base |
| H6 Santa Rosa del Sur | Acepta | 3+16=19 de 29 víctimas (66%) | Mostrar la variación sin ese evento |
| H7 muestra y denominador (FIP) | Acepta | FIP ~1,16 al día frente a ~0,57 de la base; «uno cada 1,7 días» puede leerse como frecuencia nacional | Subir el aviso de muestra junto a drones; reformular la frecuencia |
| H8 bombardeos sin fuente | Acepta | Punto sensible sin enlace | Citar con enlace (Medicina Legal, decisión judicial) o suprimir |
| H9 truncamientos y balances | Acepta | «13.58…» y «…» son defecto visible | Completar o retirar; presentar neutral y con fuente |
| H10 agrupaciones | Acepta en parte | Solo si la fuente distingue estructuras | Desagregar donde se pueda |
| H11 empate Huila/Valle | Acepta | Ambos con 11 | Citar el empate |
| H12 redacción | Acepta en parte | «1 heridos» se corrige; «De la Espriella» no se pudo verificar | Corregir concordancia; verificar el nombre |
| H13 terceros yuxtapuestos | Acepta en parte | Ya dice «no se suman» | Hacerlo más visible |
| A1 (autor) corte incompleto | Propio | La ventana 4–10 nov incluye un día en curso | Declarar corte con hora |
| A2 (autor) enlace al tablero | Propio | Apunta a un artefacto de claude.ai; el destinatario puede no poder abrirlo | Confirmar acceso o usar la URL pública |

## 3. Revisión de R13 (Neider)
| Hallazgo | Arbitraje | Comentario |
|---|---|---|
| H1–H13, A1, A2 | Acepta la respuesta del autor completa (10-nov-2026, en el chat) | Neider arbitra como R13: GESEG con Claude redactó la hoja |
**Resultado:** ajustar la confianza.
**Cambios de confianza o de juicio derivados (por aplicar):** «actividad estable» → hechos estables con daño a civiles y vehículos con explosivos al alza; retirar «en expansión» o añadir serie; «brecha»/«poca judicialización» → «operaciones registradas en la base», confianza baja; graduar los juicios principales; aviso de muestra junto al titular de drones; fuente o supresión de «Bombardeos bajo escrutinio»; completar o retirar balances truncados; rotular las dos cifras «38»; corte con hora; verificar enlace al tablero.
**Estado de aplicación:** NO aplicados. El PDF viene de un artefacto de claude.ai (enlace del pie) al que esta cuenta no tiene acceso (404), y el `data.json` local tiene 42 hechos, no 99. Se necesita la fuente HTML o la base para regenerar. Mientras tanto, la versión actual conserva el rótulo «Control automatizado de equipo rojo (IA); revisión independiente pendiente» y no debe circular como corregida.

## 6. Aprobación
Pendiente (aprobador designado en DM-24; el nombre va solo en registros internos).

## 7. Seguimiento de la aplicación (10-nov-2026)
Neider entregó `template_ejecutivo.html` (copia en `fuente_recibida/`). Es una plantilla con marcadores `__LOGO__`, `__DATA__` y `__GEO__`: no contiene los 99 hechos ni las operaciones. Además **no coincide con el PDF revisado**: el subtítulo es otro («Lectura breve dirigida a analistas…» frente a «Lectura de tres minutos para gobierno nacional y local…») y el orden de secciones difiere (en el PDF, drones va en la página 2 antes de tendencia y actores; en la plantilla va después). Parece una versión anterior. Pendiente: la plantilla vigente y el `DATA` (con `ops` y `ops_agregados`) con que se generó el PDF. No se editó nada para no introducir regresiones.

### 7.1 Plantilla v2 (10-nov-2026)
Neider indicó usar la plantilla recibida. `aplicar_cambios_er0023.py` genera `plantilla_v2/template_ejecutivo_v2.html` (la recibida queda intacta en `fuente_recibida/`): subtítulo y orden de secciones alineados con el PDF; H1, H2, H3, H5, H6, H7, H8, H9, H11, H12, A1 aplicados; H4 con confianza en palabras (sin probabilidades); descensos en color neutro. Sintaxis JS verificada. **No se generó PDF:** faltan el `DATA` de los 99 hechos (con `ops` y `ops_agregados`) y el `GEO`/logo. H8: las frases de Medicina Legal y del juez se muestran solo si `ops_agregados` trae su fuente; H10 y A2 siguen pendientes (A2: confirmar acceso al enlace del tablero).

### 7.2 Revisión de la plantilla v2 (10-nov-2026)
Prueba de render con los 42 hechos locales, operaciones simuladas y GEO/logo del OTVA (solo en el directorio temporal de la sesión; no es entregable). Resultado: 4 páginas, orden correcto, sin errores de JS; encontrado y corregido el titular del punto 1 (decía «van al alza» aunque los vehículos con explosivos estaban planos; ahora nombra solo las series que suben). Corrección al §7: el `data.json` local **sí** contiene Santa Rosa del Sur (7-nov); la búsqueda anterior solo miró `platform/`. Sigue sin explicarse la diferencia 42 frente a 99 hechos.

## 8. Aplicación al producto (10-nov-2026)
Con el `DATA` de 99 hechos (copia en `fuente_recibida/`) se generó `salida/Observatorio_GESEG_Ejecutivo-4.pdf` (4 páginas, Letter, texto al 80 % para que quepa el contenido con las fuentes reales; copia en Descargas con ese nombre; HTML de origen junto al PDF). El original se conserva en `_versiones_anteriores/`; el script `construir_pdf.py` lo reproduce.
**Verificación contra la base (hecha por el autor):** todas las cifras del PDF original coinciden con el `data.json` (99 hechos; 31 muertos; 231 heridos; 102 civiles; 55 drones; 38 civiles por drones en 11 ataques; ventanas 8/29 frente a 8/39; 73 operaciones, 7 bombardeos con 56 muertos, 170 capturados, 30 vinculadas). La diferencia 42 frente a 99 era el `data.json` local desactualizado.
**Hallazgos nuevos por la base:** (1) los dos «38» son coincidencia y miden cosas distintas (H5 confirmado); (2) de los 38 civiles muertos o heridos en 14 días, **31 fueron por vehículos con explosivos y solo 7 por drones**: el aumento del daño a civiles no viene de los drones, lo que refuerza la hipótesis rival del agente; ahora figura en «Lo esencial»; (3) H8: las afirmaciones de Medicina Legal (El Colombiano) y del Juez 34 de Familia (Vanguardia) sí tienen fuente en la base y ahora llevan enlace; (4) «De la Espriella» procede de las fuentes citadas.
**Rótulo vigente:** control automatizado de equipo rojo (IA) + arbitraje de R13 (Neider, 10-nov-2026); revisión independiente pendiente (aprobación: DM-24). El PDF no lleva leyenda de revisión.
**Pendiente:** H10 (desagregar estructuras) y A2 (enlace al tablero apunta a un artefacto de claude.ai; verificar acceso). Los cambios solicitados sobre el «Extremo» se aplicaron como redacción; la decisión de pasar a «Muy alto» sigue en manos de Neider.

Nota técnica: la plantilla original, renderizada en este equipo, da 9 páginas (no 4); su ajuste a 4 páginas dependía de las fuentes de sustitución del entorno original. `construir_pdf.py` incrusta Libre Franklin e IBM Plex Mono para que el resultado sea reproducible.

## 9. Decisión de R13 sobre el nivel de riesgo (10-nov-2026)
Neider decide **mantener «Extremo»** para los drones con explosivos, con la redacción ya aplicada (dominante en la base, letal y con afectación a civiles; sin «en expansión»; confianza moderada). Sin cambios adicionales al PDF.
