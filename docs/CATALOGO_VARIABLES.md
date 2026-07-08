# CATÁLOGO UNIVERSAL DE VARIABLES · Dataria
**Regla de gobierno (Héctor, 6 jul 2026):** este catálogo es la fuente única de nombres.
1. Toda variable se usa con EL MISMO nombre en backend, payload y front, y entre secciones.
2. El catálogo SOLO CRECE: una sección/ajuste nuevo AGREGA variable nueva; NUNCA se cambia
   el significado o nombre de una variable que otra sección ya consume.
3. Variables específicas de un uso llevan el contexto del uso (p. ej. `m2_terreno` solo
   existe en horizontal); las comunes significan lo mismo en todos los usos.
4. Constantes de negocio: UNA sola definición en `app.py`; prohibido duplicar tablas.

Formato: **nombre** · qué es · fuente/fórmula · quién la consume.

---

## 1. Entrada (`ZonaRequest`)
| Variable | Qué es | Consumidor |
|---|---|---|
| `lat`, `lng` | Pin del predio | Todo el pipeline |
| `predio_m2` | Tamaño del terreno | `isochrone_profile` (perfil de isócrona) |
| `uso_comercial` | Flag comercial (isócrona 24 seg) | `isochrone_profile` |
| `producto` | Modo de uso (`vivienda_vertical`/`vivienda_horizontal`/…) | Ruteo de capa de oferta y función de producto |
| `zone_name`, `colonia`, `municipio`, `estado`, `pais` | Identidad capturada | `assemble_zone_payload` (name/subtitle) |
| `unidades_proyecto` | Unidades que construirá el proyecto | Tope del pronóstico 12/18/24 |

## 2. Constantes de negocio (fuente única en app.py)
| Constante | Valor | Regla |
|---|---|---|
| `NSE_TCA` | A 1.12 · B 1.0 · C+ 1.39 · C 1.03 · D+ 0.74 · D 0.37 · E 0 | TCA % anual de hogares por NSE. ÚNICA tabla. |
| `NSE_INCOME_BANDS` | bandas ingreso mensual AMAI | Capacidad de pago (auxiliar; el NSE lo da la base) |
| `NSE_VIV_PISO_M` (en derive_segments) | A 6.8 · B 3.05 · C+ 1.35 · C 0.577 · D+ 0.349 · D 0.2 · E 0 (M MXN) | Pisos de valor de vivienda por NSE (techo de inducción, percepción de valor) |
| `PM2_VERTICAL_MIN` | 20,000 | Piso de plausibilidad de $/m² vertical |
| `M2_MIN, M2_MAX` | 25, 500 | Banda física de m² de producto |
| `EVIDENCIA_MIN` | 3 | Unidades vendidas para validar un nivel |
| `PCT_POOL_ACTIVO` | 0.05 | Fracción de "Mercado en venta" que se anualiza |
| `_DIRECTO_TOL_*` | ticket ±15% · pm² ±15% · m² ±20% · rec exactas | Comparable directo de ABSORCIÓN |
| `_PRECIO_TOL_*` | ticket ±15% · área ±30% · rec ±1 (sin filtro pm²) | Comparable directo de PRECIO |
| `_MON_TOL_*` | duplican `_PRECIO_TOL_*` | Monitor (pendiente consolidar; cambiar en pareja) |
| `PRECIO_TOL_VEREDICTO` | 0.05 | Veredicto caro/en_línea/barato |
| `VENTAJA_DISENO` | 1.20 | (Histórica) diseñar para vender ≥20% más rápido |
| `RAMP_ARRANQUE/CONSOLIDA/COLA` | 0.60 / 0.70 / 0.20 | Curva de maduración m1-6 / m7-18 / m19-24 |
| `SIGNAL_WEIGHTS` | ticket .40 · pm² .30 · pos .30 · nse .00 | Señales del clustering de mercados |
| `CLUSTER_MASA_MIN`, `GAP_MIN`, `VAR_EXPLAINED_MIN`, `CV_GLOBAL_MIN`, `SEP_MEDIAS_MIN`, `SOLAPE_ESPACIAL_MAX` | 3 · 0.85 · 0.35 · 0.12 · 0.18 · 0.60 | Validación robusta de mercados |
| `MULTIPLO_HIPOTECARIO` | 4.5 | Capacidad de compra = ingreso mensual × 12 × 4.5 |

