# Perfiles finales: cinco perfiles y regla de entrega (D-029)

Descriptivo. Los perfiles representan **votos faltantes** (pesos w = déficit), no personas; el contexto describe la sección, no a las personas (D-010).

**Nota de lectura (D-026):** `im_2020` alto = **menos** marginación; `iim_dp2` alto = **menos** intensidad migratoria; `pctl_mov_estado` alto = llegada neta de registros a la sección (bajo = salida neta), percentil dentro del estado (D-016).

## 0. Cifras de control

- [OK] celdas objetivo = 472,539 (esperadas 472,539)
- [OK] Σ pesos = 472,539.000 = nº de celdas 472,539
- [OK] logL recalculada K=5 = -4,495,183.7 coincide con la selección del número de perfiles (-4,495,183.7)
- [OK] responsabilidades suman 1 por celda
- [OK] una fila por celda objetivo, 5 perfiles
- [OK] persistencia: celdas objetivo encontradas 1:1 en brecha_celda
- [OK] perfiles_k4.parquet alineado fila a fila con K=5
- [OK] regla de D-029: K=5 es la entrega (p = 0.050, 5 perfiles claros)
- [OK] entrega: Σ celdas = 472,539 = total (472,539)
- [OK] entrega: Σ % del déficit = 100.000000
- [OK] entrega: Σ LN 2024 = 50,669 miles = total

- logL K=5 = -4,495,183.7; logL K=1 = -5,013,096.1; celdas con w=0: 162; variables continuas: ['delta', 'pc1', 'pc2', 'pc3'].
- **Elección de cómputo:** 2 procesos en vez de 4 (máquina compartida). No cambia ningún resultado (semillas por réplica, no por proceso).
- Tiempos (s, primera corrida): estabilidad K=5 2818, prueba contra el azar K=5 4462; esta ejecución 7 s.

## 1. Estabilidad (bootstrap de secciones por estado, B secuencial D-017, control en frío)

- B = 20 réplicas (mín 20, EE ≤ 0.025, tope 200); tope alcanzado: no. Control en frío: 5 réplicas; t crítico 2.78; dif. media logL tibio − frío = 325.58 nats; réplicas tibias sin convergir: 0.

| perfil | clase | jaccard_medio | ee_mc | lectura_fpc | jaccard_frio_medio | dif_tibio_menos_frio | ee_dif | frio_domina | clara |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 0.893 | 0.0152 | muy estable | 0.894 | -0.0054 | 0.0058 | no | SÍ |
| 2 | 1 | 0.941 | 0.0071 | muy estable | 0.940 | +0.0040 | 0.0039 | no | SÍ |
| 3 | 4 | 0.944 | 0.0070 | muy estable | 0.926 | +0.0060 | 0.0059 | no | SÍ |
| 4 | 2 | 0.855 | 0.0238 | muy estable | 0.861 | -0.0088 | 0.0092 | no | SÍ |
| 5 | 3 | 0.911 | 0.0130 | muy estable | 0.891 | +0.0015 | 0.0014 | no | SÍ |


## 2. Prueba contra el azar (permutación de cada variable por separado, w con su celda)

- G_obs = logL_5 − logL_1 = 517912.4 nats; G_nulo (B = 19): mín 183586.4, mediana 185547.2, máx 188066.0; permutaciones con G ≥ G_obs: **0/19**; **p = 0.050** (mínimo posible 0.050); ajustes nulos sin óptimo repetido: 0; 468 s por permutación.

## 3. Regla fijada de antemano (D-029) y veredicto

Una clase es **clara** si cumple las dos: (i) Jaccard principal ≥ 0.85 (el tibio, o el frío si la clase está regida por el frío, D-017); (ii) la solución tiene 0/19 permutaciones con G ≥ G_obs (p = 0.05). **K=5 es la entrega** si p = 0.05 y hay ≥ 4 clases claras; si no, **K=5 no cumple**. Si las 5 son claras se entregan las 5; las no claras van al 'resto'.

- Clases claras: **5** (perfiles [1, 2, 3, 4, 5]). p = 0.050.
- **Veredicto: K=5 es la entrega.**

## 4. Descripción de los 5 perfiles (ordenados por % del déficit)

Porcentajes con responsabilidad × w. Celdas y LN de la asignación dura en las columnas marcadas. Medianas ponderadas por responsabilidad × w; la tasa de homicidio (v2023, D-027) es solo descriptor, por municipio.

