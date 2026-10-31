"""Cambios territoriales con la tabla de equivalencias (D-015). La marca sale SOLO de la
tabla (sin umbrales). Lectura de columnas idéntica a externos._tabla_equiv: action/orig.dest/when
(1-3). split.from = sección hija (orig.dest = madres, 'a|b'); split.to = sección madre
(orig.dest = hijas, 'a:b' rango o 'a|b'); merged.to = sección dada de baja (dest = receptora);
mun.chg / state.chg = cambio de municipio / entidad."""
import re
from pathlib import Path

import pandas as pd

from . import config as C

RAIZ = C.RAIZ
EQUIV = RAIZ / "data" / "raw" / "externos" / "reseccionamiento" / "tablaEquivalenciasSeccionalesDesde1994.csv"
BASE = RAIZ / "data" / "interim" / "base"
OUT_EVENTOS = BASE / "cambios_territoriales.parquet"
OUT_MARCADA = BASE / "movilidad_seccion_marcada.parquet"
ANIO_MIN, ANIO_MAX = min(C.ANIOS), max(C.ANIOS)  # ventana de las elecciones (D-003)

TIPO_PROPIO = {"split.from": "alta_por_division", "split.to": "division_madre",
               "merged.to": "baja_por_fusion", "mun.chg": "cambio_municipio",
               "state.chg": "cambio_entidad"}
TIPO_CONTRAPARTE = {"split.from": "division_madre", "split.to": "alta_por_division",
                    "merged.to": "fusion_receptora"}


def _numeros(txt):
    """Parsea 'a|b', 'a:b' (rango inclusivo) o 'a' en una lista de enteros."""
    out = []
    for tok in re.split(r"[|,]", txt or ""):
        tok = tok.strip()
        m = re.fullmatch(r"(\d+):(\d+)", tok)
        if m:
            out.extend(range(int(m[1]), int(m[2]) + 1))
        elif tok.isdigit():
            out.append(int(tok))
    return out


def _anio(w, alta, baja, accion):
    m = re.match(r"\d{4}", w or "")
    if m:
        return int(m[0]), False
    # respaldo documentado: split.from -> alta; las demás acciones -> baja (si existe)
    v = alta if accion == "split.from" else baja
    return (v, True) if v else (None, True)


def leer_eventos():
    """Devuelve (eventos, info). eventos: (edo, seccion, anio_evento, tipo_evento, seccion_relacionada)."""
    t = pd.read_csv(EQUIV, dtype=str)
    filas, info = [], {"filas_tabla": len(t), "anio_de_respaldo": 0, "sin_anio": 0}
    t = t.rename(columns={"orig.dest": "od", "orig.dest2": "od2", "orig.dest3": "od3"})
    for _, r in t.iterrows():
        edo, sec = int(r["edon"]), int(r["seccion"])
        alta = int(r["alta"]) if str(r["alta"]).isdigit() else None
        baja = int(r["baja"]) if str(r["baja"]).isdigit() else None
        for a, od, w in ((r["action"], r["od"], r["when"]), (r["action2"], r["od2"], r["when2"]),
                         (r["action3"], r["od3"], r["when3"])):
            if not isinstance(a, str) or a not in TIPO_PROPIO:
                continue
            anio, resp = _anio(w if isinstance(w, str) else None, alta, baja, a)
            if anio is None:
                info["sin_anio"] += 1
                continue
            info["anio_de_respaldo"] += int(resp)
            rel = _numeros(od if isinstance(od, str) else "")
            for s in rel or [None]:
                filas.append((edo, sec, anio, TIPO_PROPIO[a], s))
                if s is not None and a in TIPO_CONTRAPARTE:
                    filas.append((edo, s, anio, TIPO_CONTRAPARTE[a], sec))
    ev = pd.DataFrame(filas, columns=["edo", "seccion", "anio_evento", "tipo_evento", "seccion_relacionada"])
    ev = ev.drop_duplicates()
    ev = ev[(ev.anio_evento >= ANIO_MIN) & (ev.anio_evento <= ANIO_MAX)]
    ev["seccion_relacionada"] = ev["seccion_relacionada"].astype("Int64")
    ev = ev.sort_values(["edo", "seccion", "anio_evento", "tipo_evento", "seccion_relacionada"]).reset_index(drop=True)
    return ev, info


def marcar(con, eventos):
    """movilidad_seccion + cambio_territorial_en_par (evento con e_prev < anio_evento <= e) y
    tipo_evento (lista de tipos distintos). No recalcula la métrica."""
    con.register("ev", eventos)
    con.execute(f"""CREATE OR REPLACE TABLE marcada AS
        WITH h AS (
          SELECT m.e_prev, m.e, m.edo, m.seccion,
                 string_agg(DISTINCT v.tipo_evento, ',' ORDER BY v.tipo_evento) AS tipo_evento
          FROM '{BASE / "movilidad_seccion.parquet"}' m
          JOIN ev v ON v.edo=m.edo AND v.seccion=m.seccion
                   AND v.anio_evento > m.e_prev AND v.anio_evento <= m.e
          GROUP BY ALL)
        SELECT m.*, (h.edo IS NOT NULL) AS cambio_territorial_en_par, h.tipo_evento
        FROM '{BASE / "movilidad_seccion.parquet"}' m
        LEFT JOIN h ON h.e_prev=m.e_prev AND h.e=m.e AND h.edo=m.edo AND h.seccion=m.seccion""")
    con.execute(f"COPY (SELECT * FROM marcada ORDER BY e_prev, edo, seccion) TO '{OUT_MARCADA}' (FORMAT parquet, COMPRESSION zstd)")
