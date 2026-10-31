"""Validación con 2024: los cinco perfiles reajustados solo con 2009-2021 frente al déficit de 2024 (D-025, D-029).

Reajusta la mezcla K=5 con 2009-2021 (misma construcción que la referencia de cuatro perfiles), mide la curva de
captura contra 2024 y compara con ΔAUC y bootstrap pareado (D-027): (a) historial propio − K5; (b) K5 − K4.
También mide la persistencia por perfil y el ARI con los perfiles del periodo completo.
Entradas: cachés de seleccion_numero_perfiles (pca.pkl) y referencia_cuatro_perfiles (ajuste_2009_2021_K4.pkl),
perfiles_k4.parquet, perfiles_finales.parquet, brecha_celda y panel_celda_eleccion.
Salidas: reports/validacion/validacion_2024/, caché data/interim/validacion_2024/ (borrarla para rehacer el ajuste).
Uso: .venv/bin/python scripts/validacion/validacion_2024.py"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import pickle
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import mezcla_mixta as MM

K = C.K_EVALUADO_K5            # D-029
K4 = 4                         # referencia de cuatro perfiles (D-029)
N_PROC = 4                     # procesos en paralelo (no cambia ningún resultado)
LLAVE = CF.LLAVE
PROC = C.PROCESADOS
SAL = C.salidas(__file__)
INT_SEL = C.INTERIM / "seleccion_numero_perfiles"        # solo lectura
INT_REF = C.INTERIM / "referencia_cuatro_perfiles"       # solo lectura
INT = C.cache("validacion_2024")
T0 = time.time()
QA = []


def log(*a):
    print(f"[{time.time() - T0:7.0f}s]", *a, flush=True)


def chk(cond, texto):
    QA.append(f"- [{'OK' if cond else 'FALLA'}] {texto}")
    assert cond, texto


def md_t(df):
    df = df.astype(object)
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)] +
                     ["| " + " | ".join(map(str, r)) + " |" for r in df.to_numpy()])


# ======================================================================== 1. universo y datos 2009-21 (D-025)
with open(INT_SEL / "pca.pkl", "rb") as fh:
    P = pickle.load(fh)
U0 = CF.cargar_universo(PROC)
cel, h_ok, obj0, m4 = U0["cel"], U0["h_ok"], U0["obj0"], U0["m4"]
chk(obj0.sum() == U0["b"]["objetivo_0921"].fillna(False).astype(bool).sum(), f"población objetivo 2009-21 = {obj0.sum():,} celdas")
o0 = cel[obj0].reset_index(drop=True)
dat0, x0, n_cero0 = CF.construir_datos(o0, P["d"], P["pcs"], P["r"], "delta_0921", "deficit_0921")
chk(abs(dat0.w.sum() - dat0.n) < 1e-6 * dat0.n, f"Σ pesos = {dat0.w.sum():,.1f} = nº de celdas {dat0.n:,}")
for c in LLAVE:
    x0[c] = x0[c].astype("int64")

# ======================================================================== 2. ajustes 2009-21: K=4 (de la referencia, lectura) y K=5
with open(INT_REF / "ajuste_2009_2021_K4.pkl", "rb") as fh:
    mod4, ll4, info4 = pickle.load(fh)
R4, ll4_chk = MM.estep(dat0, mod4)
chk(abs(ll4_chk - ll4) < 0.1, f"K=4 2009-21: logL recalculada {ll4_chk:,.1f} = caché de la referencia ({ll4:,.1f}): mismos datos")
ruta5 = INT / "ajuste_2009_2021_K5.pkl"
if ruta5.exists():
    with open(ruta5, "rb") as fh:
        mod5, ll5, info5 = pickle.load(fh)
    log("ajuste K=5 2009-21 leído de caché")
else:
    rng = np.random.default_rng([C.SEMILLA, 2, K])      # misma regla de semilla que seleccion.tarea_ajuste
    aj5, info5 = MM.ajustar_con_reinicios(dat0, K, rng, log=log)
    mod5, ll5 = aj5.modelo, aj5.logL
    with open(ruta5, "wb") as fh:
        pickle.dump((mod5, ll5, info5), fh)
R5, ll5_chk = MM.estep(dat0, mod5)
chk(abs(ll5_chk - ll5) < 0.1, f"K=5 2009-21: logL recalculada {ll5_chk:,.1f} = ajuste ({ll5:,.1f})")
map4, map5 = R4.argmax(1), R5.argmax(1)


def reetiq(map0, ref, KK):
    """Asignación húngara contra la asignación completa `ref` (perfil 1..KK, w) en las celdas comunes (D-021)."""
    xp = x0[LLAVE].merge(ref[LLAVE + ["perfil", "w"]], on=LLAVE, how="left", validate="1:1")
    comun = xp["perfil"].notna().to_numpy()
    mapa, cruce = CF.reetiquetar(xp.perfil[comun].to_numpy(int) - 1, map0[comun], xp.w[comun].to_numpy(), KK)
    p0 = mapa[map0] + 1
    ari = CF.ari_ponderado(xp.perfil[comun].to_numpy(int), p0[comun], xp.w[comun].to_numpy())
    return p0, ari, int(comun.sum()), cruce, mapa


sal4 = pd.read_parquet(PROC / "perfiles_k4.parquet")
sal5 = pd.read_parquet(PROC / "perfiles_finales.parquet")
for s in (sal4, sal5):
    for c in LLAVE:
        s[c] = s[c].astype("int64")
perfil4_0, ari4, ncom4, cr4, _ = reetiq(map4, sal4, K4)
perfil5_0, ari5, ncom5, cr5, mapa5 = reetiq(map5, sal5, K)
cruce5 = pd.DataFrame({f"perfil_completo_{j + 1}": [100 * cr5[k, j] / cr5[:, j].sum() for k in range(K)] for j in range(K)},
                      index=[f"clase 2009-21 → perfil {mapa5[k] + 1}" for k in range(K)])
cruce5.round(2).to_csv(SAL / "cruce_K5_0921.csv", float_format="%.3f")
pd.DataFrame([dict(K=K4, ARI_ponderado=ari4, celdas_comunes=ncom4), dict(K=K, ARI_ponderado=ari5, celdas_comunes=ncom5)]).to_csv(
    SAL / "ari.csv", index=False, float_format="%.5f")

# ======================================================================== 3. r̂ de cada método y AUC
r_a = (cel["p_tilde_0921"].astype(float) / (cel["E_0921"] / cel["N_0921"])).to_numpy()
post_a = np.isnan(r_a)
r_a = np.where(post_a, 1.0, r_a)       # sin historial propio: razón 1 = "solo edad y sexo", al final
r_5, post_5, rp5, rn5 = CF.rhat_mezcla(cel, h_ok, obj0, o0, perfil5_0, K)
r_4, post_4, rp4, rn4 = CF.rhat_mezcla(cel, h_ok, obj0, o0, perfil4_0, K4)
M = {"historial propio": (r_a, post_a), "mezcla K=5 (2009-21)": (r_5, post_5), "mezcla K=4 (2009-21)": (r_4, post_4)}
U = {"solo celdas con historial 2009-21": m4 & h_ok, "todas las celdas con 2024": m4}
ln24 = cel["ln_2024"].to_numpy(float)
d24 = cel["deficit_2024_crudo"].to_numpy(float)
ref_k4 = pd.read_csv(C.salidas("perfiles/referencia_cuatro_perfiles") / "captura_resumen.csv")
auc_rows, curvas = [], []
for un, mk in U.items():
    for nom, (r, post) in M.items():
        c, ap, as_ = CF.curva_captura(r[mk], ln24[mk], d24[mk], None if post is None else post[mk])
        auc_rows.append(dict(universo=un, metodo=nom, AUC_pos=ap, AUC_signo=as_, celdas=int(mk.sum())))
        curvas.append(c.assign(universo=un, metodo=nom))
auc_t = pd.DataFrame(auc_rows)
auc_t.to_csv(SAL / "auc.csv", index=False, float_format="%.5f")
pd.concat(curvas, ignore_index=True).to_parquet(INT / "curvas_captura_K5.parquet", index=False)
g = lambda un, nom: float(auc_t[(auc_t.universo == un) & (auc_t.metodo == nom)].AUC_pos.iloc[0])
UV, UT = list(U)
chk(abs(g(UV, "historial propio") - 0.75909) < 5e-6 and abs(g(UT, "historial propio") - 0.69199) < 1.5e-5,
    f"historial propio: AUC {g(UV, 'historial propio'):.5f} (con historial, control 0.75909) y {g(UT, 'historial propio'):.5f} (todas, control 0.69199)")
for un in U:
    ref = float(ref_k4[(ref_k4.universo == un) & (ref_k4.metodo == "mezcla K=4 (2009-21)")].AUC_pos.iloc[0])
    chk(abs(g(un, "mezcla K=4 (2009-21)") - ref) < 5e-6, f"{un}: AUC mezcla K=4 {g(un, 'mezcla K=4 (2009-21)'):.5f} reproduce la referencia ({ref:.5f})")

# ======================================================================== 4. ΔAUC con bootstrap pareado (D-027)
comparaciones = [("(a) historial propio − K5", "historial propio", "mezcla K=5 (2009-21)"),
                 ("(b) K5 − K4", "mezcla K=5 (2009-21)", "mezcla K=4 (2009-21)")]


def tarea_delta(iu, ic):
    un, (nombre, n1, n2) = UV if iu == 0 else UT, comparaciones[ic]
    ruta = INT / f"dauc_{iu}_{ic}.pkl"
    if ruta.exists():
        with open(ruta, "rb") as fh:
            return pickle.load(fh)
    mk = U[un]
    (r1, p1), (r2, p2) = M[n1], M[n2]
    t = time.time()
    o = CF.delta_auc_bootstrap(r1[mk], None if p1 is None else p1[mk], r2[mk], None if p2 is None else p2[mk],
                               ln24[mk], d24[mk], cel["edo"].to_numpy()[mk], cel["seccion"].to_numpy()[mk])
    o["seg"] = time.time() - t
    with open(ruta, "wb") as fh:
        pickle.dump(o, fh)
    return o


jobs = [(iu, ic) for iu in (0, 1) for ic in (0, 1)]
salidas = Parallel(n_jobs=N_PROC)(delayed(tarea_delta)(*j) for j in jobs)
dt = []
for (iu, ic), o in zip(jobs, salidas):
    un, (nombre, n1, n2) = (UV, UT)[iu], comparaciones[ic]
    dt.append(dict(universo=un, comparacion=nombre, AUC_1=o["auc1"], AUC_2=o["auc2"], delta_AUC=o["delta"], IC95_inf=o["lo"],
                   IC95_sup=o["hi"], excluye_0=bool(o["lo"] > 0 or o["hi"] < 0), B=o["B"], seg=o["seg"], media_replicas=o["deltas"].mean()))
    chk(abs(o["auc1"] - g(un, n1)) < 1e-9 and abs(o["auc2"] - g(un, n2)) < 1e-9, f"{un} · {nombre}: AUC observado = tabla de AUC")
dt = pd.DataFrame(dt)
dt.to_csv(SAL / "delta_auc.csv", index=False, float_format="%.5f")

# ======================================================================== 5. persistencia por perfil
E0, O0 = cel["E_0921"].to_numpy(float), cel["O_0921"].to_numpy(float)
E4, O4 = cel["E_24"].to_numpy(float), cel["O_24"].to_numpy(float)
n24 = cel["n_2024"].to_numpy(float)
obj24 = cel["objetivo_24"].fillna(False).astype(bool).to_numpy()
ln24f = np.nan_to_num(ln24)


def fila_persist(nombre, mk):
    mk2 = mk & m4
    return dict(perfil=nombre, celdas=int(mk.sum()), ln_2024_miles=ln24f[mk].sum() / 1e3,
                razon_OE_0921=O0[mk].sum() / E0[mk].sum(), razon_OE_2024=O4[mk2].sum() / E4[mk2].sum(),
                pct_sigue_bajo_2024_ponderado_n24=100 * np.average(obj24[mk2], weights=n24[mk2]),
                pct_sigue_bajo_2024_celdas=100 * obj24[mk2].mean())


pp = np.zeros(len(cel), int)
pp[np.flatnonzero(obj0)] = perfil5_0
filas = [fila_persist(f"perfil {p}", pp == p) for p in range(1, K + 1)]
filas += [fila_persist("todos los objetivo_0921", obj0), fila_persist("no objetivo_0921 (con historial)", h_ok & ~obj0),
          fila_persist("base: todas las celdas con historial", h_ok)]
per = pd.DataFrame(filas)
per.to_csv(SAL / "persistencia_K5.csv", index=False, float_format="%.5f")
chk(int(per.celdas[:K].sum()) == int(obj0.sum()), f"persistencia: Σ celdas de los {K} perfiles = objetivo_0921 ({obj0.sum():,})")

# ======================================================================== reporte
fm = lambda df, d=4: md_t(df.round(d))
razon_txt = ", ".join(f"P{p}: {rp5[p - 1]:.4f}" for p in range(1, K + 1))
md = ["# Validación con 2024: cinco perfiles reajustados con 2009-21 (D-025, D-029)\n",
      "Mezcla K=5 reajustada con 2009-21 (objetivo_0921, δ̃ = delta_0921, w = déficit 2009-21; misma construcción que la referencia de cuatro perfiles), "
      "ordenada contra el déficit crudo 2024. Descriptivo; el ΔAUC mide la variabilidad del conjunto de evaluación (D-027).\n",
      "## 0. Cifras de control\n", *QA, "",
      f"- Ajuste K=5 2009-21: logL = {ll5:,.1f}; reinicios {info5['reinicios']}, óptimo repetido {info5['repeticiones']} veces "
      f"(repetido={info5['repetido']}), no convergieron {info5['no_convergio']}, pisos {info5['pisos']}; semilla [{C.SEMILLA}, 2, {K}]; celdas con w=0: {n_cero0}.",
      f"- Razón ΣO/ΣE 2009-21 por perfil (r̂): {razon_txt}; no objetivo con historial: {rn5:.4f}.\n",
      "## 1. AUC de la curva de captura (D-025)\n", fm(auc_t.drop(columns="AUC_signo"), 5),
      f"\n## 2. ΔAUC_pos con bootstrap pareado de secciones por estado (B = {C.B_PERMANENCIA}, IC {int(100 * C.NIVEL_IC_PERMANENCIA)}%)\n", fm(dt, 5),
      "\n## 3. K=5 reajustado con 2009-21 frente al K=5 completo\n",
      f"- ARI ponderado (w del K=5 completo) en {ncom5:,} celdas comunes (de {dat0.n:,}): **{ari5:.3f}** (K=4: {ari4:.3f}).\n",
      "Cruce (columnas = perfil del K=5 completo; % de su peso w en cada clase 2009-21):\n", md_t(cruce5.round(1).reset_index().rename(columns={"index": "clase 2009-21"})),
      "\n## 4. Persistencia por perfil (mezcla K=5 de 2009-21 → 2024)\n",
      "Razones O/E agrupadas ΣO/ΣE; '% sigue bajo' = objetivo_24 entre celdas con 2024, ponderado por n_2024; base = todas las celdas con historial.\n",
      fm(per, 3)]
(SAL / "control.md").write_text("\n".join(md) + "\n", encoding="utf-8")
log("reporte escrito")
print(auc_t.round(5).to_string()); print(dt.round(5).to_string()); print(per.round(3).to_string()); print("ARI", ari5)
