"""Brecha de cada celda frente a lo esperado para su edad y sexo, y población objetivo (D-022).
Entrada: data/processed/panel_celda_eleccion.parquet
Salidas: data/processed/brecha_celda.parquet, reports/preparacion/brecha_esperada/
Uso: .venv/bin/python scripts/preparacion/brecha_esperada.py"""
import time
import numpy as np
import pandas as pd
from ine_perfiles import config as C
from ine_perfiles import brecha as B

T0 = time.time()
PROC = C.PROCESADOS
TAB = C.salidas(__file__)

COLS = ["edo", "seccion", "sexo", "grupo", "aelec", "sv", "nv", "n", "ln"]
panel = pd.read_parquet(PROC / "panel_celda_eleccion.parquet", columns=COLS)
panel["ln"] = panel["ln"].astype("float64")
n_filas = len(panel)

cel, phis, q_gse, pers = B.calcular(panel)

md = ["# Brecha frente a lo esperado por sexo y edad (D-022)", ""]


def tabla(df):
    f = lambda v: f"{v:.4g}" if isinstance(v, (float, np.floating)) else str(v)
    L = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    L += ["| " + " | ".join(f(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(L) + "\n"


# ---- cifras de control
md += ["## 1. Cifras de control", ""]
p = panel[panel.n > 0]
nac24 = 100 * p[p.aelec == 2024].sv.sum() / p[p.aelec == 2024].n.sum()
ref, tol = C.CIFRAS_CONTROL[2024]["nacional"]
md.append(f"- Tasa del panel 2024 = Σsv/Σn = **{nac24:.3f}%** (control {ref} ± {tol}): "
          f"{'OK' if abs(nac24 - ref) <= tol else 'FALLA'}.")
q = p.merge(q_gse, on=["sexo", "grupo", "aelec"])
q["e"] = q.n * q.q
s = q.groupby(["sexo", "grupo", "aelec"]).agg(O=("sv", "sum"), E=("e", "sum"))
err = float(((s.O - s.E).abs() / s.O).max())
md.append(f"- Σ O = Σ E por sexo × grupo × elección ({len(s)} combinaciones): error relativo máximo **{err:.2e}**.")
md.append(f"- Filas del panel: {n_filas:,}; con n>0: {len(p):,}. Celdas con alguna n>0: **{len(cel):,}** "
          f"(esperadas 983,708).")
fuera = int(((cel.q <= 0) | (cel.q >= 1)).sum())
md.append(f"- Celdas con q_c en {{0,1}} (degeneradas): {fuera}. Celdas con NaN en prob_bajo: "
          f"{int(cel.prob_bajo.isna().sum())}.")
md.append("")

# ---- phi
md += ["## 2. Precisión φ por estrato (beta-binomial con media conocida)", "",
       "φ grande = poca sobredispersión (la celda se acerca a lo esperado solo por azar binomial); "
       "φ pequeña = mucha. Convergencia: `estado` ('mle' = óptimo interior), `convergio` = "
       "reporte del optimizador.", ""]
t = phis["total"][["sexo", "grupo", "n_celdas", "phi", "estado", "convergio"]].rename(
    columns={"phi": "phi_total"})
for k, nom in (("p0921", "phi_0921"), ("p24", "phi_24")):
    x = phis[k][["sexo", "grupo", "phi", "estado", "convergio"]].rename(
        columns={"phi": nom, "estado": "estado_" + nom, "convergio": "conv_" + nom})
    t = t.merge(x, on=["sexo", "grupo"], how="left")
md.append(tabla(t))
t.to_csv(TAB / "phi_estratos.csv", index=False)
todos = pd.concat([phis[k] for k in phis])
md.append(f"- Estratos × periodo con φ=∞ (sin sobredispersión): "
          f"{int(np.isinf(todos.phi).sum())}; en borde inferior: {int((todos.estado=='borde_inferior').sum())}; "
          f"sin convergencia reportada: {int((~todos.convergio.fillna(True).astype(bool)).sum())}.")
md.append("")

# ---- verificación celdas grandes
md += ["## 3. Verificación: en celdas grandes p̃ ≈ O/N", ""]
corte = cel.N.quantile(0.9)
gr = cel[cel.N >= corte]
d = (gr.p_tilde - gr.O / gr.N).abs()
md.append(f"- Decil superior de N (N ≥ {corte:,.0f}; {len(gr):,} celdas): |p̃ − O/N| máximo = "
          f"**{d.max():.4f}**, mediana = {d.median():.5f}.")
md.append("")

# ---- población objetivo
obj = cel[cel.objetivo]
ln = cel["ln_2024"].fillna(0)
ln_tot = ln.sum()
md += ["## 4. Población objetivo (prob_bajo > 1/2)", "",
       f"- Celdas: **{len(obj):,}** ({100*len(obj)/len(cel):.1f}% de {len(cel):,}).",
       f"- Lista nominal 2024 en celdas objetivo: {ln[cel.objetivo].sum():,.0f} "
       f"(**{100*ln[cel.objetivo].sum()/ln_tot:.1f}%** de {ln_tot:,.0f}).",
       f"- Déficit total (Σ max(déficit,0), votos por elección): **{cel.deficit.clip(lower=0).sum():,.0f}**; "
       f"neto Σ déficit: {cel.deficit.sum():,.0f}.",
       f"- Déficit crudo 2024: Σ positivo = **{cel.deficit_2024_crudo.clip(lower=0).sum():,.0f}**, "
       f"neto = {cel.deficit_2024_crudo.sum():,.0f}.", ""]


def mediana_pond(x, w):
    o = np.argsort(x.to_numpy()); xs = x.to_numpy()[o]; cw = np.cumsum(w.to_numpy()[o])
    return float(xs[np.searchsorted(cw, cw[-1] / 2)])


filas = []
for (s_, g_), x in cel.groupby(level=["sexo", "grupo"]):
    o = x[x.objetivo]
    filas.append(dict(sexo=s_, grupo=g_, celdas=len(x), celdas_obj=len(o),
                      pct_celdas_obj=100 * len(o) / len(x),
                      pct_LN_obj=100 * o.ln_2024.fillna(0).sum() / max(x.ln_2024.fillna(0).sum(), 1),
                      delta_mediana_pond=mediana_pond(o.delta, o.N) if len(o) else np.nan,
                      deficit_pos=x.deficit.clip(lower=0).sum()))
des = pd.DataFrame(filas)
md.append(tabla(des)); des.to_csv(TAB / "desglose_sexo_grupo.csv", index=False)

# ---- deciles prob_bajo
md += ["## 5. Distribución de prob_bajo", ""]
dec = cel.prob_bajo.quantile(np.linspace(0, 1, 11))
md.append(tabla(pd.DataFrame({"cuantil": [f"{100*i//10}%" for i in range(11)],
                              "prob_bajo": dec.values})))
for lo, hi in ((0.5, 0.6), (0.6, 0.8), (0.8, 0.95), (0.95, 1.0001)):
    k = int(((cel.prob_bajo > lo) & (cel.prob_bajo <= hi)).sum())
    md.append(f"- ({lo}, {min(hi,1)}]: {k:,} celdas ({100*k/len(cel):.1f}%)")
md.append("")

# ---- persistencia
md += ["## 6. Persistencia (D-022)", "",
       f"- Celdas con ambos periodos: {pers['celdas_ambas']:,}; objetivo 2009–21 entre ellas: {pers['celdas_objetivo']:,}.",
       f"- Spearman ponderada por n_2024 entre δ̃(2009–21) y δ̃(2024): **{pers['spearman']:.3f}**.",
       f"- Fracción (ponderada por n_2024) de la población objetivo 2009–21 con prob_bajo_24 > 1/2: "
       f"**{pers['frac_objetivo_sigue']:.3f}**, frente a **{pers['frac_todas']:.3f}** en todas las celdas.", ""]
lectura = (f"el orden de la brecha se conserva (Spearman {pers['spearman']:.2f}) y la población objetivo "
           f"2009–21 sigue por debajo en 2024 con frecuencia {pers['frac_objetivo_sigue']:.2f} frente a "
           f"{pers['frac_todas']:.2f} del total de celdas.")
md.append(f"Lectura (descriptiva, sin umbral de decisión): {lectura}")
md.append("")

# ---- salida
f32 = [c for c in cel.columns if c not in ("O", "E", "N", "O_0921", "E_0921", "N_0921",
                                           "O_24", "E_24", "N_24", "objetivo", "objetivo_0921",
                                           "objetivo_24", "m")]
out = cel.copy()
for c in f32:
    out[c] = out[c].astype("float32")
out["m"] = out.m.astype("int8")
out.reset_index().to_parquet(PROC / "brecha_celda.parquet", index=False)

t_tot = time.time() - T0
md += ["## 7. Cómo se corre", "", "`.venv/bin/python scripts/preparacion/brecha_esperada.py` "
       f"(tiempo de ejecución: {t_tot:.0f} s). Idempotente. Salida: `data/processed/brecha_celda.parquet`, "
       "tablas en `reports/preparacion/brecha_esperada/`.", ""]
(TAB / "control.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
