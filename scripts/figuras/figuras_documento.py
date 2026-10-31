"""Figuras, mapas y tablas del documento técnico (D-033, D-036).

Lee solo salidas ya generadas por la cadena (data/processed, reports/ y cachés de data/interim) y no recalcula el
modelo. Cada figura guarda junto a ella el CSV con sus datos.
Salidas: reports/figuras/figuras_documento/; caché cartográfica en data/interim/cartografia/.
Uso: .venv/bin/python scripts/figuras/figuras_documento.py
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import json
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from ine_perfiles import brecha as B
from ine_perfiles import config as C
from ine_perfiles import evaluacion as CF
from ine_perfiles import descriptores as D

OUT = C.salidas(__file__)
FINALES = C.salidas("perfiles/perfiles_finales")         # salidas de perfiles_finales (solo lectura)
PROC = C.PROCESADOS
INT = C.INTERIM
CACHE = C.cache("cartografia")
SHP = C.RAIZ / "data" / "raw" / "externos" / "cartografia" / "secciones_2018_mxDistritos"
LLAVE = CF.LLAVE
K = C.K_EVALUADO_K5
ELECCIONES = list(C.ELECCIONES)
PRESIDENCIALES = [a for a, (_, t) in C.ELECCIONES.items() if t == "presidencial"]

# ------------------------------------------------------------------ estilo (todas las elecciones de esta sección son de estilo, no metodológicas)
TINTA, TINTA2, REJILLA = "#1f1f1e", "#5c5c58", "#e4e3df"
ANCHO, MEDIA = 6.5, 3.2            # pulgadas: ancho completo (texto de 16.6 cm) y media página
COLORES = ["#0b2e59", "#6cb2e8", "#b8470e", "#00916e", "#8a3a9e"]        # un color fijo por perfil
NOMBRES = ["P1 Norte urbano", "P2 Centro urbano, brecha leve", "P3 Rural Bajío y norte-centro",
           "P4 Recién llegados urbanos", "P5 Sureste rural e indígena"]
CORTOS = ["P1", "P2", "P3", "P4", "P5"]
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Carlito", "Liberation Sans", "DejaVu Sans"],
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.edgecolor": TINTA2, "axes.labelcolor": TINTA,
    "xtick.color": TINTA2, "ytick.color": TINTA2, "text.color": TINTA, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.5,
    "lines.linewidth": 1.4, "pdf.fonttype": 42, "axes.axisbelow": True,
})
CTRL = []     # cifras de control impresas al final


def ctrl(nombre, valor, esperado=None, tol=None):
    """Registra una cifra de control y, si hay valor esperado, la verifica con assert."""
    if esperado is not None:
        assert abs(valor - esperado) <= tol, f"control {nombre}: {valor} vs {esperado} (tol {tol})"
    CTRL.append((nombre, valor, esperado))
    print(f"[control] {nombre} = {valor:.6g}" + ("" if esperado is None else f"  (esperado {esperado}, tol {tol})"))


def guardar(fig, nombre, png=False):
    """PDF vectorial; los mapas van en PNG a 300 dpi porque el PDF vectorial pesa más de 2 MB."""
    if png:
        fig.savefig(OUT / f"{nombre}.png", dpi=300)
    else:
        fig.savefig(OUT / f"{nombre}.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ datos
def cargar():
    """Celdas objetivo con su perfil (entrega K=5), responsabilidades, peso w, LN 2024 y datos de sección."""
    sal = pd.read_parquet(PROC / "perfiles_finales.parquet")
    for c in LLAVE:
        sal[c] = sal[c].astype("int64")
    sal["perfil"] = sal["perfil"].astype(int)
    assert len(sal) == C.SENS_CELDAS_OBJETIVO_CONTROL and set(sal.perfil) == set(range(1, K + 1))
    b = pd.read_parquet(PROC / "brecha_celda.parquet", columns=LLAVE + ["ln_2024", "delta", "objetivo"])
    for c in LLAVE:
        b[c] = b[c].astype("int64")
    ln_total_celdas = b.ln_2024.astype("float64").sum()
    desc = pd.read_parquet(PROC / "descriptores_seccion.parquet")
    x = sal.merge(b[LLAVE + ["ln_2024", "delta"]], on=LLAVE, how="left", validate="1:1")
    x["ln_2024"] = x["ln_2024"].fillna(0).astype("float64")     # celdas sin 2024: LN 0
    x["delta"] = x["delta"].astype("float64")
    x = x.merge(desc[["edo", "seccion", "mpio", "tiposec", "circunscripcion"]].astype({"edo": "int64", "seccion": "int64"}),
                on=["edo", "seccion"], how="left", validate="m:1")
    return sal, b, desc, x, ln_total_celdas


# ------------------------------------------------------------------ ficha de los perfiles: variables del modelo (D-024)
def variables_perfil(x):
    """Perfil x variable del modelo. Categóricas: razón % en el perfil / % en la población objetivo (perfiles_finales/composicion_K5.csv;
    ponderadas por responsabilidad x w, igual que el modelo). Continuas: media del perfil menos media de la población
    objetivo, en desviaciones estándar de la población objetivo (z); ponderadas por responsabilidad x w (perfil) y por w
    (población objetivo); w = peso de la mezcla (déficit normalizado, D-024)."""
    comp = pd.read_csv(FINALES / "composicion_K5.csv")
    comp["categoria"] = comp["categoria"].astype(str)
    etq_edad = {str(g["id"]): g["etiqueta"] for g in json.load(open(PROC / "cortes_edad.json"))["grupos"]}
    assert len(etq_edad) == 7
    # control de la razón categórica recalculada (misma ponderación): sexo mujeres y tipo de sección
    for var, col, cat in (("sexo", "sexo", 1), ("tiposec", "tiposec", "R")):
        for k in range(1, K + 1):
            wk = x[f"resp_perfil_{k}"] * x.w
            sel = (x[col] == cat)
            r = (wk[sel].sum() / wk.sum()) / (x.w[sel].sum() / x.w.sum())
            r_tab = float(comp[(comp.perfil == k) & (comp.variable == var) & (comp.categoria == str(cat))].razon.iloc[0])
            assert abs(r - r_tab) < 5e-4, f"razón {var}={cat} perfil {k}: {r} vs {r_tab}"
    filas = []                                     # (bloque, etiqueta, tipo, [valor por perfil])
    def cat_fila(bloque, etiqueta, var, cat):
        v = [float(comp[(comp.perfil == k) & (comp.variable == var) & (comp.categoria == str(cat))].razon.iloc[0])
             for k in range(1, K + 1)]
        filas.append((bloque, etiqueta, "razon", v))
    cat_fila("Sexo", "Mujeres", "sexo", 1)
    for g in range(1, 8):
        cat_fila("Edad", etq_edad[str(g)], "grupo", g)
    for c in range(1, 6):
        cat_fila("Circunscripción", f"Circunscripción {c}", "circunscripcion", c)
    for t, n in (("U", "Urbana"), ("M", "Mixta"), ("R", "Rural")):
        cat_fila("Tipo de sección", n, "tiposec", t)
    # continuas
    with open(INT / "seleccion_numero_perfiles" / "pca.pkl", "rb") as fh:
        P = pickle.load(fh)
    sec = P["d"][["edo", "seccion"]].astype("int64").copy()
    for j in range(P["r"]):
        sec[f"pc{j + 1}"] = P["pcs"][:, j]
    xs = x.merge(sec, on=["edo", "seccion"], how="left", validate="m:1")
    assert len(xs) == len(x)
    cont = [("delta", "δ̃ (más negativa = más severa)", "Brecha"),
            ("pc1", "CP1 · rezago educativo y de acceso (+ = más)", "Contexto"),
            ("pc2", "CP2 · población mayor (+) o joven (−)", "Contexto"),
            ("pc3", "CP3 · lengua indígena y migración (+)", "Contexto")]
    cont_csv = []
    for col, etiqueta, bloque in cont:
        v = xs[col].to_numpy(float)
        ok = ~np.isnan(v)
        w = xs.w.to_numpy(float)
        mu = np.average(v[ok], weights=w[ok])
        sd = np.sqrt(np.average((v[ok] - mu) ** 2, weights=w[ok]))
        z = []
        for k in range(1, K + 1):
            wk = (xs[f"resp_perfil_{k}"] * xs.w).to_numpy(float)
            z.append((np.average(v[ok], weights=wk[ok]) - mu) / sd)
        filas.append((bloque, etiqueta, "z", z))
        cont_csv.append((col, mu, sd))
    tab = pd.DataFrame([dict(bloque=b, variable=e, tipo=t, **{CORTOS[k]: v[k] for k in range(K)}) for b, e, t, v in filas])
    tab.round(4).to_csv(OUT / "variables_perfil.csv", index=False)
    pd.DataFrame(cont_csv, columns=["variable", "media_ponderada_w", "desv_est_ponderada_w"]).round(5).to_csv(
        OUT / "variables_perfil_escala_z.csv", index=False)
    return tab


def pca_cargas():
    with open(INT / "seleccion_numero_perfiles" / "pca.pkl", "rb") as fh:
        P = pickle.load(fh)
    r = P["r"]
    assert r == 3 and len(P["cols"]) == 18
    val, vec = P["val"], P["vec"][:, :r]
    carga = vec * np.sqrt(val[:r])                   # correlación variable-componente (PCA sobre matriz de correlación)
    t = pd.DataFrame({"variable": P["cols"]})
    for j in range(r):
        t[f"vector_propio_cp{j + 1}"] = vec[:, j]
    for j in range(r):
        t[f"carga_correlacion_cp{j + 1}"] = carga[:, j]
    resumen = pd.DataFrame({"variable": [f"% de varianza CP{j + 1}" for j in range(r)] + ["% de varianza acumulada (3 CP)"],
                            **{f"carga_correlacion_cp{j + 1}": [np.nan] * (r + 1) for j in range(r)}})
    for j in range(r):
        resumen.loc[j, f"carga_correlacion_cp{j + 1}"] = 100 * P["var_exp"][j]
    resumen.loc[r, "carga_correlacion_cp1"] = 100 * P["var_exp"][:r].sum()
    pd.concat([t, resumen], ignore_index=True).round(4).to_csv(OUT / "pca_cargas.csv", index=False)
    ctrl("varianza explicada por 3 CP (%)", 100 * P["var_exp"][:r].sum())
    return t


# ------------------------------------------------------------------ brecha por tipo de elección
def trayectorias(sal):
    """Observada 100·Σsv/Σn (D-001) y esperada 100·Σn·q_gse/Σn (D-022) por perfil y elección (asignación dura de la entrega)."""
    p = pd.read_parquet(PROC / "panel_celda_eleccion.parquet", columns=LLAVE + ["aelec", "sv", "n"])
    q = B.tasa_esperada(p.assign(sv=p.sv.astype("int64"), n=p.n.astype("int64")))
    for c in LLAVE:
        p[c] = p[c].astype("int64")
    p = p[p.n > 0].merge(q, on=["sexo", "grupo", "aelec"], how="left", validate="m:1")
    assert p.q.notna().all()
    p["sv"], p["n"] = p.sv.astype("int64"), p.n.astype("int64")
    p["e"] = p.n * p.q
    nac = p.groupby("aelec")[["sv", "n"]].sum()
    ctrl("participación nacional 2024 del panel (%)", float(100 * nac.loc[2024, "sv"] / nac.loc[2024, "n"]), 59.67, 5e-3)
    ctrl("participación nacional 2021 del panel (%; informativa; difiere de la cifra oficial 51.84)", float(100 * nac.loc[2021, "sv"] / nac.loc[2021, "n"]))
    p = p.merge(sal[LLAVE + ["perfil"]], on=LLAVE, how="inner", validate="m:1")
    g = p.groupby(["perfil", "aelec"])[["sv", "n", "e"]].sum()
    obj = p.groupby("aelec")[["sv", "n", "e"]].sum().assign(perfil=0).set_index("perfil", append=True).swaplevel()
    g = pd.concat([g, obj])
    t = pd.DataFrame(dict(observada=100 * g.sv / g.n, esperada=100 * g.e / g.n)).reset_index()
    t["diferencia_pts"] = t.observada - t.esperada
    t = t.rename(columns={"perfil": "perfil_0_es_poblacion_objetivo"})
    t.round(3).to_csv(OUT / "trayectorias.csv", index=False)
    return t


def fig_trayectorias(t):
    """Brecha (observada − esperada, puntos) por perfil, en dos paneles: presidenciales e intermedias. Cada elección se
    compara con la anterior de su mismo tipo; el zigzag presidencial–intermedia queda fuera de la figura."""
    t = t.rename(columns={"perfil_0_es_poblacion_objetivo": "perfil"})
    INTERMEDIAS = [a for a in ELECCIONES if a not in PRESIDENCIALES]
    fig, axs = plt.subplots(1, 2, figsize=(ANCHO, 3.0), sharey=True)
    lo = np.floor(t.diferencia_pts.min() / 2) * 2
    for ax, anios, titulo in ((axs[0], PRESIDENCIALES, "Elecciones presidenciales"), (axs[1], INTERMEDIAS, "Elecciones intermedias")):
        ax.plot([anios[0] - 0.8, anios[-1]], [0, 0], color=TINTA2, lw=0.8)
        ax.text(anios[-1] + 0.5, 0, "Esperado", fontsize=7.5, va="center", color=TINTA2, fontweight="bold")
        s0 = t[(t.perfil == 0) & t.aelec.isin(anios)].sort_values("aelec")
        ax.plot(s0.aelec, s0.diferencia_pts, color=TINTA2, ls=(0, (3, 2)), lw=1.2, zorder=2)
        for k in range(1, K + 1):
            s = t[(t.perfil == k) & t.aelec.isin(anios)].sort_values("aelec")
            ax.plot(s.aelec, s.diferencia_pts, color=COLORES[k - 1], lw=1.8, marker="o", ms=4, mec="white", mew=0.6, zorder=3)
        # rótulos al final de cada línea, separados para que no se encimen
        fin = t[t.aelec == anios[-1]].set_index("perfil").diferencia_pts
        ys = dict(sorted(fin.items(), key=lambda kv: kv[1]))
        prev = -np.inf
        for k, y in ys.items():
            y = max(y, prev + 0.85)
            prev = y
            etq = "Promedio" if k == 0 else CORTOS[k - 1]
            ax.text(anios[-1] + 0.5, y, f"{etq} {fin[k]:+.1f}".replace("-", "−"), fontsize=7.5, va="center",
                    color=TINTA2 if k == 0 else COLORES[k - 1], fontweight="bold")
        ax.set_title(titulo, fontsize=9, loc="left", fontweight="bold")
        ax.set_xticks(anios); ax.set_xlim(anios[0] - 0.8, anios[-1] + 4.6)
        ax.set_ylim(lo, 0.8)
    axs[0].set_ylabel("Diferencia con lo esperado (puntos)")
    h = [Line2D([], [], color=COLORES[k], lw=1.8, marker="o", ms=4, label=NOMBRES[k]) for k in range(K)] + \
        [Line2D([], [], color=TINTA2, lw=1.2, ls=(0, (3, 2)), label="Promedio de los cinco perfiles")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.085, right=0.99, top=0.92, bottom=0.27, wspace=0.08)
    guardar(fig, "trayectorias")


# ------------------------------------------------------------------ figura 3 · mapas municipales
def geometrias_municipales():
    """Cartografía seccional 2018 (espejo de Magar) -> municipios (entidad, municipio) en EPSG:6372, simplificados. Con caché."""
    import geopandas as gpd
    ruta, ruta_e = CACHE / "municipios_2018_6372.gpkg", CACHE / "estados_2018_6372.gpkg"
    if ruta.exists() and ruta_e.exists():
        return gpd.read_file(ruta), gpd.read_file(ruta_e)
    TOL = 300.0                    # m: tolerancia de simplificación (estilo: a 6.5 in de ancho, 1 px a 300 dpi ≈ 2.3 km)
    partes, lim = [], []
    estados = sorted(p for p in SHP.iterdir() if (p / "SECCION.shp").exists())
    assert len(estados) == 32
    for d in estados:                                  # un estado a la vez (memoria)
        g = gpd.read_file(d / "SECCION.shp", columns=["entidad", "municipio"])
        g = g.to_crs(6372)
        g["geometry"] = g.geometry.make_valid()
        m = g.dissolve(by=["entidad", "municipio"], as_index=False)
        m["geometry"] = m.geometry.simplify(TOL, preserve_topology=True)
        partes.append(m[["entidad", "municipio", "geometry"]])
        e = g[["entidad", "geometry"]].dissolve(by="entidad", as_index=False)       # contorno estatal sin huecos entre municipios simplificados
        e["geometry"] = e.geometry.simplify(TOL, preserve_topology=True)
        lim.append(e)
        print("  cartografía", d.name, len(g), "secciones ->", len(m), "municipios", flush=True)
    mun = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs="EPSG:6372")
    mun["entidad"], mun["municipio"] = mun.entidad.astype(int), mun.municipio.astype(int)
    mun.to_file(ruta, driver="GPKG")
    est = gpd.GeoDataFrame(pd.concat(lim, ignore_index=True), crs="EPSG:6372")
    est.to_file(ruta_e, driver="GPKG")
    return mun, est


def datos_municipio(x, b, desc):
    """LN 2024 por municipio: total (todas las celdas de brecha_celda) y por perfil (suma de resp x ln de las celdas objetivo)."""
    mp = desc[["edo", "seccion", "mpio"]].astype("int64")
    bb = b[["edo", "seccion", "ln_2024"]].merge(mp, on=["edo", "seccion"], how="left", validate="m:1")
    assert bb.mpio.notna().all(), "celdas de brecha_celda sin municipio en los descriptores"
    tot = bb.groupby(["edo", "mpio"]).ln_2024.sum().astype("float64").rename("ln_total")
    cols = {}
    for k in range(1, K + 1):
        cols[f"ln_P{k}"] = (x[f"resp_perfil_{k}"] * x.ln_2024)
    r = pd.DataFrame(cols).assign(edo=x.edo.to_numpy(), mpio=x.mpio.to_numpy()).groupby(["edo", "mpio"]).sum()
    m = pd.concat([tot, r], axis=1).fillna(0.0).reset_index()
    for k in range(1, K + 1):
        m[f"pct_P{k}"] = 100 * m[f"ln_P{k}"] / m.ln_total
    m["ln_objetivo"] = m[[f"ln_P{k}" for k in range(1, K + 1)]].sum(axis=1)
    m["pct_objetivo"] = 100 * m.ln_objetivo / m.ln_total
    return m


def mapas(x, b, desc, ln_total_celdas):
    import geopandas as gpd
    mun, est = geometrias_municipales()
    m = datos_municipio(x, b, desc)
    ctrl("LN 2024 total de los mapas (millones) = LN 2024 de las celdas", m.ln_total.sum() / 1e6, ln_total_celdas / 1e6, 1e-6)
    ctrl("LN 2024 objetivo en los mapas (millones) = Σ resp x ln de las celdas objetivo", m.ln_objetivo.sum() / 1e6, x.ln_2024.sum() / 1e6, 1e-6)
    # unión por clave; no se inventa correspondencia
    claves_g = set(zip(mun.entidad, mun.municipio))
    claves_d = set(zip(m.edo, m.mpio))
    sin_geo = m[[(e, p) not in claves_g for e, p in zip(m.edo, m.mpio)]]
    sin_dato = [k for k in claves_g if k not in claves_d]
    pct_ln_sin_geo = 100 * sin_geo.ln_total.sum() / m.ln_total.sum()
    print(f"[mapas] municipios en datos: {len(m)}; en cartografía: {len(mun)}; datos sin geometría: {len(sin_geo)} "
          f"({pct_ln_sin_geo:.3f}% de la LN 2024); geometrías sin datos: {len(sin_dato)}")
    ctrl("municipios de los datos sin geometría", len(sin_geo))
    ctrl("% de la LN 2024 en municipios sin geometría", pct_ln_sin_geo)
    ctrl("geometrías sin datos", len(sin_dato))
    sin_geo.assign(pct_ln=100 * sin_geo.ln_total / m.ln_total.sum()).to_csv(OUT / "mapas_municipios_sin_geometria.csv", index=False)
    mg = mun.merge(m.rename(columns={"edo": "entidad", "mpio": "municipio"}), on=["entidad", "municipio"], how="left", validate="1:1")
    # contorno estatal consistente con la geometría simplificada
    from shapely.geometry import MultiPolygon, Polygon
    def sin_huecos(g):        # los huecos son rendijas de la cartografía seccional; los enclaves (CDMX) los dibuja su propio contorno
        ps = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        return MultiPolygon([Polygon(p.exterior) for p in ps])
    est["geometry"] = est.geometry.apply(sin_huecos)
    pct_cols = [f"pct_P{k}" for k in range(1, K + 1)]
    vmax = float(np.nanpercentile(mg[pct_cols].to_numpy(), 99))          # escala común a los cinco mapas: 0 al percentil 99 global
    ctrl("tope común de la escala de color (% de la LN del municipio)", vmax)
    mg[["entidad", "municipio", "ln_total", "ln_objetivo", "pct_objetivo"] + pct_cols].round(4).to_csv(OUT / "mapas_municipios.csv", index=False)
    cmap = LinearSegmentedColormap.from_list("uno", ["#f2f6fb", "#a9c6e4", "#4f86bf", "#1d4f8c", "#08234a"])
    norm = Normalize(0, vmax)
    xmin, ymin, xmax, ymax = mg.total_bounds
    GRIS_SIN = "#ececea"
    def lienzo(alto=3.6):
        fig, ax = plt.subplots(figsize=(ANCHO, alto))
        ax.set_axis_off(); ax.set_aspect("equal")
        ax.set_xlim(xmin - 5e4, xmax + 5e4); ax.set_ylim(ymin - 5e4, ymax + 5e4)
        fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
        return fig, ax
    for k in range(1, K + 1):
        fig, ax = lienzo()
        v = mg[f"pct_P{k}"]
        mg[v.isna()].plot(ax=ax, color=GRIS_SIN, lw=0)
        mg[v.notna()].plot(ax=ax, column=f"pct_P{k}", cmap=cmap, norm=norm, lw=0.05, edgecolor="#ffffff")
        est.boundary.plot(ax=ax, color="#6b6b66", lw=0.35, alpha=0.75)
        cax = ax.inset_axes([0.035, 0.115, 0.30, 0.03])
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal", extend="max")
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=7.5, length=2)
        cb.set_label("% de la LN 2024 del municipio", fontsize=8)
        guardar(fig, f"mapa_P{k}", png=True)
    # perfil dominante
    L = mg[[f"ln_P{k}" for k in range(1, K + 1)]].to_numpy()
    dom = np.where(mg.ln_objetivo.fillna(0) > 0, np.nanargmax(np.nan_to_num(L), axis=1) + 1, 0)
    UMBRAL = 50.0                                      # % de la LN del municipio: debajo, la población objetivo no domina (mayoría simple)
    dom = np.where(mg.pct_objetivo.fillna(0) < UMBRAL, 0, dom)
    mg["dominante"] = dom
    cuenta = mg.dominante.value_counts().sort_index()
    ln_dom = {k: float(mg.loc[mg.dominante == k, "ln_total"].sum() / 1e6) for k in range(0, K + 1)}
    print("[mapas] municipios por perfil dominante (0 = objetivo < 50% o sin dato):", cuenta.to_dict())
    pd.DataFrame({"dominante_0_es_objetivo_menor_50pct": list(ln_dom), "municipios": [int(cuenta.get(k, 0)) for k in ln_dom],
                  "ln_total_millones": list(ln_dom.values())}).to_csv(OUT / "mapa_dominante.csv", index=False)
    fig, ax = lienzo()
    mg[mg.dominante == 0].plot(ax=ax, color=GRIS_SIN, lw=0.05, edgecolor="white")
    for k in range(1, K + 1):
        mg[mg.dominante == k].plot(ax=ax, color=COLORES[k - 1], lw=0.05, edgecolor="white")
    est.boundary.plot(ax=ax, color="#ffffff", lw=0.4, alpha=0.9)
    h = [Patch(facecolor=COLORES[k], label=NOMBRES[k]) for k in range(K)] + [Patch(facecolor=GRIS_SIN, label="Población objetivo < 50% de la LN")]
    leg = ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0.0, 0.0), frameon=False, fontsize=8, handlelength=1.1, labelspacing=0.3)
    guardar(fig, "mapa_dominante", png=True)
    for f in sorted(OUT.glob("mapa_*.png")):
        print(f"[mapas] {f.name}: {f.stat().st_size / 1e6:.2f} MB")


# ------------------------------------------------------------------ cifras de contexto de cada página de perfil
DESCR = [  # (columna de perfiles_finales/perfiles_K5.csv, columna de descriptores o 'tasa', etiqueta)
    ("med_graproes", "graproes", "Escolaridad (años)"),
    ("med_prop_internet", "prop_internet", "Hogares con internet"),
    ("med_prop_hli", "prop_hli", "Habla lengua indígena"),
    ("med_prop_nacida_otra_ent", "prop_nacida_otra_ent", "Nacidos en otra entidad"),
    ("med_razon_ln_p18", "razon_ln_p18", "Lista nominal / pob. 18+"),
    ("med_iim_dp2", "iim_dp2", "Baja intens. migratoria"),
    ("med_im_2020", "im_2020", "Baja marginación"),
    ("med_pctl_mov_estado", "pctl_mov_estado", "Movilidad"),
    ("med_prop_18a24", "prop_18a24", "Tienen 18–24 años"),
    ("med_prop_60ymas", "prop_60ymas", "Tienen 60 años o más"),
    ("mediana_tasa_homicidio_100mil", "tasa", "Tasa de homicidio"),
]


def pctl_ponderado(v, w, valor):
    """Percentil (0-100) de `valor` en la distribución ponderada (w) de v; los empates cuentan a mitad."""
    ok = ~np.isnan(v)
    v, w = v[ok], w[ok]
    menor = w[v < valor].sum()
    igual = w[v == valor].sum()
    return 100 * (menor + igual / 2) / w.sum()


def descriptores(x, desc):
    pf = pd.read_csv(FINALES / "perfiles_K5.csv").set_index("perfil")
    viol = pd.read_parquet(INT / "externos" / "violencia_mpio.parquet")
    tasa = CF.violencia_a_secciones(desc, viol, "tasa_contr_v2023")
    w = x.w.to_numpy(float)
    vals = {}
    for _, col, _ in DESCR:
        vals[col] = CF.a_celdas(x, desc, tasa if col == "tasa" else desc[col].to_numpy(float))
    filas = []
    for k in range(1, K + 1):
        wk = (x[f"resp_perfil_{k}"] * x.w).to_numpy(float)
        for csvcol, col, etq in DESCR:
            med = float(pf.loc[k, csvcol])
            rec = D.cuantil_ponderado(vals[col], wk, [0.5])[0]
            assert abs(rec - med) < 1e-9 * max(1, abs(med)), f"mediana {col} perfil {k}: {rec} vs {med}"
            med_obj = float(D.cuantil_ponderado(vals[col], w, [0.5])[0])
            filas.append(dict(perfil=CORTOS[k - 1], descriptor=etq, columna=col, mediana_perfil=med, mediana_objetivo=med_obj,
                              percentil_perfil_en_objetivo=pctl_ponderado(vals[col], w, med),
                              percentil_objetivo_en_objetivo=pctl_ponderado(vals[col], w, med_obj)))
    t = pd.DataFrame(filas)
    t.round(5).to_csv(OUT / "descriptores.csv", index=False)


# ------------------------------------------------------------------ curva de captura
def captura():
    """Curvas de captura fuera de tiempo (D-025, D-032): azar, historial propio, perfiles K=5 y línea base objetivo_0921 sí/no."""
    UV = "solo celdas con historial 2009-21"
    c5 = pd.read_parquet(INT / "validacion_2024" / "curvas_captura_K5.parquet")
    c5 = c5[c5.universo == UV]
    b = pd.read_parquet(PROC / "brecha_celda.parquet",
                        columns=["E", "E_0921", "objetivo_0921", "E_24", "ln_2024", "deficit_2024_crudo"])
    cel = b[b["E"] > 0].reset_index(drop=True)                # universo de cargar_universo (D-025)
    h_ok = cel.E_0921.notna().to_numpy()
    obj0 = cel.objetivo_0921.fillna(False).astype(bool).to_numpy()
    m4 = np.nan_to_num(cel.E_24.to_numpy(float)) > 0
    mk = m4 & h_ok
    r_b = np.where(obj0, 0.0, 1.0)                            # D-032: dos bloques, objetivo primero
    cb, auc_b, _ = CF.curva_captura(r_b[mk], cel.ln_2024.to_numpy(float)[mk], cel.deficit_2024_crudo.to_numpy(float)[mk], None)
    curvas = {"hist": c5[c5.metodo == "historial propio"], "k5": c5[c5.metodo == "mezcla K=5 (2009-21)"], "base": cb}
    auc = {k: float(np.trapezoid(c.y_pos, c.x)) for k, c in curvas.items()}
    ctrl("AUC historial propio (reproducido)", auc["hist"], 0.759, 5e-4)
    ctrl("AUC perfiles K=5 (reproducido)", auc["k5"], 0.720, 5e-4)
    ctrl("AUC línea base objetivo sí/no (reproducido)", auc["base"], 0.672, 5e-4)
    a_mpio = pd.read_csv(C.salidas("validacion/intervalos_municipio") / "auc_linea_base.csv")
    a_mpio = a_mpio[a_mpio.universo == UV].set_index("metodo").AUC_pos
    assert abs(auc["base"] - a_mpio["línea base objetivo_0921 sí/no"]) < 5e-4
    xg = np.linspace(0, 1, 1001)
    filas = pd.DataFrame({"x": xg, "azar": xg})
    for k, c in curvas.items():
        filas[k] = np.interp(xg, c.x, c.y_pos)
    filas.rename(columns={"hist": "historial_propio", "k5": "perfiles_K5", "base": "linea_base_objetivo_si_no"}).round(5).to_csv(
        OUT / "captura.csv", index=False)
    est = {"hist": dict(color=TINTA, ls="-", lw=1.4, label="Historial propio"),
           "k5": dict(color="#1c5cab", ls="-", lw=1.7, label="Perfiles K=5"),
           "base": dict(color="#b8470e", ls=(0, (4, 2)), lw=1.3, label="Objetivo sí/no")}
    fig, ax = plt.subplots(figsize=(MEDIA, 3.0))
    ax.plot([0, 1], [0, 1], color=TINTA2, ls=":", lw=1.0, label="Azar  0.500")
    for k in ("hist", "k5", "base"):
        kw = dict(est[k]); kw["label"] = f"{kw['label']}  {auc[k]:.3f}"
        ax.plot(xg, filas[k], zorder=3, **kw)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
    ax.set_xlabel("Fracción acumulada de la lista nominal 2024", fontsize=8.5)
    ax.set_ylabel("Fracción acumulada del déficit 2024", fontsize=8.5)
    ax.legend(title="Orden con 2009–2021 (AUC)", title_fontsize=7.5, loc="lower right", frameon=False, handlelength=2.2, fontsize=8)
    fig.subplots_adjust(left=0.15, right=0.97, top=0.98, bottom=0.14)
    guardar(fig, "captura")


# ------------------------------------------------------------------ tablas del documento, generadas de los CSV (sin copiar cifras a mano)
CONTEXTO = [  # (columna de descriptores.csv, etiqueta, formato)
    ("graproes", "Escolaridad (años)", lambda v: f"{v:.1f}"),
    ("prop_internet", "Hogares con internet", lambda v: f"{100 * v:.0f}%"),
    ("prop_hli", "Habla lengua indígena", lambda v: f"{100 * v:.1f}%"),
    ("prop_nacida_otra_ent", "Nació en otra entidad", lambda v: f"{100 * v:.0f}%"),
    ("prop_60ymas", "Tiene 60 años o más", lambda v: f"{100 * v:.0f}%"),
    ("razon_ln_p18", "Electores / pob. 18+", lambda v: f"{v:.2f}"),
]


def tabla_contexto():
    """Mediana de cada indicador en las secciones de cada perfil frente a la población objetivo (ponderadas; descriptores.csv)."""
    t = pd.read_csv(OUT / "descriptores.csv")
    filas = []
    for col, etq, fmt in CONTEXTO:
        fila = {"indicador": etq}
        for k in CORTOS:
            s = t[(t.perfil == k) & (t.columna == col)].iloc[0]
            fila[k] = fmt(s.mediana_perfil)
        fila["poblacion_objetivo"] = fmt(s.mediana_objetivo)
        filas.append(fila)
    pd.DataFrame(filas).to_csv(OUT / "contexto_perfiles.csv", index=False)


BATERIA = [  # (bloque, id, texto corto, decimales)
    ("En el tiempo (puntos)", "T01", "La brecha se agrava (por elección)", 1),
    ("En el tiempo (puntos)", "T02", "Más profunda en las intermedias", 1),
    ("Dentro de la misma sección (diferencia de brecha)", "T03", "Hombres 25–46 más abajo que mujeres 25–46", 2),
    ("Dentro de la misma sección (diferencia de brecha)", "T04", "Jóvenes 18–24 más abajo que adultos 32–69", 2),
    ("Dentro de la misma sección (diferencia de brecha)", "T05", "Personas de 80+ más abajo que adultos 32–69", 2),
    ("Dentro de la misma sección (diferencia de brecha)", "T06", "Adultos 25–46 más abajo que adultos 47–69", 2),
    ("Entre sus secciones, más profunda donde… (correlación)", "T07", "…más gente nació en otra entidad", 2),
    ("Entre sus secciones, más profunda donde… (correlación)", "T08", "…llegan más electores", 2),
    ("Entre sus secciones, más profunda donde… (correlación)", "T09", "…más se habla lengua indígena", 2),
    ("Entre sus secciones, más profunda donde… (correlación)", "T10", "…hay menos internet", 2),
    ("Entre sus secciones, más profunda donde… (correlación)", "T11", "…hay más migración a EE. UU.", 2),
    ("Otras", "T12", "Más electores registrados que adultos (razón)", 2),
    ("Otras", "T13", "Más profunda en secciones rurales que urbanas", 2),
]
SIMBOLO = {"se cumple": "✓", "contraria": "✗", "no se cumple": "○", "no concluyente": "?"}


def tabla_pruebas():
    """Tabla única de pruebas (D-036): mismo renglón para los cinco perfiles; `*` marca las pruebas de la lectura de cada perfil."""
    d = pd.read_csv(C.salidas("validacion/bateria_comun") / "bateria_comun.csv")
    # D-034: la doble medida solo rige los contrastes de edad (T04–T06); el de sexo (T03) usa su veredicto directo
    d["v"] = np.where(d.id.isin(["T04", "T05", "T06"]), d.veredicto_combinado, d.veredicto)
    assert set(d.v) <= set(SIMBOLO) and len(d) == 13 * K
    filas = []
    for bloque, i, texto, dec in BATERIA:
        fila = {"bloque": bloque, "id": i, "prueba": texto}
        for k in range(1, K + 1):
            r = d[(d.id == i) & (d.perfil == k)].iloc[0]
            v = 0.0 if round(r.valor, dec) == 0 else r.valor          # sin "−0.00"
            fila[f"P{k}"] = f"{SIMBOLO[r.v]} {v:+.{dec}f}".replace("-", "−") + (" *" if r.de_su_lectura else "")
        filas.append(fila)
    pd.DataFrame(filas).to_csv(OUT / "tabla_pruebas.csv", index=False)
    print(d.pivot(index="id", columns="perfil", values="v").to_string())


if __name__ == "__main__":
    sal, b, desc, x, ln_tot = cargar()
    # la suma de % del déficit por perfil es 100 (D-024)
    pf = pd.read_csv(FINALES / "perfiles_K5.csv")
    ctrl("Σ % del déficit por perfil", float(pf.pct_deficit.sum()), 100.0, 1e-6)
    ctrl("% del déficit recalculado (Σ resp x w por perfil)", float(sum(100 * (x[f"resp_perfil_{k}"] * x.w).sum() / x.w.sum() for k in range(1, K + 1))), 100.0, 1e-6)
    tab = variables_perfil(x)
    pca_cargas()
    t = trayectorias(sal)
    print(t.round(2).to_string())
    fig_trayectorias(t)
    mapas(x, b, desc, ln_tot)
    descriptores(x, desc)
    captura()
    tabla_contexto()
    tabla_pruebas()
    print("\n== cifras de control ==")
    for n, v, e in CTRL:
        print(f"  {n}: {v:.6g}" + ("" if e is None else f" (esperado {e})"))
    print("listo")
