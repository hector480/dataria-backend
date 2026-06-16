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

    # Cobertura aproximada: fracción de proyectos de alto valor dentro de la isócrona
    # (en backend usamos proporción de proyectos como proxy del 20% de área)
    cobertura = len(altos) / max(len(dentro), 1)
    out["cobertura_pct"] = round(cobertura * 100)
    if cobertura >= COBERTURA_MIN:
        out["metodo"] = "cluster_alto_valor"
        out["n_zona"] = len(altos)
        out["proyectos"] = altos
    else:
        out["motivo"] = "Cobertura del clúster de alto valor < 20% · no se recorta"
    return out


# ──────────────────────── Demografía base (de AGEBs) ────────────────────────
# Mapeo de NSE INEGI a las clases del tablero
NSE_MAP = {"A": "A", "B": "B", "C+": "C+", "C": "C", "D+": "D+", "D": "D", "E": "E"}


def derive_demografia(agebs: List[Dict]) -> Dict[str, Any]:
    """Agrega los AGEBs a KPIs demográficos de zona. Ausencia => None."""
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

    ingreso_hogar = (ing_total / hog) if (ing_total is not None and hog) else None

    # NSE por hogares (campo C94 "NSE PER" o C47)
    nse_field = "NSE PER" if any("NSE PER" in r for r in agebs) else "XI_Nivel socioeconómico por ingreso"
    nse_hog: Dict[str, float] = {}
    nse_ing: Dict[str, List[float]] = {}
    for r in agebs:
        cls = r.get(nse_field)
        h = _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020"))
        if cls in NSE_MAP and h is not None:
            key = NSE_MAP[cls]
            nse_hog[key] = nse_hog.get(key, 0.0) + h
            ing_ageb = _num(r.get("Ingresos totales 2026"))
            if ing_ageb is not None and h > 0:
                nse_ing.setdefault(key, []).append(ing_ageb / h)

    nse = {}
    total_hog = sum(nse_hog.values()) if nse_hog else 0
    for k, h in nse_hog.items():
        ingreso = round(statistics.mean(nse_ing[k])) if nse_ing.get(k) else None
        nse[k] = {"hog": round(h), "pct": round(h / total_hog * 100, 1) if total_hog else None,
                  "ingreso": ingreso}
    nse_dominante = max(nse_hog, key=nse_hog.get) if nse_hog else None

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
    nse_field = "NSE PER" if any("NSE PER" in r for r in agebs) else "XI_Nivel socioeconómico por ingreso"
    agg: Dict[str, Dict] = {}
    for r in agebs:
        cls = r.get(nse_field)
        if cls not in NSE_MAP:
            continue
        k = NSE_MAP[cls]
        d = agg.setdefault(k, {"poblacion": 0.0, "hogares": 0.0,
                               "ninos": 0.0, "adolescentes": 0.0, "jovenes": 0.0,
                               "jov_adultos": 0.0, "consolidados": 0.0, "empty_nest": 0.0})
        d["poblacion"] += _num(r.get("Población total 2026")) or _num(r.get("POB1")) or 0
        d["hogares"] += _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020")) or 0
        d["ninos"] += _num(r.get("Niños")) or 0
        d["adolescentes"] += _num(r.get("Adolescentes")) or 0
        d["jovenes"] += _num(r.get("Jovenes")) or 0
        d["jov_adultos"] += _num(r.get("Jovenes_adultos")) or 0
        d["consolidados"] += _num(r.get("Consolidados")) or 0
        d["empty_nest"] += _num(r.get("Nesters")) or 0

    out = []
    order = ["A", "B", "C+", "C", "D+", "D", "E"]
    for k in order:
        rng = nse_ranges[k]
        d = agg.get(k, {"poblacion": 0, "hogares": 0, "ninos": 0, "adolescentes": 0,
                        "jovenes": 0, "jov_adultos": 0, "consolidados": 0, "empty_nest": 0})
        out.append({
            "NSE": k,
            "ing_min": rng["ing_min"], "ing_max": rng["ing_max"] or 0,
            "viv_min": rng["viv_min"], "viv_max": rng["viv_max"] or 0,
            "tca": rng["tca"],
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


def derive_segments(agebs: List[Dict], ft: List[Dict]) -> List[Dict[str, Any]]:
    """
    Deriva buckets de demanda combinando:
      - Demanda anual de vivienda por AGEB (C173) y rangos de valor (C186).
      - Oferta real por bucket (tipologías ft) para clasificar status.
    Status: sweet_spot / desatendido / oportunidad / atendido / oceano_rojo / bajo_crecimiento.
    """
    if not agebs:
        return []

    # Demanda por rango de valor (campo "Rangos demanda vivienda numerico" agrupa)
    # Sumamos demanda anual y hogares por NSE/rango.
    # Construimos buckets simples a partir de "Demanda anual vivienda" distribuida por "Rangos demanda vivienda".
    demanda_por_rango: Dict[str, Dict] = {}
    for r in agebs:
        rango = r.get("Rangos demanda vivienda")
        dem = _num(r.get("Demanda anual vivienda"))
        nse_cls = r.get("NSE PER") or r.get("XI_Nivel socioeconómico por ingreso")
        hog = _num(r.get("Hogares totales 2026")) or 0
        if rango and dem is not None:
            d = demanda_por_rango.setdefault(rango, {"nuevas_fam": 0.0, "hogares": 0.0, "nse": nse_cls})
            d["nuevas_fam"] += dem
            d["hogares"] += hog or 0

    # Oferta por bucket de precio (de ft · F____UNIDAD)
    def bucket_for_price(p_m: float):
        for lo, hi, label in PRICE_BUCKETS:
            if lo <= p_m < hi:
                return label
        return None

    oferta_bucket: Dict[str, int] = {}
    for t in ft:
        a = t.get("attributes", {})
        precio = _price(a.get("F____UNIDAD"))
        disp = _num(a.get("UNIDADES_DISPONIBLES")) or 0
        if precio:
            lbl = bucket_for_price(precio / 1e6)
            if lbl:
                oferta_bucket[lbl] = oferta_bucket.get(lbl, 0) + int(disp)

    # Ensamblar segmentos: usamos los rangos de demanda detectados
    segments = []
    # Ordenar por valor numérico del rango si está disponible
    rangos_sorted = sorted(demanda_por_rango.items(),
                           key=lambda kv: _extract_low(kv[0]) or 0)
    if not rangos_sorted:
        return []

    # Sweet spot: el rango con mayor demanda (nuevas familias) que también tenga oferta moderada
    max_dem = max((v["nuevas_fam"] for _, v in rangos_sorted), default=0)
    for rango, v in rangos_sorted:
        low = _extract_low(rango)
        high = _extract_high(rango)
        nuevas = round(v["nuevas_fam"], 1)
        nse_cls = v["nse"] if v["nse"] in NSE_MAP else "—"
        lbl_bucket = bucket_for_price((low or 0) / 1e6) if low else None
        oferta = oferta_bucket.get(lbl_bucket, 0) if lbl_bucket else 0

        # Clasificación de status (demanda vs oferta)
        if nuevas == 0:
            status = "bajo_crecimiento"; origen = "supply_driven"
        elif nuevas >= max_dem * 0.85:
            status = "sweet_spot"; origen = "demand_driven"
        elif oferta == 0:
            status = "desatendido"; origen = "demand_driven"
        elif oferta < nuevas * 12:
            status = "oportunidad"; origen = "demand_driven"
        elif oferta < nuevas * 36:
            status = "atendido"; origen = "demand_driven"
        else:
            status = "oceano_rojo"; origen = "demand_driven"

        mkt_total = round(v["hogares"])
        segments.append({
            "NSE": nse_cls, "bucket": rango,
            "val_min": low, "val_max": high,
            "mkt_total": mkt_total, "nuevas_fam": nuevas,
            "mkt_venta": round(mkt_total * 0.83) if mkt_total else 0,
            "mkt_renta": round(mkt_total * 0.17) if mkt_total else 0,
            "rent_min": 0, "rent_max": 0,
            "ing_min": 0, "ing_max": 0,
            "hog_propios": round(mkt_total * 0.65) if mkt_total else 0,
            "status": status, "origen": origen, "segments_in_bucket": 1,
        })

    # Garantizar UN solo sweet_spot
    sweets = [s for s in segments if s["status"] == "sweet_spot"]
    if len(sweets) > 1:
        best = max(sweets, key=lambda s: s["nuevas_fam"])
        for s in sweets:
            if s is not best:
                s["status"] = "oportunidad"
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
    """Un producto por bucket con demanda + supply-only de buckets altos. DPO anchor aplicado."""
    productos = []
    color_by_status = {
        "sweet_spot": "green", "desatendido": "blue", "oportunidad": "purple",
        "atendido": "teal", "oceano_rojo": "red", "bajo_crecimiento": "amber",
    }
    for s in segments:
        # Tamaño/precio representativos del bucket desde ft
        val_mid = None
        if s.get("val_min") and s.get("val_max"):
            val_mid = (float(s["val_min"]) + float(s["val_max"])) / 2
        elif s.get("val_min"):
            val_mid = float(s["val_min"]) * 1.1

        # m² representativo (de ft en el rango de precio), con banda física
        m2_vals = []
        pm2_vals = []
        for t in ft:
            a = t.get("attributes", {})
            precio = _price(a.get("F____UNIDAD"))
            ap = _num(a.get("ÁREA_PRIVATIVA"))
            pm2 = _pm2(a.get("F___M2"))
            if precio and val_mid and abs(precio - val_mid) / val_mid < 0.15:
                if ap and M2_MIN <= ap <= M2_MAX:
                    m2_vals.append(ap)
                if pm2:
                    pm2_vals.append(pm2)
        m2 = round(statistics.median(m2_vals)) if m2_vals else None
        pm2 = round(statistics.median(pm2_vals)) if pm2_vals else None

        # DPO anchor: ticket no por debajo del val_min del segmento
        ticket_M = round(val_mid / 1e6, 2) if val_mid else None
        if ticket_M and s.get("val_min"):
            ticket_M = max(ticket_M, round(float(s["val_min"]) / 1e6, 2))

        productos.append({
            "tipo": f"{s['NSE']} · {s['bucket']}",
            "color": color_by_status.get(s["status"], "teal"),
            "rec": "N/D",
            "m2": f"{m2} m²" if m2 else "N/D",
            "pm2": f"${pm2:,}" if pm2 else "N/D",
            "ticket": f"${ticket_M:.2f}M" if ticket_M else "N/D",
            "abs": "N/D",
            "mercado": f"NSE {s['NSE']} · {s['bucket']}",
            "status": s["status"],
            "recomendado": s["status"] in ("sweet_spot", "desatendido", "oportunidad", "atendido"),
            "featured": s["status"] == "sweet_spot",
            "seg_dim": f"{s['NSE']} · {s['bucket']}",
            "mkt_segmento": s["mkt_total"], "nuevas_fam": s["nuevas_fam"],
            "categoria": _status_label(s["status"]),
            "perfiles": [],
        })
    # Solo un featured
    feats = [p for p in productos if p.get("featured")]
    if len(feats) > 1:
        best = max(feats, key=lambda p: p.get("nuevas_fam", 0))
        for p in feats:
            if p is not best:
                p["featured"] = False
    return productos


def _status_label(status: str) -> str:
    return {
        "desatendido": "Gap · Desatendido", "sweet_spot": "Sweet Spot Estructural",
        "atendido": "Mercado Core · Atendido", "oportunidad": "Sub-oferta · Oportunidad",
        "oceano_rojo": "Océano Rojo · Sobreoferta", "bajo_crecimiento": "Supply-Driven · Sin Demanda",
    }.get(status, status)


# ──────────────────────── Productos renta (Checkpoint F) ────────────────────────
def derive_productos_renta(ft_renta: List[Dict], agebs: List[Dict]) -> List[Dict[str, Any]]:
    """Deriva productos de renta de la oferta vv_renta + V_RENTA por AGEB."""
    productos = []
    # Tickets de renta reales de la oferta
    for t in ft_renta[:40]:
        a = t.get("attributes", {})
        ap = _num(a.get("ÁREA_PRIVATIVA"))
        precio = _num(a.get("F____UNIDAD"))  # en renta, F____UNIDAD = renta mensual
        rec = _num(a.get("CANTIDAD_DE_RECAMARAS"))
        if ap and M2_MIN <= ap <= M2_MAX and precio and precio > 1000:
            productos.append({
                "tipo": a.get("PROYECTO", "N/D"),
                "m2": f"{round(ap)} m²",
                "rec": f"{int(rec)} Rec" if rec else "N/D",
                "renta_ud": f"${round(precio):,}/mes",
                "pm2_renta": f"${round(precio/ap):,}/m²/mes" if ap else "N/D",
                "status": "atendido", "recomendado": True, "featured": False,
                "mercado": f"{a.get('NSE_INGRESO', 'N/D')} · {a.get('CORREDOR___ZONA', 'N/D')}",
            })
    return productos[:6]


# ──────────────────────── Comercio (potencial retail) ────────────────────────
def derive_comercio(agebs: List[Dict]) -> Dict[str, Any]:
    """Agrega gasto y demanda retail por categoría de los AGEBs."""
    if not agebs:
        return {}
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
    return {
        "ingreso_anual": round(ing_total) if ing_total else None,
        "demanda": demanda,
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
                          comercio, perception, agebs_count) -> Dict[str, Any]:
    proyectos = _build_proyectos(resumen)
    kpis = _build_kpis(proyectos, ft)
    inv = _build_inventario(ft)

    # Centro = pin del predio
    center = [req.lat, req.lng]

    zone_name = req.zone_name or "Zona de análisis"
    municipio = req.municipio or "N/D"
    estado = req.estado or "N/D"

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
        "recamaras": None,
        "proyectos": proyectos,
        "kpis": kpis,
        "avgAbs": kpis["avg_abs"], "avgPm2": kpis["avg_pm2"],
        "inventario_precio": inv["inventario_precio"],
        "inventario_m2": inv["inventario_m2"],
        "productos": productos,
        "productos_renta": productos_renta,
        "renta_segmentos": [],
        "demanda_segmentos": [],
        "renta_baseline": {"m2": None, "pm2": None, "units": None, "occ": None},
        "sensibilidad_baseline": {"m2": None, "pm2": None, "abs_base": None, "ticket_base": None},
        "comercio": comercio,
        "ingreso_anual": comercio.get("ingreso_anual"),
        "demanda": comercio.get("demanda", {}),
        # Metadatos de la zona de análisis (sección Zona de análisis)
        "_zona_analisis": {
            "perfil_iso": profile["key"], "perfil_label": profile["label"],
            "isocronas": iso_out,
            "predio_m2": req.predio_m2, "uso_comercial": req.uso_comercial,
            "norm": req.norm.dict() if req.norm else None,
            "perception": {
                "n_total": perception["n_total"], "n_zona": perception["n_zona"],
                "media": round(perception["media"]) if perception.get("media") else None,
                "sd": round(perception["sd"]) if perception.get("sd") else None,
                "cv": round(perception["cv"], 4) if perception.get("cv") is not None else None,
                "barrera": perception["barrera"], "metodo": perception["metodo"],
                "cobertura_pct": perception["cobertura_pct"], "motivo": perception["motivo"],
                "proyectos": perception["proyectos"],
            },
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
        "civil": _build_civil(),  # placeholder estructural si no hay data fina
        "hog_comp": _build_hog_comp(demografia),
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
        for nse_k in ["A", "B", "C+", "C"]:
            v = round(by_nse.get(nse_k, {}).get(key, 0)) if by_nse.get(nse_k) else 0
            col = "Cm" if nse_k == "C+" else nse_k
            row[col] = v
            total += v
        # sumar también D+/D/E al total
        for nse_k in ["D+", "D", "E"]:
            total += round(by_nse.get(nse_k, {}).get(key, 0)) if by_nse.get(nse_k) else 0
        row["Total"] = total
        row["pct"] = None
        out.append(row)
    return out


def _build_civil():
    # Sin data civil fina por AGEB en el agregado → estructura vacía marcada N/D
    # El template tolera dict vacío; cada edad se omite si no hay data.
    return {}


def _build_hog_comp(demografia):
    return {
        "familiares_total": None, "no_familiares_total": None,
        "nucleares": None, "ampliados": None, "compuestos": None,
        "unipersonal": None, "corresidentes": None,
    }


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

app = FastAPI(title="Dataria Orchestrator", version="1.0")

# CORS abierto para que el tablero (servido en cualquier origen http/https) consuma el API.
# Para producción, restringir allow_origins a los dominios de Dataria.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────── Modelos de petición ────────────────────────
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
    return {"ok": True, "service": "dataria-orchestrator", "version": "1.0"}


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
    demografia = derive_demografia(agebs)             # population, households, tca, nse, tenencia...
    nse_dim = derive_nse_dim(agebs)                   # nse_dim[] para DIM_DATA
    segments = derive_segments(agebs, ft)             # 12 buckets de demanda
    productos = derive_productos_venta(ft, segments)  # productos venta
    productos_renta = derive_productos_renta(ft_renta, agebs)  # productos renta
    comercio = derive_comercio(agebs)                 # potencial comercio/retail

    # ── Ensamblaje del payload (esquema que consume el template) ──
    payload = assemble_zone_payload(
        req=req, profile=profile, isocronas=isocronas,
        resumen=resumen, ft=ft, pagos=pagos,
        resumen_renta=resumen_renta,
        demografia=demografia, nse_dim=nse_dim, segments=segments,
        productos=productos, productos_renta=productos_renta,
        comercio=comercio, perception=perception, agebs_count=len(agebs),
    )
    return payload
