"""Perfiles finales: evaluación de la mezcla con cinco perfiles y regla de entrega (D-029).

Toma el ajuste K=5 de la selección del número de perfiles, mide su estabilidad (D-017) y su prueba contra el
azar, aplica la regla de perfiles claros fijada de antemano (D-029) y describe los cinco perfiles.
Entradas: caché de seleccion_numero_perfiles (pca.pkl, ajuste_K5.pkl, ajuste_K1.pkl), perfiles_k4.parquet,
brecha_celda y violencia_mpio.
Salidas: data/processed/perfiles_finales.parquet, reports/perfiles/perfiles_finales/,
caché data/interim/perfiles_finales/ (borrarla para rehacer el bootstrap y las permutaciones).
Uso: .venv/bin/python scripts/perfiles/perfiles_finales.py"""
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
from scipy import stats

from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import descriptores as D
from ine_perfiles import estabilidad as EST
from ine_perfiles import mezcla_mixta as MM
from ine_perfiles import seleccion as S

K = C.K_EVALUADO_K5                                    # D-029
N_PROC_K5 = 2                                          # procesos en paralelo (no cambia ningún resultado)
LLAVE = CF.LLAVE
PROC = C.PROCESADOS
SAL = C.salidas(__file__)
INT_SEL = C.INTERIM / "seleccion_numero_perfiles"      # solo lectura
INT = C.cache("perfiles_finales")
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
        ruta = INT / "tiempos.json"                     # el tiempo de la corrida que calculó se conserva
        prev = json.load(open(ruta)) if ruta.exists() else {}
        TIEMPOS[self.n] = max(time.time() - self.t, prev.get(self.n, 0))
        prev[self.n] = TIEMPOS[self.n]
        json.dump(prev, open(ruta, "w"), ensure_ascii=False)
        log(f"{self.n}: {time.time() - self.t:.0f}s (primera corrida: {TIEMPOS[self.n]:.0f}s)")


# ======================================================================== 1. ajuste K=5 y responsabilidades
S.INT = INT                              # bootstrap y permutaciones de K=5 van a su propia caché
S.N_PROC = N_PROC_K5
with open(INT_SEL / "pca.pkl", "rb") as fh:
    P = pickle.load(fh)
dat, x, et, nombres_cont, n_cero = S.construir(P)
S.DAT = dat
n_obj = dat.n
chk(n_obj == 472539, f"celdas objetivo = {n_obj:,} (esperadas 472,539)")
chk(abs(dat.w.sum() - n_obj) < 1e-6 * n_obj, f"Σ pesos = {dat.w.sum():,.3f} = nº de celdas {n_obj:,}")
with open(INT_SEL / f"ajuste_K{K}.pkl", "rb") as fh:
    modelo = pickle.load(fh)[0]
R, ll = MM.estep(dat, modelo)
ll_ref = float(pd.read_csv(C.salidas("perfiles/seleccion_numero_perfiles") / "seleccion_K.csv").set_index("K").loc[K, "logL"])
chk(abs(ll - ll_ref) < 0.1, f"logL recalculada K=5 = {ll:,.1f} coincide con la selección del número de perfiles ({ll_ref:,.1f})")
chk(np.allclose(R.sum(1), 1), "responsabilidades suman 1 por celda")
a5 = MM.Ajuste(modelo, ll, R, 0, True, 0.0)
f, comp, pos, mapa, pmax = S.perfiles(K, types.SimpleNamespace(R=R), x, et, P)
perfil = np.array([pos[int(k)] for k in mapa])
orden_clase = [k for k, _ in sorted(pos.items(), key=lambda kv: kv[1])]
Rp = R[:, orden_clase]                           # columna j = perfil j+1
x = x.copy()
for c in LLAVE:
    x[c] = x[c].astype("int64")
sal = x[LLAVE].copy()
sal["perfil"] = perfil.astype("int8")
sal["clase_map"] = mapa.astype("int8")
sal["prob_max"] = pmax
for j in range(K):
    sal[f"resp_perfil_{j + 1}"] = Rp[:, j]
sal["w"] = dat.w
chk(len(sal) == n_obj and sorted(np.unique(perfil)) == list(range(1, K + 1)), "una fila por celda objetivo, 5 perfiles")

