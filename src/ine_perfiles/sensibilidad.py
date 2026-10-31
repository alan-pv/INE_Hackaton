"""Sensibilidad de los perfiles a la gubernatura concurrente (D-030) y a los votos no especificados (D-031).

Lógica reutilizable: lo esperado estratificado además por la bandera k (D-030), definiciones de voto
con el NS (D-031/b), brecha D-022 por escenario, comparación de poblaciones objetivo, cruce de pesos
y regla de mayoría (D-030), y la tabla observado/esperado por perfil y elección (D-030).
Participación = SV/(SV+NV) (D-001) salvo en las cotas de D-031. Todo es descriptivo.
"""
import numpy as np
import pandas as pd

from . import brecha as B
from . import config as C
from . import mezcla_mixta as MM
from . import evaluacion as CF

LLAVE = B.LLAVE
ESTRATO = B.ESTRATO
ESCENARIOS = ("principal",) + tuple(C.SENS_ESCENARIOS)


# ---------------------------------------------------------------- definiciones de voto
def preparar_panel(panel, escenario, conc=None):
    """Devuelve LLAVE + aelec + sv (votos) + n (denominador) [+ k] según el escenario.
    principal / concurrencia: votos = SV, n = SV+NV (D-001). ns_voto (D-031): votos = SV+NS, n = SV+NV+NS.
    ns_abst (D-031): votos = SV, n = SV+NV+NS. En 'concurrencia' añade k = gubernatura (nulos/ausentes = 0, D-030)."""
    assert escenario in ESCENARIOS, escenario
    p = panel[LLAVE + ["aelec", "sv", "nv", "ns"]].copy()
    sv, nv, ns = (p[c].astype("int64") for c in ("sv", "nv", "ns"))
    if escenario in ("principal", "concurrencia"):
        p["sv"], p["n"] = sv, sv + nv
    elif escenario == "ns_voto":
        p["sv"], p["n"] = sv + ns, sv + nv + ns
    else:
        p["sv"], p["n"] = sv, sv + nv + ns
    p = p.drop(columns=["nv", "ns"])
    if escenario == "concurrencia":
        n0 = len(p)
        p = p.merge(conc, on=["aelec", "edo"], how="left", validate="m:1")
        assert len(p) == n0
        p["k"] = p["k"].fillna(0).astype("int8")
    return p


def cargar_concurrencia(ruta):
    """k = gubernatura (D-030) por (aelec, edo); nulos = 0 (False). Llave única verificada."""
    c = pd.read_parquet(ruta, columns=["aelec", "edo", "gubernatura"])
    c = c.rename(columns={"gubernatura": "k"})
    c["k"] = c["k"].fillna(0).astype("int8")
    assert not c.duplicated(["aelec", "edo"]).any()
    assert set(c["k"].unique()) <= {0, 1}
    return c


# ---------------------------------------------------------------- D-022 / D-030
def tasa_esperada_k(p, extra=()):
    """q = Σsv/Σn por (sexo, grupo, aelec[, extra]) con n>0. Con extra=['k'] es q_gsek (D-030)."""
    extra = list(extra)
    g = p[p.n > 0].groupby(ESTRATO + ["aelec"] + extra, observed=True)[["sv", "n"]].sum()
    g["q"] = g.sv.astype("float64") / g.n.astype("float64")
    return g[["q"]].reset_index()


# ---------------------------------------------------------------- D-022
def agregar_celdas_k(p, q, extra=(), aelecs=None):
    """Como brecha.agregar_celdas pero uniendo q por (sexo, grupo, aelec[, extra]).
    Devuelve (celdas indexadas por LLAVE con N, O, E, m, q, razon_cruda ; error relativo máximo de Σ O = Σ E
    dentro de cada estrato sexo × grupo × aelec[× extra])."""
    extra = list(extra)
    p = p[p.n > 0]
    if aelecs is not None:
        p = p[p.aelec.isin(list(aelecs))]
    n0 = len(p)
    p = p[LLAVE + ["aelec", "sv", "n"] + extra].merge(q, on=ESTRATO + ["aelec"] + extra, how="left", validate="m:1")
    assert len(p) == n0 and p["q"].notna().all()
    p["sv"] = p.sv.astype("float64")
    p["n"] = p.n.astype("float64")
    p["e"] = p.n * p.q
    s = p.groupby(ESTRATO + ["aelec"] + extra, observed=True)[["sv", "e"]].sum()
    err = float((np.abs(s.sv - s.e) / s.sv).max())
    g = p.groupby(LLAVE, observed=True).agg(N=("n", "sum"), O=("sv", "sum"), E=("e", "sum"), m=("aelec", "size"))
    g["q"] = g.E / g.N
    g["razon_cruda"] = g.O / g.E
    return g, err


