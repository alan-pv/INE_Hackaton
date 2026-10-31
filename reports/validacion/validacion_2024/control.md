# Validación con 2024: cinco perfiles reajustados con 2009-21 (D-025, D-029)

Mezcla K=5 reajustada con 2009-21 (objetivo_0921, δ̃ = delta_0921, w = déficit 2009-21; misma construcción que la referencia de cuatro perfiles), ordenada contra el déficit crudo 2024. Descriptivo; el ΔAUC mide la variabilidad del conjunto de evaluación (D-027).

## 0. Cifras de control

- [OK] población objetivo 2009-21 = 396,632 celdas
- [OK] Σ pesos = 396,632.0 = nº de celdas 396,632
- [OK] K=4 2009-21: logL recalculada -3,748,229.8 = caché de la referencia (-3,748,229.8): mismos datos
- [OK] K=5 2009-21: logL recalculada -3,706,509.4 = ajuste (-3,706,509.4)
- [OK] historial propio: AUC 0.75909 (con historial, control 0.75909) y 0.69198 (todas, control 0.69199)
- [OK] solo celdas con historial 2009-21: AUC mezcla K=4 0.72971 reproduce la referencia (0.72971)
- [OK] todas las celdas con 2024: AUC mezcla K=4 0.68917 reproduce la referencia (0.68917)
- [OK] solo celdas con historial 2009-21 · (a) historial propio − K5: AUC observado = tabla de AUC
- [OK] solo celdas con historial 2009-21 · (b) K5 − K4: AUC observado = tabla de AUC
- [OK] todas las celdas con 2024 · (a) historial propio − K5: AUC observado = tabla de AUC
- [OK] todas las celdas con 2024 · (b) K5 − K4: AUC observado = tabla de AUC
- [OK] persistencia: Σ celdas de los 5 perfiles = objetivo_0921 (396,632)

- Ajuste K=5 2009-21: logL = -3,706,509.4; reinicios 5, óptimo repetido 2 veces (repetido=True), no convergieron 0, pisos 0; semilla [0, 2, 5]; celdas con w=0: 200.
- Razón ΣO/ΣE 2009-21 por perfil (r̂): P1: 0.8045, P2: 0.9083, P3: 0.8446, P4: 0.7867, P5: 0.8389; no objetivo con historial: 1.1521.

## 1. AUC de la curva de captura (D-025)

| universo | metodo | AUC_pos | celdas |
|---|---|---|---|
| solo celdas con historial 2009-21 | historial propio | 0.75909 | 788460 |
| solo celdas con historial 2009-21 | mezcla K=5 (2009-21) | 0.72003 | 788460 |
| solo celdas con historial 2009-21 | mezcla K=4 (2009-21) | 0.72971 | 788460 |
| todas las celdas con 2024 | historial propio | 0.69198 | 958098 |
| todas las celdas con 2024 | mezcla K=5 (2009-21) | 0.6814 | 958098 |
| todas las celdas con 2024 | mezcla K=4 (2009-21) | 0.68917 | 958098 |

## 2. ΔAUC_pos con bootstrap pareado de secciones por estado (B = 1999, IC 95%)

| universo | comparacion | AUC_1 | AUC_2 | delta_AUC | IC95_inf | IC95_sup | excluye_0 | B | seg | media_replicas |
|---|---|---|---|---|---|---|---|---|---|---|
| solo celdas con historial 2009-21 | (a) historial propio − K5 | 0.75909 | 0.72003 | 0.03906 | 0.03784 | 0.04026 | True | 1999 | 236.31254 | 0.03905 |
| solo celdas con historial 2009-21 | (b) K5 − K4 | 0.72003 | 0.72971 | -0.00968 | -0.01059 | -0.00877 | True | 1999 | 146.26006 | -0.00968 |
| todas las celdas con 2024 | (a) historial propio − K5 | 0.69198 | 0.6814 | 0.01058 | 0.00923 | 0.01201 | True | 1999 | 246.25224 | 0.01059 |
| todas las celdas con 2024 | (b) K5 − K4 | 0.6814 | 0.68917 | -0.00778 | -0.00847 | -0.00703 | True | 1999 | 167.0459 | -0.00777 |

## 3. K=5 reajustado con 2009-21 frente al K=5 completo

- ARI ponderado (w del K=5 completo) en 367,230 celdas comunes (de 396,632): **0.769** (K=4: 0.813).

Cruce (columnas = perfil del K=5 completo; % de su peso w en cada clase 2009-21):

| clase 2009-21 | perfil_completo_1 | perfil_completo_2 | perfil_completo_3 | perfil_completo_4 | perfil_completo_5 |
|---|---|---|---|---|---|
| clase 2009-21 → perfil 2 | 0.3 | 84.4 | 0.2 | 3.4 | 0.2 |
| clase 2009-21 → perfil 4 | 7.7 | 3.8 | 0.0 | 91.4 | 0.2 |
| clase 2009-21 → perfil 5 | 0.1 | 0.3 | 0.5 | 5.1 | 96.2 |
| clase 2009-21 → perfil 3 | 0.0 | 0.9 | 94.5 | 0.0 | 3.4 |
| clase 2009-21 → perfil 1 | 91.8 | 10.6 | 4.8 | 0.0 | 0.0 |

## 4. Persistencia por perfil (mezcla K=5 de 2009-21 → 2024)

Razones O/E agrupadas ΣO/ΣE; '% sigue bajo' = objetivo_24 entre celdas con 2024, ponderado por n_2024; base = todas las celdas con historial.

| perfil | celdas | ln_2024_miles | razon_OE_0921 | razon_OE_2024 | pct_sigue_bajo_2024_ponderado_n24 | pct_sigue_bajo_2024_celdas |
|---|---|---|---|---|---|---|
| perfil 1 | 74723 | 11356.674 | 0.804 | 0.831 | 88.684 | 83.359 |
| perfil 2 | 142472 | 18664.09 | 0.908 | 0.983 | 54.099 | 52.291 |
| perfil 3 | 87898 | 7240.817 | 0.845 | 0.84 | 81.588 | 79.135 |
| perfil 4 | 48881 | 6069.069 | 0.787 | 0.847 | 85.296 | 79.911 |
| perfil 5 | 42658 | 3524.009 | 0.839 | 0.866 | 72.421 | 69.723 |
| todos los objetivo_0921 | 396632 | 46854.659 | 0.858 | 0.899 | 72.025 | 69.279 |
| no objetivo_0921 (con historial) | 417438 | 41452.984 | 1.152 | 1.119 | 20.671 | 24.296 |
| base: todas las celdas con historial | 814070 | 88307.643 | 1.0 | 1.003 | 47.847 | 46.16 |
