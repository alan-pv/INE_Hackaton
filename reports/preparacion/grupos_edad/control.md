# Grupos de edad (D-007)

Generado por `scripts/preparacion/grupos_edad.py`. Unidad: edad simple, curva nacional (sexo 0/1), logit de SV/(SV+NV), pesos w = n.

## Por qué centrar
El nivel de cada elección es efecto periodo (D-007): la participación oscila ~15 pp entre presidenciales e intermedias en todas las edades. Se resta a cada logit su media ponderada por n, de modo que los cortes describen la **forma** de la curva y no el año electoral. En el CV, en la elección dejada fuera se reestiman intercepto y pendientes (cortes fijos) y se mide el error cuadrático medio ponderado de la forma.

## Edades excluidas (p en {0,1}, logit indefinido)

- 2009: ninguna
- 2012: [122, 124, 128, 132]
- 2015: ninguna
- 2018: [119, 120, 124, 130, 135, 137]
- 2021: [122, 123, 124, 127, 131, 134, 135, 137, 139]
- 2024: [121, 122, 127, 139, 140]

## Selección de k (CV dejando fuera una elección, regla 1-SE)

| k | CV-error medio | SE |
|---|---|---|
| 0 | 0.07178 | 0.00355 |
| 1 | 0.01708 | 0.00144 |
| 2 | 0.00581 | 0.00104 |
| 3 | 0.00303 | 0.00026 |
| 4 | 0.00189 | 0.00031 |
| 5 | 0.00115 | 0.00025 |
| 6 | 0.00103 | 0.00023 |
| 7 | 0.00081 | 0.00017 |
| 8 | 0.00059 | 0.00014 |

k de error mínimo = 8; **k elegido (1-SE) = 8**.

**Aviso:** el CV sigue bajando hasta el máximo explorado (K_MAX=8); el k elegido está en la frontera del rango y la curva suave admite más segmentos. Ver crítica en el informe del implementador.

## Cortes por elección (curva centrada, ajuste por elección)

Convención: corte = primera edad del nuevo tramo.

| Elección | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|---|---|---|---|---|---|---|---|---|
| 2009 | 20 | 23 | 28 | 46 | 62 | 74 | 85 | 105 |
| 2012 | 20 | 23 | 31 | 37 | 50 | 61 | 72 | 80 |
| 2015 | 20 | 25 | 29 | 33 | 41 | 68 | 75 | 83 |
| 2018 | 20 | 23 | 28 | 32 | 45 | 63 | 72 | 80 |
| 2021 | 20 | 23 | 28 | 45 | 69 | 76 | 84 | 99 |
| 2024 | 20 | 26 | 48 | 57 | 64 | 65 | 73 | 82 |
| **mediana** | **20** | **23** | **28** | **41** | **56** | **66** | **74** | **82** |
| mín–máx | 20–20 | 23–26 | 28–48 | 32–57 | 41–69 | 61–76 | 72–85 | 80–105 |
| curva promedio 6 | 20 | 23 | 28 | 38 | 48 | 67 | 74 | 82 |

## Grupos del análisis pooled (k=8, NO es la selección final)

| id | etiqueta | edad_min | edad_max |
|---|---|---|---|
| 1 | 18–19 | 18 | 19 |
| 2 | 20–22 | 20 | 22 |
| 3 | 23–27 | 23 | 27 |
| 4 | 28–40 | 28 | 40 |
| 5 | 41–55 | 41 | 55 |
| 6 | 56–65 | 56 | 65 |
| 7 | 66–73 | 66 | 73 |
| 8 | 74–81 | 74 | 81 |
| 9 | 82+ | 82 | None |

## [pooled] LN, votantes efectivos (n=SV+NV) y participación por grupo y elección

