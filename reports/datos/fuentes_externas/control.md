# Fuentes externas (D-015)

> **Advertencia (D-010):** todos los indicadores son de CONTEXTO de la sección o del municipio. Las correlaciones son descriptivas, a nivel agregado; no se atribuyen a las personas de un perfil (falacia ecológica) ni implican causa (D-010).

## 1. ECEG 2020: lectura y valores no disponibles

- Archivo: `INE_SECCION_2020.csv`, 68,806 secciones, 226 columnas (leído como texto).
- Valores no numéricos en TODAS las columnas (vacíos, `*`, `N/D`, etc.): **0** celdas . Códigos negativos (no disponible/confidencial, no documentados en el descriptor; inferidos por ser conteos imposibles): {-6: 1298, -9.0: 5} en 7 secciones; se convierten a NULL en las columnas usadas. Los demás NULL provienen de denominadores = 0.
- TIPO -> U/M/R: M=6,386, R=18,605, U=43,815 (D-015).

### Fórmulas (proporciones en [0,1]; NULL si denominador = 0)

| Descriptor | Fórmula | Denominador | min | max | nulos |
|---|---|---|---|---|---|
| `prop_sin_escolaridad` | P15YM_SE / P_15YMAS | población de 15+ | 0.0000 | 0.8450 | 72 |
| `prop_analfabeta` | P15YM_AN / P_15YMAS | población de 15+ | 0.0000 | 1.0000 | 72 |
| `prop_posbasica` | P18YM_PB / P_18YMAS | población de 18+ | 0.0000 | 1.0000 | 72 |
| `prop_hli` | P3YM_HLI / P_3YMAS | población de 3+ | 0.0000 | 1.0000 | 72 |
| `prop_afro` | POB_AFRO / POBTOT | población total | 0.0000 | 0.9935 | 72 |
| `prop_internet` | VPH_INTER / TVIVPARHAB | total de viviendas particulares habitadas | 0.0000 | 1.0000 | 76 |
| `prop_celular` | VPH_CEL / TVIVPARHAB | total de viviendas particulares habitadas | 0.0000 | 1.0000 | 76 |
| `prop_nacida_otra_ent` | PNACOE / POBTOT | población total | 0.0000 | 1.0000 | 72 |
| `prop_res_otra_ent_2015` | PRESOE15 / P_5YMAS | población de 5+ | 0.0000 | 0.8436 | 72 |
| `prop_discapacidad` | PCON_DISC / POBTOT | población total | 0.0000 | 0.5000 | 72 |
| `prop_18a24` | P_18A24 / P_18YMAS | población de 18+ | 0.0000 | 0.9575 | 72 |
| `prop_60ymas` | P_60YMAS / P_18YMAS | población de 18+ | 0.0000 | 1.0000 | 72 |
| `graproes` | GRAPROES (años, tal cual) | población de 15+ | | | 6 |
| `pobtot_eceg`, `p_18ymas_eceg` | POBTOT, P_18YMAS (conteos) | | | | 0 |

Los conteos `pobtot_eceg` y `p_18ymas_eceg` se dejan en NULL en secciones heredadas (no son la población de la sección hija).
Nota: VPH_INTER y VPH_CEL se dividen entre TVIVPARHAB: con VIVPAR_HAB 2,110 secciones excedían 1; con TVIVPARHAB, 0.

## 2. Cobertura ECEG

- **2021:** 68,806 de 68,812 secciones (99.99%); LN 100.00%.
- **2024 directa:** 67,976 de 70,751 secciones (96.08%); LN 94.72%.
- **2024 con herencia:** 2,775 de 2,775 secciones faltantes resueltas (100.00%); LN resuelta 100.00% de la faltante. Cobertura total 2024: 100.00% secciones, 100.00% LN.
- No resueltas: 0 (LN 0) [].

### Validación de las secciones madre (tabla de equivalencias de Magar vs CCPC)

- Madres distintas (raíces en ECEG): 779; presentes en CCPC 2021: 779 (100.00%); sin registro en CCPC 2021: 0.
- Madres marcadas en la tabla como divididas (`split.to`) o con año de baja: 666 (85.49%); madres que siguen vigentes en 2024: 167.
- Secciones heredadas por cadena (la madre inmediata tampoco está en ECEG, se sube a su origen): 8.
- Conflictos (varias madres en ECEG; se toma la de mayor LN 2021, empate = menor número): **3**.
  - (14, 3664) <- [(14, 2396), (14, 2399), (14, 2400), (14, 2406), (14, 2415)], elegida (14, 2400)
  - (21, 2764) <- [(21, 405), (21, 406)], elegida (21, 405)
  - (29, 645) <- [(29, 296), (29, 298)], elegida (29, 296)
- Conservación de LN por familia (LN 2024 de hijas + madres vigentes / LN 2021 de las madres), 773 familias; cuantiles 5/25/50/75/95: {0.05: 0.967, 0.25: 1.042, 0.5: 1.08, 0.75: 1.133, 0.95: 1.371}. Es descriptivo: no se fija umbral.

