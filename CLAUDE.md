# DATARIA · Instrucciones permanentes del proyecto

Este archivo es la fuente de verdad de reglas y contexto. Se lee COMPLETO al inicio de cada
sesión. Antes de cualquier trabajo mayor, leer también: `docs/ESTADO_DATARIA.md` (estado y
pendientes), `docs/ARQUITECTURA_SECCIONES.md` (arquitectura) y `docs/LISTA_REVISION.md` (backlog).

## Qué es Dataria
SaaS de inteligencia inmobiliaria para LatAm (competidor de Placer.ai) que productiza la
metodología DIGO®/DPO de Prosperia. Director General y único decisor de checkpoints: Héctor
González. Analiza zonas (pin en mapa → isócronas → demografía + oferta real) y recomienda
producto óptimo: segmentos de demanda, mix, precios, absorción, amenaza competitiva.

## Comunicación
- SIEMPRE en español, conciso, sin apodos.
- NO preguntar reglas ya definidas: buscar primero en este archivo, `docs/`, el código y el
  historial. Preguntar solo dudas genuinamente nuevas o de mayor profundidad.
- Checkpoints: confirmación explícita de Héctor antes de avanzar de fase o cambiar alcance.

## REGLAS NO NEGOCIABLES (violarlas = fallo crítico)
1. **Integridad de datos 100%**: dato ausente = `N/D`. NUNCA 0, null, promedios sustitutos ni
   valores inventados. Solo datos reales de la API PRSP/ArcGIS.
2. **Todo el cálculo en el BACKEND** (`app.py`). El tablero SOLO muestra: lee del payload y de
   `ANALYSIS_VARS` (`z._vars` / `getVars()`). Extender, nunca duplicar cálculo en el front.
   Cada cambio toca el backend Y el punto del front que lo consume.
3. **NO promediar/ponderar el NSE entre niveles**: la información es granular por segmento.
   (La ponderación por proximidad del NSE dominante NO promedia niveles: elige el dominante.)
4. **Causa raíz antes de corregir**: diagnosticar y ENUNCIAR la causa raíz; verificar con
   comprobaciones dirigidas (grep/tests), no con inspección visual.
5. **No eliminar ni arriesgar funcionalidad ya validada.** Ante duda, preservar y preguntar.
6. **Tras cada corrección**: volver a `docs/LISTA_REVISION.md`, anotarla y revisarla DOS veces
   antes de entregar. Nunca entregar incompleto ni "rápido".
7. **Segmentado por secciones** con nombres de variables consistentes entre secciones: lo que
   una sección produce y otra consume debe llamarse igual en todo el flujo.
8. **Validar siempre** contra las zonas ancla (ZMM Centro y Valle Poniente); confirmar en
   Jalisco cuando el cambio afecte lógica universal.

## REGLAS DE NEGOCIO CONFIRMADAS (no re-preguntar; citar al aplicar)

### Zona de influencia y percepción de valor
- La **ISÓCRONA define la ZONA** (alcance físico: quién llega). La **PERCEPCIÓN DE VALOR define
  el VALOR del producto**: NSE del precio mediano de la oferta vertical real (VVV). La
  percepción PREDOMINA sobre el NSE demográfico crudo y puede SUBIR con evidencia de oferta
  superior. Implementada en `_nse_percepcion_valor(ft)`; aplicada en `derive_demografia` y
  `derive_segments`.
- **NSE dominante** = mayor masa de hogares en la isócrona = "el más accesible desde el predio".
- **Ponderación por proximidad (capacidad de pago demográfica)**: la masa se COMBINA con la
  cercanía real al pin: `masa_pond[nse] = masa[nse] × factor_proximidad[nse]`, con factor =
  promedio de `1/(1+dist_km)` de las AGEB georreferenciadas de ese NSE (de `parse_di_geometria`,
  KMZ del DI). Sin geometría o sin pin → masa simple (integridad: no inventar posiciones).
  Implementada en `_factor_proximidad_por_nse` + `_nse_dominante_agebs`; usada por demografía,
  segmentos y comercio. Solo cambia el VALOR del dominante; no altera ninguna otra regla.
- **Inducción de demanda hacia arriba permitida**: se puede recomendar precio mayor al del NSE
  dominante, con TECHO = piso del NSE inmediatamente superior PRESENTE en la zona (el comprador
  sacrifica entorno por mejor precio en producto nuclear casi equivalente).
- Todo se calcula **por zona**, nunca con promedios de ciudad/municipio/estado/país.

### TCA (fuente única)
`NSE_TCA = {"A":1.12, "B":1.0, "C+":1.39, "C":1.03, "D+":0.74, "D":0.37, "E":0}` — constante
global ÚNICA en `app.py`. La usan `derive_nse_dim`, `derive_segments` y productos. El front lee
`s.tca` del payload. PROHIBIDO duplicar tablas de TCA en cualquier parte.

