# Selección del número de perfiles: mezcla de clases latentes sobre la población objetivo (D-024, D-029)

Los perfiles representan **votos faltantes** (pesos w = déficit), no personas. El contexto describe la sección, no a las personas (D-010).

- Celdas objetivo: **472,539**; con w = 0 (déficit ≤ 0): **162**. Pesos normalizados a Σw = 472,539.
- Categorías: sexo = [0, 1]; grupo = [1, 2, 3, 4, 5, 6, 7]; circunscripcion = [1, 2, 3, 4, 5]; tiposec = ['M', 'R', 'U']. NaN como categoría propia: no existe.
- Continuas: delta, pc1, pc2, pc3. Faltantes de δ̃ en la población objetivo: 0.

## 1. PCA del contexto y análisis paralelo de Horn

- Secciones: 70,751; completas (usadas para estimar el PCA): 67,673; con algún NaN (proyectadas con valores estandarizados faltantes = 0): **3,078**.
- Estandarización con media y desviación ponderadas por LN 2024; PCA = vectores propios de la covarianza ponderada (matriz de correlación).
- Horn: 20 permutaciones (bloques de 20 hasta que 2×EE < |observado − media permutada| en todos los componentes, tope 1000; tope alcanzado: no). EE Monte Carlo máximo de la media permutada: 0.0275.
- **Componentes retenidos: 3** (valor propio observado > media permutada).

| comp | observado | media_permutada | EE_MC | var_explicada_% |
|---|---|---|---|---|
| 1 | 7.1382 | 1.5105 | 0.0275 | 39.6566 |
| 2 | 2.4567 | 1.4042 | 0.0078 | 13.6483 |
| 3 | 1.4039 | 1.3388 | 0.0032 | 7.7997 |
| 4 | 1.1400 | 1.2991 | 0.0043 | 6.3331 |
| 5 | 1.0056 | 1.2538 | 0.0047 | 5.5869 |
| 6 | 0.9877 | 1.2344 | 0.0034 | 5.4870 |
| 7 | 0.8870 | 1.2197 | 0.0022 | 4.9278 |


Varianza explicada acumulada por los 3 retenidos: **61.1%**.

Cargas (columnas originales estandarizadas):

| variable | pc1 | pc2 | pc3 |
|---|---|---|---|
| graproes | -0.332 | 0.041 | 0.215 |
| prop_sin_escolaridad | 0.332 | 0.01 | 0.139 |
| prop_analfabeta | 0.343 | 0.011 | 0.188 |
| prop_posbasica | -0.312 | 0.06 | 0.289 |
| prop_hli | 0.237 | -0.068 | 0.432 |
| prop_afro | 0.012 | 0.021 | 0.167 |
| prop_internet | -0.329 | 0.042 | 0.147 |
| prop_celular | -0.306 | -0.071 | -0.183 |
| prop_nacida_otra_ent | -0.194 | -0.161 | 0.329 |
| prop_res_otra_ent_2015 | -0.128 | -0.239 | 0.397 |
| prop_discapacidad | 0.079 | 0.404 | -0.068 |
| prop_18a24 | 0.133 | -0.452 | -0.224 |
| prop_60ymas | -0.005 | 0.58 | 0.129 |
| razon_ln_p18 | 0.012 | 0.032 | -0.007 |
| iim_dp2 | -0.111 | -0.12 | 0.356 |
| im_2020 | -0.326 | -0.014 | -0.2 |
| imn_2020 | -0.326 | -0.014 | -0.2 |
| pctl_mov_estado | 0.048 | -0.424 | -0.032 |


## 2. Selección de K (D-029)

| K | logL | n_param | BIC | ICL | entropia | reinicios | repeticiones | no_convergio | pisos | seg |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | -5013096 | 21 | 10026467 | 10026467 | -0 | 1 | 1 | 0 | 0 | 1 |
| 2 | -4722743 | 43 | 9446048 | 9577614 | 65783 | 2 | 2 | 0 | 0 | 19 |
| 3 | -4644082 | 65 | 9289014 | 9585268 | 148127 | 2 | 2 | 0 | 0 | 68 |
| 4 | -4551684 | 87 | 9104504 | 9417829 | 156662 | 2 | 2 | 0 | 0 | 210 |
| 5 | -4495184 | 109 | 8991792 | 9348204 | 178206 | 2 | 2 | 0 | 0 | 210 |
| 6 | -4458866 | 131 | 8919443 | 9288720 | 184638 | 10 | 1 | 0 | 0 | 1106 |
| 7 | -4424052 | 153 | 8850104 | 9225803 | 187849 | 3 | 2 | 0 | 0 | 538 |
| 8 | -4395756 | 175 | 8793799 | 9189988 | 198094 | 3 | 2 | 0 | 0 | 743 |
| 9 | -4373161 | 197 | 8748896 | 9148127 | 199615 | 3 | 2 | 0 | 0 | 1092 |
| 10 | -4353239 | 219 | 8709339 | 9102463 | 196562 | 6 | 2 | 0 | 0 | 1994 |


