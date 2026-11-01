# Arquitectura

Cómo está organizado el repositorio, qué hace cada script, en qué orden se corre y cómo verificar que el resultado se reproduce.

## Estructura

```
README.md              resultados
Makefile               orden de ejecución de la cadena completa
pyproject.toml         dependencias (Python 3.12)
docs/
  ARQUITECTURA.md      este documento
  METODOLOGIA.md       el método y cada decisión D-xxx que cita el código
  DATOS.md             fuentes, enlaces de descarga y dónde va cada archivo
src/                   paquete ine_perfiles con la lógica reutilizable (probada en tests/); ver src/README.md
scripts/               puntos de entrada, agrupados por etapa
  datos/  preparacion/  perfiles/  validacion/  figuras/
tests/                 pruebas (pytest)
reports/               salidas de cada script: reports/<etapa>/<script>/
data/                  raw/ (descargas), interim/ (intermedios y cachés), processed/ (tablas por celda); no se suben
entregables/           documento técnico, fichas de perfil y presentación ejecutiva
```

**Convención de salidas.** Cada script `scripts/<etapa>/<nombre>.py` escribe en `reports/<etapa>/<nombre>/`: un `control.md` con sus cifras de control (cada una marcada `[OK]` o detiene el script si falla), sus tablas en CSV y sus figuras. Los cálculos largos guardan su caché en `data/interim/<nombre>/`, de modo que volver a correr un script solo rehace lo que falta.

## Cómo reproducir

```bash
make instalar          # crea .venv e instala el paquete (requiere uv)
# descargar los datos a data/raw/ según docs/DATOS.md
make todo              # datos → preparacion → perfiles → validacion → figuras → pruebas
```

Cada etapa también se corre sola (`make datos`, `make perfiles`, etc.), y cada script se puede ejecutar directamente con `.venv/bin/python scripts/<etapa>/<nombre>.py` (en Windows, `.venv\Scripts\python`). Sin caché, la etapa de perfiles tarda varias horas (los ajustes, el bootstrap y las permutaciones); con caché, la cadena completa tarda unos minutos.

## Cadena de scripts

### 1. Datos (`scripts/datos/`)

| Script | Qué hace | Salida principal |
|---|---|---|
| `ingesta_ccpc.py` | Lee cada año de la CCPC por separado, concilia filas contra el CSV y verifica el SHA-256 de cada ZIP (D-003) | `data/interim/ccpc/` |
| `limpieza_ccpc.py` | Tablas base: celdas, catálogo de secciones y movilidad; verifica las cifras de control de participación (D-001, D-002, D-004, D-005) | `data/interim/base/` |
| `cambios_territoriales.py` | Marca las secciones reseccionadas con la tabla de equivalencias (D-015, D-016) | `data/interim/base/movilidad_seccion_marcada.parquet` |
| `fuentes_externas.py` | Censo 2020 por sección, CONAPO por municipio y gubernaturas concurrentes (D-015) | `data/interim/externos/` |
| `violencia_municipio.py` | Tasa municipal de homicidios, contraída hacia la del estado (D-027) | `data/interim/externos/violencia_mpio.parquet` |

### 2. Preparación (`scripts/preparacion/`)

| Script | Qué hace | Salida principal |
|---|---|---|
| `grupos_edad.py` | Estima los siete grupos de edad donde la curva nacional cambia de pendiente (D-007) | `data/processed/cortes_edad.json` |
| `panel_cohortes.py` | Sigue cada celda sección × sexo × grupo de edad por generación en las seis elecciones (D-006) | `data/processed/panel_celda_eleccion.parquet` |
| `contexto_seccion.py` | Indicadores de contexto de cada sección y llegada o salida de electores (D-010, D-016) | `data/processed/descriptores_seccion.parquet` |
| `brecha_esperada.py` | Brecha de cada celda frente a lo esperado para su edad y sexo, y población objetivo (D-009, D-022) | `data/processed/brecha_celda.parquet` |