# ======================================================================== 2. estabilidad (D-017) y prueba contra el azar (D-029)
orden, inicio, largo, edo_sec = EST.indice_secciones(x["edo"].to_numpy(), x["seccion"].to_numpy())
S.BOOT.update(edo_sec=edo_sec, orden=orden, inicio=inicio, largo=largo, idx=None)
ll1_ruta = INT / "ajuste_K1.pkl"
pool = get_context("fork").Pool(N_PROC_K5)
with Reloj("estabilidad K=5"):
    res_est, tope = S.estabilidad(K, modelo, R.argmax(axis=1), pool)
with Reloj("prueba contra el azar K=5"):
    nulo = S.prueba_azar(K, pool)
pool.close(); pool.join()

# logL_1 observada: igual que en la selección del número de perfiles (ajuste K=1 de la caché original, E-step sobre los datos)
with open(INT_SEL / "ajuste_K1.pkl", "rb") as fh:
    mod1 = pickle.load(fh)[0]
_, ll1 = MM.estep(dat, mod1)
Gobs = ll - ll1
Gn = np.array([q["G"] for q in nulo])
n_ge = int((Gn >= Gobs).sum())
p_val = (1 + n_ge) / (len(Gn) + 1)
J = np.array([q["jt"] for q in res_est]); ee = EST.ee_monte_carlo(J)
frio = [q for q in res_est if "jf" in q]
Jt, Jf = np.array([q["jt"] for q in frio]), np.array([q["jf"] for q in frio])
dif = Jt - Jf
eed = dif.std(axis=0, ddof=1) / np.sqrt(len(dif))
tc = stats.t.ppf(0.975, len(dif) - 1)
tj = pd.DataFrame(dict(clase=np.arange(K), perfil=[pos[k] for k in range(K)], jaccard_medio=J.mean(axis=0), ee_mc=ee,
                       lectura_fpc=[EST.lectura_fpc(v) for v in J.mean(axis=0)], jaccard_frio_medio=Jf.mean(axis=0),
                       dif_tibio_menos_frio=dif.mean(axis=0), ee_dif=eed,
                       frio_domina=np.abs(dif.mean(axis=0)) > tc * eed)).sort_values("perfil").reset_index(drop=True)
tj["permutaciones_G_ge_Gobs"] = n_ge
tj["clara"] = [CF.es_clara(r.jaccard_medio, r.frio_domina, n_ge, jaccard_frio=r.jaccard_frio_medio) for r in tj.itertuples()]
tj.to_csv(SAL / "jaccard_K5.csv", index=False)
azar = dict(K=K, logL_5=ll, logL_1=ll1, Gobs=Gobs, min=Gn.min(), med=np.median(Gn), max=Gn.max(), n_ge=n_ge, B=len(Gn), p=p_val,
            norep=sum(not q["rep"] for q in nulo), seg=np.mean([q["seg"] for q in nulo]))
pd.DataFrame([azar]).to_csv(SAL / "azar.csv", index=False)
claras = [int(p) for p in tj.loc[tj["clara"], "perfil"]]
entrega_ok = CF.veredicto_k5(n_ge, len(claras))
log(f"veredicto: n_ge={n_ge} p={p_val:.3f} claras={claras} K=5 es la entrega: {entrega_ok}")

# ======================================================================== 3. descripción de los 5 perfiles
viol = pd.read_parquet(C.RAIZ / "data" / "interim" / "externos" / "violencia_mpio.parquet")
tasa_c = CF.a_celdas(x, P["d"], CF.violencia_a_secciones(P["d"], viol, "tasa_contr_v2023"))
f["mediana_tasa_homicidio_100mil"] = [D.cuantil_ponderado(tasa_c, Rp[:, j] * dat.w, [0.5])[0] for j in range(K)]
b = pd.read_parquet(PROC / "brecha_celda.parquet", columns=LLAVE + ["objetivo_0921", "objetivo_24", "n_2024", "E_24", "E_0921"])
for c in LLAVE:
    b[c] = b[c].astype("int64")
pb = x[LLAVE].merge(b, on=LLAVE, how="left", validate="1:1")
chk(len(pb) == n_obj and pb["E_24"].notna().sum() > 0, "persistencia: celdas objetivo encontradas 1:1 en brecha_celda")
obj0 = pb["objetivo_0921"].fillna(False).astype(bool).to_numpy()
obj24 = pb["objetivo_24"].fillna(False).astype(bool).to_numpy()
n24 = np.nan_to_num(pb["n_2024"].to_numpy(float))  # celdas sin 2024 pesan 0
m4 = np.nan_to_num(pb["E_24"].to_numpy(float)) > 0
ok_b = np.nan_to_num(b["E_24"].to_numpy(float)) > 0
b0 = b["objetivo_0921"].fillna(False).astype(bool).to_numpy()
b24 = b["objetivo_24"].fillna(False).astype(bool).to_numpy()
nb = np.nan_to_num(b["n_2024"].to_numpy(float))
hist = b["E_0921"].notna().to_numpy()


