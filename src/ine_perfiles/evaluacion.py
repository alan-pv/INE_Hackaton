"""Evaluación de los perfiles (D-021, D-025, D-027, D-029, D-032).

ARI ponderado, reetiquetado de soluciones (asignación húngara), datos de la mezcla con cualquier periodo,
universo y curva de captura fuera de tiempo, ΔAUC con bootstrap pareado por sección o por municipio,
paso de la violencia municipal a secciones y celdas, y la regla de perfiles claros de D-029.
Todo es descriptivo: no hay umbrales de coincidencia.
"""
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from ine_perfiles import config as C
from ine_perfiles import mezcla_mixta as MM

LLAVE = ["edo", "seccion", "sexo", "grupo"]
CATS = ["sexo", "grupo", "circunscripcion", "tiposec"]   # D-024 (las mismas que seleccion.CATS)


# ------------------------------------------------------------------ ARI ponderado (D-021)
def comb2(x):
    """x(x-1)/2 sobre reales: con pesos enteros coincide con el número de pares."""
    x = np.asarray(x, float)
    return x * (x - 1.0) / 2.0


def ari_ponderado(a, b, w=None):
    """ARI con la misma fórmula de pares de sklearn pero con la tabla de contingencia de pesos (D-021).
    Con w = 1 coincide con sklearn.metrics.adjusted_rand_score; con pesos enteros, con el ARI de las filas replicadas."""
    a, b = np.asarray(a), np.asarray(b)
    w = np.ones(len(a)) if w is None else np.asarray(w, float)
    assert len(a) == len(b) == len(w)
    ia, ua = pd.factorize(a)
    ib, ub = pd.factorize(b)
    tabla = np.bincount(ia * len(ub) + ib, weights=w, minlength=len(ua) * len(ub)).reshape(len(ua), len(ub))
    n = tabla.sum()
    suma = comb2(tabla).sum()
    sa, sb = comb2(tabla.sum(1)).sum(), comb2(tabla.sum(0)).sum()
    esperado = sa * sb / comb2(n)
    maximo = 0.5 * (sa + sb)
    if maximo == esperado:       # misma convención que sklearn: particiones triviales/idénticas -> 1
        return 1.0
    return float((suma - esperado) / (maximo - esperado))


# ------------------------------------------------------------------ datos de la mezcla (D-024)
def construir_datos(o, sec, pcs, r, col_delta, col_deficit):
    """Misma construcción que seleccion.construir, parametrizada por columnas para usar otro periodo (D-024).
    o: celdas de la población objetivo con LLAVE, col_delta, col_deficit; sec: secciones con
    edo, seccion, tiposec, circunscripcion; pcs: componentes (n_secciones, >=r). Pesos normalizados a Σw = n."""
    sec = sec[["edo", "seccion", "tiposec", "circunscripcion"]].copy()
    for j in range(r):
        sec[f"pc{j + 1}"] = pcs[:, j]
    x = o[LLAVE + [col_delta, col_deficit]].merge(sec, on=["edo", "seccion"], how="left", validate="m:1")
    assert len(x) == len(o) and x["circunscripcion"].notna().all()
    assert (x["sexo"].to_numpy() == o["sexo"].to_numpy()).all()
    w = np.maximum(x[col_deficit].to_numpy(float), 0.0)
    n_cero = int((w == 0).sum())
    w = w * len(w) / w.sum()
    cat, ncat = [], []
    for c in CATS:
        cod, uniq = pd.factorize(x[c].astype("object").where(x[c].notna(), "NaN"), sort=True)
        cat.append(cod)
        ncat.append(len(uniq))
    nombres = [col_delta] + [f"pc{j + 1}" for j in range(r)]
    dat = MM.Datos(np.column_stack(cat), tuple(ncat), x[nombres].to_numpy(float), w)
    return dat, x, n_cero


