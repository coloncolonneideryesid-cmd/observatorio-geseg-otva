"""Consultas de solo lectura sobre la base de eventos (núcleo `otva`). Nada aquí escribe."""
import json, sqlite3
from collections import Counter, defaultdict
from . import config as C

ATR = {"A": "Atribuida por autoridad competente con acto verificable", "B": "Autoridad sin acto público",
       "C": "Prensa citando fuente oficial", "D": "Prensa sin fuente identificable", "E": "Sin atribución"}


def _db():
    if not C.EVENTS_DB.exists():
        raise FileNotFoundError("Falta la carga inicial: python -m etl.cargar inicial")
    c = sqlite3.connect(f"file:{C.EVENTS_DB.as_posix()}?mode=ro", uri=True)
    return c


PUBLICABLES = ("PRELIMINAR", "VERIFICADO_EQUIPO", "VERIFICADO_INDEPENDIENTE")


def eventos(todos=False):
    """Última versión de cada evento, en el orden de la v0, con los campos de la v0 más el estado v1.
    Por defecto solo lo publicable (lo que ve cualquier usuario); `todos=True` incluye candidatos, descartados y retractados."""
    out = []
    with _db() as c:
        for payload, status, arch, v in c.execute(
                """SELECT v.legacy_payload,v.status,v.archive_status,v.version FROM event e JOIN event_version v USING(event_id)
                   WHERE v.version=(SELECT MAX(version) FROM event_version WHERE event_id=e.event_id) ORDER BY e.seq"""):
            if not todos and status not in PUBLICABLES:
                continue
            e = json.loads(payload)
            e.update(estado_v1=status, archivo=arch, version=v)
            out.append(e)
    return out


def meta():
    with _db() as c:
        upd = c.execute("SELECT value FROM meta WHERE key='updated'").fetchone()
        ex = c.execute("SELECT COUNT(*) FROM excluded_record").fetchone()[0]
        cx = c.execute("SELECT COUNT(*) FROM context_note").fetchone()[0]
    return {"corte": upd[0] if upd else None, "excluidos": ex, "contexto": cx}


def resumen():
    ev = eventos()
    n = len(ev)
    m = lambda e: e["m_civ"] + e["m_fp"]
    h = lambda e: e["h_civ"] + e["h_fp"]
    mes = Counter(e["fecha"][:7] for e in ev)
    return {
        **meta(), "total": n,
        "fallecidos": sum(map(m, ev)), "heridos": sum(map(h, ev)),
        "fuente_unica": sum(1 for e in ev if len(e["fuentes"]) == 1),
        "incompleto": sum(1 for e in ev if len(e["fuentes"]) == 1 or e["estado"] != "Confirmado"),
        "por_depto": sorted(Counter(e["depto"] for e in ev).items(), key=lambda x: (-x[1], x[0])),
        "por_atrib": [[k, Counter(e["atrib"] for e in ev).get(k, 0), ATR[k]] for k in "ABCDE"],
        "por_mes": sorted(mes.items()),
        "por_grupo": sorted(Counter(e["grupo"] for e in ev).items(), key=lambda x: -x[1]),
        "por_mod": sorted(Counter(e["mod"] for e in ev).items(), key=lambda x: -x[1]),
    }


def calidad():
    ev = eventos(todos=True)
    with _db() as c:
        docs = c.execute("SELECT COUNT(*), SUM(sha256 IS NOT NULL) FROM source_document").fetchone()
        audit = c.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    dom = defaultdict(int)
    for e in ev:
        for u in e["fuentes"]:
            dom[u.split("/")[2].replace("www.", "")] += 1
    return {"eventos": len(ev), "documentos": docs[0], "documentos_archivados": docs[1] or 0,
            "sin_archivar": sum(1 for e in ev if e["archivo"] != "archived"),
            "estados": dict(Counter(e["estado_v1"] for e in ev)), "estado_v0": dict(Counter(e["estado"] for e in ev)),
            "por_n_fuentes": dict(Counter(len(e["fuentes"]) for e in ev)),
            "dominios": sorted(dom.items(), key=lambda x: -x[1]), "registros_bitacora": audit}
