"""Selección del número de perfiles: mezcla de clases latentes sobre la población objetivo (D-024, D-029).

Etapas: (A) PCA ponderado del contexto y análisis paralelo de Horn; (B) ajuste con K = 1..K_MAX_FOCAL (ICL, BIC);
(C) estabilidad por bootstrap de secciones (D-017) en el K de menor ICL y en K=4; (D) prueba contra el azar;
(E) perfiles y reporte. Los ajustes quedan en la caché data/interim/seleccion_numero_perfiles/, que usan los
demás scripts de perfiles.
Uso: .venv/bin/python scripts/perfiles/seleccion_numero_perfiles.py [--rehacer] [--nulo-max-grande=N]
Con --nulo-max-grande=N la prueba contra el azar del K de menor ICL usa solo N permutaciones (cada una tarda más
de una hora); el reporte lo declara. La entrega se corrió con N = 4.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"

import pickle
import sys
import time
from multiprocessing import get_context

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ine_perfiles import config as C
from ine_perfiles import descriptores as D
from ine_perfiles import estabilidad as EST
from ine_perfiles import mezcla_mixta as MM
from ine_perfiles import seleccion as S
from ine_perfiles.seleccion import CATS, log, md_tabla, perfiles

S.REHACER = "--rehacer" in sys.argv
NULO_MAX_GRANDE = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--nulo-max-grande=")), None)
S.INT = INT = C.cache("seleccion_numero_perfiles")
SAL = C.salidas(__file__)
K_COMPARA = 4                    # referencia de cuatro perfiles (D-029), se evalúa siempre
T0 = time.time()


def main():
    log("A. preparacion, PCA, Horn")
    P = S.cache("pca.pkl", S.preparar)
    DAT, x, etiquetas, nombres_cont, n_cero = S.construir(P)
    S.DAT = DAT                      # antes de crear los procesos trabajadores
    log(f"   celdas={DAT.n}  w=0: {n_cero}  componentes retenidos={P['r']}  Horn R={P['horn']['R']}")

    ctx = get_context("fork")
    pool = ctx.Pool(S.N_PROC)

    # ---------------- B. seleccion de K
    log("B. seleccion de K")
    Ks = list(range(1, C.K_MAX_FOCAL + 1))
    ajustes = {}
    pend = []
    for K in Ks:
        ruta = INT / f"ajuste_K{K}.pkl"
        if ruta.exists() and not S.REHACER:
            with open(ruta, "rb") as fh:
                ajustes[K] = pickle.load(fh)
        else:
            pend.append(K)
    if pend:
        for K, mod, ll, info in pool.imap_unordered(S.tarea_ajuste, sorted(pend, reverse=True)):
            ajustes[K] = (mod, ll, info)
            with open(INT / f"ajuste_K{K}.pkl", "wb") as fh:
                pickle.dump(ajustes[K], fh)
            log(f"   K={K}: logL={ll:.1f} reinicios={info['reinicios']} rep={info['repeticiones']} t={info['segundos']:.0f}s")
    filasK, fit = [], {}
    for K in Ks:
        mod, ll, info = ajustes[K]
        R, ll2 = MM.estep(DAT, mod)
        a = MM.Ajuste(mod, ll2, R, 0, True, 0.0)
        cr = MM.criterios(a, DAT)
        cr.update(reinicios=info["reinicios"], repeticiones=info["repeticiones"], repetido=info["repetido"],
                  no_convergio=info["no_convergio"], pisos=info["pisos"], seg=info["segundos"])
        filasK.append(cr)
        fit[K] = a
    tK = pd.DataFrame(filasK)
    tK.to_csv(SAL / "seleccion_K.csv", index=False)
    K_icl = int(tK.loc[tK["ICL"].idxmin(), "K"])
    K_bic = int(tK.loc[tK["BIC"].idxmin(), "K"])
    log(f"   K(ICL)={K_icl}  K(BIC)={K_bic}")
    K_star = K_icl

    # ---------------- C. estabilidad
    log("C. estabilidad")
    edo_c = x["edo"].to_numpy()
    orden, inicio, largo, edo_sec = EST.indice_secciones(edo_c, x["seccion"].to_numpy())
    S.BOOT.update(edo_sec=edo_sec, orden=orden, inicio=inicio, largo=largo, idx=None)
    pool.close(); pool.join()
    pool = ctx.Pool(S.N_PROC)
    Ks_est = [K_star] + ([K_COMPARA] if K_star != K_COMPARA else [])
    est = {}
    for K in Ks_est:
        mapa = fit[K].R.argmax(axis=1)
        est[K] = S.estabilidad(K, fit[K].modelo, mapa, pool)
    # ---------------- D. prueba contra el azar
    log("D. prueba contra el azar")
    nulo = {K: S.prueba_azar(K, pool, None if K == K_COMPARA else NULO_MAX_GRANDE) for K in Ks_est}
    pool.close(); pool.join()
    log("E. perfiles y reporte")
    reportar(P, DAT, x, etiquetas, nombres_cont, n_cero, tK, K_icl, K_bic, fit, est, nulo)



# ============================================================================ E. perfiles y reporte
def reportar(P, dat, x, etiquetas, nombres_cont, n_cero, tK, K_icl, K_bic, fit, est, nulo):
    from scipy import stats
    horn = P["horn"]
    r = P["r"]
    cols = P["cols"]
    carg = pd.DataFrame(P["vec"][:, :r], index=cols, columns=[f"pc{j + 1}" for j in range(r)])
    carg.round(4).to_csv(SAL / "cargas_pca.csv")
    pd.DataFrame(dict(componente=np.arange(1, len(P["val"]) + 1), observado=P["val"], media_permutada=horn["media"],
                      ee_mc=horn["ee"], var_explicada=P["var_exp"])).to_csv(SAL / "horn.csv", index=False)
    # --- perfiles del K elegido
    K = K_icl
    prof, comp, pos, mapa, pmax = perfiles(K, fit[K], x, etiquetas, P)
    prof.to_csv(SAL / "perfiles.csv", index=False)
    comp.to_csv(SAL / "perfiles_composicion.csv", index=False)
    # --- estabilidad
    L = []
    resumen_est = {}
    for Kk, (res, tope) in est.items():
        J = np.array([q["jt"] for q in res])
        ee = EST.ee_monte_carlo(J)
        frio = [q for q in res if "jf" in q]
        Jt = np.array([q["jt"] for q in frio]); Jf = np.array([q["jf"] for q in frio])
        dif = Jt - Jf
        eed = dif.std(axis=0, ddof=1) / np.sqrt(len(dif))
        tc = stats.t.ppf(0.975, len(dif) - 1)
        # perfil (orden por deficit) de cada clase de este K
        _, _, posk, _, _ = perfiles(Kk, fit[Kk], x, etiquetas, P)
        t = pd.DataFrame(dict(clase=np.arange(Kk), perfil=[posk[k] for k in range(Kk)], jaccard_medio=J.mean(axis=0),
                              ee_mc=ee, lectura_fpc=[EST.lectura_fpc(v) for v in J.mean(axis=0)],
                              jaccard_frio_medio=Jf.mean(axis=0), dif_tibio_menos_frio=dif.mean(axis=0), ee_dif=eed,
                              frio_domina=np.abs(dif.mean(axis=0)) > tc * eed)).sort_values("perfil")
        t.to_csv(SAL / f"jaccard_K{Kk}.csv", index=False)
        resumen_est[Kk] = dict(t=t, B=len(res), tope=tope, nf=len(frio), tc=tc,
                               it_t=np.mean([q["it_t"] for q in res]), seg_t=np.mean([q["seg_t"] for q in res]),
                               seg_f=np.mean([q["seg_f"] for q in frio]), no_conv=sum(not q["conv_t"] for q in res),
                               dlogL=np.mean([q["logL_t"] - q["logL_f"] for q in frio]))
    # --- azar
    azar = {}
    for Kk, sal_n in nulo.items():
        G = np.array([q["G"] for q in sal_n])
        Gobs = fit[Kk].logL - fit[1].logL
        azar[Kk] = dict(Gobs=Gobs, min=G.min(), med=np.median(G), max=G.max(), n_ge=int((G >= Gobs).sum()),
                        p=(1 + (G >= Gobs).sum()) / (len(G) + 1), B=len(G), G=G,
                        norep=sum(not q["rep"] for q in sal_n), seg=np.mean([q["seg"] for q in sal_n]))
    pd.DataFrame([{k: v for k, v in dict(K=Kk, **a).items() if k != "G"} for Kk, a in azar.items()]).to_csv(SAL / "azar.csv", index=False)
    # --- figuras
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    ax[0].plot(tK["K"], tK["BIC"] - tK["BIC"].min(), "o-", label="BIC"); ax[0].plot(tK["K"], tK["ICL"] - tK["ICL"].min(), "s-", label="ICL")
    ax[0].set_xlabel("K"); ax[0].set_ylabel("criterio - mínimo"); ax[0].set_yscale("symlog"); ax[0].legend(); ax[0].set_title("Selección de K")
    for Kk, d in resumen_est.items():
        ax[1].plot(d["t"]["perfil"], d["t"]["jaccard_medio"], "o-", label=f"K={Kk}")
    for u in (0.5, 0.6, 0.75, 0.85):
        ax[1].axhline(u, color="gray", lw=.5, ls=":")
    ax[1].set_xlabel("perfil (orden por déficit)"); ax[1].set_ylabel("Jaccard medio"); ax[1].set_title("Estabilidad"); ax[1].legend()
    a = azar[K]
    ax[2].hist(a["G"], bins=10, color="C0", alpha=.7); ax[2].axvline(a["Gobs"], color="C3"); ax[2].set_title(f"Ganancia logL, K={K}: nulo vs observado")
    ax[2].set_xlabel("G = logL_K - logL_1")
    fig.tight_layout(); fig.savefig(SAL / "resumen.png", dpi=110); plt.close(fig)
    # --- reporte
    t_sel = tK[["K", "logL", "n_param", "BIC", "ICL", "entropia", "reinicios", "repeticiones", "no_convergio", "pisos", "seg"]].copy()
    t_sel["K"] = t_sel["K"].astype(int)
    bic_min_K = K_bic
    bic_no_se_detiene = (bic_min_K == tK["K"].max())
    L = []
    A = L.append
    A("# Selección del número de perfiles: mezcla de clases latentes sobre la población objetivo (D-024, D-029)\n")
    A("Los perfiles representan **votos faltantes** (pesos w = déficit), no personas. El contexto describe la sección, no a las personas (D-010).\n")
    A(f"- Celdas objetivo: **{dat.n:,}**; con w = 0 (déficit ≤ 0): **{n_cero}**. Pesos normalizados a Σw = {dat.n:,}.")
    A(f"- Categorías: " + "; ".join(f"{c} = {etiquetas[c]}" for c in CATS) + f". NaN como categoría propia: {'sí' if any('NaN' in map(str, etiquetas[c]) for c in CATS) else 'no existe'}.")
    A(f"- Continuas: {', '.join(nombres_cont)}. Faltantes de δ̃ en la población objetivo: {int(np.isnan(dat.X[:,0]).sum())}.\n")
    A("## 1. PCA del contexto y análisis paralelo de Horn\n")
    A(f"- Secciones: {P['n_sec']:,}; completas (usadas para estimar el PCA): {int(P['comp'].sum()):,}; con algún NaN (proyectadas con valores estandarizados faltantes = 0): **{P['n_incompletas']:,}**.")
    A(f"- Estandarización con media y desviación ponderadas por LN 2024; PCA = vectores propios de la covarianza ponderada (matriz de correlación).")
    A(f"- Horn: {horn['R']} permutaciones (bloques de 20 hasta que 2×EE < |observado − media permutada| en todos los componentes, tope 1000; tope alcanzado: {'sí' if horn['tope'] else 'no'}). EE Monte Carlo máximo de la media permutada: {horn['ee'].max():.4f}.")
    A(f"- **Componentes retenidos: {r}** (valor propio observado > media permutada).\n")
    h = pd.DataFrame(dict(comp=np.arange(1, min(len(P['val']), r + 4) + 1)))
    n_h = len(h)
    h["observado"] = P["val"][:n_h]; h["media_permutada"] = horn["media"][:n_h]; h["EE_MC"] = horn["ee"][:n_h]; h["var_explicada_%"] = 100 * P["var_exp"][:n_h]
    A(md_tabla(h, {**{c: "{:.4f}" for c in h.columns if c != "comp"}, "comp": "{:d}"}))
    A(f"\nVarianza explicada acumulada por los {r} retenidos: **{100 * P['var_exp'][:r].sum():.1f}%**.\n")
    A("Cargas (columnas originales estandarizadas):\n")
    A(md_tabla(carg.round(3).reset_index().rename(columns={"index": "variable"})))
    A("\n## 2. Selección de K (D-029)\n")
    A(md_tabla(t_sel, {"K": "{:d}", "n_param": "{:d}", "logL": "{:.0f}", "BIC": "{:.0f}", "ICL": "{:.0f}", "entropia": "{:.0f}", "seg": "{:.0f}", "reinicios": "{:d}", "repeticiones": "{:d}", "no_convergio": "{:d}", "pisos": "{:d}"}))
    A(f"\n- **K elegido (mínimo ICL, criterio i): {K_icl}.** Mínimo de BIC: K = {K_bic}. El BIC {'**no se detiene** dentro del rango (su mínimo está en el tope K = ' + str(int(tK['K'].max())) + ')' if bic_no_se_detiene else 'se detiene antes del tope del rango'}.")
    A(f"- Reinicios cuyo mejor óptimo no se repitió (< 2 reinicios a < 1 nat): K = {[int(k) for k in tK.loc[~tK['repetido'], 'K']] or 'ninguno'}. Piso de varianza activado (suma en la M-step final): {int(tK['pisos'].sum())}.\n")
    A("## 3. Estabilidad (bootstrap de secciones estratificado por estado, D-017)\n")
    for Kk, d in resumen_est.items():
        A(f"### K = {Kk}\n")
        A(f"- B = {d['B']} réplicas (mínimo {S.B_MIN}, EE ≤ {S.EE_MAX}, tope {S.B_TOPE}); tope alcanzado: {'sí' if d['tope'] else 'no'}. Réplicas tibias a tol 1e-10: {d['it_t']:.0f} iteraciones en promedio ({d['seg_t']:.0f} s); sin convergir: {d['no_conv']}.")
        A(f"- Control en frío: {d['nf']} réplicas (k-means++ + refinado), {d['seg_f']:.0f} s en promedio; t crítico = {d['tc']:.2f}; diferencia media de logL tibio − frío = {d['dlogL']:.2f} nats.\n")
        tt = d["t"][["perfil", "clase", "jaccard_medio", "ee_mc", "lectura_fpc", "jaccard_frio_medio", "dif_tibio_menos_frio", "ee_dif", "frio_domina"]].copy()
        tt["frio_domina"] = tt["frio_domina"].map({True: "sí", False: "no"})
        A(md_tabla(tt, {"perfil": "{:d}", "clase": "{:d}", "jaccard_medio": "{:.3f}", "ee_mc": "{:.4f}", "jaccard_frio_medio": "{:.3f}", "dif_tibio_menos_frio": "{:+.4f}", "ee_dif": "{:.4f}"}))
        A("")
    A("## 4. Prueba contra el azar (permutación de cada variable por separado, w con su celda)\n")
    for Kk, a in azar.items():
        A(f"- **K = {Kk}**: G_obs = {a['Gobs']:.1f} nats; G_nulo (B = {a['B']}): mín {a['min']:.1f}, mediana {a['med']:.1f}, máx {a['max']:.1f}; permutaciones con G ≥ G_obs: {a['n_ge']}; **p = {a['p']:.3f}** (p mínimo posible = {1 / (a['B'] + 1):.3f}). Ajustes nulos cuyo óptimo no se repitió: {a['norep']}. {a['seg']:.0f} s por permutación.")
    if NULO_MAX_GRANDE is not None:
        A(f"\n**Aviso de costo:** para K = {K_icl} cada permutación costó ~{azar[K_icl]['seg'] / 60:.0f} min (4 procesos en paralelo); se corrieron solo {azar[K_icl]['B']} de las {C.B_NULO} previstas en D-029 (`--nulo-max-grande`). Con B = {azar[K_icl]['B']} el p mínimo posible es {1 / (azar[K_icl]['B'] + 1):.2f}; para llegar a 0.05 hay que completar las {C.B_NULO} (la caché es reanudable: volver a correr sin la opción).")
    A("\n## 5. Perfiles (K = %d, ordenados por %% del déficit)\n" % K)
    A("Ordenamiento: Σ responsabilidades × w de la clase (suma ponderada, no el MAP). Composición ponderada por responsabilidad × w; razón × = % en el perfil / % en toda la población objetivo (ponderada por w). Medianas del contexto ponderadas por responsabilidad × w (describen la sección, D-010).\n")
    tp = prof[["perfil", "pct_deficit", "celdas", "ln_2024_miles", "delta_medio", "deficit_crudo_2024_pos", "pct_crudo_2024", "pmax_media", "pct_pmax_ge_09"]].copy()
    tp.columns = ["perfil", "% déficit", "celdas", "LN 2024 (miles)", "δ̃ medio", "déficit crudo 2024 (+)", "% crudo 2024", "prob máx media", "% prob máx ≥ 0.9"]
    A(md_tabla(tp, {"perfil": "{:d}", "% déficit": "{:.1f}", "celdas": "{:,.0f}", "LN 2024 (miles)": "{:,.0f}", "δ̃ medio": "{:.3f}", "déficit crudo 2024 (+)": "{:,.0f}", "% crudo 2024": "{:.1f}", "prob máx media": "{:.3f}", "% prob máx ≥ 0.9": "{:.1f}"}))
    A("\nComposición (% del déficit del perfil, razón ×):\n")
    for c in CATS:
        cc = comp[comp["variable"] == c].copy()
        cc["celda"] = cc.apply(lambda q: f"{q['pct']:.0f}% ({q['razon']:.2f}×)", axis=1)
        pv = cc.pivot(index="perfil", columns="categoria", values="celda").reset_index()
        pv.columns = [str(z) for z in pv.columns]
        A(f"**{c}**\n")
        A(md_tabla(pv))
        A("")
    A("Medianas ponderadas del contexto de la sección (valores originales):\n")
    cm = prof[["perfil"] + ["med_" + c for c in D.COLS_CONTEXTO]].copy()
    cm.columns = ["perfil"] + D.COLS_CONTEXTO
    A(md_tabla(cm, {**{"perfil": "{:d}"}, **{c: "{:.3g}" for c in D.COLS_CONTEXTO}}))
    cpu_aj = tK["seg"].sum()
    cpu_bt = {Kk: sum(q["seg_t"] + q.get("seg_f", 0) for q in res) for Kk, (res, _) in est.items()}
    cpu_nu = {Kk: sum(q["seg"] for q in v) for Kk, v in nulo.items()}
    A("\n## 6. Tiempos\n")
    A(f"Tiempo de proceso sumado (segundos-CPU de trabajadores; con 4 procesos el reloj es ~1/4, con la máquina compartida): selección de K {cpu_aj / 3600:.1f} h; bootstrap " + "; ".join(f"K={Kk} {v / 3600:.1f} h" for Kk, v in cpu_bt.items()) + "; permutaciones " + "; ".join(f"K={Kk} {v / 3600:.1f} h (B={len(nulo[Kk])})" for Kk, v in cpu_nu.items()) + ". Esta ejecución del script solo lee la caché de `data/interim/seleccion_numero_perfiles/` y arma el reporte.\n")
    previo = ""
    if (SAL / "control.md").exists():                # la lectura escrita a mano se conserva entre corridas
        t = (SAL / "control.md").read_text(encoding="utf-8")
        if "## 7. Lectura" in t:
            previo = t.split("## 7. Lectura", 1)[1].strip()
    A("## 7. Lectura\n\n" + (previo if previo and "Se completa" not in previo else "(Se completa tras revisar las cifras.)") + "\n")
    (SAL / "control.md").write_text("\n".join(L), encoding="utf-8")
    log("reporte escrito")


if __name__ == "__main__":
    main()
