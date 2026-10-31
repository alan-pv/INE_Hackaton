"""Contexto de cada sección (D-010, D-013, D-015, D-016, D-024).
Movilidad robusta = O/E acumulado sobre pares válidos (Σobs/Σesp), su log y su percentil en el estado.
La marca por texto de OBSERVACIONES y la tabla de circunscripciones salen de fuentes citadas."""
import re

import numpy as np
import pandas as pd

from . import config as C

RAIZ = C.RAIZ
EQUIV = RAIZ / "data" / "raw" / "externos" / "reseccionamiento" / "tablaEquivalenciasSeccionalesDesde1994.csv"
BASE = RAIZ / "data" / "interim" / "base"
EXT = RAIZ / "data" / "interim" / "externos"
PROC = RAIZ / "data" / "processed"

# D-016 punto 2: criterio de texto de la fuente. Solo incorporación tardía al padrón documentada;
# 'error' / 'podria ser' / 'check' son dudas o correcciones de la propia tabla, no del dato de la sección.
PATRON_INCORPORACION_TARDIA = re.compile(r"incorpor\w*\s+tarde", re.I)

# D-024: Acuerdo INE/CG130/2023 (27-feb-2023), vigente desde el PEF 2023-2024. Clave de entidad -> circunscripción.
CIRCUNSCRIPCION_POR_EDO = {
    2: 1, 3: 1, 8: 1, 10: 1, 14: 1, 18: 1, 25: 1, 26: 1,     # BC, BCS, Chih, Dgo, Jal, Nay, Sin, Son
    1: 2, 5: 2, 11: 2, 19: 2, 24: 2, 28: 2, 32: 2,           # Ags, Coah, Gto, NL, SLP, Tamps, Zac
    4: 3, 7: 3, 20: 3, 23: 3, 27: 3, 30: 3, 31: 3,           # Camp, Chis, Oax, QRoo, Tab, Ver, Yuc
    9: 4, 12: 4, 13: 4, 17: 4, 21: 4, 29: 4,                 # CDMX, Gro, Hgo, Mor, Pue, Tlax
    6: 5, 15: 5, 16: 5, 22: 5,                               # Col, Mex, Mich, Qro
}

COLS_ECEG = ["graproes", "prop_sin_escolaridad", "prop_analfabeta", "prop_posbasica", "prop_hli",
             "prop_afro", "prop_internet", "prop_celular", "prop_nacida_otra_ent",
             "prop_res_otra_ent_2015", "prop_discapacidad", "prop_18a24", "prop_60ymas"]
COLS_CONAPO = ["iim_dp2", "im_2020", "imn_2020"]  # D-015 (intensidad migratoria, marginación); ver reporte


def marcar_observaciones(equiv_csv=EQUIV):
    """Secciones (edo, seccion) cuya nota OBSERVACIONES documenta una incorporación tardía (D-016)."""
    t = pd.read_csv(equiv_csv, dtype=str)
    obs = t["OBSERVACIONES"].fillna("")
    m = t[obs.str.contains(PATRON_INCORPORACION_TARDIA)]
    out = pd.DataFrame({"edo": m["edon"].astype(int), "seccion": m["seccion"].astype(int),
                        "mun": m["mun"], "observacion": m["OBSERVACIONES"]})
    return out.drop_duplicates(["edo", "seccion"]).reset_index(drop=True)


def filtrar_pares_validos(mov, marcadas):
    """D-016: quita pares con cambio territorial o reseccionamiento y las secciones marcadas por texto.
    La nota no trae año, así que se excluyen todos los pares de la sección marcada."""
    ok = ~(mov["cambio_territorial_en_par"].fillna(False) | mov["reseccionada_en_par"].fillna(False))
    m = mov[ok]
    llaves = set(zip(marcadas["edo"], marcadas["seccion"]))
    marca = [(a, b) in llaves for a, b in zip(m["edo"], m["seccion"])]
    return m[~np.array(marca, dtype=bool)]


def oe_acumulado(pares, llave=("edo", "seccion")):
    """Σobs/Σesp por llave; log; n de pares."""
    g = pares.groupby(list(llave)).agg(obs=("observado", "sum"), esp=("esperado", "sum"),
                                       n_pares=("e", "nunique")).reset_index()
    g["oe_acum"] = g["obs"] / g["esp"].where(g["esp"] > 0)
    g["log_oe"] = np.log(g["oe_acum"].where(g["oe_acum"] > 0))
    return g


def percentil_en_estado(df, col="log_oe"):
    """Percentil (0-100, rango promedio) de `col` dentro de cada estado; NaN se mantiene."""
    return 100 * df.groupby("edo")[col].rank(pct=True, method="average")


def oe_municipio(pares, cat):
    """Σobs/Σesp por municipio de 2024 (D-016)."""
    p = pares.merge(cat[["edo", "seccion", "mpio_2024"]], on=["edo", "seccion"], how="inner")
    g = p.groupby(["edo", "mpio_2024"]).agg(obs=("observado", "sum"), esp=("esperado", "sum"),
                                            n_secciones=("seccion", "nunique")).reset_index()
    g = g.rename(columns={"mpio_2024": "mpio"})
    g["oe_mpio"] = g["obs"] / g["esp"].where(g["esp"] > 0)
    g["log_oe_mpio"] = np.log(g["oe_mpio"].where(g["oe_mpio"] > 0))
    return g


def cuantil_ponderado(x, w, qs):
    """Cuantiles ponderados (definición de la CDF ponderada por la izquierda); ignora NaN."""
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    ok = ~np.isnan(x) & (w > 0)
    x, w = x[ok], w[ok]
    if len(x) == 0:
        return [np.nan] * len(qs)
    o = np.argsort(x, kind="mergesort")
    x, w = x[o], w[o]
    cw = np.cumsum(w) / w.sum()
    return [float(x[min(np.searchsorted(cw, q, side="left"), len(x) - 1)]) for q in qs]


COLS_CONTEXTO = COLS_ECEG + ["razon_ln_p18"] + COLS_CONAPO + ["pctl_mov_estado"]
