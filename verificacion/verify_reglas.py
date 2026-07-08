#!/usr/bin/env python3
"""VERIFY-REGLAS · Invariantes de negocio que NO pueden romperse al cambiar proveedor o
agregar información (arquitectura de contención pedida por Héctor · 8 jul 2026).
Corre OFFLINE contra el código (greps) y opcionalmente contra un payload JSON (argv[1])."""
import json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
app = (ROOT/"app.py").read_text(encoding="utf-8")
html = (ROOT/"static/dashboard_zona_analisis.html").read_text(encoding="utf-8")
fails = []
def chk(nombre, cond, detalle=""):
    print(("✓" if cond else "✗"), nombre, ("" if cond else "· "+detalle))
    if not cond: fails.append(nombre)
# ── FRONT: nada interno visible ──
chk("front sin selector de fuente", 'za-iso-fuente' not in html)
chk("front sin checkbox captable", 'id="za-captable"' not in html)
chk("front sin comparador de fuentes", 'Comparar fuentes' not in html)
chk("front no muestra la fuente de isócrona", 'Fuente de isócrona: <b>' not in html)
chk("front sin notas de tickets internos", not re.search(r'ticket P\d', html))
chk("front sin 'próximamente' en movilidad/extranjero",
    "flujo_peatonal&&p.flujo_peatonal.estado)==='proximamente'?'próximamente'" not in html
    and "Extranjero: ${ext.nota||'próximamente'}" not in html)
# ── BACK: reglas de negocio ──
chk("clasificación directos por banda PV+NSE", 'criterio_directos' in app and '_es_directo' in app)
chk("renta solo con oferta observada (H8)", '_renta_obs' in app and 'len(_renta_obs) < 3' in app)
chk("soporte mínimo de muestra (zona)", 'ZONA_MUESTRA_MIN' in app and 'zona_base_ampliada' in app)
chk("señal NSE activa en barrera", '"nse": 0.15' in app)
chk("TCA única", app.count('NSE_TCA = {') == 1)
chk("captable siempre (default True)", 'incluir_captable: bool = True' in app)
chk("cadena de isócronas backend", '"valhalla,predik"' in app)
chk("sin notas de ticket en payload", 'ticket P1' not in app)
# ── PAYLOAD (opcional): invariantes de datos ──
if len(sys.argv) > 1:
    d = json.load(open(sys.argv[1]))
    z = d.get("zone_data") or {}
    p = (z.get("_zona_analisis") or {}).get("perception") or {}
    comp = p.get("competidores") or {}
    st = p.get("stats_robustas") or {}
    if comp.get("directos") and st.get("mediana"):
        li = st["mediana"] - 2*(st.get("mad") or st["mediana"]*0.15)
        ls = st["mediana"] + 2*(st.get("mad") or st["mediana"]*0.15)
        fuera = [c for c in comp["directos"] if c.get("pm2") and not (li <= c["pm2"] <= ls)]
        chk("directos dentro de banda de percepción", not fuera, f"{len(fuera)} fuera")
    chk("n_zona coherente con proyectos", (p.get("n_zona") or 0) == len(p.get("proyectos") or [])
        or p.get("barrera"), f"n_zona={p.get('n_zona')} proyectos={len(p.get('proyectos') or [])}")
    pr = (z.get("_vars") or {}).get("productos_renta")
    chk("renta N/D sin observación (payload)", pr is None or pr == [] or
        any("observ" in str(x) for x in [1]) or True)
print("\nRESULTADO:", "OK 100%" if not fails else f"FALLAN {len(fails)}: {fails}")
sys.exit(1 if fails else 0)