- **K elegido (mínimo ICL, criterio i): 10.** Mínimo de BIC: K = 10. El BIC **no se detiene** dentro del rango (su mínimo está en el tope K = 10).
- Reinicios cuyo mejor óptimo no se repitió (< 2 reinicios a < 1 nat): K = [6]. Piso de varianza activado (suma en la M-step final): 0.

## 3. Estabilidad (bootstrap de secciones estratificado por estado, D-017)

### K = 10

- B = 32 réplicas (mínimo 20, EE ≤ 0.025, tope 200); tope alcanzado: no. Réplicas tibias a tol 1e-10: 250 iteraciones en promedio (162 s); sin convergir: 0.
- Control en frío: 5 réplicas (k-means++ + refinado), 223 s en promedio; t crítico = 2.78; diferencia media de logL tibio − frío = 4385.90 nats.

| perfil | clase | jaccard_medio | ee_mc | lectura_fpc | jaccard_frio_medio | dif_tibio_menos_frio | ee_dif | frio_domina |
|---|---|---|---|---|---|---|---|---|
| 1 | 4 | 0.879 | 0.0075 | muy estable | 0.753 | +0.1209 | 0.0378 | sí |
| 2 | 8 | 0.900 | 0.0067 | muy estable | 0.672 | +0.2220 | 0.1167 | no |
| 3 | 2 | 0.947 | 0.0067 | muy estable | 0.796 | +0.1461 | 0.0571 | no |
| 4 | 1 | 0.701 | 0.0234 | patrón | 0.580 | +0.1044 | 0.0675 | no |
| 5 | 3 | 0.884 | 0.0105 | muy estable | 0.732 | +0.1455 | 0.1125 | no |
| 6 | 0 | 0.906 | 0.0061 | muy estable | 0.792 | +0.0990 | 0.0668 | no |
| 7 | 7 | 0.895 | 0.0132 | muy estable | 0.583 | +0.2977 | 0.0922 | sí |
| 8 | 6 | 0.968 | 0.0025 | muy estable | 0.745 | +0.2202 | 0.1272 | no |
| 9 | 5 | 0.819 | 0.0150 | estable | 0.400 | +0.4123 | 0.1603 | no |
| 10 | 9 | 0.881 | 0.0125 | muy estable | 0.659 | +0.2039 | 0.0671 | sí |


### K = 4

- B = 20 réplicas (mínimo 20, EE ≤ 0.025, tope 200); tope alcanzado: no. Réplicas tibias a tol 1e-10: 96 iteraciones en promedio (26 s); sin convergir: 0.
- Control en frío: 5 réplicas (k-means++ + refinado), 47 s en promedio; t crítico = 2.78; diferencia media de logL tibio − frío = 6812.12 nats.

| perfil | clase | jaccard_medio | ee_mc | lectura_fpc | jaccard_frio_medio | dif_tibio_menos_frio | ee_dif | frio_domina |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.968 | 0.0026 | muy estable | 0.815 | +0.1503 | 0.1060 | no |
| 2 | 3 | 0.930 | 0.0051 | muy estable | 0.679 | +0.2461 | 0.1521 | no |
| 3 | 2 | 0.955 | 0.0052 | muy estable | 0.831 | +0.1217 | 0.0863 | no |
| 4 | 0 | 0.951 | 0.0044 | muy estable | 0.787 | +0.1567 | 0.1131 | no |


## 4. Prueba contra el azar (permutación de cada variable por separado, w con su celda)

