# Batería común: datos y pertenencia como en pruebas_lecturas

## Cifras de control

- Celdas objetivo: 472,539 (control 472,539) OK. Celdas de brecha_celda: 983,708.
- Celdas sin n_2024: 25,610 (ln_2024 también falta en ellas: sin población en 2024): peso 0 en las medias de brecha (25,610 celdas con peso 0). Celdas con delta NaN: 0.
- Celdas por perfil (orden del documento) 80,573 / 170,916 / 109,591 / 56,264 / 55,195 OK.
- Secciones con celdas: 70,681; con LN 2024 total > 0: 68,651 (2030 sin LN, excluidas).
- Municipios (edo, mpio) con secciones: 2,465; estados: 32.
- Σ LN_perfil (celdas objetivo, resp x LN 2024) = 50,669,281; Σ ln_2024 de celdas objetivo = 50,669,281 (deben coincidir; dif = 7.451e-09).
- Secciones sin perfil mayoritario: 40,847.

### Secciones donde el perfil es mayoritario

| perfil | secciones_mayoritarias | ln_seccion_mayoritaria | ln_del_perfil_en_ellas | ln_del_perfil_total | pct_ln_perfil_captada | secciones_rurales | secciones_urbanas |
|---|---|---|---|---|---|---|---|
| 1 | 5109 | 1.052e+07 | 8.541e+06 | 1.162e+07 | 73.54 | 110 | 4521 |
| 2 | 10896 | 1.784e+07 | 1.324e+07 | 1.966e+07 | 67.35 | 7 | 10636 |
| 3 | 6177 | 6.901e+06 | 5.431e+06 | 8.169e+06 | 66.49 | 4024 | 1137 |
| 4 | 3326 | 5.459e+06 | 4.286e+06 | 7.105e+06 | 60.32 | 41 | 3077 |
| 5 | 2296 | 2.689e+06 | 2.139e+06 | 4.118e+06 | 51.94 | 1390 | 538 |

- Medida log(sv_2024/E_2024): celdas excluidas por sv_2024 = 0, E_2024 = 0 o NaN: 32,391 de 983,708 (6,781 de ellas con peso n_2024 > 0).
- Tiempo hasta estadísticos de sección: 2 s.
- Bootstrap: B = 1999, nivel 0.95, semilla [0, 9]; suma de multiplicidades por estado conservada: True.
# Batería común de pruebas T01–T13 (D-036)

## Cifras de control

- Celdas objetivo: 472,539 (control 472,539) OK. Participación nacional 2024 (panel, de la caché de pruebas_lecturas) = 59.67% (control 59.67%) OK.
- Bootstrap: B = 1999, semilla [0, 9], mismas multiplicidades que pruebas_lecturas. Tendencia (T01, T02) leída de su caché.
- Conciliación con pruebas_lecturas/predicciones.csv: 24 celdas comparadas, dif. máxima = 0.00e+00 (tolerancia 1e-9): OK.
- T11: Spearman(brecha, iim_dp2) multiplicado por -1 (IC = (-sup, -inf)). Razón: `iim_dp2` crece cuando BAJA la intensidad migratoria (D-026; Spearman municipal -0.96 con remesas); pruebas_lecturas predecía signo + (P3.ii); aquí negativo = consistente.
- T03 con log(O/E) 2024 (`_L`) no existía en pruebas_lecturas (solo contrastes de edad); se calculó aquí con la misma función y la misma pertenencia.
- T02: media de la diferencia observada-esperada (pp) en intermedias (2009, 2015, 2021) menos presidenciales (2012, 2018, 2024), réplica a réplica, de `tend_dif` de pruebas_lecturas.
- `*` = la prueba corresponde a la lectura del perfil. P2 solo tiene T02 como prueba de su lectura.

## Secciones mayoritarias por perfil

