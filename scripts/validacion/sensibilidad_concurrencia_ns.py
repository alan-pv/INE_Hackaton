"""Sensibilidad de los perfiles a la gubernatura concurrente (D-030) y a los votos no especificados (D-031).

Por escenario (concurrencia, ns_voto, ns_abst) y un control (principal): lo esperado con su definición, la brecha
completa (D-022), los datos de la mezcla con la MISMA PCA y un reajuste tibio de K=5 desde el ajuste entregado (D-021).
Entradas: panel_celda_eleccion, brecha_celda, perfiles_finales, concurrencia (data/interim/externos/) y la caché de
seleccion_numero_perfiles (pca.pkl, ajuste_K5.pkl).
Salidas: reports/validacion/sensibilidad_concurrencia_ns/, caché data/interim/sensibilidad_concurrencia_ns/ (retomable).
Uso: .venv/bin/python scripts/validacion/sensibilidad_concurrencia_ns.py"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import gc
import json
import pickle
import time

import numpy as np
import pandas as pd

from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import mezcla_mixta as MM
from ine_perfiles import sensibilidad as S

K = C.K_EVALUADO_K5                                      # D-029
LLAVE = S.LLAVE
PROC = C.PROCESADOS
SAL = C.salidas(__file__)
INT_SEL = C.INTERIM / "seleccion_numero_perfiles"        # solo lectura
INT = C.cache("sensibilidad_concurrencia_ns")
COLS_PANEL = LLAVE + ["aelec", "sv", "nv", "ns", "ln"]
T0 = time.time()
QA, TIEMPOS = [], {}


def log(*a):
    print(f"[{time.time() - T0:7.0f}s]", *a, flush=True)


def chk(cond, texto):
    QA.append(f"- [{'OK' if cond else 'FALLA'}] {texto}")
    assert cond, texto


def md_t(df):
    df = df.astype(object)
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)] +
                     ["| " + " | ".join(map(str, r)) + " |" for r in df.to_numpy()])


def tiempo(nombre, seg):
    ruta = INT / "tiempos.json"                          # el tiempo de la corrida que calculó se conserva
    prev = json.load(open(ruta)) if ruta.exists() else {}
    prev[nombre] = max(seg, prev.get(nombre, 0))
    json.dump(prev, open(ruta, "w"), ensure_ascii=False)
    TIEMPOS[nombre] = prev[nombre]


def a_llave_int(df):
    for c in LLAVE:
        df[c] = df[c].astype("int64")
    return df


# ======================================================================== 0. entradas fijas
entrega = a_llave_int(pd.read_parquet(PROC / "perfiles_finales.parquet"))
chk(len(entrega) == C.SENS_CELDAS_OBJETIVO_CONTROL and not entrega.duplicated(LLAVE).any(),
    f"entrega K=5: {len(entrega):,} celdas, llave única")
with open(INT_SEL / "pca.pkl", "rb") as fh:
    P = pickle.load(fh)
SEC, PCS, R_PCA = P["d"], P["pcs"], P["r"]
del P
with open(INT_SEL / f"ajuste_K{K}.pkl", "rb") as fh:
    MOD0 = pickle.load(fh)[0]
conc = S.cargar_concurrencia(C.INTERIM / "externos" / "concurrencia.parquet")
gc.collect()

# ---- cifras de control del panel (fórmula oficial D-001) y base 2024
ruta_b24 = INT / "base_2024.parquet"
ruta_ctrl = INT / "cifras_control.json"
if ruta_b24.exists() and ruta_ctrl.exists():
    ctrl = json.load(open(ruta_ctrl))
    base24 = pd.read_parquet(ruta_b24)
    base24 = a_llave_int(base24).set_index(LLAVE)
else:
    pan = pd.read_parquet(PROC / "panel_celda_eleccion.parquet", columns=COLS_PANEL)
    ctrl = {}
    for a, cc in C.CIFRAS_CONTROL.items():
        pa = pan[pan.aelec == a]
        for nom, msk in (("nacional", slice(None)), ("mujeres", pa.sexo == C.SEXO_MUJER), ("hombres", pa.sexo == C.SEXO_HOMBRE)):
            d = pa if nom == "nacional" else pa[msk]
            ctrl[f"{a}_{nom}"] = 100 * float(d.sv.sum()) / float(d.sv.sum() + d.nv.sum())
    base24 = S.base_2024(pan)
    base24.reset_index().to_parquet(ruta_b24, index=False)
    json.dump(ctrl, open(ruta_ctrl, "w"))
    del pan
    gc.collect()
for a, cc in C.CIFRAS_CONTROL.items():
    for nom, (val, tol) in cc.items():
        if a == 2024:      # el panel sigue cohortes de 2024 (D-006): solo 2024 reproduce la cifra oficial; 2009/2021 se informan
            chk(abs(ctrl[f"{a}_{nom}"] - val) <= tol, f"participación {a} {nom} = {ctrl[f'{a}_{nom}']:.2f}% (control {val}%, tol {tol})")
        else:
            QA.append(f"- [info] participación {a} {nom} en el panel (cohortes de 2024, D-006) = {ctrl[f'{a}_{nom}']:.2f}% (cifra oficial {val}%, no aplica al panel)")
ln24 = base24["ln_2024"]
n24 = base24["n_2024"]
del ctrl


# ======================================================================== 1. brecha por escenario (con caché)
def brecha(esc):
    ruta, rphi, rmeta = INT / f"cel_{esc}.parquet", INT / f"phi_{esc}.csv", INT / f"meta_{esc}.json"
    if ruta.exists() and rphi.exists() and rmeta.exists():
        cel = a_llave_int(pd.read_parquet(ruta)).set_index(LLAVE)
        log(f"{esc}: brecha leída de caché ({len(cel):,} celdas)")
        return cel, pd.read_csv(rphi), json.load(open(rmeta))
    t = time.time()
    pan = pd.read_parquet(PROC / "panel_celda_eleccion.parquet", columns=COLS_PANEL)
    nfilas = len(pan)
    p = S.preparar_panel(pan, "principal" if esc == "principal" else esc, conc)
    del pan
    gc.collect()
    extra = ["k"] if esc == "concurrencia" else []
    cel, phi, q, err = S.brecha_escenario(p, extra)
    meta = dict(filas_panel=nfilas, filas_n_pos=int((p.n > 0).sum()), error_conservacion=err, celdas=len(cel),
                celdas_objetivo=int(cel.objetivo.sum()), votos_faltantes=S.votos_faltantes(cel),
                n_k1=int(p.k.sum()) if "k" in p else 0)
    if esc == "concurrencia":
        # tabla observado/esperado por perfil y elección con las dos definiciones de lo esperado (D-030)
        q_main = S.tasa_esperada_k(p)
        tab = S.tabla_perfil_eleccion(p, entrega, q_main, q)
        tab.to_csv(INT / "tabla_perfil_eleccion.csv", index=False, float_format="%.6f")
    cel.reset_index().to_parquet(ruta, index=False)
    phi.to_csv(rphi, index=False)
    json.dump(meta, open(rmeta, "w"))
    del p, q
    gc.collect()
    tiempo(f"brecha_{esc}", time.time() - t)
    log(f"{esc}: brecha calculada en {time.time() - t:.0f}s ({len(cel):,} celdas, objetivo {meta['celdas_objetivo']:,})")
    return cel, phi, meta


def refit(esc, cel):
    """Reajuste tibio K=5 (D-021). Devuelve (asig, info) con asig = LLAVE, delta, deficit, w, clase."""
    rasig, rinfo = INT / f"asig_{esc}.parquet", INT / f"refit_{esc}.pkl"
    if rasig.exists() and rinfo.exists():
        log(f"{esc}: reajuste leído de caché")
        return a_llave_int(pd.read_parquet(rasig)), pickle.load(open(rinfo, "rb"))
    t = time.time()
    dat, x, n_cero = S.datos_mezcla(cel, SEC, PCS, R_PCA)
    chk(abs(dat.w.sum() - dat.n) < 1e-6 * dat.n, f"{esc}: Σ pesos = {dat.w.sum():,.1f} = nº de celdas {dat.n:,}")
    R0, ll0 = MM.estep(dat, MOD0)                    # logL del ajuste final sobre los datos del escenario (antes de reajustar)
    aj = S.reajuste_tibio(dat, MOD0)
    clase = aj.R.argmax(1)
    info = dict(logL_inicial=ll0, logL=aj.logL, iteraciones=aj.n_iter,
                convergio=aj.convergio, pisos=aj.pisos,
                n_cero=n_cero, celdas=dat.n, ncat=dat.ncat, seg=time.time() - t,
                ari_map_inicial_vs_final=CF.ari_ponderado(R0.argmax(1), clase, dat.w))
    asig = x[LLAVE + ["delta", "deficit"]].copy()
    asig["w"] = dat.w
    asig["clase"] = clase.astype("int8")
    asig["clase0"] = R0.argmax(1).astype("int8")      # MAP del ajuste final SIN reajustar (control)
    asig.to_parquet(rasig, index=False)
    pickle.dump(info, open(rinfo, "wb"))
    tiempo(f"refit_{esc}", time.time() - t)
    log(f"{esc}: reajuste {info['iteraciones']} it, convergió={info['convergio']}, logL {ll0:,.1f} -> {aj.logL:,.1f}, {time.time() - t:.0f}s")
    del dat, x, aj, R0
    gc.collect()
    return asig, info


# ======================================================================== 2. ejecución
res = {}
for esc in S.ESCENARIOS:
    cel, phi, meta = brecha(esc)
    chk(meta["error_conservacion"] < C.SENS_TOL_CONSERVACION,
        f"{esc}: Σ O = Σ E por sexo×grupo×elección{'×k' if esc == 'concurrencia' else ''}; error relativo máx. {meta['error_conservacion']:.2e}")
    res[esc] = dict(cel=cel, phi=phi, meta=meta)
    if esc == "principal":
        chk(meta["celdas_objetivo"] == C.SENS_CELDAS_OBJETIVO_CONTROL,
            f"principal reproducida: {meta['celdas_objetivo']:,} celdas objetivo (control {C.SENS_CELDAS_OBJETIVO_CONTROL:,})")
        chk(round(meta["votos_faltantes"] / 1e6, 2) == C.SENS_VOTOS_FALTANTES_CONTROL_M,
            f"principal reproducida: {meta['votos_faltantes']:,.0f} votos faltantes por elección (control {C.SENS_VOTOS_FALTANTES_CONTROL_M} M)")
        b = pd.read_parquet(PROC / "brecha_celda.parquet", columns=LLAVE + ["delta", "objetivo", "n_2024", "ln_2024"])
        b = a_llave_int(b).set_index(LLAVE)
        j = cel[["delta", "objetivo"]].join(b[["delta", "objetivo"]], how="outer", lsuffix="", rsuffix="_b")
        chk(len(j) == len(cel) == len(b), f"principal: mismas {len(b):,} celdas que brecha_celda.parquet")
        chk(bool((j.objetivo == j.objetivo_b).all()), "principal: la población objetivo coincide celda a celda con brecha_celda.parquet")
        chk(float(np.nanmax(np.abs(j.delta - j.delta_b))) < 1e-4, f"principal: δ̃ = brecha_celda (máx |Δ| = {float(np.nanmax(np.abs(j.delta - j.delta_b))):.1e}; float32)")
        ii = b.index[b.ln_2024.notna()]
        chk(float(np.abs(ln24.reindex(ii).to_numpy() - b.ln_2024.reindex(ii).to_numpy()).max()) < 1e-3, "LN 2024 de la base = brecha_celda.ln_2024")
        del b, j
    gc.collect()

asig = {}
info = {}
for esc in S.ESCENARIOS:
    asig[esc], info[esc] = refit(esc, res[esc]["cel"])
    gc.collect()

# ======================================================================== 3. comparaciones con la entrega
cel_p = res["principal"]["cel"]
ent = entrega[LLAVE + ["perfil", "w"]]
filas_pob, filas_sp, filas_ari, filas_def, reglas, cruces = [], [], [], [], [], {}
perfil_nom = [f"P{j}" for j in range(1, K + 1)]
for esc in S.ESCENARIOS:
    cs = res[esc]["cel"]
    a = asig[esc]
    # --- control del escenario "principal": MAP de ajuste_K5 sin reajustar vs entrega
    m = a.merge(ent, on=LLAVE, how="inner", validate="1:1", suffixes=("", "_ent"))
    comunes = len(m)
    ref = m.perfil.to_numpy(int) - 1
    # reetiquetado Hungarian y ARI
    mapa, cruce = CF.reetiquetar(ref, m.clase.to_numpy(), m.w_ent.to_numpy(), K)
    ari = CF.ari_ponderado(ref, mapa[m.clase.to_numpy()], m.w_ent.to_numpy())
    rg = S.cruce_y_regla(ref, m.clase.to_numpy(), m.w_ent.to_numpy(), K)
    rg_s = S.cruce_y_regla(ref, m.clase.to_numpy(), m.w.to_numpy(), K)         # mismo cruce con los pesos del propio escenario
    orden = np.argsort(rg["mapa"])                                             # fila i = clase asignada al perfil i+1
    cr = pd.DataFrame(rg["pct_fila"][orden], columns=perfil_nom,
                      index=[f"clase {c} (→ P{rg['mapa'][c] + 1})" for c in orden]).round(1)
    cr["peso_%"] = (100 * rg["peso_clase"][orden] / rg["peso_clase"].sum()).round(1)
    cr["cuota_máx_%"] = (100 * rg["cuota"][orden]).round(1)
    cr["¿>½ en un perfil?"] = np.where(rg["cumple"][orden], "SÍ", "NO")
    cruces[esc] = (cr, rg, rg_s, orden)
    ari0 = CF.ari_ponderado(ref, CF.reetiquetar(ref, m.clase0.to_numpy(), m.w_ent.to_numpy(), K)[0][m.clase0.to_numpy()], m.w_ent.to_numpy())
    filas_ari.append(dict(escenario=esc, celdas_escenario=len(a), celdas_comunes=comunes, ARI_ponderado=ari,
                          ARI_sin_reajustar=ari0, regla_global="SÍ" if rg["global_cumple"] else "NO",
                          regla_global_pesos_escenario="SÍ" if rg_s["global_cumple"] else "NO",
                          iteraciones=info[esc]["iteraciones"], convergio=info[esc]["convergio"],
                          logL_inicial=info[esc]["logL_inicial"], logL=info[esc]["logL"], seg=info[esc]["seg"]))
    # --- % del déficit por perfil (escenario con sus clases reetiquetadas)
    perf_esc = rg["mapa"][a.clase.to_numpy()] + 1
    pe = S.pct_deficit_por_perfil(a.deficit.to_numpy(), perf_esc, K)
    mp = entrega[LLAVE + ["perfil"]].merge(cel_p[["deficit"]].reset_index(), on=LLAVE, how="left", validate="1:1")
    chk(mp.deficit.notna().all(), f"{esc}: la entrega tiene déficit principal en las {len(mp):,} celdas")
    pp = S.pct_deficit_por_perfil(mp.deficit.to_numpy(), mp.perfil.to_numpy(), K)
    for j in range(K):
        filas_def.append(dict(escenario=esc, perfil=f"P{j + 1}", pct_deficit_principal=pp[j], pct_deficit_escenario=pe[j],
                              dif_pts=pe[j] - pp[j]))
    # --- población objetivo y votos faltantes
    c = S.comparar_objetivos(cel_p, cs, ln24)
    c.update(escenario=esc, votos_faltantes_M=res[esc]["meta"]["votos_faltantes"] / 1e6,
             votos_faltantes_principal_M=res["principal"]["meta"]["votos_faltantes"] / 1e6)
    filas_pob.append(c)
    rho, nsp = S.spearman_delta(cel_p, cs, n24)
    filas_sp.append(dict(escenario=esc, spearman_delta=rho, celdas=nsp))
    # --- regla por clase
    for c0 in orden:
        reglas.append(dict(escenario=esc, clase=f"clase {c0} (→ P{rg['mapa'][c0] + 1})", perfil_dominante=f"P{rg['dominante'][c0] + 1}",
                           cuota_pct=100 * rg["cuota"][c0], cumple="SÍ" if rg["cumple"][c0] else "NO",
                           cuota_pct_pesos_escenario=100 * rg_s["cuota"][c0]))
    log(f"{esc}: ARI {ari:.4f}; regla global {rg['global_cumple']}")

pob = pd.DataFrame(filas_pob)
sp = pd.DataFrame(filas_sp)
ari_t = pd.DataFrame(filas_ari)
defi = pd.DataFrame(filas_def)
reg = pd.DataFrame(reglas)
pob.to_csv(SAL / "poblacion_objetivo.csv", index=False, float_format="%.5f")
sp.to_csv(SAL / "spearman.csv", index=False, float_format="%.5f")
ari_t.to_csv(SAL / "ari.csv", index=False, float_format="%.5f")
defi.to_csv(SAL / "deficit_por_perfil.csv", index=False, float_format="%.4f")
reg.to_csv(SAL / "regla_mayoria.csv", index=False, float_format="%.3f")
for esc, (cr, rg, rg_s, orden) in cruces.items():
    cr.to_csv(SAL / f"cruce_{esc}.csv")

# control del principal reproducido: sin reajuste el ARI debe ser ~1 (mismos datos, mismo modelo)
a_p = ari_t[ari_t.escenario == "principal"].iloc[0]
chk(a_p.ARI_sin_reajustar > 0.999, f"principal: ARI de ajuste_K5 sobre los datos recalculados vs entrega = {a_p.ARI_sin_reajustar:.5f} (> 0.999)")

# ======================================================================== 4. tabla perfil × elección (concurrencia)
tab = pd.read_csv(INT / "tabla_perfil_eleccion.csv")
tab.to_csv(SAL / "perfil_eleccion_concurrencia.csv", index=False, float_format="%.4f")
imp = S.intermedias_menos_presidenciales(tab)
imp.to_csv(SAL / "intermedias_menos_presidenciales.csv", index=False, float_format="%.4f")
chk(tab.groupby("perfil").size().eq(len(C.ELECCIONES)).all(), f"tabla perfil × elección: {len(tab)} filas = {K} perfiles × {len(C.ELECCIONES)} elecciones")

# ======================================================================== 5. reporte
fm = lambda df, d=4: md_t(df.round(d))
md = ["# Sensibilidad a la gubernatura concurrente (D-030) y a los votos no especificados (D-031)\n",
      "Escenarios: `concurrencia` (q_gsek, D-030), `ns_voto` (votos = SV+NS, n = SV+NV+NS, D-031) y `ns_abst` (votos = SV, n = SV+NV+NS, D-031). "
      "`principal` es la misma cadena recalculada con este código (control). Reajuste tibio de K=5 desde `ajuste_K5.pkl`, tolerancia "
      f"{MM.TOL_REFINA:g}, tope {MM.MAXIT_REFINA} it (D-021), con la misma PCA (r = {R_PCA}). Participación = SV/(SV+NV) (D-001) salvo en las cotas de D-031.\n",
      "## 0. Cifras de control y verificaciones\n", *QA, "",
      "## 1. Población objetivo y votos faltantes (por elección)\n",
      "frac_ln_sigue = fracción de la LN 2024 del objetivo principal que sigue en el objetivo del escenario; jaccard_ln = Jaccard ponderado por LN 2024.\n",
      fm(pob[["escenario", "celdas_principal", "celdas_escenario", "celdas_interseccion", "celdas_union", "ln_principal", "ln_escenario",
              "frac_ln_sigue", "jaccard_ln", "votos_faltantes_M", "votos_faltantes_principal_M"]], 4),
      "\n## 2. Spearman ponderada (peso n_2024 principal) de δ̃ escenario vs principal\n", fm(sp, 4),
      "\n## 3. Reajuste tibio K=5: ARI ponderado contra la entrega K=5 (pesos w de la entrega, celdas comunes)\n",
      "ARI_sin_reajustar = ajuste_K5 aplicado sin reajustar a los datos del escenario (piso de lo que mueven solo los datos); la diferencia con ARI_ponderado es lo que mueve el reajuste.\n",
      fm(ari_t, 4)]
for esc in S.ESCENARIOS:
    cr, rg, rg_s, orden = cruces[esc]
    md += [f"\n### Cruce de pesos · {esc} (% del peso w de la entrega de cada clase del escenario, por perfil principal)\n", md_t(cr.reset_index().rename(columns={"index": "clase del escenario"})),
           f"\n**Regla D-030 ({esc}): {'SÍ — cada clase tiene más de la mitad de su peso en un solo perfil principal' if rg['global_cumple'] else 'NO — al menos una clase no cumple'}.** "
           f"(Con los pesos w del propio escenario: {'SÍ' if rg_s['global_cumple'] else 'NO'}.)"]
md += ["\n## 4. Regla de mayoría por clase (D-030)\n", fm(reg, 2),
       "\n## 5. % del déficit por perfil (escenario vs principal; déficit positivo D-022)\n"]
for esc in S.ESCENARIOS:
    md += [f"\n**{esc}**\n", fm(defi[defi.escenario == esc].drop(columns="escenario"), 3)]
md += ["\n## 6. Observado vs esperado por perfil y elección (asignación principal; esperada principal q_gse vs con concurrencia q_gsek)\n",
       "Puntos de participación SV/(SV+NV), agregando las celdas del perfil en cada elección. efecto_calendario = esp_principal − esp_concurrencia.\n",
       fm(tab, 3),
       "\n## 7. Intermedias (2009, 2015, 2021) menos presidenciales (2012, 2018, 2024), puntos\n",
       "Media de (observada − esperada) en cada grupo de elecciones. `calendario_pts` = diferencia del patrón explicada al pasar de q_gse a q_gsek; `calendario_pct` su porcentaje del patrón principal.\n",
       fm(imp, 3),
       "\n## 8. Brecha por escenario: φ por estrato y metadatos\n"]
for esc in S.ESCENARIOS:
    mt = res[esc]["meta"]
    md += [f"\n**{esc}**: filas panel {mt['filas_panel']:,}; con n>0 {mt['filas_n_pos']:,}; celdas {mt['celdas']:,}; objetivo {mt['celdas_objetivo']:,}; "
           f"votos faltantes {mt['votos_faltantes']:,.0f}; error de conservación {mt['error_conservacion']:.2e}"
           + (f"; filas con gubernatura = {mt['n_k1']:,}" if esc == "concurrencia" else "") + ".\n",
           fm(res[esc]["phi"][["sexo", "grupo", "phi", "estado", "n_celdas"]], 3)]
md += ["\n## 9. Tiempos de cómputo (s, primera corrida)\n", fm(pd.DataFrame({"paso": list(TIEMPOS), "segundos": [round(v) for v in TIEMPOS.values()]}), 0),
       f"\nTiempo total de esta corrida: {time.time() - T0:.0f} s."]
(SAL / "control.md").write_text("\n".join(md) + "\n", encoding="utf-8")
log("reporte escrito")
for t_ in (pob, sp, ari_t, defi, reg, imp):
    print(t_.round(4).to_string())
