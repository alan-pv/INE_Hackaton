"""Fuentes externas por sección y municipio: Censo 2020 (INEGI), CONAPO y gubernaturas concurrentes (D-015).
Salidas: data/interim/externos/*.parquet, reports/datos/fuentes_externas/control.md
Uso: .venv/bin/python scripts/datos/fuentes_externas.py"""
import time

from ine_perfiles import config as C
from ine_perfiles import externos as X
from ine_perfiles.ingesta import conectar


def pct(a, b):
    return f"{100 * a / b:.2f}%"


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def main():
    t0 = time.time()
    con = conectar()
    X.INT_EXT.mkdir(parents=True, exist_ok=True)
    ncol, ncel, cent, neg, nafect = X.auditar_centinelas()
    X.construir_eceg2020(con)
    n20, nul20 = X.nulos(con, "eceg2020", X.DESC_COLS)
    r24 = X.construir_eceg2024(con)
    n24, nul24 = X.nulos(con, "eceg2024", X.DESC_COLS + ["seccion_madre"])
    res = X.construir_residencia(con)
    cp = X.construir_conapo(con)
    cc = X.construir_concurrencia(con)
    cor, ncor = X.correlaciones(con)

    # rangos de proporciones
    props = [d[0] for d in X.DESCRIPTORES]
    rng = con.execute("SELECT " + ", ".join(f"min({p}), max({p})" for p in props) + " FROM eceg2020").fetchall()[0]
    cobe21 = con.execute("""SELECT count(*), sum(ln) FROM (SELECT edo, seccion, sum(ln) ln FROM ccpc WHERE aelec=2021 GROUP BY 1,2)""").fetchall()[0]
    cobe21c = con.execute("""SELECT count(*), sum(s.ln) FROM (SELECT edo, seccion, sum(ln) ln FROM ccpc WHERE aelec=2021 GROUP BY 1,2) s
                             JOIN eceg2020 e USING (edo, seccion)""").fetchall()[0]
    tipos = con.execute("SELECT tipo, count(*) FROM eceg2020 GROUP BY 1 ORDER BY 1").fetchall()
    mpio = con.execute("SELECT count(DISTINCT (edo, mpio)) FROM ccpc WHERE aelec=2024").fetchall()[0][0]

    L = []
    w = L.append
    w("# Fuentes externas (D-015)\n")
    w("> **Advertencia (D-010):** todos los indicadores son de CONTEXTO de la sección o del municipio. Las "
      "correlaciones son descriptivas, a nivel agregado; no se atribuyen a las personas de un perfil (falacia "
      "ecológica) ni implican causa (D-010).\n")
    w("## 1. ECEG 2020: lectura y valores no disponibles\n")
    w(f"- Archivo: `INE_SECCION_2020.csv`, {n20:,} secciones, {ncol} columnas (leído como texto).")
    w(f"- Valores no numéricos en TODAS las columnas (vacíos, `*`, `N/D`, etc.): **{ncel}** celdas {cent if cent else ''}. "
      f"Códigos negativos (no disponible/confidencial, no documentados en el descriptor; inferidos por ser conteos imposibles): {neg} "
      f"en {nafect} secciones; se convierten a NULL en las columnas usadas. Los demás NULL provienen de denominadores = 0.")
    w(f"- TIPO -> U/M/R: " + ", ".join(f"{t}={n:,}" for t, n in tipos) + " (D-015).\n")
    w("### Fórmulas (proporciones en [0,1]; NULL si denominador = 0)\n")
    w("| Descriptor | Fórmula | Denominador | min | max | nulos |\n|---|---|---|---|---|---|")
    for i, (nom, n, d, desc) in enumerate(X.DESCRIPTORES):
        w(f"| `{nom}` | {n} / {d} | {desc.split(' / ')[1]} | {rng[2*i]:.4f} | {rng[2*i+1]:.4f} | {nul20[nom]} |")
    w(f"| `graproes` | GRAPROES (años, tal cual) | población de 15+ | | | {nul20['graproes']} |")
    w("| `pobtot_eceg`, `p_18ymas_eceg` | POBTOT, P_18YMAS (conteos) | | | | "
      f"{nul20['pobtot_eceg']} |")
    w("\nLos conteos `pobtot_eceg` y `p_18ymas_eceg` se dejan en NULL en secciones heredadas (no son la población de la sección hija).")
    w("Nota: VPH_INTER y VPH_CEL se dividen entre TVIVPARHAB: con VIVPAR_HAB 2,110 secciones excedían 1; con TVIVPARHAB, 0.\n")
    w("## 2. Cobertura ECEG\n")
    w(f"- **2021:** {cobe21c[0]:,} de {cobe21[0]:,} secciones ({pct(cobe21c[0], cobe21[0])}); LN {pct(cobe21c[1], cobe21[1])}.")
    w(f"- **2024 directa:** {r24['n_directas']:,} de {r24['n_2024']:,} secciones ({pct(r24['n_directas'], r24['n_2024'])}); "
      f"LN {pct(r24['ln_directas'], r24['ln_2024'])}.")
    w(f"- **2024 con herencia:** {r24['n_resueltas']:,} de {r24['n_faltan']:,} secciones faltantes resueltas "
      f"({pct(r24['n_resueltas'], r24['n_faltan'])}); LN resuelta {pct(r24['ln_resueltas'], r24['ln_faltan'])} de la faltante. "
      f"Cobertura total 2024: {pct(r24['n_directas'] + r24['n_resueltas'], r24['n_2024'])} secciones, "
      f"{pct(r24['ln_directas'] + r24['ln_resueltas'], r24['ln_2024'])} LN.")
    w(f"- No resueltas: {r24['n_sin_resolver']} (LN {r24['ln_sin_resolver']:,}) {r24['sin_resolver']}.\n")
    w("### Validación de las secciones madre (tabla de equivalencias de Magar vs CCPC)\n")
    w(f"- Madres distintas (raíces en ECEG): {r24['n_madres']:,}; presentes en CCPC 2021: {r24['madres_en_ccpc21']:,} "
      f"({pct(r24['madres_en_ccpc21'], r24['n_madres'])}); sin registro en CCPC 2021: {r24['n_madres_sin_ccpc21']}.")
    w(f"- Madres marcadas en la tabla como divididas (`split.to`) o con año de baja: {r24['madres_divididas_o_baja']:,} "
      f"({pct(r24['madres_divididas_o_baja'], r24['n_madres'])}); madres que siguen vigentes en 2024: {r24['madres_vigentes_2024']:,}.")
    w(f"- Secciones heredadas por cadena (la madre inmediata tampoco está en ECEG, se sube a su origen): {r24['n_cadena']}.")
    w(f"- Conflictos (varias madres en ECEG; se toma la de mayor LN 2021, empate = menor número): **{r24['n_conflictos']}**.")
    for k, rs, m in r24["conflictos"][:20]:
        w(f"  - {k} <- {rs}, elegida {m}")
    w(f"- Conservación de LN por familia (LN 2024 de hijas + madres vigentes / LN 2021 de las madres), {r24['n_familias']:,} familias; "
      f"cuantiles 5/25/50/75/95: {r24['ratio_familia']}. Es descriptivo: no se fija umbral.\n")
    w("## 3. Indicador de residencia (D-013): `razon_ln_p18`\n")
    nac = res["nacional"]
    w(f"- LN CCPC 2021 (SEXO<2) de la sección / P_18YMAS. Secciones con cruce directo: {res['n_cruce']:,} de {res['n_2021']:,}; "
      f"con valor no nulo: {nac[1]:,}.")
    q = nac[3]
    w(f"- Nacional: min {nac[2]:.3f}; p1 {q[0]:.3f}; p5 {q[1]:.3f}; p10 {q[2]:.3f}; p25 {q[3]:.3f}; **p50 {q[4]:.3f}**; "
      f"p75 {q[5]:.3f}; p90 {q[6]:.3f}; p95 {q[7]:.3f}; p99 {q[8]:.3f}; max {nac[4]:.3f}.")
    w("\n| edo | n | p10 | p50 | p90 |\n|---|---|---|---|---|")
    for _, r in res["estados"].iterrows():
        w(f"| {int(r.edo)} | {int(r.n):,} | {r.p10:.3f} | {r.p50:.3f} | {r.p90:.3f} |")
    w("\nCuidados (D-013): censo de marzo 2020 vs LN de junio 2021; el censo incluye residentes de cualquier nacionalidad.\n")
    w("## 4. CONAPO por municipio INE\n")
    w("Cruce INEGI <-> INE por nombre normalizado dentro de la entidad (las dos listas del xlsx no están alineadas por fila). "
      f"Métodos: {cp['metodos']}. Municipios INE del catálogo: {cp['n_mapa']:,}.")
    w(f"- Municipios del catálogo INEGI sin contraparte INE: {cp['sin_ine']}; INE sin contraparte INEGI: {cp['sin_inegi']}.")
    c = cp["cob"]
    w(f"- **Cobertura CCPC 2024:** {c[1]:,} de {c[0]:,} municipios ({pct(c[1], c[0])}); LN {pct(c[3], c[2])}.")
    w(f"- Con IIM (índice no nulo): {c[4]:,} municipios, LN {pct(c[5], c[2])}. Con IM 2020: {c[6]:,} municipios, LN {pct(c[7], c[2])}.")
    rp = cp["razon_pob"]
    w(f"- Validación del cruce: razón población ECEG / POB_TOT CONAPO por municipio: n={rp['count']:.0f}, "
      f"p1 {rp['1%']:.3f}, p50 {rp['50%']:.3f}, p99 {rp['99%']:.3f}, min {rp['min']:.3f}, max {rp['max']:.3f}.")
    w(f"- Claves INE repetidas en el catálogo (se conserva la de razón de población más cercana a 1; descartadas): "
      f"{cp['descartados_dup'].values.tolist()}.")
    w("- Cruces no exactos:\n\n" + md(cp["difusos"]))
    w("\n- Municipios CCPC 2024 sin cruce (por LN):\n\n" + md(cp["sin_cruce"].head(40)))
    w(f"\n- Nulos en la salida: {cp['nulos']}\n")
    w("## 5. Concurrencia\n")
    w(f"- Rejilla completa aelec x edo: {cc['filas']} filas; con elección local concurrente {cc['con_local']}. "
      f"Gubernaturas por año: {cc['gub_por_anio']}. `dip_local` NULL (no desglosado en 2018) en {cc['dip_nulos']} filas.")
    w("- D-015: solo `gubernatura` se marca verificada (`gubernatura_verificada=TRUE`); `otras_banderas_verificadas=FALSE` en todas, con el texto original en `verificacion_texto`.\n")
    w("## 6. Nulos por variable (eceg_seccion2024)\n")
    w(f"Filas: {n24:,}.\n\n| variable | nulos |\n|---|---|")
    for k, v in nul24.items():
        w(f"| {k} | {v:,} |")
    w("\n## 7. Correlación de Spearman con la participación 2024 (SV/(SV+NV), SEXO<2)\n")
    w("**Solo descriptivo, unidad = sección (D-010).** `razon_ln_p18` es de 2021 (se cruza con participación 2024 solo para ver asociación); "
      "`iim_dp2` e `im_2020` son municipales y se repiten en todas las secciones del municipio (los n efectivos de municipio son mucho menores).\n")
    w(f"Secciones con participación 2024: {ncor:,}.\n")
    w(md(cor))
    w(f"\n_Tiempo de ejecución: {time.time() - t0:.0f} s._")
    (C.salidas(__file__) / "control.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:30]))


if __name__ == "__main__":
    main()
