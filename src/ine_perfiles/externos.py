"""Integración de fuentes externas (D-015): ECEG 2020, equivalencias seccionales,
residencia (D-013), CONAPO y concurrencia. Los descriptores son de CONTEXTO (D-010):
nunca se atribuyen a las personas de un perfil (falacia ecológica)."""
import difflib
import math
import unicodedata
from pathlib import Path

import pandas as pd

from . import config as C

RAW_EXT = C.RAIZ / "data" / "raw" / "externos"
INT_EXT = C.RAIZ / "data" / "interim" / "externos"
ECEG_CSV = RAW_EXT / "inegi_eceg2020" / "conjunto_de_datos" / "INE_SECCION_2020.csv"
CAT_MUN = RAW_EXT / "inegi_eceg2020" / "catalogos" / "cat_municipios_2020_INEGI-INE-ECEG.xlsx"
EQUIV = RAW_EXT / "reseccionamiento" / "tablaEquivalenciasSeccionalesDesde1994.csv"
IIM = RAW_EXT / "conapo" / "iim_base2020m.csv"
IMM = RAW_EXT / "conapo" / "IMM_2020.xlsx"
CONCUR = RAW_EXT / "concurrencia" / "concurrencia_2009_2024.csv"

OUT_ECEG2020 = INT_EXT / "eceg_seccion2020.parquet"
OUT_ECEG2024 = INT_EXT / "eceg_seccion2024.parquet"
OUT_RESID = INT_EXT / "residencia_seccion.parquet"
OUT_CONAPO = INT_EXT / "conapo_mpio_ine.parquet"
OUT_CONCUR = INT_EXT / "concurrencia.parquet"

# TIPO de ECEG: 2 Urbana, 3 Mixta, 4 Rural (deducido al comparar conteos con TIPOSEC 2021)  # D-015
TIPO_ECEG = {"2": "U", "3": "M", "4": "R"}

# Descriptores: (nombre, numerador, denominador, descripción). Proporciones en [0,1];
# NULL si el denominador es 0. Cada denominador es la población de referencia del
# descriptor INEGI (Descriptor_indicadores_ECEG_Seccion_2020).  # D-010, D-015
DESCRIPTORES = [
    ("prop_sin_escolaridad", "P15YM_SE", "P_15YMAS", "15+ sin escolaridad / población de 15+"),
    ("prop_analfabeta", "P15YM_AN", "P_15YMAS", "15+ analfabeta / población de 15+"),
    ("prop_posbasica", "P18YM_PB", "P_18YMAS", "18+ con educación posbásica / población de 18+"),
    ("prop_hli", "P3YM_HLI", "P_3YMAS", "3+ que habla lengua indígena / población de 3+"),
    ("prop_afro", "POB_AFRO", "POBTOT", "afromexicana o afrodescendiente / población total"),
    ("prop_internet", "VPH_INTER", "TVIVPARHAB", "viviendas particulares habitadas con Internet / total de viviendas particulares habitadas"),
    ("prop_celular", "VPH_CEL", "TVIVPARHAB", "viviendas particulares habitadas con celular / total de viviendas particulares habitadas"),
    ("prop_nacida_otra_ent", "PNACOE", "POBTOT", "nacida en otra entidad / población total"),
    ("prop_res_otra_ent_2015", "PRESOE15", "P_5YMAS", "5+ que en marzo 2015 residía en otra entidad / población de 5+"),
    ("prop_discapacidad", "PCON_DISC", "POBTOT", "con discapacidad / población total"),
    ("prop_18a24", "P_18A24", "P_18YMAS", "18 a 24 años / población de 18+"),
    ("prop_60ymas", "P_60YMAS", "P_18YMAS", "60+ / población de 18+"),
]
# columnas crudas necesarias (además de las llaves)
_CRUDAS = sorted({c for _, n, d, _ in DESCRIPTORES for c in (n, d)} | {"GRAPROES", "POBTOT", "P_18YMAS", "TVIVPARHAB"})
DESC_COLS = ["tipo", "pobtot_eceg", "p_18ymas_eceg", "graproes"] + [d[0] for d in DESCRIPTORES]