| perfil | pct_deficit | celdas_duras | ln_2024_miles_duro | delta_medio | pmax_media | pct_pmax_ge_09 | mediana_tasa_homicidio_100mil |
|---|---|---|---|---|---|---|---|
| 1 | 30.4 | 80,573 | 11,741 | -0.612 | 0.794 | 37.5 | 24.4 |
| 2 | 26.5 | 170,916 | 20,479 | -0.305 | 0.833 | 48.5 | 16.8 |
| 3 | 17.9 | 109,591 | 8,204 | -0.553 | 0.890 | 66.9 | 24.3 |
| 4 | 16.3 | 56,264 | 6,530 | -0.595 | 0.790 | 36.9 | 25.8 |
| 5 | 8.8 | 55,195 | 3,716 | -0.683 | 0.902 | 70.2 | 17.1 |


Composición (% del déficit del perfil, razón × frente a la población objetivo):

**sexo**

| perfil | 0 | 1 |
|---|---|---|
| 1 | 46% (0.96×) | 54% (1.04×) |
| 2 | 48% (1.00×) | 52% (1.00×) |
| 3 | 57% (1.20×) | 43% (0.82×) |
| 4 | 41% (0.86×) | 59% (1.13×) |
| 5 | 49% (1.02×) | 51% (0.98×) |


**grupo**

| perfil | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| 1 | 5% (1.26×) | 12% (1.28×) | 17% (1.19×) | 32% (1.01×) | 29% (0.93×) | 4% (0.70×) | 2% (0.40×) |
| 2 | 2% (0.56×) | 5% (0.56×) | 11% (0.80×) | 35% (1.14×) | 35% (1.13×) | 6% (1.00×) | 5% (1.09×) |
| 3 | 4% (1.05×) | 9% (1.00×) | 13% (0.90×) | 26% (0.84×) | 30% (0.99×) | 9% (1.52×) | 8% (1.81×) |
| 4 | 3% (0.84×) | 8% (0.87×) | 14% (0.99×) | 33% (1.04×) | 34% (1.10×) | 5% (0.93×) | 3% (0.56×) |
| 5 | 7% (1.62×) | 15% (1.60×) | 17% (1.19×) | 25% (0.79×) | 21% (0.70×) | 6% (1.12×) | 9% (1.94×) |


**circunscripcion**

| perfil | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 1 | 60% (1.63×) | 27% (1.24×) | 4% (0.25×) | 3% (0.23×) | 6% (0.47×) |
| 2 | 15% (0.41×) | 16% (0.73×) | 19% (1.26×) | 30% (2.28×) | 20% (1.55×) |
| 3 | 18% (0.49×) | 33% (1.53×) | 11% (0.75×) | 13% (1.01×) | 24% (1.85×) |
| 4 | 62% (1.69×) | 19% (0.87×) | 11% (0.75×) | 1% (0.10×) | 6% (0.48×) |
| 5 | 15% (0.40×) | 3% (0.16×) | 57% (3.78×) | 19% (1.43×) | 6% (0.43×) |


**tiposec**

| perfil | M | R | U |
|---|---|---|---|
| 1 | 13% (1.00×) | 2% (0.13×) | 85% (1.17×) |
| 2 | 5% (0.35×) | 0% (0.03×) | 95% (1.30×) |
| 3 | 22% (1.68×) | 48% (3.44×) | 30% (0.41×) |
| 4 | 12% (0.97×) | 1% (0.09×) | 86% (1.18×) |
| 5 | 21% (1.63×) | 51% (3.63×) | 28% (0.38×) |


Medianas ponderadas del contexto de la sección (valores originales):

| perfil | graproes | prop_sin_escolaridad | prop_analfabeta | prop_posbasica | prop_hli | prop_afro | prop_internet | prop_celular | prop_nacida_otra_ent | prop_res_otra_ent_2015 | prop_discapacidad | prop_18a24 | prop_60ymas | razon_ln_p18 | iim_dp2 | im_2020 | imn_2020 | pctl_mov_estado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9.22 | 0.0334 | 0.0235 | 0.37 | 0.00508 | 0.00873 | 0.545 | 0.932 | 0.14 | 0.0219 | 0.0407 | 0.193 | 0.113 | 1.07 | 64.1 | 59.4 | 0.93 | 72.9 |
| 2 | 9.84 | 0.0366 | 0.0273 | 0.466 | 0.0102 | 0.0113 | 0.59 | 0.907 | 0.155 | 0.0213 | 0.0497 | 0.166 | 0.172 | 1.12 | 64.6 | 59.1 | 0.925 | 38.6 |
| 3 | 7.46 | 0.0856 | 0.0771 | 0.213 | 0.00172 | 0.00449 | 0.262 | 0.849 | 0.0488 | 0.0118 | 0.0545 | 0.18 | 0.177 | 1.16 | 62.9 | 56.4 | 0.884 | 65.8 |
| 4 | 10.3 | 0.0186 | 0.0116 | 0.509 | 0.00743 | 0.0127 | 0.681 | 0.953 | 0.36 | 0.0626 | 0.0355 | 0.176 | 0.0983 | 1.05 | 64 | 59.1 | 0.926 | 70.3 |
| 5 | 6.7 | 0.127 | 0.137 | 0.189 | 0.103 | 0.00712 | 0.156 | 0.755 | 0.0393 | 0.0184 | 0.0469 | 0.176 | 0.169 | 1.12 | 64.1 | 52.9 | 0.828 | 71.2 |


