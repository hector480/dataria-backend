#!/usr/bin/env python3
"""
Verificación de funciones INTERACTIVAS (bloque D de la lista):
  D1 sliders de Producto (updateSensi)
  D2 Crea tu mezcla VENTA (todos los modos: periodo, recomendacion, unidades, perfil, manual, sensibilidad)
  D3 Crea tu mezcla RENTA (todos los modos)
  D4 Monitorea tu proyecto (monitorImport + renderMonitorAnalysis)
  D5 sliders de Renta (updateRenta)
Invoca cada función con datos EN VIVO y verifica: no lanza error, no produce N/D/NaN rotos.
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

import asyncio, subprocess, json, sys, importlib
import app as _app

PRSP = "https://payment-system-prsp.onrender.com"

async def get_payload():
    importlib.reload(_app)
    req = _app.ZonaRequest(lat=25.66412, lng=-100.28454, predio_m2=1200,
                           zone_name="Monterrey Contry", municipio="Monterrey", estado="Nuevo León")
    await _app.zona_poligono(req)
    d = await _app.zona_procesar(req)
    return d

def build_harness(main_js, payload_json):
    return r'''
function mk(){return {textContent:'',_html:'',get innerHTML(){return this._html;},set innerHTML(v){this._html=v;},
 style:new Proxy({},{get:()=>'',set:()=>true}),classList:{add:()=>{},remove:()=>{},toggle:()=>{},contains:()=>false},
 getAttribute:()=>null,setAttribute:()=>{},addEventListener:()=>{},querySelectorAll:()=>[],querySelector:()=>null,
 appendChild:()=>{},removeChild:()=>{},offsetHeight:500,offsetWidth:500,getContext:()=>new Proxy({},{get:()=>()=>{}}),
 dataset:{},value:'0',checked:false,focus:()=>{},closest:()=>null,remove:()=>{}};}
const els={};
global.document={getElementById:(id)=>{if(!els[id])els[id]=mk();return els[id];},querySelectorAll:()=>[mk()],
 querySelector:()=>mk(),addEventListener:()=>{},createElement:()=>mk(),head:{appendChild:()=>{}},body:{appendChild:()=>{}}};
let domCb=null; global.window={addEventListener:(e,c)=>{if(e==='DOMContentLoaded')domCb=c;},ResizeObserver:null};
global.requestAnimationFrame=(c)=>{try{c();}catch(e){}};global.setTimeout=(c)=>{try{if(typeof c==='function')c();}catch(e){}};
global.fetch=()=>Promise.resolve({ok:true,json:()=>Promise.resolve({})});
global.alert=()=>{};
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

 const results=[];
 function tryFn(name, fn){
   try{ fn(); 
     // recolectar el HTML de todas las secciones de mezcla/monitor para chequear N/D roto
     let html='';
     ['page-mezcla','page-mezclaRenta','page-monitor','page-producto','page-renta'].forEach(id=>{if(els[id])html+=(els[id].innerHTML||'');});
     const bad=['$undefined','$NaN','>NaN<','>undefined<','undefined m²','null m²','$null','NaN%','NaN un/mes'];
     const found=bad.filter(b=>html.includes(b));
     results.push(name+': '+(found.length?'FMT_BAD['+found.join(',')+']':'OK'));
   }catch(e){ results.push(name+': ERROR '+e.message); }
 }

 // D2 · Mezcla VENTA · catálogo y modos
 const cat = (typeof getFullProductCatalog==='function')?getFullProductCatalog():[];
 results.push('catalogo_venta: '+cat.length+' productos');
 // llenar _manualMix con 2 productos reales del catálogo
 if(typeof _manualMix!=='undefined' && cat.length){
   _manualMix=[{tipo:cat[0].tipo,units:50}];
   if(cat[1])_manualMix.push({tipo:cat[1].tipo,units:30});
 }
 tryFn('D2.periodo', ()=>renderMixPeriodo());
 tryFn('D2.recomendacion', ()=>renderMixRecomendacion());
 tryFn('D2.unidades', ()=>renderMixUnidades());
 tryFn('D2.perfil', ()=>renderMixPerfil());
 tryFn('D2.manual', ()=>renderManualMix());
 tryFn('D2.sensibilidad', ()=>renderMixSensitivity());

 // D3 · Mezcla RENTA
 const catR=(typeof getDemandDrivenRentaProducts==='function')?getDemandDrivenRentaProducts(1.0):[];
 results.push('catalogo_renta: '+catR.length+' productos');
 if(typeof _manualMixRenta!=='undefined' && catR.length){
   _manualMixRenta=[{tipo:catR[0].tipo,units:40}];
   if(catR[1])_manualMixRenta.push({tipo:catR[1].tipo,units:20});
 }
 tryFn('D3.periodo', ()=>renderMixRentaPeriodo());
 tryFn('D3.recomendacion', ()=>renderMixRentaRecomendacion());
 tryFn('D3.unidades', ()=>renderMixRentaUnidades());
 tryFn('D3.perfil', ()=>renderMixRentaPerfil());
 tryFn('D3.manual', ()=>renderMixRentaManual());
 tryFn('D3.sensibilidad', ()=>renderMixRentaSensitivity());

 // D1 · sliders Producto
 if(typeof updateSensi==='function') tryFn('D1.updateSensi', ()=>updateSensi());
 // D5 · sliders Renta
 if(typeof updateRenta==='function') tryFn('D5.updateRenta', ()=>updateRenta());

 // D4 · Monitor (importar mezcla venta y analizar)
 if(typeof monitorImport==='function') tryFn('D4.import_venta', ()=>monitorImport('venta'));
 if(typeof renderMonitorAnalysis==='function') tryFn('D4.analysis', ()=>renderMonitorAnalysis());

 console.log('INTERACTIVE_RESULTS_START');
 results.forEach(r=>console.log('  '+r));
 console.log('INTERACTIVE_RESULTS_END');
}catch(e){console.log('INIT_ERROR:'+e.message+' | '+e.stack);}
'''.replace("__PAYLOAD__", payload_json)

async def main():
    payload = await get_payload()
    # extraer el JS principal del tablero
    html = open(_HTML_PATH).read()
    import re
    scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
    main_js = max(scripts, key=len)  # el bloque JS más grande
    harness = build_harness(main_js, json.dumps(payload))
    open("/tmp/_verify_interactive.js", "w").write(harness)
    out = subprocess.run(["node", "/tmp/_verify_interactive.js"], capture_output=True, text=True, timeout=90)
    print(out.stdout)
    if out.stderr.strip():
        print("STDERR:", out.stderr[:500])

if __name__ == "__main__":
    asyncio.run(main())
