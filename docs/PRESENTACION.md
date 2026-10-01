# ReservaIQ · Requerimientos, diseño y demo

**Microproyecto 3 · UAO · Prof. Oscar Mondragón**

Juan Ospina Tenorio · Natalia Hernández Piedrahita · Miguel Ángel Diuza

[Ver el diseño en Canva](https://www.canva.com/d/0RDtRC3Au5C7vEJ)

Contenido documental actualizado el 1 de octubre de 2026 UTC. La actualización correspondiente de Canva está preparada y pendiente de aprobación para guardar. Esta copia permite consultar el contenido sin Canva y no reproduce su maquetación. Las notas internas antiguas de Canva no se actualizan mediante esta integración.

## 1. Priorización de reservas hoteleras

ReservaIQ ayuda al equipo del hotel a priorizar revisiones. Integra un modelo entrenado en Azure ML con un calendario y una lista de reservas guardadas. El personal interpreta el resultado y decide la acción.

## 2. Requerimientos del cliente

Hotel Brisa del Valle es un cliente ficticio de Cali. Su equipo necesita decidir qué reservas revisar con el tiempo disponible y conservar el seguimiento. Tradujimos esa necesidad en funciones y condiciones comprobables.

| Función | Comportamiento esperado |
| --- | --- |
| Capturar y analizar | Fechas o CSV y un índice de cancelación |
| Guardar y recuperar | Código de reserva y persistencia compartida en la web |
| Revisar y exportar | Lista de tamaño K y estados consultables |

**Aceptación:** las fechas producen entradas válidas, guardar confirma un código y conserva el registro al reiniciar. Los contadores permiten consultar pendientes, revisadas y archivadas. K representa cuántas reservas puede revisar el equipo.

**Restricciones y calidad:** diez variables, CSV de 1–500 filas, anticipación de 0–60 días y estancias de 1–30 noches. Validación en el servidor, modelo trazable y consumo acotado. La demo pública admite solo datos ficticios y no confirma una habitación.

## 3. Alternativas y elección

| Alternativa | Fortaleza | Límite |
| --- | --- | --- |
| Reglas manuales | Simples de explicar | Umbrales rígidos |
| Clasificador + lista | Prioridad medible | Exige evaluación |
| AutoML | Explora alternativas | Más ensayos y consumo variable |

Reglas y AutoML se compararon como alternativas de diseño; no se ejecutaron. Elegimos clasificación supervisada para controlar el costo y medir la prioridad. Entrenamos regresión logística, Random Forest y Gradient Boosting frente a una base constante; seleccionamos por average precision en validación.

## 4. Datos y alcance

**119.390 reservas originales; 35.387 utilizadas en las tres particiones.**

Diez entradas: seis categorías del hotel y la reserva, más anticipación, mes de llegada y noches entre semana y de fin de semana. El calendario calcula estas cuatro variables a partir de creación, llegada y salida.

Alcance: anticipación de **0–60 días** y estancia de **1–30 noches**.

Datos históricos de dos hoteles de Portugal (2015–2017). Filtramos el alcance, retiramos duplicados y fijamos ventanas temporales. Las nuevas reservas quedan en SQLite y no se añaden al entrenamiento.

Fuente: Antonio, Almeida y Nunes (2019), distribución TidyTuesday, CC BY 4.0. [Artículo original](https://doi.org/10.1016/j.dib.2018.11.126).

## 5. Arquitectura de la solución

![Arquitectura de MICROPROYECTO3](figuras/arquitectura-azure-web.svg)

Azure ML prepara los datos, compara modelos y evalúa la prueba reservada. Después del trabajo Completed se registra el modelo seleccionado y se verifica su copia. Evaluación usa también validación para importancia de variables, sin reentrenar.

App Service F1 publica interfaz y API, y carga el modelo descargado. Calendario o CSV pasan por validación e inferencia. Un contenedor Blob privado conserva una instantánea SQLite de las reservas compartidas. La identidad administrada limita el acceso al contenedor y un ETag impide sobrescribir cambios concurrentes.

**Guardar no reentrena el modelo ni modifica las métricas históricas.** La variante local sigue disponible y conserva su SQLite independiente.

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

**Preparación, entrenamiento y evaluación: Completed.** Nueva ejecución `microproyecto3-reejecucion-20261001` en `MICROPROYECTO3`, región North Central US. Modelo registrado `reservaiq:1`. Las 7.990 predicciones y el SHA-256 coinciden con la ejecución original. App Service publica la demo y Blob conserva las reservas compartidas. El clúster tiene 0–1 nodos y quedó verificado en cero. Recursos conservados hasta el 5 de octubre inclusive, hora de Colombia.

| Alcance | USD |
| --- | ---: |
| Consumo original del 25 de septiembre, antes de impuestos | 0,0620879781 |
| Consumo de MICROPROYECTO3 | Sin filas todavía |
| CPU, supuesto de 1 h × 0,146 USD/h | 0,1460 |
| Registro Basic, 6 días × 0,1666 USD/día | 0,9996 |
| Almacenamiento, operaciones y margen | 0,8544 |
| App Service F1 | 0 |
| Total estimado de ejecución y conservación | 2 |
| Límite autorizado | 3 |

Consulta de Cost Management: 01/10/2026, 03:20 UTC. La estimación no es factura. El valor original no corresponde a la nueva ejecución. [Desglose y evidencia](COSTOS.md).

## 9. Flujo de una reserva en la demo

1. **Elegir fechas:** creación, llegada y salida en el calendario.
2. **Revisar los detalles:** seis categorías y resumen de la estancia.
3. **Analizar y guardar:** índice del modelo y confirmación con código.
4. **Consultar Mis reservas:** filtrar pendientes, revisar y volver a abrir.

El calendario se puede ocultar sin perder las fechas. La aplicación calcula anticipación, mes y reparto de noches. **Solo analizar no crea un registro.**

La web conserva fechas, entradas, resultado y estado en Blob privado con formato SQLite. Se verificó su conservación después de reiniciar App Service. Todos comparten los registros ficticios. Guardar permite dar seguimiento, sin confirmar disponibilidad hotelera. Los CSV usan el mismo modelo y permiten revisar el lote antes de guardarlo.

**CSV:** 1–500 filas; analizar → vista previa → guardar lote. **Caso histórico:** reserva 12301, índice aproximado 39,8, cancelación conocida. **Error de entrada:** 61 días de anticipación o cero noches deben rechazarse sin guardado.

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
| 67 pruebas en cada sistema | 41 de Python + 26 de JavaScript en Windows y Ubuntu. Cubren datos, API, fechas, lotes, persistencia y controles de la interfaz |
| 7.990 predicciones coincidentes | El modelo descargado reproduce los resultados guardados de las reservas de prueba |
| SHA-256 del artefacto | La huella identifica el archivo utilizado; los registros distinguen el trabajo original del nuevo trabajo completado |
| Validación colombiana pendiente | Antes de operar en Colombia hay que validar con datos locales y medir el efecto real de las acciones |

Además se realizaron 31 comprobaciones HTTPS y nueve registros persistieron tras reiniciar App Service. Las pruebas de API y componentes no sustituyen una revisión completa en navegador. Los datos históricos no garantizan desempeño en Colombia ni demuestran cancelaciones evitadas.

[Evidencia automática de la versión publicada](https://github.com/nathernandez1189/reservaiq-azure-ml/actions) · [Alcance de las verificaciones](EVIDENCIAS.md).

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