# ---------------------------------------------------------------- ECEG
def auditar_centinelas():
    """Cuenta valores no numéricos (vacíos, '*', 'N/D') y códigos negativos en TODAS las columnas
    de la ECEG. Los negativos (-6, -9) son códigos de no disponible/confidencial: se convierten a NULL.
    Devuelve (n_columnas, n_no_numericas, {valor: n}, {codigo_negativo: n}, n_secciones_afectadas)."""
    d = pd.read_csv(ECEG_CSV, dtype=str, keep_default_na=False)
    cuenta, neg, afect = {}, {}, set()
    for c in d.columns:
        n = pd.to_numeric(d[c], errors="coerce")
        for v in d.loc[n.isna(), c]:
            cuenta[v] = cuenta.get(v, 0) + 1
        for v, k in n[n < 0].value_counts().items():
            neg[v] = neg.get(v, 0) + int(k)
        afect |= set(d.index[n < 0])
    return d.shape[1], sum(cuenta.values()), cuenta, neg, len(afect)


def construir_eceg2020(con):
    """Tabla eceg2020 (edo, seccion, municipio_ine, descriptores) en la conexión y en Parquet."""
    # códigos negativos (-6, -9) = no disponible/confidencial -> NULL
    cols = ", ".join(f'CASE WHEN TRY_CAST("{c}" AS DOUBLE) >= 0 THEN TRY_CAST("{c}" AS DOUBLE) END AS "{c}"'
                     for c in _CRUDAS)
    con.execute(f"""CREATE OR REPLACE TABLE eceg_cruda AS
        SELECT CAST(ENTIDAD AS INTEGER) AS edo, CAST(SECCION AS INTEGER) AS seccion,
               CAST(MUNICIPIO AS INTEGER) AS mpio_ine, TIPO, {cols}
        FROM read_csv('{ECEG_CSV}', all_varchar=true)""")
    exprs = [f"CASE WHEN {d} > 0 THEN {n} / {d} END AS {nom}" for nom, n, d, _ in DESCRIPTORES]
    con.execute(f"""CREATE OR REPLACE TABLE eceg2020 AS
        SELECT edo, seccion, mpio_ine,
               CASE TIPO WHEN '2' THEN 'U' WHEN '3' THEN 'M' WHEN '4' THEN 'R' END AS tipo,
               POBTOT AS pobtot_eceg, P_18YMAS AS p_18ymas_eceg, GRAPROES AS graproes,
               {', '.join(exprs)}
        FROM eceg_cruda""")
    INT_EXT.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY eceg2020 TO '{OUT_ECEG2020}' (FORMAT parquet, COMPRESSION zstd)")


# ---------------------------------------------------------------- equivalencias
def _tabla_equiv(con):
    con.execute(f"""CREATE OR REPLACE TABLE equiv_cruda AS
        SELECT edon, seccion, alta, baja, action, "orig.dest" AS od, action2, "orig.dest2" AS od2,
               action3, "orig.dest3" AS od3 FROM read_csv('{EQUIV}', all_varchar=true)""")
    con.execute("""CREATE OR REPLACE TABLE equiv AS
        SELECT CAST(edon AS INTEGER) AS edo, CAST(seccion AS INTEGER) AS seccion,
               TRY_CAST(alta AS INTEGER) AS alta, TRY_CAST(baja AS INTEGER) AS baja,
               action, od, action2, od2, action3, od3 FROM equiv_cruda""")
    filas = con.execute("SELECT edo, seccion, action, od, action2, od2, action3, od3 FROM equiv").fetchall()
    madres_de, divide = {}, {}
    for edo, sec, a1, o1, a2, o2, a3, o3 in filas:
        for a, o in ((a1, o1), (a2, o2), (a3, o3)):
            if a == "split.from" and o:
                madres_de[(edo, sec)] = [int(x) for x in o.split("|") if x.strip().isdigit()]
            if a == "split.to":
                divide[(edo, sec)] = True
    return madres_de, divide


def _raices(clave, madres_de, en_eceg, visitados=None):
    """Secciones de ECEG de las que desciende `clave` (sigue la cadena split.from hasta ECEG)."""
    visitados = visitados or set()
    if clave in visitados:
        return []
    visitados = visitados | {clave}
    out = []
    for m in madres_de.get(clave, []):
        k = (clave[0], m)
        if k in en_eceg:
            out.append(k)
        else:
            out.extend(_raices(k, madres_de, en_eceg, visitados))
    return list(dict.fromkeys(out))