def reetiquetar(ref, nuevo, w, K):
    """Reetiqueta las clases `nuevo` (0..K-1) contra `ref` (0..K-1) con el máximo cruce ponderado (Hungarian).
    Devuelve (mapa nuevo->ref como arreglo, matriz de cruce KxK de pesos)."""
    cruce = np.zeros((K, K))
    np.add.at(cruce, (np.asarray(nuevo), np.asarray(ref)), np.asarray(w, float))
    fila, col = linear_sum_assignment(-cruce)
    mapa = np.empty(K, dtype=int)
    mapa[fila] = col
    return mapa, cruce


# ------------------------------------------------------------------ curva de captura (D-025)
def curva_captura(rhat, ln, d, despues=None):
    """Ordena las celdas de menor a mayor r̂ (las de `despues`=True al final, cada grupo por r̂) y devuelve la
    curva (x = fracción acumulada de LN 2024; y_pos = fracción acumulada del déficit positivo por celda
    max(d,0); y_sig = déficit con signo acumulado entre el déficit positivo total, porque el total con signo
    es ~0: Σ O = Σ E por estrato, D-022). Los empates (mismo grupo y mismo r̂) se tratan como un bloque con
    segmento recto = esperanza bajo desempate aleatorio. Devuelve (DataFrame de bloques, AUC_pos, AUC_sig)."""
    rhat = np.asarray(rhat, float)
    assert not np.isnan(rhat).any()
    despues = np.zeros(len(rhat), bool) if despues is None else np.asarray(despues, bool)
    df = pd.DataFrame(dict(post=despues, r=rhat, ln=np.asarray(ln, float), d=np.asarray(d, float)))
    df["dpos"] = df.d.clip(lower=0)
    g = df.groupby(["post", "r"], sort=True)[["ln", "d", "dpos"]].sum().reset_index()
    x = np.concatenate([[0.0], g.ln.cumsum() / g.ln.sum()])
    ypos = np.concatenate([[0.0], g.dpos.cumsum() / g.dpos.sum()])
    ysig = np.concatenate([[0.0], g.d.cumsum() / g.dpos.sum()])
    c = pd.DataFrame(dict(x=x, y_pos=ypos, y_sig=ysig))
    return c, float(np.trapezoid(ypos, x)), float(np.trapezoid(ysig, x))


# ------------------------------------------------------------------ violencia municipal (D-027)
def violencia_a_secciones(desc, viol, col):
    """D-027: une la tasa municipal (col) a las secciones por (edo, mpio), validate m:1. Devuelve un
    arreglo alineado con las filas de `desc`; NaN donde el municipio no tiene tasa (no se imputa)."""
    assert not viol.duplicated(["edo", "mpio"]).any()
    m = desc[["edo", "mpio"]].merge(viol[["edo", "mpio", col]], on=["edo", "mpio"], how="left", validate="m:1")
    assert len(m) == len(desc)
    return m[col].to_numpy(float)


def a_celdas(cel, sec, valores):
    """Lleva un valor por sección (arreglo alineado con `sec`, que trae edo y seccion) a cada celda de `cel`."""
    s = sec[["edo", "seccion"]].astype("int64")
    s["_v"] = np.asarray(valores, float)
    m = cel[["edo", "seccion"]].astype("int64").merge(s, on=["edo", "seccion"], how="left", validate="m:1")
    assert len(m) == len(cel)
    return m["_v"].to_numpy(float)


