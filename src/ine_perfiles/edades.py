"""Estimación de cortes de edad (D-007): regresión lineal por tramos continua (hinge)
sobre el logit de participación por edad simple, mínimos cuadrados ponderados (w = n).
Convención: corte = primera edad del nuevo tramo."""
from itertools import combinations
import numpy as np

REINICIOS = 20  # reinicios aleatorios del refinamiento (costo de cómputo; semilla fija)
SEMILLA = 20261031
K_MAX = 8  # D-007 (rango explorado de cortes; k se elige por CV-LOEO + 1-SE)


def logit(p):
    return np.log(p / (1 - p))


def curva_por_edad(con, aelec, sexos=(0, 1)):
    """Curva nacional por edad simple: edad, n=SV+NV, p=SV/n. Excluye p en {0,1}.
    Devuelve (edad, n, y=logit(p), edades_excluidas)."""
    s = ",".join(str(int(x)) for x in sexos)
    filas = con.execute(
        f"SELECT edad, sum(sv+nv) AS n, sum(sv) AS sv FROM ccpc "
        f"WHERE aelec={int(aelec)} AND sexo IN ({s}) GROUP BY edad HAVING sum(sv+nv)>0 "
        f"ORDER BY edad").fetchall()
    edad = np.array([f[0] for f in filas], float)
    n = np.array([f[1] for f in filas], float)
    p = np.array([f[2] for f in filas], float) / n
    ok = (p > 0) & (p < 1)
    return edad[ok], n[ok], logit(p[ok]), [int(e) for e in edad[~ok]]


def centrar(y, w):
    """Quita el nivel de la elección (efecto periodo, D-007): y - media ponderada."""
    return y - np.average(y, weights=w)


def _base(x, cortes):
    cols = [np.ones_like(x), x] + [np.maximum(x - b, 0.0) for b in cortes]
    return np.column_stack(cols)


def ajustar_fijos(x, y, w, cortes):
    """MCP ponderados con cortes fijos. Devuelve (coef, SSE ponderada)."""
    X = _base(x, cortes)
    sw = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    r = y - X @ coef
    return coef, float(np.sum(w * r * r))


def _sse(x, y, w, cortes):
    return ajustar_fijos(x, y, w, cortes)[1]


def candidatos(x):
    """Cortes en edades enteras estrictamente dentro del rango (con al menos
    una observación a cada lado para identificar el tramo)."""
    xs = np.unique(x)
    return [int(v) for v in xs[2:-1]]


def _sse_lote(x, y, w, fijos, lote):
    """SSE ponderada de muchos conjuntos de cortes a la vez (ecuaciones normales
    por lotes, x reescalada para condicionar). lote: array (m, j) de cortes extra."""
    sc = 50.0
    x0 = x.min()
    xs = (x - x0) / sc
    lote = (np.asarray(lote, float).reshape(len(lote), -1) - x0) / sc
    fj = (np.asarray(fijos, float) - x0) / sc
    m = lote.shape[0]
    cols = [np.ones((m, xs.size)), np.broadcast_to(xs, (m, xs.size))]
    for b in fj:
        cols.append(np.broadcast_to(np.maximum(xs - b, 0.0), (m, xs.size)))
    for jj in range(lote.shape[1]):
        cols.append(np.maximum(xs[None, :] - lote[:, jj:jj + 1], 0.0))
    X = np.stack(cols, axis=2)                       # (m, n, p)
    XtW = X.transpose(0, 2, 1) * w[None, None, :]
    A = XtW @ X
    bvec = XtW @ y
    A = A + 1e-10 * np.eye(A.shape[1])[None] * np.trace(A, axis1=1, axis2=2)[:, None, None]
    coef = np.linalg.solve(A, bvec[..., None])[..., 0]
    return np.sum(w * y * y) - np.sum(coef * bvec, axis=1)


def buscar_cortes(x, y, w, k, reinicios=None, inicio=None):
    """Exacta para k<=2; codiciosa + refinamiento coordenado para k>=3.
    Devuelve (cortes ordenados, SSE)."""
    cand = np.array(candidatos(x))
    if k == 0:
        return [], _sse(x, y, w, [])
    if k <= 2:
        lote = np.array(list(combinations(cand, k)))
        i = int(np.argmin(_sse_lote(x, y, w, [], lote)))
        c = [int(v) for v in lote[i]]
        return c, _sse(x, y, w, c)
    inicios = [sorted(inicio)] if inicio else []
    cortes = []
    for _ in range(k):  # inicio codicioso
        libres = np.array([c for c in cand if c not in cortes])
        s = _sse_lote(x, y, w, cortes, libres[:, None])
        cortes.append(int(libres[int(np.argmin(s))]))
    inicios.append(sorted(cortes))
    rng = np.random.default_rng(SEMILLA)  # reinicios aleatorios contra óptimos locales
    for _ in range(REINICIOS if reinicios is None else reinicios):
        inicios.append(sorted(int(v) for v in rng.choice(cand, size=k, replace=False)))
    mejor, mejor_sse = None, np.inf
    for cortes in inicios:
        cortes, sse = _refinar(x, y, w, cand, cortes)
        if sse < mejor_sse * (1 - 1e-12):
            mejor, mejor_sse = cortes, sse
    return mejor, mejor_sse


def _refinar(x, y, w, cand, cortes):
    """Refinamiento coordenado hasta que ningún corte mejore."""
    k = len(cortes)
    sse = _sse(x, y, w, cortes)
    mejora = True
    while mejora:
        mejora = False
        for j in range(k):
            otros = cortes[:j] + cortes[j + 1:]
            libres = np.array([c for c in cand if c not in otros])
            s = _sse_lote(x, y, w, otros, libres[:, None])
            mc = int(libres[int(np.argmin(s))])
            if mc != cortes[j]:
                nuevo = _sse(x, y, w, otros + [mc])
                if nuevo < sse * (1 - 1e-9):
                    cortes, sse, mejora = sorted(otros + [mc]), nuevo, True
    return cortes, sse


