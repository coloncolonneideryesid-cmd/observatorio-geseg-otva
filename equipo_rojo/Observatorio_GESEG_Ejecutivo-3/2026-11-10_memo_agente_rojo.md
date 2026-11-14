# Memo de equipo rojo · Hoja ejecutiva «Terrorismo y violencia armada en Colombia: situación al 10 de noviembre de 2026» · 10-nov-2026
Rótulo: Control automatizado de equipo rojo (IA). No equivale a revisión independiente.

## Recomendación: ajustar la confianza
Los datos son internamente coherentes: revisé las sumas del paquete y cuadran, incluidos 31 muertos (25 + 6), 144 víctimas por drones (55%), 66% de uniformados, autoría 25+33+2+39=99 y operaciones por actor. Lo que no se sostiene es la inferencia. Hay tres ajustes:
- Bajar la confianza de «Extremo / en expansión».
- Reformular el juicio de «brecha de respuesta del Estado».
- Declarar probabilidad y confianza por juicio.

## Premortem
Si en tres meses el juicio resultó equivocado, las explicaciones más plausibles son:
1. **La amenaza que escaló fue otra.** El 14 de noviembre en adelante crecieron los vehículos con explosivos (5 frente a 1) y el daño a civiles (38 frente a 12), y la atención se fue a los drones. Los drones se mantuvieron en 9 frente a 9.
2. **La dominancia de los drones (56%) es un artefacto de la muestra.** La base recoge hechos de «alta visibilidad» y excluye combates y atentados frustrados. Los drones son muy cubiertos por la prensa, y la FIP cuenta 318 ataques en 274 días (~1,16 al día) frente a 0,58 al día en la base.
3. **La «brecha» de respuesta era un vacío de registro.** Que no figuren operaciones o capturas en una muestra de resultados «visibles» no demuestra que no ocurrieran. La conclusión sobre Cauca, Huila y Chocó puede ser contraproducente ante el destinatario.

## Hipótesis rival más fuerte
La amenaza se está **diversificando**, no concentrando en drones: pasa a vehículos con explosivos y a mayor afectación a civiles. Los drones serían el techo estable de una muestra sesgada por visibilidad.

Para que gane tendría que ser cierto que:
- la proporción de drones cae al ampliar la muestra con hechos menos visibles;
- los vehículos con explosivos y los civiles heridos siguen subiendo las próximas dos semanas;
- la letalidad de los drones depende de pocos eventos extremos.

El paquete es compatible con esta hipótesis. Entre los 14 y los 28 días previos, los drones están planos (9 frente a 9) y las señales que suben son vehículos con explosivos y civiles. Santa Rosa del Sur (3 muertos, 16 heridos) explica 19 de las 29 víctimas de la semana. En Cauca, la mayor concentración y nivel «Alto», los drones son 10 de 28 hechos (36%).

## Supuestos críticos
| Supuesto | Calificación | Qué lo pondría en duda |
|---|---|---|
| La base es representativa de la dinámica real de modalidades | Débil | Declara ser una muestra de alta visibilidad. La FIP cuenta ~2× la tasa de ataques con drones, y la base excluye frustrados |
| «Extremo» exige expansión territorial | Débil | No hay serie de primera aparición por departamento ni por mes. La tendencia de 14 días es «=» |
| La cobertura de recolección fue constante desde el 7-ago | Discutible | La primera semana es parcial. Si hubo curva de aprendizaje, la tendencia se distorsiona |
| Operaciones registradas frente a atentados mide «respuesta» | Débil | Son universos distintos (finanzas, narcotráfico, bombardeos); la muestra es «verificada», no el total oficial; las capturas judiciales se registran con retraso |
| El señalamiento «oficial» es un indicador fiable de autoría | Discutible | Es atribución institucional, no decisión judicial. El producto lo advierte, pero «Disidencias FARC» agrupa estructuras distintas |
| Comparar 7 días contra 7 días (8 hechos frente a 8) describe la tendencia | Discutible | Ventanas cortas con n=8 son ruido. Una sola acción explica la caída o el pico de víctimas |

