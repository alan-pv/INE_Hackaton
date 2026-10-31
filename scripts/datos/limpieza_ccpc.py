"""Limpieza de la CCPC y tablas base (D-001, D-002, D-004, D-005, D-006).
Construye data/interim/base/ (celdas, catálogo de secciones, movilidad) y verifica las cifras de control de participación.
Salidas: reports/datos/limpieza_ccpc/control.md
Uso: .venv/bin/python scripts/datos/limpieza_ccpc.py"""
import time

from ine_perfiles import config as C
from ine_perfiles import limpieza as L


SIN_COMA = {"aelec", "e_prev", "e", "edo", "mpio", "seccion"}


def tabla(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        celdas = []
        for c, v in zip(cols, r):
            if isinstance(v, float) and v == v and v.is_integer() and "pct" not in c and "p" != c[0]:
                v = int(v)
            if c in SIN_COMA:
                celdas.append(str(int(v)))
            elif isinstance(v, int):
                celdas.append(f"{v:,}")
            else:
                celdas.append(f"{v:,.4f}" if isinstance(v, float) else str(v))
        out.append("| " + " | ".join(celdas) + " |")
    return "\n".join(out)


def main():
    t0 = time.time()
    con = L.correr_todo()
    t_proc = time.time() - t0
    S, K, CAT, MC, MS = (f"read_parquet('{p}')" for p in
                         (L.SECCION_ANIO, L.CELDAS, L.CATALOGO, L.MOV_COHORTE, L.MOV_SECCION))
    df = lambda q: con.execute(q).df()
    md = ["# Limpieza de la CCPC y tablas base", "",
          f"Tiempo de procesamiento: {t_proc:.0f} s. Decisiones: D-001, D-002, D-004, D-005, D-006.", ""]

    # 1. sin observación (D-002)
    md += ["## 1. Secciones sin observación por año (D-002)", "",
           tabla(df(f"""SELECT aelec, count(*) secciones, sum(sin_observacion::INT) sin_obs,
             sum(ln) FILTER (sin_observacion) ln_sin_obs,
             round(100*sum(ln) FILTER (sin_observacion)/sum(ln),3) pct_ln FROM {S} GROUP BY 1 ORDER BY 1""")), "",
           "Top-5 estados por LN sin observación (por año):", ""]
    for a in C.ANIOS:
        d = df(f"""SELECT {a} aelec, edo, sum(sin_observacion::INT) sin_obs,
          sum(ln) FILTER (sin_observacion) ln_sin_obs FROM {S} WHERE aelec={a}
          GROUP BY edo ORDER BY ln_sin_obs DESC NULLS LAST LIMIT 5""")
        md += [f"**{a}**", "", tabla(d.fillna(0).astype({"ln_sin_obs": int})), ""]

    # 2. participación nacional y cotas
    md += ["## 2. Participación oficial y cotas de Manski nacionales (D-001)", "",
           "Recomputada desde `seccion_anio` (suma de sv, nv, ns).", "",
           tabla(df(f"""SELECT aelec, round(100*sum(sv)/sum(sv+nv),3) participacion_pct,
             round(100*sum(sv)/sum(ln),3) cota_inf_pct, round(100*sum(sv+ns)/sum(ln),3) cota_sup_pct
             FROM {S} GROUP BY 1 ORDER BY 1""")), "",
           "Cifras de control:", ""]
    ctl = []
    for a, cc in sorted(C.CIFRAS_CONTROL.items()):
        v = con.execute(f"SELECT 100*sum(sv)/sum(sv+nv) FROM {S} WHERE aelec={a}").fetchall()[0][0]
        ctl.append(f"- {a}: calculado {v:.3f} vs control {cc['nacional'][0]} "
                   f"(tol {cc['nacional'][1]}): {'OK' if abs(v-cc['nacional'][0])<=cc['nacional'][1] else 'FALLA'}")
    md += ctl + [""]

    # 3. edad > 110 (D-004)
    md += ["## 3. Edad > 110 vs resto (D-004; solo sensibilidad, no filtra)", "",
           tabla(df(f"""SELECT aelec, edad_gt_110, sum(ln) ln, sum(sv) sv, sum(nv) nv, sum(ns) ns,
             round(100*sum(sv)/nullif(sum(sv+nv),0),3) participacion_pct
             FROM {K} GROUP BY 1,2 ORDER BY 1,2""")), ""]

    # 4. n_anios y cambios
    md += ["## 4. Catálogo", "",
           f"Secciones en el catálogo: {con.execute(f'SELECT count(*) FROM {CAT}').fetchall()[0][0]:,}", "",
           tabla(df(f"SELECT n_anios, count(*) secciones FROM {CAT} GROUP BY 1 ORDER BY 1")), "",
           tabla(df(f"""SELECT sum(cambia_mpio::INT) cambian_mpio, sum(cambia_tiposec::INT) cambian_tiposec,
             sum((ref_anio<>2024)::INT) sin_2024_ref_otro_anio FROM {CAT}""")), "",
           "Secciones con >1 mpio o >1 tiposec dentro de un mismo año (se tomó el de mayor LN):", "",
           tabla(df(f"""SELECT aelec, sum((n_mpio>1)::INT) multi_mpio, sum((n_tiposec>1)::INT) multi_tiposec
             FROM {S} GROUP BY 1 ORDER BY 1""")), ""]

    # 5. movilidad
    md += ["## 5. Movilidad por cohorte (riesgo D-006)", "",
           "Estandarizacion indirecta: esperado = sum ln_prev x razon_nacional(sexo, cohorte) sobre el "
           "soporte comun (secciones presentes en ambos anios, cohortes con ln_prev nacional > 0); "
           "observado = sum ln_e; movilidad_rel = ln(observado/esperado). >0 llegada neta, <0 salida neta.", "",
           "Secciones reseccionadas por par (movilidad NULL) y verificacion sum(obs)/sum(esp) = 1:", "",
           tabla(df(f"""SELECT e_prev, e, count(*) secciones, sum(reseccionada_en_par::INT) reseccionadas,
             sum(observado) observado, sum(esperado) esperado,
             round(sum(observado)/sum(esperado),8) obs_sobre_esp FROM {MS} GROUP BY 1,2 ORDER BY 1,2""")), "",
           "Casos aparte a nivel celda (sexo x cohorte x seccion; ln_prev=0 incluye cohortes que aun no existian):", "",
           tabla(df(f"""SELECT e_prev, e, count(*) celdas,
             sum((ln_prev=0)::INT) ln_prev_0, sum((ln_e=0)::INT) ln_e_0,
             sum((movilidad_rel IS NOT NULL)::INT) con_movilidad FROM {MC} GROUP BY 1,2 ORDER BY 1,2""")), "",
           "Distribucion de movilidad_rel de seccion (p10/p50/p90):", "",
           tabla(df(f"""SELECT e_prev, e, count(movilidad_rel) secciones,
             round(quantile_cont(movilidad_rel,0.1),4) p10, round(quantile_cont(movilidad_rel,0.5),4) p50,
             round(quantile_cont(movilidad_rel,0.9),4) p90 FROM {MS} GROUP BY 1,2 ORDER BY 1,2""")), "",
           "Por sexo (seccion x sexo):", "",
           tabla(df(f"""SELECT e_prev, e, sexo, count(movilidad_rel) filas,
             round(quantile_cont(movilidad_rel,0.1),4) p10, round(quantile_cont(movilidad_rel,0.5),4) p50,
             round(quantile_cont(movilidad_rel,0.9),4) p90 FROM read_parquet('{L.MOV_SECCION_SEXO}')
             GROUP BY 1,2,3 ORDER BY 1,2,3""")), ""]
    muni = f"""SELECT c.edo, c.mpio_2024 mpio, any_value(c.mpionom_2024) municipio, count(*) secciones,
        round(ln(sum(s.observado)/sum(s.esperado)),4) movilidad_municipio
      FROM {MS} s JOIN {CAT} c USING (edo, seccion)
      WHERE s.e_prev=2021 AND s.e=2024 AND s.movilidad_rel IS NOT NULL GROUP BY c.edo, c.mpio_2024"""
    md += ["Top-10 municipios con movilidad mas negativa 2021->2024 (ln de sum obs / sum esp):", "",
           tabla(df(f"SELECT * FROM ({muni}) ORDER BY movilidad_municipio LIMIT 10")), "",
           "Top-10 mas positiva:", "",
           tabla(df(f"SELECT * FROM ({muni}) ORDER BY movilidad_municipio DESC LIMIT 10")), ""]

    (C.salidas(__file__) / "control.md").write_text("\n".join(md))
    print(f"OK {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
