# Aplica a la plantilla recibida los cambios aceptados por R13 en ER-0023 (10-nov-2026).
# Entrada: fuente_recibida/template_ejecutivo_recibido_2026-11-10.html  ->  Salida: plantilla_v2/template_ejecutivo_v2.html
import re, pathlib, sys
base = pathlib.Path(__file__).parent
src = (base / "fuente_recibida" / "template_ejecutivo_recibido_2026-11-10.html").read_text(encoding="utf-8")
h = src

def rep(old, new, count=1):
    global h
    assert h.count(old) >= 1, "No encontrado: " + old[:80]
    h = h.replace(old, new) if count == 0 else h.replace(old, new, count)

# --- Estructura alineada con el PDF revisado ---
h = re.sub(r'\s*<dl class="ficha">.*?</dl>', '', h, flags=re.S)
h = re.sub(r'<span class="part">[^<]*</span>', '', h)
rep('Lectura breve dirigida a analistas, líderes políticos y empresariales y tanques de pensamiento. Sigue un orden fijo: resumen, la amenaza (dónde, cómo evoluciona y quién), la amenaza prioritaria de drones y la respuesta del Estado. Las cifras salen de la misma base verificada del tablero completo del Observatorio GESEG.',
    'Lectura de tres minutos para gobierno nacional y local: la amenaza prioritaria de drones con explosivos, dónde se concentra el riesgo, cómo evoluciona la tendencia, quién aparece señalado y cómo responde el Estado. Las cifras salen de la misma base verificada del tablero completo del Observatorio GESEG.')
rep('<h2>1 · Dónde se concentra</h2>', '<h2>1 · Dónde está el riesgo</h2>')
rep('<h2>2 · Cómo evoluciona</h2><span>Hechos por semana y señales de alerta, contados hacia atrás desde el corte</span>', '<h2>2 · Tendencia y señales de alerta</h2><span>Hechos por semana, contadas hacia atrás desde el corte</span>')
rep('<h2>4 · Drones con explosivos</h2>', '<h2>Amenaza prioritaria · Drones con explosivos</h2>')
rep('<span class="part">II', '<span class="part">II') if '<span class="part">II' in h else None
rep('<h2>5 · Cómo responde el Estado</h2>', '<h2>4 · Respuesta del Estado</h2>')
h = h.replace('<div class="corrw"><h3 style="margin:0 0 8px;font-size:14px;font-weight:700;color:var(--ink);text-transform:uppercase;letter-spacing:.05em">1 · Corredores críticos</h3>', '<div class="corrw">')
# Reordenar: esencial, 1 dónde, drones, 2 tendencia, 3 quién, 4 respuesta
secs = re.findall(r'  <section class="sec".*?</section>\n', h, flags=re.S)
assert len(secs) == 6, len(secs)
ess, dnd, tend, quien, dron, resp = secs
nuevo = ess + dnd + dron + tend + quien + resp
inicio = h.index(secs[0]); fin = h.index(secs[-1]) + len(secs[-1])
h = h[:inicio] + nuevo + h[fin:]
rep('  #pgD{break-before:page}', '  #pgD{break-before:page}\n  #pg2{break-before:page}')

# --- Holgura de impresión: texto nuevo más largo; se compacta el bloque @media print ---
rep('  h1{font-size:24px}', '  h1{font-size:24px}\n  .delta{font-size:10.5px;white-space:nowrap}\n  .kpi .l{font-size:12.5px}\n  .kpi .s{font-size:11px}\n  .cut{font-size:10.5px;white-space:normal}\n  .ctx{font-size:11px;gap:2px}\n  .crit li{font-size:12px;gap:6px}\n  .crit{gap:5px}\n  .watch{font-size:12px;padding:8px 12px}\n  .thr-hd{padding:10px 14px}\n  .dbar{margin-bottom:3px}\n  #dTop .it,.ev .it{padding:4px 0}\n  .pair{padding:2px 0!important}\n  .agg{font-size:11px;gap:3px}\n  .opk .kpi{padding:8px 12px}\n  #map{max-height:170px}\n  body{zoom:.8}\n  #pgD,#pg2,#pgO{break-before:auto!important}')

