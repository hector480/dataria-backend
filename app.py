"""
Dataria · Backend de orquestación en vivo (archivo único)
==========================================================
Versión combinada para despliegue simple: dpo + assembler + main en un solo app.py.
Endpoints:  GET /health   ·   POST /api/zona/analyze
"""

# ╔══════════════ SECCIÓN 1: DERIVACIÓN DIGO/DPO (dpo) ══════════════╗
import statistics
from typing import Optional, List, Dict, Any

# Banda de plausibilidad física (m²)
M2_MIN, M2_MAX = 25, 500
CV_BARRERA = 0.30      # umbral de "barrera amplia" de percepción de valor
COBERTURA_MIN = 0.20   # 20% mínimo de cobertura de isócrona sobre clúster alto valor


# ──────────────────────── Helpers numéricos N/D-safe ────────────────────────
def _num(v) -> Optional[float]:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        # -1 es marcador de "no disponible" en los datasets de origen
        if v == -1:
            return None
        return float(v)
    return None


def _price(v) -> Optional[float]:
    """Precio de unidad plausible: > 100k. Filtra -1, 0 y placeholders."""
    n = _num(v)
    return n if (n is not None and n > 100000) else None


def _pm2(v) -> Optional[float]:
    """Precio por m² plausible: > 1000."""
    n = _num(v)
    return n if (n is not None and n > 1000) else None


def _sum(rows: List[Dict], key: str) -> Optional[float]:
    vals = [_num(r.get(key)) for r in rows]
    vals = [v for v in vals if v is not None]
    return sum(vals) if vals else None


def _wavg(rows: List[Dict], key: str, weight: str) -> Optional[float]:
    num = 0.0
    den = 0.0
    for r in rows:
        v = _num(r.get(key)); w = _num(r.get(weight))
        if v is not None and w is not None and w > 0:
            num += v * w; den += w
    return (num / den) if den > 0 else None


# ──────────────────────── Isócrona por tamaño/uso ────────────────────────
def isochrone_profile(predio_m2: Optional[float], comercial: bool) -> Dict[str, Any]:
    """Replica exacta de la regla del tablero (sección Zona de análisis)."""
    if comercial or (predio_m2 is not None and predio_m2 > 35000):
        return {"key": "p24seg", "label": "24 min (segmentada 8/14)", "minutos": [8, 14, 24], "principal": 24}
    if predio_m2 is None:
        # Sin tamaño y sin comercial: default conservador 8 min
        return {"key": "p8", "label": "8 min", "minutos": [8], "principal": 8}
    if predio_m2 < 1500:
        return {"key": "p8", "label": "8 min", "minutos": [8], "principal": 8}
    if predio_m2 < 15000:
        return {"key": "p14", "label": "14 min", "minutos": [8, 14], "principal": 14}
    if predio_m2 <= 35000:
        return {"key": "p18", "label": "18 min", "minutos": [8, 18], "principal": 18}
    return {"key": "p24seg", "label": "24 min (segmentada 8/14)", "minutos": [8, 14, 24], "principal": 24}


# ──────────────────────── Geometría: punto en anillo ────────────────────────
def _point_in_ring(lng: float, lat: float, ring: List[List[float]]) -> bool:
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _row_coords(row: Dict):
    """Extrae (lng, lat) de un registro VVV (geometry o X_coor/Y_coor)."""
    a = row.get("attributes", {})
    g = row.get("geometry", {})
    lat = g.get("y") if isinstance(g.get("y"), (int, float)) else a.get("Y_coor")
    lng = g.get("x") if isinstance(g.get("x"), (int, float)) else a.get("X_coor")
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        return (lng, lat)
    return (None, None)


def filter_vvv_by_polygon(vvv: Dict, ring: List[List[float]]) -> Dict:
    """
    Filtra los datasets de VVV (resumen, ft, pagos) dejando SOLO los registros cuyo
    punto cae DENTRO del polígono de la isócrona. Garantía de integridad espacial:
    el backend de ArcGIS puede usar bounding box; aquí imponemos el polígono exacto.
    Universal para cualquier zona de México.
    """
    if not vvv or "datasets" not in vvv:
        return vvv
    ds = vvv["datasets"]
    resumen = ds.get("resumen", [])
    ft = ds.get("ft", [])
    pagos = ds.get("pagos", [])

    # 1. Proyectos (resumen) dentro del polígono → set de nombres válidos
    resumen_in = []
    proyectos_validos = set()
    for row in resumen:
        lng, lat = _row_coords(row)
        if lng is not None and _point_in_ring(lng, lat, ring):
            resumen_in.append(row)
            nombre = row.get("attributes", {}).get("PROYECTO")
            if nombre:
                proyectos_validos.add(nombre)

    # 2. ft (tipologías): dentro del polígono por coords propias O pertenece a proyecto válido
    ft_in = []
    for t in ft:
        lng, lat = _row_coords(t)
        nombre = t.get("attributes", {}).get("PROYECTO")
        if lng is not None and _point_in_ring(lng, lat, ring):
            ft_in.append(t)
        elif nombre and nombre in proyectos_validos:
            ft_in.append(t)

    # 3. pagos: solo de proyectos válidos
    pagos_in = [p for p in pagos if p.get("attributes", {}).get("PROYECTO") in proyectos_validos] \
        if proyectos_validos else pagos

    out = dict(vvv)
    out["datasets"] = {"resumen": resumen_in, "ft": ft_in, "pagos": pagos_in}
    out["_spatial_filter"] = {
        "resumen_in": len(resumen_in), "resumen_total": len(resumen),
        "ft_in": len(ft_in), "ft_total": len(ft),
    }
    return out


# ──────────────────────── Percepción de valor + ajuste de zona ────────────────────────
def value_perception_adjust(resumen: List[Dict], base_ring: List[List[float]]) -> Dict[str, Any]:
    """
    Capa de percepción de valor sobre la isócrona base (8 min) y ajuste de
    zona de influencia real por uniformidad de precios (CV).
    """
    proyectos = []
    for row in resumen:
        a = row.get("attributes", {})
        g = row.get("geometry", {})
        pm2 = _num(a.get("F__M2_PROM"))
        la = _num(g.get("y")) if g.get("y") is not None else _num(a.get("Y_coor"))
        ln = _num(g.get("x")) if g.get("x") is not None else _num(a.get("X_coor"))
        if pm2 is not None and pm2 > 1000 and la is not None and ln is not None:
            proyectos.append({"name": a.get("PROYECTO") or a.get("Nombre") or "N/D",
                              "pm2": pm2, "lat": la, "lng": ln})

    dentro = [p for p in proyectos if _point_in_ring(p["lng"], p["lat"], base_ring)]
    precios = [p["pm2"] for p in dentro]

    out = {
        "n_total": len(dentro), "n_zona": len(dentro),
        "media": None, "sd": None, "cv": None,
        "barrera": False, "metodo": "isocrona", "cobertura_pct": 100,
        "motivo": None, "proyectos": dentro,
        # Nombres de proyectos que definen la ZONA AJUSTADA (para filtrar inventario/KPIs/mapa).
        # None = sin recorte (usar todos los de la isócrona).
        "cluster_names": None,
    }
    if len(precios) < 3:
        out["motivo"] = "Muestra insuficiente para clúster · se mantiene la isócrona"
        return out

    media = statistics.mean(precios)
    sd = statistics.pstdev(precios)
    cv = sd / media if media > 0 else None
    out.update(media=media, sd=sd, cv=cv)

    if cv is None or cv <= CV_BARRERA:
        return out  # uniforme → zona = isócrona

    # Barrera amplia → recortar a clúster de alto valor (precio >= media)
    out["barrera"] = True
    altos = [p for p in dentro if p["pm2"] >= media]
    if len(altos) < 2:
        out["motivo"] = "Clúster de alto valor sin masa suficiente · se mantiene la isócrona"
        return out

    cobertura = len(altos) / max(len(dentro), 1)
    out["cobertura_pct"] = round(cobertura * 100)
    if cobertura >= COBERTURA_MIN:
        out["metodo"] = "cluster_alto_valor"
        out["n_zona"] = len(altos)
        out["proyectos"] = altos
        # Restringir el inventario al clúster de alto valor
        out["cluster_names"] = set(p["name"] for p in altos if p.get("name") and p["name"] != "N/D")
    else:
        out["motivo"] = "Cobertura del clúster de alto valor < 20% · no se recorta"
    return out


# ──────────────────────── Demografía base (de AGEBs) ────────────────────────
# Mapeo de NSE INEGI a las clases del tablero
NSE_MAP = {"A": "A", "B": "B", "C+": "C+", "C": "C", "D+": "D+", "D": "D", "E": "E"}

# Rangos de ingreso MENSUAL por hogar (estándar AMAI/DIGO · MXN). Universal para todo México.
NSE_INCOME_BANDS = [
    ("A",  200000, None),
    ("B",   90000, 199999),
    ("C+",  40000, 89999),
    ("C",   17000, 39999),
    ("D+",  10000, 16999),
    ("D",    4000, 9999),
    ("E",       0, 3999),
]


def _ageb_ixh_mensual(r: Dict) -> Optional[float]:
    """Ingreso por hogar MENSUAL del AGEB. IXH (C95) es anual → /12. Fallback: Ingresos totales / hogares / 12."""
    ixh = _num(r.get("IXH"))
    if ixh is not None and ixh > 0:
        return ixh / 12.0
    ing = _num(r.get("Ingresos totales 2026"))
    hog = _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020"))
    if ing is not None and hog and hog > 0:
        return ing / hog / 12.0
    return None


def _ageb_vcasa(r: Dict) -> Optional[float]:
    """Valor de vivienda del AGEB (campo 'V CASAS')."""
    return _num(r.get("V CASAS")) or _num(r.get("V_CASAS")) or _num(r.get("V_CASA"))


def classify_nse_by_income(ixh_mensual: Optional[float]) -> Optional[str]:
    """Clasifica el NSE de un AGEB por su ingreso mensual real (AMAI). Universal."""
    if ixh_mensual is None:
        return None
    for nse, lo, hi in NSE_INCOME_BANDS:
        if ixh_mensual >= lo and (hi is None or ixh_mensual <= hi):
            return nse
    return "E"


def ageb_nse(r: Dict) -> Optional[str]:
    """
    NSE del AGEB tomado DIRECTAMENTE de la capa de NSE de ArcGIS (base Prosperia):
    campo 'NSE PER' (NSE por persona) con respaldo 'XI_Nivel socioeconómico por ingreso'.
    Estas capas ya vienen clasificadas por la fuente; no se recalcula por bandas de ingreso.
    Universal para todo México: la clasificación la provee ArcGIS, no un heurístico local.
    """
    cls = r.get("NSE PER") or r.get("XI_Nivel socioeconómico por ingreso")
    if cls:
        cls = str(cls).strip()
        # Normalizar variantes de etiqueta a las claves canónicas
        if cls in NSE_MAP:
            return cls
        # variantes comunes: "C plus" → "C+", "D plus" → "D+"
        cls2 = cls.replace(" plus", "+").replace("Plus", "+").replace(" ", "")
        if cls2 in NSE_MAP:
            return cls2
    return None


def _nse_percepcion_valor(ft: List[Dict], pm2_min: int = 20000) -> Optional[str]:
    """
    PERCEPCIÓN DE VALOR de la zona = NSE del PRECIO MEDIANO de la oferta vertical real (VVV).
    Regla DIGO: la isócrona define la ZONA, pero la percepción de valor define el VALOR del
    producto. El precio mediano de lo que realmente se ofrece/vende indica para qué percepción
    se construye, independiente de la demografía de la isócrona. Devuelve la clave NSE o None.
    """
    if not ft:
        return None
    precios_m = []
    for t in ft:
        a = t.get("attributes", {})
        precio = _price(a.get("F____UNIDAD"))
        pm2v = _pm2(a.get("F___M2"))
        if precio and pm2v and pm2v >= pm2_min:   # solo oferta vertical plausible
            precios_m.append(precio / 1e6)
    if not precios_m:
        return None
    mediano_m = statistics.median(precios_m)
    bands = [("A", 6.8, None), ("B", 3.05, 6.8), ("C+", 1.35, 3.05), ("C", 0.577, 1.35),
             ("D+", 0.349, 0.577), ("D", 0.2, 0.349), ("E", 0, 0.2)]
    for nse, lo, hi in bands:
        if mediano_m >= lo and (hi is None or mediano_m < hi):
            return nse
    return None


