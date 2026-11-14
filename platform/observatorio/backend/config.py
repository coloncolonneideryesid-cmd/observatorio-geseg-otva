"""Rutas y parámetros. OTVA_DATA_DIR permite apuntar a otra carpeta de datos (las pruebas la usan)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORM = ROOT.parent                      # contiene el paquete `otva` (núcleo de datos)
DATA = Path(os.environ.get("OTVA_DATA_DIR", ROOT / "data"))
DB_DIR = DATA / "db"
EVENTS_DB = DB_DIR / "otva.db"              # eventos, historia inmutable, bitácora de datos
USERS_DB = DB_DIR / "usuarios.db"           # usuarios, intentos y bitácora de acceso
SECRET = DB_DIR / "secret.key"
CREDENCIALES = DB_DIR / "CREDENCIALES_INICIALES.txt"
STATIC = ROOT / "backend" / "static"
VIVO = PLATFORM.parent / "data" / "data.json"      # v0 viva (OTVA 01)
EXPORT = DATA / "export"                             # data.json publicable generado desde la base

TOKEN_HORAS = 8
MAX_FALLOS_USUARIO_IP = 5
MAX_FALLOS_IP = 20
VENTANA_MIN = 15
CLAVE_MIN = 10
ROLES = ("lector", "editor", "admin")
