"""Pruebas de la regla de los cinco perfiles (D-011, D-029)."""
import numpy as np

from ine_perfiles import evaluacion as CF
from ine_perfiles import config as C


def test_veredicto_k5():
    assert CF.veredicto_k5(0, 4) and CF.veredicto_k5(0, 5)
    assert not CF.veredicto_k5(0, 3)
    assert not CF.veredicto_k5(1, 5)
    assert C.N_CLARAS_MIN_K5 == 4 and C.K_EVALUADO_K5 == 5


def test_etiquetas_entrega_k5():
    e = CF.etiquetas_entrega_k5([1, 2, 3, 4, 5, 3], [1, 2, 4, 5])
    assert list(e) == ["E1", "E2", "resto", "E3", "E4", "resto"]
    e5 = CF.etiquetas_entrega_k5(np.array([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5])
    assert "resto" not in set(e5)


def test_es_clara():
    assert CF.es_clara(0.9, False, 0)
    assert not CF.es_clara(0.84, False, 0)
    assert not CF.es_clara(0.9, True, 0, jaccard_frio=0.8)   # regida por el frío: manda el frío (D-017)
    assert CF.es_clara(0.9, True, 0, jaccard_frio=0.9)
    assert not CF.es_clara(0.9, False, 1)