def cargar_universo(proc):
    """Universo de la curva de captura (D-025): celdas con E>0 con los agregados 2009-21 recalculados
    (m_0921, deficit_0921). Devuelve dict(b, cel, h_ok, obj0, m4). Todos los scripts de validación usan este mismo universo."""
    from ine_perfiles import brecha as B
    b = pd.read_parquet(proc / "brecha_celda.parquet")
    cel = b[b["E"] > 0].reset_index(drop=True)
    for c in LLAVE:
        cel[c] = cel[c].astype("int64")
    panel = pd.read_parquet(proc / "panel_celda_eleccion.parquet", columns=LLAVE + ["aelec", "sv", "nv", "n", "ln"])
    panel["ln"] = panel["ln"].astype("float64")
    q_gse = B.tasa_esperada(panel)
    c0 = B.agregar_celdas(panel, q_gse, [a for a in C.ELECCIONES if a < 2024]).reset_index()
    del panel
    for c in LLAVE:
        c0[c] = c0[c].astype("int64")
    c0 = c0[LLAVE + ["m", "N", "E"]].rename(columns={"m": "m_0921", "N": "N_chk", "E": "E_chk"})
    cel = cel.merge(c0, on=LLAVE, how="left", validate="1:1")
    h_ok = cel["E_0921"].notna().to_numpy()
    cel["deficit_0921"] = (cel.E_0921 - cel.N_0921 * cel.p_tilde_0921.astype(float)) / cel.m_0921
    obj0 = cel["objetivo_0921"].fillna(False).astype(bool).to_numpy()
    m4 = np.nan_to_num(cel["E_24"].to_numpy(float)) > 0
    return dict(b=b, cel=cel, h_ok=h_ok, obj0=obj0, m4=m4)


def rhat_mezcla(cel, h_ok, obj0, o0, perfil0, K):
    """r̂ de una mezcla ajustada con 2009-21 (D-025): razón ΣO/ΣE 2009-21 del perfil asignado; las celdas no objetivo_0921 reciben la
    razón agrupada de las no objetivo con historial y van al final. Devuelve (r, después, razón por perfil, razón no objetivo)."""
    razon_perfil = np.array([o0.O_0921[perfil0 == p].sum() / o0.E_0921[perfil0 == p].sum() for p in range(1, K + 1)])
    razon_nobj = cel.O_0921[h_ok & ~obj0].sum() / cel.E_0921[h_ok & ~obj0].sum()
    r = np.full(len(cel), razon_nobj)
    r[np.flatnonzero(obj0)] = razon_perfil[perfil0 - 1]
    return r, ~obj0, razon_perfil, razon_nobj


# ------------------------------------------------------------------ ΔAUC con bootstrap pareado (D-027)
def _auc_pos_bloques(orden, inicios, ln, dpos, mult):
    """AUC del déficit positivo con celdas ya ordenadas (`orden`) y bloques de empate (`inicios`), con
    multiplicidad `mult` por celda. Idéntica a curva_captura sobre las filas replicadas."""
    l = np.add.reduceat((ln * mult)[orden], inicios)
    p = np.add.reduceat((dpos * mult)[orden], inicios)
    x = np.concatenate([[0.0], np.cumsum(l) / l.sum()])
    y = np.concatenate([[0.0], np.cumsum(p) / p.sum()])
    return float(np.sum(np.diff(x) * (y[1:] + y[:-1]) / 2.0))


def _orden_bloques(rhat, despues):
    """Orden de curva_captura: primero las celdas no `despues`, cada grupo por r̂ creciente; bloques = (grupo, r̂) iguales."""
    rhat = np.asarray(rhat, float)
    post = np.zeros(len(rhat), bool) if despues is None else np.asarray(despues, bool)
    orden = np.lexsort((rhat, post))
    r_o, p_o = rhat[orden], post[orden]
    nuevo = np.concatenate([[True], (r_o[1:] != r_o[:-1]) | (p_o[1:] != p_o[:-1])])
    return orden, np.flatnonzero(nuevo)


