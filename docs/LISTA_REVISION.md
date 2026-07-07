# LISTA MAESTRA DE REVISIÓN v2
# Base de verdad: dashboard_centro.html (NSE C/C+) + dashboard_valle_poniente.html (NSE A premium)
# Regla: VOLVER A ESTA LISTA tras cada corrección. Revisar 2 veces antes de entregar.
#
# Referencias:
#   Centro: sweet $4.88M (Centro Activo), 6 productos, pm2 $26k-$90k, NSE C/C+
#   Valle Poniente: sweet $14.91M, productos $2M-$37M, pm2 $48k-$150k, supply-driven en tope, NSE A


# ════ DECISIÓN HÉCTOR (regla de percepción de valor, ya establecida) ════
# La ISÓCRONA determina la ZONA (quién llega físicamente). La PERCEPCIÓN DE VALOR
# determina el VALOR DEL PRODUCTO según la zona. La percepción de valor DOMINANTE
# predomina (el valor de vivienda que más se observa/vende), y PUEDE AUMENTARSE si
# existe EVIDENCIA DE OFERTA en valores superiores. El NSE/sweet spot del producto
# vertical se ancla a esta percepción de valor observada en la oferta (VVV), NO solo
# a la demografía de la isócrona. Demografía = demanda; Oferta = percepción de valor.
# Caso: Valle Poniente (demografía diluida a D+, pero oferta vertical premium $142k/m²
# → producto debe reconocer percepción de valor A premium).

## V. REGLA DE PERCEPCIÓN DE VALOR (opción 2)
- [x] V1. NSE/percepción dominante del PRODUCTO se ancla al valor de vivienda observado en la oferta (VVV), no solo demografía
- [x] V2. Percepción puede AUMENTAR si hay evidencia de oferta en valores superiores
- [x] V3. Centro sigue medio (C/C+); Valle Poniente vuelve a premium (A) tras la regla
- [x] V4. La demografía (isócrona) sigue determinando la DEMANDA; la oferta determina la PERCEPCIÓN DE VALOR

═══ PARTE 1 · VALIDACIÓN (vs Centro + Valle Poniente) ═══

## A. PRODUCTO — mostrar TODOS (opción 3)
- [x] A1. Muestra TODOS los productos (incl. oceano_rojo, bajo_crecimiento)
- [x] A2. Incluye SUPPLY-DRIVEN (oferta+absorción sin demanda DIM)
- [x] A3. Campos completos (tipo..perfiles)
- [x] A4. Status válidos
- [x] A5. Sin N/D ni 0 indebido en m2/pm2/ticket
- [x] A6. Sweet spot anclado al NSE dominante por convergencia
- [x] A7. Absorción realista
- [x] A8. pm2 coherente con vertical y NSE (Centro $26-90k; VP $48-150k)

## B. DEMANDA POR PERFIL
- [x] B1. demanda_segmentos por PERFIL real (no status)
- [x] B2. Campos: segmento, perfil, nse, ticket, m2, abs, mix
- [x] B3. Clasifica por segmento de mercado (perfil)

## C. OFERTA CLASIFICADA POR SEGMENTO
- [x] C1. inventario_m2
- [x] C2. inventario_precio
- [x] C3. Oferta por segmento DPO (evidencia vend/disp)
- [x] C4. Resta demanda-oferta → status

## D. SLIDERS Y FUNCIONES INTERACTIVAS
- [x] D1. Slider Producto (updateSensi)
- [x] D2. Mezcla VENTA (6 modos)
- [x] D3. Mezcla RENTA (6 modos)
- [x] D4. Monitor (import + analysis)
- [x] D5. Slider Renta (updateRenta)

## E. FORMATO MÉXICO
- [x] E1. Miles con coma
- [x] E2. Signo $ correcto
- [x] E3. m²/%/mes/un con unidad
- [x] E4. Nada de $undefined/NaN/null

## F. COMERCIO
- [x] F1. Inquilino (tenant con marcas)
- [x] F2. Categoría (giro) ≠ tenant
- [x] F3. Renta $/m²/mes según ventas
- [x] F4. anchor identificado
- [x] F5. ingreso_anual, gla_target, renta_low/high

## G. CONSISTENCIA (Centro + Valle Poniente)
- [x] G1. Centro: sweet medio (C/C+), pm2 $26-90k, sin N/D
- [x] G2. Valle Poniente: sweet premium (A), pm2 $48-150k, supply-driven tope, sin N/D
- [x] G3. segments con origen; totals; mercado_meta
- [x] G4. verify_all 10/10 + formato OK + interactive 0 errores

═══ PARTE 2 · ARQUITECTURA (prep 3 secciones nuevas) ═══

## M. MODULARIZACIÓN BACKEND POR SECCIÓN
- [x] M1. Cada sección en su módulo Python (demografía, inventario, demanda, producto, renta, comercio, mezcla, monitor)
- [x] M2. Orquestador central que ensambla
- [x] M3. app.py mismo contrato de salida tras modularizar
- [x] M4. verify_all 10/10 tras modularización (sin regresión)

## N. GUARDAR ESCENARIO
- [x] N1. Guardar escenario en mezcla VENTA
- [x] N2. Guardar escenario en mezcla RENTA
- [x] N3. Guardar escenario en Monitor
- [x] N4. Escenarios persistentes (storage) sin romper render

## O. CUENTAS Y CONTROL DE ACCESO
- [x] O1. Backend prep para generar cuentas
- [x] O2. Acceso por SECCIÓN (habilitable)
- [x] O3. Acceso por ZONA (autorizada/no)
- [x] O4. Acceso GENERAL preliminar disponible aunque DETALLE restringido
- [x] O5. Lógica que filtra payload según permisos (detalle vs preliminar)

## P. PREP 3 SECCIONES NUEVAS (andamiaje)
- [x] P1. Registro de secciones extensible (vivienda_horizontal, lotes, explorador)
- [x] P2. Documentar cómo agregar una sección

═══ DECISIÓN HÉCTOR (jun · opción 2) ═══
REGLA PERCEPCIÓN DE VALOR (ya establecida, re-confirmada):
- La ISÓCRONA determina la ZONA de influencia (quién puede llegar).
- La PERCEPCIÓN DE VALOR determina el VALOR del producto según la zona.
- La percepción de valor DOMINANTE predomina (el nivel de precio donde converge
  la mayor masa de oferta vertical observada en VVV).
- Puede AUMENTARSE si existe EVIDENCIA de oferta a niveles superiores.
- Esto resuelve el mercado dual: la demografía dice "quién vive cerca",
  la oferta vertical dice "para quién se construye realmente".

## V. PERCEPCIÓN DE VALOR ANCLA EL PRODUCTO
- [x] V1. NSE dominante de PRODUCTO se ancla al valor de vivienda observado en oferta vertical (VVV), no solo demografía isócrona
- [x] V2. Percepción dominante = bucket con mayor masa de oferta vertical real
- [x] V3. Puede elevarse con evidencia de oferta a niveles superiores (techo por evidencia)
- [x] V4. Centro vuelve a sweet medio C/C+ (~$4.88M ref); VP vuelve a premium A (~$14.91M ref)


═══ ZONA DE INFLUENCIA REAL · DETECCIÓN UNIVERSAL DE MERCADOS (jun · implementado) ═══
REGLA: La isócrona define quién llega; los datos de oferta deciden si dentro hay UNO o
VARIOS mercados. Si una barrera (física, de NSE del AGEB, o de percepción de valor) parte
la zona, la zona de influencia REAL es el MERCADO DEL PIN (el cluster compatible con el
predio), no toda la isócrona. El código detecta el EFECTO de la barrera en los datos; NO
usa el río ni ninguna barrera física como variable. Universal para todo México.

## ZIR. ZONA DE INFLUENCIA REAL (backend: módulo "Detección de mercados")
- [x] ZIR1. Clustering k-AUTO (k=2,3) sobre señales ponderadas normalizadas
- [x] ZIR2. Señales: ticket/unidad 0.40 · pm² 0.30 · posición-al-pin 0.30 (renormalizadas)
- [x] ZIR3. Validación robusta: gap≥0.85 Y var_explained≥0.35 Y masa≥3 por cluster
- [x] ZIR4. Salvaguardas anti-falso-positivo: CV global≥0.12, sep_medias≥0.18, sep_espacial
- [x] ZIR5. Zona morada = MERCADO DEL PIN (centroide=pin), no "el de mayor valor"
- [x] ZIR6. Conserva regla de elevación de percepción de valor (V1–V4) intacta
- [x] ZIR7. Integridad: sin datos suficientes → isócrona; hull solo si ≥3 puntos
- [x] ZIR8. Backend universal; el front solo dibuja zona_poligono + muestra mercados{}
- [x] ZIR9. Validado con pin 25.66108,-100.45263: 2 mercados, morado=oeste $63,881/m² (8 proy)

## PENDIENTES (requieren información externa)
- [ ] PEND1. 4ª SEÑAL NSE DEL AGEB · georreferenciación por CVEGEO.
        Cada AGEB trae CVEGEO (id INEGI), pero NO trae coordenadas/geometría en el
        Excel de DescargaDI. Falta el endpoint PRSP que devuelve geometría/centroide
        de AGEB por CVEGEO (PRSP no expone /docs ni /openapi.json; rutas probadas → 404).
        GANCHO LISTO: fetch_ageb_geometria(cvegeo_list) devuelve {} hoy; nse_rank por
        proyecto = N/D; SIGNAL_WEIGHTS["nse"]=0.0. Al tener la doc: implementar la
        consulta, parsear centroide, subir peso NSE (~0.15) y renormalizar. NO requiere
        reescribir el clustering.
        ACCIÓN HÉCTOR: compartir documentación/endpoint PRSP de geometría AGEB por CVEGEO.


═══ MODELO DE 3 ZONAS · COMPETIDORES Y DEMANDA (jun · implementado) ═══
REGLA: 
- ZONA MORADA (independiente) = mercado del pin = COMPETIDORES DIRECTOS (oferta primaria a comparar).
- ZONA AZUL (8 min) = primaria → COMPETIDORES PRIMARIOS.
- ZONA VERDE (14/18/24 según tamaño) = secundaria → COMPETIDORES SECUNDARIOS.
- DEMANDA = azul + verde combinadas. INVENTARIO/KPIs = azul + verde combinadas.
- El morado YA NO recorta el inventario (antes sí); ahora solo define el set directo.

## C3Z. MODELO 3 ZONAS
- [x] C3Z1. Oferta VVV + demografía se traen del anillo MAYOR (azul+verde combinadas)
- [x] C3Z2. clasificar_competidores: directo(morado) / primario(azul) / secundario(verde)
- [x] C3Z3. Morado independiente (point-in-polygon real), anclado a base_ring para detección
- [x] C3Z4. Inventario/KPIs usan universo completo; morado NO recorta inventario
- [x] C3Z5. Front dibuja 3 sets con colores; morado con bringToFront() (fix visibilidad)
- [x] C3Z6. Degrada bien sin verde (predio <1500 → secundarios=0)
- [x] C3Z7. Validado pin: directos=6, primarios=14, secundarios=8, AGEBs demanda=54
- [x] C3Z8. Integridad: proyectos sin coords se omiten (no se inventan)


