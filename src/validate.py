#!/usr/bin/env python3
"""Valida data/data.json del Observatorio GESEG. Falla con mensaje claro si hay errores."""
import json, sys, re, datetime as dt
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INICIO = dt.date(2026, 8, 7)
MODS = ["Dron con explosivos", "Vehículo con explosivos", "Explosivo / IED", "Granada / artefacto lanzado",
        "Paro armado", "Homicidio selectivo", "Ataque armado"]
GRUPOS = ["ELN", "Disidencias FARC", "Clan del Golfo / EGC", "ACSN", "Autor individual (capturado)", "No determinado"]
ESTADOS = ["Confirmado", "Preliminar", "En investigación"]
PREC = ["Municipal aproximada", "Departamental aproximada"]
STR = ["id", "fecha", "hora", "depto", "mpio", "lugar", "prec_coord", "tipo", "mod", "objetivo", "clase", "autor", "grupo",
       "atrib", "evidencia", "h_nota", "danos", "eco", "desplaz", "servicios", "estado", "discrepancia", "actualizacion"]
INT = ["m_civ", "m_fp", "h_civ", "h_fp"]


def main():
    d = json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))
    err = []
    try:
        corte = dt.date.fromisoformat(d["updated"])
    except Exception:
        sys.exit("ERROR: 'updated' ausente o no es AAAA-MM-DD")
    ev = d.get("events", [])
    for k in ("excluded", "context"):
        if not isinstance(d.get(k), list):
            err.append(f"'{k}' debe ser lista")
    ids = Counter(e.get("id") for e in ev)
    for e in ev:
        i = e.get("id", "?")
        for k in STR + INT + ["lat", "lon", "fuentes"]:
            if k not in e:
                err.append(f"{i}: falta el campo '{k}'")
        if any(k not in e for k in STR + INT + ["lat", "lon", "fuentes"]):
            continue
        for k in STR:
            if not isinstance(e[k], str):
                err.append(f"{i}: '{k}' debe ser texto")
        for k in INT:
            if not isinstance(e[k], int) or isinstance(e[k], bool) or e[k] < 0:
                err.append(f"{i}: '{k}' debe ser entero >= 0")
        if not re.fullmatch(r"CO-2026-\d{3}", i):
            err.append(f"{i}: formato de id inválido")
        if ids[i] > 1:
            err.append(f"{i}: id duplicado")
        try:
            f = dt.date.fromisoformat(e["fecha"])
            if f < INICIO:
                err.append(f"{i}: fecha {f} anterior al 2026-08-07")
            if f > corte:
                err.append(f"{i}: fecha {f} posterior al corte {corte}")
        except Exception:
            err.append(f"{i}: fecha inválida")
        if not (re.fullmatch(r"\d{2}:\d{2}", e["hora"]) or e["hora"] in ("Sin dato", "Noche", "Madrugada", "Mañana", "Tarde", "Día")):
            err.append(f"{i}: hora inválida '{e['hora']}'")
        if e["atrib"] not in list("ABCDE"):
            err.append(f"{i}: atrib '{e['atrib']}' fuera de A–E")
        if e["mod"] not in MODS:
            err.append(f"{i}: mod '{e['mod']}' fuera de la lista controlada")
        if e["grupo"] not in GRUPOS:
            err.append(f"{i}: grupo '{e['grupo']}' fuera de la lista")
        if e["estado"] not in ESTADOS:
            err.append(f"{i}: estado inválido")
        if e["prec_coord"] not in PREC:
            err.append(f"{i}: prec_coord inválida")
        if e["atrib"] == "E" and e["grupo"] != "No determinado":
            err.append(f"{i}: atrib E exige grupo 'No determinado' (no se infiere autoría)")
        if not (isinstance(e["lat"], (int, float)) and isinstance(e["lon"], (int, float))
                and -4.3 <= e["lat"] <= 13.5 and -79.1 <= e["lon"] <= -66.8):
            err.append(f"{i}: coordenadas fuera de Colombia")
        fu = e["fuentes"]
        if not isinstance(fu, list) or not 1 <= len(fu) <= 3 or not all(isinstance(u, str) and u.startswith("https://") for u in fu):
            err.append(f"{i}: 'fuentes' debe tener 1 a 3 URL https://")
    # posibles duplicados
    for a in range(len(ev)):
        for b in range(a + 1, len(ev)):
            x, y = ev[a], ev[b]
            try:
                if (x["mpio"] == y["mpio"] and x["mod"] == y["mod"]
                        and abs((dt.date.fromisoformat(x["fecha"]) - dt.date.fromisoformat(y["fecha"])).days) <= 1):
                    err.append(f"posible duplicado: {x['id']} y {y['id']} (mismo municipio, modalidad y fecha ±1 día)")
            except Exception:
                pass
    if err:
        print("VALIDACIÓN FALLIDA:")
        for m in err:
            print(" -", m)
        sys.exit(1)
    mu = sum(e["m_civ"] + e["m_fp"] for e in ev)
    he = sum(e["h_civ"] + e["h_fp"] for e in ev)
    print("VALIDACIÓN OK")
    print(f"Corte: {corte} | Incidentes: {len(ev)} | Muertos: {mu} | Heridos: {he}")
    print(f"Departamentos: {len({e['depto'] for e in ev})} | Municipios: {len({(e['depto'], e['mpio']) for e in ev})}")
    print("Por grupo:", dict(Counter(e['grupo'] for e in ev)))
    print("Por atribución:", dict(sorted(Counter(e['atrib'] for e in ev).items())))
    print("Fuente única:", sum(1 for e in ev if len(e['fuentes']) == 1))
    print(f"Excluidos: {len(d['excluded'])} | Contexto: {len(d['context'])}")


if __name__ == "__main__":
    main()