| perfil | secciones_mayoritarias | ln_seccion_mayoritaria | ln_del_perfil_en_ellas | ln_del_perfil_total | pct_ln_perfil_captada | secciones_rurales | secciones_urbanas |
|---|---|---|---|---|---|---|---|
| 1 | 5109 | 1.052e+07 | 8.541e+06 | 1.162e+07 | 73.54 | 110 | 4521 |
| 2 | 10896 | 1.784e+07 | 1.324e+07 | 1.966e+07 | 67.35 | 7 | 10636 |
| 3 | 6177 | 6.901e+06 | 5.431e+06 | 8.169e+06 | 66.49 | 4024 | 1137 |
| 4 | 3326 | 5.459e+06 | 4.286e+06 | 7.105e+06 | 60.32 | 41 | 3077 |
| 5 | 2296 | 2.689e+06 | 2.139e+06 | 4.118e+06 | 51.94 | 1390 | 538 |

## Valor y veredicto (medida δ̃; * = de su lectura)

| id | prueba | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|
| T01 | La brecha se agrava con el tiempo | -1.199 se cumple * | +0.330 contraria | -0.602 se cumple | +0.058 no se cumple | +0.371 contraria |
| T02 | Más profunda en intermedias que en presidenciales | +1.172 contraria | -3.418 se cumple * | +2.777 contraria | -2.666 se cumple | -0.057 no se cumple |
| T03 | Hombres 25–46 más abajo que mujeres 25–46 (misma sección) | +0.052 contraria | +0.038 contraria | -0.185 se cumple * | +0.133 contraria | -0.041 no se cumple |
| T04 | Jóvenes 18–24 más abajo que adultos 32–69 | -0.062 se cumple | +0.106 contraria | -0.016 no se cumple | +0.073 no se cumple | -0.184 se cumple * |
| T05 | Personas de 80+ más abajo que adultos 32–69 | +0.137 contraria | +0.097 contraria | +0.036 contraria | +0.147 contraria | -0.018 no se cumple * |
| T06 | Adultos 25–46 más abajo que 47–69 (los que más se mudan) | -0.040 se cumple | -0.008 no se cumple | +0.020 contraria | +0.067 contraria * | -0.073 se cumple |
| T07 | Más profunda donde hay más nacidos en otra entidad | -0.288 se cumple * | +0.097 no se cumple | +0.072 contraria | -0.212 se cumple * | +0.117 contraria |
| T08 | Más profunda donde llegan más electores | -0.160 se cumple * | -0.054 no se cumple | -0.059 no se cumple | -0.066 no se cumple * | -0.049 no se cumple |
| T09 | Más profunda donde más se habla lengua indígena | -0.287 se cumple | -0.106 se cumple | -0.008 no se cumple | -0.223 se cumple | -0.145 se cumple * |
| T10 | Más profunda donde hay menos internet | -0.193 se cumple | -0.344 se cumple | +0.027 no se cumple | -0.432 se cumple | -0.137 se cumple * |
| T11 | Más profunda donde hay más intensidad migratoria a EE. UU. | -0.000 no se cumple | -0.154 se cumple | +0.059 no se cumple * | -0.199 se cumple | -0.159 se cumple |
| T12 | Más electores registrados que adultos residentes | -0.041 contraria | +0.021 se cumple | +0.053 se cumple * | -0.104 contraria | +0.006 no se cumple |
| T13 | Más profunda en secciones rurales que urbanas | -0.000 no se cumple | -0.003 no se cumple | +0.045 contraria | -0.054 no se cumple | -0.030 no se cumple * |

## Veredicto combinado (δ̃ y log(O/E) 2024; T03–T06, versión base)

