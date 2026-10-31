"""Brecha de cada celda frente a lo esperado por su sexo y edad (D-022).

Estandarización indirecta (D-022), contracción beta-binomial con media conocida q_c
(D-022, estilo D-009), población objetivo (D-022), votos faltantes (D-022) y
persistencia (D-022). Participación = SV/(SV+NV) (D-001).
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import betainc, expit, gammaln, logit
from scipy.stats import rankdata  # noqa: F401  (útil para pruebas)

from . import config as C

LLAVE = ["edo", "seccion", "sexo", "grupo"]
ESTRATO = ["sexo", "grupo"]

# Elección de cómputo (no es parámetro del método, D-022): intervalo de búsqueda de log(phi) y
# tolerancia del optimizador. Si el óptimo cae en el borde superior se reporta phi -> infinito
# (sin sobredispersión); en el inferior, phi -> 0 (dependencia extrema).
LOGPHI_MIN, LOGPHI_MAX = -7.0, 25.0
XATOL = 1e-8
MARGEN_BORDE = 1e-3   # distancia al borde para declarar "en el borde"


# ---------------------------------------------------------------- D-022
def tasa_esperada(panel):
    """q_gse = Σsv/Σn por (sexo, grupo, aelec) con n>0 (D-022). Devuelve DataFrame con q."""
    p = panel[panel.n > 0]
    g = p.groupby(ESTRATO + ["aelec"], observed=True)[["sv", "n"]].sum(min_count=1)
    g["q"] = g.sv.astype("float64") / g.n.astype("float64")
    return g[["q"]].reset_index()


# ---------------------------------------------------------------- D-022
def agregar_celdas(panel, q_gse, aelecs=None):
    """Por celda: N, O, E, q, m, razon_cruda sobre elecciones con n>0 (D-022).
    `aelecs` restringe las elecciones (D-022). Devuelve DataFrame indexado por LLAVE."""
    p = panel[panel.n > 0]
    if aelecs is not None:
        p = p[p.aelec.isin(list(aelecs))]
    p = p[LLAVE + ["aelec", "sv", "n"]].merge(q_gse, on=ESTRATO + ["aelec"], how="left")
    p["sv"] = p.sv.astype("float64"); p["n"] = p.n.astype("float64")
    p["e"] = p.n * p.q
    g = p.groupby(LLAVE, observed=True).agg(N=("n", "sum"), O=("sv", "sum"),
                                            E=("e", "sum"), m=("aelec", "size"))
    g["q"] = g.E / g.N
    g["razon_cruda"] = g.O / g.E
    return g


# ---------------------------------------------------------------- D-022
def _nll_phi(logphi, O, N, q):
    """-logL (sin constantes) de la beta-binomial con media q conocida, precisión phi."""
    phi = np.exp(logphi)
    a, b = phi * q, phi * (1 - q)
    ll = (gammaln(O + a) + gammaln(N - O + b) - gammaln(N + phi)
          + gammaln(phi) - gammaln(a) - gammaln(b))
    return -float(ll.sum())


def _nll_binomial(O, N, q):
    """-logL (sin constantes) del límite binomial (phi -> inf), misma convención que _nll_phi."""
    return -float((O * np.log(q) + (N - O) * np.log1p(-q)).sum())


def ajustar_phi(O, N, q):
    """MLE de phi con media conocida q_c (D-022). Optimiza log(phi) en 1-D.
    Devuelve dict(phi, estado, ll, ll_binomial, n_celdas). Estados: 'mle',
    'sin_sobredispersion' (phi=inf: la binomial ajusta al menos igual), 'borde_inferior'."""
    O = np.asarray(O, float); N = np.asarray(N, float); q = np.asarray(q, float)
    ok = (q > 0) & (q < 1) & (N > 0)
    O, N, q = O[ok], N[ok], q[ok]
    if len(O) < 2:
        return dict(phi=np.inf, estado="sin_sobredispersion", ll=np.nan, ll_binomial=np.nan,
                    n_celdas=len(O))
    r = minimize_scalar(_nll_phi, bounds=(LOGPHI_MIN, LOGPHI_MAX), args=(O, N, q),
                        method="bounded", options={"xatol": XATOL})
    llb = -_nll_binomial(O, N, q)
    ll = -r.fun
    x = r.x
    if x > LOGPHI_MAX - MARGEN_BORDE or ll <= llb:
        estado, phi = "sin_sobredispersion", np.inf
    elif x < LOGPHI_MIN + MARGEN_BORDE:
        estado, phi = "borde_inferior", float(np.exp(x))
    else:
        estado, phi = "mle", float(np.exp(x))
    return dict(phi=phi, estado=estado, ll=ll, ll_binomial=llb, n_celdas=len(O),
                convergio=bool(r.success))


def posterior(O, N, q, phi):
    """Posterior Beta(a=O+phi q, b=N-O+phi(1-q)); devuelve p_tilde, delta, prob_bajo (D-022).
    phi puede ser un arreglo por celda (inf = binomial, posterior degenerada en O/N... se trata
    como a,b muy grandes: p_tilde = O/N salvo N=0). prob_bajo = P(p<q) = betainc(a, b, q)."""
    O = np.asarray(O, float); N = np.asarray(N, float); q = np.asarray(q, float)
    phi = np.broadcast_to(np.asarray(phi, float), O.shape)
    a = O + phi * q
    b = N - O + phi * (1 - q)
    p_tilde = a / (a + b)
    delta = logit(p_tilde) - logit(q)
    prob_bajo = betainc(a, b, q)
    return p_tilde, delta, prob_bajo


def contraer(cel, estrato_idx=None):
    """Ajusta phi por estrato sexo x grupo y añade phi, p_tilde, delta, prob_bajo, objetivo.
    `cel` indexado por LLAVE. Devuelve (cel_con_columnas, tabla_phi)."""
    cel = cel.copy()
    cel["phi"] = np.nan
    filas = []
    sexo = cel.index.get_level_values("sexo").to_numpy()
    grupo = cel.index.get_level_values("grupo").to_numpy()
    for (s, g) in sorted(set(zip(sexo, grupo))):
        msk = (sexo == s) & (grupo == g)
        aj = ajustar_phi(cel.O.to_numpy()[msk], cel.N.to_numpy()[msk], cel.q.to_numpy()[msk])
        cel.loc[msk, "phi"] = aj["phi"]
        filas.append(dict(sexo=int(s), grupo=int(g), **aj))
    pt, de, pb = posterior(cel.O.to_numpy(), cel.N.to_numpy(), cel.q.to_numpy(),
                           cel.phi.to_numpy())
    cel["p_tilde"], cel["delta"], cel["prob_bajo"] = pt, de, pb
    cel["objetivo"] = cel.prob_bajo > C.PROB_OBJETIVO       # D-022
    return cel, pd.DataFrame(filas)


# ---------------------------------------------------------------- D-022
def deficit_ultima(cel, panel, q_gse, aelec=2024):
    """Añade déficit (D-022) y las columnas crudas de la última elección."""
    cel = cel.copy()
    cel["deficit"] = cel.N * (cel.q - cel.p_tilde) / cel.m
    p = panel[(panel.aelec == aelec) & (panel.n > 0)][LLAVE + ["sv", "n", "ln"]]
    p = p.merge(q_gse[q_gse.aelec == aelec][ESTRATO + ["q"]], on=ESTRATO, how="left")
    p = p.set_index(LLAVE)
    cel[f"n_{aelec}"] = p.n.astype("float64").reindex(cel.index)
    cel[f"sv_{aelec}"] = p.sv.astype("float64").reindex(cel.index)
    cel[f"E_{aelec}"] = cel[f"n_{aelec}"] * p.q.reindex(cel.index)
    cel[f"ln_{aelec}"] = p.ln.astype("float64").reindex(cel.index)
    cel[f"deficit_{aelec}_crudo"] = cel[f"E_{aelec}"] - cel[f"sv_{aelec}"]
    return cel


# ---------------------------------------------------------------- D-022
def spearman_ponderada(x, y, w):
    """Spearman ponderada = Pearson ponderada de los rangos ponderados.
    Rango ponderado de x_i = (Σ w_j [x_j < x_i] + ½ Σ w_j [x_j = x_i]) / Σw (cdf ponderada a
    mitad de bloque, empates con el mismo rango). Con pesos iguales difiere del rango medio
    habitual en una constante, así que coincide con scipy.stats.spearmanr (D-022)."""
    x = np.asarray(x, float); y = np.asarray(y, float); w = np.asarray(w, float)

    def rango(v):
        u, inv = np.unique(v, return_inverse=True)
        bloque = np.bincount(inv, weights=w)
        antes = np.cumsum(bloque) - bloque
        return ((antes + 0.5 * bloque) / w.sum())[inv]

    rx, ry = rango(x), rango(y)
    mx, my = np.average(rx, weights=w), np.average(ry, weights=w)
    cov = np.average((rx - mx) * (ry - my), weights=w)
    return float(cov / np.sqrt(np.average((rx - mx) ** 2, weights=w)
                               * np.average((ry - my) ** 2, weights=w)))


def persistencia(c0921, c24, w24):
    """Compara la brecha 2009-21 con la de 2024 (D-022). Entradas indexadas por LLAVE.
    w24 = n_2024 por celda (Series). Devuelve dict de resultados."""
    j = c0921[["delta", "prob_bajo", "objetivo"]].join(
        c24[["delta", "prob_bajo"]], how="inner", lsuffix="_0921", rsuffix="_24")
    j["w"] = w24.reindex(j.index)
    j = j[j.w > 0]
    rho = spearman_ponderada(j.delta_0921, j.delta_24, j.w)
    obj = j.objetivo
    seguir = (j.prob_bajo_24 > C.PROB_OBJETIVO)
    frac_obj = float(np.average(seguir[obj], weights=j.w[obj]))
    frac_todas = float(np.average(seguir, weights=j.w))
    return dict(celdas_ambas=len(j), spearman=rho, frac_objetivo_sigue=frac_obj,
                frac_todas=frac_todas, celdas_objetivo=int(obj.sum()))


# ---------------------------------------------------------------- pipeline
def calcular(panel):
    """Pipeline completo. Devuelve (celdas, tabla_phi dict por periodo, q_gse, persist)."""
    q_gse = tasa_esperada(panel)
    cel, phi_t = contraer(agregar_celdas(panel, q_gse))
    cel = deficit_ultima(cel, panel, q_gse)
    c0921, phi_0921 = contraer(agregar_celdas(panel, q_gse, [a for a in C.ELECCIONES if a < 2024]))
    c24, phi_24 = contraer(agregar_celdas(panel, q_gse, [2024]))
    for suf, c in (("_0921", c0921), ("_24", c24)):
        for col in ["O", "E", "N", "phi", "p_tilde", "delta", "prob_bajo", "objetivo"]:
            cel[col + suf] = c[col].reindex(cel.index)
    pers = persistencia(c0921, c24, cel["n_2024"])
    return cel, dict(total=phi_t, p0921=phi_0921, p24=phi_24), q_gse, pers
