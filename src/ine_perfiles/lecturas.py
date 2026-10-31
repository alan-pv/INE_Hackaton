"""Pruebas de las lecturas de cada perfil (D-034). Lógica reutilizable y testeable.

Unidad: las secciones donde el perfil es mayoritario (D-034): LN 2024 de las celdas objetivo ponderada por la
responsabilidad del perfil / LN 2024 total de la sección > 1/2. Se usan todas las celdas de la sección (objetivo o no).
Inferencia: bootstrap de municipios (edo, mpio) con reemplazo, estratificado por estado (D-032), percentil (D-027).
Una asociación entre secciones es contextual, no individual (D-010).
"""
import numpy as np
import pandas as pd

from . import brecha as B

UMBRAL_MAYORIA = 0.5   # D-034: "mayor a 1/2" (mayoría simple; no es un parámetro estimado)


# ---------------------------------------------------------------- pertenencia (D-034)
def pertenencia(obj, ln_sec, k_perfiles):
    """obj: celdas objetivo con edo, seccion, ln_2024 y resp_perfil_1..K. ln_sec: Series/DataFrame con
    (edo, seccion, ln_tot) = LN 2024 total de la sección. Devuelve DataFrame por sección con ln_perfil_k,
    frac_k y `perfil_may` (0 si ningún perfil supera 1/2; como las fracciones suman <= 1 solo uno puede)."""
    g = obj[["edo", "seccion"]].copy()
    for k in range(1, k_perfiles + 1):
        g[f"ln_perfil_{k}"] = obj[f"resp_perfil_{k}"].to_numpy(float) * obj["ln_2024"].to_numpy(float)
    g = g.groupby(["edo", "seccion"], as_index=False).sum()
    s = ln_sec.merge(g, on=["edo", "seccion"], how="left").fillna(0.0)
    tot = s["ln_tot"].to_numpy(float)
    may = np.zeros(len(s), int)
    for k in range(1, k_perfiles + 1):
        s[f"frac_{k}"] = np.divide(s[f"ln_perfil_{k}"], tot, out=np.zeros(len(s)), where=tot > 0)
        may[s[f"frac_{k}"].to_numpy() > UMBRAL_MAYORIA] = k
    s["perfil_may"] = may
    return s


# ---------------------------------------------------------------- brecha por sección y grupo (D-034)
def brecha_seccion(cel, sexos=None, grupos=None, col="delta"):
    """Media ponderada de delta (peso `w`) por sección (edo, seccion) de las celdas del grupo (sexos, grupos).
    cel: DataFrame con edo, seccion, sexo, grupo, delta, w. Devuelve DataFrame (edo, seccion, brecha, w_sum);
    brecha = NaN si el peso total es 0."""
    m = np.ones(len(cel), bool)
    if sexos is not None:
        m &= cel["sexo"].isin(list(sexos)).to_numpy()
    if grupos is not None:
        m &= cel["grupo"].isin(list(grupos)).to_numpy()
    m &= cel[col].notna().to_numpy()      # celdas sin la medida no pesan (D-034: log(O/E) exige sv>0 y E>0)
    c = cel.loc[m, ["edo", "seccion", col, "w"]].copy()
    c["wd"] = c[col].to_numpy(float) * c["w"].to_numpy(float)
    g = c.groupby(["edo", "seccion"], as_index=False)[["wd", "w"]].sum()
    g["brecha"] = np.where(g["w"] > 0, g["wd"] / g["w"].where(g["w"] > 0, 1.0), np.nan)
    return g.rename(columns={"w": "w_sum"})[["edo", "seccion", "brecha", "w_sum"]]


def contraste_seccion(cel, A, Bg, col="delta"):
    """Contraste dentro de sección: brecha(A) - brecha(B) por sección; A y B son dict(sexos=, grupos=).
    Solo secciones donde ambos grupos tienen peso > 0 (D-034). Devuelve DataFrame (edo, seccion, contraste)."""
    a = brecha_seccion(cel, col=col, **A).rename(columns={"brecha": "a"})[["edo", "seccion", "a"]]
    b = brecha_seccion(cel, col=col, **Bg).rename(columns={"brecha": "b"})[["edo", "seccion", "b"]]
    m = a.merge(b, on=["edo", "seccion"], how="inner")
    m["contraste"] = m["a"] - m["b"]
    return m.dropna(subset=["contraste"])[["edo", "seccion", "contraste"]]


# ---------------------------------------------------------------- bootstrap de municipios
def multiplicidades(estrato_mun, B_rep, rng):
    """Matriz (B_rep, n_mun) de multiplicidades: dentro de cada estrato se extraen n_estrato municipios
    con reemplazo (D-032, estratificado por estado). Cada fila suma, por estrato, el tamaño del estrato."""
    estrato_mun = np.asarray(estrato_mun)
    n = len(estrato_mun)
    M = np.zeros((B_rep, n), np.int16)
    for e in np.unique(estrato_mun):
        idx = np.flatnonzero(estrato_mun == e)
        d = rng.integers(0, len(idx), size=(B_rep, len(idx)))
        for b in range(B_rep):
            M[b, idx] = np.bincount(d[b], minlength=len(idx))
    return M


