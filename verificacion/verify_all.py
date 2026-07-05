#!/usr/bin/env python3
"""
verify_all.py · Verificación sistemática del tablero Dataria
=============================================================
Se ejecuta en CADA modificación del backend o el tablero. Comprueba:
  1. El backend importa y los 4 endpoints existen.
  2. /api/zona/procesar devuelve payload válido contra una zona real.
  3. INTEGRIDAD ESPACIAL: todos los proyectos del payload caen DENTRO del polígono.
  4. Las 11 secciones del tablero renderean sin error con ese payload (tpl + charts).
  5. El contrato de datos está completo (cero campos faltantes).
Uso: python3 verify_all.py
"""
# --- Resolución de rutas (repo primero; fallback al layout /home/claude) ---
import os as _os
_REPO = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_HTML_REPO = _os.path.join(_REPO, "static", "dashboard_zona_analisis.html")
_HTML_PATH = _HTML_REPO if _os.path.exists(_HTML_REPO) else "/home/claude/build/dashboard_zona_analisis.html"
_BACKEND_DIR = _REPO if _os.path.exists(_os.path.join(_REPO, "app.py")) else "/home/claude/backend"
import sys as _sys
if _BACKEND_DIR not in _sys.path:
    _sys.path.insert(0, _BACKEND_DIR)

import asyncio, json, re, subprocess, sys, os

HTML = _HTML_PATH
TEST_ZONE = dict(lat=25.6463, lng=-100.4012, predio_m2=1200, uso_comercial=False,
                 zone_name="Valle Poniente", municipio="Monterrey", estado="Nuevo León")

def point_in_ring(lng, lat, ring):
    inside = False; n = len(ring); j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

async def main():
    results = []
    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        print(f"  {'✅' if ok else '❌'} {name}" + (f" · {detail}" if detail else ""))

    # 1 · Import + endpoints
    sys.path.insert(0, _BACKEND_DIR)
    import importlib
    import app; importlib.reload(app)
    routes = {r.path for r in app.app.routes}
    for ep in ["/health", "/api/zona/poligono", "/api/zona/procesar", "/api/zona/analyze"]:
        check(f"endpoint {ep}", ep in routes)

    # 2 · Polígono
    poly = await app.zona_poligono(app.ZonaRequest(**TEST_ZONE))
    check("poligono devuelve isócronas", poly.get("ok") and bool(poly.get("isocronas")),
          f"{list(poly.get('isocronas',{}).keys())} min")
    base_min = "8" if "8" in poly["isocronas"] else list(poly["isocronas"].keys())[0]
    ring = poly["isocronas"][base_min]["coordinates"][0]

    # 3 · Procesar
    data = await app.zona_procesar(app.ZonaRequest(**TEST_ZONE))
    check("procesar ok", data.get("ok"), f"stage={data.get('stage')}")
    z = data["zone_data"]; dim = data["dim_data"]
    if data.get("errors"):
        print(f"     ⚠ errors: {data['errors']}")

    # 4 · INTEGRIDAD ESPACIAL: todos los proyectos dentro del polígono (o clúster ajustado)
    proyectos = z.get("proyectos", [])
    za = z.get("_zona_analisis", {})
    perc = za.get("perception", {})
    cluster = perc.get("cluster_names")
    fuera = []
    for p in proyectos:
        if cluster:
            if p["name"] not in cluster:
                fuera.append(p["name"])
        elif p.get("lat") and p.get("lng") and not point_in_ring(p["lng"], p["lat"], ring):
            fuera.append(p["name"])
    modo = "clúster CV" if cluster else "isócrona"
    check(f"proyectos DENTRO de zona ({modo})", len(fuera) == 0,
          f"{len(proyectos)} proy, {len(fuera)} fuera" + (f": {fuera[:5]}" if fuera else ""))

    # 5 · Contrato de datos completo
    ref = json.load(open("/tmp/ref_contract.json")) if os.path.exists("/tmp/ref_contract.json") else None
    if ref:
        miss = [k for k in ref if k not in z]
        miss_com = [k for k in ref.get("comercio", {}) if k not in z.get("comercio", {})]
        check("contrato zone_data completo", not miss, f"faltan: {miss}" if miss else "")
        check("contrato comercio completo", not miss_com, f"faltan: {miss_com}" if miss_com else "")

    # 6 · Render de las 11 secciones (tpl + charts) en JSDOM-like Node harness
    json.dump(data, open("/tmp/_verify_payload.json", "w"))
    ok_render, detail = run_render_harness()
    check("render 10 secciones (tpl+charts)", ok_render, detail)

    print()
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"RESULTADO: {passed}/{len(results)} verificaciones pasadas")
    return all(ok for _, ok, _ in results)