## 3. Campos de la base (ArcGIS vía PRSP) — nombres tal cual llegan
### 3.1 DescargaDI · XLSX por AGEB (di/export, activeMap=NSE)
`Población total 2026` · `Hogares totales 2026` (fallback `Hogares totales 2020`) ·
`Ingresos totales 2026` · `IXH` (ingreso por hogar MENSUAL) · `Personas por hogar 2026` ·
`Tasa de crecimiento anual` · `NSE PER` (NSE oficial del AGEB; respaldo
`XI_Nivel socioeconómico por ingreso`) · `V CASAS` (valor de vivienda) ·
`Demanda anual vivienda` (flujo nuevas familias/año) · `Mercado en venta` (pool comprador
activo) · `Rangos demanda vivienda` (rango de precio de esa demanda) ·
`Casa`/`Departamento o edificio`/`Vivienda en vecidad o cuartería`/`Otro tipo de vivienda`
(tipo de vivienda) · `Propia`/`Alquilada`/`Prestada`/`Otra situación` (tenencia) ·
edades `0 a 4` … `75 y Más` · `Niños`/`Adolescentes`/`Jovenes`/`Jovenes_adultos`/
`Consolidados`/`Nesters` (etapas de vida) · `Municipio` · `Estado` · tipología de hogar y
situación conyugal (usadas por `_build_di_detail`).
### 3.2 DescargaDI · KMZ (mismo ZIP) → `agebs_geo`
Por AGEB: `nse_rank` (ordinal 1=A…), `nse_txt`, centroide `lng`/`lat`.
### 3.3 VVV (vvv/query, capa por modo: `vv_venta` · `vv_renta` · `vh_venta`)
resumen (proyecto): `PROYECTO` · `F__M2_PROM` (pm² prom) · `F__UD_PROM` (ticket prom) ·
`X_coor`/`Y_coor`. ft (tipología): `F____UNIDAD` (precio unidad) · `F___M2` ($/m²) ·
`ÁREA_TOTAL`/`ÁREA_PRIVATIVA` (vertical) · `ÁREA_CONSTRUCCIÓN`/`ÁREA_TERRENO` (horizontal) ·
`CANTIDAD_DE_RECAMARAS` · `UNIDADES_VENDIDAS` · `UNIDADES_DISPONIBLES` · `Abs_Demanda`
(absorción un/mes observada de la tipología).
### 3.4 Predik (predik/isochrone)
Polígono GeoJSON por `minutes` y `transport_type=driving`.

## 4. Segmento de demanda (`dim_data.segments[]` · derive_segments)
| Variable | Qué es / fórmula |
|---|---|
| `NSE` | NSE del segmento por INGRESO real del bucket (`nse_by_ingreso`; fallback por valor de vivienda) |
| `bucket` | Etiqueta del rango de precio |
| `val_min`, `val_max` | Rango de precio (MXN) |
| `nuevas_fam` | Σ `Demanda anual vivienda` de las AGEB cuyo rango cae en el bucket (flujo/año) |
| `mkt_total` | Σ hogares de esas AGEB (profundidad/depth) |
| `demanda_total` | Σ `Mercado en venta` (pool comprador activo del bucket) |
| `tca` | `NSE_TCA[NSE]` (fuente única) |
| `ing_min`, `ing_max` | Banda de ingreso del NSE |
| `evidencia_vendidas`, `evidencia_disp` | Unidades vendidas/disponibles de la oferta en el bucket |
| `status` | sweet_spot / desatendido / oportunidad / atendido / oceano_rojo / bajo_crecimiento |
| `origen` | demand_driven / supply_driven |
| `aplicable` | Bucket dentro del rango de valor con oferta real del modo |
| `dual_featured`, `nota_mercado` | Ancla por percepción de valor sin demanda DIM local |
| `mkt_venta`, `mkt_renta`, `hog_propios` | H7 ✓: mkt_total × tenencia REAL del bucket (Alquilada/Propia de sus AGEBs; fallback zona; sin dato → None/N/D) |
| `share_renta`, `share_propia` | H7 ✓ (nuevas): proporción de tenencia real aplicada al bucket (decimal; None sin dato) |
| `rent_min`, `rent_max` | H8 ✓: valor × `renta_pct_zona` (tasa de renta OBSERVADA de la zona) |
| `renta_pct_zona`, `renta_pct_fuente` | H8 ✓ (nuevas): mediana($/m²/mes vv_renta) ÷ mediana($/m² venta); fuente `observada` (≥3 obs en ambas capas) o `base_digo` (0.4% fallback documentado) |

