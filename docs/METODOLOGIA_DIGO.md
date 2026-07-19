# METODOLOGÍA DIGO®/DPO · Fuente de verdad del método
**Dictada por Héctor González (6 jul 2026). Este documento manda sobre el código: si el código
contradice este método, el código está mal (salvo regla confirmada posterior en CLAUDE.md).**
Complementa CLAUDE.md (reglas operativas) y docs/CATALOGO_VARIABLES.md (nombres universales).

---

## 0. Alcance de la herramienta
Análisis de mercado y definición de producto inmobiliario para SEIS usos, cada uno con reglas
particulares pero el MISMO método:
1. Vivienda vertical
2. Vivienda unifamiliar horizontal
3. Lotes unifamiliares
4. Parques industriales
5. Centros comerciales
6. Parques de logística

## 1. Fuentes de datos (únicas y suficientes)
- **Base ArcGIS de Prosperia (vía API PRSP)**: TODA la información necesaria está ahí
  (demografía por AGEB, NSE, ingresos, edades, patrón de gasto por categoría comercial,
  oferta VVV/VH, población extranjera, etc.). NO se inventa información ni se busca en otra
  fuente. Si algo no se encuentra → PREGUNTAR a Héctor (da pistas de dónde está en la base).
  Si el API actual no apunta a la sección correcta de la base, se MODIFICA el API/consulta
  para apuntar bien (no se sustituye el dato).
- **Predik (vía API PRSP)**: isócronas y zonas de influencia. SIEMPRE se consulta.
- Estándares de industria para asociar perfil de usuario → producto típico: **ICSC, ULI** y
  bibliografía de autoridad (documentar la referencia al diseñar cada regla). Ante una
  solicitud de análisis: primero verificar si existe un estándar global documentado
  (p. ej. modelo de **Huff** para demanda de espacios de conveniencia/comercial) y luego
  seguir el instinto de Héctor si no lo hay.

## 2. Premisa maestra: PRIMERO el potencial de demanda
Todo análisis inicia entendiendo la demanda potencial, organizada geográficamente por AGEB
(todo dato está relacionado a un punto geográfico dentro de una AGEB):
- Población y edades · etapa de vida por grupo de edad
- Conformación familiar (tipología de hogar)
- Ingresos MENSUALES que producen
- Ritmo de crecimiento (TCA)
- De ahí se obtiene cuántas personas/familias provocan demanda de CADA producto analizado
  (cada uso tiene reglas de demanda particulares, pero todo sale de la misma base por AGEB).

## 3. Zona de influencia (siempre vía Predik)
La zona de influencia depende de TRES factores:
1. **Tamaño del terreno** a analizar.
2. **Uso inmobiliario** analizado (cada uso tiene su tiempo de isócrona propio).
3. **Atracción de población externa**: si la zona atrae población de fuera del radio,
   se buscan **zonas de origen y zonas de destino** a un tiempo que depende del tamaño
   y del uso.
Los tiempos por uso/tamaño se CONFIRMAN con Héctor al revisar cada sección y quedan
registrados en el backend por uso y por tamaño.
- **Zonas turísticas**: el mercado EXTRANJERO se mide siempre (la población extranjera está
  en la base ArcGIS; si no se localiza, preguntar).
- **Barreras de accesibilidad** (ríos, montañas, falta de calles) se leen en la CONFORMACIÓN
  de la isócrona/zona de influencia — no se modelan como variables físicas, se observa su
  efecto (regla ya implementada en detección de mercados).

## 4. Entendimiento del entorno (base de todo)
Orden del primer análisis:
1. **NSE por AGEB (cartografía ArcGIS)** e identificación de cambios DRÁSTICOS de NSE.
   Regla clave: los NSE se definen por ESTILO DE VIDA/patrón de gasto, NO por ingreso.
   Un D+ puede ganar el doble que un C- y aun así tener hábitos de consumo y vida distintos.
   La diferencia se lee en la sección de la base que muestra CÓMO DISTRIBUYEN SU GASTO en
   categorías comerciales. D no es compatible con C.
2. **Percepción de valor de los inmuebles**: el precio es SEÑAL del valor percibido (no lo
   establece). Señala cuánto está dispuesto a pagar alguien por un inmueble en la AGEB.
   **Zonas en transición**: AGEBs de NSE C/D con precios de NSE B — se identifican y se
   consideran en los análisis específicos que lo requieran.
3. **Uso de suelo actual y DENSIDAD**: clasificar cuánta población de qué NSE y patrón de
   gasto existe. Una AGEB grande NO pesa igual que una AGEB densa (normalizar por densidad).
   Usos y destinos de suelo maduros/establecidos dan contexto de la zona.
