"""Pruebas de las lecturas de cada perfil con predicciones fijadas de antemano (D-034).

Unidad: secciones donde el perfil es mayoritario (resp x LN 2024 de celdas objetivo / LN total > 1/2); se usan todas
las celdas de la sección y su brecha de todo el periodo. Contrastes dentro de sección (prueba principal), asociaciones
entre secciones (Spearman ponderada, peso LN) y tendencia 2009->2024. IC95% percentil con bootstrap de municipios
estratificado por estado (D-032), B y nivel de config (D-027), semilla [SEMILLA, 9].
Entradas: brecha_celda, perfiles_finales, descriptores_seccion, panel_celda_eleccion y violencia_mpio.
Salidas: reports/validacion/pruebas_lecturas/, caché data/interim/pruebas_lecturas/resultados.pkl (borrarlo para rehacer).
Uso: .venv/bin/python scripts/validacion/pruebas_lecturas.py"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import pickle
import time

import numpy as np
import pandas as pd

from ine_perfiles import brecha as B
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
log("# Pruebas de las lecturas de cada perfil (D-034)\n")
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
SEC.to_csv(SAL / "secciones_por_perfil.csv", index=False)
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


# (perfil, lectura, id, texto de la predicción, signo predicho, función)
PRED = [
    (3, "Emigración a EE. UU.", "P3.i-a", "Brecha de hombres 25–46 más profunda que la de mujeres 25–46 (en sus secciones)", -1,
     lambda: contraste_perfil("c_H_M_2546", 3, False)),
    (3, "Emigración a EE. UU.", "P3.i-b", "Esa diferencia H−M 25–46 es mayor que en las secciones de los demás perfiles", -1,
     lambda: contraste_perfil("c_H_M_2546", 3, True)),
    (3, "Emigración a EE. UU.", "P3.ii", "Spearman(brecha, iim_dp2) > 0 (más intensidad migratoria = brecha más profunda)", +1,
     lambda: spearman_perfil("iim_dp2", 3)),
    (3, "Emigración a EE. UU.", "P3.iii", "Mediana de razon_ln_p18 de sus secciones mayor que la de la población objetivo", +1,
     lambda: mediana_p3_vs_objetivo("razon_ln_p18", 3)),
    (4, "Domicilio desactualizado / recién llegados", "P4.i-a", "Brecha de 25–46 más profunda que la de 47–69 (en sus secciones)", -1,
     lambda: contraste_perfil("c_2546_4769", 4, False)),
    (4, "Domicilio desactualizado / recién llegados", "P4.i-b", "Esa diferencia 25–46 vs 47–69 es mayor que en los demás perfiles", -1,
     lambda: contraste_perfil("c_2546_4769", 4, True)),
    (4, "Domicilio desactualizado / recién llegados", "P4.ii-a", "Spearman(brecha, prop_nacida_otra_ent) < 0", -1,
     lambda: spearman_perfil("prop_nacida_otra_ent", 4)),
    (4, "Domicilio desactualizado / recién llegados", "P4.ii-b", "Spearman(brecha, pctl_mov_estado) < 0", -1,
     lambda: spearman_perfil("pctl_mov_estado", 4)),
    (5, "Barreras de acceso", "P5.i-a", "Brecha de 80+ más profunda que la de 32–69 (en sus secciones)", -1,
     lambda: contraste_perfil("c_80_3269", 5, False)),
    (5, "Barreras de acceso", "P5.i-b", "Esa diferencia 80+ vs 32–69 es mayor que en los demás perfiles", -1,
     lambda: contraste_perfil("c_80_3269", 5, True)),
    (5, "Barreras de acceso", "P5.i-c", "Brecha de 18–24 más profunda que la de 32–69 (en sus secciones)", -1,
     lambda: contraste_perfil("c_1824_3269", 5, False)),
    (5, "Barreras de acceso", "P5.i-d", "Esa diferencia 18–24 vs 32–69 es mayor que en los demás perfiles", -1,
     lambda: contraste_perfil("c_1824_3269", 5, True)),
    (5, "Barreras de acceso", "P5.ii-a", "Spearman(brecha, prop_hli) < 0", -1, lambda: spearman_perfil("prop_hli", 5)),
    (5, "Barreras de acceso", "P5.ii-b", "Spearman(brecha, 1 − prop_internet) < 0", -1, lambda: spearman_perfil("falta_internet", 5)),
    (5, "Barreras de acceso", "P5.iii", "Brecha de sus secciones rurales más profunda que la de las urbanas (tiposec R vs U)", -1,
     lambda: rural_menos_urbano(5)),
    (1, "Baja vinculación local, población joven en llegada", "P1.i-a", "Spearman(brecha, pctl_mov_estado) < 0", -1,
     lambda: spearman_perfil("pctl_mov_estado", 1)),
    (1, "Baja vinculación local, población joven en llegada", "P1.i-b", "Spearman(brecha, prop_nacida_otra_ent) < 0", -1,
     lambda: spearman_perfil("prop_nacida_otra_ent", 1)),
]

AGE = [x for x in PRED if x[2] in ("P4.i-a", "P4.i-b", "P5.i-a", "P5.i-b", "P5.i-c", "P5.i-d")]
_col = {"P4.i-a": ("c_2546_4769", False), "P4.i-b": ("c_2546_4769", True), "P5.i-a": ("c_80_3269", False),
        "P5.i-b": ("c_80_3269", True), "P5.i-c": ("c_1824_3269", False), "P5.i-d": ("c_1824_3269", True)}
PRED_L = [(k, l, pid + "-L", t + " [log(O/E) 2024]", sg, (lambda c=_col[pid], k=k: contraste_perfil(c[0] + "_L", k, c[1])))
          for k, l, pid, t, sg, f in AGE]
ruta = INT / "resultados.pkl"
if ruta.exists():
    R = pickle.load(open(ruta, "rb"))
    log(f"- Resultados leídos de caché {ruta.name} (borrarlo para rehacer).")
else:
    R = {}
    for k, lect, pid, txt, sg, f in PRED + PRED_L:
        t = time.time()
        R[pid] = resumen(f())
        print(f"  {pid}: {R[pid][0]:+.4f} [{R[pid][1]:+.4f}, {R[pid][2]:+.4f}]  ({time.time() - t:.0f} s)", flush=True)
    # descriptor P1: homicidios (D-027)
    R["P1.desc"] = resumen(spearman_perfil("log_tasa_homicidio", 1))

    # ------------------------------------------------------------------ tendencia (P1 ii)
    panel = pd.read_parquet(PROC / "panel_celda_eleccion.parquet", columns=["edo", "seccion", "sexo", "grupo", "aelec", "sv", "nv", "n"])
    for c in ("edo", "seccion", "sexo", "grupo"):
        panel[c] = panel[c].astype("int64")
    t24 = panel[panel["aelec"] == 2024]
    ctrl = float(t24["sv"].sum() / (t24["sv"].sum() + t24["nv"].sum()))
    R["control_2024"] = ctrl
    R["panel_n_igual_sv_nv"] = bool((panel["n"] == panel["sv"] + panel["nv"]).all())
    q = B.tasa_esperada(panel)
    p = panel[panel["n"] > 0].merge(q, on=["sexo", "grupo", "aelec"], how="left", validate="m:1")
    del panel
    p = p.merge(obj[["edo", "seccion", "sexo", "grupo", "perfil"]], on=["edo", "seccion", "sexo", "grupo"], how="inner", validate="m:1")
    p = p.merge(S[["edo", "seccion", "mun"]], on=["edo", "seccion"], how="inner", validate="m:1")
    p["sv"] = p["sv"].astype(float); p["nv"] = p["nv"].astype(float)
    p["nn"] = p["sv"] + p["nv"]                       # SV + NV (D-001)
    p["e"] = p["nn"] * p["q"]
    elecs = sorted(p["aelec"].unique())
    R["elecciones"] = elecs
    R["panel_celdas_obj"] = int(p[["edo", "seccion", "sexo", "grupo"]].drop_duplicates().shape[0])
    dif = np.zeros((K, len(elecs), Bn + 1))              # puntos
    obs_pt = np.zeros((K, len(elecs))); esp_pt = np.zeros((K, len(elecs)))
    for k in range(1, K + 1):
        for j, a in enumerate(elecs):
            s = p[(p["perfil"] == k) & (p["aelec"] == a)]
            sv_m = np.bincount(s["mun"], weights=s["sv"], minlength=n_mun)
            n_m = np.bincount(s["mun"], weights=s["nn"], minlength=n_mun)
            e_m = np.bincount(s["mun"], weights=s["e"], minlength=n_mun)
            dif[k - 1, j] = 100 * LF.razon_boot(M1, sv_m - e_m, n_m)
            obs_pt[k - 1, j] = 100 * sv_m.sum() / n_m.sum(); esp_pt[k - 1, j] = 100 * e_m.sum() / n_m.sum()
    xs = np.arange(len(elecs))
    pend = np.stack([LF.pendiente_mco(dif[k].T, xs) for k in range(K)])      # (K, B+1), puntos por elección
    R["tend_dif"] = dif; R["tend_pend"] = pend; R["obs_pt"] = obs_pt; R["esp_pt"] = esp_pt
    R["P1.ii-a"] = resumen(pend[0])
    R["P1.ii-b"] = resumen(pend[0] - pend[1:].mean(axis=0))
    pickle.dump(R, open(ruta, "wb"))

# ------------------------------------------------------------------ tablas
PRED = PRED + PRED_L + [
    (1, "Baja vinculación local, población joven en llegada", "P1.ii-a", "Pendiente de la diferencia observada−esperada 2009→2024 negativa (pp por elección)", -1, None),
    (1, "Baja vinculación local, población joven en llegada", "P1.ii-b", "Esa pendiente es más negativa que la media de los demás perfiles", -1, None),
]
filas = []
for k, lect, pid, txt, sg, f in PRED:
    v, lo, hi = R[pid]
    filas.append(dict(perfil=k, lectura=lect, id=pid, prediccion=txt, estadistico="pendiente (pp/elección)" if "ii-" in pid and k == 1 else
                      ("Spearman ponderada" if "Spearman" in txt else ("diferencia de medianas" if pid == "P3.iii" else "diferencia de brecha (δ̃)")),
                      valor=v, ic_inf=lo, ic_sup=hi, signo_predicho=sg, veredicto=LF.veredicto_prediccion(v, lo, hi, sg),
                      medida="log(O/E) 2024" if pid.endswith("-L") else ("sin medida δ̃ (tendencia)" if k == 1 and "ii-" in pid else
                                                                          ("δ̃ todo el periodo" if "Spearman" not in txt else "Spearman sobre δ̃"))))
PT = pd.DataFrame(filas)
PT["id_inciso"] = PT["id"].str.replace("-L", "", regex=False)
_v = PT.set_index("id")["veredicto"]
PT["veredicto_combinado"] = [LF.veredicto_combinado(_v[i], _v[i + "-L"]) if i + "-L" in _v.index else _v[i] for i in PT["id_inciso"]]
PT = PT.drop(columns="id_inciso")
v, lo, hi = R["P1.desc"]
PT = pd.concat([PT, pd.DataFrame([dict(perfil=1, lectura="Baja vinculación local, población joven en llegada", id="P1.desc",
                                       prediccion="Descriptor (sin predicción): Spearman(brecha, log tasa de homicidio municipal 2023)",
                                       estadistico="Spearman ponderada", valor=v, ic_inf=lo, ic_sup=hi, signo_predicho=0,
                                       veredicto="descriptor (D-027)", veredicto_combinado="descriptor (D-027)", medida="Spearman sobre δ̃")])], ignore_index=True)
PT.to_csv(SAL / "predicciones.csv", index=False)

LECT = {1: "Baja vinculación local, población joven en llegada", 3: "Emigración a EE. UU.",
        4: "Domicilio desactualizado / recién llegados", 5: "Barreras de acceso"}
vr = []
for k in (1, 3, 4, 5):
    x = PT[(PT["perfil"] == k) & (PT["signo_predicho"] != 0) & ~PT["id"].str.endswith("-L")]   # un renglón por inciso
    vc = x["veredicto_combinado"]
    vr.append(dict(perfil=k, lectura=LECT[k], incisos=len(x), se_cumplen=int((vc == "se cumple").sum()),
                   contrarias=int((vc == "contraria").sum()), no_concluyentes=int((vc == "no concluyente").sum()),
                   no_se_cumplen=int((vc == "no se cumple").sum()),
                   veredicto=LF.veredicto_lectura_concluyente(vc)))
vr.insert(1, dict(perfil=2, lectura="Vota cuando la elección moviliza", incisos=0, se_cumplen=0, contrarias=0,
                  veredicto="sin pruebas de motivo (patrón medido en D-030)"))
VR = pd.DataFrame(vr).sort_values("perfil")
VR.to_csv(SAL / "veredictos.csv", index=False)

elecs = R["elecciones"]
filas = []
for k in range(1, K + 1):
    for j, a in enumerate(elecs):
        lo, hi = LF.ic_percentil(R["tend_dif"][k - 1, j, 1:], C.NIVEL_IC_PERMANENCIA)
        filas.append(dict(perfil=k, eleccion=a, observada_pct=R["obs_pt"][k - 1, j], esperada_pct=R["esp_pt"][k - 1, j],
                          dif_pp=R["tend_dif"][k - 1, j, 0], ic_inf=lo, ic_sup=hi))
    v, lo, hi = resumen(R["tend_pend"][k - 1])
    filas.append(dict(perfil=k, eleccion="pendiente_pp_por_eleccion", dif_pp=v, ic_inf=lo, ic_sup=hi))
v, lo, hi = R["P1.ii-b"]
filas.append(dict(perfil=1, eleccion="pendiente_P1_menos_media_otros", dif_pp=v, ic_inf=lo, ic_sup=hi))
TD = pd.DataFrame(filas)
TD.to_csv(SAL / "tendencia.csv", index=False)

# ------------------------------------------------------------------ reporte
log(f"- Panel: control 2024 SV/(SV+NV) = {100 * R['control_2024']:.2f}% (control 59.67%); n = sv + nv en todas las filas: "
    f"{R['panel_n_igual_sv_nv']}. Celdas objetivo presentes en el panel: {R['panel_celdas_obj']:,}.")
assert abs(R["control_2024"] - CONTROL_2024) < 5e-5
log("\n## Predicciones (IC95% bootstrap de municipios)\n")
log(md(PT.round(4)))
log("\n## Veredictos por lectura (D-034)\n")
log(md(VR))
log("\n## Tendencia de la diferencia observada − esperada (puntos porcentuales)\n")
log(md(TD.round(3)))
log("""
## Elecciones de implementación (no están fijadas literalmente en D-034)

