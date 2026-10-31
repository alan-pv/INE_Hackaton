# Sensibilidad a la gubernatura concurrente (D-030) y a los votos no especificados (D-031)

Escenarios: `concurrencia` (q_gsek, D-030), `ns_voto` (votos = SV+NS, n = SV+NV+NS, D-031) y `ns_abst` (votos = SV, n = SV+NV+NS, D-031). `principal` es la misma cadena recalculada con este código (control). Reajuste tibio de K=5 desde `ajuste_K5.pkl`, tolerancia 1e-10, tope 3000 it (D-021), con la misma PCA (r = 3). Participación = SV/(SV+NV) (D-001) salvo en las cotas de D-031.

## 0. Cifras de control y verificaciones

- [OK] entrega K=5: 472,539 celdas, llave única
- [OK] participación 2024 nacional = 59.67% (control 59.67%, tol 0.01)
- [OK] participación 2024 mujeres = 64.20% (control 64.2%, tol 0.05)
- [OK] participación 2024 hombres = 54.76% (control 54.8%, tol 0.05)
- [info] participación 2021 nacional en el panel (cohortes de 2024, D-006) = 52.22% (cifra oficial 51.84%, no aplica al panel)
- [info] participación 2021 mujeres en el panel (cohortes de 2024, D-006) = 56.03% (cifra oficial 55.62%, no aplica al panel)
- [info] participación 2021 hombres en el panel (cohortes de 2024, D-006) = 48.12% (cifra oficial 47.76%, no aplica al panel)
- [info] participación 2009 nacional en el panel (cohortes de 2024, D-006) = 44.36% (cifra oficial 44.06%, no aplica al panel)
- [info] participación 2009 mujeres en el panel (cohortes de 2024, D-006) = 47.67% (cifra oficial 47.35%, no aplica al panel)
- [info] participación 2009 hombres en el panel (cohortes de 2024, D-006) = 40.81% (cifra oficial 40.53%, no aplica al panel)
- [OK] principal: Σ O = Σ E por sexo×grupo×elección; error relativo máx. 1.41e-16
- [OK] principal reproducida: 472,539 celdas objetivo (control 472,539)
- [OK] principal reproducida: 3,733,540 votos faltantes por elección (control 3.73 M)
- [OK] principal: mismas 983,708 celdas que brecha_celda.parquet
- [OK] principal: la población objetivo coincide celda a celda con brecha_celda.parquet
- [OK] principal: δ̃ = brecha_celda (máx |Δ| = 1.2e-07; float32)
- [OK] LN 2024 de la base = brecha_celda.ln_2024
- [OK] concurrencia: Σ O = Σ E por sexo×grupo×elección×k; error relativo máx. 1.83e-16
- [OK] ns_voto: Σ O = Σ E por sexo×grupo×elección; error relativo máx. 1.48e-16
- [OK] ns_abst: Σ O = Σ E por sexo×grupo×elección; error relativo máx. 1.30e-16
- [OK] principal: la entrega tiene déficit principal en las 472,539 celdas
- [OK] concurrencia: la entrega tiene déficit principal en las 472,539 celdas
- [OK] ns_voto: la entrega tiene déficit principal en las 472,539 celdas
- [OK] ns_abst: la entrega tiene déficit principal en las 472,539 celdas
- [OK] principal: ARI de ajuste_K5 sobre los datos recalculados vs entrega = 1.00000 (> 0.999)
- [OK] tabla perfil × elección: 30 filas = 5 perfiles × 6 elecciones

## 1. Población objetivo y votos faltantes (por elección)

frac_ln_sigue = fracción de la LN 2024 del objetivo principal que sigue en el objetivo del escenario; jaccard_ln = Jaccard ponderado por LN 2024.

