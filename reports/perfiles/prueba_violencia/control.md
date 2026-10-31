# Prueba de la violencia homicida dentro del modelo (D-027)

La violencia es una continua aparte (`z_violencia`, log de la tasa municipal contraída estandarizado a nivel sección con pesos LN 2024), fuera de la PCA (D-027). Asociación, no causa (D-010, D-027). El contexto describe secciones, no personas.

## 0. Cifras de control

- [OK] celdas objetivo = 472,539 (esperadas 472,539)
- [OK] Σ pesos = 472,539.000 = nº de celdas 472,539
- [OK] secciones sin tasa v2023 = 195 (195 esperadas; merge m:1 por (edo, mpio))
- [OK] secciones = 70,751
- [OK] z_violencia (v2023) tiene media 0 y sd 1 ponderadas por LN 2024
- [OK] celdas objetivo sin tasa (se marginan, D-024): 1,739 (0.37%)
- [OK] variables continuas: ['delta', 'pc1', 'pc2', 'pc3', 'z_violencia']
- [OK] responsabilidades suman 1 por celda
- [OK] perfiles_k4.parquet cuadra 1:1 con las celdas objetivo
- [OK] pesos w de perfiles_k4 = pesos de esta corrida
- [OK] población objetivo 2009-21 = 396,632 celdas
- [OK] mezcla 2009-21: Σ pesos = 396,632.0 = nº de celdas 396,632
- [OK] solo celdas con historial 2009-21: AUC_pos mezcla sin violencia = 0.72971 reproduce referencia_cuatro_perfiles (0.72971)
- [OK] solo celdas con historial 2009-21: AUC_pos historial propio = 0.75909 reproduce referencia_cuatro_perfiles (0.75909)
- [OK] todas las celdas con 2024: AUC_pos mezcla sin violencia = 0.68917 reproduce referencia_cuatro_perfiles (0.68917)
- [OK] todas las celdas con 2024: AUC_pos historial propio = 0.69198 reproduce referencia_cuatro_perfiles (0.69198)
- [OK] AUC con historial de la mezcla K=4 sin violencia = 0.730
- [OK] solo celdas con historial 2009-21 · (i) mezcla con − mezcla sin: AUC observado = AUC de la tabla de capturas
- [OK] solo celdas con historial 2009-21 · (ii) historial propio − mezcla sin: AUC observado = AUC de la tabla de capturas
- [OK] solo celdas con historial 2009-21 · (ii) historial propio − mezcla con: AUC observado = AUC de la tabla de capturas
- [OK] todas las celdas con 2024 · (i) mezcla con − mezcla sin: AUC observado = AUC de la tabla de capturas
- [OK] todas las celdas con 2024 · (ii) historial propio − mezcla sin: AUC observado = AUC de la tabla de capturas
- [OK] todas las celdas con 2024 · (ii) historial propio − mezcla con: AUC observado = AUC de la tabla de capturas

- logL K=4 con violencia -5,198,294.5; K=1 -5,689,441.1; reinicios 4, óptimo repetido True (2 veces), no convergieron 0, pisos 0. Mezcla 2009-21 con violencia: logL -4,289,591.0, reinicios 3, repetido True, pisos 0.
- Tiempos (s) de la corrida que calculó cada etapa (las siguientes leen la caché): ajuste K=4 y K=1 98, estabilidad 213, prueba contra el azar 1436, universo 2009-21 2, ajuste 2009-21 con violencia 37, bootstrap ΔAUC (B=1999, 6 comparaciones) 2; total 14. CPU del bootstrap de estabilidad: 0.20 h-CPU.

## 1. Correlación de la violencia con los componentes principales

Spearman ponderada por LN 2024, a nivel sección, en las 70,556 secciones con tasa (z_violencia v2023 contra pc1–pc3):

| componente | spearman_ponderada | secciones |
|---|---|---|
| pc1 | -0.0565 | 70556 |
| pc2 | 0.0781 | 70556 |
| pc3 | -0.1476 | 70556 |


## 2. Estabilidad y prueba contra el azar de K=4 con violencia

- Bootstrap de secciones estratificado por estado: B = 20 réplicas (mín. 20, EE ≤ 0.025, tope 200; tope alcanzado: no); control en frío: 5 réplicas, t crítico 2.78.

| perfil | clase | jaccard_medio | ee_mc | lectura_fpc | jaccard_frio_medio | dif_tibio_menos_frio | ee_dif | frio_domina |
|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 0.9466 | 0.0053 | muy estable | 0.9425 | 0.0002 | 0.0001 | False |
| 2 | 0 | 0.957 | 0.0041 | muy estable | 0.9537 | 0.0001 | 0.0001 | False |
| 3 | 3 | 0.9654 | 0.0046 | muy estable | 0.9691 | 0.0 | 0.0 | False |
| 4 | 1 | 0.9672 | 0.0028 | muy estable | 0.9662 | 0.0 | 0.0 | False |


