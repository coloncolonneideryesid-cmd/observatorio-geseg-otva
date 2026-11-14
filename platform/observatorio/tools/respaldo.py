"""Copia de seguridad de las bases (eventos y usuarios) en backups/AAAA-MM-DD_HHMMSS.  Uso: python tools/respaldo.py"""
import shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend import config as C  # noqa: E402

dest = ROOT / "backups" / time.strftime("%Y-%m-%d_%H%M%S")
dest.mkdir(parents=True, exist_ok=True)
for f in (C.EVENTS_DB, C.USERS_DB):
    if f.exists():
        shutil.copy2(f, dest / f.name)
print("Copia en", dest, "(contiene usuarios y claves cifradas: guárdela fuera del repositorio)")
