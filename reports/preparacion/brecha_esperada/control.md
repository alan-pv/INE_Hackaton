# Brecha frente a lo esperado por sexo y edad (D-022)

## 1. Cifras de control

- Tasa del panel 2024 = Σsv/Σn = **59.670%** (control 59.67 ± 0.01): OK.
- Σ O = Σ E por sexo × grupo × elección (66 combinaciones): error relativo máximo **1.41e-16**.
- Filas del panel: 4,300,581; con n>0: 4,299,117. Celdas con alguna n>0: **983,708** (esperadas 983,708).
- Celdas con q_c en {0,1} (degeneradas): 0. Celdas con NaN en prob_bajo: 0.

## 2. Precisión φ por estrato (beta-binomial con media conocida)

φ grande = poca sobredispersión (la celda se acerca a lo esperado solo por azar binomial); φ pequeña = mucha. Convergencia: `estado` ('mle' = óptimo interior), `convergio` = reporte del optimizador.

| sexo | grupo | n_celdas | phi_total | estado | convergio | phi_0921 | estado_phi_0921 | conv_phi_0921 | phi_24 | estado_phi_24 | conv_phi_24 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 68117 | 12.66 | mle | True | nan | nan | nan | 12.66 | mle | True |
| 0 | 2 | 70614 | 13.58 | mle | True | 12.37 | mle | True | 12.5 | mle | True |
| 0 | 3 | 70674 | 18.18 | mle | True | 17.44 | mle | True | 15.57 | mle | True |
| 0 | 4 | 70680 | 22.46 | mle | True | 21.91 | mle | True | 18.83 | mle | True |
| 0 | 5 | 70681 | 22.65 | mle | True | 21.98 | mle | True | 20.22 | mle | True |
| 0 | 6 | 70659 | 23.89 | mle | True | 23.51 | mle | True | 21.63 | mle | True |
| 0 | 7 | 70408 | 26.79 | mle | True | 27 | mle | True | 20.08 | mle | True |
| 1 | 1 | 68070 | 13.83 | mle | True | nan | nan | nan | 13.83 | mle | True |
| 1 | 2 | 70594 | 14.16 | mle | True | 11.39 | mle | True | 14.48 | mle | True |
| 1 | 3 | 70672 | 17.01 | mle | True | 15.7 | mle | True | 16.89 | mle | True |
| 1 | 4 | 70680 | 19.81 | mle | True | 18.87 | mle | True | 17.79 | mle | True |
| 1 | 5 | 70680 | 21.01 | mle | True | 19.88 | mle | True | 19.32 | mle | True |
| 1 | 6 | 70661 | 22.01 | mle | True | 21.83 | mle | True | 19.52 | mle | True |
| 1 | 7 | 70518 | 24.96 | mle | True | 25.4 | mle | True | 18.41 | mle | True |

- Estratos × periodo con φ=∞ (sin sobredispersión): 0; en borde inferior: 0; sin convergencia reportada: 0.

## 3. Verificación: en celdas grandes p̃ ≈ O/N

- Decil superior de N (N ≥ 1,283; 98,485 celdas): |p̃ − O/N| máximo = **0.0079**, mediana = 0.00059.

## 4. Población objetivo (prob_bajo > 1/2)

- Celdas: **472,539** (48.0% de 983,708).
- Lista nominal 2024 en celdas objetivo: 50,669,281 (**52.4%** de 96,738,356).
- Déficit total (Σ max(déficit,0), votos por elección): **3,733,562**; neto Σ déficit: 253,589.
- Déficit crudo 2024: Σ positivo = **4,310,001**, neto = 0.

| sexo | grupo | celdas | celdas_obj | pct_celdas_obj | pct_LN_obj | delta_mediana_pond | deficit_pos |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 68117 | 31223 | 45.84 | 50.74 | -0.3162 | 7.797e+04 |
| 0 | 2 | 70614 | 32366 | 45.84 | 52.45 | -0.3391 | 1.703e+05 |
| 0 | 3 | 70674 | 33236 | 47.03 | 53.63 | -0.294 | 2.543e+05 |
| 0 | 4 | 70680 | 34725 | 49.13 | 54.58 | -0.2589 | 5.52e+05 |
| 0 | 5 | 70681 | 34590 | 48.94 | 52.25 | -0.2294 | 5.565e+05 |
| 0 | 6 | 70659 | 34648 | 49.04 | 47.78 | -0.2415 | 9.852e+04 |
| 0 | 7 | 70408 | 35587 | 50.54 | 47.7 | -0.2298 | 7.536e+04 |
| 1 | 1 | 68070 | 29456 | 43.27 | 48.78 | -0.3091 | 7.453e+04 |
| 1 | 2 | 70594 | 31861 | 45.13 | 51.35 | -0.3286 | 1.75e+05 |
| 1 | 3 | 70672 | 33836 | 47.88 | 53.87 | -0.2898 | 2.775e+05 |
| 1 | 4 | 70680 | 35175 | 49.77 | 54.61 | -0.2464 | 6.145e+05 |
| 1 | 5 | 70680 | 33779 | 47.79 | 50.73 | -0.2281 | 5.946e+05 |
| 1 | 6 | 70661 | 34841 | 49.31 | 46.59 | -0.2618 | 1.171e+05 |
| 1 | 7 | 70518 | 37216 | 52.78 | 47.72 | -0.2414 | 9.529e+04 |

## 5. Distribución de prob_bajo

| cuantil | prob_bajo |
|---|---|
| 0% | 0 |
| 10% | 1.207e-06 |
| 20% | 0.004052 |
| 30% | 0.06409 |
| 40% | 0.228 |
| 50% | 0.4495 |
| 60% | 0.6947 |
| 70% | 0.8999 |
| 80% | 0.9923 |
| 90% | 1 |
| 100% | 1 |

- (0.5, 0.6]: 40,318 celdas (4.1%)
- (0.6, 0.8]: 85,093 celdas (8.7%)
- (0.8, 0.95]: 88,212 celdas (9.0%)
- (0.95, 1]: 258,916 celdas (26.3%)

## 6. Persistencia (D-022)

- Celdas con ambos periodos: 788,460; objetivo 2009–21 entre ellas: 383,235.
- Spearman ponderada por n_2024 entre δ̃(2009–21) y δ̃(2024): **0.717**.
- Fracción (ponderada por n_2024) de la población objetivo 2009–21 con prob_bajo_24 > 1/2: **0.720**, frente a **0.478** en todas las celdas.

Lectura (descriptiva, sin umbral de decisión): el orden de la brecha se conserva (Spearman 0.72) y la población objetivo 2009–21 sigue por debajo en 2024 con frecuencia 0.72 frente a 0.48 del total de celdas.

## 7. Cómo se corre

`.venv/bin/python scripts/preparacion/brecha_esperada.py` (tiempo de ejecución: 19 s). Idempotente. Salida: `data/processed/brecha_celda.parquet`, tablas en `reports/preparacion/brecha_esperada/`.
