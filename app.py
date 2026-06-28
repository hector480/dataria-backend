"""
Dataria · Backend de orquestación en vivo (archivo único)
==========================================================
Versión combinada para despliegue simple: dpo + assembler + main en un solo app.py.
Endpoints:  GET /health   ·   POST /api/zona/analyze
"""

# ╔══════════════ SECCIÓN 1: DERIVACIÓN DIGO/DPO (dpo) ══════════════╗
import statistics
import math
import random
import re
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


# ──────────────────────── Envolvente convexa (hull) ────────────────────────
def _convex_hull(points: List[List[float]]) -> List[List[float]]:
    """Envolvente convexa (monotone chain) sobre puntos [[lng, lat], ...].

    Devuelve el anillo CERRADO (primer punto repetido al final) en formato
    [[lng, lat], ...]. Si hay menos de 3 puntos distintos, devuelve [] (no se
    puede formar un polígono → integridad: sin invención).
    """
    pts = sorted(set((float(p[0]), float(p[1])) for p in points
                     if p and p[0] is not None and p[1] is not None))
    if len(pts) < 3:
        return []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return []
    ring = [[x, y] for (x, y) in hull]
    ring.append(ring[0])  # cerrar el anillo
    return ring


# ════════════════════ Detección universal de mercados (clustering) ════════════════════
#
# REGLA UNIVERSAL DE ZONA DE INFLUENCIA REAL
# ------------------------------------------
# Una isócrona puede contener DOS (o más) mercados distintos pegados, separados por una
# barrera —física (río con pocos puentes), de NSE del AGEB, o de percepción de valor—.
# El CV global puede ser moderado y aun así ocultar la frontera: lo que la delata es que
# al PARTIR los proyectos en grupos espacialmente contiguos, cada grupo es internamente
# homogéneo (CV interno bajo) y sus medias son muy distintas.
#
# No buscamos la barrera física; buscamos su EFECTO en los datos. Así la regla es universal,
# exista o no un río. El método:
#   1. Vector por proyecto con señales normalizadas y ponderadas:
#        ticket/unidad (0.40) · precio $/m² (0.30) · posición vs pin (0.30)
#        [+ NSE del AGEB (gancho enchufable) cuando exista geometría por CVEGEO]
#   2. k-means con k AUTOMÁTICO (k=1,2,3): se elige la partición con mejor separabilidad.
#   3. Validación robusta de que hay >1 mercado: gap de medias normalizado ≥ 0.85 Y
#      varianza explicada ≥ 0.35, con masa mínima por cluster (≥ 3 proyectos).
#   4. La zona de influencia real = cluster MÁS COMPATIBLE CON EL PIN (centroide = pin).
#
# Pesos de las señales (renormalizados si alguna señal no está disponible → integridad).
SIGNAL_WEIGHTS = {"ticket": 0.40, "pm2": 0.30, "pos": 0.30, "nse": 0.0}  # nse=0 hasta tener geometría
CLUSTER_MASA_MIN = 3       # proyectos mínimos por cluster para considerarlo un mercado
GAP_MIN = 0.85             # separación de medias normalizada mínima
VAR_EXPLAINED_MIN = 0.35   # proporción de varianza explicada por la partición mínima
# Salvaguardas contra falsos positivos (zonas realmente uniformes):
CV_GLOBAL_MIN = 0.12       # si el CV global de la zona es menor, NO hay dos mercados que separar
SEP_MEDIAS_MIN = 0.18      # diferencia mínima de medias entre mercados (proporción), p.ej. 18%
SOLAPE_ESPACIAL_MAX = 0.60 # solape máximo permitido de los rangos espaciales de los clusters
KMEANS_RESTARTS = 12
KMEANS_ITERS = 60


def _zscore_params(vals: List[float]):
    """(media, desviación) ignorando None; desviación 1.0 si no hay dispersión."""
    v = [x for x in vals if x is not None]
    if len(v) < 2:
        return (statistics.mean(v) if v else 0.0), 1.0
    m = statistics.mean(v)
    s = statistics.pstdev(v) or 1.0
    return m, s


def fetch_ageb_geometria(cvegeo_list: List[str]) -> Dict[str, Dict[str, float]]:
    """GANCHO ENCHUFABLE · georreferenciación de AGEB por CVEGEO.

    Devuelve {cvegeo: {"lng": x, "lat": y}} con el CENTROIDE de cada AGEB para usar
    el NSE del AGEB como 4ª señal del clustering. Hoy PRSP no expone (aún) un endpoint
    documentado de geometría por CVEGEO, por lo que devuelve {} (NSE = N/D, no se inventa).

    Cuando exista la documentación del endpoint PRSP de geometría de AGEB:
      • Implementar aquí la consulta (POST {PRSP_BASE}/<ruta>, body con cvegeo_list).
      • Parsear el centroide/geometría de cada CVEGEO de la respuesta.
      • Subir SIGNAL_WEIGHTS["nse"] (p. ej. a 0.15) y renormalizar los demás pesos.
    El resto del clustering ya está preparado para incorporar la señal sin reescribirse.
    """
    return {}


def _build_feature_vectors(proyectos: List[Dict], pin_lng: float, pin_lat: float):
    """Vectores ponderados y normalizados por proyecto. Renormaliza pesos según
    las señales realmente disponibles (integridad: no se inventan señales faltantes)."""
    tickets = [p.get("ticket") for p in proyectos]
    pm2s = [p.get("pm2") for p in proyectos]
    lngs = [p.get("lng") for p in proyectos]
    lats = [p.get("lat") for p in proyectos]

    has_ticket = sum(1 for t in tickets if t is not None) >= max(3, len(proyectos) // 2)
    has_nse = any(p.get("nse_rank") is not None for p in proyectos)  # gancho NSE

    # Pesos activos según disponibilidad real de señales
    w = dict(SIGNAL_WEIGHTS)
    if not has_ticket:
        w["ticket"] = 0.0
    if not has_nse:
        w["nse"] = 0.0
    total_w = sum(w.values()) or 1.0
    w = {k: v / total_w for k, v in w.items()}  # renormalizar

    m_tk, s_tk = _zscore_params(tickets)
    m_pm, s_pm = _zscore_params(pm2s)
    m_ln, s_ln = _zscore_params(lngs)
    m_lt, s_lt = _zscore_params(lats)
    nse_ranks = [p.get("nse_rank") for p in proyectos]
    m_ns, s_ns = _zscore_params(nse_ranks)

    X = []
    for p in proyectos:
        f = []
        # ticket (si falta en un proyecto puntual, proxy con pm² para no perderlo)
        if w["ticket"] > 0:
            tval = p.get("ticket")
            if tval is not None:
                f.append(w["ticket"] * ((tval - m_tk) / s_tk))
            else:
                f.append(w["ticket"] * ((p.get("pm2", m_pm) - m_pm) / s_pm))
        if w["pm2"] > 0:
            f.append(w["pm2"] * ((p.get("pm2", m_pm) - m_pm) / s_pm))
        if w["pos"] > 0:
            # posición relativa al PIN (no al centro de masa): lng pesa completo, lat mitad
            f.append(w["pos"] * ((p["lng"] - pin_lng) / s_ln))
            f.append(w["pos"] * 0.5 * ((p["lat"] - pin_lat) / s_lt))
        if w["nse"] > 0 and p.get("nse_rank") is not None:
            f.append(w["nse"] * ((p["nse_rank"] - m_ns) / s_ns))
        X.append(f)
    return X, w


def _euclid(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))


def _kmeans(X: List[List[float]], k: int, seed: int = 42):
    """k-means con múltiples reinicios. Devuelve (labels, inertia)."""
    if k <= 1 or len(X) <= k:
        return [0] * len(X), 0.0
    rnd = random.Random(seed)
    best = None
    for _ in range(KMEANS_RESTARTS):
        idx = rnd.sample(range(len(X)), k)
        centroids = [X[i][:] for i in idx]
        labels = [0] * len(X)
        for _ in range(KMEANS_ITERS):
            for i, x in enumerate(X):
                labels[i] = min(range(k), key=lambda c: _euclid(x, centroids[c]))
            moved = False
            for c in range(k):
                grp = [X[i] for i in range(len(X)) if labels[i] == c]
                if grp:
                    nc = [sum(g[j] for g in grp) / len(grp) for j in range(len(X[0]))]
                    if nc != centroids[c]:
                        centroids[c] = nc
                        moved = True
            if not moved:
                break
        inertia = sum(_euclid(X[i], centroids[labels[i]]) ** 2 for i in range(len(X)))
        if best is None or inertia < best[1]:
            best = (labels[:], inertia)
    return best


def _partition_metrics(proyectos: List[Dict], labels: List[int], k: int):
    """Métricas de separabilidad sobre pm² entre los k grupos.
    Devuelve (gap_min_normalizado, varianza_explicada, masa_ok, stats_por_grupo)."""
    precios_all = [p["pm2"] for p in proyectos]
    if len(precios_all) < 2:
        return 0.0, 0.0, False, []
    M = statistics.mean(precios_all)
    var_total = statistics.pvariance(precios_all) or 1e-9

    grupos = []
    for c in range(k):
        gp = [proyectos[i]["pm2"] for i in range(len(proyectos)) if labels[i] == c]
        if gp:
            grupos.append({
                "c": c, "n": len(gp),
                "media": statistics.mean(gp),
                "sd": statistics.pstdev(gp),
                "cv": (statistics.pstdev(gp) / statistics.mean(gp)) if statistics.mean(gp) else None,
            })
    if len(grupos) < 2:
        return 0.0, 0.0, False, grupos

    # masa mínima por grupo
    masa_ok = all(g["n"] >= CLUSTER_MASA_MIN for g in grupos)

    # gap normalizado: para cada par adyacente por media, (Δmedias)/(sd_i+sd_j); tomamos el mínimo
    gs = sorted(grupos, key=lambda g: g["media"])
    gaps = []
    for i in range(len(gs) - 1):
        denom = (gs[i]["sd"] + gs[i + 1]["sd"]) or 1.0
        gaps.append(abs(gs[i + 1]["media"] - gs[i]["media"]) / denom)
    gap_min = min(gaps) if gaps else 0.0

    # varianza explicada = varianza entre medias / varianza total
    n_tot = sum(g["n"] for g in grupos)
    between = sum(g["n"] * (g["media"] - M) ** 2 for g in grupos) / n_tot
    var_explained = between / var_total

    return gap_min, var_explained, masa_ok, grupos


def _separacion_espacial(proyectos: List[Dict], labels: List[int], c_a: int, c_b: int) -> float:
    """Mide qué tan separados ESPACIALMENTE están dos clusters (0=encimados, 1=disjuntos).

    Proyecta cada proyecto sobre el eje que une los centroides de los dos clusters y
    calcula el solape de los rangos proyectados. Devuelve 1 - solape: alto = frontera
    espacial real (mercados en lados distintos), bajo = grupos entremezclados (falso
    positivo de un mercado uniforme partido artificialmente)."""
    A = [proyectos[i] for i in range(len(proyectos)) if labels[i] == c_a]
    B = [proyectos[i] for i in range(len(proyectos)) if labels[i] == c_b]
    if not A or not B:
        return 0.0
    ca = (statistics.mean(p["lng"] for p in A), statistics.mean(p["lat"] for p in A))
    cb = (statistics.mean(p["lng"] for p in B), statistics.mean(p["lat"] for p in B))
    vx, vy = cb[0] - ca[0], cb[1] - ca[1]
    norm = math.hypot(vx, vy) or 1e-9
    vx, vy = vx / norm, vy / norm  # eje unitario centroide A→B

    def proj_range(grp):
        vals = [p["lng"] * vx + p["lat"] * vy for p in grp]
        return min(vals), max(vals)
    a_lo, a_hi = proj_range(A)
    b_lo, b_hi = proj_range(B)
    # solape de los dos intervalos sobre el eje
    inter = max(0.0, min(a_hi, b_hi) - max(a_lo, b_lo))
    union = max(a_hi, b_hi) - min(a_lo, b_lo)
    solape = inter / union if union > 0 else 1.0
    return 1.0 - solape