═══════════════════════════════════════════════════════════════════
BACKLOG MAESTRO POR FASES (jun · registrado, NO empezar 2/3 antes de 1)
═══════════════════════════════════════════════════════════════════

── FASE 1 · ARREGLAR REGRESIONES + VARIABLES NOMBRADAS ──  [COMPLETA ✓]
Universo Inventario/Demanda/Producto/Mezclas = LOS 3 SETS (azul+verde+morado).
Fórmula runbook (canónica): Absorción individual = nuevas_familias/año ÷ 12 × captación.
Profundidad = hogares del segmento (depth). Ritmo = nuevas_familias/año (flow).
Verificación de cada sección: verify_all 8/8 + render 10/10 + verify_interactive 16 OK.

- [x] F1.0 ANALYSIS_VARS · build_analysis_vars (backend) + z._vars + window.ANALYSIS_VARS +
        getVars() (front). Fuente única desde el PIN: isócronas, 3 sets, universo, ingreso
        real, segmentos granulares, productos, sweet spot. (28 universo, ingreso $313,977).
- [x] F1.1 MAPA · basemap Esri World Imagery (satélite)+etiquetas; isócronas azul/verde +
        zona morada bringToFront; marcadores por 3 sets (directo/primario/secundario) vía
        getVars; filtros+leyenda por set. (harness: 28 marcadores 6+14+8, satélite, morado).
- [x] F1.2 INVENTARIO · backend _build_typologies agrupa tipologías por proyecto (TYPOLOGIES),
        filtra SOLO los 28 proyectos de los 3 sets, expone _typologies; front hidrata.
        211 tipologías reales. Preventa precio_ud=None (nunca 0). (62→28 proyectos).
- [x] F1.3 DEMANDA · datos granulares por AGEB (NSE, IXH mensual, rangos demanda, demanda
        anual real). NO promediar. Eliminada redistribución artificial. Ingreso=IXH real del
        NSE dominante. Buckets fuera de oferta vertical marcados aplicable:false.
- [x] F1.4 PRODUCTO · absorción = fórmula canónica nuevas_fam/12 × captación (validada en
        Valle Poniente). Reemplazado cálculo heurístico (cuotas/penalizaciones/elasticidad).
        Sync perfecto con Demanda (nuevas_fam coincide bucket a bucket). Campos depth/flow/
        abs_num/nuevas_fam_year para el slider. (sync ✓ 9 buckets, tplProducto 7 productos).
- [x] F1.5 MEZCLAS (venta y renta) · getActiveMix/getActiveMixRenta usan getDemandDrivenProducts
        (misma fuente que Producto). recomendado respeta aplicable → buckets sin oferta vertical
        NO entran a la mezcla. Front renta filtra recomendado en live. (venta 6, renta 6).
- [x] F1.6 MONITOR · restaurada función de alimentar proyecto: origen "Cargar proyecto del
        inventario" con selector de los 28 comparables; monitorLoadProject carga el mix REAL
        de tipologías (precio/m²/rec/uds) desde TYPOLOGIES, omite preventa sin precio. Análisis
        competitivo corre con el mix (±15% precio, ±30% m², ±1 rec). (Jardín Secreto→5 tip→18 comp).
- [x] F1.7 DEMANDA muestra no-aplicables · Tabla 3 muestra TODOS los buckets; los fuera de
        rango de oferta vertical se marcan "N/A · fuera de rango" (atenuado + leyenda), el resto
        "✓ con oferta". Tabla mapeo (Producto): acción "Fuera de oferta vertical" + badge N/A.
        CSV con columna Oferta Vertical. Dato de demanda intacto. (2 N/A + 7 con oferta).


── FIX · TAMAÑO DE PRODUCTO ANCLADO AL PROGRAMA (regla DPO documentada) ──  [HECHO ✓]
- [x] BUG: derive_productos_venta/renta hacían m² = ticket/pm², produciendo metrajes
        absurdos (28 m² studios para vivienda económica NSE C/D+) aunque el precio fuera
        correcto. Detectado con pin 25.79989,-100.45898 (NSE D+).
- [x] REGLA documentada (reportes Valle Poniente V2 / Calzada): el tamaño se ancla al
        PROGRAMA DE RECÁMARAS del ticket (banda habitable real), el pm² se deriva como
        ticket/m². Bandas: ≤1.5M→45-58 1R · ≤3.5M→62-80 2R · ≤8M→80-110 2R · ≤12M→105-140
        3R · ≤18M→135-180 3R · ≤25M→180-260 3-4R · >25M→260-360 4R PH. Posición en banda
        según NSE. m² observado real de la base manda si existe (integridad).
- [x] Recámaras ancladas al TICKET (monotónicas), no solo al m² (evita no-monotonías).
        Aplicado a venta Y renta. Verificado: VP $20M→219 m² 3-4R (doc: 240 Sky-Residence),
        $28.75M→304 m² PH (doc: 320 Grand PH); pin NSE D+ $1.12M→50 m² 1R (antes 28 m²).
        Integridad post-fix: nf 9/9, abs 8/8, pm2==ticket/m2 9/9, recomendado⊆aplicable ✓.
        verify_all 8/8+10/10, verify_interactive 16 OK.


── TABLERO MULTI-PRODUCTO · SELECTOR DE MODO ──  [EN CURSO]
- [x] PASO 1 · Ruteo backend por modo (req.producto). PRODUCTO_MODES con 7 modos
        (vivienda_vertical y vivienda_horizontal activos; lotes/industrial/logistica/
        oficinas/hotel declarados, devuelven no_disponible). Pipeline demográfico COMÚN
        (isócronas/DI/percepción/competidores/segmentos/comercio se ejecuta una vez);
        bifurca solo en (1) capa de oferta (vv_venta vs vh_venta) y (2) función de
        producto. Óptimo en RAM: un solo pipeline, dos puntos de ruteo. Renta solo en
        vertical. Capa horizontal descubierta en API: vh_venta (área construcción+terreno,
        demanda V CASAS). Verificado: vertical intacto, horizontal trae vh_venta (universo
        propio), lotes→no_disponible. verify_all 8/8+10/10, interactive 16 OK.
- [x] PASO 2 · Selector front en topbar (7 modos, 2 activos). CURRENT_PRODUCTO +
        setProductoMode; body de procesar/poligono envía producto. Cambiar de modo
        invalida análisis vigente (fuerza regenerar con la capa correcta). Modos no
        activos muestran aviso "en preparación" sin cambiar estado. Verificado (selector
        OK, render 7/7, sin regresión).
- [x] PASO 3 · derive_productos_horizontal IMPLEMENTADO: réplica fiel de venta (absorción
        canónica nuevas_fam/12, anclaje al programa por ticket, recomendado⊆aplicable) con
        variables de CASA: dos áreas (ÁREA_CONSTRUCCIÓN principal + ÁREA_TERRENO), bandas de
        casa (2 Rec 55-95m² → 4 Rec+ 280-400m²), pm² construcción propio por NSE, ratio
        terreno/construcción por NSE, m² observado real de vh_venta manda. Programa arranca
        en 2 Rec (no studios). Verificado VP: $8.5M→212/150 (=Los Cenizos real), $12.5M→270
        (=Privada Encinos). Integridad: abs 8/8, pm2=ticket/m2 8/8, recom⊆aplic, terreno 8/8,
        renta=0, featured≤1. 8/8+10/10+16 OK.
- [ ] PASO 4 · _build_typologies y demanda horizontal (V CASAS) propias del modo.
- [ ] PASO 5 · Adaptar secciones front (Inventario/Producto) a campos horizontales
        (terreno+construcción) cuando el modo es horizontal.


── BARRERA DE NSE EN ZONA DE INFLUENCIA · HABILITADA POR DATOS ──  [EN CURSO]
- [x] Verificado: la consulta de zona (di/export) ya devuelve geometría georreferenciada
        por AGEB en el KMZ del mismo ZIP (sin red extra). No depende de endpoint nuevo.
- [x] parse_di_geometria: extrae del KMZ por AGEB → centroide (lng,lat) + NSE ordinal
        (nse_rank) + NSE textual. 21/21, 60/60, 134/134 en pruebas. Integrado al pipeline
        (mismo di_bytes), expuesto en _zona_analisis.agebs_geo. import re a nivel módulo.
- [x] _nse_separacion_espacial + _nse_barrier_info extendida: combina COMPOSICIÓN (XLSX:
        qué NSE y cuánto) con SEPARACIÓN ESPACIAL (KMZ: dónde). Barrera real solo si hay
        mezcla relevante Y frontera espacial (ratio dist-centroides/dispersión ≥ 1.0).
        Verificado discrimina bien: Tepic ratio 0.31→no barrera (homogéneo disperso),
        VP ratio 1.81→barrera (premium separado de popular). verify_all 8/8+10/10, 16 OK.
- [x] INTEGRADA: value_perception_adjust evalúa _zona_por_barrera_nse cuando la oferta NO
        detecta barrera. Si hay frontera espacial de NSE → metodo='barrera_nse', zona_poligono=
        hull del bloque de NSE del pin. Competidores: con barrera_nse se clasifican por isócrona
        (la barrera recorta DEMANDA, no el set de oferta). Verificado: VP recorta 14 vs 63 pts
        (barrera_nse), Tepic/D+Mty mantienen isócrona. 8/8+10/10+16 OK.

── FASE 2 · CUENTAS, PERFILES Y AUDITORÍA ──  [SIGUIENTE]
- [ ] F2.1 Sistema de cuentas de usuario con credenciales (alta/baja/edición).
- [ ] F2.2 Perfiles de acceso (qué secciones ve cada perfil; front muestra/oculta por atributo).
- [ ] F2.3 Auditoría de cuentas y credenciales (log de creación/cambios/accesos).
- [ ] F2.4 Persistencia real de cuentas (hoy _CUENTAS en memoria, se pierde al reiniciar).
        Base ya existente: _CUENTAS, /api/cuentas, filter_payload_by_access, /api/zona/procesar_auth.

── FASE 3 · PERSISTENCIA, EXPORTAR/COMPARTIR + BASE DE DATOS ──
- [ ] F3.1 Sistema de base de datos (definir motor: SQLite/Postgres en Render).
- [ ] F3.2 Cada sección con funciones GUARDAR / EXPORTAR / COMPARTIR (backend preparado).
- [ ] F3.3 Modelo de datos: análisis guardados, escenarios, mezclas, por usuario/zona.

── FASE 4 · SECCIONES NUEVAS (SOLO DESPUÉS DE 1-3) ──
- [ ] F4.1 vivienda_horizontal · F4.2 lotes_urbanizados · F4.3 explorador_nacional

PENDIENTE EXTERNO (no bloquea): PEND1 endpoint geometría AGEB por CVEGEO (4ª señal NSE).
ACCIÓN HÉCTOR: compartir doc del endpoint cuando esté disponible.

── PASO 5 · FRONT DE CASA + HERRAMIENTAS · COMPLETADO ──  [HECHO]
- [x] tplProducto/openProductDetail: tarjeta "Tamaño" ahora condicional. Si el producto trae
        m2_terreno (horizontal) → muestra "Construcción" + valor + "Terreno: Xm²". Si no
        (vertical) → "Tamaño" normal. Verificado bloque aislado: H=Construcción+Terreno+212,
        V=Tamaño+58 sin terreno. El bloque vive en openProductDetail (modal de detalle), no en
        tplProducto (lista) — por eso el harness inicial probaba la función equivocada.
