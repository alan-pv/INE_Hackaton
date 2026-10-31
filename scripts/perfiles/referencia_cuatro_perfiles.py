"""Referencia de cuatro perfiles: la mezcla con K=4 y su captura del déficit de 2024 (D-025, D-029).

Sirve de comparación para elegir cinco perfiles (D-029) y para la prueba de la violencia (D-027):
(1) perfiles K=4 del periodo completo; (2) la misma mezcla reajustada solo con 2009-2021; (3) curva de captura
del déficit de 2024 ordenando con 2009-2021: historial propio, mezcla K=4 y orden al azar; (4) persistencia por perfil.
Entradas: caché de seleccion_numero_perfiles (pca.pkl, ajuste_K4.pkl), brecha_celda y panel_celda_eleccion.
Salidas: data/processed/perfiles_k4.parquet, reports/perfiles/referencia_cuatro_perfiles/,
caché data/interim/referencia_cuatro_perfiles/ (borrar ajuste_2009_2021_K4.pkl para rehacer el ajuste).
Uso: .venv/bin/python scripts/perfiles/referencia_cuatro_perfiles.py"""
import pickle
import time
import types

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import mezcla_mixta as MM
from ine_perfiles import seleccion as S

K = 4
LLAVE = CF.LLAVE
SAL = C.salidas(__file__)
INT_SEL = C.INTERIM / "seleccion_numero_perfiles"        # solo lectura
INT = C.cache("referencia_cuatro_perfiles")
T0 = time.time()
TIEMPOS = {}
QA = []   # cifras de control


def log(*a):
    print(f"[{time.time() - T0:7.0f}s]", *a, flush=True)


def chk(cond, texto):
    QA.append(f"- [{'OK' if cond else 'FALLA'}] {texto}")
    assert cond, texto


def tic(nombre):
    TIEMPOS[nombre] = time.time()


def toc(nombre):
    TIEMPOS[nombre] = time.time() - TIEMPOS[nombre]
    log(f"{nombre}: {TIEMPOS[nombre]:.0f}s")


# ======================================================================== 1. mezcla K=4 del periodo completo
with open(INT_SEL / "pca.pkl", "rb") as fh:
    P = pickle.load(fh)
dat, x, et, nombres_cont, n_cero = S.construir(P)
S.DAT = dat
with open(INT_SEL / f"ajuste_K{K}.pkl", "rb") as fh:
    modelo = pickle.load(fh)[0]
R, ll = MM.estep(dat, modelo)
f, comp, pos, mapa, pmax = S.perfiles(K, types.SimpleNamespace(R=R), x, et, P)
perfil = np.array([pos[int(k)] for k in mapa])
orden_clase = [k for k, _ in sorted(pos.items(), key=lambda kv: kv[1])]
Rp = R[:, orden_clase]                       # columna j = perfil j+1
n_obj = dat.n
chk(n_obj == C.SENS_CELDAS_OBJETIVO_CONTROL, f"celdas objetivo = {n_obj:,} (esperadas {C.SENS_CELDAS_OBJETIVO_CONTROL:,})")
chk(abs(dat.w.sum() - n_obj) < 1e-6 * n_obj, f"Σ pesos = {dat.w.sum():,.3f} = nº de celdas {n_obj:,}")

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
sal.to_parquet(C.PROCESADOS / "perfiles_k4.parquet", index=False)
chk(len(sal) == n_obj, "perfiles_k4.parquet: una fila por celda objetivo")
chk(np.allclose(Rp.sum(1), 1), "responsabilidades suman 1 por celda")

# ======================================================================== 2. universo y mezcla reajustada con 2009-21
tic("universo 2009-21")
U0 = CF.cargar_universo(C.PROCESADOS)
cel, h_ok, obj0, m4, b = U0["cel"], U0["h_ok"], U0["obj0"], U0["m4"], U0["b"]
toc("universo 2009-21")
chk(not cel.duplicated(LLAVE).any(), f"llave (edo, seccion, sexo, grupo) única en {len(cel):,} celdas con E>0 (de {len(b):,})")
rowcel = x[LLAVE].merge(cel[LLAVE].assign(r=np.arange(len(cel))), on=LLAVE, how="left", validate="1:1")["r"]
chk(rowcel.notna().all() and len(rowcel) == n_obj, "toda celda objetivo está en el universo de la curva de captura (merge 1:1)")
chk(np.allclose((cel.E - cel.N * cel.p_tilde.astype(float)) / cel.m, cel.deficit, atol=1e-3),
    "fórmula déficit = (E − N·p̃)/m reproduce la columna `deficit` del periodo completo (D-022)")
