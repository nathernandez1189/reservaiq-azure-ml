# Arquitectura y flujo de ReservaIQ

![Flujo de datos y artefactos: pipeline, registro en Azure y aplicación local](figuras/arquitectura.svg)

El diagrama representa **transferencias de datos y artefactos**. Las flechas no indican que todo se ejecute automáticamente ni constituyen un orden cronológico completo. El pipeline contiene exactamente tres componentes: preparación, entrenamiento y evaluación. El registro y la descarga se realizaron después de comprobar el trabajo terminado.

## Entrenamiento y evaluación en Azure

| Origen → destino | Qué se transfiere | Relación con la implementación |
| --- | --- | --- |
| CSV / Blob → preparación | Archivo original `hotels.csv` | Entrada `raw` de `azure/pipeline.yml` |
| Preparación → entrenamiento | Entrenamiento y validación | El componente recibe la carpeta `splits`; `train()` lee `train.csv` y `validation.csv` |
| Preparación → evaluación | Prueba reservada | El componente recibe `splits`; `evaluate()` lee `test.csv` para las métricas finales |
| Entrenamiento → evaluación | Modelo y selección fijada | Entrada `trained`: `model.joblib` y `selection.json` |
| Entrenamiento → registro | Artefacto `model.joblib` | Se registra como `reservaiq:1` desde la salida `trained` del trabajo completado |
| Evaluación → aplicación local | Métricas, ejemplos y predicciones descargadas | Salida `report`; `summary.json` alimenta las vistas de evidencia y la cohorte ilustrativa |
| Registro → aplicación local | Copia verificada del modelo | Descarga, SHA-256 y `artifacts/runtime.json` vinculan el modelo con su procedencia |
| Aplicación → personal del hotel | Índice, lista de tamaño K y exportaciones | La decisión sobre cualquier intervención sigue siendo humana |

El diagrama destaca el uso de la prueba en evaluación. La carpeta `splits` también contiene validación y el manifiesto: evaluación lee validación para la importancia por permutación, sin reajustar el modelo ni el umbral. Las salidas se conservan en Blob; las flechas entre etapas resumen esos archivos almacenados y no son conexiones de red directas entre servicios.

## Componentes y responsabilidades

| Componente | Responsabilidad | Por qué se utiliza |
| --- | --- | --- |
| Workspace Azure ML | Organizar trabajos, entornos y versiones registradas del modelo | Trazabilidad |
| Blob Storage asociado | Conservar las entradas y salidas de las etapas | Separar archivos del cómputo |
| Clúster CPU, 0–1 nodos | Ejecutar los tres componentes | Limitar capacidad ociosa y concurrencia |
| Preparación | Contrato de datos, deduplicación, fechas y particiones | Reducir contaminación temporal |
| Entrenamiento | Ajustar transformaciones, comparar candidatos y fijar el umbral con validación | Selección controlada, sin utilizar la prueba |
| Evaluación | Aplicar el modelo fijo a la prueba y producir métricas y predicciones | Medir generalización retrospectiva |
| Registro en Azure ML | Identificar el modelo como `reservaiq:1` | Conservar la procedencia y la versión |
| Descarga y verificación local | Comprobar archivo, huella y resultados | Vincular la demo con la ejecución documentada |
| Servidor e interfaz local | Validar entradas, inferir, analizar lotes, mostrar prioridad y exportar | Demostrar el uso sin endpoint permanente |
| Personal del hotel | Interpretar resultados y decidir las acciones | Mantener supervisión humana |

## Secuencia de ejecución y operación

1. Subir la entrada y ejecutar el pipeline definido en [`azure/pipeline.yml`](../azure/pipeline.yml).
2. Esperar las tres etapas completadas y revisar las salidas. **Evaluación no crea ni reentrena el modelo.**
3. Registrar el archivo de la salida de entrenamiento; descargar modelo y resultados. Estos pasos están documentados por separado en [`azure/README.md`](../azure/README.md).
4. Verificar SHA-256, procedencia y coincidencia de las 7.990 predicciones antes de utilizar el modelo en la aplicación.
5. Iniciar la aplicación local: una reserva o CSV pasa por validación de entradas y por el modelo para obtener índices. La lista por K de la demo utiliza una cohorte histórica ilustrativa de 150 reservas ya puntuadas; no es un sistema de reservas en producción.
6. Conservar las evidencias y cerrar los recursos temporales de Azure después de verificar las descargas. La demo continúa con sus archivos locales.

La ejecución y el registro en Azure son históricos: el grupo temporal fue eliminado tras conservar los resultados. No se necesita recrearlo para evaluar la demo. La aplicación no está publicada como servicio de producción.

## Fuente y reproducción del diagrama

El informe y las figuras del repositorio utilizan la misma definición vectorial en `scripts/diagrama_arquitectura.py`. La variante oscura mantiene la misma topología para su uso en Canva. Para regenerar las figuras y el informe:

```bash
python -m pip install -r requirements-docs.txt
python scripts/diagrama_arquitectura.py
python scripts/generar_informe.py
```

El diagrama muestra los componentes pertinentes a los criterios del microproyecto; los recursos auxiliares y supuestos de consumo están descritos en [Costos](COSTOS.md). La imagen de ejecución, las dependencias, los datos y los artefactos se identifican en las [evidencias](EVIDENCIAS.md).
