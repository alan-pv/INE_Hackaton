# Contexto de cada sección y movilidad de electores (D-015, D-016)

Marco: 70,751 secciones con LN 2024 (catálogo); LN 2024 total 98,330,348.

## Movilidad robusta (D-016)
- Pares sección×par: 344,910; excluidos por cambio territorial o reseccionamiento: 13,410.
- Pares válidos tras excluir además las secciones marcadas por texto: 331,480.
- Criterio de texto (D-016): OBSERVACIONES de la tabla de equivalencias que contiene `incorpor* tarde` (regex, sin distinguir mayúsculas). La nota no trae año, así que se excluyen todos los pares de la sección marcada. Se revisaron además las notas con `error`, `padron`, `ausencia`: solo 16-2692 dice 'error de dedo', y es una corrección de la propia tabla (no un dato de la sección), por lo que no se marca. Las notas 'podria ser', 'check merge?' son dudas y no se marcan. 25-2187/2188/2189 (D-016) no tienen nota textual: no se marcan.
- Secciones marcadas (4):

| edo | sección | municipio | nota |
|---|---|---|---|
| 17 | 699 | HUEYAPAN | hubo controversia scjn ratifico pero se incorporo tarde---inferi codigo ife y q seccion en |
| 17 | 700 | HUEYAPAN | hubo controversia scjn ratifico pero se incorporo tarde---inferi codigo ife y q seccion en |
| 17 | 701 | HUEYAPAN | hubo controversia scjn ratifico pero se incorporo tarde---inferi codigo ife y q seccion en |
| 17 | 702 | HUEYAPAN | hubo controversia scjn ratifico pero se incorporo tarde---inferi codigo ife y q seccion en |

- Secciones con O/E acumulado: 69,773; pares válidos por sección: mediana 5.
- Mediana del O/E acumulado 0.982; log: p5 -0.073, p95 0.064.
- Municipios con O/E: 2,476 (archivo `data/processed/movilidad_municipio.parquet`).

## Cobertura de descriptores (marco 2024)

| descriptor | % secciones | % LN 2024 |
|---|---|---|
| graproes | 99.99 | 100.00 |
| prop_sin_escolaridad | 99.92 | 99.97 |
| prop_analfabeta | 99.92 | 99.97 |
| prop_posbasica | 99.92 | 99.97 |
| prop_hli | 99.92 | 99.97 |
| prop_afro | 99.92 | 99.97 |
| prop_internet | 99.92 | 99.97 |
| prop_celular | 99.92 | 99.97 |
| prop_nacida_otra_ent | 99.92 | 99.97 |
| prop_res_otra_ent_2015 | 99.92 | 99.97 |
| prop_discapacidad | 99.92 | 99.97 |
| prop_18a24 | 99.92 | 99.97 |
| prop_60ymas | 99.92 | 99.97 |
| razon_ln_p18 | 96.00 | 94.70 |
| iim_dp2 | 99.66 | 99.71 |
| im_2020 | 99.72 | 99.79 |
| imn_2020 | 99.72 | 99.79 |
| pctl_mov_estado | 96.07 | 94.71 |
| oe_mpio | 99.99 | 99.99 |
| circunscripcion | 100.00 | 100.00 |
| tiposec | 100.00 | 100.00 |

Secciones con `eceg_heredado`: 2,775. tiposec es el de la CCPC (D-015).

## Circunscripción (D-024)

Entidades asignadas: 32 de 32; circunscripciones: [1, 2, 3, 4, 5]; entidades por circunscripción: {1: 8, 2: 7, 3: 7, 4: 6, 5: 4}. Secciones del marco sin circunscripción: 0.

Fuente:

- Instituto Nacional Electoral, Consejo General. *Acuerdo INE/CG130/2023 por el que se aprueba la demarcación territorial de las cinco circunscripciones electorales plurinominales federales en que se divide el país y la capital de la entidad federativa que será cabecera de cada una de ellas, a propuesta de la Junta General Ejecutiva* (sesión extraordinaria del 27 de febrero de 2023; se usa a partir del PEF 2023-2024, punto TERCERO). URL: https://repositoriodocumental.ine.mx/xmlui/bitstream/handle/123456789/149740/CGex202302-27-ap-1.pdf. Consultada 2026-10-24. Nivel de evidencia: [O]. Verificado: la tabla del punto PRIMERO (Querétaro pasa de la 2 a la 5 e Hidalgo de la 5 a la 4 respecto del marco anterior) coincide con la usada.
