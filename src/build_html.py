#!/usr/bin/env python3
"""Inyecta datos, contornos y logo en la plantilla -> dist/observatorio.html"""
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
html = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
html = html.replace("__DATA__", safe(data)).replace("__GEO__", safe(geo)).replace("__LOGO__", logo)
out = ROOT / "dist" / "observatorio.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")
(out.parent / "index.html").write_text(html, encoding="utf-8")  # página de inicio para Vercel
print("OK ->", out, f"({out.stat().st_size // 1024} KB)")
