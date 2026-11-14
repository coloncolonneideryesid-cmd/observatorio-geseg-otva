"""API del Observatorio OTVA (plano interno). FastAPI; sin documentación pública; cabeceras de seguridad."""
import hashlib, json, sys, time
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config as C, db, almacen

sys.path.insert(0, str(C.PLATFORM))   # paquete `otva` (núcleo)
from otva import core, ciclo          # noqa: E402

app = FastAPI(title="Observatorio OTVA", docs_url=None, redoc_url=None, openapi_url=None)
db.asegurar_admin()
if C.EVENTS_DB.exists():              # aplica migraciones pendientes del esquema de eventos
    core.connect(str(C.EVENTS_DB)).close()

CSP = ("default-src 'self'; img-src 'self' data: https://tile.openstreetmap.org https://*.tile.openstreetmap.org; "
       "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; font-src 'self' data:; "
       "frame-ancestors 'none'; base-uri 'self'; form-action 'self'")


@app.middleware("http")
async def cabeceras(request: Request, call_next):
    r = await call_next(request)
    r.headers.update({"Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                      "Referrer-Policy": "strict-origin-when-cross-origin", "Cache-Control": "no-store",
                      "Permissions-Policy": "geolocation=(), camera=(), microphone=()"})
    return r


def sesion(request: Request, permitir_cambio=False):
    h = request.headers.get("authorization", "")
    d = db.leer(h[7:]) if h.startswith("Bearer ") else None
    if not d:
        raise HTTPException(401, "Sesión no válida o vencida")
    if d["c"] and not permitir_cambio:
        raise HTTPException(403, "Debe cambiar su clave inicial antes de continuar")
    return d


def admin(d=Depends(sesion)):
    if d["r"] != "admin":
        raise HTTPException(403, "Solo administradores")
    return d


def editor(d=Depends(sesion)):
    if d["r"] not in ("editor", "admin"):
        raise HTTPException(403, "Solo editores y administradores")
    return d


def ahora():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def escribir(fn):
    """Abre la base en modo escritura, ejecuta fn(conn) y traduce los rechazos del ciclo a 422."""
    conn = core.connect(str(C.EVENTS_DB))
    try:
        return fn(conn)
    except ciclo.Rechazo as e:
        raise HTTPException(422, e.motivos)
    finally:
        conn.close()


class Login(BaseModel):
    usuario: str = Field(max_length=60)
    clave: str = Field(max_length=200)


class Clave(BaseModel):
    nueva: str = Field(max_length=200)


class NuevoUsuario(BaseModel):
    nombre: str = Field(min_length=3, max_length=60)
    rol: str
    clave: str = Field(max_length=200)


@app.post("/api/login")
def login(b: Login, request: Request):
    u, motivo = db.verificar(b.usuario, b.clave, request.client.host if request.client else "?")
    if motivo == "bloqueado":
        raise HTTPException(429, "Demasiados intentos. Espere unos minutos.")
    if not u:
        raise HTTPException(401, "Usuario o clave incorrectos")
    return {"token": db.emitir(u["nombre"], u["rol"], u["cambiar_clave"]), "usuario": u["nombre"], "rol": u["rol"],
            "cambiar_clave": bool(u["cambiar_clave"])}


@app.post("/api/clave")
def clave(b: Clave, request: Request):
    s = sesion(request, permitir_cambio=True)
    try:
        db.cambiar_clave(s["u"], b.nueva)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"token": db.emitir(s["u"], s["r"], 0)}


@app.get("/api/yo")
def yo(d=Depends(sesion)):
    return {"usuario": d["u"], "rol": d["r"]}


@app.get("/api/resumen")
def resumen(d=Depends(sesion)):
    return almacen.resumen()


@app.get("/api/eventos")
def eventos(d=Depends(sesion)):
    return almacen.eventos()


@app.get("/api/calidad")
def calidad(d=Depends(sesion)):
    return almacen.calidad()


# ---------------- ciclo de casos ----------------
class Cambios(BaseModel):
    cambios: dict
    nota: str = Field("", max_length=300)


class Transicion(BaseModel):
    a: str
    motivo: str = Field("", max_length=500)


