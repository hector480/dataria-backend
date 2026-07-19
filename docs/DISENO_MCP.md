# DISEÑO · MOTOR + MCP + APP MÓVIL (conectar Dataria con Claude y con el bolsillo) — v2 para checkpoint
**Estado: PROPUESTA · esperando checkpoint de Héctor (19 jul 2026). Cero código hasta el visto bueno.**
Un solo MOTOR alimenta tres caras: (1) Claude conversacional (web/Mac/teléfono) vía MCP,
(2) una APP MÓVIL sencillísima (GPS o pin en mapa → recomendación de producto), y (3) la
futura narrativa interpretada. Nada de esto toca reglas ni secciones existentes: solo LEE.

## Pieza 0 · EL MOTOR: RESUMEN EJECUTIVO
`POST /api/zona/resumen_ejecutivo` (mismo backend; reutiliza el caché de zona_procesar).
Entrada: lat, lng, predio_m2, producto. Salida JSON compacto (~5-8 KB):
- identidad: zona, municipio, FECHA DE CORTE de la oferta, fuente de isócrona vigente
  (si opera el respaldo, aquí se declara — transparencia en el dato)
- percepcion: NSE por percepción, banda P10-P90, núcleo P25-P75, mediana/MAD, n
- demografia: población, hogares, TCA, personas/hogar, mezcla NSE, tenencia
- sets: directos (nombre, $/m², ticket) + secundarios sup/inf
- buckets: rango de precio → nuevas familias/año, evidencia vendidas/disp, aplicable
- dem1: top perfiles por demanda insatisfecha (cohorte, NSE, capacidad, programa, sugerido)
- productos: recomendados + sweet spot + no recomendados con motivo (LA recomendación)
- renta: banda observada, share, ocupación (N/D mientras la base no la traiga)
- captable: viajes/día, municipios ancla · estrella: producto estrella (laboratorio)
INTEGRIDAD: solo rebana campos que YA existen en el payload; ausente = N/D; cero cálculo nuevo.

## Pieza 1 · MCP REMOTO (Claude en cualquier dispositivo)
Montado en `/mcp/{token}` del mismo servicio. Herramientas v1 (solo lectura, sobre el motor):
analizar_zona · producto_recomendado · comparables · perfiles_demanda · mercado_captable
(mismos argumentos: lat, lng, predio_m2, uso). Registro: claude.ai → Conectores → URL con
token → aparece en web, Mac y app móvil de Claude. SDK oficial `mcp` de Python (o protocolo
mínimo a mano si pelea con Render; el contrato no cambia).

## Pieza 2 · APP MÓVIL (PWA "mapa + pin → producto")
Página móvil servida por el mismo backend (`/app/{token}`), instalable en pantalla de inicio
sin App Store. Flujo de UNA pantalla:
1. Mapa (mismo Leaflet del tablero) + botón "📍 Usar mi ubicación" (GPS del teléfono, con
   permiso del usuario, un toque) o picar el pin a mano.
2. Dos controles: tamaño de predio (default 3,000 m²) y uso (default vivienda vertical).
3. Botón "Analizar" → llama al MOTOR → muestra la RECOMENDACIÓN DE PRODUCTO que la
   herramienta ya calcula: sweet spot, oportunidades con su porqué (demanda vs evidencia),
   programa, $/m² del núcleo, ticket, perfiles — presentada limpia, con las guías Dataria.
   SIN costo de IA: en v1 no hay llamada a Claude; todo sale del cálculo propio.
v1.5 (checkpoint aparte): botón "Interpretación completa" → llamada a Claude DESDE el
servidor con el prompt de interpretación basado en METODOLOGIA (el prompt ES regla de
negocio: lo dicta/aprueba Héctor) · requiere llave de Anthropic · costo por análisis en
centavos. La app y el MCP no cambian: es una capa encima del mismo motor.

## Seguridad v1 (tajada del pendiente #1)
Token largo aleatorio en la URL (env `DATARIA_MCP_TOKEN` en Render). SIN la variable, ni el
MCP ni la app se montan (seguro por defecto: producción no cambia hasta que Héctor la ponga).
Tradeoff declarado: token en URL viaja cifrado pero puede quedar en logs — suficiente para
uso propio/equipo en v1; OAuth y cuentas llegan con F-E/seguridad completa (#1 sigue abierto).

## Validación antes de entregar
Batería completa + coherencia payload↔resumen en las 4 anclas (cada campo del resumen
idéntico a su fuente) + handshake MCP contra producción + PWA probada en tu teléfono (GPS y
pin) + verify_reglas ampliado (nada montado sin token). Anotación en LISTA, dos revisiones.

## Orden de construcción propuesto (un solo lote)
Motor → MCP → PWA v1. Todo entra en un push; tú pones DATARIA_MCP_TOKEN en Render (te doy
los pasos), registras el conector una vez y abres la app desde el teléfono.
