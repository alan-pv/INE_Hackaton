import pandas as pd
import pytest
from ine_perfiles import cohortes as B

pytestmark = pytest.mark.skipif(not B.PANEL.exists(), reason="corre scripts/preparacion/panel_cohortes.py")


@pytest.fixture(scope="module")
def panel():
    return pd.read_parquet(B.PANEL)


def test_conciliacion_2024(panel):
    con = B.conectar()
    sv, n = con.execute(f"""WITH cat AS (SELECT edo, seccion FROM read_parquet('{B.CATALOGO}') WHERE ref_anio=2024)
        SELECT sum(sv), sum(sv+nv) FROM read_parquet('{B.CELDAS}') c JOIN cat USING (edo, seccion)
        WHERE aelec=2024 AND sexo<2 AND NOT sin_observacion""").fetchone()
    p = panel[panel.aelec == 2024]
    assert int(p.sv.sum()) == int(sv) and int(p.n.sum()) == int(n)


def test_solo_sexo_binario(panel):
    assert set(panel.sexo.unique()) <= {0, 1}


def test_claves_unicas(panel):
    assert not panel.duplicated(["edo", "seccion", "sexo", "grupo", "aelec"]).any()


def test_n_es_sv_mas_nv(panel):
    assert (panel.n == panel.sv + panel.nv).all()


def test_fraccion_cohortes_18_19_solo_en_2024():
    fr = B.fraccion_cohortes()
    assert fr[(1, 2024)] == 1.0 and all(fr[(1, a)] == 0.0 for a in B.ELEC if a < 2024)
