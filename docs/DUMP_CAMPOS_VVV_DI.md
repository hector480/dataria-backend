# DUMP DE CAMPOS · VVV (venta/renta) y DescargaDI — 18 jul 2026

Gate de descubrimiento pedido el 6-7 jul (INV-1/5/6/7, RES-4, P1/P3), corrido con la API
PRSP sana desde el sandbox. **Método**: anillo de consulta circular r=2.5 km alrededor de
cada pin (SOLO delimita la consulta a las capas; no es geometría de análisis). Zonas:
ZMM Centro (25.6866,-100.3161) y Guadalupe (25.6767,-100.2565 · caso freshness RES-4).
Los registros VVV llegan como features ArcGIS `{attributes, geometry}`; aquí se listan los
campos de `attributes` (+ `geometry_x/y`). Presencia = % de filas con valor no vacío.

## HALLAZGOS DIRIGIDOS

### Freshness (RES-4 · caso Guadalupe) — CAUSA RAÍZ ACOTADA
- `FECHA_DE_LEVANTAMIENTO` existe al 100% en resumen/ft/pagos de venta y renta.
  Formato MIXTO: epoch ms en `resumen` (p.ej. 1770595200000) e ISO en `ft` ('2026-02-09').
- **vv_venta: TODO el universo está fechado 2026-02-09** (ZMM 282/282 · Guadalupe 24/24).
  No hay registros posteriores a febrero EN EL WRAPPER → el 'febrero habiendo junio/julio'
  NO es filtrado del backend Dataria: es lo que entrega la capa vía PRSP. Si la base ArcGIS
  tiene capturas jun/jul (Héctor lo confirma), el corte está ENTRE la base y el wrapper →
  misma familia del ticket P3 (en el tintero por decisión del 18 jul).
- **vv_renta está fechada 2023** (jun-2023 y dic-2023 en ambas zonas). La banda P10-P90
  que ancla la renta se observa sobre datos de 2023 — el método es correcto (observado),
  pero la transparencia manda: mostrar `fecha_corte` también en renta.
- ACCIÓN POSIBLE SIN TICKET (propuesta · checkpoint): publicar `fecha_corte`/`periodo_dato`
  en el payload y tablero (regla RES-4 del catálogo) + aviso de staleness (hoy−corte >N días).

### Desarrollador (INV-5)
- **0 columnas** tipo desarrollador/constructor/promotor en venta, renta o DI. El dato que
  'está en la base' NO llega por el wrapper → candidato a la misma conversación PRSP.

### Ficha técnica (INV-6/7)
- SÍ existen: `CAJONES_ASIGNADOS` (100% ft venta y renta), `ACABADO_EN_MURO` (83% resumen),
  y en venta.resumen los campos de amenidades/equipamiento marcados con '●' (ver listado).
- No aparecen descripción/cercanías como texto → lo de INV-6 sale de regla de negocio
  propia o de otra fuente, no de estas capas.

### P1 (flotante/extranjero) y P3 (series)
- P1: 0 columnas (esperado; ticket en el tintero). P3: no hay serie temporal — solo el
  snapshot vigente con su fecha (los 'hits' del patrón eran falsos positivos tipo
  'RECAMARAS'→'mar', 'separad'→'sep', 'Información'→'forma').

## ZONA ZMM_CENTRO · consulta: anillo_consulta_2.5km (solo dump de campos)

