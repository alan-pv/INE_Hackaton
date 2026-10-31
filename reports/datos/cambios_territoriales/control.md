# Cambios territoriales en la movilidad (D-015)

Generado por `scripts/datos/cambios_territoriales.py`. La marca sale SOLO de la tabla de equivalencias (Magar, de terceros, no validada contra anexos del INE); ningún umbral de valores.

## Interpretación de la tabla (igual que `externos._tabla_equiv`)

- Hasta 3 eventos por fila: `action/orig.dest/when`, `action2/...`, `action3/...`.
- `split.from`: la sección es hija (alta); `orig.dest` = madres (`a|b`). `split.to`: la sección es madre; `orig.dest` = hijas (rango `a:b` o `a|b`). `merged.to`: la sección se da de baja y `orig.dest` es la receptora. `mun.chg` / `state.chg`: cambio de municipio / entidad (sin sección relacionada).
- Además de la fila propia se genera el evento en la contraparte (madre vigente de una división = `division_madre`; receptora de una fusión = `fusion_receptora`), que conserva su número: es el caso que la limpieza no detectaba por sí sola.
- Año del evento = `when` (primeros 4 dígitos). Respaldo si falta o no es numérico: `alta` para `split.from`, `baja` para el resto. Usos del respaldo: 1; eventos sin año (descartados): 8.
- Ventana 2009-2024. Un evento marca el par (e_prev, e] si e_prev < anio_evento <= e. Limitación: la tabla da año, no fecha; un evento del año de la elección (p. ej. 2021) puede ser posterior a la jornada.
- Los eventos de 2025 de la tabla son provisionales y quedan fuera de la ventana.

Filas de la tabla: 75,929. Eventos 2009-2024: 22,656 filas, 12,853 secciones.

## Eventos por tipo y año

| anio_evento | alta_por_division | baja_por_fusion | cambio_municipio | division_madre | fusion_receptora |
|---|---|---|---|---|---|
| 2009 | 505 | 172 | 4 | 505 | 172 |
| 2010 | 4 | 0 | 7 | 4 | 0 |
| 2011 | 866 | 8 | 36 | 866 | 8 |
| 2012 | 1039 | 6 | 6 | 1039 | 6 |
| 2013 | 1379 | 121 | 16 | 1379 | 121 |
| 2014 | 19 | 0 | 19 | 19 | 0 |
| 2015 | 500 | 50 | 19 | 500 | 50 |
| 2016 | 0 | 0 | 93 | 0 | 0 |
| 2017 | 78 | 0 | 0 | 78 | 0 |
| 2018 | 145 | 0 | 14 | 145 | 0 |
| 2019 | 0 | 0 | 9 | 0 | 0 |
| 2020 | 361 | 13 | 49 | 361 | 13 |
| 2021 | 959 | 574 | 7 | 959 | 574 |
| 2022 | 1305 | 0 | 110 | 1306 | 0 |
| 2023 | 2784 | 221 | 2 | 2785 | 221 |
| 2024 | 0 | 0 | 45 | 0 | 0 |

## Conciliación

- Filas `movilidad_seccion`: 344,910; `movilidad_seccion_marcada`: 344,910; OK.

## Marcas por par

| par | secciones | marcadas | pct_marcadas | marcadas_y_reseccionada | marcadas_conservan_numero |
|---|---|---|---|---|---|
| 2009→2012 | 66744 | 1944.0000 | 2.9100 | 1890.0000 | 54.0000 |
| 2012→2015 | 68583 | 2289.0000 | 3.3400 | 2084.0000 | 205.0000 |
| 2015→2018 | 68409 | 215.0000 | 0.3100 | 47.0000 | 168.0000 |
| 2018→2021 | 69587 | 2557.0000 | 3.6700 | 1948.0000 | 609.0000 |
| 2021→2024 | 71587 | 4200.0000 | 5.8700 | 3599.0000 | 601.0000 |

`reseccionada_en_par` es la bandera de la limpieza (presencia en el catálogo); `marcadas_conservan_numero` son las que esa bandera no veía.

## Combinaciones de tipo de evento entre marcadas