| escenario | celdas_principal | celdas_escenario | celdas_interseccion | celdas_union | ln_principal | ln_escenario | frac_ln_sigue | jaccard_ln | votos_faltantes_M | votos_faltantes_principal_M |
|---|---|---|---|---|---|---|---|---|---|---|
| principal | 472539 | 472539 | 472539 | 472539 | 50671843.0 | 50671843.0 | 1.0 | 1.0 | 3.7335 | 3.7335 |
| concurrencia | 472539 | 471026 | 453180 | 490385 | 50671843.0 | 50731680.0 | 0.9596 | 0.9213 | 3.6885 | 3.7335 |
| ns_voto | 472539 | 480697 | 439714 | 513522 | 50671843.0 | 50318692.0 | 0.9145 | 0.8479 | 3.8508 | 3.7335 |
| ns_abst | 472539 | 460311 | 424088 | 508762 | 50671843.0 | 49992222.0 | 0.9034 | 0.834 | 4.056 | 3.7335 |

## 2. Spearman ponderada (peso n_2024 principal) de δ̃ escenario vs principal

| escenario | spearman_delta | celdas |
|---|---|---|
| principal | 1.0 | 958098 |
| concurrencia | 0.9917 | 958098 |
| ns_voto | 0.9583 | 958098 |
| ns_abst | 0.9568 | 958098 |

## 3. Reajuste tibio K=5: ARI ponderado contra la entrega K=5 (pesos w de la entrega, celdas comunes)

ARI_sin_reajustar = ajuste_K5 aplicado sin reajustar a los datos del escenario (piso de lo que mueven solo los datos); la diferencia con ARI_ponderado es lo que mueve el reajuste.

| escenario | celdas_escenario | celdas_comunes | ARI_ponderado | ARI_sin_reajustar | regla_global | regla_global_pesos_escenario | iteraciones | convergio | logL_inicial | logL | seg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| principal | 472539 | 472539 | 1.0 | 1.0 | SÍ | SÍ | 1 | True | -4495183.7366 | -4495183.7362 | 3.0791 |
| concurrencia | 471026 | 453180 | 0.8711 | 0.9375 | SÍ | SÍ | 121 | True | -4466056.7208 | -4463337.5862 | 63.9268 |
| ns_voto | 480697 | 439714 | 0.8336 | 0.9001 | SÍ | SÍ | 115 | True | -4594137.3672 | -4592215.1272 | 62.4019 |
| ns_abst | 460311 | 424088 | 0.5703 | 0.8954 | SÍ | SÍ | 158 | True | -4476368.5083 | -4452154.7113 | 81.911 |

### Cruce de pesos · principal (% del peso w de la entrega de cada clase del escenario, por perfil principal)

| clase del escenario | P1 | P2 | P3 | P4 | P5 | peso_% | cuota_máx_% | ¿>½ en un perfil? |
|---|---|---|---|---|---|---|---|---|
| clase 0 (→ P1) | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 31.4 | 100.0 | SÍ |
| clase 1 (→ P2) | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 27.1 | 100.0 | SÍ |
| clase 4 (→ P3) | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 17.9 | 100.0 | SÍ |
| clase 2 (→ P4) | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 15.6 | 100.0 | SÍ |
| clase 3 (→ P5) | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 8.1 | 100.0 | SÍ |

**Regla D-030 (principal): SÍ — cada clase tiene más de la mitad de su peso en un solo perfil principal.** (Con los pesos w del propio escenario: SÍ.)

### Cruce de pesos · concurrencia (% del peso w de la entrega de cada clase del escenario, por perfil principal)

| clase del escenario | P1 | P2 | P3 | P4 | P5 | peso_% | cuota_máx_% | ¿>½ en un perfil? |
|---|---|---|---|---|---|---|---|---|
| clase 0 (→ P1) | 96.2 | 1.9 | 0.9 | 1.0 | 0.0 | 31.0 | 96.2 | SÍ |
| clase 1 (→ P2) | 5.3 | 89.4 | 0.5 | 4.7 | 0.0 | 29.2 | 89.4 | SÍ |
| clase 4 (→ P3) | 0.1 | 0.5 | 98.6 | 0.0 | 0.7 | 17.7 | 98.6 | SÍ |
| clase 2 (→ P4) | 0.1 | 1.0 | 0.0 | 97.8 | 1.0 | 14.2 | 97.8 | SÍ |
| clase 3 (→ P5) | 0.0 | 0.4 | 0.5 | 0.1 | 99.0 | 7.9 | 99.0 | SÍ |