## 5. Producto (`zone_data.productos[]`)
Comunes (venta vertical y horizontal): `tipo` · `rec` · `m2` (+`m2_num`) · `pm2` (+`pm2_num`) ·
`ticket` (+`ticket_num`) · `abs` (+`abs_num`) · `abs_origen`
(comparables_directos / demanda_sin_competencia / sin_demanda / sobreofertado /
absorcion_oferta_directa) · `abs_n_directos` · `abs_mediana_directos` (dato de validación) ·
`abs_competidores` (flujo competidor activo) · `abs_inv_competidor` · `abs_pronostico{12,18,24}` ·
`pm2_recomendado` · `ticket_recomendado_M` · `precio_tol_veredicto` · `status` · `recomendado` ·
`no_recomendable_motivo` · `aplicable` · `featured` · `seg_dim` · `mkt_segmento` · `nuevas_fam` ·
`nuevas_fam_year` (flow) · `depth` (stock hogares) · `mix_num` · `perfiles` · `categoria` ·
`nota_mercado` · `tca` · `competidores` · `mercado`.
Solo vertical: `variantes[]` (multi-programa: `{rec, m2, pm2, area_recamaras_max,
min_m2_recamara, _base}`).
Solo horizontal: `m2_construccion` · `m2_terreno` (+`m2_terreno_num`).
Renta (`productos_renta[]`): mismos nombres con renta mensual en `ticket`/`renta`.

## 6. Zona de análisis (`zone_data._zona_analisis` · perception)
`isocronas{min: geojson}` · `zona_poligono` (morado) · `barrera` · `metodo`
(isocrona / mercado_del_pin / barrera_nse) · `media`/`sd`/`cv` ($/m² de la zona) ·
`cobertura_pct` · `motivo` · `sin_valor_percibido` · `nota_valor` ·
`mercados{detectado,k,gap,var_explained,pesos,pin_cluster}` ·
`competidores{directos[],primarios[],secundarios[],n_*}` (sets morado/azul/verde) ·
`valor_zona{pm2,m2_ref,ticket_ref_M,fuente,rigidez,n_comparables,nota}` (cascada
directos→primarios→secundarios→percepción de valor) · `agebs_geo`.

## 7. Demografía (`dim_data` + zone_data)
`population` · `households` · `tca` (decimal ponderado por población) · `personas_hogar` ·
`ingreso_hogar` (IXH real del NSE dominante) · `ingreso_total_anual` · `nse{A..E:{hog,pct,
ingreso}}` (claves front: Cm=C+, Dm=D+) · `nse_dominante` (etiqueta con percepción de valor
si aplica) · `tenencia{propia,alquilada,prestada,otra}` (%) · `hog_renta` · `edad_grupos[6]`
(niños/adolescentes/jóvenes/jov_adultos/consolidados/maduros) · `municipio` · `estado` ·
`pais` · `municipios_todos` · `nse_dim[]` (por NSE: rangos, `ixh_nse`, `viv_nse`, población
por etapa de vida, `tca`) · `di_detail{tipologia_hogar, personas_hogar, …}`.