def brecha_escenario(p, extra=()):
    """D-022 completo para un panel preparado. Devuelve (cel, tabla_phi, q, error_conservacion)."""
    q = tasa_esperada_k(p, extra)
    cel, err = agregar_celdas_k(p, q, extra)
    cel, phi = B.contraer(cel)                                   # φ por estrato sexo × grupo; objetivo = prob_bajo > 1/2 (D-022)
    cel["deficit"] = cel.N * (cel.q - cel.p_tilde) / cel.m       # D-022 (votos faltantes por elección)
    return cel, phi, q, err


def votos_faltantes(cel):
    """Σ max(déficit, 0) sobre la población objetivo (D-022, D-030)."""
    return float(cel.deficit[cel.objetivo].clip(lower=0).sum())


# ---------------------------------------------------------------- base 2024 (pesos)
def base_2024(panel):
    """ln_2024 y n_2024 (SV+NV, definición principal) por celda (pesos comunes de Jaccard y Spearman)."""
    p = panel[panel.aelec == 2024]
    b = p[LLAVE].copy()
    b["ln_2024"] = p["ln"].astype("float64").to_numpy()
    b["n_2024"] = (p["sv"].astype("int64") + p["nv"].astype("int64")).astype("float64").to_numpy()
    assert not b.duplicated(LLAVE).any()
    return b.set_index(LLAVE)


# ---------------------------------------------------------------- datos de la mezcla (misma PCA)
def datos_mezcla(cel, d, pcs, r):
    """Datos de la mezcla de la población objetivo del escenario con la MISMA PCA (D-024, D-030)."""
    o = cel[cel.objetivo].reset_index()
    for c in LLAVE:
        o[c] = o[c].astype("int64")
    dat, x, n_cero = CF.construir_datos(o, d, pcs, r, "delta", "deficit")
    return dat, x, n_cero


def reajuste_tibio(dat, mod0):
    """Reajuste tibio desde mod0 con la tolerancia refinada de D-017 / D-021."""
    for v, c in enumerate(dat.ncat):
        assert mod0.theta[v].shape[1] == c, "las categorías del escenario no coinciden con el ajuste K=5"
    return MM.ajustar(dat, mod0, tol=MM.TOL_REFINA, maxit=MM.MAXIT_REFINA)


# ---------------------------------------------------------------- D-030 · población objetivo
def comparar_objetivos(cel_p, cel_s, ln24):
    """Fracción de la LN 2024 del objetivo principal que sigue en el objetivo del escenario; Jaccard ponderado por
    LN 2024; nº de celdas y LN de cada objetivo. `ln24` Series indexada por LLAVE (ausentes = 0)."""
    A = cel_p.index[cel_p.objetivo.to_numpy()]
    Bs = cel_s.index[cel_s.objetivo.to_numpy()]
    inter, union = A.intersection(Bs), A.union(Bs)
    ln = lambda idx: float(np.nan_to_num(ln24.reindex(idx).to_numpy(float)).sum())
    lA, lI, lU = ln(A), ln(inter), ln(union)
    return dict(celdas_principal=len(A), celdas_escenario=len(Bs), celdas_interseccion=len(inter), celdas_union=len(union),
                ln_principal=lA, ln_escenario=ln(Bs), frac_ln_sigue=lI / lA if lA > 0 else np.nan,
                jaccard_ln=lI / lU if lU > 0 else np.nan)


def spearman_delta(cel_p, cel_s, n24):
    """Spearman ponderada (peso n_2024 principal) de δ̃ escenario vs principal en las celdas comunes con peso > 0."""
    j = cel_p[["delta"]].join(cel_s[["delta"]], how="inner", lsuffix="_p", rsuffix="_s")
    j["w"] = n24.reindex(j.index).to_numpy(float)
    j = j[(j.w > 0) & j.delta_p.notna() & j.delta_s.notna()]
    return B.spearman_ponderada(j.delta_p, j.delta_s, j.w), len(j)


