# DISEÑO DEM-1 · Segmentos de demanda objetivo (el corazón del método)
**Estado: PROPUESTA para checkpoint de Héctor (7 jul 2026). No se codifica hasta el GO.**
Corrige el defecto señalado ("más m² siempre con $/m² más caro") y construye la matriz
universal perfil → programa → precio que alimentará TODOS los usos inmobiliarios.

---

## 0. Principio rector (y qué corrige)
El defecto actual: los segmentos se generan por BUCKET DE PRECIO y el producto deriva m²
del ticket, así que "más caro" siempre parece "más grande y más $/m²". La realidad del
mercado: a un MISMO bucket llegan hogares en etapas de vida distintas que exigen programas
distintos; y a mismo ticket, MÁS m² implica MENOR $/m² (no mayor). El $/m² solo sube si el
NSE/percepción de la zona lo valida.

**DEM-1 = desglosar cada bucket en PERFILES (etapa de vida × NSE × ingreso), conservando
la contabilidad por bucket ya validada.** Los totales de demanda por bucket NO cambian
(regla 5: no arriesgar lo validado); se REPARTEN entre perfiles con masas reales. Producto
(fase siguiente, checkpoint aparte) consumirá estos perfiles para generar un programa por
perfil en lugar del heurístico actual de variantes.

## 1. Insumos (todos reales, por AGEB · base ArcGIS)
Pirámide de edades (quinquenal + etapas Niños/Adolescentes/Jóvenes/Jóvenes adultos/
Consolidados/Nesters) · tipología de hogar (familiar nuclear/ampliado/compuesto,
unipersonal, corresidente) · personas/hogar · situación conyugal · IXH mensual · NSE PER ·
tenencia (share_renta H7) · "Demanda anual vivienda" + "Rangos demanda vivienda" (flujo) ·
"Mercado en venta" (pool) · TCA. Oferta (laboratorio): ft con programa/precio/ventas.

## 2. Cohortes de etapa de vida (estándar household lifecycle · ULI/análisis de vivienda)
| Cohorte | Definición | Programa base (regla de recámara compartida ya validada + estándar) | Cajones base* |
|---|---|---|---|
| C1 Joven solo | unipersonal, 18-34 | 1 rec (studio/1R) | 1 |
| C2 Pareja joven sin hijos | familiar 2 personas, jefes 18-34 | 1-2 rec | 1-1.5 |
| C3 Familia en formación | familiar con hijos 0-9 | 2-3 rec (hijos chicos comparten) | 1.5-2 |
| C4 Familia consolidada | familiar con hijos 10-19 | 3+ rec (adolescentes no comparten por género) | 2 |
| C5 Corresidentes | no familiar, no pareja | 1 rec POR residente | 1 por rec |
| C6 Adulto solo 35-54 | unipersonal 35-54 | 1-2 rec (1 + flex) | 1 |
| C7 Nido vacío / maduros | jefes 55+, sin hijos en casa | 2 rec (1 + flex/visitas) | 1-2 |
*Cajones: la NORMATIVA capturada (ZonaRequest.norm.estac) MANDA cuando exista; la tabla es
el default por cohorte ajustado por NSE (A/B +0.5). Gancho listo para la sección normativa.

**Cómo se estiman las masas (sin inventar):** las cohortes se calculan POR AGEB como
ASIGNACIÓN de masas reales observadas: los hogares unipersonales/corresidentes vienen
directos de tipología de hogar; los familiares se reparten entre C2/C3/C4/C7 en proporción
a las masas reales de la pirámide (parejas jóvenes ∝ jóvenes adultos casados/unión libre;
C3 ∝ niños; C4 ∝ adolescentes; C7 ∝ nesters). El método de asignación queda documentado y
auditable (`fuente_masas`); cuando la base publique hogares por etapa directamente (estilo
P1), se enchufa sin rediseño. Confianza reportada por segmento (masa y nº de AGEBs).

## 3. Cruce con NSE × ingreso × capacidad de pago
- El cruce se hace POR AGEB (cada AGEB ya trae NSE e IXH reales) y se agrega por NSE.
  Emergen tantos bloques de segmentos como NSE con masa relevante haya (umbral propuesto:
  ≥5% de hogares de la zona o ≥300 hogares — decisión U1).
- **Capacidad de pago (RETO al múltiplo fijo 4.5):** el estándar hipotecario mexicano
  dimensiona por MENSUALIDAD (pago ≤ 25-30% del ingreso) a tasa y plazo de referencia, no
  por múltiplo fijo. Propuesta: `precio_max = mensualidad_max × factor(tasa, plazo) ÷
  (1 − enganche)` con constantes de catálogo `PTI_REF=0.28`, `TASA_REF` (configurable,
  hoy ~10.5-11%), `PLAZO_REF=240m`, `ENGANCHE_REF=10%`. Con esos valores el precio/ingreso
  anual resulta ≈ 3.6-4.2 — el 4.5 vigente queda como TECHO optimista (banda documentada
  [3.5, 4.5], central ~4.0 — decisión U3). Así el rango de precio de cada perfil sale de
  su ingreso REAL, no al revés.
- **Gaussiano/no gaussiano (dónde SÍ y dónde NO):** sobre la distribución conjunta
  ingreso×edad de los AGEBs se prueba mezcla de gaussianas (GMM, k=1 vs 2 por BIC) SOLO si
  hay masa suficiente (≥30 AGEBs) para detectar submercados de ingreso dentro de un mismo
  NSE (p. ej. zona en transición). Con muestras chicas el GMM sobreajusta (estándar:
  no aplicarlo); se usa conteo directo + medianas robustas (RES-2). El resultado del test
  se reporta (`gmm_aplicado`, componentes) — transparencia, no caja negra.

