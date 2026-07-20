# AUDITORÍA COMPLETA DE LA HERRAMIENTA · registro vivo
**Arrancada 19 jul 2026 por orden de Héctor ("todo; primero lo autónomo"). Método en 6
piezas (V&V adaptado a Dataria): (1) linaje de datos, (2) fidelidad de método, (3)
invariantes automáticas, (4) pruebas metamórficas, (5) panel de anclas, (6) validez externa.**

## Estado inicial (19 jul 2026 · fase autónoma)

### Pieza 1 · LINAJE — herramienta instalada + primer censo
`verificacion/verify_linaje.py` (nuevo): cruza lo PRODUCIDO por el backend, lo DOCUMENTADO
en el catálogo y lo CONSUMIDO por el front. Censo inicial:
- Producidas backend: **608** claves · Consumidas front: **489** · Catalogadas: **59**
- **HALLAZGO MAYOR A·295**: variables producidas Y consumidas SIN entrada de catálogo — la
  regla de gobierno del catálogo nunca se aplicó retroactivamente al vocabulario histórico
  (el catálogo solo creció con lo nuevo). Plan: backfill POR SECCIÓN durante la auditoría
  (documentar significado desde el código; el catálogo solo crece → es documentación, no
  cambio de reglas).
- C·270: producidas sin consumidor front — mezcla de claves internas/API-only legítimas y
  posible carga muerta → triage por sección.
- B·10: mayormente falsos positivos del heurístico (fragmentos de prosa del regex) — el
  script se declara heurístico: cada punto es A REVISAR, no veredicto.

### Piezas 2-3-5 · lo ya cubierto ANTES de esta auditoría (acumulado)
Método vs código: auditoría §9 de METODOLOGIA (6 jul) + sesión una-por-una (18 jul, 5
preguntas + 7 decisiones + §10 parámetros). Invariantes: verify_reglas 20 · verify_unit 23
· verify_all/render · verify_interactive (ahora también en página real). Anclas activas:
ZMM Centro, Valle Poniente, GDL Centro, pin del director, pin de validación de Héctor.

### Pieza 6 · validez externa — primer caso PASADO
Ejercicio de doble intérprete (19 jul, pin 25.65816,-100.44901 · 3,000 m² · vertical):
lectura independiente de ingredientes vs recomendación de la herramienta → CONVERGENCIA
ALTA (hueco $15-25M, sweet $8.5M en núcleo, océano rojo $5-7M, no-aplicables abajo).
Punto de regla abierto para Héctor: ¿producto de banda B en predio de percepción A?
El laboratorio respaldó el programa (estrella West Torre A · 2 rec grande · 100% desplazado).

### Doble lectura de las 11 SECCIONES con el pin real (front vivo en producción df61d1f)
zona-analisis ✓ · resumen ✓ · mapa ✓ (título y Directos(5) = payload) · inventario ✓ ·
demanda ✓ (hogares = payload) · producto ✓ (sweet en pantalla = payload) · comercio ✓ ·
mezcla ✓ · mezclaRenta ✓ · monitor ✓ · **renta ✗ token `$null`** — ES el defecto del
simulador YA CORREGIDO el 18 jul (guardas m²/pm²/units/occ) que espera el commit de Héctor:
la auditoría lo reproduce en vivo y quedará verde con ese push. Spot-checks numéricos
payload↔pantalla: 9/9 ✓.

## Plan por sección (siguientes sesiones de auditoría)
Orden del tablero: Zona de Análisis → Resumen → Mapa → Inventario → Demanda → Producto →
Renta → Comercio → Mezclas → Monitor. En cada una: (a) backfill de catálogo de SUS
variables (A·295 repartidas), (b) triage de sus claves C, (c) linaje campo→capa→regla→
pantalla, (d) invariantes nuevas a verify_reglas/unit, (e) doble lectura profunda (no solo
tokens: sentido de negocio de cada número mostrado), (f) hallazgos → COLA_DECISIONES.
Registro de cada sesión: aquí + LISTA_REVISION.