def derive_demografia(agebs: List[Dict], ft: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Agrega los AGEBs a KPIs demográficos de zona. Ausencia => None.
    Si se pasa `ft` (oferta vertical VVV), el NSE dominante mostrado refleja la PERCEPCIÓN DE
    VALOR (el NSE para el que realmente se construye), que predomina sobre la demografía cruda
    de la isócrona cuando hay oferta vertical observada."""
    if not agebs:
        return {
            "population": None, "households": None, "tca": None,
            "personas_hogar": None, "ingreso_hogar": None, "ingreso_total_anual": None,
            "nse": {}, "nse_dominante": None, "tenencia": {}, "hog_renta": None,
            "edad_grupos": None,
        }

    pob = _sum(agebs, "Población total 2026") or _sum(agebs, "POB1")
    hog = _sum(agebs, "Hogares totales 2026") or _sum(agebs, "Hogares totales 2020")
    ing_total = _sum(agebs, "Ingresos totales 2026")
    personas_hogar = _wavg(agebs, "Personas por hogar 2026", "Hogares totales 2026")

    # TCA: tasa de crecimiento anual ponderada por población (decimal)
    tca_pct = _wavg(agebs, "Tasa de crecimiento anual", "POB1")
    tca = round(tca_pct / 100.0, 4) if tca_pct is not None else None

    # Ingreso por hogar MENSUAL ponderado (IXH es anual → /12)
    ixh_vals = []
    for r in agebs:
        ixh_m = _ageb_ixh_mensual(r)
        h = _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020"))
        if ixh_m is not None and h:
            ixh_vals.append((ixh_m, h))
    if ixh_vals:
        num = sum(v * w for v, w in ixh_vals); den = sum(w for _, w in ixh_vals)
        ingreso_hogar = num / den if den else None
    else:
        ingreso_hogar = None

    # NSE por hogares, clasificado por INGRESO REAL del AGEB (universal AMAI)
    nse_hog: Dict[str, float] = {}
    nse_ing: Dict[str, List[float]] = {}
    for r in agebs:
        key = ageb_nse(r)
        h = _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020"))
        if key in NSE_MAP and h is not None:
            nse_hog[key] = nse_hog.get(key, 0.0) + h
            ixh_m = _ageb_ixh_mensual(r)
            if ixh_m is not None:
                nse_ing.setdefault(key, []).append(ixh_m)

    nse = {}
    total_hog = sum(nse_hog.values()) if nse_hog else 0
    # El template usa claves Cm (=C+) y Dm (=D+)
    key_map = {"C+": "Cm", "D+": "Dm"}
    for k, h in nse_hog.items():
        ingreso = round(statistics.mean(nse_ing[k])) if nse_ing.get(k) else None
        tkey = key_map.get(k, k)
        nse[tkey] = {"hog": round(h), "pct": round(h / total_hog * 100, 1) if total_hog else None,
                     "ingreso": ingreso}
    # Garantizar que todas las claves que el template consulta existan (hog=0 si no hay)
    for tkey in ["A", "B", "Cm", "C", "Dm", "D", "E"]:
        nse.setdefault(tkey, {"hog": 0, "pct": 0, "ingreso": None})
    nse_dom_key = max(nse_hog, key=nse_hog.get) if nse_hog else None
    # PERCEPCIÓN DE VALOR PREDOMINA: si la oferta vertical observada indica un NSE superior al
    # demográfico, el NSE dominante mostrado se eleva a esa percepción (la zona se construye
    # para ese nivel). La isócrona define la zona; la percepción de valor define el producto.
    NSE_ORDEN_PV = ["A", "B", "C+", "C", "D+", "D", "E"]
    rank_pv = {n: i for i, n in enumerate(NSE_ORDEN_PV)}
    nse_percepcion = _nse_percepcion_valor(ft) if ft else None
    percepcion_aplicada = False
    if nse_percepcion and nse_dom_key and rank_pv.get(nse_percepcion, 99) < rank_pv.get(nse_dom_key, 99):
        nse_dom_key = nse_percepcion
        percepcion_aplicada = True
    # Etiqueta descriptiva (el front muestra el string completo y hace split(' ')[0] para la letra)
    NSE_DESC = {
        "A": "NSE alto · residencial premium", "B": "NSE medio-alto",
        "C+": "NSE medio-alto · aspiracional", "C": "NSE medio",
        "D+": "NSE medio-bajo", "D": "NSE bajo", "E": "NSE de subsistencia",
    }
    if percepcion_aplicada:
        # El % de hogares ya no aplica (es percepción de valor de oferta, no demografía)
        nse_dominante = f"{nse_dom_key} · {NSE_DESC.get(nse_dom_key, '')} · por percepción de valor"
    else:
        dom_pct = round(nse_hog[nse_dom_key] / total_hog * 100, 1) if (nse_dom_key and total_hog) else None
        nse_dominante = (f"{nse_dom_key} · {NSE_DESC.get(nse_dom_key, '')}"
                         + (f" ({dom_pct}%)" if dom_pct else "")) if nse_dom_key else None

    # Tenencia (C81-84) en %
    propia = _sum(agebs, "Propia"); alquilada = _sum(agebs, "Alquilada")
    prestada = _sum(agebs, "Prestada"); otra = _sum(agebs, "Otra situación")
    ten_total = sum(v for v in [propia, alquilada, prestada, otra] if v is not None)
    tenencia = {}
    if ten_total > 0:
        tenencia = {
            "propia": round((propia or 0) / ten_total * 100, 1),
            "alquilada": round((alquilada or 0) / ten_total * 100, 1),
            "prestada": round((prestada or 0) / ten_total * 100, 1),
            "otra": round((otra or 0) / ten_total * 100, 1),
        }
    hog_renta = round(alquilada) if alquilada is not None else None

    # Edad: agrupación a las 6 bandas del tablero (niños, adolescentes, jóvenes, jov_adultos, consolidados, maduros)
    edad_grupos = _derive_edad_grupos(agebs)

    return {
        "population": round(pob) if pob else None,
        "households": round(hog) if hog else None,
        "tca": tca,
        "personas_hogar": round(personas_hogar, 2) if personas_hogar else None,
        "ingreso_hogar": round(ingreso_hogar) if ingreso_hogar else None,
        "ingreso_total_anual": round(ing_total) if ing_total else None,
        "nse": nse, "nse_dominante": nse_dominante,
        "tenencia": tenencia, "hog_renta": hog_renta,
        "edad_grupos": edad_grupos,
    }


def _derive_edad_grupos(agebs: List[Dict]) -> Optional[List[int]]:
    """6 bandas: niños(0-9), adolescentes(10-15), jóvenes(16-19), jov_adultos(20-29), consolidados(30-54), maduros(55+)."""
    bands = {
        "ninos": ["0 a 4", "5 a 9"],
        "adolescentes": ["10 a 14"],
        "jovenes": ["15 a 19"],
        "jov_adultos": ["20 a 24", "25 a 29"],
        "consolidados": ["30 a 34", "35 a 39", "40 a 44", "45 a 49", "50 a 54"],
        "maduros": ["55 a 59", "60 a 64", "65 a 69", "70 a 74", "75 y Más"],
    }
    out = []
    any_data = False
    for band, cols in bands.items():
        s = 0.0
        present = False
        for c in cols:
            v = _sum(agebs, c)
            if v is not None:
                s += v; present = True
        if present:
            any_data = True
        out.append(round(s))
    return out if any_data else None


# ──────────────────────── NSE_DIM (para DIM_DATA) ────────────────────────
def derive_nse_dim(agebs: List[Dict]) -> List[Dict[str, Any]]:
    """Construye nse_dim[] con rangos de ingreso/vivienda y población por grupo de edad."""
    if not agebs:
        return []
    # Rangos de ingreso por NSE (estándar AMAI/DIGO, preservados del template)
    nse_ranges = {
        "A":  {"ing_min": 200000, "ing_max": None, "viv_min": 6800000, "viv_max": None, "tca": 1.12},
        "B":  {"ing_min": 90000,  "ing_max": 199999, "viv_min": 3050000, "viv_max": 6799999, "tca": 1.0},
        "C+": {"ing_min": 40000,  "ing_max": 89999,  "viv_min": 1350000, "viv_max": 3049999, "tca": 1.39},
        "C":  {"ing_min": 17000,  "ing_max": 39999,  "viv_min": 577000,  "viv_max": 1349999, "tca": 1.03},
        "D+": {"ing_min": 10000,  "ing_max": 16999,  "viv_min": 349000,  "viv_max": 576999,  "tca": 0.74},
        "D":  {"ing_min": 4000,   "ing_max": 9999,   "viv_min": 200000,  "viv_max": 348999,  "tca": 0.37},
        "E":  {"ing_min": 0,      "ing_max": 3999,   "viv_min": 0,       "viv_max": 199999,  "tca": 0},
    }
    agg: Dict[str, Dict] = {}
    for r in agebs:
        k = ageb_nse(r)   # clasificación por ingreso real (universal)
        if k not in NSE_MAP:
            continue
        d = agg.setdefault(k, {"poblacion": 0.0, "hogares": 0.0,
                               "ninos": 0.0, "adolescentes": 0.0, "jovenes": 0.0,
                               "jov_adultos": 0.0, "consolidados": 0.0, "empty_nest": 0.0,
                               "ixh_w": 0.0, "viv_w": 0.0})
        h = _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020")) or 0
        d["poblacion"] += _num(r.get("Población total 2026")) or _num(r.get("POB1")) or 0
        d["hogares"] += h
        d["ninos"] += _num(r.get("Niños")) or 0
        d["adolescentes"] += _num(r.get("Adolescentes")) or 0
        d["jovenes"] += _num(r.get("Jovenes")) or 0
        d["jov_adultos"] += _num(r.get("Jovenes_adultos")) or 0
        d["consolidados"] += _num(r.get("Consolidados")) or 0
        d["empty_nest"] += _num(r.get("Nesters")) or 0
        # IXH mensual ponderado por hogares
        ixh_m = _ageb_ixh_mensual(r)
        if ixh_m is not None and h:
            d["ixh_w"] += ixh_m * h
        # Valor de vivienda (V CASAS) ponderado por hogares
        vcasa = _ageb_vcasa(r)
        if vcasa is not None and h:
            d["viv_w"] += vcasa * h

    out = []
    order = ["A", "B", "C+", "C", "D+", "D", "E"]
    for k in order:
        rng = nse_ranges[k]
        d = agg.get(k, {"poblacion": 0, "hogares": 0, "ninos": 0, "adolescentes": 0,
                        "jovenes": 0, "jov_adultos": 0, "consolidados": 0, "empty_nest": 0,
                        "ixh_w": 0, "viv_w": 0})
        hog = d["hogares"]
        # ixh_nse: ingreso por hogar MENSUAL real del NSE; si no hay dato, punto medio del rango
        if hog and d["ixh_w"] > 0:
            ixh = round(d["ixh_w"] / hog)
        else:
            ixh = round((rng["ing_min"] + (rng["ing_max"] or rng["ing_min"] * 1.3)) / 2)
        # viv_nse: valor de vivienda real ponderado; si no hay dato, punto medio del rango
        if hog and d["viv_w"] > 0:
            viv = round(d["viv_w"] / hog)
        else:
            viv = round((rng["viv_min"] + (rng["viv_max"] or rng["viv_min"] * 1.3)) / 2)
        out.append({
            "NSE": k,
            "ing_min": rng["ing_min"], "ing_max": rng["ing_max"] or 0,
            "viv_min": rng["viv_min"], "viv_max": rng["viv_max"] or 0,
            "tca": rng["tca"],
            "ixh_nse": ixh, "viv_nse": viv,
            "poblacion": round(d["poblacion"]),
            "hogares": round(d["hogares"]),
            "ninos": round(d["ninos"], 1), "adolescentes": round(d["adolescentes"], 1),
            "jovenes": round(d["jovenes"], 1), "jov_adultos": round(d["jov_adultos"], 1),
            "consolidados": round(d["consolidados"], 1), "empty_nest": round(d["empty_nest"], 1),
        })
    return out


# ──────────────────────── Segmentos de demanda (Checkpoint A) ────────────────────────
PRICE_BUCKETS = [
    (0, 2.5, "< $2.5M"), (2.5, 3.5, "$2.5M-$3.5M"), (3.5, 5.0, "$3.5M-$5.0M"),
    (5.0, 7.0, "$5.0M-$7.0M"), (7.0, 10.0, "$7.0M-$10.0M"),
    (10.0, 15.0, "$10.0M-$15.0M"), (15.0, 99.0, "> $15.0M"),
]


def _nse_dominante_agebs(agebs: List[Dict]):
    """
    BARRERA DE NSE (regla de zona de influencia · universal):
    Dentro de la isócrona puede haber mezcla de submercados de distinto NSE. El análisis
    de demanda NO se hace sobre el promedio de la zona, sino sobre el NSE DOMINANTE:
    el de mayor representatividad (masa de hogares) dentro de la isócrona, que por la
    propia accesibilidad de la isócrona es también el más accesible desde el predio.

    Devuelve (agebs_dominante, nse_dom, nse_superior, share_dom):
      • agebs_dominante: solo las AGEB del NSE dominante (sobre las que se calcula demanda).
      • nse_dom: clave del NSE dominante.
      • nse_superior: el NSE inmediatamente superior presente en la zona (define el TECHO
        de inducción de demanda hacia arriba — siempre por debajo del piso de esa zona).
      • share_dom: fracción de hogares que representa el dominante (para reportar la barrera).
    """
    if not agebs:
        return agebs, None, None, 1.0
    # Orden de NSE de mayor a menor poder adquisitivo
    NSE_ORDEN = ["A", "B", "C+", "C", "D+", "D", "E"]
    rank = {n: i for i, n in enumerate(NSE_ORDEN)}
    # Masa de hogares por NSE (representatividad real en la isócrona)
    masa = {}
    for r in agebs:
        nse = ageb_nse(r)
        if not nse:
            continue
        hog = _num(r.get("Hogares totales 2026")) or _num(r.get("Total de hogares")) or 1
        masa[nse] = masa.get(nse, 0) + hog
    if not masa:
        return agebs, None, None, 1.0
    total_hog = sum(masa.values())
    nse_dom = max(masa, key=lambda n: masa[n])
    share_dom = masa[nse_dom] / total_hog if total_hog else 1.0
    # NSE inmediatamente superior PRESENTE en la zona (techo de inducción)
    nse_superior = None
    for n in NSE_ORDEN:
        if n in masa and rank.get(n, 99) < rank.get(nse_dom, 0):
            nse_superior = n  # el último (más cercano) por encima del dominante
    # AGEB del submercado dominante
    agebs_dom = [r for r in agebs if ageb_nse(r) == nse_dom]
    return agebs_dom, nse_dom, nse_superior, share_dom


def _nse_barrier_info(agebs: List[Dict]) -> Dict[str, Any]:
    """Reporte legible de la barrera de NSE aplicada a la zona de influencia."""
    agebs_dom, nse_dom, nse_superior, share_dom = _nse_dominante_agebs(agebs)
    # Composición NSE completa de la isócrona (informativa)
    masa = {}
    for r in agebs:
        nse = ageb_nse(r)
        if not nse:
            continue
        hog = _num(r.get("Hogares totales 2026")) or _num(r.get("Total de hogares")) or 1
        masa[nse] = masa.get(nse, 0) + hog
    total = sum(masa.values()) or 1
    composicion = {k: round(v / total * 100, 1) for k, v in sorted(masa.items(), key=lambda kv: -kv[1])}
    barrera = len(masa) > 1 and share_dom < 0.85  # hay mezcla relevante de submercados
    return {
        "nse_dominante": nse_dom,
        "nse_superior": nse_superior,
        "share_dominante_pct": round(share_dom * 100, 1),
        "agebs_dominante": len(agebs_dom),
        "agebs_total": len(agebs),
        "composicion_nse": composicion,
        "barrera": barrera,
        "metodo": "nse_dominante" if barrera else "isocrona_uniforme",
        "nota": (f"Análisis sobre NSE dominante {nse_dom} ({round(share_dom*100)}% de hogares, "
                 f"el más accesible). Demanda inducible hasta por debajo del piso de NSE {nse_superior}."
                 if barrera and nse_superior else
                 f"Zona homogénea en NSE {nse_dom}" if nse_dom else "Sin datos de NSE"),
    }


def derive_segments(agebs: List[Dict], ft: List[Dict]) -> List[Dict[str, Any]]:
    """
    Metodología DPO de demanda (universal para todo México):

    0. BARRERA DE NSE: el análisis se hace sobre el NSE DOMINANTE de la zona de influencia
       (mayor masa de hogares en la isócrona), no sobre el promedio. Se puede inducir demanda
       a precios mayores, pero por debajo del piso del NSE superior (mejor precio a cambio de
       sacrificar entorno urbano, con producto nuclear casi tan bueno).
    1. CAPACIDAD DE COMPRA: cada hogar puede pagar vivienda ≈ ingreso_anual × MÚLTIPLO
       (4.5 años). La demanda base se asigna al bucket de precio que su ingreso permite.
    2. ANCLA DE PERCEPCIÓN DE VALOR: el nivel de precio "natural" de la zona se valida
       contra el producto que realmente se vende (VVV).
    3. EXPANSIÓN CON EVIDENCIA: la demanda puede subir a buckets superiores solo si hay
       EVIDENCIA de unidades vendidas ahí (VVV) coherente con ingresos altos en la zona.
    4. TOPE: no se permiten más de 2 buckets por encima del nivel de valor percibido de la
       zona si NO hay evidencia de venta de producto en esos niveles.
    """
    if not agebs:
        return []

    # ── 0 · BARRERA DE NSE (identifica el submercado dominante; NO recorta la demanda) ──
    # La demanda se calcula sobre TODO el espectro de la zona de influencia. La barrera de
    # NSE se usa para: (a) anclar el SWEET SPOT al bucket del NSE dominante (el más accesible),
    # (b) fijar el TECHO DE INDUCCIÓN (piso del NSE superior). Todos los buckets con demanda
    # u oferta se muestran como productos (recomendados o no).
    agebs_dom, nse_dom, nse_superior, share_dom = _nse_dominante_agebs(agebs)

    # ── Buckets de precio canónicos (M MXN) ──
    BUCKETS = [
        (0, 1.5, "< $1.5M"), (1.5, 2.5, "$1.5M-$2.5M"), (2.5, 3.5, "$2.5M-$3.5M"),
        (3.5, 5.0, "$3.5M-$5.0M"), (5.0, 7.0, "$5.0M-$7.0M"), (7.0, 10.0, "$7.0M-$10.0M"),
        (10.0, 15.0, "$10.0M-$15.0M"), (15.0, 25.0, "$15.0M-$25.0M"), (25.0, 999.0, "> $25.0M"),
    ]
    def bucket_idx(precio_m):
        for i, (lo, hi, _) in enumerate(BUCKETS):
            if lo <= precio_m < hi:
                return i
        return None

    # ── 1 · DEMANDA POR CAPACIDAD DE COMPRA ──
    # INEGI ya estima la capacidad de compra real por hogar en "Rangos demanda vivienda"
    # (captura patrimonio, apalancamiento, etc., no solo múltiplo de ingreso corriente).
    # Tomamos esa demanda por rango y la mapeamos a nuestros buckets canónicos.
    demanda_bucket = {i: {"nuevas_fam": 0.0, "hogares": 0.0} for i in range(len(BUCKETS))}
    for r in agebs:
        rango = r.get("Rangos demanda vivienda")
        dem = _num(r.get("Demanda anual vivienda"))
        hog = _num(r.get("Hogares totales 2026")) or 0
        if not rango or dem is None:
            continue
        low = _extract_low(rango)   # valor en MXN
        if low is None:
            continue
        bi = bucket_idx(low / 1e6)
        if bi is None:
            continue
        demanda_bucket[bi]["nuevas_fam"] += dem
        demanda_bucket[bi]["hogares"] += hog

    # ── 2 · Evidencia de venta real por bucket (VVV) ──
    PM2_VERTICAL_MIN = 20000   # piso de plausibilidad: pm2 vertical real
    evidencia = {i: {"vendidas": 0, "disp": 0, "n": 0, "pm2_vals": []} for i in range(len(BUCKETS))}
    for t in ft:
        a = t.get("attributes", {})
        precio = _price(a.get("F____UNIDAD"))
        if not precio:
            continue
        bi = bucket_idx(precio / 1e6)
        if bi is None:
            continue
        evidencia[bi]["vendidas"] += int(_num(a.get("UNIDADES_VENDIDAS")) or 0)
        evidencia[bi]["disp"] += int(_num(a.get("UNIDADES_DISPONIBLES")) or 0)
        evidencia[bi]["n"] += 1
        pm2v = _pm2(a.get("F___M2"))
        if pm2v and pm2v >= PM2_VERTICAL_MIN:
            evidencia[bi]["pm2_vals"].append(pm2v)
    # ¿El bucket tiene oferta VERTICAL plausible? (mediana pm2 ≥ piso vertical)
    for i in evidencia:
        pv = evidencia[i]["pm2_vals"]
        evidencia[i]["es_vertical"] = bool(pv) and statistics.median(pv) >= PM2_VERTICAL_MIN

    # ── REGLA DE PERCEPCIÓN DE VALOR (universal) ──
    # La ISÓCRONA determina la ZONA (demografía → demanda). La PERCEPCIÓN DE VALOR del
    # PRODUCTO la determina la OFERTA observada: el valor de vivienda vertical que realmente
    # se vende en la zona. La percepción de valor DOMINANTE predomina y PUEDE AUMENTAR si hay
    # evidencia de oferta en valores superiores. Así, una zona con demografía diluida (p.ej.
    # Valle Poniente sale D+ por accesibilidad) pero con oferta vertical premium ($142k/m²)
    # reconoce su percepción de valor real (A premium) para anclar el producto.
    NSE_ORDEN_PV = ["A", "B", "C+", "C", "D+", "D", "E"]
    rank_pv = {n: k for k, n in enumerate(NSE_ORDEN_PV)}
    def _nse_de_precio_m(precio_m):
        bands = [("A", 6.8, None), ("B", 3.05, 6.8), ("C+", 1.35, 3.05), ("C", 0.577, 1.35),
                 ("D+", 0.349, 0.577), ("D", 0.2, 0.349), ("E", 0, 0.2)]
        for nse, lo, hi in bands:
            if precio_m >= lo and (hi is None or precio_m < hi):
                return nse
        return None
    # Percepción de valor dominante = NSE del PRECIO MEDIANO de la oferta vertical real.
    # El precio mediano de lo que se vende/ofrece indica para qué percepción se construye en
    # la zona (la masa de oferta vertical), independiente de la demografía de la isócrona.
    precios_oferta_m = []
    for t in ft:
        a = t.get("attributes", {})
        precio = _price(a.get("F____UNIDAD"))
        pm2v = _pm2(a.get("F___M2"))
        # solo oferta vertical plausible (pm2 ≥ piso vertical)
        if precio and pm2v and pm2v >= PM2_VERTICAL_MIN:
            precios_oferta_m.append(precio / 1e6)
    nse_percepcion = None
    if precios_oferta_m:
        precio_mediano_m = statistics.median(precios_oferta_m)
        nse_percepcion = _nse_de_precio_m(precio_mediano_m)
    # La percepción de valor PREDOMINA: si la oferta observada indica un NSE superior al
    # demográfico, el ancla del producto sube a esa percepción (puede aumentar con evidencia).
    nse_dom_demografico = nse_dom
    salto_percepcion = 0   # cuántos niveles NSE sube la percepción sobre la demografía
    if nse_percepcion and rank_pv.get(nse_percepcion, 99) < rank_pv.get(nse_dom, 99):
        salto_percepcion = rank_pv.get(nse_dom, 0) - rank_pv.get(nse_percepcion, 0)
        nse_dom = nse_percepcion
        # Recalcular el NSE superior respecto a la nueva percepción dominante
        nse_superior = None
        for n in NSE_ORDEN_PV:
            if rank_pv.get(n, 99) < rank_pv.get(nse_dom, 0):
                nse_superior = n  # el más cercano por encima

    # ── 3 · Nivel de valor percibido = bucket con mayor demanda por capacidad de compra ──
    nivel_percibido = max(demanda_bucket, key=lambda i: demanda_bucket[i]["nuevas_fam"]) \
        if any(demanda_bucket[i]["nuevas_fam"] for i in demanda_bucket) else 0

    # ── 4 · TOPE: no exceder +2 buckets sobre el nivel percibido SIN evidencia de venta ──
    EVIDENCIA_MIN = 3  # unidades vendidas para validar producto en ese nivel
    bucket_max_permitido = nivel_percibido + 2
    for i in range(nivel_percibido + 1, len(BUCKETS)):
        if evidencia[i]["vendidas"] >= EVIDENCIA_MIN:
            bucket_max_permitido = max(bucket_max_permitido, i)  # la evidencia extiende el tope

    # ── TECHO DE INDUCCIÓN POR BARRERA DE NSE ──
    # Se puede inducir demanda a precios mayores que el NSE dominante (mejor precio a cambio
    # de sacrificar entorno urbano, con producto nuclear casi tan bueno), PERO siempre por
    # DEBAJO del piso de valor de vivienda del NSE superior presente en la zona.
    NSE_VIV_PISO_M = {"A": 6.8, "B": 3.05, "C+": 1.35, "C": 0.577, "D+": 0.349, "D": 0.2, "E": 0.0}
    if nse_superior:
        piso_superior_m = NSE_VIV_PISO_M.get(nse_superior, 999)
        # Último bucket cuyo techo no alcanza el piso del NSE superior
        techo_induccion = 0
        for i, (lo, hi, _) in enumerate(BUCKETS):
            if lo < piso_superior_m:
                techo_induccion = i
        # El tope no puede exceder el techo de inducción (salvo evidencia dura ya contemplada)
        bucket_max_permitido = min(bucket_max_permitido, max(techo_induccion, nivel_percibido))

    # Redistribuir demanda que excede el tope (sin evidencia) hacia el máximo permitido
    for i in range(bucket_max_permitido + 1, len(BUCKETS)):
        if demanda_bucket[i]["nuevas_fam"] > 0 or demanda_bucket[i]["hogares"] > 0:
            demanda_bucket[bucket_max_permitido]["nuevas_fam"] += demanda_bucket[i]["nuevas_fam"]
            demanda_bucket[bucket_max_permitido]["hogares"] += demanda_bucket[i]["hogares"]
            demanda_bucket[i] = {"nuevas_fam": 0.0, "hogares": 0.0}

    # ── Construir segmentos ──
    def nse_by_viv(valor_m):
        bands = [("A", 6.8, None), ("B", 3.05, 6.8), ("C+", 1.35, 3.05), ("C", 0.577, 1.35),
                 ("D+", 0.349, 0.577), ("D", 0.2, 0.349), ("E", 0, 0.2)]
        for nse, lo, hi in bands:
            if valor_m >= lo and (hi is None or valor_m < hi):
                return nse
        return "—"
    nse_ing_band = {"A": (200000, 350000), "B": (90000, 199999), "C+": (40000, 89999),
                    "C": (17000, 39999), "D+": (10000, 16999), "D": (4000, 9999), "E": (0, 3999)}

    segments = []
    total_nf = sum(demanda_bucket[i]["nuevas_fam"] for i in demanda_bucket)

    def nse_by_viv2(valor_m):
        return nse_by_viv(valor_m)
    def _nse_de_bucket(i):
        lo, hi, _ = BUCKETS[i]
        mid = (lo + (hi if hi < 999 else lo * 1.3)) / 2
        return nse_by_viv(mid)
    NSE_ORDEN = ["A", "B", "C+", "C", "D+", "D", "E"]
    rank = {n: k for k, n in enumerate(NSE_ORDEN)}
    rank_dom = rank.get(nse_dom, 99)
    rank_sup = rank.get(nse_superior, -1) if nse_superior else -1

    # ════════ SELECCIÓN UNIFICADA DEL PRODUCTO ANCLA (sweet / featured) ════════
    # Regla: la PERCEPCIÓN DE VALOR (bucket del precio mediano de la oferta vertical) define
    # el nivel del producto ancla. Sobre ese nivel:
    #   • si el bucket tiene demanda DIM local → es SWEET SPOT (demand-driven).
    #   • si NO tiene demanda local pero sí oferta vertical → es ancla de PERCEPCIÓN DE VALOR
    #     (mercado_dual): el producto se vende a foráneos/inversionistas (nota explícita).
    # El bucket de percepción de valor: el del precio mediano de la oferta vertical observada.
    pv_idx = None
    if precios_oferta_m:
        pv_idx = bucket_idx(statistics.median(precios_oferta_m))
    # Si ese bucket no tiene oferta vertical plausible, bajar al bucket vertical más cercano
    if pv_idx is None or not evidencia.get(pv_idx, {}).get("es_vertical"):
        verticales = [i for i in range(len(BUCKETS)) if evidencia[i].get("es_vertical")
                      and evidencia[i]["vendidas"] > 0]
        if verticales and pv_idx is not None:
            pv_idx = min(verticales, key=lambda i: abs(i - pv_idx))
        elif verticales:
            pv_idx = max(verticales, key=lambda i: evidencia[i]["vendidas"])
        else:
            pv_idx = None

    sweet_idx = None
    mercado_dual = False
    dual_idx = None
    if pv_idx is not None:
        if demanda_bucket[pv_idx]["nuevas_fam"] > 0:
            # Convergencia demanda×oferta en el nivel de percepción de valor → sweet spot
            sweet_idx = pv_idx
        else:
            # Oferta vertical en el nivel de percepción de valor SIN demanda DIM local:
            # mercado anclado a percepción de valor / foráneo (dual)
            mercado_dual = True
            dual_idx = pv_idx
    else:
        # No hay oferta vertical en absoluto: mercado incipiente demand-driven puro.
        # El ancla es el bucket de mayor demanda dentro del techo de inducción.
        cand = {i: demanda_bucket[i]["nuevas_fam"] for i in range(len(BUCKETS))
                if demanda_bucket[i]["nuevas_fam"] > 0
                and rank.get(_nse_de_bucket(i), 99) <= rank_dom}
        if not cand:
            cand = {i: demanda_bucket[i]["nuevas_fam"] for i in range(len(BUCKETS))
                    if demanda_bucket[i]["nuevas_fam"] > 0}
        sweet_idx = max(cand, key=cand.get) if cand else None


    for i, (lo, hi, label) in enumerate(BUCKETS):
        db = demanda_bucket[i]
        vend = evidencia[i]["vendidas"]; disp = evidencia[i]["disp"]
        tiene_demanda = db["nuevas_fam"] > 0 or db["hogares"] > 0
        tiene_oferta = vend > 0 or disp > 0 or evidencia[i]["n"] > 0
        # OPCIÓN 3: incluir el bucket si tiene demanda O si tiene oferta (supply-driven)
        if not tiene_demanda and not tiene_oferta:
            continue

        nuevas = round(db["nuevas_fam"], 1)
        mkt_total = round(db["hogares"])
        mid_m = (lo + (hi if hi < 999 else lo * 1.3)) / 2
        nse_cls = nse_by_viv(mid_m)

        # ORIGEN: demand_driven si hay demanda DIM local; supply_driven si solo hay oferta
        origen = "demand_driven" if tiene_demanda else "supply_driven"

        # Status: combina demanda (nuevas familias) con oferta disponible + evidencia de venta
        if i == sweet_idx:
            status = "sweet_spot"
        elif not tiene_demanda and tiene_oferta:
            # Supply-driven: el mercado lo atiende la oferta sin demanda DIM local medible.
            # Si se vende (evidencia), es atendido/oceano_rojo; si no, bajo_crecimiento.
            if vend >= 3 and disp < vend:
                status = "atendido"
            elif disp > 0 and vend == 0:
                status = "bajo_crecimiento"
            else:
                status = "oceano_rojo"
        elif nuevas == 0:
            status = "bajo_crecimiento"
        elif disp == 0 and vend == 0:
            status = "desatendido"
        elif disp < nuevas * 12:
            status = "oportunidad"
        elif disp < nuevas * 36:
            status = "atendido"
        else:
            status = "oceano_rojo"

        ing_lo, ing_hi = nse_ing_band.get(nse_cls, (0, 0))
        # Renta mensual ≈ 0.4% del valor de vivienda. Para el bucket inferior (lo=0),
        # usar un piso representativo para no devolver renta 0/N/D.
        hi_eff = (hi if hi < 999 else lo * 1.3)
        lo_eff = lo if lo > 0 else hi_eff * 0.5   # piso del bucket inferior
        rent_min = round(lo_eff * 1e6 * 0.004)
        rent_max = round(hi_eff * 1e6 * 0.004)
        es_dual_featured = (mercado_dual and i == dual_idx)
        seg = {
            "NSE": nse_cls, "bucket": label,
            "val_min": lo * 1e6, "val_max": (hi if hi < 999 else lo * 1.3) * 1e6,
            "mkt_total": mkt_total, "nuevas_fam": nuevas,
            "mkt_venta": round(mkt_total * 0.83) if mkt_total else 0,
            "mkt_renta": round(mkt_total * 0.17) if mkt_total else 0,
            "rent_min": rent_min, "rent_max": rent_max,
            "ing_min": ing_lo, "ing_max": ing_hi,
            "hog_propios": round(mkt_total * 0.65) if mkt_total else 0,
            "evidencia_vendidas": vend, "evidencia_disp": disp,
            "status": status, "origen": origen, "segments_in_bucket": 1,
        }
        if es_dual_featured:
            seg["dual_featured"] = True
            if salto_percepcion >= 3:
                # Salto grande (p.ej. D+→A): zona popular con oferta vertical de lujo para foráneos
                seg["nota_mercado"] = "Mercado foráneo/inversionista · oferta vertical premium sin demanda local DIM"
            else:
                # Salto moderado: la percepción de valor de la zona supera su demografía;
                # el producto vertical atiende a la percepción de valor dominante observada.
                seg["nota_mercado"] = "Producto anclado a la percepción de valor de la zona (oferta vertical observada)"
        segments.append(seg)

    return segments


def _extract_low(rango: str) -> Optional[float]:
    """De '$2,800,000-$3,399,999' o '8,333,333 - 10,000,000' → 2800000.0 (float)."""
    if not rango:
        return None
    import re
    # Captura grupos numéricos con comas/puntos (sin el signo $)
    nums = re.findall(r"[\d][\d,\.]*", str(rango).replace("$", ""))
    if nums:
        try:
            return float(nums[0].replace(",", ""))
        except ValueError:
            return None
    return None


def _extract_high(rango: str) -> Optional[float]:
    if not rango:
        return None
    import re
    nums = re.findall(r"[\d][\d,\.]*", str(rango).replace("$", ""))
    if len(nums) >= 2:
        try:
            return float(nums[1].replace(",", ""))
        except ValueError:
            return None
    return None


# ──────────────────────── Productos venta (Checkpoint B) ────────────────────────
def derive_productos_venta(ft: List[Dict], segments: List[Dict]) -> List[Dict[str, Any]]:
    """
    Un producto por bucket de demanda. Replica la metodología DPO de los tableros estáticos:
      • TAMAÑO (m²) = ticket / precio_m²  (siempre se deriva, nunca N/D si hay precio).
      • ABSORCIÓN demand-driven = nuevas_fam/mes, modulada por:
          - TCA del NSE (crecimiento de nuevas familias),
          - tamaño del mercado potencial (nuevas familias del segmento),
          - competencia directa en el corredor (nº de tipologías que compiten en el bucket),
          - elasticidad de ticket: tickets altos (>$16M) caen fuerte la absorción.
      • RECÁMARAS derivadas del tamaño.
    """
    color_by_status = {
        "sweet_spot": "green", "desatendido": "blue", "oportunidad": "purple",
        "atendido": "teal", "oceano_rojo": "red", "bajo_crecimiento": "amber",
    }
    # Precio/m² de referencia por NSE (de los tableros estáticos validados · MXN)
    PM2_POR_NSE = {"A": 140000, "B": 95000, "C+": 55000, "C": 40000,
                   "D+": 30000, "D": 22000, "E": 16000}
    # Recámaras según área interior (m²)
    def recamaras_por_m2(m2):
        if m2 is None: return "N/D"
        if m2 < 45:  return "Studio"
        if m2 < 65:  return "1 Rec"
        if m2 < 95:  return "2 Rec"
        if m2 < 140: return "3 Rec"
        return "3-4 Rec"

    # Competencia directa por bucket: nº de tipologías de la oferta (ft) en cada rango de precio
    competencia = {}
    for t in ft:
        a = t.get("attributes", {})
        precio = _price(a.get("F____UNIDAD"))
        if not precio:
            continue
        for s in segments:
            if s.get("val_min") and s.get("val_max") and s["val_min"] <= precio < s["val_max"]:
                competencia[s["bucket"]] = competencia.get(s["bucket"], 0) + 1
                break

    # Familias-mes máximas de toda la zona (para normalizar elasticidad)
    max_nf_month = max((s.get("nuevas_fam", 0) / 12 for s in segments), default=0)

    productos = []
    for s in segments:
        vmin = s.get("val_min")
        vmax = s.get("val_max")
        val_mid = None
        if vmin is not None and vmax is not None and (vmin or vmax):
            # Si val_min es 0 (bucket inferior), usar val_max como referencia superior
            if vmin and vmax:
                val_mid = (float(vmin) + float(vmax)) / 2
            elif vmax:
                val_mid = float(vmax) * 0.75   # bucket inferior: punto representativo bajo el techo
            elif vmin:
                val_mid = float(vmin) * 1.1

        # DPO anchor: ticket no por debajo del val_min del segmento
        ticket_M = round(val_mid / 1e6, 2) if val_mid else None
        if ticket_M and vmin:
            ticket_M = max(ticket_M, round(float(vmin) / 1e6, 2))

        # precio/m²: mediana real de ft en el rango; si no hay o es implausible, referencia NSE.
        # Un pm2 vertical real está sobre ~$20,000/m²; valores menores son ruido (bodegas,
        # cocheras, lotes) y se descartan a favor de la referencia del NSE.
        PM2_VERTICAL_MIN = 20000
        pm2_vals = []
        for t in ft:
            a = t.get("attributes", {})
            precio = _price(a.get("F____UNIDAD"))
            pm2v = _pm2(a.get("F___M2"))
            if (precio and val_mid and abs(precio - val_mid) / val_mid < 0.20
                    and pm2v and pm2v >= PM2_VERTICAL_MIN):
                pm2_vals.append(pm2v)
        pm2 = round(statistics.median(pm2_vals)) if pm2_vals else PM2_POR_NSE.get(s["NSE"], 50000)
        if pm2 < PM2_VERTICAL_MIN:
            pm2 = PM2_POR_NSE.get(s["NSE"], 50000)

        # TAMAÑO (m²) = ticket / precio_m²  · banda física [25, 500]
        m2 = None
        if ticket_M and pm2:
            m2 = round(ticket_M * 1e6 / pm2)
            m2 = max(M2_MIN, min(M2_MAX, m2))

        # ABSORCIÓN demand-driven realista (absorción de UN proyecto, no de todo el mercado).
        # La demanda mensual del segmento se reparte entre los proyectos que compiten en él.
        nf_month = (s.get("nuevas_fam", 0) or 0) / 12   # familias nuevas/mes del segmento (todo el mercado)
        n_comp = competencia.get(s["bucket"], 0)
        disp = s.get("evidencia_disp", 0) or 0
        vend = s.get("evidencia_vendidas", 0) or 0

        # Cuota de mercado: la demanda se reparte entre los competidores directos + el nuevo
        # proyecto. Sin competencia, un proyecto entrante captura una fracción de adopción
        # realista del mercado (no el 100%, por estacionalidad/awareness/financiamiento).
        CAPTURA_SIN_COMPETENCIA = 0.35   # un solo jugador no absorbe toda la demanda al instante
        competidores_efectivos = n_comp + 1   # competidores existentes + el nuevo proyecto
        if n_comp > 0:
            abs_rate = nf_month / competidores_efectivos
        else:
            abs_rate = nf_month * CAPTURA_SIN_COMPETENCIA

        # Ritmo de venta observado del bucket (evidencia VVV): unidades vendidas distribuidas
        # en ~24 meses de comercialización típica, repartidas entre los proyectos que venden.
        abs_evidencia = None
        if vend >= 3:
            n_proy_vend = max(n_comp, 1)
            abs_evidencia = (vend / 24.0) / n_proy_vend

        # Penalización por sobreoferta: si los disponibles superan ampliamente la demanda
        # anual, el bucket está saturado (océano rojo) y la absorción cae.
        if nf_month > 0 and disp > nf_month * 12 * 3:      # >3 años de inventario disponible
            abs_rate *= 0.4
        elif nf_month > 0 and disp > nf_month * 12 * 2:    # 2-3 años de inventario
            abs_rate *= 0.65

        # Elasticidad de ticket: tickets muy altos pierden capacidad crediticia
        if ticket_M is not None:
            if ticket_M > 25:   abs_rate *= 0.55
            elif ticket_M > 16: abs_rate *= 0.75

        # La evidencia de venta real establece un piso (la zona demuestra que absorbe)
        if abs_evidencia:
            abs_rate = max(abs_rate, abs_evidencia)

        # Supply-driven (sin demanda DIM): la absorción viene solo de la evidencia de venta
        if s.get("origen") == "supply_driven" or nf_month == 0:
            abs_rate = abs_evidencia or 0

        # Techo de cordura: ningún proyecto vertical absorbe >12 un/mes de forma sostenida
        abs_rate = min(abs_rate, 12.0)

        mix_pct = None
        tot_nf = sum(x.get("nuevas_fam", 0) for x in segments) or 0
        if tot_nf and s.get("nuevas_fam"):
            mix_pct = round(s["nuevas_fam"] / tot_nf * 100)
        nse_tca = {"A": 1.39, "B": 1.66, "C+": 1.66, "C": 1.70, "D+": 2.41, "D": 3.49, "E": 0}.get(s["NSE"], 1.5)

        productos.append({
            "tipo": f"{recamaras_por_m2(m2)} · {s['bucket']}" if m2 else f"{s['NSE']} · {s['bucket']}",
            "badge": f"{mix_pct}%" if mix_pct is not None else "—",
            "color": color_by_status.get(s["status"], "teal"),
            "rec": recamaras_por_m2(m2),
            "m2": f"{m2} m²" if m2 else "N/D",
            "pm2": f"${pm2:,}" if pm2 else "N/D",
            "ticket": f"${ticket_M:.2f}M" if ticket_M else "N/D",
            "abs": f"{abs_rate:.1f} un/mes" if abs_rate else "N/D",
            "tca": nse_tca,
            "competidores": n_comp,
            "mercado": f"NSE {s['NSE']} · {s['bucket']} · {n_comp} competidores directos",
            "status": s["status"],
            "recomendado": s["status"] in ("sweet_spot", "desatendido", "oportunidad", "atendido") or s.get("dual_featured", False),
            "featured": s["status"] == "sweet_spot" or s.get("dual_featured", False),
            "seg_dim": f"{s['NSE']} · {s['bucket']}",
            "mkt_segmento": s["mkt_total"], "nuevas_fam": s["nuevas_fam"],
            "categoria": _status_label(s["status"]),
            "perfiles": _perfiles_por_segmento(s["NSE"], m2, ticket_M),
            "nota_mercado": s.get("nota_mercado"),
        })
    # Solo un featured
    feats = [p for p in productos if p.get("featured")]
    if len(feats) > 1:
        best = max(feats, key=lambda p: p.get("nuevas_fam", 0))
        for p in feats:
            if p is not best:
                p["featured"] = False
    elif not feats:
        # Mercado puramente supply-driven (sin sweet spot demand-driven): destacar el producto
        # que el mercado valida con mayor absorción/venta real (el más relevante para invertir).
        def _abs_num(p):
            try:
                return float(str(p.get("abs", "0")).replace(" un/mes", "")) if p.get("abs") not in (None, "N/D") else 0.0
            except ValueError:
                return 0.0
        recomendables = [p for p in productos if p.get("recomendado")]
        pool = recomendables or productos
        if pool:
            best = max(pool, key=_abs_num)
            best["featured"] = True
    return productos


def _status_label(status: str) -> str:
    return {
        "desatendido": "Gap · Desatendido", "sweet_spot": "Sweet Spot Estructural",
        "atendido": "Mercado Core · Atendido", "oportunidad": "Sub-oferta · Oportunidad",
        "oceano_rojo": "Océano Rojo · Sobreoferta", "bajo_crecimiento": "Supply-Driven · Sin Demanda",
    }.get(status, status)


# ──────────────────────── Productos renta (Checkpoint F) ────────────────────────
def derive_productos_renta(ft_renta: List[Dict], segments: List[Dict]) -> List[Dict[str, Any]]:
    """
    Productos de renta derivados de los segments DPO. Para cada bucket con mercado de renta:
      • RENTA mensual = punto medio de rent_min/rent_max (~0.4% del valor de vivienda).
      • TAMAÑO (m²) = mismo criterio que venta (ticket de compra / precio_m²).
      • RENTA/m² = renta_mensual / m².
      • ABSORCIÓN de contratos/mes = nuevas familias que RENTAN/mes del segmento.
    Si hay oferta de renta real (ft_renta), se usa para validar renta/m² de la zona.
    """
    if not segments:
        return []
    PM2_POR_NSE = {"A": 140000, "B": 95000, "C+": 55000, "C": 40000,
                   "D+": 30000, "D": 22000, "E": 16000}

    def recamaras_por_m2(m2):
        if m2 is None: return "N/D"
        if m2 < 45:  return "Studio"
        if m2 < 65:  return "1 Rec"
        if m2 < 95:  return "2 Rec"
        if m2 < 140: return "3 Rec"
        return "3-4 Rec"

    # renta/m² observada de la oferta real (para validar/anclar)
    pm2_renta_obs = []
    for t in ft_renta:
        a = t.get("attributes", {})
        ap = _num(a.get("ÁREA_PRIVATIVA")); pr = _num(a.get("F____UNIDAD"))
        if ap and 25 <= ap <= 500 and pr and pr > 1000:
            pm2_renta_obs.append(pr / ap)
    pm2_renta_zona = round(statistics.median(pm2_renta_obs)) if pm2_renta_obs else None

    # propensión a rentar de la zona (mkt_renta / mkt_total) para distribuir el sweet spot
    best = max(segments, key=lambda s: s.get("mkt_renta", 0) or 0, default=None)

    productos = []
    for s in segments:
        if s.get("status") == "bajo_crecimiento":
            continue
        rent_min = s.get("rent_min"); rent_max = s.get("rent_max")
        renta_mid = ((rent_min or 0) + (rent_max or 0)) / 2 if (rent_min is not None and rent_max) else None
        # m² del segmento (mismo método que venta)
        vmin = s.get("val_min"); vmax = s.get("val_max")
        val_mid = None
        if vmin and vmax:
            val_mid = (vmin + vmax) / 2
        elif vmax:
            val_mid = vmax * 0.75
        pm2_venta = PM2_POR_NSE.get(s["NSE"], 50000)
        m2 = None
        if val_mid and pm2_venta:
            m2 = max(M2_MIN, min(M2_MAX, round(val_mid / pm2_venta)))
        pm2_renta = round(renta_mid / m2) if (renta_mid and m2) else None
        # ABSORCIÓN de renta = nuevas familias que rentan/mes (mkt_renta es stock; usamos nuevas_fam × propensión a rentar)
        nf = s.get("nuevas_fam", 0) or 0
        mkt_total = s.get("mkt_total", 0) or 1
        prop_renta = (s.get("mkt_renta", 0) or 0) / mkt_total if mkt_total else 0
        abs_renta = round(nf / 12 * prop_renta, 2) if nf and prop_renta else None

        productos.append({
            "tipo": f"{recamaras_por_m2(m2)} Renta · {s['bucket']}" if m2 else f"Renta {s['NSE']}",
            "rec": recamaras_por_m2(m2),
            "m2": f"{m2} m²" if m2 else "N/D",
            "pm2_renta": f"${pm2_renta:,}/m²/mes" if pm2_renta else "N/D",
            "renta_ud": f"${round(renta_mid):,}/mes" if renta_mid else "N/D",
            "abs_renta": f"{abs_renta} contratos/mes" if abs_renta else "N/D",
            "ocupacion_target": "92%",
            "status": s.get("status", "atendido"),
            "recomendado": s.get("status") in ("sweet_spot", "desatendido", "oportunidad", "atendido"),
            "featured": (best is not None and s is best),
            "seg_renta": f"{s['NSE']} · {s['bucket']}",
            "mkt_segmento": round(s.get("mkt_renta", 0)),
            "nuevas_fam_year": nf,
            "mercado": f"NSE {s['NSE']} · renta {s['bucket']}",
        })
    return productos


# ──────────────────────── Comercio (potencial retail) ────────────────────────
def derive_comercio(agebs: List[Dict]) -> Dict[str, Any]:
    """Agrega gasto retail por categoría y deriva GLA potencial vía ventas-por-m²."""
    if not agebs:
        return {}
    # Gasto anual por categoría (montos MXN · campos C193-201)
    gasto_cats = {
        "Retail": "Gasto Retail", "Supermercado": "Gasto Supermercado",
        "Servicios": "Gasto Servicios", "Educacion": "Gasto Educación",
        "Restaurantes": "Gasto Restaurantes", "Cuidado": "Gasto Cuidado personal",
        "Entret": "Gasto Entretenimiento", "MV": "Gasto Mantenimiento de la vivienda",
        "Mueb": "Gasto Mueblería", "Salud": "Gasto Cuidado de la salud",
    }
    demanda = {}
    for k, col in gasto_cats.items():
        v = _sum(agebs, col)
        demanda[k] = round(v) if v is not None else None

    ing_total = _sum(agebs, "Ingresos totales 2026")

    # Ventas por m²/año típicas del giro (MXN) → GLA = gasto capturado / ventas_m2
    CAPTURA = 0.25
    ventas_m2_anual = {
        "Supermercado": 95000, "Retail": 65000, "Restaurantes": 55000,
        "Educacion": 40000, "Servicios": 60000, "Salud": 70000,
        "Entret": 45000, "Cuidado": 58000, "Mueb": 38000, "MV": 35000,
    }
    # Categoría (giro) del rubro
    categoria_giro = {
        "Supermercado": "Supermercado", "Retail": "Retail / Departamental",
        "Restaurantes": "Restaurantes / F&B", "Educacion": "Educación",
        "Servicios": "Servicios financieros", "Salud": "Salud / Farmacia",
        "Entret": "Entretenimiento / Gym", "Cuidado": "Cuidado personal",
        "Mueb": "Mueblería / Hogar", "MV": "Mejoras del hogar",
    }
    # Inquilino potencial sugerido (marcas/conceptos concretos por giro)
    tenant_ideal = {
        "Supermercado": "HEB · Soriana · City Market", "Retail": "Suburbia · Coppel · boutiques",
        "Restaurantes": "Toks · Italianni's · casual dining", "Educacion": "Kumon · academias · colegios",
        "Servicios": "BBVA · Banorte · servicios", "Salud": "Farmacias · clínica · laboratorio",
        "Entret": "Smart Fit · Cinépolis · gym", "Cuidado": "Spa · estética · barbería",
        "Mueb": "Showroom hogar · decoración", "MV": "Ferretería · mejoras",
    }
    renta_m2_cat = {
        "Supermercado": 180, "Retail": 320, "Restaurantes": 420, "Educacion": 250,
        "Servicios": 380, "Salud": 300, "Entret": 280, "Cuidado": 400,
        "Mueb": 220, "MV": 200,
    }
    oportunidad = {}
    for k, gasto in demanda.items():
        vm2 = ventas_m2_anual.get(k)
        if gasto is not None and gasto > 0 and vm2:
            m2 = round(gasto * CAPTURA / vm2)
            if m2 > 0:
                oportunidad[k] = m2
    gla_target = round(sum(oportunidad.values())) if oportunidad else None

    # Demanda captable @ 15% (lo que un nuevo desarrollo puede capturar realísticamente)
    CAPTABLE_PCT = 0.15
    captable = {k: round(m2 * CAPTABLE_PCT) for k, m2 in oportunidad.items()}

    # Rangos de renta comercial $/m²/mes como texto (formato del template)
    renta_rango = {
        "Supermercado": "$160-200", "Retail": "$280-360", "Restaurantes": "$380-460",
        "Educacion": "$220-280", "Servicios": "$340-420", "Salud": "$260-340",
        "Entret": "$240-320", "Cuidado": "$360-440", "Mueb": "$200-260", "MV": "$180-240",
    }
    product_mix = []
    for k, m2 in sorted(oportunidad.items(), key=lambda kv: -kv[1]):
        product_mix.append({
            "giro": categoria_giro.get(k, k),
            "m2": m2,
            "pct": round(m2 / gla_target * 100, 1) if gla_target else 0,
            "tenant": tenant_ideal.get(k, k),
            "renta": renta_rango.get(k, "N/D"),
            "renta_m2": renta_m2_cat.get(k),
            "anchor": (k == "Supermercado"),
        })
    renta_low = None
    renta_high = None
    if gla_target and product_mix:
        renta_mensual = sum((p["m2"] * (p["renta_m2"] or 0)) for p in product_mix) * 0.85
        renta_low = round(renta_mensual / 1e6, 2)
        renta_high = round(renta_mensual * 1.35 / 1e6, 2)  # escenario alto (~+35%)

    # Formato abreviado del ingreso anual (texto que el front muestra como $XX.XB)
    def _fmt_abrev(v):
        if v is None:
            return None
        if v >= 1e9:
            return f"{v/1e9:.1f}B"
        if v >= 1e6:
            return f"{v/1e6:.1f}M"
        if v >= 1e3:
            return f"{v/1e3:.1f}k"
        return str(round(v))

    return {
        "ingreso_anual": _fmt_abrev(ing_total),
        "demanda": demanda,
        "oportunidad": oportunidad,
        "captable": captable,
        "product_mix": product_mix,
        "gla_target": gla_target,
        "renta_low": renta_low,
        "renta_high": renta_high,
    }


def _derive_comercio_OLD(agebs):
    cats = {
        "Supermercado": "Demanda Supermercado", "Retail": "Demanda Retail",
        "Restaurantes": "Demanda Restaurantes", "Educacion": "Demanda Educacion",
        "Servicios": "Demanda Servicios", "Salud": "Demanda CuidadodeSalud",
        "Entret": "Demanda Entretenimiento", "Cuidado": "Demanda Cuidado_personal",
        "Mueb": "Demanda Muebleria",
    }
    demanda = {}
    for k, col in cats.items():
        v = _sum(agebs, col)
        demanda[k] = round(v) if v is not None else None
    ing_total = _sum(agebs, "Ingresos totales 2026")

    # m² potenciales de oferta comercial por categoría (campos "... m2")
    cats_m2 = {
        "Supermercado": "Demanda Supermercado m2", "Retail": "Demanda Retail m2",
        "Restaurantes": "Demanda Restaurantes m2", "Educacion": "Demanda Educacion m2",
        "Servicios": "Demanda Servicios m2", "Salud": "Demanda CuidadodeSalud m2",
        "Entret": "Demanda Entretenimiento m2", "Cuidado": "Demanda Cuidado_personal m2",
        "Mueb": "Demanda Muebleria m2",
    }
    oportunidad = {}
    for k, col in cats_m2.items():
        v = _sum(agebs, col)
        if v is not None and v > 0:
            oportunidad[k] = round(v)
    gla_target = round(sum(oportunidad.values())) if oportunidad else None

    # Product mix comercial: distribuir GLA por categoría con tenant ideal y renta/m²
    tenant_ideal = {
        "Supermercado": "Supermercado ancla", "Retail": "Tiendas departamentales",
        "Restaurantes": "Food & beverage", "Educacion": "Academias / colegios",
        "Servicios": "Bancos / servicios", "Salud": "Clínica / farmacia",
        "Entret": "Cine / gimnasio", "Cuidado": "Spa / estética", "Mueb": "Mueblería / hogar",
    }
    renta_m2_cat = {  # renta comercial $/m²/mes típica por giro (referencia de mercado)
        "Supermercado": 180, "Retail": 320, "Restaurantes": 420, "Educacion": 250,
        "Servicios": 380, "Salud": 300, "Entret": 280, "Cuidado": 400, "Mueb": 220,
    }
    product_mix = []
    for k, m2 in sorted(oportunidad.items(), key=lambda kv: -kv[1]):
        is_anchor = (k == "Supermercado")
        product_mix.append({
            "giro": k, "m2": m2,
            "pct": round(m2 / gla_target * 100, 1) if gla_target else None,
            "tenant": tenant_ideal.get(k, k),
            "renta_m2": renta_m2_cat.get(k),
            "anchor": is_anchor,
        })
    # Renta estimada del centro comercial (escenario low): GLA × renta promedio × factor ocupación
    renta_low = None
    if gla_target and product_mix:
        renta_mensual = sum((p["m2"] * (p["renta_m2"] or 0)) for p in product_mix) * 0.85
        renta_low = round(renta_mensual / 1e6, 2)  # en M MXN/mes

    return {
        "ingreso_anual": round(ing_total) if ing_total else None,
        "demanda": demanda,
        "oportunidad": oportunidad,
        "product_mix": product_mix,
        "gla_target": gla_target,
        "renta_low": renta_low,
    }


# ╔══════════════ SECCIÓN 2: ENSAMBLADOR (assembler) ══════════════╗
from typing import Optional, List, Dict, Any


def _num(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if v == -1:
            return None
        return float(v)
    return None


def _price(v):
    n = _num(v)
    return n if (n is not None and n > 100000) else None


def _pm2v(v):
    n = _num(v)
    return n if (n is not None and n > 1000) else None


def _build_proyectos(resumen: List[Dict]) -> List[Dict[str, Any]]:
    out = []
    for row in resumen:
        a = row.get("attributes", {})
        g = row.get("geometry", {})
        lat = _num(g.get("y")) if g.get("y") is not None else _num(a.get("Y_coor"))
        lng = _num(g.get("x")) if g.get("x") is not None else _num(a.get("X_coor"))
        total = _num(a.get("UNIDADES_TOTALES"))
        disp = _num(a.get("UNIDADES_DISPONIBLES"))
        vend = _num(a.get("UNIDADES_VENDIDAS"))
        ticket = _num(a.get("F__UD_PROM"))
        pm2 = _num(a.get("F__M2_PROM"))
        absn = _num(a.get("ABSORCIÓN_PROYECTO"))
        avance = _num(a.get("AVANCE_COMERCIAL"))
        out.append({
            "name": a.get("PROYECTO") or a.get("Nombre") or "N/D",
            "lat": lat, "lng": lng,
            "abs": round(absn, 2) if absn is not None else None,
            "avance": round(avance * 100, 1) if avance is not None else None,
            "ticket": round(ticket / 1e6, 2) if ticket else None,
            "pm2": round(pm2) if pm2 else None,
            "total": int(total) if total else None,
            "disp": int(disp) if disp is not None else None,
            "vend": int(vend) if vend is not None else None,
        })
    return out


def _build_kpis(proyectos: List[Dict], ft: List[Dict]) -> Dict[str, Any]:
    total = sum(p["total"] for p in proyectos if p.get("total"))
    vend = sum(p["vend"] for p in proyectos if p.get("vend"))
    disp = sum(p["disp"] for p in proyectos if p.get("disp"))
    abs_vals = [p["abs"] for p in proyectos if p.get("abs")]
    avg_abs = round(sum(abs_vals) / len(abs_vals), 2) if abs_vals else None

    # ticket / pm2 ponderado por unidades
    tnum = tden = pnum = pden = 0.0
    for t in ft:
        a = t.get("attributes", {})
        precio = _price(a.get("F____UNIDAD")); pm2 = _pm2v(a.get("F___M2"))
        u = _num(a.get("UNIDADES_TOTALES")) or 0
        if precio and u:
            tnum += precio * u; tden += u
        if pm2 and u:
            pnum += pm2 * u; pden += u
    avg_ticket = round(tnum / tden / 1e6, 2) if tden else None
    avg_pm2 = round(pnum / pden) if pden else None

    return {
        "proyectos": len(proyectos),
        "unidades": total or None,
        "vendidas": vend or None,
        "disponibles": disp or None,
        "avg_abs": avg_abs, "avg_pm2": avg_pm2, "avg_ticket": avg_ticket,
    }


def _build_inventario(ft: List[Dict]) -> Dict[str, List]:
    PRICE = [(0, 2.5, "< $2.5M"), (2.5, 3.5, "$2.5M - $3.5M"), (3.5, 5.0, "$3.5M - $5.0M"),
             (5.0, 7.0, "$5.0M - $7.0M"), (7.0, 10.0, "$7.0M - $10.0M"),
             (10.0, 15.0, "$10.0M - $15.0M"), (15.0, 99.0, "> $15.0M")]
    M2 = [(0, 60, "< 60 m²"), (60, 80, "60-80 m²"), (80, 110, "80-110 m²"),
          (110, 150, "110-150 m²"), (150, 9999, "> 150 m²")]

    rows = []
    for t in ft:
        a = t.get("attributes", {})
        rows.append({
            "precio": _price(a.get("F____UNIDAD")), "m2": _num(a.get("ÁREA_PRIVATIVA")),
            "total": _num(a.get("UNIDADES_TOTALES")) or 0,
            "vend": _num(a.get("UNIDADES_VENDIDAS")) or 0,
        })
    total_units = sum(r["total"] for r in rows) or 0

    def bucketize(buckets, key, div):
        res = []
        for lo, hi, label in buckets:
            inb = [r for r in rows if r[key] is not None and lo <= r[key] / div < hi]
            uds = sum(r["total"] for r in inb)
            vend = sum(r["vend"] for r in inb)
            res.append({"rango": label, "uds": int(uds),
                        "pct": round(uds / total_units * 100, 1) if total_units else None,
                        "abs": None})
        return res

    return {
        "inventario_precio": bucketize(PRICE, "precio", 1e6),
        "inventario_m2": bucketize(M2, "m2", 1.0),
    }


def assemble_zone_payload(req, profile, isocronas, resumen, ft, pagos, resumen_renta,
                          demografia, nse_dim, segments, productos, productos_renta,
                          comercio, perception, agebs_count,
                          agebs=None, ft_renta=None) -> Dict[str, Any]:
    agebs = agebs or []
    ft_renta = ft_renta or []
    proyectos = _build_proyectos(resumen)
    kpis = _build_kpis(proyectos, ft)
    inv = _build_inventario(ft)

    # Centro = pin del predio
    center = [req.lat, req.lng]

    zone_name = req.zone_name or "Zona de análisis"
    municipio = req.municipio or "N/D"
    estado = req.estado or "N/D"

    # Derivaciones de demanda/renta que dependen de varios insumos
    renta_segmentos = derive_renta_segmentos(segments, agebs)
    demanda_segmentos = derive_demanda_segmentos(segments, productos)
    recamaras = derive_recamaras(agebs)

    # Enlazar m² y recámaras de los productos de renta a los renta_segmentos (por bucket)
    if productos_renta and renta_segmentos:
        pr_by_bucket = {p.get("seg_renta", "").split(" · ")[-1]: p for p in productos_renta}
        for rs in renta_segmentos:
            pr = pr_by_bucket.get(rs.get("seg"))
            if pr:
                if pr.get("m2") and pr["m2"] != "N/D":
                    rs["m2"] = pr["m2"].replace(" m²", "")
                if pr.get("rec") and pr["rec"] != "N/D":
                    rs["rec"] = pr["rec"]

    # Renta baseline para el simulador: medianas reales de la oferta de renta
    rentas_oferta = []
    m2_oferta = []
    for t in ft_renta:
        a = t.get("attributes", {})
        ap = _num(a.get("ÁREA_PRIVATIVA")); pr = _num(a.get("F____UNIDAD"))
        if ap and 25 <= ap <= 500 and pr and pr > 1000:
            rentas_oferta.append(pr / ap); m2_oferta.append(ap)
    rb_m2 = round(statistics.median(m2_oferta)) if m2_oferta else None
    rb_pm2 = round(statistics.median(rentas_oferta)) if rentas_oferta else None
    # Fallback: si no hay oferta de renta levantada, derivar del producto de renta featured (sweet spot)
    if (rb_m2 is None or rb_pm2 is None) and productos_renta:
        sweet = next((p for p in productos_renta if p.get("featured")), productos_renta[0])
        import re as _re
        if rb_m2 is None and sweet.get("m2") and sweet["m2"] != "N/D":
            nums = _re.findall(r"\d+", sweet["m2"])
            if nums:
                rb_m2 = int(nums[0])
        if rb_pm2 is None and sweet.get("pm2_renta") and sweet["pm2_renta"] != "N/D":
            pn = _re.findall(r"[\d,]+", sweet["pm2_renta"])
            if pn:
                rb_pm2 = int(pn[0].replace(",", ""))
    renta_baseline = {
        "m2": rb_m2, "pm2": rb_pm2,
        "units": 120 if rb_m2 else None,   # supuesto de proyecto típico para el simulador
        "occ": 90 if rb_m2 else None,
    }

    # Isócronas como GeoJSON (para que el tablero pinte los anillos)
    iso_out = {str(m): geo for m, geo in isocronas.items()}

    zone_data = {
        "name": zone_name,
        "subtitle": f"{municipio} · {estado} · México",
        "municipality": municipio,
        "label": f"Vivienda vertical · {kpis['proyectos']} proyectos · {kpis.get('unidades') or 'N/D'} unidades",
        "center": center, "zoom": 13,
        "population": demografia["population"],
        "households": demografia["households"],
        "tca": demografia["tca"],
        "personas_hogar": demografia["personas_hogar"],
        "ingreso_hogar": demografia["ingreso_hogar"],
        "ingreso_total_anual": demografia["ingreso_total_anual"],
        "nse": demografia["nse"],
        "nse_dominante": demografia["nse_dominante"],
        "tenencia": demografia["tenencia"],
        "hog_renta": demografia["hog_renta"],
        "edad_grupos": demografia["edad_grupos"],
        "recamaras": recamaras,
        "proyectos": proyectos,
        "kpis": kpis,
        "avgAbs": kpis["avg_abs"], "avgPm2": kpis["avg_pm2"],
        "inventario_precio": inv["inventario_precio"],
        "inventario_m2": inv["inventario_m2"],
        "productos": productos,
        "productos_renta": productos_renta,
        "renta_segmentos": renta_segmentos,
        "demanda_segmentos": demanda_segmentos,
        "renta_baseline": renta_baseline,
        "sensibilidad_baseline": _build_sensibilidad_baseline(productos, segments),
        "comercio": comercio,
        "ingreso_anual": comercio.get("ingreso_anual"),
        "renta_low": comercio.get("renta_low"),
        "renta_high": comercio.get("renta_high"),
        "demanda": comercio.get("demanda", {}),
        # Metadatos de la zona de análisis (sección Zona de análisis)
        "_zona_analisis": {
            "perfil_iso": profile["key"], "perfil_label": profile["label"],
            "isocronas": iso_out,
            "predio_m2": req.predio_m2, "uso_comercial": req.uso_comercial,
            "norm": req.norm.model_dump() if req.norm else None,
            "perception": {
                "n_total": perception["n_total"], "n_zona": perception["n_zona"],
                "media": round(perception["media"]) if perception.get("media") else None,
                "sd": round(perception["sd"]) if perception.get("sd") else None,
                "cv": round(perception["cv"], 4) if perception.get("cv") is not None else None,
                "barrera": perception["barrera"], "metodo": perception["metodo"],
                "cobertura_pct": perception["cobertura_pct"], "motivo": perception["motivo"],
                "proyectos": perception["proyectos"],
                "cluster_names": perception.get("cluster_names"),
                "ajuste_inventario": perception.get("ajuste_inventario"),
            },
            "nse_barrier": _nse_barrier_info(agebs),
        },
    }

    # DIM_DATA (para tplDemanda)
    totals = {
        "mkt_total": sum(s["mkt_total"] for s in segments),
        "mkt_venta": sum(s["mkt_venta"] for s in segments),
        "mkt_renta": sum(s["mkt_renta"] for s in segments),
        "nuevas_fam_anual": round(sum(s["nuevas_fam"] for s in segments), 1),
    }
    dim_data = {
        "nse_dim": nse_dim,
        "segments": segments,
        "totals": totals,
        "mercado_meta": _build_mercado_meta(nse_dim, demografia),
        "civil": _build_civil(agebs),
        "hog_comp": _build_hog_comp(agebs),
    }

    return {
        "ok": True,
        "meta": {
            "agebs": agebs_count,
            "proyectos_vvv": len(resumen),
            "tipologias_vvv": len(ft),
            "demografia_disponible": agebs_count > 0,
        },
        "zone_data": zone_data,
        "dim_data": dim_data,
    }


def _build_mercado_meta(nse_dim, demografia):
    if not nse_dim:
        return []
    # Mapea a la estructura de filas que el template indexa por [1..7]
    labels = [("Hogares", "hogares"), ("Niños (0-9)", "ninos"),
              ("Adolescentes (10-15)", "adolescentes"), ("Jóvenes (16-19)", "jovenes"),
              ("Jóvenes adultos (20-29)", "jov_adultos"), ("Consolidados (30-54)", "consolidados"),
              ("Adultos maduros (55+)", "empty_nest")]
    by_nse = {d["NSE"]: d for d in nse_dim}
    out = []
    for label, key in labels:
        row = {"label": label}
        total = 0
        for nse_k in ["A", "B", "C+", "C", "D+", "D", "E"]:
            v = round(by_nse.get(nse_k, {}).get(key, 0)) if by_nse.get(nse_k) else 0
            col = "Cm" if nse_k == "C+" else "Dm" if nse_k == "D+" else nse_k
            row[col] = v
            total += v
        row["Total"] = total
        row["pct"] = None
        out.append(row)
    # pct sobre población total (filas etarias) usando la fila Hogares como base poblacional alterna
    pob_total = sum(r["Total"] for r in out if r["label"].startswith(("Niños", "Adolesc", "Jóvenes", "Consolid", "Adultos")))
    for r in out:
        if r["label"].startswith(("Niños", "Adolesc", "Jóvenes", "Consolid", "Adultos")) and pob_total:
            r["pct"] = round(r["Total"] / pob_total * 100, 2)
    return out


def _build_civil(agebs):
    """Estado civil por grupo de edad (% sobre población del grupo). Desde campos C107-C166."""
    if not agebs:
        return {}
    grupos = ["20 a 24", "25 a 29", "30 a 34", "35 a 39", "40 a 44",
              "45 a 49", "50 a 54", "55 a 59", "60 a 64", "65 a 69", "70 a 74", "75 y Más"]
    estados = ["soltera", "casada", "en union libre", "separad  divorcia", "separad"]
    out = {}
    pob_total_zona = 0.0
    for r in agebs:
        pob_total_zona += _num(r.get("Población total 2026")) or _num(r.get("POB1")) or 0
    for g in grupos:
        acc = {"soltera": 0.0, "casada": 0.0, "union_libre": 0.0, "separada": 0.0, "no_esp": 0.0, "total": 0.0}
        present = False
        for r in agebs:
            s = _num(r.get(f"{g} soltera"))
            c = _num(r.get(f"{g} casada"))
            u = _num(r.get(f"{g} en union libre"))
            sep = _num(r.get(f"{g} separad  divorcia"))
            if sep is None:
                sep = _num(r.get(f"{g} separad"))
            if any(x is not None for x in [s, c, u, sep]):
                present = True
                acc["soltera"] += s or 0
                acc["casada"] += c or 0
                acc["union_libre"] += u or 0
                acc["separada"] += sep or 0
        if not present:
            continue
        tot = acc["soltera"] + acc["casada"] + acc["union_libre"] + acc["separada"]
        acc["total"] = tot
        if tot <= 0:
            continue
        out[g] = {
            "pob_pct": round(tot / pob_total_zona * 100, 2) if pob_total_zona else 0,
            "soltera": round(acc["soltera"] / tot * 100, 2),
            "casada": round(acc["casada"] / tot * 100, 2),
            "union_libre": round(acc["union_libre"] / tot * 100, 2),
            "separada": round(acc["separada"] / tot * 100, 2),
            "no_esp": 0.0,
        }
    return out


def _build_sensibilidad_baseline(productos, segments):
    """Baseline del simulador de Producto: del producto featured (sweet spot) o el primero recomendado."""
    import re as _re
    base = next((p for p in productos if p.get("featured")), None)
    if base is None:
        base = next((p for p in productos if p.get("recomendado")), None)
    if base is None and productos:
        base = productos[0]
    if base is None:
        return {"m2": None, "pm2": None, "abs_base": None, "ticket_base": None}

    def _parse_int(s):
        nums = _re.findall(r"[\d,]+", str(s).replace(",", ""))
        return int(nums[0]) if nums else None
    def _parse_float(s):
        nums = _re.findall(r"[\d.]+", str(s))
        return float(nums[0]) if nums else None

    m2 = _parse_int(base.get("m2")) if base.get("m2") != "N/D" else None
    pm2 = _parse_int(base.get("pm2")) if base.get("pm2") != "N/D" else None
    ticket = _parse_float(base.get("ticket")) if base.get("ticket") != "N/D" else None
    # abs base: la MISMA absorción que muestra el producto featured (incluye evidencia/competencia),
    # para que el simulador de sensibilidad parta del valor visible. Fallback: nuevas_fam/12.
    abs_base = None
    if base.get("abs") and base["abs"] != "N/D":
        abs_base = _parse_float(base["abs"])   # "2.2 un/mes" → 2.2
    if abs_base is None and base.get("nuevas_fam"):
        abs_base = round(base["nuevas_fam"] / 12, 2)
    return {"m2": m2, "pm2": pm2, "abs_base": abs_base, "ticket_base": ticket}


def _build_hog_comp(agebs):
    """Composición de hogares (C60-C67). Valores absolutos."""
    if not agebs:
        return {"familiares_total": None, "no_familiares_total": None, "nucleares": None,
                "ampliados": None, "compuestos": None, "unipersonal": None, "corresidentes": None}
    def s(col):
        v = _sum(agebs, col)
        return round(v) if v is not None else 0
    return {
        "familiares_total": s("Hogares familiares totales"),
        "nucleares": s("Hogares nucleares"),
        "ampliados": s("Hogares  ampliados"),
        "compuestos": s("Hogares compuestos"),
        "no_familiares_total": s("Hogares  no familiares totales"),
        "unipersonal": s("Hogares unipersonales"),
        "corresidentes": s("Hogares corresidentes"),
    }


def _perfiles_por_segmento(nse, m2, ticket_M):
    """
    Asigna perfiles de comprador (PROFILE_CATALOG estándar) según NSE, tamaño y ticket.
    La demanda se mide por PERFIL de comprador, no solo por bucket de precio.
    Universal para todo México.
    """
    perfiles = []
    m2 = m2 or 0
    # Por tamaño (tipología) → ciclo de vida del comprador
    if m2 and m2 < 50:
        perfiles += ["joven_profesional", "inversionista", "soltero"]
    elif m2 < 75:
        perfiles += ["dink_accesible", "joven_profesional", "inversionista"]
    elif m2 < 110:
        perfiles += ["familia_joven", "dink_premium", "foraneo_ejecutivo"]
    elif m2 < 160:
        perfiles += ["familia_consolidada", "familia_joven", "empty_nester"]
    else:
        perfiles += ["familia_consolidada", "empty_nester", "inversionista"]
    # Por NSE (poder adquisitivo) → matiz premium/accesible
    if nse in ("A", "B") and "dink_premium" not in perfiles:
        perfiles.append("dink_premium")
    if nse in ("D+", "D", "E") and "soltero" not in perfiles:
        perfiles.append("soltero")
    # Tickets muy altos → patrimonial/inversionista
    if ticket_M and ticket_M >= 12 and "inversionista" not in perfiles:
        perfiles.append("inversionista")
    # Únicos, máximo 3
    seen = []
    for p in perfiles:
        if p not in seen:
            seen.append(p)
    return seen[:3]


# Etiquetas legibles del perfil de comprador (para el campo "perfil" de la tabla de demanda)
PERFIL_LABEL = {
    "joven_profesional": "Joven profesional", "dink_accesible": "DINK accesible",
    "familia_joven": "Familia joven", "familia_consolidada": "Familia consolidada",
    "dink_premium": "DINK premium", "empty_nester": "Empty nester",
    "inversionista": "Inversionista", "foraneo_ejecutivo": "Foráneo ejecutivo",
    "soltero": "Soltero/a",
}


def derive_demanda_segmentos(segments, productos=None):
    """Tabla superior de Demanda (z.demanda_segmentos). Mide por PERFIL de comprador.
    Toma m² y absorción de los productos derivados y asigna el perfil de comprador real."""
    productos = productos or []
    prod_by_bucket = {}
    for p in productos:
        prod_by_bucket[p.get("seg_dim", "")] = p
    total_mkt = max(sum(x["mkt_venta"] for x in segments), 1)
    out = []
    for s in segments:
        if s.get("status") in ("bajo_crecimiento",):
            continue
        key = f"{s['NSE']} · {s['bucket']}"
        prod = prod_by_bucket.get(key)
        # m² y absorción del producto correspondiente
        m2_num = None
        m2 = "N/D"
        if prod and prod.get("m2") and prod["m2"] != "N/D":
            m2 = prod["m2"].replace(" m²", "")
            try: m2_num = int(m2)
            except ValueError: m2_num = None
        abs_val = "N/D"
        if prod and prod.get("abs") and prod["abs"] != "N/D":
            abs_val = prod["abs"].replace(" un/mes", "")
        # Ticket coherente (bucket inferior val_min=0 → usar val_max*0.75)
        vmin = s.get("val_min"); vmax = s.get("val_max")
        if vmin and vmax:
            ticket_M = (vmin + vmax) / 2 / 1e6
        elif vmax:
            ticket_M = vmax * 0.75 / 1e6
        else:
            ticket_M = None
        ticket_str = f"${ticket_M:.2f}M" if ticket_M else "N/D"
        # PERFIL de comprador (no status)
        perfiles = _perfiles_por_segmento(s["NSE"], m2_num, ticket_M)
        perfil_label = " · ".join(PERFIL_LABEL.get(p, p) for p in perfiles[:2]) if perfiles else "N/D"
        out.append({
            "segmento": prod.get("tipo") if prod else f"NSE {s['NSE']}",
            "perfil": perfil_label,
            "nse": s["NSE"],
            "ticket": ticket_str,
            "m2": m2,
            "abs": abs_val,
            "mix": round(s["mkt_venta"] / total_mkt * 100) if s.get("mkt_venta") else 0,
            "perfiles": perfiles,
            "origen": s.get("origen", "demand_driven"),
        })
    return out


def derive_renta_segmentos(segments, agebs=None):
    """
    Segmentos de renta (z.renta_segmentos) derivados de los mismos segments DPO de venta.
    Cada bucket de valor de vivienda tiene su renta-equivalente mensual (rent_min/rent_max,
    ~0.4% del valor) y su mercado de renta (mkt_renta = hogares que rentan en el bucket).
    Universal: la renta se ancla a la capacidad de compra y a la propensión a rentar de la zona.
    """
    if not segments:
        return []
    # Sweet spot de renta = bucket con mayor mercado de renta (mkt_renta)
    best = max(segments, key=lambda s: s.get("mkt_renta", 0) or 0, default=None)
    out = []
    for s in segments:
        if s.get("status") == "bajo_crecimiento":
            continue
        rent_min = s.get("rent_min"); rent_max = s.get("rent_max")
        ing_min = s.get("ing_min"); ing_max = s.get("ing_max")
        # m² del segmento: lo toma del producto de venta correspondiente si existe; si no, N/D
        out.append({
            "seg": s.get("bucket", "N/D"),
            "perfil": _status_label(s.get("status", "")),
            "nse": s.get("NSE", "N/D"),
            "ing": (f"${round(ing_min/1000)}k-${round(ing_max/1000)}k"
                    if ing_min and ing_max else "N/D"),
            "renta": (f"${round(rent_min/1000,1)}k-${round(rent_max/1000,1)}k"
                      if rent_min is not None and rent_max else "N/D"),
            "rent_min": rent_min, "rent_max": rent_max,
            "rec": "N/D",   # se completa desde el producto de renta
            "m2": "N/D",    # se completa desde el producto de renta
            "hog": round(s.get("mkt_renta", 0)) if s.get("mkt_renta") else 0,
            "mkt_renta": s.get("mkt_renta", 0),
            "nuevas_fam": s.get("nuevas_fam", 0),
            "sweet": (best is not None and s is best),
        })
    return out


def derive_recamaras(agebs):
    """
    Distribución % de recámaras demandadas, derivada de la composición de hogares:
      1 rec ← unipersonales + corresidentes
      2 rec ← nucleares (parejas/familias jóvenes) · principal demanda vertical
      3 rec ← ampliados + compuestos (familias grandes)
    Devuelve [%1rec, %2rec, %3rec, %4+rec]. Si no hay data → None (N/D).
    """
    if not agebs:
        return None
    def s(col):
        v = _sum(agebs, col)
        return v if v is not None else 0
    uni = s("Hogares unipersonales") + s("Hogares corresidentes")
    nuc = s("Hogares nucleares")
    amp = s("Hogares  ampliados") + s("Hogares compuestos")
    total = uni + nuc + amp
    if total <= 0:
        return None
    # 2 rec captura nucleares + parte de unipersonales (DINK); 1 rec resto unipersonal
    r1 = uni * 0.55
    r2 = nuc * 0.70 + uni * 0.45
    r3 = nuc * 0.30 + amp * 0.70
    r4 = amp * 0.30
    tot = r1 + r2 + r3 + r4
    if tot <= 0:
        return None
    return [round(r1 / tot * 100, 1), round(r2 / tot * 100, 1),
            round(r3 / tot * 100, 1), round(r4 / tot * 100, 1)]


# ╔══════════════ SECCIÓN 3: SERVIDOR FASTAPI (main) ══════════════╗
import os
import io
import zipfile
import statistics
from typing import Optional, List, Dict, Any

import httpx
import openpyxl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


PRSP_BASE = os.environ.get("PRSP_BASE", "https://payment-system-prsp.onrender.com")
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "180"))

app = FastAPI(title="Dataria Orchestrator", version="2.0")

# CORS abierto para que el tablero (servido en cualquier origen http/https) consuma el API.
# Para producción, restringir allow_origins a los dominios de Dataria.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════════════════
# ARQUITECTURA MODULAR POR SECCIÓN · REGISTRO + CONTROL DE ACCESO
# ════════════════════════════════════════════════════════════════════════════
# Cada sección del tablero es un módulo lógico independiente: se puede optimizar,
# cambiar, agregar o eliminar SIN tocar las demás. El orquestador (zona_procesar)
# ensambla las secciones habilitadas. Esto prepara el terreno para las 3 secciones
# nuevas (vivienda_horizontal, lotes_urbanizados, explorador_nacional).
#
# Cada entrada declara:
#   • key          identificador estable de la sección
#   • label        nombre legible
#   • payload_keys campos del zone_data/dim_data que produce (para filtrado de acceso)
#   • access_tier  "preliminar" (visible en evaluación general) | "detalle" (requiere permiso)
#   • page_id      id de la página en el front (para habilitar/deshabilitar UI)
# La función derivadora vive en su propia función derive_* (ya modular); aquí solo
# se registra el metadato que permite ensamblar, filtrar por acceso y extender.

SECTION_REGISTRY = {
    "resumen":    {"label": "Resumen ejecutivo", "page_id": "page-resumen",
                   "access_tier": "preliminar", "payload_keys": ["name", "subtitle", "kpis"]},
    "mapa":       {"label": "Mapa de zona", "page_id": "page-mapa",
                   "access_tier": "preliminar", "payload_keys": ["center", "proyectos", "isocronas"]},
    "demografia": {"label": "Demografía / NSE", "page_id": "page-resumen",
                   "access_tier": "preliminar", "payload_keys": ["population", "households", "nse", "nse_dominante"]},
    "inventario": {"label": "Inventario / Oferta", "page_id": "page-inventario",
                   "access_tier": "detalle", "payload_keys": ["inventario_precio", "inventario_m2", "proyectos"]},
    "demanda":    {"label": "Demanda por perfil", "page_id": "page-demanda",
                   "access_tier": "detalle", "payload_keys": ["demanda_segmentos", "mercado_meta", "civil"]},
    "producto":   {"label": "Producto óptimo (DPO)", "page_id": "page-producto",
                   "access_tier": "detalle", "payload_keys": ["productos", "sensibilidad_baseline"]},
    "renta":      {"label": "Mercado de renta", "page_id": "page-renta",
                   "access_tier": "detalle", "payload_keys": ["productos_renta", "renta_segmentos", "renta_baseline"]},
    "comercio":   {"label": "Comercio / Tenant mix", "page_id": "page-comercio",
                   "access_tier": "detalle", "payload_keys": ["comercio"]},
    "mezcla":     {"label": "Crea tu mezcla · Venta", "page_id": "page-mezcla",
                   "access_tier": "detalle", "payload_keys": ["productos"]},
    "mezcla_renta": {"label": "Crea tu mezcla · Renta", "page_id": "page-mezclaRenta",
                   "access_tier": "detalle", "payload_keys": ["productos_renta"]},
    "monitor":    {"label": "Monitorea tu proyecto", "page_id": "page-monitor",
                   "access_tier": "detalle", "payload_keys": ["productos", "proyectos"]},
    # ── Secciones nuevas (andamiaje · se implementarán en el siguiente paso) ──
    "vivienda_horizontal": {"label": "Vivienda horizontal", "page_id": "page-vivienda-horizontal",
                   "access_tier": "detalle", "payload_keys": ["vivienda_horizontal"], "scaffold": True},
    "lotes_urbanizados": {"label": "Venta de lotes urbanizados", "page_id": "page-lotes",
                   "access_tier": "detalle", "payload_keys": ["lotes_urbanizados"], "scaffold": True},
    "explorador_nacional": {"label": "Explorador nacional", "page_id": "page-explorador",
                   "access_tier": "preliminar", "payload_keys": ["explorador_nacional"], "scaffold": True},
}


def section_keys(include_scaffold: bool = False) -> List[str]:
    """Lista de secciones registradas. Por defecto excluye las de andamiaje (aún no implementadas)."""
    return [k for k, v in SECTION_REGISTRY.items() if include_scaffold or not v.get("scaffold")]


# ── Control de acceso por cuenta (preparación del modelo de operación) ──
# Cada cuenta declara: secciones habilitadas y zonas autorizadas para DETALLE.
# El acceso GENERAL (preliminar) está disponible aunque el DETALLE esté restringido:
# así un usuario puede hacer evaluaciones preliminares de cualquier zona, pero solo
# ve el detalle completo de las zonas que tiene autorizadas.

ACCESS_PRELIMINAR = "preliminar"   # KPIs generales, mapa, demografía, NSE dominante
ACCESS_DETALLE = "detalle"         # producto, demanda, renta, comercio, mezcla, monitor


def filter_payload_by_access(payload: Dict[str, Any], permisos: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Filtra el payload de una zona según los permisos de la cuenta.
    permisos = {
        "secciones": ["resumen","mapa",...] | "*",   # secciones habilitadas
        "zonas_detalle": ["ZMM_VallePoniente",...] | "*",  # zonas con acceso a DETALLE
        "zona_actual": "ZMM_Centro",
    }
    Si la zona actual NO está autorizada para detalle, se entregan SOLO las secciones de
    tier 'preliminar' (evaluación general), y las de 'detalle' se sustituyen por un marcador
    de acceso restringido (sin exponer datos). Si permisos es None → acceso completo (admin/local).
    """
    if not permisos:
        return payload   # sin restricciones (modo local/admin)

    secciones_hab = permisos.get("secciones", "*")
    zonas_detalle = permisos.get("zonas_detalle", "*")
    zona_actual = permisos.get("zona_actual")

    zona_autorizada_detalle = (zonas_detalle == "*" or
                               (zona_actual and zona_actual in (zonas_detalle or [])))

    out = dict(payload)
    z = dict(payload.get("zone_data", {}))
    restringidas = []

    for key, meta in SECTION_REGISTRY.items():
        if meta.get("scaffold"):
            continue
        # ¿La sección está habilitada para esta cuenta?
        sec_habilitada = (secciones_hab == "*" or key in (secciones_hab or []))
        # ¿Requiere detalle y la zona no está autorizada?
        es_detalle = meta["access_tier"] == ACCESS_DETALLE
        bloquear = (not sec_habilitada) or (es_detalle and not zona_autorizada_detalle)
        if bloquear:
            for pk in meta["payload_keys"]:
                if pk in z:
                    z[pk] = None   # se oculta el dato (el front muestra "acceso restringido")
            restringidas.append(key)

    out["zone_data"] = z
    out["_access"] = {
        "zona_autorizada_detalle": bool(zona_autorizada_detalle),
        "secciones_restringidas": sorted(set(restringidas)),
        "modo": "detalle" if zona_autorizada_detalle else "preliminar",
    }
    return out



class Normatividad(BaseModel):
    usos: Optional[str] = None
    densidad: Optional[float] = None
    altura: Optional[float] = None
    cus: Optional[float] = None
    cos: Optional[float] = None
    cav: Optional[float] = None
    estac: Optional[str] = None


class ZonaRequest(BaseModel):
    lat: float
    lng: float
    predio_m2: Optional[float] = None
    uso_comercial: bool = False
    zone_name: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    norm: Optional[Normatividad] = None


# ──────────────────────── Clientes de servicios ────────────────────────
async def fetch_isochrone(client: httpx.AsyncClient, lat: float, lng: float, minutes: int) -> Dict:
    r = await client.post(f"{PRSP_BASE}/api/predik/isochrone", json={
        "latitude": lat, "longitude": lng, "minutes": minutes, "transport_type": "driving"
    })
    r.raise_for_status()
    geo = r.json()
    if geo.get("type") != "Polygon" or "coordinates" not in geo:
        raise HTTPException(502, f"Isócrona inválida para {minutes} min")
    return geo


async def fetch_vvv(client: httpx.AsyncClient, ring: List[List[float]], tipo: str = "vv_venta") -> Dict:
    body = {
        "tipo": tipo,
        "geometry": {"rings": [ring], "spatialReference": {"wkid": 4326}},
        "filters": {},
        "returnGeometry": True,
        "resultRecordCount": 500,
    }
    r = await client.post(f"{PRSP_BASE}/api/v1/vvv/query", json=body)
    r.raise_for_status()
    return r.json()


async def fetch_descarga_di(client: httpx.AsyncClient, ring: List[List[float]], active_map: str = "NSE") -> Optional[bytes]:
    body = {
        "activeMap": active_map,
        "cliente": "Dataria",
        "proyecto": "ZonaAnalisis",
        "geometry": {"rings": [ring], "spatialReference": {"wkid": 4326}},
    }
    r = await client.post(f"{PRSP_BASE}/api/descargas/di/export", json=body)
    if r.status_code != 200:
        # 413 (demasiados registros) u otro → devolvemos None; demografía quedará N/D
        return None
    if not r.content.startswith(b"PK"):
        return None
    return r.content


def parse_di_xlsx(zip_bytes: bytes) -> List[Dict[str, Any]]:
    """Extrae los AGEBs del ZIP de DescargaDI como lista de dicts {header: value}."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    xlsx_name = next((n for n in z.namelist() if n.endswith(".xlsx")), None)
    if not xlsx_name:
        return []
    wb = openpyxl.load_workbook(io.BytesIO(z.read(xlsx_name)), data_only=True)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    rows = []
    for r in range(2, ws.max_row + 1):
        rec = {}
        empty = True
        for ci, h in enumerate(headers, 1):
            if h is None:
                continue
            v = ws.cell(r, ci).value
            rec[str(h).strip()] = v
            if v not in (None, ""):
                empty = False
        if not empty:
            rows.append(rec)
    return rows


# ──────────────────────── Endpoint principal ────────────────────────
@app.get("/health")
async def health():
    return {"ok": True, "service": "dataria-orchestrator", "version": "2.0", "stages": ["poligono", "procesar", "analyze"]}


@app.post("/api/zona/analyze")
async def analyze(req: ZonaRequest):
    profile = isochrone_profile(req.predio_m2, req.uso_comercial)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        # 1 · Isócronas (todas las del perfil)
        isocronas: Dict[int, Dict] = {}
        try:
            for m in profile["minutos"]:
                isocronas[m] = await fetch_isochrone(client, req.lat, req.lng, m)
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Predik no disponible: {e}")

        # Anillo base para intersección = 8 min (siempre presente) o principal
        base_min = 8 if 8 in isocronas else profile["principal"]
        base_ring = isocronas[base_min]["coordinates"][0]

        # 2 · Oferta (VVV) venta + renta
        try:
            vvv_venta = await fetch_vvv(client, base_ring, "vv_venta")
            vvv_renta = await fetch_vvv(client, base_ring, "vv_renta")
        except httpx.HTTPError as e:
            raise HTTPException(502, f"VVV no disponible: {e}")

        # 3 · Demografía (DescargaDI · NSE acotado por isócrona)
        di_bytes = await fetch_descarga_di(client, base_ring, "NSE")

    agebs = parse_di_xlsx(di_bytes) if di_bytes else []

    # ── Derivación VVV: proyectos resumen + tipologías ft ──
    resumen = vvv_venta.get("datasets", {}).get("resumen", [])
    ft = vvv_venta.get("datasets", {}).get("ft", [])
    pagos = vvv_venta.get("datasets", {}).get("pagos", [])
    resumen_renta = vvv_renta.get("datasets", {}).get("resumen", [])
    ft_renta = vvv_renta.get("datasets", {}).get("ft", [])

    # Percepción de valor + ajuste de zona de influencia (CV)
    perception = value_perception_adjust(resumen, base_ring)

    # ── Derivación DIGO/DPO ──
    demografia = derive_demografia(agebs, ft)         # population, households, tca, nse, tenencia...
    nse_dim = derive_nse_dim(agebs)                   # nse_dim[] para DIM_DATA
    segments = derive_segments(agebs, ft)             # 12 buckets de demanda
    productos = derive_productos_venta(ft, segments)  # productos venta
    productos_renta = derive_productos_renta(ft_renta, segments)  # productos renta
    comercio = derive_comercio(agebs)                 # potencial comercio/retail

    # ── Ensamblaje del payload (esquema que consume el template) ──
    payload = assemble_zone_payload(
        req=req, profile=profile, isocronas=isocronas,
        resumen=resumen, ft=ft, pagos=pagos,
        resumen_renta=resumen_renta,
        demografia=demografia, nse_dim=nse_dim, segments=segments,
        productos=productos, productos_renta=productos_renta,
        comercio=comercio, perception=perception, agebs_count=len(agebs),
        agebs=agebs, ft_renta=ft_renta,
    )
    return payload


# ════════════════════════════════════════════════════════════════
# FLUJO EN DOS ETAPAS
#   Etapa 1: /api/zona/poligono  → SOLO Predik. Rápido. Devuelve la
#            isócrona para que el tablero pinte el polígono de inmediato.
#   Etapa 2: /api/zona/procesar  → VVV + DescargaDI + derivaciones.
#            Llena el resto de secciones. Tolerante a fallos por bloque.
# ════════════════════════════════════════════════════════════════

@app.post("/api/zona/poligono")
async def zona_poligono(req: ZonaRequest):
    """ETAPA 1 (rápida): devuelve solo las isócronas. No depende de VVV ni DescargaDI."""
    profile = isochrone_profile(req.predio_m2, req.uso_comercial)
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        isocronas: Dict[int, Dict] = {}
        try:
            for m in profile["minutos"]:
                isocronas[m] = await fetch_isochrone(client, req.lat, req.lng, m)
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Predik no disponible: {e}")
    return {
        "ok": True,
        "stage": "poligono",
        "perfil_iso": profile["key"],
        "perfil_label": profile["label"],
        "minutos": profile["minutos"],
        "principal": profile["principal"],
        "isocronas": {str(m): geo for m, geo in isocronas.items()},
        "center": [req.lat, req.lng],
    }


@app.post("/api/zona/procesar")
async def zona_procesar(req: ZonaRequest):
    """
    ETAPA 2 (pesada): toma el mismo input, recalcula la isócrona base y
    procesa VVV + DescargaDI + derivaciones. Devuelve el payload completo.
    Cada bloque está aislado: si uno falla, los demás se entregan igual y
    se reporta el error en `errors` sin tumbar toda la respuesta.
    """
    profile = isochrone_profile(req.predio_m2, req.uso_comercial)
    errors = {}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        # Isócrona base (8 min o principal) — necesaria para acotar VVV/DI
        try:
            base_min = 8 if 8 in profile["minutos"] else profile["principal"]
            base_iso = await fetch_isochrone(client, req.lat, req.lng, base_min)
            isocronas = {base_min: base_iso}
            # Las demás isócronas del perfil (para pintar anillos), tolerante a fallo
            for m in profile["minutos"]:
                if m not in isocronas:
                    try:
                        isocronas[m] = await fetch_isochrone(client, req.lat, req.lng, m)
                    except Exception:
                        pass
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Predik no disponible: {e}")
        base_ring = isocronas[base_min]["coordinates"][0]

        # VVV (oferta) — si falla, seguimos con listas vacías
        vvv_venta, vvv_renta = {}, {}
        try:
            vvv_venta = await fetch_vvv(client, base_ring, "vv_venta")
        except Exception as e:
            errors["vvv_venta"] = str(e)
        try:
            vvv_renta = await fetch_vvv(client, base_ring, "vv_renta")
        except Exception as e:
            errors["vvv_renta"] = str(e)

        # DescargaDI (demografía) — si falla, demografía queda N/D
        di_bytes = None
        try:
            di_bytes = await fetch_descarga_di(client, base_ring, "NSE")
        except Exception as e:
            errors["descarga_di"] = str(e)

    # FILTRO ESPACIAL: garantizar que solo entren proyectos/tipologías DENTRO del polígono
    vvv_venta = filter_vvv_by_polygon(vvv_venta, base_ring)
    vvv_renta = filter_vvv_by_polygon(vvv_renta, base_ring)
    if vvv_venta.get("_spatial_filter"):
        sf = vvv_venta["_spatial_filter"]
        if sf["resumen_total"] > sf["resumen_in"] or sf["ft_total"] > sf["ft_in"]:
            errors["filtro_espacial"] = (f"VVV devolvió fuera de zona: "
                f"resumen {sf['resumen_total']}→{sf['resumen_in']}, ft {sf['ft_total']}→{sf['ft_in']}")

    agebs = parse_di_xlsx(di_bytes) if di_bytes else []
    resumen = vvv_venta.get("datasets", {}).get("resumen", [])
    ft = vvv_venta.get("datasets", {}).get("ft", [])
    pagos = vvv_venta.get("datasets", {}).get("pagos", [])
    resumen_renta = vvv_renta.get("datasets", {}).get("resumen", [])
    ft_renta = vvv_renta.get("datasets", {}).get("ft", [])

    # Cada derivación aislada
    def _safe(fn, label, default):
        try:
            return fn()
        except Exception as e:
            errors[label] = str(e)
            return default

    perception = _safe(lambda: value_perception_adjust(resumen, base_ring), "perception",
                       {"n_total": 0, "n_zona": 0, "media": None, "sd": None, "cv": None,
                        "barrera": False, "metodo": "isocrona", "cobertura_pct": 0,
                        "motivo": "No disponible", "proyectos": [], "cluster_names": None})

    # ── ZONA AJUSTADA POR CLÚSTER DE VALOR (CV) ──
    # Si hay barrera de valor, el inventario/KPIs/productos/mapa se restringen al clúster
    # de alto valor que define la percepción. Universal: aplica solo cuando hay barrera.
    cluster_names = perception.get("cluster_names")
    if cluster_names:
        before_r, before_ft = len(resumen), len(ft)
        resumen = [r for r in resumen if r.get("attributes", {}).get("PROYECTO") in cluster_names]
        ft = [t for t in ft if t.get("attributes", {}).get("PROYECTO") in cluster_names]
        pagos = [p for p in pagos if p.get("attributes", {}).get("PROYECTO") in cluster_names]
        perception["ajuste_inventario"] = (
            f"Zona ajustada por barrera de valor (CV={round(perception.get('cv') or 0, 2)}): "
            f"inventario recortado al clúster de alto valor "
            f"(proyectos {before_r}→{len(resumen)}, tipologías {before_ft}→{len(ft)})")

    demografia = _safe(lambda: derive_demografia(agebs, ft), "demografia", derive_demografia([]))
    nse_dim = _safe(lambda: derive_nse_dim(agebs), "nse_dim", [])
    segments = _safe(lambda: derive_segments(agebs, ft), "segments", [])
    productos = _safe(lambda: derive_productos_venta(ft, segments), "productos", [])
    productos_renta = _safe(lambda: derive_productos_renta(ft_renta, segments), "productos_renta", [])
    comercio = _safe(lambda: derive_comercio(agebs), "comercio", {})

    # cluster_names es un set (no serializable) → convertir a lista para el payload
    if isinstance(perception.get("cluster_names"), set):
        perception["cluster_names"] = sorted(perception["cluster_names"])

    payload = assemble_zone_payload(
        req=req, profile=profile, isocronas=isocronas,
        resumen=resumen, ft=ft, pagos=pagos, resumen_renta=resumen_renta,
        demografia=demografia, nse_dim=nse_dim, segments=segments,
        productos=productos, productos_renta=productos_renta,
        comercio=comercio, perception=perception, agebs_count=len(agebs),
        agebs=agebs, ft_renta=ft_renta,
    )
    payload["stage"] = "procesar"
    payload["errors"] = errors
    return payload


# ════════════════════════════════════════════════════════════════════════════
# CUENTAS DE USUARIO Y CONTROL DE ACCESO (modelo de operación)
# ════════════════════════════════════════════════════════════════════════════
# Preparación del backend para generar cuentas con atributos de acceso por sección
# y por zona. Almacén en memoria (sustituible por DB/identidad real en producción).
# El objetivo operativo: restringir el acceso DETALLADO a zonas no autorizadas,
# manteniendo el acceso GENERAL (preliminar) disponible para evaluaciones.

class CuentaCreate(BaseModel):
    usuario: str
    nombre: Optional[str] = None
    # Secciones habilitadas: lista de keys de SECTION_REGISTRY, o "*" para todas
    secciones: Any = "*"
    # Zonas con acceso a DETALLE: lista de zone_name, o "*" para todas
    zonas_detalle: Any = "*"
    # Rol informativo (no controla acceso por sí solo)
    rol: Optional[str] = "analista"


# Almacén en memoria (no persistente entre reinicios; en producción → base de datos)
_CUENTAS: Dict[str, Dict[str, Any]] = {}


def _cuenta_to_permisos(cuenta: Dict[str, Any], zona_actual: Optional[str]) -> Dict[str, Any]:
    return {
        "secciones": cuenta.get("secciones", "*"),
        "zonas_detalle": cuenta.get("zonas_detalle", "*"),
        "zona_actual": zona_actual,
    }


@app.get("/api/secciones")
def listar_secciones():
    """Devuelve el registro de secciones (para que el front sepa qué habilitar/mostrar)."""
    return {
        "secciones": [
            {"key": k, "label": v["label"], "page_id": v["page_id"],
             "access_tier": v["access_tier"], "scaffold": v.get("scaffold", False)}
            for k, v in SECTION_REGISTRY.items()
        ],
        "activas": section_keys(),
    }


@app.post("/api/cuentas")
def crear_cuenta(c: CuentaCreate):
    """Crea/actualiza una cuenta con sus atributos de acceso por sección y por zona."""
    _CUENTAS[c.usuario] = {
        "usuario": c.usuario, "nombre": c.nombre or c.usuario,
        "secciones": c.secciones, "zonas_detalle": c.zonas_detalle, "rol": c.rol,
    }
    return {"ok": True, "cuenta": _CUENTAS[c.usuario]}


@app.get("/api/cuentas")
def listar_cuentas():
    return {"cuentas": list(_CUENTAS.values())}


@app.get("/api/cuentas/{usuario}")
def obtener_cuenta(usuario: str):
    c = _CUENTAS.get(usuario)
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    return c


@app.delete("/api/cuentas/{usuario}")
def borrar_cuenta(usuario: str):
    if usuario in _CUENTAS:
        del _CUENTAS[usuario]
        return {"ok": True}
    raise HTTPException(404, "Cuenta no encontrada")


class ZonaProcesarAuth(ZonaRequest):
    """zona/procesar con identidad opcional: si se envía `usuario`, el payload se filtra
    según los permisos de la cuenta (detalle vs preliminar). Sin usuario → acceso completo."""
    usuario: Optional[str] = None


@app.post("/api/zona/procesar_auth")
async def zona_procesar_auth(req: ZonaProcesarAuth):
    """
    Igual que /api/zona/procesar pero aplica control de acceso por cuenta.
    Si la zona no está autorizada para detalle, devuelve solo la vista preliminar.
    """
    base = ZonaRequest(**{k: getattr(req, k) for k in ZonaRequest.model_fields})
    payload = await zona_procesar(base)
    if req.usuario:
        cuenta = _CUENTAS.get(req.usuario)
        if not cuenta:
            raise HTTPException(403, "Cuenta no encontrada o sin permisos")
        permisos = _cuenta_to_permisos(cuenta, req.zone_name)
        payload = filter_payload_by_access(payload, permisos)
    return payload