def construir_eceg2024(con):
    """eceg_seccion2024: (edo, seccion) de CCPC 2024 + descriptores directos o heredados de
    la sección madre de 2021 (D-015). Devuelve dict de estadísticas de validación."""
    con.execute("""CREATE OR REPLACE TABLE s24 AS
        SELECT edo, seccion, sum(ln) AS ln FROM ccpc WHERE aelec=2024 GROUP BY 1,2""")
    con.execute("""CREATE OR REPLACE TABLE s21 AS
        SELECT edo, seccion, sum(ln) AS ln FROM ccpc WHERE aelec=2021 GROUP BY 1,2""")
    madres_de, divide = _tabla_equiv(con)
    en_eceg = set(con.execute("SELECT edo, seccion FROM eceg2020").fetchall())
    ln21 = {(e, s): l for e, s, l in con.execute("SELECT edo, seccion, ln FROM s21").fetchall()}
    ln24 = {(e, s): l for e, s, l in con.execute("SELECT edo, seccion, ln FROM s24").fetchall()}
    en24 = set(ln24)
    baja_equiv = {(e, s): b for e, s, b in con.execute("SELECT edo, seccion, baja FROM equiv").fetchall()}

    faltan = sorted(k for k in ln24 if k not in en_eceg)
    filas, sin_resolver, conflictos = [], [], []
    for k in faltan:
        r = _raices(k, madres_de, en_eceg)
        if not r:
            sin_resolver.append(k)
            continue
        # varias madres: la de mayor LN 2021; empate -> menor número de sección (determinista)
        madre = sorted(r, key=lambda m: (-ln21.get(m, 0), m[1]))[0]
        if len(r) > 1:
            conflictos.append((k, r, madre))
        filas.append((k[0], k[1], madre[1], len(r)))
    mad = pd.DataFrame(filas, columns=["edo", "seccion", "seccion_madre", "n_madres"])
    con.register("mad_df", mad)

    pcols = ", ".join(f"e.{c}" for c in DESC_COLS if c not in ("pobtot_eceg", "p_18ymas_eceg"))
    con.execute(f"""CREATE OR REPLACE TABLE eceg2024 AS
        SELECT s.edo, s.seccion,
               {pcols},
               CASE WHEN m.seccion IS NULL THEN e.pobtot_eceg END AS pobtot_eceg,
               CASE WHEN m.seccion IS NULL THEN e.p_18ymas_eceg END AS p_18ymas_eceg,
               (m.seccion IS NOT NULL) AS eceg_heredado, m.seccion_madre
        FROM s24 s
        LEFT JOIN mad_df m ON m.edo=s.edo AND m.seccion=s.seccion
        LEFT JOIN eceg2020 e ON e.edo=s.edo AND e.seccion=COALESCE(m.seccion_madre, s.seccion)""")
    con.execute(f"COPY (SELECT * FROM eceg2024 ORDER BY edo, seccion) TO '{OUT_ECEG2024}' (FORMAT parquet, COMPRESSION zstd)")

    # --- validación de las madres contra CCPC 2021 y la tabla
    madres_set = {(e, m) for e, s, m, _ in filas}
    todas_madres = {m for k in faltan for m in _raices(k, madres_de, en_eceg)}
    en21 = sum(1 for m in todas_madres if m in ln21)
    divididas = sum(1 for m in todas_madres if divide.get(m) or baja_equiv.get(m) is not None)
    sigue24 = sum(1 for m in todas_madres if m in en24)
    # conservación de LN por familias (componentes hijas-madres): LN2024 familia / LN2021 madres
    padre = {}

    def f(x):
        padre.setdefault(x, x)
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x
    for k in faltan:
        for m in _raices(k, madres_de, en_eceg):
            padre[f(k)] = f(m)
    fam = {}
    for k in faltan:
        if k in padre:
            fam.setdefault(f(k), {"hijas": set(), "madres": set()})["hijas"].add(k)
    for k in faltan:
        for m in _raices(k, madres_de, en_eceg):
            fam[f(k)]["madres"].add(m)
    ratios = []
    for g in fam.values():
        l21 = sum(ln21.get(m, 0) for m in g["madres"])
        l24 = sum(ln24.get(h, 0) for h in g["hijas"]) + sum(ln24.get(m, 0) for m in g["madres"])
        if l21 > 0:
            ratios.append(l24 / l21)
    ratios = pd.Series(ratios)
    res = {
        "n_2024": len(ln24), "ln_2024": sum(ln24.values()),
        "n_directas": len(ln24) - len(faltan),
        "ln_directas": sum(v for k, v in ln24.items() if k in en_eceg),
        "n_faltan": len(faltan), "ln_faltan": sum(ln24[k] for k in faltan),
        "n_resueltas": len(filas), "ln_resueltas": sum(ln24[(e, s)] for e, s, _, _ in filas),
        "n_sin_resolver": len(sin_resolver), "sin_resolver": sin_resolver,
        "ln_sin_resolver": sum(ln24[k] for k in sin_resolver),
        "n_conflictos": len(conflictos), "conflictos": conflictos,
        "n_madres": len(todas_madres), "madres_en_ccpc21": en21,
        "madres_divididas_o_baja": divididas, "madres_vigentes_2024": sigue24,
        "n_cadena": sum(1 for k in faltan if any((k[0], m) not in en_eceg for m in madres_de.get(k, []))),
        "n_familias": len(ratios),
        "ratio_familia": ratios.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).to_dict() if len(ratios) else {},
        "n_madres_sin_ccpc21": len(todas_madres) - en21,
    }
    return res


