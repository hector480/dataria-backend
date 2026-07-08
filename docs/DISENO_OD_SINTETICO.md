# DISEÑO OD-SINTÉTICO · Segunda fuente de mercado captable, MEJOR que Predik
**Estado: PROPUESTA para checkpoint de Héctor (8 jul 2026). Premisa aceptada: Predik NO
volverá a ser una dependencia. La nueva fuente debe ser segura, estable, gratuita y
superior a lo que se esperaba de Predik.**

## 1. Qué se esperaba de Predik y por qué esto puede ser MEJOR
Predik (telemetría) prometía flujos origen-destino observados. Sus debilidades: caja negra
(muestra sesgada a apps, sin auditar), dependencia de un tercero que ya falló (403), costo.
La alternativa propuesta es un **motor OD sintético ANCLADO A DATOS OBSERVADOS OFICIALES**:

| Criterio | Predik | OD-sintético INEGI |
|---|---|---|
| Seguridad/estabilidad | tercero que ya falló | el ancla censal VIAJA EN EL REPO (no puede "caerse") |
| Auditabilidad | caja negra | método estándar documentado línea por línea |
| Costo | de pago | gratuito |
| NSE del origen | no nativo | nativo (tu base por AGEB) |
| Motivo del viaje | inferido | explícito por capa (trabajo/estudio/compras/turismo) |
| Actualización | opaca | censal + recalibrable con CUALQUIER telemetría futura (si Predik vuelve, sirve para CALIBRAR, no como dependencia) |

## 2. Fuentes (todas gratuitas y oficiales)
- **S1 · INEGI Censo 2020 (cuestionario ampliado) · MOVILIDAD**: matrices municipio→
  municipio OBSERVADAS de viajes al TRABAJO y a la ESCUELA. Se preprocesan UNA VEZ a un
  archivo compacto (CSV/SQLite, pocos MB) **versionado en el repo** → cero dependencia de
  servicios vivos. Es el ancla observada del modelo.
- **S2 · INEGI DENUE (API pública, token gratuito)**: establecimientos con ubicación exacta
  y estrato de personal ocupado → masas de ATRACCIÓN del destino (empleo, escuelas,
  hospitales, comercio) y de los DESTINOS COMPETIDORES (Huff de destinos en competencia).
- **S3 · Isócronas multi-proveedor** (ya construidas): fricción de tiempo real de manejo.
- **S4 · Tu base ArcGIS por AGEB**: masas de origen, NSE, y extranjero (ticket P1).
- **S5 · DATATUR/Sectur (abierto)**: ocupación hotelera y mezcla nacional/extranjera por
  destino turístico → capa del motivo TURISMO en zonas de playa/turísticas.

## 3. Método (estándar de planeación de transporte · Ortúzar & Willumsen)
1. **Marginales observados**: del censo, cuántos viajes de trabajo/estudio ENTRAN al
   municipio del pin desde cada municipio de origen (dato real, no modelo).
2. **Desagregación a AGEB**: modelo gravitacional (masa del AGEB × fricción de tiempo por
   isócrona) **balanceado por IPF/Fratar** para que la suma por municipio CUADRE EXACTO
   con los marginales censales → "sintético anclado a observado".
3. **Destinos en competencia (Huff completo)**: la atracción del pin se pondera contra los
   subcentros competidores (DENUE) → share captable realista, no optimista.
4. **Capas por motivo**: trabajo/estudio (censo) · compras/servicios (Huff-DENUE, ya
   estándar en la metodología para comercio) · turismo (DATATUR + columnas P1).
5. **Confianza declarada por capa** en el payload (observado / anclado / modelado), igual
   que ya hacemos con `masa_fuente` y `renta_pct_fuente`.

## 4. Arquitectura (contrato estable)
- MISMO contrato `mercado_captable` ya publicado (v1 Huff): solo cambia
  `metodo: "od_sintetico_inegi_v1"` y se agregan `motivos{trabajo,estudio,compras,turismo}`
  y `confianza`. El front NO cambia (catálogo respetado).
- Cadena de cálculo con degradación declarada: **v2 OD-sintético → v1 Huff (hoy en
  producción) → None**. Nada se rompe si falta una pieza.
- Piezas: `datos/od_censo_2020.(csv|sqlite)` (preproceso versionado) ·
  `fetch_denue(client, pin, radio)` (env `DATARIA_DENUE_TOKEN`) ·
  `derive_mercado_captable_v2(...)` · calibración por ciudad guardada en
  `datos/calibracion_od.json`.

## 5. Limitaciones honestas (declaradas en el payload)
- El OD censal es a nivel MUNICIPIO y solo motivos trabajo/estudio; la bajada a AGEB es
  modelada (IPF+Huff) — por eso el ancla municipal es EXACTA y la desagregación lleva
  `confianza: "anclado"`.
- Compras y turismo son modelo (Huff-DENUE / DATATUR) hasta calibrar con conteos reales.
- Censo 2020: se actualiza con la intercensal/censo siguiente; la estructura queda lista.

## 6. Fases
- **OD-A · Preproceso del ancla censal** (bloqueante): generar `od_censo_2020` compacto.
  El sandbox tiene bloqueada la descarga de INEGI → opciones: (a) columnas de movilidad
  publicadas EN TU BASE ArcGIS (ideal: todo vive en tu fuente única · pregunta Q1), o
  (b) descarga manual/por tu equipo del tabulado de movilidad del censo y me lo dejas en
  `docs/referencias/`, o (c) script de descarga que corre en Render al desplegar.
- **OD-B · DENUE**: adapter + token (Q2) → masas de atracción y destinos competidores.
- **OD-C · Motor v2** (gravedad + IPF + Huff destinos) + validación en anclas ZMM/VP/GDL
  contra sanity checks (¿los orígenes top coinciden con lo que tu experiencia dice de esas
  zonas?) y comparación v1 vs v2 en el tablero (mismo patrón del comparador de isócronas).
- **OD-D · Turismo**: DATATUR + P1 para Los Cabos/Vallarta/Cancún/etc. (Q3).

## Preguntas para Héctor (Q)
- **Q1** · ¿Tu equipo puede publicar EN LA BASE (por AGEB o municipio) los campos censales
  de movilidad ("población ocupada que trabaja en otro municipio", municipio de trabajo/
  estudio)? Si sí, TODO el ancla vive en tu fuente única y no dependemos ni de descargas.
- **Q2** · Token DENUE: se registra gratis en inegi.org.mx; ¿lo generas tú o tu equipo y lo
  ponemos como env `DATARIA_DENUE_TOKEN` en Render?
- **Q3** · ¿Qué zonas turísticas calibro primero? (propongo Los Cabos, Vallarta, Cancún).
