"""Datos y ajuste de la mezcla de clases latentes sobre la población objetivo (D-017, D-024, D-029).

Lo comparten los scripts de perfiles: PCA ponderado del contexto con análisis paralelo de Horn, construcción
de los datos de la mezcla, ajuste con reinicios, estabilidad por bootstrap de secciones, prueba contra el azar
y descripción de los perfiles. Los procesos trabajadores (fork) leen el estado de este módulo: antes de usarlos,
cada script fija `DAT`, `BOOT`, `INT` y `N_PROC`.
"""
import pickle
import time

import numpy as np
import pandas as pd

from ine_perfiles import config as C
from ine_perfiles import descriptores as D
from ine_perfiles import estabilidad as EST
from ine_perfiles import mezcla_mixta as MM

CATS = ["sexo", "grupo", "circunscripcion", "tiposec"]   # D-024: variables categóricas del modelo
B_MIN, EE_MAX, B_TOPE = 20, 0.025, 200                    # D-017: réplicas mínimas, error Monte Carlo máximo, tope
N_FRIO = 5                                                # D-017: réplicas de control con arranque en frío
UMBRAL_CONF = 0.9                                         # solo descriptivo: % de celdas con probabilidad máxima ≥ 0.9

# estado que leen los procesos trabajadores
INT = C.INTERIM / "seleccion_numero_perfiles"             # caché (cada script puede apuntarla a la suya)
N_PROC = 4                                                # procesos en paralelo (no cambia ningún resultado)
REHACER = False
DAT = None
BOOT = {}
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.0f}s]", *a, flush=True)


def cache(nombre, f):
    ruta = INT / nombre
    if ruta.exists() and not REHACER:
        with open(ruta, "rb") as fh:
            return pickle.load(fh)
    r = f()
    with open(ruta, "wb") as fh:
        pickle.dump(r, fh)
    return r


# ---------------------------------------------------------------- datos, PCA y Horn (D-024)
def preparar():
    b = pd.read_parquet(C.PROCESADOS / "brecha_celda.parquet")
    o = b[b["objetivo"]].reset_index(drop=True)
    d = pd.read_parquet(C.PROCESADOS / "descriptores_seccion.parquet")
    cols = D.COLS_CONTEXTO
    X = d[cols].to_numpy(float)
    wln = d["ln_2024"].to_numpy(float)
    comp = ~np.isnan(X).any(axis=1)
    Zc, mu, sd = MM.estandarizar_ponderado(X[comp], wln[comp])
    val, vec = MM.valores_propios_ponderados(Zc, wln[comp])
    horn = MM.analisis_paralelo(Zc, wln[comp], np.random.default_rng([C.SEMILLA, 1]), log=log)
    r = horn["n_retenidos"]
    # proyección de todas las secciones; faltantes estandarizados = 0 (la media)
    Zall = np.where(np.isnan(X), 0.0, (X - mu) / sd)
    pcs = Zall @ vec[:, :r]
    # signo: la mayor carga absoluta de cada componente, positiva
    for j in range(r):
        if vec[np.argmax(np.abs(vec[:, j])), j] < 0:
            vec[:, j] *= -1
            pcs[:, j] *= -1
    return dict(o=o, d=d, cols=cols, comp=comp, val=val, vec=vec, horn=horn, r=r, pcs=pcs,
                n_incompletas=int((~comp).sum()), n_sec=len(d),
                var_exp=val / val.sum())


def construir(P):
    o, d, r = P["o"], P["d"], P["r"]
    sec = d[["edo", "seccion", "tiposec", "circunscripcion"]].copy()
    for j in range(r):
        sec[f"pc{j + 1}"] = P["pcs"][:, j]
    x = o[["edo", "seccion", "sexo", "grupo", "delta", "deficit", "deficit_2024_crudo", "ln_2024"]].merge(
        sec, on=["edo", "seccion"], how="left", validate="m:1")
    assert len(x) == len(o) and x["circunscripcion"].notna().all()
    assert (x["sexo"].to_numpy() == o["sexo"].to_numpy()).all()        # mismo orden de filas
    w = np.maximum(x["deficit"].to_numpy(float), 0.0)                   # D-024: ponderada por votos faltantes
    n_cero = int((w == 0).sum())
    w = w * len(w) / w.sum()
    cat, etiquetas, ncat = [], {}, []
    for c in CATS:
        cod, uniq = pd.factorize(x[c].astype("object").where(x[c].notna(), "NaN"), sort=True)
        cat.append(cod)
        etiquetas[c] = list(uniq)
        ncat.append(len(uniq))
    nombres_cont = ["delta"] + [f"pc{j + 1}" for j in range(r)]
    Xc = x[nombres_cont].to_numpy(float)
    dat = MM.Datos(np.column_stack(cat), tuple(ncat), Xc, w)
    return dat, x, etiquetas, nombres_cont, n_cero


