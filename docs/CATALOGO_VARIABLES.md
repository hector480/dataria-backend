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
`veto_percepcion` (VETO DE PERCEPCIÓN · decisión 6 · 19 jul 2026: True cuando el $/m²
publicado del producto queda DEBAJO del piso de percepción del predio — P10 robusto de lo
observado = `percepcion_detalle.limite_inferior`. El veto apaga `recomendado` y `featured`
DESPUÉS de todas las reglas existentes, NO toca `aplicable`/`status`/absorción, y
`no_recomendable_motivo` ACUMULA "debajo del piso de percepción del predio (P10 $X/m²)"
— combinado con " · " si ya había motivo de absorción. Sin P10 observado o sin `pm2_num`
numérico NO hay veto: no se inventa. Solo productos de VENTA del modo activo; renta queda
fuera porque su $/m² mensual no es comparable con la percepción de venta).
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

## 8f. CAPTABLE v1/v2 + ISO-MULTI front + OD (aditivas)
| Variable | Qué es |
|---|---|
| `ZonaRequest.incluir_captable / captable_min` | Opt-in del mercado captable (anillo principal+10, tope 30 min) |
| `zone_data.mercado_captable{activo, metodo, exponente, anillo_min, fuente_isocrona, n_agebs_corona, masa_fuente, origenes[], extranjero, poligono_captable, nota, ancla_censal}` | Orígenes del captable. `metodo`: huff_gravity_v1 (modelo) u od_sintetico_inegi_v1 (anclado a censo) |
| `origenes[i]{nse, municipio, n_agebs, hogares_est, dist_km_mediana, share_pct, fuente_share, viajes_censales_muni}` | `fuente_share`: censo_2020 (observado) o modelo_huff (declarado) |
| `extranjero{presente, poblacion_extranjera, share_pct, zona_turistica, umbral_pct, nota}` | Se enciende solo al aparecer columnas (P1); umbral turístico 3% configurable |
| `ancla_censal{ok, fuente, muni_destino, viajes_totales_censo, cobertura_corona_pct, confianza, motivos_disponibles}` | Trazabilidad del anclaje censal |
| `GET /api/od/status?estado&muni` | Diagnóstico de la cadena del ancla (local/autofetch/errores + marginales top) |
| Constantes env | `DATARIA_HUFF_EXP=2 · DATARIA_CAPTABLE_MIN_TOPE=30 · DATARIA_UMBRAL_EXTRANJERO=0.03 · DATARIA_OD_URL_TPL · DATARIA_OD_AUTOFETCH=1 · DATARIA_OD_DIR · DATARIA_OD_COBERTURA_MIN=0.6` |
| `datos/od_censo/<estado>.csv` | Ancla censal canónica versionada (ORIGEN, DESTINO, MOTIVO, VIAJES) |

## 8g · Movilidad (zone_data.movilidad · PEAT-1/TRAF-1 · solo crece)
| Variable | Tipo | Descripción |
|---|---|---|
| movilidad.peatonal.estado | str | ok · error · (nunca inventar) |
| movilidad.peatonal.minutos | int | contorno peatonal (default 10 · env DATARIA_PEAT_MIN) |
| movilidad.peatonal.fuente | str | valhalla_pedestrian_osm (red vial real) |
| movilidad.peatonal.area_km2 | float | área del alcance caminando |
| movilidad.peatonal.poligono | ring | anillo [lng,lat] para el mapa |
| movilidad.peatonal.hogares / poblacion | int/N-D | masa REAL de AGEBs (KMZ DI) con centroide dentro; N/D si la base no publica masa |
| movilidad.peatonal.n_agebs / masa_fuente | int/str | transparencia de la masa (hogares_kmz · poblacion_kmz) |
| movilidad.peatonal.flujo_peatonal.estado | str | proximamente (sin fuente gratuita observada; DENUE+censo lo modelará) |
| movilidad.vehicular.estado | str | ok · proximamente (sin DATARIA_TOMTOM_KEY) · error |
| movilidad.vehicular.indice_fluidez | float | mediana velocidad_actual/flujo_libre (1.0=libre) · pin+4 cardinales ~1 km |
| movilidad.vehicular.velocidad_kmh / velocidad_libre_kmh | float | medianas robustas (km/h) |
| movilidad.vehicular.n_puntos / fuente / nota | — | tomtom_flow · instantánea, no promedio histórico |

