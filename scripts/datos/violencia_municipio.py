"""Violencia homicida municipal (D-027): solo descriptor de los perfiles.
Descarga (si falta) los microdatos de defunciones de INEGI, agrega por municipio y año de ocurrencia,
mapea a municipios INE y calcula la tasa cruda y la contraída por ventana.
Salidas: data/interim/externos/violencia_mpio.parquet, reports/datos/violencia_municipio/control.md
Uso: .venv/bin/python scripts/datos/violencia_municipio.py"""
import time

import numpy as np
import pandas as pd

from ine_perfiles import config as C
from ine_perfiles import externos as X
from ine_perfiles import violencia as V

# Cifras oficiales de INEGI (defunciones por homicidio, año de REGISTRO) para contrastar las ediciones.
# (valor, fuente). Referencias completas en docs/DATOS.md.
OFICIAL_REGISTRO = {
    2009: (19803, "prensa que cita a INEGI (La Opinión; sin boletín oficial localizado)"),
    2010: (25757, "prensa que cita a INEGI (La Opinión; sin boletín oficial localizado)"),
    2011: (27213, "prensa que cita a INEGI (La Opinión; sin boletín oficial localizado)"),
    2019: (36476, "boletín INEGI 2020, dato PRELIMINAR"),
    2020: (36773, "boletín INEGI 2021, resultados definitivos"),
    2022: (32223, "boletín INEGI 2023, dato PRELIMINAR"),
    2024: (33550, "prensa que cita resultados definitivos de INEGI (Excélsior)"),
}


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    df = df.copy()
    for c in df.columns:  # años y claves sin separador de miles; conteos enteros sin decimales
        if any(k in str(c) for k in ("año", "edicion", "primer_anio", "edo", "mpio")):
            df[c] = df[c].map(lambda v: str(int(v)) if pd.notna(v) and float(v) == int(v) else str(v))
        elif str(c).startswith("hom_") or c in ("n_hom", "poblacion"):
            df[c] = df[c].map(lambda v: int(v) if pd.notna(v) else v)
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:,.3f}" if isinstance(v, (float, np.floating)) else
                                     f"{v:,}" if isinstance(v, (int, np.integer)) else str(v) for v in r) + " |")
    return "\n".join(out)


