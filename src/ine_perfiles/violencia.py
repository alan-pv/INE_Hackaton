"""Violencia homicida municipal (D-027).

Fuente: INEGI, Estadísticas de defunciones registradas (microdatos / datos abiertos).
Se cuenta por año de OCURRENCIA y municipio de ocurrencia (D-027). Cada edición de
registro se lee por separado y las ediciones son disjuntas (cada defunción está en la
edición de su año de registro); se suman todas las que traen ocurrencias de cada año.
Tasa = Σ homicidios / (población Censo 2020 × años); contracción Poisson-gamma hacia la
tasa del estado con dispersión por máxima verosimilitud (D-027, igual que D-009/D-022)."""
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

from . import config as C
from . import externos as X

RAW_DEF = X.RAW_EXT / "inegi_defunciones"
OUT_AGREGADO = X.INT_EXT / "defunciones_agregadas.parquet"
OUT_VIOLENCIA = X.INT_EXT / "violencia_mpio.parquet"
URL_BASE = "https://www.inegi.org.mx/contenidos"

# Ediciones: (año de registro, ruta lógica en INEGI, nombre del zip, formato, ruta interna del dato)
_G = "/programas/edr/datosabiertos/defunciones"
_D = "/programas/edr/microdatos/defunciones/datos"
EDICIONES = (
    [(2009, f"{_D}/defunciones_generales_base_datos_2005_2009_dbf.zip", "dbf",
      "defunciones_base_datos_2009_dbf/DEFUN09.dbf")]
    + [(a, f"{_D}/defunciones_generales_base_datos_2010_2014_dbf.zip", "dbf",
        f"defunciones_base_datos_{a}_dbf/DEFUN{a % 100}.dbf") for a in (2010, 2011)]
    + [(2012, f"{_G}/2012/defunciones_base_datos_2012_csv.zip", "csv", "conjunto_de_datos/defunciones_generales_2012.csv"),
       (2013, f"{_G}/2013/defunciones_base_datos_2013_csv.zip", "csv", "conjunto_de_datos/defunciones_generales_2013.csv"),
       (2014, f"{_G}/2014/defunciones_base_datos_2014_csv.zip", "csv", "conjunto_de_datos/defunciones_generales_2014.csv"),
       (2015, f"{_G}/2015/defunciones_base_datos_2015_csv.zip", "csv", "conjunto_de_datos/defunciones_generales_2015.csv"),
       (2016, f"{_G}/2016/defunciones_base_datos_2016_csv.zip", "csv", "conjunto_de_datos/defunciones_generales_2016.csv"),
       (2017, f"{_G}/2017/conjunto_de_datos_defunciones_generales_2017_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_generales_2017.CSV"),
       (2018, f"{_G}/2018/conjunto_de_datos_defunciones_registradas_2018_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_registradas_2018.CSV"),
       (2019, f"{_G}/2019/conjunto_de_datos_defunciones_registradas_2019_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_registradas_2019.CSV"),
       (2020, f"{_G}/2020/conjunto_de_datos_defunciones_registradas_2020_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_registrados_2020.csv"),
       (2021, f"{_G}/2021/conjunto_de_datos_defunciones_registradas_2021_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_registradas_2021.csv"),
       (2022, f"{_G}/2022/conjunto_de_datos_defunciones_registradas_2022_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_registradas_2022.csv"),
       (2023, f"{_G}/2023/conjunto_de_datos_defunciones_registradas_2023_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_registradas_2023_csv.CSV"),
       (2024, f"{_G}/2024/conjunto_de_datos_edr2024_csv.zip", "csv",
        "conjunto_de_datos/conjunto_de_datos_defunciones_registradas24_csv.csv")]
)


def zip_de(ruta):
    return RAW_DEF / Path(ruta).name


def descargar(log=print):
    """Descarga los zip que falten (idempotente). Los archivos no se modifican ni se ejecutan."""
    import subprocess
    RAW_DEF.mkdir(parents=True, exist_ok=True)
    for ruta in dict.fromkeys(e[1] for e in EDICIONES):
        z = zip_de(ruta)
        if z.exists() and z.stat().st_size > 0:
            continue
        log(f"descargando {ruta}")
        tmp = z.with_suffix(".part")
        subprocess.run(["curl", "-sfL", "-A", "Mozilla/5.0", "-o", str(tmp), URL_BASE + ruta], check=True)
        if tmp.read_bytes()[:2] != b"PK":  # INEGI responde HTML 200 si la liga no existe
            tmp.unlink()
            raise RuntimeError(f"no es un zip: {ruta}")
        tmp.rename(z)


