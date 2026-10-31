"""Mezcla de clases latentes con variables mixtas y pesos (D-024).

Independencia local dentro de cada clase: multinomial por variable categorica y normal con
varianza diagonal por variable continua. EM ponderado por w (D-024): la logL ponderada queda
en unidades de celda si sum(w) = n. Las continuas faltantes se marginan (la fila no aporta a esa
dimension, D-024). Reinicios y convergencia: reglas de D-017 (D-024).
Tambien incluye el PCA ponderado con analisis paralelo de Horn (D-024).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
from scipy.special import logsumexp

# --- Elecciones de computo (D-017 / D-024; no son parametros del modelo)
TOL_EXPLORA = 1e-7       # D-017: exploracion, mejora relativa de logL
TOL_REFINA = 1e-10       # D-017 (correccion): refinamiento de TODOS los reinicios
MAXIT_EXPLORA = 500      # tope de iteraciones de exploracion (se reporta si se alcanza)
MAXIT_REFINA = 3000      # D-017 correccion 2
MAX_REINICIOS = 10       # D-017
NATS_REPETICION = 1.0    # D-017: |dlogL| < 1 nat para considerar repetido el optimo
REPETICIONES = 2         # D-017: el mejor optimo debe verse >= 2 veces
# --- Protecciones numericas (declaradas; se reporta si se activan)
PISO_VAR_REL = 1e-6      # piso de varianza = 1e-6 x varianza global ponderada de la variable
PISO_PROB = 1e-12        # piso de probabilidades multinomiales y pesos de clase (evita log 0)


@dataclass
class Datos:
    """cat: (n, V) enteros 0..ncat[v]-1; X: (n, C) con NaN = faltante; w: (n,) pesos >= 0."""
    cat: np.ndarray
    ncat: tuple
    X: np.ndarray
    w: np.ndarray

    def __post_init__(self):
        self.cat = np.ascontiguousarray(self.cat, dtype=np.int64).reshape(len(self.w), -1)
        self.X = np.ascontiguousarray(self.X, dtype=np.float64).reshape(len(self.w), -1)
        self.w = np.ascontiguousarray(self.w, dtype=np.float64)
        self.ncat = tuple(int(c) for c in self.ncat)
        self.M = ~np.isnan(self.X)
        self.X0 = np.where(self.M, self.X, 0.0)
        # desplazamiento por la media global ponderada (solo estabilidad numerica de E[x^2]-m^2)
        sw = (self.M * self.w[:, None]).sum(axis=0)
        self.shift = np.where(sw > 0, (self.M * self.w[:, None] * self.X0).sum(axis=0) / np.where(sw > 0, sw, 1), 0.0)
        self.Xs = np.where(self.M, self.X0 - self.shift, 0.0)
        self.Xs2 = self.Xs ** 2
        self.Mf = self.M.astype(np.float64)
        # tablas por combinacion unica de categoricas (el log de la parte categorica se calcula una vez por combo)
        if self.cat.shape[1]:
            clave = np.zeros(len(self.w), dtype=np.int64)
            for v, c in enumerate(self.ncat):
                clave = clave * c + self.cat[:, v]
            self.combo_u, primero, self.combo = np.unique(clave, return_index=True, return_inverse=True)
            self.cat_u = self.cat[primero]
        else:
            self.combo = np.zeros(len(self.w), dtype=np.int64)
            self.cat_u = np.zeros((1, 0), dtype=np.int64)
        desp = np.concatenate([[0], np.cumsum(self.ncat)])[:-1] if self.ncat else np.array([], dtype=np.int64)
        self.desp = desp
        n, V = self.cat.shape
        if V:
            cols = (self.cat + desp[None, :]).ravel()
            filas = np.repeat(np.arange(n), V)
            self.onehot = sp.csr_matrix((np.ones(n * V), (filas, cols)), shape=(n, int(sum(self.ncat))))
        else:
            self.onehot = sp.csr_matrix((n, 0))

    @property
    def n(self):
        return len(self.w)

    @property
    def C(self):
        return self.X.shape[1]

    def subconjunto(self, filas):
        return Datos(self.cat[filas], self.ncat, self.X[filas], self.w[filas])

    def columnas(self, cols):
        return Datos(self.cat, self.ncat, self.X[:, cols], self.w)

    def n_cont_efectivas(self):
        return int(((self.M * self.w[:, None]).sum(axis=0) > 0).sum())


@dataclass
class Modelo:
    pi: np.ndarray            # (K,)
    theta: list               # V arrays (K, ncat_v)
    mu: np.ndarray            # (K, C)
    var: np.ndarray           # (K, C)

    @property
    def K(self):
        return len(self.pi)


@dataclass
class Ajuste:
    modelo: Modelo
    logL: float
    R: np.ndarray
    n_iter: int
    convergio: bool
    segundos: float
    historia: list = field(default_factory=list)
    pisos: int = 0            # veces que se activo el piso de varianza en la ultima M-step


def n_param(K, ncat, C_efectivas):
    """Parametros libres: (K-1) + K*sum(ncat-1) + 2*K*C continuas (D-024)."""
    return (K - 1) + K * int(sum(c - 1 for c in ncat)) + 2 * K * int(C_efectivas)


def _var_global(dat):
    """Varianza global ponderada por continua (base del piso)."""
    Wc = dat.M * dat.w[:, None]
    sw = Wc.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        m = (Wc * dat.X0).sum(axis=0) / sw
        v = (Wc * (dat.X0 - m) ** 2).sum(axis=0) / sw
    return np.where(sw > 0, v, 1.0)


# ----------------------------------------------------------------------------- E-step
def log_clases(dat, mod):
    """(n, K): log pi_k + log f(x_i | k) con continuas faltantes marginadas."""
    K = mod.K
    lp = np.zeros((dat.n, K)) + np.log(np.maximum(mod.pi, PISO_PROB))[None, :]
    if dat.cat.shape[1]:
        tab = np.zeros((len(dat.cat_u), K))
        for v in range(dat.cat.shape[1]):
            tab += np.log(mod.theta[v]).T[dat.cat_u[:, v]]
        lp += tab[dat.combo]
    if dat.C:
        mu = mod.mu - dat.shift[None, :]
        iv = 1.0 / mod.var
        lp += -0.5 * (dat.Mf @ np.log(2 * np.pi * mod.var).T + dat.Xs2 @ iv.T
                      - 2 * dat.Xs @ (mu * iv).T + dat.Mf @ (mu * mu * iv).T)
    return lp


def estep(dat, mod):
    lp = log_clases(dat, mod)
    mx = lp.max(axis=1)
    lp -= mx[:, None]
    np.exp(lp, out=lp)
    z = lp.sum(axis=1)
    ll = mx + np.log(z)
    R = lp / z[:, None]
    return R, float(np.dot(dat.w, ll))


# ----------------------------------------------------------------------------- M-step
def mstep(dat, R, vglob):
    K = R.shape[1]
    Rw = R * dat.w[:, None]
    sk = Rw.sum(axis=0)
    pi = np.maximum(sk / max(dat.w.sum(), 1e-300), PISO_PROB)
    pi = pi / pi.sum()
    theta = []
    if dat.cat.shape[1]:
        cnt = np.asarray((dat.onehot.T @ Rw)).T       # (K, sum ncat)
        for v, c in enumerate(dat.ncat):
            t = cnt[:, dat.desp[v]:dat.desp[v] + c]
            t = t / np.maximum(t.sum(axis=1, keepdims=True), 1e-300)
            t = np.maximum(t, PISO_PROB)
            theta.append(t / t.sum(axis=1, keepdims=True))
    sw = Rw.T @ dat.Mf                      # (K, C)
    ok = sw > 0
    den = np.where(ok, sw, 1.0)
    m1 = (Rw.T @ dat.Xs) / den              # media desplazada
    v = np.maximum((Rw.T @ dat.Xs2) / den - m1 * m1, 0.0)
    piso = PISO_VAR_REL * vglob[None, :]
    pisos = int((ok & (v < piso)).sum())
    mu = np.where(ok, m1 + dat.shift[None, :], 0.0)
    var = np.where(ok, np.maximum(v, piso), 1.0)
    return Modelo(pi, theta, mu, var), pisos


def ajustar(dat, mod0, tol=TOL_EXPLORA, maxit=MAXIT_EXPLORA, vglob=None):
    """EM ponderado desde mod0. Parada: mejora relativa de logL < tol (D-017)."""
    t0 = time.time()
    vglob = _var_global(dat) if vglob is None else vglob
    mod = mod0
    hist = []
    R, ll = estep(dat, mod)
    hist.append(ll)
    conv = False
    pisos = 0
    it = 0
    while it < maxit:
        mod, pisos = mstep(dat, R, vglob)
        R, ll2 = estep(dat, mod)
        it += 1
        hist.append(ll2)
        if abs(ll2 - ll) < tol * abs(ll2):
            ll = ll2
            conv = True
            break
        ll = ll2
    return Ajuste(mod, ll, R, it, conv, time.time() - t0, hist, pisos)


# ----------------------------------------------------------------------------- inicializacion
def _caracteristicas(dat):
    """Continuas estandarizadas (media/sd ponderadas; NaN -> 0) + one-hot, para k-means++."""
    sw = (dat.M * dat.w[:, None]).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        m = np.where(sw > 0, (dat.M * dat.w[:, None] * dat.X0).sum(axis=0) / sw, 0.0)
    sd = np.sqrt(_var_global(dat))
    sd = np.where(sd > 0, sd, 1.0)
    Z = np.where(dat.M, (dat.X0 - m) / sd, 0.0)
    return np.hstack([Z, dat.onehot.toarray()])


def inicializar(dat, K, rng, F=None):
    """k-means++ ponderado (D^2 x w) -> asignacion dura -> M-step (D-017, D-024)."""
    F = _caracteristicas(dat) if F is None else F
    n = dat.n
    p = dat.w / dat.w.sum()
    centros = [rng.choice(n, p=p)]
    d2 = ((F - F[centros[0]]) ** 2).sum(axis=1)
    for _ in range(1, K):
        q = dat.w * d2
        if q.sum() <= 0:
            q = dat.w.copy()
        j = rng.choice(n, p=q / q.sum())
        centros.append(j)
        d2 = np.minimum(d2, ((F - F[j]) ** 2).sum(axis=1))
    C = F[centros]
    dist = (F ** 2).sum(1)[:, None] - 2 * F @ C.T + (C ** 2).sum(1)[None, :]
    asig = dist.argmin(axis=1)
    R = np.zeros((n, K))
    R[np.arange(n), asig] = 1.0
    mod, _ = mstep(dat, R, _var_global(dat))
    return mod


def ajustar_con_reinicios(dat, K, rng, max_reinicios=MAX_REINICIOS, log=None):
    """D-017 (corregida): cada reinicio se explora a TOL_EXPLORA y se refina a TOL_REFINA;
    se para cuando la mejor logL se repite >= REPETICIONES veces con |dlogL| < 1 nat.
    Devuelve (mejor Ajuste, info dict)."""
    t0 = time.time()
    vglob = _var_global(dat)
    F = _caracteristicas(dat) if K > 1 else None
    res = []
    if K == 1:
        a = ajustar(dat, inicializar(dat, 1, rng, F=np.zeros((dat.n, 1))), TOL_REFINA, MAXIT_REFINA, vglob)
        return a, dict(logLs=[a.logL], repeticiones=1, reinicios=1, no_convergio=int(not a.convergio),
                       segundos=time.time() - t0, pisos=a.pisos, repetido=True)
    for r in range(max_reinicios):
        a = ajustar(dat, inicializar(dat, K, rng, F), TOL_EXPLORA, MAXIT_EXPLORA, vglob)
        a = ajustar(dat, a.modelo, TOL_REFINA, MAXIT_REFINA, vglob)
        res.append(a)
        mejor = max(x.logL for x in res)
        rep = sum(abs(x.logL - mejor) < NATS_REPETICION for x in res)
        if log:
            log(f"    K={K} reinicio {r + 1}: logL={a.logL:.2f} it={a.n_iter} conv={a.convergio} mejor={mejor:.2f} rep={rep}")
        if rep >= REPETICIONES:
            break
    mejor = max(res, key=lambda x: x.logL)
    rep = sum(abs(x.logL - mejor.logL) < NATS_REPETICION for x in res)
    info = dict(logLs=[x.logL for x in res], repeticiones=rep, reinicios=len(res),
                no_convergio=int(sum(not x.convergio for x in res)), segundos=time.time() - t0,
                pisos=mejor.pisos, repetido=rep >= REPETICIONES)
    return mejor, info


# ----------------------------------------------------------------------------- criterios
def entropia(R, w):
    """Entropia ponderada -sum w_i sum_k R_ik log R_ik."""
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(R > 0, R * np.log(R), 0.0)
    return float(-(w * t.sum(axis=1)).sum())


def criterios(ajuste, dat):
    """BIC = -2 logL + p ln N e ICL = BIC + 2 entropia (menor es mejor). N = numero de celdas,
    logL ponderada en unidades de celda (D-024)."""
    K = ajuste.modelo.K
    p = n_param(K, dat.ncat, dat.n_cont_efectivas())
    bic = -2 * ajuste.logL + p * np.log(dat.n)
    ent = entropia(ajuste.R, dat.w)
    return dict(K=K, logL=ajuste.logL, n_param=p, BIC=bic, entropia=ent, ICL=bic + 2 * ent)


def clasificar(dat, mod):
    """MAP, probabilidad maxima y responsabilidades."""
    R, _ = estep(dat, mod)
    return R.argmax(axis=1), R.max(axis=1), R


# ----------------------------------------------------------------------------- PCA ponderado + Horn
def estandarizar_ponderado(X, w):
    """Media y sd ponderadas (ignorando NaN por columna). Devuelve (Z con NaN, media, sd)."""
    X = np.asarray(X, float)
    M = ~np.isnan(X)
    Wc = M * w[:, None]
    sw = Wc.sum(axis=0)
    m = (Wc * np.where(M, X, 0)).sum(axis=0) / sw
    sd = np.sqrt((Wc * (np.where(M, X, 0) - m) ** 2).sum(axis=0) / sw)
    return (X - m) / sd, m, sd


def valores_propios_ponderados(Z, w):
    """Valores y vectores propios (descendentes) de la covarianza ponderada de Z."""
    mz = (Z * w[:, None]).sum(axis=0) / w.sum()
    Zc = Z - mz
    cov = (Zc * w[:, None]).T @ Zc / w.sum()
    val, vec = np.linalg.eigh(cov)
    o = np.argsort(val)[::-1]
    return val[o], vec[:, o]


def analisis_paralelo(Z, w, rng, bloque=20, r_max=1000, factor_ee=2.0, log=None):
    """Horn (D-024): permuta cada columna por separado, recalcula los valores propios.
    R secuencial (D-017 adaptada): se agregan bloques hasta que, en todos los componentes,
    factor_ee x EE Monte Carlo de la media permutada < |observado - media permutada|, o hasta r_max.
    Devuelve dict con obs, media, ee, R, n_retenidos, parado_por_tope."""
    obs, _ = valores_propios_ponderados(Z, w)
    perm = []
    parado = False
    while True:
        for _ in range(bloque):
            Zp = np.column_stack([rng.permutation(Z[:, j]) for j in range(Z.shape[1])])
            perm.append(valores_propios_ponderados(Zp, w)[0])
        P = np.array(perm)
        media = P.mean(axis=0)
        ee = P.std(axis=0, ddof=1) / np.sqrt(len(P))
        if log:
            log(f"    Horn R={len(P)}")
        if np.all(factor_ee * ee < np.abs(obs - media)):
            break
        if len(P) >= r_max:
            parado = True
            break
    # se retienen los primeros componentes consecutivos (los valores propios son decrecientes)
    ret = int(np.argmax(~(obs > media))) if np.any(~(obs > media)) else len(obs)
    return dict(obs=obs, media=media, ee=ee, R=len(P), n_retenidos=ret, tope=parado)