**Regla D-030 (concurrencia): SÍ — cada clase tiene más de la mitad de su peso en un solo perfil principal.** (Con los pesos w del propio escenario: SÍ.)

### Cruce de pesos · ns_voto (% del peso w de la entrega de cada clase del escenario, por perfil principal)

| clase del escenario | P1 | P2 | P3 | P4 | P5 | peso_% | cuota_máx_% | ¿>½ en un perfil? |
|---|---|---|---|---|---|---|---|---|
| clase 0 (→ P1) | 89.9 | 8.4 | 1.6 | 0.1 | 0.0 | 34.1 | 89.9 | SÍ |
| clase 1 (→ P2) | 1.7 | 96.1 | 0.5 | 1.6 | 0.1 | 23.7 | 96.1 | SÍ |
| clase 4 (→ P3) | 0.2 | 1.1 | 97.1 | 0.0 | 1.7 | 17.9 | 97.1 | SÍ |
| clase 2 (→ P4) | 2.8 | 4.4 | 0.0 | 92.6 | 0.2 | 16.4 | 92.6 | SÍ |
| clase 3 (→ P5) | 0.1 | 0.7 | 0.5 | 1.8 | 96.9 | 8.0 | 96.9 | SÍ |

**Regla D-030 (ns_voto): SÍ — cada clase tiene más de la mitad de su peso en un solo perfil principal.** (Con los pesos w del propio escenario: SÍ.)

### Cruce de pesos · ns_abst (% del peso w de la entrega de cada clase del escenario, por perfil principal)

| clase del escenario | P1 | P2 | P3 | P4 | P5 | peso_% | cuota_máx_% | ¿>½ en un perfil? |
|---|---|---|---|---|---|---|---|---|
| clase 0 (→ P1) | 90.7 | 1.4 | 0.4 | 7.4 | 0.2 | 24.4 | 90.7 | SÍ |
| clase 1 (→ P2) | 22.4 | 66.8 | 0.5 | 10.2 | 0.1 | 37.6 | 66.8 | SÍ |
| clase 4 (→ P3) | 5.4 | 3.9 | 88.4 | 0.0 | 2.3 | 19.7 | 88.4 | SÍ |
| clase 2 (→ P4) | 0.2 | 3.4 | 0.0 | 89.2 | 7.2 | 11.2 | 89.2 | SÍ |
| clase 3 (→ P5) | 0.0 | 0.5 | 3.6 | 0.2 | 95.6 | 7.1 | 95.6 | SÍ |

**Regla D-030 (ns_abst): SÍ — cada clase tiene más de la mitad de su peso en un solo perfil principal.** (Con los pesos w del propio escenario: SÍ.)

## 4. Regla de mayoría por clase (D-030)

| escenario | clase | perfil_dominante | cuota_pct | cumple | cuota_pct_pesos_escenario |
|---|---|---|---|---|---|
| principal | clase 0 (→ P1) | P1 | 100.0 | SÍ | 100.0 |
| principal | clase 1 (→ P2) | P2 | 100.0 | SÍ | 100.0 |
| principal | clase 4 (→ P3) | P3 | 100.0 | SÍ | 100.0 |
| principal | clase 2 (→ P4) | P4 | 100.0 | SÍ | 100.0 |
| principal | clase 3 (→ P5) | P5 | 100.0 | SÍ | 100.0 |
| concurrencia | clase 0 (→ P1) | P1 | 96.19 | SÍ | 95.86 |
| concurrencia | clase 1 (→ P2) | P2 | 89.43 | SÍ | 90.35 |
| concurrencia | clase 4 (→ P3) | P3 | 98.58 | SÍ | 98.6 |
| concurrencia | clase 2 (→ P4) | P4 | 97.8 | SÍ | 97.76 |
| concurrencia | clase 3 (→ P5) | P5 | 99.05 | SÍ | 99.04 |
| ns_voto | clase 0 (→ P1) | P1 | 89.88 | SÍ | 88.76 |
| ns_voto | clase 1 (→ P2) | P2 | 96.12 | SÍ | 97.54 |
| ns_voto | clase 4 (→ P3) | P3 | 97.07 | SÍ | 97.17 |
| ns_voto | clase 2 (→ P4) | P4 | 92.63 | SÍ | 92.43 |
| ns_voto | clase 3 (→ P5) | P5 | 96.93 | SÍ | 97.12 |
| ns_abst | clase 0 (→ P1) | P1 | 90.67 | SÍ | 88.19 |
| ns_abst | clase 1 (→ P2) | P2 | 66.8 | SÍ | 67.86 |
| ns_abst | clase 4 (→ P3) | P3 | 88.41 | SÍ | 87.88 |
| ns_abst | clase 2 (→ P4) | P4 | 89.21 | SÍ | 88.61 |
| ns_abst | clase 3 (→ P5) | P5 | 95.65 | SÍ | 93.01 |