def detect_markets(proyectos: List[Dict], pin_lng: float, pin_lat: float) -> Dict[str, Any]:
    """Detección universal de mercados dentro de la isócrona.

    Entrada: proyectos [{name, pm2, lat, lng, ticket?, nse_rank?}] (ya dentro de la isócrona).
    Salida: dict con la partición elegida y la asignación del PIN.
      • barrera (bool): True si se detecta >1 mercado robusto.
      • k_elegido, labels, grupos, gap, var_explained.
      • pin_cluster: índice del cluster donde cae el pin (mercado compatible con el predio).
      • cluster_proyectos: lista de proyectos del cluster del pin.
      • pesos: pesos de señales realmente aplicados (auditoría/integridad).

    Salvaguardas contra falsos positivos (zonas realmente uniformes):
      1. CV global de la zona ≥ CV_GLOBAL_MIN (si la zona ya es uniforme, no se parte).
      2. Diferencia de medias entre mercados ≥ SEP_MEDIAS_MIN (separación REAL, no relativa).
      3. Separación espacial de los clusters ≥ (1 - SOLAPE_ESPACIAL_MAX) (frontera real).
    """
    out = {
        "barrera": False, "k_elegido": 1, "labels": [0] * len(proyectos),
        "grupos": [], "gap": None, "var_explained": None,
        "pin_cluster": 0, "cluster_proyectos": proyectos, "pesos": None,
        "motivo": None,
    }
    n = len(proyectos)
    if n < 2 * CLUSTER_MASA_MIN:
        out["motivo"] = f"Muestra insuficiente para detectar mercados (n={n} < {2*CLUSTER_MASA_MIN})"
        return out

    # SALVAGUARDA 1: si la zona ya es uniforme (CV global bajo), no hay mercados que separar.
    precios = [p["pm2"] for p in proyectos]
    media_global = statistics.mean(precios)
    cv_global = (statistics.pstdev(precios) / media_global) if media_global else 0.0
    if cv_global < CV_GLOBAL_MIN:
        out["motivo"] = (f"Zona uniforme (CV global {cv_global:.2f} < {CV_GLOBAL_MIN}) · "
                         f"un solo mercado (zona = isócrona)")
        return out

    X, pesos = _build_feature_vectors(proyectos, pin_lng, pin_lat)
    out["pesos"] = pesos

    # k automático: probar k=2 y k=3, validar separabilidad, elegir el mejor robusto
    candidatos = []
    for k in (2, 3):
        if n < k * CLUSTER_MASA_MIN:
            continue
        labels, _ = _kmeans(X, k, seed=42)
        gap, var_exp, masa_ok, grupos = _partition_metrics(proyectos, labels, k)

        # SALVAGUARDA 2: separación de medias absoluta (real) entre los dos mercados extremos
        if len(grupos) >= 2:
            ms = sorted(g["media"] for g in grupos)
            sep_medias = (ms[-1] - ms[0]) / ms[-1] if ms[-1] else 0.0
        else:
            sep_medias = 0.0

        # SALVAGUARDA 3: separación espacial entre los dos clusters más distintos en media
        if len(grupos) >= 2:
            gs = sorted(grupos, key=lambda g: g["media"])
            sep_esp = _separacion_espacial(proyectos, labels, gs[0]["c"], gs[-1]["c"])
        else:
            sep_esp = 0.0

        es_robusto = (gap >= GAP_MIN and var_exp >= VAR_EXPLAINED_MIN and masa_ok
                      and sep_medias >= SEP_MEDIAS_MIN
                      and sep_esp >= (1.0 - SOLAPE_ESPACIAL_MAX))
        # puntaje: voto combinado de gap + varianza (la métrica más robusta)
        score = (gap / GAP_MIN) + (var_exp / VAR_EXPLAINED_MIN)
        candidatos.append({"k": k, "labels": labels, "gap": gap, "var": var_exp,
                           "masa_ok": masa_ok, "robusto": es_robusto, "score": score,
                           "grupos": grupos, "sep_medias": sep_medias, "sep_esp": sep_esp})

    robustos = [c for c in candidatos if c["robusto"]]
    if not robustos:
        out["motivo"] = "Sin partición robusta · un solo mercado (zona = isócrona)"
        return out

    # Elegir la partición robusta de mayor score
    mejor = max(robustos, key=lambda c: c["score"])
    out.update(barrera=True, k_elegido=mejor["k"], labels=mejor["labels"],
               grupos=mejor["grupos"], gap=round(mejor["gap"], 3),
               var_explained=round(mejor["var"], 3))

    # Asignar el PIN a su mercado: cluster cuyo CENTROIDE ESPACIAL está más cerca del pin
    k = mejor["k"]; labels = mejor["labels"]
    centroides = []
    for c in range(k):
        pts = [proyectos[i] for i in range(n) if labels[i] == c]
        if not pts:
            centroides.append((c, float("inf")))
            continue
        clng = statistics.mean(p["lng"] for p in pts)
        clat = statistics.mean(p["lat"] for p in pts)
        d = math.hypot(clng - pin_lng, clat - pin_lat)
        centroides.append((c, d))
    pin_cluster = min(centroides, key=lambda t: t[1])[0]
    out["pin_cluster"] = pin_cluster
    out["cluster_proyectos"] = [proyectos[i] for i in range(n) if labels[i] == pin_cluster]
    return out


