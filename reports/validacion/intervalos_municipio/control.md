# Intervalos por municipio, línea base de captura y peso de 80+ (D-032)

Construcción de órdenes idéntica a la validación con 2024 (universo D-025). Semillas: bootstrap por sección = [SEMILLA, 6] (D-027); por municipio = [SEMILLA, 8] (D-032); B = 1999, IC percentil 95%. N de procesos: 2. Tiempo total de la corrida: 7 s (los bootstraps cacheados no se vuelven a calcular; tiempos por bootstrap en la tabla 2).

## 0. Cifras de control

- [OK] logL recalculada de K=4 y K=5 (2009-21) = cachés de la referencia y de la validación con 2024
- [OK] solo celdas con historial 2009-21: AUC historial propio = 0.75909 reproduce 0.759
- [OK] solo celdas con historial 2009-21: AUC mezcla K=5 (2009-21) = 0.72003 reproduce 0.72
- [OK] solo celdas con historial 2009-21: AUC mezcla K=4 (2009-21) = 0.72971 reproduce 0.73
- [OK] solo celdas con historial 2009-21: AUC línea base = 0.67180 (esperado ≈ 0.672)
- [OK] descriptores_seccion: (edo, seccion) único
- [OK] unión celda → municipio conserva filas
- [OK] remuestreo conserva el nº de municipios por estado (2,464 municipios en 32 estados, universo con historial)
- [OK] solo celdas con historial 2009-21 · historial − K5: AUC observado = tabla de AUC (ambos bootstraps)
- [OK] solo celdas con historial 2009-21 · K5 − K4: AUC observado = tabla de AUC (ambos bootstraps)
- [OK] solo celdas con historial 2009-21 · K5 − línea base: AUC observado = tabla de AUC (ambos bootstraps)
- [OK] todas las celdas con 2024 · historial − K5: AUC observado = tabla de AUC (ambos bootstraps)
- [OK] todas las celdas con 2024 · K5 − K4: AUC observado = tabla de AUC (ambos bootstraps)
- [OK] todas las celdas con 2024 · K5 − línea base: AUC observado = tabla de AUC (ambos bootstraps)
- [OK] IC por sección historial − K5 = [0.038, 0.040], igual que en la validación con 2024
- [OK] grupo abierto (80+) en cortes_edad.json: id = [7]
- [OK] entrega K5 (472,539 celdas) unida a brecha_celda sin pérdidas
- [OK] Σ % del déficit total por perfil = 100
- [OK] Σ % del déficit sin 80+ por perfil = 100

- Celdas sin municipio en `descriptores_seccion` (se agrupan como (estado, mpio = -1)): solo celdas con historial 2009-21: 0 celdas; todas las celdas con 2024: 0 celdas.

## 1. AUC con línea base (D-032)

| universo | metodo | AUC_pos | celdas |
|---|---|---|---|
| solo celdas con historial 2009-21 | historial propio | 0.75909 | 788460 |
| solo celdas con historial 2009-21 | mezcla K=5 (2009-21) | 0.72003 | 788460 |
| solo celdas con historial 2009-21 | mezcla K=4 (2009-21) | 0.72971 | 788460 |
| solo celdas con historial 2009-21 | línea base objetivo_0921 sí/no | 0.6718 | 788460 |
| todas las celdas con 2024 | historial propio | 0.69198 | 958098 |
| todas las celdas con 2024 | mezcla K=5 (2009-21) | 0.6814 | 958098 |
| todas las celdas con 2024 | mezcla K=4 (2009-21) | 0.68917 | 958098 |
| todas las celdas con 2024 | línea base objetivo_0921 sí/no | 0.64264 | 958098 |

## 2. ΔAUC_pos con IC por sección y por municipio (D-032)

ΔAUC = método 1 − método 2; el IC por municipio es el principal (conservador). `ancho_mpio_sobre_secc` = cociente de anchos.

