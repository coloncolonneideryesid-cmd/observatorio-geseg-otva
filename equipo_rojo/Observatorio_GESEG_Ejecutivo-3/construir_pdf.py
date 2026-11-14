# Inyecta DATA/GEO/logo en plantilla_v2 y deja el HTML listo para imprimir a PDF con Chrome.
import json, pathlib, sys
base = pathlib.Path(__file__).parent
otva = base.parents[1]
data = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
json.loads(data)
geo = (otva / "data" / "geo.json").read_text(encoding="utf-8")
logo = (otva / "assets" / "geseg_logo.svg").read_text(encoding="utf-8")
tpl = (base / "plantilla_v2" / "template_ejecutivo_v2.html").read_text(encoding="utf-8")
import base64, re
def b64(f): return base64.b64encode((base / "plantilla_v2" / "fonts" / f).read_bytes()).decode()
fonts = ("<style>@font-face{font-family:'Libre Franklin';font-weight:100 900;font-style:normal;src:url(data:font/woff2;base64,%s) format('woff2')}"
         "@font-face{font-family:'IBM Plex Mono';font-weight:500;font-style:normal;src:url(data:font/woff2;base64,%s) format('woff2')}</style>") % (b64("LibreFranklin-latin.woff2"), b64("IBMPlexMono-500-latin.woff2"))
tpl = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>', fonts, tpl)
tpl = re.sub(r'<link rel="preconnect"[^>]*>\s*', '', tpl)
html = "<!doctype html><html lang='es'><meta charset='utf-8'>" + tpl.replace("__LOGO__", logo).replace("__DATA__", data).replace("__GEO__", geo) + "</html>"
out = pathlib.Path(sys.argv[2]); out.write_text(html, encoding="utf-8"); print(out)