- [x] CONFIRMADO: "crea tu mezcla" (tplMezcla) y "monitorea el precio" (tplMonitor) SÍ están
        en el código y RENDERIZAN con datos en vivo (tplProducto 70063ch, tplMezcla 22716ch,
        tplMonitor 8211ch). Páginas page-mezcla/page-monitor registradas. NO desaparecieron del
        código; si no se vieron en deploy fue problema de navegación/render runtime.
- [x] Front completo compila (node --check OK). Guardado a outputs (static + raíz).

── VALIDACIÓN MASIVA JALISCO + NUEVO LEÓN · COMPLETADA ──  [HECHO]
- [x] COBERTURA: 21 zonas con oferta vh_venta confirmada (>16 pedidas). JAL: Zapopan,
        Zapopan Norte, Tlaquepaque, Tonalá, Tonalá Oriente, Tlajomulco, El Salto, Ocotlán.
        NL: San Pedro, Apodaca, Escobedo, Santa Catarina, García, García Sur, Juárez,
        Pesquería, Salinas Victoria, Ciénega de Flores, Cd Benito Juárez, Allende, Linares.
- [x] 92 PUNTOS ALEATORIOS validados (>80 pedidos), 2 modos c/u = 208 análisis ejecutados.
        Horizontal: 91 OK / 0 fallos de regla / 0 errores de código / 13 sin oferta.
        Vertical (control): 34 OK / 0 fallos / 0 errores / 70 sin oferta. Tasa éxito 100%.
- [x] 10 REGLAS DE NEGOCIO verificadas por punto, CERO violaciones: R1 NSE de zona presente,
        R2 zona de influencia (método+polígono), R3 barrera NSE espacial, R4 demanda con
        segmentos, R5 absorción=nuevas_fam/12, R6 pm2=ticket/m2 (construcción en horizontal),
        R7 recomendado⊆aplicable, R8 casa sin studios/1rec y sin renta, R9 un featured,
        R10 tamaños 25-500 m².
- [x] HERRAMIENTAS en vivo (horizontal): "crea tu mezcla" recibe productos de casa con
        terreno + recomendados; "monitorea el precio" recibe competidores + inventario por
        bucket. Confirmado con datos reales en Zapopan Norte y Apodaca.

── CORRECCIONES SISTÉMICAS · PIN 25.83721,-100.35195 (General Escobedo NL) ──  [HECHO]
Causa raíz: el front mostraba escenario previo (Valle Poniente) y campos en español vacíos,
y el backend tenía errores metodológicos. Corregido en backend (front solo lee):

1. IDENTIFICACIÓN DE ZONA: _derive_ubicacion extrae Municipio/Estado reales de los AGEBs
   (campos 'Municipio'/'Estado' de la base). name/subtitle/municipality salen de datos reales;
   sin AGEBs quedan None (front en blanco). Expuesto en _vars (municipio/estado/pais).
2. LABEL POR MODO: _zone_label refleja el modo real (no "vivienda vertical" fijo) y los KPIs
   reales; si no hay oferta dice "sin oferta en comercialización".
3. ZONA SIN VALOR PERCIBIDO: flag sin_valor_percibido + nota_valor cuando no hay oferta
   comparable ("la zona no tiene un valor preestablecido rígido...").
4. ABSORCIÓN REALISTA: _absorcion_realista reparte la demanda mensual entre competidores
   (+ techo de 6 un/mes por proyecto). Corrige absorciones irreales (28→6). Aplicado a
   vertical Y horizontal.
5. PRODUCTO ALINEADO A CAPACIDAD DE PAGO: el bucket inferior (val_min=0) ya no usa el techo
   del bucket como precio; usa la capacidad de pago real (ingreso×12×4.5). En El Carmen NSE D+
   el producto pasó de $1.12M a $0.54M (coherente con IXH 12,176).
6. NSE DEL SEGMENTO POR INGRESO REAL: nse_by_ingreso clasifica el NSE del segmento por el IXH
   real de sus hogares (quién compra), no por el precio de la vivienda. Corrige "NSE C en zona D".
7. DETALLE DEMOGRÁFICO REAL: _build_di_detail genera tipo_vivienda, situación conyugal,
   tipología de hogar y población en hogares desde los AGEBs (no el DI_VP_DETAIL hardcodeado).
   Front conectado: usa data.dim_data.di_detail en vivo; la tabla se muestra con ese dato.
VALIDADO EN JALISCO: Zapopan (387k hab, 14 proy), Tonalá (235k hab, 7 proy) — ubicación,
absorción y producto correctos. verify_all 8/8+10/10, interactive 16 OK.

── VALOR DE ZONA EN CASCADA · REGLA DE NEGOCIO RESTAURADA ──  [HECHO]
Regla: la sección "zona de análisis" SIEMPRE muestra un valor, exista o no oferta.
- _valor_zona_cascada (backend): directos → primarios → secundarios → percepción de valor
  por NSE/capacidad de pago. NUNCA devuelve None. Cada nivel usa datos reales; si un nivel
  no tiene datos, baja al siguiente. Devuelve pm2, ticket_ref_M, m2_ref, fuente, rigidez, nota.
  Niveles 1-3 = "mercado_establecido"; nivel 4 = "indicativo" (lo afina la demanda+calidad).
- Integrado en zona_procesar: perception.valor_zona + perception.media se completan con la
  cascada cuando no hay clúster. El nivel 4 toma pm²/ticket del producto recomendado (ya
  anclado a capacidad de pago). Expuesto en _zona_analisis.perception.valor_zona.
- Front (zaApplyBackendPerception + zaRenderResults): la tarjeta "Zona de influencia real"
  muestra "Valor de zona ($/m²)", ticket de referencia y fuente. "Percepción de valor" ya no
  dice "0 comparables / N/D": cuando no hay comparables, muestra el valor por percepción de
  valor con la nota de que es indicativo.
- VALIDADO NL y JAL: Escobedo sin oferta → $8,852/m² indicativo; Valle Poniente → $47,170
  directos; Tonalá → $20,000 directos; rural Jalisco → $14,603 indicativo. verify 8/8+10/10+16.

── SECCIÓN "DEMANDA" NO RENDERIZABA · CAUSA RAÍZ Y FIX ──  [HECHO]
Síntoma: "Demanda" aparecía vacía pero Producto/Renta/Comercio/Mezcla/Monitor sí mostraban
datos. Causa raíz: NO era falta de datos (el backend SÍ enviaba demanda real). Era un campo
null que hacía truncar TODA la sección al hacer .toFixed()/.toLocaleString() sobre null:
  • DI_VP_DETAIL.personas_hogar.no_familiares era None → .toFixed(2) tronaba tplDemanda entera.
  • z.kpis.unidades era null (sin oferta) → .toLocaleString() tronaba tplInventario entera.
Una sección que truena se queda en blanco; las demás (que tronaban en otra tabla o no) seguían.
FIX:
1. BACKEND: _build_di_detail calcula personas_hogar.no_familiares REAL desde "Población no
   familiar total" / "Hogares no familiares totales" (antes None). familiares idem.
2. FRONT (defensivo, sin lógica de negocio): proteger .toFixed()/.toLocaleString() con guardas
   !=null → 'N/D' en personas_hogar (×3), z.personas_hogar y kpis.unidades. Un campo faltante
   ya NO tumba una sección completa.
CONSISTENCIA VERIFICADA: sin demanda real → 0 productos (no inventa). Pin usuario: 1 segmento
real → 1 producto. Zona despoblada: 0 demanda → 0 producto. La cadena demanda→producto es
consistente; el problema era de render, no de datos inventados.
VALIDADO NL (Escobedo) y JAL (Tonalá): TODAS las secciones renderizan, Demanda incluida
(49k y 52k ch). verify_all 8/8+10/10, interactive 16 OK. NO se tocó "zona de análisis".

── PLACEHOLDERS HARDCODEADOS ELIMINADOS DE RAÍZ (Valle Poniente / {{}} / "62") ──  [HECHO]
Causa raíz definitiva: estos textos NO estaban en el flujo de datos; estaban escritos a mano
(hardcodeados) en el HTML estático y nunca se reemplazaban. Por eso sobrevivían a cada arreglo
del backend. Eliminados uno por uno:
1. <title> (línea 14): quitado {{ZONE_NAME}}.
2. Footer sidebar (774): {{ZONE_NAME}}·{{ESTADO}} → id="sb-footer-zona" dinámico.
3. Breadcrumb topbar (791): "Valle Poniente" → id="topbar-zona" dinámico.
4. Badge ubicación (807): {{ZONE_NAME}}·{{MUNICIPIO}} → id="topbar-ubicacion" dinámico.
5. Tags topbar (808-809): "14 proyectos / 1,770 unidades" → ids dinámicos.
6. ZONE_KEY_PLACEHOLDER (871) — ORIGEN DEL "62": objeto gigante de Monterrey/Valle Poniente
   (62 proyectos, 9,240 uds, productos, rentas) → objeto VACÍO con estructura mínima (todo
   null/N/D/[]). Antes de un análisis el tablero ya no muestra Valle Poniente.
7. DIM_DATA_BY_ZONE (876), DI_VP_DETAIL (879), FORMA_ENTREGA_DATA (889): vaciados.
8. Comentario (1111), fallbacks de meta (2461-2467), placeholders de inputs (6240,6242): genéricos.
NUEVO: función zaUpdateChrome(z) actualiza topbar/footer/título con los datos REALES del backend
tras cada análisis (nombre, municipio, kpis.proyectos, kpis.unidades, subtitle).
switchZone ahora usa zaRenderAllSafe (render por sección tolerante) en vez de renderAllPages, para
que el estado inicial sin análisis no truene.
VERIFICADO: 0 placeholders {{}}, 0 "Valle Poniente", 0 "62 proyectos", 0 "9,240". Topbar con
datos reales (Tonalá · 7 proyectos · 818 unidades). verify_all 8/8+10/10, interactive 16 OK.
PENDIENTE PRÓXIMA SESIÓN: revisar "Absorción estimada" — el usuario dice que no cuadra con el
dato real en todas las secciones (revisar regla de negocio de absorción a fondo).

── ELIMINACIÓN DE RAÍZ DE DATOS DEMO VALLE PONIENTE / MONTERREY ──  [HECHO]
Reportado 7+ veces: encabezados "Valle Poniente", placeholders {{zone_name}}/{{estado}},
y el número "62" a la derecha de Resumen y Mapa. CAUSA RAÍZ: el HTML traía ~195 mil
caracteres de DATOS DEMO HARDCODEADOS de Monterrey (corredor Contry / Valle Poniente)
en objetos JS estáticos. Aunque en vivo se sobreescriben, cualquier fallo dejaba ver el demo.
SOLUCIÓN DEFINITIVA (no parche): se VACIARON por completo todos los objetos demo:
  • AMENIDADES_DATA, AMENIDADES_DATA_BY_ZONE
  • INVENTORY_DISTRIBUTION_CHARTS, INVENTORY_DISTRIBUTION_CHARTS_BY_ZONE
  • TYPOLOGIES_BY_ZONE (−139k chars: ~60 proyectos Monterrey), PROJECT_META_BY_ZONE (−40k)
  • DESIGN_TIERS_BY_ZONE, FORMA_ENTREGA_DATA_BY_ZONE, DI_DETAIL_BY_ZONE, PROFILE_CATALOG
