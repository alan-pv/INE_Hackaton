"""Limpieza de la CCPC y tablas base (D-001, D-002, D-004, D-005, D-006).

Ninguna fila se elimina: solo se agregan banderas. Salidas en data/interim/base/.
"""
import shutil
from . import config as C
from .ingesta import conectar

BASE = C.RAIZ / "data" / "interim" / "base"
SECCION_ANIO = BASE / "seccion_anio.parquet"
CELDAS = BASE / "celdas.parquet"
CATALOGO = BASE / "catalogo_secciones.parquet"
MOV_COHORTE = BASE / "movilidad_cohorte.parquet"
MOV_SECCION = BASE / "movilidad_seccion.parquet"
MOV_SECCION_SEXO = BASE / "movilidad_seccion_sexo.parquet"

# D-004: 110 es el umbral DESCRIPTIVO usado en docs/investigacion/DATOS.md; solo para el
# reporte de sensibilidad. NO filtra nada.
EDAD_DESCRIPTIVA = 110


def _copy(con, query, destino):
    con.execute(f"COPY ({query}) TO '{destino}' (FORMAT parquet, COMPRESSION zstd)")


def seccion_anio(con):
    """D-002 / D-001: una fila por (aelec, edo, seccion). Si mpio/tiposec/def/del varían
    dentro del año se toma el de mayor LN. participacion NULL si sv+nv=0."""
    q = """
    WITH g AS (
      SELECT aelec, edo, seccion, mpio, mpionom, edonom, tiposec, def, "del",
             sum(ln) ln, sum(sv) sv, sum(nv) nv, sum(ns) ns
      FROM ccpc GROUP BY ALL),
    t AS (
      SELECT aelec, edo, seccion, sum(ln) ln, sum(sv) sv, sum(nv) nv, sum(ns) ns,
             count(DISTINCT mpio) n_mpio, count(DISTINCT tiposec) n_tiposec,
             arg_max(mpio, ln) mpio, arg_max(mpionom, ln) mpionom, arg_max(edonom, ln) edonom,
             arg_max(tiposec, ln) tiposec, arg_max(def, ln) def, arg_max("del", ln) "del"
      FROM g GROUP BY aelec, edo, seccion)
    SELECT aelec, edo, seccion, ln, sv, nv, ns,
           (sv + nv = 0) AS sin_observacion,
           CASE WHEN sv + nv = 0 THEN NULL ELSE sv::DOUBLE / (sv + nv) END AS participacion,
           CASE WHEN ln = 0 THEN NULL ELSE sv::DOUBLE / ln END AS cota_inf,
           CASE WHEN ln = 0 THEN NULL ELSE (sv + ns)::DOUBLE / ln END AS cota_sup,
           mpio, mpionom, edonom, tiposec, def, "del", n_mpio, n_tiposec
    FROM t ORDER BY aelec, edo, seccion"""
    _copy(con, q, SECCION_ANIO)


def celdas(con):
    """Celdas aelec x edo x seccion x sexo x edad con banderas; sin eliminar filas (D-004, D-005).

    cohorte = aelec - edad: año de nacimiento aproximado. La fecha de elección cae entre el
    2-jun y el 5-jul, así que, sin conocer el cumpleaños, el error de clasificación es <= 1 año
    y afecta igual a todas las secciones.
    """
    q = f"""
    SELECT c.aelec, c.edo, c.seccion, c.sexo, c.edad, c.aelec - c.edad AS cohorte,
           c.ln, c.sv, c.nv, c.ns,
           s.sin_observacion,
           (c.sexo = {C.SEXO_NO_BINARIO}) AS no_binario,
           (c.edad > {EDAD_DESCRIPTIVA}) AS edad_gt_110
    FROM ccpc c JOIN read_parquet('{SECCION_ANIO}') s USING (aelec, edo, seccion)"""
    _copy(con, q, CELDAS)


def catalogo(con):
    """Catálogo de secciones con atributos 2024 (o del último año presente + ref_anio)."""
    lns = ", ".join(f"max(CASE WHEN aelec={a} THEN ln END) AS ln_{a}" for a in C.ANIOS)
    q = f"""
    WITH s AS (SELECT * FROM read_parquet('{SECCION_ANIO}')),
    agg AS (
      SELECT edo, seccion, list(aelec ORDER BY aelec) anios_presente, count(*) n_anios,
             min(aelec) primer_anio, max(aelec) ultimo_anio,
             count(DISTINCT mpio) > 1 cambia_mpio, count(DISTINCT tiposec) > 1 cambia_tiposec,
             {lns}
      FROM s GROUP BY edo, seccion)
    SELECT a.edo, a.seccion, r.mpio AS mpio_2024, r.mpionom AS mpionom_2024,
           r.edonom AS edonom_2024, r.tiposec AS tiposec_2024, r.def AS def_2024,
           r."del" AS del_2024,
           a.ultimo_anio AS ref_anio,
           a.anios_presente, a.n_anios, a.primer_anio, a.ultimo_anio,
           a.cambia_mpio, a.cambia_tiposec,
           a.ln_2009, a.ln_2012, a.ln_2015, a.ln_2018, a.ln_2021, a.ln_2024
    FROM agg a JOIN s r ON r.edo=a.edo AND r.seccion=a.seccion AND r.aelec=a.ultimo_anio
    ORDER BY a.edo, a.seccion"""
    _copy(con, q, CATALOGO)


