# Cómo se construyó ReservaIQ y por qué

## 1. Una decisión concreta del hotel

Hotel Brisa del Valle de Cali es el cliente ficticio. Su necesidad es distribuir una capacidad limitada de revisión entre reservas. La salida principal es una lista ordenada de tamaño K. La aplicación no realiza contactos, cancelaciones ni cobros. Esto mantiene el alcance demostrable y evita confundir predicción con una intervención que aún no se ha medido.

Se compararon reglas manuales, clasificación supervisada y AutoML. Se eligió clasificación con cuatro candidatos porque permite contrastar rendimiento, explicar cada etapa y controlar la cantidad de ensayos y el costo.

## 2. Datos y contrato de entrada

El archivo público de Antonio, Almeida y Nunes contiene 119.390 reservas históricas de dos hoteles de Portugal. `data/source.json` registra la fuente, licencia y SHA256; `data/hotels.csv` conserva el archivo original. No se atribuyen estos datos al cliente de Cali.

`core.py` define cuatro variables numéricas y seis categóricas. La anticipación se limita a 0–60 días y la estancia total a 1–30 noches. Este alcance permite construir ventanas temporales con desenlaces observables dentro del horizonte histórico. El mes de llegada se convierte a número.

Se excluyen estado final, fecha del estado, habitación asignada y modificaciones porque pueden revelar hechos posteriores. También se excluyen ADR y depósito por disponibilidad temporal incierta, país e identificadores de agencia o empresa. La inferencia no utiliza nombres ni datos de contacto.

## 3. Preparación y separación por tiempo

`pipeline.py prepare` aplica el alcance, elimina duplicados exactos y calcula una fecha de creación aproximada: llegada menos anticipación. Se retiran 7.603 filas repetidas de 55.053 dentro del alcance. Quedan 47.450; los filtros de período y madurez dejan 35.387 para modelado.

| Partición | Creación de reserva | Desenlace conocido antes de | Registros |
| --- | --- | --- | ---: |
| Entrenamiento | Julio 2015–junio 2016 | 1 septiembre 2016 | 21.236 |
| Validación | Septiembre–noviembre 2016 | 1 febrero 2017 | 6.161 |
| Prueba | Febrero–mayo 2017 | 1 septiembre 2017 | 7.990 |

Los intervalos reducen la posibilidad de usar desenlaces futuros en una etapa anterior. El dataset no conserva instantáneas de cada variable en el momento de reserva: la evaluación sigue siendo retrospectiva. Tampoco se puede descartar dependencia entre huéspedes recurrentes o grupos. La deduplicación puede retirar reservas legítimas indistinguibles.

## 4. Transformación y comparación de modelos

`pipeline.py train` ajusta escalado y codificación de categorías dentro de un pipeline de scikit-learn usando solo entrenamiento. Se comparan una predicción constante, regresión logística, Random Forest y Gradient Boosting con semilla 42. No se usa la prueba para elegir algoritmo ni umbral.

El criterio es mayor average precision en validación. Resume precisión y detección a distintos puntos de decisión. El umbral se elige por F1 en una cuadrícula previamente fijada de 0,05 a 0,95. La diferencia entre logística y Gradient Boosting es pequeña: el resultado no demuestra superioridad universal.

## 5. Evaluación y decisión por capacidad

`pipeline.py evaluate` abre la prueba reservada, calcula AP, ROC AUC, precisión, detección, F1, Brier y matriz de confusión. Conserva todas las predicciones en `artifacts/test_predictions.csv`. La importancia por permutación se calcula sobre una muestra fija de validación; expresa sensibilidad global, no causalidad individual.

La lista por capacidad ordena los índices y selecciona exactamente K. Es distinta de una alerta por umbral. En el experimento local, el 20 % superior reúne 705 cancelaciones en 1.598 reservas, frente a una frecuencia base de 1.831/7.990. La concentración es 1,93 veces la esperada con selección aleatoria. No se ha probado que una llamada evite una cancelación ni que el hotel recupere ingresos.

## 6. Aplicación e inferencia

`app.py` carga un artefacto confiable y expone las rutas individuales y por lote. El servidor escucha en 127.0.0.1. Rechaza peticiones de otro origen, entradas mayores de 150 KB, lotes vacíos y más de 500 filas. `core.py` aplica el mismo contrato en ambos casos.

`web/` implementa cuatro vistas: decisiones, reserva individual, evidencia y arquitectura. Los datos editados invalidan el resultado anterior. La lista completa y las predicciones se exportan en JSON; el CSV de `ejemplos-csv/` permite reproducir el lote sin preparar datos adicionales.

## 7. Pipeline en Azure ML

`azure/pipeline.yml` conecta preparación, entrenamiento y evaluación mediante componentes CLI v2. Las salidas se almacenan como artefactos del trabajo. El entrenamiento se ejecuta en CPU con máximo un nodo; el mínimo cero permite liberar cómputo al quedar inactivo. Se limita la duración de cada etapa y no se mantiene un endpoint de inferencia.

El modelo registrado se descarga para utilizarlo en la aplicación local. Su origen se documenta en `artifacts/runtime.json`: nombre del trabajo, estado, versión y SHA256. La aplicación solo confirma origen Azure cuando el estado es Completed y la huella coincide con el modelo cargado.

## 8. Verificación y versionado

Las pruebas comprueban integridad del dataset, separación temporal, madurez de etiquetas, ausencia de variables de desenlace, selección en validación, concordancia de métricas y predicciones, inferencia guardada, validación de entradas, lotes y origen de peticiones. Se incorpora una verificación automatizada en GitHub Actions. Sus resultados se consultan en la pestaña Actions; la configuración por sí sola no prueba una ejecución exitosa.

Los commits agrupan cambios reales por responsabilidad: contrato de datos; entrenamiento y evaluación; aplicación y CSV; configuración Azure; documentación y evidencias.

## Fuentes

- [Dataset original y artículo](https://doi.org/10.1016/j.dib.2018.11.126).
- [Distribución CSV y diccionario](https://github.com/rfordatascience/tidytuesday/tree/main/data/2020/2020-02-11).
- [Componentes de comandos de Azure ML](https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-component-command?view=azureml-api-2).
- [Control de costos de Azure ML](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-optimize-cost?view=azureml-api-2).
