# Pruebas de las lecturas de cada perfil (D-034)

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
- Resultados leídos de caché resultados.pkl (borrarlo para rehacer).
- Panel: control 2024 SV/(SV+NV) = 59.67% (control 59.67%); n = sv + nv en todas las filas: True. Celdas objetivo presentes en el panel: 460,206.

## Predicciones (IC95% bootstrap de municipios)

| perfil | lectura | id | prediccion | estadistico | valor | ic_inf | ic_sup | signo_predicho | veredicto | medida | veredicto_combinado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Emigración a EE. UU. | P3.i-a | Brecha de hombres 25–46 más profunda que la de mujeres 25–46 (en sus secciones) | diferencia de brecha (δ̃) | -0.185 | -0.2055 | -0.1647 | -1 | se cumple | δ̃ todo el periodo | se cumple |
| 3 | Emigración a EE. UU. | P3.i-b | Esa diferencia H−M 25–46 es mayor que en las secciones de los demás perfiles | diferencia de brecha (δ̃) | -0.2352 | -0.2592 | -0.2112 | -1 | se cumple | δ̃ todo el periodo | se cumple |
| 3 | Emigración a EE. UU. | P3.ii | Spearman(brecha, iim_dp2) > 0 (más intensidad migratoria = brecha más profunda) | Spearman ponderada | -0.0589 | -0.1378 | 0.0167 | 1 | no se cumple | Spearman sobre δ̃ | no se cumple |
| 3 | Emigración a EE. UU. | P3.iii | Mediana de razon_ln_p18 de sus secciones mayor que la de la población objetivo | diferencia de medianas | 0.0526 | 0.0396 | 0.0657 | 1 | se cumple | δ̃ todo el periodo | se cumple |
| 4 | Domicilio desactualizado / recién llegados | P4.i-a | Brecha de 25–46 más profunda que la de 47–69 (en sus secciones) | diferencia de brecha (δ̃) | 0.067 | 0.0328 | 0.0947 | -1 | contraria | δ̃ todo el periodo | no concluyente |
| 4 | Domicilio desactualizado / recién llegados | P4.i-b | Esa diferencia 25–46 vs 47–69 es mayor que en los demás perfiles | diferencia de brecha (δ̃) | 0.0837 | 0.0507 | 0.1092 | -1 | contraria | δ̃ todo el periodo | contraria |
| 4 | Domicilio desactualizado / recién llegados | P4.ii-a | Spearman(brecha, prop_nacida_otra_ent) < 0 | Spearman ponderada | -0.2115 | -0.3216 | -0.0848 | -1 | se cumple | Spearman sobre δ̃ | se cumple |
| 4 | Domicilio desactualizado / recién llegados | P4.ii-b | Spearman(brecha, pctl_mov_estado) < 0 | Spearman ponderada | -0.0663 | -0.2155 | 0.0549 | -1 | no se cumple | Spearman sobre δ̃ | no se cumple |
| 5 | Barreras de acceso | P5.i-a | Brecha de 80+ más profunda que la de 32–69 (en sus secciones) | diferencia de brecha (δ̃) | -0.0175 | -0.0784 | 0.0428 | -1 | no se cumple | δ̃ todo el periodo | no concluyente |
| 5 | Barreras de acceso | P5.i-b | Esa diferencia 80+ vs 32–69 es mayor que en los demás perfiles | diferencia de brecha (δ̃) | -0.121 | -0.1826 | -0.0608 | -1 | se cumple | δ̃ todo el periodo | se cumple |
| 5 | Barreras de acceso | P5.i-c | Brecha de 18–24 más profunda que la de 32–69 (en sus secciones) | diferencia de brecha (δ̃) | -0.1841 | -0.2561 | -0.1151 | -1 | se cumple | δ̃ todo el periodo | se cumple |
| 5 | Barreras de acceso | P5.i-d | Esa diferencia 18–24 vs 32–69 es mayor que en los demás perfiles | diferencia de brecha (δ̃) | -0.2217 | -0.2966 | -0.1517 | -1 | se cumple | δ̃ todo el periodo | se cumple |
| 5 | Barreras de acceso | P5.ii-a | Spearman(brecha, prop_hli) < 0 | Spearman ponderada | -0.1453 | -0.2317 | -0.0537 | -1 | se cumple | Spearman sobre δ̃ | se cumple |
| 5 | Barreras de acceso | P5.ii-b | Spearman(brecha, 1 − prop_internet) < 0 | Spearman ponderada | -0.1374 | -0.2142 | -0.0589 | -1 | se cumple | Spearman sobre δ̃ | se cumple |
| 5 | Barreras de acceso | P5.iii | Brecha de sus secciones rurales más profunda que la de las urbanas (tiposec R vs U) | diferencia de brecha (δ̃) | -0.0305 | -0.0785 | 0.0177 | -1 | no se cumple | δ̃ todo el periodo | no se cumple |
| 1 | Baja vinculación local, población joven en llegada | P1.i-a | Spearman(brecha, pctl_mov_estado) < 0 | Spearman ponderada | -0.1598 | -0.2878 | -0.0458 | -1 | se cumple | Spearman sobre δ̃ | se cumple |
| 1 | Baja vinculación local, población joven en llegada | P1.i-b | Spearman(brecha, prop_nacida_otra_ent) < 0 | Spearman ponderada | -0.288 | -0.4387 | -0.1138 | -1 | se cumple | Spearman sobre δ̃ | se cumple |
| 4 | Domicilio desactualizado / recién llegados | P4.i-a-L | Brecha de 25–46 más profunda que la de 47–69 (en sus secciones) [log(O/E) 2024] | diferencia de brecha (δ̃) | -0.015 | -0.0242 | -0.0041 | -1 | se cumple | log(O/E) 2024 | no concluyente |
| 4 | Domicilio desactualizado / recién llegados | P4.i-b-L | Esa diferencia 25–46 vs 47–69 es mayor que en los demás perfiles [log(O/E) 2024] | diferencia de brecha (δ̃) | 0.0384 | 0.0275 | 0.0503 | -1 | contraria | log(O/E) 2024 | contraria |
| 5 | Barreras de acceso | P5.i-a-L | Brecha de 80+ más profunda que la de 32–69 (en sus secciones) [log(O/E) 2024] | diferencia de brecha (δ̃) | -0.0902 | -0.1426 | -0.0408 | -1 | se cumple | log(O/E) 2024 | no concluyente |
| 5 | Barreras de acceso | P5.i-b-L | Esa diferencia 80+ vs 32–69 es mayor que en los demás perfiles [log(O/E) 2024] | diferencia de brecha (δ̃) | -0.0556 | -0.1079 | -0.0051 | -1 | se cumple | log(O/E) 2024 | se cumple |
| 5 | Barreras de acceso | P5.i-c-L | Brecha de 18–24 más profunda que la de 32–69 (en sus secciones) [log(O/E) 2024] | diferencia de brecha (δ̃) | -0.2927 | -0.3492 | -0.2396 | -1 | se cumple | log(O/E) 2024 | se cumple |
| 5 | Barreras de acceso | P5.i-d-L | Esa diferencia 18–24 vs 32–69 es mayor que en los demás perfiles [log(O/E) 2024] | diferencia de brecha (δ̃) | -0.2501 | -0.3069 | -0.1974 | -1 | se cumple | log(O/E) 2024 | se cumple |
| 1 | Baja vinculación local, población joven en llegada | P1.ii-a | Pendiente de la diferencia observada−esperada 2009→2024 negativa (pp por elección) | pendiente (pp/elección) | -1.199 | -1.63 | -0.7505 | -1 | se cumple | sin medida δ̃ (tendencia) | se cumple |
| 1 | Baja vinculación local, población joven en llegada | P1.ii-b | Esa pendiente es más negativa que la media de los demás perfiles | pendiente (pp/elección) | -1.238 | -1.601 | -0.8474 | -1 | se cumple | sin medida δ̃ (tendencia) | se cumple |
| 1 | Baja vinculación local, población joven en llegada | P1.desc | Descriptor (sin predicción): Spearman(brecha, log tasa de homicidio municipal 2023) | Spearman ponderada | -0.2116 | -0.3972 | -0.0021 | 0 | descriptor (D-027) | Spearman sobre δ̃ | descriptor (D-027) |