@app.get("/api/catalogos")
def catalogos(d=Depends(editor)):
    ev = almacen.eventos(todos=True)
    muni = {}
    for e in ev:
        muni.setdefault(e["depto"], {})[e["mpio"]] = [e["lat"], e["lon"]]
    uniq = lambda k: sorted({e[k] for e in ev})
    return {"mods": ciclo.MODS, "grupos": ciclo.GRUPOS, "estados": ciclo.ESTADOS_V0, "prec": ciclo.PREC, "horas": ciclo.HORAS,
            "objetivos": uniq("objetivo"), "clases": uniq("clase"), "municipios": muni}


@app.get("/api/casos")
def casos(d=Depends(editor)):
    return escribir(ciclo.casos)


@app.post("/api/casos")
def crear(b: dict, d=Depends(editor)):
    return {"id": escribir(lambda c: ciclo.crear_caso(c, b, d["u"], d["r"], ahora()))}


@app.put("/api/casos/{legacy_id}")
def editar(legacy_id: str, b: Cambios, d=Depends(editor)):
    return {"version": escribir(lambda c: ciclo.editar_caso(c, legacy_id, b.cambios, d["u"], d["r"], ahora(), b.nota))}


@app.post("/api/casos/{legacy_id}/transicion")
def transicion(legacy_id: str, b: Transicion, d=Depends(editor)):
    return {"version": escribir(lambda c: ciclo.transicionar(c, legacy_id, b.a, d["u"], d["r"], ahora(), b.motivo))}


@app.get("/api/casos/{legacy_id}/historial")
def historial(legacy_id: str, d=Depends(editor)):
    return escribir(lambda c: ciclo.historial(c, ciclo.id_de(c, legacy_id)))


@app.post("/api/sincronizar")
def sincronizar(d=Depends(admin)):
    if not C.VIVO.exists():
        raise HTTPException(404, "No se encuentra el data.json vivo de OTVA 01")
    data = json.loads(C.VIVO.read_text(encoding="utf-8"))
    return escribir(lambda c: ciclo.sincronizar(c, data, ahora(), d["u"]))


@app.post("/api/exportar")
def exportar(d=Depends(admin)):
    """Genera data/export/data.json (formato v0) solo con lo publicable. NO toca el data.json vivo ni publica nada."""
    def hacer(c):
        out = ciclo.exportar_publicable(c)
        errs = [f"{e['id']}: {m}" for e in out["events"] for m in ciclo.validar_registro(e, out["updated"])]
        if errs:
            raise ciclo.Rechazo(["El conjunto exportable no pasa la validación:"] + errs[:10])
        C.EXPORT.mkdir(parents=True, exist_ok=True)
        ruta = C.EXPORT / "data.json"
        txt = json.dumps(out, ensure_ascii=False, indent=1)
        ruta.write_text(txt, encoding="utf-8")
        h = hashlib.sha256(txt.encode("utf-8")).hexdigest()
        c.execute("INSERT INTO export_log(ts,usuario,ruta,sha256,n_eventos) VALUES (?,?,?,?,?)", (ahora(), d["u"], str(ruta), h, len(out["events"])))
        core.audit_append(c, ahora(), d["r"], "exportar", "data.json", {"usuario": d["u"], "sha256": h, "n": len(out["events"])})
        c.commit()
        return {"ruta": str(ruta), "sha256": h, "eventos": len(out["events"]), "corte": out["updated"]}
    return escribir(hacer)


@app.get("/api/usuarios")
def usuarios(d=Depends(admin)):
    return db.usuarios()


@app.post("/api/usuarios")
def nuevo(b: NuevoUsuario, d=Depends(admin)):
    try:
        db.crear_usuario(b.nombre, b.rol, b.clave)
    except Exception as e:
        raise HTTPException(422, "No se pudo crear el usuario: " + str(e)[:80])
    db.registrar(d["u"], "crear_usuario", b.nombre)
    return {"ok": True}


@app.get("/api/bitacora")
def bitacora(d=Depends(admin)):
    return db.bitacora()


@app.exception_handler(FileNotFoundError)
async def sin_carga(request, exc):
    return JSONResponse({"detail": "Falta la carga inicial de datos (python -m etl.cargar inicial)"}, status_code=503)


if (C.STATIC / "assets").exists():
    app.mount("/assets", StaticFiles(directory=C.STATIC / "assets"), name="assets")


@app.get("/{ruta:path}")
def spa(ruta: str):
    if ruta.startswith("api/"):
        raise HTTPException(404)
    f = C.STATIC / "index.html"
    if not f.exists():
        return JSONResponse({"detail": "Interfaz no compilada: cd frontend && npm install && npm run build"}, status_code=503)
    return FileResponse(f)