## 3. Indicador de residencia (D-013): `razon_ln_p18`

- LN CCPC 2021 (SEXO<2) de la sección / P_18YMAS. Secciones con cruce directo: 68,806 de 68,812; con valor no nulo: 68,734.
- Nacional: min 0.001; p1 0.548; p5 0.803; p10 0.905; p25 1.032; **p50 1.138**; p75 1.259; p90 1.434; p95 1.637; p99 2.730; max 405.667.

| edo | n | p10 | p50 | p90 |
|---|---|---|---|---|
| 1 | 622 | 0.968 | 1.152 | 1.282 |
| 2 | 2,014 | 0.891 | 1.141 | 1.488 |
| 3 | 484 | 0.858 | 1.100 | 1.447 |
| 4 | 532 | 0.905 | 1.093 | 1.308 |
| 5 | 1,699 | 0.912 | 1.139 | 1.478 |
| 6 | 370 | 0.967 | 1.166 | 1.357 |
| 7 | 2,097 | 0.871 | 1.135 | 1.518 |
| 8 | 3,195 | 0.900 | 1.198 | 1.590 |
| 9 | 5,527 | 0.937 | 1.129 | 1.324 |
| 10 | 1,369 | 0.954 | 1.190 | 1.486 |
| 11 | 3,161 | 0.952 | 1.178 | 1.462 |
| 12 | 2,681 | 0.931 | 1.150 | 1.509 |
| 13 | 1,762 | 0.858 | 1.122 | 1.491 |
| 14 | 3,612 | 0.927 | 1.187 | 1.429 |
| 15 | 6,523 | 0.848 | 1.080 | 1.337 |
| 16 | 2,703 | 0.961 | 1.179 | 1.521 |
| 17 | 913 | 0.933 | 1.105 | 1.380 |
| 18 | 968 | 0.939 | 1.131 | 1.348 |
| 19 | 2,816 | 0.811 | 1.154 | 1.442 |
| 20 | 2,474 | 0.907 | 1.121 | 1.457 |
| 21 | 2,679 | 0.905 | 1.128 | 1.408 |
| 22 | 890 | 0.913 | 1.131 | 1.365 |
| 23 | 1,036 | 0.750 | 1.147 | 1.710 |
| 24 | 1,793 | 0.936 | 1.136 | 1.459 |
| 25 | 3,756 | 0.905 | 1.170 | 1.563 |
| 26 | 1,528 | 0.889 | 1.134 | 1.452 |
| 27 | 1,143 | 0.924 | 1.117 | 1.395 |
| 28 | 2,016 | 0.986 | 1.178 | 1.427 |
| 29 | 611 | 0.943 | 1.084 | 1.282 |
| 30 | 4,862 | 0.881 | 1.091 | 1.407 |
| 31 | 1,122 | 0.925 | 1.087 | 1.258 |
| 32 | 1,776 | 1.021 | 1.194 | 1.454 |

Cuidados (D-013): censo de marzo 2020 vs LN de junio 2021; el censo incluye residentes de cualquier nacionalidad.

## 4. CONAPO por municipio INE

Cruce INEGI <-> INE por nombre normalizado dentro de la entidad (las dos listas del xlsx no están alineadas por fila). Métodos: {'exacto': 2442, 'difuso': 21, 'nombre_repetido_por_orden': 2}. Municipios INE del catálogo: 2,465.
- Municipios del catálogo INEGI sin contraparte INE: ['02006', '17036']; INE sin contraparte INEGI: [(4, 12)].
- **Cobertura CCPC 2024:** 2,465 de 2,477 municipios (99.52%); LN 99.79%.
- Con IIM (índice no nulo): 2,453 municipios, LN 99.71%. Con IM 2020: 2,465 municipios, LN 99.79%.
- Validación del cruce: razón población ECEG / POB_TOT CONAPO por municipio: n=2465, p1 0.808, p50 1.000, p99 1.265, min 0.163, max 3.029.
- Claves INE repetidas en el catálogo (se conserva la de razón de población más cercana a 1; descartadas): [[20, 208, '20209'], [20, 316, '20319']].
- Cruces no exactos:

| edo | mpio | cve_geo | metodo | razon_pob_eceg_conapo |
|---|---|---|---|---|
| 5 | 7 | 05007 | difuso | 1.0002 |
| 7 | 107 | 07071 | difuso | 1.0109 |
| 10 | 6 | 10006 | difuso | 0.9936 |
| 17 | 13 | 17013 | difuso | 0.9841 |
| 19 | 10 | 19010 | difuso | 0.8497 |
| 19 | 14 | 19014 | difuso | 1.0025 |
| 19 | 15 | 19015 | difuso | 1.0022 |
| 19 | 16 | 19016 | difuso | 1.0006 |
| 19 | 20 | 19020 | difuso | 1.0015 |
| 19 | 21 | 19021 | difuso | 1.0002 |
| 19 | 22 | 19022 | difuso | 0.9954 |
| 19 | 23 | 19023 | difuso | 0.9994 |
| 19 | 24 | 19024 | difuso | 0.9955 |
| 19 | 25 | 19025 | difuso | 0.8322 |
| 20 | 43 | 20043 | difuso | 1.0023 |
| 20 | 208 | 20208 | nombre_repetido_por_orden | 1.0255 |
| 20 | 316 | 20318 | nombre_repetido_por_orden | 0.9832 |
| 20 | 459 | 20459 | difuso | 0.9971 |
| 20 | 549 | 20549 | difuso | 1.0035 |
| 29 | 37 | 29037 | difuso | 1.0000 |
| 30 | 47 | 30045 | difuso | 1.0032 |
| 30 | 122 | 30121 | difuso | 1.0008 |
| 30 | 202 | 30202 | difuso | 1.0069 |