# ---------------------------------------------------------------- trabajadores (D-017, D-029)
def tarea_ajuste(K):
    rng = np.random.default_rng([C.SEMILLA, 2, K])
    a, info = MM.ajustar_con_reinicios(DAT, K, rng, log=log)
    return K, a.modelo, a.logL, info


def tarea_boot(args):
    K, b, modelo, mapa = args
    rng = np.random.default_rng([C.SEMILLA, 3, K, b])
    filas, _ = EST.remuestrear_secciones(rng, BOOT["edo_sec"], BOOT["orden"], BOOT["inicio"], BOOT["largo"])
    sub = DAT.subconjunto(filas)
    uni, pos = np.unique(filas, return_index=True)
    t0 = time.time()
    a = MM.ajustar(sub, modelo, MM.TOL_REFINA, MM.MAXIT_REFINA)
    mp = MM.clasificar(sub, a.modelo)[0]
    jt = EST.jaccard_por_clase(mapa[uni], mp[pos], K)
    out = dict(K=K, b=b, jt=jt, it_t=a.n_iter, conv_t=a.convergio, seg_t=time.time() - t0)
    if b < N_FRIO:
        t1 = time.time()
        a0 = MM.ajustar(sub, MM.inicializar(sub, K, rng), MM.TOL_EXPLORA, MM.MAXIT_EXPLORA)
        a0 = MM.ajustar(sub, a0.modelo, MM.TOL_REFINA, MM.MAXIT_REFINA)
        mf = MM.clasificar(sub, a0.modelo)[0]
        out.update(jf=EST.jaccard_por_clase(mapa[uni], mf[pos], K), logL_t=a.logL, logL_f=a0.logL,
                   it_f=a0.n_iter, seg_f=time.time() - t1)
    return out


def tarea_nulo(args):
    K, b = args
    rng = np.random.default_rng([C.SEMILLA, 4, K, b])
    cat = np.column_stack([rng.permutation(DAT.cat[:, v]) for v in range(DAT.cat.shape[1])])
    X = np.column_stack([rng.permutation(DAT.X[:, c]) for c in range(DAT.C)])
    d = MM.Datos(cat, DAT.ncat, X, DAT.w)          # w queda con su celda
    t0 = time.time()
    a1, _ = MM.ajustar_con_reinicios(d, 1, rng)
    aK, info = MM.ajustar_con_reinicios(d, K, rng)
    return dict(K=K, b=b, G=aK.logL - a1.logL, logL1=a1.logL, logLK=aK.logL, rep=info["repetido"],
                reinicios=info["reinicios"], seg=time.time() - t0)


def estabilidad(K, modelo, mapa, pool):
    """Réplicas bootstrap en bloques de N_PROC hasta que el error Monte Carlo sea ≤ EE_MAX (D-017)."""
    res, b = [], 0
    while True:
        lote = [(bb, INT / f"boot_K{K}_b{bb}.pkl") for bb in range(b, b + N_PROC)]
        pend = [(K, bb, modelo, mapa) for bb, ruta in lote if REHACER or not ruta.exists()]
        if pend:
            for r in pool.map(tarea_boot, pend):
                with open(INT / f"boot_K{K}_b{r['b']}.pkl", "wb") as fh:
                    pickle.dump(r, fh)
        for bb, ruta in lote:
            with open(ruta, "rb") as fh:
                res.append(pickle.load(fh))
        b += N_PROC
        J = np.array([r["jt"] for r in res])
        ee = EST.ee_monte_carlo(J) if len(J) > 1 else np.full(K, np.inf)
        log(f"  bootstrap K={K}: B={len(res)}  EE max={ee.max():.4f}")
        if len(res) >= B_MIN and ee.max() <= EE_MAX:
            return res, False
        if len(res) >= B_TOPE:
            return res, True


