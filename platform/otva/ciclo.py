"""Ciclo de vida de los casos: crear, editar, revisar, retractar, sincronizar con la v0 y exportar lo publicable.

Reglas (ADR-002/003):
  CANDIDATO -> PRELIMINAR      editor/admin; pasa las compuertas de publicación (duras: nunca se saltan)
  CANDIDATO -> DESCARTADO      editor/admin, con motivo
  PRELIMINAR -> VERIFICADO_EQUIPO   solo admin, y distinto de quien creó o editó el caso (dos llaves)
  PRELIMINAR|VERIFICADO_EQUIPO -> RETRACTADO | DESCARTADO   solo admin, con motivo
  VERIFICADO_INDEPENDIENTE  reservado a R13: el sistema no lo asigna mientras ese rol no exista
Cada cambio crea una versión nueva (la historia es inmutable) y queda en event_action y en audit_log.
"""
import datetime as dt, json, os, re, time, unicodedata, uuid
from urllib.parse import urlparse

from . import core, gates

INICIO = dt.date(2026, 8, 7)
MODS = ["Dron con explosivos", "Vehículo con explosivos", "Explosivo / IED", "Granada / artefacto lanzado",
        "Paro armado", "Homicidio selectivo", "Ataque armado"]
GRUPOS = ["ELN", "Disidencias FARC", "Clan del Golfo / EGC", "ACSN", "Autor individual (capturado)", "No determinado"]
ESTADOS_V0 = ["Confirmado", "Preliminar", "En investigación"]
PREC = ["Municipal aproximada", "Departamental aproximada"]
HORAS = ["Sin dato", "Madrugada", "Mañana", "Tarde", "Noche", "Día"]
STR = ["fecha", "hora", "depto", "mpio", "lugar", "prec_coord", "tipo", "mod", "objetivo", "clase", "autor", "grupo", "atrib",
       "evidencia", "h_nota", "danos", "eco", "desplaz", "servicios", "estado", "discrepancia"]
INT = ["m_civ", "m_fp", "h_civ", "h_fp"]
PUBLICABLES = ("PRELIMINAR", "VERIFICADO_EQUIPO", "VERIFICADO_INDEPENDIENTE")
DEFECTOS = {"hora": "Sin dato", "prec_coord": "Municipal aproximada", "h_nota": "No documentado", "danos": "No documentado",
            "eco": "No cuantificado", "desplaz": "No documentado", "servicios": "No documentado", "discrepancia": "",
            "m_civ": 0, "m_fp": 0, "h_civ": 0, "h_fp": 0, "estado": "Preliminar", "clase": "Incierto – autoría y finalidad no establecidas",
            "autor": "No determinado", "grupo": "No determinado", "atrib": "E", "evidencia": "Ninguna autoridad ha atribuido el hecho."}


class Rechazo(Exception):
    """Operación no permitida o datos inválidos; `.motivos` es la lista para mostrar al usuario."""
    def __init__(self, motivos):
        self.motivos = [motivos] if isinstance(motivos, str) else list(motivos)
        super().__init__("; ".join(self.motivos))


def _uuid7():
    ms = int(time.time() * 1000)
    b = bytearray(ms.to_bytes(6, "big") + os.urandom(10))
    b[6] = (b[6] & 0x0F) | 0x70
    b[8] = (b[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(b)))


def _fecha_de(ts):
    return ts[:10]