### Persistencia descriptiva (la asignación usó todo el periodo 2009-2024)

'% sigue' = % de las celdas `objetivo_0921` del perfil (asignación dura, con 2024 observado) que son `objetivo_24`, ponderado por n_2024. **Aviso:** la mezcla se ajustó con el periodo completo, que incluye 2024; es descriptivo, no validación fuera de tiempo. Filas 'base' = referencia.

| grupo | celdas_objetivo_0921 | pct_sigue_objetivo_24_pond_n2024 | pct_sigue_objetivo_24_celdas |
|---|---|---|---|
| perfil 1 | 58315 | 93.238 | 89.55 |
| perfil 2 | 136215 | 63.094 | 61.808 |
| perfil 3 | 80850 | 85.489 | 83.294 |
| perfil 4 | 42146 | 84.302 | 80.952 |
| perfil 5 | 36307 | 79.043 | 76.096 |
| los 5 perfiles | 353833 | 77.189 | 75.036 |
| base: todas las celdas objetivo_0921 (universo E_24>0) | 383235 | 72.025 | 69.279 |
| base: todas las celdas con historial 2009-21 (% que son objetivo_24) | 788460 | 47.847 | 46.16 |


## 5. Comparación contra la referencia de cuatro perfiles (`perfiles_k4.parquet`)

Cruce ponderado por w: fila = perfil K=4, columna = % de su peso en cada perfil K=5 (numeración de cada ajuste por % del déficit).

| perfil_K4 | K5_perfil_1 | K5_perfil_2 | K5_perfil_3 | K5_perfil_4 | K5_perfil_5 |
|---|---|---|---|---|---|
| 1 | 15.4 | 72.8 | 0.8 | 10.9 | 0.1 |
| 2 | 70.4 | 0.4 | 0.0 | 28.9 | 0.3 |
| 3 | 10.2 | 0.2 | 89.3 | 0.0 | 0.4 |
| 4 | 0.1 | 0.3 | 2.5 | 18.5 | 78.7 |


Inverso (fila = perfil K=5, % de su peso en cada perfil K=4):

| perfil_K5 | K4_perfil_1 | K4_perfil_2 | K4_perfil_3 | K4_perfil_4 |
|---|---|---|---|---|
| 1 | 18.1 | 75.5 | 6.3 | 0.0 |
| 2 | 99.3 | 0.5 | 0.1 | 0.1 |
| 3 | 1.6 | 0.0 | 97.0 | 1.4 |
| 4 | 25.9 | 62.3 | 0.0 | 11.8 |
| 5 | 0.7 | 1.3 | 0.9 | 97.1 |


ARI ponderado (w) K=4 vs K=5: **0.5604**; sin ponderar: **0.6529**.

## 6. Entrega con cinco perfiles (D-029)

Perfiles claros numerados por % del déficit (E1, E2, ...); el resto, si lo hay, se declara con su % del déficit y LN, sin campaña propia. Archivo por celda: `data/processed/perfiles_finales.parquet` (no se publica, D-005).

| perfil_entrega | perfiles_K5 | celdas | pct_deficit | ln_2024_miles | pct_ln_objetivo | delta_medio |
|---|---|---|---|---|---|---|
| E1 | 1 | 80573 | 31.358 | 11740.815 | 23.171 | -0.617 |
| E2 | 2 | 170916 | 27.053 | 20478.537 | 40.416 | -0.297 |
| E3 | 3 | 109591 | 17.894 | 8203.966 | 16.191 | -0.552 |
| E4 | 4 | 56264 | 15.61 | 6530.134 | 12.888 | -0.606 |
| E5 | 5 | 55195 | 8.086 | 3715.829 | 7.333 | -0.696 |