def prueba_azar(K, pool, B=None):
    """Prueba contra el azar con B permutaciones (por omisión C.B_NULO, D-029); retoma desde la caché."""
    tareas = [(K, b) for b in range(C.B_NULO if B is None else B)]
    pend = [t for t in tareas if REHACER or not (INT / f"nulo_K{t[0]}_b{t[1]}.pkl").exists()]
    for r in pool.imap_unordered(tarea_nulo, pend):
        with open(INT / f"nulo_K{K}_b{r['b']}.pkl", "wb") as fh:
            pickle.dump(r, fh)
        log(f"   nulo K={K} b={r['b']}: G={r['G']:.1f} ({r['seg']:.0f}s)")
    sal = []
    for t in tareas:
        with open(INT / f"nulo_K{t[0]}_b{t[1]}.pkl", "rb") as fh:
            sal.append(pickle.load(fh))
    return sal


# ---------------------------------------------------------------- descripción de los perfiles
def perfiles(K, a, x, etiquetas, P):
    """Tabla de perfiles (ordenados por % del déficit), composición y asignación de cada celda."""
    R = a.R
    w = DAT.w
    Rw = R * w[:, None]
    mapa = R.argmax(axis=1)
    pmax = R.max(axis=1)
    deficit_k = Rw.sum(axis=0)
    orden = np.argsort(-deficit_k)
    pos = {int(k): i + 1 for i, k in enumerate(orden)}            # perfil 1 = mayor % del déficit
    crudo = np.nan_to_num(np.maximum(x["deficit_2024_crudo"].to_numpy(float), 0))
    ln = x["ln_2024"].to_numpy(float)
    delta = x["delta"].to_numpy(float)
    ctxs = P["d"][["edo", "seccion"] + P["cols"]]
    ctx = x[["edo", "seccion"]].merge(ctxs, on=["edo", "seccion"], how="left")
    filas, comp = [], []
    for k in orden:
        r = R[:, k]
        rw = Rw[:, k]
        f = dict(perfil=pos[int(k)], clase=int(k), pct_deficit=100 * rw.sum() / w.sum(), celdas=r.sum(),
                 ln_2024_miles=np.dot(r, np.nan_to_num(ln)) / 1e3,
                 delta_medio=np.dot(rw, delta) / rw.sum(),
                 deficit_crudo_2024_pos=np.dot(r, crudo), pct_crudo_2024=100 * np.dot(r, crudo) / crudo.sum(),
                 pmax_media=pmax[mapa == k].mean(), pct_pmax_ge_09=100 * (pmax[mapa == k] >= UMBRAL_CONF).mean())
        for c in D.COLS_CONTEXTO:
            f["med_" + c] = D.cuantil_ponderado(ctx[c].to_numpy(float), rw, [0.5])[0]
        filas.append(f)
        for c in CATS:
            for j, e in enumerate(etiquetas[c]):
                m = (DAT.cat[:, CATS.index(c)] == j)
                pk = rw[m].sum() / rw.sum()
                pg = w[m].sum() / w.sum()
                comp.append(dict(perfil=pos[int(k)], variable=c, categoria=e, pct=100 * pk, razon=pk / pg))
    return pd.DataFrame(filas), pd.DataFrame(comp), pos, mapa, pmax


def md_tabla(df, fmt=None):
    """Tabla en Markdown para los reportes de control."""
    fmt = fmt or {}
    cab = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    cuerpo = ""
    for _, r in df.iterrows():
        cel = []
        for c in df.columns:
            v = r[c]
            f = fmt.get(c, "{}")
            if isinstance(v, str):
                cel.append(v)
            else:
                try:
                    cel.append(f.format(v))
                except ValueError:
                    cel.append(f.format(int(v)))
        cuerpo += "| " + " | ".join(cel) + " |\n"
    return cab + cuerpo