# ---------- validación (misma regla que src/validate.py de la v0) ----------
def validar_registro(e: dict, corte: str | None = None):
    err = []
    for k in STR + INT + ["lat", "lon", "fuentes"]:
        if k not in e:
            err.append(f"falta el campo '{k}'")
    if err:
        return err
    for k in STR:
        if not isinstance(e[k], str):
            err.append(f"'{k}' debe ser texto")
    for k in INT:
        if not isinstance(e[k], int) or isinstance(e[k], bool) or e[k] < 0:
            err.append(f"'{k}' debe ser un entero mayor o igual a 0")
    try:
        f = dt.date.fromisoformat(e["fecha"])
        if f < INICIO:
            err.append(f"la fecha es anterior al {INICIO} (inicio del observatorio)")
        if corte and f > dt.date.fromisoformat(corte):
            err.append("la fecha es posterior a hoy")
    except Exception:
        err.append("fecha inválida (use AAAA-MM-DD)")
    if not (re.fullmatch(r"\d{2}:\d{2}", e["hora"]) or e["hora"] in HORAS):
        err.append(f"hora inválida '{e['hora']}'")
    if e["atrib"] not in list("ABCDE"):
        err.append("la atribución debe ser A–E")
    if e["mod"] not in MODS:
        err.append("modalidad fuera de la lista controlada")
    if e["grupo"] not in GRUPOS:
        err.append("grupo fuera de la lista controlada")
    if e["estado"] not in ESTADOS_V0:
        err.append("estado inválido")
    if e["prec_coord"] not in PREC:
        err.append("precisión de coordenada inválida")
    if e["atrib"] == "E" and e["grupo"] != "No determinado":
        err.append("atribución E exige grupo 'No determinado' (no se infiere autoría)")
    if e["atrib"] in "ABCD" and not e["evidencia"].strip():
        err.append("atribución A–D exige indicar la base (quién atribuye)")
    if not (isinstance(e["lat"], (int, float)) and isinstance(e["lon"], (int, float))
            and -4.3 <= e["lat"] <= 13.5 and -79.1 <= e["lon"] <= -66.8):
        err.append("coordenadas fuera de Colombia")
    fu = e["fuentes"]
    if not isinstance(fu, list) or not 1 <= len(fu) <= 3 or not all(isinstance(u, str) and u.startswith("https://") for u in fu):
        err.append("las fuentes deben ser de 1 a 3 enlaces https://")
    for k in ("tipo", "lugar", "depto", "mpio"):
        if isinstance(e.get(k), str) and not e[k].strip():
            err.append(f"'{k}' no puede estar vacío")
    return err


# ---------- lectura ----------
def _ultima(conn, event_id):
    r = conn.execute("""SELECT v.version,v.status,v.row_hash,v.legacy_payload,v.archive_status,v.claim_flags,e.legacy_id,e.seq
                        FROM event e JOIN event_version v USING(event_id)
                        WHERE e.event_id=? AND v.version=(SELECT MAX(version) FROM event_version WHERE event_id=e.event_id)""",
                     (event_id,)).fetchone()
    if not r:
        raise Rechazo("Caso no encontrado")
    return {"version": r[0], "status": r[1], "row_hash": r[2], "payload": json.loads(r[3]), "archive": r[4],
            "flags": json.loads(r[5]), "legacy_id": r[6], "seq": r[7]}


def id_de(conn, legacy_id):
    r = conn.execute("SELECT event_id FROM event WHERE legacy_id=?", (legacy_id,)).fetchone()
    if not r:
        raise Rechazo("Caso no encontrado")
    return r[0]


def creador(conn, event_id):
    r = conn.execute("SELECT usuario FROM event_action WHERE event_id=? AND accion='crear' ORDER BY id LIMIT 1", (event_id,)).fetchone()
    return r[0] if r else "sistema"


def editores(conn, event_id):
    return {r[0] for r in conn.execute("SELECT usuario FROM event_action WHERE event_id=? AND accion IN ('crear','editar')", (event_id,))}


def historial(conn, event_id):
    cols = ["ts", "usuario", "rol", "accion", "estado_de", "estado_a", "nota", "version"]
    return [dict(zip(cols, r)) for r in conn.execute(
        "SELECT ts,usuario,rol,accion,estado_de,estado_a,nota,version FROM event_action WHERE event_id=? ORDER BY id", (event_id,))]


def casos(conn):
    """Todos los casos (última versión), con estado v1 y creador; para la cola interna."""
    out = []
    for eid, lid, seq in conn.execute("SELECT event_id,legacy_id,seq FROM event ORDER BY seq"):
        u = _ultima(conn, eid)
        out.append({**u["payload"], "event_id": eid, "estado_v1": u["status"], "version": u["version"],
                    "creado_por": creador(conn, eid), "origen_app": "origen:app" in u["flags"]})
    return out


def siguiente_id(conn):
    n = max([int(r[0].split("-")[-1]) for r in conn.execute("SELECT legacy_id FROM event WHERE legacy_id LIKE 'CO-2026-%'")] or [0])
    return f"CO-2026-{n + 1:03d}"


def oficial(url: str) -> bool:
    h = (urlparse(url).hostname or "").lower()
    return h.endswith(".gov.co") or h.endswith(".mil.co")


def grupo_editorial(url: str) -> str:
    h = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return ".".join(h.split(".")[-3:]) if h.endswith((".gov.co", ".mil.co", ".com.co", ".org.co")) else ".".join(h.split(".")[-2:])