def movilidad(con):
    """D-006 (riesgo): crecimiento de la LN de la cohorte entre elecciones consecutivas,
    relativo al crecimiento nacional de la misma (sexo, cohorte). Solo sexo 0 y 1 (D-005).

    - Soporte comun: razon_nacional(sexo, cohorte) = sum ln_e / sum ln_prev solo sobre
      secciones presentes en AMBAS elecciones y cohortes con ln_prev nacional > 0 (las que
      entran a los 18 anios no tienen previa y quedan con razon_nacional NULL).
    - movilidad_cohorte (celda): log(razon_seccion/razon_nacional). A nivel de celda es
      RUIDOSA (desigualdad de Jensen en celdas pequenas): NO debe promediarse en logs.
    - movilidad_seccion: estandarizacion indirecta (tipo SMR). esperado = sum ln_prev *
      razon_nacional; observado = sum ln_e de las mismas cohortes (incluye celdas con
      ln_e=0); movilidad_rel = ln(observado/esperado). >0 llegada neta, <0 salida neta.
      Se calcula tambien por (seccion, sexo). Secciones no presentes en ambos anios:
      movilidad NULL y reseccionada_en_par=TRUE.
    """
    con.execute("SET preserve_insertion_order=false")
    tmp = BASE / "_mov_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    h, m = C.SEXO_HOMBRE, C.SEXO_MUJER
    for ep, e in zip(C.ANIOS[:-1], C.ANIOS[1:]):
        q = f"""
        WITH a AS (SELECT edo, seccion, sexo, cohorte, sum(ln) ln FROM read_parquet('{CELDAS}')
                   WHERE aelec={ep} AND sexo IN ({h},{m}) GROUP BY ALL),
        b AS (SELECT edo, seccion, sexo, cohorte, sum(ln) ln FROM read_parquet('{CELDAS}')
              WHERE aelec={e} AND sexo IN ({h},{m}) GROUP BY ALL),
        comun AS (SELECT edo, seccion FROM read_parquet('{SECCION_ANIO}') WHERE aelec IN ({ep},{e})
                  GROUP BY edo, seccion HAVING count(*) = 2),
        j AS (SELECT coalesce(a.edo,b.edo) edo, coalesce(a.seccion,b.seccion) seccion,
                     coalesce(a.sexo,b.sexo) sexo, coalesce(a.cohorte,b.cohorte) cohorte,
                     coalesce(a.ln,0) ln_prev, coalesce(b.ln,0) ln_e
              FROM a FULL JOIN b USING (edo, seccion, sexo, cohorte)),
        jc AS (SELECT j.*, (c.seccion IS NULL) AS reseccionada_en_par
               FROM j LEFT JOIN comun c USING (edo, seccion)),
        nac AS (SELECT sexo, cohorte, sum(ln_e)::DOUBLE / sum(ln_prev) razon_nacional
                FROM jc WHERE NOT reseccionada_en_par GROUP BY 1,2 HAVING sum(ln_prev) > 0)
        SELECT {ep} AS e_prev, {e} AS e, jc.edo, jc.seccion, jc.sexo, jc.cohorte, ln_prev, ln_e,
               CASE WHEN ln_prev>0 THEN ln_e::DOUBLE/ln_prev END AS razon_seccion,
               n.razon_nacional, reseccionada_en_par,
               CASE WHEN ln_prev>0 AND ln_e>0 AND n.razon_nacional IS NOT NULL
                    THEN ln(ln_e::DOUBLE/ln_prev / n.razon_nacional) END AS movilidad_rel
        FROM jc LEFT JOIN nac n USING (sexo, cohorte)"""
        _copy(con, q, tmp / f"{ep}_{e}.parquet")  # un archivo por par (memoria)
    _copy(con, f"SELECT * FROM read_parquet('{tmp}/*.parquet') "
               f"ORDER BY e_prev, edo, seccion, sexo, cohorte", MOV_COHORTE)
    shutil.rmtree(tmp)
    M = f"read_parquet('{MOV_COHORTE}')"
    for destino, claves in ((MOV_SECCION, "e_prev, e, edo, seccion"),
                            (MOV_SECCION_SEXO, "e_prev, e, edo, seccion, sexo")):
        q = f"""
        SELECT {claves}, reseccionada_en_par,
               CASE WHEN reseccionada_en_par THEN NULL ELSE obs_ END AS observado,
               CASE WHEN reseccionada_en_par THEN NULL ELSE esp_ END AS esperado,
               CASE WHEN NOT reseccionada_en_par AND esp_ > 0 AND obs_ > 0
                    THEN ln(obs_ / esp_) END AS movilidad_rel,
               n_ AS n_celdas
        FROM (SELECT {claves}, bool_or(reseccionada_en_par) AS reseccionada_en_par,
                     sum(ln_e) FILTER (razon_nacional IS NOT NULL) AS obs_,
                     sum(ln_prev * razon_nacional) AS esp_,
                     count(*) FILTER (razon_nacional IS NOT NULL) AS n_
              FROM {M} GROUP BY {claves})"""
        _copy(con, q, destino)


def correr_todo():
    BASE.mkdir(parents=True, exist_ok=True)
    con = conectar()
    seccion_anio(con)
    celdas(con)
    catalogo(con)
    movilidad(con)
    return con