- Prueba contra el azar (cada variable continua, incluida la violencia, y categórica permutada por separado): G_obs = 491,146.6 nats; G_nulo (B = 19): mín 166,671.1, mediana 171,092.2, máx 173,925.6; permutaciones con G ≥ G_obs: 0; **p = 0.050** (mínimo posible 0.050); ajustes nulos cuyo óptimo no se repitió: 4.

## 3. Perfiles K=4 con violencia (orden por % del déficit)

Tasa de homicidio = tasa municipal contraída 2009–2023 por 100 mil habitantes por año (`tasa_contr_v2023`); mediana ponderada por responsabilidad × w, calculada a nivel celda sobre las celdas con tasa. `mediana_z_violencia` = mediana de `z_violencia`.

| perfil | pct_deficit | celdas | ln_2024_miles | delta_medio | pct_crudo_2024 | pmax_media | pct_pmax_ge_09 | med_graproes | med_prop_internet | med_im_2020 | med_pctl_mov_estado | mediana_tasa_homicidio_100mil | mediana_z_violencia |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 35.005 | 111548.424 | 12585.776 | -0.636 | 34.914 | 0.846 | 50.203 | 9.58 | 0.61 | 59.14 | 66.348 | 33.064 | 0.87 |
| 2 | 34.123 | 178716.89 | 24127.865 | -0.336 | 28.185 | 0.886 | 65.27 | 9.73 | 0.574 | 59.079 | 47.882 | 15.747 | -0.045 |
| 3 | 18.575 | 103041.594 | 7908.388 | -0.601 | 22.065 | 0.899 | 70.635 | 7.58 | 0.289 | 56.961 | 67.635 | 27.525 | 0.644 |
| 4 | 12.296 | 79232.092 | 6047.253 | -0.604 | 14.836 | 0.908 | 71.384 | 7.52 | 0.228 | 54.329 | 71.39 | 15.798 | -0.041 |


K=4 sin violencia (referencia_cuatro_perfiles), la misma mediana de tasa de homicidio para comparar (numeración propia de ese ajuste):

| perfil | pct_deficit_sin_violencia | mediana_tasa_homicidio_100mil |
|---|---|---|
| 1 | 36.157 | 17.496 |
| 2 | 33.279 | 26.741 |
| 3 | 19.644 | 24.308 |
| 4 | 10.92 | 17.961 |


### Rasgos sobrerrepresentados con violencia (razón ≥ 1.25 o ≥ 40%; filtro solo de presentación)

#### Perfil 1

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 43.69 | 0.91 |
| sexo | 1 | 56.31 | 1.08 |
| circunscripcion | 1 | 82.63 | 2.24 |
| tiposec | U | 87.59 | 1.2 |


#### Perfil 2

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 47.05 | 0.98 |
| sexo | 1 | 52.95 | 1.01 |
| circunscripcion | 3 | 20.68 | 1.36 |
| circunscripcion | 4 | 26.29 | 2.0 |
| circunscripcion | 5 | 20.46 | 1.57 |
| tiposec | U | 91.8 | 1.26 |


#### Perfil 3

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 56.61 | 1.18 |
| sexo | 1 | 43.39 | 0.83 |
| grupo | 6 | 8.62 | 1.49 |
| grupo | 7 | 7.51 | 1.64 |
| circunscripcion | 2 | 37.5 | 1.72 |
| circunscripcion | 5 | 25.46 | 1.95 |
| tiposec | M | 20.4 | 1.59 |
| tiposec | R | 45.54 | 3.23 |


#### Perfil 4

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 48.35 | 1.01 |
| sexo | 1 | 51.65 | 0.99 |
| grupo | 1 | 6.6 | 1.62 |
| grupo | 2 | 14.06 | 1.52 |
| grupo | 7 | 7.79 | 1.7 |
| circunscripcion | 3 | 61.57 | 4.06 |
| tiposec | M | 21.39 | 1.67 |
| tiposec | R | 39.73 | 2.82 |


## 4. ARI contra el K=4 sin violencia

472,539 celdas objetivo: **ARI ponderado (w) = 0.6062**; sin ponderar 0.5806. Cruce (fila = perfil sin violencia; % del peso w que cae en cada perfil con violencia):

| perfil sin violencia | con_perfil_1 | con_perfil_2 | con_perfil_3 | con_perfil_4 |
|---|---|---|---|---|
| 1 | 18.7 | 79.6 | 1.2 | 0.5 |
| 2 | 85.8 | 11.2 | 1.9 | 1.1 |
| 3 | 0.3 | 5.1 | 86.3 | 8.3 |
| 4 | 1.9 | 0.4 | 3.4 | 94.2 |


## 5. Mezcla 2009–21 con violencia (v2020, estandarizada con sus propios parámetros)

