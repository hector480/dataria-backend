# PLAN V2 · Rediseño sección por sección (Vivienda Vertical primero)
**Fuente: listado de Héctor (6 jul 2026). Modo de trabajo: Héctor corrige desde el front;
Claude traduce a reglas universales procesadas en el backend. Cada ítem se reta contra un
estándar de industria antes de implementarse. IDs referenciables en todo el proyecto.**

Regla transversal: todo lo que se construya aquí para vivienda vertical se diseña con
variables de catálogo reutilizables para horizontal, lotes, industrial, comercial y
logística (mismo proceso, particularidades por uso).

---

## ZONA DE ANÁLISIS (ZA)
Objetivo: precisión en la zona de análisis; contra quién SÍ se compite y contra quién no
(mal diseñados o distinta percepción de valor).

| ID | Qué pidió Héctor | Estándar/reto aplicable | Depende de |
|---|---|---|---|
| ZA-1 | Nombre del análisis + guardado con fecha de modificación + cuentas de usuario (username/password, verificación por correo con clave temporal) + tablero de administración de cuentas | Estándar: auth con hash (bcrypt/argon2), tokens de verificación con expiración, OWASP API Top 10 (ya era pendiente #1). Requiere DB real (SQLite/Postgres en Render) — conecta con Fase 2/3 del backlog maestro | Decisión de servicio de correo (P4) |
| ZA-2 | Detectar ubicación del predio desde el pin (reverse geocoding) y desde dirección escrita (geocoding) | Estándar: geocodificador (Nominatim/ArcGIS geocoder). YA existía como "pendiente opcional" en LISTA_REVISION | Confirmar geocoder disponible en PRSP/ArcGIS (P5) |
| ZA-3 | Isócrona por superficie del terreno + zonas de influencia para competidores/referentes + **zonas de origen-destino de mercado captable** + variables de normatividad listas (sin usar aún) | HALLAZGO: el API PRSP hoy SOLO expone isócronas de Predik (`/api/predik/isochrone`; health "via isochrone"; rutas OD probadas → 404). Las zonas origen-destino requieren exponer esa capacidad de Predik en el API | ACCIÓN HÉCTOR (P2) |
| ZA-4 | Mapa GRANDE con capas encendibles/apagables: NSE, Percepción de Valor, Zona de influencia, Zonas de origen del mercado captable (color + lista por colonia con % de representatividad, NSE/edad/motivo de visita) · isócronas explicadas por propósito sin revelar el método | Estándar GIS: control de capas (Leaflet layers control), coropletas por AGEB (ya existe la geometría del KMZ). El captable depende de ZA-3 | ZA-3, MAPA-1 |
| ZA-5 | Sets de competidores desplegables al hacer clic por categoría (directos/primarios/secundarios) | UI sobre datos ya existentes (competidores por set en payload) | — |
| ZA-6 | Delimitar percepción de valor: límites inferior/superior + características del mercado meta que genera demanda para esa zona | Bandas por percentiles robustos (P10/P25/P75/P90) de la oferta del mercado del pin, no promedio. Mercado meta descrito desde NSE/etapa de vida/ingreso del catálogo | — |
| ZA-7 | Tabla de zona de influencia real SIN N/D: dispersión, coeficiente de variación + métricas de tendencia (gaussianas o no) de población en crecimiento y valor de zona correcto (por reglas de zona, no promedio de todo) | Estándar: mediana + MAD (desviación absoluta mediana), CV robusto, percentiles; tendencia poblacional con tasa compuesta por AGEB. El "valor de zona" ya usa cascada (directos→…); se refuerza con mediana/MAD y n | — |
| ZA-8 | Sintaxis universal de identidad del análisis: `nombre_usuario · colonia · municipio · estado · vAAAAMMDDHHMM` presente en TODOS los encabezados de la herramienta | Variable de catálogo nueva: `analisis_id_str` (+ `analisis_nombre`, `analisis_version`). Se construye en backend y todos los templates la leen | ZA-1 (nombre) |

## RESUMEN (RES)
| ID | Qué pidió | Estándar/reto | Depende de |
|---|---|---|---|
| RES-1 | Proyectos clasificados: comparables activos primero, luego los que agotaron en los últimos 8 meses; inventario/nombre/absorción/precio = el dato MÁS RECIENTE; columna de promedio del último trimestre y absorción media desde lanzamiento | "Absorción desde lanzamiento" = sales velocity estándar (unidades vendidas ÷ meses desde salida). REQUIERE: fecha de lanzamiento y serie por periodo en la base (P3). Uniformidad de comparables con detección de outliers (mediana ± k·MAD / IQR Tukey) sin que distorsionen la lectura | P3 (campos de fecha/serie) |
| RES-2 | Nunca promedios: medianas/moda/métrica robusta + modelo para "normales vs anormales" | CORRECTO y estándar: mediana + MAD; outliers por IQR o z-score robusto. Se aplica en TODA la herramienta (regla de catálogo: `*_mediana`, `*_p25`, `*_p75`, `*_mad`, `*_outliers[]`) | — |
| RES-3 | Reemplazar TCA y acrónimos (glosario o nombre completo); mostrar tamaño (mediana/moda); variables de TODO el inventario vs SOLO disponible — pidió mi input | RESPUESTA CLAUDE: mostrar ambos pero con roles distintos — el DISPONIBLE manda para precio de mercado vigente (lo agotado ya no marca precio: regla ya confirmada en Monitor) y el TOTAL manda para velocidad/absorción histórica y mezcla exitosa. UI: métrica principal = disponible; "histórico total" = segunda línea/toggle. Glosario al final de cada sección (usabilidad: no interrumpe el escaneo de tabla) | — |
| RES-4 | Freshness: mostrar SIEMPRE el dato más nuevo (caso Guadalupe: mostraba febrero habiendo junio/julio) | En verificación con dump de campos (fecha/periodo en VVV). Si la capa trae varios periodos por tipología, el backend debe filtrar al más reciente; regla nueva de catálogo: `periodo_dato`, `fecha_corte` visibles en todos los tableros | Descubrimiento en curso |
| RES-5 | Producto estrella por proyecto (clic o subrenglón): tamaño, precio/m² y por unidad a la fecha, % desplazado + TOP 3 de producto estrella por zona (y por segmento si hay >1 mercado) — replicable a todos los usos | Variables catálogo: `producto_estrella{...}` por proyecto y `top3_estrella[]` por zona/segmento. Criterio: mayor % desplazado con velocity normalizada (no promedio) | RES-1 |

## MAPA (MAPA)
| ID | Qué pidió | Recomendación |
|---|---|---|
| MAPA-1 | ¿Capas (NSE, percepción, densidad, captable) aquí o en Zona de Análisis? Pidió recomendación UX | RESPUESTA CLAUDE: UN solo mapa maestro (sección MAPA) con control de capas estándar GIS — evita mantener dos mapas sincronizados y duplicar renders (costo y bugs). En ZONA DE ANÁLISIS queda el mapa de trabajo (pin + isócronas + zona morada + competidores) con 2-3 toggles mínimos (NSE, percepción) para la lectura inicial; el análisis profundo de capas vive en MAPA con leyendas y lista de colonias captables. Patrón estándar: "overview first, zoom and filter, details on demand" (Shneiderman) |

## INVENTARIO (INV)
| ID | Qué pidió | Estándar/reto | Depende de |
|---|---|---|---|
| INV-1 | Todo el inventario con lógica de RESUMEN pero al detalle producto×proyecto + forma de entrega/acabados + TODA la información disponible de la base | Dump de campos en curso: se mostrará TODO lo que la capa traiga (sin escatimar) | Descubrimiento |
| INV-2 | Absorción del mes en curso + trimestre + histórica desde lanzamiento; % plusvalía en los 3 periodos por proyecto/producto/segmento/perfil; activadores de escenario temporal arriba | Plusvalía = variación de precio entre periodos → REQUIERE serie temporal en la base (P3). Si la capa solo trae snapshot, pedir al equipo PRSP exponer la serie (la base la tiene: Héctor confirma capturas mensuales) | P3 |
| INV-3 | Botón "Fichas de inventario": PDF hoja carta para bancos — portada (nombre proyecto/banco/desarrollador via ventana emergente), una sección por proyecto, una hoja por producto + resumen de INV-1/2. Guías de diseño Dataria (Geist/JetBrains, ink/azure/pulse/paper) | Generación en backend (reportlab/weasyprint). Endpoint nuevo `/api/zona/ficha_inventario` | INV-1/2 |
| INV-4 | Filtros con rangos manuales del usuario + producto estrella del corredor con esos parámetros vs el de la zona (absorción, $/m², $/unidad, plusvalías) | Variables: `filtro_rango_usuario{...}`, `producto_estrella_corredor{...}` | RES-5 |
| INV-5 | Ficha de proyecto no muestra DESARROLLADOR — está en la base: encontrarlo y mostrarlo | Dump de campos en curso | Descubrimiento |
| INV-6 | Ficha sin descripción/mercado meta/cercanías y campos N/A: recuperar la regla de negocio que los generaba u obtenerlos de la base; mostrar el periodo más reciente | Buscar en template estático histórico la regla que generaba descripción/cercanías; lo que sea de base → dump | Descubrimiento |
| INV-7 | Ficha por TIPOLOGÍA además de la de proyecto: programa, acabados/equipamiento, estacionamientos, $/unidad, $/m², absorción, Δprecio vs periodo anterior CON fecha del periodo | Igual: requiere serie de periodos (P3) + campos de equipamiento/cajones (dump) | P3 |
| INV-8 | Todo lo anterior va también al PDF y a exportar .csv/.xls | — | INV-3 |

## DEMANDA (DEM)
| ID | Qué pidió | Estándar/reto |
|---|---|---|
| DEM-1 | Rediseño del corazón: SEGMENTOS DE DEMANDA OBJETIVO. Un producto por combinación real de (etapa de vida × NSE × rango de ingreso × capacidad de pago), no "más m² = más $/m²". Asociar perfil de hogar → programa (recámaras+cajones) → ajustar por ingreso/capacidad a $/m² dentro de rango con variantes funcionales y comprables. Medir demanda con modelo gaussiano/no gaussiano: mercado total, crecimiento del segmento, demanda estimada. SEPARAR mercado natural (dentro de la zona) del captable (zonas de origen; extranjeros visibles si aplica). Base para TODOS los usos | Propuesta CLAUDE (a detallar en doc de diseño DEM-1 antes de codificar — checkpoint): (1) cohortes de etapa de vida desde pirámide de edades + tipología de hogar del DI (jóvenes solos/parejas sin hijos/familias con hijos por edad/nido vacío — estándar de household lifecycle); (2) cruce con NSE e ingreso real (IXH) por AGEB → matriz segmentos; (3) programa por cohorte con regla de recámara compartida ya validada + cajones por NSE/normativa; (4) capacidad de pago = ingreso × múltiplo hipotecario (4.5 ya en catálogo) con banda por enganche/tasa; (5) tamaño del segmento: mezcla de distribuciones (GMM) sobre ingreso×edad cuando la masa lo permita; con muestras chicas, conteo directo por AGEB (integridad > sofisticación); (6) demanda = flujo (Demanda anual) + pool activo (Mercado en venta×5%) del segmento — ya en catálogo; (7) captable: pendiente de ZA-3 (OD Predik) y P1 (flotante/extranjeros en base) |

---

## PREGUNTAS · RESPUESTAS DE HÉCTOR (6 jul 2026)
- **P1** · Flotante/extranjera: debe estar en "mercado captable"/demanda (columna de población
  extranjera). Si no aparece en el dump → PENDIENTE NO OLVIDAR: Héctor levanta ticket con el
  equipo de base de datos; aparecerá en horas. Revisar en cada dump nuevo.
- **P2** · OD: Predik SÍ lo tiene. El wrapper PRSP NO lo expone (21 rutas sondeadas → 404;
  health="via isochrone"). → TICKET equipo PRSP con contrato propuesto:
  `POST /api/predik/origen_destino` body `{latitude, longitude, minutes, direction:
  "origins"|"destinations", transport_type:"driving"}` → `{zonas:[{nombre (colonia),
  geometry (Polygon), share_pct (viajes de esa zona / total), viajes_abs}]}`.
- **P3** · La capa VV expone SOLO el periodo vigente; los históricos deben existir como
  columnas en la base ArcGIS → confirmar en dump de campos; si no llegan por el wrapper,
  mismo ticket PRSP (serie por periodo para absorción mensual/trimestral/histórica y
  plusvalía INV-2/7 y RES-1).
- **P4** · NO hay correo transaccional → ZA-1 se implementa por etapas: cuentas con
  contraseña HASHEADA (estándar) creadas desde tablero admin, SIN verificación por correo;
  la verificación se enchufa cuando exista servicio de correo. DB: se define en F-E
  (Postgres/persistencia en Render pendiente de aprobación de infra).
- **P5** · Geocoder: intentar ArcGIS como estándar; fallback abierto rápido y preciso.
  IMPLEMENTADO (F-A): cadena ArcGIS World Geocoder → Nominatim/OSM en
  `/api/zona/geocode` y `/api/zona/reverse`; cuando PRSP exponga el geocodificador del
  ArcGIS de Prosperia se apunta vía env `DATARIA_ARCGIS_GEOCODE` sin tocar código.

## FASES PROPUESTAS (checkpoint de Héctor para arrancar)
- **F-A · Fundaciones de dato e identidad** (desbloquea todo): freshness RES-4 + dump/mapa de campos reales (INV-5/6, RES-1) + identidad del análisis ZA-8 (sin cuentas aún: nombre+versión en payload) + métricas robustas RES-2 (medianas/MAD/percentiles en catálogo).
- **F-B · Zona de Análisis y Mapa**: ZA-5/6/7 + MAPA-1 (mapa maestro con capas NSE/percepción/densidad desde el KMZ) + ZA-4 parcial (sin captable hasta P2).
- **F-C · Resumen e Inventario**: RES-1/3/5 + INV-1/2/4/5/6/7 + fichas PDF INV-3/8 (requiere P3 para plusvalías).
- **F-D · Demanda**: doc de diseño DEM-1 → checkpoint → implementación + validación en zonas ancla.
- **F-E · Cuentas y guardado** (ZA-1/2): DB + auth + verificación por correo + tablero admin (requiere P4/P5).
Cada fase cierra con la batería completa + validación en anclas + Jalisco.