def delta_auc_bootstrap(rhat1, despues1, rhat2, despues2, ln, deficit, edo, seccion,
                        B=None, nivel=None, sufijo=None):
    """D-027: ΔAUC_pos = AUC(método 1) − AUC(método 2) en la curva de captura (D-025), con bootstrap pareado que
    remuestrea SECCIONES con reemplazo, estratificado por estado (D-017), y recalcula ambas curvas en cada
    réplica. Mide la variabilidad del conjunto de evaluación, no la del ajuste. Intervalo percentil con
    k = (B+1)(1−nivel)/2 entero: [k-ésimo menor, (B+1−k)-ésimo menor] (Davison y Hinkley, 1997).
    Semilla [SEMILLA, sufijo]. Vectorizado: el orden por r̂ se calcula una vez; cada réplica solo reagrupa pesos.
    Devuelve dict(delta, auc1, auc2, deltas, auc1_rep, auc2_rep, lo, hi, B)."""
    from ine_perfiles import estabilidad as EST
    B = C.B_PERMANENCIA if B is None else B
    nivel = C.NIVEL_IC_PERMANENCIA if nivel is None else nivel
    sufijo = C.SUFIJO_SEMILLA_PERMANENCIA if sufijo is None else sufijo
    ln, d = np.asarray(ln, float), np.asarray(deficit, float)
    dpos = np.clip(d, 0, None)
    n = len(ln)
    assert all(len(v) == n for v in (rhat1, rhat2, edo, seccion))
    k = (B + 1) * (1 - nivel) / 2
    assert abs(k - round(k)) < 1e-9, "(B+1)(1-nivel)/2 debe ser entero"
    k = int(round(k))
    cod = pd.factorize(pd.MultiIndex.from_arrays([np.asarray(edo), np.asarray(seccion)]))[0]
    orden_s, inicio, largo, edo_sec = EST.indice_secciones(edo, seccion)
    ns = len(largo)
    m1, m2 = _orden_bloques(rhat1, despues1), _orden_bloques(rhat2, despues2)
    uno = np.ones(n)
    a1 = _auc_pos_bloques(m1[0], m1[1], ln, dpos, uno)
    a2 = _auc_pos_bloques(m2[0], m2[1], ln, dpos, uno)
    # precálculo por método (orden fijo): ln, déficit positivo y sección de cada celda ya ordenados
    pre = [(ln[o], dpos[o], cod[o], ini) for o, ini in (m1, m2)]

    def auc_rep(p, cnt):
        l_o, d_o, c_o, ini = p
        m = cnt[c_o]
        l = np.add.reduceat(l_o * m, ini)
        q = np.add.reduceat(d_o * m, ini)
        x = np.concatenate([[0.0], np.cumsum(l) / l.sum()])
        y = np.concatenate([[0.0], np.cumsum(q) / q.sum()])
        return float(np.sum(np.diff(x) * (y[1:] + y[:-1]) / 2.0))

    rng = np.random.default_rng([C.SEMILLA, sufijo])
    r1, r2 = np.empty(B), np.empty(B)
    for b in range(B):
        _, elegidas = EST.remuestrear_secciones(rng, edo_sec, orden_s, inicio, largo)
        cnt = np.bincount(elegidas, minlength=ns).astype(float)
        r1[b], r2[b] = auc_rep(pre[0], cnt), auc_rep(pre[1], cnt)
    dl = r1 - r2
    s = np.sort(dl)
    return dict(delta=a1 - a2, auc1=a1, auc2=a2, deltas=dl, auc1_rep=r1, auc2_rep=r2, lo=float(s[k - 1]), hi=float(s[B - k]), B=B)


def es_clara(jaccard_medio, frio_domina, n_ge, jaccard_frio=None, jaccard_min=None, n_ge_max=None):
    """D-029: clase 'clara' = Jaccard principal >= umbral (D-011) y solución con permutaciones con G >= G_obs no
    mayores que el máximo admitido. El Jaccard principal es el tibio, salvo que la clase esté regida por el frío:
    entonces es el frío (D-017). Estar regida por el frío no descalifica por sí solo."""
    jaccard_min = C.JACCARD_CLARO if jaccard_min is None else jaccard_min
    n_ge_max = C.N_GE_NULO_CLARO if n_ge_max is None else n_ge_max
    if frio_domina:
        assert jaccard_frio is not None, "clase regida por el frío: hace falta su Jaccard frío (D-017)"
        principal = jaccard_frio
    else:
        principal = jaccard_medio
    return bool(principal >= jaccard_min and n_ge <= n_ge_max)


# ------------------------------------------------------------------ regla de los cinco perfiles (D-029)
def veredicto_k5(n_ge, n_claras, n_clases=None):
    """D-029: 'K=5 es la entrega' si la solución tiene permutaciones con G >= G_obs no mayores que
    C.N_GE_NULO_CLARO (p = 0.05) y al menos C.N_CLARAS_MIN_K5 clases claras; si no, 'K=5 no cumple'."""
    return bool(n_ge <= C.N_GE_NULO_CLARO and n_claras >= C.N_CLARAS_MIN_K5)