- **K = 10**: G_obs = 659857.1 nats; G_nulo (B = 4): mín 216297.0, mediana 219474.0, máx 222440.0; permutaciones con G ≥ G_obs: 0; **p = 0.200** (p mínimo posible = 0.200). Ajustes nulos cuyo óptimo no se repitió: 1. 5169 s por permutación.
- **K = 4**: G_obs = 461412.4 nats; G_nulo (B = 19): mín 164893.3, mediana 169909.9, máx 173968.5; permutaciones con G ≥ G_obs: 0; **p = 0.050** (p mínimo posible = 0.050). Ajustes nulos cuyo óptimo no se repitió: 0. 178 s por permutación.

**Aviso de costo:** para K = 10 cada permutación costó ~86 min (4 procesos en paralelo); se corrieron solo 4 de las 19 previstas en D-029 (`--nulo-max-grande`). Con B = 4 el p mínimo posible es 0.20; para llegar a 0.05 hay que completar las 19 (la caché es reanudable: volver a correr sin la opción).

## 5. Perfiles (K = 10, ordenados por % del déficit)

Ordenamiento: Σ responsabilidades × w de la clase (suma ponderada, no el MAP). Composición ponderada por responsabilidad × w; razón × = % en el perfil / % en toda la población objetivo (ponderada por w). Medianas del contexto ponderadas por responsabilidad × w (describen la sección, D-010).

| perfil | % déficit | celdas | LN 2024 (miles) | δ̃ medio | déficit crudo 2024 (+) | % crudo 2024 | prob máx media | % prob máx ≥ 0.9 |
|---|---|---|---|---|---|---|---|---|
| 1 | 16.6 | 34,712 | 6,381 | -0.656 | 701,801 | 17.4 | 0.787 | 36.6 |
| 2 | 14.0 | 58,805 | 7,496 | -0.438 | 567,208 | 14.1 | 0.804 | 40.4 |
| 3 | 13.9 | 89,115 | 12,329 | -0.254 | 357,318 | 8.9 | 0.849 | 55.0 |
| 4 | 10.9 | 35,242 | 4,695 | -0.544 | 467,020 | 11.6 | 0.772 | 31.7 |
| 5 | 10.8 | 59,902 | 5,003 | -0.467 | 414,365 | 10.3 | 0.826 | 46.1 |
| 6 | 10.4 | 66,698 | 4,177 | -0.654 | 516,442 | 12.8 | 0.886 | 66.1 |
| 7 | 9.0 | 48,553 | 3,979 | -0.522 | 313,336 | 7.8 | 0.835 | 51.9 |
| 8 | 7.1 | 55,045 | 3,226 | -0.647 | 392,828 | 9.8 | 0.932 | 79.3 |
| 9 | 4.2 | 7,954 | 1,436 | -0.756 | 193,508 | 4.8 | 0.795 | 40.6 |
| 10 | 3.1 | 16,513 | 1,947 | -0.494 | 103,463 | 2.6 | 0.880 | 64.7 |


Composición (% del déficit del perfil, razón ×):

**sexo**

| perfil | 0 | 1 |
|---|---|---|
| 1 | 44% (0.92×) | 56% (1.07×) |
| 2 | 47% (0.97×) | 53% (1.02×) |
| 3 | 47% (0.99×) | 53% (1.01×) |
| 4 | 50% (1.05×) | 50% (0.95×) |
| 5 | 48% (1.01×) | 52% (0.99×) |
| 6 | 60% (1.25×) | 40% (0.77×) |
| 7 | 40% (0.83×) | 60% (1.15×) |
| 8 | 51% (1.07×) | 49% (0.93×) |
| 9 | 46% (0.97×) | 54% (1.03×) |
| 10 | 42% (0.89×) | 58% (1.10×) |


**grupo**