def _clave_dup(e):
    return f"{e['mpio']}|{e['mod']}|{e['fecha']}"


def _duplicados(conn, e, excluir_id=None):
    """Mismo municipio y modalidad con fecha ±1 día frente a otros casos vigentes (misma regla que la v0)."""
    out = []
    for eid, lid, in conn.execute("SELECT event_id,legacy_id FROM event"):
        if eid == excluir_id:
            continue
        u = _ultima(conn, eid)
        if u["status"] in ("DESCARTADO", "RETRACTADO"):
            continue
        x = u["payload"]
        try:
            if x["mpio"] == e["mpio"] and x["mod"] == e["mod"] and abs((dt.date.fromisoformat(x["fecha"]) - dt.date.fromisoformat(e["fecha"])).days) <= 1:
                out.append(lid)
        except Exception:
            pass
    return out


def evaluar_compuertas(conn, event_id, payload, exigir_archivo=False):
    dups = _duplicados(conn, payload, event_id)
    srcs = [gates.Source(doc_id=u, outlet_group_id=grupo_editorial(u), is_official=oficial(u), archived=False) for u in payload["fuentes"]]
    c = gates.Candidate(
        event_key=_clave_dup(payload), attribution_level=payload["atrib"],
        attribution_ref=payload["evidencia"] if payload["atrib"] in "ABCD" and payload["evidencia"].strip() else None,
        sources=srcs, texts=[payload[k] for k in ("tipo", "lugar", "evidencia", "h_nota", "danos", "desplaz", "servicios")],
        lat=payload["lat"], lon=payload["lon"],
        casualties={k: payload[k] for k in INT})
    duras, blandas = gates.evaluar(c, known_keys={_clave_dup(payload)} if dups else frozenset(), exigir_archivo=exigir_archivo)
    if re.search("infraestructura", payload["objetivo"], re.I) and not re.search("institucional", payload["objetivo"], re.I):
        blandas = blandas + ["infraestructura sensible: el lugar y la hora deben publicarse degradados (municipio y semana)"]
    return (duras, blandas), dups


# ---------- escritura ----------
def _accion(conn, eid, version, ts, usuario, rol, accion, de, a, nota):
    conn.execute("INSERT INTO event_action(event_id,version,ts,usuario,rol,accion,estado_de,estado_a,nota) VALUES (?,?,?,?,?,?,?,?,?)",
                 (eid, version, ts, usuario, rol, accion, de, a, nota))
    lid = conn.execute("SELECT legacy_id FROM event WHERE event_id=?", (eid,)).fetchone()[0]
    core.audit_append(conn, ts, rol, f"caso_{accion}", lid, {"usuario": usuario, "v": version, "de": de, "a": a, "nota": nota})


def _version(conn, eid, version, status, payload, prev_hash, flags, archive="legacy_unarchived"):
    row = core.map_event(payload)
    row.update(event_id=eid, version=version, status=status, claim_flags=core.canon(flags), archive_status=archive)
    fields = {k: row[k] for k in core.COLS}
    h = core.sha(core.canon(fields) + prev_hash)
    conn.execute(f"INSERT INTO event_version({','.join(core.COLS)},prev_hash,row_hash) VALUES ({','.join('?' * len(core.COLS))},?,?)",
                 [row[k] for k in core.COLS] + [prev_hash, h])
    return h


def crear_caso(conn, reg: dict, usuario: str, rol: str, ts: str):
    if rol not in ("editor", "admin"):
        raise Rechazo("Solo editores y administradores registran casos")
    e = {**DEFAULTS_COPIA(), **{k: v for k, v in reg.items() if k not in ("id", "actualizacion")}}
    if e.get("atrib") == "E":
        e["grupo"] = "No determinado"
    err = validar_registro(e, _fecha_de(ts))
    if err:
        raise Rechazo(err)
    e["id"] = siguiente_id(conn)
    e["actualizacion"] = _fecha_de(ts)
    dups = _duplicados(conn, e)
    if dups:
        raise Rechazo(f"Posible duplicado de {', '.join(dups)} (mismo municipio y modalidad, fecha ±1 día)")
    eid = _uuid7()
    seq = (conn.execute("SELECT COALESCE(MAX(seq),-1) FROM event").fetchone()[0]) + 1
    conn.execute("INSERT INTO event(event_id,legacy_id,seq) VALUES (?,?,?)", (eid, e["id"], seq))
    for pos, url in enumerate(e["fuentes"]):
        did = core.sha(url)
        conn.execute("INSERT OR IGNORE INTO source_document(doc_id,url,canonical_url) VALUES (?,?,?)", (did, url, url))
    _version(conn, eid, 1, "CANDIDATO", e, "", ["origen:app"])
    _vincular_fuentes(conn, eid, 1, e)
    _accion(conn, eid, 1, ts, usuario, rol, "crear", None, "CANDIDATO", None)
    conn.commit()
    return e["id"]