## Veredictos por lectura (D-034)

| perfil | lectura | incisos | se_cumplen | contrarias | no_concluyentes | no_se_cumplen | veredicto |
|---|---|---|---|---|---|---|---|
| 1 | Baja vinculación local, población joven en llegada | 4 | 4 | 0 | 0 | 0 | respaldada |
| 2 | Vota cuando la elección moviliza | 0 | 0 | 0 | nan | nan | sin pruebas de motivo (patrón medido en D-030) |
| 3 | Emigración a EE. UU. | 4 | 3 | 0 | 0 | 1 | parcial |
| 4 | Domicilio desactualizado / recién llegados | 4 | 1 | 1 | 1 | 1 | parcial |
| 5 | Barreras de acceso | 7 | 5 | 0 | 1 | 1 | parcial |

## Tendencia de la diferencia observada − esperada (puntos porcentuales)

| perfil | eleccion | observada_pct | esperada_pct | dif_pp | ic_inf | ic_sup |
|---|---|---|---|---|---|---|
| 1 | 2009 | 36.82 | 43.3 | -6.476 | -8.872 | -4.207 |
| 1 | 2012 | 52.11 | 61.65 | -9.539 | -11.05 | -8.11 |
| 1 | 2015 | 35.47 | 46.17 | -10.7 | -12.88 | -8.695 |
| 1 | 2018 | 48.52 | 61.91 | -13.39 | -14.34 | -12.35 |
| 1 | 2021 | 36.93 | 50.86 | -13.93 | -14.92 | -12.77 |
| 1 | 2024 | 46.52 | 58.22 | -11.7 | -12.58 | -10.73 |
| 1 | pendiente_pp_por_eleccion | nan | nan | -1.199 | -1.63 | -0.751 |
| 2 | 2009 | 37.71 | 43.82 | -6.114 | -7.123 | -5.178 |
| 2 | 2012 | 58.21 | 62.06 | -3.853 | -4.53 | -3.289 |
| 2 | 2015 | 40.05 | 47.3 | -7.25 | -8.246 | -6.318 |
| 2 | 2018 | 60.04 | 62.97 | -2.931 | -3.745 | -2.143 |
| 2 | 2021 | 46.04 | 52.7 | -6.659 | -7.301 | -5.961 |
| 2 | 2024 | 57.7 | 60.68 | -2.986 | -3.611 | -2.346 |
| 2 | pendiente_pp_por_eleccion | nan | nan | 0.33 | 0.139 | 0.515 |
| 3 | 2009 | 37.11 | 44.64 | -7.536 | -8.164 | -6.913 |
| 3 | 2012 | 53.08 | 62.08 | -9.001 | -9.485 | -8.503 |
| 3 | 2015 | 42.77 | 47.41 | -4.641 | -5.232 | -4.064 |
| 3 | 2018 | 52.15 | 62.09 | -9.942 | -10.58 | -9.275 |
| 3 | 2021 | 42.66 | 51.73 | -9.079 | -9.837 | -8.318 |
| 3 | 2024 | 48.24 | 58.89 | -10.64 | -11.14 | -10.17 |
| 3 | pendiente_pp_por_eleccion | nan | nan | -0.602 | -0.776 | -0.431 |
| 4 | 2009 | 33.69 | 44.42 | -10.73 | -12.6 | -8.065 |
| 4 | 2012 | 54.49 | 62.77 | -8.288 | -9.574 | -6.44 |
| 4 | 2015 | 35.02 | 47.67 | -12.65 | -14.76 | -9.611 |
| 4 | 2018 | 54 | 63.2 | -9.203 | -10.16 | -8.015 |
| 4 | 2021 | 41.01 | 52.31 | -11.31 | -12.28 | -10.05 |
| 4 | 2024 | 50.73 | 59.93 | -9.202 | -10.46 | -7.749 |
| 4 | pendiente_pp_por_eleccion | nan | nan | 0.058 | -0.348 | 0.361 |
| 5 | 2009 | 33.99 | 45.42 | -11.43 | -12.12 | -10.73 |
| 5 | 2012 | 53.62 | 62.44 | -8.821 | -9.637 | -8.034 |
| 5 | 2015 | 38.15 | 47.21 | -9.064 | -10.03 | -8.024 |
| 5 | 2018 | 54.2 | 61.43 | -7.23 | -7.982 | -6.506 |
| 5 | 2021 | 44.03 | 50.41 | -6.386 | -7.516 | -5.137 |
| 5 | 2024 | 46.46 | 57.12 | -10.66 | -11.6 | -9.834 |
| 5 | pendiente_pp_por_eleccion | nan | nan | 0.371 | 0.171 | 0.568 |
| 1 | pendiente_P1_menos_media_otros | nan | nan | -1.238 | -1.601 | -0.847 |

