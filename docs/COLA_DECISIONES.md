# COLA DE DECISIONES PARA HÉCTOR · para sesiones una-por-una
**Actualizada 19 jul 2026. Nada de esta lista se implementa sin tu palomeo.**

## Bloque 1 · Decisiones chicas (rápidas, una sentada)
1. Declarar la ampliación 8→14 en el motivo de la zona morada (o exponer el campo) — hoy no viaja al tablero.
2. Fecha de corte visible + aviso de dato viejo (RES-4; el caso Guadalupe: todo el levantamiento de venta es 2026-02-09 y renta 2023).
3. Exponer el desglose por bucket de DEM-1 (ledger `buckets`) para auditar conservación por bucket desde el payload.
4. Etiquetas de las tres bandas de $/m² (capa P25/P75 · comparables ±2·MAD · ZA-6 P10-P90) — dijiste "por ahora no"; queda aquí.
5. Supuesto `units=120` del simulador de renta (¿120? ¿otro? ¿etiquetado "supuesto"?).
6. Regla de mezcla: ¿un producto de banda B ("oportunidad" con demanda+evidencia) cabe en un predio de percepción A, o la percepción lo veta? (salió del ejercicio de validación).

## Bloque 2 · Hallazgos nuevos de la auditoría (autónoma, 19 jul)
7. Catálogo: backfill de ~295 variables vivas sin documentar — propongo hacerlo por sección durante la auditoría (solo documentación; el catálogo solo crece). Confirma el enfoque.
8. Claves producidas sin consumidor (~270): al triarlas por sección, las que resulten carga muerta ¿se limpian o se conservan como API? (decisión por lote cuando te muestre cada lista).

## Bloque 3 · Gaps estructurales de tu metodología (§9) — cada uno lleva diseño + checkpoint
- **G1 Tiempos de isócrona por USO** — necesito de ti: la tabla de tiempos por cada uno de los 6 usos (o palomear la actual por tamaño como base).
- **G2 Población flotante** — diseño mío → checkpoint; necesito pistas de dónde viven en la base las concentraciones de trabajo/estudio.
- **G3 Mercado extranjero turístico** — necesito de ti: dónde está la población extranjera en la base (dijiste que existe).
- **G4 Densidad de AGEB** (normalizar masa) — diseño mío → checkpoint.
- **G5 Gasto como barrera de compatibilidad NSE** — diseño mío → checkpoint.
- **G6 Zonas en transición** como variable consultable — diseño mío → checkpoint.
- **G7 Perfil de usuario ICSC/ULI** — investigación documentada de estándares → checkpoint (¿autorizas búsqueda web de las referencias ICSC/ULI cuando toque?).
- **G8 Pronóstico gaussiano/no gaussiano + Huff comercio** — diseño mío → checkpoint.
- **G9 Metaproducto** (amenidades/acabados por perfil; backend aún no entrega amenidades procesadas — pendiente #4).
- **G10 Usos nuevos** (lotes, industrial, logística, CC, hotel) — uno por uno, cada uno con su pipeline.

## Bloque 3.5 · Hallazgos de la auditoría de Producto (bloque 5 · 19 jul)
- **#9 Supply-only calculado en el front** — getSupplyOnlySuggestions deriva promedios
  ponderados sobre TYPOLOGIES en el navegador. El PROMEDIO aquí es deliberado (es el foil
  del "método tradicional", rotulado "Promedio observado · NO recomendados sin validación
  demand-driven"), no viola RES-2 (que rige TUS estadísticas). Lo que choca con tu regla es
  DÓNDE se calcula: debería producirlo el backend y el front solo pintarlo. Refactor sin
  cambio de comportamiento — ¿lo hago?
- **#10 Fichas de diseño (DESIGN_TIERS) con contenido editorial fijo en el front** — el
  detalle de producto muestra perfiles de edad, ingresos ($200-300k/mes), acabados y
  amenidades ESCRITOS en el código del front, no derivados de la base, y se presentan como
  si fueran de la zona. Opciones: (a) derivarlos de la base/backend (¿qué fuente los
  respaldaría?), (b) rotularlos "plantilla editorial Dataria", (c) quitarlos. Tu llamada.

## Bloque 3.6 · Hallazgo de la auditoría de Comercio (bloque 6 · 19 jul)
- **#11 Constantes del método comercio sin ratificar en §10** — el gasto por categoría SÍ
  viene de la base (campos "Gasto …" C193-201), pero la derivación usa parámetros que nunca
  pasaron por tu una-por-una: CAPTURA 25% (gasto de la zona que captura el comercio local),
  tabla de ventas por m²/año por giro (10 valores típicos tecleados: Supermercado $95k …
  Mejoras del hogar $35k), demanda captable 15% (la etiqueta del front coincide con el
  backend), renta sostenible = 10% de ventas ±12%, GLA mínimo viable 100 m², factor 0.85
  del escenario low y +35% del high, ancla fija = Supermercado, y el catálogo de tenants
  sugeridos por NSE (marcas: City Market/Liverpool… · HEB/Suburbia… · Bodega
  Aurrerá/Coppel…). Nada se tocó — ¿los ratificas tal cual (van a §10), los ajustas, o
  quieres fuentes de industria documentadas para la tabla de ventas/m²?

## Bloque 3.7 · Hallazgos de la auditoría de Mezclas + Monitor (bloque 7 · 19 jul)
- **#12 Modo Recomendación filtra por PROMEDIOS calculados en el front** — los umbrales
  "absorción ≥ promedio de la zona Y $/m² ≥ promedio" (venta y renta) se calculan en el
  navegador (vivos: 0.57 un/mes · $83,335). En pantalla se rotulan "Promedio zona"
  (honesto), pero tu RES-2 pide MEDIANAS para estadísticas de zona y tu regla pide el
  cálculo en backend. ¿Cambio los umbrales a MEDIANA calculada en backend (recomendado,
  consistente con RES-2), o ratificas el promedio aquí a propósito (es un umbral de
  selección, no un dato mostrado) y solo lo muevo a backend?
- **#13 Constantes del Monitor sin ratificar en §10** — tolerancias de competidor directo
  ±15% ticket · ±30% área · ±1 recámara (FUENTE ÚNICA compartida con el precio
  recomendado, y están declaradas en pantalla — arquitectura correcta), escalera de
  estrategia por threat ratio (>2.0 reposicionar · >1.0 aguantar · >0.5 monitorear · ≤0.5
  acelerar), área fallback 60 m² cuando no capturas m², y PRECIO_TOL_VEREDICTO (±5% para
  caro/en línea/barato). ¿Las ratificas tal cual a §10 o ajustas alguna?

## Bloque 4 · Lo aparcado por tu decisión (para el final)
MCP + app móvil (diseño listo en DISENO_MCP.md) · modelo de cobro (benchmark entregado) ·
F-E cuentas/bitácora/medidor · seguridad completa #1 (gate de cualquier lanzamiento público).

## Ahora mismo en tu GitHub Desktop (commit cuando gustes · solo docs)
docs/AUDITORIA_SECCIONES.md · docs/LISTA_REVISION.md · docs/COLA_DECISIONES.md (registro
de la verificación post-push del veto — el código ya está desplegado y verificado).
Siguiente en la mesa: decisiones #9-#13 de esta cola, una por una cuando gustes.