## SECCIÓN 1 · ZONA DE ANÁLISIS — AUDITADA (19 jul 2026)
- EN VIVO (producción b6a2927): corrección 1 verificada end-to-end — 3 pines seguidos → 3
  domicilios DISTINTOS del backend (arcgis: La Banda / Sarabia / La Aurora GDL); payload
  regenerado (Contry): fecha_corte_venta=2026-02-09 y renta=2023-12-28 leídas del dato ✓;
  renta_baseline.units=160 con fuente "mediana observada de unidades/proyecto" ✓; ledger
  buckets_desglose presente en todos los perfiles y CONSERVACIÓN DE MASA POR BUCKET EXACTA
  en los 8 buckets ✓ (auditoría que el ledger de la decisión 3 habilitó).
- LINAJE: variables de ZA documentadas en CATALOGO (backfill de ~45 términos históricos,
  campo→regla). Invariantes de ZA ya cubiertas por verify_reglas/unit (banda, clip, sets,
  soporte de muestra); sin invariantes nuevas necesarias en este bloque.
- HALLAZGOS: sin defectos nuevos en ZA tras la corrección 1. Claves C de ZA (sin consumidor
  front): mayormente internas del análisis (agebs_geo total, caches) — legítimas API-only.
- Siguiente bloque: Resumen + Mapa. Revisada dos veces.

## SECCIONES 2-3 · RESUMEN + MAPA — AUDITADAS (19 jul 2026)
- RESUMEN (payload vivo Contry): fecha de corte visible (Oferta al 2026-02-09 · Renta al
  2023-12-28) ✓; KPIs = payload ✓; producto estrella en pantalla = top_estrella ✓; glosario ✓;
  cero tokens rotos ✓; y VERIFICACIÓN DE MÉTODO: el $/m² mostrado es la MEDIANA ROBUSTA del
  DISPONIBLE con núcleo P25-P75 (oferta_stats), NO el promedio — RES-2/RES-3 cumplidas
  (sonda inicial marcó falso por el formato "k"; falso positivo del harness). HALLAZGO menor:
  kpis.avg_* (promedios legacy) viven en payload sin uso en pantalla → triage lote #8.
- MAPA (payload vivo): título/conteos = payload ✓; primarios oculto en 0 ✓; capa PV
  etiquetada (<P25/>P75) ✓; leyenda con la regla vigente ✓; cero tokens ✓. (El ciclo de vida
  ya quedó auditado y corregido el 18-19 jul.)
- Sin correcciones necesarias en este bloque. Backfill de catálogo hecho. Siguiente:
  Inventario. Revisada dos veces.

## SECCIÓN 4 · INVENTARIO — AUDITADA (19 jul 2026)
- Payload vivo Contry con _typologies poblado (flujo real): 196 tipologías · 16 proyectos;
  encabezado = payload ✓; filas por proyecto ✓; campos de tipología COMPLETOS (incl. cajones
  y avance — INV-7 parcial ya servido por la capa) ✓; cero tokens ✓; único "próximamente" =
  plusvalías por periodo (P3, permitido) ✓; CSV y Fichas PDF presentes (INV-3 validado 6 jul).
- Corredor a la medida (INV-4): endpoint vivo con validación correcta (422 ante parámetro
  faltante de mi sonda — artefacto del harness, no defecto; el front envía analisis_key).
- Artefacto de harness declarado: "0 tipologías" inicial = globals por zona sin poblar en la
  inyección (el flujo real los puebla). Sin correcciones. INV-5/6 siguen gated por wrapper
  (declarados como permitidos). Siguiente: Demanda. Revisada dos veces.

