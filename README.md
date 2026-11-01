# Los votos que faltan

**Cinco perfiles para saber dónde buscarlos**

Hackathon INE 2026, *Hackea la participación*. Reto 1: Perfiles ciudadanos de participación.
Equipo Los Bien Dotados, Facultad de Ciencias de la Computación, BUAP.
J. A. Pomares Valdés, V. J. López Martínez, L. E. Ramiro Luna y L. G. Olivares Soto (asesor).

Entregables: [documento técnico](entregables/documento_tecnico.pdf) · [fichas de perfil](entregables/fichas_de_perfil.pdf) · [presentación ejecutiva](entregables/presentacion_ejecutiva.pptx)

## Resumen

Con los Conteos Censales de Participación Ciudadana (CCPC) 2009–2024 se reconstruyó el historial de voto de 983,708 grupos sección × sexo × edad en seis elecciones federales. Cada grupo se comparó con la participación nacional de su misma edad y sexo, y los que votan por debajo de lo esperado se dividieron en cinco perfiles.

- 3.7 millones de votos dejan de emitirse en cada elección federal frente a lo esperado por edad y sexo.
- 50.7 millones de electores (52% de la lista nominal) están en grupos que votan menos de lo esperado.
- 72% de esos grupos siguen por debajo en 2024 (la base es 48%): es un patrón, no un accidente.
- Los cinco perfiles son estables, distintos del azar y ubicables en el mapa.

La propuesta tiene dos piezas: el historial de cada sección dice **dónde** invertir y el perfil dice **a quién** hablarle y **cómo**.

## Método

1. Seguir cada grupo sección × sexo × edad como generación a lo largo de las seis elecciones.
2. Calcular su brecha frente a lo esperado por edad y sexo.
3. Quedarse con la población objetivo: 472,539 grupos que concentran los 3.7 millones de votos faltantes.
4. Agrupar con una mezcla de clases latentes y contexto del Censo 2020.
5. Validar con 2024, sensibilidad y pruebas de cada lectura.

Detalle en [docs/METODOLOGIA.md](docs/METODOLOGIA.md).

## Los cinco perfiles

| Perfil | % del déficit | Estabilidad | Sigue debajo en 2024 | Rasgos de sus secciones |
|---|:---:|:---:|:---:|---|
| **P1. Norte urbano** | 30.4% | 0.89 | 89% | Circunscripción 1; la brecha más grave y la única que se agrava en cada elección (de −6.6 a −13.9 puntos entre 2009 y 2021) |
| **P2. Centro urbano, brecha leve** | 26.5% | 0.94 | 54% | El más extenso (40% de la LN objetivo); casi alcanza lo esperado en las presidenciales y se aleja en las intermedias |
| **P3. Rural del Bajío y norte-centro** | 17.9% | 0.94 | 82% | 7.5 años de escolaridad y 26% de hogares con internet; los hombres de 25–46 votan menos que las mujeres de su edad |
| **P4. Recién llegados urbanos** | 16.3% | 0.86 | 85% | 36% nacieron en otra entidad; 10.3 años de escolaridad y 68% con internet |
| **P5. Sureste rural e indígena** | 8.8% | 0.91 | 72% | 10.3% habla lengua indígena, 16% tiene internet y 6.7 años de escolaridad |

% del déficit: parte de los votos faltantes que concentra el perfil. Estabilidad: Jaccard medio en el bootstrap de secciones (≥ 0.85 es muy estable). Sigue debajo en 2024: grupos del perfil, definidos solo con 2009–2021, que siguen por debajo de lo esperado en 2024. Los rasgos describen las secciones donde se concentra el perfil, no a las personas.

![Perfil dominante por municipio](reports/figuras/figuras_documento/mapa_dominante.png)

Perfil con más peso en cada municipio donde la población objetivo es la mayoría de la lista nominal. Los mapas de cada perfil están en `reports/figuras/figuras_documento/mapa_P1.png` a `mapa_P5.png`.

![Brecha por perfil y elección](reports/figuras/figuras_documento/trayectorias.png)

## Qué tan sólidos son

Ajustados solo con 2009–2021, los perfiles concentran mejor el déficit de 2024 que la regla simple "objetivo sí/no".

| Orden con 2009–2021 | AUC |
|---|:---:|
| Historial propio de cada sección | 0.759 |
| Perfiles K=5 | 0.720 |
| Objetivo sí/no | 0.672 |
| Azar | 0.500 |

| Prueba | Resultado |
|---|---|
| Estabilidad | Jaccard 0.855–0.944 en 20 réplicas bootstrap de secciones |
| Contra el azar | Supera las 19 permutaciones de datos barajados (p = 0.05); con seis perfiles el ajuste ya no repite su óptimo, así que cinco es el límite que sostienen los datos |
| Gubernatura concurrente | Se conserva el 96% de la LN objetivo y cada perfil reaparece con 89–99% de su peso |
| Votos no especificados | Contados como voto o como abstención se conserva el 91% y el 90% de la LN objetivo |
| Costo del quinto perfil | Frente a cuatro perfiles, −0.010 de AUC, a cambio de separar un grupo con estrategia propia (P4) |
| Violencia | Empeora la anticipación de 2024; queda solo como descriptor |

La lectura de cada perfil se contrastó con 13 pruebas iguales para los cinco, que podían fallar. La de P4 es la más débil y así se reporta en el documento técnico. La tabla completa está en [tabla_pruebas.csv](reports/figuras/figuras_documento/tabla_pruebas.csv).

## Reproducir

Los datos originales (unos 4.5 GB) no se incluyen; [docs/DATOS.md](docs/DATOS.md) lista las fuentes y dónde va cada archivo. Requiere Python 3.12 y [uv](https://docs.astral.sh/uv/).

Linux o macOS:

```bash
make instalar   # entorno con uv
make todo       # datos, preparación, perfiles, validación, figuras y pruebas
```

Windows con `make` (por ejemplo, desde Git Bash): los mismos comandos; el Makefile detecta Windows y usa `.venv/Scripts/python`.

Windows en PowerShell, sin `make`:

```powershell
uv venv .venv --python 3.12
uv pip install --python .venv\Scripts\python.exe -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q          # solo las pruebas
.venv\Scripts\python.exe scripts\datos\ingesta_ccpc.py   # y así cada script; el orden está en el Makefile
```

Cada script deja sus tablas, figuras y cifras de control en [reports/](reports/). Arquitectura y orden de la cadena: [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

Solo se usan datos agregados y públicos: CCPC del INE, Censo 2020 del INEGI, CONAPO y defunciones del INEGI. No se publica ninguna cifra a nivel de celda.
