# Código fuente: paquete `ine_perfiles`

Aquí está la lógica reutilizable del proyecto. Los scripts de [`scripts/`](../scripts/) la llaman en el orden del [`Makefile`](../Makefile), y las pruebas de [`tests/`](../tests/) la verifican. Cada función cita la decisión que implementa (`D-xxx`, ver [`docs/METODOLOGIA.md`](../docs/METODOLOGIA.md)).

Se instala en modo editable con `make instalar`; después se importa como `from ine_perfiles import config`.

| Módulo | Contenido |
|---|---|
| `config.py` | Rutas, elecciones, parámetros del método (cada uno con su `# D-xxx`) y cifras de control |
| `ingesta.py`, `limpieza.py`, `territorio.py`, `externos.py`, `violencia.py` | Lectura y limpieza de la CCPC y de las fuentes externas |
| `edades.py` | Regresión segmentada para los grupos de edad |
| `cohortes.py` | Construcción del panel de cohortes |
| `descriptores.py` | Contexto de sección, movilidad y cuantiles ponderados |
| `brecha.py` | Lo esperado, la contracción beta-binomial y la población objetivo |
| `mezcla_mixta.py` | Mezcla de clases latentes con variables mixtas (EM, reinicios, criterios, PCA ponderado, Horn) |
| `seleccion.py` | Datos de la mezcla, ajuste, bootstrap, prueba contra el azar y descripción de perfiles; lo comparten los scripts de perfiles |
| `estabilidad.py` | Bootstrap de secciones estratificado por estado y Jaccard por perfil |
| `evaluacion.py` | ARI ponderado, reetiquetado, curva de captura, ΔAUC con bootstrap pareado y regla de perfiles claros |
| `sensibilidad.py` | Escenarios de concurrencia y NS |
| `lecturas.py` | Contrastes y asociaciones de las pruebas de las lecturas |

## Qué script usa cada módulo

| Etapa | Scripts | Módulos |
|---|---|---|
| Datos | `scripts/datos/` | `ingesta`, `limpieza`, `territorio`, `externos`, `violencia` |
| Preparación | `scripts/preparacion/` | `edades`, `cohortes`, `descriptores`, `brecha` |
| Perfiles | `scripts/perfiles/` | `mezcla_mixta`, `seleccion`, `estabilidad`, `evaluacion` |
| Validación | `scripts/validacion/` | `evaluacion`, `sensibilidad`, `lecturas` |
| Figuras | `scripts/figuras/` | `brecha`, `descriptores`, `evaluacion` |