def fila_persist(nombre, sel):
    s = sel & obj0 & m4
    return dict(grupo=nombre, celdas_objetivo_0921=int(s.sum()),
                pct_sigue_objetivo_24_pond_n2024=100 * np.average(obj24[s], weights=n24[s]) if s.any() else np.nan,
                pct_sigue_objetivo_24_celdas=100 * obj24[s].mean() if s.any() else np.nan)


def fila_base(nombre, sel):
    s = sel & ok_b
    return dict(grupo=nombre, celdas_objetivo_0921=int(s.sum()),
                pct_sigue_objetivo_24_pond_n2024=100 * np.average(b24[s], weights=nb[s]),
                pct_sigue_objetivo_24_celdas=100 * b24[s].mean())


pers = pd.DataFrame([fila_persist(f"perfil {j}", perfil == j) for j in range(1, K + 1)]
                    + [fila_persist("los 5 perfiles", np.ones(n_obj, bool)),
                       fila_base("base: todas las celdas objetivo_0921 (universo E_24>0)", b0),
                       fila_base("base: todas las celdas con historial 2009-21 (% que son objetivo_24)", hist)])
pers.to_csv(SAL / "persistencia.csv", index=False, float_format="%.4f")
ln = np.nan_to_num(x["ln_2024"].to_numpy(float))
f["celdas_duras"] = [int((perfil == j).sum()) for j in f["perfil"]]
f["ln_2024_miles_duro"] = [ln[perfil == j].sum() / 1e3 for j in f["perfil"]]
f.to_csv(SAL / "perfiles_K5.csv", index=False)
comp.to_csv(SAL / "composicion_K5.csv", index=False)

# ======================================================================== 4. cruces
sal4 = pd.read_parquet(PROC / "perfiles_k4.parquet")
chk(len(sal4) == n_obj and (sal4[LLAVE].to_numpy() == sal[LLAVE].to_numpy()).all(), "perfiles_k4.parquet alineado fila a fila con K=5")
p4 = sal4["perfil"].to_numpy(int)


def cruce(a_lab, b_lab, w):
    t = pd.crosstab(a_lab, b_lab, values=w, aggfunc="sum", normalize="index").fillna(0) * 100
    return t


c4 = cruce(p4, perfil, dat.w)
c4.index.name = "perfil_K4"
c4.columns = [f"K5_perfil_{c}" for c in c4.columns]
c4.to_csv(SAL / "cruce_K4_K5.csv", float_format="%.3f")
c4_inv = cruce(perfil, p4, dat.w)
ari4 = dict(ARI_ponderado_w=CF.ari_ponderado(p4, perfil, dat.w), ARI_sin_ponderar=CF.ari_ponderado(p4, perfil))

# ======================================================================== 5. entrega (D-029)
chk(entrega_ok, f"regla de D-029: K=5 es la entrega (p = {p_val:.3f}, {len(claras)} perfiles claros)")
etq = CF.etiquetas_entrega_k5(perfil, claras)
ent = sal.copy()
ent.insert(len(LLAVE) + 1, "perfil_entrega", etq)
ent.to_parquet(PROC / "perfiles_finales.parquet", index=False)
dlt = x["delta"].to_numpy(float)
filas = []
for e in pd.unique(etq):
    s = etq == e
    filas.append(dict(perfil_entrega=e, perfiles_K5=",".join(str(p) for p in sorted(set(perfil[s]))), celdas=int(s.sum()),
                      pct_deficit=100 * dat.w[s].sum() / dat.w.sum(), ln_2024_miles=ln[s].sum() / 1e3,
                      pct_ln_objetivo=100 * ln[s].sum() / ln.sum(), delta_medio=np.average(dlt[s], weights=dat.w[s])))
te = pd.DataFrame(filas).sort_values("pct_deficit", ascending=False).reset_index(drop=True)
te.to_csv(SAL / "entrega_K5.csv", index=False, float_format="%.5g")
chk(te["celdas"].sum() == n_obj, f"entrega: Σ celdas = {te['celdas'].sum():,} = total ({n_obj:,})")
chk(abs(te["pct_deficit"].sum() - 100) < 1e-9, f"entrega: Σ % del déficit = {te['pct_deficit'].sum():.6f}")
chk(abs(te["ln_2024_miles"].sum() - ln.sum() / 1e3) < 1e-6 * ln.sum() / 1e3, f"entrega: Σ LN 2024 = {te['ln_2024_miles'].sum():,.0f} miles = total")