# ---------------------------------------------------------------- residencia (D-013)
def construir_residencia(con):
    """razon_ln_p18 = LN CCPC 2021 de la sección / P_18YMAS de ECEG, solo cruce directo 2021;
    NULL si P_18YMAS = 0. LN con SEXO<2 (D-005)."""
    con.execute(f"""CREATE OR REPLACE TABLE residencia AS
        SELECT s.edo, s.seccion, s.ln AS ln_2021, e.p_18ymas_eceg AS p_18ymas,
               CASE WHEN e.p_18ymas_eceg > 0 THEN s.ln / e.p_18ymas_eceg END AS razon_ln_p18
        FROM (SELECT edo, seccion, sum(ln) AS ln FROM ccpc WHERE aelec=2021 AND sexo<2 GROUP BY 1,2) s
        JOIN eceg2020 e ON e.edo=s.edo AND e.seccion=s.seccion""")
    con.execute(f"COPY (SELECT * FROM residencia ORDER BY edo, seccion) TO '{OUT_RESID}' (FORMAT parquet, COMPRESSION zstd)")
    nac = con.execute("""SELECT count(*), count(razon_ln_p18), min(razon_ln_p18),
        quantile_cont(razon_ln_p18,[0.01,0.05,0.1,0.25,0.5,0.75,0.9,0.95,0.99]), max(razon_ln_p18)
        FROM residencia""").fetchall()[0]
    est = con.execute("""SELECT edo, count(razon_ln_p18) n, quantile_cont(razon_ln_p18,0.1) p10,
        quantile_cont(razon_ln_p18,0.5) p50, quantile_cont(razon_ln_p18,0.9) p90
        FROM residencia GROUP BY 1 ORDER BY 1""").df()
    cobertura = con.execute("""SELECT (SELECT count(*) FROM (SELECT DISTINCT edo, seccion FROM ccpc WHERE aelec=2021)),
        (SELECT count(*) FROM residencia)""").fetchall()[0]
    return {"nacional": nac, "estados": est, "n_2021": cobertura[0], "n_cruce": cobertura[1]}


# ---------------------------------------------------------------- CONAPO
def _norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()