## 8h · ZONA-RÍO + RENTA-ANCLA + CAPTABLE-V3 (8 jul 2026 tarde · solo crece)
| Variable | Tipo | Descripción |
|---|---|---|
| perception.metodo = "banda_percepcion" | str | Zona morada = casco convexo de los ≥3 competidores DIRECTOS de banda ∩ isócrona (clip Sutherland-Hodgman `_clip_ring_sutherland_hodgman`). La zona no cruza río/bloques de distinta percepción-NSE |
| perception.cobertura_pct | float | Con banda_percepcion: área clip / área anillo ×100 (1 decimal, `_area_ring_km2`) |
| productos_renta[i].ancla_obs{p10, p90, n_obs, dentro_banda} | dict | Banda P10–P90 de renta/m² OBSERVADA (F___M2 de vv_renta = $/m²/mes; respaldo F____UNIDAD_MENSUAL/ÁREA_PRIVATIVA). pm2_renta = interpolación en banda por posición NSE; fuera de banda → aplicable=False y pm2_renta=N/D |
| mercado_captable.metodo = "gravedad_ipf_v3" | str | Viajes municipales censales desagregados a celdas NSE×municipio de la corona por gravedad (Ortúzar & Willumsen) + IPF 1 iteración (totales municipales EXACTOS) |
| mercado_captable.confianza = "anclado_municipal" | str | El volumen municipal es censal observado; el reparto a celdas es modelo |
| mercado_captable.ipf{munis_anclados, commuters_total_dia, f_prox_por_nse} | dict | Trazabilidad del IPF (`_captable_v3_ipf`) |
| origenes[i].commuters_dia | int | Viajes/día del origen hacia el destino (suma de sus celdas) |
| origenes[i].pct_poblacion_commuter | float/"N/D" | commuters/población DI de la celda ×100 · N/D si >100 (no interpretable: municipio ⊃ corona) o sin población |
| origenes[i].hogares_di / hogares_di_nota | int/str | (8 jul mañana) hogares reales del DI captable por NSE cuando el KMZ no publica masa |
| mercado_captable.perfil_captable{commuters_total_dia, distribucion_nse_pct, edad_grupos, ingreso_hogar_mensual, gasto_anual, alcance} | dict | Perfil de commuters: NSE del modelo anclado + edad/ingreso/gasto REALES del XLSX de la corona; dimensión ausente = "N/D" |
| mercado_captable.columnas_faltantes | list | Columnas del DI que faltaron para el perfil (vacía si nada faltó) |

## Ocupación de renta observada (18 jul 2026 · orden directa de Héctor)
| Variable | Tipo | Significado |
|---|---|---|
| productos_renta[i].ocupacion_target | str | CAMBIO POR ORDEN DE HÉCTOR (18 jul 2026): antes "92%" fijo (marcado 'revisar'); REGLA FINAL = "N/D" siempre — la capa vv_renta no trae ocupación física (su ESTATUS es estado del anuncio, no del edificio; verificado con datos reales). Cuando la base publique ocupación real se conecta en _ocupacion_renta_obs. El contrato del front (string parseable o N/D) se conserva |
| productos_renta[i].ocupacion_obs_n | int/null | NUEVA · nº de tipologías con estatus que soportan la ocupación observada (transparencia de muestra) |
| renta_baseline.occ | int/null | CAMBIO (misma orden): antes 90 fijo; REGLA FINAL = null (sin ocupación en la base) → el slider del simulador se muestra deshabilitado con N/D. Se llenará cuando exista el dato real |
| renta_baseline.occ_fuente / occ_n | str/int | NUEVAS · fuente declarada ("observada · ESTATUS capa renta") y n de la muestra |
| competidores.directos/secundarios[i].nota_set | str | (ya existía 8 jul) ahora también en ex-primarios degradados: "distinta percepción de valor/NSE (cliente compartido)" — regla dictada tal cual (18 jul) |