Cero referencias a "valle_poniente" o nombres de proyectos Monterrey en el archivo.
Las guardas "CURRENT_ZONE==='valle_poniente'" se sustituyeron por condiciones basadas en
datos REALES (si el backend manda inventario/amenidades, se muestran; si no, no).
Robustez: TYPOLOGIES/PROJECT_META inicializan a {}; computeInventoryBands y los charts de
distribución protegidos contra INVENTORY_DISTRIBUTION_CHARTS=null.
EL "62": confirmado que venía del demo. Ahora Resumen y Mapa muestran kpis.proyectos REAL:
Escobedo (sin oferta) → "0 proyectos"; Tonalá (con oferta) → "7 proyectos". NUNCA "62".
NOTA: no pude verificar Render (dominio fuera de allowlist). Si el "62" persiste en
producción tras subir esto, es señal de que el deploy NO tenía el archivo más reciente.
VALIDADO NL (Escobedo) + JAL (Tonalá): 9/9 secciones renderizan. verify_all 8/8+10/10,
interactive 16. Correcciones previas (zona de análisis, demanda) intactas.

── ABSORCIÓN ESTIMADA · REGLA DE NEGOCIO DEFINITIVA (toda la app) ──  [HECHO]
Regla del usuario (confirmada): la absorción de un producto se deriva de la DEMANDA REAL
menos la oferta DIRECTAMENTE COMPARABLE producto-por-producto (ticket, $/m², programa
arquitectónico/recámaras, calidad-equipamiento). Aplicada en TODO el backend, no solo en
una sección.
IMPLEMENTACIÓN:
  • Eliminado _absorcion_realista y su TECHO FIJO de 6.0 (artificial). Sustituido por:
  • _abs_comparables_directos(ticket, pm2, rec, m2, ft): de las tipologías reales (campo
    Abs_Demanda del API), filtra las DIRECTAS = mismo programa de recámaras y ticket ±15% /
    pm² ±15% / m² ±20%. Sólo absorciones reales > 0. Helper _rec_to_int parsea '2 Rec'→2.
  • _absorcion_producto(nuevas_fam_year, abs_directos):
      - CON directos  → mediana real de los directos × 1.20 (VENTAJA_DISENO: vender ≥20% más
        rápido que la competencia directa). origen='comparables_directos'.
      - SIN directos  → captura 100% de la demanda mensual (nuevas_fam/12). Sin techo. Es la
        magia del proceso: segmento con demanda y sin competencia → producto dominante.
        origen='demanda_sin_competencia'.
      - Sin base → abs=None (N/D).
  • Aplicado en derive_productos_venta Y derive_productos_horizontal. Expuesto al front:
    abs_origen, abs_n_directos, abs_mediana_directos por producto.
  • FRONT (backend manda): en vivo, abs_base usa SIEMPRE p.abs del backend (ya aplica la
    regla); ya NO recae en el cálculo local nuevas_fam/12 cuando el backend da bajo. El front
    solo ajusta por sliders de captación; no recalcula la absorción base.
VALIDADO:
  - Escobedo (sin oferta): 28.8 un/mes = 345.8 fam/12, origen demanda_sin_competencia. ✓
  - Valle Poniente $15-25M: 4 directos, mediana 0.13 ×1.20 = 0.16, origen comparables_directos. ✓
  - Tonalá: '2 Rec $1.5-2.5M' 7 directos abs 1.9; '3 Rec $2.5-3.5M' 16 directos abs 1.1. ✓
verify_all 8/8+10/10, interactive 16. Demanda y zona de análisis intactas.