def _leer_edicion(edicion, ruta, fmt, interno):
    """Lee una edición y devuelve filas (ent, mun, anio_ocur, anio_regis, hom) como enteros."""
    z = zip_de(ruta)
    if fmt == "dbf":
        import pyogrio
        d = pyogrio.read_dataframe(f"/vsizip/{z}/{interno}", read_geometry=False, use_arrow=False)
        d.columns = [c.lower() for c in d.columns]
    else:
        with zipfile.ZipFile(z) as zf, zf.open(interno) as h:
            d = pd.read_csv(h, dtype=str, encoding="latin1", low_memory=False)
        d.columns = [c.lower().lstrip("﻿") for c in d.columns]
    var = "tipo_defun" if "tipo_defun" in d.columns else "presunto"
    num = lambda s: pd.to_numeric(s.astype(str).str.strip(), errors="coerce")
    out = pd.DataFrame({"ent": num(d["ent_ocurr"]), "mun": num(d["mun_ocurr"]),
                        "anio_ocur": num(d["anio_ocur"]), "anio_regis": num(d["anio_regis"]),
                        "hom": num(d[var]) == C.CODIGO_HOMICIDIO})
    return out, var


def agregar_ediciones(log=print):
    """Agrega cada edición por (ocurrencia: ent, mun, año). Devuelve (tabla, control por edición).
    n_def = todas las defunciones, n_hom = presuntos homicidios (D-027)."""
    partes, ctrl = [], []
    for ed, ruta, fmt, interno in EDICIONES:
        d, var = _leer_edicion(ed, ruta, fmt, interno)
        fuera_ed = int((d.anio_regis != ed).sum())  # control de ediciones disjuntas
        g = (d.fillna({"ent": -1, "mun": -1, "anio_ocur": -1}).groupby(["ent", "mun", "anio_ocur"])
             .agg(n_def=("hom", "size"), n_hom=("hom", "sum")).reset_index())
        g.insert(0, "edicion", ed)
        partes.append(g)
        ctrl.append({"edicion": ed, "variable": var, "filas": len(d), "homicidios": int(d.hom.sum()),
                     "filas_con_anio_regis_distinto": fuera_ed})
        log(f"edición {ed}: {len(d)} filas, {int(d.hom.sum())} homicidios ({var})")
    return pd.concat(partes, ignore_index=True), pd.DataFrame(ctrl)


def cargar_agregado(log=print):
    """Agregado por ediciones, con caché en Parquet (se regenera si falta)."""
    ctrl_p = OUT_AGREGADO.with_name("defunciones_control.parquet")
    if OUT_AGREGADO.exists() and ctrl_p.exists():
        return pd.read_parquet(OUT_AGREGADO), pd.read_parquet(ctrl_p)
    X.INT_EXT.mkdir(parents=True, exist_ok=True)
    agg, ctrl = agregar_ediciones(log)
    agg.to_parquet(OUT_AGREGADO, compression="zstd")
    ctrl.to_parquet(ctrl_p)
    return agg, ctrl


# ---------------------------------------------------------------- conteos por municipio
def clasificar(agg, anio_ini, anio_fin):
    """Clasifica los homicidios del agregado en una ventana de años de ocurrencia.
    Devuelve (conteos por (ent, mun, año) de lo especificado, resumen de no especificados)."""
    h = agg[agg.n_hom > 0]
    ent_ne, mun_ne = h.ent.eq(C.NO_ESP_ENT) | h.ent.lt(0), h.mun.eq(C.NO_ESP_MUN) | h.mun.lt(0)
    anio_ne = h.anio_ocur.eq(C.NO_ESP_ANIO) | h.anio_ocur.lt(0)
    en_vent = h.anio_ocur.between(anio_ini, anio_fin)
    res = {"total_todas_ocurrencias": int(h.n_hom.sum()),
           "anio_no_especificado": int(h[anio_ne].n_hom.sum()),
           "fuera_de_ventana": int(h[~anio_ne & ~en_vent].n_hom.sum()),
           "en_ventana": int(h[en_vent].n_hom.sum()),
           "en_ventana_ent_no_esp": int(h[en_vent & ent_ne].n_hom.sum()),
           "en_ventana_mun_no_esp": int(h[en_vent & ~ent_ne & mun_ne].n_hom.sum())}
    ok = h[en_vent & ~ent_ne & ~mun_ne]
    c = ok.groupby(["ent", "mun", "anio_ocur"], as_index=False).n_hom.sum()
    return c.astype({"ent": int, "mun": int, "anio_ocur": int}), res