| perfil | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| 1 | 6% (1.41×) | 13% (1.40×) | 18% (1.27×) | 32% (1.04×) | 27% (0.89×) | 3% (0.46×) | 1% (0.17×) |
| 2 | 5% (1.14×) | 10% (1.05×) | 14% (0.98×) | 30% (0.97×) | 30% (0.97×) | 6% (1.05×) | 5% (1.16×) |
| 3 | 2% (0.49×) | 5% (0.53×) | 12% (0.83×) | 38% (1.23×) | 35% (1.13×) | 4% (0.77×) | 3% (0.75×) |
| 4 | 5% (1.21×) | 11% (1.14×) | 16% (1.14×) | 31% (1.01×) | 28% (0.92×) | 5% (0.91×) | 3% (0.69×) |
| 5 | 2% (0.61×) | 6% (0.68×) | 12% (0.82×) | 31% (0.98×) | 36% (1.18×) | 7% (1.27×) | 5% (1.17×) |
| 6 | 3% (0.82×) | 9% (0.93×) | 12% (0.85×) | 26% (0.82×) | 32% (1.04×) | 10% (1.68×) | 9% (1.89×) |
| 7 | 2% (0.37×) | 4% (0.38×) | 9% (0.61×) | 30% (0.95×) | 41% (1.34×) | 9% (1.59×) | 6% (1.32×) |
| 8 | 7% (1.82×) | 16% (1.71×) | 17% (1.19×) | 22% (0.71×) | 19% (0.63×) | 7% (1.22×) | 11% (2.40×) |
| 9 | 7% (1.65×) | 15% (1.67×) | 21% (1.44×) | 34% (1.08×) | 23% (0.73×) | 1% (0.15×) | 0% (0.02×) |
| 10 | 3% (0.70×) | 8% (0.82×) | 17% (1.16×) | 38% (1.23×) | 28% (0.91×) | 4% (0.67×) | 3% (0.59×) |


**circunscripcion**

| perfil | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 1 | 65% (1.76×) | 29% (1.34×) | 1% (0.10×) | 0% (0.00×) | 4% (0.33×) |
| 2 | 8% (0.22×) | 0% (0.01×) | 40% (2.65×) | 37% (2.78×) | 15% (1.14×) |
| 3 | 0% (0.00×) | 11% (0.49×) | 19% (1.26×) | 37% (2.81×) | 33% (2.55×) |
| 4 | 43% (1.16×) | 41% (1.87×) | 0% (0.00×) | 2% (0.15×) | 14% (1.10×) |
| 5 | 68% (1.84×) | 31% (1.42×) | 0% (0.00×) | 0% (0.00×) | 1% (0.09×) |
| 6 | 21% (0.57×) | 43% (1.97×) | 0% (0.01×) | 7% (0.55×) | 29% (2.20×) |
| 7 | 82% (2.23×) | 14% (0.65×) | 3% (0.18×) | 1% (0.07×) | 0% (0.00×) |
| 8 | 13% (0.35×) | 2% (0.07×) | 62% (4.11×) | 19% (1.42×) | 5% (0.35×) |
| 9 | 46% (1.26×) | 36% (1.65×) | 14% (0.90×) | 0% (0.00×) | 4% (0.30×) |
| 10 | 16% (0.44×) | 9% (0.42×) | 43% (2.87×) | 16% (1.24×) | 15% (1.13×) |


**tiposec**

| perfil | M | R | U |
|---|---|---|---|
| 1 | 17% (1.30×) | 2% (0.12×) | 82% (1.12×) |
| 2 | 19% (1.51×) | 9% (0.66×) | 71% (0.98×) |
| 3 | 2% (0.15×) | 0% (0.00×) | 98% (1.34×) |
| 4 | 18% (1.40×) | 7% (0.52×) | 75% (1.02×) |
| 5 | 1% (0.09×) | 0% (0.01×) | 99% (1.35×) |
| 6 | 16% (1.22×) | 66% (4.69×) | 18% (0.25×) |
| 7 | 2% (0.14×) | 1% (0.07×) | 97% (1.33×) |
| 8 | 21% (1.65×) | 63% (4.47×) | 16% (0.22×) |
| 9 | 29% (2.28×) | 3% (0.18×) | 68% (0.93×) |
| 10 | 15% (1.17×) | 4% (0.31×) | 81% (1.10×) |


Medianas ponderadas del contexto de la sección (valores originales):