def DEFAULTS_COPIA():
    return dict(DEFECTOS)


def _vincular_fuentes(conn, eid, version, e):
    for pos, url in enumerate(e["fuentes"]):
        conn.execute("INSERT OR IGNORE INTO event_source VALUES (?,?,?,?,?)", (eid, version, core.sha(url), "supports", pos))


def editar_caso(conn, legacy_id, cambios: dict, usuario: str, rol: str, ts: str, nota: str = ""):
    if rol not in ("editor", "admin"):
        raise Rechazo("Solo editores y administradores editan casos")
    eid = id_de(conn, legacy_id)
    u = _ultima(conn, eid)
    if u["status"] in ("DESCARTADO", "RETRACTADO"):
        raise Rechazo(f"Un caso {u['status'].lower()} no se edita")
    prohibido = {"id", "actualizacion"} & set(cambios)
    if prohibido:
        raise Rechazo("Campos no editables: " + ", ".join(sorted(prohibido)))
    e = {**u["payload"], **cambios}
    if e.get("atrib") == "E":
        e["grupo"] = "No determinado"
    err = validar_registro(e, _fecha_de(ts))
    if err:
        raise Rechazo(err)
    if e == u["payload"]:
        raise Rechazo("No hay cambios")
    e["actualizacion"] = _fecha_de(ts)
    dups = _duplicados(conn, e, eid)
    if dups:
        raise Rechazo(f"Posible duplicado de {', '.join(dups)}")
    nuevo = "PRELIMINAR" if u["status"] == "VERIFICADO_EQUIPO" else u["status"]   # editar invalida la verificación previa
    v = u["version"] + 1
    for url in e["fuentes"]:
        conn.execute("INSERT OR IGNORE INTO source_document(doc_id,url,canonical_url) VALUES (?,?,?)", (core.sha(url), url, url))
    _version(conn, eid, v, nuevo, e, u["row_hash"], u["flags"], u["archive"])
    _vincular_fuentes(conn, eid, v, e)
    _accion(conn, eid, v, ts, usuario, rol, "editar", u["status"], nuevo, nota or ", ".join(sorted(cambios)))
    conn.commit()
    return v


TRANSICIONES = {
    ("CANDIDATO", "PRELIMINAR"): ("editor", "admin"),
    ("CANDIDATO", "DESCARTADO"): ("editor", "admin"),
    ("PRELIMINAR", "VERIFICADO_EQUIPO"): ("admin",),
    ("PRELIMINAR", "DESCARTADO"): ("admin",),
    ("PRELIMINAR", "RETRACTADO"): ("admin",),
    ("VERIFICADO_EQUIPO", "RETRACTADO"): ("admin",),
}


def transicionar(conn, legacy_id, a: str, usuario: str, rol: str, ts: str, motivo: str = ""):
    eid = id_de(conn, legacy_id)
    u = _ultima(conn, eid)
    de = u["status"]
    if a == "VERIFICADO_INDEPENDIENTE":
        raise Rechazo("VERIFICADO_INDEPENDIENTE está reservado al revisor independiente (R13); ese rol aún no está asignado")
    if (de, a) not in TRANSICIONES:
        raise Rechazo(f"Transición no permitida: {de} → {a}")
    if rol not in TRANSICIONES[(de, a)]:
        raise Rechazo(f"Su rol ({rol}) no puede pasar un caso de {de} a {a}")
    if a in ("DESCARTADO", "RETRACTADO") and len(motivo.strip()) < 10:
        raise Rechazo("Indique el motivo (al menos 10 caracteres)")
    if a == "VERIFICADO_EQUIPO" and usuario in editores(conn, eid) | {creador(conn, eid)}:
        raise Rechazo("Dos llaves: quien creó o editó el caso no puede verificarlo; debe hacerlo otra persona")
    if (de, a) == ("CANDIDATO", "PRELIMINAR"):
        (duras, blandas), dups = evaluar_compuertas(conn, eid, u["payload"])
        if duras:
            raise Rechazo(["No pasa las compuertas de publicación:"] + duras)
        if blandas and not (rol == "admin" and len(motivo.strip()) >= 10):
            raise Rechazo(["Requiere revisión humana:"] + blandas + ["Un administrador puede continuar indicando el motivo."])
    v = u["version"] + 1
    _version(conn, eid, v, a, u["payload"], u["row_hash"], u["flags"], u["archive"])
    _vincular_fuentes(conn, eid, v, u["payload"])
    _accion(conn, eid, v, ts, usuario, rol, "transicion", de, a, motivo.strip() or None)
    conn.commit()
    return v