# ======================================================================== 6. figura
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(tj["perfil"], tj["jaccard_medio"], "o-", label="tibio"); ax[0].plot(tj["perfil"], tj["jaccard_frio_medio"], "s--", label="frío")
ax[0].axhline(C.JACCARD_CLARO, color="gray", ls=":"); ax[0].set_xlabel("perfil (orden por % del déficit)"); ax[0].set_ylabel("Jaccard medio")
ax[0].set_xticks(range(1, K + 1)); ax[0].legend(); ax[0].set_title("Estabilidad K=5")
ax[1].hist(Gn, bins=8, alpha=.6, label="nulo"); ax[1].axvline(Gobs, color="C3", lw=2, label="observado")
ax[1].set_xlabel("G = logL_5 − logL_1"); ax[1].set_title("Contra el azar"); ax[1].legend()
fig.tight_layout(); fig.savefig(SAL / "resumen.png", dpi=110); plt.close(fig)

# ======================================================================== 7. reporte
md_t = lambda df, d=3: S.md_tabla(df.round(d).astype(object))
L = []
A = L.append
A("# Perfiles finales: cinco perfiles y regla de entrega (D-029)\n")
A("Descriptivo. Los perfiles representan **votos faltantes** (pesos w = déficit), no personas; el contexto describe la sección, no a las personas (D-010).\n")
A("**Nota de lectura (D-026):** `im_2020` alto = **menos** marginación; `iim_dp2` alto = **menos** intensidad migratoria; "
  "`pctl_mov_estado` alto = llegada neta de registros a la sección (bajo = salida neta), percentil dentro del estado (D-016).\n")
A("## 0. Cifras de control\n"); L.extend(QA)
A(f"\n- logL K=5 = {ll:,.1f}; logL K=1 = {ll1:,.1f}; celdas con w=0: {n_cero}; variables continuas: {nombres_cont}.")
A(f"- **Elección de cómputo:** {N_PROC_K5} procesos en vez de 4 (máquina compartida). No cambia ningún resultado (semillas por réplica, no por proceso).")
A("- Tiempos (s, primera corrida): " + ", ".join(f"{k} {v:.0f}" for k, v in TIEMPOS.items()) + f"; esta ejecución {time.time() - T0:.0f} s.\n")
A("## 1. Estabilidad (bootstrap de secciones por estado, B secuencial D-017, control en frío)\n")
A(f"- B = {len(res_est)} réplicas (mín {S.B_MIN}, EE ≤ {S.EE_MAX}, tope {S.B_TOPE}); tope alcanzado: {'sí' if tope else 'no'}. Control en frío: {len(frio)} réplicas; "
  f"t crítico {tc:.2f}; dif. media logL tibio − frío = {np.mean([q['logL_t'] - q['logL_f'] for q in frio]):.2f} nats; réplicas tibias sin convergir: {sum(not q['conv_t'] for q in res_est)}.\n")
tt = tj[["perfil", "clase", "jaccard_medio", "ee_mc", "lectura_fpc", "jaccard_frio_medio", "dif_tibio_menos_frio", "ee_dif", "frio_domina", "clara"]].copy()
tt["frio_domina"] = tt["frio_domina"].map({True: "sí", False: "no"}); tt["clara"] = tt["clara"].map({True: "SÍ", False: "no"})
A(S.md_tabla(tt.astype(object), {"jaccard_medio": "{:.3f}", "ee_mc": "{:.4f}", "jaccard_frio_medio": "{:.3f}", "dif_tibio_menos_frio": "{:+.4f}", "ee_dif": "{:.4f}"}))
A("\n## 2. Prueba contra el azar (permutación de cada variable por separado, w con su celda)\n")
A(f"- G_obs = logL_5 − logL_1 = {Gobs:.1f} nats; G_nulo (B = {azar['B']}): mín {azar['min']:.1f}, mediana {azar['med']:.1f}, máx {azar['max']:.1f}; "
  f"permutaciones con G ≥ G_obs: **{n_ge}/{azar['B']}**; **p = {p_val:.3f}** (mínimo posible {1 / (C.B_NULO + 1):.3f}); ajustes nulos sin óptimo repetido: {azar['norep']}; {azar['seg']:.0f} s por permutación.\n")
