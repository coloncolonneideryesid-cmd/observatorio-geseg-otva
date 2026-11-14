#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificador_fuentes.py - 07 Observatorio de Terrorismo y Violencia Armada (OTVA)

Herramienta de validacion y verificacion del repositorio de fuentes abiertas.
Solo usa la biblioteca estandar de Python (jsonschema es opcional).

Modos:
  python3 verificador_fuentes.py                     # valida estructura e integridad (sin red)
  python3 verificador_fuentes.py --construir-maestro # regenera fuentes_maestras.json
  python3 verificador_fuentes.py --comprobar-urls    # comprueba URLs (requiere red)
  python3 verificador_fuentes.py --comprobar-urls --descubrir   # ademas busca RSS y salas de prensa
  python3 verificador_fuentes.py --comprobar-urls --actualizar  # escribe resultados en los JSON

Principios:
  * Una comprobacion tecnica (HTTP 2xx) NO certifica titularidad ni contenido.
  * El estado 'inactiva' solo se asigna tras N fallos consecutivos (parametros_consulta.json).
  * Cada ejecucion queda registrada en reportes/registro_ejecuciones.jsonl, haya exito o error.
  * Nunca se usan credenciales, ni se evaden bloqueos, ni se consultan cuentas privadas.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import html.parser
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVOS_FUENTES = [
    "fuentes_institucionales.json",
    "fuentes_medios_nacionales.json",
    "fuentes_medios_regionales.json",
    "fuentes_redes_sociales.json",
    "fuentes_internacionales_academicas.json",
]
MAESTRO = "fuentes_maestras.json"
ESQUEMA = "esquema_validacion.json"
PARAMETROS = "parametros_consulta.json"
CATEGORIAS = "categorias_monitoreo.json"
DIR_REPORTES = os.path.join(BASE, "reportes")
URL_FIELDS = ["url_principal", "url_consulta", "url_comunicados", "url_rss", "url_api"]
# Plataformas que no se pueden comprobar sin API autorizada (muro de inicio de sesion)
NO_COMPROBABLES = {"X", "Facebook", "Instagram", "TikTok", "Threads"}


def ahora():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def cargar(nombre):
    with open(os.path.join(BASE, nombre), encoding="utf-8") as f:
        return json.load(f)


def guardar(nombre, data):
    ruta = os.path.join(BASE, nombre)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, ruta)


