"""Carga del Observatorio.  Uso:
  python -m etl.cargar inicial [data.json]      crea data/db/otva.db desde la v0 (por defecto, el data.json vivo de OTVA 01)
  python -m etl.cargar inicial --instantanea    usa la instantánea congelada 78d8e27 (42 eventos)
Si la base existe, se rechaza salvo --reemplazar (que antes guarda una copia en backups/)."""
import argparse, json, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))      # paquete `otva`
sys.path.insert(0, str(ROOT))
from otva import core                      # noqa: E402
from backend import config as C            # noqa: E402

VIVO = ROOT.parent.parent / "data" / "data.json"
SNAP = ROOT.parent / "fixtures" / "v0_snapshot_78d8e27.json"


def inicial(origen: Path, reemplazar: bool, rol: str):
    C.DB_DIR.mkdir(parents=True, exist_ok=True)
    if C.EVENTS_DB.exists():
        if not reemplazar:
            raise SystemExit(f"Ya existe {C.EVENTS_DB}. Use --reemplazar para rehacerla (se guarda copia en backups/).")
        bk = ROOT / "backups" / time.strftime("%Y-%m-%d_%H%M%S")
        bk.mkdir(parents=True, exist_ok=True)
        shutil.copy2(C.EVENTS_DB, bk / C.EVENTS_DB.name)
        C.EVENTS_DB.unlink()
    data = json.loads(origen.read_text(encoding="utf-8"))
    conn = core.connect(str(C.EVENTS_DB))
    core.import_v0(conn, data, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), role=rol)
    chk = (core.verify_event_chain(conn), core.audit_verify(conn))
    conn.close()
    if chk != (None, None):
        raise SystemExit(f"La cadena de integridad no cuadra tras la carga: {chk}")
    print(f"OK: {len(data['events'])} eventos, {len(data['excluded'])} excluidos, {len(data['context'])} de contexto "
          f"(corte {data['updated']}) -> {C.EVENTS_DB}\nIntegridad: cadenas de eventos y bitácora verificadas.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["inicial"])
    ap.add_argument("archivo", nargs="?")
    ap.add_argument("--instantanea", action="store_true")
    ap.add_argument("--reemplazar", action="store_true")
    ap.add_argument("--usuario", default="sistema", help="rol o responsable de la carga (se registra en la bitácora)")
    a = ap.parse_args()
    src = SNAP if a.instantanea else Path(a.archivo) if a.archivo else VIVO
    if not src.exists():
        raise SystemExit(f"No se encuentra {src}")
    inicial(src, a.reemplazar, a.usuario)