# ---------------------------------------------------------------- D-030 · cruce y regla de mayoría
def cruce_y_regla(perfil_ref, clase_esc, w, K, umbral=None):
    """perfil_ref y clase_esc en 0..K-1 (celdas comunes), pesos w. Devuelve dict con: cruce (K×K, filas = clase del escenario,
    columnas = perfil principal), mapa Hungarian clase→perfil, % por fila, y por clase (perfil dominante, cuota, cumple).
    cumple = cuota > umbral (estrictamente más de la mitad, D-030). Global = todas las clases cumplen."""
    umbral = C.SENS_MAYORIA if umbral is None else umbral
    mapa, cruce = CF.reetiquetar(perfil_ref, clase_esc, w, K)
    tot = cruce.sum(1)
    cuota = np.divide(cruce, tot[:, None], out=np.zeros_like(cruce), where=tot[:, None] > 0)
    dom = cuota.argmax(1)
    cumple = cuota.max(1) > umbral
    return dict(cruce=cruce, mapa=mapa, pct_fila=100 * cuota, dominante=dom, cuota=cuota.max(1), cumple=cumple,
                global_cumple=bool(cumple.all()), peso_clase=tot)


def pct_deficit_por_perfil(deficit, perfil, K):
    """% del déficit positivo (D-022) de cada perfil 1..K."""
    d = np.maximum(np.asarray(deficit, float), 0.0)
    s = np.array([d[np.asarray(perfil) == p].sum() for p in range(1, K + 1)])
    return 100 * s / s.sum()


# ---------------------------------------------------------------- D-030 · observado − esperado por perfil y elección
def tabla_perfil_eleccion(p, perfil, q_main, q_k):
    """p: panel preparado 'concurrencia' (sv, n, k). perfil: DataFrame LLAVE + perfil (una fila por celda objetivo).
    Por perfil y elección: participación observada = Σsv/Σn, esperada principal = Σ n q_gse/Σn, esperada con
    concurrencia = Σ n q_gsek/Σn, y diferencias en puntos."""
    p = p[p.n > 0]
    n0 = len(p)
    p = p[LLAVE + ["aelec", "sv", "n", "k"]].merge(perfil[LLAVE + ["perfil"]], on=LLAVE, how="inner", validate="m:1")
    p = p.merge(q_main.rename(columns={"q": "q_main"}), on=ESTRATO + ["aelec"], how="left", validate="m:1")
    p = p.merge(q_k.rename(columns={"q": "q_k"}), on=ESTRATO + ["aelec", "k"], how="left", validate="m:1")
    assert p.q_main.notna().all() and p.q_k.notna().all() and 0 < len(p) <= n0
    n = p.n.astype("float64")
    p["n"], p["sv"] = n, p.sv.astype("float64")
    p["e_main"], p["e_k"] = n * p.q_main, n * p.q_k
    g = p.groupby(["perfil", "aelec"], observed=True)[["sv", "n", "e_main", "e_k"]].sum().reset_index()
    t = pd.DataFrame(dict(perfil=g.perfil, aelec=g.aelec, obs=100 * g.sv / g.n, esp_principal=100 * g.e_main / g.n,
                          esp_concurrencia=100 * g.e_k / g.n))
    t["dif_principal"] = t.obs - t.esp_principal
    t["dif_concurrencia"] = t.obs - t.esp_concurrencia
    t["efecto_calendario"] = t.esp_principal - t.esp_concurrencia
    return t


def intermedias_menos_presidenciales(t, inter=None, pres=None):
    """Por perfil: media de (obs − esperada) en intermedias menos la de presidenciales, con ambas esperadas (D-030)."""
    inter = C.SENS_ELECCIONES_INTERMEDIAS if inter is None else inter
    pres = C.SENS_ELECCIONES_PRESIDENCIALES if pres is None else pres
    filas = []
    for perfil, g in t.groupby("perfil"):
        f = dict(perfil=perfil)
        for col, nom in (("dif_principal", "principal"), ("dif_concurrencia", "concurrencia")):
            mi = g.loc[g.aelec.isin(inter), col].mean()
            mp = g.loc[g.aelec.isin(pres), col].mean()
            f[f"inter_{nom}"], f[f"pres_{nom}"], f[f"inter_menos_pres_{nom}"] = mi, mp, mi - mp
        f["calendario_pts"] = f["inter_menos_pres_principal"] - f["inter_menos_pres_concurrencia"]
        f["calendario_pct"] = (100 * f["calendario_pts"] / f["inter_menos_pres_principal"]
                               if f["inter_menos_pres_principal"] != 0 else np.nan)
        filas.append(f)
    return pd.DataFrame(filas)
