import numpy as np
import pandas as pd

from ine_perfiles import descriptores as D


def _mov():
    filas = []
    for e_prev, e, ob, es in [(2009, 2012, 110, 100), (2012, 2015, 90, 100), (2015, 2018, 100, 100)]:
        filas.append(dict(e_prev=e_prev, e=e, edo=1, seccion=1, observado=ob, esperado=es,
                          cambio_territorial_en_par=False, reseccionada_en_par=False))
    # par con cambio territorial en la sección 1 (debe excluirse)
    filas.append(dict(e_prev=2018, e=2021, edo=1, seccion=1, observado=500, esperado=100,
                      cambio_territorial_en_par=True, reseccionada_en_par=False))
    for s, f in [(2, 1.2), (3, 0.8)]:
        filas.append(dict(e_prev=2009, e=2012, edo=1, seccion=s, observado=100 * f, esperado=100,
                          cambio_territorial_en_par=False, reseccionada_en_par=False))
    filas.append(dict(e_prev=2009, e=2012, edo=2, seccion=1, observado=100, esperado=100,
                      cambio_territorial_en_par=False, reseccionada_en_par=True))
    return pd.DataFrame(filas)


def test_oe_acumulado_sintetico_y_exclusion():
    marc = pd.DataFrame({"edo": [1], "seccion": [3]})
    v = D.filtrar_pares_validos(_mov(), marc)
    assert not v["cambio_territorial_en_par"].any() and not v["reseccionada_en_par"].any()
    assert not ((v.edo == 1) & (v.seccion == 3)).any()  # sección marcada excluida
    g = D.oe_acumulado(v).set_index(["edo", "seccion"])
    # Σobs/Σesp = (110+90+100)/(300) = 1.0, no el promedio contaminado por el par excluido
    assert np.isclose(g.loc[(1, 1), "oe_acum"], 1.0)
    assert np.isclose(g.loc[(1, 2), "log_oe"], np.log(1.2))
    assert (1, 3) not in g.index and (2, 1) not in g.index


def test_percentil_dentro_del_estado():
    g = pd.DataFrame({"edo": [1, 1, 1, 2, 2], "log_oe": [0.1, 0.2, 0.3, 5.0, np.nan]})
    p = D.percentil_en_estado(g)
    assert np.allclose(p[:3], [100 / 3, 200 / 3, 100])
    assert p[3] == 100 and np.isnan(p[4])


def test_marca_hueyapan_y_circunscripciones():
    m = D.marcar_observaciones()
    assert {(17, 701), (17, 702)} <= set(zip(m.edo, m.seccion))
    assert len(D.CIRCUNSCRIPCION_POR_EDO) == 32 and set(D.CIRCUNSCRIPCION_POR_EDO) == set(range(1, 33))
    assert set(D.CIRCUNSCRIPCION_POR_EDO.values()) == {1, 2, 3, 4, 5}
