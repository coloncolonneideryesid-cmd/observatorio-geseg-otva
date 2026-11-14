"""Prueba de la API en una carpeta de datos temporal (no toca data/). Uso: python tests/prueba_integral.py"""
import os, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = tempfile.mkdtemp()
os.environ["OTVA_DATA_DIR"] = TMP
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parent))

from etl import cargar                      # noqa: E402
from backend import config as C             # noqa: E402

cargar.inicial(cargar.SNAP, False, "prueba")
from fastapi.testclient import TestClient   # noqa: E402
from backend.main import app                # noqa: E402

cli = TestClient(app)


def clave_inicial():
    return C.CREDENCIALES.read_text(encoding="utf-8").split("Clave inicial: ")[1].split("\n")[0]


def auth(t): return {"Authorization": f"Bearer {t}"}


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = cli.post("/api/login", json={"usuario": "admin", "clave": clave_inicial()})
        assert r.status_code == 200 and r.json()["cambiar_clave"] is True
        cls.t0 = r.json()["token"]
        r = cli.post("/api/clave", json={"nueva": "Clave-de-prueba-2026"}, headers=auth(cls.t0))
        assert r.status_code == 200
        cls.t = r.json()["token"]

    def test_sin_token_401(self):
        for u in ("/api/resumen", "/api/eventos", "/api/calidad", "/api/usuarios", "/api/bitacora"):
            self.assertEqual(cli.get(u).status_code, 401, u)

    def test_token_falso_o_alterado(self):
        self.assertEqual(cli.get("/api/resumen", headers=auth("x.y")).status_code, 401)
        self.assertEqual(cli.get("/api/resumen", headers=auth(self.t[:-3] + "abc")).status_code, 401)

    def test_clave_inicial_bloquea_datos_hasta_cambiarla(self):
        self.assertEqual(cli.get("/api/resumen", headers=auth(self.t0)).status_code, 403)

    def test_credenciales_iniciales_se_borran(self):
        self.assertFalse(C.CREDENCIALES.exists())

    def test_resumen_coincide_con_la_v0(self):
        r = cli.get("/api/resumen", headers=auth(self.t)).json()
        self.assertEqual((r["total"], r["excluidos"], r["contexto"], r["corte"]), (42, 25, 3, "2026-11-08"))
        self.assertEqual({k: n for k, n, _ in r["por_atrib"]}, {"A": 0, "B": 16, "C": 0, "D": 6, "E": 20})
        self.assertEqual(r["fuente_unica"], 10)

    def test_eventos_y_calidad(self):
        ev = cli.get("/api/eventos", headers=auth(self.t)).json()
        orig = [e for e in ev if e["id"] <= "CO-2026-042"]   # los 42 de la v0; otras pruebas de la clase pueden crear casos
        self.assertEqual(len(orig), 42); self.assertTrue(all(e["estado_v1"] == "PRELIMINAR" for e in orig))
        q = cli.get("/api/calidad", headers=auth(self.t)).json()
        self.assertEqual(q["sin_archivar"], q["eventos"]); self.assertGreaterEqual(q["eventos"], 42); self.assertEqual(q["documentos_archivados"], 0)

    def test_cabeceras_y_sin_documentacion(self):
        r = cli.get("/api/docs"); self.assertIn(r.status_code, (401, 404))
        self.assertIn("text/html", cli.get("/openapi.json").headers["content-type"])  # no hay esquema de API público
        h = cli.post("/api/login", json={"usuario": "x", "clave": "y"}).headers
        self.assertIn("default-src 'self'", h["content-security-policy"]); self.assertEqual(h["x-frame-options"], "DENY")

    def test_clave_corta_rechazada(self):
        self.assertEqual(cli.post("/api/clave", json={"nueva": "corta"}, headers=auth(self.t)).status_code, 422)

    def test_lector_no_accede_a_administracion(self):
        r = cli.post("/api/usuarios", json={"nombre": "lector1", "rol": "lector", "clave": "Lectura-2026-ok"}, headers=auth(self.t))
        self.assertEqual(r.status_code, 200)
        t = cli.post("/api/login", json={"usuario": "lector1", "clave": "Lectura-2026-ok"}).json()
        tl = cli.post("/api/clave", json={"nueva": "Lectura-2026-nueva"}, headers=auth(t["token"])).json()["token"]
        self.assertEqual(cli.get("/api/resumen", headers=auth(tl)).status_code, 200)
        for u in ("/api/usuarios", "/api/bitacora"):
            self.assertEqual(cli.get(u, headers=auth(tl)).status_code, 403, u)

    def test_limite_de_intentos_fallidos(self):
        for _ in range(5):
            self.assertEqual(cli.post("/api/login", json={"usuario": "fantasma", "clave": "mal"}).status_code, 401)
        self.assertEqual(cli.post("/api/login", json={"usuario": "fantasma", "clave": "mal"}).status_code, 429)

    def _usuario(self, nombre, rol):
        cli.post("/api/usuarios", json={"nombre": nombre, "rol": rol, "clave": f"{nombre}-clave-2026"}, headers=auth(self.t))
        t = cli.post("/api/login", json={"usuario": nombre, "clave": f"{nombre}-clave-2026"}).json()["token"]
        return cli.post("/api/clave", json={"nueva": f"{nombre}-nueva-2026"}, headers=auth(t)).json()["token"]

    def test_ciclo_de_casos_por_la_api(self):
        ana, luis = self._usuario("ana", "editor"), self._usuario("luis", "lector")
        caso = dict(fecha="2026-11-12", hora="Noche", depto="Cauca", mpio="Argelia", lugar="Casco urbano", lat=2.2, lon=-77.1,
                    tipo="Ataque con dron contra la estación", mod="Dron con explosivos", objetivo="Fuerza Pública", atrib="E",
                    fuentes=["https://www.policia.gov.co/noticia/prueba"])
        self.assertEqual(cli.post("/api/casos", json=caso, headers=auth(luis)).status_code, 403)       # lector no registra
        r = cli.post("/api/casos", json=caso, headers=auth(ana)); self.assertEqual(r.status_code, 200, r.text)
        cid = r.json()["id"]
        # candidato: no es público
        self.assertNotIn(cid, [e["id"] for e in cli.get("/api/eventos", headers=auth(luis)).json()])
        self.assertEqual(cli.get("/api/casos", headers=auth(luis)).status_code, 403)
        # el editor lo pasa a preliminar (fuente oficial) y ya es público
        r = cli.post(f"/api/casos/{cid}/transicion", json={"a": "PRELIMINAR"}, headers=auth(ana)); self.assertEqual(r.status_code, 200, r.text)
        self.assertIn(cid, [e["id"] for e in cli.get("/api/eventos", headers=auth(luis)).json()])
        # el editor no verifica ni retracta; el admin sí, pero no el que lo creó (ana no es admin; admin distinto)
        for a in ("VERIFICADO_EQUIPO", "RETRACTADO"):
            self.assertEqual(cli.post(f"/api/casos/{cid}/transicion", json={"a": a, "motivo": "motivo suficientemente largo"}, headers=auth(ana)).status_code, 422)
        r = cli.post(f"/api/casos/{cid}/transicion", json={"a": "VERIFICADO_INDEPENDIENTE"}, headers=auth(self.t))
        self.assertEqual(r.status_code, 422); self.assertIn("R13", " ".join(r.json()["detail"]))
        self.assertEqual(cli.post(f"/api/casos/{cid}/transicion", json={"a": "VERIFICADO_EQUIPO"}, headers=auth(self.t)).status_code, 200)
        h = cli.get(f"/api/casos/{cid}/historial", headers=auth(self.t)).json()
        self.assertEqual([x["accion"] for x in h], ["crear", "transicion", "transicion"])
        # la exportación solo lleva lo publicable y pasa la validación; el lector no puede exportar
        self.assertEqual(cli.post("/api/exportar", headers=auth(ana)).status_code, 403)
        ex = cli.post("/api/exportar", headers=auth(self.t)); self.assertEqual(ex.status_code, 200, ex.text)
        self.assertEqual(ex.json()["eventos"], 43)
        # retractar lo saca de lo público
        self.assertEqual(cli.post(f"/api/casos/{cid}/transicion", json={"a": "RETRACTADO", "motivo": "La fuente corrigió la información"}, headers=auth(self.t)).status_code, 200)
        self.assertNotIn(cid, [e["id"] for e in cli.get("/api/eventos", headers=auth(luis)).json()])

    def test_rechazos_se_explican(self):
        r = cli.post("/api/casos", json={"fecha": "2026-11-12"}, headers=auth(self.t))
        self.assertEqual(r.status_code, 422); self.assertIsInstance(r.json()["detail"], list)

    def test_la_interfaz_se_sirve(self):
        r = cli.get("/")
        self.assertIn(r.status_code, (200, 503))


if __name__ == "__main__":
    unittest.main(verbosity=2)