# ---------- exportación y sincronización ----------
def exportar_publicable(conn) -> dict:
    """data.json (formato v0) solo con casos en estados publicables, en el orden original."""
    ev = []
    for eid, in conn.execute("SELECT event_id FROM event ORDER BY seq"):
        u = _ultima(conn, eid)
        if u["status"] in PUBLICABLES:
            ev.append(u["payload"])
    base = core.export_v0(conn)
    fechas = [e["actualizacion"] for e in ev] + [base["updated"]]
    return {"updated": max(fechas), "events": ev, "excluded": base["excluded"], "context": base["context"]}


def sincronizar(conn, data: dict, ts: str, usuario: str = "sistema"):
    """Lleva a la base lo que cambió en la v0 viva (nuevos eventos, ediciones, excluidos y contexto).
    No pisa casos creados en la aplicación: si la v0 usa un id que la aplicación ya tomó con otro contenido, se informa."""
    nuevos, editados, conflictos, ausentes = [], [], [], []
    vivos = {e["id"] for e in data["events"]}
    for e in data["events"]:
        r = conn.execute("SELECT event_id FROM event WHERE legacy_id=?", (e["id"],)).fetchone()
        if not r:
            row = core.map_event(e)
            seq = conn.execute("SELECT COALESCE(MAX(seq),-1) FROM event").fetchone()[0] + 1
            conn.execute("INSERT INTO event(event_id,legacy_id,seq) VALUES (?,?,?)", (row["event_id"], e["id"], seq))
            for url in e["fuentes"]:
                conn.execute("INSERT OR IGNORE INTO source_document(doc_id,url,canonical_url) VALUES (?,?,?)", (core.sha(url), url, url))
            _version(conn, row["event_id"], 1, "PRELIMINAR", e, "", [])
            _vincular_fuentes(conn, row["event_id"], 1, e)
            _accion(conn, row["event_id"], 1, ts, usuario, "sistema", "sincronizar", None, "PRELIMINAR", "nuevo desde la v0")
            nuevos.append(e["id"])
            continue
        eid = r[0]
        u = _ultima(conn, eid)
        if core.canon(u["payload"]) == core.canon(e):
            continue
        if "origen:app" in u["flags"]:
            conflictos.append(e["id"])
            continue
        v = u["version"] + 1
        for url in e["fuentes"]:
            conn.execute("INSERT OR IGNORE INTO source_document(doc_id,url,canonical_url) VALUES (?,?,?)", (core.sha(url), url, url))
        _version(conn, eid, v, u["status"], e, u["row_hash"], u["flags"], u["archive"])
        _vincular_fuentes(conn, eid, v, e)
        _accion(conn, eid, v, ts, usuario, "sistema", "sincronizar", u["status"], u["status"], "editado en la v0")
        editados.append(e["id"])
    for lid, flags in conn.execute("SELECT e.legacy_id,v.claim_flags FROM event e JOIN event_version v USING(event_id) "
                                   "WHERE v.version=(SELECT MAX(version) FROM event_version WHERE event_id=e.event_id)"):
        if lid not in vivos and "origen:app" not in json.loads(flags):
            ausentes.append(lid)
    conn.execute("DELETE FROM excluded_record"); conn.execute("DELETE FROM context_note")
    for i, r in enumerate(data["excluded"]):
        conn.execute("INSERT INTO excluded_record VALUES (?,?)", (i, core.canon(r)))
    for i, r in enumerate(data["context"]):
        conn.execute("INSERT INTO context_note VALUES (?,?)", (i, core.canon(r)))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('updated', ?)", (data["updated"],))
    core.audit_append(conn, ts, "sistema", "sincronizar_v0", "data.json",
                      {"nuevos": nuevos, "editados": editados, "conflictos": conflictos, "ausentes": ausentes, "corte": data["updated"]})
    conn.commit()
    return {"nuevos": nuevos, "editados": editados, "conflictos": conflictos, "ausentes": ausentes}