## Decisiones una-por-una del 19 jul 2026 (órdenes de Héctor)
| Variable | Tipo | Significado |
|---|---|---|
| segmentos_dem1[i].buckets_desglose | dict | NUEVA · ledger {bucket: nuevas familias recibidas} del reparto DEM-1 — habilita auditar conservación de masa POR bucket (decisión 3) |
| zone_data.fecha_corte_venta / fecha_corte_renta | str/null | NUEVAS · máxima FECHA_DE_LEVANTAMIENTO observada por capa (RES-4); se muestra discreta en el encabezado de Resumen; sin dato → null y no se muestra (decisión 2) |
| renta_baseline.units | int/null | CAMBIO (decisión 5): mediana OBSERVADA de unidades por proyecto de la zona (antes 120 fijo); null → slider deshabilitado |
| renta_baseline.units_fuente | str/null | NUEVA · fuente declarada del arranque de unidades |

## BACKFILL ZA (auditoría 19 jul 2026 · variables históricas de Zona de Análisis documentadas desde el código)
| Variable (_vars / _zona_analisis) | Significado (fuente → regla) |
|---|---|
| pin, predio_m2, uso_comercial | Entrada del usuario (lat/lng, m² del predio, flag comercial) |
| perfil_iso / perfil_label / isocronas_min / isocrona_primaria_min / isocrona_secundaria_min | Perfil de isócronas por tamaño (§10): minutos usados, primaria (azul) y secundaria (verde); geometrías por cadena Predik→Valhalla |
| iso_fuente_usada / iso_nota | Fuente de isócrona vigente y nota (solo dato interno; front limpio por directiva) |
| zona_poligono / barrera_mercado / metodo / cobertura_pct / motivo | Zona de influencia real (morado): cascada banda_percepcion→barrera_nse→mercado_del_pin→isocrona; % del anillo cubierto y explicación |
| mercados_detectados / gap_separabilidad / varianza_explicada / cluster_names / mercados | Detección universal de mercados (clustering sobre señales ticket/pm2/pos/nse) |
| perception.n_total/n_zona/media/sd/cv/valor_zona/sin_valor_percibido/nota_valor/ajuste_inventario/proyectos | Percepción de valor del mercado del pin: conteos, estadística, valor de zona (VVV manda sobre demografía) |
| percepcion_detalle.pm2_mediana/pm2_mad/banda_nucleo/limite_inferior/limite_superior/extremos/n_comparables/outliers_n/nse_percepcion/mercado_meta/nota | ZA-6: bandas robustas (piso P10 · núcleo P25-P75 · techo P90, mediana/MAD, Tukey) + mercado meta derivado |
| competidores_directos/primarios/secundarios + n_* + set_competidor / criterio_directos / rango_percepcion / nota_set | Sets por regla dictada (directo = banda±2·MAD + NSE ±1 + isócrona primaria; resto secundario sup/inf; primarios solo sin banda evaluable) |
| universo_proyectos / n_universo / proyectos / kpis | Universo de oferta VVV del anillo mayor y KPIs robustos |
| poblacion / hogares / ingreso_hogar / nse_dominante / tca / municipio / estado / pais / municipios_todos | Demografía del DI (AGEB): masa, IXH real del NSE dominante (dominante por masa × proximidad, percepción puede subirlo), TCA |
| segmentos_demanda / productos / productos_renta / sweet_spot | Puentes a DIM/Producto/Renta (documentados en sus secciones) |
| agebs_geo / nse_barrier | Geometrías AGEB del KMZ con NSE (capas y barrera espacial) |
| fecha_corte_venta / fecha_corte_renta | (19 jul) máx FECHA_DE_LEVANTAMIENTO por capa — encabezado de Resumen |

## BACKFILL RESUMEN + MAPA (auditoría 19 jul 2026)
| Variable | Significado |
|---|---|
| oferta_stats.pm2_total/pm2_disponible/m2_*/precio_M_*/abs_* | RES-3: estadística ROBUSTA dual (mediana/núcleo P25-P75/MAD/n) del inventario TOTAL vs DISPONIBLE — disponible manda para precio vigente; total para histórico |
| top_estrella.zona[] / por_segmento{} / criterio_estrella | RES-5: producto estrella (mayor % desplazado con velocity normalizada, evidencia ≥3 ventas) por zona y por segmento |
| resumen_comercial | Texto ejecutivo del corredor generado de los datos (sin promedios) |
| inventario_precio / inventario_m2 | Distribuciones de inventario por rango (gráficas Resumen/Inventario) |
| kpis.avg_abs / avg_pm2 / avg_ticket / avgAbs / avgPm2 | LEGACY (promedios): ya NO se muestran en Resumen (la pantalla usa oferta_stats robustas); candidatos a triage del lote #8 — conservados como API por compatibilidad |
| MAPA_CAPAS / buildCapaNse / buildCapaPv (front) | Capas del mapa maestro: polígonos AGEB por NSE (agebs_geo del KMZ) y puntos por percepción (P25/P75 de stats robustas del mercado del pin) — front solo pinta datos del payload |