def primera_aparicion(agg, anio_ini):
    """Primer año (≥ anio_ini) con alguna defunción registrada en el municipio de ocurrencia.
    Estima desde cuándo existe un municipio creado después de 2009 (D-027, decisión de cómputo)."""
    d = agg[(agg.n_def > 0) & (agg.anio_ocur >= anio_ini) & (agg.anio_ocur < C.NO_ESP_ANIO)
            & (agg.mun != C.NO_ESP_MUN) & (agg.ent != C.NO_ESP_ENT) & (agg.ent > 0) & (agg.mun > 0)]
    f = d.groupby(["ent", "mun"], as_index=False).anio_ocur.min().rename(columns={"anio_ocur": "primer_anio"})
    return f.assign(cve_geo=lambda x: x.ent.astype(int).map("{:02d}".format) + x.mun.astype(int).map("{:03d}".format))


# ---------------------------------------------------------------- contracción Poisson-gamma
def _logver_nb(logphi, O, E, mu):
    """-logverosimilitud de la binomial negativa marginal: O ~ Poisson(E·λ), λ ~ Gamma(media μ,
    varianza φμ²), es decir k = 1/φ: NB con media Eμ y parámetro de tamaño k."""
    k = np.exp(-logphi)
    m = E * mu
    ll = (gammaln(O + k) - gammaln(k) - gammaln(O + 1) + k * (np.log(k) - np.log(k + m))
          + O * (np.log(m) - np.log(k + m)))
    return -float(np.sum(ll))


def estimar_dispersion(O, E, mu, cotas=(-12.0, 12.0)):
    """MLE de φ (varianza relativa de λ) con media μ conocida. Devuelve (φ, en_frontera).
    Se optimiza log φ en `cotas` (solo de cómputo, ±12 ≈ 6e-6 .. 1.6e5); si el óptimo cae en
    la cota, la verosimilitud es monótona (sin información) y se marca `en_frontera`."""
    O, E = np.asarray(O, float), np.asarray(E, float)
    if len(O) < 2 or mu <= 0:
        return float("nan"), True
    r = minimize_scalar(lambda t: _logver_nb(t, O, E, mu), bounds=cotas, method="bounded",
                        options={"xatol": 1e-8})
    return float(np.exp(r.x)), bool(min(abs(r.x - cotas[0]), abs(r.x - cotas[1])) < 1e-3)


def contraer(O, E, mu, phi):
    """Media posterior de λ: μ(O+k)/(Eμ+k) con k=1/φ  =  w·(O/E) + (1-w)·μ, w = φEμ/(1+φEμ).
    φ→∞: tasa cruda; φ→0: tasa del estado (D-027). Acepta φ=inf y φ=0."""
    O, E, mu = np.asarray(O, float), np.asarray(E, float), np.asarray(mu, float)
    if np.isinf(phi):
        w = np.ones_like(E)
    else:
        a = phi * E * mu
        w = a / (1.0 + a)
    cruda = np.divide(O, E, out=np.zeros_like(O), where=E > 0)
    return w * cruda + (1 - w) * mu


def tasa_contraida(df, col_o="homicidios", col_e="exposicion", grupo="edo"):
    """Añade tasa_cruda, tasa_estado, phi, tasa_contr (por habitante-año). φ por estado;
    si el MLE del estado cae en la frontera se usa el nacional (decisión de cómputo a ratificar).
    Devuelve (df, tabla de dispersiones)."""
    df = df.copy()
    est = df.groupby(grupo).agg(O=(col_o, "sum"), E=(col_e, "sum"))
    df["tasa_estado"] = df[grupo].map(est.O / est.E)
    df["tasa_cruda"] = df[col_o] / df[col_e]
    # φ nacional: media de cada observación = tasa de su estado
    mu_obs = df.tasa_estado.to_numpy()
    r = minimize_scalar(lambda t: _logver_nb(t, df[col_o].to_numpy(float), df[col_e].to_numpy(float), mu_obs),
                        bounds=(-12.0, 12.0), method="bounded", options={"xatol": 1e-8})
    phi_nac = float(np.exp(r.x))
    filas = []
    for g, s in df.groupby(grupo):
        phi, front = estimar_dispersion(s[col_o], s[col_e], float(est.loc[g, "O"] / est.loc[g, "E"]))
        cae = front or not np.isfinite(phi)
        filas.append({grupo: g, "n_mpios": len(s), "phi_estado": phi, "en_frontera": front,
                      "phi_usado": phi_nac if cae else phi, "fuente": "nacional" if cae else "estado"})
    tab = pd.DataFrame(filas)
    df["phi"] = df[grupo].map(tab.set_index(grupo).phi_usado)
    df["tasa_contr"] = np.nan
    for g, ix in df.groupby(grupo).groups.items():
        s = df.loc[ix]
        df.loc[ix, "tasa_contr"] = contraer(s[col_o], s[col_e], s.tasa_estado.iloc[0], s.phi.iloc[0])
    return df, tab, phi_nac