A("## 3. Regla fijada de antemano (D-029) y veredicto\n")
A(f"Una clase es **clara** si cumple las dos: (i) Jaccard principal ≥ {C.JACCARD_CLARO} (el tibio, o el frío si la clase está regida por el frío, D-017); "
  f"(ii) la solución tiene {C.N_GE_NULO_CLARO}/{C.B_NULO} permutaciones con G ≥ G_obs (p = {1 / (C.B_NULO + 1):.2f}). "
  f"**K=5 es la entrega** si p = {1 / (C.B_NULO + 1):.2f} y hay ≥ {C.N_CLARAS_MIN_K5} clases claras; si no, **K=5 no cumple**. "
  "Si las 5 son claras se entregan las 5; las no claras van al 'resto'.\n")
A(f"- Clases claras: **{len(claras)}** (perfiles {claras}). p = {p_val:.3f}.")
A(f"- **Veredicto: {'K=5 es la entrega' if entrega_ok else 'K=5 no cumple'}.**\n")
A("## 4. Descripción de los 5 perfiles (ordenados por % del déficit)\n")
A("Porcentajes con responsabilidad × w. Celdas y LN de la asignación dura en las columnas marcadas. Medianas ponderadas por responsabilidad × w; "
  "la tasa de homicidio (v2023, D-027) es solo descriptor, por municipio.\n")
tp = f[["perfil", "pct_deficit", "celdas_duras", "ln_2024_miles_duro", "delta_medio", "pmax_media", "pct_pmax_ge_09", "mediana_tasa_homicidio_100mil"]]
A(S.md_tabla(tp.astype(object), {"pct_deficit": "{:.1f}", "celdas_duras": "{:,}", "ln_2024_miles_duro": "{:,.0f}", "delta_medio": "{:.3f}",
                                 "pmax_media": "{:.3f}", "pct_pmax_ge_09": "{:.1f}", "mediana_tasa_homicidio_100mil": "{:.1f}"}))
A("\nComposición (% del déficit del perfil, razón × frente a la población objetivo):\n")
for c in S.CATS:
    cc = comp[comp["variable"] == c].copy()
    cc["celda"] = cc.apply(lambda q: f"{q['pct']:.0f}% ({q['razon']:.2f}×)", axis=1)
    pv = cc.pivot(index="perfil", columns="categoria", values="celda").reset_index()
    pv.columns = [str(z) for z in pv.columns]
    A(f"**{c}**\n"); A(S.md_tabla(pv)); A("")
A("Medianas ponderadas del contexto de la sección (valores originales):\n")
cm = f[["perfil"] + ["med_" + c for c in D.COLS_CONTEXTO]].copy(); cm.columns = ["perfil"] + D.COLS_CONTEXTO
A(S.md_tabla(cm.astype(object), {c: "{:.3g}" for c in D.COLS_CONTEXTO}))
A("\n### Persistencia descriptiva (la asignación usó todo el periodo 2009-2024)\n")
A("'% sigue' = % de las celdas `objetivo_0921` del perfil (asignación dura, con 2024 observado) que son `objetivo_24`, ponderado por n_2024. "
  "**Aviso:** la mezcla se ajustó con el periodo completo, que incluye 2024; es descriptivo, no validación fuera de tiempo. Filas 'base' = referencia.\n")
A(md_t(pers))
A("\n## 5. Comparación contra la referencia de cuatro perfiles (`perfiles_k4.parquet`)\n")
A("Cruce ponderado por w: fila = perfil K=4, columna = % de su peso en cada perfil K=5 (numeración de cada ajuste por % del déficit).\n")
A(md_t(c4.reset_index(), 1))
A("\nInverso (fila = perfil K=5, % de su peso en cada perfil K=4):\n")
A(md_t(c4_inv.rename(columns=lambda c: f"K4_perfil_{c}").reset_index().rename(columns={"index": "perfil_K5", "row_0": "perfil_K5"}), 1))
A(f"\nARI ponderado (w) K=4 vs K=5: **{ari4['ARI_ponderado_w']:.4f}**; sin ponderar: **{ari4['ARI_sin_ponderar']:.4f}**.\n")
A("## 6. Entrega con cinco perfiles (D-029)\n")
A("Perfiles claros numerados por % del déficit (E1, E2, ...); el resto, si lo hay, se declara con su % del déficit y LN, sin campaña propia. "
  "Archivo por celda: `data/processed/perfiles_finales.parquet` (no se publica, D-005).\n")
A(md_t(te, 3))
(SAL / "control.md").write_text("\n".join(L) + "\n", encoding="utf-8")
log("reporte escrito")
