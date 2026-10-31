"""Pruebas de las fuentes externas (D-015). Requieren scripts/datos/fuentes_externas.py ejecutado."""
import pytest
from ine_perfiles import externos as X

pytestmark = pytest.mark.skipif(not X.OUT_ECEG2024.exists(), reason="corre scripts/datos/fuentes_externas.py")


def q(con, s):
    return con.execute(s).fetchall()


def test_cobertura_2021_eceg(con):
    n, c = q(con, f"""SELECT count(*), count(e.seccion) FROM
        (SELECT DISTINCT edo, seccion FROM ccpc WHERE aelec=2021) s
        LEFT JOIN read_parquet('{X.OUT_ECEG2020}') e USING (edo, seccion)""")[0]
    assert c / n >= 0.999  # valor auditado 99.99%


def test_cobertura_directa_2024(con):
    n = q(con, f"SELECT count(*) FROM read_parquet('{X.OUT_ECEG2024}') WHERE NOT eceg_heredado")[0][0]
    assert n == 67976


def test_2024_completa_y_herencia(con):
    n, h, nm = q(con, f"""SELECT count(*), sum(eceg_heredado::int), count(seccion_madre)
                          FROM read_parquet('{X.OUT_ECEG2024}')""")[0]
    assert n == 70751 and h == nm == 70751 - 67976


@pytest.mark.parametrize("archivo,llave", [
    ("OUT_ECEG2020", "edo, seccion"), ("OUT_ECEG2024", "edo, seccion"), ("OUT_RESID", "edo, seccion"),
    ("OUT_CONAPO", "edo, mpio"), ("OUT_CONCUR", "aelec, edo")])
def test_sin_duplicados(con, archivo, llave):
    p = getattr(X, archivo)
    assert q(con, f"SELECT count(*) - count(DISTINCT ({llave})) FROM read_parquet('{p}')")[0][0] == 0


@pytest.mark.parametrize("archivo", ["OUT_ECEG2020", "OUT_ECEG2024"])
def test_proporciones_en_0_1(con, archivo):
    for nom, *_ in X.DESCRIPTORES:
        mn, mx = q(con, f"SELECT min({nom}), max({nom}) FROM read_parquet('{getattr(X, archivo)}')")[0]
        assert 0 <= mn and mx <= 1, (nom, mn, mx)


def test_tipo_u_m_r(con):
    assert {r[0] for r in q(con, f"SELECT DISTINCT tipo FROM read_parquet('{X.OUT_ECEG2024}')")} == {"U", "M", "R"}


def test_herencia_copia_madre(con):
    n = q(con, f"""SELECT count(*) FROM read_parquet('{X.OUT_ECEG2024}') h
        JOIN read_parquet('{X.OUT_ECEG2020}') m ON m.edo=h.edo AND m.seccion=h.seccion_madre
        WHERE h.eceg_heredado AND h.graproes IS DISTINCT FROM m.graproes""")[0][0]
    assert n == 0


def test_residencia(con):
    mn, = q(con, f"SELECT count(*) FROM read_parquet('{X.OUT_RESID}') WHERE p_18ymas = 0 AND razon_ln_p18 IS NOT NULL")[0]
    assert mn == 0
    med = q(con, f"SELECT quantile_cont(razon_ln_p18, 0.5) FROM read_parquet('{X.OUT_RESID}')")[0][0]
    assert 1.13 < med < 1.15  # D-013: mediana 1.14


def test_conapo_cve_geo_5_digitos(con):
    r = q(con, f"""SELECT count(*) FROM read_parquet('{X.OUT_CONAPO}')
                   WHERE length(cve_geo) <> 5 OR NOT regexp_matches(cve_geo, '^[0-9]{{5}}$')""")
    assert r[0][0] == 0


def test_conapo_cobertura_ln(con):
    c, t = q(con, f"""WITH m AS (SELECT edo, mpio, sum(ln) ln FROM ccpc WHERE aelec=2024 GROUP BY 1,2)
        SELECT sum(CASE WHEN c.mpio IS NOT NULL THEN m.ln END), sum(m.ln)
        FROM m LEFT JOIN read_parquet('{X.OUT_CONAPO}') c ON c.edo=m.edo AND c.mpio=m.mpio""")[0]
    assert c / t > 0.99


def test_concurrencia(con):
    assert q(con, f"SELECT count(*) FROM read_parquet('{X.OUT_CONCUR}')")[0][0] == 6 * 32
    g = dict(q(con, f"SELECT aelec, sum(gubernatura) FROM read_parquet('{X.OUT_CONCUR}') GROUP BY 1"))
    assert g[2024] == 9 and g[2021] == 15