### Multi-programa por bucket de precio
A mismo ticket: menos m² = más recámaras chicas; más m² = menos recámaras amplias.
- Mínimos por recámara: lujo (NSE A/B) 13 m²; económico (C y abajo) 9 m².
- % del área total ocupada por recámaras: lujo 50%; económico 60%.
- Validación física: `n_rec × m²_min ≤ %_recámaras × área_total`; si no cabe, topar `n_rec`.
- Generar SOLO variantes con demanda real = oferta vendida en el bucket
  (`CANTIDAD_DE_RECAMARAS` de ft con ventas) + hogares del DI (composición).
Funciones: `_variantes_multiprograma`, `_demanda_recamaras_bucket`, `_min_m2_recamara`,
`_pct_area_recamaras`, `_recamaras_que_caben`. El producto lleva campo `variantes`.

### Regla de recámara compartida
Salvo hogares UNIPERSONALES y de CORRESIDENTES, 2 adultos (papá y mamá) comparten la recámara
principal → hogares FAMILIARES: recámaras = personas − 1; unipersonal = 1; corresidentes = una
por residente. Usa `di_detail.tipologia_hogar` y `personas_hogar` (en ZMM: 87% familiares).
Implementada en `_demanda_recamaras_bucket` + `_pesos_tipologia_hogar`.

### Absorción
- Regla base con demanda DIM; **si demanda DIM = 0 pero hay competidores DIRECTOS vendiendo**:
  absorción = mediana de absorción de directos × n (origen `absorcion_oferta_directa`, cuenta
  como recomendable). Sobreofertado con directos → también mediana×n. Sin directos → `N/D`
  legítimo o 0 explícito. Función: `_absorcion_producto`.

### Precio recomendado (Producto y Monitor · consistente vertical/horizontal)
- Regla: **mediana de $/m² de los competidores DIRECTOS reales** — inventario disponible > 0,
  ticket ±15% (`_PRECIO_TOL_TICKET=0.15`), área ±30% (`_PRECIO_TOL_AREA=0.30`), recámaras ±1
  (`_PRECIO_TOL_REC=1`). Ticket recomendado = pm²_rec × m².
- Veredicto vs precio del usuario con `PRECIO_TOL_VEREDICTO=0.05` (±5%): caro / en_linea / barato.
- Producto: `_precio_recomendado_directos` (sobre ft). Monitor: `_precio_recomendado_mix_item`
  (sobre `_typologies`), integrada en `amenaza_competitiva` → endpoint `/api/zona/evaluar_mix`.
- La consistencia vertical/horizontal está garantizada porque `_typologies` se construye con el
  ft del MODO ACTIVO (`_build_typologies`). En el Monitor el bloque de precio se muestra
  AUTOMÁTICAMENTE por producto (sin directos → nota N/D legítima). Sin match aproximado en front.
- Sin competencia directa comparable → `N/D` (el producto define el precio). Nunca inventar.

### Otras constantes/lecturas clave
- `PCT_POOL_ACTIVO=0.05` (mercado activo). `ageb_nse(r)` lee 'NSE PER' o
  'XI_Nivel socioeconómico por ingreso'. Columnas DI: "Hogares totales 2026", "Mercado en
  venta", "Demanda anual vivienda", "Rangos demanda vivienda".
- Tolerancias `_MON_TOL_*` duplican `_PRECIO_TOL_*` con los mismos valores (pendiente menor de
  consolidación; NO cambiar valores de una sin la otra).

## ARQUITECTURA (resumen · detalle en docs/ARQUITECTURA_SECCIONES.md)
- **Backend**: `app.py` (FastAPI, ~4,800 líneas). Único archivo. Deploy: repo GitHub
  `hector480/dataria-backend` → Render (redeploy automático al push).
  Flujo: `POST /api/zona/poligono` (isócronas) → `POST /api/zona/procesar` (payload completo)
  → `POST /api/zona/evaluar_mix` (Monitor, item o lote). Tablero servido en `/tablero`.
- **Front**: `static/dashboard_zona_analisis.html` (~7,600 líneas; Leaflet + Chart.js). SOLO
  renderiza. Funciones críticas del mapa: guard anti re-inyección de `page-zona-analisis` en
  `zaRenderAllSafe` (preserva el mapa Leaflet montado), `zaSetPin`, `zaApplyBackendPerception`
  (pinta isócronas + zona + competidores).
- **Datos (API PRSP)**: `https://payment-system-prsp.onrender.com` — Predik isócronas, VVV
  (vv_venta|vv_renta), DescargaDI (XLSX demografía + KMZ geometría NSE por AGEB). A veces
  devuelve vacío transitorio (sleep de Render) → SIEMPRE reintentar en loop (hasta 5 veces)
  hasta que `dim_data.segments` no esté vacío.
- **Secciones**: `SECTION_REGISTRY` (access_tier preliminar|detalle). Modo activo:
  vivienda_vertical y vivienda_horizontal. Andamiaje pendiente: lotes_urbanizados, industrial,
  explorador_nacional.

