"""Panel de cohortes: celda sección × sexo × grupo de edad × elección, seguida por generación (D-006, D-007).

Cada celda reúne las cohortes que en 2024 forman su grupo de edad y suma, en cada elección, solo las que ya tenían
18 años o más. Excluye las secciones-año sin observación (D-002) y el sexo no binario (D-005).
Entradas: data/interim/base/{celdas,catalogo_secciones}.parquet y data/processed/cortes_edad.json.
Salidas: data/processed/panel_celda_eleccion.parquet, reports/preparacion/panel_cohortes/control.md
Uso: .venv/bin/python scripts/preparacion/panel_cohortes.py"""
import time

import numpy as np
import pandas as pd

from ine_perfiles import cohortes as B
from ine_perfiles import config as C

SAL = C.salidas(__file__)
T0 = time.time()


def tabla(df, idx=True):
    if idx:
        df = df.reset_index()
    f = lambda v: f"{v:.4g}" if isinstance(v, (float, np.floating)) else str(v)
    L = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    L += ["| " + " | ".join(f(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(L) + "\n"


con = B.conectar()
GR = {g["id"]: g["etiqueta"] for g in B.grupos()}
B.construir_panel(con)
panel = con.execute("SELECT * FROM panel").df()

# conciliación 2024 contra las celdas limpias
rec = con.execute(f"""
WITH cat AS (SELECT edo, seccion FROM read_parquet('{B.CATALOGO}') WHERE ref_anio=2024)
SELECT sum(sv), sum(sv+nv) FROM read_parquet('{B.CELDAS}') c JOIN cat USING (edo, seccion)
WHERE c.aelec=2024 AND c.sexo<2 AND NOT c.sin_observacion""").fetchone()
p24 = panel[panel.aelec == 2024]
concil = (int(p24.sv.sum()), int(p24.n.sum()), int(rec[0]), int(rec[1]))
assert concil[0] == concil[2] and concil[1] == concil[3], concil
assert not panel.duplicated(["edo", "seccion", "sexo", "grupo", "aelec"]).any()
part24 = 100 * concil[0] / concil[1]
assert abs(part24 - C.CIFRAS_CONTROL[2024]["nacional"][0]) <= C.CIFRAS_CONTROL[2024]["nacional"][1], part24

panel = B.ordenar(panel)
panel.to_parquet(B.PANEL, index=False, compression="zstd")

# cobertura: nº de elecciones con votantes (n > 0) por celda
cob = panel[panel.n > 0].groupby(["edo", "seccion", "sexo", "grupo"]).size().rename("n_elecciones").reset_index()
cob["grupo_et"] = cob.grupo.map(GR)
ct = pd.crosstab(cob.grupo_et, cob.n_elecciones, normalize="index") * 100

md = ["# Panel de cohortes (D-006, D-007)", "",
      "## 1. Conciliación 2024", "",
      f"Σ sv panel = {concil[0]:,} vs celdas.parquet = {concil[2]:,}; Σ n panel = {concil[1]:,} vs {concil[3]:,} "
      "(sexo<2, secciones presentes en 2024, sin `sin_observacion`): coinciden exactamente. "
      f"Participación 2024 = {part24:.2f}% (cifra de control 59.67%, D-001).", "",
      f"Filas del panel: {len(panel):,}. Celdas distintas: {panel[['edo', 'seccion', 'sexo', 'grupo']].drop_duplicates().shape[0]:,}.", "",
      "## 2. Elecciones observadas por celda (n > 0)", "",
      "% de celdas por nº de elecciones con votantes. El grupo 18–19 solo existe en 2024: las cohortes que lo forman eran menores de edad antes.", "",
      tabla(ct.round(2)),
      f"Tiempo: {time.time() - T0:.0f} s."]
(SAL / "control.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
