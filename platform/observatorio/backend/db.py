"""Usuarios, claves (PBKDF2), tokens firmados, límite de intentos y bitácora de acceso."""
import base64, hashlib, hmac, json, os, secrets, sqlite3, time
from . import config as C

ITER = 200_000


def _conn():
    C.DB_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(C.USERS_DB)
    c.row_factory = sqlite3.Row
    c.executescript("""
      CREATE TABLE IF NOT EXISTS usuario(nombre TEXT PRIMARY KEY, rol TEXT NOT NULL, sal TEXT NOT NULL, hash TEXT NOT NULL,
                                         cambiar_clave INTEGER NOT NULL DEFAULT 1, creado TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS intento(ts REAL NOT NULL, usuario TEXT NOT NULL, ip TEXT NOT NULL, ok INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS acceso(ts TEXT NOT NULL, usuario TEXT NOT NULL, accion TEXT NOT NULL, detalle TEXT);""")
    return c


def _hash(clave: str, sal: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, ITER).hex()


def secreto() -> bytes:
    C.DB_DIR.mkdir(parents=True, exist_ok=True)
    if not C.SECRET.exists():
        C.SECRET.write_bytes(secrets.token_bytes(32))
    return C.SECRET.read_bytes()


def registrar(usuario, accion, detalle=""):
    with _conn() as c:
        c.execute("INSERT INTO acceso VALUES (?,?,?,?)", (time.strftime("%Y-%m-%dT%H:%M:%S"), usuario, accion, detalle))


def asegurar_admin():
    """Primer arranque: crea `admin` con clave aleatoria y la deja en CREDENCIALES_INICIALES.txt."""
    with _conn() as c:
        if c.execute("SELECT 1 FROM usuario LIMIT 1").fetchone():
            return
        clave = secrets.token_urlsafe(12)
        sal = os.urandom(16)
        c.execute("INSERT INTO usuario VALUES (?,?,?,?,1,?)", ("admin", "admin", sal.hex(), _hash(clave, sal), time.strftime("%Y-%m-%d")))
    C.CREDENCIALES.write_text(f"Usuario: admin\nClave inicial: {clave}\nSe le pedirá cambiarla al ingresar; luego borre este archivo.\n", encoding="utf-8")


def crear_usuario(nombre, rol, clave):
    if rol not in C.ROLES or len(clave) < C.CLAVE_MIN:
        raise ValueError("rol o clave inválidos")
    sal = os.urandom(16)
    with _conn() as c:
        c.execute("INSERT INTO usuario VALUES (?,?,?,?,1,?)", (nombre, rol, sal.hex(), _hash(clave, sal), time.strftime("%Y-%m-%d")))


def bloqueado(usuario, ip):
    desde = time.time() - C.VENTANA_MIN * 60
    with _conn() as c:
        ui = c.execute("SELECT COUNT(*) FROM intento WHERE ts>? AND ok=0 AND usuario=? AND ip=?", (desde, usuario, ip)).fetchone()[0]
        i = c.execute("SELECT COUNT(*) FROM intento WHERE ts>? AND ok=0 AND ip=?", (desde, ip)).fetchone()[0]
    return ui >= C.MAX_FALLOS_USUARIO_IP or i >= C.MAX_FALLOS_IP


def verificar(usuario, clave, ip):
    """Devuelve (fila_usuario|None, motivo). Cuenta intentos fallidos."""
    if bloqueado(usuario, ip):
        return None, "bloqueado"
    with _conn() as c:
        u = c.execute("SELECT * FROM usuario WHERE nombre=?", (usuario,)).fetchone()
        ok = bool(u) and hmac.compare_digest(_hash(clave, bytes.fromhex(u["sal"])), u["hash"])
        c.execute("INSERT INTO intento VALUES (?,?,?,?)", (time.time(), usuario, ip, int(ok)))
    registrar(usuario, "ingreso_ok" if ok else "ingreso_fallido", ip)
    return (u if ok else None), ("ok" if ok else "credenciales")


def cambiar_clave(usuario, nueva):
    if len(nueva) < C.CLAVE_MIN:
        raise ValueError(f"La clave debe tener al menos {C.CLAVE_MIN} caracteres")
    sal = os.urandom(16)
    with _conn() as c:
        c.execute("UPDATE usuario SET sal=?, hash=?, cambiar_clave=0 WHERE nombre=?", (sal.hex(), _hash(nueva, sal), usuario))
    registrar(usuario, "cambio_clave")
    if C.CREDENCIALES.exists():
        C.CREDENCIALES.unlink()


def emitir(usuario, rol, cambiar):
    p = base64.urlsafe_b64encode(json.dumps({"u": usuario, "r": rol, "c": int(cambiar), "e": int(time.time() + C.TOKEN_HORAS * 3600)}).encode()).decode()
    return p + "." + hmac.new(secreto(), p.encode(), hashlib.sha256).hexdigest()


def leer(token):
    try:
        p, firma = token.rsplit(".", 1)
        if not hmac.compare_digest(firma, hmac.new(secreto(), p.encode(), hashlib.sha256).hexdigest()):
            return None
        d = json.loads(base64.urlsafe_b64decode(p))
        return d if d["e"] > time.time() else None
    except Exception:
        return None


def usuarios():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT nombre,rol,cambiar_clave,creado FROM usuario ORDER BY nombre")]


def bitacora(n=100):
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM acceso ORDER BY rowid DESC LIMIT ?", (n,))]