| id | prueba | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|
| T01 | La brecha se agrava con el tiempo | -1.199 se cumple * | +0.330 contraria | -0.602 se cumple | +0.058 no se cumple | +0.371 contraria |
| T02 | Más profunda en intermedias que en presidenciales | +1.172 contraria | -3.418 se cumple * | +2.777 contraria | -2.666 se cumple | -0.057 no se cumple |
| T03 | Hombres 25–46 más abajo que mujeres 25–46 (misma sección) | +0.052 no concluyente | +0.038 no concluyente | -0.185 se cumple * | +0.133 contraria | -0.041 no concluyente |
| T04 | Jóvenes 18–24 más abajo que adultos 32–69 | -0.062 se cumple | +0.106 no concluyente | -0.016 no concluyente | +0.073 no concluyente | -0.184 se cumple * |
| T05 | Personas de 80+ más abajo que adultos 32–69 | +0.137 no concluyente | +0.097 no concluyente | +0.036 no concluyente | +0.147 no concluyente | -0.018 no concluyente * |
| T06 | Adultos 25–46 más abajo que 47–69 (los que más se mudan) | -0.040 se cumple | -0.008 no concluyente | +0.020 no concluyente | +0.067 no concluyente * | -0.073 se cumple |
| T07 | Más profunda donde hay más nacidos en otra entidad | -0.288 se cumple * | +0.097 no se cumple | +0.072 contraria | -0.212 se cumple * | +0.117 contraria |
| T08 | Más profunda donde llegan más electores | -0.160 se cumple * | -0.054 no se cumple | -0.059 no se cumple | -0.066 no se cumple * | -0.049 no se cumple |
| T09 | Más profunda donde más se habla lengua indígena | -0.287 se cumple | -0.106 se cumple | -0.008 no se cumple | -0.223 se cumple | -0.145 se cumple * |
| T10 | Más profunda donde hay menos internet | -0.193 se cumple | -0.344 se cumple | +0.027 no se cumple | -0.432 se cumple | -0.137 se cumple * |
| T11 | Más profunda donde hay más intensidad migratoria a EE. UU. | -0.000 no se cumple | -0.154 se cumple | +0.059 no se cumple * | -0.199 se cumple | -0.159 se cumple |
| T12 | Más electores registrados que adultos residentes | -0.041 contraria | +0.021 se cumple | +0.053 se cumple * | -0.104 contraria | +0.006 no se cumple |
| T13 | Más profunda en secciones rurales que urbanas | -0.000 no se cumple | -0.003 no se cumple | +0.045 contraria | -0.054 no se cumple | -0.030 no se cumple * |

## Pruebas T03–T06, versión «más que en los otros perfiles»

| id | perfil | valor_vs_otros | ic_vs_otros_inf | ic_vs_otros_sup | veredicto_vs_otros | veredicto_combinado_vs_otros |
|---|---|---|---|---|---|---|
| T03 | 1 | 0.051 | 0.0295 | 0.0723 | contraria | contraria |
| T03 | 2 | 0.0425 | 0.013 | 0.075 | contraria | contraria |
| T03 | 3 | -0.2352 | -0.2592 | -0.2112 | se cumple | se cumple |
| T03 | 4 | 0.1379 | 0.1121 | 0.1583 | contraria | contraria |
| T03 | 5 | -0.0579 | -0.1056 | -0.014 | se cumple | se cumple |
| T04 | 1 | -0.1136 | -0.1464 | -0.0798 | se cumple | se cumple |
| T04 | 2 | 0.1399 | 0.1051 | 0.1776 | contraria | contraria |
| T04 | 3 | -0.0475 | -0.0811 | -0.0102 | se cumple | se cumple |
| T04 | 4 | 0.0567 | -0.025 | 0.1158 | no se cumple | no se cumple |
| T04 | 5 | -0.2217 | -0.2966 | -0.1517 | se cumple | se cumple |
| T05 | 1 | 0.0542 | 0.0265 | 0.0803 | contraria | no concluyente |
| T05 | 2 | 0.0013 | -0.0299 | 0.0307 | no se cumple | no concluyente |
| T05 | 3 | -0.0717 | -0.0939 | -0.0474 | se cumple | se cumple |
| T05 | 4 | 0.0583 | 0.0136 | 0.0959 | contraria | no concluyente |
| T05 | 5 | -0.121 | -0.1826 | -0.0608 | se cumple | se cumple |
| T06 | 1 | -0.0453 | -0.0608 | -0.0288 | se cumple | se cumple |
| T06 | 2 | -0.0038 | -0.0225 | 0.0164 | no se cumple | no concluyente |
| T06 | 3 | 0.0311 | 0.0101 | 0.0524 | contraria | no concluyente |
| T06 | 4 | 0.0837 | 0.0507 | 0.1092 | contraria | contraria |
| T06 | 5 | -0.0707 | -0.1031 | -0.0401 | se cumple | se cumple |

