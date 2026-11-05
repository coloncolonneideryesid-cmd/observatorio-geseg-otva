#!/usr/bin/env python3
"""Briefing ejecutivo de situación (PDF, uso interno) a partir de data/data.json.
Uso: python src/briefing.py   ->  briefing/Briefing OTVA AAAA-MM-DD.pdf  (carpeta fuera de git: no se publica)"""
import json, shutil, subprocess, tempfile, datetime as dt, html, collections as C
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
D = json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))
E = D["events"]
CORTE = dt.date.fromisoformat(D["updated"])
START = dt.date(2026, 8, 7)
M = lambda e: e["m_civ"] + e["m_fp"]
H = lambda e: e["h_civ"] + e["h_fp"]
esc = lambda s: html.escape(str(s))
MES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
fl = lambda d: f"{d.day} de {MES[d.month]} de {d.year}"
fc = lambda s: (lambda d: f"{d.day} {MES[d.month][:3]}.")(dt.date.fromisoformat(s))


def win(a, b):
    x = [e for e in E if a <= dt.date.fromisoformat(e["fecha"]) <= b]
    return len(x), sum(map(M, x)), sum(map(H, x))


n, mu, he = len(E), sum(map(M, E)), sum(map(H, E))
last = win(CORTE - dt.timedelta(27), CORTE)
prev = win(CORTE - dt.timedelta(55), CORTE - dt.timedelta(28))
deps = C.Counter(e["depto"] for e in E)
mods = C.Counter(e["mod"] for e in E)
dron = mods["Dron con explosivos"]
civ = sum(1 for e in E if M(e) + H(e) and (e["m_civ"] + e["h_civ"]))
sin = sum(1 for e in E if e["atrib"] == "E")
ofi = sum(1 for e in E if e["atrib"] == "B")
inc = sum(1 for e in E if len(e["fuentes"]) == 1 or e["estado"] != "Confirmado")
top = sorted(E, key=lambda e: -(3 * M(e) + H(e)))[:6]
big = top[0]
palmar = [e for e in E if e["mpio"] == "San José del Palmar"]
huila = deps["Huila"]
elnc = sum(1 for e in E if e["grupo"] == "ELN")
disc = sum(1 for e in E if e["grupo"] == "Disidencias FARC")