def curva_promedio(curvas):
    """Promedio por edad de curvas centradas [(x, n, yc), ...], ponderado por n.
    Devuelve (x, w=suma de n, y)."""
    num, den = {}, {}
    for x, n, yc in curvas:
        for a, ni, yi in zip(x, n, yc):
            num[a] = num.get(a, 0.0) + ni * yi
            den[a] = den.get(a, 0.0) + ni
    xs = np.array(sorted(num))
    w = np.array([den[a] for a in xs])
    return xs, w, np.array([num[a] / den[a] for a in xs])


def cv_loeo(curvas, kmax=K_MAX):
    """Validación cruzada dejando fuera una elección. curvas: lista de (x, n, y) sin centrar.
    Cortes sobre la curva promedio centrada de las otras; en la elección fuera se
    reestiman intercepto y pendientes con cortes fijos; error = MSE ponderado de la forma.
    Devuelve {k: (media, se, errores_por_fold, cortes_por_fold)}."""
    cen = [(x, n, centrar(y, n)) for x, n, y in curvas]
    out = {}
    for k in range(0, kmax + 1):
        errs, cs = [], []
        for e in range(len(cen)):
            xt, wt, yt = curva_promedio([c for i, c in enumerate(cen) if i != e])
            cortes, _ = buscar_cortes(xt, yt, wt, k)
            xe, ne, ye = cen[e]
            _, sse = ajustar_fijos(xe, ye, ne, cortes)
            errs.append(sse / ne.sum())
            cs.append(cortes)
        errs = np.array(errs)
        out[k] = (float(errs.mean()), float(errs.std(ddof=1) / np.sqrt(len(errs))), errs.tolist(), cs)
    return out


def regla_1se(cv):
    """k más chico con error medio <= mínimo + 1 SE (SE del k de error mínimo)."""
    kmin = min(cv, key=lambda k: cv[k][0])
    umbral = cv[kmin][0] + cv[kmin][1]
    return min(k for k in cv if cv[k][0] <= umbral), kmin


def etiqueta_grupo(emin, emax):
    return f"{emin}+" if emax is None else f"{emin}–{emax}"


def definir_grupos(cortes, edad_min=18):
    """Grupos [edad_min,b1), [b1,b2), ..., [bk,inf). Corte = primera edad del nuevo tramo."""
    lim = [edad_min] + list(cortes)
    grupos = []
    for i, a in enumerate(lim):
        b = lim[i + 1] - 1 if i + 1 < len(lim) else None
        grupos.append({"id": i + 1, "etiqueta": etiqueta_grupo(a, b), "edad_min": int(a), "edad_max": b if b is None else int(b)})
    return grupos


def bootstrap_secciones(sv, n, edades, k, inicio, B, semilla):
    """Bootstrap por sección (D-007): sv, n matrices (secciones x edades). Remuestrea
    secciones con reemplazo (conteos multinomiales), recalcula la curva y reajusta k cortes.
    Devuelve array (B, k) de cortes."""
    rng = np.random.default_rng(semilla)
    ns = sv.shape[0]
    res = []
    for _ in range(B):
        c = rng.multinomial(ns, np.full(ns, 1.0 / ns)).astype(float)
        sb, nb = c @ sv, c @ n
        ok = (nb > 0) & (sb > 0) & (sb < nb)
        x, ww = edades[ok], nb[ok]
        y = logit(sb[ok] / ww)
        cs, _ = buscar_cortes(x, centrar(y, ww), ww, k, reinicios=2, inicio=inicio)
        res.append(cs)
    return np.array(res)


def error_mc_percentil(muestras, q, rem=1000, semilla=0):
    """Error Monte Carlo (EE) del percentil q de las B réplicas, por remuestreo de las réplicas."""
    rng = np.random.default_rng(semilla)
    v = [np.percentile(rng.choice(muestras, size=len(muestras)), q) for _ in range(rem)]
    return float(np.std(v, ddof=1))


def puntos_spline(x, y, w, grid=None):
    """Spline de suavizado ponderado (lambda por GCV, scipy make_smoothing_spline).
    Devuelve (lambda, edades de cruce de 1a derivada por 0, edades de cambio de signo de la 2a,
    spline). Rejilla en edades enteras entre min(x) y max(x)."""
    from scipy.interpolate import make_smoothing_spline
    sp = make_smoothing_spline(x, y, w=w / w.mean(), lam=None)
    g = np.linspace(x.min(), x.max(), 2000) if grid is None else grid
    d1, d2 = sp.derivative(1)(g), sp.derivative(2)(g)
    z1 = [float(g[i]) for i in range(len(g) - 1) if d1[i] * d1[i + 1] < 0]
    z2 = [float(g[i]) for i in range(len(g) - 1) if d2[i] * d2[i + 1] < 0]
    return sp, z1, z2


def cortes_comunes(cortes_h, cortes_m):
    """Cortes comunes (D-007): media por posición de hombres y mujeres, redondeo half-up.
    Aborta si k difiere entre sexos."""
    if len(cortes_h) != len(cortes_m):
        raise ValueError(f"k difiere entre sexos (H={len(cortes_h)}, M={len(cortes_m)}); "
                         "no se improvisa una regla: revisar los cortes antes de continuar.")
    return [int(np.floor((a + b) / 2 + 0.5)) for a, b in zip(cortes_h, cortes_m)]
