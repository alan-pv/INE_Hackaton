"""Pruebas de la brecha con datos sintéticos (D-022)."""
import numpy as np
import pandas as pd
from scipy.stats import beta, spearmanr

from ine_perfiles import brecha as B


def _sim(phi, k=4000, seed=1):
    r = np.random.default_rng(seed)
    q = r.uniform(0.3, 0.8, k); N = r.integers(50, 2000, k).astype(float)
    p = r.beta(phi * q, phi * (1 - q))
    return r.binomial(N.astype(int), p).astype(float), N, q


def test_recupera_phi():
    for phi in (20.0, 200.0):
        O, N, q = _sim(phi)
        est = B.ajustar_phi(O, N, q)["phi"]
        assert abs(np.log(est / phi)) < np.log(1.15)


def test_sin_sobredispersion():
    r = np.random.default_rng(2)
    q = r.uniform(0.3, 0.8, 3000); N = np.full(3000, 100)
    O = r.binomial(N, q).astype(float)
    aj = B.ajustar_phi(O, N.astype(float), q)
    assert aj['estado'] == 'sin_sobredispersion' or aj['phi'] > 10 * 100  # >> N


def _panel():
    r = np.random.default_rng(3)
    filas = []
    for c in range(300):
        for e in (2009, 2012, 2024):
            n = int(r.integers(20, 300)); filas.append(
                (1, c, c % 2, 1 + c % 2, e, int(r.binomial(n, 0.5)), n))
    d = pd.DataFrame(filas, columns=["edo", "seccion", "sexo", "grupo", "aelec", "sv", "n"])
    d["nv"] = d.n - d.sv
    return d


def test_sumas_O_igual_E():
    p = _panel()
    q = B.tasa_esperada(p)
    c = B.agregar_celdas(p, q)
    s = c.groupby(["sexo", "grupo"])[["O", "E"]].sum()
    assert np.allclose(s.O, s.E, rtol=1e-10)


def test_prob_bajo_y_limites():
    O = np.array([30., 10, 5]); N = np.array([50., 40, 20]); q = np.array([0.6, 0.5, 0.4])
    pt, de, pb = B.posterior(O, N, q, 30.0)
    a = O + 30 * q; b = N - O + 30 * (1 - q)
    assert np.allclose(pb, beta.cdf(q, a, b))
    # phi grande y N pequeño: p_tilde ~ q
    pt, _, _ = B.posterior(np.array([1.]), np.array([2.]), np.array([0.6]), 1e8)
    assert abs(pt[0] - 0.6) < 1e-6
    # N enorme: p_tilde ~ O/N
    pt, _, _ = B.posterior(np.array([7e8]), np.array([1e9]), np.array([0.6]), 30.0)
    assert abs(pt[0] - 0.7) < 1e-6


def test_spearman_ponderada_iguales():
    r = np.random.default_rng(4)
    x = r.normal(size=500); y = x + r.normal(size=500); x[:20] = x[20:40]  # empates
    assert abs(B.spearman_ponderada(x, y, np.ones(500)) - spearmanr(x, y)[0]) < 1e-12
