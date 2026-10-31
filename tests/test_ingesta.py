import pytest
from ine_perfiles import config as C


def test_filas_por_anio(con):
    r = dict(con.execute("SELECT aelec, count(*) FROM ccpc GROUP BY 1").fetchall())
    assert r == C.FILAS_ESPERADAS


def test_secciones_2024(con):
    n = con.execute("SELECT count(DISTINCT (edo, seccion)) FROM ccpc WHERE aelec=2024").fetchall()[0][0]
    assert n == C.SECCIONES_2024


def test_ln_igual_suma(con):
    assert con.execute("SELECT count(*) FROM ccpc WHERE ln <> sv+nv+ns").fetchall()[0][0] == 0


@pytest.mark.parametrize("col", ["aelec", "edo", "mpio", "seccion", "sexo", "edad", "ln", "sv", "nv", "ns"])
def test_sin_nulos_estrictas(con, col):
    assert con.execute(f"SELECT count(*) FROM ccpc WHERE {col} IS NULL").fetchall()[0][0] == 0


def _part(con, anio, sexo=None):
    f = "" if sexo is None else f"AND sexo={sexo}"
    sv, nv = con.execute(f"SELECT sum(sv), sum(nv) FROM ccpc WHERE aelec={anio} {f}").fetchall()[0]
    return 100 * sv / (sv + nv)


@pytest.mark.parametrize("anio", sorted(C.CIFRAS_CONTROL))
def test_cifras_control(con, anio):
    cc = C.CIFRAS_CONTROL[anio]
    for clave, sexo in (("nacional", None), ("mujeres", C.SEXO_MUJER), ("hombres", C.SEXO_HOMBRE)):
        valor, tol = cc[clave]
        assert abs(_part(con, anio, sexo) - valor) <= tol, (anio, clave)
