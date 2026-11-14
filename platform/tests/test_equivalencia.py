import hashlib, json, sqlite3, sys, unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from otva import core  # noqa: E402

SNAP = ROOT / "fixtures" / "v0_snapshot_78d8e27.json"
SNAP_SHA = "c8d53f5113c930133c774ef6c007fc04c2e8bcf29f57b7c50ba94c933c1a3db0"
TS = "2026-11-09T00:00:00Z"


def load():
    raw = SNAP.read_bytes()
    return raw, json.loads(raw.decode("utf-8"))


def fresh():
    _, data = load()
    conn = core.connect()
    core.import_v0(conn, data, TS)
    return conn, data


class Equivalencia(unittest.TestCase):
    def test_instantanea_congelada(self):
        raw, data = load()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SNAP_SHA)
        self.assertEqual((len(data["events"]), len(data["excluded"]), len(data["context"])), (42, 25, 3))

    def test_ida_y_vuelta_identica(self):
        conn, data = fresh()
        self.assertEqual(core.export_v0(conn), core._nfc(data))

    def test_v0_ya_estaba_en_nfc(self):
        _, data = load()
        self.assertEqual(core._nfc(data), data, "la v0 tiene textos no NFC; documentar la diferencia")

    def test_columnas_coinciden_con_el_registro_original(self):
        conn, data = fresh()
        by = {e["id"]: e for e in data["events"]}
        rows = conn.execute("""SELECT legacy_id,depto,mpio,attribution_level,casualties_civil_killed,casualties_public_force_killed,
            casualties_civil_injured,casualties_public_force_injured,t_start,status,actor_name FROM event e
            JOIN event_version v USING(event_id)""").fetchall()
        self.assertEqual(len(rows), 42)
        for lid, d, m, a, mc, mf, hc, hf, t, st, actor in rows:
            e = by[lid]
            self.assertEqual((d, m, a, mc, mf, hc, hf, t, st),
                             (e["depto"], e["mpio"], e["atrib"], e["m_civ"], e["m_fp"], e["h_civ"], e["h_fp"], e["fecha"], "PRELIMINAR"))
            self.assertEqual(actor, None if e["grupo"] == "No determinado" else e["grupo"])

    def test_totales_del_tablero(self):
        conn, data = fresh()
        ev = data["events"]
        q = lambda s: conn.execute(s).fetchone()[0]
        self.assertEqual(q("SELECT SUM(casualties_civil_killed) FROM event_version"), sum(e["m_civ"] for e in ev))
        self.assertEqual(q("SELECT SUM(casualties_public_force_killed) FROM event_version"), sum(e["m_fp"] for e in ev))
        self.assertEqual(dict(conn.execute("SELECT attribution_level,COUNT(*) FROM event_version GROUP BY 1")),
                         dict(Counter(e["atrib"] for e in ev)))
        self.assertEqual(dict(conn.execute("SELECT depto,COUNT(*) FROM event_version GROUP BY 1")),
                         dict(Counter(e["depto"] for e in ev)))

    def test_regla_de_atribucion(self):
        """Sin autoridad que atribuya (E) no hay actor atribuido; A-D deben tener base."""
        conn, _ = fresh()
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM event_version WHERE attribution_level='E' AND actor_name IS NOT NULL").fetchone()[0], 0)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM event_version WHERE attribution_level IN ('A','B','C','D') AND (attribution_basis IS NULL OR attribution_basis='')").fetchone()[0], 0)

    def test_toda_fuente_enlazada(self):
        conn, data = fresh()
        n = sum(len(e["fuentes"]) for e in data["events"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM event_source").fetchone()[0], n)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM event e WHERE NOT EXISTS (SELECT 1 FROM event_source s WHERE s.event_id=e.event_id)").fetchone()[0], 0)

    def test_historicos_marcados_sin_archivo(self):
        conn, _ = fresh()
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM event_version WHERE archive_status<>'legacy_unarchived'").fetchone()[0], 0)


class Reproducibilidad(unittest.TestCase):
    def test_mismo_input_mismos_hashes(self):
        a, _ = fresh(); b, _ = fresh()
        q = "SELECT event_id,version,row_hash FROM event_version ORDER BY event_id"
        self.assertEqual(a.execute(q).fetchall(), b.execute(q).fetchall())
        self.assertEqual(a.execute("SELECT row_hash FROM audit_log").fetchall(), b.execute("SELECT row_hash FROM audit_log").fetchall())

    def test_importacion_estricta_con_valor_desconocido(self):
        _, data = load()
        data["events"][0]["estado"] = "Verificado"
        with self.assertRaises(ValueError):
            core.import_v0(core.connect(), data, TS)


class Integridad(unittest.TestCase):
    def test_cadenas_integras(self):
        conn, _ = fresh()
        self.assertIsNone(core.verify_event_chain(conn))
        self.assertIsNone(core.audit_verify(conn))

    def test_historia_y_bitacora_son_de_solo_adicion(self):
        conn, _ = fresh()
        for sql in ("UPDATE event_version SET status='VERIFICADO_INDEPENDIENTE'", "DELETE FROM event_version",
                    "UPDATE audit_log SET role='x'", "DELETE FROM audit_log"):
            with self.assertRaises(sqlite3.DatabaseError, msg=sql):
                conn.execute(sql)

    def test_manipulacion_privilegiada_se_detecta(self):
        conn, _ = fresh()
        conn.execute("DROP TRIGGER event_version_no_update")
        conn.execute("UPDATE event_version SET casualties_civil_killed=99 WHERE rowid=1")
        self.assertIsNotNone(core.verify_event_chain(conn))
        conn.execute("DROP TRIGGER audit_log_no_update")
        conn.execute("UPDATE audit_log SET action='otra' WHERE id=1")
        self.assertEqual(core.audit_verify(conn), 1)

    def test_no_se_pueden_asignar_estados_invalidos_ni_negativos(self):
        conn, _ = fresh()
        conn.execute("DROP TRIGGER event_version_no_update")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE event_version SET status='VERIFICADO'")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE event_version SET casualties_civil_killed=-1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
