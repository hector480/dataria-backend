# ESTADO DATARIA — Documento de traspaso a Cowork
**Fecha de corte: 4 de julio de 2026.** Todo lo listado como HECHO está validado con la batería
completa (verify_all 8/8 + render 10/10, verify_interactive 16/16, render 9/9 secciones limpio
en ZMM Centro y Valle Poniente, compilación backend y sintaxis front).

---

## CÓMO RETOMAR (primera sesión en Cowork)
1. Este repo ya contiene todo: `CLAUDE.md` (reglas permanentes — se lee automático),
   `app.py`, `static/dashboard_zona_analisis.html`, `docs/` y `verificacion/`.
2. Pegar el prompt de arranque (`PROMPT_ARRANQUE.txt` del paquete de traspaso).
3. Claude debe: leer CLAUDE.md + docs/, confirmar reglas, resumir estado, correr validación
   base (compilar backend + node --check del front) y ESPERAR instrucciones.
4. Ventaja nueva del entorno local: se puede validar producción directamente
   (`https://dataria-orchestrator.onrender.com/tablero`), cosa imposible en el entorno anterior.

---

## COMPLETADO Y VALIDADO (acumulado, más reciente primero)

### Ponderación por proximidad del NSE dominante (capacidad de pago demográfica)
- Regla: el dominante es "el más accesible"; la accesibilidad se cuantifica con distancia real
  al pin. Decisión confirmada: COMBINAR masa de hogares × factor de proximidad.
- `_factor_proximidad_por_nse(agebs_geo, pin_lng, pin_lat)`: por NSE, promedio de 1/(1+dist_km)
  de sus AGEB (centroides del KMZ vía `parse_di_geometria`). Sin geometría/pin → {} (masa simple).
- Aplicada en `_nse_dominante_agebs`, `derive_demografia` (nse_dom_key), `derive_segments` y
  `derive_comercio`, en los endpoints `analyze` y `zona_procesar` (pasan agebs_geo + req.lng/lat).
- Validación decisiva: caso con masa C lejana y A pegada al pin → sin proximidad domina C, con
  proximidad domina A (factores A=0.87, C=0.109). ZMM sigue dominante B y VP dominante A
  (la percepción de valor sigue predominando). `share_dom` se reporta sobre masa real.

### Precio recomendado del Monitor · automático y consistente vertical/horizontal
- Backend: `_precio_recomendado_mix_item(item, typologies)` (mediana $/m² de directos: disp>0,
  ticket ±15%, área ±30%, rec ±1) integrada en `amenaza_competitiva` → devuelve
  pm2_recomendado, ticket_recomendado_M, precio_n_directos, pm2_usuario, precio_tol_veredicto,
  veredicto_precio (±5%: caro/en_linea/barato). Endpoint `/api/zona/evaluar_mix`.
- Front: el bloque "Precio recomendado" se muestra AUTOMÁTICAMENTE en la tarjeta de cada
  producto del análisis del Monitor (tras la estrategia). Sin directos → nota N/D legítima.
  El botón "$ precio" por fila se conserva. Eliminado el match aproximado
  (`monitorBuscarPrecioBackend`) que fallaba con productos custom y en horizontal.
- Validado: vertical (ZMM) 2/2 productos con bloque y veredicto; horizontal (Zapopan, oferta
  real de casas $11–14M): casa $16M → CARO ($/m² rec $69,766); casa $9M → N/D correcto.

### Multi-programa por bucket + regla de recámara compartida
- Variantes por producto (`variantes`) según demanda real (oferta vendida + hogares DI),
  validación física de recámaras, mínimos 13/9 m², % área 50/60.
- Recámara compartida: familiares = personas−1; unipersonal = 1; corresidentes = 1 por
  residente. Con 3.07 pers/hogar (ZMM) → base familiar 2, variantes 1-2-3. ZMM 8/8 y VP 9/9
  productos con variantes.

### Migración total de cálculo front → backend
- TCA: `NSE_TCA` constante global única; eliminadas 3 tablas hardcodeadas (front y backend).
- Monitor: amenaza competitiva completa en backend (`amenaza_competitiva`,
  `_competidores_mix_item`, `_segmento_para_ticket`); front async con debounce
  (`MONITor_DEBOUNCE_MS=300`, `monitorFetchThreats`, `mapThreatFromBackend`).