| Grupo | Elección | LN | n | Participación |
|---|---|---|---|---|
| 18–19 | 2009 | 2,622,531 | 2,558,185 | 43.98% |
| 20–22 | 2009 | 5,784,775 | 5,644,723 | 36.20% |
| 23–27 | 2009 | 10,032,765 | 9,791,622 | 34.09% |
| 28–40 | 2009 | 25,092,295 | 24,482,539 | 39.43% |
| 41–55 | 2009 | 19,283,122 | 18,817,496 | 50.73% |
| 56–65 | 2009 | 7,149,705 | 6,980,458 | 57.25% |
| 66–73 | 2009 | 3,698,115 | 3,610,667 | 57.28% |
| 74–81 | 2009 | 2,310,905 | 2,257,398 | 50.17% |
| 82+ | 2009 | 1,507,618 | 1,472,849 | 28.03% |
| 18–19 | 2012 | 3,015,318 | 3,008,758 | 62.03% |
| 20–22 | 2012 | 6,056,220 | 6,042,663 | 54.54% |
| 23–27 | 2012 | 9,888,800 | 9,866,141 | 52.45% |
| 28–40 | 2012 | 23,899,077 | 23,845,485 | 57.71% |
| 41–55 | 2012 | 19,055,673 | 19,015,757 | 69.04% |
| 56–65 | 2012 | 7,375,904 | 7,359,906 | 73.77% |
| 66–73 | 2012 | 3,668,913 | 3,660,643 | 72.68% |
| 74–81 | 2012 | 2,260,697 | 2,255,552 | 65.87% |
| 82+ | 2012 | 1,270,360 | 1,267,408 | 45.85% |
| 18–19 | 2015 | 3,238,477 | 3,037,419 | 44.22% |
| 20–22 | 2015 | 6,650,629 | 6,234,989 | 36.90% |
| 23–27 | 2015 | 10,812,828 | 10,140,873 | 35.06% |
| 28–40 | 2015 | 24,249,284 | 22,729,482 | 42.10% |
| 41–55 | 2015 | 21,452,593 | 20,142,659 | 53.32% |
| 56–65 | 2015 | 8,680,617 | 8,168,864 | 60.14% |
| 66–73 | 2015 | 4,302,344 | 4,055,275 | 63.13% |
| 74–81 | 2015 | 2,619,358 | 2,467,278 | 56.74% |
| 82+ | 2015 | 1,557,332 | 1,467,647 | 37.26% |
| 18–19 | 2018 | 3,533,731 | 3,291,377 | 60.60% |
| 20–22 | 2018 | 6,485,726 | 6,032,119 | 53.50% |
| 23–27 | 2018 | 11,325,702 | 10,539,931 | 52.35% |
| 28–40 | 2018 | 24,969,335 | 23,258,620 | 59.10% |
| 41–55 | 2018 | 23,285,684 | 21,705,354 | 67.75% |
| 56–65 | 2018 | 9,959,004 | 9,288,134 | 72.29% |
| 66–73 | 2018 | 4,884,871 | 4,556,959 | 72.88% |
| 74–81 | 2018 | 2,883,040 | 2,686,642 | 66.69% |
| 82+ | 2018 | 1,796,904 | 1,675,119 | 45.71% |
| 18–19 | 2021 | 3,223,188 | 3,082,705 | 51.61% |
| 20–22 | 2021 | 6,671,125 | 6,374,813 | 42.65% |
| 23–27 | 2021 | 11,213,272 | 10,717,250 | 39.87% |
| 28–40 | 2021 | 26,232,969 | 25,091,090 | 44.97% |
| 41–55 | 2021 | 24,571,360 | 23,517,323 | 57.17% |
| 56–65 | 2021 | 11,033,022 | 10,566,047 | 64.65% |
| 66–73 | 2021 | 5,486,917 | 5,256,436 | 68.27% |
| 74–81 | 2021 | 3,164,880 | 3,029,636 | 62.33% |
| 82+ | 2021 | 1,935,400 | 1,853,513 | 41.55% |
| 18–19 | 2024 | 3,563,333 | 3,330,893 | 56.76% |
| 20–22 | 2024 | 6,692,006 | 6,251,718 | 49.18% |
| 23–27 | 2024 | 11,248,779 | 10,507,272 | 47.13% |
| 28–40 | 2024 | 26,962,952 | 25,215,909 | 53.20% |
| 41–55 | 2024 | 25,706,661 | 24,055,215 | 64.33% |
| 56–65 | 2024 | 12,235,115 | 11,464,979 | 71.91% |
| 66–73 | 2024 | 6,313,486 | 5,919,194 | 76.14% |
| 74–81 | 2024 | 3,529,212 | 3,309,660 | 70.90% |
| 82+ | 2024 | 2,078,699 | 1,949,752 | 50.95% |

## [pooled] Tamaño de celda sección × sexo × grupo, 2024 (n = SV+NV; celdas con n>0)

| Grupo | Mediana | P10 | P90 | Celdas |
|---|---|---|---|---|
| 18–19 | 17 | 4 | 49 | 140,317 |
| 20–22 | 31 | 8 | 92 | 141,284 |
| 23–27 | 55 | 15 | 151 | 141,457 |
| 28–40 | 133 | 37 | 354 | 141,496 |
| 41–55 | 134 | 38 | 323 | 141,497 |
| 56–65 | 68 | 20 | 148 | 141,485 |
| 66–73 | 37 | 10 | 78 | 141,397 |
| 74–81 | 21 | 5 | 44 | 140,941 |
| 82+ | 12 | 3 | 28 | 138,827 |