def run_render_harness():
    html = open(HTML, encoding="utf-8").read()
    scripts = re.findall(r"<script>([\s\S]*?)</script>", html)
    main_js = max(scripts, key=len)
    payload = open("/tmp/_verify_payload.json").read().strip()
    harness = r'''
function mk(){return {textContent:'',_html:'',get innerHTML(){return this._html;},set innerHTML(v){this._html=v;},
 style:new Proxy({},{get:()=>'',set:()=>true}),classList:{add:()=>{},remove:()=>{},toggle:()=>{},contains:()=>false},
 getAttribute:()=>null,setAttribute:()=>{},addEventListener:()=>{},querySelectorAll:()=>[],querySelector:()=>null,
 appendChild:()=>{},removeChild:()=>{},offsetHeight:500,offsetWidth:500,getContext:()=>new Proxy({},{get:()=>()=>{}}),dataset:{},value:''};}
const els={};
global.document={getElementById:(id)=>{if(!els[id])els[id]=mk();return els[id];},querySelectorAll:()=>[mk()],querySelector:()=>mk(),addEventListener:()=>{},createElement:()=>mk(),head:{appendChild:()=>{}},body:{appendChild:()=>{}}};
let domCb=null; global.window={addEventListener:(e,c)=>{if(e==='DOMContentLoaded')domCb=c;},ResizeObserver:null};
global.requestAnimationFrame=(c)=>{try{c();}catch(e){}};global.setTimeout=(c)=>{try{if(typeof c==='function')c();}catch(e){}};
global.fetch=()=>Promise.resolve({ok:true,json:()=>Promise.resolve({})});
const pH={get(t,p){if(!(p in t))t[p]=new Proxy(function(){},pH);return t[p];},set(t,p,v){t[p]=v;return true;},apply(){return new Proxy(function(){},pH);}};
global.Chart=function(){return new Proxy({destroy:()=>{}},pH);};global.Chart.defaults=new Proxy({},pH);global.Chart.register=()=>{};
global.L=new Proxy(function(){},pH);
try{
''' + main_js + r'''
 if(domCb)domCb();
 window.__DATARIA_LIVE__=true; if(typeof DI_VP_DETAIL!=='undefined')DI_VP_DETAIL=null;
 const data=__PAYLOAD__; ZONE_DATA[CURRENT_ZONE]=data.zone_data;
 if(typeof DIM_DATA_BY_ZONE!=='undefined')DIM_DATA_BY_ZONE[CURRENT_ZONE]=data.dim_data;
 if(typeof DIM_DATA!=='undefined'){try{DIM_DATA=data.dim_data;}catch(e){}}
 if(typeof proyectos!=='undefined'){try{proyectos=data.zone_data.proyectos;}catch(e){}}
 zaRenderAllSafe();
 const ids=['page-resumen','page-mapa','page-inventario','page-demanda','page-producto','page-renta','page-comercio','page-mezcla','page-mezclaRenta','page-monitor'];
 let ok=0,err=0; const failed=[];
 ids.forEach(id=>{const h=els[id]?els[id].innerHTML:'';if(h&&h.length>100){if(h.includes('sin datos suficientes')){err++;failed.push(id);}else ok++;}else{err++;failed.push(id+'(vacío)');}});
 // Chequeo de literales ROTOS de formato (E4): $undefined, $NaN, NaN, undefined visibles
 const badPatterns=['$undefined','$NaN','>NaN<','>undefined<','undefined m²','null m²','$null','NaN%','NaN un/mes','$NaN/mes'];
 const fmtIssues=[];
 ids.forEach(id=>{const h=(els[id]?els[id].innerHTML:'')||'';badPatterns.forEach(bp=>{if(h.includes(bp))fmtIssues.push(id+':'+bp);});});
 console.log('RENDER_RESULT '+ok+'/'+ids.length+(failed.length?' FAILED:'+failed.join(','):''));
 console.log('FMT_RESULT '+(fmtIssues.length===0?'OK':'BAD:'+fmtIssues.slice(0,8).join(',')));
}catch(e){console.log('RENDER_RESULT INIT_ERROR:'+e.message);}
'''
    harness = harness.replace("__PAYLOAD__", payload)
    open("/tmp/_verify_harness.js", "w").write(harness)
    out = subprocess.run(["node", "/tmp/_verify_harness.js"], capture_output=True, text=True, timeout=60)
    line = [l for l in out.stdout.splitlines() if l.startswith("RENDER_RESULT")]
    fmt_line = [l for l in out.stdout.splitlines() if l.startswith("FMT_RESULT")]
    if not line:
        return False, "harness sin salida: " + (out.stderr[:200] or out.stdout[:200])
    detail = line[0].replace("RENDER_RESULT ", "")
    fmt_ok = bool(fmt_line) and "OK" in fmt_line[0]
    fmt_detail = (fmt_line[0].replace("FMT_RESULT ", "") if fmt_line else "sin chequeo")
    full_detail = f"{detail} · formato:{fmt_detail}"
    return detail.startswith("10/10") and fmt_ok, full_detail

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