## Elecciones de implementación (no están fijadas literalmente en D-034)

- Cada inciso de una predicción con dos partes (p. ej. P3.i: «es más profunda» y «mayor que en los demás perfiles») se prueba y califica por separado; el veredicto de lectura cuenta incisos.
- Peso de la brecha de grupo: n_2024; en las celdas sin n_2024 tampoco hay ln_2024 (sin población 2024), así que pesan 0.
- Peso LN de la sección = Σ ln_2024 de todas sus celdas (mismo denominador de la regla de mayoría). Contrastes: solo secciones donde ambos grupos tienen peso > 0.
- «Demás perfiles» = secciones mayoritarias de los otros cuatro perfiles juntas (las sin perfil mayoritario no entran).
- P3.iii: mediana ponderada (peso LN de la sección) de razon_ln_p18 en secciones P3 menos la mediana en la población objetivo (secciones ponderadas por su LN 2024 de celdas objetivo).
- P5.iii: rural = tiposec R, urbana = tiposec U (las mixtas M no entran); brecha de sección ponderada por LN.
- Tendencia: perfil asignado por celda (columna `perfil`); esperada = Σ n·q_gse/Σ n con q_gse nacional fijo (no se recalcula en cada réplica); bootstrap con las mismas multiplicidades de municipio aplicadas a las celdas; pendiente sobre el índice de elección 0..5 (2009, 2012, 2015, 2018, 2021, 2024: espaciadas 3 años, la pendiente es por elección).
- Sensibilidad de edad (D-034, agregado): los seis contrastes de edad se repiten con log(sv_2024/E_2024) (celdas con sv_2024 > 0 y E_2024 > 0, mismo peso n_2024, misma pertenencia y mismas réplicas). Veredicto combinado: igual en ambas medidas, se queda; si no, «no concluyente» (no cuenta). Lectura: respaldada = todos los incisos concluyentes se cumplen y ninguno es contrario; parcial = alguno se cumple; no respaldada = ninguno. Los renglones con id terminado en -L son la versión log(O/E); la columna `veredicto_combinado` es la que cuenta.
- Asociaciones: se descartan las secciones con descriptor NaN; la brecha de la sección usa todas sus celdas (peso n_2024).
- Un IC de percentil del bootstrap sin corrección; las asociaciones entre secciones son contextuales (D-010).


Tiempo total: 2 s.
