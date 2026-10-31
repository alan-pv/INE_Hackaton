# Referencia de cuatro perfiles y captura del déficit de 2024 (D-025, D-029)

Perfiles ordenados por % del déficit (responsabilidades × w). El contexto describe la sección, no a las personas (D-010).

**Nota de lectura (D-026):** `im_2020` alto = **menos** marginación; `iim_dp2` alto = **menos** intensidad migratoria; `pctl_mov_estado` alto = más llegada neta de registros a la sección que la esperada (bajo = salida neta), percentil dentro del estado (D-016).

## 0. Cifras de control

- [OK] celdas objetivo = 472,539 (esperadas 472,539)
- [OK] Σ pesos = 472,539.000 = nº de celdas 472,539
- [OK] perfiles_k4.parquet: una fila por celda objetivo
- [OK] responsabilidades suman 1 por celda
- [OK] llave (edo, seccion, sexo, grupo) única en 983,708 celdas con E>0 (de 983,708)
- [OK] toda celda objetivo está en el universo de la curva de captura (merge 1:1)
- [OK] fórmula déficit = (E − N·p̃)/m reproduce la columna `deficit` del periodo completo (D-022)
- [OK] población objetivo 2009-21 = 396,632 celdas
- [OK] mezcla 2009-21: Σ pesos = 396,632.0 = nº de celdas 396,632
- [OK] construir_datos reproduce seleccion.construir (cat, X, w) en el periodo completo
- [OK] déficit crudo 2024 = E_24 − O_24 (float32 vs float64)

- logL del K=4 completo recalculada desde la caché: -4,551,683.7. Variables continuas: ['delta', 'pc1', 'pc2', 'pc3']; celdas con w=0: 162.
- Mezcla 2009-21: celdas objetivo_0921 396,632; celdas con w=0: 200; logL = -3,748,229.8; reinicios 3, óptimo repetido True (2 veces), no convergieron 0, pisos 0.
- Tiempos (s): universo 2009-21 3, ajuste 2009-21 0, curvas 4; total 16.

## 1. Perfiles K=4

| perfil | pct_deficit | celdas | ln_2024_miles | delta_medio | pct_crudo_2024 | pmax_media | pct_pmax_ge_09 | med_graproes | med_prop_internet | med_im_2020 | med_pctl_mov_estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 36.157 | 214794.22 | 25556.095 | -0.326 | 29.594 | 0.874 | 60.119 | 9.86 | 0.596 | 59.14 | 42.245 |
| 2 | 33.279 | 76896.644 | 11137.792 | -0.671 | 33.887 | 0.805 | 40.988 | 9.49 | 0.587 | 59.207 | 76.017 |
| 3 | 19.644 | 112600.713 | 8833.342 | -0.562 | 23.453 | 0.89 | 67.097 | 7.59 | 0.279 | 56.724 | 67.082 |
| 4 | 10.92 | 68247.422 | 5142.052 | -0.659 | 13.065 | 0.902 | 69.997 | 7.28 | 0.226 | 54.338 | 72.692 |


### Rasgos sobrerrepresentados (razón ≥ 1.25 o ≥ 40%; filtro solo de presentación)

#### Perfil 1

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 47.09 | 0.98 |
| sexo | 1 | 52.91 | 1.01 |
| circunscripcion | 4 | 24.52 | 1.86 |
| circunscripcion | 5 | 17.91 | 1.37 |
| tiposec | U | 94.78 | 1.3 |


#### Perfil 2

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 43.2 | 0.9 |
| sexo | 1 | 56.8 | 1.09 |
| grupo | 2 | 11.58 | 1.25 |
| circunscripcion | 1 | 69.79 | 1.89 |
| tiposec | U | 84.82 | 1.16 |


#### Perfil 3

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 56.91 | 1.19 |
| sexo | 1 | 43.09 | 0.83 |
| grupo | 6 | 8.5 | 1.47 |
| grupo | 7 | 7.76 | 1.7 |
| circunscripcion | 2 | 34.28 | 1.57 |
| circunscripcion | 5 | 23.67 | 1.82 |
| tiposec | M | 21.94 | 1.71 |
| tiposec | R | 45.24 | 3.21 |


#### Perfil 4

| variable | categoria | pct | razon |
|---|---|---|---|
| sexo | 0 | 47.85 | 1.0 |
| sexo | 1 | 52.15 | 1.0 |
| grupo | 1 | 6.19 | 1.51 |
| grupo | 2 | 13.89 | 1.5 |
| grupo | 7 | 7.53 | 1.65 |
| circunscripcion | 3 | 55.96 | 3.69 |
| tiposec | M | 20.3 | 1.58 |
| tiposec | R | 41.7 | 2.96 |