chk(obj0.sum() == b["objetivo_0921"].fillna(False).astype(bool).sum(), f"población objetivo 2009-21 = {obj0.sum():,} celdas")
o0 = cel[obj0].reset_index(drop=True)
dat0, x0, n_cero0 = CF.construir_datos(o0, P["d"], P["pcs"], P["r"], "delta_0921", "deficit_0921")
chk(abs(dat0.w.sum() - dat0.n) < 1e-6 * dat0.n, f"mezcla 2009-21: Σ pesos = {dat0.w.sum():,.1f} = nº de celdas {dat0.n:,}")

# control: la construcción parametrizada reproduce la de seleccion.construir con los datos del periodo completo
oc = cel[cel["objetivo"]].reset_index(drop=True)
datc, _, _ = CF.construir_datos(oc, P["d"], P["pcs"], P["r"], "delta", "deficit")
chk(datc.n == dat.n and (datc.cat == dat.cat).all() and np.allclose(datc.X, dat.X, equal_nan=True) and np.allclose(datc.w, dat.w),
    "construir_datos reproduce seleccion.construir (cat, X, w) en el periodo completo")

ruta0 = INT / "ajuste_2009_2021_K4.pkl"
tic("ajuste 2009-21")
if ruta0.exists():
    with open(ruta0, "rb") as fh:
        mod0, ll0, info0 = pickle.load(fh)
    log("ajuste 2009-21 leído de caché")
else:
    rng = np.random.default_rng([C.SEMILLA, 2, K])      # misma regla de semilla que seleccion.tarea_ajuste
    aj0, info0 = MM.ajustar_con_reinicios(dat0, K, rng, log=log)
    mod0, ll0 = aj0.modelo, aj0.logL
    with open(ruta0, "wb") as fh:
        pickle.dump((mod0, ll0, info0), fh)
toc("ajuste 2009-21")
R0, _ = MM.estep(dat0, mod0)
map0 = R0.argmax(1)
# reetiquetado contra los K=4 completos (asignación húngara sobre el cruce ponderado por w, D-021)
xp = pd.DataFrame(dict(i=np.arange(dat0.n))).join(
    x0[LLAVE].merge(sal[LLAVE + ["perfil", "w"]], on=LLAVE, how="left", validate="1:1")[["perfil", "w"]])
comun = xp["perfil"].notna().to_numpy()
mapa_h, cruce_h = CF.reetiquetar(xp.perfil[comun].to_numpy(int) - 1, map0[comun], xp.w[comun].to_numpy(), K)
perfil0 = mapa_h[map0] + 1
ari_0921 = CF.ari_ponderado(xp.perfil[comun].to_numpy(int), perfil0[comun], xp.w[comun].to_numpy())
cruce_tab = pd.DataFrame({f"perfil_completo_{j + 1}": [cruce_h[k, j] / cruce_h[:, j].sum() * 100 for k in range(K)] for j in range(K)},
                         index=[f"clase 2009-21 → perfil {mapa_h[k] + 1}" for k in range(K)])

# ======================================================================== 3. curva de captura de 2024 (D-025)
r_a = (cel["p_tilde_0921"].astype(float) / (cel["E_0921"] / cel["N_0921"])).to_numpy()
post_a = np.isnan(r_a)
r_a = np.where(post_a, 1.0, r_a)       # sin historial propio: razón 1 = "solo edad y sexo", al final
r_c, post_c, razon_perfil, razon_nobj = CF.rhat_mezcla(cel, h_ok, obj0, o0, perfil0, K)
r_d = np.random.default_rng(C.SEMILLA).permutation(len(cel)).astype(float)
metodos = {"historial propio": (r_a, post_a), "mezcla K=4 (2009-21)": (r_c, post_c), "azar": (r_d, None)}

