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

## Bloque 4 · Lo aparcado por tu decisión (para el final)
MCP + app móvil (diseño listo en DISENO_MCP.md) · modelo de cobro (benchmark entregado) ·
F-E cuentas/bitácora/medidor · seguridad completa #1 (gate de cualquier lanzamiento público).

## Ahora mismo en tu GitHub Desktop (commit cuando gustes)
static/dashboard_zona_analisis.html (guardas simulador — cierra el $null vivo) ·
docs/LISTA_REVISION.md · docs/DISENO_MCP.md · docs/AUDITORIA_SECCIONES.md ·
docs/COLA_DECISIONES.md · verificacion/verify_linaje.py
