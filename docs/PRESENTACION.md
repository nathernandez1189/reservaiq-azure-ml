# ReservaIQ · Requerimientos, diseño y demo

**Microproyecto 3 · UAO · Prof. Oscar Mondragón**

Juan Ospina Tenorio · Natalia Hernández Piedrahita · Miguel Ángel Diuza

[Ver el diseño en Canva](https://www.canva.com/d/0RDtRC3Au5C7vEJ)

Contenido actualizado el 30/09/2026 para las doce diapositivas principales y la página adicional de agradecimiento. La actualización nativa de Canva quedó guardada tras la aprobación del equipo y su contenido se verificó mediante la integración. Esta copia permite consultar el contenido sin Canva y no reproduce su maquetación.

## 1. Priorización de reservas hoteleras

ReservaIQ ayuda al equipo del hotel a priorizar revisiones. Integra un modelo entrenado en Azure ML con un calendario y una lista de reservas guardadas. El personal interpreta el resultado y decide la acción.

## 2. Requerimientos del cliente

Hotel Brisa del Valle es un cliente ficticio de Cali. Su equipo necesita decidir qué reservas revisar con el tiempo disponible y conservar el seguimiento. Tradujimos esa necesidad en funciones y condiciones comprobables.

| Función | Comportamiento esperado |
| --- | --- |
| Capturar y analizar | Fechas o CSV y un índice de cancelación |
| Guardar y recuperar | Código de reserva y persistencia local |
| Revisar y exportar | Lista de tamaño K y estados consultables |

**Aceptación:** las fechas producen entradas válidas, guardar confirma un código y conserva el registro al reiniciar. Los contadores permiten consultar pendientes, revisadas y archivadas. K representa cuántas reservas puede revisar el equipo.

**Restricciones y calidad:** diez variables, CSV de 1–500 filas, anticipación de 0–60 días y estancias de 1–30 noches. Validación en el servidor, modelo trazable y consumo acotado. La copia local no confirma una habitación.

## 3. Alternativas y elección

| Alternativa | Fortaleza | Límite |
| --- | --- | --- |
| Reglas manuales | Simples de explicar | Umbrales rígidos |
| Clasificador + lista | Prioridad medible | Exige evaluación |
| AutoML | Explora alternativas | Más ensayos y consumo variable |

Elegimos clasificación supervisada porque permite aprender de reservas históricas, comparar modelos y medir errores. La lista priorizada convierte el resultado en una decisión operativa, manteniendo control sobre los ensayos y el consumo de cómputo.

## 4. Datos y alcance

**119.390 reservas originales; 35.387 utilizadas en las tres particiones.**

Diez entradas: seis categorías del hotel y la reserva, más anticipación, mes de llegada y noches entre semana y de fin de semana. El calendario calcula estas cuatro variables a partir de creación, llegada y salida.

Alcance: anticipación de **0–60 días** y estancia de **1–30 noches**.

Datos históricos de dos hoteles de Portugal (2015–2017). Filtramos el alcance, retiramos duplicados y fijamos ventanas temporales. Las nuevas reservas quedan en SQLite y no se añaden al entrenamiento.

Fuente: Antonio, Almeida y Nunes (2019), distribución TidyTuesday, CC BY 4.0. [Artículo original](https://doi.org/10.1016/j.dib.2018.11.126).

## 5. Arquitectura de la solución

![Arquitectura: tres etapas del pipeline, registro en Azure y aplicación local](figuras/arquitectura.svg)

Azure ML coordina tres componentes CLI v2: preparación, entrenamiento y evaluación. Preparación proporciona entrenamiento y validación al entrenador, y prueba reservada al evaluador. El entrenador produce el modelo elegido; evaluación recibe ese modelo y produce métricas y predicciones.

El registro del modelo sigue perteneciendo a Azure y es un paso posterior al trabajo Completed. Descargamos el modelo y los resultados, comprobamos SHA-256 y usamos esos archivos en la aplicación local. No se mantiene un endpoint de inferencia. La lista por capacidad y los resultados apoyan la revisión humana.

El calendario y la entrada CSV pasan por validación e inferencia. SQLite conserva fechas, entradas, índice, código y estado. La aplicación permite recuperarlos y presentar la lista de revisión al personal. **Azure conserva tres etapas. Calendario y SQLite amplían la aplicación local. Guardar no reentrena el modelo.**

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

## 9. Flujo de una reserva en la demo

1. **Elegir fechas:** creación, llegada y salida en el calendario.
2. **Revisar los detalles:** seis categorías y resumen de la estancia.
3. **Analizar y guardar:** índice del modelo y confirmación con código.
4. **Consultar Mis reservas:** filtrar pendientes, revisar y volver a abrir.

El calendario se puede ocultar sin perder las fechas. La aplicación calcula anticipación, mes y reparto de noches. **Solo analizar no crea un registro.**

SQLite conserva fechas, entradas, resultado y estado en este computador. Guardar permite dar seguimiento, sin confirmar disponibilidad hotelera. Los CSV usan el mismo modelo y permiten revisar el lote antes de guardarlo.

[Flujo operativo detallado](figuras/flujo-reserva.svg) · [Guía de uso](GUIA-DE-USO.md).

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
| 56 pruebas en cada sistema | 31 de Python + 25 de JavaScript en Windows y Ubuntu. Cubren datos, API, fechas, lotes, persistencia y controles de la interfaz |
| 7.990 predicciones coincidentes | El modelo descargado reproduce los resultados guardados de las reservas de prueba |
| SHA-256 del artefacto | La huella identifica el archivo utilizado; los registros conservan el trabajo completado y el cierre de recursos |
| Validación colombiana pendiente | Antes de operar en Colombia hay que validar con datos locales y medir el efecto real de las acciones |

El guardado y el calendario cuentan con pruebas de componentes. Estas no sustituyen una revisión completa en navegador. Los datos históricos no garantizan desempeño en Colombia ni demuestran cancelaciones evitadas.

[Evidencia automática de la versión de aplicación 2b2ac95](https://github.com/nathernandez1189/reservaiq-azure-ml/actions/runs/36797755296) · [Alcance de las verificaciones](EVIDENCIAS.md).

## 12. Priorización con revisión humana

ReservaIQ integra requerimientos, un pipeline de Azure ML y una demo con fechas, guardado y seguimiento. El equipo revisa las reservas priorizadas y decide las acciones. Un uso real requiere validación local y medir el efecto de esas acciones.

En la prueba histórica, revisar el 20 % prioritario concentra **1,93 veces la frecuencia de cancelación esperada al seleccionar al azar**. Es evidencia de priorización, no de cancelaciones evitadas.

[Repositorio y evidencias](https://github.com/nathernandez1189/reservaiq-azure-ml)

---

## Página adicional de cierre

Gracias por su atención.

## Cobertura y duración objetivo

| Criterio | Diapositivas |
| --- | --- |
| Análisis de requerimientos, alternativas, datos y costos | 1–4 y 8 |
| Diseño, componentes y flujo | 5, 6 y 9 |
| Implementación y demostración | 9–11, con la aplicación abierta |
| Presentación de la solución | Recorrido completo en 15 minutos |

| Integrante | Láminas | Contenido y demo | Margen | Bloque |
| --- | --- | --- | --- | --- |
| Juan Ospina Tenorio | 1–4 | 4 min 30 s | 30 s | 0–5 min |
| Natalia Hernández Piedrahita | 5–8 | 4 min 40 s | 20 s | 5–10 min |
| Miguel Ángel Diuza | 9–12 y cierre | 4 min 50 s | 10 s | 10–15 min |

La pauta suma 14 minutos de contenido y demostración, más un minuto de margen. Es una planificación, no un ensayo medido. La demostración ocurre dentro del bloque de Miguel, no después de los 15 minutos.

Para revisar el respaldo de cada afirmación: [informe técnico](Informe-tecnico.md), [arquitectura](ARQUITECTURA.md), [modelo](MODELO.md), [costos](COSTOS.md) y [evidencias](EVIDENCIAS.md).
