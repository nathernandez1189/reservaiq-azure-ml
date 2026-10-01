# ReservaIQ · Contenido de la presentación ampliada

**Microproyecto 3 · UAO · Prof. Oscar Mondragón**

Juan Ospina Tenorio · Natalia Hernández Piedrahita · Miguel Ángel Diuza

[Ver el diseño en Canva](https://www.canva.com/d/20i32hmvo0gpTiA)

Copia consultable del contenido de las 12 diapositivas guardadas el 29/09/2026. La información y las cifras corresponden a la versión ampliada; las tablas y el diagrama se representan en Markdown para permitir su lectura sin Canva. Esta copia no conserva la maquetación visual del diseño.

## 1. Priorización de reservas hoteleras

ReservaIQ ayuda a decidir qué reservas revisar primero cuando el equipo del hotel tiene tiempo limitado. Utilizamos aprendizaje automático en Azure para ordenar la atención; la decisión final permanece en manos del personal.

## 2. La decisión del hotel

Hotel Brisa del Valle es un cliente ficticio de Cali. Su equipo necesita priorizar confirmaciones porque no puede revisar todas las reservas con la misma intensidad. El objetivo es ordenar la atención según la capacidad disponible.

**Necesidad: qué revisar primero → lista priorizada: seleccionar K → revisión humana: decisión final.**

La solución debe analizar una reserva, ordenar una lista de tamaño K, procesar lotes y exportar resultados. K representa cuántas reservas puede revisar el equipo; no es una cantidad fija ni una orden de contactar a todos los registros con alerta.

Restricciones: diez variables, CSV de 1–500 filas, anticipación de 0–60 días y estancias de 1–30 noches. Sin contactos, cancelaciones ni cobros automáticos.

## 3. Alternativas y elección

| Alternativa | Fortaleza | Límite |
| --- | --- | --- |
| Reglas manuales | Simples de explicar | Umbrales rígidos |
| Clasificador + lista | Prioridad medible | Exige evaluación |
| AutoML | Explora alternativas | Más ensayos y consumo variable |

Elegimos clasificación supervisada porque permite aprender de reservas históricas, comparar modelos y medir errores. La lista priorizada convierte el resultado en una decisión operativa, manteniendo control sobre los ensayos y el consumo de cómputo.

## 4. Datos y alcance

**119.390 reservas originales; 35.387 utilizadas en las tres particiones.**

Diez variables: hotel, alimentación, segmento, canal, habitación reservada, tipo de cliente, anticipación, mes de llegada y noches entre semana y de fin de semana.

Alcance: anticipación de **0–60 días** y estancia de **1–30 noches**.

Los datos son de dos hoteles de Portugal, con llegadas en 2015–2017. Aplicamos alcance, deduplicación y ventanas temporales. No pertenecen al cliente ficticio y no incluyen nombres ni contactos como predictores.

Fuente: Antonio, Almeida y Nunes (2019), distribución TidyTuesday, CC BY 4.0. [Artículo original](https://doi.org/10.1016/j.dib.2018.11.126).

## 5. Arquitectura de la solución

![Arquitectura: tres etapas del pipeline, registro en Azure y aplicación local](figuras/arquitectura.svg)

Azure ML coordina tres componentes CLI v2: preparación, entrenamiento y evaluación. Preparación proporciona entrenamiento y validación al entrenador, y prueba reservada al evaluador. El entrenador produce el modelo elegido; evaluación recibe ese modelo y produce métricas y predicciones.

El registro del modelo sigue perteneciendo a Azure y es un paso posterior al trabajo Completed. Descargamos el modelo y los resultados, comprobamos SHA-256 y usamos esos archivos en la aplicación local. No se mantiene un endpoint de inferencia. La lista por capacidad y los resultados apoyan la revisión humana.

Las flechas describen datos y artefactos; el registro y la descarga no son componentes adicionales del pipeline. La carpeta de particiones incluye también validación para calcular importancia de variables durante la evaluación, sin volver a ajustar el modelo.

## 6. Evaluación por tiempo

| Partición | Reservas | Período por fecha derivada de creación |
| --- | ---: | --- |
| Entrenamiento | 21.236 | Julio de 2015 a junio de 2016 |
| Validación | 6.161 | Septiembre a noviembre de 2016 |
| Prueba | 7.990 | Febrero a mayo de 2017 |

Entrenamiento: ajustamos el escalado, la codificación de categorías y los modelos usando únicamente los datos de este período.

Validación: comparamos los candidatos y fijamos el umbral. Dejamos separación temporal para conocer los desenlaces anteriores.

Prueba: medimos el desempeño final sin cambiar el modelo. Excluimos estado final y otros campos que pueden revelar el futuro.

## 7. Comparación de modelos

| Candidato | Average precision en validación |
| --- | ---: |
| Base constante | 0,2185 |
| Regresión logística | 0,4028 |
| Random Forest | 0,3677 |
| Gradient Boosting | 0,4103 |

Elegimos Gradient Boosting por su mayor average precision en validación. La ventaja frente a logística es pequeña; no demuestra superioridad universal.

**Prueba final: AP 0,4134; ROC AUC 0,7307.** Estas métricas corresponden a las 7.990 reservas que no se usaron para seleccionar el modelo.

**Umbral: 0,17.** Se eligió por F1 en validación. El índice no es una probabilidad calibrada.

## 8. Azure ejecutado y costo acotado

**Preparación: Completed · Entrenamiento: Completed · Evaluación: Completed.**

El pipeline completó preparación, entrenamiento y evaluación en North Central US. Registramos y descargamos `reservaiq:1`. Las 7.990 predicciones coinciden con la ejecución local. Se utilizó un clúster de 0–1 nodos y se eliminaron los recursos temporales después de conservar las salidas.

| Concepto | USD |
| --- | ---: |
| CPU: 1 hora × US$0,146 | 0,146 |
| Auxiliares supuestos | 0,500 |
| Margen | 0,354 |
| **Total estimado** | **1,000** |

Es un escenario aproximado, no la factura final. La consulta de costos del 25/09/2026 aún no mostraba cargos consolidados.

## 9. Demo: priorizar y analizar

1. Ajustar capacidad: elegir 30 de 150 reservas ilustrativas.
2. Explorar una reserva: editar sus datos y consultar el índice del modelo.
3. Mostrar un error: consultar una falsa alerta y una omisión.
4. Cargar el CSV: analizar ocho reservas y abrir el resultado JSON.

En toda la prueba, seleccionar el 20 % reúne **705 cancelaciones entre 1.598 reservas**: concentración **1,93×**, precisión **44,1 %** y cancelaciones capturadas **38,5 %**.

Estas cifras describen el resultado retrospectivo de las 7.990 reservas de prueba; no significan cancelaciones evitadas ni ingresos recuperados.

## 10. Errores que debemos reconocer

| Resultado histórico | Con alerta | Sin alerta |
| --- | ---: | ---: |
| Canceló | 1.467 | 364 |
| No canceló | 2.715 | 3.444 |

Al umbral **0,17**: detección **80,1 %** y precisión **35,1 %**.

El modelo detecta 1.467 de las 1.831 cancelaciones y omite 364. También genera 2.715 falsas alertas. Por eso el índice orienta una revisión humana: una alerta no demuestra que la reserva se cancelará. La lista de tamaño K responde a la capacidad del hotel.

## 11. Evidencia y límites

| Evidencia | Qué comprueba |
| --- | --- |
| 14 pruebas automáticas aprobadas | Datos, separación temporal, métricas, inferencia individual, lotes y rechazo de entradas inválidas |
| 7.990 predicciones coincidentes | El modelo descargado reproduce los resultados guardados de las reservas de prueba |
| SHA-256 del artefacto | La huella identifica el archivo utilizado; los registros conservan el trabajo completado y el cierre de recursos |
| Validación colombiana pendiente | Antes de operar en Colombia hay que validar con datos locales y medir el efecto real de las acciones |

Los datos son históricos y no contienen versiones de cada campo al reservar. Las capturas de sesión local se distinguen de los registros de Azure. La importancia de variables describe asociaciones globales, no causas individuales.

## 12. Priorización con revisión humana

ReservaIQ integra el análisis del problema, un diseño en Azure ML y una demo reproducible. El modelo ayuda a distribuir la revisión; el personal decide las acciones. Antes de un uso real se necesitan datos locales y una evaluación del efecto de esas acciones.

En la prueba histórica, revisar el 20 % prioritario concentra **1,93 veces la frecuencia de cancelación esperada al seleccionar al azar**. Es evidencia de priorización, no de cancelaciones evitadas.

[Repositorio y evidencias](https://github.com/nathernandez1189/reservaiq-azure-ml)

---

Distribución objetivo: Juan, diapositivas 1–4, cinco minutos; Natalia, 5–8, cinco minutos; Miguel Ángel, 9–12, cinco minutos incluida la demostración. El tiempo final debe comprobarse con un ensayo.

Para revisar el respaldo de cada afirmación: [informe técnico](Informe-tecnico.md), [arquitectura](ARQUITECTURA.md), [modelo](MODELO.md), [costos](COSTOS.md) y [evidencias](EVIDENCIAS.md).

## Actualización de la aplicación: guardado local

La demo se amplió después de preparar estas doce diapositivas. En la aplicación actual, Centro de decisiones se llama Inicio y Explorar una reserva se llama Nueva reserva. Se añadieron Mis reservas y Cómo probarlo. Analizar y guardar conserva una copia local; Solo analizar no la guarda. La importación CSV ahora muestra una vista previa antes de guardar o descargar.

El diagrama del repositorio y el informe incluyen SQLite local. Esta actualización del código no edita automáticamente el diseño alojado en Canva. El método de modelado, los resultados y la evidencia histórica de Azure conservan sus valores. La [guía de uso actual](GUIA-DE-USO.md) y las [pruebas guiadas](PRUEBAS-GUIADAS.md) describen las nuevas acciones.


La versión actual también incorpora un calendario y tres pasos: **Fechas → Detalles → Revisar y guardar**. Calcula automáticamente las cuatro variables temporales y conserva las fechas al guardar. Los ejemplos históricos siguen disponibles con sus variables originales. Este cambio está en la aplicación y en el informe del repositorio; no implica una modificación automática de las diapositivas nativas de Canva.
