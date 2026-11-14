"""Equivalencia del tablero: los constructores vigentes (build_html/build_xlsx) sobre la salida de la base deben dar el
mismo HTML (byte a byte) y el mismo Excel (salvo la hora de creación) que sobre la instantánea congelada.
Trabaja en copias temporales: nunca toca dist/."""
import json, os, shutil, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path

PLATFORM = Path(__file__).resolve().parent.parent
ROOT = PLATFORM.parent
sys.path.insert(0, str(PLATFORM)); sys.path.insert(0, str(PLATFORM / "preview"))
from otva import core  # noqa: E402
import build_preview as bp  # noqa: E402

SNAP = PLATFORM / "fixtures" / "v0_snapshot_78d8e27.json"
XLSX = "Observatorio_Violencia_Armada_Colombia_2026.xlsx"


def stage(tmp: Path, data_text: str) -> Path:
    for d in ("src", "assets", "briefing"):
        if (ROOT / d).exists():
            shutil.copytree(ROOT / d, tmp / d)
    (tmp / "data").mkdir()
    shutil.copy(ROOT / "data" / "geo.json", tmp / "data" / "geo.json")
    (tmp / "data" / "data.json").write_text(data_text, encoding="utf-8")
    env = dict(os.environ, PYTHONUTF8="1")
    for script in ("build_html.py", "build_xlsx.py"):
        r = subprocess.run([sys.executable, str(tmp / "src" / script)], cwd=tmp, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-800:]
    return tmp / "dist"


class Tablero(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        snap_text = SNAP.read_text(encoding="utf-8")
        conn = core.connect(); core.import_v0(conn, json.loads(snap_text), "2026-11-09T00:00:00Z")
        exported = json.dumps(core.export_v0(conn), ensure_ascii=False, indent=1)
        cls.a = stage(cls.tmp / "A", snap_text)
        cls.b = stage(cls.tmp / "B", exported)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_html_identico_byte_a_byte(self):
        self.assertEqual((self.a / "observatorio.html").read_bytes(), (self.b / "observatorio.html").read_bytes())

    def test_excel_identico_salvo_marca_de_tiempo(self):
        za, zb = zipfile.ZipFile(self.a / XLSX), zipfile.ZipFile(self.b / XLSX)
        self.assertEqual(sorted(za.namelist()), sorted(zb.namelist()))
        self.assertEqual([n for n in za.namelist() if za.read(n) != zb.read(n)], ["docProps/core.xml"])

    def test_vista_previa_solo_agrega_lo_decidido(self):
        base = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
        new = bp.apply_changes(base)
        restored = new.replace(bp.BANNER, "").replace(bp.ROW_NEW, bp.ROW_OLD)
        self.assertEqual(restored, base)
        self.assertIn("Preliminar, sin revisión independiente", new)
        self.assertIn("Versiones distintas", new)

    def test_vista_previa_no_usa_palabras_prohibidas(self):
        new = bp.apply_changes((ROOT / "src" / "template.html").read_text(encoding="utf-8"))
        added = bp.BANNER + bp.ROW_NEW
        for w in ("validado", "verificado", "inteligencia", "OSINT"):
            self.assertNotIn(w, added.replace("sin revisión independiente", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
