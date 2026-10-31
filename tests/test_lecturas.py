"""Pruebas de las lecturas de cada perfil (D-034) con datos sintéticos."""
import numpy as np
import pandas as pd

from ine_perfiles import lecturas as LF


def test_regla_mayoria_estricta():
    obj = pd.DataFrame(dict(edo=[1, 1, 1, 1], seccion=[1, 1, 2, 2], ln_2024=[50.0, 50.0, 50.0, 50.0],
                            resp_perfil_1=[1.0, 0.0, 0.5, 0.5], resp_perfil_2=[0.0, 0.0, 0.5, 0.5]))
    ln_sec = pd.DataFrame(dict(edo=[1, 1, 1], seccion=[1, 2, 3], ln_tot=[200.0, 100.0, 80.0]))
    s = LF.pertenencia(obj, ln_sec, 2).set_index("seccion")
    assert s.loc[1, "frac_1"] == 0.25 and s.loc[1, "perfil_may"] == 0   # 50/200
    assert s.loc[2, "frac_1"] == 0.5 and s.loc[2, "perfil_may"] == 0    # exactamente 1/2 no es mayoría
    assert s.loc[3, "perfil_may"] == 0
    obj.loc[0, "ln_2024"] = 150.0
    s = LF.pertenencia(obj, ln_sec, 2).set_index("seccion")
    assert s.loc[1, "perfil_may"] == 1


def test_contraste_dentro_de_seccion():
    # sección 1: hombres 25-46 (grupo 3 y 4) vs mujeres; pesos distintos
    cel = pd.DataFrame(dict(edo=[1] * 6, seccion=[1, 1, 1, 1, 2, 2], sexo=[0, 0, 1, 1, 0, 1], grupo=[3, 4, 3, 4, 3, 3],
                            delta=[-1.0, -3.0, -0.5, -0.5, -2.0, -1.0], w=[1.0, 3.0, 2.0, 2.0, 5.0, 5.0]))
    h = dict(sexos=[0], grupos=(3, 4)); m = dict(sexos=[1], grupos=(3, 4))
    c = LF.contraste_seccion(cel, h, m).set_index("seccion")["contraste"]
    assert abs(c[1] - ((-1 * 1 + -3 * 3) / 4 - (-0.5))) < 1e-12      # -2.5 + 0.5 = -2
    assert abs(c[2] - (-2.0 + 1.0)) < 1e-12
    # un grupo sin peso deja la sección fuera
    cel.loc[cel.sexo.eq(1) & cel.seccion.eq(2), "w"] = 0.0
    assert 2 not in LF.contraste_seccion(cel, h, m)["seccion"].to_numpy()


def test_bootstrap_respeta_estratos():
    estr = np.array([0, 0, 0, 1, 1, 2])
    M = LF.multiplicidades(estr, 200, np.random.default_rng(0))
    for e in (0, 1, 2):
        assert (M[:, estr == e].sum(axis=1) == (estr == e).sum()).all()
    assert (M[:, 5] == 1).all()                         # estrato de un municipio no varía
    assert (M[:, :3] == 0).any() and M.max() > 1        # sí remuestrea dentro del estrato


def test_media_por_municipio_igual_filas_replicadas():
    r = np.random.default_rng(1)
    v = r.normal(size=30); w = r.random(30) + 0.1; mun = r.integers(0, 6, 30)
    num, den = LF.media_ponderada_por_mun(v, w, mun, 6, np.ones(30, bool))
    mult = np.array([[2, 0, 1, 3, 0, 1]], float)
    est = LF.razon_boot(mult, num, den)[0]
    rep = np.repeat(np.arange(30), mult[0, mun].astype(int))
    assert abs(est - np.average(v[rep], weights=w[rep])) < 1e-12


def test_veredictos():
    assert LF.veredicto_prediccion(-0.2, -0.3, -0.1, -1) == "se cumple"
    assert LF.veredicto_prediccion(-0.2, -0.3, 0.1, -1) == "no se cumple"
    assert LF.veredicto_prediccion(0.2, 0.1, 0.3, -1) == "contraria"
    assert LF.veredicto_lectura(["se cumple", "se cumple"]) == "respaldada"
    assert LF.veredicto_lectura(["se cumple", "no se cumple"]) == "parcial"
    assert LF.veredicto_lectura(["contraria", "no se cumple"]) == "no respaldada"


def test_pendiente_y_mediana():
    y = np.array([[1.0, 3.0, 5.0], [0.0, 0.0, 0.0]])
    assert np.allclose(LF.pendiente_mco(y, np.arange(3)), [2.0, 0.0])
    assert LF.mediana_ponderada([1, 2, 3], [1, 1, 1]) == 2.0
    assert LF.mediana_ponderada([1, 2, 3], [1, 1, 5]) == 3.0


def test_medida_log_y_veredicto_combinado():
    cel = pd.DataFrame(dict(edo=[1, 1, 1], seccion=[1, 1, 1], sexo=[0, 0, 0], grupo=[3, 5, 5],
                            delta=[-1.0, -2.0, -4.0], delta_log=[-0.5, np.nan, -1.0], w=[1.0, 1.0, 1.0]))
    b = LF.brecha_seccion(cel, grupos=[5], col="delta_log")
    assert abs(b["brecha"].iloc[0] + 1.0) < 1e-12           # la celda NaN no pesa
    assert LF.veredicto_combinado("se cumple", "se cumple") == "se cumple"
    assert LF.veredicto_combinado("contraria", "se cumple") == "no concluyente"
    assert LF.veredicto_lectura_concluyente(["se cumple", "no concluyente"]) == "respaldada"
    assert LF.veredicto_lectura_concluyente(["se cumple", "contraria", "no concluyente"]) == "parcial"
    assert LF.veredicto_lectura_concluyente(["no se cumple", "no concluyente"]) == "no respaldada"