- Cada inciso de una predicción con dos partes (p. ej. P3.i: «es más profunda» y «mayor que en los demás perfiles») se prueba y califica por separado; el veredicto de lectura cuenta incisos.
- Peso de la brecha de grupo: n_2024; en las celdas sin n_2024 tampoco hay ln_2024 (sin población 2024), así que pesan 0.
- Peso LN de la sección = Σ ln_2024 de todas sus celdas (mismo denominador de la regla de mayoría). Contrastes: solo secciones donde ambos grupos tienen peso > 0.
- «Demás perfiles» = secciones mayoritarias de los otros cuatro perfiles juntas (las sin perfil mayoritario no entran).
- P3.iii: mediana ponderada (peso LN de la sección) de razon_ln_p18 en secciones P3 menos la mediana en la población objetivo (secciones ponderadas por su LN 2024 de celdas objetivo).
- P5.iii: rural = tiposec R, urbana = tiposec U (las mixtas M no entran); brecha de sección ponderada por LN.
- Tendencia: perfil asignado por celda (columna `perfil`); esperada = Σ n·q_gse/Σ n con q_gse nacional fijo (no se recalcula en cada réplica); bootstrap con las mismas multiplicidades de municipio aplicadas a las celdas; pendiente sobre el índice de elección 0..5 (2009, 2012, 2015, 2018, 2021, 2024: espaciadas 3 años, la pendiente es por elección).
- Sensibilidad de edad (D-034, agregado): los seis contrastes de edad se repiten con log(sv_2024/E_2024) (celdas con sv_2024 > 0 y E_2024 > 0, mismo peso n_2024, misma pertenencia y mismas réplicas). Veredicto combinado: igual en ambas medidas, se queda; si no, «no concluyente» (no cuenta). Lectura: respaldada = todos los incisos concluyentes se cumplen y ninguno es contrario; parcial = alguno se cumple; no respaldada = ninguno. Los renglones con id terminado en -L son la versión log(O/E); la columna `veredicto_combinado` es la que cuenta.
- Asociaciones: se descartan las secciones con descriptor NaN; la brecha de la sección usa todas sus celdas (peso n_2024).
- Un IC de percentil del bootstrap sin corrección; las asociaciones entre secciones son contextuales (D-010).
""")
log(f"\nTiempo total: {time.time() - T0:.0f} s.")
(SAL / "control.md").write_text("\n".join(QA) + "\n", encoding="utf-8")