4. **Concentraciones de trabajo, estudio e infraestructura** (hospitales, puertos,
   aeropuertos, corredores corporativos y hoteleros, parques industriales): atraen
   **población flotante** (igual que zonas turísticas de playa). De ahí salen señales de
   demanda ADICIONAL a la de la población permanente (cuartos de hotel, m² comerciales de
   restaurantes/conveniencia). El ritmo de crecimiento de esos espacios pronostica el
   crecimiento de esa demanda. El NSE y estilo de gasto de la población flotante también
   se mide (por sus zonas de origen).
5. **Pronóstico**: métodos gaussianos y NO gaussianos para el comportamiento de población,
   con la información de la base + modelos matemáticos estándar aplicables (p. ej. Huff).

Tener esta información clara, ordenada y lista —zonas de análisis de demanda, zonas de
oferta competidora, población flotante, barreras de percepción de valor y NSE, y el
crecimiento de esas variables— ES el fundamento del método.

## 5. Definiciones de NSE (por estilo de vida, antecedente familiar y formativo — NO por ingreso)
| NSE | Definición |
|---|---|
| A | Familias fundadoras. Estudios superiores y posgrados en prestigiosas universidades extranjeras. |
| B | Empresarios. Estudios superiores y posgrados en prestigiosas universidades. **Gastan más que los A.** |
| C+ | Profesionistas. Estudios superiores y posgrados. |
| C | Profesionistas y empleados. Estudios superiores. Etapas iniciales de su carrera profesional. |
| D+ | Trabajadores y técnicos especializados. Estudios superiores o técnicos. |
| D | Técnicos y obreros. Estudios técnicos o educación básica. |
| E | Desempleados y migrantes rurales. Educación básica trunca o nula. |

Nota operativa: la capa NSE de ArcGIS ('NSE PER') ya trae esta clasificación por AGEB; el
backend la LEE (no la recalcula por bandas de ingreso, salvo fallback documentado). Las
bandas de ingreso son herramienta auxiliar (capacidad de pago), no definición del NSE.

## 6. Flujo DEMANDA → OFERTA → PRODUCTO (por perfil de usuario)
Para CUALQUIER uso inmobiliario:
1. **DEMANDA** = demanda de la zona + demanda de población flotante (si aplica por
   infraestructura educativa, aeropuertos, puertos, parques industriales, corredores
   corporativos/hoteleros o turismo).
2. **Clasificar la demanda por PERFIL DE USUARIO** y asociar cada perfil a un **producto
   típico** según estándares de industria (ICSC, ULI, bibliografía de autoridad —
   investigar y documentar).
3. **Clasificar la OFERTA** de la misma manera (asociada a perfil de usuario).
4. **RESTAR: oferta existente − demanda existente POR PERFIL** → demanda insatisfecha.
5. **Pronóstico de crecimiento de la demanda** (gaussiano/no gaussiano).
6. **Prototipos de producto** para perfiles con demanda insatisfecha:
   mercado meta → ingreso → precio potencial → tamaño asociado a ese precio/perfil
   (con el entendimiento de la oferta) → programa arquitectónico (recámaras) → detalles
   del METAPRODUCTO (amenidades, nivel de acabados, extras) según el perfil.
7. **La OFERTA es el LABORATORIO**: los inventarios existentes confirman o descalifican
   los detalles que harán exitoso el producto (análisis detallado de la oferta).
8. **Variantes de atractivo**: evaluar si el producto mejora al REDUCIR PRECIO vía reducir
   TAMAÑO o reducir CALIDAD, para volverlo más atractivo al mercado meta (siempre validado
   contra la oferta-laboratorio).
9. **Conclusión** = producto demandado, presentado como demanda − oferta.

## 7. Catálogo de variables universal (regla de gobierno)
- Existe UN catálogo de variables estándar documentado (docs/CATALOGO_VARIABLES.md) usado
  en todos los modelos y consumido por el front con el mismo nombre.
- El catálogo SOLO CRECE: un ajuste o sección nueva genera una VARIABLE NUEVA; NUNCA se
  modifica el significado/nombre de una variable usada por otra sección.
- Cada uso inmobiliario tiene reglas particulares aunque el método sea el mismo: sus
  variables propias se registran con prefijo del uso.