── ABSORCIÓN · FÓRMULA REFINADA (demanda mensual real + pool de mercado en venta) ──  [HECHO]
Correcciones del usuario sobre la regla anterior:
  1. "Demanda anual vivienda" ES anual → se divide /12 para volverla mensual (nf_mensual).
  2. Se incorpora la DEMANDA TOTAL = campo "Mercado en venta" (col. a la izq. de "Demanda anual
     vivienda" en el XLSX DI). Es el pool de compradores potenciales activos en venta del AGEB
     (≈5.1% de los hogares; 77 const por AGEB; Σ zona Escobedo=1616). Regula la velocidad en
     segmentos sobreofertados. NO es "Hogares totales 2026" (todos los hogares).
  3. Factor del pool calibrado a 0.075 (no 0.85). Resultado en rango comercial realista.
FÓRMULA FINAL (un/mes):
     nf_mensual   = nuevas_familias_anual / 12
     pool_mensual = (demanda_total × 0.075) / 12       (PCT_POOL_ACTIVO = 0.075)
     numerador    = pool_mensual + nf_mensual
       • CON comparables directos → abs = max(numerador, mediana_absorción_directos)
         (la mediana real de los directos es el PISO a superar)
       • SIN comparables directos → abs = numerador
       • abs = None si numerador ≤ 0 y sin directos
IMPLEMENTACIÓN:
  • derive_segments: demanda_bucket acumula "mercado_venta" (de col "Mercado en venta",
    ponderado por prop_casa en horizontal). El segmento expone demanda_total.
  • _absorcion_producto(nuevas_fam_year, demanda_total, abs_directos): aplica la fórmula.
  • Llamado en derive_productos_venta y derive_productos_horizontal con s["demanda_total"].
VALIDADO:
  - Escobedo horizontal (sin oferta): abs=38.9 un/mes = (1616×0.075)/12 + 345.8/12 = 10.1+28.8. ✓
  - Tonalá horizontal (con oferta): "2 Rec $1.5-2.5M" 7 directos mediana 1.55 → abs 1.6;
    "3 Rec $2.5-3.5M" 16 directos mediana 0.92 → abs 0.9. ✓
verify_all 8/8+10/10, interactive 16, 9/9 secciones renderizan.

── ABSORCIÓN · FÓRMULA FINAL (numerador del bucket − inventario competidor) ──  [HECHO]
Reescritura completa de la regla tras refinamiento del usuario. Reemplaza versiones previas.
NUMERADOR (anual, SOLO del bucket de precio comparable, renglón por renglón):
    numerador = Σ ( "Demanda anual vivienda" + "Mercado en venta" × 0.05 )
    sobre los AGEBs cuyo rango cae en ESE bucket (no el acumulado de la zona).
    PCT_POOL_ACTIVO = 0.05 (antes 0.075/0.85).
RESTA DE INVENTARIO COMPETIDOR (solo si hay comparables directos):
    • SIN directos → resultado = numerador
    • CON directos → resultado = numerador − Σ(UNIDADES_DISPONIBLES de tipologías comparables)
MENSUALIZAR: absorción = resultado / 12
    • numerador ≤ 0 (sin demanda en el bucket) → abs=None/N/D, origen "sin_demanda", NO se recomienda.
    • resultado ≤ 0 (inventario competidor ≥ demanda anual) → abs=0, origen "sobreofertado".
MEDIANA de absorción de los directos: ya NO entra al cálculo. Se devuelve y se MUESTRA a la
    derecha como dato de validación (producto ganador vs mediocre). Front: fila "Mediana
    competencia directa (n)" bajo "Absorción esperada (catálogo)".
IMPLEMENTACIÓN:
    • _abs_comparables_directos ahora devuelve {abs_vals (→mediana dato), disp_total (→se resta), n}.
    • _absorcion_producto(nuevas_fam_year, demanda_total, directos) aplica numerador−inventario, /12.
    • Producto expone: abs_origen, abs_n_directos, abs_mediana_directos, abs_inv_competidor.
    • FRONT: absDemand usa SIEMPRE extractAbsRate(p.abs) del backend; ya NO recalcula
      nuevas_fam_month×captureRate. Backend manda.
VALIDADO (NL+JAL):
    - Escobedo horizontal (sin oferta): numerador 345.8+1616×0.05=426.6 /12 = 35.5 un/mes. ✓
    - GDL centro "1 Rec <$1.5M": numerador−68 inv = 33.9 un/mes (demanda supera inventario). ✓
    - GDL "1 Rec $1.5-2.5M": numerador 22+pool − 112 inv < 0 → sobreofertado N/D. ✓
    - Tonalá buckets con directos pero demanda 0 → sin_demanda N/D (no recomendado). ✓
    - Zapopan "2 Rec $3.5-5M": 26 nf, 1 inv → 3.2 un/mes viable; "$5-7M" 133 inv → sobreofertado. ✓
verify_all 8/8+10/10, interactive 16, 9/9 secciones renderizan.
NOTA: PENDIENTES no iniciados → (1) programa arquitectónico gaussiano (edad+ocupantes por grupo
familiar → hogar más probable → diseño desde oferta como muestra); (2) regla de diseño según tope
de precio (tope bajo: −m²/+amenidades, mayor $/m²; capacidad alta: +m²/+calidad). Escala de buckets
puede bajarse a $200k (ideal) o $500k si un bucket queda sin demanda.

── ABSORCIÓN FLUJO-CONTRA-FLUJO + PRONÓSTICO 12/18/24 MESES ──  [BACKEND HECHO · FRONT PENDIENTE]
Refinamiento del usuario: la fórmula anterior restaba un STOCK (inventario disponible) de un
FLUJO (demanda mensual). Corregido a flujo-contra-flujo para un ritmo de venta realista del
proyecto nuevo, considerando que los competidores SIGUEN compitiendo.
ABSORCIÓN BASE (un/mes):
    demanda_mensual = ( Demanda anual vivienda + Mercado en venta×0.05 ) / 12   [del bucket]
    abs_competidores = Σ Abs_Demanda de comparables directos CON inventario disponible > 0
                       (los agotados ya no competirán a futuro; NO se cuentan)
    • SIN directos → abs = demanda_mensual
    • CON directos → abs = demanda_mensual − abs_competidores   (flujo contra flujo)
    · numerador_anual ≤ 0 → N/D, no recomendado (sin demanda en bucket)
    · abs ≤ 0 → sobreofertado (competencia activa consume toda la demanda)
    La mediana de Abs_Demanda de directos NO entra al cálculo → dato de validación (ganador/mediocre).
PRONÓSTICO acumulado a 12/18/24 meses (selector del front):
    ventas(N) = min( Σ mes=1..N [ abs × factor_curva(mes) ] , unidades_proyecto )
    Curva de maduración (tramos fijos): arranque m1–6 = 60% · consolidación m7–18 = 70% ·
    cola m19–24 = 20%. (RAMP_ARRANQUE/CONSOLIDA/COLA).
    Tope = unidades_proyecto (campo del front, ZonaRequest.unidades_proyecto). Devuelve acumulado,
    ritmo mensual, mes_agotamiento, topado.
    Competencia: mantiene su Abs_Demanda constante en el horizonte (conservador), traída SIEMPRE
    EN VIVO del API (ft de vvv/query) en cada análisis; verificado: sin caché ni hardcode.
IMPLEMENTACIÓN:
    • _abs_comparables_directos ahora devuelve abs_compet (Σ Abs_Demanda de directos con disp>0).
    • _absorcion_producto(nuevas_fam_year, demanda_total, directos, unidades_proyecto):
      demanda_mensual − abs_compet; arma pronóstico {12,18,24}. Helpers: _factor_curva,
      pronostico_ventas.
    • Producto expone: abs_competidores, abs_pronostico {12:{acumulado,mensual[],mes_agotamiento,
      topado},18,24}.
    • ZonaRequest +unidades_proyecto (Optional[int]). Propagado a derive_productos_venta/horizontal.
VALIDADO:
    - Escobedo (sin compet, 80 un): abs 35.5; pronóstico topa a 80 u, agota mes 4. ✓
    - Zapopan "2R $3.5-5M": compet agotados → abs 2.5, 32 u a 24m (ganador). ✓
    - Zapopan "1R $1.5-2.5M": demanda 5.7 − compet 5.31 = 0.4 u/mes (competencia activa). ✓
    - Zapopan "2R $5-7M": 72 compet, abs_compet 6.4 > demanda → sobreofertado N/D. ✓
verify_all 8/8+10/10, interactive 16, 9/9 secciones renderizan.
FRONT: helper global pronosticoRows(p) muestra el pronóstico acumulado a 12/18/24 meses en el
modal de detalle del producto (bajo la mediana y la absorción de competidores activos). Lee
p.abs_pronostico del backend; no recalcula. Verificado: genera filas 12m/24m con acumulado.
PENDIENTE FRONT MENOR: capturar "unidades del proyecto" como input editable que repopule el
análisis (hoy se pasa por ZonaRequest.unidades_proyecto; sin él el pronóstico es sin tope).

── PARTE A · PROPAGACIÓN DE LA ABSORCIÓN A TODOS LOS TABLEROS Y SECCIONES ──  [HECHO]
Objetivo: asegurar que la absorción flujo-contra-flujo + pronóstico funcione igual en vertical
venta, horizontal venta y renta, en las 4 secciones (Demanda, Producto, Mezcla venta/renta,
Monitor), sin arrastrar bugs de versiones previas. NADA de lo aprobado se eliminó.
DECISIONES DEL USUARIO:
  • Renta MANTIENE su lógica actual (nuevas familias que rentan/mes × propensión). NO se le
    aplica flujo-contra-flujo NI pronóstico (es ocupación estabilizada, no venta con agotamiento).
  • Slider de captación (10–100%) SE MANTIENE: modula la absorción para escenarios conservadores.
  • En Mezcla y Monitor, la absorción base de cada producto es la del BACKEND (p.abs), modulada
    por el slider: abs_base = p.abs (en vivo) → abs_demand = abs_base × captureRate.
AUDITORÍA DEL FRONT (cadena de absorción consistente):
  • getDemandDrivenProducts(captureRate) alimenta Producto/Mezcla/Monitor: en vivo
    (__DATARIA_LIVE__) abs_base = extractAbsRate(p.abs) del backend (sin recálculo local);
    fallback nuevas_fam/12 solo en preview no-vivo. abs_demand = abs_base × cr.
  • Producto (detalle): absDemand = extractAbsRate(p.abs) directo del backend.
  • Comentarios desactualizados (mencionaban "×1.20" de la versión vieja) corregidos a la
    fórmula vigente flujo-contra-flujo. Sin cambio de lógica.
VALIDADO:
  • Validación cruzada Zapopan: p.abs backend (1.3, 0.8, 2.4, N/D) = abs_base que consume Mezcla;
    con slider 100% abs_demand = p.abs. Sobreofertado → 0 sin recálculo.
  • Producto/Mezcla/Monitor renderizan en vivo. verify_all 8/8+10/10, interactive 16.
PENDIENTE → PARTE B (siguiente entrega): multi-programa por bucket de precio (1/2/3 rec del mismo
ticket → distinto m²/$m²/NSE/etapa de vida), filtrado por composición familiar real (gaussiano,
combina rec fijas 1/2/3 con lo que la zona justifique), cada escenario con su propia absorción
flujo-contra-flujo y pronóstico vs comparables directos de SU programa, agrupados en tranches de
$/m² por cuantiles de la oferta real. m² por bandas de recámaras ahora, refinado con gaussiano
después. Aplica en Producto, Mezcla venta/renta, Monitor.

── FIX · TABLERO EN BLANCO AL CARGAR (portada zona-análisis no renderizaba) ──  [HECHO]
SÍNTOMA: el tablero abría en blanco; "no carga zona de análisis".
DIAGNÓSTICO (causa raíz): la página de portada `page-zona-analisis` es la página .active por
defecto (línea ~821) pero NO estaba incluida en la lista de zaRenderAllSafe(); solo se renderizaba
en renderAllPages(). En el arranque (DOMContentLoaded → switchZone('ZONE_KEY_PLACEHOLDER') →
zaRenderAllSafe()), la portada nunca ejecutaba su template tplZonaAnalisis(z) y quedaba como
<div> vacío. El resto de páginas sí renderizaban pero estaban ocultas (no .active), de modo que
el usuario veía la portada en blanco.
VERIFICACIÓN del diagnóstico (no inspección visual): simulación del flujo DOMContentLoaded con
DOM mock → page-zona-analisis = 0 chars antes del fix; tplZonaAnalisis(placeholder) no truena
(template estático de captura, no depende de z) → seguro renderizarlo siempre.
FIX: agregar ['page-zona-analisis', tplZonaAnalisis] como PRIMER elemento de la lista de
zaRenderAllSafe(), dentro del mismo try/catch tolerante. Así la portada se rinde en cada
switchZone (incl. arranque). No se tocó renderAllPages ni la cadena de inicialización.
VALIDADO: simulación DOMContentLoaded → page-zona-analisis ahora 4940 chars con el formulario
"Ubicación del predio". Con payload real, 9/9 secciones renderizan. verify_all 8/8+10/10,
interactive 16. Las secciones sin datos (placeholder vacío) se aíslan con gracia (try/catch),
sin romper el render.

── FIX · "14" HARDCODEADO JUNTO A RESUMEN Y MAPA (badges del sidebar) ──  [HECHO]
SÍNTOMA: aparecía un "14" fijo a la derecha de "Resumen" y de "Mapa", sin importar la zona.
CAUSA RAÍZ (fuente común, no por sección): NO estaba en las secciones, sino en el SIDEBAR.
Dos <span class="sb-badge">14</span> hardcodeados en los ítems de menú "Resumen" (línea ~697)
y "Mapa" (~705). Valor estático sobrante de la demo vieja de Monterrey. Como el sidebar es fijo,
el "14" se mostraba en ambos ítems en cualquier zona. (Por eso reparar las secciones una a una
no lo resolvía: el número no venía de las secciones.)
FIX: se les quitó el "14" y se les dio id (sb-badge-resumen / sb-badge-mapa). zaUpdateChrome ahora
los puebla con el CONTEO REAL de proyectos del backend (kpis.proyectos); vacío cuando no hay
proyectos (portada / zona sin oferta), para no mostrar "0" ni un valor demo.
VALIDADO: zaUpdateChrome con zona de 7 proyectos → badges "7"/"7"; con 0 proyectos → vacíos.
Búsqueda confirmó que no quedan otros números fijos en badges del sidebar. verify_all 8/8+10/10,
interactive 16, Resumen y Mapa renderizan.

── FIX TRIPLE · PRODUCTO (N/D) + COMERCIO (estático) + MONITOR (precio recomendado) ──  [HECHO]

1) PRODUCTO · N/D en absorción inconsistente:
   CAUSA: productos con abs_origen sin_demanda/sobreofertado llegaban como recomendado=true con
   N/D. DECISIÓN usuario: mostrarlos pero marcados "no recomendable" con el motivo.
   FIX (backend): helper _recomendable_por_absorcion(abs_origen) → {recomendable, motivo}.
   sin_demanda → "Sin demanda en el rango de precio"; sobreofertado → "Sobreofertado ·
   competencia satura la demanda". recomendado y featured ahora exigen recomendable por absorción.
   Producto expone no_recomendable_motivo. Aplicado en venta y horizontal.
   FIX (front): la card de producto muestra el motivo (ámbar) en vez de "N/D" a secas.

2) COMERCIO · siempre mismos precios/giros/inquilinos (eran diccionarios fijos):
   DECISIONES usuario: (a) renta $/m² derivada del gasto real captable por m² de cada giro en la
   zona; (b) inquilinos por catálogo de NSE (premium/medio/popular), usando el MAYOR entre NSE
   demográfico y percepción de valor (híbrido); (c) solo giros con GLA captable ≥ 100 m².
   FIX (backend) derive_comercio(agebs, nse_dom_key, ft):
   • renta_m2 = (gasto×CAPTURA×CAPTABLE / m2_GLA) × 0.10 / 12  (renta ≈ 10% de ventas/m²/año).
   • TENANTS_POR_NSE {premium:A/B, medio:C+/C, popular:D+/D/E}; nivel por NSE efectivo = mayor de
     demográfico (_nse_dominante_agebs) y percepción (_nse_percepcion_valor(ft)).
   • giros_viables = captable ≥ GLA_MIN_VIABLE(100); fallback al mayor si ninguno llega.
   VALIDADO: Zapopan (oferta premium)→9 giros, inquilinos premium (City Market/Liverpool/Sonora
   Grill); Escobedo (popular)→1 giro, Bodega Aurrerá. Renta y giros distintos por zona.

3) MONITOR · botón de PRECIO RECOMENDADO que se había perdido (existía en tableros estáticos):
   REGLA (investigada en código, no inventada): precio recomendado $/m² = mediana de $/m² de los
   COMPARABLES DIRECTOS (mismo programa/ticket/tamaño). El producto se ancla al mercado observado
   (la ventaja de diseño se expresa en absorción ≥20% más rápida — VENTAJA_DISENO — no en
   sobreprecio, para no salir de la capacidad de pago). Veredicto caro/barato/en línea con ±5%.
   FIX (backend): _abs_comparables_directos ahora devuelve pm2_vals; _precio_recomendado_directos
   → pm2_recomendado y ticket_recomendado_M. PRECIO_TOL_VEREDICTO=0.05. Producto expone
   pm2_recomendado, ticket_recomendado_M, precio_tol_veredicto. Todo en el backend, por zona.
   FIX (front): botón "$ precio" por fila del mix en Monitor → monitorPrecioVeredicto(idx):
   busca el producto del backend que matchea (mismo programa, ticket ±25%), compara el $/m² del
   usuario contra pm2_recomendado y emite veredicto CARO/BARATO/EN LÍNEA (±5%). Sin match → aviso
   de "sin competencia directa comparable".
   VALIDADO: en línea ($3M/58m²=51.7k vs recom 51.1k) ✓; caro ($4M/58m²=69k) ✓.

verify_all 8/8+10/10, interactive 16, 9/9 secciones renderizan. Nada aprobado se eliminó.

