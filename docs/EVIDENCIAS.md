# Evidencias del microproyecto

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

Las pruebas comprueban catorce aspectos del modelo, datos y API. Incluyen el CSV entregado y la concordancia entre resultados individuales y por lote. La prueba de procedencia exige trabajo Completed y SHA256 coincidente antes de afirmar un modelo de Azure.

## Revisión de interfaz y capturas

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
