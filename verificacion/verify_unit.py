#!/usr/bin/env python3
"""VERIFY-UNIT · Pruebas unitarias con MOCKS de las reglas del 8 jul 2026 (tarde):
  1. CAPTABLE-V3 · desagregación IPF: los totales municipales se conservan EXACTOS.
  2. ZONA-RÍO · clip Sutherland-Hodgman: la zona morada SIEMPRE ⊆ isócrona y ⊆ casco.
  3. RENTA-ANCLA · pm² de renta solo dentro de la banda P10–P90 observada.
Corre OFFLINE (sin red). Salida: OK/FALLA por caso y exit code."""
import math, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import app as A

fails = []


def chk(nombre, cond, detalle=""):
    print(("✓" if cond else "✗"), nombre, ("" if cond else "· " + str(detalle)[:160]))
    if not cond:
        fails.append(nombre)


# ════════ 1 · CAPTABLE-V3 · IPF conserva totales municipales EXACTOS ════════
PIN = (-100.44849, 25.65766)
corona_rows = [
    # (Municipio, NSE, hogares, población) — masa real simulada del XLSX
    {"CVEGEO": "190190001", "Municipio": "Santa Catarina",
     "XI_Nivel socioeconómico por ingreso": "C+", "Hogares totales 2026": 1200,
     "Población total 2026": 4100, "IXH": 52000},
    {"CVEGEO": "190190002", "Municipio": "Santa Catarina",
     "XI_Nivel socioeconómico por ingreso": "C", "Hogares totales 2026": 800,
     "Población total 2026": 2900, "IXH": 30000},
    {"CVEGEO": "190260001", "Municipio": "Monterrey",
     "XI_Nivel socioeconómico por ingreso": "B", "Hogares totales 2026": 2500,
     "Población total 2026": 8000, "IXH": 120000},
    {"CVEGEO": "190480001", "Municipio": "García",
     "XI_Nivel socioeconómico por ingreso": "D+", "Hogares totales 2026": 3000,
     "Población total 2026": 11000, "IXH": 14000},   # García SIN flujo censal en el mock
]
geo_corona = [
    {"nse_txt": "C+", "lng": PIN[0] + 0.05, "lat": PIN[1] + 0.02},
    {"nse_txt": "C",  "lng": PIN[0] + 0.08, "lat": PIN[1] - 0.03},
    {"nse_txt": "B",  "lng": PIN[0] - 0.10, "lat": PIN[1] + 0.06},
    {"nse_txt": "D+", "lng": PIN[0] + 0.15, "lat": PIN[1] + 0.10},
]
sal = {"SANTA CATARINA": 12345.6, "MONTERREY": 98765.4}   # marginales censales del mock

v3 = A._captable_v3_ipf(corona_rows, geo_corona, sal, PIN[0], PIN[1])
chk("v3 corre con insumos mínimos", v3 is not None)
if v3:
    por_muni = {}
    for c in v3["celdas"]:
        if c.get("commuters_dia") is not None:
            m = A._norm_nombre(c["municipio"])
            por_muni[m] = por_muni.get(m, 0.0) + c["commuters_dia"]
    for m, esperado in {"SANTA CATARINA": 12345.6, "MONTERREY": 98765.4}.items():
        chk(f"IPF conserva EXACTO el total municipal de {m}",
            abs(por_muni.get(m, 0.0) - esperado) < 1e-6,
            f"obtenido={por_muni.get(m)} esperado={esperado}")
    chk("municipio SIN flujo censal NO recibe commuters (no se inventa)",
        "GARCIA" not in por_muni and all(
            c.get("commuters_dia") is None for c in v3["celdas"]
            if A._norm_nombre(c["municipio"]) == "GARCIA"))
    chk("total = suma de marginales anclados",
        abs(v3["total_commuters_dia"] - (12345.6 + 98765.4)) < 1e-6,
        v3["total_commuters_dia"])
    # dentro de un municipio, la celda con más masa×fricción recibe más commuters
    sc = [c for c in v3["celdas"] if A._norm_nombre(c["municipio"]) == "SANTA CATARINA"]
    cmas = max(sc, key=lambda c: c["commuters_dia"])
    chk("reparto intra-municipio sigue masa×fricción (C+ 1200 hog > C 800 hog)",
        cmas["nse"] == "C+", [(c["nse"], round(c["commuters_dia"], 1)) for c in sc])

# sin ancla municipal → None (v3 no aplica, se declara lo anterior)
chk("sin flujos censales → v3 None", A._captable_v3_ipf(corona_rows, geo_corona, {}, *PIN) is None)
chk("sin corona XLSX → v3 None", A._captable_v3_ipf([], geo_corona, sal, *PIN) is None)
chk("sin geometría KMZ → v3 None (sin fricción real no se modela)",
    A._captable_v3_ipf(corona_rows, [], sal, *PIN) is None)

