#!/usr/bin/env python3
"""Vista previa del tablero v1 (NO toca dist/ ni src/).

Parte de la plantilla vigente (src/template.html) y agrega solo dos cosas decididas el 9-nov-2026:
  1. banner «Preliminar, sin revisión independiente» (ADR-002/003);
  2. fila «Versiones distintas» en la ficha del incidente cuando el registro trae `discrepancia` (ADR-009).
Salida: platform/preview/out/observatorio_v1_preview.html
Uso: python platform/preview/build_preview.py [ruta/data.json]   (por defecto, la exportación de la base desde la instantánea)
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLATFORM = HERE.parent
ROOT = PLATFORM.parent
sys.path.insert(0, str(PLATFORM))
from otva import core  # noqa: E402

BANNER = ('<div class="note warn" role="note"><strong>Preliminar, sin revisión independiente.</strong> '
          'Los registros se publican tras controles automáticos y revisión posterior del equipo; ninguno ha tenido '
          'revisión independiente. Las atribuciones son las que hacen las fuentes citadas, no hechos probados.</div>\n')
NAV_ANCHOR = '<nav class="tabs" aria-label="Secciones">'
ROW_OLD = '${r("Fuentes",links(e))}</dl>`;}'
ROW_NEW = '${e.discrepancia?r("Versiones distintas","⚠ "+esc(e.discrepancia)):""}${r("Fuentes",links(e))}</dl>`;}'


def apply_changes(template: str) -> str:
    for anchor in (NAV_ANCHOR, ROW_OLD):
        if template.count(anchor) != 1:
            raise SystemExit(f"La plantilla cambió: ancla no encontrada o repetida: {anchor[:40]!r}")
    return template.replace(NAV_ANCHOR, BANNER + NAV_ANCHOR).replace(ROW_OLD, ROW_NEW)


def render(template: str, data: dict, geo: dict, logo: str) -> str:
    safe = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return template.replace("__DATA__", safe(data)).replace("__GEO__", safe(geo)).replace("__LOGO__", logo)


def load_logo() -> str:
    logo = (ROOT / "assets" / "geseg_logo.svg").read_text(encoding="utf-8").strip()
    logo = logo.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)
    return re.sub(r'\s(role|aria-label)="[^"]*"', "", logo)


def main():
    if len(sys.argv) > 1:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    else:
        snap = json.loads((PLATFORM / "fixtures" / "v0_snapshot_78d8e27.json").read_text(encoding="utf-8"))
        conn = core.connect(); core.import_v0(conn, snap, "2026-11-09T00:00:00Z"); data = core.export_v0(conn)
    geo = json.loads((ROOT / "data" / "geo.json").read_text(encoding="utf-8"))
    tpl = apply_changes((ROOT / "src" / "template.html").read_text(encoding="utf-8"))
    out = HERE / "out" / "observatorio_v1_preview.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render(tpl, data, geo, load_logo()), encoding="utf-8")
    print("OK ->", out)


if __name__ == "__main__":
    main()
