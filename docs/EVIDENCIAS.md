# Evidencias del microproyecto

## Versión publicada en MICROPROYECTO3

Corte: 1 de octubre de 2026 UTC. Nueva ejecución `microproyecto3-reejecucion-20261001`, tres etapas Completed, modelo `reservaiq:1` y demo web en App Service F1. Es una nueva ejecución del mismo proyecto, separada del trabajo original `mango_wire_5f09pdg4m3`.

- [Estados y activos Azure](../azure/evidence/microproyecto3/execution.json), [procedencia del modelo](../azure/evidence/microproyecto3/runtime.json) y [pipeline ejecutado](../azure/evidence/microproyecto3/pipeline.yml).
- **67 pruebas**: 41 Python y 26 JavaScript en cada sistema de CI, Windows y Ubuntu. [Ejecución verificada](https://github.com/nathernandez1189/reservaiq-azure-ml/actions/runs/36809150020).
- **31 comprobaciones HTTPS**, incluyendo predicción, guardado, lote CSV, validación y conflictos. Nueve reservas ficticias conservaron sus datos después de reiniciar App Service. [Resultados](../azure/evidence/microproyecto3/web-verification.json).
- Misma huella SHA-256 del modelo y 7.990 predicciones coincidentes con los artefactos originales conservados. Esta equivalencia no transforma las dos ejecuciones en un mismo trabajo.
- [Costos fechados](COSTOS.md): original US$0,0620879781 antes de impuestos; MICROPROYECTO3 todavía sin filas de costo. Estimación de conservación US$2 y límite US$3.

Las comprobaciones de API y componentes no equivalen a un recorrido visual completo del sitio alojado. La revisión visual automatizada del navegador quedó bloqueada por la política de acceso. Tampoco se ha medido el ensayo de 15 minutos.

## Revisión actual de la demo web

Se revisaron las 15 imágenes aportadas por el equipo de la interfaz de seis vistas. [Inventario y explicación de cada pantalla](EVIDENCIA-WEB-ACTUAL.md). Se distinguen las instrucciones visibles de las pruebas ejecutadas y la estimación de US$2 del costo facturado. Los PNG originales todavía no están incorporados; la revisión visual se basa en los adjuntos de la conversación.

La [consulta HTTPS actual de solo lectura](../azure/evidence/microproyecto3/web-current-check.json) comprueba disponibilidad, estado del modelo y lectura de reservas. No guarda registros ni reinicia recursos.

## Registro histórico de comprobaciones anteriores

Los conteos y estados siguientes corresponden a las versiones y fechas indicadas. Se conservan como antecedentes y no sustituyen el corte actual.

Las métricas y el modelo entregados corresponden al pipeline de Azure ML `mango_wire_5f09pdg4m3`, con sus tres etapas en estado Completed. La aplicación utiliza la copia descargada del modelo registrado `reservaiq:1`. La verificación local posterior comprueba las 7.990 predicciones guardadas y la identidad del archivo.

| Evidencia | Archivo | Qué demuestra |
| --- | --- | --- |
| Fuente y huella | `data/source.json` | Procedencia del CSV y comprobación de integridad |
| Manifiesto | `artifacts/splits/data_manifest.json` | Alcance, exclusiones, fechas y tamaños |
| Comparación | `artifacts/trained/selection.json` | Selección de modelo y umbral en validación |
| Modelo serializado | `artifacts/trained/model.joblib` | Artefacto utilizado para inferencia |
| Prueba reservada | `artifacts/test_predictions.csv` | Cada predicción y desenlace usados en métricas |
| Resultados | `artifacts/summary.json` | Métricas, casos, matriz e importancia |
| Comprobación local | `docs/verificacion.json` | Resultado y alcance de las pruebas |
| Ejecución automática | GitHub Actions | Resultado de la ejecución correspondiente al commit |
| CSV de carga | `ejemplos-csv/reservas-listas.csv` | Ocho registros con el contrato exacto |

## Reproducir las comprobaciones

```bash
python -m unittest discover -s tests -v
```

Las pruebas comprueban quince aspectos del modelo, datos y API. Incluyen el CSV entregado, la concordancia entre resultados individuales y por lote y la lectura de resultados con una configuración regional de Windows. La prueba de procedencia exige trabajo Completed y SHA256 coincidente antes de afirmar un modelo de Azure.

## Revisión histórica de interfaz y capturas del 24 de septiembre

Se revisaron las cuatro capturas aportadas por el equipo: [galería comentada](CAPTURAS.md). Los originales y sus huellas se conservan en `docs/capturas/`. El anexo del informe reproduce cada imagen y explica la decisión, los resultados visibles y los límites de la evidencia.

Todas muestran una etiqueta de modelo local. La vista de Azure muestra “Sin ejecución”, “No creado” y “Por verificar”; esos rótulos describen la sesión capturada, no el estado acreditado por los registros de Azure incluidos abajo. No se ha determinado la causa de esa diferencia. Las imágenes no se retocan para cambiar estados.

La captura de lotes muestra el mensaje de ocho reservas procesadas y resultado descargado. No se verificó el contenido de esa descarga a partir de la imagen. Las pruebas del servidor comprueban el contrato y la inferencia; no certifican la navegación del cliente de extremo a extremo. La revisión de imágenes aportadas y la comprobación automática tienen alcances distintos.

## Evidencia de Azure

| Registro | Alcance |
| --- | --- |
| `azure/evidence/run.json` | Pipeline, tres etapas Completed, modelo registrado y huellas de las diez salidas |
| `azure/evidence/comparison.json` | Las 7.990 predicciones coinciden entre local y Azure; diferencia máxima 0,0 |
| `azure/evidence/console.txt` | Extractos literales de preparación, comparación y evaluación |
| `azure/environment-lock.json` | Imagen base y final por digest, Python 3.12.14 y paquetes observados |
| `azure/evidence/billing.json` | Consulta de costos sin cargos consolidados al momento de revisión |
| `azure/evidence/closure.json` | Cierre del grupo temporal después de descargar y verificar las salidas |
| `artifacts/runtime.json` | Procedencia del modelo cargado por la aplicación |

La versión registrada y el archivo del entrenamiento tienen SHA256 `d1a01086d1fa360d52dd21888a505ad8197b6b18d67784b81bfe0ac304d859dd`. Los CSV de las tres particiones y su manifiesto coinciden byte por byte con los locales. La serialización del modelo es distinta entre entornos, pero las predicciones del modelo elegido son idénticas. La comparación de candidatos es la producida en Azure; la regresión logística presenta una diferencia pequeña respecto de la ejecución local.

Los registros públicos se extraen de respuestas de Azure CLI y de archivos descargados de Blob Storage. Se omiten suscripción, tenant, identidades y URLs privadas. `summary.json` añade la confirmación de procedencia después de la verificación; `run.json` distingue su huella publicada de la huella de la salida original. Los estados Completed son evidencia histórica de la ejecución, incluso después del cierre de infraestructura.


## Revisión de arquitectura del 29/09/2026

Se contrastó el diagrama con las dependencias de `azure/pipeline.yml` y con las lecturas y salidas de `pipeline.py`. La figura muestra prueba y modelo como entradas separadas de evaluación; métricas y predicciones como sus salidas; registro dentro de Azure; y descarga a la aplicación local. Registro y descarga se distinguen de los tres componentes del pipeline.

La figura del informe, las variantes SVG del repositorio y el diagrama de Canva proceden de una misma definición. Se revisaron las doce páginas del PDF y el encuadre de la diapositiva 5. Las catorce pruebas del proyecto pasaron; también se verificó que `/arquitectura.svg` responde HTTP 200 con el tipo SVG y el contenido esperado. Esta comprobación del servidor no equivale a una prueba completa de navegación en el navegador.

Las capturas históricas del anexo se conservan sin modificaciones. El modelo, las particiones y las métricas del experimento no cambiaron en esta revisión.

## Comprobación de navegación del 29/09/2026

La apertura de la aplicación en el navegador detectó que la edición del diagrama había retirado el inicio de la sección `project` y su elemento `architecture-status`. La inicialización se detenía al intentar actualizar ese elemento. Se restauraron la sección de Diseño y Azure y los controles de evaluación, manteniendo el SVG en su vista correspondiente.

Se reforzó la prueba existente de procedencia para exigir las cuatro vistas independientes y los elementos de estado de Azure dentro de `project`. Las 14 pruebas volvieron a pasar. También se comprobaron en el navegador las cuatro vistas, el caso 12301 (índice 39,8), su edición a siete días de anticipación (13,6), los casos de falsa alerta y omisión, y el lote entregado de ocho filas (cero por encima del umbral). Con K igual a 30, la cohorte ilustrativa muestra 12 cancelaciones históricas.

El navegador mostró el mensaje de descarga del lote; esta revisión no compara los bytes de esa descarga del navegador. Las pruebas de API verifican el contenido de las respuestas. El alcance de la revisión manual son estos recorridos observados, no todos los dispositivos o condiciones de red. No se cambiaron los datos, el modelo ni las métricas.

## Compatibilidad con Windows del 30/09/2026

La apertura en Windows mostró `Failed to fetch` mientras el servidor registraba `UnicodeDecodeError: 'charmap'`. La lectura de `summary.json` dependía de la configuración regional. Al interpretar como CP1252 los bytes UTF-8 de la palabra «Índice», la petición a `/api/summary` terminaba sin respuesta.

Se añadió una prueba que reproduce ese fallo en el controlador GET con CP1252 como codificación predeterminada. Falló antes de la corrección y pasó después de fijar UTF-8 en las lecturas de resultados y procedencia. Las otras lecturas de texto del pipeline, las pruebas y los generadores también usan UTF-8 explícito. El conjunto local terminó con 15 pruebas correctas. Los datos, el modelo y las métricas permanecen iguales.

Git conserva los CSV sin conversión de finales de línea para mantener sus huellas al clonar en Windows. GitHub Actions ejecuta las comprobaciones en Ubuntu y Windows con el modo UTF-8 implícito desactivado; el estado de cada ejecución se consulta en la acción del commit correspondiente. La comprobación automática no sustituye la confirmación de apertura en el computador del compañero.

Si aparece `ModuleNotFoundError: No module named 'joblib'`, deben instalarse todas las dependencias de `requirements.txt` con el mismo intérprete que inicia la aplicación. El README utiliza directamente el Python de `.venv` en PowerShell para evitar mezclarlo con otra instalación. El modo `-X utf8` es una alternativa temporal documentada por [Python para Windows](https://docs.python.org/3.12/using/windows.html#utf-8-mode).

## Guardado local y recorrido guiado — 30/09/2026

Se añadieron persistencia SQLite y las vistas Mis reservas y Cómo probarlo. Las diez variables, el modelo, los datos históricos y sus métricas permanecen sin cambios.

- **24 pruebas Python aprobadas:** modelo, contrato, API HTTP real y guardado, incluido un lote de 500 reservas. Se verificó recuperar el mismo registro después de reiniciar el servidor; reintentos concurrentes sin duplicados; edición por revisión; archivo y restauración; reversión completa de lotes inválidos. Las huellas de los artefactos históricos se comparan antes y después de las operaciones de persistencia.
- **14 pruebas JavaScript aprobadas:** siete del lector CSV y siete de componentes de interfaz con una API simulada en jsdom. Comprueban la separación entre analizar y guardar, edición, representación segura de referencias, filtros y restauración, vista previa del lote y errores de conexión. No representan una sesión en un navegador real.
- Comandos: `python -X utf8=0 -m unittest discover -s tests -v` y `npm test`. GitHub Actions ejecuta ambas suites en Windows y Ubuntu; los resultados remotos se consultan en [Actions](https://github.com/nathernandez1189/reservaiq-azure-ml/actions/workflows/verificacion.yml).
- Informe PDF de **13 páginas** renderizado y revisado. El diagrama incorpora la base local; las capturas originales se conservan identificadas como correspondientes a la interfaz anterior.

**Límite de esta revisión:** el navegador rechazó el acceso porque no pudo verificar su política administrativa. No se eludió ese control. Por ello la nueva navegación, la apariencia responsive y las descargas en un navegador real quedan pendientes de comprobación visual. Las pruebas del servidor y los componentes sí se ejecutaron. La [prueba guiada](PRUEBAS-GUIADAS.md) permite realizar el recorrido al abrir la aplicación.

No se inició cómputo ni se crearon recursos en Azure. Las bases locales y datos de prueba no forman parte del repositorio ni del ZIP de entrega.


## Calendario, pasos y tarjetas de estado — 30/09/2026 (hora Colombia)

Se añadió el calendario de llegada/salida, la derivación de variables temporales, la revisión en tres pasos y las tarjetas pulsables de Guardadas, Pendientes, Revisadas y Archivadas. No se modificaron el modelo, el dataset ni sus métricas.

- **31 pruebas Python aprobadas:** las anteriores más aritmética de fechas, límites, años bisiestos, cambio de año, migración de SQLite sin alterar campos previos, rechazo de una versión futura, consistencia de fechas/variables en la API y recuperación de fechas tras reiniciar el servidor.
- **22 pruebas JavaScript aprobadas:** CSV, aritmética independiente de zona horaria, calendario y teclado, recorrido completo hasta guardar/editar, fechas inválidas sin interrupción, conservación del modo histórico y filtros pulsables con búsqueda y paginación. Los componentes usan jsdom y una API simulada.
- Total local: **53 pruebas** con `python -X utf8=0 -m unittest discover -s tests -v` y `npm test`. La verificación remota de cada revisión se consulta en Actions; no se confunde con la ejecución local.
- Informe de **13 páginas** regenerado y revisado visualmente; guía y protocolo actualizados para el calendario y los contadores.

El acceso a la aplicación en el navegador volvió a ser rechazado por una comprobación de seguridad administrativa indisponible. No se eludió ese control. La apariencia en tamaños de pantalla, la navegación en navegador real y la usabilidad con personas no están certificadas por estas pruebas; quedan descritas en [Experiencia de usuario](EXPERIENCIA-DE-USUARIO.md) y [Pruebas guiadas](PRUEBAS-GUIADAS.md). No se publicaron capturas que aparenten demostrar esa nueva revisión visual. Las capturas anteriores mantienen sus fechas y alcance.

Las pruebas se ejecutaron con bases aisladas. No se iniciaron máquinas ni recursos de Azure, y no se publicaron reservas personales.


### Ajuste final: ocultar calendario y revisar la rúbrica

La última ampliación pasó **24 pruebas JavaScript** (55 en total al sumar las 31 Python). Se comprueba ocultar/mostrar sin cambiar fechas o resultado; cierre al elegir salida; recuperación de una reserva con el calendario recogido; y navegación desde los cuatro criterios del proyecto a sus pruebas y resultados.

La primera ejecución remota detectó dos fallos de limpieza de los archivos temporales de las pruebas de migración en Windows. Se corrigió el cierre explícito de sus conexiones SQLite; la aplicación ya cerraba sus conexiones. El resultado de la nueva ejecución remota se consulta en Actions para la revisión final.

Se revisó el recorte de calendario aportado en la conversación, con hora 19:30:08 del 30/09/2026 en el nombre. Muestra llegada 02/10/2026 y salida 10/10/2026; precede al control de ocultar y no acredita guardado ni navegación completa. El archivo temporal no pudo leerse por restricciones del sistema y no se publicó una copia ni una huella inventada.


La fecha de creación quedó visible junto a llegada y salida y puede elegirse en el mismo calendario. La selección activa indica qué campo se modifica. El recorrido de creación, cambio de anticipación, guardado, edición y rechazo de una creación posterior a la llegada está cubierto por una prueba adicional: **25 pruebas JavaScript y 31 Python; 56 en total**.
