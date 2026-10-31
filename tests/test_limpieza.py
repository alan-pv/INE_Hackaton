import pytest
from ine_perfiles import config as C
from ine_perfiles import limpieza as L

pytestmark = pytest.mark.skipif(not L.CATALOGO.exists(), reason="corre scripts/datos/limpieza_ccpc.py")


def q(con, s):
    return con.execute(s).fetchall()


def test_celdas_suman_igual_que_ccpc(con):
    a = q(con, "SELECT aelec, sum(ln), sum(sv), sum(nv), sum(ns), count(*) FROM ccpc GROUP BY 1 ORDER BY 1")
    b = q(con, f"SELECT aelec, sum(ln), sum(sv), sum(nv), sum(ns), count(*) "
               f"FROM read_parquet('{L.CELDAS}') GROUP BY 1 ORDER BY 1")
    assert a == b


def test_seccion_anio_suma_igual(con):
    a = q(con, "SELECT aelec, sum(ln), sum(sv), sum(nv), sum(ns) FROM ccpc GROUP BY 1 ORDER BY 1")
    b = q(con, f"SELECT aelec, sum(ln), sum(sv), sum(nv), sum(ns) FROM read_parquet('{L.SECCION_ANIO}') GROUP BY 1 ORDER BY 1")
    assert a == b


@pytest.mark.parametrize("anio", sorted(C.CIFRAS_CONTROL))
def test_participacion_nacional_desde_seccion_anio(con, anio):
    v = q(con, f"SELECT 100*sum(sv)/sum(sv+nv) FROM read_parquet('{L.SECCION_ANIO}') WHERE aelec={anio}")[0][0]
    val, tol = C.CIFRAS_CONTROL[anio]["nacional"]
    assert abs(v - val) <= tol


def test_participacion_en_0_1_y_nula_si_sin_obs(con):
    S = f"read_parquet('{L.SECCION_ANIO}')"
    assert q(con, f"SELECT count(*) FROM {S} WHERE participacion<0 OR participacion>1")[0][0] == 0
    assert q(con, f"SELECT count(*) FROM {S} WHERE (participacion IS NULL) <> sin_observacion")[0][0] == 0


def test_cotas_ordenadas(con):
    S = f"read_parquet('{L.SECCION_ANIO}')"
    n = q(con, f"SELECT count(*) FROM {S} WHERE participacion IS NOT NULL AND "
               f"NOT (cota_inf <= participacion + 1e-12 AND participacion <= cota_sup + 1e-12)")[0][0]
    assert n == 0


def test_catalogo_2024(con):
    K = f"read_parquet('{L.CATALOGO}')"
    assert q(con, f"SELECT count(*) FROM {K} WHERE ref_anio=2024")[0][0] == C.SECCIONES_2024
    assert q(con, f"SELECT count(*) FROM {K} WHERE ref_anio=2024 AND mpio_2024 IS NULL")[0][0] == 0
    assert q(con, f"SELECT count(*) - count(DISTINCT (edo, seccion)) FROM {K}")[0][0] == 0


def test_cohorte(con):
    K = f"read_parquet('{L.CELDAS}')"
    assert q(con, f"SELECT count(*) FROM {K} WHERE cohorte <> aelec - edad")[0][0] == 0


def test_banderas(con):
    K = f"read_parquet('{L.CELDAS}')"
    assert q(con, f"SELECT count(*) FROM {K} WHERE no_binario <> (sexo={C.SEXO_NO_BINARIO})")[0][0] == 0
    assert q(con, f"SELECT count(*) FROM {K} WHERE edad_gt_110 <> (edad>110)")[0][0] == 0


def test_movilidad_observado_igual_esperado_nacional(con):
    r = q(con, f"SELECT e_prev, sum(observado)/sum(esperado) FROM read_parquet('{L.MOV_SECCION}') "
               f"WHERE NOT reseccionada_en_par GROUP BY 1")
    assert len(r) == 5
    for _, v in r:
        assert abs(v - 1) < 1e-9


def test_movilidad_seccion_sexo_consistente(con):
    r = q(con, f"SELECT e_prev, sum(observado)/sum(esperado) FROM read_parquet('{L.MOV_SECCION_SEXO}') "
               f"WHERE NOT reseccionada_en_par GROUP BY 1")
    assert all(abs(v - 1) < 1e-9 for _, v in r)


def test_reseccionadas_sin_movilidad(con):
    assert q(con, f"SELECT count(*) FROM read_parquet('{L.MOV_SECCION}') "
                  f"WHERE reseccionada_en_par AND movilidad_rel IS NOT NULL")[0][0] == 0
