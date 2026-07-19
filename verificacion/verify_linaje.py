#!/usr/bin/env python3
"""VERIFY-LINAJE · Auditoría de linaje de variables (Héctor · 19 jul 2026).
Cruce ESTÁTICO entre lo que el backend PRODUCE (claves de payload en app.py), lo que el
CATÁLOGO documenta (docs/CATALOGO_VARIABLES.md) y lo que el FRONT CONSUME
(static/dashboard_zona_analisis.html). Detecta:
  A) claves producidas por el backend que el front usa pero el catálogo NO documenta
  B) variables del catálogo sin productor aparente en el backend (documentación huérfana)
  C) claves producidas que nadie consume en el front (carga muerta o API-only: se listan)
  D) claves que el front consume y el backend no produce (riesgo de undefined)
Es heurístico (regex sobre código): un hallazgo es un PUNTO A REVISAR, no un veredicto.
Corre OFFLINE. Uso: python3 verificacion/verify_linaje.py [--full]"""
import re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
app = (ROOT / "app.py").read_text(encoding="utf-8")
html = (ROOT / "static/dashboard_zona_analisis.html").read_text(encoding="utf-8")
cat = (ROOT / "docs/CATALOGO_VARIABLES.md").read_text(encoding="utf-8")

# ── 1 · PRODUCIDAS: claves string en dicts del backend ("clave": …) ──
producidas = collections.Counter(m.group(1) for m in re.finditer(r'"([a-z_][a-z0-9_]{2,40})"\s*:', app))
# ── 2 · CATALOGADAS: primer token de cada fila de tabla del catálogo ──
catalogadas = set()
for line in cat.splitlines():
    m = re.match(r'\|\s*([A-Za-z_][\w\.\[\]\{\}, /]*?)\s*\|', line)
    if m and m.group(1).lower() not in ("variable", "---"):
        for tok in re.findall(r"[a-z_][a-z0-9_]{2,40}", m.group(1)):
            catalogadas.add(tok)
# ── 3 · CONSUMIDAS: accesos .clave y ['clave'] en el JS del front ──
main_js = max(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.DOTALL), key=len)
consumidas = collections.Counter()
for m in re.finditer(r"\.([a-z_][a-z0-9_]{2,40})\b", main_js):
    consumidas[m.group(1)] += 1
for m in re.finditer(r"\[['\"]([a-z_][a-z0-9_]{2,40})['\"]\]", main_js):
    consumidas[m.group(1)] += 1

# ── Ruido a excluir: builtins JS/Py, atributos DOM, palabras comunes ──
RUIDO = set("""length map filter push join slice splice concat replace split indexOf includes forEach reduce
find findIndex sort some every keys values entries toFixed toLocaleString toString charAt trim toLowerCase
toUpperCase innerHTML textContent style value classList dataset getElementById querySelector querySelectorAll
appendChild removeChild addEventListener createElement getContext round floor ceil abs max min pow sqrt random
log warn error stringify parse then catch json ok status headers body method name label color key type text
title width height data options scales plugins legend display position ticks grid font size weight radius
borderWidth backgroundColor borderColor datasets labels x y r id class html head tail sum get set add has
items item index count total copy update pop remove clear next iter range len str int float dict list tuple
bool none true false null undefined self cls args kwargs return yield lambda print open read write close
append extend insert lower upper strip startswith endswith format enumerate zip sorted reversed isinstance
getattr setattr hasattr globals locals super init main env environ path exists mkdir""".split())

prod = {k for k, v in producidas.items() if k not in RUIDO and v >= 1}
cons = {k for k, v in consumidas.items() if k not in RUIDO}

A_sin_catalogo = sorted((prod & cons) - catalogadas)
B_sin_productor = sorted(catalogadas - prod - cons)
C_sin_consumidor = sorted(prod - cons - catalogadas)
D_sin_productor_front = sorted(cons - prod)

def reporte(titulo, lst, cap=40):
    print(f"\n── {titulo} · {len(lst)} ──")
    for x in lst[:cap]:
        print("  ", x)
    if len(lst) > cap:
        print(f"   … y {len(lst)-cap} más (corre con --full)")

full = "--full" in sys.argv
cap = 10000 if full else 40
print("VERIFY-LINAJE · heurístico: cada punto es A REVISAR, no un veredicto")
print(f"producidas backend: {len(prod)} · catalogadas: {len(catalogadas)} · consumidas front: {len(cons)}")
reporte("A · producida Y consumida pero SIN catálogo (documentar)", A_sin_catalogo, cap)
reporte("B · catalogada sin productor NI consumidor aparente (¿huérfana/renombrada?)", B_sin_productor, cap)
reporte("C · producida sin consumidor front (¿carga muerta o API-only?)", C_sin_consumidor, cap)
reporte("D · consumida en front sin productor backend (¿riesgo undefined o var local JS?)", D_sin_productor_front, cap)
