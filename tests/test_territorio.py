"""Pruebas de los cambios territoriales (D-015)."""
import duckdb
import pytest

from ine_perfiles import territorio as T


@pytest.fixture(scope="module")
def tablas():
    if not (T.OUT_EVENTOS.exists() and T.OUT_MARCADA.exists()):
        pytest.skip("corre scripts/datos/cambios_territoriales.py")
    return duckdb.connect()


def test_parseo_numeros():
    assert T._numeros("646:648") == [646, 647, 648]
    assert T._numeros("366|408|459") == [366, 408, 459]
    assert T._numeros(None) == []


def test_claves_unicas(tablas):
    n, u = tablas.execute(f"""SELECT count(*), count(DISTINCT (e_prev, e, edo, seccion))
                              FROM '{T.OUT_MARCADA}'""").fetchone()
    assert n == u
    n, u = tablas.execute(f"""SELECT count(*), count(DISTINCT (edo, seccion, anio_evento, tipo_evento, seccion_relacionada))
                              FROM '{T.OUT_EVENTOS}'""").fetchone()
    assert n == u


def test_mismas_filas_que_movilidad(tablas):
    a = tablas.execute(f"SELECT count(*) FROM '{T.BASE / 'movilidad_seccion.parquet'}'").fetchone()[0]
    b = tablas.execute(f"SELECT count(*) FROM '{T.OUT_MARCADA}'").fetchone()[0]
    assert a == b


def test_ventana_y_madre_conserva_numero(tablas):
    mn, mx = tablas.execute(f"SELECT min(anio_evento), max(anio_evento) FROM '{T.OUT_EVENTOS}'").fetchone()
    assert T.ANIO_MIN <= mn and mx <= T.ANIO_MAX
    # caso Ags 487 (hija 2004, fuera de ventana) -> usar una división dentro de ventana: toda hija tiene madre registrada
    sin_madre = tablas.execute(f"""SELECT count(*) FROM '{T.OUT_EVENTOS}' h
        WHERE tipo_evento='alta_por_division' AND seccion_relacionada IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM '{T.OUT_EVENTOS}' m WHERE m.edo=h.edo AND m.seccion=h.seccion_relacionada
            AND m.seccion_relacionada=h.seccion AND m.anio_evento=h.anio_evento AND m.tipo_evento='division_madre')""").fetchone()[0]
    assert sin_madre == 0


def test_hueyapan_reportado(tablas):
    """Se reporta (no se exige) si la tabla marca 17-701; el test fija el resultado observado."""
    r = tablas.execute(f"""SELECT cambio_territorial_en_par FROM '{T.OUT_MARCADA}'
                           WHERE edo=17 AND seccion=701 AND e_prev=2021 AND e=2024""").fetchone()
    assert r is not None
    assert r[0] is False  # la tabla no registra evento para 17-700/701/702 (ver reports/datos/cambios_territoriales/control.md)
    assert "Hueyapan" in open(T.RAIZ / "reports" / "datos" / "cambios_territoriales" / "control.md", encoding="utf-8").read()
