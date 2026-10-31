"""Batería común: las mismas 13 pruebas (T01–T13) aplicadas a los cinco perfiles (D-036).

Misma lógica, datos, pertenencia (sección mayoritaria), pesos, semilla [SEMILLA, 9], B y multiplicidades que
pruebas_lecturas.py, de modo que las celdas en común coinciden exactamente (se concilian al final). La tendencia
(T01, T02) se lee de la caché de pruebas_lecturas, que debe correr antes.
Salidas: reports/validacion/bateria_comun/ (bateria_comun.csv en formato largo y control.md).
Uso: .venv/bin/python scripts/validacion/bateria_comun.py"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import pickle
import time

import numpy as np
import pandas as pd

from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import lecturas as LF

SUFIJO_LECTURAS = 9            # D-034: semilla propia [SEMILLA, 9]
K = 5                          # perfiles de la entrega (D-029)
N_CELDAS_OBJ = C.SENS_CELDAS_OBJETIVO_CONTROL   # cifra de control de perfiles_finales (D-022)
CONTROL_2024 = C.CIFRAS_CONTROL[2024]["nacional"][0] / 100   # D-001
PROC = C.PROCESADOS
EXT = C.INTERIM / "externos"
INT = C.cache("pruebas_lecturas")
SAL = C.salidas(__file__)
LECT = C.salidas("validacion/pruebas_lecturas")      # salidas de pruebas_lecturas (solo lectura)
T0 = time.time()
H, MU = C.SEXO_HOMBRE, C.SEXO_MUJER
# Códigos de grupo de edad (data/processed/cortes_edad.json): 1 18–19, 2 20–24, 3 25–31, 4 32–46, 5 47–69, 6 70–79, 7 80+
G1824, G2546, G3269, G4769, G80 = (1, 2), (3, 4), (4, 5), (5,), (7,)
QA = []


def md(df):
    """Tabla markdown sin depender de tabulate."""
    cols = list(df.columns)
    f = lambda v: f"{v:.4g}" if isinstance(v, (float, np.floating)) else str(v)
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
                     + ["| " + " | ".join(f(v) for v in r) + " |" for r in df.itertuples(index=False)])


def log(s=""):
    QA.append(s)
    print(s, flush=True)


# ------------------------------------------------------------------ datos
cel = pd.read_parquet(PROC / "brecha_celda.parquet",
                      columns=["edo", "seccion", "sexo", "grupo", "delta", "n_2024", "ln_2024", "sv_2024", "E_2024"])
for c in ("edo", "seccion", "sexo", "grupo"):
    cel[c] = cel[c].astype("int64")
n_nan_w = int(cel["n_2024"].isna().sum())
# D-034: peso n_2024; si falta se usa ln_2024 (que también falta en esas celdas: sin población 2024) -> peso 0
cel["w"] = cel["n_2024"].fillna(cel["ln_2024"]).fillna(0.0).astype(float)
n_w0 = int((cel["w"] <= 0).sum())
cel["ln_2024"] = cel["ln_2024"].fillna(0.0).astype(float)
cel["delta"] = cel["delta"].astype(float)
n_delta_nan = int(cel["delta"].isna().sum())
# D-034 (agregado): medida cruda de 2024 log(sv_2024/E_2024), solo con sv_2024 > 0 y E_2024 > 0
_ok = (cel["sv_2024"] > 0) & (cel["E_2024"] > 0)
cel["delta_log"] = np.where(_ok, np.log(cel["sv_2024"].where(_ok, 1.0).astype(float) / cel["E_2024"].where(_ok, 1.0).astype(float)), np.nan)
n_log_excl = int((~_ok).sum()); n_log_excl_w = int((~_ok & (cel["w"] > 0)).sum())

desc = pd.read_parquet(PROC / "descriptores_seccion.parquet",
                       columns=["edo", "seccion", "mpio", "tiposec", "prop_hli", "prop_internet", "prop_nacida_otra_ent",
                                "razon_ln_p18", "iim_dp2", "pctl_mov_estado"])
for c in ("edo", "seccion", "mpio"):
    desc[c] = desc[c].astype("int64")
desc["falta_internet"] = 1.0 - desc["prop_internet"]          # D-034 P5 ii
viol = pd.read_parquet(EXT / "violencia_mpio.parquet", columns=["edo", "mpio", C.COL_VIOLENCIA["v2023"]])
viol[["edo", "mpio"]] = viol[["edo", "mpio"]].astype("int64")
desc["log_tasa_homicidio"] = CF.violencia_a_secciones(desc, viol, C.COL_VIOLENCIA["v2023"])

obj = pd.read_parquet(PROC / "perfiles_finales.parquet")
for c in ("edo", "seccion", "sexo", "grupo"):
    obj[c] = obj[c].astype("int64")
obj = obj.merge(cel[["edo", "seccion", "sexo", "grupo", "ln_2024"]], on=["edo", "seccion", "sexo", "grupo"],
                how="left", validate="1:1")
assert len(obj) == N_CELDAS_OBJ, len(obj)
assert obj["ln_2024"].notna().all()
log("# Batería común: datos y pertenencia como en pruebas_lecturas\n")
log("## Cifras de control\n")
log(f"- Celdas objetivo: {len(obj):,} (control {N_CELDAS_OBJ:,}) OK. Celdas de brecha_celda: {len(cel):,}.")
log(f"- Celdas sin n_2024: {n_nan_w:,} (ln_2024 también falta en ellas: sin población en 2024): peso 0 en las medias de brecha "
    f"({n_w0:,} celdas con peso 0). Celdas con delta NaN: {n_delta_nan}.")
assert (obj.groupby("perfil").size().reindex(range(1, K + 1)).to_numpy() == [80573, 170916, 109591, 56264, 55195]).all()
log("- Celdas por perfil (orden del documento) 80,573 / 170,916 / 109,591 / 56,264 / 55,195 OK.")

# ------------------------------------------------------------------ pertenencia (D-034)
ln_sec = cel.groupby(["edo", "seccion"], as_index=False)["ln_2024"].sum().rename(columns={"ln_2024": "ln_tot"})
n_sec_ln0 = int((ln_sec["ln_tot"] <= 0).sum())
ln_sec = ln_sec[ln_sec["ln_tot"] > 0].reset_index(drop=True)
S = LF.pertenencia(obj, ln_sec, K)
S = S.merge(desc, on=["edo", "seccion"], how="left", validate="1:1")
assert S["mpio"].notna().all()
log(f"- Secciones con celdas: {len(ln_sec) + n_sec_ln0:,}; con LN 2024 total > 0: {len(ln_sec):,} ({n_sec_ln0} sin LN, excluidas).")
mun, estr = LF.indices_municipio(S)
n_mun = len(estr)
S["mun"] = mun
log(f"- Municipios (edo, mpio) con secciones: {n_mun:,}; estados: {len(np.unique(estr))}.")
ln_perfil_tot = np.array([S[f"ln_perfil_{k}"].sum() for k in range(1, K + 1)])
filas = []
for k in range(1, K + 1):
    m = S["perfil_may"].to_numpy() == k
    filas.append(dict(perfil=k, secciones_mayoritarias=int(m.sum()), ln_seccion_mayoritaria=float(S.loc[m, "ln_tot"].sum()),
                      ln_del_perfil_en_ellas=float(S.loc[m, f"ln_perfil_{k}"].sum()),
                      ln_del_perfil_total=float(ln_perfil_tot[k - 1]),
                      pct_ln_perfil_captada=100 * float(S.loc[m, f"ln_perfil_{k}"].sum() / ln_perfil_tot[k - 1]),
                      secciones_rurales=int((m & (S["tiposec"] == "R").to_numpy()).sum()),
                      secciones_urbanas=int((m & (S["tiposec"] == "U").to_numpy()).sum())))
SEC = pd.DataFrame(filas)
log(f"- Σ LN_perfil (celdas objetivo, resp x LN 2024) = {ln_perfil_tot.sum():,.0f}; Σ ln_2024 de celdas objetivo = {obj['ln_2024'].sum():,.0f} "
    f"(deben coincidir; dif = {abs(ln_perfil_tot.sum() - (obj[[f'resp_perfil_{k}' for k in range(1, K+1)]].sum(axis=1) * obj['ln_2024']).sum()):.3e}).")
log(f"- Secciones sin perfil mayoritario: {int((S['perfil_may'] == 0).sum()):,}.\n")
log("### Secciones donde el perfil es mayoritario\n")
log(md(SEC.round(2)))
log("")

# ------------------------------------------------------------------ estadísticos a nivel sección
b_all = LF.brecha_seccion(cel).rename(columns={"brecha": "brecha_sec"})[["edo", "seccion", "brecha_sec"]]
S = S.merge(b_all, on=["edo", "seccion"], how="left", validate="1:1")
GR = dict(
    H2546=dict(sexos=[H], grupos=G2546), M2546=dict(sexos=[MU], grupos=G2546),
    A2546=dict(grupos=G2546), A4769=dict(grupos=G4769), A80=dict(grupos=G80), A1824=dict(grupos=G1824), A3269=dict(grupos=G3269))
CONTR = {"c_H_M_2546": ("H2546", "M2546"), "c_2546_4769": ("A2546", "A4769"),
         "c_80_3269": ("A80", "A3269"), "c_1824_3269": ("A1824", "A3269")}
for nom, (a, b) in CONTR.items():
    c = LF.contraste_seccion(cel, GR[a], GR[b]).rename(columns={"contraste": nom})
    S = S.merge(c, on=["edo", "seccion"], how="left", validate="1:1")
    if nom != "c_H_M_2546":     # solo los contrastes de edad llevan la versión log(O/E) 2024
        c = LF.contraste_seccion(cel, GR[a], GR[b], col="delta_log").rename(columns={"contraste": nom + "_L"})
        S = S.merge(c, on=["edo", "seccion"], how="left", validate="1:1")
log(f"- Medida log(sv_2024/E_2024): celdas excluidas por sv_2024 = 0, E_2024 = 0 o NaN: {n_log_excl:,} de {len(cel):,} "
    f"({n_log_excl_w:,} de ellas con peso n_2024 > 0).")
log(f"- Tiempo hasta estadísticos de sección: {time.time() - T0:.0f} s.")

# ------------------------------------------------------------------ bootstrap
rng = np.random.default_rng([C.SEMILLA, SUFIJO_LECTURAS])
Bn = C.B_PERMANENCIA
M = LF.multiplicidades(estr, Bn, rng)
M1 = np.vstack([np.ones((1, n_mun)), M.astype(np.float64)])      # fila 0 = estimación puntual
mun_s = S["mun"].to_numpy()
pm = S["perfil_may"].to_numpy()
lnw = S["ln_tot"].to_numpy(float)
log(f"- Bootstrap: B = {Bn}, nivel {C.NIVEL_IC_PERMANENCIA}, semilla [{C.SEMILLA}, {SUFIJO_LECTURAS}]; suma de multiplicidades por estado "
    f"conservada: {bool(all((M[:, estr == e].sum(axis=1) == (estr == e).sum()).all() for e in np.unique(estr)))}.")

def resumen(reps):
    """reps[0] = puntual; devuelve (valor, lo, hi)."""
    lo, hi = LF.ic_percentil(reps[1:], C.NIVEL_IC_PERMANENCIA)
    return float(reps[0]), lo, hi


def media_perfil(col, mask):
    num, den = LF.media_ponderada_por_mun(S[col].to_numpy(float), lnw, mun_s, n_mun, mask & S[col].notna().to_numpy())
    return LF.razon_boot(M1, num, den)


def contraste_perfil(col, k, vs_otros):
    r = media_perfil(col, pm == k)
    if vs_otros:
        r = r - media_perfil(col, (pm != k) & (pm > 0))
    return r


def spearman_perfil(col, k):
    ok = (pm == k) & S[col].notna().to_numpy() & S["brecha_sec"].notna().to_numpy()
    return LF.spearman_boot(S["brecha_sec"].to_numpy(float)[ok], S[col].to_numpy(float)[ok], lnw[ok], mun_s[ok], M1)


def mediana_p3_vs_objetivo(col, k):
    ok = S[col].notna().to_numpy()
    x = S[col].to_numpy(float)
    w_obj = S[[f"ln_perfil_{j}" for j in range(1, K + 1)]].sum(axis=1).to_numpy(float)   # LN objetivo de la sección
    a = LF.mediana_boot(x[ok & (pm == k)], lnw[ok & (pm == k)], mun_s[ok & (pm == k)], M1)
    b = LF.mediana_boot(x[ok & (w_obj > 0)], w_obj[ok & (w_obj > 0)], mun_s[ok & (w_obj > 0)], M1)
    return a - b


def rural_menos_urbano(k):
    return media_perfil("brecha_sec", (pm == k) & (S["tiposec"] == "R").to_numpy()) - \
        media_perfil("brecha_sec", (pm == k) & (S["tiposec"] == "U").to_numpy())


# ------------------------------------------------------------------ batería común
ruta = INT / "resultados.pkl"
assert ruta.exists(), "falta la caché de tendencia: correr scripts/validacion/pruebas_lecturas.py primero"
R = pickle.load(open(ruta, "rb"))
elecs = list(R["elecciones"])
assert elecs == [2009, 2012, 2015, 2018, 2021, 2024], elecs
assert R["tend_dif"].shape == (K, 6, Bn + 1)
assert abs(R["control_2024"] - CONTROL_2024) < 5e-5
i_int = [elecs.index(a) for a in (2009, 2015, 2021)]; i_pres = [elecs.index(a) for a in (2012, 2018, 2024)]
# D-026: iim_dp2 crece cuando BAJA la intensidad migratoria; se multiplica por -1 para que negativo = brecha más profunda donde hay más intensidad
neg = lambda r: -r
# T11: IC de -rho = (-hi, -lo)
def t02(k):
    d = R["tend_dif"][k - 1]
    return d[i_int].mean(axis=0) - d[i_pres].mean(axis=0)
CON = {"T03": "c_H_M_2546", "T04": "c_1824_3269", "T05": "c_80_3269", "T06": "c_2546_4769"}
# c_H_M_2546_L no existe en pruebas_lecturas (solo contrastes de edad): se calcula aquí con la misma función
c = LF.contraste_seccion(cel, GR["H2546"], GR["M2546"], col="delta_log").rename(columns={"contraste": "c_H_M_2546_L"})
S = S.merge(c, on=["edo", "seccion"], how="left", validate="1:1")
PR = [  # id, texto, unidad, signo, función(k) -> réplicas
    ("T01", "La brecha se agrava con el tiempo", "pp/elección", -1, lambda k: R["tend_pend"][k - 1]),
    ("T02", "Más profunda en intermedias que en presidenciales", "pp", -1, t02),
    ("T03", "Hombres 25–46 más abajo que mujeres 25–46 (misma sección)", "diferencia de brecha logit", -1, lambda k: contraste_perfil("c_H_M_2546", k, False)),
    ("T04", "Jóvenes 18–24 más abajo que adultos 32–69", "diferencia de brecha logit", -1, lambda k: contraste_perfil("c_1824_3269", k, False)),
    ("T05", "Personas de 80+ más abajo que adultos 32–69", "diferencia de brecha logit", -1, lambda k: contraste_perfil("c_80_3269", k, False)),
    ("T06", "Adultos 25–46 más abajo que 47–69 (los que más se mudan)", "diferencia de brecha logit", -1, lambda k: contraste_perfil("c_2546_4769", k, False)),
    ("T07", "Más profunda donde hay más nacidos en otra entidad", "correlación de Spearman", -1, lambda k: spearman_perfil("prop_nacida_otra_ent", k)),
    ("T08", "Más profunda donde llegan más electores", "correlación de Spearman", -1, lambda k: spearman_perfil("pctl_mov_estado", k)),
    ("T09", "Más profunda donde más se habla lengua indígena", "correlación de Spearman", -1, lambda k: spearman_perfil("prop_hli", k)),
    ("T10", "Más profunda donde hay menos internet", "correlación de Spearman", -1, lambda k: spearman_perfil("falta_internet", k)),
    ("T11", "Más profunda donde hay más intensidad migratoria a EE. UU.", "correlación de Spearman", -1, lambda k: neg(spearman_perfil("iim_dp2", k))),
    ("T12", "Más electores registrados que adultos residentes", "diferencia de medianas", +1, lambda k: mediana_p3_vs_objetivo("razon_ln_p18", k)),
    ("T13", "Más profunda en secciones rurales que urbanas", "diferencia de brecha logit", -1, lambda k: rural_menos_urbano(k)),
]
LECT_DE = {1: ("T01", "T07", "T08"), 2: ("T02",), 3: ("T03", "T11", "T12"), 4: ("T06", "T07", "T08"), 5: ("T04", "T05", "T09", "T10", "T13")}
V = LF.veredicto_prediccion
NAN = float("nan")


def celda(rep, sg):
    v, lo, hi = resumen(rep)
    return v, lo, hi, V(v, lo, hi, sg)


filas = []
for pid, txt, unidad, sg, f in PR:
    for k in range(1, K + 1):
        t = time.time()
        fila = dict(id=pid, prueba=txt, perfil=k, unidad=unidad, signo_consistente="positiva" if sg > 0 else "negativa")
        rural_sin = pid == "T13" and (SEC.loc[k - 1, "secciones_rurales"] < 1 or SEC.loc[k - 1, "secciones_urbanas"] < 1)
        if rural_sin:
            fila.update(valor=NAN, ic_inf=NAN, ic_sup=NAN, veredicto="sin datos")
        else:
            v, lo, hi, ver = celda(f(k), sg)
            if not np.isfinite(v):
                ver = "sin datos"
            fila.update(valor=v, ic_inf=lo, ic_sup=hi, veredicto=ver)
        if pid in CON:
            c0 = CON[pid]
            v, lo, hi, ver = celda(contraste_perfil(c0, k, True), sg)
            fila.update(valor_vs_otros=v, ic_vs_otros_inf=lo, ic_vs_otros_sup=hi, veredicto_vs_otros=ver)
            vl, llo, lhi, verl = celda(contraste_perfil(c0 + "_L", k, False), sg)
            vlo, olo, ohi, verlo = celda(contraste_perfil(c0 + "_L", k, True), sg)
            fila.update(valor_L=vl, ic_L_inf=llo, ic_L_sup=lhi, veredicto_L=verl,
                        valor_vs_otros_L=vlo, ic_vs_otros_L_inf=olo, ic_vs_otros_L_sup=ohi, veredicto_vs_otros_L=verlo,
                        veredicto_combinado=LF.veredicto_combinado(fila["veredicto"], verl),
                        veredicto_combinado_vs_otros=LF.veredicto_combinado(ver, verlo))
        else:
            fila.update(veredicto_combinado=fila["veredicto"])
        fila["de_su_lectura"] = pid in LECT_DE[k]
        filas.append(fila)
        print(f"  {pid} P{k}: {fila['valor']:+.4f} [{fila['ic_inf']:+.4f}, {fila['ic_sup']:+.4f}] {fila['veredicto']} ({time.time() - t:.0f} s)", flush=True)
BT = pd.DataFrame(filas)
cols = ["id", "prueba", "perfil", "valor", "ic_inf", "ic_sup", "unidad", "signo_consistente", "veredicto", "valor_vs_otros",
        "ic_vs_otros_inf", "ic_vs_otros_sup", "veredicto_vs_otros", "valor_L", "ic_L_inf", "ic_L_sup", "veredicto_L",
        "valor_vs_otros_L", "ic_vs_otros_L_inf", "ic_vs_otros_L_sup", "veredicto_vs_otros_L", "veredicto_combinado",
        "veredicto_combinado_vs_otros", "de_su_lectura"]
BT = BT[cols]
BT.to_csv(SAL / "bateria_comun.csv", index=False)

# ------------------------------------------------------------------ conciliación con pruebas_lecturas
P7 = pd.read_csv(LECT / "predicciones.csv").set_index("id")
MAP = [  # (id en pruebas_lecturas, id en la batería, perfil, columna base, signo de conversión)
    ("P1.i-a", "T08", 1, ""), ("P1.i-b", "T07", 1, ""), ("P1.ii-a", "T01", 1, ""),
    ("P3.i-a", "T03", 3, ""), ("P3.i-b", "T03", 3, "_vs_otros"), ("P3.ii", "T11", 3, "neg"), ("P3.iii", "T12", 3, ""),
    ("P4.i-a", "T06", 4, ""), ("P4.i-b", "T06", 4, "_vs_otros"), ("P4.ii-a", "T07", 4, ""), ("P4.ii-b", "T08", 4, ""),
    ("P5.i-a", "T05", 5, ""), ("P5.i-b", "T05", 5, "_vs_otros"), ("P5.i-c", "T04", 5, ""), ("P5.i-d", "T04", 5, "_vs_otros"),
    ("P5.ii-a", "T09", 5, ""), ("P5.ii-b", "T10", 5, ""), ("P5.iii", "T13", 5, ""),
    ("P4.i-a-L", "T06", 4, "_L"), ("P4.i-b-L", "T06", 4, "_vs_otros_L"), ("P5.i-a-L", "T05", 5, "_L"), ("P5.i-b-L", "T05", 5, "_vs_otros_L"),
    ("P5.i-c-L", "T04", 5, "_L"), ("P5.i-d-L", "T04", 5, "_vs_otros_L")]
rec = []
maxd = 0.0
for p7, t, k, suf in MAP:
    r = BT[(BT["id"] == t) & (BT["perfil"] == k)].iloc[0]
    if suf in ("", "neg"):
        v, lo, hi = r["valor"], r["ic_inf"], r["ic_sup"]
    elif suf == "_vs_otros":
        v, lo, hi = r["valor_vs_otros"], r["ic_vs_otros_inf"], r["ic_vs_otros_sup"]
    elif suf == "_L":
        v, lo, hi = r["valor_L"], r["ic_L_inf"], r["ic_L_sup"]
    else:
        v, lo, hi = r["valor_vs_otros_L"], r["ic_vs_otros_L_inf"], r["ic_vs_otros_L_sup"]
    a = P7.loc[p7, ["valor", "ic_inf", "ic_sup"]].to_numpy(float)
    if suf == "neg":
        a = np.array([-a[0], -a[2], -a[1]])
    d = float(np.abs(a - np.array([v, lo, hi])).max())
    maxd = max(maxd, d)
    rec.append(dict(id_lecturas=p7, id_bateria=t, perfil=k, variante=suf or "base", dif_max=d, ok=d < 1e-9))
REC = pd.DataFrame(rec)
assert REC["ok"].all(), REC[~REC["ok"]]

# ------------------------------------------------------------------ reporte
def pivote(col_v):
    out = []
    for pid, txt, *_ in PR:
        r = {"id": pid, "prueba": txt}
        for k in range(1, K + 1):
            x = BT[(BT["id"] == pid) & (BT["perfil"] == k)].iloc[0]
            val = "NaN" if not np.isfinite(x["valor"]) else f"{x['valor']:+.3f}"
            r[f"P{k}"] = f"{val} {x[col_v]}" + (" *" if x["de_su_lectura"] else "")
        out.append(r)
    return pd.DataFrame(out)


log("# Batería común de pruebas T01–T13 (D-036)\n")
log("## Cifras de control\n")
log(f"- Celdas objetivo: {len(obj):,} (control {N_CELDAS_OBJ:,}) OK. Participación nacional 2024 (panel, de la caché de pruebas_lecturas) = {100 * R['control_2024']:.2f}% (control 59.67%) OK.")
log(f"- Bootstrap: B = {Bn}, semilla [{C.SEMILLA}, {SUFIJO_LECTURAS}], mismas multiplicidades que pruebas_lecturas. Tendencia (T01, T02) leída de su caché.")
log(f"- Conciliación con pruebas_lecturas/predicciones.csv: {len(REC)} celdas comparadas, dif. máxima = {maxd:.2e} (tolerancia 1e-9): OK.")
log("- T11: Spearman(brecha, iim_dp2) multiplicado por -1 (IC = (-sup, -inf)). Razón: `iim_dp2` crece cuando BAJA la intensidad migratoria (D-026; Spearman municipal -0.96 con remesas); pruebas_lecturas predecía signo + (P3.ii); aquí negativo = consistente.")
log("- T03 con log(O/E) 2024 (`_L`) no existía en pruebas_lecturas (solo contrastes de edad); se calculó aquí con la misma función y la misma pertenencia.")
log("- T02: media de la diferencia observada-esperada (pp) en intermedias (2009, 2015, 2021) menos presidenciales (2012, 2018, 2024), réplica a réplica, de `tend_dif` de pruebas_lecturas.")
log("- `*` = la prueba corresponde a la lectura del perfil. P2 solo tiene T02 como prueba de su lectura.\n")
log("## Secciones mayoritarias por perfil\n")
log(md(SEC.round(2)))
log("\n## Valor y veredicto (medida δ̃; * = de su lectura)\n")
log(md(pivote("veredicto")))
log("\n## Veredicto combinado (δ̃ y log(O/E) 2024; T03–T06, versión base)\n")
log(md(pivote("veredicto_combinado")))
log("\n## Pruebas T03–T06, versión «más que en los otros perfiles»\n")
x = BT[BT["id"].isin(CON)][["id", "perfil", "valor_vs_otros", "ic_vs_otros_inf", "ic_vs_otros_sup", "veredicto_vs_otros", "veredicto_combinado_vs_otros"]]
log(md(x.round(4)))
log("\n## Tabla larga completa\n")
log(md(BT.round(4)))
log(f"\nTiempo total: {time.time() - T0:.0f} s.")
(SAL / "control.md").write_text("\n".join(QA) + "\n", encoding="utf-8")
