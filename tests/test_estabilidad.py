import numpy as np
from ine_perfiles import estabilidad as E


def test_jaccard_identica_y_permutada():
    o = np.repeat([0, 1, 2], 10)
    assert np.allclose(E.jaccard_por_clase(o, o), 1.0)
    perm = np.array([2, 0, 1])[o]
    assert np.allclose(E.jaccard_por_clase(o, perm), 1.0)


def test_jaccard_valor_conocido():
    o = np.array([0, 0, 0, 0, 1, 1])
    r = np.array([0, 0, 0, 1, 1, 1])
    j = E.jaccard_por_clase(o, r)
    assert np.allclose(j, [3 / 4, 2 / 3])


def test_remuestreo_conserva_secciones_por_estado():
    edo = np.repeat([1, 2], [3, 2])
    sec = np.array([10, 10, 11, 12, 10])
    # 5 celdas; secciones (1,10)x2, (1,11), (2,12), (2,10): 2 por estado
    orden, ini, lar, esec = E.indice_secciones(edo, sec)
    assert len(esec) == 4 and lar.sum() == 5
    filas, el = E.remuestrear_secciones(np.random.default_rng(3), esec, orden, ini, lar)
    assert (esec[el] == 1).sum() == 2 and (esec[el] == 2).sum() == 2
    assert len(filas) == lar[el].sum()
    # las filas de cada seccion elegida aparecen completas
    esperado = np.concatenate([orden[ini[s]:ini[s] + lar[s]] for s in el])
    assert np.array_equal(filas, esperado)


def test_lectura():
    assert E.lectura_fpc(0.9) == "muy estable" and E.lectura_fpc(0.5) == "disuelto"