## 2. Captura del déficit de 2024 ordenando con 2009-21 (D-025)

Curva de captura: celdas de menor a mayor r̂ (información solo de 2009-21); x = fracción acumulada de LN 2024; y = fracción acumulada del déficit crudo 2024 Σ(E_24 − O_24). `pos`: parte positiva por celda, normalizada por su total (termina en 1). `signo`: déficit con signo acumulado entre el déficit positivo total (termina en ≈ 0, porque Σ O = Σ E por estrato en 2024: total con signo = 0.00). Empates de r̂ = segmento recto (esperanza con desempate aleatorio). AUC = área bajo la curva (0.5 = diagonal para `pos`). Métodos: historial propio = p̃_0921/(E_0921/N_0921) [las celdas sin historial van al final con razón 1]; mezcla K=4 reajustada con 2009-21 (r̂ = ΣO/ΣE del perfil asignado; las celdas no objetivo_0921 van al final con razón 1.1521); azar = orden aleatorio con semilla 0. Figura: `captura.png`.

| universo | metodo | AUC_pos | AUC_signo | celdas |
|---|---|---|---|---|
| todas las celdas con 2024 | historial propio | 0.692 | 0.4012 | 958098 |
| todas las celdas con 2024 | mezcla K=4 (2009-21) | 0.6892 | 0.3658 | 958098 |
| todas las celdas con 2024 | azar | 0.5005 | 0.0002 | 958098 |
| solo celdas con historial 2009-21 | historial propio | 0.7591 | 0.5011 | 788460 |
| solo celdas con historial 2009-21 | mezcla K=4 (2009-21) | 0.7297 | 0.4123 | 788460 |
| solo celdas con historial 2009-21 | azar | 0.5004 | -0.0201 | 788460 |


### Mezcla K=4 reajustada con 2009-21

- Datos: población objetivo_0921, δ̃ = delta_0921, w = déficit 2009-21 = (E_0921 − N_0921·p̃_0921)/m_0921; mismo PCA y Horn que la selección de K (3 componentes); reglas de D-017, semilla [C.SEMILLA, 2, K].
- Reetiquetado (asignación húngara) contra los K=4 completos en 367,230 celdas comunes (de 396,632); ARI ponderado entre ambas asignaciones: **0.813**.

Cruce (columnas = perfil completo; % del peso w de cada perfil completo que cae en cada clase 2009-21):

| clase 2009-21 | perfil_completo_1 | perfil_completo_2 | perfil_completo_3 | perfil_completo_4 |
|---|---|---|---|---|
| clase 2009-21 → perfil 2 | 10.5 | 97.2 | 0.6 | 0.1 |
| clase 2009-21 → perfil 4 | 0.4 | 1.3 | 0.9 | 98.8 |
| clase 2009-21 → perfil 1 | 86.4 | 1.1 | 0.2 | 0.4 |
| clase 2009-21 → perfil 3 | 2.6 | 0.4 | 98.3 | 0.6 |


## 3. Persistencia por perfil (mezcla 2009-21 → 2024)

Razones O/E agrupadas ΣO/ΣE; '% sigue bajo' = objetivo_24 en 2024 entre celdas con 2024; base = todas las celdas con historial.

| perfil | celdas | ln_2024_miles | razon_OE_0921 | razon_OE_2024 | pct_sigue_bajo_2024_ponderado_n24 | pct_sigue_bajo_2024_celdas |
|---|---|---|---|---|---|---|
| perfil 1 | 187496 | 23617.305 | 0.902 | 0.97 | 58.29 | 56.441 |
| perfil 2 | 66571 | 10687.614 | 0.749 | 0.794 | 93.596 | 89.621 |
| perfil 3 | 94648 | 8386.757 | 0.841 | 0.842 | 82.244 | 79.371 |
| perfil 4 | 47917 | 4162.983 | 0.832 | 0.859 | 75.518 | 71.859 |
| todos los objetivo_0921 | 396632 | 46854.659 | 0.858 | 0.899 | 72.025 | 69.279 |
| no objetivo_0921 (con historial) | 417438 | 41452.984 | 1.152 | 1.119 | 20.671 | 24.296 |
| base: todas las celdas con historial | 814070 | 88307.643 | 1.0 | 1.003 | 47.847 | 46.16 |

