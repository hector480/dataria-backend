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