## 5. % del déficit por perfil (escenario vs principal; déficit positivo D-022)


**principal**

| perfil | pct_deficit_principal | pct_deficit_escenario | dif_pts |
|---|---|---|---|
| P1 | 31.358 | 31.358 | 0.0 |
| P2 | 27.053 | 27.053 | -0.0 |
| P3 | 17.894 | 17.894 | 0.0 |
| P4 | 15.61 | 15.61 | 0.0 |
| P5 | 8.086 | 8.086 | 0.0 |

**concurrencia**

| perfil | pct_deficit_principal | pct_deficit_escenario | dif_pts |
|---|---|---|---|
| P1 | 31.358 | 31.017 | -0.341 |
| P2 | 27.053 | 29.818 | 2.766 |
| P3 | 17.894 | 18.031 | 0.137 |
| P4 | 15.61 | 13.386 | -2.224 |
| P5 | 8.086 | 7.749 | -0.337 |

**ns_voto**

| perfil | pct_deficit_principal | pct_deficit_escenario | dif_pts |
|---|---|---|---|
| P1 | 31.358 | 32.827 | 1.469 |
| P2 | 27.053 | 25.01 | -2.043 |
| P3 | 17.894 | 17.885 | -0.009 |
| P4 | 15.61 | 16.082 | 0.472 |
| P5 | 8.086 | 8.197 | 0.111 |

**ns_abst**

| perfil | pct_deficit_principal | pct_deficit_escenario | dif_pts |
|---|---|---|---|
| P1 | 31.358 | 26.05 | -5.308 |
| P2 | 27.053 | 35.95 | 8.898 |
| P3 | 17.894 | 19.156 | 1.262 |
| P4 | 15.61 | 11.5 | -4.109 |
| P5 | 8.086 | 7.344 | -0.742 |

## 6. Observado vs esperado por perfil y elección (asignación principal; esperada principal q_gse vs con concurrencia q_gsek)

Puntos de participación SV/(SV+NV), agregando las celdas del perfil en cada elección. efecto_calendario = esp_principal − esp_concurrencia.

