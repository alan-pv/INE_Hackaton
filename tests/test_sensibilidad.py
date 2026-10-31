"""Pruebas de la sensibilidad (D-030, D-031) con datos sintéticos pequeños."""
import numpy as np
import pandas as pd
import pytest

from ine_perfiles import brecha as B
from ine_perfiles import config as C
from ine_perfiles import sensibilidad as S


def panel_sintetico(seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    for edo in (1, 2):
        for sec in range(1, 31):
            for sexo in (0, 1):
                for grupo in (1, 2):
                    for aelec in (2009, 2012):
                        ln = int(rng.integers(40, 200))
                        ns = int(rng.integers(0, 6))
                        sv = int(rng.binomial(ln - ns, 0.45 + 0.1 * (edo == 2) + 0.05 * (aelec == 2012)))
                        nv = ln - ns - sv
                        filas.append((edo, sec, sexo, grupo, aelec, sv, nv, ns, ln))
    return pd.DataFrame(filas, columns=["edo", "seccion", "sexo", "grupo", "aelec", "sv", "nv", "ns", "ln"])


CONC = pd.DataFrame({"aelec": [2009, 2009, 2012, 2012], "edo": [1, 2, 1, 2], "k": np.array([1, 0, 0, 0], dtype="int8")})


def test_sin_extra_reproduce_brecha():
    pan = panel_sintetico()
    pan["n"] = pan.sv + pan.nv
    p = S.preparar_panel(pan, "principal")
    cel, _, _, err = S.brecha_escenario(p)
    q = B.tasa_esperada(pan)
    ref = B.agregar_celdas(pan, q)
    np.testing.assert_allclose(cel.E, ref.E)
    np.testing.assert_allclose(cel.O, ref.O)
    assert err < C.SENS_TOL_CONSERVACION


def test_estratificacion_con_k_conserva_y_cambia_lo_esperado():
    pan = panel_sintetico()
    p = S.preparar_panel(pan, "concurrencia", CONC)
    assert set(p.k.unique()) == {0, 1}
    q0 = S.tasa_esperada_k(p)
    qk = S.tasa_esperada_k(p, ["k"])
    cel, err = S.agregar_celdas_k(p, qk, ["k"])
    assert err < C.SENS_TOL_CONSERVACION                      # Σ O = Σ E por sexo×grupo×aelec×k
    cel0, err0 = S.agregar_celdas_k(p, q0)
    assert err0 < C.SENS_TOL_CONSERVACION
    assert not np.allclose(cel.E, cel0.E)                     # lo esperado sí cambia con k
    # globalmente Σ O = Σ E en ambas definiciones
    assert abs(cel.O.sum() - cel.E.sum()) < 1e-6 * cel.O.sum()
    # el estado 1 en 2009 (k=1) y el 2 (k=0) tienen q distintas dentro del mismo sexo×grupo×aelec
    x = qk[(qk.aelec == 2009) & (qk.sexo == 0) & (qk.grupo == 1)]
    assert len(x) == 2 and x.q.nunique() == 2


def test_ausentes_de_concurrencia_son_falso():
    pan = panel_sintetico()
    conc = CONC[CONC.edo == 1]                                 # falta el estado 2
    p = S.preparar_panel(pan, "concurrencia", conc)
    assert (p.k[p.edo == 2] == 0).all() and len(p) == len(pan)


def test_cotas_ns():
    pan = panel_sintetico()
    a = S.preparar_panel(pan, "ns_voto")
    b = S.preparar_panel(pan, "ns_abst")
    p0 = S.preparar_panel(pan, "principal")
    assert (a.sv == pan.sv + pan.ns).all() and (a.n == pan.sv + pan.nv + pan.ns).all()
    assert (b.sv == pan.sv).all() and (b.n == a.n).all()
    assert (p0.n == pan.sv + pan.nv).all()
    # orden de las cotas (D-001): abstención <= principal <= voto, en la tasa nacional
    tasa = lambda d: d.sv.sum() / d.n.sum()
    assert tasa(b) <= tasa(p0) <= tasa(a)
    for p in (a, b):
        cel, _, _, err = S.brecha_escenario(p)
        assert err < C.SENS_TOL_CONSERVACION


def test_regla_de_mayoria():
    K = 3
    ref = np.array([0, 0, 1, 1, 2, 2])
    # clase 0 = perfil 0 puro; clase 1 = 60/40 entre perfiles 1 y 2; clase 2 = resto
    w = np.ones(6)
    esc = np.array([0, 0, 1, 1, 1, 2])
    r = S.cruce_y_regla(ref, esc, w, K)
    assert r["cuota"][0] == 1.0 and r["cumple"][0]
    assert abs(r["cuota"][1] - 2 / 3) < 1e-12 and r["cumple"][1]
    assert r["global_cumple"]
    # exactamente la mitad no es "más de la mitad"
    r2 = S.cruce_y_regla(np.array([0, 1, 0, 1]), np.array([0, 0, 1, 1]), np.ones(4), 2)
    assert not r2["cumple"].any() and not r2["global_cumple"]


def test_pct_deficit_y_jaccard():
    pct = S.pct_deficit_por_perfil([10, -5, 30, 60], [1, 1, 2, 2], 2)
    np.testing.assert_allclose(pct, [10, 90])
    idx = pd.MultiIndex.from_product([[1], [1, 2, 3, 4], [0], [1]], names=B.LLAVE)
    cp = pd.DataFrame({"objetivo": [True, True, False, False]}, index=idx)
    cs = pd.DataFrame({"objetivo": [True, False, True, False]}, index=idx)
    ln = pd.Series([10.0, 30.0, 20.0, 5.0], index=idx)
    r = S.comparar_objetivos(cp, cs, ln)
    assert r["celdas_interseccion"] == 1 and r["celdas_union"] == 3
    assert abs(r["frac_ln_sigue"] - 10 / 40) < 1e-12 and abs(r["jaccard_ln"] - 10 / 60) < 1e-12


def test_intermedias_menos_presidenciales():
    filas = []
    for a, d in zip((2009, 2012, 2015, 2018, 2021, 2024), (-4, 1, -4, 1, -4, 1)):
        filas.append((1, a, d, d + 2))
    t = pd.DataFrame(filas, columns=["perfil", "aelec", "dif_principal", "dif_concurrencia"])
    r = S.intermedias_menos_presidenciales(t)
    assert abs(r.inter_menos_pres_principal[0] + 5) < 1e-12 and abs(r.inter_menos_pres_concurrencia[0] + 5) < 1e-12


def test_tabla_perfil_eleccion_consistente():
    pan = panel_sintetico()
    p = S.preparar_panel(pan, "concurrencia", CONC)
    q0, qk = S.tasa_esperada_k(p), S.tasa_esperada_k(p, ["k"])
    perfil = p[B.LLAVE].drop_duplicates().copy()
    perfil["perfil"] = (perfil.seccion % 2 + 1).astype("int8")
    t = S.tabla_perfil_eleccion(p, perfil, q0, qk)
    assert len(t) == 2 * 2
    # todas las celdas en un solo perfil: la observada coincide con la nacional por elección y la esperada principal también
    perfil["perfil"] = 1
    t1 = S.tabla_perfil_eleccion(p, perfil, q0, qk)
    nac = pan.groupby("aelec").apply(lambda d: 100 * d.sv.sum() / (d.sv.sum() + d.nv.sum()), include_groups=False)
    np.testing.assert_allclose(t1.set_index("aelec").obs, nac)
    np.testing.assert_allclose(t1.set_index("aelec").esp_principal, nac)
