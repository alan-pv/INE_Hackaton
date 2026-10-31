"""Grupos de edad estimados donde la curva nacional de participación cambia de pendiente (D-007).
Salidas: data/processed/cortes_edad.json, reports/preparacion/grupos_edad/ (control.md y curvas de edad)
Uso: .venv/bin/python scripts/preparacion/grupos_edad.py"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ine_perfiles import config as C
from ine_perfiles.ingesta import conectar
from ine_perfiles import edades as E

RAIZ = C.RAIZ
OUT_JSON = RAIZ / "data" / "processed" / "cortes_edad.json"
FIG = C.salidas(__file__)
OUT_MD = FIG / "control.md"
for d in (OUT_JSON.parent,):
    d.mkdir(parents=True, exist_ok=True)

con = conectar()
ANIOS = C.ANIOS


def cargar(sexos):
    cur, exc = [], {}
    for a in ANIOS:
        x, n, y, ex = E.curva_por_edad(con, a, sexos)
        cur.append((x, n, y)); exc[a] = ex
    return cur, exc


def seleccionar(cur):
    cv = E.cv_loeo(cur)
    k, kmin = E.regla_1se(cv)
    # cortes por elección (curva centrada) y mediana por posición
    por_el = {}
    for a, (x, n, y) in zip(ANIOS, cur):
        por_el[a], _ = E.buscar_cortes(x, E.centrar(y, n), n, k)
    mat = np.array([por_el[a] for a in ANIOS]) if k else np.zeros((6, 0))
    med = [int(round(float(np.median(mat[:, j])))) for j in range(k)]
    xp, wp, yp = E.curva_promedio([(x, n, E.centrar(y, n)) for x, n, y in cur])
    prom, _ = E.buscar_cortes(xp, yp, wp, k)
    return dict(cv=cv, k=k, kmin=kmin, por_el=por_el, mat=mat, med=med, prom=prom, curva_prom=(xp, wp, yp))


cur, exc = cargar((0, 1))
R = seleccionar(cur)
k, cortes = R["k"], R["med"]
grupos = E.definir_grupos(cortes)
print("k", k, "cortes", cortes, "prom", R["prom"])

# sensibilidad por sexo
SEX = {}
for nombre, s in (("hombres", (0,)), ("mujeres", (1,))):
    c2, _ = cargar(s)
    r2 = seleccionar(c2)
    SEX[nombre] = r2
    print(nombre, r2["k"], r2["med"])


# --- sensibilidad k-1 / k+1 (cortes por elección, mediana)
def med_k(kk):
    po = {}
    for a, (x, n, y) in zip(ANIOS, cur):
        po[a], _ = E.buscar_cortes(x, E.centrar(y, n), n, kk)
    m = np.array([po[a] for a in ANIOS])
    return [int(round(float(np.median(m[:, j])))) for j in range(kk)], po
SENS_K = {}
for kk in (k - 1, k + 1):
    if kk >= 1:
        SENS_K[kk] = med_k(kk)[0]

# --- spline suavizado (lambda por GCV) sobre la curva promedio centrada
xp, wp, yp = R["curva_prom"]
sp, z1, z2 = E.puntos_spline(xp, yp, wp)
LIM_SPL = 100  # solo se interpretan cruces donde hay datos (n pequeño >100 años); ver reporte

# --- bootstrap por sección, 2024
B = 200  # por costo de cómputo; se reporta el error Monte Carlo de los percentiles
SEM_BOOT = 20261024
filas = con.execute("""SELECT edo, seccion, edad, sum(sv) sv, sum(sv+nv) n FROM ccpc
  WHERE aelec=2024 AND sexo IN (0,1) GROUP BY 1,2,3""").fetchnumpy()
llave = filas["edo"].astype(np.int64) * 10000 + filas["seccion"].astype(np.int64)
_, si = np.unique(llave, return_inverse=True)
ed_u, ei = np.unique(filas["edad"], return_inverse=True)
SV = np.zeros((si.max() + 1, ed_u.size)); NN = np.zeros_like(SV)
SV[si, ei] = filas["sv"]; NN[si, ei] = filas["n"]
print("bootstrap sobre", SV.shape[0], "secciones")
boot = E.bootstrap_secciones(SV, NN, ed_u.astype(float), k, R["por_el"][2024], B, SEM_BOOT)
IC = []
for j in range(k):
    lo, hi = np.percentile(boot[:, j], [2.5, 97.5])
    IC.append({"corte": cortes[j], "ic_2.5": float(lo), "ic_97.5": float(hi),
               "mc_se_2.5": E.error_mc_percentil(boot[:, j], 2.5), "mc_se_97.5": E.error_mc_percentil(boot[:, j], 97.5),
               "mediana_boot": float(np.median(boot[:, j]))})
print(IC)

# --- prueba edad vs cohorte: pendiente del corte contra el año de elección
anios = np.array(ANIOS, float)
EDAD_COH = []
for j in range(k):
    yj = R["mat"][:, j].astype(float)
    A = np.column_stack([np.ones(6), anios - anios.mean()])
    b, res, *_ = np.linalg.lstsq(A, yj, rcond=None)
    r = yj - A @ b
    se = np.sqrt(r @ r / 4 / np.sum((anios - anios.mean()) ** 2))
    EDAD_COH.append((j + 1, float(b[1]), float(se)))

# tamaños por grupo
def grupo_sql(grupos):
    partes = []
    for g in grupos:
        cond = f"edad>={g['edad_min']}" + (f" AND edad<={g['edad_max']}" if g["edad_max"] is not None else "")
        partes.append(f"WHEN {cond} THEN {g['id']}")
    return "CASE " + " ".join(partes) + " END"

gsql = grupo_sql(grupos)
tam = con.execute(f"""SELECT aelec, {gsql} AS g, sum(ln) ln, sum(sv+nv) n, sum(sv)*1.0/sum(sv+nv) p
  FROM ccpc WHERE sexo IN (0,1) GROUP BY 1,2 ORDER BY 1,2""").fetchall()
celdas = con.execute(f"""SELECT g, median(n), quantile_cont(n,0.1), quantile_cont(n,0.9), count(*) FROM (
  SELECT edo, seccion, sexo, {gsql} AS g, sum(sv+nv) n FROM ccpc WHERE aelec=2024 AND sexo IN (0,1)
  GROUP BY 1,2,3,4) GROUP BY g ORDER BY g""").fetchall()

# --- selección final por sexo (D-007): k por LOEO+1-SE en cada sexo, cortes comunes
if SEX["hombres"]["k"] != SEX["mujeres"]["k"]:
    raise SystemExit(f"k difiere entre sexos: H={SEX['hombres']['k']} M={SEX['mujeres']['k']}. Abortado.")
k_fin = SEX["hombres"]["k"]
cortes_fin = E.cortes_comunes(SEX["hombres"]["med"], SEX["mujeres"]["med"])
grupos_fin = E.definir_grupos(cortes_fin)
gsql_f = grupo_sql(grupos_fin)
tam_f = con.execute(f"""SELECT aelec, {gsql_f} AS g, sum(ln) ln, sum(sv+nv) n, sum(sv)*1.0/sum(sv+nv) p
  FROM ccpc WHERE sexo IN (0,1) GROUP BY 1,2 ORDER BY 1,2""").fetchall()
celdas_f = con.execute(f"""SELECT g, median(n), quantile_cont(n,0.1), quantile_cont(n,0.9), count(*) FROM (
  SELECT edo, seccion, sexo, {gsql_f} AS g, sum(sv+nv) n FROM ccpc WHERE aelec=2024 AND sexo IN (0,1)
  GROUP BY 1,2,3,4) GROUP BY g ORDER BY g""").fetchall()
LAND = sorted(set([v for v in z1 if v < 95] + [v for v in z2 if v < 95]))
print("FINAL", k_fin, cortes_fin, grupos_fin)

# JSON
cv_json = {str(kk): [v[0], v[1]] for kk, v in R["cv"].items()}
pooled = {
    "k": k, "cortes": cortes, "grupos": grupos, "cv": cv_json,
    "aviso": ("k=8 esta en la frontera del rango explorado (K_MAX=8): el CV pooled baja monotonamente y no hay k interior; "
              "la curva pooled mezcla dos formas (hombres/mujeres) y exige tramos extra."),
    "cortes_por_eleccion": {str(a): R["por_el"][a] for a in ANIOS},
    "cortes_curva_promedio": R["prom"],
    "ic_bootstrap_2024": IC, "bootstrap": {"B": B, "semilla": SEM_BOOT, "unidad": "secciones"},
    "sensibilidad_k": {str(kk): v for kk, v in SENS_K.items()},
    "spline": {"cruces_1a_derivada": z1, "cambios_signo_2a_derivada": z2}}
por_sexo = {n: {"k": r["k"], "k_cv_minimo": r["kmin"], "cortes": r["med"],
                "cv": {str(kk): [v[0], v[1]] for kk, v in r["cv"].items()},
                "cortes_por_eleccion": {str(a): r["por_el"][a] for a in ANIOS}} for n, r in SEX.items()}
seleccion = {"regla": ("k elegido por sexo con CV dejando fuera una eleccion + 1-SE; cortes por sexo = mediana por posicion "
                       "de los cortes por eleccion; cortes comunes = media por posicion de hombres y mujeres, redondeo half-up; "
                       "aborta si k difiere entre sexos"),
             "k": k_fin, "cortes": cortes_fin, "grupos": grupos_fin, "por_sexo": por_sexo}
json.dump({
    "k": k_fin, "cortes": cortes_fin, "grupos": grupos_fin,
    "seleccion_final": seleccion, "analisis_pooled": pooled,
    "convencion": "corte = primera edad del nuevo tramo; grupos [18,b1),[b1,b2),...,[bk,inf)",
    "metodo": ("Regresion lineal por tramos continua (hinge) sobre logit(SV/(SV+NV)) por edad simple, MCP con w=n, curva centrada "
               "por eleccion; k por LOEO + 1-SE por sexo; cortes comunes = media H/M half-up."),
    "decision": "D-007"}, open(OUT_JSON, "w"), ensure_ascii=False, indent=1)

# figuras
fig, axs = plt.subplots(2, 3, figsize=(15, 8), sharey=True)
for ax, a, (x, n, y) in zip(axs.ravel(), ANIOS, cur):
    yc = E.centrar(y, n)
    cs = R["por_el"][a]
    coef, _ = E.ajustar_fijos(x, yc, n, cs)
    ax.scatter(x, yc, s=np.clip(n / n.max() * 60, 2, 60), alpha=.5, color="#4C78A8")
    xx = np.linspace(x.min(), x.max(), 400)
    ax.plot(xx, E._base(xx, cs) @ coef, color="#E45756", lw=2)
    for c in cs: ax.axvline(c, color="gray", ls="--", lw=.8)
    ax.axvline(0, alpha=0); ax.set_title(f"{a}  cortes: {cs}"); ax.set_xlim(17, 100); ax.set_xlabel("Edad")
    ax.grid(alpha=.3)
axs[0, 0].set_ylabel("logit de participación (centrado)"); axs[1, 0].set_ylabel("logit de participación (centrado)")
fig.suptitle(f"Curva logit por edad y ajuste por tramos (k={k}); eje truncado a 100 años", y=1.0)
fig.tight_layout(); fig.savefig(FIG / "curva_edad_elecciones.png", dpi=150); plt.close(fig)

XMAX = 95  # recorte SOLO visual: edades >95 tienen n despreciable
PIE = "Eje x recortado a 18–95 años solo para visualización (n despreciable por encima); el ajuste usa todas las edades."
_fin = json.load(open(OUT_JSON))
cortes_f, grupos_f = _fin["cortes"], _fin["grupos"]


def sombrear(ax, cs, grs):
    lim = [18] + cs + [XMAX]
    for i, g in enumerate(grs):
        if i % 2 == 0:
            ax.axvspan(lim[i], lim[i + 1], color="gray", alpha=.12, lw=0)
        ax.text((lim[i] + lim[i + 1]) / 2, ax.get_ylim()[1], g["etiqueta"], ha="center", va="top", fontsize=9)
    for c in cs:
        ax.axvline(c, color="gray", ls="--", lw=.8)


xp, wp, yp = R["curva_prom"]
m = xp <= XMAX
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.scatter(xp[m], yp[m], s=np.clip(wp[m] / wp.max() * 80, 3, 80), alpha=.55, color="#4C78A8", label="Promedio 2009–2024 (tamaño ∝ n)")
coef, _ = E.ajustar_fijos(xp, yp, wp, cortes_f)
xx = np.linspace(xp.min(), XMAX, 400)
ax.plot(xx, E._base(xx, cortes_f) @ coef, color="#E45756", lw=2, label=f"Ajuste por tramos con cortes finales {cortes_f}")
ax.set_xlim(18, XMAX); ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1] + 0.25)
sombrear(ax, cortes_f, grupos_f)
ax.set_xlabel("Edad (años)"); ax.set_ylabel("logit de participación (centrado por elección)")
ax.set_title("Curva de participación por edad (promedio 2009–2024, centrada por elección) y grupos finales")
ax.legend(loc="lower right"); ax.grid(alpha=.3)
fig.text(0.01, 0.005, PIE, fontsize=8, ha="left")
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(FIG / "curva_edad_promedio.png", dpi=150); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
for ax, (nombre, col) in zip(axs, (("hombres", "#4C78A8"), ("mujeres", "#E45756"))):
    xs_, ws_, ys_ = SEX[nombre]["curva_prom"]
    cs = SEX[nombre]["med"]
    mm = xs_ <= XMAX
    ax.scatter(xs_[mm], ys_[mm], s=np.clip(ws_[mm] / ws_.max() * 80, 3, 80), alpha=.55, color=col)
    cf, _ = E.ajustar_fijos(xs_, ys_, ws_, cs)
    xg = np.linspace(xs_.min(), XMAX, 400)
    ax.plot(xg, E._base(xg, cs) @ cf, color="black", lw=1.8)
    for c in cs:
        ax.axvline(c, color=col, ls="--", lw=1)
    ax.set_xlim(18, XMAX)
    ax.set_title(f"{nombre.capitalize()}: cortes {cs}")
    ax.set_xlabel("Edad (años)"); ax.grid(alpha=.3)
axs[0].set_ylabel("logit de participación (centrado por elección)")
fig.suptitle("Curva de participación por edad y sexo (promedio 2009–2024, centrada por elección) y cortes por sexo")
fig.text(0.01, 0.005, PIE, fontsize=8, ha="left")
fig.tight_layout(rect=(0, 0.03, 1, 0.97)); fig.savefig(FIG / "curva_edad_por_sexo.png", dpi=150); plt.close(fig)

# reporte
L = []
w = L.append
w("# Grupos de edad (D-007)\n")
w("Generado por `scripts/preparacion/grupos_edad.py`. Unidad: edad simple, curva nacional (sexo 0/1), logit de SV/(SV+NV), pesos w = n.\n")
w("## Por qué centrar\nEl nivel de cada elección es efecto periodo (D-007): la participación oscila ~15 pp entre presidenciales e intermedias en todas las edades. Se resta a cada logit su media ponderada por n, de modo que los cortes describen la **forma** de la curva y no el año electoral. En el CV, en la elección dejada fuera se reestiman intercepto y pendientes (cortes fijos) y se mide el error cuadrático medio ponderado de la forma.\n")
w("## Edades excluidas (p en {0,1}, logit indefinido)\n")
for a in ANIOS:
    w(f"- {a}: {exc[a] if exc[a] else 'ninguna'}")
w("\n## Selección de k (CV dejando fuera una elección, regla 1-SE)\n")
w("| k | CV-error medio | SE |\n|---|---|---|")
for kk, v in R["cv"].items():
    w(f"| {kk} | {v[0]:.5f} | {v[1]:.5f} |")
w(f"\nk de error mínimo = {R['kmin']}; **k elegido (1-SE) = {k}**.\n")
if k == E.K_MAX:
    w(f"**Aviso:** el CV sigue bajando hasta el máximo explorado (K_MAX={E.K_MAX}); el k elegido está en la frontera del rango y la curva suave admite más segmentos. Ver crítica en el informe del implementador.\n")
w("## Cortes por elección (curva centrada, ajuste por elección)\n")
w("Convención: corte = primera edad del nuevo tramo.\n")
w("| Elección | " + " | ".join(f"c{j+1}" for j in range(k)) + " |\n|---|" + "---|" * k)
for a in ANIOS:
    w(f"| {a} | " + " | ".join(str(c) for c in R["por_el"][a]) + " |")
w("| **mediana** | " + " | ".join(f"**{c}**" for c in cortes) + " |")
w("| mín–máx | " + " | ".join(f"{int(R['mat'][:, j].min())}–{int(R['mat'][:, j].max())}" for j in range(k)) + " |")
w("| curva promedio 6 | " + " | ".join(str(c) for c in R["prom"]) + " |")
w("\n## Grupos del análisis pooled (k=8, NO es la selección final)\n")
w("| id | etiqueta | edad_min | edad_max |\n|---|---|---|---|")
for g in grupos:
    w(f"| {g['id']} | {g['etiqueta']} | {g['edad_min']} | {g['edad_max']} |")
w("\n## [pooled] LN, votantes efectivos (n=SV+NV) y participación por grupo y elección\n")
w("| Grupo | Elección | LN | n | Participación |\n|---|---|---|---|---|")
et = {g["id"]: g["etiqueta"] for g in grupos}
for a, g, ln, n, p in tam:
    w(f"| {et[g]} | {a} | {int(ln):,} | {int(n):,} | {p*100:.2f}% |")
w("\n## [pooled] Tamaño de celda sección × sexo × grupo, 2024 (n = SV+NV; celdas con n>0)\n")
w("| Grupo | Mediana | P10 | P90 | Celdas |\n|---|---|---|---|---|")
for g, m, p10, p90, nc in celdas:
    w(f"| {et[g]} | {m:.0f} | {p10:.0f} | {p90:.0f} | {nc:,} |")

w("\n## Intervalos de confianza (bootstrap por sección, 2024)\n")
w(f"Remuestreo de secciones (70k, con reemplazo) B={B} (elegido por costo de cómputo), semilla {SEM_BOOT}; se reajustan los k cortes en cada réplica (semilla de inicio: ajuste puntual 2024). El error Monte Carlo es el EE de cada percentil estimado a partir de las B réplicas.\n")
w("| Corte | Mediana final | Ajuste 2024 | IC 95% percentil | EE-MC p2.5 / p97.5 |\n|---|---|---|---|---|")
for j, d in enumerate(IC):
    w(f"| c{j+1} | {d['corte']} | {R['por_el'][2024][j]} | {d['ic_2.5']:.1f}–{d['ic_97.5']:.1f} | {d['mc_se_2.5']:.2f} / {d['mc_se_97.5']:.2f} |")
w("\n## Contraste con spline de suavizado (lambda por GCV)\n")
w("Spline cúbico ponderado (w=n) sobre la curva promedio centrada, `scipy.interpolate.make_smoothing_spline` con lambda por validación cruzada generalizada. Edades donde la 1a derivada cruza 0 (extremos de la curva) y donde la 2a derivada cambia de signo (inflexiones):\n")
w(f"- 1a derivada = 0: {[round(v,1) for v in z1]}")
w(f"- 2a derivada cambia de signo: {[round(v,1) for v in z2]}")
w("- Cruces con edad > 95 caen donde n es mínimo y no son interpretables.\n")
w("\n## Sensibilidad al número de cortes\n")
for kk, cs in sorted(SENS_K.items()):
    w(f"- k={kk}: cortes {cs}; grupos: " + ", ".join(g['etiqueta'] for g in E.definir_grupos(cs)))
w(f"- k={k} (elegido): cortes {cortes}; grupos: " + ", ".join(g['etiqueta'] for g in grupos))
w("\n## ¿Efecto de edad o de cohorte?\n")
w("Si un corte es un efecto de EDAD, debe quedarse en la misma edad aunque pasen 3–15 años entre elecciones (pendiente 0 años/año). Si fuera de COHORTE, se desplazaría +3 años por elección (pendiente +1 año/año). Pendiente de OLS del corte contra el año (6 elecciones, 2009–2024), con su EE:\n")
w("| Corte | Pendiente (años de edad por año calendario) | EE | Desplazamiento 2009→2024 (años) |\n|---|---|---|---|")
for j, b, se in EDAD_COH:
    w(f"| c{j} | {b:+.3f} | {se:.3f} | {R['mat'][-1, j-1]-R['mat'][0, j-1]:+d} |")
w("\n## Sensibilidad por sexo\n")
for nombre, r in SEX.items():
    w(f"### {nombre.capitalize()}: k elegido = {r['k']} (k mín = {r['kmin']}), cortes (mediana) = {r['med']}")
    w("CV: " + "; ".join(f"k={kk}: {v[0]:.5f}±{v[1]:.5f}" for kk, v in r["cv"].items()))
    w("Por elección: " + "; ".join(f"{a}: {r['por_el'][a]}" for a in ANIOS) + "\n")
w(f"Ambos sexos: k = {k}, cortes = {cortes}\n")

w("\n# SELECCIÓN FINAL (por sexo)\n")
w("**Regla:** las celdas de D-009 son por sexo, así que k se elige por sexo (LOEO + 1-SE). La curva pooled mezcla dos formas distintas (hombres y mujeres tienen calendarios de vida diferentes) y exige tramos extra: es un artefacto de mezcla, y explica que el CV pooled no encuentre k interior (k=8, frontera). Por sexo, el CV sí tiene mínimo interior-estable en k=6 en ambos. Cortes comunes = media por posición de los cortes de hombres y mujeres, redondeo half-up (convención: corte = primera edad del nuevo tramo). Si k difiere entre sexos el script aborta.\n")
w(f"- Hombres (k={SEX['hombres']['k']}): {SEX['hombres']['med']}")
w(f"- Mujeres (k={SEX['mujeres']['k']}): {SEX['mujeres']['med']}")
w(f"- **Cortes comunes (k={k_fin}): {cortes_fin}**")
w("- Grupos: " + ", ".join(g['etiqueta'] for g in grupos_fin) + "\n")
w("## Contraste con landmarks del spline y con IC bootstrap 2024\n")
w("Landmarks (spline GCV, curva promedio, edades <95): " + ", ".join(f"{v:.1f}" for v in LAND) + " (mínimo/máximo = 1a derivada nula; inflexiones = 2a derivada cambia de signo). El IC bootstrap es el del corte del mismo número de orden del análisis pooled k=8 (no es el mismo modelo; se muestra la compatibilidad con cualquier IC).\n")
w("| Corte común | Landmark más cercano | Distancia (años) | Dentro de algún IC 2024 pooled |\n|---|---|---|---|")
for c in cortes_fin:
    lm = min(LAND, key=lambda v: abs(v - c))
    dentro = [f"c{j+1}[{d['ic_2.5']:.0f}–{d['ic_97.5']:.0f}]" for j, d in enumerate(IC) if d['ic_2.5'] <= c <= d['ic_97.5']]
    w(f"| {c} | {lm:.1f} | {abs(lm-c):.1f} | {', '.join(dentro) if dentro else 'ninguno'} |")
w("\n## Participación 2024 por grupo final y tamaño de celda sección × sexo\n")
et_f = {g["id"]: g["etiqueta"] for g in grupos_fin}
p24 = {g: (ln, n, p) for a, g, ln, n, p in tam_f if a == 2024}
w("| Grupo | LN 2024 | n 2024 | Participación 2024 | Mediana n por celda | P10 | P90 | Celdas |\n|---|---|---|---|---|---|---|---|")
for g, m, p10, p90, nc in celdas_f:
    ln, n, p = p24[g]
    w(f"| {et_f[g]} | {int(ln):,} | {int(n):,} | {p*100:.2f}% | {m:.0f} | {p10:.0f} | {p90:.0f} | {nc:,} |")
w("\n### Participación por grupo final y elección\n")
w("| Grupo | " + " | ".join(str(a) for a in ANIOS) + " |\n|---|" + "---|" * len(ANIOS))
for g in sorted(et_f):
    w(f"| {et_f[g]} | " + " | ".join(f"{[t for t in tam_f if t[0]==a and t[1]==g][0][4]*100:.2f}%" for a in ANIOS) + " |")
OUT_MD.write_text("\n".join(L), encoding="utf-8")
print("ok")
