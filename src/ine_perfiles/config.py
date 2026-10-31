"""Configuración central: rutas, elecciones, parámetros del método y cifras de control.
Cada parámetro cita la decisión que lo justifica (docs/METODOLOGIA.md)."""
from pathlib import Path

# Raíz del proyecto, calculada relativa a este archivo (src/ine_perfiles/config.py)
RAIZ = Path(__file__).resolve().parents[2]
RAW_CCPC = RAIZ / "data" / "raw" / "ccpc"            # descargas originales de la CCPC (docs/DATOS.md)
SHA256SUMS = RAW_CCPC / "SHA256SUMS"                 # D-003 (SHA-256 de cada ZIP)
INTERIM = RAIZ / "data" / "interim"                  # resultados intermedios y cachés
INTERIM_CCPC = INTERIM / "ccpc"                      # D-003 (Parquet particionado por año)
PROCESADOS = RAIZ / "data" / "processed"             # tablas finales por celda (no se publican, D-005)
REPORTES = RAIZ / "reports"                          # cifras de control, tablas y figuras de cada script


def salidas(script):
    """Carpeta de resultados de un script: reports/<etapa>/<nombre>/, el mismo camino que scripts/<etapa>/<nombre>.py.
    Acepta la ruta del script (__file__) o el texto "etapa/nombre" para leer las salidas de otro script."""
    p = Path(script)
    ruta = REPORTES / p.parent.name / p.stem if p.suffix == ".py" else REPORTES / p
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def cache(nombre):
    """Carpeta de caché de un script en data/interim/<nombre>/ (permite retomar los cálculos largos)."""
    ruta = INTERIM / nombre
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


# Años de la CCPC, cada uno se lee por separado  # D-003
ANIOS = [2009, 2012, 2015, 2018, 2021, 2024]

# Tabla fija de elecciones federales (FELECCION no se parsea porque su formato cambia entre años)  # D-003
# aelec -> (fecha ISO, tipo)
ELECCIONES = {
    2009: ("2009-07-05", "intermedia"),
    2012: ("2012-07-01", "presidencial"),
    2015: ("2015-06-07", "intermedia"),
    2018: ("2018-07-01", "presidencial"),
    2021: ("2021-06-06", "intermedia"),
    2024: ("2024-06-02", "presidencial"),
}

# Mapeo de columnas del CSV (16 campos, en orden) a nombres en minúsculas
COLUMNAS_CSV = ["AELEC", "FELECCION", "EDOCVE", "EDONOM", "MPIOCVE", "MPIONOM", "SECCION",
                "TIPOSEC", "DEF", "DEL", "SEXO", "EDAD", "LN", "SV", "NV", "NS"]

# Filas esperadas por año en el CSV crudo (conciliación)  # D-003
FILAS_ESPERADAS = {2009: 8706843, 2012: 8604456, 2015: 9106059,
                   2018: 9251122, 2021: 9430502, 2024: 9773730}
SECCIONES_2024 = 70751  # (edo, seccion) distintos en 2024  # D-003

# Recursos de DuckDB (ajustar a la máquina; no cambian ningún resultado)
DUCKDB_MEMORY_LIMIT = "5GB"
DUCKDB_THREADS = 6

# Códigos de SEXO (diccionario CCPC 2024: 0 Hombres, 1 Mujeres, 2 No binario)  # D-005
SEXO_HOMBRE, SEXO_MUJER, SEXO_NO_BINARIO = 0, 1, 2

# Población objetivo y mezcla
PROB_OBJETIVO = 0.5       # D-022: más probable abajo que arriba de lo esperado (regla de Bayes con pérdida simétrica)
K_MAX_FOCAL = 10          # D-029: rango de K explorado
B_NULO = 19               # D-029: permutaciones de la prueba contra el azar (p mínimo = 1/20)
SEMILLA = 0               # reproducibilidad de todos los procesos aleatorios

# Cifras de control, participación % = 100*SV/(SV+NV)  # D-001
# {aelec: {"nacional": (valor, tolerancia_pts), "mujeres": (...), "hombres": (...)}}
CIFRAS_CONTROL = {
    2024: {"nacional": (59.67, 0.01), "mujeres": (64.2, 0.05), "hombres": (54.8, 0.05)},
    2021: {"nacional": (51.84, 0.01), "mujeres": (55.62, 0.01), "hombres": (47.76, 0.01)},
    2009: {"nacional": (44.06, 0.01), "mujeres": (47.35, 0.01), "hombres": (40.53, 0.01)},
}

# Violencia homicida municipal (D-027)
VENTANAS_VIOLENCIA = {"v2023": (2009, 2023), "v2020": (2009, 2020)}  # D-027: años completos previos a 2024 / a 2021
CODIGO_HOMICIDIO = 2        # D-027: `presunto` (≤2021) y `tipo_defun` (≥2022) = 2 "Homicidio" (catálogo de INEGI)
NO_ESP_ENT, NO_ESP_MUN, NO_ESP_ANIO = 99, 999, 9999  # D-027: códigos "no especificado" de INEGI: se cuentan, no se reparten
POR_HABITANTES = 100_000    # D-027: tasas por 100 mil habitantes por año

# Comparación de curvas de captura con bootstrap pareado (D-025, D-027)
B_PERMANENCIA = 1999        # D-027: (B+1)*0.025 = 50 es entero (intervalo percentil exacto)
NIVEL_IC_PERMANENCIA = 0.95  # D-027: intervalo percentil al 95%
SUFIJO_SEMILLA_PERMANENCIA = 6  # D-027: semilla [SEMILLA, sufijo] del bootstrap pareado
COL_VIOLENCIA = {"v2023": "log_tasa_contr_v2023", "v2020": "log_tasa_contr_v2020"}  # D-027: modelo completo / fuera de tiempo

# Perfiles claros y regla de los cinco perfiles (D-011, D-029)
JACCARD_CLARO = 0.85            # D-011: Jaccard medio mínimo ("muy estable")
N_GE_NULO_CLARO = 0             # D-029: permutaciones con G >= G_obs admitidas (0/B_NULO, p = 0.05)
K_EVALUADO_K5 = 5               # D-029: número de perfiles entregado
N_CLARAS_MIN_K5 = 4             # D-029: clases claras mínimas para entregar K=5

# Sensibilidad (D-030, D-031)
SENS_ESCENARIOS = ("concurrencia", "ns_voto", "ns_abst")  # D-030, D-031
SENS_CELDAS_OBJETIVO_CONTROL = 472_539   # D-022: cifra de control de la población objetivo
SENS_VOTOS_FALTANTES_CONTROL_M = 3.73    # D-022: votos faltantes por elección (millones, redondeo a 0.01)
SENS_TOL_CONSERVACION = 1e-9             # D-022: error relativo máximo de Σ O = Σ E por estrato
SENS_MAYORIA = 0.5                       # D-030: "más de la mitad" del peso en un solo perfil
SENS_ELECCIONES_INTERMEDIAS = tuple(a for a, (_, t) in ELECCIONES.items() if t == "intermedia")    # D-030
SENS_ELECCIONES_PRESIDENCIALES = tuple(a for a, (_, t) in ELECCIONES.items() if t == "presidencial")  # D-030
