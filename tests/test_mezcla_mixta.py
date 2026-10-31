"""Pruebas de la mezcla mixta ponderada (D-024)."""
import numpy as np
from sklearn.metrics import adjusted_rand_score

from ine_perfiles import mezcla_mixta as MM


def simular(n=6000, seed=0):
    rng = np.random.default_rng(seed)
    z = rng.choice(3, size=n, p=[0.3, 0.5, 0.2])
    th = [np.array([[.9, .1], [.1, .9], [.5, .5]]),
          np.array([[.8, .1, .1], [.1, .8, .1], [.1, .1, .8]])]
    cat = np.column_stack([[rng.choice(2, p=th[0][k]) for k in z], [rng.choice(3, p=th[1][k]) for k in z]])
    mu = np.array([[-3.0, 0.0], [0.0, 3.0], [3.0, -3.0]])
    X = mu[z] + rng.normal(size=(n, 2))
    return MM.Datos(cat, (2, 3), X, np.ones(n)), z


def test_recupera_tres_clases():
    d, z = simular()
    a, info = MM.ajustar_con_reinicios(d, 3, np.random.default_rng(1))
    mapa, pmax, _ = MM.clasificar(d, a.modelo)
    assert adjusted_rand_score(z, mapa) >= 0.9


def test_em_monotono():
    d, _ = simular(2000)
    mod0 = MM.inicializar(d, 3, np.random.default_rng(2))
    a = MM.ajustar(d, mod0, tol=1e-12, maxit=80)
    h = np.array(a.historia)
    assert np.all(np.diff(h) > -1e-6)


def test_duplicar_celda_equivale_a_peso_2():
    d, _ = simular(500, seed=3)
    d.w[0] = 2.0
    d2 = MM.Datos(np.vstack([d.cat, d.cat[:1]]), d.ncat, np.vstack([d.X, d.X[:1]]), np.r_[np.ones(500), 1.0])
    d1 = MM.Datos(d.cat, d.ncat, d.X, d.w)
    mod0 = MM.inicializar(d1, 3, np.random.default_rng(4))
    a1 = MM.ajustar(d1, mod0, 1e-12, 200)
    a2 = MM.ajustar(d2, mod0, 1e-12, 200)
    assert abs(a1.logL - a2.logL) < 1e-6
    assert np.allclose(a1.modelo.mu, a2.modelo.mu, atol=1e-8)
    assert np.allclose(a1.modelo.pi, a2.modelo.pi, atol=1e-10)


def test_marginalizacion_de_dimension_toda_nan():
    d, _ = simular(1500, seed=5)
    dn = MM.Datos(d.cat, d.ncat, np.column_stack([d.X, np.full(d.n, np.nan)]), d.w)
    mod0 = MM.inicializar(d, 3, np.random.default_rng(6))
    a = MM.ajustar(d, mod0, 1e-12, 100)
    mod1 = MM.Modelo(mod0.pi, mod0.theta, np.column_stack([mod0.mu, np.zeros(3)]), np.column_stack([mod0.var, np.ones(3)]))
    b = MM.ajustar(dn, mod1, 1e-12, 100)
    assert abs(a.logL - b.logL) < 1e-8
    assert np.allclose(a.modelo.mu, b.modelo.mu[:, :2])
    assert dn.n_cont_efectivas() == 2
    assert MM.criterios(a, d)["n_param"] == MM.criterios(b, dn)["n_param"]


def test_horn_retiene_un_componente():
    rng = np.random.default_rng(7)
    n = 3000
    f = rng.normal(size=n)
    X = np.column_stack([0.9 * f + 0.45 * rng.normal(size=n) for _ in range(6)])
    Z, _, _ = MM.estandarizar_ponderado(X, np.ones(n))
    r = MM.analisis_paralelo(Z, np.ones(n), np.random.default_rng(8), bloque=10, r_max=40)
    assert r["n_retenidos"] == 1


def test_parametros_libres():
    assert MM.n_param(3, (2, 7), 4) == 2 + 3 * (1 + 6) + 2 * 3 * 4