| par | tipo_evento | n |
|---|---|---|
| 2009→2012 | alta_por_division | 1793 |
| 2009→2012 | division_madre | 69 |
| 2009→2012 | cambio_municipio | 40 |
| 2009→2012 | baja_por_fusion | 13 |
| 2009→2012 | alta_por_division,fusion_receptora | 11 |
| 2009→2012 | alta_por_division,division_madre | 8 |
| 2009→2012 | alta_por_division,cambio_municipio | 6 |
| 2009→2012 | alta_por_division,cambio_municipio,division_madre | 3 |
| 2009→2012 | fusion_receptora | 1 |
| 2012→2015 | alta_por_division | 1840 |
| 2012→2015 | fusion_receptora | 154 |
| 2012→2015 | baja_por_fusion | 152 |
| 2012→2015 | division_madre | 67 |
| 2012→2015 | cambio_municipio | 35 |
| 2012→2015 | alta_por_division,division_madre | 19 |
| 2012→2015 | alta_por_division,cambio_municipio | 18 |
| 2012→2015 | alta_por_division,fusion_receptora | 2 |
| 2012→2015 | baja_por_fusion,cambio_municipio | 1 |
| 2012→2015 | baja_por_fusion,fusion_receptora | 1 |
| 2015→2018 | cambio_municipio | 95 |
| 2015→2018 | alta_por_division,division_madre | 68 |
| 2015→2018 | alta_por_division | 42 |
| 2015→2018 | alta_por_division,cambio_municipio | 5 |
| 2015→2018 | division_madre | 3 |
| 2015→2018 | alta_por_division,cambio_municipio,division_madre | 2 |
| 2018→2021 | alta_por_division | 1164 |
| 2018→2021 | baja_por_fusion | 533 |
| 2018→2021 | fusion_receptora | 524 |
| 2018→2021 | division_madre | 251 |
| 2018→2021 | cambio_municipio | 56 |
| 2018→2021 | alta_por_division,division_madre | 17 |
| 2018→2021 | alta_por_division,cambio_municipio | 7 |
| 2018→2021 | alta_por_division,fusion_receptora | 2 |
| 2018→2021 | baja_por_fusion,cambio_municipio | 1 |
| 2018→2021 | cambio_municipio,fusion_receptora | 1 |
| 2018→2021 | division_madre,fusion_receptora | 1 |
| 2021→2024 | alta_por_division | 2695 |
| 2021→2024 | division_madre | 863 |
| 2021→2024 | baja_por_fusion | 217 |
| 2021→2024 | fusion_receptora | 206 |
| 2021→2024 | alta_por_division,cambio_municipio | 80 |
| 2021→2024 | cambio_municipio | 76 |
| 2021→2024 | alta_por_division,division_madre | 61 |
| 2021→2024 | baja_por_fusion,fusion_receptora | 1 |
| 2021→2024 | alta_por_division,fusion_receptora | 1 |

## Validación: Hueyapan, Morelos (edo 17, secciones 700-702)

Filas de la tabla (campos relevantes):

| seccion | mun | alta | baja | action | when | OBSERVACIONES |
|---|---|---|---|---|---|---|
| 700 | HUEYAPAN | 1993 |  |  |  | hubo controversia scjn ratifico pero se incorporo tarde---inferi codigo ife y q seccion en hueyapan de la ausencia seccion en resultados ay 2021---seccion en barrio san andres |
| 701 | HUEYAPAN | 1993 |  |  |  | hubo controversia scjn ratifico pero se incorporo tarde---inferi codigo ife y q seccion en hueyapan de la ausencia seccion en resultados ay 2021---seccion en barrio san felipe |
| 702 | HUEYAPAN | 1993 |  |  |  | hubo controversia scjn ratifico pero se incorporo tarde---inferi codigo ife y q seccion en hueyapan de la ausencia seccion en resultados ay 2021---seccion en barrio san jacinto |

| par | seccion | observado | esperado | movilidad_rel | reseccionada_en_par | cambio_territorial_en_par | tipo_evento |
|---|---|---|---|---|---|---|---|
| 2018→2021 | 700 | 1370.0000 | 1358.7000 | 0.0080 | False | False | None |
| 2018→2021 | 701 | 10.0000 | 1193.7000 | -4.7820 | False | False | None |
| 2018→2021 | 702 | 62.0000 | 1311.2000 | -3.0520 | False | False | None |
| 2021→2024 | 700 | 1436.0000 | 1404.0000 | 0.0230 | False | False | None |
| 2021→2024 | 701 | 1281.0000 | 9.9000 | 4.8660 | False | False | None |
| 2021→2024 | 702 | 1454.0000 | 63.4000 | 3.1330 | False | False | None |