| perfil | aelec | obs | esp_principal | esp_concurrencia | dif_principal | dif_concurrencia | efecto_calendario |
|---|---|---|---|---|---|---|---|
| 1 | 2009 | 36.747 | 43.301 | 43.838 | -6.554 | -7.091 | -0.537 |
| 1 | 2012 | 52.08 | 61.651 | 61.524 | -9.571 | -9.444 | 0.126 |
| 1 | 2015 | 35.411 | 46.165 | 46.33 | -10.755 | -10.919 | -0.165 |
| 1 | 2018 | 48.516 | 61.91 | 61.495 | -13.395 | -12.98 | 0.415 |
| 1 | 2021 | 36.959 | 50.861 | 50.39 | -13.901 | -13.43 | 0.471 |
| 1 | 2024 | 46.52 | 58.217 | 57.851 | -11.697 | -11.331 | 0.366 |
| 2 | 2009 | 37.718 | 43.823 | 43.639 | -6.105 | -5.92 | 0.185 |
| 2 | 2012 | 58.185 | 62.059 | 62.065 | -3.873 | -3.88 | -0.007 |
| 2 | 2015 | 40.034 | 47.3 | 47.09 | -7.265 | -7.056 | 0.21 |
| 2 | 2018 | 60.008 | 62.964 | 63.088 | -2.955 | -3.08 | -0.125 |
| 2 | 2021 | 46.047 | 52.688 | 52.828 | -6.642 | -6.782 | -0.14 |
| 2 | 2024 | 57.695 | 60.682 | 60.832 | -2.986 | -3.137 | -0.15 |
| 3 | 2009 | 37.081 | 44.654 | 43.962 | -7.572 | -6.881 | 0.691 |
| 3 | 2012 | 53.073 | 62.083 | 62.127 | -9.01 | -9.053 | -0.044 |
| 3 | 2015 | 42.739 | 47.424 | 48.209 | -4.686 | -5.471 | -0.785 |
| 3 | 2018 | 52.153 | 62.098 | 62.165 | -9.944 | -10.011 | -0.067 |
| 3 | 2021 | 42.669 | 51.746 | 51.508 | -9.076 | -8.839 | 0.237 |
| 3 | 2024 | 48.245 | 58.888 | 59.015 | -10.643 | -10.771 | -0.127 |
| 4 | 2009 | 33.624 | 44.447 | 44.25 | -10.822 | -10.625 | 0.197 |
| 4 | 2012 | 54.441 | 62.792 | 61.832 | -8.351 | -7.39 | 0.961 |
| 4 | 2015 | 34.99 | 47.701 | 47.518 | -12.711 | -12.527 | 0.183 |
| 4 | 2018 | 53.982 | 63.226 | 62.106 | -9.244 | -8.124 | 1.12 |
| 4 | 2021 | 41.059 | 52.35 | 51.509 | -11.291 | -10.451 | 0.841 |
| 4 | 2024 | 50.731 | 59.933 | 58.862 | -9.202 | -8.131 | 1.071 |
| 5 | 2009 | 33.967 | 45.437 | 44.462 | -11.471 | -10.495 | 0.976 |
| 5 | 2012 | 53.577 | 62.453 | 61.874 | -8.876 | -8.297 | 0.579 |
| 5 | 2015 | 38.239 | 47.225 | 46.908 | -8.986 | -8.669 | 0.317 |
| 5 | 2018 | 54.132 | 61.441 | 61.17 | -7.308 | -7.037 | 0.271 |
| 5 | 2021 | 44.054 | 50.424 | 50.578 | -6.369 | -6.524 | -0.155 |
| 5 | 2024 | 46.46 | 57.119 | 56.897 | -10.659 | -10.437 | 0.222 |

## 7. Intermedias (2009, 2015, 2021) menos presidenciales (2012, 2018, 2024), puntos

Media de (observada − esperada) en cada grupo de elecciones. `calendario_pts` = diferencia del patrón explicada al pasar de q_gse a q_gsek; `calendario_pct` su porcentaje del patrón principal.

| perfil | inter_principal | pres_principal | inter_menos_pres_principal | inter_concurrencia | pres_concurrencia | inter_menos_pres_concurrencia | calendario_pts | calendario_pct |
|---|---|---|---|---|---|---|---|---|
| 1 | -10.403 | -11.554 | 1.151 | -10.48 | -11.251 | 0.771 | 0.379 | 32.977 |
| 2 | -6.671 | -3.272 | -3.399 | -6.586 | -3.366 | -3.22 | -0.179 | 5.254 |
| 3 | -7.112 | -9.866 | 2.754 | -7.064 | -9.945 | 2.882 | -0.127 | -4.624 |
| 4 | -11.608 | -8.932 | -2.676 | -11.201 | -7.882 | -3.32 | 0.644 | -24.051 |
| 5 | -8.942 | -8.948 | 0.006 | -8.563 | -8.59 | 0.028 | -0.022 | -373.092 |

## 8. Brecha por escenario: φ por estrato y metadatos


**principal**: filas panel 4,300,581; con n>0 4,299,117; celdas 983,708; objetivo 472,539; votos faltantes 3,733,540; error de conservación 1.41e-16.