## SECCIÓN 5 · DEMANDA (DIM + DEM-1) — AUDITADA (19 jul 2026)
- Pantalla vs payload (Contry vivo): 8 buckets DIM con PERFIL real por segmento (B1-B3 ✓,
  p.ej. "1 Rec · $1.5M-$2.5M · DINK accesible · Joven…"), 23 perfiles DEM-1 renderizados con
  sus 3 estatus (desatendido/equilibrado/sobreofertado), nuevas familias en pantalla =
  payload ✓, conservación meta ok:true ✓ y LEDGER re-verificado EXACTO por bucket ✓; cero
  tokens rotos ✓ (sin N/D porque la zona no los necesita — honesto).
- Artefactos de sonda declarados (no defectos): "< $1.5M" se muestra HTML-escapado (&lt;) y
  di_detail alimenta GRÁFICAS canvas (no texto), fuera del alcance del probe textual.
- PTI ya recomputado independiente 49/49 (18 jul, ancla ZMM). P1 flotante sigue en tintero.
  Sin correcciones. Siguiente: Producto (con implementación del VETO · decisión 6).
  Revisada dos veces.

## SECCIÓN 6 · PRODUCTO — AUDITADA + VETO IMPLEMENTADO (19 jul 2026)
- VETO DE PERCEPCIÓN (decisión 6: "la percepción veta") implementado en BACKEND, dentro de
  assemble_zone_payload justo después de percepcion_detalle (cubre las 2 rutas de endpoint):
  producto con pm2_num DEBAJO del piso (P10 = percepcion_detalle.limite_inferior) →
  recomendado=False, featured=False (invariante estrella ⊆ recomendado), veto_percepcion=True,
  motivo "debajo del piso de percepción del predio (P10 $X/m²)" que se ACUMULA al de
  absorción con " · ". No toca aplicable/status/absorción; el producto SIGUE mostrándose.
  Sin P10 observado o sin pm2 numérico → sin veto (no se inventa). Downstream ya ve el
  estado post-veto: sensibilidad_baseline, demanda_segmentos, mezcla del front (filtra
  recomendado). valor_zona nivel 4 usa prod_ref pre-assemble, pero ese nivel solo existe
  SIN comparables (sin P10) → sin conflicto posible con el veto (verificado en código).
- Front: SOLO pinta — caja roja "⛔ No recomendable: <motivo>" en la tarjeta cuando
  veto_percepcion. Cero cálculo nuevo en front.
