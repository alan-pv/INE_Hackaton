import json
import numpy as np
from ine_perfiles import config as C
from ine_perfiles import edades as E


def test_recupera_cortes_sinteticos():
    rng = np.random.default_rng(0)
    x = np.arange(18, 91, dtype=float)
    y = 0.5 + 0.0 * x - 0.15 * np.maximum(x - 18, 0) + 0.17 * np.maximum(x - 25, 0) - 0.04 * np.maximum(x - 60, 0)
    y = y + rng.normal(0, 0.01, x.size)
    w = np.full(x.size, 1000.0)
    cortes, _ = E.buscar_cortes(x, y, w, 2)
    assert cortes == [25, 60]
    # codicioso + refinamiento con k=3 incluye los verdaderos
    c3, _ = E.buscar_cortes(x, y, w, 3)
    assert 25 in c3 and 60 in c3 and c3 == sorted(c3)


def test_json_cortes():
    f = C.RAIZ / "data" / "processed" / "cortes_edad.json"
    assert f.exists()
    d = json.load(open(f))
    assert d["cortes"] == sorted(d["cortes"]) and len(d["cortes"]) == d["k"]
    g = d["grupos"]
    assert g[0]["edad_min"] == 18 and g[-1]["edad_max"] is None
    for a, b in zip(g[:-1], g[1:]):
        assert a["edad_max"] + 1 == b["edad_min"]


def test_seleccion_final():
    d = json.load(open(C.RAIZ / "data" / "processed" / "cortes_edad.json"))
    sf = d["seleccion_final"]
    assert d["grupos"] == sf["grupos"] and d["cortes"] == sf["cortes"]
    ks = {v["k"] for v in sf["por_sexo"].values()}
    assert ks == {sf["k"]} and len(sf["cortes"]) == sf["k"]
    assert sf["cortes"] == sorted(sf["cortes"])
    assert d["analisis_pooled"]["k"] == 8


def test_cortes_comunes_half_up_y_aborta():
    import pytest
    assert E.cortes_comunes([20, 23], [20, 26]) == [20, 25]
    with pytest.raises(ValueError):
        E.cortes_comunes([1, 2], [1])
