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

