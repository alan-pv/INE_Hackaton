"""Prueba de la violencia homicida dentro del modelo (D-027).

Agrega la tasa municipal de homicidios como variable de la mezcla K=4 y aplica la regla fijada de antemano:
la violencia se queda en el modelo solo si mejora la captura del déficit de 2024 (IC95% de ΔAUC por encima de 0)
y la mezcla conserva su estabilidad y su prueba contra el azar. Si no, queda solo como descriptor.
Entradas: caché de seleccion_numero_perfiles (pca.pkl) y de referencia_cuatro_perfiles (ajuste_2009_2021_K4.pkl),
perfiles_k4.parquet, brecha_celda, panel_celda_eleccion, descriptores_seccion y violencia_mpio.
Salidas: data/processed/perfiles_k4_violencia.parquet, reports/perfiles/prueba_violencia/,
caché data/interim/prueba_violencia/.
Uso: .venv/bin/python scripts/perfiles/prueba_violencia.py"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"

import json
import pickle
import time
import types
from multiprocessing import get_context

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats

from ine_perfiles import brecha as B
from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import descriptores as D
from ine_perfiles import estabilidad as EST
from ine_perfiles import mezcla_mixta as MM
from ine_perfiles import seleccion as S

K = 4
LLAVE = CF.LLAVE
PROC = C.PROCESADOS
SAL = C.salidas(__file__)
INT_SEL = C.INTERIM / "seleccion_numero_perfiles"          # solo lectura
INT_REF = C.INTERIM / "referencia_cuatro_perfiles"         # solo lectura
INT = C.cache("prueba_violencia")
V23, V20 = C.COL_VIOLENCIA["v2023"], C.COL_VIOLENCIA["v2020"]
T0 = time.time()
TIEMPOS, QA = {}, []


def log(*a):
    print(f"[{time.time() - T0:7.0f}s]", *a, flush=True)


def chk(cond, texto):
    QA.append(f"- [{'OK' if cond else 'FALLA'}] {texto}")
    assert cond, texto


class Reloj:
    def __init__(self, nombre):
        self.n = nombre

    def __enter__(self):
        self.t = time.time()

    def __exit__(self, *e):
        # el tiempo de la corrida que calculó el resultado se conserva en la caché (las corridas posteriores lo leen)
        ruta = INT / "tiempos.json"
        prev = json.load(open(ruta)) if ruta.exists() else {}
        TIEMPOS[self.n] = max(time.time() - self.t, prev.get(self.n, 0))
        prev[self.n] = TIEMPOS[self.n]
        json.dump(prev, open(ruta, "w"), ensure_ascii=False)
        log(f"{self.n}: {time.time() - self.t:.0f}s (primera corrida: {TIEMPOS[self.n]:.0f}s)")


def cache_ajuste(nombre, dat_, k):
    ruta = INT / nombre
    if ruta.exists():
        with open(ruta, "rb") as fh:
            return pickle.load(fh)
    rng = np.random.default_rng([C.SEMILLA, 2, k])         # misma regla de semilla que seleccion.tarea_ajuste
    a, info = MM.ajustar_con_reinicios(dat_, k, rng, log=log)
    r = (a.modelo, a.logL, info)
    with open(ruta, "wb") as fh:
        pickle.dump(r, fh)
    return r


# ======================================================================== 1. datos y violencia estandarizada
S.INT = INT                                  # bootstrap y permutaciones de esta prueba van a su propia caché
with open(INT_SEL / "pca.pkl", "rb") as fh:
    P = pickle.load(fh)
desc = P["d"]
viol = pd.read_parquet(C.RAIZ / "data" / "interim" / "externos" / "violencia_mpio.parquet")
dat, x, et, nombres_cont, n_cero = S.construir(P)
n_obj = dat.n
chk(n_obj == 472539, f"celdas objetivo = {n_obj:,} (esperadas 472,539)")
chk(abs(dat.w.sum() - n_obj) < 1e-6 * n_obj, f"Σ pesos = {dat.w.sum():,.3f} = nº de celdas {n_obj:,}")
for c in LLAVE:
    x[c] = x[c].astype("int64")
wln = desc["ln_2024"].to_numpy(float)
v23s, v20s = CF.violencia_a_secciones(desc, viol, V23), CF.violencia_a_secciones(desc, viol, V20)
chk(int(np.isnan(v23s).sum()) == 195, f"secciones sin tasa v2023 = {int(np.isnan(v23s).sum())} (195 esperadas; merge m:1 por (edo, mpio))")
chk(len(P["d"]) == len(v23s) == 70751, "secciones = 70,751")
z23, mu23, sd23 = MM.estandarizar_ponderado(v23s[:, None], wln)      # igual que el contexto antes de la PCA (D-024)
z20, mu20, sd20 = MM.estandarizar_ponderado(v20s[:, None], wln)
z23, z20 = z23[:, 0], z20[:, 0]
okz = ~np.isnan(z23)
chk(abs(np.average(z23[okz], weights=wln[okz])) < 1e-9 and abs(np.sqrt(np.average(z23[okz] ** 2, weights=wln[okz])) - 1) < 1e-9,
    "z_violencia (v2023) tiene media 0 y sd 1 ponderadas por LN 2024")
zc = CF.a_celdas(x, desc, z23)
chk(int(np.isnan(zc).sum()) > 0 and np.isnan(zc).mean() < 0.01, f"celdas objetivo sin tasa (se marginan, D-024): {int(np.isnan(zc).sum()):,} ({100 * np.isnan(zc).mean():.2f}%)")
dat_v = MM.Datos(dat.cat, dat.ncat, np.column_stack([dat.X, zc]), dat.w)
nombres_v = nombres_cont + ["z_violencia"]
chk(dat_v.C == dat.C + 1 and np.allclose(dat_v.X[:, :dat.C], dat.X, equal_nan=True), f"variables continuas: {nombres_v}")

# correlaciones con los PC (sección, ponderada por LN 2024)
corr = []
for j in range(P["r"]):
    corr.append(dict(componente=f"pc{j + 1}", spearman_ponderada=B.spearman_ponderada(z23[okz], P["pcs"][okz, j], wln[okz]),
                     secciones=int(okz.sum())))
corr = pd.DataFrame(corr)
corr.to_csv(SAL / "correlacion_pc.csv", index=False, float_format="%.5f")
log("correlaciones con PC:", corr.spearman_ponderada.round(3).tolist())

# ======================================================================== 2. K=4 completo con violencia
with Reloj("ajuste K=4 y K=1"):
    mod4, ll4, info4 = cache_ajuste("ajuste_K4.pkl", dat_v, K)
    mod1, ll1, info1 = cache_ajuste("ajuste_K1.pkl", dat_v, 1)
R, ll = MM.estep(dat_v, mod4)
_, ll_1 = MM.estep(dat_v, mod1)
S.DAT = dat_v
f, comp, pos, mapa, pmax = S.perfiles(K, types.SimpleNamespace(R=R), x, et, P)
perfil = np.array([pos[int(k)] for k in mapa])
orden_clase = [k for k, _ in sorted(pos.items(), key=lambda kv: kv[1])]
Rp = R[:, orden_clase]
sal = x[LLAVE].copy()
sal["perfil"] = perfil.astype("int8")
sal["clase_map"] = mapa.astype("int8")
sal["prob_max"] = pmax
for j in range(K):
    sal[f"resp_perfil_{j + 1}"] = Rp[:, j]
sal["w"] = dat.w
sal.to_parquet(PROC / "perfiles_k4_violencia.parquet", index=False)
chk(np.allclose(Rp.sum(1), 1), "responsabilidades suman 1 por celda")

# estabilidad (B secuencial, D-017) y prueba contra el azar (B_NULO permutaciones)
orden, inicio, largo, edo_sec = EST.indice_secciones(x["edo"].to_numpy(), x["seccion"].to_numpy())
S.BOOT.update(edo_sec=edo_sec, orden=orden, inicio=inicio, largo=largo, idx=None)
ctx = get_context("fork")
pool = ctx.Pool(S.N_PROC)
with Reloj("estabilidad"):
    res_est, tope = S.estabilidad(K, mod4, R.argmax(axis=1), pool)
with Reloj("prueba contra el azar"):
    nulo = S.prueba_azar(K, pool)
pool.close(); pool.join()
J = np.array([q["jt"] for q in res_est])
ee = EST.ee_monte_carlo(J)
frio = [q for q in res_est if "jf" in q]
Jt, Jf = np.array([q["jt"] for q in frio]), np.array([q["jf"] for q in frio])
dif = Jt - Jf
eed = dif.std(axis=0, ddof=1) / np.sqrt(len(dif))
tc = stats.t.ppf(0.975, len(dif) - 1)
est = pd.DataFrame(dict(clase=np.arange(K), perfil=[pos[k] for k in range(K)], jaccard_medio=J.mean(axis=0), ee_mc=ee,
                        lectura_fpc=[EST.lectura_fpc(v) for v in J.mean(axis=0)], jaccard_frio_medio=Jf.mean(axis=0),
                        dif_tibio_menos_frio=dif.mean(axis=0), ee_dif=eed,
                        frio_domina=np.abs(dif.mean(axis=0)) > tc * eed)).sort_values("perfil")
est.to_csv(SAL / "jaccard_K4_violencia.csv", index=False)
G = np.array([q["G"] for q in nulo])
Gobs = ll - ll_1
n_ge = int((G >= Gobs).sum())
p_azar = (1 + n_ge) / (len(G) + 1)
azar = dict(Gobs=Gobs, min=G.min(), med=np.median(G), max=G.max(), n_ge=n_ge, p=p_azar, B=len(G), norep=sum(not q["rep"] for q in nulo))
pd.DataFrame([azar]).to_csv(SAL / "azar_K4_violencia.csv", index=False)

# ======================================================================== 3. perfiles con tasa de homicidio; ARI contra K=4 sin violencia
tasa_sec = CF.violencia_a_secciones(desc, viol, "tasa_contr_v2023")
tasa_c = CF.a_celdas(x, desc, tasa_sec)
sin = pd.read_parquet(PROC / "perfiles_k4.parquet")
mg = x[LLAVE].merge(sin, on=LLAVE, how="left", validate="1:1")
chk(len(mg) == n_obj and mg["perfil"].notna().all(), "perfiles_k4.parquet cuadra 1:1 con las celdas objetivo")
chk(np.allclose(mg["w"].to_numpy(), dat.w), "pesos w de perfiles_k4 = pesos de esta corrida")
perfil_sin = mg["perfil"].to_numpy(int)
Rp_sin = mg[[f"resp_perfil_{j + 1}" for j in range(K)]].to_numpy()
ari_w = CF.ari_ponderado(perfil_sin, perfil, dat.w)
ari_u = CF.ari_ponderado(perfil_sin, perfil)
cruce = pd.crosstab(perfil_sin, perfil, values=dat.w, aggfunc="sum", normalize="index").fillna(0) * 100
cruce.index.name = "perfil sin violencia"
cruce.to_csv(SAL / "cruce_perfiles.csv", float_format="%.3f")


def med_tasa(Rm):
    return [D.cuantil_ponderado(tasa_c, Rm[:, j] * dat.w, [0.5])[0] for j in range(K)]


tasa_con, tasa_sin = med_tasa(Rp), med_tasa(Rp_sin)
z_con = [D.cuantil_ponderado(zc, Rp[:, j] * dat.w, [0.5])[0] for j in range(K)]
f = f.sort_values("perfil").reset_index(drop=True)
f["mediana_tasa_homicidio_100mil"] = tasa_con
f["mediana_z_violencia"] = z_con
f.to_csv(SAL / "perfiles_K4_violencia.csv", index=False)
comp.to_csv(SAL / "composicion_K4_violencia.csv", index=False)
pct_sin = [100 * (Rp_sin[:, j] * dat.w).sum() / dat.w.sum() for j in range(K)]
t_sin = pd.DataFrame(dict(perfil=np.arange(1, K + 1), pct_deficit_sin_violencia=pct_sin, mediana_tasa_homicidio_100mil=tasa_sin))

# ======================================================================== 4. universo, mezcla 2009-21 y r̂ de cada método
with Reloj("universo 2009-21"):
    U0 = CF.cargar_universo(PROC)
cel, h_ok, obj0, m4 = U0["cel"], U0["h_ok"], U0["obj0"], U0["m4"]
b = U0["b"]
chk(obj0.sum() == b["objetivo_0921"].fillna(False).astype(bool).sum(), f"población objetivo 2009-21 = {obj0.sum():,} celdas")
o0 = cel[obj0].reset_index(drop=True)
dat0, x0, n_cero0 = CF.construir_datos(o0, desc, P["pcs"], P["r"], "delta_0921", "deficit_0921")
chk(abs(dat0.w.sum() - dat0.n) < 1e-6 * dat0.n, f"mezcla 2009-21: Σ pesos = {dat0.w.sum():,.1f} = nº de celdas {dat0.n:,}")
for c in LLAVE:
    x0[c] = x0[c].astype("int64")
z0 = CF.a_celdas(x0, desc, z20)
dat0v = MM.Datos(dat0.cat, dat0.ncat, np.column_stack([dat0.X, z0]), dat0.w)
with Reloj("ajuste 2009-21 con violencia"):
    mod0v, ll0v, info0v = cache_ajuste("ajuste_2009_2021_K4.pkl", dat0v, K)
with open(INT_REF / "ajuste_2009_2021_K4.pkl", "rb") as fh:          # mezcla 2009-21 sin violencia (referencia_cuatro_perfiles), solo lectura
    mod0s, ll0s, info0s = pickle.load(fh)
map0v = MM.estep(dat0v, mod0v)[0].argmax(1)
map0s = MM.estep(dat0, mod0s)[0].argmax(1)


def reetiq(map0, ref):
    """Reetiqueta contra el K=4 del periodo completo (D-021) y devuelve perfil 2009-21 en 1..K."""
    xp = x0[LLAVE].merge(ref[LLAVE + ["perfil", "w"]], on=LLAVE, how="left", validate="1:1")
    comun = xp["perfil"].notna().to_numpy()
    mapa_h, cr = CF.reetiquetar(xp.perfil[comun].to_numpy(int) - 1, map0[comun], xp.w[comun].to_numpy(), K)
    p0 = mapa_h[map0] + 1
    return p0, CF.ari_ponderado(xp.perfil[comun].to_numpy(int), p0[comun], xp.w[comun].to_numpy()), int(comun.sum()), cr


perfil0v, ari0v, ncom_v, cr_v = reetiq(map0v, sal)
perfil0s, ari0s, ncom_s, cr_s = reetiq(map0s, sin)
cruce0v = pd.DataFrame({f"perfil_completo_{j + 1}": [cr_v[k, j] / cr_v[:, j].sum() * 100 for k in range(K)] for j in range(K)})
cruce0v.index = [f"clase 2009-21 → perfil {i + 1}" for i in range(K)]

# r̂ de cada método sobre el universo `cel` (misma construcción que referencia_cuatro_perfiles)
r_a = (cel["p_tilde_0921"].astype(float) / (cel["E_0921"] / cel["N_0921"])).to_numpy()
post_a = np.isnan(r_a)
r_a = np.where(post_a, 1.0, r_a)
r_ms, post_ms, rp_s, rn_s = CF.rhat_mezcla(cel, h_ok, obj0, o0, perfil0s, K)
r_mv, post_mv, rp_v, rn_v = CF.rhat_mezcla(cel, h_ok, obj0, o0, perfil0v, K)
M = {"historial propio": (r_a, post_a), "mezcla sin violencia": (r_ms, post_ms), "mezcla con violencia": (r_mv, post_mv)}

U = {"solo celdas con historial 2009-21": m4 & h_ok, "todas las celdas con 2024": m4}
ln24 = cel["ln_2024"].to_numpy(float)
d24 = cel["deficit_2024_crudo"].to_numpy(float)
ref_k4 = pd.read_csv(C.salidas("perfiles/referencia_cuatro_perfiles") / "captura_resumen.csv")
auc_rows = []
for un, mk in U.items():
    for nom, (r, post) in M.items():
        a_ = CF.curva_captura(r[mk], ln24[mk], d24[mk], None if post is None else post[mk])[1]
        auc_rows.append(dict(universo=un, metodo=nom, AUC_pos=a_, celdas=int(mk.sum())))
auc_t = pd.DataFrame(auc_rows)
auc_t.to_csv(SAL / "auc.csv", index=False, float_format="%.5f")
g = lambda un, nom: float(auc_t[(auc_t.universo == un) & (auc_t.metodo == nom)].AUC_pos.iloc[0])
for un in U:
    for nom_ref, nom in (("mezcla K=4 (2009-21)", "mezcla sin violencia"), ("historial propio", "historial propio")):
        ref = float(ref_k4[(ref_k4.universo == un) & (ref_k4.metodo == nom_ref)].AUC_pos.iloc[0])
        chk(abs(g(un, nom) - ref) < 5e-6, f"{un}: AUC_pos {nom} = {g(un, nom):.5f} reproduce referencia_cuatro_perfiles ({ref:.5f})")
chk(abs(g("solo celdas con historial 2009-21", "mezcla sin violencia") - 0.730) < 5e-4, "AUC con historial de la mezcla K=4 sin violencia = 0.730")

# ======================================================================== 5. ΔAUC con bootstrap pareado (D-027)
comparaciones = [
    ("(i) mezcla con − mezcla sin", "mezcla con violencia", "mezcla sin violencia"),
    ("(ii) historial propio − mezcla sin", "historial propio", "mezcla sin violencia"),
    ("(ii) historial propio − mezcla con", "historial propio", "mezcla con violencia"),
]


def tarea_delta(un, nombre, n1, n2):
    ruta = INT / ("dauc_%s_%s.pkl" % (list(U).index(un), comparaciones.index((nombre, n1, n2))))
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


with Reloj(f"bootstrap ΔAUC (B={C.B_PERMANENCIA}, {len(comparaciones) * len(U)} comparaciones)"):
    jobs = [(un, *c) for un in U for c in comparaciones]
    salidas = Parallel(n_jobs=S.N_PROC)(delayed(tarea_delta)(*j) for j in jobs)
dt = []
for (un, nombre, n1, n2), o in zip(jobs, salidas):
    dt.append(dict(universo=un, comparacion=nombre, AUC_1=o["auc1"], AUC_2=o["auc2"], delta_AUC=o["delta"], IC95_inf=o["lo"], IC95_sup=o["hi"],
                   excluye_0=bool(o["lo"] > 0 or o["hi"] < 0), B=o["B"], seg=o["seg"], media_replicas=o["deltas"].mean()))
    chk(abs(o["auc1"] - g(un, n1)) < 1e-9 and abs(o["auc2"] - g(un, n2)) < 1e-9, f"{un} · {nombre}: AUC observado = AUC de la tabla de capturas")
dt = pd.DataFrame(dt)
dt.to_csv(SAL / "delta_auc.csv", index=False, float_format="%.5f")

# veredicto con la regla fijada de antemano (D-027)
UV = "solo celdas con historial 2009-21"
fila = lambda pref: dt[(dt.universo == UV) & dt.comparacion.str.startswith(pref)].iloc[0]
muy_estable = bool((est.jaccard_medio >= 0.85).all())
sin_frio = bool(~est.frio_domina.any())
p_ok = bool(abs(p_azar - 1 / (C.B_NULO + 1)) < 1e-12)
cond_mezcla = muy_estable and sin_frio and p_ok
fr = fila("(i)")
c1 = bool(fr.IC95_inf > 0)
ver = pd.DataFrame([dict(modelo="mezcla K=4", delta_AUC=fr.delta_AUC, IC95_inf=fr.IC95_inf, IC95_sup=fr.IC95_sup,
                         IC_por_encima_de_0=c1, estabilidad_fpc_y_p="sí" if cond_mezcla else "no",
                         veredicto="se queda" if (c1 and cond_mezcla) else "queda como descriptor")])
ver.to_csv(SAL / "veredicto.csv", index=False, float_format="%.5f")

# figura: bosque de ΔAUC y tasa de homicidio por perfil
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
dd = dt[dt.universo == UV].reset_index(drop=True)
yy = np.arange(len(dd))[::-1]
ax[0].errorbar(dd.delta_AUC, yy, xerr=[dd.delta_AUC - dd.IC95_inf, dd.IC95_sup - dd.delta_AUC], fmt="o", capsize=3)
ax[0].axvline(0, c="k", lw=.8); ax[0].set_yticks(yy); ax[0].set_yticklabels(dd.comparacion, fontsize=7)
ax[0].set_xlabel("ΔAUC_pos (IC percentil 95%, B=1999, universo con historial)"); ax[0].set_title("Regla de permanencia (D-027)")
w_ = 0.38
ax[1].bar(np.arange(1, K + 1) - w_ / 2, tasa_sin, w_, label="K=4 sin violencia"); ax[1].bar(np.arange(1, K + 1) + w_ / 2, tasa_con, w_, label="K=4 con violencia")
ax[1].set_xlabel("perfil (orden por % del déficit)"); ax[1].set_ylabel("mediana de la tasa de homicidio por 100 mil / año"); ax[1].legend()
ax[1].set_title("Violencia municipal por perfil (descriptivo)")
fig.tight_layout(); fig.savefig(SAL / "permanencia.png", dpi=110); plt.close(fig)

# ======================================================================== 6. reporte
md_t = lambda df, d=3: S.md_tabla(df.round(d).astype(object).rename(columns=str))
cols = ["perfil", "pct_deficit", "celdas", "ln_2024_miles", "delta_medio", "pct_crudo_2024", "pmax_media", "pct_pmax_ge_09", "med_graproes",
        "med_prop_internet", "med_im_2020", "med_pctl_mov_estado", "mediana_tasa_homicidio_100mil", "mediana_z_violencia"]
tot = time.time() - T0
cpu_bt = sum(q["seg_t"] + q.get("seg_f", 0) for q in res_est)
md = ["# Prueba de la violencia homicida dentro del modelo (D-027)\n",
      "La violencia es una continua aparte (`z_violencia`, log de la tasa municipal contraída estandarizado a nivel sección con pesos LN 2024), "
      "fuera de la PCA (D-027). Asociación, no causa (D-010, D-027). El contexto describe secciones, no personas.\n",
      "## 0. Cifras de control\n", *QA, "",
      f"- logL K=4 con violencia {ll:,.1f}; K=1 {ll_1:,.1f}; reinicios {info4['reinicios']}, óptimo repetido {info4['repetido']} ({info4['repeticiones']} veces), "
      f"no convergieron {info4['no_convergio']}, pisos {info4['pisos']}. Mezcla 2009-21 con violencia: logL {ll0v:,.1f}, reinicios {info0v['reinicios']}, repetido {info0v['repetido']}, pisos {info0v['pisos']}.",
      "- Tiempos (s) de la corrida que calculó cada etapa (las siguientes leen la caché): " + ", ".join(f"{k} {v:.0f}" for k, v in TIEMPOS.items()) + f"; total {tot:.0f}. CPU del bootstrap de estabilidad: {cpu_bt / 3600:.2f} h-CPU.\n",
      "## 1. Correlación de la violencia con los componentes principales\n",
      f"Spearman ponderada por LN 2024, a nivel sección, en las {int(okz.sum()):,} secciones con tasa (z_violencia v2023 contra pc1–pc{P['r']}):\n", md_t(corr, 4),
      "\n## 2. Estabilidad y prueba contra el azar de K=4 con violencia\n",
      f"- Bootstrap de secciones estratificado por estado: B = {len(res_est)} réplicas (mín. {S.B_MIN}, EE ≤ {S.EE_MAX}, tope {S.B_TOPE}; tope alcanzado: {'sí' if tope else 'no'}); control en frío: {len(frio)} réplicas, t crítico {tc:.2f}.\n",
      md_t(est[["perfil", "clase", "jaccard_medio", "ee_mc", "lectura_fpc", "jaccard_frio_medio", "dif_tibio_menos_frio", "ee_dif", "frio_domina"]], 4),
      f"\n- Prueba contra el azar (cada variable continua, incluida la violencia, y categórica permutada por separado): G_obs = {Gobs:,.1f} nats; "
      f"G_nulo (B = {len(G)}): mín {G.min():,.1f}, mediana {np.median(G):,.1f}, máx {G.max():,.1f}; permutaciones con G ≥ G_obs: {n_ge}; **p = {p_azar:.3f}** "
      f"(mínimo posible {1 / (len(G) + 1):.3f}); ajustes nulos cuyo óptimo no se repitió: {azar['norep']}.\n",
      "## 3. Perfiles K=4 con violencia (orden por % del déficit)\n",
      "Tasa de homicidio = tasa municipal contraída 2009–2023 por 100 mil habitantes por año (`tasa_contr_v2023`); mediana ponderada por responsabilidad × w, "
      "calculada a nivel celda sobre las celdas con tasa. `mediana_z_violencia` = mediana de `z_violencia`.\n",
      md_t(f[cols], 3),
      "\nK=4 sin violencia (referencia_cuatro_perfiles), la misma mediana de tasa de homicidio para comparar (numeración propia de ese ajuste):\n", md_t(t_sin, 3),
      "\n### Rasgos sobrerrepresentados con violencia (razón ≥ 1.25 o ≥ 40%; filtro solo de presentación)\n"]
for p in range(1, K + 1):
    s_ = comp[(comp.perfil == p) & ((comp.razon >= 1.25) | (comp.pct >= 40))]
    md += [f"#### Perfil {p}\n", md_t(s_[["variable", "categoria", "pct", "razon"]], 2), ""]
md += ["## 4. ARI contra el K=4 sin violencia\n",
       f"{n_obj:,} celdas objetivo: **ARI ponderado (w) = {ari_w:.4f}**; sin ponderar {ari_u:.4f}. Cruce (fila = perfil sin violencia; % del peso w que cae en cada perfil con violencia):\n",
       md_t(cruce.rename(columns=lambda c: f"con_perfil_{c}").reset_index(), 1),
       "\n## 5. Mezcla 2009–21 con violencia (v2020, estandarizada con sus propios parámetros)\n",
       f"- Población objetivo_0921 {dat0.n:,} celdas (w=0: {n_cero0}); z_violencia v2020: media ponderada {mu20[0]:.4f}, sd {sd20[0]:.4f} (v2023: {mu23[0]:.4f}, {sd23[0]:.4f}).",
       f"- Reetiquetado Hungarian contra el K=4 del periodo completo **con violencia** en {ncom_v:,} celdas comunes; ARI ponderado {ari0v:.3f} (sin violencia contra su K=4: {ari0s:.3f}, {ncom_s:,} celdas).",
       f"- Razones ΣO/ΣE por perfil 2009-21 con violencia: {np.round(rp_v, 4).tolist()} (no objetivo con historial {rn_v:.4f}); sin violencia: {np.round(rp_s, 4).tolist()} ({rn_s:.4f}).\n",
       md_t(cruce0v.reset_index().rename(columns={"index": "clase 2009-21"}), 1),
       "\n## 6. Regla de permanencia (D-027)\n",
       f"AUC_pos de la curva de captura fuera de tiempo (D-025). ΔAUC = AUC(1) − AUC(2). Bootstrap pareado que remuestrea **secciones** con reemplazo, estratificado por estado "
       f"(D-017), B = {C.B_PERMANENCIA}, semilla [C.SEMILLA, {C.SUFIJO_SEMILLA_PERMANENCIA}], ambas curvas recalculadas en cada réplica; intervalo percentil 95% = "
       f"estadísticos de orden {int((C.B_PERMANENCIA + 1) * 0.025)} y {C.B_PERMANENCIA + 1 - int((C.B_PERMANENCIA + 1) * 0.025)} de {C.B_PERMANENCIA} "
       "(Davison y Hinkley, 1997). **Mide la variabilidad del conjunto de evaluación (qué secciones se evalúan), no la del ajuste de los modelos.** "
       "### AUC_pos por método\n", md_t(auc_t, 5),
       "\n### ΔAUC_pos con IC95%\n", md_t(dt[["universo", "comparacion", "AUC_1", "AUC_2", "delta_AUC", "IC95_inf", "IC95_sup", "excluye_0", "B", "seg"]], 5),
       "\n### Veredicto mecánico (universo con historial)\n",
       "Se queda = el IC95% de ΔAUC está por encima de 0 **y** K=4 con violencia mantiene estabilidad y p. Operacionalización de la segunda: "
       "Jaccard medio ≥ 0.85 (lectura `fpc` \"muy estable\", D-011) en las 4 clases, ninguna clase regida por el frío y p = "
       f"{1 / (C.B_NULO + 1):.2f} (0 de {C.B_NULO} permutaciones con G ≥ G_obs). Resultado de esa segunda condición: muy estable en todas = {muy_estable}; sin clase regida por el frío = {sin_frio}; p mínimo = {p_ok}.\n",
       md_t(ver, 5),
       f"\nFigura: `permanencia.png`. Salida por celda: `data/processed/perfiles_k4_violencia.parquet`."]
(SAL / "control.md").write_text("\n".join(md) + "\n", encoding="utf-8")
log(f"reporte escrito; total {tot:.0f}s")
