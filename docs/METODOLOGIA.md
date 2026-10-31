# Metodología

Este documento explica el método y registra cada decisión que lo define. El código cita estas decisiones con su número (`# D-xxx`), para que cualquier parámetro se pueda rastrear hasta su justificación. La explicación completa, con referencias bibliográficas, está en `entregables/documento_tecnico.pdf`.

## El método en cinco pasos

1. **Seguir a cada grupo en el tiempo.** La unidad es la celda sección × sexo × grupo de edad. Cada celda se sigue por generación en las seis elecciones federales de 2009 a 2024 (D-006, D-007).
2. **Compararla con lo esperado.** Lo esperado de una celda es la participación nacional de su misma generación y sexo en cada elección. La diferencia, contraída para que las celdas pequeñas no exageren, es su **brecha** (D-009, D-022).
3. **Definir la población objetivo.** Son las celdas con más probabilidad de estar por debajo de lo esperado que por encima. Representan el 48% de las celdas y el 52% de la lista nominal, y dejan de emitir 3.7 millones de votos por elección (D-022).
4. **Dividir esa población en perfiles.** Se usa una mezcla de clases latentes con variables mixtas, ponderada por votos faltantes. Combina quiénes son (sexo, edad), dónde están (circunscripción, tipo de sección), qué tan grave es su brecha y el contexto de su sección (D-024). Se entregan **cinco perfiles**: es el mayor número que pasa las tres pruebas fijadas de antemano (D-029).
5. **Probar el resultado.** Se mide si los perfiles, ajustados solo con 2009–2021, anticipan el déficit de 2024 (D-025). También se prueba su sensibilidad a la gubernatura concurrente y al NS (D-030, D-031), con intervalos por municipio (D-032). La lectura de cada perfil se contrasta con pruebas que podrían fallar (D-034, D-036).

**Uso propuesto:** el historial de cada sección dice **dónde** invertir; el perfil dice **a quién** hablarle y **cómo** (D-026).

**Límites:** con datos agregados no hay inferencia individual ni causal (D-010). Quien ya no vive en su sección aparece como abstencionista (D-013).

---

## Decisiones

### Datos

- **D-001 · Fórmula de participación.** SV/(SV+NV), la oficial del INE; reproduce 59.67% (2024), 51.84% (2021) y 44.06% (2009). El NS se trata con dos cotas: todo como voto y todo como abstención (resultado en D-031).
- **D-002 · Secciones sin dato.** Si en una elección SV+NV = 0, su participación queda vacía ese año (la fórmula no está definida); la sección se conserva en los demás.
- **D-003 · Ingesta.** Cada año se lee por separado y se comprueba que las filas cargadas sean las del CSV original y el SHA-256 de cada ZIP (leer todos los años juntos llegó a perder 2024 sin avisar).
- **D-004 · Edades extremas.** Se conservan en el grupo de mayor edad: son registros reales de la lista nominal y pesan 0.0002%.
- **D-005 · Privacidad.** Solo sexo hombre/mujer (el no binario son 105 registros en todo el país y se reporta solo como cifra nacional). No se publica ninguna tasa por celda; solo agregados por perfil o municipio.
- **D-015 · Fuentes externas.** Censo 2020 por sección (INEGI) con llave (estado, sección); las secciones nuevas de 2024 heredan el valor de su sección madre. CONAPO por municipio mediante el catálogo INEGI–INE. De la concurrencia solo se usa la gubernatura, la única bandera verificada. Tipo de sección: el de la CCPC.
- **D-016 · Llegada o salida de electores.** Observado entre esperado acumulado de la lista de cada cohorte en su sección, expresado como percentil dentro del estado. Se excluyen las secciones reseccionadas; no hay umbral de atípicos.
- **D-027 · Homicidios.** INEGI, defunciones por homicidio según municipio de ocurrencia, 2009–2023; tasa contraída hacia la del estado (Poisson-gamma). Se probó dentro del modelo con una regla fijada de antemano y empeoró la anticipación de 2024 (−0.005 de AUC), así que solo describe.

### Unidad, edades y contexto

- **D-006 · Unidad.** La celda sección × sexo × grupo de edad, seguida por generación en las elecciones anteriores. Dentro de una sección conviven grupos que votan muy distinto.
- **D-007 · Grupos de edad.** Se estiman donde la curva nacional de participación cambia de pendiente (regresión segmentada por sexo, centrada por elección; número de cortes por validación dejando fuera una elección). Resultado: 18–19, 20–24, 25–31, 32–46, 47–69, 70–79 y 80+.
- **D-009 · Contracción.** Las tasas de celdas pequeñas se acercan a su valor esperado en proporción a la información que les falta (beta-binomial, Bayes empírico). Evita fijar un tamaño mínimo de celda.
- **D-010 · Contexto, no personas.** Las variables del Censo describen la sección, nunca a sus habitantes ("se concentra en secciones con escolaridad X"), por la falacia ecológica.
- **D-013 · Abstención administrativa.** Quien ya no vive en su sección aparece como abstencionista (VNM 2023: el 87.9% de la LN reside en su sección). Se mide con la razón LN / población de 18+ y con D-016, y se declara como límite.

