"""Ingesta CCPC a Parquet (D-003): año por año, columnas VARCHAR, conversión explícita,
conciliación de filas y validación LN = SV + NV + NS."""
import shutil
import duckdb
from . import config as C

_COLS_VARCHAR = "{" + ",".join(f"'{c}':'VARCHAR'" for c in C.COLUMNAS_CSV) + "}"

# Conversión estricta (falla si no convierte); DEF/DEL con TRY_CAST por espacios y vacíos
_SELECT = """
SELECT
  CAST(AELEC AS INTEGER)    AS aelec,
  CAST(EDOCVE AS INTEGER)   AS edo,
  EDONOM                    AS edonom,
  CAST(MPIOCVE AS INTEGER)  AS mpio,
  MPIONOM                   AS mpionom,
  CAST(SECCION AS INTEGER)  AS seccion,
  trim(TIPOSEC)             AS tiposec,
  TRY_CAST(trim(DEF) AS INTEGER) AS def,
  TRY_CAST(trim("DEL") AS INTEGER) AS "del",
  CAST(SEXO AS INTEGER)     AS sexo,
  CAST(EDAD AS INTEGER)     AS edad,
  CAST(LN AS INTEGER)       AS ln,
  CAST(SV AS INTEGER)       AS sv,
  CAST(NV AS INTEGER)       AS nv,
  CAST(NS AS INTEGER)       AS ns
FROM read_csv('{glob}', header=true, quote='"', delim=',', columns={cols})
"""


def _nueva_conexion():
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{C.DUCKDB_MEMORY_LIMIT}'")
    con.execute(f"SET threads={C.DUCKDB_THREADS}")
    return con


def ingestar_anio(con, anio):
    """Lee un año, concilia, valida y escribe aelec=YYYY/ (zstd). Devuelve dict con conteos."""
    carpeta = C.RAW_CCPC / f"DatosAbiertos_DECEyEC_ConteosCensales{anio}"
    glob = str(carpeta / "*.csv")
    crudo = con.execute(
        f"SELECT count(*) FROM read_csv('{glob}', header=true, quote='\"', delim=',', "
        f"columns={_COLS_VARCHAR})").fetchall()[0][0]
    if crudo != C.FILAS_ESPERADAS[anio]:
        raise RuntimeError(f"{anio}: filas crudas {crudo} != esperadas {C.FILAS_ESPERADAS[anio]}")

    sel = _SELECT.format(glob=glob, cols=_COLS_VARCHAR)
    # el año del archivo debe ser el de la carpeta
    distintos = con.execute(f"SELECT DISTINCT aelec FROM ({sel})").fetchall()
    if distintos != [(anio,)]:
        raise RuntimeError(f"{anio}: AELEC en archivos = {distintos}")
    # LN = SV + NV + NS en todas las filas
    viol = con.execute(f"SELECT count(*) FROM ({sel}) WHERE ln <> sv + nv + ns").fetchall()[0][0]
    if viol:
        raise RuntimeError(f"{anio}: {viol} filas con LN <> SV+NV+NS")

    destino = C.INTERIM_CCPC / f"aelec={anio}"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    archivo = destino / "data.parquet"
    # aelec va en la ruta (hive), no dentro del archivo
    con.execute(f"COPY (SELECT * EXCLUDE (aelec) FROM ({sel})) TO '{archivo}' "
                f"(FORMAT parquet, COMPRESSION zstd)")
    escrito = con.execute(f"SELECT count(*) FROM read_parquet('{archivo}')").fetchall()[0][0]
    if escrito != crudo:
        raise RuntimeError(f"{anio}: filas escritas {escrito} != crudas {crudo}")
    return {"anio": anio, "crudo": crudo, "escrito": escrito, "violaciones_ln": viol}


def ingestar_todo():
    """Ingesta idempotente de los 6 años (sobrescribe)."""
    con = _nueva_conexion()
    C.INTERIM_CCPC.mkdir(parents=True, exist_ok=True)
    return [ingestar_anio(con, a) for a in C.ANIOS]


def conectar():
    """Conexión DuckDB con la VIEW `ccpc` sobre el Parquet (hive_partitioning por aelec)."""
    con = _nueva_conexion()
    patron = str(C.INTERIM_CCPC / "aelec=*" / "*.parquet")
    con.execute(f"CREATE VIEW ccpc AS SELECT * FROM read_parquet('{patron}', hive_partitioning=true)")
    return con