- Validación offline 6/6 con los números REALES del ejercicio (piso 61,690 vs pm2 45,455 →
  vetado; pm2 EXACTO en el piso → NO veta, "debajo" estricto; sin piso → sin veto; motivo
  combinado con sobreofertado ✓). Batería: py_compile ✓ · node --check ✓ · verify_reglas
  23/23 (3 invariantes estáticos nuevos) + 2 de payload (pre-veto DETECTA "2 recomendados
  bajo piso", post-veto OK — probado con la estructura real del payload vivo).
- DOUBLE-READ page-producto vs payload vivo (Contry): 8 productos, 6 recomendados, 1
  featured = 1 etiqueta ★ en pantalla ✓; TODOS los campos (m2/pm2/ticket/mercado/seg_dim)
  de los 8 aparecen literales en el HTML (miss=0) ✓; cero tokens rotos ✓; supply-only
  poblado por el flujo real y rotulado "Promedio observado" ✓; sensibilidad_baseline
  presente {92 m² · $92,391 · 7.7 · $8.5M} ✓.
- ANCLA PRE-VETO para verificar tras tu push: el payload Contry vivo trae piso 71,222.89 y
  DOS recomendados bajo piso (pm2 18,400 y 33,333) → tras el push deben quedar vetados
  (n_rec 6→4 en Contry) y el caso del ejercicio (pin 25.65816,-100.44901: 45,455 < 61,690)
  debe salir con caja roja. Nota técnica: stats_robustas viaja VACÍO en el payload; la
  fuente del piso en payload es percepcion_detalle.limite_inferior (invariante ajustado a
  esa ruta, verificado en vivo).
- HALLAZGOS (a COLA_DECISIONES, sin tocar): (a) supply-only se CALCULA en el front
  (promedios ponderados sobre TYPOLOGIES) — el promedio es deliberado (foil del "método
  tradicional", rotulado) y no viola RES-2 (que rige TUS estadísticas), pero el cálculo
  debería vivir en backend (#9); (b) DESIGN_TIERS/getProductDesignTier con contenido
  editorial FIJO en el front (perfiles de edad, ingresos, acabados) que NO proviene de la
  base y se muestra en el detalle de producto (#10).
- Estado: IMPLEMENTADA pendiente de push+verificación en producción. Revisada dos veces.

## SECCIÓN 7 · RENTA + COMERCIO — AUDITADAS (19 jul 2026)
- RENTA (pantalla viva vs payload Contry): 7 segmentos con 1 sweet ★, TODOS en pantalla
  (el "< $1.5M" vive como "&lt;" — artefacto de sonda ya conocido, no defecto); KPIs
  hog_renta 8,845 ✓ · alquilada 17.2% ✓ · demanda 2 rec 47.2% ✓; renta_baseline conforme a
  las REGLAS FINALES: m2=50 (mediana), pm2=null → slider DESHABILITADO con N/D, units=160
  con units_fuente="mediana observada de unidades/proyecto de la zona", occ=null (N/D
  SIEMPRE, §10) → slider deshabilitado (verificado por PROPIEDAD el.disabled=true, no por
  serialización); ingresos proyectados del simulador en N/D (dependen de occ — honesto);
  cero tokens rotos. productos_renta (7, 3 recomendados) se pintan en Mezcla Renta →
  bloque 7.
- COMERCIO (pantalla viva vs payload): double-read completo ✓ — GLA objetivo 10,465 =
  Σ product_mix EXACTO; pct Σ=100.0; captable = 15% de oportunidad EXACTO por categoría
  (la etiqueta "@ 15%" del front ES la constante del backend — congruente); ingreso anual
  $3.5B ✓; renta low $0.7M ✓; NSE dominante en subtítulo ✓; 7/7 giros y 7/7 rentas en
  pantalla ("F&B" vive como "F&amp;B" — artefacto de sonda); ancla ⚓ = Supermercado ✓;
  cero tokens. renta_high (0.94) se produce y NO se muestra → C-key al triage #8.
- Semilla del front verificada: ZONE_DATA arranca con PLACEHOLDER de nulls (sin números
  inventados embebidos) y el backend inyecta lo real. Conforme.
- NSE efectivo del comercio = max(demográfico, percepción de valor) — congruente con el
  principio dictado "la percepción manda sobre la demografía". Conforme.
- HALLAZGO #11 (a COLA, sin tocar): las constantes del método comercio NO están
  ratificadas en §10 — CAPTURA 25% del gasto de la zona, tabla ventas_m2_anual (10 valores
  "típicos de industria" tecleados: Supermercado 95k … MV 35k), CAPTABLE_PCT 15%,
  OCC_RENTA 10% (renta ≈ % de ventas), GLA_MIN_VIABLE 100 m², banda de renta ±12%, factor
  0.85 de renta_low, +35% de renta_high, ancla fija Supermercado, y el catálogo
  TENANTS_POR_NSE (marcas sugeridas por nivel — vive en backend, lugar correcto, pero su
  contenido no proviene de la base). El gasto por categoría SÍ es de la base (C193-201).
  Pendiente: tu ratificación una-por-una (mismo tratamiento que el 18 jul).
- Sin cambios de código en este bloque (solo docs). Revisada dos veces.

## SECCIÓN 8 · MEZCLAS (VENTA + RENTA) + MONITOR — AUDITADAS (19 jul 2026)
- MEZCLA VENTA (viva, Contry): pool = productos recomendados EXACTO (6/6; con el veto
  vigente pasará a 4 post-push — el filtro `recomendado` lo absorbe sin tocar nada);
  EN VIVO la absorción base de cada producto = LA DEL BACKEND (verificado 6/6, diferencia
  <0.01; el slider de captación solo modula el escenario — "backend manda" cumplido);
  supply-only FUERA del pool demand-driven (0/6) y solo en modo manual; captación default
  100% visible; cero tokens en 64,425 chars de DOM.
- MEZCLA RENTA (viva): pool 3/3 = recomendados; `_occ` null 3/3 y `_renta_anual_ud` null
  3/3 — la regla "ocupación N/D SIEMPRE" fluye hasta la mezcla sin que nadie re-invente el
  90; captación renta default 50%; cero tokens.
- MONITOR (vivo): mix arranca VACÍO (0 filas — nada inventado al abrir), horizonte 24m
  (rango visible 6-60); los criterios en pantalla (±15% precio · ±30% tamaño · ±1 rec ·
  unid_disp>0) SON las constantes del backend (_MON_TOL_* = alias de _PRECIO_TOL_*, fuente
  única — congruencia pantalla↔cálculo verificada); la amenaza y el precio recomendado
  (MEDIANA de directos + PRECIO_TOL_VEREDICTO) se calculan 100% EN BACKEND vía
  evaluar_mix con debounce — el front solo envía y pinta. ARQUITECTURA MODELO para
  refactors #9/#12. Cero tokens.
- HALLAZGOS (a COLA, sin tocar): #12 el modo Recomendación (venta Y renta) filtra por
  PROMEDIOS de zona calculados en front (avgAbs 0.57 · avgPm2 $83,335 vivos; en pantalla
  rotulados "Promedio zona" — honesto, pero RES-2 pide medianas y el cálculo debería ser
  backend). #13 constantes del Monitor sin ratificar en §10 (tolerancias ±15/±30/±1 —
  fuente única y declaradas en pantalla —, escalera 2.0/1.0/0.5, fallback 60 m²,
  PRECIO_TOL_VEREDICTO). Defaults de UI visibles y editables (captura 100%/50%, 24m, 120
  unidades, fila nueva del Monitor) documentados en catálogo — no son constantes ocultas.
- Sin cambios de código en este bloque. Revisada dos veces.

## CIERRE DE AUDITORÍA · 8/8 SECCIONES (19 jul 2026)
ZA · Resumen+Mapa · Inventario · Demanda · Producto(+VETO) · Renta · Comercio ·
Mezclas+Monitor — todas auditadas contra pantalla viva y payload real. Correcciones de
código de la auditoría: domicilio del pin (siempre-reemplaza), ciclo de vida del mapa,
VETO de percepción (decisión 6, pendiente de push+verificación). Hallazgos en cola:
#7-#13 + G1-G10. Batería final: verify_reglas 23/23 estáticos ✓.

## VERIFICACIÓN POST-PUSH DEL VETO — EN PRODUCCIÓN ✓ (19 jul 2026, tras push de Héctor)
- Deploy de Render confirmado (front nuevo servido). Dos análisis FRESCOS vía producción:
- PIN EJERCICIO (25.65816,-100.44901 · 3,000 m² vertical): piso vivo 61,689.76 → motivo
  "P10 $61,690/m²" (ancla exacta). VETADOS 3: 1 Rec@18,400 · 1 Rec@33,333 · y EL CASO DEL
  EJERCICIO "2 Rec · $2.5M-$3.5M"@45,455 ✓. n_rec=4, 3 cajas rojas renderizadas con el
  front nuevo, featured sin vetar, invariantes de payload OK.
- CONTRY (25.66412,-100.28454 · 1,200 m²): piso vivo 71,222.89 → "P10 $71,223/m²" (ancla
  exacta). VETADOS exactamente los 2 predichos: @18,400 y @33,333 ✓. n_rec 6→4 (ancla
  exacta), 2 cajas rojas, invariantes OK.
- Estado de la decisión 6: IMPLEMENTADA → VERIFICADA EN PRODUCCIÓN. Revisada dos veces.