# ---------------------------------------------------------------- tabla final
def construir(agg, mapa, pob):
    """Tabla por municipio INE (edo, mpio) para las ventanas de D-027.
    `mapa`: DataFrame (edo, mpio, cve_geo); `pob`: DataFrame (edo, mpio, pob_tot_conapo).
    Años de exposición: desde max(inicio de ventana, primera aparición del municipio) hasta el fin."""
    base = mapa.merge(pob, on=["edo", "mpio"], how="inner")
    pa = primera_aparicion(agg, min(v[0] for v in C.VENTANAS_VIOLENCIA.values()))[["cve_geo", "primer_anio"]]
    base = base.merge(pa, on="cve_geo", how="left")
    res, tabs, auditoria = base[["edo", "mpio", "cve_geo", "pob_tot_conapo", "primer_anio"]].copy(), {}, {}
    for nom, (ini, fin) in C.VENTANAS_VIOLENCIA.items():
        cont, resumen = clasificar(agg, ini, fin)
        cont["cve_geo"] = cont.ent.map("{:02d}".format) + cont.mun.map("{:03d}".format)
        tot = cont.groupby("cve_geo", as_index=False).n_hom.sum()
        b = base[["edo", "mpio", "cve_geo", "pob_tot_conapo", "primer_anio"]].merge(tot, on="cve_geo", how="left")
        b["n_hom"] = b.n_hom.fillna(0)
        # municipio sin ninguna defunción en la ventana: sin exposición observable -> se descarta y se reporta
        b["anio0"] = b.primer_anio.clip(lower=ini).fillna(ini)
        b["anios"] = (fin - b.anio0 + 1).clip(lower=0)
        b["exposicion"] = b.pob_tot_conapo * b.anios
        sin_exp = b[(b.exposicion <= 0) | b.pob_tot_conapo.isna()]
        b = b[(b.exposicion > 0) & b.pob_tot_conapo.notna()].copy()
        b = b.rename(columns={"n_hom": "homicidios"})
        b, tab, phi_nac = tasa_contraida(b)
        res = res.merge(b[["cve_geo", "homicidios", "anios", "tasa_cruda", "tasa_contr"]]
                        .rename(columns={"homicidios": f"hom_{nom}", "anios": f"anios_{nom}",
                                         "tasa_cruda": f"tasa_cruda_{nom}", "tasa_contr": f"tasa_contr_{nom}"}),
                        on="cve_geo", how="left")
        res[f"tasa_cruda_{nom}"] *= C.POR_HABITANTES
        res[f"tasa_contr_{nom}"] *= C.POR_HABITANTES
        res[f"log_tasa_contr_{nom}"] = np.log(res[f"tasa_contr_{nom}"] / C.POR_HABITANTES)  # log de tasa por habitante-año
        usados = set(cont.cve_geo) & set(b.cve_geo)
        no_map = cont[~cont.cve_geo.isin(set(base.cve_geo))]
        resumen.update({"homicidios_mapeados": int(b.homicidios.sum()),
                        "homicidios_mun_sin_mapear": int(no_map.n_hom.sum()),
                        "n_claves_sin_mapear": int(no_map.cve_geo.nunique()),
                        "n_mpios_sin_exposicion": len(sin_exp)})
        tabs[nom], auditoria[nom] = tab.assign(phi_nacional=phi_nac), (resumen, no_map)
    return res.rename(columns={"pob_tot_conapo": "poblacion"}), tabs, auditoria