### Población objetivo

- **D-022 · Lo esperado y la brecha.** Lo esperado de una celda es la participación nacional de su misma generación y sexo en cada elección (estandarización indirecta); así el ciclo presidencial–intermedio queda descontado. La brecha se contrae (D-009) con una dispersión φ por cada uno de los 14 estratos de edad y sexo. **Población objetivo:** celdas con probabilidad mayor que 1/2 de estar por debajo de lo esperado; no hay corte de "cuánto abajo", la severidad entra como peso. Votos faltantes = esperados − contraídos, por elección.

### Perfiles

- **D-024 · Modelo.** Mezcla de clases latentes con variables mixtas sobre la población objetivo, ponderada por votos faltantes. Variables: sexo, grupo de edad, circunscripción, tipo de sección, brecha y tres componentes principales del contexto (análisis paralelo de Horn), para que un tema medido por varias columnas no pese varias veces.
- **D-017 · Reglas de ajuste.** Reinicios k-means++ hasta que el mejor óptimo se repita (máximo 10), refinados a tolerancia 1e-10. Estabilidad: bootstrap de secciones estratificado por estado, Jaccard por perfil, réplicas hasta que su error Monte Carlo sea ≤ 0.025, con cinco réplicas de control en frío; si el frío difiere del tibio más que su error, manda el frío.
- **D-011 · Lectura del Jaccard.** Escala del paquete `fpc`: ≥ 0.85 muy estable.
- **D-029 · Cinco perfiles.** BIC e ICL mejoran hasta 10, así que no eligen. K=5 es el mayor número que pasa las tres pruebas: óptimo repetido, Jaccard ≥ 0.85 en todos los perfiles (0.855–0.944) y prueba contra datos barajados (p = 0.05 con 19 permutaciones). K=6 no repite su óptimo. Costo del quinto perfil frente a cuatro: −0.010 de AUC de captura. K=4 se conserva como referencia de comparación.
- **D-026 · Lectura de variables.** `im_2020` crece cuando *baja* la marginación; `iim_dp2` crece cuando *baja* la intensidad migratoria; `pctl_mov_estado` alto = llegan más electores de los esperados. Hallazgo: para decidir *dónde* invertir, el historial de cada celda predice 2024 mejor que los perfiles; los perfiles dicen *a quién* y *cómo*.

### Validación

- **D-025 · Curva de captura.** Se ordenan las celdas con 2009–2021 y se mide qué fracción de los votos faltantes de 2024 concentra cada orden (AUC), en las celdas con historial.
- **D-032 · Intervalos por municipio.** Los intervalos remuestrean municipios (las secciones vecinas no son independientes), B = 1999. Línea base "objetivo sí/no" para medir lo que aportan los perfiles. Peso de 80+: 4.6% del déficit.
- **D-030 · Gubernatura concurrente.** Se rehízo todo con la gubernatura dentro de lo esperado: se conserva el 96% de la LN objetivo y cada perfil reaparece con 89–99% de su peso. En P2 el calendario explica 0.18 de sus 3.4 puntos de diferencia intermedia–presidencial.
- **D-031 · No especificados.** Con el NS como voto o como abstención se conserva el 91% y el 90% de la LN objetivo; P2 es el perfil más sensible.
- **D-021 · Comparación de soluciones.** Los perfiles de dos soluciones se emparejan por máximo traslape (asignación húngara), con la misma tolerancia de D-017.
- **D-034 · Lecturas de cada perfil.** Patrón (se mide), lectura (hipótesis) y pruebas (consecuencias que podrían fallar). Unidad: secciones donde el perfil es mayoritario; prueba principal: contrastes dentro de la misma sección. Una prueba se cumple si el signo es el esperado y el IC 95% (municipios) excluye el 0. Los contrastes de edad se repiten con la brecha cruda de 2024; si las dos medidas no coinciden, la prueba es no concluyente.
- **D-036 · Batería común.** Las mismas 13 pruebas se aplican a los cinco perfiles y se presentan en una sola tabla, para que la lectura de cada perfil se compare contra los demás y no parezca hecha a la medida. Cada lectura se califica solo con las pruebas que le corresponden, fijadas en D-034.

### Estrategias y documento

- **D-014 · Mensajes.** Nunca normas de baja participación ("aquí casi nadie vota"), información negativa sobre gobiernos o partidos, ni presión social con el historial individual. Los efectos de otros países se citan como referencia, no como pronóstico.
- **D-033 · Formato.** Carta, una columna, Calibri 11 (Carlito, métricamente idéntica), interlineado 1.5, máximo 12 cuartillas, como pide la convocatoria.

> Los números faltantes en la serie (D-008, D-012, D-018 a D-020, D-023, D-028, D-035) correspondían a modelos explorados que no forman parte de la entrega; se conservan los demás números para que coincidan con el código.
