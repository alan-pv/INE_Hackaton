"""Utilidades del bootstrap de la mezcla (D-017): remuestreo estratificado de secciones,
Jaccard por clase (Hennig, 2007) y lectura con la escala `fpc` de D-011."""
import numpy as np


def indice_secciones(estado_celda, seccion_celda):
    """Agrupa filas por seccion (llave (edo, seccion): el número de sección no es único a nivel nacional).
    Devuelve (orden, inicio, largo, edo_sec): `orden[inicio[s]:inicio[s]+largo[s]]` son las filas de la seccion s."""
    import pandas as pd
    cod, uniq = pd.factorize(pd.MultiIndex.from_arrays([np.asarray(estado_celda), np.asarray(seccion_celda)]))
    orden = np.argsort(cod, kind="stable")
    largo = np.bincount(cod, minlength=len(uniq))
    inicio = np.concatenate([[0], np.cumsum(largo)[:-1]])
    return orden, inicio, largo, uniq.get_level_values(0).to_numpy()


def remuestrear_secciones(rng, edo_sec, orden, inicio, largo):
    """D-017: secciones con reemplazo, estratificado por estado (mismo numero de secciones por estado).
    Las filas de una seccion repetida se duplican. Devuelve (filas, secciones_elegidas)."""
    elegidas = []
    for e in np.unique(edo_sec):
        ids = np.flatnonzero(edo_sec == e)
        elegidas.append(rng.choice(ids, size=len(ids), replace=True))
    elegidas = np.concatenate(elegidas)
    ln = largo[elegidas]
    pos = np.repeat(inicio[elegidas] - (np.cumsum(ln) - ln), ln) + np.arange(ln.sum())
    return orden[pos], elegidas


def jaccard_por_clase(orig, rep, K=None):
    """D-017: para cada clase original, el maximo Jaccard contra las clases de la replica.
    `orig` y `rep` son etiquetas enteras (>=0) de las mismas celdas."""
    orig = np.asarray(orig, dtype=np.int64)
    rep = np.asarray(rep, dtype=np.int64)
    K = int(K if K is not None else orig.max() + 1)
    J = int(max(rep.max() + 1, 1))
    C = np.bincount(orig * J + rep, minlength=K * J).reshape(K, J).astype(float)
    a = C.sum(axis=1)[:, None]
    b = C.sum(axis=0)[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        jac = np.where(a + b - C > 0, C / (a + b - C), 0.0)
    return jac.max(axis=1)


# Escala de lectura declarada de D-011 (paquete fpc), no un corte de decision.
def lectura_fpc(j):
    if j >= 0.85:
        return "muy estable"
    if j >= 0.75:
        return "estable"
    if j >= 0.6:
        return "patrón"
    if j > 0.5:
        return "no confiable"
    return "disuelto"


def ee_monte_carlo(x):
    """sd/sqrt(B) por columna (x: B x K)."""
    x = np.asarray(x, dtype=float)
    return x.std(axis=0, ddof=1) / np.sqrt(x.shape[0])