# semanas desde el 7-ago
nw = (CORTE - START).days // 7 + 1
wk = [0] * nw
for e in E:
    wk[(dt.date.fromisoformat(e["fecha"]) - START).days // 7] += 1


def chart_weeks():
    W, Hh, pad = 520, 125, 22
    mx = max(wk) or 1
    bw = (W - 2 * pad) / nw
    s = f'<svg viewBox="0 0 {W} {Hh+26}" width="100%" role="img" aria-label="Incidentes por semana">'
    for i, v in enumerate(wk):
        h = (Hh - 20) * v / mx
        x = pad + i * bw + 3
        s += f'<rect x="{x:.1f}" y="{Hh-h:.1f}" width="{bw-6:.1f}" height="{h:.1f}" fill="#0053BB" rx="2"/>'
        s += f'<text x="{x+(bw-6)/2:.1f}" y="{Hh-h-4:.1f}" text-anchor="middle" font-size="10" fill="#0D1F3C" font-weight="700">{v or ""}</text>'
        a = START + dt.timedelta(7 * i)
        s += f'<text x="{x+(bw-6)/2:.1f}" y="{Hh+13}" text-anchor="middle" font-size="8.5" fill="#46556D">{a.day}/{a.month}</text>'
    s += f'<line x1="{pad}" x2="{W-pad}" y1="{Hh}" y2="{Hh}" stroke="#D6DDE8"/></svg>'
    return s


def chart_deps():
    items = deps.most_common()
    mx = items[0][1]
    s = ""
    for d, v in items:
        r = [e for e in E if e["depto"] == d]
        s += (f'<tr><td class="l">{esc(d)}</td><td style="width:46%"><span class="bar" style="width:{100*v/mx:.0f}%"></span></td>'
              f'<td class="n">{v}</td><td class="n r">{sum(map(M, r))}</td><td class="n">{sum(map(H, r))}</td></tr>')
    return s


def row_top(e):
    u = e["fuentes"][0]
    return (f'<tr><td class="n">{fc(e["fecha"])}</td><td><b>{esc(e["mpio"])}</b> ({esc(e["depto"])})</td>'
            f'<td>{esc(e["mod"])}</td><td class="n r">{M(e)}</td><td class="n r">{H(e)}</td>'
            f'<td>{esc(e["grupo"]) if e["atrib"]!="E" else "Sin atribución"}</td>'
            f'<td><a href="{esc(u)}">fuente</a></td></tr>')


css = """
@page{size:Letter;margin:0}
*{box-sizing:border-box}
body{margin:0;font:10.4pt/1.42 Arial,Helvetica,sans-serif;color:#0D1F3C;background:#fff}
.page{width:8.5in;height:11in;position:relative;overflow:hidden;page-break-after:always;padding:0 .55in}
.page:last-child{page-break-after:auto}
.head{background:#0D1F3C;color:#fff;margin:0 -.55in;padding:.28in .55in .22in;border-bottom:5px solid #0053BB}
.head .k{font-size:8.5pt;letter-spacing:.14em;text-transform:uppercase;color:#9ec3ff}
.head h1{padding-right:1.3in;font-size:21pt;margin:.04in 0 .02in;line-height:1.12}
.head .s{font-size:10pt;color:#cfe0ff}
.head .lg{position:absolute;right:.55in;top:.26in;font-size:15pt;font-weight:700;letter-spacing:.18em}
.head .lg small{display:block;font-size:6.5pt;letter-spacing:.02em;font-weight:400;text-align:right}
h2{font-size:12.5pt;margin:.2in 0 .06in;color:#0053BB;border-bottom:1.5px solid #D6DDE8;padding-bottom:3px}
.concl{background:#F5F7FA;border-left:6px solid #0053BB;padding:.12in .16in;margin-top:.2in;font-size:11.2pt}
.concl b.t{display:block;font-size:8.5pt;letter-spacing:.12em;text-transform:uppercase;color:#0053BB;margin-bottom:3px}
.kp{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;margin-top:.16in}
.kp div{border:1px solid #D6DDE8;border-radius:6px;padding:7px 8px;background:#fff}
.kp b{display:block;font-size:19pt;line-height:1;color:#0053BB}
.kp b.r{color:#8D1C1C}
.kp span{font-size:7.8pt;color:#46556D}
ul{margin:.04in 0 0;padding-left:.2in}li{margin-bottom:.05in}
table{border-collapse:collapse;width:100%;font-size:8.8pt}
th{background:#0D1F3C;color:#fff;font-size:7.6pt;text-transform:uppercase;letter-spacing:.04em;padding:5px 6px;text-align:left}
td{border-bottom:1px solid #E3E8F0;padding:4px 6px;vertical-align:top}
td.n{text-align:right;white-space:nowrap}td.r{color:#8D1C1C;font-weight:700}td.l{white-space:nowrap}
.bar{display:inline-block;height:9px;background:#0053BB;border-radius:3px}
a{color:#0053BB}
.two{display:grid;grid-template-columns:1fr 1fr;gap:.22in}
.obs li b{color:#0053BB}
.foot{position:absolute;left:.55in;right:.55in;bottom:.28in;font-size:7.6pt;color:#46556D;border-top:1px solid #D6DDE8;padding-top:4px;display:flex;justify-content:space-between}
.note{font-size:8.6pt;color:#46556D;margin-top:.06in}
"""

top_rows = "".join(row_top(e) for e in top)
palm = palmar[0]["fecha"] if palmar else ""
body = f"""
<div class="page">
<div class="head"><div class="lg">GESEG<small>Gestión de la Seguridad S.A.S.</small></div>
<div class="k">Briefing de situación · uso interno</div>
<h1>Terrorismo y violencia armada en Colombia</h1>
<div class="s">Observatorio territorial OTVA · desde el 7 de agosto de 2026 hasta el {fl(CORTE)}</div></div>

<div class="concl"><b class="t">La conclusión</b>
El observatorio documenta <b>{n} incidentes, {mu} fallecidos y {he} heridos en {len(deps)} departamentos</b>. El ritmo se aceleró: en los últimos 28 días hay {last[0]} incidentes y {last[1]} fallecidos, frente a {prev[0]} y {prev[1]} en los 28 anteriores. El hecho con más víctimas es <b>{esc(big['mpio'])} ({esc(big['depto'])}, {fc(big['fecha'])})</b>: {big['m_civ']} civiles muertos y cerca de {H(big)} heridos, aún preliminar y sin atribución. Los drones con explosivos son la modalidad dominante ({dron} de {n}).</div>

<div class="kp">
<div><b>{n}</b><span>Incidentes</span></div><div><b class="r">{mu}</b><span>Fallecidos<br>{sum(e['m_fp'] for e in E)} FP · {sum(e['m_civ'] for e in E)} civiles</span></div>
<div><b class="r">{he}</b><span>Heridos<br>{sum(e['h_fp'] for e in E)} FP · {sum(e['h_civ'] for e in E)} civiles</span></div>
<div><b>{len(deps)}</b><span>Departamentos</span></div><div><b>{dron}</b><span>Con drones<br>{100*dron//n} % del total</span></div><div><b>{100*sin//n} %</b><span>Sin autor<br>determinado</span></div></div>

<h2>Qué muestran los datos</h2>
<ul>
<li><b>Aceleración reciente.</b> Últimos 28 días ({fc((CORTE - dt.timedelta(27)).isoformat())} a {fc(CORTE.isoformat())}): {last[0]} incidentes, {last[1]} fallecidos, {last[2]} heridos. Los 28 días previos: {prev[0]}, {prev[1]} y {prev[2]}. Parte del salto se debe a un solo hecho (Planadas) y la comparación puede reflejar también la cobertura de las fuentes.</li>
<li><b>Drones.</b> {dron} de {n} registros; ataques contra estaciones de Policía y tropas, sobre todo en el sur del Cesar, el Catatumbo, el Chocó y el occidente del Huila ({huila} registros en Huila).</li>
<li><b>Civiles.</b> {civ} registros afectaron a población civil; el más grave, Planadas, con un bebé de dos meses entre los muertos, según la Gobernación del Tolima y la Presidencia.</li>
<li><b>Autoría.</b> {sin} de {n} registros ({100*sin//n} %) no tienen autor nombrado por autoridades; {ofi} ({100*ofi//n} %) tienen atribución oficial (ELN {elnc}, disidencias de las FARC {disc}). Una atribución oficial no es decisión judicial.</li>
<li><b>Información incompleta.</b> {inc} de {n} registros ({100*inc//n} %) son preliminares, están en investigación o tienen una sola fuente: las cifras de víctimas pueden cambiar.</li>
</ul>

<h2>Incidentes por semana (desde el 7 de agosto)</h2>
{chart_weeks()}
<div class="note">Semanas contadas desde el 7 de agosto; la última es parcial. Cuenta registros verificados en fuentes abiertas, no el universo de los hechos.</div>
<div class="foot"><span>GESEG · Del dato a la decisión · Fuentes abiertas</span><span>Corte {fl(CORTE)} · 1/2</span></div>
</div>

<div class="page">
<div class="head" style="padding:.18in .55in .14in"><div class="lg" style="top:.16in;font-size:12pt">GESEG</div><div class="k">Briefing de situación · {fl(CORTE)}</div></div>

<h2>Dónde ocurre</h2>
<table><tr><th>Departamento</th><th></th><th>Incid.</th><th>Fallec.</th><th>Heridos</th></tr>{chart_deps()}</table>
<div class="note">Describe hechos registrados; no es una clasificación de seguridad de los territorios.</div>

<h2>Los hechos más graves</h2>
<table><tr><th>Fecha</th><th>Lugar</th><th>Modalidad</th><th>Fall.</th><th>Her.</th><th>Presunto responsable</th><th></th></tr>{top_rows}</table>
<div class="note">Orden por víctimas (fallecidos pesan el triple). «Sin atribución» = ninguna autoridad nombró al autor.</div>

<div class="two">
<div><h2>Qué observar</h2><ul class="obs">
<li><b>Planadas (Tolima).</b> Balance definitivo de víctimas y si alguna autoridad atribuye el ataque.</li>
<li><b>Drones contra estaciones y tropas.</b> Nuevos hechos en el sur del Cesar, el Catatumbo, el Chocó (San José del Palmar tiene {len(palmar)} registros) y el occidente del Huila.</li>
<li><b>Artefactos en zona urbana.</b> Hechos con civiles afectados (Cúcuta, Algeciras, Planadas).</li>
<li><b>Brecha de autoría.</b> Cuántos de los {sin} hechos sin autor reciben atribución oficial.</li>
</ul></div>
<div><h2>Alcance y límites</h2><ul>
<li>Instrumento de fuentes abiertas de GESEG; no es producto de inteligencia ni de contrainteligencia.</li>
<li>«Presunto acto terrorista» es una clasificación analítica provisional, no una calificación jurídica.</li>
<li>Los conteos por actor no equivalen a responsabilidad judicial.</li>
<li>Sin nombres de víctimas ni valoración económica.</li>
<li>Revisión independiente pendiente de aprobación.</li>
</ul></div></div>

<div class="foot"><span>Tablero vivo: observatorio-geseg-otva.vercel.app · base data.json</span><span>Corte {fl(CORTE)} · 2/2</span></div>
</div>
"""
doc = f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Briefing OTVA {CORTE}</title><style>{css}</style></head><body>{body}</body></html>'

tmp = Path(tempfile.mkdtemp())
(tmp / "b.html").write_text(doc, encoding="utf-8")
out = ROOT / "briefing"
out.mkdir(exist_ok=True)
pdf = out / f"Briefing OTVA {CORTE}.pdf"
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={tmp / 'b.pdf'}",
                (tmp / "b.html").as_uri()], check=True, capture_output=True, timeout=120)
shutil.copy(tmp / "b.pdf", pdf)
(out / f"Briefing OTVA {CORTE}.html").write_text(doc, encoding="utf-8")
print("OK ->", pdf)