# ════════ 2 · ZONA-RÍO · clip Sutherland-Hodgman: zona ⊆ isócrona y ⊆ casco ════════
def _en_ring(p, ring, tol=1e-9):
    """Dentro del anillo o a distancia ≤ tol de una arista (los vértices del clip caen
    sobre la frontera por construcción)."""
    if A._point_in_ring(p[0], p[1], ring):
        return True
    for i in range(len(ring) - 1):
        ax, ay = ring[i]
        bx, by = ring[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            continue
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        qx, qy = ax + t * dx, ay + t * dy
        if (p[0] - qx) ** 2 + (p[1] - qy) ** 2 <= tol:
            return True
    return False


# isócrona CÓNCAVA en "L" (sujeto) y directos cuyo casco se sale de la L
iso_L = [[0, 0], [4, 0], [4, 1.5], [1.5, 1.5], [1.5, 4], [0, 4], [0, 0]]
directos = [[0.5, 0.5], [3.5, 0.5], [0.5, 3.5], [3.2, 1.2]]   # el casco cruza la muesca de la L
hull = A._convex_hull(directos)
clip = A._clip_ring_sutherland_hodgman(iso_L, hull)
chk("clip produce anillo cerrado ≥4 vértices", len(clip) >= 4 and clip[0] == clip[-1], len(clip))
if clip:
    chk("TODOS los vértices del clip ⊆ isócrona", all(_en_ring(p, iso_L) for p in clip[:-1]))
    chk("TODOS los vértices del clip ⊆ casco de directos", all(_en_ring(p, hull) for p in clip[:-1]))
    a_clip, a_hull, a_iso = (A._area_ring_km2(clip), A._area_ring_km2(hull), A._area_ring_km2(iso_L))
    chk("área clip < área casco (la muesca de la isócrona recorta)", a_clip < a_hull,
        f"clip={a_clip} hull={a_hull}")
    chk("área clip ≤ área isócrona", a_clip <= a_iso, f"clip={a_clip} iso={a_iso}")
    # muestreo interior: ningún punto del clip fuera de la isócrona (anti-cruce de río)
    xs = [p[0] for p in clip[:-1]]; ys = [p[1] for p in clip[:-1]]
    malos = []
    for i in range(25):
        for j in range(25):
            x = min(xs) + (max(xs) - min(xs)) * (i + 0.5) / 25
            y = min(ys) + (max(ys) - min(ys)) * (j + 0.5) / 25
            if A._point_in_ring(x, y, clip) and not A._point_in_ring(x, y, iso_L):
                malos.append((round(x, 3), round(y, 3)))
    chk("ningún punto interior del clip cae FUERA de la isócrona", not malos, malos[:4])

# casco totalmente dentro → clip ≈ casco (tolerancia RELATIVA 0.1%: _area_ring_km2 usa
# lat0 = promedio de latitudes de CADA anillo → proyecciones ligeramente distintas)
hull_in = A._convex_hull([[0.3, 0.3], [1.2, 0.3], [0.8, 1.2]])
clip_in = A._clip_ring_sutherland_hodgman(iso_L, hull_in)
chk("casco interior queda intacto (área igual)",
    clip_in and abs(A._area_ring_km2(clip_in) - A._area_ring_km2(hull_in))
    / A._area_ring_km2(hull_in) < 1e-3,
    (A._area_ring_km2(clip_in or []), A._area_ring_km2(hull_in)))
# casco totalmente FUERA → intersección vacía
hull_out = A._convex_hull([[10, 10], [12, 10], [11, 12]])
chk("casco fuera de la isócrona → [] (no se inventa zona)",
    A._clip_ring_sutherland_hodgman(iso_L, hull_out) == [])
# degenerado: <3 directos no forma casco
chk("<3 puntos no forman casco (regla ≥3 directos)", A._convex_hull([[0, 0], [1, 1]]) == [])

# ════════ 3 · RENTA-ANCLA · pm² solo dentro de la banda observada ════════
def _ft_renta(vals):
    return [{"attributes": {"F___M2": v, "ÁREA_PRIVATIVA": 100,
                            "F____UNIDAD_MENSUAL": v * 100}} for v in vals]


seg_base = {"status": "atendido", "aplicable": True, "bucket": "2.0–3.0M",
            "mkt_renta": 100, "mkt_total": 400, "nuevas_fam": 60}
seg_ok = dict(seg_base, NSE="B", val_min=2.0e6, val_max=3.0e6,
              rent_min=16000, rent_max=22000)     # pm²_seg ≈ 19000/62 ≈ 306 → EN banda
seg_fuera = dict(seg_base, NSE="D", val_min=0.30e6, val_max=0.45e6,
                 rent_min=1500, rent_max=2500)    # pm²_seg ≈ 2000/47 ≈ 43 → FUERA de banda
obs = _ft_renta([200, 210, 210, 240, 260, 300, 420])   # banda observada p10–p90

prods = A.derive_productos_renta(obs, [seg_ok, seg_fuera])
p_ok = next((p for p in prods if "B" in p["seg_renta"]), None)
p_f = next((p for p in prods if "D" in p["seg_renta"]), None)
chk("renta: segmento dentro de banda publica pm² interpolado", p_ok and p_ok["pm2_renta"] != "N/D",
    p_ok and p_ok["pm2_renta"])
if p_ok:
    v = float(p_ok["pm2_renta"].replace("$", "").replace(",", "").split("/")[0])
    st = A._stats_robustas([200, 210, 210, 240, 260, 300, 420])
    chk("renta: pm² publicado DENTRO de P10–P90 observado",
        st["p10"] <= v <= st["p90"], f"{v} vs [{st['p10']},{st['p90']}]")
chk("renta: segmento fuera de banda → N/D y no aplicable",
    p_f and p_f["pm2_renta"] == "N/D" and p_f["aplicable"] is False
    and p_f["recomendado"] is False, p_f and (p_f["pm2_renta"], p_f["aplicable"]))
chk("renta: <3 observaciones → [] (H8 intacto)",
    A.derive_productos_renta(_ft_renta([250, 300]), [seg_ok]) == [])
chk("renta: sin ft_renta → [] (H8 intacto)", A.derive_productos_renta([], [seg_ok]) == [])

print("\nRESULTADO:", "OK 100%" if not fails else f"FALLAN {len(fails)}: {fails}")
sys.exit(1 if fails else 0)
