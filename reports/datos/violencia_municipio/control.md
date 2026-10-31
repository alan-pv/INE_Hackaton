# Violencia homicida municipal (D-027)

Generado por `scripts/datos/violencia_municipio.py` en 7 s. Salida: `data/interim/externos/violencia_mpio.parquet` (2,465 municipios INE).

## 1. Archivos descargados (INEGI, Estadísticas de defunciones registradas)

Descubiertos con la API de descarga masiva de la página del programa (https://www.inegi.org.mx/programas/edr/). Fecha de consulta: 2026-10-26. Las ligas de INEGI devuelven HTML con código 200 si el archivo no existe, por eso el script verifica la firma `PK` del zip.

| Zip | URL | Tamaño (MB) |
|---|---|---|
| defunciones_generales_base_datos_2005_2009_dbf.zip | https://www.inegi.org.mx/contenidos/programas/edr/microdatos/defunciones/datos/defunciones_generales_base_datos_2005_2009_dbf.zip | 72.9 |
| defunciones_generales_base_datos_2010_2014_dbf.zip | https://www.inegi.org.mx/contenidos/programas/edr/microdatos/defunciones/datos/defunciones_generales_base_datos_2010_2014_dbf.zip | 94.5 |
| defunciones_base_datos_2012_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2012/defunciones_base_datos_2012_csv.zip | 20.4 |
| defunciones_base_datos_2013_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2013/defunciones_base_datos_2013_csv.zip | 17.8 |
| defunciones_base_datos_2014_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2014/defunciones_base_datos_2014_csv.zip | 19.2 |
| defunciones_base_datos_2015_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2015/defunciones_base_datos_2015_csv.zip | 24.4 |
| defunciones_base_datos_2016_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2016/defunciones_base_datos_2016_csv.zip | 20.1 |
| conjunto_de_datos_defunciones_generales_2017_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2017/conjunto_de_datos_defunciones_generales_2017_csv.zip | 21.2 |
| conjunto_de_datos_defunciones_registradas_2018_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2018/conjunto_de_datos_defunciones_registradas_2018_csv.zip | 23.6 |
| conjunto_de_datos_defunciones_registradas_2019_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2019/conjunto_de_datos_defunciones_registradas_2019_csv.zip | 23.6 |
| conjunto_de_datos_defunciones_registradas_2020_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2020/conjunto_de_datos_defunciones_registradas_2020_csv.zip | 39.0 |
| conjunto_de_datos_defunciones_registradas_2021_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2021/conjunto_de_datos_defunciones_registradas_2021_csv.zip | 40.5 |
| conjunto_de_datos_defunciones_registradas_2022_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2022/conjunto_de_datos_defunciones_registradas_2022_csv.zip | 31.6 |
| conjunto_de_datos_defunciones_registradas_2023_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2023/conjunto_de_datos_defunciones_registradas_2023_csv.zip | 34.2 |
| conjunto_de_datos_edr2024_csv.zip | https://www.inegi.org.mx/contenidos/programas/edr/datosabiertos/defunciones/2024/conjunto_de_datos_edr2024_csv.zip | 31.0 |

Formato: 2009–2011 vienen en DBF (los datos abiertos CSV de INEGI empiezan en 2012); 2012–2024 en CSV. Las ediciones son por **año de registro** y son disjuntas (columna 'filas con anio_regis distinto' = 0).

## 2. Códigos usados por edición

Homicidio = código 2 en `presunto` (ediciones 2009–2021: 1 accidente, 2 homicidio, 3 suicidio, 4 se ignora, 5 operaciones legales, 8 no aplica) y en `tipo_defun` (2022–2024: 1 accidente, 2 homicidio, 3 suicidio, 4 enfermedad, 5 intervención legal, 9 se ignora). Entidad y municipio de ocurrencia: `ent_ocurr`, `mun_ocurr` (999 = municipio no especificado, ent. 99 = no especificada); año de ocurrencia: `anio_ocur` (9999 = no especificado). En 2024 el diccionario anuncia `CVEGEO`, pero el CSV no la trae: se arma con entidad (2 díg.) + municipio (3 díg.). Verificado en los catálogos `presunta_defuncion_violenta.csv` de los zip de 2020 y 2024.

| edicion | variable | filas | homicidios | filas_con_anio_regis_distinto |
|---|---|---|---|---|
| 2009 | presunto | 564,673 | 19,804 | 0 |
| 2010 | presunto | 592,018 | 25,757 | 0 |
| 2011 | presunto | 590,693 | 27,213 | 0 |
| 2012 | presunto | 602,354 | 25,967 | 0 |
| 2013 | presunto | 623,599 | 23,063 | 0 |
| 2014 | presunto | 633,641 | 20,013 | 0 |
| 2015 | presunto | 655,688 | 20,763 | 0 |
| 2016 | presunto | 685,766 | 24,560 | 0 |
| 2017 | presunto | 703,047 | 32,082 | 0 |
| 2018 | presunto | 722,611 | 36,687 | 0 |
| 2019 | presunto | 747,784 | 36,662 | 0 |
| 2020 | presunto | 1,086,743 | 36,773 | 0 |
| 2021 | presunto | 1,122,249 | 35,700 | 0 |
| 2022 | tipo_defun | 847,716 | 33,291 | 0 |
| 2023 | tipo_defun | 799,869 | 32,253 | 0 |
| 2024 | tipo_defun | 819,672 | 33,550 | 0 |

## 3. Totales nacionales contra la cifra oficial

### 3.1 Por año de REGISTRO (la edición completa), contra INEGI

| año | edición (registro) | oficial | dif | fuente oficial |
|---|---|---|---|---|
| 2009 | 19,804 | 19,803 | 1 | prensa que cita a INEGI (La Opinión; sin boletín oficial localizado) |
| 2010 | 25,757 | 25,757 | 0 | prensa que cita a INEGI (La Opinión; sin boletín oficial localizado) |
| 2011 | 27,213 | 27,213 | 0 | prensa que cita a INEGI (La Opinión; sin boletín oficial localizado) |
| 2019 | 36,662 | 36,476 | 186 | boletín INEGI 2020, dato PRELIMINAR |
| 2020 | 36,773 | 36,773 | 0 | boletín INEGI 2021, resultados definitivos |
| 2022 | 33,291 | 32,223 | 1,068 | boletín INEGI 2023, dato PRELIMINAR |
| 2024 | 33,550 | 33,550 | 0 | prensa que cita resultados definitivos de INEGI (Excélsior) |

Las cifras 'PRELIMINAR' se revisan al alza en la edición definitiva, por eso la edición descargada puede ser mayor. Coincide exactamente la definitiva 2020 (36,773) y la de 2024 (33,550). Las cifras [P] de 2009–2011 vienen de prensa y no tienen boletín oficial localizado (se citan de prensa).

### 3.2 Por año de OCURRENCIA (sumando todas las ediciones descargadas; es la serie que se usa)

| año ocurrencia | homicidios (todas las ediciones) | de ellos, registrados después |
|---|---|---|
| 2009 | 19833 | 779 |
| 2010 | 26149 | 1,149 |
| 2011 | 27513 | 1,350 |
| 2012 | 25989 | 1,261 |
| 2013 | 22612 | 860 |
| 2014 | 19716 | 660 |
| 2015 | 20406 | 437 |
| 2016 | 24781 | 752 |
| 2017 | 32333 | 958 |
| 2018 | 36631 | 1,109 |
| 2019 | 36511 | 1,005 |
| 2020 | 36995 | 1,351 |
| 2021 | 35216 | 1,043 |
| 2022 | 32848 | 953 |
| 2023 | 31701 | 795 |
| 2024 | 32065 | 0 |

Rezago: las ocurrencias de 2023 se completan con la edición 2024 (y quedan sin las registradas en 2025 en adelante, aún no publicadas); las de 2009 tienen 15 años de ediciones. La subestimación del último año es de un orden parecido al aporte de la última edición (columna 'registrados después' de años recientes).

## 4. No especificados y no mapeados

### Ventana v2023 (2009–2023)

| concepto | homicidios / cuenta |
|---|---|
| total_todas_ocurrencias | 464,138 |
| anio_no_especificado | 1,820 |
| fuera_de_ventana | 33,084 |
| en_ventana | 429,234 |
| en_ventana_ent_no_esp | 5,902 |
| en_ventana_mun_no_esp | 1,204 |
| homicidios_mapeados | 422,011 |
| homicidios_mun_sin_mapear | 117 |
| n_claves_sin_mapear | 8 |
| n_mpios_sin_exposicion | 0 |

Claves INEGI con homicidios que no están en el mapeo (top 10):

| cve_geo | n_hom |
|---|---|
| 02006 | 86 |
| 02007 | 18 |
| 20319 | 5 |
| 12083 | 2 |
| 20209 | 2 |
| 17036 | 2 |
| 04013 | 1 |
| 12085 | 1 |

### Ventana v2020 (2009–2020)

| concepto | homicidios / cuenta |
|---|---|
| total_todas_ocurrencias | 464,138 |
| anio_no_especificado | 1,820 |
| fuera_de_ventana | 132,849 |
| en_ventana | 329,469 |
| en_ventana_ent_no_esp | 4,248 |
| en_ventana_mun_no_esp | 672 |
| homicidios_mapeados | 324,526 |
| homicidios_mun_sin_mapear | 23 |
| n_claves_sin_mapear | 3 |
| n_mpios_sin_exposicion | 1 |

Claves INEGI con homicidios que no están en el mapeo (top 10):

| cve_geo | n_hom |
|---|---|
| 02006 | 16 |
| 20319 | 5 |
| 20209 | 2 |

Los 'no especificados' (año, entidad o municipio) se cuentan y **no se reparten**: no entran a ninguna tasa. Los homicidios en municipios sin mapear tampoco.

## 5. Municipios creados después de 2009 (decisión de cómputo, a ratificar)

Regla usada: años de exposición de un municipio = desde `max(2009, primer año con alguna defunción registrada en ese municipio)` hasta el fin de la ventana. 13 municipios del catálogo aparecen después de 2009:

| edo | mpio | cve_geo | primer_anio | poblacion |
|---|---|---|---|---|
| 4 | 13 | 04012 | 2019 | 15,297 |
| 7 | 119 | 07120 | 2018 | 4,315 |
| 7 | 120 | 07121 | 2018 | 8,718 |
| 7 | 121 | 07122 | 2018 | 15,587 |
| 7 | 122 | 07123 | 2018 | 10,783 |
| 7 | 123 | 07124 | 2016 | 23,847 |
| 7 | 124 | 07125 | 2021 | 11,650 |
| 17 | 34 | 17034 | 2019 | 11,347 |
| 17 | 35 | 17035 | 2013 | 27,805 |
| 20 | 254 | 20256 | 2010 | 229 |
| 20 | 280 | 20282 | 2010 | 653 |
| 20 | 518 | 20518 | 2010 | 113 |
| 23 | 11 | 23011 | 2014 | 26,921 |

Limitación: antes de su creación, las ocurrencias de su territorio están en el municipio de origen, cuya población (Censo 2020) ya no incluye al nuevo. Esto infla levemente la tasa del municipio de origen. No se reasigna por falta de una tabla oficial de segregaciones.

## 6. Dispersión estimada (φ = varianza relativa de la tasa municipal; k = 1/φ)

Se ajusta por máxima verosimilitud de la binomial negativa marginal, con media = tasa del estado. Se estima **una φ por estado**; si el óptimo de un estado cae en la frontera de búsqueda (verosimilitud monótona, sin información) se usa la φ nacional. Regla de cómputo declarada (D-027).

### v2023: φ nacional = 0.498; estados que usan la nacional: 1

| edo | n_mpios | phi_estado | en_frontera | phi_usado | fuente |
|---|---|---|---|---|---|
| 1 | 11 | 0.000 | 1 | 0.498 | nacional |
| 2 | 5 | 0.298 | 0 | 0.298 | estado |
| 3 | 5 | 0.113 | 0 | 0.113 | estado |
| 4 | 12 | 0.531 | 0 | 0.531 | estado |
| 5 | 38 | 0.529 | 0 | 0.529 | estado |
| 6 | 10 | 0.156 | 0 | 0.156 | estado |
| 7 | 124 | 0.558 | 0 | 0.558 | estado |
| 8 | 67 | 0.451 | 0 | 0.451 | estado |
| 9 | 16 | 0.221 | 0 | 0.221 | estado |
| 10 | 39 | 0.528 | 0 | 0.528 | estado |
| 11 | 46 | 0.491 | 0 | 0.491 | estado |
| 12 | 81 | 0.370 | 0 | 0.370 | estado |
| 13 | 84 | 0.311 | 0 | 0.311 | estado |
| 14 | 125 | 0.331 | 0 | 0.331 | estado |
| 15 | 125 | 0.256 | 0 | 0.256 | estado |
| 16 | 113 | 0.295 | 0 | 0.295 | estado |
| 17 | 35 | 0.441 | 0 | 0.441 | estado |
| 18 | 20 | 0.459 | 0 | 0.459 | estado |
| 19 | 51 | 2.199 | 0 | 2.199 | estado |
| 20 | 568 | 0.705 | 0 | 0.705 | estado |
| 21 | 217 | 0.393 | 0 | 0.393 | estado |
| 22 | 18 | 0.092 | 0 | 0.092 | estado |
| 23 | 11 | 0.452 | 0 | 0.452 | estado |
| 24 | 58 | 0.234 | 0 | 0.234 | estado |
| 25 | 18 | 0.272 | 0 | 0.272 | estado |
| 26 | 72 | 0.862 | 0 | 0.862 | estado |
| 27 | 17 | 0.243 | 0 | 0.243 | estado |
| 28 | 43 | 1.035 | 0 | 1.035 | estado |
| 29 | 60 | 0.333 | 0 | 0.333 | estado |
| 30 | 212 | 0.459 | 0 | 0.459 | estado |
| 31 | 106 | 0.326 | 0 | 0.326 | estado |
| 32 | 58 | 0.552 | 0 | 0.552 | estado |

### v2020: φ nacional = 0.508; estados que usan la nacional: 0

| edo | n_mpios | phi_estado | en_frontera | phi_usado | fuente |
|---|---|---|---|---|---|
| 1 | 11 | 0.034 | 0 | 0.034 | estado |
| 2 | 5 | 0.266 | 0 | 0.266 | estado |
| 3 | 5 | 0.137 | 0 | 0.137 | estado |
| 4 | 12 | 0.477 | 0 | 0.477 | estado |
| 5 | 38 | 0.464 | 0 | 0.464 | estado |
| 6 | 10 | 0.287 | 0 | 0.287 | estado |
| 7 | 123 | 0.549 | 0 | 0.549 | estado |
| 8 | 67 | 0.512 | 0 | 0.512 | estado |
| 9 | 16 | 0.233 | 0 | 0.233 | estado |
| 10 | 39 | 0.498 | 0 | 0.498 | estado |
| 11 | 46 | 0.464 | 0 | 0.464 | estado |
| 12 | 81 | 0.387 | 0 | 0.387 | estado |
| 13 | 84 | 0.291 | 0 | 0.291 | estado |
| 14 | 125 | 0.323 | 0 | 0.323 | estado |
| 15 | 125 | 0.259 | 0 | 0.259 | estado |
| 16 | 113 | 0.306 | 0 | 0.306 | estado |
| 17 | 35 | 0.540 | 0 | 0.540 | estado |
| 18 | 20 | 0.468 | 0 | 0.468 | estado |
| 19 | 51 | 2.434 | 0 | 2.434 | estado |
| 20 | 568 | 0.734 | 0 | 0.734 | estado |
| 21 | 217 | 0.413 | 0 | 0.413 | estado |
| 22 | 18 | 0.115 | 0 | 0.115 | estado |
| 23 | 11 | 0.447 | 0 | 0.447 | estado |
| 24 | 58 | 0.232 | 0 | 0.232 | estado |
| 25 | 18 | 0.304 | 0 | 0.304 | estado |
| 26 | 72 | 0.910 | 0 | 0.910 | estado |
| 27 | 17 | 0.262 | 0 | 0.262 | estado |
| 28 | 43 | 1.070 | 0 | 1.070 | estado |
| 29 | 60 | 0.335 | 0 | 0.335 | estado |
| 30 | 212 | 0.478 | 0 | 0.478 | estado |
| 31 | 106 | 0.366 | 0 | 0.366 | estado |
| 32 | 58 | 0.368 | 0 | 0.368 | estado |

## 7. Distribución de la tasa contraída (por 100 mil por año)

### v2023

| estadístico | contraída | cruda |
|---|---|---|
| count | 2,465.000 | 2,465.000 |
| mean | 20.705 | 20.516 |
| std | 25.823 | 27.938 |
| min | 0.780 | 0.000 |
| 5% | 2.595 | 0.000 |
| 25% | 7.456 | 6.189 |
| 50% | 13.057 | 12.550 |
| 75% | 23.974 | 24.684 |
| 95% | 62.556 | 65.561 |
| 99% | 129.662 | 135.875 |
| max | 364.853 | 403.780 |

Municipios con tasa: 2,465 de 2,465.

### v2020

| estadístico | contraída | cruda |
|---|---|---|
| count | 2,464.000 | 2,464.000 |
| mean | 20.582 | 20.417 |
| std | 27.093 | 29.663 |
| min | 0.840 | 0.000 |
| 5% | 2.566 | 0.000 |
| 25% | 7.271 | 5.886 |
| 50% | 12.962 | 12.356 |
| 75% | 23.358 | 23.830 |
| 95% | 61.127 | 65.192 |
| 99% | 139.155 | 153.364 |
| max | 420.010 | 461.770 |

Municipios con tasa: 2,464 de 2,465.

## 8. Top-10 municipios por tasa contraída (revisión de plausibilidad)

### v2023

| cve_geo | municipio | poblacion | hom_v2023 | tasa_cruda_v2023 | tasa_contr_v2023 |
|---|---|---|---|---|---|
| 19050 | Vallecillo | 1,552 | 94 | 403.780 | 364.853 |
| 08028 | Guadalupe | 4,237 | 232 | 365.038 | 352.229 |
| 19015 | Doctor Coss | 1,360 | 77 | 377.451 | 336.636 |
| 08029 | Guadalupe y Calvo | 50,514 | 1,680 | 221.721 | 221.155 |
| 19040 | Parás | 906 | 34 | 250.184 | 212.704 |
| 08041 | Maguarichi | 1,302 | 41 | 209.933 | 192.323 |
| 26065 | Tubutama | 1,473 | 46 | 208.192 | 184.501 |
| 08053 | Praxedis G. Guerrero | 5,111 | 143 | 186.526 | 182.419 |
| 08047 | Moris | 4,447 | 122 | 182.895 | 178.354 |
| 26060 | Sáric | 2,058 | 59 | 191.124 | 175.211 |

### v2020

| cve_geo | municipio | poblacion | hom_v2020 | tasa_cruda_v2020 | tasa_contr_v2020 |
|---|---|---|---|---|---|
| 08028 | Guadalupe | 4,237 | 222 | 436.630 | 420.010 |
| 19050 | Vallecillo | 1,552 | 86 | 461.770 | 408.354 |
| 19015 | Doctor Coss | 1,360 | 47 | 287.990 | 251.426 |
| 08029 | Guadalupe y Calvo | 50,514 | 1,489 | 245.641 | 244.963 |
| 19040 | Parás | 906 | 32 | 294.334 | 241.714 |
| 08041 | Maguarichi | 1,302 | 40 | 256.016 | 231.773 |
| 08053 | Praxedis G. Guerrero | 5,111 | 139 | 226.635 | 220.899 |
| 28024 | Mier | 6,385 | 157 | 204.907 | 196.944 |
| 08066 | Uruachi | 6,512 | 153 | 195.792 | 192.200 |
| 26065 | Tubutama | 1,473 | 40 | 226.296 | 189.289 |

## 9. Estabilidad entre ventanas

Correlación de Spearman entre log tasa contraída v2020 y v2023 (n = 2,464 municipios): **0.9763**.

## 10. Notas

- Población constante (Censo 2020, `pob_tot_conapo`) para todos los años: es un denominador (D-027), no una serie.
- Homicidio = presunto homicidio del certificado de defunción (INEGI), no el SESNSP (D-027).
- Municipios con 0 homicidios en la ventana tienen tasa cruda 0 y tasa contraída > 0 (nunca log de cero).