## WORKFLOW DE VALIDACIÓN OBLIGATORIO (tras CADA cambio)
1. `python3 -m py_compile app.py` (compila).
2. Extraer el script del HTML (regex `<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>`) → `node --check`.
3. Regenerar payloads frescos de ZMM Centro y Valle Poniente llamando `zona_poligono` +
   `zona_procesar` con asyncio y REINTENTOS (ver pins abajo).
4. Render de las 9 secciones limpio en ambas zonas (harness Node con mocks de DOM/Chart.js; los
   errores `toFixed/toLocaleString` en STDERR del mock de Chart.js son artefactos del harness,
   NO del código).
5. `verificacion/verify_all.py` → 8/8 y render 10/10 con formato OK.
5b. `verificacion/verify_reglas.py` → OK 100% (invariantes de negocio: NUNCA romperse al cambiar proveedor o agregar información).
6. `verificacion/verify_interactive.py` → 16/16 checks OK (usa zona Monterrey Contry EN VIVO).
7. Revisar `docs/LISTA_REVISION.md` DOS veces; anotar el cambio con causa raíz y validación.
8. **Ahora con acceso local**: validar también contra Render tras el push
   (`https://dataria-orchestrator.onrender.com/tablero` y endpoints) — antes no era posible.
Los verificadores esperan por defecto `app.py` en la raíz del repo y
`static/dashboard_zona_analisis.html` (rutas configurables en su encabezado).

## PINS DE PRUEBA (zonas de referencia)
- **ZMM Centro** (ancla NSE C/C+ → dominante B por percepción): lat 25.6866, lng -100.3161,
  colonia Centro, Monterrey, NL. ~40 proyectos, ~$74k/m², 8 productos, 3.07 pers/hogar.
- **Valle Poniente** (ancla premium, dominante A): lat 25.6500, lng -100.4100, San Pedro Garza
  García, NL. 26 proyectos, ~$103k/m², 9 productos, 3.51 pers/hogar.
- **Monterrey Contry** (zona de verify_interactive): 25.66412, -100.28454.
- **GDL Centro** 20.6597, -103.3496 · **Zapopan** 20.7214, -103.3918 (horizontal CON oferta:
  úsala para probar horizontal) · **Escobedo** 25.83721, -100.35195 (horizontal SIN oferta
  vertical → typologies=0, N/D legítimo).
- Snippet de regeneración (adaptar pin/producto):
  `req=ZonaRequest(lat=…, lng=…, predio_m2=1500, zone_name=…, colonia=…, municipio=…,
  estado=…, pais='México', producto='vivienda_vertical'); await zona_poligono(req);
  d=await zona_procesar(req)` — reintentar si `d['dim_data']['segments']` vacío.

## PENDIENTES PRIORITARIOS (detalle en docs/ESTADO_DATARIA.md y docs/LISTA_REVISION.md)
1. **Seguridad del API antes de cualquier lanzamiento público**: sin autenticación, CORS
   abierto, `_CUENTAS` en memoria sin contraseñas ni persistencia; `/api/zona/evaluar_mix`
   sin auth. (Sugerencia: investigar OWASP API Security Top 10 y proponer plan.)
2. **Capa NSE/IXH como barrera de mercado**: `nse_rank` llega `None` con peso 0.0 en
   `_build_feature_vectors` (`SIGNAL_WEIGHTS["nse"]=0.0`); integrar la señal ahora que existe
   `agebs_geo` (sin alterar reglas: solo activar la señal con validación en zonas ancla).
3. **Arranque del tablero**: verificar en producción que el arranque con
   `switchZone('ZONE_KEY_PLACEHOLDER')` no deja pantalla en blanco (diagnóstico histórico en
   LISTA_REVISION; el fix del mapa por re-inyección de `zaRenderAllSafe` es OTRO fix y está
   cerrado y validado).
4. Backend debe entregar amenidades y bandas de inventario procesadas (el front tiene lectores
   puros `getProjectAmenityScore`/`computeInventoryBands` esperando datos).
5. Programa arquitectónico gaussiano completo (recámaras/tamaño por edad + ocupantes;
   `di_detail` ya trae tipologia_hogar y personas_hogar).
6. Secciones de andamiaje: lotes_urbanizados, industrial, explorador_nacional.
7. Integración ArcGIS directa: `config/arcgis_mapping.yaml` (194 campos pre-poblados) +
   `arcgis_discovery.py`; faltan `service_url`, `layer_id`/`table_id` y token.
8. Consolidación front+backend en un solo servicio Render; persistencia real de cuentas (DB).
9. Menor: consolidar `_PRECIO_TOL_*` y `_MON_TOL_*` (valores idénticos duplicados).

## QUÉ SUBIR AL PUBLICAR
`app.py` (raíz del repo) + `static/dashboard_zona_analisis.html`. Render redepliega solo.
`docs/` acompaña versionado. Footer vigente del tablero: "Elaborado: Dataria Team · San Pedro
Garza García, Nuevo León y Guadalajara, Jalisco · Hecho en México".
