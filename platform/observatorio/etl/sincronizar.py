"""Sincroniza la base con la v0 viva (data.json de OTVA 01).  Uso:
  python -m etl.sincronizar [ruta/data.json]
Trae eventos nuevos, ediciones, excluidos y contexto. No pisa casos creados en la aplicación (informa los conflictos)."""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent)); sys.path.insert(0, str(ROOT))
from otva import core, ciclo        # noqa: E402
from backend import config as C     # noqa: E402

VIVO = ROOT.parent.parent / "data" / "data.json"


def main(origen: Path):
    if not C.EVENTS_DB.exists():
        raise SystemExit("Falta la carga inicial: python -m etl.cargar inicial")
    data = json.loads(origen.read_text(encoding="utf-8"))
    conn = core.connect(str(C.EVENTS_DB))
    r = ciclo.sincronizar(conn, data, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    chk = (core.verify_event_chain(conn), core.audit_verify(conn))
    conn.close()
    print(f"Corte {data['updated']}: {len(r['nuevos'])} nuevos {r['nuevos']}, {len(r['editados'])} editados {r['editados']}.")
    if r["conflictos"]:
        print("CONFLICTO (id usado por la v0 y por un caso creado en la aplicación; resuélvalo a mano):", r["conflictos"])
    if r["ausentes"]:
        print("Aviso: estos casos de la v0 ya no están en el data.json vivo:", r["ausentes"])
    if chk != (None, None):
        raise SystemExit(f"La cadena de integridad no cuadra: {chk}")
    print("Integridad verificada.")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else VIVO)