def main():
    t0 = time.time()
    V.descargar()
    agg, ctrl = V.cargar_agregado()

    # mapeo INEGI -> INE: el mismo de CONAPO (externos.mapa_municipios) restringido a las claves retenidas
    mapa, _, _ = X.mapa_municipios()
    cp = pd.read_parquet(X.OUT_CONAPO)[["edo", "mpio", "cve_geo", "pob_tot_conapo"]]
    mapa = mapa.rename(columns={"mpio_ine": "mpio"})[["edo", "mpio", "cve_geo"]].astype({"edo": int, "mpio": int})
    mapa = mapa.merge(cp[["edo", "mpio", "cve_geo"]], on=["edo", "mpio", "cve_geo"], how="inner")
    res, tabs, aud = V.construir(agg, mapa, cp[["edo", "mpio", "pob_tot_conapo"]])
    res = res.drop(columns="primer_anio").merge(
        V.primera_aparicion(agg, 2009)[["cve_geo", "primer_anio"]], on="cve_geo", how="left")
    res = res.sort_values(["edo", "mpio"]).reset_index(drop=True)
    res.to_parquet(V.OUT_VIOLENCIA, compression="zstd")

    # ---- control: totales por año de registro (edición) y por año de ocurrencia
    por_ed = ctrl.set_index("edicion").homicidios
    f_ctrl = pd.DataFrame([{"año": a, "edición (registro)": int(por_ed.get(a, 0)),
                            "oficial": OFICIAL_REGISTRO[a][0], "dif": int(por_ed.get(a, 0)) - OFICIAL_REGISTRO[a][0],
                            "fuente oficial": OFICIAL_REGISTRO[a][1]} for a in OFICIAL_REGISTRO])
    hom = agg[agg.n_hom > 0]
    por_ocu = hom[hom.anio_ocur.between(2009, 2024)].groupby("anio_ocur").n_hom.sum()
    por_ocu_ed = hom[hom.anio_ocur.between(2009, 2024)].groupby(["anio_ocur", "edicion"]).n_hom.sum().unstack(fill_value=0)
    f_ocu = pd.DataFrame({"año ocurrencia": por_ocu.index.astype(int), "homicidios (todas las ediciones)": por_ocu.values.astype(int),
                          "de ellos, registrados después": [int(por_ocu_ed.loc[a, [e for e in por_ocu_ed.columns if e > a]].sum()) for a in por_ocu.index]})

    # ---- reporte
    L = ["# Violencia homicida municipal (D-027)", "",
         f"Generado por `scripts/datos/violencia_municipio.py` en {time.time() - t0:.0f} s. Salida: `data/interim/externos/violencia_mpio.parquet` "
         f"({len(res):,} municipios INE).", "",
         "## 1. Archivos descargados (INEGI, Estadísticas de defunciones registradas)", "",
         "Descubiertos con la API de descarga masiva de la página del programa (https://www.inegi.org.mx/programas/edr/). "
         "Fecha de consulta: 2026-10-26. Las ligas de INEGI devuelven HTML con código 200 si el archivo no existe, "
         "por eso el script verifica la firma `PK` del zip.", "",
         "| Zip | URL | Tamaño (MB) |", "|---|---|---|"]
    for ruta in dict.fromkeys(e[1] for e in V.EDICIONES):
        z = V.zip_de(ruta)
        L.append(f"| {z.name} | {V.URL_BASE}{ruta} | {z.stat().st_size / 1e6:.1f} |")
    L += ["", "Formato: 2009–2011 vienen en DBF (los datos abiertos CSV de INEGI empiezan en 2012); 2012–2024 en CSV. "
          "Las ediciones son por **año de registro** y son disjuntas (columna 'filas con anio_regis distinto' = 0).", "",
          "## 2. Códigos usados por edición", "",
          "Homicidio = código 2 en `presunto` (ediciones 2009–2021: 1 accidente, 2 homicidio, 3 suicidio, 4 se ignora, "
          "5 operaciones legales, 8 no aplica) y en `tipo_defun` (2022–2024: 1 accidente, 2 homicidio, 3 suicidio, 4 enfermedad, "
          "5 intervención legal, 9 se ignora). Entidad y municipio de ocurrencia: `ent_ocurr`, `mun_ocurr` (999 = municipio no especificado, "
          "ent. 99 = no especificada); año de ocurrencia: `anio_ocur` (9999 = no especificado). En 2024 el diccionario anuncia "
          "`CVEGEO`, pero el CSV no la trae: se arma con entidad (2 díg.) + municipio (3 díg.). Verificado en los catálogos "
          "`presunta_defuncion_violenta.csv` de los zip de 2020 y 2024.", "",
         md(ctrl), "",
         "## 3. Totales nacionales contra la cifra oficial", "",
         "### 3.1 Por año de REGISTRO (la edición completa), contra INEGI", "", md(f_ctrl), "",
         "Las cifras 'PRELIMINAR' se revisan al alza en la edición definitiva, por eso la edición descargada puede ser mayor. "
         "Coincide exactamente la definitiva 2020 (36,773) y la de 2024 (33,550). Las cifras [P] de 2009–2011 vienen de prensa y "
         "no tienen boletín oficial localizado (se citan de prensa).", "",
         "### 3.2 Por año de OCURRENCIA (sumando todas las ediciones descargadas; es la serie que se usa)", "", md(f_ocu), "",
         "Rezago: las ocurrencias de 2023 se completan con la edición 2024 (y quedan sin las registradas en 2025 en adelante, aún no publicadas); "
         "las de 2009 tienen 15 años de ediciones. La subestimación del último año es de un orden parecido al aporte de la última "
         "edición (columna 'registrados después' de años recientes).", ""]
    L += ["## 4. No especificados y no mapeados", ""]
    for nom, (resumen, no_map) in aud.items():
        a, b = C.VENTANAS_VIOLENCIA[nom]
        L += [f"### Ventana {nom} ({a}–{b})", "",
              md(pd.DataFrame([resumen]).T.reset_index().rename(columns={"index": "concepto", 0: "homicidios / cuenta"})), ""]
        if len(no_map):
            top = no_map.groupby("cve_geo", as_index=False).n_hom.sum().sort_values("n_hom", ascending=False).head(10)
            L += ["Claves INEGI con homicidios que no están en el mapeo (top 10):", "", md(top), ""]
    L += ["Los 'no especificados' (año, entidad o municipio) se cuentan y **no se reparten**: no entran a ninguna tasa. "
          "Los homicidios en municipios sin mapear tampoco.", "",
          "## 5. Municipios creados después de 2009 (decisión de cómputo, a ratificar)", ""]
    tarde = res[res.primer_anio > 2009][["edo", "mpio", "cve_geo", "primer_anio", "poblacion"]]
    L += [f"Regla usada: años de exposición de un municipio = desde `max(2009, primer año con alguna defunción registrada en ese municipio)` "
          f"hasta el fin de la ventana. {len(tarde)} municipios del catálogo aparecen después de 2009:", "", md(tarde), "",
          "Limitación: antes de su creación, las ocurrencias de su territorio están en el municipio de origen, cuya población "
          "(Censo 2020) ya no incluye al nuevo. Esto infla levemente la tasa del municipio de origen. No se reasigna por falta de una tabla oficial de segregaciones.", "",
          "## 6. Dispersión estimada (φ = varianza relativa de la tasa municipal; k = 1/φ)", "",
          "Se ajusta por máxima verosimilitud de la binomial negativa marginal, con media = tasa del estado. Se estima **una φ por estado**; "
          "si el óptimo de un estado cae en la frontera de búsqueda (verosimilitud monótona, sin información) se usa la φ nacional. "
          "Regla de cómputo declarada (D-027).", ""]
    for nom, t in tabs.items():
        t = t.copy()
        L += [f"### {nom}: φ nacional = {t.phi_nacional.iloc[0]:.3f}; estados que usan la nacional: {int((t.fuente == 'nacional').sum())}", "",
              md(t[["edo", "n_mpios", "phi_estado", "en_frontera", "phi_usado", "fuente"]]), ""]
    L += ["## 7. Distribución de la tasa contraída (por 100 mil por año)", ""]
    for nom in C.VENTANAS_VIOLENCIA:
        d = res[f"tasa_contr_{nom}"].describe(percentiles=[.05, .25, .5, .75, .95, .99])
        dc = res[f"tasa_cruda_{nom}"].describe(percentiles=[.05, .25, .5, .75, .95, .99])
        L += [f"### {nom}", "", md(pd.DataFrame({"estadístico": d.index, "contraída": d.values, "cruda": dc.values})), "",
              f"Municipios con tasa: {int(res[f'tasa_contr_{nom}'].notna().sum()):,} de {len(res):,}.", ""]
    L += ["## 8. Top-10 municipios por tasa contraída (revisión de plausibilidad)", ""]
    nombres = pd.read_excel(X.CAT_MUN, header=None, dtype=str).iloc[3:][[1, 4]].dropna()
    nombres.columns = ["cve_geo", "municipio"]
    for nom in C.VENTANAS_VIOLENCIA:
        t = res.sort_values(f"tasa_contr_{nom}", ascending=False).head(10).merge(nombres.drop_duplicates("cve_geo"), on="cve_geo", how="left")
        L += [f"### {nom}", "", md(t[["cve_geo", "municipio", "poblacion", f"hom_{nom}", f"tasa_cruda_{nom}", f"tasa_contr_{nom}"]]), ""]
    ok = res[["log_tasa_contr_v2020", "log_tasa_contr_v2023"]].replace(-np.inf, np.nan).dropna()
    rho = ok.corr(method="spearman").iloc[0, 1]
    L += ["## 9. Estabilidad entre ventanas", "",
          f"Correlación de Spearman entre log tasa contraída v2020 y v2023 (n = {len(ok):,} municipios): **{rho:.4f}**.", "",
          "## 10. Notas", "",
          "- Población constante (Censo 2020, `pob_tot_conapo`) para todos los años: es un denominador (D-027), no una serie.",
          "- Homicidio = presunto homicidio del certificado de defunción (INEGI), no el SESNSP (D-027).",
          "- Municipios con 0 homicidios en la ventana tienen tasa cruda 0 y tasa contraída > 0 (nunca log de cero)."]
    (C.salidas(__file__) / "control.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"listo en {time.time() - t0:.0f} s; rho={rho:.4f}")


if __name__ == "__main__":
    main()