── FIX · NOMBRE DE ZONA no usaba colonia/municipio/estado/país ──  [HECHO]
SÍNTOMA (usuario): "sigue sin mostrar el nombre de la zona usando la colonia municipio estado
país de la base de datos".
CAUSA RAÍZ: el backend armaba zone_name = municipio (derivado de AGEBs) e IGNORABA la colonia que
el usuario captura en el formulario. El XLSX DI solo trae Estado y Municipio (NO colonia); la
colonia la captura el usuario en za-colonia. El front enviaba zone_name=colonia||ciudad pero el
backend lo descartaba (zone_name = municipio or req.zone_name).
FIX (backend):
  • ZonaRequest: agregados campos colonia: Optional[str] y pais: Optional[str].
  • Nombre = colonia capturada → si no, municipio de la base → si no, req.zone_name. Subtítulo =
    jerarquía completa: si hay colonia → "Municipio · Estado · País"; si el nombre ya es el
    municipio → "Estado · País" (sin repetir). Integridad: lo ausente no se inventa (None).
FIX (front): el body de zona_procesar ahora envía colonia: gv('za-colonia')||null y pais:'México'
  además de municipio/estado. zaUpdateChrome ya usaba z.name/z.subtitle/z.municipality (topbar,
  footer, título); los títulos de sección usan ${z.name} y ${z.subtitle}.
VALIDADO: colonia "Providencia" → name="Providencia", subtitle="Zapopan · Jalisco · México";
sin colonia → name="General Escobedo", subtitle="Nuevo León · México"; "Centro" → name="Centro",
subtitle="Guadalajara · Jalisco · México". Topbar/footer/títulos confirmados.
PENDIENTE OPCIONAL (sugerido): reverse geocoding al hacer clic en el mapa para autodetectar
colonia/ciudad/estado desde el pin (hoy la colonia depende de captura manual; el XLSX no la trae).
verify_all 8/8+10/10, interactive 16, 9/9 secciones limpias.

── FIX · PRECIO RECOMENDADO (Monitor) daba N/D de más ──  [HECHO]
SÍNTOMA (usuario, reiterado): "la función de precio correcto sigue fallando".
CAUSA RAÍZ: _precio_recomendado_directos reutilizaba los comparables de _abs_comparables_directos,
que filtran por $/m² (±15%) Y exigen recámaras EXACTAS. Filtrar por $/m² es CIRCULAR (el $/m² es
justo lo que se va a recomendar) y recámaras exactas es demasiado estricto → "sin match" frecuente.
REGLA DE NEGOCIO CORRECTA (hallada en el tablero estático template_tablero_inmobiliario.html,
función findCompetitorsForMixItem): competidor directo de PRECIO =
  • inventario DISPONIBLE > 0 (solo lo que aún compite marca precio de mercado)
  • precio de unidad válido (> 100,000; N/D se descarta)
  • ticket dentro de ±15%
  • área dentro de ±30%
  • recámaras dentro de ±1
  • NO se filtra por $/m² (sería circular)
  precio recomendado $/m² = MEDIANA de los $/m² de esos directos; ticket rec = pm²_rec × m².
FIX (backend): _precio_recomendado_directos reescrita con firma (ticket_M, rec, m2, ft); recorre la
oferta real ft EN VIVO replicando esa regla. Constantes nuevas _PRECIO_TOL_TICKET=0.15,
_PRECIO_TOL_AREA=0.30, _PRECIO_TOL_REC=1. Independiente de la lógica de absorción (que mantiene su
filtro estricto por $/m² y recámaras exactas — son cosas distintas). Las 2 llamadas (venta y
horizontal) actualizadas a la nueva firma. PRECIO_TOL_VEREDICTO=0.05 sin cambios.
FRONT: monitorPrecioVeredicto / monitorBuscarPrecioBackend ya leen p.pm2_recomendado,
p.ticket_recomendado_M, p.precio_tol_veredicto; veredicto caro/barato/en línea ±5%; N/D legítimo
("sin competencia directa") bien manejado. Sin cambios necesarios.
VALIDADO: Zapopan 8/9 productos con precio recomendado ($48k–$121k/m², coherente); GDL Centro 6/8;
Escobedo NL → N/D (sin oferta vertical, integridad respetada). Veredicto end-to-end: en línea 0.0%,
caro +15.0%, barato -15.0%. verify_all 8/8+10/10, interactive 16, 9/9 secciones limpias.


# ════════════════════════════════════════════════════════════════════════════════
# MIGRACIÓN CÁLCULO FRONT→BACKEND (sesión migración · "nada procesado en el front")
# ════════════════════════════════════════════════════════════════════════════════
# REGLA: el tablero (front) SOLO muestra; TODO el cálculo de negocio vive en el backend.
# Auditoría detectó cálculo de negocio en el front en dos grupos. Ambos migrados.

## M1. TCA por segmento (inconsistencia real backend≠front) — [x] HECHO + VALIDADO en vivo
- Síntoma: computeDemandSegments (front) tenía tabla TCA hardcodeada {A:1.39,C+:1.66,C:1.70,
  D+:2.41,D:3.49} DISTINTA de la del backend {A:1.12,C+:1.39,C:1.03,D+:0.74,D:0.37}.
- Causa: el backend tenía la TCA correcta en nse_ranges (derive_nse_dim) pero NO la incluía en
  cada segment de dim_data.segments; el front la recalculaba con tabla propia errónea.
- BUG encontrado al corregir: el primer intento usó nse_ranges dentro de derive_segments, pero
  nse_ranges vive en derive_nse_dim (otra función) → habría dado NameError. CORREGIDO creando
  constante global NSE_TCA (módulo, junto a NSE_INCOME_BANDS) como FUENTE ÚNICA.
- FIX backend: NSE_TCA global; derive_segments añade "tca": NSE_TCA.get(nse_cls,0) a cada seg;
  derive_nse_dim referencia NSE_TCA en su tabla local (una sola fuente de verdad).
- FIX front: computeDemandSegments lee s.tca del backend (tca: s.tca!=null ? s.tca : null);
  eliminada la tabla tcaMap hardcodeada.
- VALIDADO en vivo (ZMM Centro, datos reales): tca por segmento = canónica (C=1.03, C+=1.39,
  B=1.0, A=1.12). Coincide exactamente con el backend.

## M2. Monitor · amenaza competitiva (trío del front) — [x] HECHO + VALIDADO end-to-end
- Eliminadas del front: findCompetitorsForMixItem, findMatchingSegment, computeCompetitiveThreat
  (calculaban competidores directos, threat ratio, demanda neta y estrategia sobre TYPOLOGIES).
- FIX backend: funciones nuevas _competidores_mix_item, _segmento_para_ticket, amenaza_competitiva
  (regla idéntica: ticket ±15%, área ±30%, rec ±1, solo inventario disponible y precio válido).
  Constantes _MON_TOL_TICKET=0.15, _MON_TOL_AREA=0.30, _MON_TOL_REC=1. Modelo MixEvalRequest
  (item único o items[] en lote). Endpoint POST /api/zona/evaluar_mix.
- FIX front: monitorFetchThreats(items,period,capture) llama al endpoint en lote (una sola llamada
  para todo el mix) enviando typologies=getTypologies() y segments=DIM_DATA.segments del payload;
  mapThreatFromBackend mapea snake_case→camelCase. renderMonitorAnalysis convertida a async.
  Sin backend → amenaza vacía (no recalcula negocio en el cliente).
- VALIDADO end-to-end (ZMM, 40 proy, 8 segs): 2Rec$3M→9 directos, seg C+, threat 0.68 monitorear;
  3Rec$8M→21 directos, seg A, threat 9.5 reposicionar; 1Rec$1.2M→0 directos, expansión. Render
  Monitor async 32135 ch limpio mostrando las 5 estrategias del backend.

## M3. Grupo 1 · percepción de valor en el front (código muerto) — [x] ELIMINADO
- Eliminadas del front (212 líneas): zaAjustarZona (CV precios, umbral CV_BARRERA=0.30, recorte a
  clúster de alto valor), zaConvexHull, zaPolyArea, zaCoberturaHullEnIso, zaStats, zaFetchValor,
  zaPointInPoly, zaPointInRing. Solo corrían en zaRunAnalysisLocal (rama "backend no configurado").
- El flujo vivo ya usaba zaApplyBackendPerception (lee cv, barrera, metodo, cobertura_pct,
  zona_poligono, competidores del backend). zaRunAnalysisLocal quedó como stub que informa que el
  análisis se procesa en el backend (no inventa datos locales).
- Front: 7779 → 7575 líneas. Sin referencias huérfanas. JS válido.

## M4. computeInventoryBands y getProjectAmenityScore — [x] LECTORES PUROS (pendiente backend)
- Operan sobre INVENTORY_DISTRIBUTION_CHARTS (init null) y AMENIDADES_DATA (init vacío) que el
  backend NO entrega en vivo → INERTES en producción (devuelven []/null con guarda, sin romper).
- DECISIÓN: se dejan como lectores puros (no inventan datos). PENDIENTE: que el backend entregue
  amenidades y bandas de inventario procesadas para que tengan datos que leer.

# VERIFICACIÓN FINAL MIGRACIÓN: backend compila, front JS válido, verify_all 8/8+10/10,
# verify_interactive OK, render 9/9 limpio (ZMM + Valle Poniente). Cero rastro de las funciones de
# cálculo migradas. TCA validada en vivo. Monitor async validado end-to-end con backend real.

## M5. Monitor · debounce de llamadas al backend — [x] HECHO + VALIDADO
- Tras migrar la amenaza competitiva al backend, cada edición de celda del mix (monitorUpdateRow)
  y cada movimiento del slider de horizonte (setMonitorPeriod, oninput) disparaba una llamada al
  endpoint /api/zona/evaluar_mix. Arrastrar el slider = decenas de llamadas/segundo.
- FIX front: timer _monitorDebounceTimer + renderMonitorAnalysisDebounced() (espera
  MONITOR_DEBOUNCE_MS=300 ms tras el último cambio y hace UNA sola llamada). monitorUpdateRow y
  setMonitorPeriod usan la versión debounced; la etiqueta del período se actualiza inmediata
  (feedback visual). Las acciones puntuales (add/remove/clear/import/load/source) siguen llamando
  a renderMonitorAnalysis() inmediato (un solo evento, respuesta instantánea).
- VALIDADO: 11 cambios rápidos (6 ediciones + 5 movimientos de slider) → 1 sola llamada al backend
  tras 300 ms; estado final correcto (último valor aplicado). Render Monitor sigue limpio.

## ZA1. Zona de análisis · Ponderación por proximidad del NSE dominante — [x] HECHO + VALIDADO
- REGLA (confirmada en sesiones previas): el NSE dominante = mayor masa de hogares, y el dominante
  es "el más accesible" desde el predio. Esta sesión: la accesibilidad se CUANTIFICA con distancia
  real al pin. Decisión del usuario: COMBINAR masa × factor de proximidad (ambos pesan); aplicar
  sobre la CAPACIDAD DE PAGO DEMOGRÁFICA (AGEBs más próximas al pin pesan más en NSE/ingreso).
- Condición: solo cambia el VALOR del NSE dominante; NO altera ninguna regla de negocio de ninguna
  sección (techo de inducción, percepción de valor VVV, demanda, buckets, absorción, multi-programa,
  precio del Monitor — todo intacto).
