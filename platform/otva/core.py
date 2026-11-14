"""Núcleo de la Fase 1: hash canónico, base SQLite, bitácora encadenada, importación y exportación de la v0.
Solo biblioteca estándar. Sin red."""
import hashlib, json, sqlite3, unicodedata, uuid
from pathlib import Path

PIPELINE_VERSION = "p1.0.0"
MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"
_NS = uuid.UUID("6f1c0e0e-7d2b-5a55-9b0e-0f0f0e7a0001")  # espacio de nombres fijo para UUID determinista

# El "estado" de la v0 (Confirmado / Preliminar / En investigación) describe la solidez de los hechos, no una revisión
# humana: todos entran como PRELIMINAR y el valor original queda en legacy_payload.
STATUS_MAP = {"Preliminar": "PRELIMINAR", "Confirmado": "PRELIMINAR", "En investigación": "PRELIMINAR"}
GEO_MAP = {"Municipal aproximada": "municipio", "Departamental aproximada": "departamento"}


def _nfc(o):
    if isinstance(o, str):
        return unicodedata.normalize("NFC", o)
    if isinstance(o, list):
        return [_nfc(x) for x in o]
    if isinstance(o, dict):
        return {_nfc(k): _nfc(v) for k, v in o.items()}
    return o


def canon(o) -> str:
    return json.dumps(_nfc(o), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def migrar(conn):
    """Aplica en orden las migraciones pendientes (idempotente)."""
    hay = conn.execute("SELECT name FROM sqlite_master WHERE name='schema_migration'").fetchone()
    hechas = {r[0] for r in conn.execute("SELECT version FROM schema_migration")} if hay else set()
    for f in sorted(MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        v = f.name[:4]
        if v not in hechas:
            conn.executescript(f.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migration VALUES (?, ?)", (v, "1970-01-01T00:00:00Z"))
    conn.commit()


def connect(path=":memory:"):
    """Abre (o crea) la base de escritura y aplica las migraciones pendientes."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    migrar(conn)
    return conn


# ---------- bitácora encadenada ----------
def audit_append(conn, ts, role, action, obj, detail) -> str:
    prev = conn.execute("SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    prev = prev[0] if prev else ""
    d = sha(canon(detail))
    h = sha(prev + canon({"ts": ts, "role": role, "action": action, "object": obj, "detail_hash": d}))
    conn.execute("INSERT INTO audit_log(ts,role,action,object,detail_hash,prev_hash,row_hash) VALUES (?,?,?,?,?,?,?)",
                 (ts, role, action, obj, d, prev, h))
    return h


def audit_verify(conn):
    """Devuelve None si la cadena es íntegra, o el id de la primera fila inconsistente."""
    prev = ""
    for id_, ts, role, action, obj, d, p, h in conn.execute(
            "SELECT id,ts,role,action,object,detail_hash,prev_hash,row_hash FROM audit_log ORDER BY id"):
        exp = sha(prev + canon({"ts": ts, "role": role, "action": action, "object": obj, "detail_hash": d}))
        if p != prev or h != exp:
            return id_
        prev = h
    return None


# ---------- importación de la v0 ----------
COLS = ["event_id", "version", "status", "event_type", "modus_raw", "t_start", "t_precision", "depto", "mpio",
        "divipola_mpio", "lat", "lon", "geo_precision", "reported_actor", "actor_name", "attribution_level",
        "attribution_basis", "casualties_civil_killed", "casualties_civil_injured", "casualties_public_force_killed",
        "casualties_public_force_injured", "kidnapped", "target_class", "archive_status", "claim_flags",
        "legacy_payload", "pipeline_version"]


def map_event(e: dict) -> dict:
    """Mapeo v0 -> v1 (docs 02 §5). Estricto: un valor desconocido detiene la importación."""
    if e["estado"] not in STATUS_MAP:
        raise ValueError(f"estado v0 sin mapeo: {e['estado']!r} ({e['id']})")
    if e["prec_coord"] not in GEO_MAP:
        raise ValueError(f"prec_coord v0 sin mapeo: {e['prec_coord']!r} ({e['id']})")
    flags = ["versiones contradictorias"] if e.get("discrepancia") else []
    return {
        "event_id": str(uuid.uuid5(_NS, e["id"])), "version": 1, "status": STATUS_MAP[e["estado"]],
        "event_type": None, "modus_raw": e["mod"], "t_start": e["fecha"], "t_precision": "día",
        "depto": e["depto"], "mpio": e["mpio"], "divipola_mpio": None, "lat": e["lat"], "lon": e["lon"],
        "geo_precision": GEO_MAP[e["prec_coord"]], "reported_actor": e["autor"],
        "actor_name": None if e["grupo"] == "No determinado" else e["grupo"],
        "attribution_level": e["atrib"], "attribution_basis": e["evidencia"],
        "casualties_civil_killed": e["m_civ"], "casualties_civil_injured": e["h_civ"],
        "casualties_public_force_killed": e["m_fp"], "casualties_public_force_injured": e["h_fp"],
        "kidnapped": None, "target_class": e["objetivo"], "archive_status": "legacy_unarchived",
        "claim_flags": canon(flags), "legacy_payload": json.dumps(_nfc(e), ensure_ascii=False, separators=(",", ":")),
        "pipeline_version": PIPELINE_VERSION,  # legacy_payload conserva el orden de claves de la v0
    }


def import_v0(conn, data: dict, ts: str, role: str = "sistema"):
    for i, e in enumerate(data["events"]):
        row = map_event(e)
        fields = {k: row[k] for k in COLS}
        h = sha(canon(fields) + "")           # prev_hash = "" en la versión 1
        conn.execute("INSERT INTO event(event_id,legacy_id,seq) VALUES (?,?,?)", (row["event_id"], e["id"], i))
        conn.execute(f"INSERT INTO event_version({','.join(COLS)},prev_hash,row_hash) VALUES ({','.join('?'*len(COLS))},?,?)",
                     [row[k] for k in COLS] + ["", h])
        for pos, url in enumerate(e["fuentes"]):
            did = sha(url)
            conn.execute("INSERT OR IGNORE INTO source_document(doc_id,url,canonical_url) VALUES (?,?,?)", (did, url, url))
            conn.execute("INSERT INTO event_source VALUES (?,?,?,?,?)", (row["event_id"], 1, did, "supports", pos))
    for i, r in enumerate(data["excluded"]):
        conn.execute("INSERT INTO excluded_record VALUES (?,?)", (i, canon(r)))
    for i, r in enumerate(data["context"]):
        conn.execute("INSERT INTO context_note VALUES (?,?)", (i, canon(r)))
    conn.execute("INSERT INTO meta VALUES ('updated', ?)", (data["updated"],))
    audit_append(conn, ts, role, "import_v0", "data.json",
                 {"events": len(data["events"]), "excluded": len(data["excluded"]), "context": len(data["context"]),
                  "updated": data["updated"], "pipeline_version": PIPELINE_VERSION})
    conn.commit()


def verify_event_chain(conn):
    """None si íntegro; si no, (event_id, version) de la primera versión inconsistente."""
    cur = conn.execute(f"SELECT {','.join(COLS)},prev_hash,row_hash FROM event_version ORDER BY event_id,version")
    prev_by = {}
    for r in cur:
        fields = dict(zip(COLS, r[:len(COLS)]))
        prev, h = r[len(COLS)], r[len(COLS) + 1]
        exp_prev = prev_by.get(fields["event_id"], "")
        if prev != exp_prev or h != sha(canon(fields) + prev):
            return fields["event_id"], fields["version"]
        prev_by[fields["event_id"]] = h
    return None


# ---------- exportación al formato de la v0 ----------
def export_v0(conn) -> dict:
    """Reconstruye data.json desde la base (última versión de cada evento, en orden de la v0)."""
    events = []
    for (payload,) in conn.execute(
            """SELECT v.legacy_payload FROM event e JOIN event_version v ON v.event_id=e.event_id
               WHERE v.version=(SELECT MAX(version) FROM event_version WHERE event_id=e.event_id)
               ORDER BY e.seq"""):
        events.append(json.loads(payload))
    excluded = [json.loads(p) for (p,) in conn.execute("SELECT payload FROM excluded_record ORDER BY seq")]
    context = [json.loads(p) for (p,) in conn.execute("SELECT payload FROM context_note ORDER BY seq")]
    updated = conn.execute("SELECT value FROM meta WHERE key='updated'").fetchone()[0]
    return {"updated": updated, "events": events, "excluded": excluded, "context": context}
