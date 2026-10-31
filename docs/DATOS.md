# Datos

El proyecto usa **solo datos agregados y públicos**. No se procesa ningún dato personal (D-005). Las descargas originales van en `data/raw/` y no se suben al repositorio por su tamaño (unos 4.5 GB). Hay dos excepciones que sí se suben, porque son pequeñas y las armó el equipo: la lista de SHA-256 de la CCPC y la tabla de gubernaturas concurrentes.

## Dónde va cada archivo

| Fuente | Carpeta en `data/raw/` | Qué usa el código |
|---|---|---|
| CCPC 2009–2024 (INE) | `ccpc/` | Un ZIP por elección y su carpeta descomprimida `DatosAbiertos_DECEyEC_ConteosCensales{AÑO}/`; `SHA256SUMS` (incluido) |
| Censo 2020 a escala de sección, ECEG 2020 (INEGI) | `externos/inegi_eceg2020/` | `conjunto_de_datos/INE_SECCION_2020.csv` y `catalogos/cat_municipios_2020_INEGI-INE-ECEG.xlsx` |
| Índice de marginación 2020 (CONAPO) | `externos/conapo/` | `IMM_2020.xlsx` |
| Índice de intensidad migratoria México–EE. UU. 2020 (CONAPO) | `externos/conapo/` | `iim_base2020m.csv` |
| Tabla de equivalencias seccionales desde 1994 | `externos/reseccionamiento/` | `tablaEquivalenciasSeccionalesDesde1994.csv` |
| Gubernaturas concurrentes 2009–2024 | `externos/concurrencia/` | `concurrencia_2009_2024.csv` (incluido; armado por el equipo con fuentes oficiales por fila) |
| Defunciones registradas (INEGI) | `externos/inegi_defunciones/` | Microdatos 2009–2024; `scripts/datos/violencia_municipio.py` los descarga si faltan |
| Cartografía de secciones 2018 | `externos/cartografia/secciones_2018_mxDistritos/` | Solo para los mapas municipales del documento |

## Fuentes y enlaces de descarga

**Conteos Censales de Participación Ciudadana (CCPC), INE.** Una fila por sección × sexo × edad × elección federal, con lista nominal (LN), sí votó (SV), no votó (NV) y no especificado (NS).
- 2009, 2012, 2015, 2018 y 2021: `https://ine.mx/wp-content/uploads/2022/04/DatosAbiertos_DECEyEC_ConteosCensales{AÑO}.zip`
- 2024: `https://ine.mx/wp-content/uploads/2025/08/DatosAbiertos_DECEyEC_ConteosCensales2024.zip`
- Participación oficial = SV / (SV + NV) (D-001). Con esta fórmula se reproducen las cifras publicadas: 59.67% en 2024, 51.84% en 2021 y 44.06% en 2009.

**Estadísticas Censales a Escalas Geoelectorales 2020 (ECEG 2020), INEGI.** Indicadores del Censo 2020 por sección electoral (escolaridad, lengua indígena, internet, lugar de nacimiento, edad). https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/geoelectorales/eceg_2020_csv.zip

**CONAPO.**
- Índice de marginación municipal 2020: https://conapo.segob.gob.mx/work/models/CONAPO/Datos_Abiertos/Municipio/IMM_2020.xlsx
- Índice de intensidad migratoria municipal 2020: https://conapo.segob.gob.mx/work/models/CONAPO/IIM/iim_base2020m.csv

**Reseccionamiento.** Tabla de equivalencias seccionales desde 1994, de E. Magar (ITAM), compilada a partir de los acuerdos de reseccionamiento del INE: https://github.com/emagar/mxDistritos

**Cartografía.** Secciones del mapa federal 2018 (fuente INE), del mismo repositorio de E. Magar: https://github.com/emagar/mxDistritos

**Gubernaturas concurrentes.** Tabla armada a mano con una fuente por fila (columna `fuente_url`); solo se usa la bandera de gubernatura, que es la única verificada (D-015).

**Defunciones por homicidio, INEGI.** Estadísticas de defunciones registradas (microdatos): https://www.inegi.org.mx/programas/edr/. El homicidio es el "presunto homicidio" del certificado de defunción, por municipio de ocurrencia (D-027). Para contrastar los totales anuales se usan:
- INEGI (2020). *Defunciones por homicidio, 2019 (preliminar)*. https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2020/EstSociodemo/Defcioneshomicidio2019.pdf
- INEGI (2021). *Estadística de defunciones registradas 2020 (resultados definitivos)*. https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2021/EstSociodemo/DefuncionesRegistradas2020definit.docx
- INEGI (2023). *Defunciones por homicidio, enero a diciembre de 2022 (preliminar)*. https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2023/DH/DH2022.pdf
- Para 2009–2011 y 2024 no se localizó un boletín oficial; se citan los totales publicados en prensa (La Opinión y Excélsior) y se marcan así en el reporte de control.

**Circunscripciones electorales.** Acuerdo INE/CG130/2023 (vigente desde el proceso 2023–2024): https://repositoriodocumental.ine.mx/xmlui/bitstream/handle/123456789/149740/CGex202302-27-ap-1.pdf

## Advertencias sobre los datos

- **Son conteos, no personas.** La unidad mínima es un grupo sección × sexo × edad; la mediana de LN por fila es de 6 a 7 personas, por eso las tasas se contraen (D-009) y los perfiles agrupan celdas, nunca personas.
- **El número de sección no es único en el país.** La llave es (estado, sección).
- **El NS no es homogéneo:** 6.4% nacional en 2024, pero cerca de 15% en Chihuahua, Campeche y Coahuila. Se trata con dos cotas (D-031).
- **La sección es la del domicilio de la credencial.** Quien se mudó sin actualizarla aparece como abstencionista donde ya no vive (D-013).
- **Las secciones cambian con el tiempo** por reseccionamiento; se marcan con la tabla de equivalencias (D-015, D-016).
- **Sexo no binario:** solo existe en 2024 y son 105 registros en todo el país; se reporta solo como cifra nacional (D-005).