- Municipios CCPC 2024 sin cruce (por LN):

| edo | mpio | nom | ln |
|---|---|---|---|
| 2 | 6 | San Quintin | 87992.0000 |
| 25 | 20 | Juan José Ríos | 30496.0000 |
| 25 | 19 | Eldorado | 29770.0000 |
| 2 | 7 | San Felipe | 15169.0000 |
| 4 | 12 | Dzitbalché | 12180.0000 |
| 12 | 82 | Ñuu Savi | 7596.0000 |
| 12 | 83 | Las Vigas | 7166.0000 |
| 17 | 36 | Hueyapan | 5814.0000 |
| 12 | 84 | San Nicolás | 5088.0000 |
| 12 | 85 | Santa Cruz del Rincón | 4960.0000 |
| 20 | 317 | San Pedro Mixtepec | 713.0000 |
| 20 | 209 | San Juan Mixtepec | 508.0000 |

- Nulos en la salida: {'iim_dp2': 12}

## 5. Concurrencia

- Rejilla completa aelec x edo: 192 filas; con elección local concurrente 137. Gubernaturas por año: {2009: 6, 2012: 7, 2015: 9, 2018: 9, 2021: 15, 2024: 9}. `dip_local` NULL (no desglosado en 2018) en 30 filas.
- D-015: solo `gubernatura` se marca verificada (`gubernatura_verificada=TRUE`); `otras_banderas_verificadas=FALSE` en todas, con el texto original en `verificacion_texto`.

## 6. Nulos por variable (eceg_seccion2024)

Filas: 70,751.

| variable | nulos |
|---|---|
| tipo | 0 |
| pobtot_eceg | 2,775 |
| p_18ymas_eceg | 2,779 |
| graproes | 4 |
| prop_sin_escolaridad | 55 |
| prop_analfabeta | 55 |
| prop_posbasica | 55 |
| prop_hli | 55 |
| prop_afro | 55 |
| prop_internet | 58 |
| prop_celular | 58 |
| prop_nacida_otra_ent | 55 |
| prop_res_otra_ent_2015 | 55 |
| prop_discapacidad | 55 |
| prop_18a24 | 55 |
| prop_60ymas | 55 |
| seccion_madre | 67,976 |

## 7. Correlación de Spearman con la participación 2024 (SV/(SV+NV), SEXO<2)

**Solo descriptivo, unidad = sección (D-010).** `razon_ln_p18` es de 2021 (se cruza con participación 2024 solo para ver asociación); `iim_dp2` e `im_2020` son municipales y se repiten en todas las secciones del municipio (los n efectivos de municipio son mucho menores).

Secciones con participación 2024: 68,651.

| variable | rho_todas | n_todas | rho_directas | n_directas |
|---|---|---|---|---|
| pobtot_eceg | -0.0456 | 65944 | -0.0456 | 65944 |
| p_18ymas_eceg | -0.0020 | 65942 | -0.0020 | 65942 |
| graproes | 0.2872 | 68649 | 0.2981 | 65942 |
| prop_sin_escolaridad | -0.2116 | 68600 | -0.2231 | 65893 |
| prop_analfabeta | -0.1668 | 68600 | -0.1779 | 65893 |
| prop_posbasica | 0.3020 | 68600 | 0.3121 | 65893 |
| prop_hli | 0.0680 | 68600 | 0.0764 | 65893 |
| prop_afro | 0.0627 | 68600 | 0.0770 | 65893 |
| prop_internet | 0.1845 | 68597 | 0.1905 | 65890 |
| prop_celular | -0.0112 | 68597 | 0.0059 | 65890 |
| prop_nacida_otra_ent | 0.0121 | 68600 | 0.0238 | 65893 |
| prop_res_otra_ent_2015 | 0.0548 | 68600 | 0.0694 | 65893 |
| prop_discapacidad | 0.0292 | 68600 | 0.0167 | 65893 |
| prop_18a24 | -0.2966 | 68600 | -0.2920 | 65893 |
| prop_60ymas | 0.2681 | 68600 | 0.2545 | 65893 |
| iim_dp2 | 0.2933 | 68423 | 0.3019 | 65718 |
| im_2020 | 0.0393 | 68467 | 0.0479 | 65760 |
| razon_ln_p18 | -0.0568 | 65893 | -0.0568 | 65893 |

_Tiempo de ejecución: 25 s._