## BACKFILL INVENTARIO (auditoría 19 jul 2026)
| Variable | Significado |
|---|---|
| _typologies{proyecto:[…]} | Tipologías por proyecto desde capa ft de VVV: tipo, area_priv/terr/total, rec, precio_ud, precio_m2, unid_total/disp/vend, abs, avance, cajones (CAJONES_ASIGNADOS de la capa) |
| PROJECT_META_BY_ZONE / _project_meta | Metadatos por proyecto (desarrollador/inicio_venta/entrega: "próximamente" permitido hasta que el wrapper los exponga — INV-5/6) |
| filtro_rango_usuario / producto_estrella_corredor (endpoint estrella_filtro) | INV-4: corredor a la medida con rangos del usuario; cálculo 100% backend (valida analisis_key) |
| /api/zona/ficha_inventario | INV-3: fichas PDF para bancos (reportlab backend; validado 6 jul) |

## BACKFILL DEMANDA (auditoría 19 jul 2026)
| Variable | Significado |
|---|---|
| dim_data.segments[] | Buckets DIM: NSE, bucket de precio, val_min/max, mkt_total/venta/renta, nuevas_fam (Demanda anual base), demanda_total, evidencia_vendidas/disp, rent_min/max, ing_min/max, status, aplicable (rango de oferta observada) |
| segmentos_dem1[] | Matriz DEM-1: perfil_id, cohorte (household lifecycle), NSE, banda_ingreso_tag, ixh_mediana, capacidad_pago_banda_M (PTI 30-35% · tasa 9.1% · 240m · eng 10%), hogares_stock, nuevas_fam_year, pool_activo (5%), programa (rec+cajones), m2_banda, pm2_derivado_banda, buckets_desglose (ledger 19 jul), oferta_perfil, demanda/insatisfecha_mensual, status_perfil, producto_sugerido, fuente_masas, confianza |
| dem1_meta | metodo_masas, umbral, capacidad (PTI/tasa/plazo/enganche), gmm por NSE con motivo (salvaguarda), conservacion {nf_buckets=nf_perfiles}, producto_perfil (PROD-PERFIL), version_modelo |
| di_detail | Detalle del DI para gráficas: tipologia_hogar/situacion_conyugal/poblacion_hogares/personas_hogar ({label,count,pct,parent}) — alimenta charts (canvas) |
| percepcion_detalle.mercado_meta | NSE/ingresos/ticket ancla/perfiles/etapas del mercado meta (ZA-6) |