## Intervalos de confianza (bootstrap por sección, 2024)

Remuestreo de secciones (70k, con reemplazo) B=200 (elegido por costo de cómputo), semilla 20261024; se reajustan los k cortes en cada réplica (semilla de inicio: ajuste puntual 2024). El error Monte Carlo es el EE de cada percentil estimado a partir de las B réplicas.

| Corte | Mediana final | Ajuste 2024 | IC 95% percentil | EE-MC p2.5 / p97.5 |
|---|---|---|---|---|
| c1 | 20 | 20 | 20.0–20.0 | 0.00 / 0.00 |
| c2 | 23 | 26 | 26.0–28.0 | 0.00 / 0.00 |
| c3 | 28 | 48 | 30.0–49.0 | 0.00 / 0.18 |
| c4 | 41 | 57 | 46.0–64.0 | 0.00 / 0.00 |
| c5 | 56 | 64 | 57.0–65.0 | 0.15 / 0.00 |
| c6 | 66 | 65 | 65.0–73.0 | 0.00 / 0.00 |
| c7 | 74 | 73 | 72.0–82.0 | 0.49 / 0.00 |
| c8 | 82 | 82 | 81.0–100.0 | 0.00 / 0.27 |

## Contraste con spline de suavizado (lambda por GCV)

Spline cúbico ponderado (w=n) sobre la curva promedio centrada, `scipy.interpolate.make_smoothing_spline` con lambda por validación cruzada generalizada. Edades donde la 1a derivada cruza 0 (extremos de la curva) y donde la 2a derivada cambia de signo (inflexiones):

- 1a derivada = 0: [25.7, 67.4]
- 2a derivada cambia de signo: [33.5, 54.7, 58.0, 95.7, 135.9]
- Cruces con edad > 95 caen donde n es mínimo y no son interpretables.


## Sensibilidad al número de cortes

- k=7: cortes [20, 24, 30, 42, 61, 72, 80]; grupos: 18–19, 20–23, 24–29, 30–41, 42–60, 61–71, 72–79, 80+
- k=9: cortes [20, 23, 28, 33, 46, 66, 74, 82, 99]; grupos: 18–19, 20–22, 23–27, 28–32, 33–45, 46–65, 66–73, 74–81, 82–98, 99+
- k=8 (elegido): cortes [20, 23, 28, 41, 56, 66, 74, 82]; grupos: 18–19, 20–22, 23–27, 28–40, 41–55, 56–65, 66–73, 74–81, 82+

## ¿Efecto de edad o de cohorte?

Si un corte es un efecto de EDAD, debe quedarse en la misma edad aunque pasen 3–15 años entre elecciones (pendiente 0 años/año). Si fuera de COHORTE, se desplazaría +3 años por elección (pendiente +1 año/año). Pendiente de OLS del corte contra el año (6 elecciones, 2009–2024), con su EE:

| Corte | Pendiente (años de edad por año calendario) | EE | Desplazamiento 2009→2024 (años) |
|---|---|---|---|
| c1 | +0.000 | 0.000 | +0 |
| c2 | +0.124 | 0.101 | +3 |
| c3 | +0.857 | 0.561 | +20 |
| c4 | +0.743 | 0.765 | +11 |
| c5 | +0.676 | 0.955 | +2 |
| c6 | -0.048 | 0.538 | -9 |
| c7 | -0.257 | 0.523 | -12 |
| c8 | -0.581 | 0.931 | -23 |

## Sensibilidad por sexo

### Hombres: k elegido = 6 (k mín = 8), cortes (mediana) = [20, 23, 28, 42, 70, 80]
CV: k=0: 0.06309±0.00468; k=1: 0.02539±0.00211; k=2: 0.00506±0.00077; k=3: 0.00409±0.00072; k=4: 0.00226±0.00051; k=5: 0.00105±0.00022; k=6: 0.00087±0.00019; k=7: 0.00080±0.00018; k=8: 0.00074±0.00015
Por elección: 2009: [20, 23, 28, 50, 70, 82]; 2012: [20, 25, 31, 38, 63, 77]; 2015: [20, 23, 28, 39, 70, 80]; 2018: [20, 23, 28, 34, 68, 79]; 2021: [20, 23, 28, 46, 70, 80]; 2024: [20, 27, 64, 65, 73, 82]

