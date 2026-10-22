#!/usr/bin/env python3
"""Agrega registros nuevos a data/data.json desde un archivo JSON (lista de eventos SIN 'id').
Asigna ids consecutivos, completa 'actualizacion', puede actualizar 'updated' y 'excluded'/'context', y valida.
Uso: python src/add_events.py nuevos.json [--corte AAAA-MM-DD]
El archivo puede ser una lista de eventos o un objeto {"events":[...], "excluded":[...], "context":[...]}."""
import json, sys, subprocess, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
f = Path(sys.argv[1])
corte = sys.argv[sys.argv.index("--corte") + 1] if "--corte" in sys.argv else dt.date.today().isoformat()
new = json.loads(f.read_text(encoding="utf-8"))
if isinstance(new, list):
    new = {"events": new}
dp = ROOT / "data" / "data.json"
d = json.loads(dp.read_text(encoding="utf-8"))
n = max(int(e["id"].split("-")[-1]) for e in d["events"])
for e in new.get("events", []):
    n += 1
    e = dict(e)
    e["id"] = f"CO-2026-{n:03d}"
    e.setdefault("discrepancia", "")
    e.setdefault("eco", "No cuantificado")
    e["actualizacion"] = corte
    d["events"].append(e)
for k in ("excluded", "context"):
    for x in new.get(k, []):
        if x not in d[k]:
            d[k].append(x)
d["updated"] = corte
bak = dp.read_text(encoding="utf-8")
dp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
r = subprocess.run([sys.executable, str(ROOT / "src" / "validate.py")])
if r.returncode:
    dp.write_text(bak, encoding="utf-8")
    sys.exit("Validación fallida: data.json restaurado.")
print(f"Agregados {len(new.get('events', []))} eventos; corte {corte}")