# --- Colores neutros para descensos (no presentar una variación corta como logro) ---
rep('.down{background:var(--lo-soft);color:var(--lo)}', '.down{background:var(--tint);color:var(--brand)}')
rep('.sig .ar.down{background:none;color:var(--lo)}', '.sig .ar.down{background:none;color:var(--brand)}')

# --- A1: corte y rezago ---
rep('· ${EV.length} hechos verificados`;', '· ${EV.length} hechos verificados · la última semana puede estar incompleta`;')

# --- H1, H6, H11: Lo esencial ---
old1 = h[h.index('  L.push(`<b>La actividad ${dir(t7,p7)}.</b>'):]
old1 = old1[:old1.index('\n')]
new1 = ('  const civW=sum(W14,"civ"), civP=sum(P14,"civ"), vbW=W14.filter(e=>e.mod==="Vehículo con explosivos").length, vbP=P14.filter(e=>e.mod==="Vehículo con explosivos").length;\n'
        '  const topW=[...W7].sort((a,b)=>(b.m+b.h)-(a.m+a.h))[0], topV=topW?topW.m+topW.h:0;\n'
        '  const cmod={}; W14.forEach(e=>{cmod[e.mod]=(cmod[e.mod]||0)+e.civ}); const cm=Object.entries(cmod).sort((a,b)=>b[1]-a[1])[0]||["",0];\n'
        '  const alza=[civW>civP?"los civiles muertos o heridos":null,vbW>vbP?"los vehículos con explosivos":null].filter(Boolean);\n'
        '  L.push(`<b>El número de hechos ${dir(t7,p7)}${alza.length?`, pero ${alza.join(" y ")} aumentan en los últimos 14 días`:""}.</b> En los últimos 7 días (${fmtD(ago(6))} a ${fmtD(CUT)}) se registraron ${t7} hechos y ${v7} víctimas, frente a ${p7} hechos y ${pv7} víctimas en los 7 días previos${topW&&v7>0&&topV/v7>=0.5?`; un solo hecho (${esc(topW.mpio)}, ${esc(topW.depto)}) aporta ${topV} de esas ${v7} víctimas`:""}. En los últimos 14 días frente a los 14 anteriores, los civiles muertos o heridos pasan de ${civP} a ${civW}${civW>civP&&cm[1]>0?` (${cm[1]} por ${cm[0].toLowerCase()})`:""} y los vehículos con explosivos de ${vbP} a ${vbW}. Con pocos hechos por semana, la comparación semanal es una señal débil.`);')
rep(old1, new1)
rep('${top3.map(d=>`${d.k} (${d.n})`).join(", ")} reúnen',
    '${top3.map(d=>`${d.k} (${d.n})`).join(", ")}${(()=>{const t=DL.slice(3).filter(d=>d.n===DL[2].n).map(d=>d.k);return t.length?` (${t.join(", ")} empata${t.length>1?"n":""} con ${DL[2].k})`:""})()} reúnen')
rep('<b>Los drones con explosivos son la amenaza prioritaria y GESEG la califica de riesgo extremo.</b> Están en ${dr} de los ${EV.length} hechos (${pct(dr,EV.length)}%)',
    '<b>Los drones con explosivos son la amenaza prioritaria y GESEG la califica de riesgo extremo (confianza moderada: la base es una muestra de hechos de alta visibilidad).</b> Están en ${dr} de los ${EV.length} hechos de la base (${pct(dr,EV.length)}%)')
rep('con ${g.m} muertos y ${g.h} heridos; ${esc(', 'con ${g.m} ${g.m===1?"muerto":"muertos"} y ${g.h} ${g.h===1?"herido":"heridos"}; ${esc(')
rep('la respuesta visible es baja frente a los atentados en ${R2.map(r=>r.d).join(", ")}', 'en ${R2.map(r=>r.d).join(", ")} la base registra pocas operaciones frente a los atentados')
rep('<span>Juicios calculados sobre la base verificada; no son estadística oficial</span>', '<span>Juicios calculados sobre la base verificada; no son estadística oficial. Confianza moderada en la concentración y la composición de los hechos; baja en la valoración de la respuesta del Estado</span>')