E4, O4 = cel["E_24"].to_numpy(float), cel["O_24"].to_numpy(float)
d24c = cel["deficit_2024_crudo"].to_numpy(float)
chk(np.allclose(d24c[m4], (E4 - O4)[m4], atol=1e-2, rtol=1e-5), "déficit crudo 2024 = E_24 − O_24 (float32 vs float64)")
ln24 = cel["ln_2024"].to_numpy(float)
U = {"todas las celdas con 2024": m4, "solo celdas con historial 2009-21": m4 & h_ok}
res, curvas_full, curvas = [], [], {}
tic("curvas")
for un, mk in U.items():
    for nom, (r, post) in metodos.items():
        c, ap, as_ = CF.curva_captura(r[mk], ln24[mk], d24c[mk], None if post is None else post[mk])
        curvas[(un, nom)] = (c, ap, as_)
        res.append(dict(universo=un, metodo=nom, AUC_pos=ap, AUC_signo=as_, celdas=int(mk.sum())))
        curvas_full.append(c.assign(universo=un, metodo=nom))
res = pd.DataFrame(res)
res.to_csv(SAL / "captura_resumen.csv", index=False, float_format="%.5f")
pd.concat(curvas_full, ignore_index=True).to_parquet(INT / "curvas_captura.parquet", index=False)
sig_total = float(d24c[m4].sum())
toc("curvas")

fig, ax = plt.subplots(1, 2, figsize=(13, 5))
col = {"historial propio": "C0", "mezcla K=4 (2009-21)": "C3", "azar": "gray"}
for i, un in enumerate(U):
    a_ = ax[i]
    for nom in metodos:
        c, ap, _ = curvas[(un, nom)]
        a_.plot(c.x, c["y_pos"], color=col[nom], lw=1.2, label=f"{nom}  AUC={ap:.3f}", rasterized=True)
    a_.plot([0, 1], [0, 1], color="k", lw=.5, ls=":")
    a_.set_xlabel("fracción acumulada de LN 2024 (celdas de menor a mayor r̂ de 2009-21)")
    a_.set_ylabel("déficit positivo acumulado de 2024")
    a_.set_title(un, fontsize=10)
    a_.legend(fontsize=8, loc="best")
fig.tight_layout()
fig.savefig(SAL / "captura.png", dpi=110)
plt.close(fig)

# ======================================================================== 4. persistencia por perfil de la mezcla reajustada
E0, O0 = cel["E_0921"].to_numpy(float), cel["O_0921"].to_numpy(float)
n24 = cel["n_2024"].to_numpy(float)
obj24 = cel["objetivo_24"].fillna(False).astype(bool).to_numpy()
ln24c = cel["ln_2024"].fillna(0).to_numpy(float)


def fila_persist(nombre, mk):
    mk2 = mk & m4
    return dict(perfil=nombre, celdas=int(mk.sum()), ln_2024_miles=ln24c[mk].sum() / 1e3,
                razon_OE_0921=O0[mk].sum() / E0[mk].sum(), razon_OE_2024=O4[mk2].sum() / E4[mk2].sum(),
                pct_sigue_bajo_2024_ponderado_n24=100 * np.average(obj24[mk2], weights=n24[mk2]),
                pct_sigue_bajo_2024_celdas=100 * obj24[mk2].mean())


pp = np.zeros(len(cel), int)
pp[np.flatnonzero(obj0)] = perfil0
filas = [fila_persist(f"perfil {p}", pp == p) for p in range(1, K + 1)]
filas.append(fila_persist("todos los objetivo_0921", obj0))
filas.append(fila_persist("no objetivo_0921 (con historial)", h_ok & ~obj0))
filas.append(fila_persist("base: todas las celdas con historial", h_ok))
per_perfil = pd.DataFrame(filas)
per_perfil.to_csv(SAL / "persistencia_perfiles.csv", index=False, float_format="%.5f")

# ======================================================================== reporte
cols = ["perfil", "pct_deficit", "celdas", "ln_2024_miles", "delta_medio", "pct_crudo_2024", "pmax_media",
        "pct_pmax_ge_09", "med_graproes", "med_prop_internet", "med_im_2020", "med_pctl_mov_estado"]
