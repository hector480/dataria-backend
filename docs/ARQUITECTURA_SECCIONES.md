# Arquitectura modular de Dataria · cómo agregar una sección

Este documento explica cómo está organizado el backend por secciones y cómo
agregar una sección nueva (p. ej. Vivienda Horizontal, Lotes Urbanizados,
Explorador Nacional) sin tocar las demás.

## 1. Principio

Cada sección del tablero es un módulo lógico independiente:
- Una **función derivadora** `derive_<seccion>(...)` que recibe los insumos crudos
  (agebs de DescargaDI, ft de VVV, segments DPO, etc.) y devuelve su bloque de datos.
- Una **entrada en `SECTION_REGISTRY`** (en `app.py`) con su metadato:
  `key`, `label`, `page_id`, `access_tier` (`preliminar` | `detalle`), `payload_keys`.
- El **orquestador** (`zona_procesar`) ensambla solo las secciones activas.
- El **control de acceso** (`filter_payload_by_access`) usa `access_tier` y `payload_keys`
  para mostrar/ocultar cada sección según los permisos de la cuenta.

Esto permite optimizar, cambiar, agregar o eliminar una sección editando únicamente
su `derive_<seccion>` y su entrada en el registro.

## 2. Pasos para agregar una sección nueva

### Backend (`app.py`)
1. Escribir `derive_<seccion>(agebs, ft, ...)` que devuelva un dict/lista con los datos
   de la sección. Respetar la regla de integridad: ausencia → `None` (nunca 0/inventado).
2. Registrarla en `SECTION_REGISTRY`:
   ```python
   "vivienda_horizontal": {
       "label": "Vivienda horizontal", "page_id": "page-vivienda-horizontal",
       "access_tier": "detalle", "payload_keys": ["vivienda_horizontal"]
   },
   ```
   (quitar `"scaffold": True` cuando ya esté implementada)
3. Llamarla en `zona_procesar` con `_safe(...)` y añadir su resultado al payload
   (`assemble_zone_payload` o directamente en `zone_data`).

### Front (`dashboard_zona_analisis.html`)
1. Añadir el `<div class="page" id="page-vivienda-horizontal"></div>`.
2. Escribir `tplViviendaHorizontal(z)` que renderice el bloque desde `z.vivienda_horizontal`.
3. Registrar el par `['page-vivienda-horizontal', tplViviendaHorizontal]` en `zaRenderAllSafe`.
4. Añadir el ítem al menú de navegación.

### Verificación
- Añadir el `page_id` a la lista de `ids` en `verify_all.py` (harness de render) y
  correr `python3 verify_all.py` → debe seguir en 10/10 + formato OK.

## 3. Control de acceso (modelo de operación)

- `access_tier: "preliminar"` → la sección se ve en evaluación general (cualquier zona).
- `access_tier: "detalle"` → la sección solo se ve si la cuenta tiene la zona autorizada.
- Las cuentas se crean vía `POST /api/cuentas` con `secciones` (qué secciones ve) y
  `zonas_detalle` (en qué zonas ve el detalle). `*` = todas.
- `POST /api/zona/procesar_auth` con `usuario` aplica el filtro automáticamente.

### Ejemplo · Explorador Nacional
El Explorador Nacional se registra con `access_tier: "preliminar"`, de modo que
cualquier cuenta puede hacer evaluaciones preliminares de cualquier zona, pero el
detalle completo (producto, demanda, renta, comercio) sigue restringido a las zonas
autorizadas de cada cuenta. Esto cumple el modelo: acceso general disponible, acceso
detallado restringido.

## 4. Escenarios guardados

Las secciones de mezcla (venta, renta) y monitor pueden guardar escenarios con
`guardarEscenario('<seccion>')`, que persiste el estado en `window.storage` bajo
`escenario:<seccion>:<zona>:<nombre>`. Una sección nueva que necesite guardar estado
puede reutilizar `guardarEscenario`/`listarEscenarios`/`cargarEscenario` añadiendo su
estado al switch de esas funciones.

---

## ANEXO (corte 4 jul 2026) · Mapa de funciones clave y flujo actual

### Flujo de un análisis
pin (lat,lng) → `POST /api/zona/poligono` (isócronas Predik) → `POST /api/zona/procesar`:
fetch VVV venta/renta + DescargaDI (XLSX `parse_di_xlsx` → agebs; KMZ `parse_di_geometria` →
`agebs_geo` con nse_txt/nse_rank + centroide por AGEB) → `value_perception_adjust` (clustering
de mercados `detect_markets` + `_build_feature_vectors`; recorte de zona al mercado del pin)
→ derivadores → payload → front (`zaApplyBackendPerception` pinta; templates leen `z` y `z._vars`).

### Derivadores y utilidades por sección (backend, `app.py`)
- Demografía: `derive_demografia(agebs, ft, agebs_geo, pin_lng, pin_lat)`;
  `_nse_percepcion_valor(ft)`; `_nse_dominante_agebs(agebs, agebs_geo, pin_lng, pin_lat)`;
  `_factor_proximidad_por_nse`; `_build_di_detail` (tipologia_hogar, personas_hogar).
- Demanda: `derive_segments(agebs, ft, tipo_vivienda, agebs_geo, pin_lng, pin_lat)` — buckets
  con `tca` (de `NSE_TCA`), demanda, evidencia, status/origen.
- Producto: `derive_productos_venta(ft, segments, unidades, personas_hogar, di_detail)` →
  productos con `variantes` (`_variantes_multiprograma` → `_demanda_recamaras_bucket` +
  `_pesos_tipologia_hogar`), `abs_*` (`_absorcion_producto`, regla absorcion_oferta_directa),
  `pm2_recomendado` (`_precio_recomendado_directos`). Horizontal: `derive_productos_horizontal`.
- Monitor: `amenaza_competitiva(item, period, capture, typologies, segments)` →
  `_competidores_mix_item`, `_segmento_para_ticket`, `_precio_recomendado_mix_item`;
  endpoint `POST /api/zona/evaluar_mix` (item único o items[]).
- Comercio: `derive_comercio(agebs, nse_dominante_ponderado, ft)`.
- Oferta/typologies: `_build_typologies(ft, nombres_universo)` → `zone_data._typologies`
  (misma estructura vertical y horizontal — base de la consistencia del Monitor).
- Variables nombradas: `build_analysis_vars(...)` → `zone_data._vars` (fuente única que TODAS
  las secciones del front consumen).

### Front (dashboard) · puntos que consumen backend
- `zaRenderAllSafe` (con guard de `page-zona-analisis` para no destruir el mapa Leaflet),
  `zaSetPin`, `zaApplyBackendPerception` (isócronas/zona/competidores).
- Monitor: `renderMonitorAnalysis` (async; bloque de precio automático por producto),
  `monitorFetchThreats` + `mapThreatFromBackend` (snake→camel), debounce 300 ms,
  `monitorPrecioVeredicto` (botón puntual, mismo backend).
- Demanda: `computeDemandSegments` lee `s.tca` (sin tablas locales).

### Constantes (una sola fuente; no duplicar)
`NSE_TCA` · `_PRECIO_TOL_TICKET=0.15` · `_PRECIO_TOL_AREA=0.30` · `_PRECIO_TOL_REC=1` ·
`PRECIO_TOL_VEREDICTO=0.05` · `PCT_POOL_ACTIVO=0.05` (los `_MON_TOL_*` duplican valores de
`_PRECIO_TOL_*`; pendiente menor de consolidación — cambiar siempre en pareja).