# --- Plurales (H12) ---
rep('${e.m?`<b>${e.m}</b> muertos<br>`:""}${e.h?`<b>${e.h}</b> heridos`:(e.m?"":"sin víctimas")}', '${e.m?`<b>${e.m}</b> ${e.m===1?"muerto":"muertos"}<br>`:""}${e.h?`<b>${e.h}</b> ${e.h===1?"herido":"heridos"}`:(e.m?"":"sin víctimas")}')
rep('${e.m?`<b>${e.m}</b> muertos<br>`:""}<b>${e.h}</b> heridos</div></div>`).join("");\n  const C=', '${e.m?`<b>${e.m}</b> ${e.m===1?"muerto":"muertos"}<br>`:""}<b>${e.h}</b> ${e.h===1?"herido":"heridos"}</div></div>`).join("");\n  const C=')

# --- H2, H7, H5: drones ---
rep('«Extremo»: amenaza dominante, letal, en expansión territorial y con afectación a civiles.</div>', '«Extremo»: amenaza dominante en la base, letal y con afectación a civiles. Criterio analítico de GESEG; confianza moderada.</div>')
rep('en promedio uno cada ${freq.toFixed(1).replace(".",",")} días, en ${deps.length} departamentos y ${mun} municipios.`',
    'en promedio uno cada ${freq.toFixed(1).replace(".",",")} días en la base, en ${deps.length} departamentos y ${mun} municipios. Cifras sobre la muestra documentada de hechos de alta visibilidad, no sobre el total nacional.`')
rep('[sum(D,"civ"),"civiles muertos o heridos",`en ${D.filter(e=>e.civ>0).length} ataques con drones`]', '[sum(D,"civ"),"civiles muertos o heridos por drones",`en ${D.filter(e=>e.civ>0).length} ataques, acumulado desde el 7 de agosto`]')
rep('La calificación de riesgo extremo descansa en la escala, la letalidad y la expansión de la amenaza, no en una variación de corto plazo.`',
    'La calificación de riesgo extremo descansa en la dominancia, la letalidad y la afectación a civiles, no en una variación de corto plazo; el periodo observado no permite afirmar que la amenaza se esté expandiendo.${(W14.filter(e=>e.mod==="Vehículo con explosivos").length>P14.filter(e=>e.mod==="Vehículo con explosivos").length)?" En las mismas dos semanas aumentaron los vehículos con explosivos y el daño a civiles (sección 2).":""}`')
rep('`<li>Cifras nacionales de terceros; no se suman a la base del observatorio.</li>`', '`<li><b>Cifras nacionales de terceros, con definiciones distintas; no se suman ni se comparan con la base del observatorio.</b></li>`')
rep('["Civiles muertos o heridos", null,"personas"]', '["Civiles muertos o heridos (todas las modalidades)", null,"personas"]')

# --- H3, H8, H9: respuesta del Estado ---
rep('["hi","Brecha alta"]', '["hi","Registro bajo"]'); rep('["mid","Brecha media"]', '["mid","Registro medio"]')
rep('["mid","Sin operaciones"]', '["mid","Sin operaciones registradas"]')
rep('<h3>Dónde golpean los grupos y dónde actúa el Estado</h3>', '<h3>Atentados y operaciones registradas en la base, por departamento</h3>')
rep('<span><i style="background:var(--brand)"></i>Operaciones del Estado</span>', '<span><i style="background:var(--brand)"></i>Operaciones registradas en la base</span>')
rep('Brecha</b> alta' if False else 'Brecha <b>alta</b>: 5 o más atentados y menos de 4 operaciones por cada 10. <b>Media</b>: menos de 8 por cada 10. <b>Proporcional</b>: 8 o más por cada 10.',
    'Registro <b>bajo</b>: 5 o más atentados y menos de 4 operaciones registradas por cada 10. <b>Medio</b>: menos de 8 por cada 10. <b>Proporcional</b>: 8 o más por cada 10. Compara dos muestras con criterios de selección distintos; no mide la respuesta total del Estado.')