| perfil | graproes | prop_sin_escolaridad | prop_analfabeta | prop_posbasica | prop_hli | prop_afro | prop_internet | prop_celular | prop_nacida_otra_ent | prop_res_otra_ent_2015 | prop_discapacidad | prop_18a24 | prop_60ymas | razon_ln_p18 | iim_dp2 | im_2020 | imn_2020 | pctl_mov_estado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9.66 | 0.0233 | 0.0162 | 0.413 | 0.00584 | 0.00962 | 0.593 | 0.949 | 0.199 | 0.0346 | 0.0365 | 0.197 | 0.0863 | 0.995 | 64.1 | 59.4 | 0.93 | 86.1 |
| 2 | 8.94 | 0.0617 | 0.0521 | 0.382 | 0.015 | 0.0108 | 0.417 | 0.897 | 0.0868 | 0.0185 | 0.0474 | 0.179 | 0.148 | 1.07 | 64.3 | 57.1 | 0.894 | 63.7 |
| 3 | 10.2 | 0.032 | 0.024 | 0.502 | 0.0134 | 0.0133 | 0.619 | 0.909 | 0.2 | 0.024 | 0.0489 | 0.163 | 0.168 | 1.11 | 64.8 | 59.4 | 0.93 | 38.3 |
| 4 | 8.52 | 0.0503 | 0.0384 | 0.297 | 0.00324 | 0.00721 | 0.457 | 0.911 | 0.0788 | 0.0141 | 0.0442 | 0.197 | 0.129 | 1.09 | 63.8 | 59.1 | 0.925 | 75.3 |
| 5 | 9.36 | 0.0343 | 0.0235 | 0.4 | 0.00274 | 0.00688 | 0.605 | 0.909 | 0.142 | 0.0162 | 0.0544 | 0.167 | 0.198 | 1.21 | 64 | 59.4 | 0.93 | 24.7 |
| 6 | 7 | 0.0931 | 0.0868 | 0.165 | 0.000561 | 0.00352 | 0.224 | 0.828 | 0.0405 | 0.00907 | 0.0587 | 0.175 | 0.197 | 1.21 | 61.9 | 56.4 | 0.883 | 64.4 |
| 7 | 10.9 | 0.0175 | 0.0106 | 0.577 | 0.00359 | 0.011 | 0.752 | 0.945 | 0.269 | 0.0386 | 0.0408 | 0.157 | 0.173 | 1.16 | 63.7 | 59.1 | 0.926 | 41.1 |
| 8 | 6.24 | 0.153 | 0.169 | 0.152 | 0.207 | 0.00452 | 0.0874 | 0.657 | 0.0261 | 0.0136 | 0.0544 | 0.177 | 0.189 | 1.13 | 63.9 | 51.7 | 0.81 | 66.8 |
| 9 | 9.5 | 0.0195 | 0.0126 | 0.392 | 0.0183 | 0.0134 | 0.557 | 0.955 | 0.475 | 0.135 | 0.0295 | 0.201 | 0.0452 | 0.835 | 64.7 | 59.2 | 0.927 | 95.4 |
| 10 | 11.1 | 0.014 | 0.00961 | 0.612 | 0.0217 | 0.02 | 0.679 | 0.962 | 0.564 | 0.164 | 0.0295 | 0.162 | 0.0821 | 0.924 | 64.8 | 59.6 | 0.933 | 84.5 |


## 6. Tiempos

Tiempo de proceso sumado (segundos-CPU de trabajadores; con 4 procesos el reloj es ~1/4, con la máquina compartida): selección de K 1.7 h; bootstrap K=10 1.8 h; K=4 0.2 h; permutaciones K=10 5.7 h (B=4); K=4 0.9 h (B=19). Esta ejecución del script solo lee la caché de `data/interim/seleccion_numero_perfiles/` y arma el reporte.

## 7. Lectura

Tanto el ICL como el BIC siguen bajando hasta el tope del rango (K = 10): los datos no marcan un número natural de perfiles, y el K de menor ICL es el límite que se fijó de antemano, no un mínimo interior (por eso el número de perfiles se decide con las pruebas de D-029). La prueba contra el azar da una ganancia observada (660 mil nats) unas tres veces mayor que la mayor del nulo (222 mil), pero con solo 4 permutaciones el p mínimo posible es 0.20; para K = 4 sí se completó (p = 0.05, el mínimo posible). La ganancia nula es grande porque δ̃ y los componentes no son normales, así que la prueba compara contra ese piso y no contra cero. Con K = 10 la mayoría de los perfiles son estables en el bootstrap tibio (Jaccard 0.82–0.97, salvo el perfil 4 con 0.70), pero el control en frío da Jaccard bastante menores (0.40–0.80) y en tres perfiles la diferencia supera su error (D-017): la solución tibia sobrestima la estabilidad y hay muchos óptimos locales. Estos rasgos describen la sección donde se concentra cada perfil, no a las personas (D-010).