- Población objetivo_0921 396,632 celdas (w=0: 200); z_violencia v2020: media ponderada -8.7553, sd 0.8020 (v2023: -8.7195, 0.8104).
- Reetiquetado Hungarian contra el K=4 del periodo completo **con violencia** en 367,230 celdas comunes; ARI ponderado 0.806 (sin violencia contra su K=4: 0.813, 367,230 celdas).
- Razones ΣO/ΣE por perfil 2009-21 con violencia: [0.7976, 0.8989, 0.8346, 0.8427] (no objetivo con historial 1.1521); sin violencia: [0.902, 0.7491, 0.8407, 0.832] (1.1521).

| clase 2009-21 | perfil_completo_1 | perfil_completo_2 | perfil_completo_3 | perfil_completo_4 |
|---|---|---|---|---|
| clase 2009-21 → perfil 1 | 2.9 | 7.2 | 97.6 | 5.9 |
| clase 2009-21 → perfil 2 | 1.1 | 0.9 | 2.2 | 93.2 |
| clase 2009-21 → perfil 3 | 94.1 | 4.6 | 0.2 | 0.1 |
| clase 2009-21 → perfil 4 | 2.0 | 87.3 | 0.0 | 0.8 |


## 6. Regla de permanencia (D-027)

AUC_pos de la curva de captura fuera de tiempo (D-025). ΔAUC = AUC(1) − AUC(2). Bootstrap pareado que remuestrea **secciones** con reemplazo, estratificado por estado (D-017), B = 1999, semilla [C.SEMILLA, 6], ambas curvas recalculadas en cada réplica; intervalo percentil 95% = estadísticos de orden 50 y 1950 de 1999 (Davison y Hinkley, 1997). **Mide la variabilidad del conjunto de evaluación (qué secciones se evalúan), no la del ajuste de los modelos.** ### AUC_pos por método

| universo | metodo | AUC_pos | celdas |
|---|---|---|---|
| solo celdas con historial 2009-21 | historial propio | 0.75909 | 788460 |
| solo celdas con historial 2009-21 | mezcla sin violencia | 0.72971 | 788460 |
| solo celdas con historial 2009-21 | mezcla con violencia | 0.72438 | 788460 |
| todas las celdas con 2024 | historial propio | 0.69198 | 958098 |
| todas las celdas con 2024 | mezcla sin violencia | 0.68917 | 958098 |
| todas las celdas con 2024 | mezcla con violencia | 0.68489 | 958098 |


### ΔAUC_pos con IC95%

| universo | comparacion | AUC_1 | AUC_2 | delta_AUC | IC95_inf | IC95_sup | excluye_0 | B | seg |
|---|---|---|---|---|---|---|---|---|---|
| solo celdas con historial 2009-21 | (i) mezcla con − mezcla sin | 0.72438 | 0.72971 | -0.00533 | -0.00641 | -0.00423 | True | 1999 | 133.39942 |
| solo celdas con historial 2009-21 | (ii) historial propio − mezcla sin | 0.75909 | 0.72971 | 0.02938 | 0.02835 | 0.03038 | True | 1999 | 281.71643 |
| solo celdas con historial 2009-21 | (ii) historial propio − mezcla con | 0.75909 | 0.72438 | 0.03471 | 0.03353 | 0.03582 | True | 1999 | 275.33313 |
| todas las celdas con 2024 | (i) mezcla con − mezcla sin | 0.68489 | 0.68917 | -0.00429 | -0.00513 | -0.00337 | True | 1999 | 161.50829 |
| todas las celdas con 2024 | (ii) historial propio − mezcla sin | 0.69198 | 0.68917 | 0.00281 | 0.00158 | 0.00408 | True | 1999 | 302.73015 |
| todas las celdas con 2024 | (ii) historial propio − mezcla con | 0.69198 | 0.68489 | 0.00709 | 0.00573 | 0.00848 | True | 1999 | 300.45551 |


### Veredicto mecánico (universo con historial)

Se queda = el IC95% de ΔAUC está por encima de 0 **y** K=4 con violencia mantiene estabilidad y p. Operacionalización de la segunda: Jaccard medio ≥ 0.85 (lectura `fpc` "muy estable", D-011) en las 4 clases, ninguna clase regida por el frío y p = 0.05 (0 de 19 permutaciones con G ≥ G_obs). Resultado de esa segunda condición: muy estable en todas = True; sin clase regida por el frío = True; p mínimo = True.

| modelo | delta_AUC | IC95_inf | IC95_sup | IC_por_encima_de_0 | estabilidad_fpc_y_p | veredicto |
|---|---|---|---|---|---|---|
| mezcla K=4 | -0.00533 | -0.00641 | -0.00423 | False | sí | queda como descriptor |


Figura: `permanencia.png`. Salida por celda: `data/processed/perfiles_k4_violencia.parquet`.