## 8. Caso de estudio de referencia · APRENDIZAJES DE PROCEDIMIENTO
**"16.10.19 - CAPITAL NATURAL - DISTRITO TEC" (PPTX, 247 láminas, en docs/referencias/;
excluido de git por tamaño)**. Referencia de PROCEDIMIENTO; sus datos (2016) NO son regla:
los datos vigentes SIEMPRE salen de ArcGIS y Predik. Secuencia del estudio (el "pipeline"
que la herramienta productiza):
1. **Macro entorno**: proyección poblacional, mancha urbana, generadores de dinámica de
   vida (concentraciones de trabajo/estudio por perfil), usos de suelo, densidad actual
   vs permitida (viv/Ha), distancias a puntos de interés.
2. **Áreas de influencia**: barreras FÍSICAS (naturales/artificiales) + barreras SOCIALES
   (contrastes de NSE en zonas muy cercanas, visibles en coropleta AGEB) + vialidades.
   Comercial: AIP 3 km / AIS 5 km (en la herramienta: isócronas Predik).
3. **Zonificación comparada**: ficha por zona (hogares, ocupantes/hogar, 4 grupos de edad,
   % foráneos, POBLACIÓN FLOTANTE, densidad personas/Ha) y selección de zonas comparables.
4. **Check list de validación del uso** (habitacional/comercial) ANTES de dimensionar.
5. **Dimensionamiento del mercado existente**: población ancla (p. ej. alumnos ITESM →
   % foráneos/extranjeros) → hogares → COMPOSICIÓN del hogar del mercado (solos/compartido)
   → capacidad de pago → demanda por programa (por cuarto en renta estudiantil).
6. **Análisis de la oferta (laboratorio)**: fichas comparables (tamaño, distancia, $/m²,
   cuartos, baños, cajones, antigüedad, % ocupación) por anillos de distancia; percepción
   de valor en renta por depto Y por habitación.
7. **Recomendación de producto**: por programa (1/2/3 cuartos), escenarios de captación
   (@100% / @30% — hoy: slider de captación), potencial MDP/mes con ocupación estabilizada
   (80%), expresado en unidades/torres; amenidades y metaproducto por perfil (QUIÉNES SON).
8. **Mercado inducido**: demanda metropolitana por NSE aplicada a la zona (nuevos
   segmentos que el producto atrae) + casos hipotéticos (sin desarrollar / desarrollando /
   con vivienda) para medir la demanda que el PROPIO desarrollo induce.
9. **Potencial de crecimiento**: densidad objetivo (viv/Ha) → hogares adicionales posibles
   → curva temporal (viviendas/año por fase, arranque→consolidación).
10. **Comercio**: categorías de gasto (patrón por NSE, gasto ≈58% del ingreso en el caso),
    ingresos/gastos del área de influencia, ANR y % ocupación de comparables, renta por
    PB/PA, competidores por rango de renta, oportunidad de expansión = gasto captable vs
    ANR existente, tipo de centro (convenience 5-7 locales / lifestyle · ICSC) y tenant mix.
11. **Conclusiones**: potencial total por segmento con precios requeridos y condiciones de
    entorno (infraestructura, corredor comercial) + curva potencial/tiempo.

---

## 9. ESTADO DE IMPLEMENTACIÓN vs MÉTODO (auditoría 6 jul 2026)

### Ya implementado y alineado
- Isócrona por tamaño (`isochrone_profile`) + flag comercial; 3 zonas (morado/azul/verde);
  demanda = azul+verde; directos = morado.
- Detección universal de mercados (efecto de barreras en datos, no barrera física) +
  barrera espacial de NSE con KMZ (`detect_markets`, `_zona_por_barrera_nse`).
- NSE dominante por masa × proximidad al pin; percepción de valor (VVV) predomina y puede
  subir; techo de inducción definido; demanda granular por AGEB sin promediar.
- Demanda por "Rangos demanda vivienda"/"Demanda anual vivienda"/"Mercado en venta" (base
  real); absorción flujo-contra-flujo con pronóstico 12/18/24.
- Producto anclado a programa por ticket; multi-programa por bucket; recámara compartida;
  oferta como laboratorio (m²/pm² observados mandan); precio recomendado por directos.

