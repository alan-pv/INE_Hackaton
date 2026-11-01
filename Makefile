# Orden de ejecución de la cadena completa. Cada etapa depende de las anteriores.
# Uso: make todo   (o una etapa: make datos, make preparacion, make perfiles, make validacion, make figuras)
# Detalle de cada script, sus entradas y salidas: docs/ARQUITECTURA.md

# Ruta del Python del entorno: .venv/Scripts en Windows, .venv/bin en Linux y macOS
ifeq ($(OS),Windows_NT)
PY ?= .venv/Scripts/python
else
PY ?= .venv/bin/python
endif

.PHONY: todo instalar datos preparacion perfiles validacion figuras pruebas

todo: datos preparacion perfiles validacion figuras pruebas

instalar:
	uv venv .venv --python 3.12
	uv pip install --python $(PY) -e '.[dev]'

# 1. Datos: CCPC y fuentes externas a Parquet
datos:
	$(PY) scripts/datos/ingesta_ccpc.py
	$(PY) scripts/datos/limpieza_ccpc.py
	$(PY) scripts/datos/cambios_territoriales.py
	$(PY) scripts/datos/fuentes_externas.py
	$(PY) scripts/datos/violencia_municipio.py

# 2. Preparación: grupos de edad, panel de cohortes, contexto de sección y brecha frente a lo esperado
preparacion:
	$(PY) scripts/preparacion/grupos_edad.py
	$(PY) scripts/preparacion/panel_cohortes.py
	$(PY) scripts/preparacion/contexto_seccion.py
	$(PY) scripts/preparacion/brecha_esperada.py

# 3. Perfiles: número de perfiles, referencia con cuatro, prueba de la violencia y los cinco perfiles finales
#    (la primera vez tarda horas; después lee la caché de data/interim/)
perfiles:
	$(PY) scripts/perfiles/seleccion_numero_perfiles.py --nulo-max-grande=4
	$(PY) scripts/perfiles/referencia_cuatro_perfiles.py
	$(PY) scripts/perfiles/prueba_violencia.py
	$(PY) scripts/perfiles/perfiles_finales.py

# 4. Validación: captura de 2024, sensibilidad, intervalos por municipio y pruebas de las lecturas
validacion:
	$(PY) scripts/validacion/validacion_2024.py
	$(PY) scripts/validacion/sensibilidad_concurrencia_ns.py
	$(PY) scripts/validacion/intervalos_municipio.py
	$(PY) scripts/validacion/pruebas_lecturas.py
	$(PY) scripts/validacion/bateria_comun.py

# 5. Figuras y tablas del documento técnico
figuras:
	$(PY) scripts/figuras/figuras_documento.py

pruebas:
	$(PY) -m pytest -q