- BACKEND:
  • Nueva _factor_proximidad_por_nse(agebs_geo, pin_lng, pin_lat): por NSE, promedio de 1/(1+dist_km)
    de sus AGEB georreferenciadas (agebs_geo de parse_di_geometria: nse_txt + centroide). {} sin
    geometría/pin → masa simple (integridad, no inventa posiciones).
  • _nse_dominante_agebs extendida: masa_pond[n] = masa[n] × proximidad[n]; dominante sobre masa
    ponderada; share_dom se reporta sobre masa real (transparencia).
  • derive_demografia: nse_dom_key usa masa ponderada (_factor_proximidad_por_nse).
  • derive_segments: pasa (agebs_geo, pin) a _nse_dominante_agebs.
  • derive_comercio: ancla al NSE dominante ponderado (consistencia entre secciones).
  • Endpoints analyze y zona_procesar: construyen agebs_geo y pasan (agebs_geo, req.lng, req.lat).
- VALIDADO: caso construido (más masa C lejos, A pegado al pin) → sin proximidad domina C, con
  proximidad domina A (factor A=0.87 vs C=0.109). Sin geometría/pin → vuelve a masa simple.
  ZMM dominante B y VP dominante A (percepción de valor sigue predominando). verify_all 8/8 + 10/10,
  verify_interactive 16/16, render 9/9 limpio (ZMM + VP). page-comercio renderiza limpio con datos.

## EST1. Footer sidebar · cambio estético — [x] HECHO
- "Elaborado: M. Salcedo · O. Mendoza" → "Elaborado: Dataria Team · San Pedro Garza García,
  Nuevo León y Guadalajara, Jalisco · Hecho en México". Cero nombres viejos restantes.

## MON-PRECIO. Monitor · precio recomendado AUTOMÁTICO por producto (vertical+horizontal) — [x] HECHO + VALIDADO
- SÍNTOMA reportado: "el precio correcto en Monitor no está habilitado".
- CAUSA RAÍZ (diagnóstico): el cálculo SÍ estaba implementado (backend _precio_recomendado_mix_item
  dentro de amenaza_competitiva; front monitorPrecioVeredicto async), PERO el precio solo se mostraba
  al presionar el botón "$ precio" por fila → resultado en contenedor aparte, poco visible. Por eso
  parecía "no habilitado": el análisis del Monitor no lo mostraba por sí solo.
- FIX (solo front, sin tocar backend ni eliminar nada): renderMonitorAnalysis ya recibía el precio en
  cada threat (monitorFetchThreats trae pm2_recomendado/veredicto_precio). Se añadió un bloque "Precio
  recomendado" AUTOMÁTICO en la tarjeta de detalle de CADA producto (tras la estrategia): Tu $/m²,
  Recomendado $/m², Ticket recom., y veredicto CARO/BARATO/EN LÍNEA. Sin directos → nota N/D legítima.
  El botón "$ precio" por fila se mantiene (no se elimina progreso previo).
- CONSISTENCIA vertical/horizontal: garantizada por diseño — el backend calcula sobre _typologies del
  modo activo (_build_typologies usa el ft del modo). Mismo cálculo para ambos.
- VALIDADO end-to-end con backend real: VERTICAL (ZMM) 2/2 productos con bloque automático (BARATO,
  EN LÍNEA). HORIZONTAL (Zapopan, oferta real de casas $11-14M): casa $16M → CARO ($/m² rec $69,766);
  casa $9M → N/D (sin directos tan baratos). Sin tokens rotos. verify_all 8/8+10/10, verify_interactive
  16/16, render 9/9 limpio.

## TRASPASO. Migración a Cowork — [x] PAQUETE GENERADO Y VALIDADO (4 jul 2026)
- Repo reorganizado: CLAUDE.md (reglas permanentes, lectura automática por sesión), docs/
  (ESTADO_DATARIA, ARQUITECTURA_SECCIONES con anexo actual, esta lista), verificacion/
  (verify_all, verify_interactive con rutas del repo + fallback legacy).
- VALIDADO desde la estructura del repo: verify_all 8/8 + render 10/10; verify_interactive
  16/16; ambos contra el código final (app.py + static/dashboard) de esta etapa.
- Primera sesión en Cowork: usar PROMPT_ARRANQUE.txt del paquete de traspaso.

## ARRQ-COWORK. Sesión 1 en Cowork · Metodología + auditoría backend — [x] HECHO (6 jul 2026)
CONTEXTO: Héctor dictó la metodología DIGO/DPO completa (fuente de verdad) y entregó el PPTX
Distrito Tec (247 láminas, caso de estudio de PROCEDIMIENTO). Se auditó el backend contra la
metodología con foco en Zona de Análisis, Demanda y Producto (vertical y horizontal).
DOCUMENTACIÓN NUEVA:
  • docs/METODOLOGIA_DIGO.md — metodología dictada + secuencia del caso Distrito Tec +
    tabla de GAPS estructurales (G1-G10: isócrona por uso, población flotante, extranjeros,
    densidad AGEB, patrón de gasto como barrera, zonas en transición, perfiles ICSC/ULI,
    pronóstico gaussiano/Huff, metaproducto, usos nuevos).
  • docs/CATALOGO_VARIABLES.md — catálogo universal de variables (regla: solo crece; una
    fuente por constante). Incluye campos de la base tal cual llegan (XLSX DI, KMZ, VVV).
  • docs/referencias/ con el PPTX (agregado a .gitignore: 260 MB > límite GitHub 100 MB).
CORRECCIONES (causa raíz → fix, todas validadas con la batería completa):
  1. filter_vvv_by_polygon/pagos: sin proyectos válidos dentro del polígono devolvía TODOS
     los pagos sin filtrar (integridad espacial rota en zonas sin resumen). → ahora [].
  2. derive_productos_horizontal no exponía tca/competidores/mercado que vertical SÍ expone
     y el front lee (p.tca ×7 en el HTML) → violación de consistencia entre secciones
     (regla 7). → agregados con los mismos nombres del catálogo.
  3. Docstring de derive_productos_venta describía la regla VIEJA (m²=ticket/pm², elasticidad,
     penalizaciones) eliminada hace sesiones → riesgo de reintroducir la regla equivocada al
     leerla. → reescrito con la regla vigente (programa por ticket, flujo-contra-flujo).
  4. PRICE_BUCKETS (módulo): tabla de buckets MUERTA (0 usos; la canónica vive en
     derive_segments.BUCKETS) → riesgo de editar la tabla equivocada. → eliminada, comentario
     apunta a la canónica.
  5. TECHO DE INDUCCIÓN INERTE (hallazgo mayor): bucket_max_permitido se calculaba (regla
     confirmada: inducción hacia arriba con techo = piso del NSE superior presente) pero NO
     se aplicaba en ningún punto. En mercados incipientes (sin oferta vertical) el ancla
     (cand) decía en el comentario "dentro del techo de inducción" y el filtro no lo aplicaba.
     → cand ahora exige i <= bucket_max_permitido. Solo afecta zonas SIN oferta del modo
     (pv_idx=None); las zonas ancla usan la ruta de percepción de valor (sin cambio).
  6. _nse_dominante_agebs/_nse_barrier_info: fallback de hogares inconsistente con el resto
     del código ("Total de hogares" sin "Hogares totales 2020") → cadena unificada
     2026 → 2020 → Total de hogares → 1.
VALIDACIÓN: py_compile OK · node --check OK · verify_all 8/8 + render 10/10 + formato OK ·
verify_interactive 16/16 OK (catálogo venta 8 / renta 7; STDERR = artefactos documentados
del harness) · regeneración en vivo ZMM Centro + Valle Poniente + Escobedo horizontal
(anclas: dominante B / A; Escobedo valida el techo de inducción activado) — resultado
anotado abajo al completar la corrida.
HALLAZGOS QUE REQUIEREN DECISIÓN DE HÉCTOR (no se tocaron · regla 5):
  H7. segments.mkt_venta/mkt_renta/hog_propios usan proporciones FIJAS 0.83/0.17/0.65 de
      mkt_total (inventadas) cuando la base trae tenencia REAL por AGEB (Propia/Alquilada).
      Alimentan Renta y mix del front. Propuesta: derivarlas de la tenencia real de la zona.
  H8. rent_min/rent_max = 0.4% del valor de vivienda (regla de dedo) cuando existe capa
      vv_renta con rentas REALES. Propuesta: anclar a rentas observadas al revisar Renta.
  H9. nse_superior tras elevación por percepción de valor se recalcula sin exigir presencia
      en la zona (regla dice "presente"). Hoy INERTE (solo afecta techo en zonas con oferta,
      donde el techo no se usa). Decidir al revisar Demanda.
  H10. ingreso_hogar del NSE dominante usa promedio simple de AGEBs (no ponderado por
      hogares). Impacto menor; decidir al revisar Demografía.
  H11. _num/_price duplicadas (líneas ~22 y ~3221, implementaciones equivalentes) y
      _MON_TOL_*/_PRECIO_TOL_* duplicadas (ya listado) → consolidación pendiente menor.

## H7-H11. Datos reales en lugar de proporciones inventadas + consolidaciones — [x] HECHO (6 jul 2026, aprobado por Héctor)
H7 · TENENCIA REAL: mkt_venta/mkt_renta/hog_propios ya NO usan 0.83/0.17/0.65 fijos. Cada
  bucket usa la tenencia REAL (Propia/Alquilada/Prestada/Otra) de SUS AGEBs, ponderada por
  hogares; fallback = tenencia agregada de la zona; sin dato en toda la zona → None (N/D
  legítimo, sumas del backend protegidas con `or 0`). Nuevas variables de catálogo:
  share_renta, share_propia (decimales por bucket). En horizontal la masa va ponderada por
  prop_casa (consistente con la demanda del modo).
  VALIDADO ZMM: share_renta real por bucket 0.144-0.184 (vs 0.17 fijo); totals renta
  15,794→16,636. Featured y dominante intactos.
H8 · TASA DE RENTA OBSERVADA: rent_min/rent_max = valor × renta_pct_zona, donde
  renta_pct_zona = mediana($/m²/mes de vv_renta) ÷ mediana($/m² de venta), con ≥3
  observaciones en ambas capas; si no alcanza → 0.4% (regla base DIGO como fallback
  DOCUMENTADO). Nuevas variables: renta_pct_zona, renta_pct_fuente (observada|base_digo).
  derive_segments recibe ft_renta (nuevo parámetro; ambos endpoints lo pasan).
  BUG CORREGIDO EN LA PROPIA H8 (causa raíz): la 1ª versión leía la renta $/m²/mes con
  _pm2 (piso >$1,000 pensado para VENTA) y descartaba TODAS las rentas reales ($100-600).
  Se lee con _num y banda plausible 20-5,000.
  VALIDADO ZMM: renta_pct_zona=0.00353 OBSERVADA → rentas recomendadas ~12% menores que
  con el 0.4% de dedo (p.ej. 1 Rec: $4,500→$3,975/mes). El mercado real de renta manda.
H9 · nse_superior tras elevación por percepción exige PRESENCIA del NSE en la zona
  (nse_presentes de los AGEBs), como dice la regla confirmada.
H10 · ingreso por NSE (y del NSE dominante) ponderado por HOGARES del AGEB, no promedio
  simple. ZMM: sin cambio visible (40,044), esperado en zonas homogéneas.
