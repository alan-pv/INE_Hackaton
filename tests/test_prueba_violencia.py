"""Pruebas de la prueba de violencia y del ΔAUC con datos sintéticos (D-027)."""
import numpy as np
import pandas as pd

from ine_perfiles import evaluacion as CF
from ine_perfiles import config as C


def _datos(n_sec=60, por_sec=6, seed=0):
    r = np.random.default_rng(seed)
    edo = np.repeat(r.integers(1, 5, n_sec), por_sec)
    sec = np.repeat(np.arange(n_sec), por_sec)
    ln = r.integers(10, 200, len(sec)).astype(float)
    d = r.normal(0, 5, len(sec))
    return edo, sec, ln, d


def test_auc_replica_igual_curva_captura_replicada():
    edo, sec, ln, d = _datos()
    r = np.random.default_rng(1).integers(0, 5, len(ln)).astype(float)   # con empates
    post = np.random.default_rng(2).random(len(ln)) < 0.2
    out = CF.delta_auc_bootstrap(r, post, -r, None, ln, d, edo, sec, B=39)
    assert abs(out["auc1"] - CF.curva_captura(r, ln, d, post)[1]) < 1e-12
    assert abs(out["auc2"] - CF.curva_captura(-r, ln, d)[1]) < 1e-12
    # una réplica con multiplicidades conocidas == curva_captura sobre las filas replicadas
    mult = np.random.default_rng(3).integers(0, 3, len(ln)).astype(float)
    o, ini = CF._orden_bloques(r, post)
    rep = np.repeat(np.arange(len(ln)), mult.astype(int))
    esp = CF.curva_captura(r[rep], ln[rep], d[rep], post[rep])[1]
    assert abs(CF._auc_pos_bloques(o, ini, ln, np.clip(d, 0, None), mult) - esp) < 1e-12


def test_rankings_identicos_delta_cero():
    edo, sec, ln, d = _datos()
    r = np.random.default_rng(4).random(len(ln))
    out = CF.delta_auc_bootstrap(r, None, r.copy(), None, ln, d, edo, sec, B=39)
    assert out["delta"] == 0 and (out["deltas"] == 0).all() and out["lo"] == 0 and out["hi"] == 0


def test_perfecto_contra_azar_excluye_cero():
    edo, sec, ln, d = _datos()
    perfecto = -d                       # ordena de mayor a menor déficit: menor r̂ = más déficit
    azar = np.random.default_rng(5).random(len(ln))
    out = CF.delta_auc_bootstrap(perfecto, None, azar, None, ln, d, edo, sec, B=C.B_PERMANENCIA)
    assert out["lo"] > 0 and out["delta"] > 0
    assert len(out["deltas"]) == 1999


def test_reproducible_con_la_semilla():
    edo, sec, ln, d = _datos()
    r1 = np.random.default_rng(6).random(len(ln))
    r2 = np.random.default_rng(7).random(len(ln))
    a = CF.delta_auc_bootstrap(r1, None, r2, None, ln, d, edo, sec, B=39)
    b = CF.delta_auc_bootstrap(r1, None, r2, None, ln, d, edo, sec, B=39)
    c = CF.delta_auc_bootstrap(r1, None, r2, None, ln, d, edo, sec, B=39, sufijo=99)
    assert (a["deltas"] == b["deltas"]).all() and not (a["deltas"] == c["deltas"]).all()


def test_indice_percentil_davison_hinkley():
    edo, sec, ln, d = _datos()
    r1 = np.random.default_rng(6).random(len(ln))
    r2 = np.random.default_rng(7).random(len(ln))
    out = CF.delta_auc_bootstrap(r1, None, r2, None, ln, d, edo, sec, B=C.B_PERMANENCIA)
    s = np.sort(out["deltas"])
    assert out["lo"] == s[49] and out["hi"] == s[1949]      # (B+1)*0.025 = 50


def test_violencia_a_secciones_y_celdas():
    desc = pd.DataFrame(dict(edo=[1, 1, 2], mpio=[1, 2, 1], seccion=[10, 11, 10]))
    viol = pd.DataFrame(dict(edo=[1, 2], mpio=[1, 1], v=[-9.0, -8.0]))
    v = CF.violencia_a_secciones(desc, viol, "v")
    assert v[0] == -9.0 and np.isnan(v[1]) and v[2] == -8.0
    cel = pd.DataFrame(dict(edo=[2, 1, 1], seccion=[10, 10, 11]))
    c = CF.a_celdas(cel, desc, v)
    assert c[0] == -8.0 and c[1] == -9.0 and np.isnan(c[2])


def test_primera_replica_igual_curva_captura_sobre_filas_replicadas():
    from ine_perfiles import estabilidad as EST
    edo, sec, ln, d = _datos(seed=8)
    r1 = np.random.default_rng(9).integers(0, 6, len(ln)).astype(float)
    r2 = np.random.default_rng(10).random(len(ln))
    out = CF.delta_auc_bootstrap(r1, None, r2, None, ln, d, edo, sec, B=39)
    orden, ini, lar, es = EST.indice_secciones(edo, sec)
    rng = np.random.default_rng([C.SEMILLA, C.SUFIJO_SEMILLA_PERMANENCIA])
    filas, _ = EST.remuestrear_secciones(rng, es, orden, ini, lar)
    a1 = CF.curva_captura(r1[filas], ln[filas], d[filas])[1]
    a2 = CF.curva_captura(r2[filas], ln[filas], d[filas])[1]
    assert abs(out["auc1_rep"][0] - a1) < 1e-12 and abs(out["auc2_rep"][0] - a2) < 1e-12
