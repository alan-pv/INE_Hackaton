"""Pruebas de la evaluación (ARI, reetiquetado, curva de captura y ΔAUC) con datos sintéticos (D-021, D-025, D-032)."""
import numpy as np
from sklearn.metrics import adjusted_rand_score

from ine_perfiles import evaluacion as CF


def _etiquetas(n=500, seed=0):
    r = np.random.default_rng(seed)
    a = r.integers(0, 4, n)
    b = np.where(r.random(n) < 0.6, a, r.integers(0, 5, n))
    return a, b


def test_ari_pesos_uno_igual_sklearn():
    a, b = _etiquetas()
    assert abs(CF.ari_ponderado(a, b) - adjusted_rand_score(a, b)) < 1e-12
    assert abs(CF.ari_ponderado(a, b, np.ones(len(a))) - adjusted_rand_score(a, b)) < 1e-12


def test_ari_pesos_enteros_igual_filas_replicadas():
    a, b = _etiquetas(300, 1)
    w = np.random.default_rng(2).integers(1, 5, len(a))
    rep = np.repeat(np.arange(len(a)), w)
    assert abs(CF.ari_ponderado(a, b, w) - adjusted_rand_score(a[rep], b[rep])) < 1e-12


def test_ari_identicas_y_etiquetas_permutadas():
    a, _ = _etiquetas()
    assert abs(CF.ari_ponderado(a, (a + 1) % 4, np.random.default_rng(3).random(len(a)))- 1.0) < 1e-12


def test_reetiquetar_hungarian():
    ref = np.array([0, 0, 1, 1, 2, 2, 3, 3])
    nuevo = np.array([2, 2, 3, 3, 0, 0, 1, 1])
    mapa, _ = CF.reetiquetar(ref, nuevo, np.ones(8), 4)
    assert (mapa[nuevo] == ref).all()


def test_curva_captura_orden_perfecto_y_aleatorio():
    r = np.random.default_rng(5)
    n = 20000
    ln = r.uniform(1, 5, n)
    d = r.normal(size=n)
    # r̂ perfectamente informativo (menor r̂ = mayor déficit)
    c, auc_p, auc_s = CF.curva_captura(-d, ln, d)
    assert abs(c.y_pos.iloc[-1] - 1) < 1e-12 and abs(c.x.iloc[-1] - 1) < 1e-12 and abs(c.y_sig.iloc[-1] - (d.sum() / np.clip(d, 0, None).sum())) < 1e-12
    assert auc_p > 0.75
    # orden aleatorio: ~diagonal
    c2, a2, s2 = CF.curva_captura(r.permutation(n).astype(float), ln, d)
    assert abs(a2 - 0.5) < 0.02 and abs(s2) < 0.05


def test_curva_empates_son_segmento_recto_y_despues():
    ln = np.array([1.0, 1, 1, 1])
    d = np.array([4.0, 0, 0, 0])
    c, auc, _ = CF.curva_captura(np.zeros(4), ln, d)
    assert len(c) == 2 and abs(auc - 0.5) < 1e-12           # un solo bloque = diagonal
    c, _, _ = CF.curva_captura(np.array([5.0, 0, 0, 0]), ln, d, despues=np.array([False, True, True, True]))
    assert abs(c.x.iloc[1] - 0.25) < 1e-12                  # el no 'despues' va primero


def _datos_boot(n=600, seed=11):
    r = np.random.default_rng(seed)
    edo = r.integers(1, 4, n)
    sec = np.arange(n)
    ln = r.uniform(1, 5, n)
    d = r.normal(size=n)
    return edo, sec, ln, d, -d + r.normal(scale=1.0, size=n), r.normal(size=n)


def test_bootstrap_grupos_un_grupo_por_celda_coincide_con_secciones():
    edo, sec, ln, d, r1, r2 = _datos_boot()
    a = CF.delta_auc_bootstrap(r1, None, r2, None, ln, d, edo, sec, B=199, nivel=0.95, sufijo=5)
    b = CF.delta_auc_bootstrap_grupos(r1, None, r2, None, ln, d, edo, sec, sufijo=5, B=199, nivel=0.95)
    assert np.allclose(a["deltas"], b["deltas"]) and a["lo"] == b["lo"] and a["hi"] == b["hi"]
    assert b["n_grupos"] == len(sec)


def test_bootstrap_grupos_respeta_estratos_y_ensancha_ic():
    from ine_perfiles import estabilidad as EST
    edo, sec, ln, d, r1, r2 = _datos_boot(900)
    mun = sec // 30                                   # 30 municipios de 30 celdas (cada uno dentro de un solo estado)
    edo = (mun % 3) + 1                               # el estado es función del municipio
    _, _, largo, edo_g = EST.indice_secciones(edo, mun)
    assert len(largo) == 30 and (largo == 30).all()
    rng = np.random.default_rng(1)
    orden, inicio, largo, edo_g = EST.indice_secciones(edo, mun)
    _, eleg = EST.remuestrear_secciones(rng, edo_g, orden, inicio, largo)
    assert (np.bincount(edo_g[eleg], minlength=4) == np.bincount(edo_g, minlength=4)).all()
    o = CF.delta_auc_bootstrap_grupos(r1, None, r2, None, ln, d, edo, mun, sufijo=8, B=199, nivel=0.95)
    assert o["n_grupos"] == 30 and o["lo"] < o["delta"] < o["hi"]
    c = CF.delta_auc_bootstrap_grupos(r1, None, r2, None, ln, d, edo, np.arange(900), sufijo=8, B=199, nivel=0.95)
    assert (o["hi"] - o["lo"]) > 0.5 * (c["hi"] - c["lo"])   # menos grupos, no un IC más angosto