# ──────────────────────── Percepción de valor + ajuste de zona ────────────────────────
def value_perception_adjust(resumen: List[Dict], base_ring: List[List[float]],
                            pin_lng: Optional[float] = None,
                            pin_lat: Optional[float] = None,
                            agebs_geo: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Capa de percepción de valor sobre la isócrona base (8 min) y ajuste de
    ZONA DE INFLUENCIA REAL mediante detección universal de mercados (clustering).

    La isócrona define quién llega; los datos de oferta (VVV) definen si dentro de
    esa isócrona hay UNO o VARIOS mercados. Si hay una barrera (física, de NSE o de
    percepción de valor), la zona de influencia real es el mercado MÁS COMPATIBLE
    CON EL PIN, no toda la isócrona. Ver `detect_markets` para el método universal.

    Devuelve `zona_poligono` (polígono GeoJSON · lista de anillos) para el mapa morado:
      • Sin barrera (un mercado)       → zona = isócrona de 8 min completa.
      • Con barrera (varios mercados)  → zona = hull del cluster del pin.
      • Sin datos suficientes          → isócrona (o None si no hay anillo).
    """
    proyectos = []
    for row in resumen:
        a = row.get("attributes", {})
        g = row.get("geometry", {})
        pm2 = _num(a.get("F__M2_PROM"))
        ticket = _num(a.get("F__UD_PROM"))   # ticket por unidad (señal de mayor peso)
        la = _num(g.get("y")) if g.get("y") is not None else _num(a.get("Y_coor"))
        ln = _num(g.get("x")) if g.get("x") is not None else _num(a.get("X_coor"))
        if pm2 is not None and pm2 > 1000 and la is not None and ln is not None:
            proyectos.append({"name": a.get("PROYECTO") or a.get("Nombre") or "N/D",
                              "pm2": pm2, "ticket": ticket, "lat": la, "lng": ln,
                              "nse_rank": None})  # nse_rank: gancho NSE (N/D hasta tener geometría)

    dentro = [p for p in proyectos if _point_in_ring(p["lng"], p["lat"], base_ring)]
    precios = [p["pm2"] for p in dentro]

    out = {
        "n_total": len(dentro), "n_zona": len(dentro),
        "media": None, "sd": None, "cv": None,
        "barrera": False, "metodo": "isocrona", "cobertura_pct": 100,
        "motivo": None, "proyectos": dentro,
        "cluster_names": None,
        "zona_poligono": [base_ring] if base_ring else None,
        # VALOR PERCIBIDO: ¿la zona tiene un precio de mercado preestablecido (oferta comparable)?
        # Si no hay comparables, no se fuerza un precio rígido: la demanda y la calidad del
        # proyecto definirán producto y precio. El front muestra esta nota en ese caso.
        "sin_valor_percibido": len(dentro) == 0,
        "nota_valor": None,
        # Auditoría del clustering (integridad/transparencia)
        "mercados": {"detectado": False, "k": 1, "gap": None, "var_explained": None,
                     "pesos": None, "pin_cluster": None},
    }
    if len(dentro) == 0:
        out["nota_valor"] = ("La zona no tiene un valor preestablecido rígido: no hay oferta "
                             "comparable en el área de influencia. La demanda y la calidad del "
                             "proyecto establecerán la posibilidad de producto y precio.")
    if len(precios) < 3:
        out["motivo"] = "Muestra insuficiente para clúster · se mantiene la isócrona"
        return out

    media = statistics.mean(precios)
    sd = statistics.pstdev(precios)
    cv = sd / media if media > 0 else None
    out.update(media=media, sd=sd, cv=cv)

    # Pin: si no se pasó, usar el centroide de masa de los proyectos como referencia.
    p_lng = pin_lng if pin_lng is not None else statistics.mean(p["lng"] for p in dentro)
    p_lat = pin_lat if pin_lat is not None else statistics.mean(p["lat"] for p in dentro)

    # ── DETECCIÓN UNIVERSAL DE MERCADOS (clustering k-auto sobre señales ponderadas) ──
    mk = detect_markets(dentro, p_lng, p_lat)
    out["mercados"] = {
        "detectado": mk["barrera"], "k": mk["k_elegido"],
        "gap": mk["gap"], "var_explained": mk["var_explained"],
        "pesos": mk["pesos"], "pin_cluster": mk["pin_cluster"],
        "motivo": mk.get("motivo"),
    }

    if not mk["barrera"]:
        # La OFERTA no detecta barrera. Antes de devolver la isócrona completa, evaluar si
        # la DEMOGRAFÍA define una barrera de NSE (frontera espacial de niveles distintos).
        # Esto cubre zonas sin oferta vertical donde el cambio de NSE/IXH sí define el submercado.
        nse_zona = _zona_por_barrera_nse(agebs_geo or [], p_lng, p_lat, base_ring)
        if nse_zona["barrera"] and nse_zona.get("zona_poligono"):
            out["barrera"] = True
            out["metodo"] = "barrera_nse"
            out["zona_poligono"] = nse_zona["zona_poligono"]
            out["cobertura_pct"] = round(nse_zona["n_bloque"] / max(len(agebs_geo or [1]), 1) * 100)
            out["motivo"] = nse_zona["motivo"]
            out["mercados"]["barrera_nse"] = True
            return out
        # Sin barrera de oferta ni de NSE → zona = isócrona completa (regla confirmada).
        out["motivo"] = mk.get("motivo") or "Un solo mercado · zona = isócrona de 8 min"
        return out

    # Hay barrera: la zona de influencia real es el MERCADO DEL PIN.
    cluster = mk["cluster_proyectos"]
    if len(cluster) < CLUSTER_MASA_MIN:
        out["motivo"] = "Mercado del pin sin masa suficiente · se mantiene la isócrona"
        return out

    cprecios = [p["pm2"] for p in cluster]
    cmedia = statistics.mean(cprecios)
    out["barrera"] = True
    out["metodo"] = "mercado_del_pin"
    out["n_zona"] = len(cluster)
    out["proyectos"] = cluster
    out["media"] = cmedia
    out["sd"] = statistics.pstdev(cprecios)
    out["cv"] = (out["sd"] / cmedia) if cmedia else None
    out["cobertura_pct"] = round(len(cluster) / max(len(dentro), 1) * 100)
    out["cluster_names"] = set(p["name"] for p in cluster if p.get("name") and p["name"] != "N/D")
    out["motivo"] = (f"{mk['k_elegido']} mercados detectados (gap={mk['gap']}, "
                     f"var={mk['var_explained']}) · zona = mercado del pin")

    # Zona de influencia real = hull del mercado del pin. Si no se forma (<3 puntos),
    # se mantiene la isócrona (integridad: no se inventa polígono).
    hull = _convex_hull([[p["lng"], p["lat"]] for p in cluster])
    if hull:
        out["zona_poligono"] = [hull]
    return out


# ──────────────────────── Clasificación de competidores en 3 zonas ────────────────────────
def clasificar_competidores(resumen: List[Dict],
                            base_ring: List[List[float]],
                            outer_ring: List[List[float]],
                            zona_poligono: Optional[List[List[List[float]]]]) -> Dict[str, Any]:
    """Clasifica cada proyecto de oferta (VVV) en uno de 3 sets de competidores:

      • DIRECTO    → dentro de la zona de influencia real (morado · mercado del pin).
                     Set de oferta competidora PRIMARIA a comparar (mismo mercado de valor).
      • PRIMARIO   → dentro de la isócrona de 8 min (azul · zona primaria), no directo.
      • SECUNDARIO → entre la isócrona azul y la mayor (verde · zona secundaria).

    Las zonas azul + verde son las GENERADORAS DE DEMANDA. El morado es independiente
    (puede caer en azul, cruzar a verde, o parcialmente fuera): se evalúa por geometría real.
    Cada proyecto devuelto lleva su etiqueta `set_competidor`.
    """
    morado_ring = zona_poligono[0] if (zona_poligono and zona_poligono[0]) else None

    def coords(row):
        a = row.get("attributes", {}); g = row.get("geometry", {})
        lng = _num(g.get("x")) if g.get("x") is not None else _num(a.get("X_coor"))
        lat = _num(g.get("y")) if g.get("y") is not None else _num(a.get("Y_coor"))
        return lng, lat

    directos, primarios, secundarios = [], [], []
    for row in resumen:
        lng, lat = coords(row)
        if lng is None or lat is None:
            continue
        a = row.get("attributes", {})
        item = {"name": a.get("PROYECTO") or a.get("Nombre") or "N/D",
                "pm2": _num(a.get("F__M2_PROM")), "ticket": _num(a.get("F__UD_PROM")),
                "lat": lat, "lng": lng}
        # DIRECTO: dentro del polígono morado (si existe)
        if morado_ring and _point_in_ring(lng, lat, morado_ring):
            item["set_competidor"] = "directo"
            directos.append(item)
        # PRIMARIO: dentro de la isócrona azul (8 min)
        elif base_ring and _point_in_ring(lng, lat, base_ring):
            item["set_competidor"] = "primario"
            primarios.append(item)
        # SECUNDARIO: dentro de la isócrona mayor (verde) pero fuera de la azul
        elif outer_ring and _point_in_ring(lng, lat, outer_ring):
            item["set_competidor"] = "secundario"
            secundarios.append(item)
        # (si no cae en ninguna, no se incluye — fuera del universo de análisis)

    return {
        "directos": directos, "primarios": primarios, "secundarios": secundarios,
        "n_directos": len(directos), "n_primarios": len(primarios), "n_secundarios": len(secundarios),
    }


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
    """Ingreso por hogar MENSUAL del AGEB.

    IMPORTANTE: el campo IXH ya viene MENSUAL por hogar (verificado contra datos reales:
    p. ej. NSE C+ → IXH ≈ $89,745/mes; NSE B → ≈ $401,847/mes; coherente con AMAI). NO se
    divide entre 12. El fallback `Ingresos totales / hogares` también es mensual por hogar.
    """
    ixh = _num(r.get("IXH"))
    if ixh is not None and ixh > 0:
        return ixh
    ing = _num(r.get("Ingresos totales 2026"))
    hog = _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020"))
    if ing is not None and hog and hog > 0:
        return ing / hog
    return None


def _ageb_vcasa(r: Dict) -> Optional[float]:
    """Valor de vivienda del AGEB (campo 'V CASAS')."""
    return _num(r.get("V CASAS")) or _num(r.get("V_CASAS")) or _num(r.get("V_CASA"))


def _ageb_prop_casa(r: Dict) -> float:
    """Proporción de viviendas tipo CASA (horizontal) sobre el total de viviendas del AGEB.

    Para vivienda HORIZONTAL: la demanda genérica de vivienda del AGEB se pondera por esta
    proporción, de modo que en zonas de casas la demanda horizontal es alta y en zonas de
    departamentos es baja. Universal: usa el conteo real de tipo de vivienda de la base.
    Integridad: si no hay dato de tipo de vivienda, devuelve 1.0 (no se descarta demanda;
    se asume que aplica al modo, evitando perder demanda por falta de desglose).
    """
    casa = _num(r.get("Casa"))
    depto = _num(r.get("Departamento o edificio"))
    vecindad = _num(r.get("Vivienda en vecidad o cuartería ")) or _num(r.get("Vivienda en vecidad o cuartería"))
    otro = _num(r.get("Otro tipo de vivienda"))
    if casa is None:
        return 1.0   # sin desglose → no se pondera (integridad: no perder demanda)
    total = sum(v for v in (casa, depto, vecindad, otro) if v is not None)
    if not total:
        return 1.0
    return max(0.0, min(1.0, casa / total))


def _ageb_prop_vertical(r: Dict) -> float:
    """Proporción de viviendas tipo DEPARTAMENTO (vertical) sobre el total del AGEB.
    Complemento conceptual de _ageb_prop_casa para el modo vertical. Hoy el modo vertical
    usa la demanda genérica (no se pondera) para no alterar el comportamiento validado;
    este helper queda disponible para refinar el modo vertical en el futuro."""
    casa = _num(r.get("Casa"))
    depto = _num(r.get("Departamento o edificio"))
    vecindad = _num(r.get("Vivienda en vecidad o cuartería ")) or _num(r.get("Vivienda en vecidad o cuartería"))
    otro = _num(r.get("Otro tipo de vivienda"))
    if depto is None:
        return 1.0
    total = sum(v for v in (casa, depto, vecindad, otro) if v is not None)
    if not total:
        return 1.0
    return max(0.0, min(1.0, depto / total))


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

    # Ingreso por hogar MENSUAL ponderado (IXH ya es mensual · ver _ageb_ixh_mensual)
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

    # INGRESO DEL HOGAR coherente con el NSE DOMINANTE (dato REAL de la base ArcGIS, no inventado).
    # El promedio ponderado de toda la isócrona diluye el ingreso del NSE alto (mezcla AGEBs A
    # con muchos D+). Cuando hay un NSE dominante (demográfico o por percepción de valor), el
    # ingreso mostrado = ingreso REAL de los AGEBs de ESE NSE (campo IXH de la base). Si ese NSE
    # no tiene AGEBs en la zona (p. ej. percepción A sin AGEB A), se cae al promedio ponderado.
    if nse_dom_key and nse_ing.get(nse_dom_key):
        ingreso_hogar = statistics.mean(nse_ing[nse_dom_key])
    # else: se conserva el promedio ponderado ya calculado arriba (último recurso, dato de base)

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

    # UBICACIÓN GEOGRÁFICA real de la zona (de la base, no inventada). El municipio/estado
    # dominante = el de mayor masa de hogares en la zona de influencia. La zona puede abarcar
    # varios municipios; se reporta el dominante y la lista completa para transparencia.
    ubic = _derive_ubicacion(agebs)

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
        # — Ubicación geográfica real —
        "municipio": ubic.get("municipio"),
        "estado": ubic.get("estado"),
        "pais": ubic.get("pais"),
        "municipios_todos": ubic.get("municipios_todos"),
    }


def _derive_ubicacion(agebs: List[Dict]) -> Dict[str, Any]:
    """Extrae municipio/estado dominantes de la zona desde los AGEBs (campos reales 'Municipio'
    y 'Estado' de la base ArcGIS). Dominante = mayor masa de hogares. País = México (la base
    es nacional MX). Integridad: si no hay dato, devuelve None (no se inventa ubicación)."""
    if not agebs:
        return {"municipio": None, "estado": None, "pais": None, "municipios_todos": []}
    muni_masa: Dict[str, float] = {}
    edo_masa: Dict[str, float] = {}
    for r in agebs:
        h = _num(r.get("Hogares totales 2026")) or _num(r.get("Hogares totales 2020")) or 1
        muni = r.get("Municipio")
        edo = r.get("Estado")
        if muni and str(muni).strip():
            m = str(muni).strip()
            muni_masa[m] = muni_masa.get(m, 0) + h
        if edo and str(edo).strip():
            e = str(edo).strip()
            edo_masa[e] = edo_masa.get(e, 0) + h
    muni_dom = max(muni_masa, key=muni_masa.get) if muni_masa else None
    edo_dom = max(edo_masa, key=edo_masa.get) if edo_masa else None
    municipios = sorted(muni_masa, key=muni_masa.get, reverse=True)
    return {
        "municipio": muni_dom,
        "estado": edo_dom,
        "pais": "México" if (muni_dom or edo_dom) else None,
        "municipios_todos": municipios,
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


def _nse_barrier_info(agebs: List[Dict], agebs_geo: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Reporte legible de la barrera de NSE aplicada a la zona de influencia.

    Combina dos señales:
      • COMPOSICIÓN (del XLSX): qué NSEs hay y en qué proporción de hogares.
      • SEPARACIÓN ESPACIAL (del KMZ georreferenciado, agebs_geo): si los AGEBs de NSE
        distinto están geográficamente separados (frontera real) o entremezclados.
    La barrera de NSE es real solo si hay mezcla relevante Y separación espacial.
    """
    agebs_geo = agebs_geo or []
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
    mezcla_relevante = len(masa) > 1 and share_dom < 0.85  # submercados de NSE distintos

    # SEPARACIÓN ESPACIAL (requiere geometría)
    espacial = _nse_separacion_espacial(agebs_geo)
    barrera = mezcla_relevante and espacial.get("separados", False)

    return {
        "nse_dominante": nse_dom,
        "nse_superior": nse_superior,
        "share_dominante_pct": round(share_dom * 100, 1),
        "agebs_dominante": len(agebs_dom),
        "agebs_total": len(agebs),
        "agebs_geo_total": len(agebs_geo),
        "composicion_nse": composicion,
        "mezcla_relevante": mezcla_relevante,
        "separacion_espacial": espacial,
        "barrera": barrera,
        "metodo": ("nse_espacial" if barrera else
                   "nse_mezclado_sin_frontera" if mezcla_relevante else
                   "isocrona_uniforme"),
        "nota": (
            f"Barrera de NSE: la zona combina niveles {', '.join(composicion.keys())} "
            f"espacialmente separados. El mercado del predio corresponde a su zona de NSE, "
            f"no a toda la isócrona."
            if barrera else
            f"Mezcla de NSE ({', '.join(composicion.keys())}) entremezclada sin frontera "
            f"geográfica: se mantiene la isócrona como zona."
            if mezcla_relevante else
            f"Zona homogénea en NSE {nse_dom}" if nse_dom else "Sin datos de NSE"),
    }


def _zona_por_barrera_nse(agebs_geo: List[Dict], pin_lng: float, pin_lat: float,
                          base_ring: List[List[float]]) -> Dict[str, Any]:
    """Determina si la DEMOGRAFÍA define una barrera de NSE que recorta la zona.

    Cuando la oferta no detecta barrera (o no hay oferta), la demografía puede definirla:
    si dentro de la isócrona hay una FRONTERA ESPACIAL de NSE (bloques de NSE distinto
    geográficamente separados), la zona de influencia real del predio es el BLOQUE DE NSE
    donde cae el pin, no toda la isócrona. Esto resuelve el caso de zonas sin oferta
    vertical donde el cambio drástico de NSE/IXH sí define un submercado.

    Devuelve {barrera, zona_poligono, n_bloque, nse_bloque, motivo}. Integridad: si no hay
    frontera o no se puede formar el hull, barrera=False (no se inventa recorte).
    """
    res = {"barrera": False, "zona_poligono": None, "motivo": None}
    sep = _nse_separacion_espacial(agebs_geo)
    if not sep.get("separados"):
        res["motivo"] = sep.get("motivo")
        return res

    pts = [g for g in agebs_geo if g.get("nse_rank") is not None and g.get("lng") and g.get("lat")]
    rank_med = sep.get("rank_corte")
    if rank_med is None:
        return res
    # Bloques: alto valor (rank ≤ mediana) vs bajo valor (rank > mediana)
    alto = [g for g in pts if g["nse_rank"] <= rank_med]
    bajo = [g for g in pts if g["nse_rank"] > rank_med]
    if len(alto) < 2 or len(bajo) < 2:
        alto = [g for g in pts if g["nse_rank"] < rank_med]
        bajo = [g for g in pts if g["nse_rank"] >= rank_med]
    if len(alto) < 2 or len(bajo) < 2:
        return res

    # ¿A qué bloque pertenece el PIN? Al del centroide más cercano.
    def centro(grp):
        return (sum(g["lng"] for g in grp) / len(grp), sum(g["lat"] for g in grp) / len(grp))
    c_alto, c_bajo = centro(alto), centro(bajo)
    d_alto = math.hypot(pin_lng - c_alto[0], pin_lat - c_alto[1])
    d_bajo = math.hypot(pin_lng - c_bajo[0], pin_lat - c_bajo[1])
    bloque = alto if d_alto <= d_bajo else bajo
    nse_bloque = "alto_valor" if d_alto <= d_bajo else "bajo_valor"

    # Hull del bloque de NSE del pin (zona de influencia socioeconómica).
    hull = _convex_hull([[g["lng"], g["lat"]] for g in bloque])
    if not hull:
        res["motivo"] = "bloque de NSE sin hull"
        return res

    res.update({
        "barrera": True,
        "zona_poligono": [hull],
        "n_bloque": len(bloque),
        "nse_bloque": nse_bloque,
        "ratio": sep.get("ratio"),
        "motivo": (f"Frontera espacial de NSE (ratio {sep.get('ratio')}). "
                   f"Zona = bloque {nse_bloque} del pin ({len(bloque)} AGEBs)."),
    })
    return res


def _nse_separacion_espacial(agebs_geo: List[Dict]) -> Dict[str, Any]:
    """Detecta si los AGEBs de NSE distinto están geográficamente separados.

    Agrupa los AGEBs en dos bloques por nse_rank (alto vs bajo respecto a la mediana),
    calcula el centroide de cada bloque y compara la separación ENTRE bloques contra la
    dispersión interna media. Si la distancia entre centroides supera la dispersión
    interna, hay frontera espacial real. Con pocos AGEBs o NSE uniforme → separados=False
    (no se inventa barrera sin evidencia espacial).
    """
    pts = [g for g in agebs_geo if g.get("nse_rank") is not None and g.get("lng") and g.get("lat")]
    if len(pts) < 6:
        return {"separados": False, "motivo": "muestra insuficiente", "n": len(pts)}
    ranks = sorted(set(g["nse_rank"] for g in pts))
    if len(ranks) < 2:
        return {"separados": False, "motivo": "NSE uniforme", "n": len(pts)}

    rank_med = statistics.median(g["nse_rank"] for g in pts)
    alto = [g for g in pts if g["nse_rank"] <= rank_med]
    bajo = [g for g in pts if g["nse_rank"] > rank_med]
    if len(alto) < 2 or len(bajo) < 2:
        alto = [g for g in pts if g["nse_rank"] < rank_med]
        bajo = [g for g in pts if g["nse_rank"] >= rank_med]
    if len(alto) < 2 or len(bajo) < 2:
        return {"separados": False, "motivo": "sin dos bloques de NSE", "n": len(pts)}

    def centro(grp):
        return (sum(g["lng"] for g in grp) / len(grp), sum(g["lat"] for g in grp) / len(grp))
    def disp(grp, c):
        return (sum(math.hypot(g["lng"] - c[0], g["lat"] - c[1]) for g in grp) / len(grp)) or 1e-9
    c_alto, c_bajo = centro(alto), centro(bajo)
    d_entre = math.hypot(c_alto[0] - c_bajo[0], c_alto[1] - c_bajo[1])
    disp_media = (disp(alto, c_alto) + disp(bajo, c_bajo)) / 2
    ratio = d_entre / disp_media if disp_media else 0.0
    SEP_MIN = 1.0
    return {
        "separados": ratio >= SEP_MIN,
        "ratio": round(ratio, 2),
        "n_alto": len(alto), "n_bajo": len(bajo),
        "rank_corte": rank_med,
        "motivo": ("frontera espacial de NSE" if ratio >= SEP_MIN
                   else "NSE entremezclado (sin frontera)"),
    }


def derive_segments(agebs: List[Dict], ft: List[Dict], tipo_vivienda: str = "vertical") -> List[Dict[str, Any]]:
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
    demanda_bucket = {i: {"nuevas_fam": 0.0, "hogares": 0.0, "ixh_w": 0.0, "ixh_hog": 0.0} for i in range(len(BUCKETS))}
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
        # PONDERACIÓN POR TIPO DE VIVIENDA: en modo horizontal, la demanda de vivienda del
        # AGEB se pondera por la proporción de viviendas tipo CASA (la demanda de casa real
        # del AGEB). En zonas de departamentos la demanda horizontal baja; en zonas de casas
        # se mantiene. El modo vertical usa la demanda genérica (comportamiento validado).
        if tipo_vivienda == "horizontal":
            peso_tipo = _ageb_prop_casa(r)
            dem = dem * peso_tipo
            hog = hog * peso_tipo
        demanda_bucket[bi]["nuevas_fam"] += dem
        demanda_bucket[bi]["hogares"] += hog
        # Ingreso real (IXH mensual) ponderado por hogares → NSE del bucket por INGRESO real,
        # no por el precio de la vivienda (evita etiquetar NSE C un bucket comprado por NSE D).
        ixh_m = _ageb_ixh_mensual(r)
        if ixh_m is not None and hog:
            demanda_bucket[bi]["ixh_w"] += ixh_m * hog
            demanda_bucket[bi]["ixh_hog"] += hog

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

    # ── DEMANDA GRANULAR REAL (sin redistribución artificial) ──
    # Cada bucket conserva la demanda REAL que la base asigna a ese rango de precio (campo
    # "Demanda anual vivienda" por AGEB, ya mapeado arriba). NO se redistribuye ni se promedia:
    # se usa la información granular tal cual la genera la base ArcGIS. El "techo de inducción"
    # y el "tope" se conservan SOLO como metadato informativo (no alteran la demanda mostrada).
    techo_induccion_idx = bucket_max_permitido  # metadato: hasta dónde es inducible la demanda
    # (intencionalmente NO se redistribuye demanda entre buckets · dato granular intacto)

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

    def nse_by_ingreso(ixh_mensual):
        """Clasifica el NSE por el INGRESO mensual real del hogar (AMAI). El NSE de un segmento
        debe reflejar QUIÉN compra (ingreso real), no el precio de la vivienda. Devuelve None si
        no hay ingreso (entonces se cae a la clasificación por valor de vivienda)."""
        if ixh_mensual is None:
            return None
        for nse, (lo, hi) in nse_ing_band.items():
            if lo <= ixh_mensual <= hi:
                return nse
        if ixh_mensual > 200000:
            return "A"
        return "E"

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


    # RANGO DE VALOR APLICABLE DE LA ZONA (para marcar buckets fuera de rango como N/A).
    # Un bucket es APLICABLE si está dentro del rango de valor donde existe oferta vertical
    # real (VVV) en la zona. Fuera de ese rango, el bucket se MUESTRA pero se marca como
    # no-aplicable (no se inventa: la marca se basa en la oferta observada, dato de la base).
    buckets_con_oferta = [i for i in range(len(BUCKETS))
                          if (evidencia[i]["vendidas"] > 0 or evidencia[i]["disp"] > 0
                              or evidencia[i]["n"] > 0)]
    if buckets_con_oferta:
        rango_oferta_lo, rango_oferta_hi = min(buckets_con_oferta), max(buckets_con_oferta)
    else:
        rango_oferta_lo, rango_oferta_hi = None, None

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
        # NSE del segmento = por INGRESO real de los hogares del bucket (quién compra), con
        # fallback a clasificación por valor de vivienda si no hay ingreso (integridad).
        ixh_bucket = (db["ixh_w"] / db["ixh_hog"]) if db.get("ixh_hog") else None
        nse_cls = nse_by_ingreso(ixh_bucket) or nse_by_viv(mid_m)

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
        # APLICABILIDAD: el bucket está dentro del rango de valor donde la zona tiene oferta
        # vertical real. Fuera de ese rango se muestra pero se marca no-aplicable.
        if rango_oferta_lo is not None:
            aplicable = (rango_oferta_lo <= i <= rango_oferta_hi)
        else:
            aplicable = True  # sin oferta observada, no se descarta nada (integridad)
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
            "aplicable": aplicable,
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
def _absorcion_realista(nuevas_fam_year: float, n_competidores: int,
                        evidencia_vendidas: int = 0, supply_driven: bool = False) -> float:
    """Absorción REALISTA de UN proyecto (un/mes), no la demanda total del bucket.

    Error metodológico corregido: reportar nuevas_fam/12 asume que un solo proyecto capta el
    100% de la demanda de toda la zona (p. ej. 28 un/mes), lo cual es irreal. La absorción de
    un proyecto es su CUOTA de la demanda mensual, repartida entre la oferta competidora:

        absorción = (nuevas_fam/12) / (competidores + 1)

    El "+1" representa el propio proyecto entrando al mercado. Con más competencia, menor cuota.
    Sin competencia (zona incipiente), el proyecto capta toda la demanda mensual PERO se aplica
    un techo de ritmo comercial realista (un proyecto sano coloca ~3-6 un/mes en preventa), para
    no proyectar absorciones imposibles aunque la demanda anual sea enorme.

    Mercado supply-driven (sin demanda DIM): se reporta desde evidencia de venta real / 24 meses.
    """
    TECHO_PROYECTO = 6.0   # un/mes máximo comercialmente plausible para un solo proyecto
    if supply_driven or (nuevas_fam_year or 0) <= 0:
        if evidencia_vendidas >= 3:
            return round(min((evidencia_vendidas / 24.0) / max(n_competidores, 1), TECHO_PROYECTO), 2)
        return 0.0
    nf_month = (nuevas_fam_year or 0) / 12.0
    cuota = nf_month / (max(n_competidores, 0) + 1)   # reparto entre competidores + el nuevo
    return round(min(cuota, TECHO_PROYECTO), 2)


def derive_productos_horizontal(ft: List[Dict], segments: List[Dict]) -> List[Dict[str, Any]]:
    """
    PRODUCTO DE VIVIENDA HORIZONTAL (casa unifamiliar en venta).

    Replica EXACTAMENTE la metodología DPO de vivienda vertical (misma absorción canónica
    nuevas_fam/12 × captación, mismo anclaje del programa al ticket, recomendado⊆aplicable),
    cambiando solo lo propio de la CASA:
      • DOS áreas: ÁREA_CONSTRUCCIÓN (la que paga el cliente, tamaño principal) y
        ÁREA_TERRENO (dato adicional del lote). En vertical era ÁREA_PRIVATIVA.
      • Bandas de tamaño de CASA (no depa): una casa es más grande que un depa al mismo
        nivel. Anclado a datos reales vh_venta: económica 2 rec ~58-110 m² constr (Valle de
        Lincoln 58/53 NSE D+ $533k); premium 3-4 rec 150-280 m² (Los Cenizos 212/150 NSE A
        $10M; Privada Encinos 270 NSE A $11.5M).
      • m² de CONSTRUCCIÓN observado real de vh_venta manda si existe.
    """
    color_by_status = {
        "sweet_spot": "green", "desatendido": "blue", "oportunidad": "purple",
        "atendido": "teal", "oceano_rojo": "red", "bajo_crecimiento": "amber",
    }
    # Precio/m² de construcción de referencia por NSE para CASA (MXN). Menor que vertical
    # porque la casa reparte valor entre construcción y terreno (no todo es construcción).
    PM2_POR_NSE = {"A": 95000, "B": 70000, "C+": 45000, "C": 32000,
                   "D+": 24000, "D": 18000, "E": 14000}

    def recamaras_por_m2(m2):
        if m2 is None: return "N/D"
        if m2 < 70:  return "2 Rec"
        if m2 < 110: return "2-3 Rec"
        if m2 < 160: return "3 Rec"
        if m2 < 230: return "3-4 Rec"
        return "4 Rec"

    # PROGRAMA DE RECÁMARAS de CASA anclado al TICKET (monotónico). Una casa parte de 2 rec
    # (no hay studios/1 rec en unifamiliar); crece a 3, 3-4 y 4+ con el valor.
    def recamaras_por_ticket(ticket_m, m2=None):
        if ticket_m is None:
            return recamaras_por_m2(m2)
        if ticket_m <= 1.0:   return "2 Rec"      # económica (Valle de Lincoln tipo)
        if ticket_m <= 2.0:   return "2 Rec"
        if ticket_m <= 3.5:   return "3 Rec"
        if ticket_m <= 6.0:   return "3 Rec"
        if ticket_m <= 10.0:  return "3-4 Rec"
        if ticket_m <= 16.0:  return "4 Rec"
        return "4 Rec +"

    # Bandas de tamaño de CONSTRUCCIÓN de casa por ticket (MXN), de datos reales vh_venta:
    #   ≤ 1.0M  → 2 Rec · 55-75 m²    (económica: Valle de Lincoln 58 m²)
    #   ≤ 2.0M  → 2 Rec · 70-95 m²
    #   ≤ 3.5M  → 3 Rec · 90-130 m²
    #   ≤ 6.0M  → 3 Rec · 120-170 m²
    #   ≤ 10.0M → 3-4 Rec · 160-220 m² (Los Cenizos 212 m²)
    #   ≤ 16.0M → 4 Rec · 210-290 m²   (Privada Encinos 270 m²)
    #   > 16.0M → 4 Rec+ · 280-400 m²
    def _banda_constr(ticket_m):
        if ticket_m is None:   return (90, 130)
        if ticket_m <= 1.0:    return (55, 75)
        if ticket_m <= 2.0:    return (70, 95)
        if ticket_m <= 3.5:    return (90, 130)
        if ticket_m <= 6.0:    return (120, 170)
        if ticket_m <= 10.0:   return (160, 220)
        if ticket_m <= 16.0:   return (210, 290)
        return (280, 400)

    # Relación terreno/construcción típica por NSE: en económica el terreno es ~igual o menor
    # (casa de 2 plantas en lote chico); en premium el terreno crece (más jardín/frente).
    def _ratio_terreno(nse):
        return {"A": 0.95, "B": 0.85, "C+": 0.80, "C": 0.85, "D+": 0.90, "D": 0.95, "E": 1.0}.get(nse, 0.85)

    # Competencia directa por bucket (tipologías de vh_venta en el rango de precio)
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

    productos = []
    for s in segments:
        vmin = s.get("val_min"); vmax = s.get("val_max")
        val_mid = None
        if vmin is not None and vmax is not None and (vmin or vmax):
            if vmin and vmax:
                val_mid = (float(vmin) + float(vmax)) / 2
            elif vmax:
                # Bucket inferior (val_min=0): NO usar el techo del bucket como precio. El ticket
                # debe reflejar la CAPACIDAD DE PAGO REAL de la demanda (ingreso del segmento ×
                # 12 × múltiplo hipotecario), no el tope del rango. Evita productos por encima de
                # lo que la población puede pagar (p. ej. casa $1.12M en zona con capacidad $0.66M).
                MULTIPLO_HIPOTECARIO = 4.5
                ing_rep = s.get("ing_min")   # ingreso mensual representativo del segmento (base real)
                cap_compra = (ing_rep * 12 * MULTIPLO_HIPOTECARIO) if ing_rep else None
                if cap_compra:
                    val_mid = min(cap_compra, float(vmax) * 0.75)  # capado al techo del bucket
                else:
                    val_mid = float(vmax) * 0.5   # sin ingreso: punto medio-bajo conservador
            elif vmin:
                val_mid = float(vmin) * 1.1
        ticket_M = round(val_mid / 1e6, 2) if val_mid else None
        if ticket_M and vmin:
            ticket_M = max(ticket_M, round(float(vmin) / 1e6, 2))

        # CONSTRUCCIÓN observada real de vh_venta en el rango (preferida)
        PM2_CASA_MIN = 8000
        constr_obs, terreno_obs, pm2_obs = [], [], []
        for t in ft:
            a = t.get("attributes", {})
            precio = _price(a.get("F____UNIDAD"))
            ac = _num(a.get("ÁREA_CONSTRUCCIÓN"))
            at = _num(a.get("ÁREA_TERRENO"))
            pm2v = _pm2(a.get("F___M2"))
            if precio and val_mid and abs(precio - val_mid) / val_mid < 0.20:
                if ac and M2_MIN <= ac <= M2_MAX: constr_obs.append(ac)
                if at and M2_MIN <= at <= M2_MAX: terreno_obs.append(at)
                if pm2v and pm2v >= PM2_CASA_MIN: pm2_obs.append(pm2v)
        constr_zona = round(statistics.median(constr_obs)) if constr_obs else None
        terreno_zona = round(statistics.median(terreno_obs)) if terreno_obs else None
        pm2_zona = round(statistics.median(pm2_obs)) if pm2_obs else None

        # TAMAÑO DE CONSTRUCCIÓN: 1º observado real; 2º banda del programa por NSE.
        lo_b, hi_b = _banda_constr(ticket_M)
        if constr_zona is not None:
            m2 = max(M2_MIN, min(M2_MAX, constr_zona))
        else:
            pos = {"A": 0.85, "B": 0.65, "C+": 0.5, "C": 0.4, "D+": 0.3, "D": 0.25, "E": 0.2}.get(s["NSE"], 0.5)
            m2 = max(M2_MIN, min(M2_MAX, round(lo_b + (hi_b - lo_b) * pos)))

        # TERRENO: observado real si existe; si no, derivado de la construcción por ratio NSE.
        if terreno_zona is not None:
            m2_terreno = max(M2_MIN, min(M2_MAX, terreno_zona))
        else:
            m2_terreno = round(m2 * _ratio_terreno(s["NSE"]))

        # pm² de construcción derivado (ticket/m²); ancla al observado si existe.
        if ticket_M and m2:
            pm2 = round(ticket_M * 1e6 / m2)
        elif pm2_zona:
            pm2 = pm2_zona
        else:
            pm2 = PM2_POR_NSE.get(s["NSE"], 35000)

        # ABSORCIÓN REALISTA: cuota de la demanda mensual repartida entre competidores (no la
        # demanda total del bucket). Ver _absorcion_realista. Aplica techo comercial por proyecto.
        n_comp = competencia.get(s["bucket"], 0)
        vend = s.get("evidencia_vendidas", 0) or 0
        abs_rate = _absorcion_realista(
            s.get("nuevas_fam", 0) or 0, n_comp, vend,
            supply_driven=(s.get("origen") == "supply_driven"))

        mix_pct = None
        tot_nf = sum(x.get("nuevas_fam", 0) for x in segments) or 0
        if tot_nf and s.get("nuevas_fam"):
            mix_pct = round(s["nuevas_fam"] / tot_nf * 100)
        nse_tca = {"A": 1.39, "B": 1.66, "C+": 1.66, "C": 1.70, "D+": 2.41, "D": 3.49, "E": 0}.get(s["NSE"], 1.5)

        productos.append({
            "tipo": f"{recamaras_por_ticket(ticket_M, m2)} · {s['bucket']}" if m2 else f"{s['NSE']} · {s['bucket']}",
            "badge": f"{mix_pct}%" if mix_pct is not None else "—",
            "color": color_by_status.get(s["status"], "teal"),
            "rec": recamaras_por_ticket(ticket_M, m2),
            "m2": f"{m2} m²" if m2 else "N/D",                     # construcción (tamaño principal)
            "m2_construccion": f"{m2} m²" if m2 else "N/D",
            "m2_terreno": f"{m2_terreno} m²" if m2_terreno else "N/D",
            "pm2": f"${pm2:,}" if pm2 else "N/D",
            "ticket": f"${ticket_M:.2f}M" if ticket_M else "N/D",
            "abs": f"{abs_rate:.1f} un/mes" if abs_rate else "N/D",
            "tca": nse_tca,
            "competidores": n_comp,
            "mercado": f"NSE {s['NSE']} · {s['bucket']} · casa {m2}m² constr / {m2_terreno}m² terreno · {n_comp} competidores",
            "status": s["status"],
            "recomendado": (s.get("aplicable", True)
                            and (s["status"] in ("sweet_spot", "desatendido", "oportunidad", "atendido")))
                           or s.get("dual_featured", False),
            "aplicable": s.get("aplicable", True),
            "featured": s["status"] == "sweet_spot" or s.get("dual_featured", False),
            "seg_dim": f"{s['NSE']} · {s['bucket']}",
            "mkt_segmento": s["mkt_total"], "nuevas_fam": s["nuevas_fam"],
            "categoria": _status_label(s["status"]),
            "perfiles": _perfiles_por_segmento(s["NSE"], m2, ticket_M),
            "nota_mercado": s.get("nota_mercado"),
            "nuevas_fam_year": s.get("nuevas_fam", 0),
            "depth": s.get("mkt_total", 0),
            "abs_num": round(abs_rate, 2) if abs_rate else 0.0,
            "pm2_num": pm2,
            "m2_num": m2,
            "m2_terreno_num": m2_terreno,
            "ticket_num": round(ticket_M * 1e6) if ticket_M else None,
            "mix_num": mix_pct if mix_pct is not None else 0,
        })
    # Un solo featured (idéntico a vertical)
    feats = [p for p in productos if p.get("featured")]
    if len(feats) > 1:
        best = max(feats, key=lambda p: p.get("nuevas_fam", 0))
        for p in feats:
            if p is not best:
                p["featured"] = False
    elif not feats:
        def _abs_num(p):
            try:
                return float(str(p.get("abs", "0")).replace(" un/mes", "")) if p.get("abs") not in (None, "N/D") else 0.0
            except ValueError:
                return 0.0
        pool = [p for p in productos if p.get("recomendado")] or productos
        if pool:
            max(pool, key=_abs_num)["featured"] = True
    return productos


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
    # Recámaras según área interior (m²) — usado solo como respaldo cuando no hay ticket.
    def recamaras_por_m2(m2):
        if m2 is None: return "N/D"
        if m2 < 45:  return "Studio"
        if m2 < 65:  return "1 Rec"
        if m2 < 95:  return "2 Rec"
        if m2 < 140: return "3 Rec"
        return "3-4 Rec"

    # PROGRAMA DE RECÁMARAS anclado al TICKET (regla DPO): crece monotónicamente con el
    # valor del segmento, igual que en las tablas de los reportes. El m² afina el tamaño
    # dentro del programa, pero no determina el nº de recámaras (evita no-monotonías como
    # un bucket de mayor ticket con menos recámaras que uno inferior).
    def recamaras_por_ticket(ticket_m, m2=None):
        if ticket_m is None:
            return recamaras_por_m2(m2)
        if ticket_m <= 1.5:   return "1 Rec"      # económico: 1 recámara habitable
        if ticket_m <= 2.5:   return "1 Rec"
        if ticket_m <= 3.5:   return "2 Rec"
        if ticket_m <= 5.0:   return "2 Rec"
        if ticket_m <= 8.0:   return "2 Rec"      # 2 Rec Core / Sweet Spot
        if ticket_m <= 12.0:  return "3 Rec"
        if ticket_m <= 18.0:  return "3 Rec"
        if ticket_m <= 25.0:  return "3-4 Rec"
        return "4 Rec PH"

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
                # Bucket inferior (val_min=0): anclar a la CAPACIDAD DE PAGO REAL del segmento
                # (ingreso × 12 × múltiplo hipotecario), capado al techo del bucket. Evita
                # productos por encima de lo que la población puede pagar.
                MULTIPLO_HIPOTECARIO = 4.5
                ing_rep = s.get("ing_min")
                cap_compra = (ing_rep * 12 * MULTIPLO_HIPOTECARIO) if ing_rep else None
                if cap_compra:
                    val_mid = min(cap_compra, float(vmax) * 0.75)
                else:
                    val_mid = float(vmax) * 0.5
            elif vmin:
                val_mid = float(vmin) * 1.1

        # DPO anchor: ticket no por debajo del val_min del segmento
        ticket_M = round(val_mid / 1e6, 2) if val_mid else None
        if ticket_M and vmin:
            ticket_M = max(ticket_M, round(float(vmin) / 1e6, 2))

        # ════════ TAMAÑO ANCLADO AL PROGRAMA · REGLA DPO DOCUMENTADA ════════
        # Metodología (reportes Valle Poniente V2 / Calzada): el TAMAÑO NO se deriva de
        # ticket/pm². Se ancla al PROGRAMA DE RECÁMARAS que corresponde al ticket del
        # segmento (un programa habitable real), y el pm² se deriva después como ticket/m².
        # Esto evita metrajes absurdos (p.ej. 28 m² para vivienda económica) cuando el pm²
        # de referencia es alto. El reporte lo enuncia: "a este ticket exigen más de 140 m²"
        # y "al cambiar el tamaño, el mercado ajusta el precio por m²".
        #
        # Bandas de tamaño por ticket (MXN), de las tablas de producto reales de los reportes:
        #   ≤ 1.5M  → 1 Rec · 45-58 m²   (económico: programa mínimo habitable, no studio)
        #   ≤ 2.5M  → 1-2 Rec · 52-68 m²
        #   ≤ 3.5M  → 2 Rec · 62-80 m²
        #   ≤ 5.0M  → 2 Rec · 70-90 m²   (2 Rec Core VP: $7.4M→80 m²; entry: ~70)
        #   ≤ 8.0M  → 2-3 Rec · 80-110 m² (Sweet Spot Calzada: 2 Rec 105 m²)
        #   ≤ 12.0M → 3 Rec · 105-140 m² (Smart Luxury 1Rec+Flex 75; mid 3R ~120)
        #   ≤ 18.0M → 3 Rec · 135-180 m² (Premium Calzada: 3 Rec 160 m²)
        #   ≤ 25.0M → 3-4 Rec · 180-260 m² (Sky-Residence VP: $20M→240 m²)
        #   > 25.0M → 4 Rec PH · 260-360 m² (Grand PH VP: $25M+→320 m²)
        def _banda_tamano(ticket_m):
            if ticket_m is None:   return (70, 90)
            if ticket_m <= 1.5:    return (45, 58)
            if ticket_m <= 2.5:    return (52, 68)
            if ticket_m <= 3.5:    return (62, 80)
            if ticket_m <= 5.0:    return (70, 90)
            if ticket_m <= 8.0:    return (80, 110)
            if ticket_m <= 12.0:   return (105, 140)
            if ticket_m <= 18.0:   return (135, 180)
            if ticket_m <= 25.0:   return (180, 260)
            return (260, 360)

        # pm² OBSERVADO real de la oferta en el rango (si existe) — para anclar a la zona.
        PM2_VERTICAL_MIN = 20000
        pm2_obs = []
        for t in ft:
            a = t.get("attributes", {})
            precio = _price(a.get("F____UNIDAD"))
            pm2v = _pm2(a.get("F___M2"))
            if (precio and val_mid and abs(precio - val_mid) / val_mid < 0.20
                    and pm2v and pm2v >= PM2_VERTICAL_MIN):
                pm2_obs.append(pm2v)
        pm2_zona = round(statistics.median(pm2_obs)) if pm2_obs else None

        # m² OBSERVADO real de la oferta en el rango (si existe) — fuente preferida.
        m2_obs = []
        for t in ft:
            a = t.get("attributes", {})
            precio = _price(a.get("F____UNIDAD"))
            area = _num(a.get("ÁREA_PRIVATIVA"))
            if (precio and val_mid and abs(precio - val_mid) / val_mid < 0.20
                    and area and M2_MIN <= area <= M2_MAX):
                m2_obs.append(area)
        m2_zona = round(statistics.median(m2_obs)) if m2_obs else None

        # TAMAÑO: 1º el observado real de la zona (si hay oferta); 2º la banda de programa
        # del ticket, posicionada según el NSE (NSE alto → extremo superior de la banda).
        lo_b, hi_b = _banda_tamano(ticket_M)
        if m2_zona is not None:
            m2 = max(M2_MIN, min(M2_MAX, m2_zona))   # dato real de la base manda
        else:
            # posición dentro de la banda según NSE (A=alto, C/D=bajo)
            pos = {"A": 0.85, "B": 0.65, "C+": 0.5, "C": 0.4, "D+": 0.3, "D": 0.25, "E": 0.2}.get(s["NSE"], 0.5)
            m2 = round(lo_b + (hi_b - lo_b) * pos)
            m2 = max(M2_MIN, min(M2_MAX, m2))

        # pm² DERIVADO del ticket y el tamaño anclado (regla: pm² = ticket / m²).
        # Si hay pm² observado real de la zona se reporta como ancla de mercado, pero el
        # tamaño ya respeta el programa, así que el pm² derivado es coherente.
        if ticket_M and m2:
            pm2 = round(ticket_M * 1e6 / m2)
        elif pm2_zona:
            pm2 = pm2_zona
        else:
            pm2 = PM2_POR_NSE.get(s["NSE"], 50000)

        # ════════ ABSORCIÓN REALISTA · CUOTA DE MERCADO ════════
        # La absorción de UN proyecto es su cuota de la demanda mensual del segmento, repartida
        # entre la oferta competidora (no la demanda total del bucket). Ver _absorcion_realista.
        # Esto corrige absorciones irreales (p. ej. 28 un/mes = toda la demanda de la zona).
        n_comp = competencia.get(s["bucket"], 0)
        vend = s.get("evidencia_vendidas", 0) or 0
        abs_rate = _absorcion_realista(
            s.get("nuevas_fam", 0) or 0, n_comp, vend,
            supply_driven=(s.get("origen") == "supply_driven"))

        mix_pct = None
        tot_nf = sum(x.get("nuevas_fam", 0) for x in segments) or 0
        if tot_nf and s.get("nuevas_fam"):
            mix_pct = round(s["nuevas_fam"] / tot_nf * 100)
        nse_tca = {"A": 1.39, "B": 1.66, "C+": 1.66, "C": 1.70, "D+": 2.41, "D": 3.49, "E": 0}.get(s["NSE"], 1.5)

        productos.append({
            "tipo": f"{recamaras_por_ticket(ticket_M, m2)} · {s['bucket']}" if m2 else f"{s['NSE']} · {s['bucket']}",
            "badge": f"{mix_pct}%" if mix_pct is not None else "—",
            "color": color_by_status.get(s["status"], "teal"),
            "rec": recamaras_por_ticket(ticket_M, m2),
            "m2": f"{m2} m²" if m2 else "N/D",
            "pm2": f"${pm2:,}" if pm2 else "N/D",
            "ticket": f"${ticket_M:.2f}M" if ticket_M else "N/D",
            "abs": f"{abs_rate:.1f} un/mes" if abs_rate else "N/D",
            "tca": nse_tca,
            "competidores": n_comp,
            "mercado": f"NSE {s['NSE']} · {s['bucket']} · {n_comp} competidores directos",
            "status": s["status"],
            # Recomendado (entra a la mezcla) SOLO si está en el rango de oferta vertical real
            # de la zona (aplicable). Un bucket con demanda demográfica alta pero SIN oferta
            # vertical (p.ej. vivienda económica de la zona ampliada) se muestra pero NO se
            # recomienda para producto vertical: no es captable con este tipo de producto.
            "recomendado": (s.get("aplicable", True)
                            and (s["status"] in ("sweet_spot", "desatendido", "oportunidad", "atendido")))
                           or s.get("dual_featured", False),
            "aplicable": s.get("aplicable", True),
            "featured": s["status"] == "sweet_spot" or s.get("dual_featured", False),
            "seg_dim": f"{s['NSE']} · {s['bucket']}",
            "mkt_segmento": s["mkt_total"], "nuevas_fam": s["nuevas_fam"],
            "categoria": _status_label(s["status"]),
            "perfiles": _perfiles_por_segmento(s["NSE"], m2, ticket_M),
            "nota_mercado": s.get("nota_mercado"),
            # — Campos numéricos para el front (slider de captación y sync con Demanda) —
            "nuevas_fam_year": s.get("nuevas_fam", 0),     # RITMO (flow): nuevas familias/año
            "depth": s.get("mkt_total", 0),                # PROFUNDIDAD (depth): hogares del segmento
            "abs_num": round(abs_rate, 2) if abs_rate else 0.0,   # absorción demand-driven (captación 100%)
            "pm2_num": pm2,
            "m2_num": m2,
            "ticket_num": round(ticket_M * 1e6) if ticket_M else None,
            "mix_num": mix_pct if mix_pct is not None else 0,
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

    # Programa y banda de tamaño anclados al ticket (regla DPO, igual que venta).
    def _banda_tamano_r(ticket_m):
        if ticket_m is None:   return (70, 90)
        if ticket_m <= 1.5:    return (45, 58)
        if ticket_m <= 2.5:    return (52, 68)
        if ticket_m <= 3.5:    return (62, 80)
        if ticket_m <= 5.0:    return (70, 90)
        if ticket_m <= 8.0:    return (80, 110)
        if ticket_m <= 12.0:   return (105, 140)
        if ticket_m <= 18.0:   return (135, 180)
        if ticket_m <= 25.0:   return (180, 260)
        return (260, 360)
    def recamaras_por_ticket_r(ticket_m, m2=None):
        if ticket_m is None:   return recamaras_por_m2(m2)
        if ticket_m <= 2.5:    return "1 Rec"
        if ticket_m <= 8.0:    return "2 Rec"
        if ticket_m <= 18.0:   return "3 Rec"
        if ticket_m <= 25.0:   return "3-4 Rec"
        return "4 Rec PH"

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
        # ticket de compra del segmento (para anclar el programa de tamaño)
        vmin = s.get("val_min"); vmax = s.get("val_max")
        val_mid = None
        if vmin and vmax:
            val_mid = (vmin + vmax) / 2
        elif vmax:
            val_mid = vmax * 0.75
        ticket_M_r = (val_mid / 1e6) if val_mid else None
        # TAMAÑO anclado al programa por ticket, posición por NSE (NO val_mid/pm2)
        lo_b, hi_b = _banda_tamano_r(ticket_M_r)
        pos = {"A": 0.85, "B": 0.65, "C+": 0.5, "C": 0.4, "D+": 0.3, "D": 0.25, "E": 0.2}.get(s["NSE"], 0.5)
        m2 = max(M2_MIN, min(M2_MAX, round(lo_b + (hi_b - lo_b) * pos))) if ticket_M_r else None
        pm2_renta = round(renta_mid / m2) if (renta_mid and m2) else None
        # ABSORCIÓN de renta = nuevas familias que rentan/mes (mkt_renta es stock; usamos nuevas_fam × propensión a rentar)
        nf = s.get("nuevas_fam", 0) or 0
        mkt_total = s.get("mkt_total", 0) or 1
        prop_renta = (s.get("mkt_renta", 0) or 0) / mkt_total if mkt_total else 0
        abs_renta = round(nf / 12 * prop_renta, 2) if nf and prop_renta else None

        productos.append({
            "tipo": f"{recamaras_por_ticket_r(ticket_M_r, m2)} Renta · {s['bucket']}" if m2 else f"Renta {s['NSE']}",
            "rec": recamaras_por_ticket_r(ticket_M_r, m2),
            "m2": f"{m2} m²" if m2 else "N/D",
            "pm2_renta": f"${pm2_renta:,}/m²/mes" if pm2_renta else "N/D",
            "renta_ud": f"${round(renta_mid):,}/mes" if renta_mid else "N/D",
            "abs_renta": f"{abs_renta} contratos/mes" if abs_renta else "N/D",
            "ocupacion_target": "92%",
            "status": s.get("status", "atendido"),
            "recomendado": (s.get("aplicable", True)
                            and s.get("status") in ("sweet_spot", "desatendido", "oportunidad", "atendido")),
            "aplicable": s.get("aplicable", True),
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


# ════════════════════════════════════════════════════════════════════════════
# INVENTARIO POR PROYECTO Y TIPOLOGÍA (formato TYPOLOGIES del front)
# Agrupa las features VVV (ft) por proyecto, en el formato que tplInventario consume.
# Filtra SOLO a los proyectos del universo de los 3 sets (directos/primarios/secundarios)
# para que el inventario muestre exclusivamente los comparables del análisis, no toda
# la ciudad. Integridad: dato ausente = "No disponible"/null, nunca inventado.
# ════════════════════════════════════════════════════════════════════════════
def _build_typologies(ft: List[Dict], nombres_universo: set) -> Dict[str, List[Dict]]:
    def _val(v):
        # -1 es marcador de "no disponible" en los datasets de origen
        n = _num(v)
        return n if (n is not None and n != -1) else None
    typ: Dict[str, List[Dict]] = {}
    for f in ft:
        a = f.get("attributes", f)
        nombre = a.get("PROYECTO") or a.get("Nombre")
        if not nombre:
            continue
        # Filtro: solo proyectos del universo de los 3 sets (si se proporcionó)
        if nombres_universo and nombre not in nombres_universo:
            continue
        area_priv = _val(a.get("ÁREA_PRIVATIVA"))
        area_terr = _val(a.get("ÁREA_DE_TERRAZA"))
        area_total = _val(a.get("ÁREA_TOTAL"))
        precio_ud = _price(a.get("F____UNIDAD"))     # preventa sin tracking → None (nunca 0)
        precio_m2 = _pm2v(a.get("F___M2"))
        total = _val(a.get("UNIDADES_TOTALES"))
        disp = _val(a.get("UNIDADES_DISPONIBLES"))
        vend = _val(a.get("UNIDADES_VENDIDAS"))
        absn = _num(a.get("Abs_Demanda"))
        cajones = _val(a.get("CAJONES_ASIGNADOS"))
        avance = (vend / total) if (total and vend is not None) else None
        typ.setdefault(nombre, []).append({
            "tipo": int(_val(a.get("TIPO"))) if _val(a.get("TIPO")) is not None else len(typ.get(nombre, [])) + 1,
            "area_priv": area_priv,
            "area_terr": area_terr if area_terr is not None else "No disponible",
            "area_total": area_total,
            "rec": int(_val(a.get("CANTIDAD_DE_RECAMARAS"))) if _val(a.get("CANTIDAD_DE_RECAMARAS")) is not None else None,
            "precio_ud": precio_ud,
            "precio_m2": precio_m2,
            "unid_total": int(total) if total is not None else None,
            "unid_disp": int(disp) if disp is not None else None,
            "unid_vend": int(vend) if vend is not None else None,
            "abs": round(absn, 4) if absn is not None else 0.0,
            "avance": round(avance, 4) if avance is not None else 0.0,
            "cajones": int(cajones) if cajones is not None else "No disponible",
        })
    # Ordenar tipologías de cada proyecto por precio_ud ascendente (None al final)
    for nombre in typ:
        typ[nombre].sort(key=lambda t: (t["precio_ud"] is None, t["precio_ud"] or 0))
    return typ


# ════════════════════════════════════════════════════════════════════════════
# VARIABLES NOMBRADAS DEL ANÁLISIS (ANALYSIS_VARS)
# Objeto único generado por cada análisis a partir del PIN. Es la FUENTE ÚNICA DE
# VERDAD que TODAS las secciones del front consumen (z._vars). Evita fuentes
# desincronizadas: Mapa, Inventario, Demanda, Producto, Mezclas y Monitor leen de aquí.
# ════════════════════════════════════════════════════════════════════════════
def build_analysis_vars(req, profile, isocronas, perception, demografia,
                        segments, productos, productos_renta, proyectos, kpis) -> Dict[str, Any]:
    """Consolida todas las variables clave del análisis en un solo objeto nombrado.
    Todo proviene de datos reales del análisis (sin promedios inventados). El front
    llama z._vars.<nombre> en cualquier sección para mostrar valores coherentes."""
    comp = (perception or {}).get("competidores") or {}
    merc = (perception or {}).get("mercados") or {}
    iso_keys = sorted(int(m) for m in (isocronas or {}).keys())
    # Universo de los 3 sets (azul+verde+morado) = todos los proyectos clasificados
    universo = (comp.get("directos") or []) + (comp.get("primarios") or []) + (comp.get("secundarios") or [])
    return {
        # — Pin y predio —
        "pin": {"lat": req.lat, "lng": req.lng},
        "predio_m2": req.predio_m2,
        "uso_comercial": req.uso_comercial,
        # — Isócronas (zonas) —
        "perfil_iso": profile["key"],
        "perfil_label": profile["label"],
        "isocrona_primaria_min": iso_keys[0] if iso_keys else None,      # azul
        "isocrona_secundaria_min": iso_keys[-1] if len(iso_keys) > 1 else None,  # verde
        "isocronas_min": iso_keys,
        # — Zona de influencia real (morado) —
        "zona_poligono": (perception or {}).get("zona_poligono"),
        "barrera_mercado": (perception or {}).get("barrera", False),
        "mercados_detectados": merc.get("k"),
        "gap_separabilidad": merc.get("gap"),
        "varianza_explicada": merc.get("var_explained"),
        # — 3 sets de competidores —
        "competidores_directos": comp.get("directos") or [],
        "competidores_primarios": comp.get("primarios") or [],
        "competidores_secundarios": comp.get("secundarios") or [],
        "n_directos": comp.get("n_directos", 0),
        "n_primarios": comp.get("n_primarios", 0),
        "n_secundarios": comp.get("n_secundarios", 0),
        # — Universo de oferta (azul+verde+morado) para Inventario/KPIs/Mezclas —
        "universo_proyectos": universo,
        "n_universo": len(universo),
        "proyectos": proyectos,         # detalle completo de oferta vertical
        "kpis": kpis,
        # — Demografía / demanda (datos granulares reales de la base) —
        "poblacion": demografia.get("population"),
        "hogares": demografia.get("households"),
        "ingreso_hogar": demografia.get("ingreso_hogar"),     # IXH real del NSE dominante
        "nse_dominante": demografia.get("nse_dominante"),
        "tca": demografia.get("tca"),
        # — Ubicación geográfica real (de la base ArcGIS) —
        "municipio": demografia.get("municipio"),
        "estado": demografia.get("estado"),
        "pais": demografia.get("pais"),
        "municipios_todos": demografia.get("municipios_todos"),
        "segmentos_demanda": segments,                        # estratos granulares + aplicable
        # — Producto / sweet spot —
        "productos": productos,
        "productos_renta": productos_renta,
        "sweet_spot": next((p for p in (productos or []) if p.get("featured")), None),
    }


def _zone_label(producto_modo: str, kpis: Dict) -> Optional[str]:
    """Etiqueta de la zona acorde al MODO analizado y a los KPIs REALES de oferta.
    Si no hay oferta (proyectos=0), lo indica explícitamente en vez de inventar cifras."""
    label_modo = {
        "vivienda_vertical": "Vivienda vertical",
        "vivienda_horizontal": "Vivienda horizontal",
        "lotes": "Lotes urbanizados", "industrial": "Industrial",
        "logistica": "Logística", "oficinas": "Oficinas", "hotel": "Hotel",
    }.get(producto_modo, "Análisis")
    n_proy = kpis.get("proyectos") or 0
    n_uds = kpis.get("unidades")
    if n_proy == 0:
        return f"{label_modo} · sin oferta en comercialización en la zona"
    uds_txt = f"{n_uds:,} unidades" if n_uds else "unidades N/D"
    return f"{label_modo} · {n_proy} proyectos en comercialización · {uds_txt}"


def assemble_zone_payload(req, profile, isocronas, resumen, ft, pagos, resumen_renta,
                          demografia, nse_dim, segments, productos, productos_renta,
                          comercio, perception, agebs_count,
                          agebs=None, ft_renta=None, agebs_geo=None,
                          producto_modo="vivienda_vertical") -> Dict[str, Any]:
    agebs = agebs or []
    ft_renta = ft_renta or []
    agebs_geo = agebs_geo or []
    proyectos = _build_proyectos(resumen)
    kpis = _build_kpis(proyectos, ft)
    inv = _build_inventario(ft)

    # Centro = pin del predio
    center = [req.lat, req.lng]

    # IDENTIFICACIÓN DE ZONA: de la base ArcGIS (real), no del request. El front manda el pin;
    # la zona (municipio, estado) se DERIVA de los AGEBs que caen en la isócrona. Si aún no hay
    # demografía (sin AGEBs), queda None y el front muestra en blanco hasta tener datos.
    municipio = demografia.get("municipio")
    estado = demografia.get("estado")
    pais = demografia.get("pais")
    # Nombre de la zona = municipio real (la unidad geográfica que la base entrega). El front
    # ya no muestra un escenario previo: si no hay municipio, el nombre queda None.
    zone_name = municipio or req.zone_name or None
    # Subtítulo solo con los componentes que existen (sin "N/D · N/D · México").
    subt_parts = [p for p in (municipio, estado, pais) if p]
    subtitle = " · ".join(subt_parts) if subt_parts else None

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
        "subtitle": subtitle,
        "municipality": municipio,
        "label": _zone_label(producto_modo, kpis),
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
                "sin_valor_percibido": perception.get("sin_valor_percibido", False),
                "nota_valor": perception.get("nota_valor"),
                "proyectos": perception["proyectos"],
                "cluster_names": perception.get("cluster_names"),
                "ajuste_inventario": perception.get("ajuste_inventario"),
                "zona_poligono": perception.get("zona_poligono"),
                "mercados": perception.get("mercados"),
                "competidores": perception.get("competidores"),
            },
            "nse_barrier": _nse_barrier_info(agebs, agebs_geo),
            "agebs_geo": agebs_geo,
        },
        "_vars": build_analysis_vars(req, profile, isocronas, perception, demografia,
                                     segments, productos, productos_renta, proyectos, kpis),
        "_typologies": _build_typologies(
            ft,
            {p.get("name") for grp in ("directos", "primarios", "secundarios")
             for p in ((perception or {}).get("competidores") or {}).get(grp, [])
             if p.get("name") and p.get("name") != "N/D"}
        ),
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
        "di_detail": _build_di_detail(agebs),
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


def _build_di_detail(agebs):
    """Detalle demográfico real de la zona (tipo de vivienda, situación conyugal, población en
    hogares, composición), en el formato que el front consume. Reemplaza el bloque hardcodeado:
    todo proviene de los AGEBs de la isócrona actual. Ausencia → listas vacías (no se inventa)."""
    if not agebs:
        return {"tipo_vivienda": [], "situacion_conyugal": [], "situacion_conyugal_total": 0,
                "poblacion_hogares": [], "tipologia_hogar": [], "personas_hogar": {}}

    def s(col):
        v = _sum(agebs, col)
        return round(v) if v is not None else 0

    # ── Tipo de vivienda (conteo real) ──
    tv = [
        ("Casa", s("Casa")),
        ("Departamento o edificio", s("Departamento o edificio")),
        ("Vivienda en vecindad o cuartería", s("Vivienda en vecidad o cuartería ") or s("Vivienda en vecidad o cuartería")),
        ("Otro tipo de vivienda", s("Otro tipo de vivienda")),
    ]
    tv_total = sum(c for _, c in tv) or 1
    tipo_vivienda = [{"label": l, "count": c, "pct": round(c / tv_total * 100, 2)}
                     for l, c in tv if c > 0]

    # ── Situación conyugal (suma de todas las bandas de edad) ──
    edades = ["20 a 24", "25 a 29", "30 a 34", "35 a 39", "40 a 44", "45 a 49", "50 a 54",
              "55 a 59", "60 a 64", "65 a 69", "70 a 74", "75 y Más"]
    conyugal_cols = {"Soltera": ["soltera"], "Casada": ["casada"],
                     "En unión libre": ["en union libre"],
                     "Separada, divorciada o viuda": ["separad  divorcia", "separad"]}
    cony = {}
    for label, sufs in conyugal_cols.items():
        tot = 0
        for e in edades:
            for suf in sufs:
                val = s(f"{e} {suf}")
                if val:
                    tot += val
                    break   # usar el primer sufijo que exista para esa edad
        cony[label] = tot
    cony_total = sum(cony.values()) or 1
    situacion_conyugal = [{"label": l, "count": c, "pct": round(c / cony_total * 100, 2)}
                          for l, c in cony.items() if c > 0]

    # ── Composición de hogares (población en hogares) ──
    hc = _build_hog_comp(agebs)
    fam = hc.get("familiares_total") or 0
    nofam = hc.get("no_familiares_total") or 0
    th_total = (fam + nofam) or 1
    tipologia_hogar = []
    if fam:
        tipologia_hogar.append({"label": "Hogares familiares", "count": fam,
                                "pct": round(fam / th_total * 100, 2), "parent": True})
        for sub, key in [("Nucleares", "nucleares"), ("Ampliados", "ampliados"), ("Compuestos", "compuestos")]:
            c = hc.get(key) or 0
            if c:
                tipologia_hogar.append({"label": sub, "count": c,
                                        "pct": round(c / fam * 100, 2), "parent_group": "familiares"})
    if nofam:
        tipologia_hogar.append({"label": "Hogares no familiares", "count": nofam,
                                "pct": round(nofam / th_total * 100, 2), "parent": True})
        for sub, key in [("Unipersonales", "unipersonal"), ("Corresidentes", "corresidentes")]:
            c = hc.get(key) or 0
            if c:
                tipologia_hogar.append({"label": sub, "count": c,
                                        "pct": round(c / nofam * 100, 2), "parent_group": "no_familiares"})

    personas_hogar = _wavg(agebs, "Personas por hogar 2026", "Hogares totales 2026")
    # Personas por hogar familiar / no familiar (de PXHFAMILIARES si existe; si no, derivado)
    ph_fam = _wavg(agebs, "PXHFAMILIARES", "Hogares familiares totales")
    ph_nofam = _wavg(agebs, "PXHNOFAMILIARES", "Hogares  no familiares totales")
    # Población en hogares (familiares vs no familiares) — estructura paralela a tipologia_hogar
    pob_fam = s("Población en hogares familiares") or (round(fam * ph_fam) if (fam and ph_fam) else 0)
    pob_nofam = s("Población en hogares no familiares") or (round(nofam * ph_nofam) if (nofam and ph_nofam) else 0)
    pob_h_total = (pob_fam + pob_nofam) or 1
    poblacion_hogares = []
    if pob_fam:
        poblacion_hogares.append({"label": "Población en hogares familiares", "count": pob_fam,
                                  "pct": round(pob_fam / pob_h_total * 100, 2), "parent": True})
    if pob_nofam:
        poblacion_hogares.append({"label": "Población en hogares no familiares", "count": pob_nofam,
                                  "pct": round(pob_nofam / pob_h_total * 100, 2), "parent": True})

    return {
        "tipo_vivienda": tipo_vivienda,
        "situacion_conyugal": situacion_conyugal,
        "situacion_conyugal_total": round(cony_total) if cony_total != 1 else 0,
        "tipologia_hogar": tipologia_hogar,
        "poblacion_hogares": poblacion_hogares,
        "personas_hogar": {
            "promedio_ponderado": round(personas_hogar, 2) if personas_hogar else None,
            "familiares": round(ph_fam, 2) if ph_fam else (round(personas_hogar, 2) if personas_hogar else None),
            "no_familiares": round(ph_nofam, 2) if ph_nofam else None,
        },
    }


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
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


PRSP_BASE = os.environ.get("PRSP_BASE", "https://payment-system-prsp.onrender.com")
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "180"))

# Directorio de estáticos: subcarpeta "static/" junto a este app.py.
# Se resuelve relativo al archivo para que funcione igual en local y en Render.
STATIC_DIR = Path(os.environ.get("DATARIA_STATIC_DIR", str(Path(__file__).resolve().parent / "static")))
TABLERO_FILE = STATIC_DIR / "dashboard_zona_analisis.html"

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
    # Modo de producto a analizar. El front (selector superior) define cuál.
    # "vivienda_vertical" (default, no rompe nada) reusa el pipeline existente.
    # "vivienda_horizontal" usa la capa vh_venta y el diseño de producto de casa.
    # Los demás (lotes, industrial, logistica, oficinas, hotel) quedan declarados
    # pero aún no implementados: el backend responde no_disponible para ellos.
    producto: str = "vivienda_vertical"


# Modos de producto reconocidos. activo=True → pipeline implementado; False → placeholder.
PRODUCTO_MODES = {
    "vivienda_vertical":   {"label": "Vivienda vertical",   "activo": True,  "oferta_layer": "vv_venta"},
    "vivienda_horizontal": {"label": "Vivienda horizontal", "activo": True,  "oferta_layer": "vh_venta"},
    "lotes":               {"label": "Lotes",               "activo": False, "oferta_layer": None},
    "industrial":          {"label": "Industrial",          "activo": False, "oferta_layer": None},
    "logistica":           {"label": "Logística",           "activo": False, "oferta_layer": None},
    "oficinas":            {"label": "Oficinas",            "activo": False, "oferta_layer": None},
    "hotel":               {"label": "Hotel",               "activo": False, "oferta_layer": None},
}


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


def parse_di_geometria(zip_bytes: bytes) -> List[Dict[str, Any]]:
    """Extrae la GEORREFERENCIACIÓN de cada AGEB del KMZ que viene en la respuesta de
    DescargaDI (activeMap='NSE'). Devuelve, por AGEB: centroide (lng,lat), su NSE
    ordinal (1=A … creciente hacia NSE bajo) y su NSE textual.

    Fuente: el mismo ZIP que ya se consulta para la demografía (no hay red adicional).
    El KMZ trae un Placemark por AGEB con id 'NSE_<ordinal>_<idx>', styleUrl '#NSE_<ordinal>'
    y la geometría poligonal real. El XLSX (atributos) y el KMZ (geometría) NO vienen en
    el mismo orden y el KMZ no trae CVEGEO, por eso la geometría se usa como capa propia
    (geometría + NSE), no se fusiona fila a fila con el XLSX. Para la barrera de mercado
    socioeconómica esto es suficiente: lo que importa es dónde está cada nivel de NSE.

    Integridad: si no hay KMZ o no se puede parsear, devuelve [] (sin inventar posiciones).
    """
    try:
        z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except Exception:
        return []
    kmz_name = next((n for n in z.namelist() if n.endswith(".kmz")), None)
    if not kmz_name:
        return []
    try:
        kml = zipfile.ZipFile(io.BytesIO(z.read(kmz_name))).read("doc.kml").decode("utf-8", errors="ignore")
    except Exception:
        return []

    out = []
    for m in re.finditer(r'<Placemark id="([^"]+)">(.*?)</Placemark>', kml, re.S):
        pid, body = m.group(1), m.group(2)
        mo = re.match(r'NSE_(\d+)_', pid)
        nse_ord = int(mo.group(1)) if mo else None
        mt = re.search(r'ingreso</td>\s*<td>([^<]+)</td>', body)
        nse_txt = mt.group(1).strip() if mt else None
        xs, ys = [], []
        for co in re.findall(r"<coordinates>(.*?)</coordinates>", body, re.S):
            for tok in co.strip().split():
                p = tok.split(",")
                if len(p) >= 2:
                    try:
                        xs.append(float(p[0])); ys.append(float(p[1]))
                    except ValueError:
                        pass
        if not xs:
            continue
        cent_lng = sum(xs) / len(xs)
        cent_lat = sum(ys) / len(ys)
        out.append({
            "nse_rank": nse_ord,        # ordinal del NSE (señal para el clustering)
            "nse_txt": nse_txt,         # NSE textual (A..E / Industrial)
            "lng": round(cent_lng, 6),
            "lat": round(cent_lat, 6),
            "n_vertices": len(xs),
        })
    return out


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
@app.get("/")
async def root():
    """Raíz informativa del API. El tablero se sirve en /tablero."""
    return {
        "ok": True,
        "service": "dataria-orchestrator",
        "version": "2.0",
        "tablero": "/tablero",
        "endpoints": ["/health", "/api/zona/poligono", "/api/zona/procesar",
                      "/api/zona/analyze", "/api/zona/procesar_auth",
                      "/api/secciones", "/api/cuentas"],
    }


@app.get("/tablero")
async def tablero():
    """Sirve el tablero (dashboard_zona_analisis.html) desde static/.

    Integridad: si el archivo no existe, devolver 404 explícito en vez de
    reventar el servidor. Así el despliegue del API no depende de que el
    estático esté presente.
    """
    if not TABLERO_FILE.is_file():
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": "Tablero no encontrado",
                "detalle": "Falta static/dashboard_zona_analisis.html en el despliegue.",
                "ruta_esperada": str(TABLERO_FILE),
            },
        )
    # no-cache para que cada despliegue del HTML se sirva fresco
    return FileResponse(
        str(TABLERO_FILE),
        media_type="text/html; charset=utf-8",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


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

        # Anillo base (azul · 8 min) = zona PRIMARIA. Anillo mayor (verde · principal)
        # = zona SECUNDARIA. La oferta y la demanda se traen del anillo MAYOR (azul+verde
        # combinadas), y luego se clasifica cada proyecto en su set (directo/primario/secundario).
        base_min = 8 if 8 in isocronas else profile["principal"]
        base_ring = isocronas[base_min]["coordinates"][0]
        outer_min = profile["principal"]                       # mayor isócrona del perfil (verde)
        outer_ring = isocronas[outer_min]["coordinates"][0] if outer_min in isocronas else base_ring

        # 2 · Oferta (VVV) venta + renta · universo = anillo MAYOR (azul+verde)
        try:
            vvv_venta = await fetch_vvv(client, outer_ring, "vv_venta")
            vvv_renta = await fetch_vvv(client, outer_ring, "vv_renta")
        except httpx.HTTPError as e:
            raise HTTPException(502, f"VVV no disponible: {e}")

        # 3 · Demografía (DescargaDI · NSE) · universo = anillo MAYOR (demanda azul+verde)
        di_bytes = await fetch_descarga_di(client, outer_ring, "NSE")

    agebs = parse_di_xlsx(di_bytes) if di_bytes else []

    # ── Derivación VVV: proyectos resumen + tipologías ft ──
    resumen = vvv_venta.get("datasets", {}).get("resumen", [])
    ft = vvv_venta.get("datasets", {}).get("ft", [])
    pagos = vvv_venta.get("datasets", {}).get("pagos", [])
    resumen_renta = vvv_renta.get("datasets", {}).get("resumen", [])
    ft_renta = vvv_renta.get("datasets", {}).get("ft", [])

    # Percepción de valor + ajuste de zona de influencia (detección de mercados)
    perception = value_perception_adjust(resumen, base_ring, req.lng, req.lat)

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

    RUTEO POR MODO DE PRODUCTO (req.producto):
    El pipeline demográfico (isócronas, DI, percepción, competidores, segmentos,
    comercio) es COMÚN a todos los modos y se ejecuta una sola vez. Solo cambian
    dos puntos según el modo: (1) la capa de oferta que se consulta, (2) la función
    que diseña el producto. Esto comparte memoria entre modos: no se cargan dos
    pipelines, solo se enruta la oferta y el diseño de producto.
    """
    modo = req.producto if req.producto in PRODUCTO_MODES else "vivienda_vertical"
    modo_cfg = PRODUCTO_MODES[modo]
    # Modos declarados pero aún no implementados → respuesta explícita (no se procesa)
    if not modo_cfg["activo"]:
        return {
            "ok": False, "stage": "procesar",
            "producto": modo, "producto_label": modo_cfg["label"],
            "no_disponible": True,
            "mensaje": f"El análisis de {modo_cfg['label']} aún no está disponible. "
                       f"Modos activos: vivienda vertical y vivienda horizontal.",
            "modos_activos": [k for k, v in PRODUCTO_MODES.items() if v["activo"]],
            "errors": {},
        }
    oferta_layer = modo_cfg["oferta_layer"]   # "vv_venta" o "vh_venta"

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
        # Anillo MAYOR (verde · zona secundaria). Oferta y demanda se traen de azul+verde
        # combinadas; luego se clasifica cada proyecto en su set (directo/primario/secundario).
        outer_min = profile["principal"]
        outer_ring = isocronas[outer_min]["coordinates"][0] if outer_min in isocronas else base_ring

        # VVV (oferta) — universo = anillo MAYOR. La capa depende del modo:
        # vivienda_vertical → vv_venta (+vv_renta); vivienda_horizontal → vh_venta (sin renta).
        vvv_venta, vvv_renta = {}, {}
        try:
            vvv_venta = await fetch_vvv(client, outer_ring, oferta_layer)
        except Exception as e:
            errors["vvv_venta"] = str(e)
        # Renta solo aplica a vivienda vertical (no hay capa de renta horizontal)
        if modo == "vivienda_vertical":
            try:
                vvv_renta = await fetch_vvv(client, outer_ring, "vv_renta")
            except Exception as e:
                errors["vvv_renta"] = str(e)

        # DescargaDI (demografía) — universo = anillo MAYOR (demanda azul+verde)
        di_bytes = None
        try:
            di_bytes = await fetch_descarga_di(client, outer_ring, "NSE")
        except Exception as e:
            errors["descarga_di"] = str(e)

    # FILTRO ESPACIAL: garantizar que solo entren proyectos/tipologías DENTRO del anillo mayor
    vvv_venta = filter_vvv_by_polygon(vvv_venta, outer_ring)
    vvv_renta = filter_vvv_by_polygon(vvv_renta, outer_ring)
    if vvv_venta.get("_spatial_filter"):
        sf = vvv_venta["_spatial_filter"]
        if sf["resumen_total"] > sf["resumen_in"] or sf["ft_total"] > sf["ft_in"]:
            errors["filtro_espacial"] = (f"VVV devolvió fuera de zona: "
                f"resumen {sf['resumen_total']}→{sf['resumen_in']}, ft {sf['ft_total']}→{sf['ft_in']}")

    agebs = parse_di_xlsx(di_bytes) if di_bytes else []
    # Georreferenciación de AGEBs (centroide + NSE) desde el KMZ del MISMO ZIP (sin red extra).
    # Capa propia para detectar la barrera de mercado socioeconómica (NSE/posición).
    try:
        agebs_geo = parse_di_geometria(di_bytes) if di_bytes else []
    except Exception as e:
        agebs_geo = []
        errors["agebs_geo"] = str(e)
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

    perception = _safe(lambda: value_perception_adjust(resumen, base_ring, req.lng, req.lat, agebs_geo), "perception",
                       {"n_total": 0, "n_zona": 0, "media": None, "sd": None, "cv": None,
                        "barrera": False, "metodo": "isocrona", "cobertura_pct": 0,
                        "motivo": "No disponible", "proyectos": [], "cluster_names": None})

    # ── CLASIFICACIÓN DE COMPETIDORES EN 3 ZONAS ──
    # El inventario/KPIs/productos usan el universo COMPLETO (azul+verde combinadas).
    # El morado define el set de competidores DIRECTOS para el análisis competitivo.
    # IMPORTANTE: la barrera de NSE recorta la zona de DEMANDA (qué AGEBs generan demanda),
    # no el set de oferta competidora. Si el método es barrera_nse, los competidores se
    # clasifican por isócrona (no por el polígono de demanda, que cubriría toda la oferta).
    zona_para_competidores = (None if perception.get("metodo") == "barrera_nse"
                              else perception.get("zona_poligono"))
    competidores = _safe(
        lambda: clasificar_competidores(resumen, base_ring, outer_ring, zona_para_competidores),
        "competidores",
        {"directos": [], "primarios": [], "secundarios": [],
         "n_directos": 0, "n_primarios": 0, "n_secundarios": 0})
    perception["competidores"] = competidores
    # Nota de zona (sin recortar inventario): describe el set directo
    if perception.get("barrera"):
        if perception.get("metodo") == "barrera_nse":
            perception["ajuste_inventario"] = (
                f"Zona de demanda recortada por barrera socioeconómica (NSE). "
                f"Competidores por cercanía: primarios (8 min) {competidores['n_primarios']} · "
                f"secundarios ({outer_min} min) {competidores['n_secundarios']}.")
        else:
            perception["ajuste_inventario"] = (
                f"Competidores directos (mercado del predio): {competidores['n_directos']} proyectos. "
                f"Primarios (8 min): {competidores['n_primarios']} · "
                f"Secundarios ({outer_min} min): {competidores['n_secundarios']}. "
                f"Inventario y KPIs usan el universo completo (zona primaria + secundaria).")

    demografia = _safe(lambda: derive_demografia(agebs, ft), "demografia", derive_demografia([]))
    nse_dim = _safe(lambda: derive_nse_dim(agebs), "nse_dim", [])
    # DEMANDA según modo: horizontal pondera por proporción de casa; vertical usa la genérica.
    tipo_viv = "horizontal" if modo == "vivienda_horizontal" else "vertical"
    segments = _safe(lambda: derive_segments(agebs, ft, tipo_viv), "segments", [])
    # PRODUCTO según modo. Vertical: depa (área privativa). Horizontal: casa (terreno+construcción).
    # La renta solo existe en vertical.
    if modo == "vivienda_horizontal":
        productos = _safe(lambda: derive_productos_horizontal(ft, segments), "productos", [])
        productos_renta = []
    else:
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
        agebs=agebs, ft_renta=ft_renta, agebs_geo=agebs_geo,
        producto_modo=modo,
    )
    payload["stage"] = "procesar"
    payload["producto"] = modo
    payload["producto_label"] = modo_cfg["label"]
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