H11 · Consolidaciones: eliminadas copias duplicadas de _num/_price (~línea 3220); _pm2v
  queda como ALIAS de _pm2 (el nombre se conserva: otros lo consumen). _MON_TOL_* ahora
  REFERENCIAN _PRECIO_TOL_* (no pueden divergir). PENDIENTE OBSERVADO: pm2_renta_zona en
  derive_productos_renta se calcula y NO se usa (variable inerte); decidir su papel al
  revisar la sección Renta. ocupacion_target="92%" hardcodeado en renta: revisar igual.
VALIDACIÓN: unit tests dirigidos (tenencia 30/10%, yield 0.005 observada, fallbacks, None
  seguro) · py_compile · node --check · verify_all 8/8 + render 10/10 (zona en vivo) ·
  ZMM antes/después completo (arriba) · verify_interactive: EN CURSO — el API PRSP hoy
  cuelga los exports DI pesados (Contry/VP/GDL); el check corre en background y se anota
  el resultado en cuanto el API responda. GDL (Jalisco, lógica universal): mismo estado.
SNAPSHOT para notas: snapshots/tablero_zmm_centro_2026-07-06.html (payload real embebido,
  gitignored). Front SIN cambios de código: mismos nombres de variables (catálogo).

## PLAN-V2. Listado maestro de Héctor por sección (vivienda vertical primero) — [REGISTRADO]
Ver docs/PLAN_V2_SECCIONES.md: backlog completo con IDs (ZA-1..8, RES-1..5, MAPA-1,
INV-1..8, DEM-1), estándares aplicables, decisiones respondidas (RES-3: disponible manda
para precio, total para velocidad; MAPA-1: un solo mapa maestro con capas), preguntas
abiertas P1-P5 (flotante/extranjeros, Predik OD, series de tiempo VVV, correo para
cuentas, geocoder) y fases F-A..F-E con checkpoints.
HALLAZGOS API (sondeo 6 jul): /api/predik solo expone isochrone (health "via isochrone";
rutas OD → 404) → P2. /api/descargas: el export DI acepta filtros `where` arbitrarios y
mode=influence (útil para explorador nacional y capas). Dump de campos VVV/DI: pendiente
por saturación del API PRSP (loop de reintentos corriendo); con él se resuelven RES-4
(freshness Guadalupe feb vs jun), INV-5 (desarrollador), INV-6/7 (campos de ficha) y P3.

## F-A. Fundaciones V2 (GO de Héctor con P1-P5 respondidas) — [x] HECHO (6 jul 2026)
Arquitectura confirmada por Héctor: MODULAR — cada sección invocable sola desde el front
(permisos por sección/zona). Entregado:
  • ZA-8 IDENTIDAD UNIVERSAL: _analisis_identidad() → analisis_nombre/version/id_str/fecha
    ('nombre · colonia · municipio · estado · vAAAAMMDDHHMM', hora centro de México).
    En zone_data + _vars; front: campo "Nombre del análisis" en formulario, body lo envía,
    topbar y título del documento la muestran (el backend la construye, el front solo pinta).
  • RES-2 ESTADÍSTICA ROBUSTA (catálogo): _percentil() y _stats_robustas() → n, mediana,
    mad, cv_robusto (MAD×1.4826/mediana), p10/p25/p75/p90, iqr, outliers Tukey (k=1.5),
    min/max. Aplicada ADITIVAMENTE (media/sd/cv se conservan: catálogo no muta) en
    value_perception_adjust (zona e isócrona y mercado del pin) y _valor_zona_cascada
    (stats del set que define el valor). Adopción visual en F-B/F-C.
  • ARQ-MODULAR: ANALYSIS_CACHE (en memoria, LRU por ts, DATARIA_CACHE_MAX=40) +
    POST /api/zona/seccion {analisis_key, seccion} → sirve UNA sección (payload_keys del
    SECTION_REGISTRY + identidad + _vars). zona_procesar guarda el análisis y devuelve
    analisis_key. Contrato estable; F-E enchufa auth/persistencia sin cambiarlo.
  • ZA-2 GEOCODING: GET /api/zona/geocode?q= y /api/zona/reverse?lat=&lng= con cadena
    ArcGIS World Geocoder → Nominatim (countrycodes=mx, User-Agent propio). NOTA: el
    sandbox bloquea ambos dominios → VALIDAR EN PRODUCCIÓN tras push (Safari).
  • P2 CONFIRMADO: wrapper PRSP sin OD (21 rutas → 404) → ticket con contrato propuesto
    (ver PLAN_V2_SECCIONES.md P2). P4: sin correo → ZA-1 por etapas (hash + admin, sin
    verificación por correo hasta tener servicio).
VALIDADO: py_compile · node --check · unitarias (identidad 2 casos, stats con outlier
  Tukey, sección demanda desde caché, key/sección inexistentes, eviction, rutas
  registradas) · verify_all 8/8 + render 10/10 (zona en vivo). PENDIENTES POR SALUD DEL
  API (loops corriendo, se anotan al caer): dump de campos VVV/DI (gate de RES-4/INV-5/
  6/7/P1/P3), verify_interactive 16/16, GDL Jalisco.

## F-B. Zona de Análisis (ZA-4/5/6/7) + Mapa maestro (MAPA-1) — [x] HECHO (6 jul 2026)
BACKEND:
  • parse_di_geometria EXTENDIDO (aditivo): cada AGEB trae ahora `ring` (polígono del
    bloque mayor, decimado ≤60 vértices), `area_km2` (shoelace equirectangular) y `attrs`
    (pares etiqueta|valor publicados por la base en el KMZ, cap 25) → capas del mapa y
    base para densidad/flotante cuando los campos existan. Consumidores previos intactos.
  • derive_percepcion_detalle (ZA-6): límites P10/P90, núcleo P25-P75, mediana/MAD,
    outliers que NO definen la zona, y MERCADO META (NSE + ingreso + ticket ancla +
    perfiles + etapas de vida top de la pirámide real). En _zona_analisis.percepcion_detalle.
FRONT (solo muestra; datos 100% backend):
  • ZA-7: tabla "Zona de influencia real" con MEDIANA/MAD/CV robusto/núcleo P25-P75/
    outliers; SIN oferta → valor por cascada con origen explícito. CERO 'N/D' (validado
    en harness con ambos casos). Normatividad: 'sin capturar' en vez de N/D (ZA-3 infra).
  • ZA-5: sets de competidores DESPLEGABLES al clic (lista por set con $/m², top 20).
  • ZA-6: tarjeta de percepción con límites inferior/superior, núcleo, mediana y mercado
    meta descrito (NSE, ingreso, etapas, perfiles).
  • ZA-4 parcial: barra de CAPAS en zona-análisis (NSE por AGEB · Percepción $/m²) +
    nota de propósito de los anillos (sin revelar método). Captable pendiente de P2.
  • MAPA-1: mapa maestro 72vh con capas encendibles (misma fábrica de capas:
    buildCapaNse/buildCapaPv · NSE coroplético por AGEB del KMZ · percepción por
    cuantiles P25/P75 en marcadores). zaClearLayers limpia capas al reprocesar.
VALIDADO: py_compile · node --check · unitarias (attrs genéricos, percepcion_detalle 2
  casos) · harness zaRenderResults CON y SIN oferta → cero N/D, ZA-5/6 presentes ·
  tplMapa con capas y 72vh · verify_all 8/8 + render 10/10 (payload en vivo).
  PENDIENTE (mismo gate API): dump de campos, verify_interactive, GDL — loops corriendo.

## F-C parcial. RES-1/3/5 + INV-4 (lo independiente del ticket P3) — [x] HECHO (6 jul 2026)
BACKEND (app.py):
  • derive_resumen_comercial(ft, segments): por PROYECTO estatus comercial (activo=inventario
    disponible · agotado=vendió todo · sin_dato), % desplazado, MEDIANAS DUALES de m²/$m²/
    precio (todo el inventario vs SOLO disponible · decisión RES-3) y producto ESTRELLA.
  • _estrella_de: criterio documentado RES-5 (1º % desplazado · 2º absorción observada ·
    3º vendidas · evidencia mínima 3 ventas). _tipologias_planas: filas canónicas de ft.
  • oferta_stats: stats robustas duales de zona (pm2/m2/precio/abs × total/disponible).
  • top_estrella: TOP 3 de la zona (excluyendo ganadoras por ronda) + estrella POR SEGMENTO
    de precio SOLO cuando >1 mercado tiene estrella (regla de Héctor). Replicable a todos
    los usos (misma forma canónica de estrella en el catálogo).
  • POST /api/zona/estrella_filtro (INV-4): corredor a la medida con rangos manuales del
    usuario (precio/m²/recámaras) calculado SIEMPRE en backend sobre _typologies del
    análisis en caché → estrella del corredor + stats robustas + comparación vs estrella
    de la zona. SECTION_REGISTRY: resumen/inventario sirven los campos nuevos vía
    /api/zona/seccion (ARQ-MODULAR).
FRONT (solo muestra):
  • Resumen: tabla ordenada ACTIVOS→AGOTADOS→sin dato con badges; columnas de medianas
    duales (tamaño incluido · RES-3) y ticket mediana; subrenglón ★ producto estrella por
    proyecto; tarjetas 🏆 TOP 3 de la zona + tabla por segmento; KPIs con MEDIANAS y núcleo
    P25-P75 (sustituyen promedios mostrados); "TCA" → "Crecimiento anual de hogares (TCA)";
    GLOSARIO al pie (tplGlosario, reutilizable).
  • Inventario: tarjeta "Corredor a la medida" con rangos manuales + botón que llama al
    endpoint y pinta estrella del corredor vs zona con núcleo P25-P75.
  • Hidratación: window.DATARIA_ANALISIS_KEY = data.analisis_key.
PENDIENTE P3 (anotado en el propio payload/nota): ventana de agotados a 8 meses,
absorción mes/trimestre/histórica y % plusvalía por periodo → serie temporal del ticket.
VALIDADO: py_compile · node --check · unitarias backend (estatus/estrella/medianas duales/
top3/por_segmento/endpoint con filtros) · harness front (payload nuevo, payload VIEJO
retrocompatible, INV-4 presente) · verify_all 8/8 + render 10/10 (en vivo).

## DEM-1. Diseño del modelo de segmentos de demanda — [PROPUESTA · esperando checkpoint]
Ver docs/DISENO_DEM1.md. Núcleo: desglosar cada bucket en PERFILES (cohorte de etapa de
vida × NSE × ingreso) con CONSERVACIÓN de la demanda por bucket ya validada; programa por
cohorte (recámara compartida + cajones con normativa cuando exista); capacidad de pago por
mensualidad (reto al múltiplo fijo 4.5 → banda 3.5-4.5); GMM solo con masa suficiente
(BIC, ≥30 AGEBs) para detectar submercados de ingreso; natural vs captable separados
(captable espera P1/P2, no se inventa); resta oferta−demanda POR PERFIL. Corrige el
defecto "más m² ⇒ más $/m²" (monotonía verificable: a mismo ticket, m²↑ ⇒ $/m²↓).
Decisiones abiertas: U1 umbral de masa (5% / 300 hog) · U2 cajones default por cohorte×NSE
· U3 banda de capacidad por mensualidad. Validación comprometida en anclas + Jalisco.
