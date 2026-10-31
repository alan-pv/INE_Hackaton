"""Panel de cohortes: cada celda sección × sexo × grupo de edad seguida por generación en las seis elecciones (D-006, D-007)."""
import json
import duckdb
from . import config as C

BASE = C.RAIZ / "data" / "interim" / "base"
CELDAS = BASE / "celdas.parquet"
CATALOGO = BASE / "catalogo_secciones.parquet"
CORTES = C.RAIZ / "data" / "processed" / "cortes_edad.json"
PROC = C.RAIZ / "data" / "processed"
PANEL = PROC / "panel_celda_eleccion.parquet"
ELEC = sorted(C.ELECCIONES)             # D-003 tabla fija
REF = 2024                              # año de referencia de los grupos (D-006)
MAYORIA = 18                            # edad de voto (ley; no es un umbral estimado)


def grupos():
    return json.loads(CORTES.read_text())["grupos"]


def conectar():
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{C.DUCKDB_MEMORY_LIMIT}'")
    con.execute(f"SET threads={C.DUCKDB_THREADS}")
    return con


def _case_grupo(col="cohorte"):
    """CASE SQL: grupo de edad EN 2024 de una cohorte (D-006, D-007). edad24 = 2024 - cohorte."""
    partes = []
    for g in grupos():
        lo, hi = g["edad_min"], g["edad_max"]
        cond = f"({REF}-{col}) >= {lo}" + (f" AND ({REF}-{col}) <= {hi}" if hi is not None else "")
        partes.append(f"WHEN {cond} THEN {g['id']}")
    return "CASE " + " ".join(partes) + " END"


def fraccion_cohortes():
    """frac_cohortes[(grupo, aelec)] = cohortes del grupo con edad >= 18 en aelec / total de cohortes.
    El grupo abierto (80+) tiene todas sus cohortes con >= 18 en toda elección (fracción 1)."""
    out = {}
    for g in grupos():
        lo, hi = g["edad_min"], g["edad_max"]
        for e in ELEC:
            if hi is None:
                out[(g["id"], e)] = 1.0
            else:
                edades_e = [e - (REF - a) for a in range(lo, hi + 1)]
                out[(g["id"], e)] = sum(x >= MAYORIA for x in edades_e) / len(edades_e)
    return out


# ---------------------------------------------------------------- panel
def construir_panel(con):
    """Panel largo celda x elección (D-006). Suma las cohortes del grupo con edad >= 18 en e,
    misma (edo, seccion, sexo); excluye section-years sin_observacion (D-002); sexo < 2 (D-005)."""
    tipos = ",".join(f"({a},'{t[1]}')" for a, t in C.ELECCIONES.items())
    fr = fraccion_cohortes()
    frs = ",".join(f"({g},{a},{v})" for (g, a), v in fr.items())
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE panel AS
    WITH cat AS (SELECT edo, seccion FROM read_parquet('{CATALOGO}') WHERE ref_anio={REF}),
    tip(aelec, tipo) AS (VALUES {tipos}),
    fr(grupo, aelec, frac_cohortes) AS (VALUES {frs}),
    base AS (
      SELECT c.edo, c.seccion, c.sexo, {_case_grupo('c.cohorte')} AS grupo, c.aelec,
             c.sv, c.nv, c.ns, c.ln
      FROM read_parquet('{CELDAS}') c JOIN cat USING (edo, seccion)
      WHERE c.sexo < 2 AND NOT c.sin_observacion AND c.edad >= {MAYORIA}
    )
    SELECT b.edo::SMALLINT edo, b.seccion::INTEGER seccion, b.sexo::TINYINT sexo, b.grupo::TINYINT grupo,
           b.aelec::SMALLINT aelec, t.tipo,
           sum(b.sv)::INTEGER sv, sum(b.nv)::INTEGER nv, (sum(b.sv)+sum(b.nv))::INTEGER n,
           sum(b.ns)::INTEGER ns, sum(b.ln)::INTEGER ln, f.frac_cohortes::FLOAT frac_cohortes
    FROM base b JOIN tip t USING (aelec) JOIN fr f USING (grupo, aelec)
    WHERE b.grupo IS NOT NULL
    GROUP BY ALL
    """)


def ordenar(panel):
    """Orden estable por (edo, sexo, grupo, aelec): el orden de filas con que se guarda el panel."""
    return panel.sort_values(["edo", "sexo", "grupo", "aelec"], kind="stable").reset_index(drop=True)