### 3. Perfiles (`scripts/perfiles/`)

| Script | Qué hace | Salida principal |
|---|---|---|
| `seleccion_numero_perfiles.py` | PCA del contexto con análisis paralelo de Horn y mezcla con K = 1 a 10 (ICL, BIC, estabilidad, prueba contra el azar) (D-017, D-024, D-029) | caché `data/interim/seleccion_numero_perfiles/` |
| `referencia_cuatro_perfiles.py` | Mezcla con K=4 como referencia: perfiles, reajuste con 2009–2021 y curva de captura de 2024 (D-025, D-029) | `data/processed/perfiles_k4.parquet` |
| `prueba_violencia.py` | Prueba, con regla fijada de antemano, si la violencia mejora el modelo; resultado: queda como descriptor (D-027) | `reports/perfiles/prueba_violencia/veredicto.csv` |
| `perfiles_finales.py` | Los cinco perfiles: estabilidad, prueba contra el azar, regla de perfiles claros y descripción (D-011, D-017, D-029) | `data/processed/perfiles_finales.parquet` |

### 4. Validación (`scripts/validacion/`)

| Script | Qué hace | Salida principal |
|---|---|---|
| `validacion_2024.py` | Reajusta los cinco perfiles con 2009–2021 y mide qué tanto anticipan el déficit de 2024 (D-025, D-027) | `reports/validacion/validacion_2024/` |
| `sensibilidad_concurrencia_ns.py` | Rehace la cadena con la gubernatura concurrente y con las dos cotas del NS (D-030, D-031) | `reports/validacion/sensibilidad_concurrencia_ns/` |
| `intervalos_municipio.py` | Intervalos remuestreando municipios, línea base "objetivo sí/no" y peso de 80+ (D-032) | `reports/validacion/intervalos_municipio/` |
| `pruebas_lecturas.py` | Pone a prueba la lectura de cada perfil con predicciones fijadas de antemano (D-034) | `reports/validacion/pruebas_lecturas/` |
| `bateria_comun.py` | Aplica las mismas 13 pruebas a los cinco perfiles (D-036) | `reports/validacion/bateria_comun/bateria_comun.csv` |

### 5. Figuras (`scripts/figuras/`)

| Script | Qué hace | Salida principal |
|---|---|---|
| `figuras_documento.py` | Figuras, mapas y tablas del documento técnico, cada una con el CSV de sus datos | `reports/figuras/figuras_documento/` |

## Paquete `src/ine_perfiles/`

La lógica reutilizable vive en el paquete `ine_perfiles`; los scripts solo la llaman en orden. La descripción de cada módulo está en [`src/README.md`](../src/README.md).

## Cifras de control

Toda corrida debe reproducirlas; los scripts se detienen si alguna no cuadra.

| Cifra | Valor | Dónde se verifica |
|---|---|---|
| Participación nacional 2024 / 2021 / 2009 (SV/(SV+NV)) | 59.67% / 51.84% / 44.06% | `limpieza_ccpc`, `panel_cohortes` |
| Participación 2024 mujeres / hombres | 64.2% / 54.8% | `ingesta_ccpc`, `limpieza_ccpc` |
| Σ observado = Σ esperado por sexo × grupo × elección | error relativo < 1e-15 | `brecha_esperada` |
| Celdas de la población objetivo | 472,539 | todos los scripts de perfiles y validación |
| Votos faltantes por elección | 3.73 millones | `brecha_esperada`, `sensibilidad_concurrencia_ns` |
| AUC de captura 2024 con historial: historial propio / K=5 / K=4 / línea base | 0.759 / 0.720 / 0.730 / 0.672 | `validacion_2024`, `intervalos_municipio` |
| Σ % del déficit de los cinco perfiles | 100% | `perfiles_finales`, `figuras_documento` |

## Pruebas

`make pruebas` (o `.venv/bin/python -m pytest -q`). Las pruebas con datos sintéticos corren siempre; las que leen datos reales se omiten si falta el archivo que generan los scripts.