## Tabla larga completa

| id | prueba | perfil | valor | ic_inf | ic_sup | unidad | signo_consistente | veredicto | valor_vs_otros | ic_vs_otros_inf | ic_vs_otros_sup | veredicto_vs_otros | valor_L | ic_L_inf | ic_L_sup | veredicto_L | valor_vs_otros_L | ic_vs_otros_L_inf | ic_vs_otros_L_sup | veredicto_vs_otros_L | veredicto_combinado | veredicto_combinado_vs_otros | de_su_lectura |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T01 | La brecha se agrava con el tiempo | 1 | -1.199 | -1.63 | -0.7505 | pp/elección | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T01 | La brecha se agrava con el tiempo | 2 | 0.3297 | 0.1393 | 0.515 | pp/elección | negativa | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T01 | La brecha se agrava con el tiempo | 3 | -0.602 | -0.7762 | -0.4314 | pp/elección | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T01 | La brecha se agrava con el tiempo | 4 | 0.0577 | -0.348 | 0.3611 | pp/elección | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T01 | La brecha se agrava con el tiempo | 5 | 0.3713 | 0.1712 | 0.5681 | pp/elección | negativa | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T02 | Más profunda en intermedias que en presidenciales | 1 | 1.172 | 0.171 | 2.263 | pp | negativa | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T02 | Más profunda en intermedias que en presidenciales | 2 | -3.418 | -4.375 | -2.399 | pp | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T02 | Más profunda en intermedias que en presidenciales | 3 | 2.777 | 2.393 | 3.193 | pp | negativa | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T02 | Más profunda en intermedias que en presidenciales | 4 | -2.666 | -3.474 | -1.46 | pp | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T02 | Más profunda en intermedias que en presidenciales | 5 | -0.0566 | -0.8627 | 0.8166 | pp | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T03 | Hombres 25–46 más abajo que mujeres 25–46 (misma sección) | 1 | 0.0515 | 0.0318 | 0.0732 | diferencia de brecha logit | negativa | contraria | 0.051 | 0.0295 | 0.0723 | contraria | -0.02 | -0.0315 | -0.0078 | se cumple | 0.0206 | 0.0077 | 0.0339 | contraria | no concluyente | contraria | False |
| T03 | Hombres 25–46 más abajo que mujeres 25–46 (misma sección) | 2 | 0.0379 | 0.021 | 0.0568 | diferencia de brecha logit | negativa | contraria | 0.0425 | 0.013 | 0.075 | contraria | 0.0032 | -0.0054 | 0.0123 | no se cumple | 0.0657 | 0.0474 | 0.0859 | contraria | no concluyente | contraria | False |
| T03 | Hombres 25–46 más abajo que mujeres 25–46 (misma sección) | 3 | -0.185 | -0.2055 | -0.1647 | diferencia de brecha logit | negativa | se cumple | -0.2352 | -0.2592 | -0.2112 | se cumple | -0.1878 | -0.2036 | -0.1716 | se cumple | -0.181 | -0.1974 | -0.1644 | se cumple | se cumple | se cumple | True |
| T03 | Hombres 25–46 más abajo que mujeres 25–46 (misma sección) | 4 | 0.1334 | 0.1053 | 0.1561 | diferencia de brecha logit | negativa | contraria | 0.1379 | 0.1121 | 0.1583 | contraria | 0.0341 | 0.0211 | 0.0471 | contraria | 0.0796 | 0.0664 | 0.0918 | contraria | contraria | contraria | False |
| T03 | Hombres 25–46 más abajo que mujeres 25–46 (misma sección) | 5 | -0.0414 | -0.0864 | 0.0009 | diferencia de brecha logit | negativa | no se cumple | -0.0579 | -0.1056 | -0.014 | se cumple | -0.1039 | -0.1414 | -0.0699 | se cumple | -0.0729 | -0.1098 | -0.0381 | se cumple | no concluyente | se cumple | False |
| T04 | Jóvenes 18–24 más abajo que adultos 32–69 | 1 | -0.0622 | -0.0972 | -0.0265 | diferencia de brecha logit | negativa | se cumple | -0.1136 | -0.1464 | -0.0798 | se cumple | -0.0932 | -0.1071 | -0.0784 | se cumple | -0.0465 | -0.0631 | -0.0278 | se cumple | se cumple | se cumple | False |
| T04 | Jóvenes 18–24 más abajo que adultos 32–69 | 2 | 0.1062 | 0.0865 | 0.1265 | diferencia de brecha logit | negativa | contraria | 0.1399 | 0.1051 | 0.1776 | contraria | 0.0041 | -0.0092 | 0.0164 | no se cumple | 0.1055 | 0.0863 | 0.1241 | contraria | no concluyente | contraria | False |
| T04 | Jóvenes 18–24 más abajo que adultos 32–69 | 3 | -0.0161 | -0.0424 | 0.011 | diferencia de brecha logit | negativa | no se cumple | -0.0475 | -0.0811 | -0.0102 | se cumple | -0.0866 | -0.1019 | -0.0709 | se cumple | -0.034 | -0.0526 | -0.0133 | se cumple | no concluyente | se cumple | False |
| T04 | Jóvenes 18–24 más abajo que adultos 32–69 | 4 | 0.0734 | -0.0074 | 0.1315 | diferencia de brecha logit | negativa | no se cumple | 0.0567 | -0.025 | 0.1158 | no se cumple | -0.0415 | -0.0801 | -0.0125 | se cumple | 0.0188 | -0.022 | 0.0492 | no se cumple | no concluyente | no se cumple | False |
| T04 | Jóvenes 18–24 más abajo que adultos 32–69 | 5 | -0.1841 | -0.2561 | -0.1151 | diferencia de brecha logit | negativa | se cumple | -0.2217 | -0.2966 | -0.1517 | se cumple | -0.2927 | -0.3492 | -0.2396 | se cumple | -0.2501 | -0.3069 | -0.1974 | se cumple | se cumple | se cumple | True |
| T05 | Personas de 80+ más abajo que adultos 32–69 | 1 | 0.1371 | 0.1131 | 0.1577 | diferencia de brecha logit | negativa | contraria | 0.0542 | 0.0265 | 0.0803 | contraria | -0.052 | -0.0735 | -0.0323 | se cumple | -0.0184 | -0.0432 | 0.0059 | no se cumple | no concluyente | no concluyente | False |
| T05 | Personas de 80+ más abajo que adultos 32–69 | 2 | 0.0968 | 0.0704 | 0.1197 | diferencia de brecha logit | negativa | contraria | 0.0013 | -0.0299 | 0.0307 | no se cumple | 0.0059 | -0.0169 | 0.0264 | no se cumple | 0.0752 | 0.0499 | 0.0993 | contraria | no concluyente | no concluyente | False |
| T05 | Personas de 80+ más abajo que adultos 32–69 | 3 | 0.0358 | 0.0168 | 0.0559 | diferencia de brecha logit | negativa | contraria | -0.0717 | -0.0939 | -0.0474 | se cumple | -0.1097 | -0.1243 | -0.095 | se cumple | -0.0855 | -0.1036 | -0.0658 | se cumple | no concluyente | se cumple | False |
| T05 | Personas de 80+ más abajo que adultos 32–69 | 4 | 0.1471 | 0.1048 | 0.1798 | diferencia de brecha logit | negativa | contraria | 0.0583 | 0.0136 | 0.0959 | contraria | -0.0392 | -0.0737 | -0.0108 | se cumple | -0.0013 | -0.0365 | 0.0281 | no se cumple | no concluyente | no concluyente | False |
| T05 | Personas de 80+ más abajo que adultos 32–69 | 5 | -0.0175 | -0.0784 | 0.0428 | diferencia de brecha logit | negativa | no se cumple | -0.121 | -0.1826 | -0.0608 | se cumple | -0.0902 | -0.1426 | -0.0408 | se cumple | -0.0556 | -0.1079 | -0.0051 | se cumple | no concluyente | se cumple | True |
| T06 | Adultos 25–46 más abajo que 47–69 (los que más se mudan) | 1 | -0.0405 | -0.0595 | -0.0216 | diferencia de brecha logit | negativa | se cumple | -0.0453 | -0.0608 | -0.0288 | se cumple | -0.0753 | -0.0872 | -0.0617 | se cumple | -0.0353 | -0.0474 | -0.0217 | se cumple | se cumple | se cumple | False |
| T06 | Adultos 25–46 más abajo que 47–69 (los que más se mudan) | 2 | -0.0084 | -0.0181 | 0.0025 | diferencia de brecha logit | negativa | no se cumple | -0.0038 | -0.0225 | 0.0164 | no se cumple | -0.0347 | -0.0423 | -0.0257 | se cumple | 0.0236 | 0.0138 | 0.0338 | contraria | no concluyente | no concluyente | False |
| T06 | Adultos 25–46 más abajo que 47–69 (los que más se mudan) | 3 | 0.02 | 0.0016 | 0.0389 | diferencia de brecha logit | negativa | contraria | 0.0311 | 0.0101 | 0.0524 | contraria | -0.0414 | -0.0528 | -0.0294 | se cumple | 0.0085 | -0.0041 | 0.0211 | no se cumple | no concluyente | no concluyente | False |
| T06 | Adultos 25–46 más abajo que 47–69 (los que más se mudan) | 4 | 0.067 | 0.0328 | 0.0947 | diferencia de brecha logit | negativa | contraria | 0.0837 | 0.0507 | 0.1092 | contraria | -0.015 | -0.0242 | -0.0041 | se cumple | 0.0384 | 0.0275 | 0.0503 | contraria | no concluyente | contraria | True |
| T06 | Adultos 25–46 más abajo que 47–69 (los que más se mudan) | 5 | -0.0725 | -0.1015 | -0.045 | diferencia de brecha logit | negativa | se cumple | -0.0707 | -0.1031 | -0.0401 | se cumple | -0.1224 | -0.1488 | -0.1 | se cumple | -0.0787 | -0.1062 | -0.0561 | se cumple | se cumple | se cumple | False |
| T07 | Más profunda donde hay más nacidos en otra entidad | 1 | -0.288 | -0.4387 | -0.1138 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T07 | Más profunda donde hay más nacidos en otra entidad | 2 | 0.0974 | -0.0208 | 0.204 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T07 | Más profunda donde hay más nacidos en otra entidad | 3 | 0.0715 | 0.0087 | 0.1333 | correlación de Spearman | negativa | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T07 | Más profunda donde hay más nacidos en otra entidad | 4 | -0.2115 | -0.3216 | -0.0848 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T07 | Más profunda donde hay más nacidos en otra entidad | 5 | 0.1169 | 0.029 | 0.2238 | correlación de Spearman | negativa | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T08 | Más profunda donde llegan más electores | 1 | -0.1598 | -0.2878 | -0.0458 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T08 | Más profunda donde llegan más electores | 2 | -0.0538 | -0.1375 | 0.0324 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T08 | Más profunda donde llegan más electores | 3 | -0.0586 | -0.1255 | 0.007 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T08 | Más profunda donde llegan más electores | 4 | -0.0663 | -0.2155 | 0.0549 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | True |
| T08 | Más profunda donde llegan más electores | 5 | -0.0486 | -0.1219 | 0.0329 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T09 | Más profunda donde más se habla lengua indígena | 1 | -0.2874 | -0.3858 | -0.1994 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T09 | Más profunda donde más se habla lengua indígena | 2 | -0.1063 | -0.1773 | -0.0332 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T09 | Más profunda donde más se habla lengua indígena | 3 | -0.0075 | -0.0732 | 0.0576 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T09 | Más profunda donde más se habla lengua indígena | 4 | -0.2226 | -0.3353 | -0.1393 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T09 | Más profunda donde más se habla lengua indígena | 5 | -0.1453 | -0.2317 | -0.0537 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T10 | Más profunda donde hay menos internet | 1 | -0.1929 | -0.2936 | -0.0855 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T10 | Más profunda donde hay menos internet | 2 | -0.3436 | -0.3969 | -0.2841 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T10 | Más profunda donde hay menos internet | 3 | 0.0269 | -0.028 | 0.0845 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T10 | Más profunda donde hay menos internet | 4 | -0.432 | -0.5172 | -0.3636 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T10 | Más profunda donde hay menos internet | 5 | -0.1374 | -0.2142 | -0.0589 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T11 | Más profunda donde hay más intensidad migratoria a EE. UU. | 1 | -0.0004 | -0.127 | 0.13 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T11 | Más profunda donde hay más intensidad migratoria a EE. UU. | 2 | -0.1535 | -0.2577 | -0.0384 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T11 | Más profunda donde hay más intensidad migratoria a EE. UU. | 3 | 0.0589 | -0.0167 | 0.1378 | correlación de Spearman | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | True |
| T11 | Más profunda donde hay más intensidad migratoria a EE. UU. | 4 | -0.1989 | -0.3281 | -0.001 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T11 | Más profunda donde hay más intensidad migratoria a EE. UU. | 5 | -0.1595 | -0.2494 | -0.0756 | correlación de Spearman | negativa | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T12 | Más electores registrados que adultos residentes | 1 | -0.0412 | -0.0558 | -0.024 | diferencia de medianas | positiva | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T12 | Más electores registrados que adultos residentes | 2 | 0.0213 | 0.01 | 0.033 | diferencia de medianas | positiva | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | False |
| T12 | Más electores registrados que adultos residentes | 3 | 0.0526 | 0.0396 | 0.0657 | diferencia de medianas | positiva | se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | se cumple | nan | True |
| T12 | Más electores registrados que adultos residentes | 4 | -0.1043 | -0.1718 | -0.0614 | diferencia de medianas | positiva | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T12 | Más electores registrados que adultos residentes | 5 | 0.0063 | -0.0107 | 0.03 | diferencia de medianas | positiva | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T13 | Más profunda en secciones rurales que urbanas | 1 | -0.0003 | -0.0703 | 0.0665 | diferencia de brecha logit | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T13 | Más profunda en secciones rurales que urbanas | 2 | -0.0029 | -0.0514 | 0.0404 | diferencia de brecha logit | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T13 | Más profunda en secciones rurales que urbanas | 3 | 0.0452 | 0.0042 | 0.0864 | diferencia de brecha logit | negativa | contraria | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | contraria | nan | False |
| T13 | Más profunda en secciones rurales que urbanas | 4 | -0.0544 | -0.2109 | 0.0963 | diferencia de brecha logit | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | False |
| T13 | Más profunda en secciones rurales que urbanas | 5 | -0.0305 | -0.0785 | 0.0177 | diferencia de brecha logit | negativa | no se cumple | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | no se cumple | nan | True |

Tiempo total: 60 s.