def mapa_municipios():
    """Catálogo INEGI <-> INE (ECEG) por nombre normalizado dentro de la entidad. Las dos
    listas del xlsx NO están alineadas por fila. Devuelve DataFrame (edo, mpio_ine, cve_geo, metodo)."""
    x = pd.read_excel(CAT_MUN, header=None, dtype=str).iloc[3:]
    a = x[[1, 2, 4]].dropna()
    a.columns = ["cve_geo", "edo", "nom"]
    a["edo"] = a.edo.astype(int)
    a["k"] = a.nom.map(_norm)
    b = x[[7, 8, 9]].dropna()
    b.columns = ["edo", "mpio_ine", "nom"]
    b["edo"] = b.edo.astype(int)
    b["mpio_ine"] = b.mpio_ine.astype(int)
    b["k"] = b.nom.map(_norm)
    out, ua, ub = [], [], []
    for edo in sorted(set(a.edo) | set(b.edo)):
        ae, be = a[a.edo == edo], b[b.edo == edo]
        usados_a, usados_b = set(), set()
        for k in sorted(set(ae.k) & set(be.k)):
            fa = ae[ae.k == k].sort_values("cve_geo")
            fb = be[be.k == k].sort_values("mpio_ine")
            metodo = "exacto" if len(fa) == len(fb) == 1 else "nombre_repetido_por_orden"
            for (_, ra), (_, rb) in zip(fa.iterrows(), fb.iterrows()):
                out.append((edo, rb.mpio_ine, ra.cve_geo, metodo))
                usados_a.add(ra.cve_geo)
                usados_b.add(rb.mpio_ine)
        la = ae[~ae.cve_geo.isin(usados_a)]
        lb = be[~be.mpio_ine.isin(usados_b)]
        # restantes: mejor similitud de nombre dentro de la entidad (voraz, 1 a 1)
        # sin umbral de similitud: el cruce se audita con la razón de población ECEG/CONAPO.
        # Un nombre que es prefijo del otro ("JONACATEPEC" / "JONACATEPEC DE LEANDRO VALLE") puntúa 1.
        def _sim(x, y):
            return 1.0 if (x.startswith(y) or y.startswith(x)) else difflib.SequenceMatcher(None, x, y).ratio()
        pares = sorted(((_sim(ra.k, rb.k), ra.cve_geo, rb.mpio_ine)
                        for _, ra in la.iterrows() for _, rb in lb.iterrows()), reverse=True)
        for sc, cg, mi in pares:
            if cg in usados_a or mi in usados_b:
                continue
            out.append((edo, mi, cg, "difuso"))
            usados_a.add(cg)
            usados_b.add(mi)
        for cg in la.cve_geo:
            if cg not in usados_a:
                ua.append(cg)
        for mi in lb.mpio_ine:
            if mi not in usados_b:
                ub.append((edo, mi))
    df = pd.DataFrame(out, columns=["edo", "mpio_ine", "cve_geo", "metodo"])
    return df, ua, ub


