"""Marca de cambios territoriales (reseccionamiento) en la movilidad de electores (D-015, D-016).
Salidas: data/interim/base/{cambios_territoriales,movilidad_seccion_marcada}.parquet,
reports/datos/cambios_territoriales/control.md
Uso: .venv/bin/python scripts/datos/cambios_territoriales.py"""

import duckdb
import pandas as pd

from ine_perfiles import config as C
from ine_perfiles import territorio as T


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def main():
    ev, info = T.leer_eventos()
    con = duckdb.connect()
    T.OUT_EVENTOS.parent.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(T.OUT_EVENTOS, index=False)
    T.marcar(con, ev)
    M = f"'{T.OUT_MARCADA}'"
    n0 = con.execute(f"SELECT count(*) FROM '{T.BASE / 'movilidad_seccion.parquet'}'").fetchone()[0]
    n1 = con.execute(f"SELECT count(*) FROM {M}").fetchone()[0]

    L = ["# Cambios territoriales en la movilidad (D-015)", "",
         "Generado por `scripts/datos/cambios_territoriales.py`. La marca sale SOLO de la tabla de equivalencias "
         "(Magar, de terceros, no validada contra anexos del INE); ningún umbral de valores.", "",
         "## Interpretación de la tabla (igual que `externos._tabla_equiv`)", "",
         "- Hasta 3 eventos por fila: `action/orig.dest/when`, `action2/...`, `action3/...`.",
         "- `split.from`: la sección es hija (alta); `orig.dest` = madres (`a|b`). `split.to`: la sección es madre; "
         "`orig.dest` = hijas (rango `a:b` o `a|b`). `merged.to`: la sección se da de baja y `orig.dest` es la receptora. "
         "`mun.chg` / `state.chg`: cambio de municipio / entidad (sin sección relacionada).",
         "- Además de la fila propia se genera el evento en la contraparte (madre vigente de una división = `division_madre`; "
         "receptora de una fusión = `fusion_receptora`), que conserva su número: es el caso que la limpieza no detectaba por sí sola.",
         f"- Año del evento = `when` (primeros 4 dígitos). Respaldo si falta o no es numérico: `alta` para `split.from`, `baja` para el resto. "
         f"Usos del respaldo: {info['anio_de_respaldo']}; eventos sin año (descartados): {info['sin_anio']}.",
         f"- Ventana {T.ANIO_MIN}-{T.ANIO_MAX}. Un evento marca el par (e_prev, e] si e_prev < anio_evento <= e. "
         "Limitación: la tabla da año, no fecha; un evento del año de la elección (p. ej. 2021) puede ser posterior a la jornada.",
         "- Los eventos de 2025 de la tabla son provisionales y quedan fuera de la ventana.", "",
         f"Filas de la tabla: {info['filas_tabla']:,}. Eventos 2009-2024: {len(ev):,} filas, "
         f"{ev[['edo','seccion']].drop_duplicates().shape[0]:,} secciones.", "",
         "## Eventos por tipo y año", ""]
    L.append(md(ev.pivot_table(index="anio_evento", columns="tipo_evento", values="seccion", aggfunc="count", fill_value=0).reset_index()))

    L += ["", "## Conciliación", "", f"- Filas `movilidad_seccion`: {n0:,}; `movilidad_seccion_marcada`: {n1:,}; "
          f"{'OK' if n0 == n1 else 'FALLA'}."]
    pares = con.execute(f"""SELECT e_prev||'→'||e AS par, count(*) AS secciones,
        sum(cambio_territorial_en_par::int) AS marcadas,
        round(100.0*sum(cambio_territorial_en_par::int)/count(*),2) AS pct_marcadas,
        sum((cambio_territorial_en_par AND reseccionada_en_par)::int) AS marcadas_y_reseccionada,
        sum((cambio_territorial_en_par AND NOT reseccionada_en_par)::int) AS marcadas_conservan_numero
        FROM {M} GROUP BY e_prev, e ORDER BY e_prev""").df()
    L += ["", "## Marcas por par", "", md(pares), "",
          "`reseccionada_en_par` es la bandera de la limpieza (presencia en el catálogo); `marcadas_conservan_numero` son las que esa bandera no veía.", ""]

    # tipo de evento entre marcadas
    tip = con.execute(f"""SELECT e_prev||'→'||e AS par, tipo_evento, count(*) AS n FROM {M}
        WHERE cambio_territorial_en_par GROUP BY ALL ORDER BY 1, 3 DESC""").df()
    L += ["## Combinaciones de tipo de evento entre marcadas", "", md(tip), ""]

    # Hueyapan
    L += ["## Validación: Hueyapan, Morelos (edo 17, secciones 700-702)", ""]
    t = pd.read_csv(T.EQUIV, dtype=str)
    h = t[(t.edon == "17") & t.seccion.isin(["700", "701", "702"])]
    L += ["Filas de la tabla (campos relevantes):", "", md(h[["seccion", "mun", "alta", "baja", "action", "when", "OBSERVACIONES"]].fillna("")), ""]
    hu = con.execute(f"""SELECT e_prev||'→'||e AS par, seccion, observado, round(esperado,1) AS esperado,
        round(movilidad_rel,3) AS movilidad_rel, reseccionada_en_par, cambio_territorial_en_par, tipo_evento
        FROM {M} WHERE edo=17 AND seccion IN (700,701,702) AND e_prev>=2018 ORDER BY e_prev, seccion""").df()
    L += [md(hu), ""]
    marcado = bool(con.execute(f"SELECT bool_or(cambio_territorial_en_par) FROM {M} WHERE edo=17 AND seccion=701 AND e_prev=2021").fetchone()[0])
    marcado18 = bool(con.execute(f"SELECT bool_or(cambio_territorial_en_par) FROM {M} WHERE edo=17 AND seccion=701 AND e_prev=2018").fetchone()[0])
    L += [f"**Resultado:** 17-701 en el par 2021→2024 {'SÍ' if marcado else 'NO'} queda marcado; en 2018→2021 {'SÍ' if marcado18 else 'NO'}. ",
          "Hallazgo: en la CCPC las tres secciones tienen LN ≈10 (701) y 62 (702) en 2021 y ≈1,300-1,450 en 2024. La anomalía de 2021→2024 es "
          "el reflejo de que la sección estaba casi vacía en 2021 (la tabla no registra evento: alta 1993, sin `action`). "
          "La columna OBSERVACIONES de la tabla dice que hubo controversia ante la SCJN y que el municipio se incorporó tarde "
          "(por eso la LN de 2021 es casi nula). La tabla NO lo codifica como evento, así que la marca por tabla no lo captura; "
          "es un caso de creación/incorporación tardía de municipio que requiere una regla complementaria (D-016).", ""]

    # colas
    d = con.execute(f"""SELECT e_prev||'→'||e AS par, cambio_territorial_en_par AS marcada, count(*) AS n,
        round(median(abs(movilidad_rel)),4) AS mediana,
        round(quantile_cont(abs(movilidad_rel),0.9),4) AS p90,
        round(quantile_cont(abs(movilidad_rel),0.99),4) AS p99,
        round(max(abs(movilidad_rel)),3) AS maximo,
        round(100.0*avg((abs(movilidad_rel)>0.5)::int),2) AS pct_abs_gt_0_5
        FROM {M} WHERE movilidad_rel IS NOT NULL GROUP BY 1, 2 ORDER BY 1, 2""").df()
    L += ["## Colas de |movilidad_rel|: marcadas vs no marcadas", "",
          "(`pct_abs_gt_0_5` es solo descriptiva de la cola; no se usa para marcar nada. Solo hay `movilidad_rel` en secciones presentes en ambas elecciones, por eso `n` de las marcadas coincide con `marcadas_conservan_numero`.)", "", md(d), ""]

    top = con.execute(f"""SELECT edo, seccion, observado, round(esperado,1) AS esperado, round(movilidad_rel,3) AS movilidad_rel,
        reseccionada_en_par FROM {M} WHERE e_prev=2021 AND e=2024 AND NOT cambio_territorial_en_par AND movilidad_rel IS NOT NULL
        ORDER BY abs(movilidad_rel) DESC LIMIT 20""").df()
    L += ["## Top-20 |movilidad_rel| 2021→2024 NO marcadas (posibles cambios no registrados en la tabla)", "",
          "Sin filtro por umbral; se listan tal cual.", "", md(top), ""]
    (C.salidas(__file__) / "control.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
