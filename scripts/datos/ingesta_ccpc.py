"""Ingesta de la CCPC 2009–2024 a Parquet, un año a la vez con conciliación de filas (D-003).
Verifica el SHA-256 de cada ZIP descargado y escribe data/interim/ccpc/aelec=AAAA/.
Salidas: reports/datos/ingesta_ccpc/control.md
Uso: .venv/bin/python scripts/datos/ingesta_ccpc.py"""
import hashlib
import sys
import time

from ine_perfiles import config as C
from ine_perfiles.ingesta import ingestar_todo, conectar


def verificar_sha256():
    filas = []
    for linea in C.SHA256SUMS.read_text().splitlines():
        if not linea.strip():
            continue
        esperado, nombre = linea.split(maxsplit=1)
        nombre = nombre.strip().lstrip("*")
        h = hashlib.sha256()
        with open(C.RAW_CCPC / nombre, "rb") as f:
            for bloque in iter(lambda: f.read(1 << 24), b""):
                h.update(bloque)
        filas.append((nombre, h.hexdigest() == esperado))
    if not all(ok for _, ok in filas):
        raise RuntimeError(f"SHA-256 no coincide: {[n for n, ok in filas if not ok]}")
    return filas


def main():
    t0 = time.time()
    sha = verificar_sha256()
    conc = ingestar_todo()
    con = conectar()
    q = lambda s: con.execute(s).fetchall()

    est = q("""SELECT aelec, count(DISTINCT (edo, seccion)), sum(ln), sum(sv), sum(nv), sum(ns),
        sum((def IS NULL)::INT), sum(("del" IS NULL)::INT), min(edad), max(edad),
        sum(CASE WHEN edad>110 THEN ln ELSE 0 END), sum(CASE WHEN sexo=2 THEN ln ELSE 0 END)
        FROM ccpc GROUP BY 1 ORDER BY 1""")
    ns_ln = dict(q("""SELECT aelec, count(*) FROM (SELECT aelec, edo, seccion FROM ccpc
        GROUP BY ALL HAVING sum(ns)=sum(ln) AND sum(ln)>0) GROUP BY 1"""))
    sexo = {(a, s): (sv, nv) for a, s, sv, nv in q(
        "SELECT aelec, sexo, sum(sv), sum(nv) FROM ccpc GROUP BY 1,2")}
    cruda = {c["anio"]: c for c in conc}

    L = ["# Ingesta de la CCPC a Parquet (D-003)", "",
         f"Generado en {time.time()-t0:.0f} s. Salida: `data/interim/ccpc/aelec=YYYY/` (zstd). Decisiones: D-001, D-003, D-004, D-005.", "",
         "## SHA-256 de los ZIP", ""]
    L += [f"- {n}: {'OK' if ok else 'FALLA'}" for n, ok in sha]
    L += ["", "## Conciliación y estadísticas por año", "",
          "| Año | Filas crudo | Filas escrito | Viol. LN=SV+NV+NS | Secciones (edo,sec) | LN | Part. oficial % | SV/LN % | NS/LN % | def nulos | del nulos | edad min | edad max | LN edad>110 | LN sexo=2 | Secc. NS=LN |",
          "|" + "---|" * 16]
    for a, ns_, ln, sv, nv, ns, dn, dl, emin, emax, l110, l2 in est:
        c = cruda[a]
        L.append(f"| {a} | {c['crudo']:,} | {c['escrito']:,} | {c['violaciones_ln']} | {ns_:,} | {ln:,} | "
                 f"{100*sv/(sv+nv):.2f} | {100*sv/ln:.2f} | {100*ns/ln:.2f} | {dn:,} | {dl:,} | {emin} | {emax} | "
                 f"{l110:,} | {l2:,} | {ns_ln.get(a, 0):,} |")
    L += ["", "## Cifras de control (participación = SV/(SV+NV), D-001)", "",
          "| Año | Grupo | Calculado % | Esperado % | Tol. pts | Resultado |", "|---|---|---|---|---|---|"]
    todo_ok = True
    for a, cc in sorted(C.CIFRAS_CONTROL.items()):
        for clave, s in (("nacional", None), ("mujeres", C.SEXO_MUJER), ("hombres", C.SEXO_HOMBRE)):
            if s is None:
                sv = sum(v[0] for (aa, _), v in sexo.items() if aa == a)
                nv = sum(v[1] for (aa, _), v in sexo.items() if aa == a)
            else:
                sv, nv = sexo[(a, s)]
            val = 100 * sv / (sv + nv)
            esp, tol = cc[clave]
            ok = abs(val - esp) <= tol
            todo_ok &= ok
            L.append(f"| {a} | {clave} | {val:.3f} | {esp} | {tol} | {'PASA' if ok else 'FALLA'} |")
    (C.salidas(__file__) / "control.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nTiempo total: {time.time()-t0:.1f} s")
    if not todo_ok:
        sys.exit("Alguna cifra de control FALLA")


if __name__ == "__main__":
    main()