## 8. `zone_data._vars` (fuente única que TODAS las secciones del front consumen)
`pin{lat,lng}` · `predio_m2` · `uso_comercial` · `perfil_iso` · `perfil_label` ·
`isocrona_primaria_min` (azul) · `isocrona_secundaria_min` (verde) · `isocronas_min[]` ·
`zona_poligono` (morado) · `barrera_mercado` · `mercados_detectados` · `gap_separabilidad` ·
`varianza_explicada` · `competidores_directos[]` · `competidores_primarios[]` ·
`competidores_secundarios[]` · `n_directos` · `n_primarios` · `n_secundarios` ·
`universo_proyectos[]` · `n_universo` · `proyectos[]` · `kpis` · `poblacion` · `hogares` ·
`ingreso_hogar` · `nse_dominante` · `tca` · `municipio` · `estado` · `pais` ·
`municipios_todos` · `segmentos_demanda[]` · `productos[]` · `productos_renta[]` ·
`sweet_spot`.

## 8b. F-B/F-C · Variables nuevas (aditivas)
| Variable | Qué es |
|---|---|
| `analisis_nombre/version/id_str/fecha` | ZA-8 · identidad universal del análisis (en zone_data y _vars) |
| `analisis_key` | Llave del análisis en caché (= id_str) para `/api/zona/seccion` y `/api/zona/estrella_filtro` |
| `stats_robustas{n,mediana,mad,cv_robusto,p10,p25,p75,p90,iqr,outliers_n,outliers,min,max}` | RES-2 · descriptor robusto estándar (en perception, valor_zona y oferta_stats) |
| `agebs_geo[i].ring / area_km2 / attrs` | F-B · polígono decimado del AGEB, área y atributos publicados por la base (capas del mapa) |
| `percepcion_detalle{pm2_mediana,pm2_mad,banda_nucleo,limite_inferior,limite_superior,extremos,n_comparables,outliers_n,nse_percepcion,mercado_meta{nse,ingreso_min,ingreso_max,ticket_ancla,perfiles,etapas_top,share_renta},nota}` | ZA-6 · delimitación de percepción + mercado meta |
| `resumen_comercial{<proyecto>:{estatus,vendidas,disp,desplazamiento_pct,m2_mediana,m2_mediana_disp,pm2_mediana,pm2_mediana_disp,precio_mediana_M,abs_mediana,n_tipologias,estrella}}` | F-C · clasificación comercial por proyecto (activo/agotado/sin_dato) con medianas duales |
| `oferta_stats{pm2_total,pm2_disponible,m2_*,precio_M_*,abs_*}` | F-C · stats robustas duales de la oferta (RES-3: disponible manda para precio vigente) |
| `top_estrella{zona[3],por_segmento{bucket:estrella}}` + `criterio_estrella` | RES-5 · producto estrella (replicable a todos los usos) |
| `estrella{proyecto,rec,m2,precio_M,pm2,vendidas,disp,desplazamiento_pct,abs}` | Forma canónica del producto estrella |
| Endpoints nuevos | `POST /api/zona/seccion` · `POST /api/zona/estrella_filtro` · `GET /api/zona/geocode` · `GET /api/zona/reverse` |

## 9. Pendientes de catálogo (se agregarán al diseñar cada sección)
Población flotante (`flotante_*`), mercado extranjero (`extranjero_*`), densidad
(`densidad_ageb`), zona en transición (`zona_transicion`), perfiles ICSC/ULI
(`perfil_usuario_*`), y variables propias de lotes / industrial / comercial / logística /
hotel (prefijo por uso).