### di.kmz — 71 filas · 8 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| area_km2 | 100.0% | 0.5002 |
| attrs | 100.0% | {'XI_Nivel socioeconómico por ingreso': 'B'} |
| lat | 100.0% | 25.681246 |
| lng | 100.0% | -100.345717 |
| n_vertices | 100.0% | 76 |
| nse_rank | 100.0% | 2 |
| nse_txt | 100.0% | B |
| ring | 100.0% | [[-100.34143, 25.68617], [-100.34073, 25.68518], |

### di.xlsx — 71 filas · 252 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| 0 a 4 | 100.0% | 16.6913517972 |
| 10 a 14 | 100.0% | 18.634705067 |
| 15 a 19 | 100.0% | 20.8379447817 |
| 20 a 24 | 100.0% | 22.8169599994 |
| 20 a 24 casada | 100.0% | 11 |
| 20 a 24 en union libre | 100.0% | 2 |
| 20 a 24 no especifico | 100.0% | 0 |
| 20 a 24 separad  divorcia | 100.0% | 2 |
| 20 a 24 soltera | 100.0% | 8 |
| 25 a 29 | 100.0% | 18.5047618446 |
| 25 a 29 casada | 100.0% | 9 |
| 25 a 29 en union libre | 100.0% | 2 |
| 25 a 29 no especifico | 100.0% | 0 |
| 25 a 29 separad  divorcia | 100.0% | 2 |
| 25 a 29 soltera | 100.0% | 6 |
| 30 a 34 | 100.0% | 17.3080806076 |
| 30 a 34 casada | 100.0% | 8 |
| 30 a 34 en union libre | 100.0% | 2 |
| 30 a 34 no especifico | 100.0% | 0 |
| 30 a 34 separad  divorcia | 100.0% | 2 |
| 30 a 34 soltera | 100.0% | 6 |
| 35 a 39 | 100.0% | 17.5358712994 |
| 35 a 39 casada | 100.0% | 8 |
| 35 a 39 en union libre | 100.0% | 2 |
| 35 a 39 no especifico | 100.0% | 0 |
| 35 a 39 separad  divorcia | 100.0% | 2 |
| 35 a 39 soltera | 100.0% | 6 |
| 40 a 44 | 100.0% | 18.7521666077 |
| 40 a 44 casada | 100.0% | 9 |
| 40 a 44 en union libre | 100.0% | 2 |
| 40 a 44 no especifico | 100.0% | 0 |
| 40 a 44 separad  divorcia | 100.0% | 2 |
| 40 a 44 soltera | 100.0% | 6 |
| 45 a 49 | 100.0% | 15.5537356612 |
| 45 a 49 casada | 100.0% | 7 |
| 45 a 49 en union libre | 100.0% | 2 |
| 45 a 49 no especifico | 100.0% | 0 |
| 45 a 49 separad  divorcia | 100.0% | 1 |
| 45 a 49 soltera | 100.0% | 5 |
| 5 a 9 | 100.0% | 17.5710874728 |
| 50 a 54 | 100.0% | 15.3865702807 |
| 50 a 54 casada | 100.0% | 7 |
| 50 a 54 en union libre | 100.0% | 2 |
| 50 a 54 no especifico | 100.0% | 0 |
| 50 a 54 separad  divorcia | 100.0% | 1 |
| 50 a 54 soltera | 100.0% | 5 |
| 55 a 59 | 100.0% | 12.063545404 |
| 55 a 59 casada | 100.0% | 6 |
| 55 a 59 en union libre | 100.0% | 1 |
| 55 a 59 no especifico | 100.0% | 0 |
| 55 a 59 separad  divorcia | 100.0% | 1 |
| 55 a 59 soltera | 100.0% | 4 |
| 60 a 64 | 100.0% | 10.3005078579 |
| 60 a 64 casada | 100.0% | 6 |
| 60 a 64 en union libre | 100.0% | 0 |
| 60 a 64 no especifico | 100.0% | 0 |
| 60 a 64 separad | 100.0% | 3 |
| 60 a 64 soltera | 100.0% | 1 |
| 65 a 69 | 100.0% | 8.9736605113 |
| 65 a 69 casada | 100.0% | 5 |
| 65 a 69 en union libre | 100.0% | 0 |
| 65 a 69 no especifico | 100.0% | 0 |
| 65 a 69 separad | 100.0% | 3 |
| 65 a 69 soltera | 100.0% | 1 |
| 70 a 74 | 100.0% | 6.7414454639 |
| 70 a 74 casada | 100.0% | 4 |
| 70 a 74 en union libre | 100.0% | 0 |
| 70 a 74 no especifico | 100.0% | 0 |
| 70 a 74 separad | 100.0% | 2 |
| 70 a 74 soltera | 100.0% | 0 |
| 75 y Más | 100.0% | 9.3276053435 |
| 75 y Más casada | 100.0% | 5 |
| 75 y Más en union libre | 100.0% | 0 |
| 75 y Más no especifico | 100.0% | 0 |
| 75 y Más separad | 100.0% | 3 |
| 75 y Más soltera | 100.0% | 1 |
| AREA | 100.0% | 50.378087066658146 |
| AREA_ORIG | 0.0% |  |
| Adolescentes | 100.0% | 18.634705067 |
| Afinidad NSE | 100.0% | SI |
| Alquilada | 100.0% | 16.5322944636 |
| CVEGEO | 100.0% | 1903900011690 |
| Casa | 100.0% | 82.4476685576 |
| Consolidados | 100.0% | 84.5364244566 |
| Corporativos | 100.0% | 0.2658647089 |
| Corporativos m2 | 100.0% | 3.9879706335 |
| Demanda ACEM | 90.1% | 0.2879256294286145 |
| Demanda CHC | 90.1% | 0.045195341474445955 |
| Demanda CME | 90.1% | 1.022805186190261 |
| Demanda CMG | 90.1% | 1.4529224634403741 |
| Demanda Cuidado_personal | 90.1% | 31.680335594753505 |
| Demanda CuidadodeSalud | 90.1% | 6.394631825719886 |
| Demanda Educacion | 90.1% | 38.12937865219358 |
| Demanda Entretenimiento | 90.1% | 24.66641285994271 |
| Demanda HSP | 90.1% | 1.6741352329262777 |
| Demanda Hospitalización | 90.1% | 1.5662128297904419 |
| Demanda MV | 90.1% | 6.966849434644957 |
| Demanda Muebleria | 90.1% | 7.249289280868385 |
| Demanda Otros | 90.1% | 0.3454351424694708 |
| Demanda Restaurantes | 90.1% | 30.833016071159353 |
| Demanda Retail | 90.1% | 50.556731705110806 |
| Demanda Servicios | 90.1% | 25.513732383536862 |
| Demanda Supermercado | 90.1% | 173.7475760892507 |
| Demanda anual vivienda | 100.0% | 1 |
| Demanda anual vivienda renta | 100.0% | 0 |
| Demanda de Vivienda en Renta de EUA | 95.8% | 0 |
| Demanda de Vivienda en Renta de otro país | 95.8% | 0 |
| Demanda de Vivienda en Venta de EUA | 95.8% | 0 |
| Demanda de Vivienda en Venta de otro país | 95.8% | 0 |
| Densidad de población | 100.0% | 4.9 |
| Densidad de población 2022 | 100.0% | 4.9 |
| Departamento o edificio | 100.0% | 5.0721472199 |
| ECO1 | 100.0% | 103 |
| ECO25 | 100.0% | 0 |
| ECO4 | 100.0% | 103 |
| EDU49_R | 100.0% | 13.5 |
| Educacion | 100.0% | Licenciatura y más |
| Estado | 100.0% | Nuevo León |
| Factor precio | 100.0% | 22.23 |
| Factor precio Oferta | 100.0% | 39.52 |
| Factor precio Total | 100.0% | 61.75 |
| Gasto Análisis clínicos y estudios médicos | 90.1% | 1909.8107 |
| Gasto Consultas médico especialista | 90.1% | 6784.2668 |
| Gasto Consultas médico general | 90.1% | 9637.2347 |
| Gasto Cuidado de la salud | 90.1% | 42415.5929 |
| Gasto Cuidado personal | 90.1% | 210135.666 |
| Gasto Cuotas a hospitales o clínicas | 90.1% | 299.7807 |
| Gasto Educación | 90.1% | 252912.1686 |
| Gasto Entretenimiento | 90.1% | 163612.3165 |
| Gasto Honorarios por servicios profesionales | 90.1% | 11104.539 |
| Gasto Hospitalización | 90.1% | 10388.6897 |
| Gasto Mantenimiento de la vivienda | 90.1% | 46211.1123 |
| Gasto Mueblería | 90.1% | 48084.5358 |
| Gasto Otros: pago de enfermeras y personal al cuidado de enfermos | 90.1% | 2291.2713 |
| Gasto Restaurantes | 90.1% | 204515.3956 |
| Gasto Retail | 90.1% | 335342.8014 |
| Gasto Servicios | 90.1% | 169232.5869 |
| Gasto Supermercado | 90.1% | 1152467.6722 |
| Gasto por exhibición Análisis clínicos y estudios médicos | 90.1% | 462 |
| Gasto por exhibición Consultas médico especialista | 90.1% | 401 |
| Gasto por exhibición Consultas médico general | 90.1% | 102 |
| Gasto por exhibición Cuotas a hospitales o clínicas | 90.1% | 1010 |
| Gasto por exhibición Honorarios por servicios profesionales | 90.1% | 6476 |
| Gasto por exhibición Hospitalización | 90.1% | 5330 |
| Gasto por exhibición Otros: pago de enfermeras y personal al cuidado de enfermos | 90.1% | 1518 |
| Hogares  ampliados | 100.0% | 23.968393642 |
| Hogares  no familiares totales | 100.0% | 11.8666368 |
| Hogares  otra situación | 100.0% | 1.5180562389 |
| Hogares compuestos | 100.0% | 1.7383524752 |
| Hogares corresidentes | 100.0% | 2.041033287 |
| Hogares de dos recámaras | 100.0% | 52.949594130899996 |
| Hogares desocupados  2026 | 100.0% | 65 |
| Hogares familiares totales | 100.0% | 78.1333632 |
| Hogares nucleares | 100.0% | 50.9085608439 |
| Hogares ocupados 2020 | 100.0% | 83 |
| Hogares ocupados 2026 | 100.0% | 90 |
| Hogares totales 2020 | 100.0% | 143 |
| Hogares totales 2026 | 100.0% | 155 |
| Hogares unipersonales | 100.0% | 9.825603513 |
| IXH | 100.0% | 34693.027248818624 |
| Información en medios masivos | 100.0% | 0.0262649905 |
| Información en medios masivos m2 | 100.0% | 0.3939748575 |
| Ingreso Residual | 90.1% | 539858.197 |
| Ingresos totales 2026 | 100.0% | 3122372.452393676 |
| Jovenes | 100.0% | 20.8379447817 |
| Jovenes_adultos | 100.0% | 41.321721844 |
| MIG11 | 100.0% | 11 |
| MIG14 | 100.0% | 0 |
| MIG15 | 100.0% | 4 |
| MIG8 | 100.0% | 142 |
| Mercado en renta | 95.8% | 18 |
| Mercado en venta | 95.8% | 69 |
| Municipio | 100.0% | Monterrey |
| NSE PER | 90.1% | D+ |
| Nesters | 100.0% | 47.4067645806 |
| Niños | 100.0% | 34.26243927 |
| OBJECTID_1 | 100.0% | 32036 |
| Orden V Casa | 100.0% | 2 |
| OrdenNSE | 100.0% | 4 |
| OrdenNSEPER | 100.0% | 5 |
| Orden_Educacion | 100.0% | 4 |
| Otra situación | 100.0% | 2.4286820301 |
| Otro tipo de vivienda | 100.0% | 0.0032614497 |
| Otros servicios excepto actividades gubernamentales | 100.0% | 0.0908559525 |
| Otros servicios excepto actividades gubernamentales m2 | 100.0% | 1.3628392875 |
| PEA 2026 | 100.0% | 112 |
| PEA desocupada 2026 | 100.0% | 0 |
| PEA ocupada 2026 | 100.0% | 112 |
| POB1 | 100.0% | 228 |
| PXHFAMILIARES | 95.8% | 3 |
| PXHNOFAMILIARES | 95.8% | 1 |
| Personas de 5 a 130 años de edad que en el 2020 residían
en otra entidad federativa. | 100.0% | 11 |
| Personas por hogar 2026 | 95.8% | 2.7 |
| Población  corresidente | 100.0% | 4.3263390222 |
| Población  nucleares | 100.0% | 130.0409270765 |
| Población  unipersonal | 100.0% | 7.6414037778 |
| Población ampliados | 100.0% | 91.8564725189 |
| Población compuestos | 100.0% | 6.6757669213 |
| Población de 5 años
y más residente en la
entidad en marzo de
2020 | 100.0% | 142 |
| Población familiar total | 100.0% | 235.0322572 |
| Población no familiar total | 100.0% | 11.9677428 |
| Población otra situación | 100.0% | 6.4590906833 |
| Población total 2026 | 100.0% | 247 |
| Población total estimada 2021 | 100.0% | 231.192 |
| Población total estimada 2023 | 100.0% | 237.710689632 |
| Población total estimada 2024 | 100.0% | 241.038639286848 |
| Población total estimada 2025 | 100.0% | 244.41318023686387 |
| Población total estimada 2026 | 100.0% | 247.83496476017996 |
| Población total estimada 2027 | 100.0% | 251.30465426682247 |
| Población total estimada 2028 | 100.0% | 254.82291942655797 |
| Población total estimada 2029 | 100.0% | 258.39044029852977 |
| Población total estimada 2030 | 100.0% | 262.0079064627092 |
| Porcentaje de hogares con automóvil 2026 | 100.0% | 60 |
| Porcentaje de hogares sin automóvil 2026 | 100.0% | 40 |
| PorcentajeDeCasa | 100.0% | 0.005234320157774041 |
| PorcentajeDeGasto | 90.1% | 3.836756675648372e-05 |
| Prestada | 100.0% | 8.6808111091 |
| Propia | 100.0% | 62.3582123973 |
| Rangos de densidad pob | 100.0% | 0.01 |
| Rangos demanda vivienda | 90.1% | $1,200,000-$1,499,999 |
| Rangos demanda vivienda numerico | 90.1% | 7 |
| Rangos demanda vivienda numerico renta | 90.1% | 7 |
| Rangos demanda vivienda renta | 90.1% | $6,000-$7,499 |
| RangosDemandaLotes | 90.1% | 400,000 - 500,000 |
| RangosDemandaLotesNumero | 90.1% | 7 |
| Servicios financieros y de seguros | 100.0% | 0.811868079 |
| Servicios financieros y de seguros m2 | 100.0% | 12.178021185 |
| Servicios inmobiliarios y de alquiler de bienes muebles e intangibles | 100.0% | 0.1518953185 |
| Servicios inmobiliarios y de alquiler de bienes muebles e intangibles m2 | 100.0% | 2.2784297775 |
| Servicios profesionales científicos y técnicos | 100.0% | 0.412617615 |
| Servicios profesionales científicos y técnicos m2 | 100.0% | 6.189264225 |
| Shape_Area | 0.0% |  |
| Shape__Area | 100.0% | 503780.8713378906 |
| Shape__Length | 100.0% | 2922.2015424603273 |
| Tasa de crecimiento AGEB | 100.0% | 1.4 |
| Tasa de crecimiento AGEB personas de EUA | 100.0% | 0.5 |
| Tasa de crecimiento AGEB personas de otro país | 100.0% | 0 |
| Tasa de crecimiento anual | 100.0% | 8.4 |
| Tasa de crecimiento de los últimos 5 años | 100.0% | 7.2 |
| Tasa de crecimiento de los últimos 5 años de personas de EUA | 100.0% | 2.7 |
| Tasa de crecimiento de los últimos 5 años de personas de otro pais | 100.0% | 0 |
| Tasa de crecimiento factor | 100.0% | 1.1 |
| V CASAS | 100.0% | 1295000 |
| VIV0 | 100.0% | 143 |
| VIV1 | 100.0% | 83 |
| VIV29 | 100.0% | 50 |
| VIV92_R | 100.0% | 2.6 |
| V_RENTA | 100.0% | 6475 |
| Vivienda en vecidad o cuartería | 100.0% | 1.1675989801 |
| Vivienda no específica | 100.0% | 1.3093237928 |
| Viviendas habitadas que disponen de automovil 2026 | 100.0% | 54 |
| XI_Nivel socioeconómico por ingreso | 100.0% | C |

### vv_renta.ft — 413 filas · 36 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| AMUEBLADO | 69.7% | ● |
| ANIO_CARGA | 100.0% | 2023 |
| CAJONES_ASIGNADOS | 100.0% | 2 |
| CANTIDAD_DE_RECAMARAS | 100.0% | 3 |
| CORREDOR___ZONA | 100.0% | Mitras |
| ELECTRODOMESTICOS | 74.8% | ● |
| ESTATUS | 94.7% | No disponible |
| Esquema | 100.0% | 2 |
| FECHA_DE_LEVANTAMIENTO | 88.4% | 2023-06-16 |
| F__M2_Demanda | 100.0% | 247.619047619048 |
| F___M2 | 100.0% | 247.619047619048 |
| F___UM_Demanda | 100.0% | 26000 |
| F____RECAMARA | 100.0% | 8666.666666666666 |
| F____UNIDAD_MENSUAL | 100.0% | 26000 |
| Frrecuencia_PU | 100.0% | 0.5 |
| GlobalID | 100.0% | 5e3e1d91-4c97-48aa-82a3-08a771bf3332 |
| IDCONCAT | 100.0% | CATEHUA/-100.3143/25.7084 |
| MES_CARGA | 100.0% | 4 |
| NO_AMUEBLADO | 5.1% | ● |
| No_ | 100.0% | 9 |
| Nombre | 100.0% | Catehua |
| OBJECTID | 100.0% | 275 |
| OBJECTID_1 | 100.0% | 4 |
| OrdenPU | 100.0% | 3 |
| PROYECTO | 100.0% | Catehua |
| TIPO | 100.0% | 1 |
| X_coor | 100.0% | -100.31437554699994 |
| Y_coor | 100.0% | 25.708430840000062 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686873600000 |
| municipio | 100.0% | Monterrey |
| ÁREA_DE_TERRAZA | 100.0% | 0 |
| ÁREA_PRIVATIVA | 100.0% | 105 |
| ÁREA_TOTAL | 100.0% | 105 |
| ÁREA_TOTAL_Demanda | 100.0% | 105 |

### vv_renta.pagos — 0 filas · 0 campos

| Campo | Presencia | Ejemplo |
|---|---|---|

### vv_renta.resumen — 207 filas · 61 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ALBERCA | 36.7% | ● |
| AMUEBLADO | 67.1% | ● |
| ANIO_CARGA | 100.0% | 2023 |
| ASADORES | 60.4% | ● |
| ASOLEADERO | 0.0% |  |
| BAR | 13.5% | ● |
| BOLICHE | 0.0% |  |
| BUSINESS_CENTER | 28.0% | ● |
| CANCHAS | 12.1% | ● |
| CASA_CLUB | 0.0% |  |
| CAVA | 0.0% |  |
| CORREDOR___ZONA | 100.0% | Mitras |
| CUARTO_DE_SEGURIDAD | 44.4% | ● |
| ELECTRODOMESTICOS | 73.9% | ● |
| ESTATUS | 0.0% |  |
| Esquema | 100.0% | 2 |
| Estado | 100.0% | Nuevo León |
| FECHA_DE_LEVANTAMIENTO | 94.2% | 1686873600000 |
| FOGATERO | 6.8% | ● |
| F__M2_PROM | 100.0% | 252.01465201465203 |
| F___REC | 100.0% | 9333.333333333332 |
| F____UNIDAD_MENSUAL_PROM | 100.0% | 23000 |
| Ficha_Tecnica | 100.0% | <a href="https://prsp.maps.arcgis.com/apps/dashb |
| GAME_ROOM___VIRTUAL | 6.8% | ● |
| GIMNASIO | 53.6% | ● |
| GOLF | 0.0% |  |
| GlobalID | 100.0% | fc731ee3-22bf-4cd6-be40-737dac77f67a |
| HABITACIÓN_DE_HUESPEDES | 3.4% | ● |
| IDCONCAT | 100.0% | CATEHUA/-100.3143/25.7084 |
| Imagen_URL | 100.0% | https://img10.naventcdn.com/avisos/18/00/55/98/2 |
| JUEGOS_PARA_NIÑOS | 25.6% | ● |
| LOBBY | 27.5% | ● |
| LUDOTECA | 32.9% | ● |
| MES_CARGA | 100.0% | 4 |
| MOTOR_LOBBY | 0.0% |  |
| Municipio | 100.0% | Monterrey |
| NO_AMUEBLADO | 6.8% | ● |
| No_ | 100.0% | 9 |
| Nombre | 100.0% | Catehua |
| OBJECTID | 100.0% | 9 |
| OBJECTID_1 | 100.0% | 4 |
| OTRO | 14.0% | Lavandería, Terraza. |
| PET_FRIENDLY | 24.2% | ● |
| PROYECTO | 100.0% | Catehua |
| SALA_DE_CINE | 13.5% | ● |
| SALA_DE_PUROS | 0.0% |  |
| SALA_DE_TÉ | 0.0% |  |
| SALÓN_MULTIUSOS | 40.1% | ● |
| SAUNA_Y_VAPOR | 0.0% |  |
| SKY_LOUNGE | 3.4% | ● |
| SPA | 0.0% |  |
| USOS_MIXTOS | 50.2% | ● |
| VITAPISTA | 12.1% | ● |
| X_coor | 100.0% | -100.31437554699994 |
| Y_coor | 100.0% | 25.708430840000062 |
| Zona | 100.0% | Noreste |
| geometry_x | 100.0% | -100.31437554699994 |
| geometry_y | 100.0% | 25.708430840000062 |
| ÁREA_SOCIAL | 43.0% | ● |
| ÁREA_TOTAL_PROM | 100.0% | 91.5 |
| ÁREA_VERDE | 32.4% | ● |

### vv_venta.ft — 282 filas · 53 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ABSORCIÓN | 100.0% | 1.7413793103448276 |
| ANIO_CARGA | 100.0% | 2026 |
| AVANCE_COMERCIAL | 100.0% | 0.7769230769230769 |
| Abs_Demanda | 100.0% | 1.7413793103448276 |
| CAJONES_ASIGNADOS | 100.0% | 1 |
| CANTIDAD_DE_RECAMARAS | 100.0% | 1 |
| CORREDOR___ZONA | 100.0% | Centro |
| ESTATUS | 100.0% | Comparable |
| Esquema | 100.0% | 1 |
| Estatus_Vendido | 100.0% | Activo |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 2026-02-09 |
| F__M2_Demanda | 67.4% | 70563.03255407471 |
| F___M2 | 100.0% | 70563.03255407471 |
| F____BODEGA | 100.0% | 144000 |
| F____CAJÓN_EXTRA | 100.0% | -1 |
| F____UNIDAD | 100.0% | 3229670 |
| Frrecuencia_PM2 | 100.0% | 0.3333333333333333 |
| Frrecuencia_PU | 100.0% | 0.5 |
| Frrecuencia_TC | 100.0% | 0.3333333333333333 |
| GlobalID | 100.0% | af6be216-178e-4ea0-a5c0-571206cd9f2e |
| IDCONCAT | 100.0% | ARIA/-100.3105/25.6833 |
| INCREMENTO_POR_NIVEL | 100.0% | 10000 |
| INGRESO | 100.0% | 86522.4081162253 |
| INICIO_DE_VENTA | 100.0% | 1619049600000 |
| MESES_EN_INVENTARIO | 100.0% | 58 |
| MES_CARGA | 100.0% | 5 |
| NSE_INGRESO | 67.4% | C+ |
| No_ | 100.0% | 29 |
| Nombre | 100.0% | Aria |
| OBJECTID | 100.0% | 326548 |
| OBJECTID_1 | 100.0% | 251 |
| OrdenPM2 | 100.0% | 35 |
| OrdenPU | 100.0% | 6 |
| OrdenTC | 100.0% | 3 |
| PROYECTO | 100.0% | Aria |
| TIPO | 100.0% | 1 |
| UD_Demanda | 100.0% | 29 |
| UNIDADES_DISPONIBLES | 100.0% | 29 |
| UNIDADES_TOTALES | 100.0% | 130 |
| UNIDADES_VENDIDAS | 100.0% | 101 |
| UT_Demanda | 100.0% | 130 |
| UV_Demanda | 100.0% | 101 |
| X_coor | 100.0% | -100.31057719835287 |
| Y_coor | 100.0% | 25.683326444342892 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686960000000 |
| municipio | 100.0% | Monterrey |
| ÁREA_DE_BODEGA | 100.0% | 4.5 |
| ÁREA_DE_TERRAZA | 100.0% | 6.18 |
| ÁREA_PRIVATIVA | 100.0% | 39.59 |
| ÁREA_TOTAL | 100.0% | 45.77 |
| ÁREA_TOTAL_Demanda | 100.0% | 45.77 |

### vv_venta.pagos — 53 filas · 22 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ANIO_CARGA | 100.0% | 2026 |
| CONTRA_ESCRITURA | 98.1% | 0.8 |
| CORREDOR___ZONA | 100.0% | Centro |
| DIFERIDO | 75.5% | 0.1 |
| ENGANCHE | 98.1% | 0.1 |
| Esquema | 100.0% | 1 |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 2026-02-09 |
| GlobalID | 100.0% | 99fd2f7a-ee57-4780-864b-af18032b4b69 |
| IDCONCAT | 100.0% | ARIA/-100.3105/25.6833 |
| MESES_DE_DIFERIDO | 100.0% | 30 |
| MES_CARGA | 100.0% | 5 |
| NOTAS_ | 98.1% | Entrega Diciembre 2028. |
| Nombre | 100.0% | Aria |
| OBJECTID | 100.0% | 81893 |
| OBJECTID_1 | 100.0% | 52 |
| PROYECTO | 100.0% | Aria |
| X_coor | 100.0% | -100.31057719835287 |
| Y_coor | 100.0% | 25.683326444342892 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686960000000 |
| municipio | 100.0% | Monterrey |

### vv_venta.resumen — 35 filas · 81 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ABSORCIÓN_PROYECTO | 100.0% | 3.086206896551724 |
| ACABADO_EN_MURO | 100.0% | ● |
| ACCESORIOS_DE_BAÑO | 91.4% | ● |
| ALBERCA | 82.9% | ● |
| ANIO_CARGA | 100.0% | 2026 |
| ASADORES | 88.6% | ● |
| ASOLEADERO | 54.3% | ● |
| AVANCE_COMERCIAL | 100.0% | 0.788546255506608 |
| BAR | 40.0% | ● |
| BAÑO | 94.3% | ● |
| BOLICHE | 0.0% |  |
| BUSINESS_CENTER | 91.4% | ● |
| CANCELERÍA | 20.0% | ● |
| CANCHAS | 14.3% | ● |
| CASA_CLUB | 0.0% |  |
| CASETA_DE_VENTAS | 22.9% | ● |
| CAVA | 0.0% |  |
| CLOSETS | 14.3% | ● |
| COCINAS | 11.4% | ● |
| CORREDOR___ZONA | 100.0% | Centro |
| CUARTO_DE_SEGURIDAD | 0.0% |  |
| ELECTRODOMESTICOS | 8.6% | A/C, Bóiler, Parrilla y Campana. |
| ESTATUS | 100.0% | Comparable |
| Esquema | 100.0% | 1 |
| Estatus_Vendido | 100.0% | Activo |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 1770595200000 |
| FOGATERO | 25.7% | ● |
| F__M2_PROM | 100.0% | 70439.41699102378 |
| F__UD_PROM | 100.0% | 3565851.8976744185 |
| Ficha_Tecnica | 100.0% | <a href="https://prsp.maps.arcgis.com/apps/dashb |
| GAME_ROOM___VIRTUAL | 31.4% | ● |
| GIMNASIO | 94.3% | ● |
| GOLF | 0.0% |  |
| GlobalID | 100.0% | 2d72ca88-feb8-4970-8d8f-3011258f1c61 |
| HABITACIÓN_DE_HUESPEDES | 14.3% | ● |
| IDCONCAT | 100.0% | ARIA/-100.3105/25.6833 |
| ILUMINACIÓN_DE_INTERIORES | 42.9% | ● |
| INICIO_DE_VENTA | 100.0% | 1619049600000 |
| Imagen_URL | 100.0% | https://i.ibb.co/vcD2n8Z/aria.jpg |
| JUEGOS_PARA_NIÑOS | 48.6% | ● |
| LOBBY | 85.7% | ● |
| LUDOTECA | 42.9% | ● |
| MESES_EN_INVENTARIO | 100.0% | 58 |
| MES_CARGA | 100.0% | 5 |
| MOTOR_LOBBY | 11.4% | ● |
| No_ | 100.0% | 29 |
| Nombre | 100.0% | Aria |
| OBJECTID | 100.0% | 48872 |
| OBJECTID_1 | 100.0% | 29 |
| OTRO | 74.3% | Amazon Room, Open Kitchen, Regaderas. |
| OTROS | 20.0% | Canceles de cristal templado 9 mm, Ventanas duov |
| PET_FRIENDLY | 62.9% | ● |
| PISOS | 100.0% | Cerámico. |
| PLAFONES | 40.0% | ● |
| PROYECTO | 100.0% | Aria |
| PUERTAS | 97.1% | ● |
| RECORRIDO_VIRTUAL | 14.3% | ● |
| SALA_DE_CINE | 22.9% | ● |
| SALA_DE_PUROS | 0.0% |  |
| SALA_DE_TÉ | 0.0% |  |
| SALÓN_MULTIUSOS | 62.9% | ● |
| SAUNA_Y_VAPOR | 2.9% | ● |
| SHOWROOM | 85.7% | ● |
| SKY_LOUNGE | 51.4% | ● |
| SPA | 0.0% |  |
| UNIDADES_DISPONIBLES | 100.0% | 48 |
| UNIDADES_TOTALES | 100.0% | 227 |
| UNIDADES_VENDIDAS | 100.0% | 179 |
| USOS_MIXTOS | 88.6% | Comercio |
| VITAPISTA | 5.7% | ● |
| X_coor | 100.0% | -100.31057719835287 |
| Y_coor | 100.0% | 25.683326444342892 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686960000000 |
| geometry_x | 100.0% | -100.31057719799998 |
| geometry_y | 100.0% | 25.683326444000045 |
| municipio | 100.0% | Monterrey |
| ÁREA_SOCIAL | 91.4% | ● |
| ÁREA_TOTAL_PROM | 100.0% | 52.704140969163 |
| ÁREA_VERDE | 45.7% | ● |

## ZONA GUADALUPE · consulta: anillo_consulta_2.5km (solo dump de campos)

### di.kmz — 63 filas · 8 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| area_km2 | 100.0% | 0.5836 |
| attrs | 100.0% | {'XI_Nivel socioeconómico por ingreso': 'B'} |
| lat | 100.0% | 25.656319 |
| lng | 100.0% | -100.264916 |
| n_vertices | 100.0% | 170 |
| nse_rank | 100.0% | 2 |
| nse_txt | 100.0% | B |
| ring | 100.0% | [[-100.25872, 25.66192], [-100.25915, 25.66132], |

### di.xlsx — 63 filas · 252 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| 0 a 4 | 100.0% | 178.2663402467 |
| 10 a 14 | 100.0% | 199.0216678819 |
| 15 a 19 | 100.0% | 222.5526248349 |
| 20 a 24 | 100.0% | 243.6888278481 |
| 20 a 24 casada | 100.0% | 115 |
| 20 a 24 en union libre | 100.0% | 26 |
| 20 a 24 no especifico | 100.0% | 1 |
| 20 a 24 separad  divorcia | 100.0% | 21 |
| 20 a 24 soltera | 100.0% | 81 |
| 25 a 29 | 100.0% | 197.6338532229 |
| 25 a 29 casada | 100.0% | 93 |
| 25 a 29 en union libre | 100.0% | 21 |
| 25 a 29 no especifico | 100.0% | 1 |
| 25 a 29 separad  divorcia | 100.0% | 17 |
| 25 a 29 soltera | 100.0% | 66 |
| 30 a 34 | 100.0% | 184.8531038167 |
| 30 a 34 casada | 100.0% | 87 |
| 30 a 34 en union libre | 100.0% | 19 |
| 30 a 34 no especifico | 100.0% | 1 |
| 30 a 34 separad  divorcia | 100.0% | 16 |
| 30 a 34 soltera | 100.0% | 62 |
| 35 a 39 | 100.0% | 187.2859452943 |
| 35 a 39 casada | 100.0% | 88 |
| 35 a 39 en union libre | 100.0% | 20 |
| 35 a 39 no especifico | 100.0% | 1 |
| 35 a 39 separad  divorcia | 100.0% | 16 |
| 35 a 39 soltera | 100.0% | 62 |
| 40 a 44 | 100.0% | 200.2761761585 |
| 40 a 44 casada | 100.0% | 94 |
| 40 a 44 en union libre | 100.0% | 21 |
| 40 a 44 no especifico | 100.0% | 1 |
| 40 a 44 separad  divorcia | 100.0% | 18 |
| 40 a 44 soltera | 100.0% | 67 |
| 45 a 49 | 100.0% | 166.1164156855 |
| 45 a 49 casada | 100.0% | 78 |
| 45 a 49 en union libre | 100.0% | 17 |
| 45 a 49 no especifico | 100.0% | 0 |
| 45 a 49 separad  divorcia | 100.0% | 15 |
| 45 a 49 soltera | 100.0% | 55 |
| 5 a 9 | 100.0% | 187.6620597302 |
| 50 a 54 | 100.0% | 164.3310623507 |
| 50 a 54 casada | 100.0% | 77 |
| 50 a 54 en union libre | 100.0% | 17 |
| 50 a 54 no especifico | 100.0% | 0 |
| 50 a 54 separad  divorcia | 100.0% | 14 |
| 50 a 54 soltera | 100.0% | 55 |
| 55 a 59 | 100.0% | 128.8406185254 |
| 55 a 59 casada | 100.0% | 61 |
| 55 a 59 en union libre | 100.0% | 14 |
| 55 a 59 no especifico | 100.0% | 0 |
| 55 a 59 separad  divorcia | 100.0% | 11 |
| 55 a 59 soltera | 100.0% | 43 |
| 60 a 64 | 100.0% | 110.0110920208 |
| 60 a 64 casada | 100.0% | 65 |
| 60 a 64 en union libre | 100.0% | 2 |
| 60 a 64 no especifico | 100.0% | 0 |
| 60 a 64 separad | 100.0% | 35 |
| 60 a 64 soltera | 100.0% | 8 |
| 65 a 69 | 100.0% | 95.8401474845 |
| 65 a 69 casada | 100.0% | 56 |
| 65 a 69 en union libre | 100.0% | 2 |
| 65 a 69 no especifico | 100.0% | 0 |
| 65 a 69 separad | 100.0% | 30 |
| 65 a 69 soltera | 100.0% | 7 |
| 70 a 74 | 100.0% | 71.9997292868 |
| 70 a 74 casada | 100.0% | 42 |
| 70 a 74 en union libre | 100.0% | 1 |
| 70 a 74 no especifico | 100.0% | 0 |
| 70 a 74 separad | 100.0% | 23 |
| 70 a 74 soltera | 100.0% | 5 |
| 75 y Más | 100.0% | 99.6203356121 |
| 75 y Más casada | 100.0% | 59 |
| 75 y Más en union libre | 100.0% | 2 |
| 75 y Más no especifico | 100.0% | 0 |
| 75 y Más separad | 100.0% | 32 |
| 75 y Más soltera | 100.0% | 7 |
| AREA | 100.0% | 44.36037246957028 |
| AREA_ORIG | 0.0% |  |
| Adolescentes | 100.0% | 199.0216678819 |
| Afinidad NSE | 100.0% | SI |
| Alquilada | 100.0% | 165.8740211178 |
| CVEGEO | 100.0% | 1903900011120 |
| Casa | 100.0% | 827.2249411951 |
| Consolidados | 100.0% | 902.8627033057 |
| Corporativos | 100.0% | 3.0265848553 |
| Corporativos m2 | 100.0% | 45.3987728295 |
| Demanda ACEM | 92.1% | 2.743814714307252 |
| Demanda CHC | 92.1% | 0.43069326096788785 |
| Demanda CME | 92.1% | 9.746919282375998 |
| Demanda CMG | 92.1% | 13.845762822252373 |
| Demanda Cuidado_personal | 92.1% | 301.9007700437208 |
| Demanda CuidadodeSalud | 92.1% | 60.93825190713101 |
| Demanda Educacion | 92.1% | 363.3575389868838 |
| Demanda Entretenimiento | 92.1% | 235.060926458616 |
| Demanda HSP | 92.1% | 15.953830815618876 |
| Demanda Hospitalización | 92.1% | 14.925374038896425 |
| Demanda MV | 92.1% | 66.39125403286597 |
| Demanda Muebleria | 92.1% | 69.08279136137494 |
| Demanda Otros | 92.1% | 3.2918569727121962 |
| Demanda Restaurantes | 92.1% | 293.82615807327 |
| Demanda Retail | 92.1% | 481.7851813206694 |
| Demanda Servicios | 92.1% | 243.1355384290668 |
| Demanda Supermercado | 92.1% | 1655.7440449419569 |
| Demanda anual vivienda | 100.0% | 1 |
| Demanda anual vivienda renta | 100.0% | 0 |
| Demanda de Vivienda en Renta de EUA | 93.7% | 0 |
| Demanda de Vivienda en Renta de otro país | 93.7% | 0 |
| Demanda de Vivienda en Venta de EUA | 93.7% | 0 |
| Demanda de Vivienda en Venta de otro país | 93.7% | 0 |
| Densidad de población | 100.0% | 59.47 |
| Densidad de población 2022 | 100.0% | 59.47 |
| Departamento o edificio | 100.0% | 50.8905437726 |
| ECO1 | 100.0% | 1260 |
| ECO25 | 100.0% | 50 |
| ECO4 | 100.0% | 1210 |
| EDU49_R | 100.0% | 12.5 |
| Educacion | 100.0% | Bachillerato,Preparatoria o equivalente |
| Estado | 100.0% | Nuevo León |
| Factor precio | 100.0% | 237.42 |
| Factor precio Oferta | 100.0% | 422.08 |
| Factor precio Total | 100.0% | 659.5 |
| Gasto Análisis clínicos y estudios médicos | 92.1% | 18199.723 |
| Gasto Consultas médico especialista | 92.1% | 64651.3156 |
| Gasto Consultas médico general | 92.1% | 91838.9448 |
| Gasto Cuidado de la salud | 92.1% | 404203.4249 |
| Gasto Cuidado personal | 92.1% | 2002507.8077 |
| Gasto Cuotas a hospitales o clínicas | 92.1% | 2856.7884 |
| Gasto Educación | 92.1% | 2410150.5561 |
| Gasto Entretenimiento | 92.1% | 1559159.1252 |
| Gasto Honorarios por servicios profesionales | 92.1% | 105821.7598 |
| Gasto Hospitalización | 92.1% | 99000.006 |
| Gasto Mantenimiento de la vivienda | 92.1% | 440373.188 |
| Gasto Mueblería | 92.1% | 458226.1551 |
| Gasto Otros: pago de enfermeras y personal al cuidado de enfermos | 92.1% | 21834.8873 |
| Gasto Restaurantes | 92.1% | 1948948.9065 |
| Gasto Retail | 92.1% | 3195681.1077 |
| Gasto Servicios | 92.1% | 1612718.0264 |
| Gasto Supermercado | 92.1% | 10982550.2501 |
| Gasto por exhibición Análisis clínicos y estudios médicos | 92.1% | 462 |
| Gasto por exhibición Consultas médico especialista | 92.1% | 401 |
| Gasto por exhibición Consultas médico general | 92.1% | 102 |
| Gasto por exhibición Cuotas a hospitales o clínicas | 92.1% | 1010 |
| Gasto por exhibición Honorarios por servicios profesionales | 92.1% | 6476 |
| Gasto por exhibición Hospitalización | 92.1% | 5330 |
| Gasto por exhibición Otros: pago de enfermeras y personal al cuidado de enfermos | 92.1% | 1518 |
| Hogares  ampliados | 100.0% | 240.4828828745 |
| Hogares  no familiares totales | 100.0% | 119.06192256 |
| Hogares  otra situación | 100.0% | 15.2311642641 |
| Hogares compuestos | 100.0% | 17.4414698341 |
| Hogares corresidentes | 100.0% | 20.4783673129 |
| Hogares de dos recámaras | 100.0% | 531.2609277802001 |
| Hogares desocupados  2026 | 100.0% | 101 |
| Hogares familiares totales | 100.0% | 783.93807744 |
| Hogares nucleares | 100.0% | 510.7825604673 |
| Hogares ocupados 2020 | 100.0% | 892 |
| Hogares ocupados 2026 | 100.0% | 903 |
| Hogares totales 2020 | 100.0% | 992 |
| Hogares totales 2026 | 100.0% | 1004 |
| Hogares unipersonales | 100.0% | 98.5835552471 |
| IXH | 100.0% | 32951.21277636605 |
| Información en medios masivos | 100.0% | 0.2989987754 |
| Información en medios masivos m2 | 100.0% | 4.484981631 |
| Ingreso Residual | 92.1% | 5144630.0142 |
| Ingresos totales 2026 | 100.0% | 29754945.13705854 |
| Jovenes | 100.0% | 222.5526248349 |
| Jovenes_adultos | 100.0% | 441.32268107100003 |
| MIG11 | 100.0% | 29 |
| MIG14 | 100.0% | 0 |
| MIG15 | 100.0% | 0 |
| MIG8 | 100.0% | 2501 |
| Mercado en renta | 93.7% | 18 |
| Mercado en venta | 93.7% | 69 |
| Municipio | 100.0% | Monterrey |
| NSE PER | 92.1% | D+ |
| Nesters | 100.0% | 506.31192292960003 |
| Niños | 100.0% | 365.9283999769 |
| OBJECTID_1 | 100.0% | 32018 |
| Orden V Casa | 100.0% | 2 |
| OrdenNSE | 100.0% | 4 |
| OrdenNSEPER | 100.0% | 5 |
| Orden_Educacion | 100.0% | 3 |
| Otra situación | 100.0% | 24.3677763685 |
| Otro tipo de vivienda | 100.0% | 0.0327232116 |
| Otros servicios excepto actividades gubernamentales | 100.0% | 1.0342976732 |
| Otros servicios excepto actividades gubernamentales m2 | 100.0% | 15.514465098 |
| PEA 2026 | 100.0% | 1275 |
| PEA desocupada 2026 | 100.0% | 51 |
| PEA ocupada 2026 | 100.0% | 1225 |
| POB1 | 100.0% | 2607 |
| PXHFAMILIARES | 93.7% | 3.2 |
| PXHNOFAMILIARES | 93.7% | 1.1 |
| Personas de 5 a 130 años de edad que en el 2020 residían
en otra entidad federativa. | 100.0% | 29 |
| Personas por hogar 2026 | 93.7% | 2.9 |
| Población  corresidente | 100.0% | 46.2060013788 |
| Población  nucleares | 100.0% | 1388.8581604366 |
| Población  unipersonal | 100.0% | 81.6114298212 |
| Población ampliados | 100.0% | 981.042002044 |
| Población compuestos | 100.0% | 71.2982718148 |
| Población de 5 años
y más residente en la
entidad en marzo de
2020 | 100.0% | 2501 |
| Población familiar total | 100.0% | 2510.1825688 |
| Población no familiar total | 100.0% | 127.8174312 |
| Población otra situación | 100.0% | 68.9841345046 |
| Población total 2026 | 100.0% | 2638 |
| Población total estimada 2021 | 100.0% | 2612.214 |
| Población total estimada 2023 | 100.0% | 2622.673304856 |
| Población total estimada 2024 | 100.0% | 2627.918651465712 |
| Población total estimada 2025 | 100.0% | 2633.1744887686436 |
| Población total estimada 2026 | 100.0% | 2638.440837746181 |
| Población total estimada 2027 | 100.0% | 2643.7177194216733 |
| Población total estimada 2028 | 100.0% | 2649.0051548605165 |
| Población total estimada 2029 | 100.0% | 2654.3031651702377 |
| Población total estimada 2030 | 100.0% | 2659.611771500578 |
| Porcentaje de hogares con automóvil 2026 | 100.0% | 75.5 |
| Porcentaje de hogares sin automóvil 2026 | 100.0% | 24.5 |
| PorcentajeDeCasa | 100.0% | 0.05251767891633288 |
| PorcentajeDeGasto | 92.1% | 0.00038495458645672 |
| Prestada | 100.0% | 87.0974714613 |
| Propia | 100.0% | 625.6607310524 |
| Rangos de densidad pob | 100.0% | 39 |
| Rangos demanda vivienda | 92.1% | $1,200,000-$1,499,999 |
| Rangos demanda vivienda numerico | 92.1% | 7 |
| Rangos demanda vivienda numerico renta | 92.1% | 7 |
| Rangos demanda vivienda renta | 92.1% | $6,000-$7,499 |
| RangosDemandaLotes | 92.1% | 400,000 - 500,000 |
| RangosDemandaLotesNumero | 92.1% | 7 |
| Servicios financieros y de seguros | 100.0% | 9.2422482208 |
| Servicios financieros y de seguros m2 | 100.0% | 138.633723312 |
| Servicios inmobiliarios y de alquiler de bienes muebles e intangibles | 100.0% | 1.7291654566 |
| Servicios inmobiliarios y de alquiler de bienes muebles e intangibles m2 | 100.0% | 25.937481849 |
| Servicios profesionales científicos y técnicos | 100.0% | 4.6972094561 |
| Servicios profesionales científicos y técnicos m2 | 100.0% | 70.4581418415 |
| Shape_Area | 0.0% |  |
| Shape__Area | 100.0% | 443603.72265625 |
| Shape__Length | 100.0% | 2824.991550073955 |
| Tasa de crecimiento AGEB | 100.0% | 0.2 |
| Tasa de crecimiento AGEB personas de EUA | 100.0% | 0 |
| Tasa de crecimiento AGEB personas de otro país | 100.0% | 0 |
| Tasa de crecimiento anual | 100.0% | 1.2 |
| Tasa de crecimiento de los últimos 5 años | 100.0% | 1.1 |
| Tasa de crecimiento de los últimos 5 años de personas de EUA | 100.0% | 0 |
| Tasa de crecimiento de los últimos 5 años de personas de otro pais | 100.0% | 0 |
| Tasa de crecimiento factor | 100.0% | 1.1 |
| V CASAS | 100.0% | 1230000 |
| VIV0 | 100.0% | 992 |
| VIV1 | 100.0% | 892 |
| VIV29 | 100.0% | 674 |
| VIV92_R | 100.0% | 2.9 |
| V_RENTA | 100.0% | 6150 |
| Vivienda en vecidad o cuartería | 100.0% | 11.7149097666 |
| Vivienda no específica | 100.0% | 13.1368820541 |
| Viviendas habitadas que disponen de automovil 2026 | 100.0% | 682 |
| XI_Nivel socioeconómico por ingreso | 100.0% | C |

### vv_renta.ft — 18 filas · 36 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| AMUEBLADO | 61.1% | ● |
| ANIO_CARGA | 100.0% | 2023 |
| CAJONES_ASIGNADOS | 100.0% | 2 |
| CANTIDAD_DE_RECAMARAS | 100.0% | 2 |
| CORREDOR___ZONA | 100.0% | Linda Vista |
| ELECTRODOMESTICOS | 61.1% | ● |
| ESTATUS | 38.9% | Comparable |
| Esquema | 100.0% | 2 |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 2023-06-17 |
| F__M2_Demanda | 100.0% | 168.067226890756 |
| F___M2 | 100.0% | 168.067226890756 |
| F___UM_Demanda | 100.0% | 20000 |
| F____RECAMARA | 100.0% | 10000 |
| F____UNIDAD_MENSUAL | 100.0% | 20000 |
| Frrecuencia_PU | 100.0% | 1 |
| GlobalID | 100.0% | 8f7cdcdb-4bb2-49a6-ba4b-f0bc8fc0c99c |
| IDCONCAT | 100.0% | ALBANALINDAVISTA/-100.2436/25.6957 |
| MES_CARGA | 100.0% | 4 |
| NO_AMUEBLADO | 38.9% | ● |
| No_ | 100.0% | 8 |
| Nombre | 100.0% | Albana Linda Vista |
| OBJECTID | 100.0% | 274 |
| OBJECTID_1 | 100.0% | 24 |
| OrdenPU | 100.0% | 2 |
| PROYECTO | 100.0% | Albana Linda Vista |
| TIPO | 100.0% | 1 |
| X_coor | 100.0% | -100.24366917699996 |
| Y_coor | 100.0% | 25.69576086400008 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686960000000 |
| municipio | 100.0% | Guadalupe |
| ÁREA_DE_TERRAZA | 100.0% | 9 |
| ÁREA_PRIVATIVA | 100.0% | 110 |
| ÁREA_TOTAL | 100.0% | 119 |
| ÁREA_TOTAL_Demanda | 100.0% | 119 |

### vv_renta.pagos — 0 filas · 0 campos

| Campo | Presencia | Ejemplo |
|---|---|---|

### vv_renta.resumen — 18 filas · 61 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ALBERCA | 61.1% | ● |
| AMUEBLADO | 61.1% | ● |
| ANIO_CARGA | 100.0% | 2023 |
| ASADORES | 61.1% | ● |
| ASOLEADERO | 0.0% |  |
| BAR | 0.0% |  |
| BOLICHE | 0.0% |  |
| BUSINESS_CENTER | 0.0% |  |
| CANCHAS | 0.0% |  |
| CASA_CLUB | 0.0% |  |
| CAVA | 0.0% |  |
| CORREDOR___ZONA | 100.0% | Linda Vista |
| CUARTO_DE_SEGURIDAD | 0.0% |  |
| ELECTRODOMESTICOS | 61.1% | ● |
| ESTATUS | 0.0% |  |
| Esquema | 100.0% | 2 |
| Estado | 100.0% | Nuevo León |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 1686960000000 |
| FOGATERO | 0.0% |  |
| F__M2_PROM | 100.0% | 168.0672268907563 |
| F___REC | 100.0% | 10000 |
| F____UNIDAD_MENSUAL_PROM | 100.0% | 20000 |
| Ficha_Tecnica | 100.0% | <a href="https://prsp.maps.arcgis.com/apps/dashb |
| GAME_ROOM___VIRTUAL | 0.0% |  |
| GIMNASIO | 61.1% | ● |
| GOLF | 0.0% |  |
| GlobalID | 100.0% | 2571e6fb-ec39-402b-beec-d9e5e0c9ce11 |
| HABITACIÓN_DE_HUESPEDES | 0.0% |  |
| IDCONCAT | 100.0% | ALBANALINDAVISTA/-100.2436/25.6957 |
| Imagen_URL | 100.0% | https://fcisphvgvinfqjwkamql.supabase.co/storage |
| JUEGOS_PARA_NIÑOS | 0.0% |  |
| LOBBY | 0.0% |  |
| LUDOTECA | 0.0% |  |
| MES_CARGA | 100.0% | 4 |
| MOTOR_LOBBY | 0.0% |  |
| Municipio | 100.0% | Guadalupe |
| NO_AMUEBLADO | 38.9% | ● |
| No_ | 100.0% | 8 |
| Nombre | 100.0% | Albana Linda Vista |
| OBJECTID | 100.0% | 8 |
| OBJECTID_1 | 100.0% | 1 |
| OTRO | 0.0% |  |
| PET_FRIENDLY | 0.0% |  |
| PROYECTO | 100.0% | Albana Linda Vista |
| SALA_DE_CINE | 0.0% |  |
| SALA_DE_PUROS | 0.0% |  |
| SALA_DE_TÉ | 0.0% |  |
| SALÓN_MULTIUSOS | 0.0% |  |
| SAUNA_Y_VAPOR | 0.0% |  |
| SKY_LOUNGE | 61.1% | ● |
| SPA | 0.0% |  |
| USOS_MIXTOS | 38.9% | ● |
| VITAPISTA | 0.0% |  |
| X_coor | 100.0% | -100.24366917699996 |
| Y_coor | 100.0% | 25.69576086400008 |
| Zona | 100.0% | Noreste |
| geometry_x | 100.0% | -100.24366917699996 |
| geometry_y | 100.0% | 25.69576086400008 |
| ÁREA_SOCIAL | 0.0% |  |
| ÁREA_TOTAL_PROM | 100.0% | 119 |
| ÁREA_VERDE | 61.1% | ● |

### vv_venta.ft — 24 filas · 53 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ABSORCIÓN | 100.0% | 0.8333333333333334 |
| ANIO_CARGA | 100.0% | 2026 |
| AVANCE_COMERCIAL | 100.0% | 1 |
| Abs_Demanda | 100.0% | 0.8333333333333334 |
| CAJONES_ASIGNADOS | 100.0% | 1 |
| CANTIDAD_DE_RECAMARAS | 100.0% | 1 |
| CORREDOR___ZONA | 100.0% | Centro |
| ESTATUS | 100.0% | Comparable |
| Esquema | 100.0% | 1 |
| Estatus_Vendido | 100.0% | Activo |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 2026-02-09 |
| F__M2_Demanda | 50.0% | 99449.14036996735 |
| F___M2 | 100.0% | -1 |
| F____BODEGA | 100.0% | -1 |
| F____CAJÓN_EXTRA | 100.0% | -1 |
| F____UNIDAD | 100.0% | -1 |
| Frrecuencia_PM2 | 100.0% | 0.3333333333333333 |
| Frrecuencia_PU | 100.0% | 0.3333333333333333 |
| Frrecuencia_TC | 100.0% | 0.3333333333333333 |
| GlobalID | 100.0% | 2ca70da2-9d97-4e7c-8ecb-0a121051a195 |
| IDCONCAT | 100.0% | NOVUSFUNDIDORA-TORRE1/-100.2790/25.6823 |
| INCREMENTO_POR_NIVEL | 100.0% | -1 |
| INGRESO | 100.0% | -1 |
| INICIO_DE_VENTA | 100.0% | 1582675200000 |
| MESES_EN_INVENTARIO | 100.0% | 72 |
| MES_CARGA | 100.0% | 5 |
| NSE_INGRESO | 50.0% | A |
| No_ | 100.0% | 228 |
| Nombre | 100.0% | Novus Fundidora - Torre 1 |
| OBJECTID | 100.0% | 326655 |
| OBJECTID_1 | 100.0% | 1723 |
| OrdenPM2 | 100.0% | -1 |
| OrdenPU | 100.0% | -1 |
| OrdenTC | 100.0% | 4 |
| PROYECTO | 100.0% | Novus Fundidora - Torre 1 |
| TIPO | 100.0% | 1 |
| UD_Demanda | 100.0% | 0 |
| UNIDADES_DISPONIBLES | 100.0% | 0 |
| UNIDADES_TOTALES | 100.0% | 60 |
| UNIDADES_VENDIDAS | 100.0% | 60 |
| UT_Demanda | 100.0% | 60 |
| UV_Demanda | 100.0% | 60 |
| X_coor | 100.0% | -100.27901529957877 |
| Y_coor | 100.0% | 25.68233583675063 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686960000000 |
| municipio | 100.0% | Monterrey |
| ÁREA_DE_BODEGA | 100.0% | 4 |
| ÁREA_DE_TERRAZA | 100.0% | -1 |
| ÁREA_PRIVATIVA | 100.0% | 52.9 |
| ÁREA_TOTAL | 100.0% | 52.9 |
| ÁREA_TOTAL_Demanda | 100.0% | 52.9 |

### vv_venta.pagos — 6 filas · 22 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ANIO_CARGA | 100.0% | 2026 |
| CONTRA_ESCRITURA | 66.7% | 0.85 |
| CORREDOR___ZONA | 100.0% | Centro |
| DIFERIDO | 83.3% | 0.05 |
| ENGANCHE | 100.0% | 0.1 |
| Esquema | 100.0% | 1 |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 2026-02-09 |
| GlobalID | 100.0% | 74c06945-e144-4cbf-aca7-0c7cbe12c26e |
| IDCONCAT | 100.0% | NOVUSFUNDIDORA-TORRE1/-100.2790/25.6823 |
| MESES_DE_DIFERIDO | 100.0% | 10 |
| MES_CARGA | 100.0% | 5 |
| NOTAS_ | 100.0% | Entrega Noviembre 2026. |
| Nombre | 100.0% | Novus Fundidora - Torre 1 |
| OBJECTID | 100.0% | 81905 |
| OBJECTID_1 | 100.0% | 353 |
| PROYECTO | 100.0% | Novus Fundidora - Torre 1 |
| X_coor | 100.0% | -100.27901529957877 |
| Y_coor | 100.0% | 25.68233583675063 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686960000000 |
| municipio | 100.0% | Monterrey |

### vv_venta.resumen — 6 filas · 81 campos

| Campo | Presencia | Ejemplo |
|---|---|---|
| ABSORCIÓN_PROYECTO | 100.0% | 3.513888888888889 |
| ACABADO_EN_MURO | 83.3% | ● |
| ACCESORIOS_DE_BAÑO | 66.7% | ● |
| ALBERCA | 100.0% | ● |
| ANIO_CARGA | 100.0% | 2026 |
| ASADORES | 100.0% | ● |
| ASOLEADERO | 83.3% | ● |
| AVANCE_COMERCIAL | 100.0% | 0.98828125 |
| BAR | 16.7% | ● |
| BAÑO | 100.0% | ● |
| BOLICHE | 0.0% |  |
| BUSINESS_CENTER | 83.3% | ● |
| CANCELERÍA | 0.0% |  |
| CANCHAS | 33.3% | ● |
| CASA_CLUB | 0.0% |  |
| CASETA_DE_VENTAS | 50.0% | ● |
| CAVA | 0.0% |  |
| CLOSETS | 0.0% |  |
| COCINAS | 16.7% | ● |
| CORREDOR___ZONA | 100.0% | Centro |
| CUARTO_DE_SEGURIDAD | 0.0% |  |
| ELECTRODOMESTICOS | 16.7% | Parrilla Eléctrica, Horno Eléctrico, Microocampa |
| ESTATUS | 100.0% | Comparable |
| Esquema | 100.0% | 1 |
| Estatus_Vendido | 100.0% | Activo |
| FECHA_DE_LEVANTAMIENTO | 100.0% | 1770595200000 |
| FOGATERO | 33.3% | ● |
| F__M2_PROM | 100.0% | 96308.47967155975 |
| F__UD_PROM | 100.0% | 7528570.536666667 |
| Ficha_Tecnica | 100.0% | <a href="https://prsp.maps.arcgis.com/apps/dashb |
| GAME_ROOM___VIRTUAL | 0.0% |  |
| GIMNASIO | 66.7% | ● |
| GOLF | 0.0% |  |
| GlobalID | 100.0% | e7116a64-8966-4724-9047-3998bf4b2ea7 |
| HABITACIÓN_DE_HUESPEDES | 0.0% |  |
| IDCONCAT | 100.0% | NOVUSFUNDIDORA-TORRE1/-100.2790/25.6823 |
| ILUMINACIÓN_DE_INTERIORES | 16.7% | LED. |
| INICIO_DE_VENTA | 100.0% | 1582675200000 |
| Imagen_URL | 100.0% | https://i.ibb.co/wY226zv/novus-fundidora.jpg |
| JUEGOS_PARA_NIÑOS | 83.3% | ● |
| LOBBY | 16.7% | ● |
| LUDOTECA | 16.7% | ● |
| MESES_EN_INVENTARIO | 100.0% | 72 |
| MES_CARGA | 100.0% | 5 |
| MOTOR_LOBBY | 0.0% |  |
| No_ | 100.0% | 228 |
| Nombre | 100.0% | Novus Fundidora - Torre 1 |
| OBJECTID | 100.0% | 48884 |
| OBJECTID_1 | 100.0% | 228 |
| OTRO | 66.7% | Tumbonas, Snack Bar, Centro Culinario, Wellnes C |
| OTROS | 0.0% |  |
| PET_FRIENDLY | 100.0% | ● |
| PISOS | 83.3% | ● |
| PLAFONES | 16.7% | ● |
| PROYECTO | 100.0% | Novus Fundidora - Torre 1 |
| PUERTAS | 83.3% | ● |
| RECORRIDO_VIRTUAL | 66.7% | ● |
| SALA_DE_CINE | 16.7% | ● |
| SALA_DE_PUROS | 0.0% |  |
| SALA_DE_TÉ | 0.0% |  |
| SALÓN_MULTIUSOS | 50.0% | ● |
| SAUNA_Y_VAPOR | 0.0% |  |
| SHOWROOM | 100.0% | ● |
| SKY_LOUNGE | 0.0% |  |
| SPA | 0.0% |  |
| UNIDADES_DISPONIBLES | 100.0% | 3 |
| UNIDADES_TOTALES | 100.0% | 256 |
| UNIDADES_VENDIDAS | 100.0% | 253 |
| USOS_MIXTOS | 33.3% | Comercio |
| VITAPISTA | 50.0% | ● |
| X_coor | 100.0% | -100.27901529957877 |
| Y_coor | 100.0% | 25.68233583675063 |
| Zona | 100.0% | Noreste |
| estado | 100.0% | Nuevo León |
| f_collector | 100.0% | 1686960000000 |
| geometry_x | 100.0% | -100.27901529999997 |
| geometry_y | 100.0% | 25.68233583700004 |
| municipio | 100.0% | Monterrey |
| ÁREA_SOCIAL | 83.3% | ● |
| ÁREA_TOTAL_PROM | 100.0% | 66.08671875 |
| ÁREA_VERDE | 83.3% | ● |
