#!/usr/bin/env python3
"""Inyecta datos, contornos, logo y red de fuentes en la plantilla -> dist/observatorio.html"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, str(ROOT / "src" / "validate.py")], check=True)
safe = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
data = json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))
geo = json.loads((ROOT / "data" / "geo.json").read_text(encoding="utf-8"))
logo = (ROOT / "assets" / "geseg_logo.svg").read_text(encoding="utf-8").strip()
logo = logo.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)
logo = re.sub(r'\s(role|aria-label)="[^"]*"', "", logo)


def red_fuentes():
    """Resumen público del directorio de fuentes abiertas (fuentes_abiertas/fuentes_maestras.json).
    Solo campos descriptivos: no se publican palabras clave, parámetros de consulta ni observaciones internas."""
    p = ROOT / "fuentes_abiertas" / "fuentes_maestras.json"
    if not p.exists():
        return None
    m = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for f in m["fuentes"]:
        r = f.get("resultado_ultima_comprobacion") or {}
        out.append({
            "id": f["id_fuente"], "n": f["nombre"], "cat": f["categoria"], "sub": f.get("subcategoria") or "",
            "niv": f.get("nivel_cobertura") or "", "dep": f.get("departamento") or "", "reg": f.get("region") or "",
            "pla": f.get("plataforma") or "", "url": f.get("url_principal") or "",
            "rss": bool(f.get("url_rss")), "api": bool(f.get("url_api")), "met": f.get("metodo_consulta") or "",
            "est": f["estado"], "conf": (f.get("confiabilidad_fuente") or "")[:2],
            "ver": (f.get("fecha_verificacion") or "")[:10],
            "mot": "" if f["estado"] == "activa" else (r.get("clasificacion") or "sin comprobación técnica"),
        })
    return {"generado": m["metadata"].get("generado", "")[:10], "fuentes": out}


html = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
html = (html.replace("__DATA__", safe(data)).replace("__GEO__", safe(geo))
        .replace("__FUENTES__", safe(red_fuentes())).replace("__LOGO__", logo))
out = ROOT / "dist" / "observatorio.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")
(out.parent / "index.html").write_text(html, encoding="utf-8")  # página de inicio para Vercel
print("OK ->", out, f"({out.stat().st_size // 1024} KB)")
