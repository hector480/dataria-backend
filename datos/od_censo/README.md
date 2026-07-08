# Ancla censal OD (flujos municipio→municipio · Censo 2020 INEGI)
Formato CANÓNICO por estado: `<estado_slug>.csv` (p. ej. `nuevo_leon.csv`) con encabezados
que contengan: ORIGEN (municipio de residencia), DESTINO (municipio de trabajo/estudio),
MOTIVO (trabajo|estudio · opcional, default trabajo) y VIAJES (personas).
Cadena de carga: 1) este directorio (versionado, inmune a caídas) · 2) autofetch
DATARIA_OD_URL_TPL · 3) sin ancla → modelo Huff v1 declarado.
Diagnóstico: GET /api/od/status?estado=Nuevo%20León&muni=Monterrey
