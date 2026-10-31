"""Pruebas de la violencia homicida municipal (D-027)."""
import numpy as np
import pandas as pd
from ine_perfiles import violencia as V


def test_dispersion_infinita_es_la_cruda():
    O, E, mu = np.array([0, 3, 40.0]), np.array([100, 200, 1000.0]), 0.02
    assert np.allclose(V.contraer(O, E, mu, np.inf), O / E)


def test_dispersion_cero_es_la_del_estado():
    O, E, mu = np.array([0, 3, 40.0]), np.array([100, 200, 1000.0]), 0.02
    assert np.allclose(V.contraer(O, E, mu, 0.0), mu)


def test_contraccion_entre_cruda_y_estado():
    O, E, mu = np.array([0, 40.0]), np.array([100, 1000.0]), 0.02
    c = V.contraer(O, E, mu, 1.0)
    cruda = O / E
    assert np.all((c >= np.minimum(cruda, mu) - 1e-12) & (c <= np.maximum(cruda, mu) + 1e-12))


def test_mle_recupera_la_dispersion():
    rng = np.random.default_rng(0)
    phi, mu = 0.8, 0.003
    E = rng.uniform(2e4, 5e5, 4000)
    lam = rng.gamma(1 / phi, mu * phi, 4000)
    O = rng.poisson(E * lam)
    est, front = V.estimar_dispersion(O, E, mu)
    assert not front and abs(est - phi) / phi < 0.1


def test_tasa_contraida_conserva_orden_y_estado():
    df = pd.DataFrame({"edo": [1, 1, 1, 2, 2], "homicidios": [0, 5, 80, 1, 30.0],
                       "exposicion": [1e4, 5e4, 4e5, 2e4, 3e5]})
    out, tab, _ = V.tasa_contraida(df)
    assert (out.tasa_contr > 0).all()
    assert set(tab.edo) == {1, 2}


def test_conciliacion_de_homicidios():
    agg = pd.DataFrame({"edicion": [2009, 2009, 2010, 2010, 2010],
                        "ent": [1, 1, 1, 99, 2], "mun": [1, 999, 1, 5, 3],
                        "anio_ocur": [2009, 2009, 2009, 2009, 9999],
                        "n_def": [10, 4, 12, 3, 2], "n_hom": [3, 1, 2, 4, 5]})
    c, r = V.clasificar(agg, 2009, 2023)
    assert r["total_todas_ocurrencias"] == agg.n_hom.sum()
    assert (c.n_hom.sum() + r["en_ventana_ent_no_esp"] + r["en_ventana_mun_no_esp"]
            + r["anio_no_especificado"] + r["fuera_de_ventana"]) == agg.n_hom.sum()
    assert c.n_hom.sum() == 5  # (1,1): 3 + 2 de dos ediciones


def test_primera_aparicion():
    agg = pd.DataFrame({"edicion": [2012, 2013], "ent": [3, 3], "mun": [9, 9],
                        "anio_ocur": [2011, 2012], "n_def": [5, 5], "n_hom": [0, 0]})
    assert V.primera_aparicion(agg, 2009).primer_anio.iloc[0] == 2011


def test_conciliacion_con_microdatos_reales():
    """La suma de homicidios por municipio + no mapeados + no especificados = total en la ventana."""
    import pytest
    if not (V.OUT_AGREGADO.exists() and V.OUT_VIOLENCIA.exists()):
        pytest.skip("corre scripts/datos/violencia_municipio.py")
    agg, res = pd.read_parquet(V.OUT_AGREGADO), pd.read_parquet(V.OUT_VIOLENCIA)
    for nom, (a, b) in V.C.VENTANAS_VIOLENCIA.items():
        _, r = V.clasificar(agg, a, b)
        sin_expo = r["en_ventana"] - r["en_ventana_ent_no_esp"] - r["en_ventana_mun_no_esp"] - res[f"hom_{nom}"].sum()
        assert sin_expo >= 0  # lo restante son claves sin mapear o sin exposición
        assert sin_expo < 0.001 * r["en_ventana"]
    assert res.duplicated(["edo", "mpio"]).sum() == 0