def indices_municipio(df):
    """Índice entero de municipio (edo, mpio) por fila de df y el estrato (edo) de cada municipio."""
    key = df["edo"].astype("int64") * 10000 + df["mpio"].astype("int64")
    u, inv = np.unique(key.to_numpy(), return_inverse=True)
    return inv, (u // 10000)


def media_ponderada_por_mun(valor, peso, mun, n_mun, mask):
    """Resumen por municipio de una media ponderada sobre las filas en `mask`: (num, den) de longitud n_mun.
    La media bootstrap de una réplica es (M @ num)/(M @ den)."""
    v = np.asarray(valor, float)[mask]; w = np.asarray(peso, float)[mask]; mu = mun[mask]
    num = np.bincount(mu, weights=v * w, minlength=n_mun)
    den = np.bincount(mu, weights=w, minlength=n_mun)
    return num, den


def razon_boot(M, num, den):
    """(M @ num)/(M @ den) para todas las réplicas; NaN si el denominador es 0."""
    d = M @ den
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(d > 0, (M @ num) / d, np.nan)


def ic_percentil(reps, nivel):
    """Intervalo percentil de las réplicas (ignora NaN)."""
    r = np.asarray(reps, float); r = r[np.isfinite(r)]
    a = (1 - nivel) / 2
    return float(np.quantile(r, a)), float(np.quantile(r, 1 - a))


def spearman_boot(x, y, w, mun, M):
    """Spearman ponderada en cada réplica: peso = w * multiplicidad del municipio de la sección."""
    out = np.full(M.shape[0], np.nan)
    for b in range(M.shape[0]):
        wb = w * M[b, mun]
        k = wb > 0
        if k.sum() > 2:
            out[b] = B.spearman_ponderada(x[k], y[k], wb[k])
    return out


def mediana_ponderada(x, w):
    """Mediana ponderada (primer valor cuya cdf ponderada alcanza 1/2)."""
    x = np.asarray(x, float); w = np.asarray(w, float)
    k = (w > 0) & np.isfinite(x)
    if not k.any():
        return np.nan
    o = np.argsort(x[k]); xs = x[k][o]; c = np.cumsum(w[k][o])
    return float(xs[np.searchsorted(c, 0.5 * c[-1])])


def mediana_boot(x, w, mun, M):
    out = np.full(M.shape[0], np.nan)
    for b in range(M.shape[0]):
        out[b] = mediana_ponderada(x, w * M[b, mun])
    return out


# ---------------------------------------------------------------- veredictos (D-034)
def veredicto_prediccion(valor, lo, hi, signo):
    """'se cumple' si el signo es el predicho y el IC excluye 0; 'contraria' si el signo es opuesto y el IC
    excluye 0; si no, 'no se cumple'. signo = +1 / -1 (D-034)."""
    if not np.isfinite(valor):
        return "no se cumple"
    excluye = (lo > 0) or (hi < 0)
    if excluye and np.sign(valor) == signo:
        return "se cumple"
    if excluye and np.sign(valor) == -signo:
        return "contraria"
    return "no se cumple"


def veredicto_lectura(vs):
    """respaldada (todas se cumplen) / parcial (algunas) / no respaldada (ninguna) (D-034)."""
    vs = list(vs)
    if not vs:
        return "sin pruebas"
    c = sum(v == "se cumple" for v in vs)
    return "respaldada" if c == len(vs) else ("no respaldada" if c == 0 else "parcial")


# ---------------------------------------------------------------- tendencia (D-034 P1 ii)
def pendiente_mco(y, x):
    """Pendiente MCO de y contra x por fila: y (R, T) -> (R,)."""
    x = np.asarray(x, float); xc = x - x.mean()
    return (np.asarray(y, float) @ xc) / (xc @ xc)


def veredicto_combinado(v_delta, v_log):
    """D-034 (agregado): si las dos medidas (δ̃ y log(O/E) crudo de 2024) dan el mismo veredicto se queda;
    si no, 'no concluyente' (no cuenta ni a favor ni en contra)."""
    return v_delta if v_delta == v_log else "no concluyente"


def veredicto_lectura_concluyente(vs):
    """Como veredicto_lectura pero ignora 'no concluyente'. respaldada = todos los concluyentes se cumplen y ninguno
    es contrario; parcial = alguno se cumple; no respaldada = ninguno se cumple."""
    vs = [v for v in vs if v != "no concluyente"]
    if not vs:
        return "sin pruebas concluyentes"
    c = sum(v == "se cumple" for v in vs)
    return "respaldada" if c == len(vs) else ("no respaldada" if c == 0 else "parcial")