- Percepción de valor: eliminadas 212 líneas de cálculo muerto del front; el flujo vivo usa
  `zaApplyBackendPerception` (lee todo del backend).

### Fixes por causa raíz (los 3 reportados de Render)
- **Mapa que desaparecía**: `zaRenderAllSafe` re-inyectaba el HTML de `page-zona-analisis` en
  cada `switchZone`, destruyendo el div del mapa Leaflet. Fix: guard que no re-inyecta si ya
  está montado. El ciclo de vida del mapa está testeado (sobrevive a procesar la zona).
- **Absorción N/D con directos vendiendo**: regla confirmada `absorcion_oferta_directa`
  (mediana de directos × n). ZMM pasó de 4 N/D a 0/8.
- **Productos faltantes**: cierre validado dentro del flujo de productos por bucket.

### Estética
- Footer: "Elaborado: Dataria Team · San Pedro Garza García, Nuevo León y Guadalajara,
  Jalisco · Hecho en México".

### Base previa (etapas anteriores, ya en producción)
- SECTION_REGISTRY modular (access_tier preliminar|detalle), guardar escenarios
  (window.storage), cuentas con acceso por sección/zona (`filter_payload_by_access`,
  `/api/zona/procesar_auth`), flujo dos etapas poligono→procesar, modo horizontal activo,
  comercio con NSE dinámico, formato México en todo el tablero.

---

## PENDIENTES (orden de prioridad)
1. **Seguridad del API** (bloqueante para lanzamiento público): auth, CORS, persistencia de
   cuentas, proteger `/api/zona/evaluar_mix`.
2. **Señal NSE en clustering de mercados**: `SIGNAL_WEIGHTS["nse"]=0.0` y `nse_rank=None` en
   `_build_feature_vectors`; activar con `agebs_geo` ya disponible, validando en zonas ancla.
3. **Arranque del tablero**: confirmar en producción que no queda pantalla en blanco al abrir
   (diagnóstico histórico del `switchZone('ZONE_KEY_PLACEHOLDER')` en LISTA_REVISION).
4. Amenidades y bandas de inventario procesadas por el backend.
5. Programa arquitectónico gaussiano (edades + ocupantes → programa).
6. Secciones: lotes_urbanizados, industrial, explorador_nacional.
7. ArcGIS directo (`config/arcgis_mapping.yaml` + `arcgis_discovery.py`; faltan service_url,
   layer_id/table_id, token).
8. Consolidar front+backend en un solo servicio Render; DB para cuentas.
9. Consolidar tolerancias duplicadas `_PRECIO_TOL_*` / `_MON_TOL_*`.

---

## REFERENCIAS TÉCNICAS RÁPIDAS
- Endpoints PRSP: Predik `/api/predik/isochrone`; VVV `/api/v1/vvv/query` (vv_venta|vv_renta);
  DescargaDI `/api/descargas/di/export` (activeMap NSE; ZIP con XLSX + KMZ).
- Payload: `zone_data` (name, subtitle, center, tca, nse, nse_dominante, proyectos, kpis,
  inventario_precio, productos [con `variantes`, `abs_origen`, `pm2_recomendado`…],
  productos_renta, comercio, `_vars`, `_typologies`, `_zona_analisis{isocronas, perception}`)
  + `dim_data` (nse_dim, segments [con `tca`], totals, di_detail{tipologia_hogar,
  personas_hogar…}) + stage/errors.
- Parámetros: PM2_VERTICAL_MIN=20000; banda física m² [25,500]; EVIDENCIA_MIN=3; techo de
  absorción 12/mes. Pisos de valor por NSE (M MXN): A 6.8 · B 3.05 · C+ 1.35 · C 0.577 ·
  D+ 0.349 · D 0.2 · E 0.
- Marca: Geist + JetBrains Mono; ink #0B1020/#1A2240, azure #0540F2/#0428B0, pulse #00B564,
  paper #F0F1F4, hair #C9CCD6; radio 6px. Basemap Esri World Imagery.