| sexo | grupo | phi | estado | n_celdas |
|---|---|---|---|---|
| 0 | 1 | 12.658 | mle | 68117 |
| 0 | 2 | 13.576 | mle | 70614 |
| 0 | 3 | 18.175 | mle | 70674 |
| 0 | 4 | 22.455 | mle | 70680 |
| 0 | 5 | 22.65 | mle | 70681 |
| 0 | 6 | 23.89 | mle | 70659 |
| 0 | 7 | 26.787 | mle | 70408 |
| 1 | 1 | 13.828 | mle | 68070 |
| 1 | 2 | 14.165 | mle | 70594 |
| 1 | 3 | 17.011 | mle | 70672 |
| 1 | 4 | 19.813 | mle | 70680 |
| 1 | 5 | 21.013 | mle | 70680 |
| 1 | 6 | 22.011 | mle | 70661 |
| 1 | 7 | 24.958 | mle | 70518 |

**concurrencia**: filas panel 4,300,581; con n>0 4,299,117; celdas 983,708; objetivo 471,026; votos faltantes 3,688,512; error de conservación 1.83e-16; filas con gubernatura = 1,284,469.

| sexo | grupo | phi | estado | n_celdas |
|---|---|---|---|---|
| 0 | 1 | 12.903 | mle | 68117 |
| 0 | 2 | 13.877 | mle | 70614 |
| 0 | 3 | 18.623 | mle | 70674 |
| 0 | 4 | 23.347 | mle | 70680 |
| 0 | 5 | 23.464 | mle | 70681 |
| 0 | 6 | 24.557 | mle | 70659 |
| 0 | 7 | 27.349 | mle | 70408 |
| 1 | 1 | 14.213 | mle | 68070 |
| 1 | 2 | 14.567 | mle | 70594 |
| 1 | 3 | 17.484 | mle | 70672 |
| 1 | 4 | 20.542 | mle | 70680 |
| 1 | 5 | 21.811 | mle | 70680 |
| 1 | 6 | 22.885 | mle | 70661 |
| 1 | 7 | 25.732 | mle | 70518 |

**ns_voto**: filas panel 4,300,581; con n>0 4,300,581; celdas 983,783; objetivo 480,697; votos faltantes 3,850,840; error de conservación 1.48e-16.

| sexo | grupo | phi | estado | n_celdas |
|---|---|---|---|---|
| 0 | 1 | 11.15 | mle | 68132 |
| 0 | 2 | 12.965 | mle | 70615 |
| 0 | 3 | 17.678 | mle | 70674 |
| 0 | 4 | 22.188 | mle | 70680 |
| 0 | 5 | 22.929 | mle | 70681 |
| 0 | 6 | 24.46 | mle | 70659 |
| 0 | 7 | 27.185 | mle | 70435 |
| 1 | 1 | 12.586 | mle | 68085 |
| 1 | 2 | 13.96 | mle | 70596 |
| 1 | 3 | 17.115 | mle | 70672 |
| 1 | 4 | 20.103 | mle | 70680 |
| 1 | 5 | 21.5 | mle | 70680 |
| 1 | 6 | 22.659 | mle | 70662 |
| 1 | 7 | 25.227 | mle | 70532 |

**ns_abst**: filas panel 4,300,581; con n>0 4,300,581; celdas 983,783; objetivo 460,311; votos faltantes 4,055,964; error de conservación 1.30e-16.

| sexo | grupo | phi | estado | n_celdas |
|---|---|---|---|---|
| 0 | 1 | 9.85 | mle | 68132 |
| 0 | 2 | 12.759 | mle | 70615 |
| 0 | 3 | 17.677 | mle | 70674 |
| 0 | 4 | 21.845 | mle | 70680 |
| 0 | 5 | 21.234 | mle | 70681 |
| 0 | 6 | 21.987 | mle | 70659 |
| 0 | 7 | 25.556 | mle | 70435 |
| 1 | 1 | 9.858 | mle | 68085 |
| 1 | 2 | 12.821 | mle | 70596 |
| 1 | 3 | 16.311 | mle | 70672 |
| 1 | 4 | 19.004 | mle | 70680 |
| 1 | 5 | 19.425 | mle | 70680 |
| 1 | 6 | 20.385 | mle | 70662 |
| 1 | 7 | 24.271 | mle | 70532 |

## 9. Tiempos de cómputo (s, primera corrida)

| paso | segundos |
|---|---|

Tiempo total de esta corrida: 9 s.