## 4. Cuantificación por segmento (perfil = cohorte × NSE)
- `hogares_stock` = masa del perfil (asignación §2 agregada por NSE).
- `nuevas_fam_year` = la demanda anual REAL del bucket (dato de la base, intacta) repartida
  entre los perfiles cuyo rango de capacidad cae en ese bucket, proporcional a su masa.
  **Conservación de masa: Σ perfiles del bucket = demanda del bucket actual (validada).**
- `pool_activo` = "Mercado en venta" × PCT_POOL_ACTIVO (regla vigente), mismo reparto.
- `crecimiento_pct` = TCA del NSE (catálogo) — y se deja declarado el upgrade a
  cohort-component (los jóvenes adultos de hoy son los consolidados de mañana) como fase
  futura documentada, no improvisada.
- `share_renta` del bucket (H7) para separar demanda de compra vs renta por perfil.
- Todo con medianas/bandas robustas; outliers reportados, nunca definiendo el segmento.

## 5. Producto por perfil (lo que corrige el defecto señalado)
Cada perfil emite: `programa {rec, cajones}`, `m2_banda` (banda del programa por ticket YA
validada + mínimos físicos por NSE del catálogo), `ticket_banda_M` (de SU capacidad de
pago) y `pm2_derivado = ticket/m²` que DEBE caer dentro del rango de percepción de valor
de la zona (ZA-6); si no cae, el perfil ajusta m² dentro de su banda (más chico = más $/m²,
más grande = menos $/m²) hasta ser funcional Y comprable. La oferta es el LABORATORIO:
el matching perfil↔oferta (programa + ticket) valida qué configuraciones ya se venden.
La resta OFERTA − DEMANDA se hace POR PERFIL (no solo por bucket) → demanda insatisfecha
por perfil = la conclusión que pediste. (La implementación toca derive_productos: se hará
en fase aparte con su propio checkpoint y validación de anclas.)

## 6. Mercado natural vs captable
- `demanda_natural` = todo lo anterior (AGEBs de la zona azul+verde).
- `demanda_captable` = zonas de ORIGEN (Predik OD · ticket P2) con captación por gravedad
  (Huff: atracción ∝ tamaño/valor ÷ fricción de tiempo) + población extranjera (P1),
  mostrando origen por colonia y % de representatividad (ZA-4). HASTA que P1/P2 existan:
  `demanda_captable = None` con nota explícita — no se inventa.
- Variables reservadas en catálogo: `captable_origenes[{colonia, share_pct, nse, viajes}]`.

## 7. Variables nuevas (catálogo · aditivas)
`segmentos_dem1[] = {perfil_id, cohorte, cohorte_label, nse, ingreso_banda[2],
capacidad_pago_banda_M[2], bucket, hogares_stock, nuevas_fam_year, pool_activo,
crecimiento_pct, share_renta, programa{rec, cajones}, m2_banda[2], ticket_banda_M[2],
pm2_derivado_banda[2], fuente_masas, confianza, gmm_componente}`
`dem1_meta = {metodo_masas, umbral_masa, gmm_aplicado, nota_captable, version_modelo}`
La sección Demanda del front muestra la matriz por perfil; `/api/zona/seccion` la sirve
independiente (ARQ-MODULAR). Los segments actuales NO se tocan (compatibilidad total).

## 8. Validación comprometida (antes de entregar)
1. Conservación de masa: Σ nuevas_fam de perfiles = demanda por bucket actual (exacta).
2. Anclas: ZMM Centro reproduce el ancla conocida (1R joven/C1-C2 en <$1.5M, NSE C/C+ con
   percepción B); VP produce familias A consolidadas 3R+ en tickets altos; Escobedo
   horizontal coherente (2-3R económicas C3/C4).
3. Monotonía correcta: a mismo bucket, m²↑ ⇒ $/m²↓ (se verifica programáticamente).
4. Jalisco (GDL/Zapopan) por ser lógica universal + batería completa 8/8, 10/10, 16/16.

## Decisiones del checkpoint (RESUELTAS con Héctor · 7 jul 2026)
- **U1 · CALIBRACIÓN, no dogma**: 5% (convención de reporte en investigación de mercados:
  celdas <5% aparentan precisión) y 300 hogares (regla 1/√n: error ±5-6% en proporciones)
  son VALORES INICIALES. Como aquí el riesgo real es el error de ASIGNACIÓN en celdas
  chicas + irrelevancia comercial (80 hogares no sostienen una torre), el umbral definitivo
  se CALIBRA por sensibilidad (0/150/300/500) en zonas ancla: se fija donde los perfiles
  dejan de cambiar conclusiones. Constantes configurables (DATARIA_UMBRAL_*).
- **U2 · GO**: cajones default por cohorte×NSE (§2); la normativa capturada MANDA.
- **U3 · CORREGIDO por Héctor**: el 28% era la convención de EUA (regla 28/36). Banca MX
  suscribe 30-35% pago-ingreso (CONDUSEF ~30% prudente). Banda: PTI_REF=0.30 (central) a
  PTI_MAX=0.35 (techo banca), tasa/plazo/enganche configurables (default 10.5% · 240 m ·
  10% — CONFIRMAR tasa de referencia vigente con Héctor). Implicación documentada: a esas
  tasas la capacidad ≈ 2.7-3.2× ingreso anual; el 4.5× histórico requiere enganche/
  patrimonio — que es lo que "Rangos demanda vivienda" de la base ya captura (ese dato
  SIGUE mandando en los buckets; la banda PTI aplica al derivar capacidad de perfiles).