def normalizar_texto(s):
    """Minusculas, sin tildes ni signos: base de la normalizacion de nombres y deduplicacion."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def normalizar_url(u):
    """URL canonica para detectar duplicados: sin esquema, sin www, sin barra final ni parametros de rastreo."""
    if not u:
        return None
    p = urllib.parse.urlsplit(u.strip())
    host = (p.hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    path = p.path.rstrip("/")
    return host + path + ("?" + urllib.parse.urlencode(q) if q else "")


# --------------------------------------------------------------------------- validacion
class Hallazgos:
    def __init__(self):
        self.items = []

    def add(self, nivel, codigo, archivo, id_fuente, detalle):
        self.items.append(dict(nivel=nivel, codigo=codigo, archivo=archivo, id_fuente=id_fuente, detalle=detalle))

    def cuenta(self, nivel):
        return sum(1 for i in self.items if i["nivel"] == nivel)


def validar(h):
    """Valida sintaxis, esquema, reglas de integridad y consistencia del maestro."""
    esquema = cargar(ESQUEMA)
    reglas = esquema["x-reglas_integridad"]
    cats = cargar(CATEGORIAS)
    temas_validos = {t["codigo"] for t in cats["temas"]}
    deptos_validos = {d["nombre_normalizado"] for d in cats["normalizacion_geografica"]["departamentos"]}
    try:
        import jsonschema  # opcional
        validador = jsonschema.Draft202012Validator(
            {**esquema["$defs"]["archivo_fuentes"], "$defs": esquema["$defs"]})
    except ImportError:
        validador = None
        h.add("aviso", "SIN_JSONSCHEMA", None, None, "jsonschema no instalado; se aplican solo reglas internas.")

    todas, ids, urls, nombres = [], {}, {}, {}
    todos_ids = {x.get("id_fuente") for a in ARCHIVOS_FUENTES for x in _safe_fuentes(a)}
    for archivo in ARCHIVOS_FUENTES + [PARAMETROS, CATEGORIAS, ESQUEMA]:
        try:
            cargar(archivo)
        except FileNotFoundError:
            h.add("error", "ARCHIVO_FALTANTE", archivo, None, "No existe el archivo.")
        except json.JSONDecodeError as e:
            h.add("error", "JSON_INVALIDO", archivo, None, str(e))

    for archivo in ARCHIVOS_FUENTES:
        try:
            doc = cargar(archivo)
        except Exception:
            continue
        if validador:
            for err in validador.iter_errors(doc):
                ruta = list(err.absolute_path)
                idf = None
                if len(ruta) >= 2 and ruta[0] == "fuentes":
                    idf = doc["fuentes"][ruta[1]].get("id_fuente")
                h.add("error", "ESQUEMA", archivo, idf, f"{'/'.join(map(str, ruta))}: {err.message}")
        for s in doc.get("fuentes", []):
            idf = s.get("id_fuente")
            todas.append((archivo, s))
            faltan = [c for c in esquema["$defs"]["fuente"]["required"] if c not in s]
            if faltan:
                h.add("error", "CAMPOS_FALTANTES", archivo, idf, ", ".join(faltan))
            if idf in ids:
                h.add("error", "ID_DUPLICADO", archivo, idf, f"Tambien en {ids[idf]}")
            ids[idf] = archivo
            pref = reglas["prefijo_por_archivo"].get(archivo)
            if pref and idf and not idf.startswith(pref):
                h.add("error", "PREFIJO_ID", archivo, idf, f"Se esperaba prefijo {pref}")
            for campo, valor in s.items():
                if valor == "" or valor == []:
                    if campo not in reglas["campos_lista_vacia_permitida"]:
                        h.add("aviso", "VACIO_EN_LUGAR_DE_NULL", archivo, idf, f"{campo} vacio: usar null")
            for t in s.get("temas_monitoreados") or []:
                if t not in temas_validos:
                    h.add("error", "TEMA_NO_TAXONOMIA", archivo, idf, t)
            dep = s.get("departamento")
            if dep and dep not in deptos_validos:
                h.add("error", "DEPARTAMENTO_NO_NORMALIZADO", archivo, idf, dep)
            if s.get("nivel_cobertura") == "municipal" and not s.get("municipio"):
                h.add("error", "MUNICIPIO_REQUERIDO", archivo, idf, "nivel municipal sin municipio")
            if s.get("nivel_cobertura") in ("departamental", "municipal") and not dep:
                h.add("error", "DEPARTAMENTO_REQUERIDO", archivo, idf, "cobertura territorial sin departamento")
            if s.get("categoria") == "red_social" and s.get("estado") == "activa" and not s.get("fecha_verificacion"):
                h.add("error", "CUENTA_ACTIVA_SIN_VERIFICAR", archivo, idf, "")
            if s.get("estado") == "activa" and not s.get("fecha_verificacion"):
                h.add("error", "ACTIVA_SIN_FECHA_VERIFICACION", archivo, idf, "")
            if s.get("fuente_relacionada") and s["fuente_relacionada"] not in todos_ids:
                h.add("error", "RELACION_ROTA", archivo, idf, s["fuente_relacionada"])
            if not s.get("url_principal") and not s.get("identificador_cuenta"):
                h.add("aviso", "REGISTRO_INCOMPLETO", archivo, idf, "Sin URL ni identificador de cuenta")
            nn = normalizar_texto(s.get("nombre"))
            if nn in nombres:
                h.add("aviso", "NOMBRE_DUPLICADO", archivo, idf, f"Igual a {nombres[nn]}")
            nombres[nn] = idf
            u = normalizar_url(s.get("url_principal"))
            if u:
                urls.setdefault(u, []).append(idf)
    for u, lst in urls.items():
        if len(lst) > 1:
            # Las direcciones sin dominio propio (p. ej. DIJIN/DIPOL) se relacionan con fuente_relacionada.
            h.add("info", "URL_COMPARTIDA", None, ",".join(lst), u)

    # consistencia con el maestro
    try:
        m = cargar(MAESTRO)
        mids = {x["id_fuente"] for x in m["fuentes"]}
        if mids != set(ids):
            h.add("error", "MAESTRO_DESINCRONIZADO", MAESTRO, None,
                  f"faltan {sorted(set(ids) - mids)[:10]} sobran {sorted(mids - set(ids))[:10]}")
    except FileNotFoundError:
        h.add("error", "ARCHIVO_FALTANTE", MAESTRO, None, "Ejecutar --construir-maestro")
    return todas


_cache = {}
def _safe_fuentes(a):
    if a not in _cache:
        try:
            _cache[a] = cargar(a).get("fuentes", [])
        except Exception:
            _cache[a] = []
    return _cache[a]


# --------------------------------------------------------------------------- maestro
def construir_maestro():
    fuentes, resumen = [], {}
    for a in ARCHIVOS_FUENTES:
        lst = cargar(a)["fuentes"]
        resumen[a] = len(lst)
        for s in lst:
            fuentes.append({**s, "archivo_origen": a})
    estados = {}
    for s in fuentes:
        estados[s["estado"]] = estados.get(s["estado"], 0) + 1
    indices = {
        "por_departamento": {}, "por_categoria": {}, "por_plataforma": {}, "por_nivel_cobertura": {},
        "por_region": {}, "por_confiabilidad": {},
    }
    claves = [("por_departamento", "departamento"), ("por_categoria", "categoria"),
              ("por_plataforma", "plataforma"), ("por_nivel_cobertura", "nivel_cobertura"),
              ("por_region", "region"), ("por_confiabilidad", "confiabilidad_fuente")]
    for s in fuentes:
        for idx, campo in claves:
            k = s.get(campo) or "sin_dato"
            indices[idx].setdefault(k, []).append(s["id_fuente"])
    doc = {
        "metadata": {
            "producto": "07 Observatorio de Terrorismo y Violencia Armada (OTVA)",
            "archivo": MAESTRO,
            "descripcion": "Directorio general consolidado. Archivo DERIVADO: no editar a mano; "
                           "editar los archivos por categoria y ejecutar --construir-maestro.",
            "version_esquema": "1.0.0", "generado": ahora(),
            "total_fuentes": len(fuentes), "por_archivo": resumen, "por_estado": estados,
        },
        "indices": indices,
        "fuentes": fuentes,
    }
    guardar(MAESTRO, doc)
    return doc


# --------------------------------------------------------------------------- red
class _LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.feeds, self.links = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link" and "alternate" in (a.get("rel") or "").lower() and \
                (a.get("type") or "").lower() in ("application/rss+xml", "application/atom+xml"):
            self.feeds.append(a.get("href"))
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])


def _ctx():
    ctx = ssl.create_default_context()
    ca = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if ca and os.path.exists(ca):
        ctx.load_verify_locations(ca)
    return ctx


def comprobar(url, params, leer=False):
    """GET con redirecciones. Devuelve dict con resultado; nunca lanza excepcion."""
    cfg = params["comprobacion_urls"]
    req = urllib.request.Request(url, headers={
        "User-Agent": cfg["user_agent"], "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CO,es;q=0.9"})
    t0 = time.time()
    res = {"url": url, "fecha": ahora(), "codigo_http": None, "url_final": None, "error": None,
           "tiempo_ms": None, "tipo_contenido": None}
    for intento in range(cfg["reintentos"] + 1):
        try:
            with urllib.request.urlopen(req, timeout=cfg["timeout_segundos"], context=_ctx()) as r:
                res.update(codigo_http=r.status, url_final=r.geturl(),
                           tipo_contenido=r.headers.get("Content-Type"))
                cuerpo = r.read(cfg["max_bytes_lectura"] if leer else 65536).decode("utf-8", "replace")
                res["_muestra"] = cuerpo[:65536]
                if leer:
                    res["_cuerpo"] = cuerpo
                res["error"] = None
                break
        except urllib.error.HTTPError as e:
            res.update(codigo_http=e.code, url_final=e.geturl(), error=f"HTTP {e.code}")
            if e.code < 500 and e.code != 429:
                break
        except Exception as e:  # DNS, TLS, timeout, conexion
            res["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(cfg["espera_entre_reintentos_segundos"])
    res["tiempo_ms"] = int((time.time() - t0) * 1000)
    return res


RETO_HOSTS = ("perfdrive.com", "captcha", "challenge", "hcaptcha.com", "recaptcha")
RETO_TEXTO = re.compile(r"(just a moment\.\.\.|cf-chl-|attention required|verify you are human|"
                        r"radware bot manager|captcha-delivery|are you a robot)", re.I)


def _dominio(u):
    h = (urllib.parse.urlsplit(u or "").hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def clasificar(res):
    c = res["codigo_http"]
    if c and 200 <= c < 400:
        final = res.get("url_final") or ""
        if any(x in _dominio(final) for x in RETO_HOSTS) or RETO_TEXTO.search(res.get("_muestra") or ""):
            return "bloqueado_o_restringido"  # pagina de reto anti-bots servida con 200
        if final and _dominio(final) != _dominio(res["url"]):
            return "redireccion_otro_dominio"  # requiere revision humana antes de aceptar el nuevo dominio
        return "ok"
    if c in (401, 403, 429) or (c == 406):
        return "bloqueado_o_restringido"  # el servidor existe pero rechaza clientes automaticos
    if c and c in (404, 410):
        return "enlace_roto"
    if c and c >= 500:
        return "error_servidor"
    return "sin_respuesta"


def descubrir(res, base_url, params):
    """Busca RSS declarados y enlaces candidatos a sala de prensa. No modifica los JSON."""
    cuerpo = res.pop("_cuerpo", "") or ""
    p = _LinkParser()
    try:
        p.feed(cuerpo)
    except Exception:
        pass
    host = urllib.parse.urlsplit(res.get("url_final") or base_url).hostname or ""
    pat = re.compile(params["descubrimiento"]["patron_enlaces_prensa"], re.I)
    feeds = sorted({urllib.parse.urljoin(res.get("url_final") or base_url, f) for f in p.feeds if f})
    prensa = []
    for l in p.links:
        abs_ = urllib.parse.urljoin(res.get("url_final") or base_url, l)
        if urllib.parse.urlsplit(abs_).hostname == host and pat.search(urllib.parse.urlsplit(abs_).path):
            prensa.append(abs_.split("#")[0])
    return {"rss_declarados": feeds[:10], "candidatos_prensa": sorted(set(prensa))[:15]}


def es_feed_valido(texto):
    """True si el documento es RSS/Atom/RDF. Se lee la etiqueta raiz porque los feeds grandes
    pueden truncarse en max_bytes_lectura y no serian XML completo."""
    try:
        root = ET.fromstring(texto.encode("utf-8"))
        return root.tag.lower().endswith(("rss", "feed", "rdf"))
    except Exception:
        cabeza = re.sub(r"<\?xml[^>]*\?>|<!--.*?-->|<\?xml-stylesheet[^>]*\?>", "", texto[:4000], flags=re.S).lstrip()
        return bool(re.match(r"<(rss|feed|rdf:RDF)[\s>]", cabeza, re.I))


def comprobar_fuentes(fuentes, params, hacer_descubrimiento):
    tareas = []
    for archivo, s in fuentes:
        if s.get("plataforma") in NO_COMPROBABLES:
            continue
        for campo in URL_FIELDS:
            if s.get(campo):
                tareas.append((archivo, s["id_fuente"], campo, s[campo]))
    resultados = []
    with cf.ThreadPoolExecutor(max_workers=params["comprobacion_urls"]["concurrencia"]) as ex:
        futs = {}
        for t in tareas:
            leer = (hacer_descubrimiento and t[2] == "url_principal") or t[2] == "url_rss"
            futs[ex.submit(comprobar, t[3], params, leer)] = t
        for f in cf.as_completed(futs):
            archivo, idf, campo, url = futs[f]
            r = f.result()
            r.update(archivo=archivo, id_fuente=idf, campo=campo, clasificacion=clasificar(r))
            r.pop("_muestra", None)
            if campo == "url_rss":
                r["feed_valido"] = es_feed_valido(r.pop("_cuerpo", "") or "")
            elif "_cuerpo" in r:
                r["descubrimiento"] = descubrir(r, url, params)
            resultados.append(r)
    return sorted(resultados, key=lambda x: (x["id_fuente"], x["campo"]))


def aplicar_resultados(resultados, params):
    """Actualiza estado, fechas y resultado_ultima_comprobacion en los archivos por categoria."""
    umbral = params["comprobacion_urls"]["fallos_consecutivos_para_inactiva"]
    horas_min = params["comprobacion_urls"]["horas_minimas_entre_primer_y_ultimo_fallo"]
    por_id = {}
    for r in resultados:
        if r["campo"] == "url_principal":
            por_id[r["id_fuente"]] = r
    cambios = 0
    for a in ARCHIVOS_FUENTES:
        doc = cargar(a)
        for s in doc["fuentes"]:
            r = por_id.get(s["id_fuente"])
            if not r:
                continue
            s["fecha_ultima_consulta"] = r["fecha"]
            s["resultado_ultima_comprobacion"] = {k: r.get(k) for k in
                ("fecha", "codigo_http", "url_final", "clasificacion", "error", "tiempo_ms")}
            if r["clasificacion"] == "ok":
                s["fallos_consecutivos"] = 0
                s["fecha_primer_fallo"] = None
                s["fecha_verificacion"] = r["fecha"]
                if s["estado"] != "activa":
                    s["estado"] = "activa"
                    cambios += 1
            elif r["clasificacion"] in ("bloqueado_o_restringido", "redireccion_otro_dominio"):
                # El servidor responde pero no a clientes automaticos, o cambio de dominio:
                # requiere verificacion manual. Si estaba activa vuelve a pendiente.
                if s["estado"] == "activa":
                    s["estado"] = "pendiente_verificacion"
                    cambios += 1
            else:
                s["fallos_consecutivos"] = (s.get("fallos_consecutivos") or 0) + 1
                s["fecha_primer_fallo"] = s.get("fecha_primer_fallo") or r["fecha"]
                horas = (dt.datetime.fromisoformat(r["fecha"]) -
                         dt.datetime.fromisoformat(s["fecha_primer_fallo"])).total_seconds() / 3600
                # Inactiva solo con N fallos consecutivos que abarquen un periodo minimo:
                # evita declarar inactiva una fuente por una caida transitoria.
                if s["fallos_consecutivos"] >= umbral and horas >= horas_min and s["estado"] != "inactiva":
                    s["estado"] = "inactiva"
                    cambios += 1
        guardar(a, doc)
    return cambios


# --------------------------------------------------------------------------- reportes
def escribir_reportes(h, fuentes, resultados, inicio, args, error=None):
    os.makedirs(DIR_REPORTES, exist_ok=True)
    origen_urls = inicio
    if not resultados:
        # Validacion sin red: conservar la ultima comprobacion real en lugar de borrarla.
        try:
            with open(os.path.join(DIR_REPORTES, "reporte_calidad.json"), encoding="utf-8") as f:
                previo = json.load(f)
            resultados = previo.get("comprobacion_urls") or []
            origen_urls = previo.get("origen_comprobacion_urls") or previo.get("inicio")
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    estados, cat = {}, {}
    for _, s in fuentes:
        estados[s["estado"]] = estados.get(s["estado"], 0) + 1
        cat[s["categoria"]] = cat.get(s["categoria"], 0) + 1
    pendientes = [dict(id_fuente=s["id_fuente"], nombre=s["nombre"], archivo=a,
                       motivo=(s.get("resultado_ultima_comprobacion") or {}).get("clasificacion")
                       or ("plataforma_no_comprobable_sin_api" if s.get("plataforma") in NO_COMPROBABLES
                           else "sin_comprobacion"),
                       observaciones=s.get("observaciones"))
                  for a, s in fuentes if s["estado"] == "pendiente_verificacion"]
    clas = {}
    for r in resultados:
        clas[r["clasificacion"]] = clas.get(r["clasificacion"], 0) + 1
    rep = {
        "generado": ahora(), "inicio": inicio, "modo": vars(args),
        "resumen": {
            "total_fuentes": len(fuentes), "por_estado": estados, "por_categoria": cat,
            "errores_validacion": h.cuenta("error"), "avisos_validacion": h.cuenta("aviso"),
            "urls_comprobadas": len(resultados), "resultado_urls": clas,
            "origen_comprobacion_urls": origen_urls,
        },
        "origen_comprobacion_urls": origen_urls,
        "hallazgos_validacion": h.items,
        "comprobacion_urls": resultados,
        "pendientes_verificacion": pendientes,
        "error_ejecucion": error,
    }
    with open(os.path.join(DIR_REPORTES, "reporte_calidad.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DIR_REPORTES, "fuentes_pendientes.json"), "w", encoding="utf-8") as f:
        json.dump(pendientes, f, ensure_ascii=False, indent=2)
    # Markdown legible
    L = [f"# Reporte de calidad - fuentes OTVA", "", f"Generado: {rep['generado']}", "",
         "## Resumen", "", f"- Total de fuentes: {len(fuentes)}"]
    L += [f"- Estado `{k}`: {v}" for k, v in sorted(estados.items())]
    L += [f"- Errores de validacion: {h.cuenta('error')}", f"- Avisos de validacion: {h.cuenta('aviso')}",
          f"- URLs comprobadas: {len(resultados)} (ejecucion iniciada {origen_urls})"]
    L += [f"  - `{k}`: {v}" for k, v in sorted(clas.items())]
    if h.items:
        L += ["", "## Hallazgos de validacion", "", "| Nivel | Codigo | Archivo | Fuente | Detalle |", "|---|---|---|---|---|"]
        L += [f"| {i['nivel']} | {i['codigo']} | {i['archivo'] or ''} | {i['id_fuente'] or ''} | {str(i['detalle'])[:120]} |"
              for i in h.items]
    malos = [r for r in resultados if r["clasificacion"] != "ok"]
    if malos:
        L += ["", "## URLs con problemas", "", "| Fuente | Campo | URL | Clasificacion | Detalle |", "|---|---|---|---|---|"]
        L += [f"| {r['id_fuente']} | {r['campo']} | {r['url']} | {r['clasificacion']} | {r['error'] or r['codigo_http']} |"
              for r in malos]
    redir = [r for r in resultados if r["clasificacion"] == "redireccion_otro_dominio"]
    if redir:
        L += ["", "## Redirecciones a otro dominio (revisar)", ""]
        L += [f"- {r['id_fuente']} {r['url']} -> {r['url_final']}" for r in redir]
    desc = [r for r in resultados if r.get("descubrimiento") and
            (r["descubrimiento"]["rss_declarados"] or r["descubrimiento"]["candidatos_prensa"])]
    if desc:
        L += ["", "## Descubrimiento (candidatos, requieren revision humana antes de registrarse)", ""]
        for r in desc:
            d = r["descubrimiento"]
            L.append(f"- **{r['id_fuente']}** RSS: {', '.join(d['rss_declarados'][:3]) or '-'} | "
                     f"prensa: {', '.join(d['candidatos_prensa'][:4]) or '-'}")
    L += ["", f"## Fuentes pendientes de verificacion ({len(pendientes)})", ""]
    L += [f"- {p['id_fuente']} {p['nombre']} - {p['motivo']}" for p in pendientes]
    with open(os.path.join(DIR_REPORTES, "reporte_calidad.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    # historial de ejecuciones (append-only)
    with open(os.path.join(DIR_REPORTES, "registro_ejecuciones.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"inicio": inicio, "fin": ahora(), "modo": vars(args),
                            "resultado": "error" if error else ("con_errores_validacion" if h.cuenta("error") else "ok"),
                            "resumen": rep["resumen"], "error": error}, ensure_ascii=False) + "\n")
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--construir-maestro", action="store_true")
    ap.add_argument("--comprobar-urls", action="store_true")
    ap.add_argument("--descubrir", action="store_true")
    ap.add_argument("--actualizar", action="store_true",
                    help="Escribe estado/fechas en los JSON a partir de la comprobacion")
    ap.add_argument("--solo", help="Lista de id_fuente separados por coma")
    args = ap.parse_args()
    inicio = ahora()
    h, fuentes, resultados, error = Hallazgos(), [], [], None
    try:
        if args.construir_maestro:
            construir_maestro()
        fuentes = validar(h)
        if args.comprobar_urls:
            params = cargar(PARAMETROS)
            sel = fuentes
            if args.solo:
                ids = set(args.solo.split(","))
                sel = [(a, s) for a, s in fuentes if s["id_fuente"] in ids]
            resultados = comprobar_fuentes(sel, params, args.descubrir)
            if args.actualizar:
                aplicar_resultados(resultados, params)
                construir_maestro()
                _cache.clear()
                h = Hallazgos()
                fuentes = validar(h)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    rep = escribir_reportes(h, fuentes, resultados, inicio, args, error)
    r = rep["resumen"]
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if error:
        print("ERROR:", error, file=sys.stderr)
        return 2
    return 1 if r["errores_validacion"] else 0


if __name__ == "__main__":
    sys.exit(main())