f.to_csv(SAL / "perfiles_K4.csv", index=False)
comp.to_csv(SAL / "composicion_K4.csv", index=False)
md_t = lambda df: S.md_tabla(df.astype(object))   # object: conserva enteros en la tabla
fm = lambda df, d=3: md_t(df.round(d))
md = ["# Referencia de cuatro perfiles y captura del déficit de 2024 (D-025, D-029)\n",
      "Perfiles ordenados por % del déficit (responsabilidades × w). El contexto describe la sección, no a las personas (D-010).\n",
      "**Nota de lectura (D-026):** `im_2020` alto = **menos** marginación; `iim_dp2` alto = **menos** intensidad migratoria; "
      "`pctl_mov_estado` alto = más llegada neta de registros a la sección que la esperada (bajo = salida neta), percentil dentro del estado (D-016).\n",
      "## 0. Cifras de control\n", *QA, "",
      f"- logL del K=4 completo recalculada desde la caché: {ll:,.1f}. Variables continuas: {nombres_cont}; celdas con w=0: {n_cero}.",
      f"- Mezcla 2009-21: celdas objetivo_0921 {dat0.n:,}; celdas con w=0: {n_cero0}; logL = {ll0:,.1f}; reinicios {info0['reinicios']}, "
      f"óptimo repetido {info0['repetido']} ({info0['repeticiones']} veces), no convergieron {info0['no_convergio']}, pisos {info0['pisos']}.",
      f"- Tiempos (s): " + ", ".join(f"{k} {v:.0f}" for k, v in TIEMPOS.items()) + f"; total {time.time() - T0:.0f}.\n",
      "## 1. Perfiles K=4\n", fm(f[cols]),
      "\n### Rasgos sobrerrepresentados (razón ≥ 1.25 o ≥ 40%; filtro solo de presentación)\n"]
for p in range(1, K + 1):
    s = comp[(comp.perfil == p) & ((comp.razon >= 1.25) | (comp.pct >= 40))]
    md += [f"#### Perfil {p}\n", fm(s[["variable", "categoria", "pct", "razon"]], 2), ""]
md += ["## 2. Captura del déficit de 2024 ordenando con 2009-21 (D-025)\n",
       "Curva de captura: celdas de menor a mayor r̂ (información solo de 2009-21); x = fracción acumulada de LN 2024; y = fracción acumulada del déficit "
       "crudo 2024 Σ(E_24 − O_24). `pos`: parte positiva por celda, normalizada por su total (termina en 1). `signo`: déficit con signo acumulado entre el "
       f"déficit positivo total (termina en ≈ 0, porque Σ O = Σ E por estrato en 2024: total con signo = {sig_total:,.2f}). "
       "Empates de r̂ = segmento recto (esperanza con desempate aleatorio). AUC = área bajo la curva (0.5 = diagonal para `pos`). "
       "Métodos: historial propio = p̃_0921/(E_0921/N_0921) [las celdas sin historial van al final con razón 1]; mezcla K=4 reajustada con 2009-21 "
       f"(r̂ = ΣO/ΣE del perfil asignado; las celdas no objetivo_0921 van al final con razón {razon_nobj:.4f}); azar = orden aleatorio con semilla {C.SEMILLA}. "
       "Figura: `captura.png`.\n",
       fm(res, 4),
       "\n### Mezcla K=4 reajustada con 2009-21\n",
       f"- Datos: población objetivo_0921, δ̃ = delta_0921, w = déficit 2009-21 = (E_0921 − N_0921·p̃_0921)/m_0921; "
       f"mismo PCA y Horn que la selección de K ({P['r']} componentes); reglas de D-017, semilla [C.SEMILLA, 2, K].",
       f"- Reetiquetado (asignación húngara) contra los K=4 completos en {int(comun.sum()):,} celdas comunes (de {dat0.n:,}); ARI ponderado entre ambas asignaciones: **{ari_0921:.3f}**.\n",
       "Cruce (columnas = perfil completo; % del peso w de cada perfil completo que cae en cada clase 2009-21):\n",
       md_t(cruce_tab.round(1).reset_index().rename(columns={"index": "clase 2009-21"})),
       "\n## 3. Persistencia por perfil (mezcla 2009-21 → 2024)\n",
       "Razones O/E agrupadas ΣO/ΣE; '% sigue bajo' = objetivo_24 en 2024 entre celdas con 2024; base = todas las celdas con historial.\n",
       fm(per_perfil, 3)]
(SAL / "control.md").write_text("\n".join(md) + "\n", encoding="utf-8")
log("reporte escrito")