### GAPS estructurales (pendientes de diseño con Héctor, sección por sección)
| # | Gap | Detalle |
|---|---|---|
| G1 | Tiempos de isócrona por USO | Hoy solo tamaño + flag comercial. Falta perfil por cada uno de los 6 usos (confirmar tiempos con Héctor). |
| G2 | Población flotante | No implementada: concentraciones de trabajo/estudio/infraestructura, zonas origen/destino, demanda adicional (hotel, comercio). |
| G3 | Mercado extranjero en zonas turísticas | No implementado; el dato existe en la base (preguntar ubicación exacta cuando toque). |
| G4 | Densidad de AGEB | La masa usa hogares absolutos; falta normalización por densidad (AGEB grande ≠ densa). |
| G5 | Patrón de gasto como definidor de NSE/compatibilidad | El gasto por categoría se usa en comercio, pero la "incompatibilidad D vs C por estilo de gasto" no se usa como barrera. |
| G6 | Zonas en transición | Precio NSE B en demografía C/D: hoy se eleva la percepción, pero no se etiqueta "zona en transición" como variable consultable. |
| G7 | Perfil de usuario como eje | La resta oferta−demanda es por bucket de precio; falta clasificar demanda Y oferta por PERFIL (estándares ICSC/ULI documentados). |
| G8 | Modelos de pronóstico | TCA lineal hoy; faltan métodos gaussianos/no gaussianos y Huff (comercio/conveniencia). |
| G9 | Metaproducto | Amenidades/acabados/extras por perfil: backend aún no entrega amenidades procesadas. |
| G10 | Usos nuevos | lotes, industrial, logística, oficinas/CC, hotel: declarados, sin pipeline. |

---

## 10. PARÁMETROS DEL MÉTODO (ratificados por Héctor · 18 jul 2026, sesión una-por-una)
Estos parámetros dejaron de ser decisiones invisibles de implementación: Héctor los revisó
uno por uno y quedaron así. Cambiarlos requiere nueva confirmación.

| Parámetro | Valor ratificado | Estándar/nota |
|---|---|---|
| Fuente de isócronas | **Orden de prioridad: Predik → Valhalla → (ORS/TomTom con llave)**, front limpio (sin etiqueta de fuente en pantalla; declarada en el dato interno). "Mediana multi-fuente" queda como opción futura: requiere diseño y checkpoint antes de implementarse | El método dicta Predik; el respaldo opera solo ante falla |
| Sets de competidores | **Regla dictada TAL CUAL**: dentro de la isócrona con OTRA percepción/NSE = SECUNDARIO (aplica a todo el anillo primario, no solo al morado). DIRECTO = banda de percepción + bloque NSE + isócrona primaria. El set "primarios" queda vacío por construcción cuando hay banda y el tablero lo oculta; sin banda evaluable se conservan los sets geométricos | Percepción/NSE mandan sobre geometría |
| Banda de comparables | mediana **± 2·MAD** (fallback ±15% sin MAD) | Estadística robusta estándar (~±1.35σ) |
| Muestra mínima de zona | **15** proyectos; menos → ampliación 8→14 min DECLARADA | Configurable (DATARIA_ZONA_MUESTRA_MIN) |
| Bloque NSE compatible | **±1 nivel** de NSE | Implementa "D no es compatible con C" |
| Capa mapa $/m² | bajo < **P25** · medio P25–P75 · alto > **P75** de lo observado en la zona | RES-2 (nunca promedios) |
| Corona captable | anillo principal **+10 min** (tope 30) · gravedad exponente **2.0** | Ortúzar & Willumsen / modelo gravitacional estándar |
| Ocupación de renta | **N/D SIEMPRE (regla final)**: la capa vv_renta no trae ocupación física — su ESTATUS es estado del ANUNCIO ('Comparable' activo · 'No disponible' retirado/rentado · vacío = el equipo de campo no obtuvo el dato; verificado ZMM 336/55/22). Todo lo dependiente muestra N/D; mueren el 92% y el 90 hardcodeados; el slider de escenario queda deshabilitado (el usuario puede fijar ocupación solo en el slider de SENSIBILIDAD, que es escenario explícito). Candidato: pedir ocupación real al equipo de base | N/D = el equipo de campo no obtuvo el dato (semántica de la base confirmada por Héctor) |

### Adenda §3 · Regla de soporte de muestra (enunciación de Héctor · 19 jul 2026)
"Deben utilizarse los valores de percepción de valor, los ingresos de la población y la
capacidad de pago EN LA ISÓCRONA, y utilizar los proyectos EN LA ZONA como referente; en la
zona secundaria suelen existir esas complementarias." — Es la práctica estándar de
comparables (ampliar el área de búsqueda hasta tener soporte, como el valuador amplía el
radio de comps). Implementación: percepción sobre el anillo primario; con muestra
insuficiente (<15, §10) las complementarias de la secundaria entran al cálculo. Por decisión
de Héctor NO se muestra explicación en pantalla (el dato interno sí lo registra).