## BACKFILL RENTA + COMERCIO (auditoría 19 jul 2026)
| Variable | Qué es / fuente | Consumidor |
|---|---|---|
| `renta_segmentos[]` | `{seg, perfil, nse, ing, renta, rec, m2, hog, sweet}` · derive_renta_segmentos(segments, agebs); `m2`/`rec` se enlazan desde `productos_renta` por bucket cuando existen | tplRenta (tabla de segmentos; ★ = sweet) |
| `renta_baseline.m2` / `.pm2` | Medianas OBSERVADAS de la oferta de renta de la zona (RES-2); null → slider del simulador deshabilitado con N/D (completa la familia occ/units ya catalogada) | Simulador de sensibilidad · Renta |
| `recamaras[3]` | % de demanda por 1 / 2 / 3+ recámaras · derive_recamaras(agebs) (base censal) | KPI "Demanda 2 rec" + recamarasChart |
| `comercio.ingreso_anual` | Texto abreviado (p.ej. "3.5B") de Σ "Ingresos totales 2026" de las AGEB | KPI Comercio |
| `comercio.demanda{cat}` | Gasto anual MXN por categoría · Σ campos "Gasto …" de la base (C193-201) | demandaCatChart |
| `comercio.oportunidad{cat}` | m² de GLA soportados = gasto × CAPTURA ÷ ventas_m2_anual[cat] | oportunidadChart + gla |
| `comercio.captable{cat}` | m² captables por un desarrollo nuevo = oportunidad × CAPTABLE_PCT (15%) — verificado EXACTO en vivo | captableChart ("@ 15%" del front = constante backend, congruente) |
| `comercio.product_mix[]` | `{giro, m2, pct, tenant, renta "$a-b", renta_m2, anchor}` · solo giros con captable ≥ GLA_MIN_VIABLE; renta derivada del gasto captable/m² (OCC_RENTA) ±12%; ancla = Supermercado; tenant del catálogo TENANTS_POR_NSE según NSE efectivo | Tabla "Producto comercial recomendado" |
| `comercio.gla_target` | Σ m² de giros viables (= Σ product_mix.m2, verificado en vivo) | KPI "GLA objetivo" |
| `comercio.renta_low` / `renta_high` | Renta mensual estimada del GLA (M MXN): Σ(m2×renta_m2)×0.85; high = ×1.35. `renta_high` NO se muestra (API-only → triage lote #8) | KPI "Renta estimada · low scenario" |
| NSE efectivo comercio | max(NSE demográfico dominante, NSE de percepción de valor de la oferta) — congruente con "la percepción manda" | Selección de catálogo de tenants |
| Constantes comercio | CAPTURA 0.25 · ventas_m2_anual{10 giros} · CAPTABLE_PCT 0.15 · OCC_RENTA 0.10 · GLA_MIN_VIABLE 100 · banda renta ±12% · factor 0.85 · high +35% · ancla=Supermercado · TENANTS_POR_NSE (marcas por nivel) | ⚠ EXISTEN en app.py y NO están ratificadas en §10 → hallazgo #11 en COLA_DECISIONES (pendientes de tu una-por-una) |

## BACKFILL MEZCLAS + MONITOR (auditoría 19 jul 2026)
| Variable | Qué es / fuente | Consumidor |
|---|---|---|
| `_captureRate` (front, escenario) | Tasa de captación VENTA del escenario · default 1.0 (100%), slider 10-100% visible | Los 5 modos de "Crea tu mezcla" |
| `_captureRateRenta` (front, escenario) | Tasa de captación RENTA · default 0.5 (50%), slider visible | Modos de mezcla renta |
| getDemandDrivenProducts(cr) | Pool de mezcla VENTA = `z.productos.filter(recomendado)` — el VETO de percepción reduce este pool automáticamente. EN VIVO (`__DATARIA_LIVE__`) `abs_base` = absorción DEL BACKEND (verificado exacto 6/6; el front no recalcula, el slider solo modula escenario) | Modos periodo/recomendación/unidades/perfil |
| getDemandDrivenRentaProducts(cr) | Pool RENTA = `productos_renta` recomendados (3/3 vivo). `_occ` = ocupación observada o null; `_renta_anual_ud` = null cuando occ es N/D (verificado 3/3 — nada re-inventa el 90) | Modos de mezcla renta |
| Supply-only en mezcla | SOLO disponible en modo manual (verificado: 0 en pool demand-driven) | Modo manual |
| `_projectMix` / `_monitorSource` / `_monitorPeriod` | Mix editable del Monitor (arranca VACÍO — nada inventado), origen custom/proyecto/venta/renta, horizonte 24m default (rango visible 6-60) | Monitor |
| API `evaluar_mix` {items·item, period, capture, typologies, segments} | AMENAZA COMPETITIVA 100% BACKEND (amenaza_competitiva): threat_ratio = ud competidoras / demanda del horizonte; net_demand; estrategia (expansión/acelerar/monitorear/aguantar/reposicionar); competidores directos; precio recomendado = MEDIANA $/m² de directos + veredicto (PRECIO_TOL_VEREDICTO). El front solo envía el mix (debounce 300ms) y pinta | Monitor secciones B/C |
| Constantes Monitor | `_MON_TOL_TICKET/AREA/REC` = alias de `_PRECIO_TOL_*` (±15% ticket · ±30% área · ±1 rec — FUENTE ÚNICA, y los criterios se declaran en pantalla, congruente); escalera de amenaza 2.0/1.0/0.5; fallback área 60 m² sin dato del usuario | ⚠ NO ratificadas en §10 → hallazgo #13 |
| Umbrales modo Recomendación | avgAbs/avgPm2 = PROMEDIOS de zona CALCULADOS EN FRONT (getZoneAverages / getRentaZoneAverages; rotulados "Promedio zona" en pantalla) | ⚠ hallazgo #12: promedio vs mediana (RES-2) + cálculo en front |