def etiquetas_entrega_k5(perfil, claras):
    """D-029: perfil (1..K por celda, numerado por % del déficit), claras (lista de perfiles claros).
    Devuelve 'E1','E2',... (claros numerados por % del déficit) y 'resto' para el resto."""
    perfil = np.asarray(perfil)
    num = {p: f"E{i + 1}" for i, p in enumerate(sorted(claras))}
    return np.array([num.get(int(p), "resto") for p in perfil], dtype=object)


# ------------------------------------------------------------------ bootstrap por municipio (D-032)
def delta_auc_bootstrap_grupos(rhat1, despues1, rhat2, despues2, ln, deficit, edo, grupo, sufijo,
                               B=None, nivel=None):
    """D-032: igual que `delta_auc_bootstrap` (D-027; B, percentil, curvas recalculadas por réplica), pero
    remuestrea GRUPOS de celdas (p. ej. municipios, llave `(edo, grupo)`) con reemplazo, estratificado por estado,
    porque las secciones de un mismo municipio no son independientes. `sufijo` (semilla
    [SEMILLA, sufijo]) es obligatorio: cada análisis declara el suyo. Con un grupo por sección coincide
    exactamente con `delta_auc_bootstrap`. Devuelve el mismo dict más `n_grupos`."""
    from ine_perfiles import estabilidad as EST
    B = C.B_PERMANENCIA if B is None else B
    nivel = C.NIVEL_IC_PERMANENCIA if nivel is None else nivel
    ln, d = np.asarray(ln, float), np.asarray(deficit, float)
    dpos = np.clip(d, 0, None)
    n = len(ln)
    assert all(len(v) == n for v in (rhat1, rhat2, edo, grupo))
    k = (B + 1) * (1 - nivel) / 2
    assert abs(k - round(k)) < 1e-9, "(B+1)(1-nivel)/2 debe ser entero"
    k = int(round(k))
    cod = pd.factorize(pd.MultiIndex.from_arrays([np.asarray(edo), np.asarray(grupo)]))[0]
    orden_s, inicio, largo, edo_g = EST.indice_secciones(edo, grupo)
    ng = len(largo)
    m1, m2 = _orden_bloques(rhat1, despues1), _orden_bloques(rhat2, despues2)
    uno = np.ones(n)
    a1 = _auc_pos_bloques(m1[0], m1[1], ln, dpos, uno)
    a2 = _auc_pos_bloques(m2[0], m2[1], ln, dpos, uno)
    pre = [(ln[o], dpos[o], cod[o], ini) for o, ini in (m1, m2)]

    def auc_rep(p, cnt):
        l_o, d_o, c_o, ini = p
        m = cnt[c_o]
        l = np.add.reduceat(l_o * m, ini)
        q = np.add.reduceat(d_o * m, ini)
        x = np.concatenate([[0.0], np.cumsum(l) / l.sum()])
        y = np.concatenate([[0.0], np.cumsum(q) / q.sum()])
        return float(np.sum(np.diff(x) * (y[1:] + y[:-1]) / 2.0))

    rng = np.random.default_rng([C.SEMILLA, sufijo])
    r1, r2 = np.empty(B), np.empty(B)
    for b in range(B):
        elegidas = np.concatenate([rng.choice(np.flatnonzero(edo_g == e), size=int((edo_g == e).sum()), replace=True)
                                   for e in np.unique(edo_g)])
        cnt = np.bincount(elegidas, minlength=ng).astype(float)
        r1[b], r2[b] = auc_rep(pre[0], cnt), auc_rep(pre[1], cnt)
    dl = r1 - r2
    s = np.sort(dl)
    return dict(delta=a1 - a2, auc1=a1, auc2=a2, deltas=dl, auc1_rep=r1, auc2_rep=r2, lo=float(s[k - 1]), hi=float(s[B - k]),
                B=B, n_grupos=ng)
