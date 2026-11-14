# Arma el paquete del equipo rojo (NG-COM-06) a partir del PDF: solo lo que el producto afirma.
import fitz, sys, pathlib
pdf, out = sys.argv[1], pathlib.Path(sys.argv[2])
d = fitz.open(pdf)
txt = "\n\n--- PÁGINA ---\n\n".join(p.get_text() for p in d)
links = sorted({l["uri"] for p in d for l in p.get_links() if l.get("uri")})
enc = f"""# Paquete para equipo rojo · Hoja ejecutiva «Terrorismo y violencia armada en Colombia: situación al 10 de noviembre de 2026» (GESEG)
Fecha de corte del producto: 10-nov-2026. Producto de 4 páginas, destinado a gobierno nacional y local. Uso institucional, fuentes abiertas.
Decisión en juego: priorizar la amenaza de drones con explosivos y valorar la respuesta del Estado (brechas por departamento).
Escala GESEG de riesgo de 5 niveles (Bajo, Medio, Alto, Muy alto, Extremo); el producto califica los drones como «Extremo». No declara escala de probabilidad ni confianza por juicio.

## Enlaces que contiene el producto
{chr(10).join(links)}
(El PDF no trae enlaces a FIP, Defensoría, El Espectador, Vicepresidente, El Colombiano ni a la alocución presidencial. Un dato de contexto de la base del mismo observatorio: Defensoría del Pueblo citada por Al Jazeera, 18-sep-2026: https://www.aljazeera.com/amp/news/2026/9/18/drone-attacks-by-colombian-armed-groups-more-than-double-in-early-2026 )

## Texto íntegro del producto (extraído del PDF; los números sueltos de gráficos aparecen fuera de contexto)

{txt}
"""
out.write_text(enc, encoding="utf-8")
print(len(enc))