def construir_conapo(con):
    mapa, sin_ine, sin_inegi = mapa_municipios()
    iim = pd.read_csv(IIM, dtype=str, encoding="latin1")
    iim = iim[iim.CVE_GEO != "0"].copy()
    iim["cve_geo"] = iim.CVE_GEO.str.zfill(5)
    iim = iim.rename(columns={"VIV_TOT": "iim_viv_tot", "VIV_REM": "iim_viv_rem", "VIV_EMIG": "iim_viv_emig",
                              "VIV_CIRC": "iim_viv_circ", "VIV_RET": "iim_viv_ret",
                              "IIM-DP2": "iim_dp2", "GIM-DP2": "gim_dp2"})
    num = ["iim_viv_tot", "iim_viv_rem", "iim_viv_emig", "iim_viv_circ", "iim_viv_ret", "iim_dp2"]
    iim[num] = iim[num].apply(pd.to_numeric, errors="coerce")
    iim = iim[["cve_geo"] + num + ["gim_dp2"]]
    imm = pd.read_excel(IMM, sheet_name="IMM_2020", dtype=str)
    imm["cve_geo"] = imm.CVE_MUN.str.zfill(5)
    imm = imm.rename(columns={"POB_TOT": "pob_tot_conapo", "ANALF": "imm_analf", "SBASC": "imm_sbasc",
                              "OVSDE": "imm_ovsde", "OVSEE": "imm_ovsee", "OVSAE": "imm_ovsae",
                              "OVPT": "imm_ovpt", "VHAC": "imm_vhac", "PL.5000": "imm_pl5000",
                              "PO2SM": "imm_po2sm", "IM_2020": "im_2020", "GM_2020": "gm_2020",
                              "IMN_2020": "imn_2020"})
    inum = ["pob_tot_conapo", "imm_analf", "imm_sbasc", "imm_ovsde", "imm_ovsee", "imm_ovsae",
            "imm_ovpt", "imm_vhac", "imm_pl5000", "imm_po2sm", "im_2020", "imn_2020"]
    imm[inum] = imm[inum].apply(pd.to_numeric, errors="coerce")
    imm = imm[["cve_geo"] + inum + ["gm_2020"]]
    r = mapa.merge(iim, on="cve_geo", how="left").merge(imm, on="cve_geo", how="left")
    # validación del cruce: población ECEG por (edo, mpio INE) frente a POB_TOT de CONAPO
    pob = con.execute("SELECT edo, mpio_ine, sum(pobtot_eceg) AS pob_eceg FROM eceg2020 GROUP BY 1,2").df()
    r = r.merge(pob, left_on=["edo", "mpio_ine"], right_on=["edo", "mpio_ine"], how="left")
    r["razon_pob_eceg_conapo"] = r.pob_eceg / r.pob_tot_conapo
    # el catálogo INE repite algunas claves (p. ej. Oaxaca 208 y 316): se conserva la fila cuya
    # población CONAPO es más cercana a la de ECEG (|log razón| mínimo) y se reporta la otra
    r["_d"] = r.razon_pob_eceg_conapo.map(lambda v: abs(math.log(v)) if v and v > 0 else float("inf"))
    r = r.sort_values(["edo", "mpio_ine", "_d"])
    dup = r[r.duplicated(["edo", "mpio_ine"], keep="first")][["edo", "mpio_ine", "cve_geo"]]
    r = r.drop_duplicates(["edo", "mpio_ine"], keep="first").drop(columns="_d")
    r = r.drop(columns=["pob_eceg"]).rename(columns={"mpio_ine": "mpio"})
    r = r.sort_values(["edo", "mpio"]).reset_index(drop=True)
    r["edo"] = r.edo.astype("int32")
    r["mpio"] = r.mpio.astype("int32")
    INT_EXT.mkdir(parents=True, exist_ok=True)
    r.to_parquet(OUT_CONAPO, index=False, compression="zstd")
    con.register("conapo_df", r)
    con.execute("CREATE OR REPLACE TABLE conapo AS SELECT * FROM conapo_df")
    # cobertura sobre CCPC 2024 (municipio INE = MPIOCVE)
    cob = con.execute("""
        WITH m AS (SELECT edo, mpio, sum(ln) ln FROM ccpc WHERE aelec=2024 GROUP BY 1,2)
        SELECT count(*), count(c.mpio), sum(m.ln), sum(CASE WHEN c.mpio IS NOT NULL THEN m.ln END),
               count(c.iim_dp2), sum(CASE WHEN c.iim_dp2 IS NOT NULL THEN m.ln END),
               count(c.im_2020), sum(CASE WHEN c.im_2020 IS NOT NULL THEN m.ln END)
        FROM m LEFT JOIN conapo c ON c.edo=m.edo AND c.mpio=m.mpio""").fetchall()[0]
    sin_cruce = con.execute("""
        WITH m AS (SELECT edo, mpio, any_value(mpionom) nom, sum(ln) ln FROM ccpc WHERE aelec=2024 GROUP BY 1,2)
        SELECT m.edo, m.mpio, m.nom, m.ln FROM m ANTI JOIN conapo c ON c.edo=m.edo AND c.mpio=m.mpio
        ORDER BY ln DESC""").df()
    return {"n_mapa": len(r), "metodos": r.metodo.value_counts().to_dict(), "sin_ine": sin_ine,
            "sin_inegi": sin_inegi, "cob": cob, "sin_cruce": sin_cruce,
            "razon_pob": r.razon_pob_eceg_conapo.describe(percentiles=[.01, .05, .5, .95, .99]).to_dict(),
            "difusos": r[r.metodo != "exacto"][["edo", "mpio", "cve_geo", "metodo", "razon_pob_eceg_conapo"]],
            "nulos": r.isna().sum()[lambda s: s > 0].to_dict(), "descartados_dup": dup}


