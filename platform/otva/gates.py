"""Compuertas de autopublicación (ADR-002) y fórmula de confianza (docs 02 §4). Funciones puras, sin red.

Un evento nuevo se autopublica solo si TODAS las compuertas duras pasan Y tiene fuente oficial o >= 2 fuentes
independientes. Si no, queda en cola interna con los motivos. Las compuertas blandas (heurísticas) mandan a cola,
nunca publican.
"""
import re
from dataclasses import dataclass, field

ADMIRALTY = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4, "E": 0.2, "F": 0.0}
W = {"F": 0.35, "I": 0.30, "K": 0.20, "O": 0.15}      # pesos provisionales (docs 02 §4)
CONF_VERSION = "conf-0.1"
COLOMBIA_BBOX = (-4.3, 13.5, -79.1, -66.8)               # lat_min, lat_max, lon_min, lon_max (amplio)

# Heurísticas de instrucciones embebidas y de nombres de personas. Son filtros de apoyo, no garantía.
INJECTION = re.compile(r"(ignore|ignora|olvida|disregard)\W+(all|todas|las|previous|anteriores|instrucciones|instructions)"
                       r"|system prompt|eres un|you are an?|\bassistant:|<\s*/?\s*(system|instructions?)\s*>", re.I)
PERSON = re.compile(r"\b(alias|alias\.|se[ñn]or|se[ñn]ora|sr\.|sra\.|capit[aá]n|coronel|teniente|sargento|cabo|soldado|"
                    r"patrullero)\s+[«\"']?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+", )
MINOR = re.compile(r"\b(menor(es)? de edad|ni[ñn][oa]s?|adolescentes?|reci[eé]n nacid)", re.I)


@dataclass
class Source:
    doc_id: str
    outlet_group_id: str
    is_official: bool = False
    archived: bool = False          # tiene sha256 y fetched_at
    copy_of: str | None = None      # doc_id del que copia verbatim (agencia/sindicada)
    admiralty_source: str = "C"


@dataclass
class Candidate:
    event_key: str                  # clave de duplicado (p. ej., mpio+fecha+tipo)
    attribution_level: str = "E"
    attribution_ref: str | None = None
    sources: list = field(default_factory=list)
    texts: list = field(default_factory=list)        # extracto, base de atribución, daños, etc.
    lat: float | None = None
    lon: float | None = None
    casualties: dict = field(default_factory=dict)   # valores int o None
    infra_sensitive: bool = False
    published_geo_precision: str = "municipio"
    published_time_precision: str = "día"
    fecha_consistente: bool = True  # fecha del evento <= fecha de captura y >= inicio del observatorio


def independent_sources(srcs):
    """Fuentes con propietario editorial distinto y sin copia verbatim."""
    return {s.outlet_group_id for s in srcs if s.copy_of is None}


def confidence(c: Candidate):
    srcs = [s for s in c.sources if s.copy_of is None]
    if not srcs:
        return 0.0, {"F": 0, "I": 0, "K": 0, "O": 0, "version": CONF_VERSION}
    F = sum(ADMIRALTY[s.admiralty_source] for s in srcs) / len(srcs)
    I = min(1.0, len(independent_sources(c.sources)) / 3)
    K = 1.0 if c.fecha_consistente else 0.0
    O = 1.0 if any(s.is_official for s in c.sources) else 0.0
    score = round(W["F"] * F + W["I"] * I + W["K"] * K + W["O"] * O, 4)
    return score, {"F": F, "I": I, "K": K, "O": O, "version": CONF_VERSION}


def evaluate(c: Candidate, known_keys=frozenset(), exigir_archivo=True):
    """Devuelve (decision, motivos). decision en {'PUBLICAR','COLA'}."""
    hard, soft = evaluar(c, known_keys, exigir_archivo)
    reasons = hard + soft
    return ("PUBLICAR" if not reasons else "COLA"), reasons


def evaluar(c: Candidate, known_keys=frozenset(), exigir_archivo=True):
    """Devuelve (motivos_duros, motivos_blandos). Los duros nunca se pueden saltar; los blandos son heurísticas
    que pasan a revisión humana. `exigir_archivo=False` es un régimen transitorio (aún no hay captura automática)."""
    hard, soft = [], []
    if not c.sources:
        hard.append("sin fuente")
    if exigir_archivo and c.sources and not all(s.archived for s in c.sources):
        hard.append("fuente sin archivar (hash y fecha de captura)")
    if c.attribution_level not in "ABCDE" or len(c.attribution_level) != 1:
        hard.append("nivel de atribución inválido")
    if c.attribution_level in "ABCD" and not c.attribution_ref:
        hard.append("atribución A–D sin referencia de apoyo")
    if any(v is not None and (not isinstance(v, int) or v < 0) for v in c.casualties.values()):
        hard.append("conteo de víctimas inválido")
    if c.lat is not None and c.lon is not None:
        a, b, x, y = COLOMBIA_BBOX
        if not (a <= c.lat <= b and x <= c.lon <= y):
            hard.append("coordenadas fuera de Colombia")
    if not c.fecha_consistente:
        hard.append("fecha incoherente")
    if c.event_key in known_keys:
        hard.append("posible duplicado")
    if c.infra_sensitive and (c.published_geo_precision not in ("municipio", "departamento") or c.published_time_precision not in ("semana", "mes")):
        hard.append("infraestructura sensible sin degradar a municipio y semana")
    blob = " ".join(t for t in c.texts if t)
    if INJECTION.search(blob):
        hard.append("instrucción embebida detectada en el texto")
    if PERSON.search(blob) or MINOR.search(blob):
        soft.append("posible nombre o referencia a persona (revisión humana)")
    official = any(s.is_official for s in c.sources)
    n_ind = len(independent_sources(c.sources))
    if not (official or n_ind >= 2):
        hard.append("ni fuente oficial ni 2 fuentes independientes")
    return hard, soft