rep('if(br.length) L.push(`<b>Brecha alta en ${br.map(r=>`${r.d} (${r.a} atentados, ${r.o} ${r.o===1?"operación":"operaciones"})`).join("; ")}.</b> Son territorios donde la presión armada supera la respuesta visible.`);',
    'if(br.length) L.push(`<b>Registro bajo de operaciones en ${br.map(r=>`${r.d} (${r.a} atentados, ${r.o} ${r.o===1?"operación":"operaciones"})`).join("; ")}.</b> En la base hay pocas operaciones frente a los atentados; no equivale a ausencia de respuesta del Estado, porque la base no recoge todas las operaciones.`);')
rep('<b>Disidencias FARC</b>: ${EV.filter(e=>e.grupo==="Disidencias FARC").length} atentados señalados y ${O.filter(o=>o.grupo==="Disidencias FARC").length} operaciones en su contra',
    '<b>Disidencias FARC</b>: ${EV.filter(e=>e.grupo==="Disidencias FARC").length} atentados señalados y ${O.filter(o=>o.grupo==="Disidencias FARC").length} operaciones registradas en su contra')
# Bombardeos: sin afirmaciones sensibles sin fuente
old_b = h[h.index('  L.push(`<b>Bombardeos bajo escrutinio:</b>'):]
old_b = old_b[:old_b.index('\n')]
new_b = ('  const MJ=(DATA.ops_agregados||[]).filter(a=>/^(Medicina Legal|Juez)/i.test(a.fuente)).slice(0,2);\n'
         '  L.push(`<b>Bombardeos:</b> ${bomb.length} bombardeos registrados con ${bomb.reduce((a,o)=>a+o.muertos,0)} muertos reportados.${MJ.length?" "+MJ.map(a=>`${esc(a.fuente.split(" (")[0])}${a.fecha_corte?` (${esc(a.fecha_corte)})`:""}: ${esc(clip(a.texto,230))}${a.url?` <a href="${esc(a.url)}">(enlace)</a>`:""}`).join(" "):""}`);')
rep(old_b, new_b)
old_j = h[h.index('  L.push(`<b>Poca judicialización de los atentados:</b>'):]
old_j = old_j[:old_j.index('\n')]
new_j = '  L.push(`<b>Operaciones vinculadas a atentados:</b> la base registra ${link.length} operaciones vinculadas a un atentado concreto. Para los atentados más recientes no hay capturas ni actuaciones judiciales conocidas en fuentes abiertas, algo esperable por el tiempo transcurrido; la base no mide judicialización.`);'
rep(old_j, new_j)
rep('const OPS=(DATA.ops||[]);', 'const OPS=(DATA.ops||[]);\nconst clip=(t,n)=>{t=String(t);if(t.length<=n)return t;const s=t.slice(0,n);const i=Math.max(s.lastIndexOf(". "),s.lastIndexOf("; "));if(i>n*0.5)return s.slice(0,i+1);const j=s.lastIndexOf(" ");return s.slice(0,j).replace(/[,;:\\s]+$/,"")+".";};')
rep('${esc(a.texto.length>230?a.texto.slice(0,227)+"…":a.texto)}', '${esc(clip(a.texto,260))}${a.url?` <a href="${esc(a.url)}">(enlace)</a>`:""}')

rep('C.map(([s,t])=>`<li><b>${esc(s)}:</b> ${esc(t)}.</li>`)', 'C.map(([s,t,u])=>`<li><b>${esc(s)}:</b> ${esc(t)}.${u?` <a href="${esc(u)}">(enlace)</a>`:""}</li>`)')
rep('.filter(([s,t])=>/drones/i.test(t)&&/Ideas para la Paz|Defensor/i.test(s))', '.filter(([s,t,u])=>/drones/i.test(t)&&/Ideas para la Paz|Defensor/i.test(s))')

out = base / "plantilla_v2"; out.mkdir(exist_ok=True)
(out / "template_ejecutivo_v2.html").write_text(h, encoding="utf-8")
print("ok", len(h))