**Resultado:** 17-701 en el par 2021→2024 NO queda marcado; en 2018→2021 NO. 
Hallazgo: en la CCPC las tres secciones tienen LN ≈10 (701) y 62 (702) en 2021 y ≈1,300-1,450 en 2024. La anomalía de 2021→2024 es el reflejo de que la sección estaba casi vacía en 2021 (la tabla no registra evento: alta 1993, sin `action`). La columna OBSERVACIONES de la tabla dice que hubo controversia ante la SCJN y que el municipio se incorporó tarde (por eso la LN de 2021 es casi nula). La tabla NO lo codifica como evento, así que la marca por tabla no lo captura; es un caso de creación/incorporación tardía de municipio que requiere una regla complementaria (D-016).

## Colas de |movilidad_rel|: marcadas vs no marcadas

(`pct_abs_gt_0_5` es solo descriptiva de la cola; no se usa para marcar nada. Solo hay `movilidad_rel` en secciones presentes en ambas elecciones, por eso `n` de las marcadas coincide con `marcadas_conservan_numero`.)

| par | marcada | n | mediana | p90 | p99 | maximo | pct_abs_gt_0_5 |
|---|---|---|---|---|---|---|---|
| 2009→2012 | False | 63735 | 0.0496 | 0.1571 | 0.7506 | 2.9710 | 3.2900 |
| 2009→2012 | True | 54 | 0.1382 | 0.6524 | 1.1052 | 1.1100 | 14.8100 |
| 2012→2015 | False | 65173 | 0.0606 | 0.1459 | 0.6720 | 2.4310 | 3.2900 |
| 2012→2015 | True | 205 | 0.0719 | 0.4424 | 0.8721 | 1.7690 | 7.3200 |
| 2015→2018 | False | 68193 | 0.0326 | 0.0816 | 0.2657 | 2.9680 | 0.2900 |
| 2015→2018 | True | 168 | 0.1197 | 0.6676 | 2.8423 | 4.0350 | 13.1000 |
| 2018→2021 | False | 67024 | 0.0250 | 0.0644 | 0.1619 | 4.7820 | 0.0900 |
| 2018→2021 | True | 609 | 0.1822 | 0.4829 | 0.9233 | 3.9920 | 9.0300 |
| 2021→2024 | False | 67375 | 0.0294 | 0.0739 | 0.1963 | 6.1500 | 0.1200 |
| 2021→2024 | True | 601 | 0.1273 | 0.4821 | 0.6942 | 0.7280 | 8.3200 |

## Top-20 |movilidad_rel| 2021→2024 NO marcadas (posibles cambios no registrados en la tabla)

Sin filtro por umbral; se listan tal cual.

| edo | seccion | observado | esperado | movilidad_rel | reseccionada_en_par |
|---|---|---|---|---|---|
| 25 | 2189 | 1.0000 | 468.5000 | -6.1500 | False |
| 17 | 701 | 1281.0000 | 9.9000 | 4.8660 | False |
| 17 | 702 | 1454.0000 | 63.4000 | 3.1330 | False |
| 28 | 2039 | 2343.0000 | 282.5000 | 2.1150 | False |
| 23 | 975 | 1415.0000 | 282.0000 | 1.6130 | False |
| 19 | 2783 | 1901.0000 | 469.8000 | 1.3980 | False |
| 19 | 2649 | 3061.0000 | 766.8000 | 1.3840 | False |
| 19 | 2272 | 2033.0000 | 517.9000 | 1.3680 | False |
| 25 | 2187 | 79.0000 | 257.7000 | -1.1820 | False |
| 19 | 2823 | 3655.0000 | 1153.2000 | 1.1540 | False |
| 25 | 2188 | 875.0000 | 282.5000 | 1.1310 | False |
| 23 | 980 | 5935.0000 | 1972.8000 | 1.1010 | False |
| 2 | 2028 | 3477.0000 | 1165.4000 | 1.0930 | False |
| 23 | 1047 | 2401.0000 | 815.7000 | 1.0800 | False |
| 15 | 6517 | 974.0000 | 348.7000 | 1.0270 | False |
| 1 | 625 | 2903.0000 | 1044.7000 | 1.0220 | False |
| 8 | 3144 | 2457.0000 | 890.5000 | 1.0150 | False |
| 23 | 1022 | 2195.0000 | 824.3000 | 0.9790 | False |
| 23 | 999 | 2211.0000 | 835.2000 | 0.9730 | False |
| 19 | 2855 | 1196.0000 | 457.9000 | 0.9600 | False |
