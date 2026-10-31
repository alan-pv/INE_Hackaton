"""Contexto de cada sección: indicadores del Censo, CONAPO y llegada o salida de electores (D-010, D-015, D-016).
Salidas: data/processed/{descriptores_seccion,movilidad_municipio}.parquet, reports/preparacion/contexto_seccion/control.md
Uso: .venv/bin/python scripts/preparacion/contexto_seccion.py"""

import pandas as pd

from ine_perfiles import descriptores as D
from ine_perfiles import config as C

mov = pd.read_parquet(D.BASE / "movilidad_seccion_marcada.parquet")
cat = pd.read_parquet(D.BASE / "catalogo_secciones.parquet")
marcadas = D.marcar_observaciones()
pares = D.filtrar_pares_validos(mov, marcadas)
sec = D.oe_acumulado(pares)
sec["pctl_mov_estado"] = D.percentil_en_estado(sec)
mun = D.oe_municipio(pares, cat)
D.PROC.mkdir(parents=True, exist_ok=True)
mun.to_parquet(D.PROC / "movilidad_municipio.parquet", index=False)

marco = cat[cat["ln_2024"].notna()][["edo", "seccion", "mpio_2024", "tiposec_2024", "ln_2024"]].rename(
    columns={"mpio_2024": "mpio", "tiposec_2024": "tiposec"})
marco["circunscripcion"] = marco["edo"].map(D.CIRCUNSCRIPCION_POR_EDO)
eceg = pd.read_parquet(D.EXT / "eceg_seccion2024.parquet")[["edo", "seccion"] + D.COLS_ECEG + ["eceg_heredado"]]
res = pd.read_parquet(D.EXT / "residencia_seccion.parquet")[["edo", "seccion", "razon_ln_p18"]]
con = pd.read_parquet(D.EXT / "conapo_mpio_ine.parquet")[["edo", "mpio"] + D.COLS_CONAPO]
d = (marco.merge(eceg, on=["edo", "seccion"], how="left").merge(res, on=["edo", "seccion"], how="left")
     .merge(con, on=["edo", "mpio"], how="left")
     .merge(sec[["edo", "seccion", "oe_acum", "log_oe", "n_pares", "pctl_mov_estado"]], on=["edo", "seccion"], how="left")
     .merge(mun[["edo", "mpio", "oe_mpio"]], on=["edo", "mpio"], how="left"))
assert d.duplicated(["edo", "seccion"]).sum() == 0
d.to_parquet(D.PROC / "descriptores_seccion.parquet", index=False)

# cobertura
ln = d["ln_2024"]
cob = []
for c in D.COLS_ECEG + ["razon_ln_p18"] + D.COLS_CONAPO + ["pctl_mov_estado", "oe_mpio", "circunscripcion", "tiposec"]:
    ok = d[c].notna()
    cob.append((c, 100 * ok.mean(), 100 * ln[ok].sum() / ln.sum()))
circ = pd.Series(D.CIRCUNSCRIPCION_POR_EDO)
with open(C.salidas(__file__) / "control.md", "w") as f:
    w = lambda s="": f.write(s + "\n")
    w("# Contexto de cada sección y movilidad de electores (D-015, D-016)\n")
    w(f"Marco: {len(d):,} secciones con LN 2024 (catálogo); LN 2024 total {ln.sum():,.0f}.\n")
    w("## Movilidad robusta (D-016)")
    n0 = len(mov)
    ex_terr = (mov["cambio_territorial_en_par"].fillna(False) | mov["reseccionada_en_par"].fillna(False)).sum()
    w(f"- Pares sección×par: {n0:,}; excluidos por cambio territorial o reseccionamiento: {ex_terr:,}.")
    w(f"- Pares válidos tras excluir además las secciones marcadas por texto: {len(pares):,}.")
    w("- Criterio de texto (D-016): OBSERVACIONES de la tabla de equivalencias que contiene `incorpor* tarde` (regex, sin distinguir mayúsculas). "
      "La nota no trae año, así que se excluyen todos los pares de la sección marcada. "
      "Se revisaron además las notas con `error`, `padron`, `ausencia`: solo 16-2692 dice 'error de dedo', y es una corrección de la propia tabla "
      "(no un dato de la sección), por lo que no se marca. Las notas 'podria ser', 'check merge?' son dudas y no se marcan. "
      "25-2187/2188/2189 (D-016) no tienen nota textual: no se marcan.")
    w(f"- Secciones marcadas ({len(marcadas)}):\n")
    w("| edo | sección | municipio | nota |\n|---|---|---|---|")
    for _, r in marcadas.iterrows():
        w(f"| {r.edo} | {r.seccion} | {r.mun} | {r.observacion[:90]} |")
    w()
    w(f"- Secciones con O/E acumulado: {sec['oe_acum'].notna().sum():,}; pares válidos por sección: mediana {sec['n_pares'].median():.0f}.")
    w(f"- Mediana del O/E acumulado {sec['oe_acum'].median():.3f}; log: p5 {sec['log_oe'].quantile(.05):.3f}, p95 {sec['log_oe'].quantile(.95):.3f}.")
    w(f"- Municipios con O/E: {len(mun):,} (archivo `data/processed/movilidad_municipio.parquet`).\n")
    w("## Cobertura de descriptores (marco 2024)\n")
    w("| descriptor | % secciones | % LN 2024 |\n|---|---|---|")
    for c, a, b in cob:
        w(f"| {c} | {a:.2f} | {b:.2f} |")
    w(f"\nSecciones con `eceg_heredado`: {int(d['eceg_heredado'].fillna(False).sum()):,}. tiposec es el de la CCPC (D-015).\n")
    w("## Circunscripción (D-024)\n")
    w(f"Entidades asignadas: {len(circ)} de 32; circunscripciones: {[int(x) for x in sorted(circ.unique())]}; "
      f"entidades por circunscripción: {circ.value_counts().sort_index().to_dict()}. "
      f"Secciones del marco sin circunscripción: {int(d['circunscripcion'].isna().sum())}.\n")
    w("Fuente:\n")
    w("- Instituto Nacional Electoral, Consejo General. *Acuerdo INE/CG130/2023 por el que se aprueba la demarcación territorial de las cinco "
      "circunscripciones electorales plurinominales federales en que se divide el país y la capital de la entidad federativa que será cabecera de "
      "cada una de ellas, a propuesta de la Junta General Ejecutiva* (sesión extraordinaria del 27 de febrero de 2023; se usa a partir del PEF 2023-2024, punto TERCERO). "
      "URL: https://repositoriodocumental.ine.mx/xmlui/bitstream/handle/123456789/149740/CGex202302-27-ap-1.pdf. Consultada 2026-10-24. Nivel de evidencia: [O]. "
      "Verificado: la tabla del punto PRIMERO (Querétaro pasa de la 2 a la 5 e Hidalgo de la 5 a la 4 respecto del marco anterior) coincide con la usada.")
print("ok")