## Hallazgos
| ID | Tipo | Severidad | Dónde | Qué | Por qué importa | Qué lo resolvería |
|---|---|---|---|---|---|---|
| H1 | Contradicción interna | Crítico | «Lo esencial» 1 y 3; p. 3 señales | El punto 1 dice «actividad estable». En 14 días los vehículos con explosivos suben (5 frente a 1) y los civiles heridos o muertos se triplican (38 frente a 12). Los titulares muestran «▼20 civiles» a 7 días | El lector queda con mensajes opuestos. La decisión de priorizar drones omite las señales que sí escalan | Explicar las dos ventanas (7 y 14 días). Elevar la señal de VBIED y civiles como alerta |
| H2 | Juicio no sustentado | Crítico | p. 2 «Riesgo extremo… en expansión territorial» | «Extremo» se define por criterios que se cumplen por construcción (dominante + letal + extendida + civiles). La expansión no tiene serie temporal. La escala de 5 niveles no define umbrales de los demás niveles | El rótulo máximo orienta recursos. Es un juicio con consecuencias | Serie por mes y departamento. Definir umbrales y por qué no hay un nivel superior. Bajar a «Muy alto» si no hay evidencia de expansión |
| H3 | Inferencia de muestra | Crítico | p. 4 «Brecha alta», «respuesta visible baja», «poca judicialización» | Se infiere una brecha del Estado comparando atentados con operaciones registradas en una muestra de «alta visibilidad». Umbrales arbitrarios (4 de cada 10, 8 de cada 10). Ausencia de registro tratada como ausencia de judicialización | Destinado a gobierno nacional y local: puede leerse como evaluación política sin respaldo. Riesgo de lenguaje por la cautela con juicios sobre gestión | Reformular como «registro de operaciones en la base». Mostrar el universo oficial. Declarar confianza baja |
| H4 | Escalas | Importante | Todo el documento | El producto declara que no usa escala de probabilidad ni confianza por juicio. «Hacia dónde va la tendencia» es una promesa del arranque que no se cumple con pronóstico | Incumple el estándar GESEG (DD-1). Los juicios prospectivos quedan sin graduar | Añadir nivel y confianza. Sugiero: dron como modalidad dominante en la base, Muy probable, confianza moderada; expansión territorial, Posibilidad real, confianza baja; brecha de respuesta, Posibilidad real, confianza baja |
| H5 | Cifra ambigua | Importante | p. 2 «38 civiles… en 11 ataques con drones» y p. 3 «38 personas (antes 12)» | Dos cifras de 38 distintas (acumulado por drones frente a 14 días de civiles totales). Puede confundirse | Riesgo de lectura errónea o de cifra citada fuera de contexto | Rotular cada una con su periodo. Verificar que no sea el mismo dato duplicado |
| H6 | Dependencia de un evento | Importante | Semana final; titular 7-nov | Santa Rosa del Sur aporta 19 de 29 víctimas de la semana. La comparación de víctimas (29 frente a 39) es sensible a pocos eventos | Las variaciones de víctimas no son tendencia | Presentar también la mediana o mostrar la variación sin ese evento |
| H7 | Muestra y denominador | Importante | p. 1 y 2; pie metodológico | Los porcentajes (56%, 70%, 55%) son sobre una muestra construida por criterios de visibilidad, y el pie lo reconoce solo al final. La FIP cita 318 ataques con drones en 274 días; la base, 55 en 95 | El lector toma 56% como la participación real de los drones | Subir el aviso de muestra junto al titular de drones. No comparar con la FIP sin conciliar definiciones |
| H8 | Lenguaje y fuentes | Importante | p. 4 «Bombardeos bajo escrutinio» | Afirmaciones sensibles (56 muertos reportados, menores de edad según Medicina Legal, orden de un juez) sin fuente enlazada en el PDF | Afirmaciones jurídicas y de DD. HH. no rastreables | Enlazar o citar cada una. Si no, suprimirlas |
| H9 | Presentación | Importante | «Balances oficiales» | Textos truncados («13.58…», «…»). Contrapone balances del Gobierno con una verificación de prensa sin metodología. Sin enlaces | El producto se vuelve político sin querer. Defecto de acabado visible para el alto Gobierno | Completar o retirar. Presentar los balances de forma neutra y con fuente |
| H10 | Agrupación | Importante | p. 3 «Quién aparece señalado» | «Disidencias FARC» y «Otros actores» agrupan estructuras distintas. 39% sin autor | Perjudica la respuesta focalizada y puede inducir sesgo de atribución | Desagregar por estructura cuando la fuente lo permita |
| H11 | Selección de ejemplos | Menor | Resumen «Lo esencial» 2 | El top 3 omite a Valle (también 11, igual que Huila) | Elección arbitraria | Citar el empate |
| H12 | Redacción | Menor | p. 3 | «1 heridos»; «Presidente De la Espriella» (verificar forma) | Acabado | Corregir |
| H13 | Causalidad | Menor | Pie de la gráfica «Defensoría: aumento del 146%… ene–may» | La cifra de terceros se yuxtapone a la base sin aclarar que miden cosas distintas | Puede leerse como validación mutua | Mantener el aviso «no se suman» más visible |

## Enlaces abiertos durante la revisión
Ninguno. No abrí el enlace de Al Jazeera ni el del artefacto. Las objeciones salen de la coherencia interna del paquete y de aritmética propia. Quedan por contrastar con sus fuentes primarias:
- FIP
- Defensoría
- El Espectador
- El Colombiano
- la alocución presidencial
- Medicina Legal sobre los bombardeos
