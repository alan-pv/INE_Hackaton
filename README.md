# Los votos que faltan

**Cinco perfiles para saber dónde buscarlos.** Hackathon INE 2026 *"Hackea la participación"*, Reto 1: Perfiles ciudadanos de participación.

Equipo **Los Bien Dotados**: J. A. Pomares Valdés, V. J. López Martínez, L. E. Ramiro Luna y L. G. Olivares Soto (asesor). Facultad de Ciencias de la Computación, BUAP.

## Resultados

Con los Conteos Censales de Participación Ciudadana (CCPC) 2009–2024 se reconstruyó el historial de voto de **983,708 grupos** sección × sexo × edad en seis elecciones federales. Cada grupo se comparó con la participación nacional de su misma edad y sexo.

| | |
|---|---|
| Grupos que votan por debajo de lo esperado (población objetivo) | **472,539** (48% de los grupos) |
| Lista nominal en esos grupos | **50.7 millones** (52% de la LN) |
| Votos que dejan de emitirse en cada elección federal | **3.7 millones** |
| Grupos debajo de lo esperado en 2009–2021 que siguen debajo en 2024 | **72%** (frente a 48% de base) |

### Los cinco perfiles

| Perfil | % del déficit | Estabilidad (Jaccard) | Sigue debajo en 2024 | Rasgos de sus secciones (mediana) |
|---|---|---|---|---|
| **P1 · Norte urbano** | 30.4% | 0.89 | 89% | Circunscripción 1, brecha grave que se agrava en cada elección (de −6.6 a −13.9 puntos entre 2009 y 2021) |
| **P2 · Centro urbano, brecha leve** | 26.5% | 0.94 | 54% | El más extenso (40% de la LN objetivo); casi alcanza lo esperado en las presidenciales y se aleja en las intermedias |
| **P3 · Rural del Bajío y norte-centro** | 17.9% | 0.94 | 82% | 7.5 años de escolaridad, 26% de hogares con internet; hombres de 25–46 más abajo que las mujeres de su edad |
| **P4 · Recién llegados urbanos** | 16.3% | 0.86 | 85% | 36% nacieron en otra entidad, 10.3 años de escolaridad, 68% con internet |
| **P5 · Sureste rural e indígena** | 8.8% | 0.91 | 72% | 10.3% habla lengua indígena, 16% con internet, 6.7 años de escolaridad |

El % del déficit es la parte de los votos faltantes que concentra cada perfil. "Sigue debajo en 2024" es el porcentaje de los grupos del perfil, definidos con 2009–2021, que siguen por debajo de lo esperado en 2024 (la base es 48%). Los rasgos describen las secciones donde se concentra el perfil, no a las personas.

### Qué tan sólidos son

- **Estables y distintos del azar.** Los cinco perfiles son "muy estables" (Jaccard ≥ 0.85 en 20 réplicas bootstrap de secciones) y la solución supera las 19 permutaciones de datos barajados (p = 0.05). Con seis perfiles el ajuste ya no repite su óptimo, así que cinco es el límite que sostienen los datos.
- **Anticipan 2024.** Ajustados solo con 2009–2021, los perfiles ordenan el déficit de 2024 con un AUC de 0.720, por encima de la línea base "objetivo sí/no" (0.672; diferencia de +0.048, IC 95% por municipio [0.040, 0.057]).
- **Dónde y a quién.** El historial de cada sección anticipa 2024 mejor que los perfiles (AUC 0.759; +0.039 [0.034, 0.044]). Por eso la propuesta tiene dos piezas: **el historial dice dónde invertir y el perfil dice a quién hablarle y cómo.**
- **Costo del quinto perfil.** Frente a cuatro perfiles, el quinto cuesta −0.010 de AUC [−0.013, −0.006] y separa un grupo con estrategia propia (P4).
- **Resisten los cambios de definición.** Con la gubernatura concurrente dentro de lo esperado se conserva el 96% de la LN objetivo. Con los votos no especificados contados como voto o como abstención se conserva el 91% y el 90%. P2 es el perfil más sensible.
- **La violencia describe, no segmenta.** Con la tasa municipal de homicidios dentro del modelo, la anticipación de 2024 empeora (−0.005 de AUC [−0.006, −0.004]). Por la regla fijada de antemano, queda solo como descriptor.
- **Las lecturas se pusieron a prueba.** La explicación de cada perfil se contrastó con pruebas que podían fallar, las mismas 13 para los cinco perfiles: P1 cumple 3 de 3, P2 1 de 1, P3 2 de 3, P4 1 de 3 (la lectura más débil) y P5 3 de 5.

## Entregables

| Archivo | Contenido |
|---|---|
| [`entregables/documento_tecnico.pdf`](entregables/documento_tecnico.pdf) | Documento técnico (12 cuartillas): método, los cinco perfiles con su mapa, sus pruebas y su estrategia |
| [`entregables/fichas_de_perfil.pdf`](entregables/fichas_de_perfil.pdf) | Fichas operativas de cada perfil para el diseño de campañas |
| [`entregables/presentacion_ejecutiva.pptx`](entregables/presentacion_ejecutiva.pptx) | Presentación ejecutiva (10 diapositivas) |

## Para entender y reproducir el proyecto

| Documento | Contenido |
|---|---|
| [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) | El método en cinco pasos y cada decisión que cita el código (`D-xxx`) |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Estructura del repositorio, cadena de scripts, cómo reproducir y cifras de control |
| [`docs/DATOS.md`](docs/DATOS.md) | Fuentes, enlaces de descarga y dónde va cada archivo |

Las cifras de este README salen de `reports/`, donde cada script deja sus tablas y sus cifras de control.

Solo se usan datos agregados y públicos (CCPC del INE, Censo 2020 del INEGI, CONAPO y defunciones del INEGI). No se publica ninguna cifra a nivel de celda.
