// Se ejecuta una sola vez: node src/make_geo.js <carpeta con world-atlas-2.0.2 y topojson-client-3.1.0 desempaquetados>
const fs = require("fs"), path = require("path");
const base = process.argv[2];
if (!base) { console.error("Uso: node src/make_geo.js <carpeta npm pack>"); process.exit(1); }
const topo = require(path.join(base, "topojson-client-3.1.0/package/dist/topojson-client.js"));
const world = JSON.parse(fs.readFileSync(path.join(base, "world-atlas-2.0.2/package/countries-10m.json"), "utf8"));
const ids = { 170: "COL", 862: "VEN", 218: "ECU", 604: "PER", 76: "BRA", 591: "PAN" };
const inBox = ([x, y]) => x >= -82 && x <= -66 && y >= -5 && y <= 13.5;
// Douglas-Peucker (tolerancia en grados) para aligerar el archivo
function dp(pts, t) {
  if (pts.length < 3) return pts;
  const [a, b] = [pts[0], pts[pts.length - 1]];
  let m = 0, i = 0;
  for (let k = 1; k < pts.length - 1; k++) {
    const [x, y] = pts[k], dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy;
    const u = l ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / l)) : 0;
    const d = Math.hypot(x - (a[0] + u * dx), y - (a[1] + u * dy));
    if (d > m) { m = d; i = k; }
  }
  return m > t ? dp(pts.slice(0, i + 1), t).slice(0, -1).concat(dp(pts.slice(i), t)) : [a, b];
}
const out = [];
for (const g of world.objects.countries.geometries) {
  const c = ids[+g.id];
  if (!c) continue;
  const f = topo.feature(world, g);
  const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
  const rings = [];
  for (const poly of polys) for (const ring of poly) {
    if (!ring.some(inBox)) continue;
    const r = [];
    for (const [x, y] of ring) {
      const p = [Math.round(x * 100) / 100, Math.round(y * 100) / 100];
      const l = r[r.length - 1];
      if (!l || l[0] !== p[0] || l[1] !== p[1]) r.push(p);
    }
    const q = dp(r, 0.02);
    if (q.length > 3) rings.push(q);
  }
  out.push({ c, p: rings });
}
fs.writeFileSync(path.join(__dirname, "..", "data", "geo.json"), JSON.stringify(out));
console.log(out.map(o => o.c + ":" + o.p.length).join(" "));