| universo | comparacion | AUC_1 | AUC_2 | delta_AUC | IC95_secc_inf | IC95_secc_sup | IC95_mpio_inf | IC95_mpio_sup | excluye_0_mpio | ancho_mpio_sobre_secc | n_municipios | B | seg_mpio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| solo celdas con historial 2009-21 | historial − K5 | 0.75909 | 0.72003 | 0.03906 | 0.03784 | 0.04026 | 0.03398 | 0.04415 | True | 4.19956 | 2464 | 1999 | 143.91186 |
| solo celdas con historial 2009-21 | K5 − K4 | 0.72003 | 0.72971 | -0.00968 | -0.01059 | -0.00877 | -0.01301 | -0.00636 | True | 3.64919 | 2464 | 1999 | 54.31485 |
| solo celdas con historial 2009-21 | K5 − línea base | 0.72003 | 0.6718 | 0.04823 | 0.04691 | 0.04957 | 0.03985 | 0.05742 | True | 6.60582 | 2464 | 1999 | 58.01569 |
| todas las celdas con 2024 | historial − K5 | 0.69198 | 0.6814 | 0.01058 | 0.00923 | 0.01201 | 0.00626 | 0.01553 | True | 3.34033 | 2465 | 1999 | 222.21789 |
| todas las celdas con 2024 | K5 − K4 | 0.6814 | 0.68917 | -0.00778 | -0.00847 | -0.00703 | -0.01065 | -0.00515 | True | 3.80766 | 2465 | 1999 | 117.73559 |
| todas las celdas con 2024 | K5 − línea base | 0.6814 | 0.64264 | 0.03876 | 0.03769 | 0.03987 | 0.03206 | 0.04556 | True | 6.18582 | 2465 | 1999 | 109.53663 |

## 3. Municipios por estado en el universo de remuestreo

| edo | solo celdas con historial 2009-21 | todas las celdas con 2024 | solo celdas con historial 2009-21_secciones | todas las celdas con 2024_secciones |
|---|---|---|---|---|
| 1 | 11 | 11 | 609 | 661 |
| 2 | 7 | 7 | 1935 | 2048 |
| 3 | 5 | 5 | 461 | 509 |
| 4 | 13 | 13 | 492 | 510 |
| 5 | 38 | 38 | 1525 | 1619 |
| 6 | 10 | 10 | 360 | 388 |
| 7 | 121 | 122 | 1944 | 2164 |
| 8 | 67 | 67 | 2871 | 2939 |
| 9 | 16 | 16 | 5495 | 5559 |
| 10 | 39 | 39 | 1333 | 1355 |
| 11 | 46 | 46 | 3111 | 3210 |
| 12 | 85 | 85 | 2585 | 2628 |
| 13 | 84 | 84 | 1701 | 1783 |
| 14 | 125 | 125 | 3518 | 3745 |
| 15 | 125 | 125 | 6389 | 6672 |
| 16 | 112 | 112 | 2584 | 2640 |
| 17 | 36 | 36 | 886 | 932 |
| 18 | 20 | 20 | 930 | 963 |
| 19 | 50 | 50 | 2693 | 2834 |
| 20 | 566 | 566 | 2372 | 2463 |
| 21 | 217 | 217 | 2586 | 2784 |
| 22 | 18 | 18 | 869 | 950 |
| 23 | 11 | 11 | 1015 | 1073 |
| 24 | 58 | 58 | 1701 | 1762 |
| 25 | 20 | 20 | 3374 | 3461 |
| 26 | 68 | 68 | 1417 | 1473 |
| 27 | 17 | 17 | 1113 | 1165 |
| 28 | 43 | 43 | 1929 | 2029 |
| 29 | 60 | 60 | 585 | 613 |
| 30 | 212 | 212 | 4774 | 4859 |
| 31 | 106 | 106 | 1079 | 1137 |
| 32 | 58 | 58 | 1681 | 1723 |

## 4. Peso de 80+ (grupo 7) por perfil de la entrega K=5 (D-032)

LN en personas; déficit = Σ max(déficit, 0) por celda; `pct_deficit_total_sin_80` = participación de cada perfil en el déficit positivo total tras excluir las celdas de 80+. Descriptivo, no cambia la entrega.

| perfil | celdas | ln_2024 | pct_LN_en_80mas | deficit_pos | pct_deficit_en_80mas | pct_deficit_total_con_80 | pct_deficit_total_sin_80 |
|---|---|---|---|---|---|---|---|
| P1 · E1 | 80573 | 11740815.0 | 0.96 | 1170770.84 | 1.76 | 31.36 | 32.28 |
| P2 · E2 | 170916 | 20478537.0 | 2.58 | 1010024.92 | 5.14 | 27.05 | 26.89 |
| P3 · E3 | 109591 | 8203966.0 | 4.52 | 668073.55 | 8.48 | 17.89 | 17.16 |
| P4 · E4 | 56264 | 6530134.0 | 1.37 | 582793.14 | 2.48 | 15.61 | 15.95 |
| P5 · E5 | 55195 | 3715829.0 | 4.9 | 301877.34 | 8.95 | 8.09 | 7.71 |
| población objetivo completa | 472539 | 50669281.0 | 2.53 | 3733539.8 | 4.57 | 100.0 | 100.0 |