# ---------------------------------------------------------------- concurrencia
def construir_concurrencia(con):
    """Rejilla completa aelec x edo (2009-2024). Solo `gubernatura` se considera verificada (D-015);
    dip_local y ayuntamientos se conservan con la bandera y el texto de verificación original."""
    c = pd.read_csv(CONCUR, dtype=str)
    for col in ("gubernatura", "dip_local", "ayuntamientos", "mismo_dia"):
        c[col] = pd.to_numeric(c[col], errors="coerce").astype("Int64")
    c["aelec"] = c.aelec.astype(int)
    base = c.drop(columns=["edo", "fuente_url", "cve_ent"]).assign(edo=c.cve_ent.astype(int))
    base = base.rename(columns={"verificacion": "verificacion_texto", "nota": "nota_fuente"})
    base["eleccion_local_concurrente"] = True
    rej = pd.MultiIndex.from_product([sorted(base.aelec.unique()), range(1, 33)], names=["aelec", "edo"]).to_frame(index=False)
    r = rej.merge(base, on=["aelec", "edo"], how="left")
    r["eleccion_local_concurrente"] = r.eleccion_local_concurrente.fillna(False).astype(bool)
    r["gubernatura"] = r.gubernatura.fillna(0).astype("int8")
    r["mismo_dia"] = r.mismo_dia.astype("Int8")
    r["dip_local"] = r.dip_local.astype("Int8")
    r["ayuntamientos"] = r.ayuntamientos.astype("Int8")
    r["gubernatura_verificada"] = True      # D-015: única bandera verificada
    r["otras_banderas_verificadas"] = False  # D-015: dip_local/ayuntamientos NO se consideran verificadas
    r = r[["aelec", "edo", "eleccion_local_concurrente", "gubernatura", "dip_local", "ayuntamientos",
           "mismo_dia", "gubernatura_verificada", "otras_banderas_verificadas", "verificacion_texto", "nota_fuente"]]
    r["aelec"] = r.aelec.astype("int32")
    r["edo"] = r.edo.astype("int32")
    r.to_parquet(OUT_CONCUR, index=False, compression="zstd")
    return {"filas": len(r), "con_local": int(r.eleccion_local_concurrente.sum()),
            "gub_por_anio": r.groupby("aelec").gubernatura.sum().to_dict(),
            "dip_nulos": int(r.dip_local[r.eleccion_local_concurrente].isna().sum())}


# ---------------------------------------------------------------- correlaciones
def correlaciones(con):
    """Spearman (sección) entre cada descriptor y la participación oficial 2024 SV/(SV+NV), SEXO<2.
    SOLO descriptivo; asociación ecológica, no efecto (D-010)."""
    from scipy.stats import spearmanr
    con.execute("""CREATE OR REPLACE TABLE part24 AS
        SELECT edo, mpio, seccion, sum(sv)/sum(sv+nv) AS part FROM ccpc
        WHERE aelec=2024 AND sexo<2 GROUP BY 1,2,3 HAVING sum(sv+nv)>0""")
    cols = [c for c in DESC_COLS if c != "tipo"]
    sel = ", ".join(f"e.{c}" for c in cols)
    df = con.execute(f"""SELECT p.part, e.eceg_heredado, {sel}, c.iim_dp2, c.im_2020, r.razon_ln_p18
        FROM part24 p JOIN eceg2024 e USING (edo, seccion)
        LEFT JOIN conapo c ON c.edo=p.edo AND c.mpio=p.mpio
        LEFT JOIN residencia r ON r.edo=p.edo AND r.seccion=p.seccion""").df()
    filas = []
    for c in cols + ["iim_dp2", "im_2020", "razon_ln_p18"]:
        fila = [c]
        for nombre, sub in (("todas", df), ("directas", df[~df.eceg_heredado.astype(bool)])):
            d = sub[["part", c]].dropna()
            rho = spearmanr(d.part, d[c])[0] if len(d) > 2 else float("nan")
            fila += [rho, len(d)]
        filas.append(fila)
    return pd.DataFrame(filas, columns=["variable", "rho_todas", "n_todas", "rho_directas", "n_directas"]), len(df)


def nulos(con, tabla, cols):
    n = con.execute(f"SELECT count(*) FROM {tabla}").fetchall()[0][0]
    q = ", ".join(f"count(*) - count({c})" for c in cols)
    v = con.execute(f"SELECT {q} FROM {tabla}").fetchall()[0]
    return n, dict(zip(cols, v))