## 8c. DEM-1 · Variables nuevas (aditivas)
| Variable | Qué es |
|---|---|
| `segmentos_dem1[]` | Perfiles de demanda: `{perfil_id, cohorte(C1..C7), cohorte_label, nse, banda_ingreso_tag(alto/bajo/null·GMM), ixh_mediana, capacidad_pago_banda_M[2], hogares_stock, nuevas_fam_year, pool_activo, crecimiento_pct(TCA), programa{rec,cajones}, m2_banda[2], pm2_derivado_banda[2], ticket_banda_M[2], bucket_principal, fuente_masas, confianza{n_agebs,hogares_grupo}}` |
| `dem1_meta` | `{metodo_masas, umbral{pct,hogares}, capacidad{pti_ref,pti_max,tasa,plazo_m,enganche}, gmm{nse:{k,medias,corte,motivo}}, conservacion{nf_buckets,nf_perfiles,ok}, nota_captable, version_modelo}` |
| Constantes | `PTI_REF=0.30 · PTI_MAX=0.35 (banca MX · U3) · TASA_HIPOTECARIA_REF=0.105 (CONFIRMAR vigente) · PLAZO_HIP_MESES=240 · ENGANCHE_REF=0.10 · UMBRAL_PERFIL_PCT=0.05 · UMBRAL_PERFIL_HOG=300 (U1: calibrar)` — todas configurables por entorno |
| `_BANDA_TAMANO_TICKET` / `_banda_tamano_por_ticket()` | FUENTE ÚNICA de bandas de tamaño por ticket (antes duplicada dentro de derive_productos_venta; mismos valores) |

## 8d. PROD-PERFIL + INV-3 · Variables nuevas (aditivas)
| Variable | Qué es |
|---|---|
| `segmentos_dem1[i].oferta_perfil{n_tipologias,n_activas,inventario_disp,oferta_flujo_mensual}` | Oferta que ATIENDE al perfil (mismo programa, ticket en su capacidad) |
| `segmentos_dem1[i].demanda_mensual / insatisfecha_mensual / status_perfil` | Resta flujo contra flujo por perfil (desatendido/equilibrado/sobreofertado/sin_movimiento) |
| `segmentos_dem1[i].producto_sugerido{rec,cajones,m2,ticket_M,pm2,en_nucleo_percepcion,ajuste}` | Producto por perfil anclado al núcleo de percepción (funcional → comprable) |
| `dem1_meta.producto_perfil{resumen,nota}` | Conteo de perfiles por status |
| `TASA_HIPOTECARIA_REF = 0.091` | 9.1% CONFIRMADA por Héctor · full backend, jamás ajustable en front |
| `POST /api/zona/ficha_inventario` | INV-3 · PDF carta para bancos (portada banco/desarrollador, resumen robusto, sección por proyecto, hoja por producto; plusvalías "próximamente" hasta P3). reportlab==4.5.1 agregado a requirements.txt |
| Marcadores "próximamente" | Ficha de proyecto: desarrollador, descripción, mercado meta, cercanías, inicio venta, entrega/acabados, amenidades y plusvalías por periodo — el dato existe en la base; la ruta del API está en tickets P1/P3 |

## 8e. ISO-MULTI · Variables nuevas (aditivas)
| Variable | Qué es |
|---|---|
| `ZonaRequest.iso_fuente` | predik (default) · valhalla · ors · tomtom — la lógica de negocio NO cambia con la fuente |
| `zone_data.iso_fuente_usada` / `iso_nota` | Con qué fuente se construyó la zona; nota cuando hubo fallback (transparencia) |
| Respuesta de `/api/zona/poligono` | + `iso_fuente`, `iso_nota` |
| `POST /api/zona/isocrona_comparar` | A/B de fuentes: área km², vértices, ms, IoU vs referencia (Predik si responde) y % de área vs referencia |
| Constantes env | `DATARIA_ISO_FUENTE` (default predik) · `DATARIA_ISO_FALLBACK` (default valhalla) · `DATARIA_VALHALLA` · `DATARIA_ORS_KEY` · `DATARIA_TOMTOM_KEY` |
| Helpers | `fetch_isochrone_fuente` (fuente+fallback declarados) · parsers que normalizan al contrato Predik · `_area_ring_km2` · `_iou_rings` |
