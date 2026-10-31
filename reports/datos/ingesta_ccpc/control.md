# Ingesta de la CCPC a Parquet (D-003)

Generado en 59 s. Salida: `data/interim/ccpc/aelec=YYYY/` (zstd). Decisiones: D-001, D-003, D-004, D-005.

## SHA-256 de los ZIP

- ConteosCensales2009.zip: OK
- ConteosCensales2012.zip: OK
- ConteosCensales2015.zip: OK
- ConteosCensales2018.zip: OK
- ConteosCensales2021.zip: OK
- ConteosCensales2024.zip: OK

## Conciliación y estadísticas por año

| Año | Filas crudo | Filas escrito | Viol. LN=SV+NV+NS | Secciones (edo,sec) | LN | Part. oficial % | SV/LN % | NS/LN % | def nulos | del nulos | edad min | edad max | LN edad>110 | LN sexo=2 | Secc. NS=LN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2009 | 8,706,843 | 8,706,843 | 0 | 64,934 | 77,481,831 | 44.06 | 43.00 | 2.41 | 28,477 | 28,477 | 18 | 130 | 1,684 | 0 | 1,004 |
| 2012 | 8,604,456 | 8,604,456 | 0 | 65,599 | 76,490,962 | 62.08 | 61.95 | 0.22 | 15,677 | 15,677 | 18 | 132 | 405 | 0 | 82 |
| 2015 | 9,106,059 | 9,106,059 | 0 | 68,362 | 83,563,462 | 47.07 | 44.19 | 6.13 | 0 | 0 | 18 | 117 | 359 | 0 | 2,042 |
| 2018 | 9,251,122 | 9,251,122 | 0 | 68,408 | 89,123,997 | 62.37 | 58.10 | 6.83 | 0 | 0 | 18 | 137 | 305 | 0 | 2,517 |
| 2021 | 9,430,502 | 9,430,502 | 0 | 68,812 | 93,532,133 | 51.84 | 49.60 | 4.32 | 0 | 0 | 18 | 139 | 377 | 0 | 1,693 |
| 2024 | 9,773,730 | 9,773,730 | 0 | 70,751 | 98,330,348 | 59.67 | 55.83 | 6.43 | 0 | 20,912 | 18 | 140 | 227 | 105 | 2,100 |

## Cifras de control (participación = SV/(SV+NV), D-001)

| Año | Grupo | Calculado % | Esperado % | Tol. pts | Resultado |
|---|---|---|---|---|---|
| 2009 | nacional | 44.061 | 44.06 | 0.01 | PASA |
| 2009 | mujeres | 47.349 | 47.35 | 0.01 | PASA |
| 2009 | hombres | 40.528 | 40.53 | 0.01 | PASA |
| 2021 | nacional | 51.838 | 51.84 | 0.01 | PASA |
| 2021 | mujeres | 55.624 | 55.62 | 0.01 | PASA |
| 2021 | hombres | 47.762 | 47.76 | 0.01 | PASA |
| 2024 | nacional | 59.670 | 59.67 | 0.01 | PASA |
| 2024 | mujeres | 64.203 | 64.2 | 0.05 | PASA |
| 2024 | hombres | 54.760 | 54.8 | 0.05 | PASA |