### Mujeres: k elegido = 6 (k mín = 8), cortes (mediana) = [20, 26, 36, 52, 69, 79]
CV: k=0: 0.08708±0.00312; k=1: 0.01408±0.00142; k=2: 0.00816±0.00131; k=3: 0.00278±0.00022; k=4: 0.00220±0.00028; k=5: 0.00128±0.00028; k=6: 0.00078±0.00013; k=7: 0.00071±0.00013; k=8: 0.00065±0.00015
Por elección: 2009: [20, 26, 47, 61, 73, 82]; 2012: [20, 31, 37, 51, 62, 76]; 2015: [20, 27, 36, 49, 69, 79]; 2018: [20, 27, 34, 52, 69, 78]; 2021: [20, 23, 28, 45, 69, 79]; 2024: [20, 26, 42, 67, 73, 81]

Ambos sexos: k = 8, cortes = [20, 23, 28, 41, 56, 66, 74, 82]


# SELECCIÓN FINAL (por sexo)

**Regla:** las celdas de D-009 son por sexo, así que k se elige por sexo (LOEO + 1-SE). La curva pooled mezcla dos formas distintas (hombres y mujeres tienen calendarios de vida diferentes) y exige tramos extra: es un artefacto de mezcla, y explica que el CV pooled no encuentre k interior (k=8, frontera). Por sexo, el CV sí tiene mínimo interior-estable en k=6 en ambos. Cortes comunes = media por posición de los cortes de hombres y mujeres, redondeo half-up (convención: corte = primera edad del nuevo tramo). Si k difiere entre sexos el script aborta.

- Hombres (k=6): [20, 23, 28, 42, 70, 80]
- Mujeres (k=6): [20, 26, 36, 52, 69, 79]
- **Cortes comunes (k=6): [20, 25, 32, 47, 70, 80]**
- Grupos: 18–19, 20–24, 25–31, 32–46, 47–69, 70–79, 80+

## Contraste con landmarks del spline y con IC bootstrap 2024

Landmarks (spline GCV, curva promedio, edades <95): 25.7, 33.5, 54.7, 58.0, 67.4 (mínimo/máximo = 1a derivada nula; inflexiones = 2a derivada cambia de signo). El IC bootstrap es el del corte del mismo número de orden del análisis pooled k=8 (no es el mismo modelo; se muestra la compatibilidad con cualquier IC).

| Corte común | Landmark más cercano | Distancia (años) | Dentro de algún IC 2024 pooled |
|---|---|---|---|
| 20 | 25.7 | 5.7 | c1[20–20] |
| 25 | 25.7 | 0.7 | ninguno |
| 32 | 33.5 | 1.5 | c3[30–49] |
| 47 | 54.7 | 7.7 | c3[30–49], c4[46–64] |
| 70 | 67.4 | 2.6 | c6[65–73] |
| 80 | 67.4 | 12.6 | c7[72–82] |

## Participación 2024 por grupo final y tamaño de celda sección × sexo

| Grupo | LN 2024 | n 2024 | Participación 2024 | Mediana n por celda | P10 | P90 | Celdas |
|---|---|---|---|---|---|---|---|
| 18–19 | 3,563,333 | 3,330,893 | 56.76% | 17 | 4 | 49 | 140,317 |
| 20–24 | 11,313,685 | 10,568,077 | 48.39% | 54 | 14 | 154 | 141,448 |
| 25–31 | 15,520,756 | 14,503,622 | 48.26% | 76 | 21 | 206 | 141,479 |
| 32–46 | 28,910,603 | 27,043,020 | 57.51% | 145 | 40 | 376 | 141,498 |
| 47–69 | 30,683,575 | 28,739,033 | 69.82% | 169 | 51 | 369 | 141,495 |
| 70–79 | 5,590,619 | 5,243,062 | 73.81% | 33 | 8 | 69 | 141,339 |
| 80+ | 2,747,672 | 2,576,885 | 54.68% | 16 | 4 | 36 | 139,967 |

### Participación por grupo final y elección

| Grupo | 2009 | 2012 | 2015 | 2018 | 2021 | 2024 |
|---|---|---|---|---|---|---|
| 18–19 | 43.98% | 62.03% | 44.22% | 60.60% | 51.61% | 56.76% |
| 20–24 | 35.33% | 53.80% | 36.29% | 52.89% | 41.73% | 48.39% |
| 25–31 | 35.01% | 52.60% | 35.85% | 53.89% | 40.24% | 48.26% |
| 32–46 | 43.57% | 62.49% | 47.17% | 63.02% | 49.81% | 57.51% |
| 47–69 | 55.07% | 72.21% | 57.99% | 70.85% | 62.48% | 69.82% |
| 70–79 | 53.96% | 69.48% | 60.18% | 70.09% | 65.78% | 73.81% |
| 80+ | 31.64% | 49.56% | 40.80% | 49.43% | 45.26% | 54.68% |