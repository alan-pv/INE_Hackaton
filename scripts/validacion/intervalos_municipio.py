"""Intervalos por municipio de la captura de 2024, línea base y peso de 80+ (D-032).

(1) Línea base "objetivo sí/no" de la curva de captura; (2) ΔAUC con bootstrap pareado (D-027) remuestreando
MUNICIPIOS (edo, mpio) con reemplazo, estratificado por estado, junto al de secciones; (3) peso de 80+ por perfil.
Usa el mismo universo y los mismos órdenes que la validación con 2024.
Entradas: cachés de seleccion_numero_perfiles (pca.pkl), referencia_cuatro_perfiles (ajuste_2009_2021_K4.pkl) y
validacion_2024 (ajuste_2009_2021_K5.pkl, dauc_*.pkl); perfiles_k4, perfiles_finales, brecha_celda,
panel_celda_eleccion y descriptores_seccion.
Salidas: reports/validacion/intervalos_municipio/, caché data/interim/intervalos_municipio/ (borrarla para rehacer).
Uso: .venv/bin/python scripts/validacion/intervalos_municipio.py"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import pickle
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from ine_perfiles import cohortes as BA
from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import estabilidad as EST
from ine_perfiles import mezcla_mixta as MM

K = C.K_EVALUADO_K5            # D-029
K4 = 4                         # referencia de cuatro perfiles (D-029)
SUFIJO_MPIO = 8                # D-032: semilla propia [SEMILLA, 8] (6 es la del bootstrap por sección, D-027)
N_PROC = 2                     # procesos en paralelo (no cambia ningún resultado)
LLAVE = CF.LLAVE
PROC = C.PROCESADOS
SAL = C.salidas(__file__)
INT_SEL = C.INTERIM / "seleccion_numero_perfiles"        # solo lectura
INT_REF = C.INTERIM / "referencia_cuatro_perfiles"       # solo lectura
INT_VAL = C.INTERIM / "validacion_2024"                  # solo lectura
INT = C.cache("intervalos_municipio")
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


# ======================================================================== 1. universo y órdenes (como en la validación con 2024)
with open(INT_SEL / "pca.pkl", "rb") as fh:
    P = pickle.load(fh)
U0 = CF.cargar_universo(PROC)
cel, h_ok, obj0, m4 = U0["cel"], U0["h_ok"], U0["obj0"], U0["m4"]
o0 = cel[obj0].reset_index(drop=True)
dat0, x0, _ = CF.construir_datos(o0, P["d"], P["pcs"], P["r"], "delta_0921", "deficit_0921")
for c in LLAVE:
    x0[c] = x0[c].astype("int64")
with open(INT_REF / "ajuste_2009_2021_K4.pkl", "rb") as fh:
    mod4, ll4, _ = pickle.load(fh)
with open(INT_VAL / "ajuste_2009_2021_K5.pkl", "rb") as fh:
    mod5, ll5, _ = pickle.load(fh)
R4, ll4c = MM.estep(dat0, mod4)
R5, ll5c = MM.estep(dat0, mod5)
chk(abs(ll4c - ll4) < 0.1 and abs(ll5c - ll5) < 0.1, "logL recalculada de K=4 y K=5 (2009-21) = cachés de la referencia y de la validación con 2024")


def reetiq(map0, ref, KK):
    xp = x0[LLAVE].merge(ref[LLAVE + ["perfil", "w"]], on=LLAVE, how="left", validate="1:1")
    comun = xp["perfil"].notna().to_numpy()
    mapa, _ = CF.reetiquetar(xp.perfil[comun].to_numpy(int) - 1, map0[comun], xp.w[comun].to_numpy(), KK)
    return mapa[map0] + 1


sal = {}
for nom, archivo in (("K4", "perfiles_k4.parquet"), ("K5", "perfiles_finales.parquet")):
    s = pd.read_parquet(PROC / archivo)
    for c in LLAVE:
        s[c] = s[c].astype("int64")
    sal[nom] = s
perfil4_0 = reetiq(R4.argmax(1), sal["K4"], K4)
perfil5_0 = reetiq(R5.argmax(1), sal["K5"], K)
r_a = (cel["p_tilde_0921"].astype(float) / (cel["E_0921"] / cel["N_0921"])).to_numpy()
post_a = np.isnan(r_a)
r_a = np.where(post_a, 1.0, r_a)
r_5, post_5, _, _ = CF.rhat_mezcla(cel, h_ok, obj0, o0, perfil5_0, K)
r_4, post_4, _, _ = CF.rhat_mezcla(cel, h_ok, obj0, o0, perfil4_0, K4)
r_b = np.where(obj0, 0.0, 1.0)      # D-032: línea base, dos bloques (objetivo primero); empates como en D-025
M = {"historial": (r_a, post_a), "K5": (r_5, post_5), "K4": (r_4, post_4), "base": (r_b, None)}
NOM = {"historial": "historial propio", "K5": "mezcla K=5 (2009-21)", "K4": "mezcla K=4 (2009-21)",
       "base": "línea base objetivo_0921 sí/no"}
UNI = {"solo celdas con historial 2009-21": m4 & h_ok, "todas las celdas con 2024": m4}
ln24 = cel["ln_2024"].to_numpy(float)
d24 = cel["deficit_2024_crudo"].to_numpy(float)

auc = {}
filas = []
for un, mk in UNI.items():
    for k, (r, post) in M.items():
        _, ap, as_ = CF.curva_captura(r[mk], ln24[mk], d24[mk], None if post is None else post[mk])
        auc[(un, k)] = ap
        filas.append(dict(universo=un, metodo=NOM[k], AUC_pos=ap, AUC_signo=as_, celdas=int(mk.sum())))
auc_t = pd.DataFrame(filas)
auc_t.to_csv(SAL / "auc_linea_base.csv", index=False, float_format="%.5f")
UV, UT = list(UNI)
for k, ref in (("historial", 0.759), ("K5", 0.720), ("K4", 0.730)):
    chk(abs(auc[(UV, k)] - ref) < 5e-4, f"{UV}: AUC {NOM[k]} = {auc[(UV, k)]:.5f} reproduce {ref}")
chk(abs(auc[(UV, "base")] - 0.672) < 5e-4, f"{UV}: AUC línea base = {auc[(UV, 'base')]:.5f} (esperado ≈ 0.672)")

# ======================================================================== 2. municipio de cada celda
desc = pd.read_parquet(PROC / "descriptores_seccion.parquet", columns=["edo", "seccion", "mpio"])
chk(not desc.duplicated(["edo", "seccion"]).any(), "descriptores_seccion: (edo, seccion) único")
mm = cel[["edo", "seccion"]].merge(desc.astype({"edo": "int64", "seccion": "int64"}), on=["edo", "seccion"], how="left", validate="m:1")
chk(len(mm) == len(cel), "unión celda → municipio conserva filas")
sin_mpio = mm["mpio"].isna().to_numpy()
n_sin = {un: int((sin_mpio & mk).sum()) for un, mk in UNI.items()}
# celdas sin municipio: un grupo propio por estado (mpio = -1) [elección de cómputo, reportada]
mpio = mm["mpio"].fillna(-1).astype("int64").to_numpy()
edo_c = cel["edo"].to_numpy()
cuenta = {}
for un, mk in UNI.items():
    g = pd.DataFrame(dict(edo=edo_c[mk], mpio=mpio[mk])).drop_duplicates()
    cuenta[un] = g.groupby("edo").size()
mpio_edo = pd.DataFrame({un: cuenta[un] for un in UNI}).fillna(0).astype(int)
secc_edo = pd.DataFrame({un: pd.DataFrame(dict(edo=edo_c[mk], s=cel["seccion"].to_numpy()[mk])).drop_duplicates().groupby("edo").size()
                         for un, mk in UNI.items()})
mpio_edo = mpio_edo.join(secc_edo, rsuffix="_secciones")
mpio_edo.to_csv(SAL / "municipios_por_estado.csv")
# el remuestreo conserva el nº de municipios por estado
mk = UNI[UV]
orden_g, ini_g, lar_g, edo_g = EST.indice_secciones(edo_c[mk], mpio[mk])
_, eleg = EST.remuestrear_secciones(np.random.default_rng([C.SEMILLA, SUFIJO_MPIO]), edo_g, orden_g, ini_g, lar_g)
chk((np.bincount(edo_g[eleg].astype(int)) == np.bincount(edo_g.astype(int))).all() and len(eleg) == len(lar_g),
    f"remuestreo conserva el nº de municipios por estado ({len(lar_g):,} municipios en {len(np.unique(edo_g))} estados, universo con historial)")

# ======================================================================== 3. bootstraps pareados
PARES = [("historial − K5", "historial", "K5"), ("K5 − K4", "K5", "K4"), ("K5 − línea base", "K5", "base")]
cl = lambda a: None if a is None else a


def tarea(iu, ip, nivel):
    un, (nombre, n1, n2) = list(UNI)[iu], PARES[ip]
    ruta = INT / f"dauc_{nivel}_{iu}_{ip}.pkl"
    if ruta.exists():
        with open(ruta, "rb") as fh:
            return pickle.load(fh)
    m = UNI[un]
    (r1, p1), (r2, p2) = M[n1], M[n2]
    t = time.time()
    a = (r1[m], None if p1 is None else p1[m], r2[m], None if p2 is None else p2[m], ln24[m], d24[m], edo_c[m])
    if nivel == "mpio":
        o = CF.delta_auc_bootstrap_grupos(*a, mpio[m], sufijo=SUFIJO_MPIO)
    else:
        o = CF.delta_auc_bootstrap(*a, cel["seccion"].to_numpy()[m])
    o["seg"] = time.time() - t
    with open(ruta, "wb") as fh:
        pickle.dump(o, fh)
    return o


# IC por sección: de la validación con 2024 (misma función y semilla) para los dos primeros pares; el de K5 − línea base se calcula aquí
for iu in (0, 1):
    for ip in (0, 1):
        src = INT_VAL / f"dauc_{iu}_{ip}.pkl"
        dst = INT / f"dauc_secc_{iu}_{ip}.pkl"
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
jobs = [(iu, ip, nv) for iu in (0, 1) for nv in ("mpio", "secc") for ip in (0, 1, 2) if not (nv == "secc" and ip < 2)]
jobs = sorted(jobs, key=lambda j: j[0])          # primero el universo principal
log("bootstraps pendientes:", [j for j in jobs if not (INT / f"dauc_{j[2]}_{j[0]}_{j[1]}.pkl").exists()])
res = Parallel(n_jobs=N_PROC, backend="multiprocessing")(delayed(tarea)(*j) for j in jobs)
RES = dict(zip(jobs, res))
for iu in (0, 1):
    for ip in (0, 1):
        with open(INT / f"dauc_secc_{iu}_{ip}.pkl", "rb") as fh:
            RES[(iu, ip, "secc")] = pickle.load(fh)
filas = []
for iu, un in enumerate(UNI):
    for ip, (nombre, n1, n2) in enumerate(PARES):
        s, g = RES[(iu, ip, "secc")], RES[(iu, ip, "mpio")]
        chk(abs(s["auc1"] - auc[(un, n1)]) < 1e-9 and abs(s["auc2"] - auc[(un, n2)]) < 1e-9 and
            abs(g["auc1"] - auc[(un, n1)]) < 1e-9, f"{un} · {nombre}: AUC observado = tabla de AUC (ambos bootstraps)")
        filas.append(dict(universo=un, comparacion=nombre, AUC_1=g["auc1"], AUC_2=g["auc2"], delta_AUC=g["delta"],
                          IC95_secc_inf=s["lo"], IC95_secc_sup=s["hi"], IC95_mpio_inf=g["lo"], IC95_mpio_sup=g["hi"],
                          excluye_0_mpio=bool(g["lo"] > 0 or g["hi"] < 0), ancho_mpio_sobre_secc=(g["hi"] - g["lo"]) / (s["hi"] - s["lo"]),
                          n_municipios=g["n_grupos"], B=g["B"], seg_mpio=g["seg"]))
dt = pd.DataFrame(filas)
dt.to_csv(SAL / "delta_auc_municipio.csv", index=False, float_format="%.5f")
chk(abs(dt.IC95_secc_inf[0] - 0.03784) < 1e-4 and abs(dt.IC95_secc_sup[0] - 0.04026) < 1e-4, "IC por sección historial − K5 = [0.038, 0.040], igual que en la validación con 2024")

# ======================================================================== 4. peso de 80+ por perfil (D-032)
g80 = [g["id"] for g in BA.grupos() if g["edad_max"] is None]
chk(len(g80) == 1, f"grupo abierto (80+) en cortes_edad.json: id = {g80}")
g80 = g80[0]
ent = pd.read_parquet(PROC / "perfiles_finales.parquet", columns=["edo", "seccion", "sexo", "grupo", "perfil", "perfil_entrega", "w"])
bc = pd.read_parquet(PROC / "brecha_celda.parquet", columns=["edo", "seccion", "sexo", "grupo", "deficit", "ln_2024"])
LL = ["edo", "seccion", "sexo", "grupo"]
for t in (ent, bc):
    for c in LL:
        t[c] = t[c].astype("int64")
e = ent.merge(bc, on=LL, how="left", validate="1:1")
chk(len(e) == len(ent) and e.deficit.notna().all(), f"entrega K5 ({len(ent):,} celdas) unida a brecha_celda sin pérdidas")
e["ln"] = e.ln_2024.fillna(0.0).astype(float)
e["dpos"] = e.deficit.clip(lower=0).astype(float)
e["es80"] = e.grupo == g80
tot_dpos, tot_dpos_no80 = e.dpos.sum(), e.dpos[~e.es80].sum()


def fila80(nombre, m):
    s = e[m]
    return dict(perfil=nombre, celdas=int(m.sum()), ln_2024=s.ln.sum(), pct_LN_en_80mas=100 * s.ln[s.es80].sum() / s.ln.sum(),
                deficit_pos=s.dpos.sum(), pct_deficit_en_80mas=100 * s.dpos[s.es80].sum() / s.dpos.sum(),
                pct_deficit_total_con_80=100 * s.dpos.sum() / tot_dpos,
                pct_deficit_total_sin_80=100 * s.dpos[~s.es80].sum() / tot_dpos_no80)


nombres = e.groupby("perfil").perfil_entrega.first()
f80 = [fila80(f"P{p} · {nombres[p]}", (e.perfil == p).to_numpy()) for p in sorted(e.perfil.unique())]
f80.append(fila80("población objetivo completa", np.ones(len(e), bool)))
t80 = pd.DataFrame(f80)
t80.to_csv(SAL / "peso_80mas.csv", index=False, float_format="%.4f")
chk(abs(t80.pct_deficit_total_con_80[:-1].sum() - 100) < 1e-6 and abs(100 * e.dpos[~e.es80].sum() / e.dpos[~e.es80].sum() - 100) < 1e-9,
    "Σ % del déficit total por perfil = 100")
chk(abs(sum(100 * e.dpos[(e.perfil == p) & ~e.es80].sum() / tot_dpos_no80 for p in e.perfil.unique()) - 100) < 1e-6, "Σ % del déficit sin 80+ por perfil = 100")

# ======================================================================== reporte
fm = lambda df, d=4: md_t(df.round(d))
sin_txt = "; ".join(f"{un}: {n_sin[un]:,} celdas" for un in UNI)
md = ["# Intervalos por municipio, línea base de captura y peso de 80+ (D-032)\n",
      "Construcción de órdenes idéntica a la validación con 2024 (universo D-025). Semillas: bootstrap por sección = [SEMILLA, "
      f"{C.SUFIJO_SEMILLA_PERMANENCIA}] (D-027); por municipio = [SEMILLA, {SUFIJO_MPIO}] (D-032); "
      f"B = {C.B_PERMANENCIA}, IC percentil {int(100 * C.NIVEL_IC_PERMANENCIA)}%. N de procesos: {N_PROC}. Tiempo total de la corrida: "
      f"{time.time() - T0:.0f} s (los bootstraps cacheados no se vuelven a calcular; tiempos por bootstrap en la tabla 2).\n",
      "## 0. Cifras de control\n", *QA, "",
      f"- Celdas sin municipio en `descriptores_seccion` (se agrupan como (estado, mpio = -1)): {sin_txt}.\n",
      "## 1. AUC con línea base (D-032)\n", fm(auc_t.drop(columns="AUC_signo"), 5),
      "\n## 2. ΔAUC_pos con IC por sección y por municipio (D-032)\n",
      "ΔAUC = método 1 − método 2; el IC por municipio es el principal (conservador). `ancho_mpio_sobre_secc` = cociente de anchos.\n",
      fm(dt, 5),
      "\n## 3. Municipios por estado en el universo de remuestreo\n", md_t(mpio_edo.reset_index()),
      f"\n## 4. Peso de 80+ (grupo {g80}) por perfil de la entrega K=5 (D-032)\n",
      "LN en personas; déficit = Σ max(déficit, 0) por celda; `pct_deficit_total_sin_80` = participación de cada perfil en el déficit positivo "
      "total tras excluir las celdas de 80+. Descriptivo, no cambia la entrega.\n", fm(t80, 2)]
(SAL / "control.md").write_text("\n".join(md) + "\n", encoding="utf-8")
log("reporte escrito")
print(auc_t.round(5).to_string()); print(dt.round(5).to_string()); print(t80.round(2).to_string())
