# -*- coding: utf-8 -*-
"""Pruebas del verificador de fuentes OTVA (sin red). Ejecutar:
    python3 -m unittest discover -s pruebas -v
"""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
import verificador_fuentes as vf  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for f in os.listdir(RAIZ):
            if f.endswith(".json"):
                shutil.copy(os.path.join(RAIZ, f), self.tmp)
        self._base = vf.BASE
        vf.BASE = self.tmp
        vf._cache.clear()

    def tearDown(self):
        vf.BASE = self._base
        vf._cache.clear()
        shutil.rmtree(self.tmp)

    def editar(self, archivo, fn):
        p = os.path.join(self.tmp, archivo)
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        fn(d)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
        vf._cache.clear()

    def codigos(self):
        h = vf.Hallazgos()
        vf.validar(h)
        return {i["codigo"] for i in h.items if i["nivel"] == "error"}


class TestValidacion(Base):
    def test_repositorio_real_sin_errores(self):
        self.assertEqual(self.codigos(), set())

    def test_id_duplicado(self):
        def f(d):
            d["fuentes"].append(copy.deepcopy(d["fuentes"][0]))
        self.editar("fuentes_medios_nacionales.json", f)
        self.assertIn("ID_DUPLICADO", self.codigos())

    def test_campo_faltante(self):
        self.editar("fuentes_medios_nacionales.json", lambda d: d["fuentes"][0].pop("url_rss"))
        self.assertIn("CAMPOS_FALTANTES", self.codigos())

    def test_prefijo_incorrecto(self):
        def f(d):
            d["fuentes"][0]["id_fuente"] = "OTVA-INS-999"
        self.editar("fuentes_medios_nacionales.json", f)
        self.assertIn("PREFIJO_ID", self.codigos())

    def test_activa_sin_fecha_verificacion(self):
        def f(d):
            d["fuentes"][0].update(estado="activa", fecha_verificacion=None)
        self.editar("fuentes_redes_sociales.json", f)
        c = self.codigos()
        self.assertIn("ACTIVA_SIN_FECHA_VERIFICACION", c)
        self.assertIn("CUENTA_ACTIVA_SIN_VERIFICAR", c)

    def test_relacion_rota(self):
        self.editar("fuentes_redes_sociales.json",
                    lambda d: d["fuentes"][0].update(fuente_relacionada="OTVA-INS-998"))
        self.assertIn("RELACION_ROTA", self.codigos())

    def test_departamento_no_normalizado(self):
        self.editar("fuentes_medios_regionales.json",
                    lambda d: d["fuentes"][0].update(departamento="Antioqia"))
        self.assertIn("DEPARTAMENTO_NO_NORMALIZADO", self.codigos())

    def test_tema_fuera_de_taxonomia(self):
        self.editar("fuentes_medios_regionales.json",
                    lambda d: d["fuentes"][0].update(temas_monitoreados=["tema_inventado"]))
        self.assertIn("TEMA_NO_TAXONOMIA", self.codigos())

    def test_maestro_desincronizado(self):
        self.editar("fuentes_maestras.json", lambda d: d["fuentes"].pop())
        self.assertIn("MAESTRO_DESINCRONIZADO", self.codigos())

    def test_cadena_vacia_genera_aviso(self):
        self.editar("fuentes_medios_regionales.json", lambda d: d["fuentes"][0].update(observaciones=""))
        h = vf.Hallazgos()
        vf.validar(h)
        self.assertIn("VACIO_EN_LUGAR_DE_NULL", {i["codigo"] for i in h.items})


class TestUtilidades(unittest.TestCase):
    def test_normalizar_url(self):
        self.assertEqual(vf.normalizar_url("https://www.eltiempo.com/colombia/?utm_source=x"),
                         vf.normalizar_url("http://eltiempo.com/colombia"))

    def test_normalizar_texto(self):
        self.assertEqual(vf.normalizar_texto("Nariño, Bolívar"), "narino bolivar")

    def test_reto_antibots_no_es_ok(self):
        r = {"url": "https://www.minhacienda.gov.co", "codigo_http": 200,
             "url_final": "https://validate.perfdrive.com/abc"}
        self.assertEqual(vf.clasificar(r), "bloqueado_o_restringido")
        r = {"url": "https://a.gov.co", "codigo_http": 200, "url_final": "https://a.gov.co/",
             "_muestra": "<title>Just a moment...</title>"}
        self.assertEqual(vf.clasificar(r), "bloqueado_o_restringido")

    def test_redireccion_otro_dominio(self):
        r = {"url": "https://noticias.caracoltv.com", "codigo_http": 200,
             "url_final": "https://www.noticiascaracol.com/"}
        self.assertEqual(vf.clasificar(r), "redireccion_otro_dominio")

    def test_www_no_es_otro_dominio(self):
        r = {"url": "https://www.teleislas.com.co", "codigo_http": 200, "url_final": "https://teleislas.com.co/"}
        self.assertEqual(vf.clasificar(r), "ok")

    def test_codigos(self):
        self.assertEqual(vf.clasificar({"url": "u", "codigo_http": 404}), "enlace_roto")
        self.assertEqual(vf.clasificar({"url": "u", "codigo_http": 403}), "bloqueado_o_restringido")
        self.assertEqual(vf.clasificar({"url": "u", "codigo_http": 503}), "error_servidor")
        self.assertEqual(vf.clasificar({"url": "u", "codigo_http": None}), "sin_respuesta")

    def test_feed(self):
        self.assertTrue(vf.es_feed_valido('<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'))
        self.assertTrue(vf.es_feed_valido('<?xml version="1.0"?>\n<feed xmlns="http://www.w3.org/2005/Atom"><entry>'))
        self.assertFalse(vf.es_feed_valido("<!DOCTYPE html><html><head></head></html>"))


class TestEstados(Base):
    def _res(self, idf, clas, fecha):
        return [{"id_fuente": idf, "campo": "url_principal", "fecha": fecha, "codigo_http": None,
                 "url_final": None, "clasificacion": clas, "error": "x", "tiempo_ms": 1}]

    def test_inactiva_requiere_periodo_minimo(self):
        p = vf.cargar(vf.PARAMETROS)
        idf = "OTVA-MNA-002"
        for hora in ("2026-11-13T10:00:00+00:00", "2026-11-13T11:00:00+00:00", "2026-11-13T12:00:00+00:00"):
            vf.aplicar_resultados(self._res(idf, "sin_respuesta", hora), p)
        s = [x for x in vf.cargar("fuentes_medios_nacionales.json")["fuentes"] if x["id_fuente"] == idf][0]
        self.assertNotEqual(s["estado"], "inactiva")  # 3 fallos en 2 h: aun no
        vf.aplicar_resultados(self._res(idf, "sin_respuesta", "2026-11-17T12:00:00+00:00"), p)
        s = [x for x in vf.cargar("fuentes_medios_nacionales.json")["fuentes"] if x["id_fuente"] == idf][0]
        self.assertEqual(s["estado"], "inactiva")

    def test_bloqueo_no_activa_ni_inactiva(self):
        p = vf.cargar(vf.PARAMETROS)
        idf = "OTVA-INS-024"
        vf.aplicar_resultados(self._res(idf, "bloqueado_o_restringido", "2026-11-13T10:00:00+00:00"), p)
        s = [x for x in vf.cargar("fuentes_institucionales.json")["fuentes"] if x["id_fuente"] == idf][0]
        self.assertEqual(s["estado"], "pendiente_verificacion")


if __name__ == "__main__":
    unittest.main()
