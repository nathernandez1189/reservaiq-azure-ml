# Evidencia de la versión web actual

Sitio revisado: [ReservaIQ en Azure App Service](https://reservaiq-microproyecto3-20261001.azurewebsites.net/).

## Procedencia y alcance

El equipo aportó 15 capturas de las seis vistas de la aplicación, fechadas por sus nombres el **30 de septiembre de 2026, 23:38–23:40 en Colombia** (1 de octubre UTC). Esta revisión describe lo visible en esas imágenes. Los PNG adjuntos no están disponibles en las rutas locales proporcionadas: **este documento contiene el inventario y las observaciones; todavía no incorpora los 15 archivos gráficos**. No se recrearon capturas.

La comprobación HTTP actual se registra por separado en [web-current-check.json](../azure/evidence/microproyecto3/web-current-check.json). La captura real del pipeline y las cuatro capturas locales históricas siguen disponibles en [CAPTURAS.md](CAPTURAS.md).

## 01. Inicio y propósito

**Fecha indicada:** 2026-09-30 23:38:35.

**Qué se observa.** La portada presenta la priorización de reservas, el acceso para elegir fechas y tres pasos de uso. Identifica una demo web compartida con reservas ficticias.

**Por qué importa.** Introduce la necesidad del hotel y el recorrido principal.

**Alcance.** La etiqueta de Azure ML se complementa con los registros del trabajo; la captura no prueba por sí sola la infraestructura.

## 02. Recorrido inicial

**Fecha indicada:** 2026-09-30 23:38:41.

**Qué se observa.** Se ven las tarjetas elegir estancia, revisar y guardar, y probar y comprender; también el acceso al ejemplo guiado.

**Por qué importa.** Facilita el primer uso y el descubrimiento de las funciones.

**Alcance.** Documenta la interfaz, no una medición de usabilidad con usuarios.

## 03. Creación y fechas de la reserva

**Fecha indicada:** 2026-09-30 23:38:50.

**Qué se observa.** El formulario muestra creación, llegada y salida, el estado Sin guardar, los tres pasos y el control Ocultar calendario.

**Por qué importa.** Expone la fecha de creación y permite comprender cómo se deriva la anticipación.

**Alcance.** Llegada y salida aún están vacías; esta imagen no documenta una reserva guardada.

## 04. Calendario y carga CSV

**Fecha indicada:** 2026-09-30 23:38:57.

**Qué se observa.** Se ve el calendario, la indicación de elegir fechas, el botón para continuar y los apartados de CSV hasta 500 registros y casos históricos.

**Por qué importa.** Distingue el recorrido individual de la importación por lote.

**Alcance.** Los apartados están cerrados; no muestra una importación ejecutada ni la validación de 500 filas.

## 05. Reservas guardadas y organización

**Fecha indicada:** 2026-09-30 23:39:04.

**Qué se observa.** Mis reservas muestra 9 guardadas, 1 pendiente, 0 revisadas y 8 archivadas. La reserva ficticia activa tiene índice 5,7 y acciones Abrir, Marcar revisada y Archivar.

**Por qué importa.** Hace visible el registro guardado, los filtros y la prioridad según capacidad.

**Alcance.** Los conteos pertenecen a esta sesión. Una captura aislada no acredita permanencia después de reiniciar; esa prueba tiene su registro HTTPS independiente.

## 06. Prueba guiada del calendario

**Fecha indicada:** 2026-09-30 23:39:15.

**Qué se observa.** Se explica el caso creación 01/10/2026, llegada 02/10 y salida 05/10: tres noches, una entre semana y dos de fin de semana, con un día de anticipación.

**Por qué importa.** Ofrece pasos y resultados esperados que un evaluador puede reproducir.

**Alcance.** Es una guía visible, no el resultado de ejecutar el caso. La variante web requiere conexión a Azure; la alternativa local permite practicar sin recursos de cómputo Azure.

## 07. Caso histórico, guardado y edición

**Fecha indicada:** 2026-09-30 23:39:24.

**Qué se observa.** La guía presenta el registro 12301, índice esperado 39,8 y comparación al cambiar de 28 a 7 días de anticipación, con índice esperado 13,6.

**Por qué importa.** Relaciona el análisis con guardar, recuperar y actualizar sin duplicar el registro.

**Alcance.** Los valores son resultados esperados de la guía; la captura no muestra la ejecución de esas cuatro acciones.

## 08. Estados, lote y conexión

**Fecha indicada:** 2026-09-30 23:39:31.

**Qué se observa.** La guía explica revisar, archivar, restaurar, analizar y guardar un CSV, además de probar entradas inválidas. Se ve Comprobar conexión.

**Por qué importa.** Permite revisar el ciclo de uso y los controles de entrada.

**Alcance.** No muestra el resultado del botón ni una respuesta de rechazo; consultar las pruebas registradas para esas comprobaciones.

## 09. Evaluación en prueba reservada

**Fecha indicada:** 2026-09-30 23:39:39.

**Qué se observa.** Se ven 21.236 registros de entrenamiento, 6.161 de validación y 7.990 de prueba. Matriz: TP 1.467, FN 364, FP 2.715 y TN 3.444; ROC AUC 0,731 y AP 0,413.

**Por qué importa.** Permite revisar resultados y errores sin confundir alerta por umbral con prioridad por capacidad.

**Alcance.** Son métricas históricas; las reservas nuevas no las modifican. El índice no es una probabilidad calibrada.

## 10. Comparación y límites del modelo

**Fecha indicada:** 2026-09-30 23:39:46.

**Qué se observa.** La tabla de validación compara base, regresión logística, Random Forest y Gradient Boosting. Se ven importancias por permutación y controles contra fuga de información.

**Por qué importa.** Explica la selección por AP y las variables relevantes, junto con las restricciones del experimento.

**Alcance.** La importancia es global y no causal. Los datos históricos de Portugal requieren validación antes de uso real en Colombia.

## 11. Problema y decisión de negocio

**Fecha indicada:** 2026-09-30 23:40:04.

**Qué se observa.** La vista describe al Hotel Brisa del Valle, cliente ficticio, y la decisión de revisar K reservas con entrada, resultado y acción humana.

**Por qué importa.** Vincula la solución técnica con una necesidad y una capacidad limitada.

**Alcance.** La demo no confirma habitaciones ni demuestra cancelaciones evitadas.

## 12. Correspondencia con la rúbrica

**Fecha indicada:** 2026-09-30 23:40:16.

**Qué se observa.** Se muestran los cuatro criterios: análisis 20 %, diseño 25 %, implementación 30 % y presentación 25 %, con enlaces a documentos, pruebas y Canva.

**Por qué importa.** Facilita localizar la evidencia de cada requisito del microproyecto.

**Alcance.** La correspondencia no asigna una nota ni certifica haber realizado una exposición de 15 minutos.

## 13. Alternativas de solución

**Fecha indicada:** 2026-09-30 23:40:26.

**Qué se observa.** La tabla compara reglas manuales, clasificación con revisión humana y AutoML; debajo comienza el diagrama de arquitectura.

**Por qué importa.** Documenta ventajas, límites y la selección del clasificador.

**Alcance.** La comparación de AutoML es conceptual; los candidatos efectivamente entrenados están en la tabla de validación.

## 14. Arquitectura completa de la demo web

**Fecha indicada:** 2026-09-30 23:40:32.

**Qué se observa.** El diagrama conecta datos, prepare, train, evaluate, registro del modelo, App Service F1, navegador y Blob privado con SQLite. La prueba reservada y el modelo llegan por separado a evaluación.

**Por qué importa.** Distingue entrenamiento, evaluación, publicación e inferencia; representa el guardado compartido y la variante local independiente.

**Alcance.** Es un diagrama explicativo de la implementación. El registro y la publicación son pasos posteriores al pipeline; guardar no reentrena.

## 15. Flujo, procedencia y costo estimado

**Fecha indicada:** 2026-09-30 23:40:43.

**Qué se observa.** Se ve el flujo en cinco pasos, trabajo Completed, modelo Azure ML y cero nodos al corte explícito 2026-10-01 02:46 UTC. El costo mostrado es aproximadamente US$2.

**Por qué importa.** Relaciona los componentes con el uso web y expone fecha de comprobación y alcance económico.

**Alcance.** US$2 es una estimación, no un costo facturado. Cero nodos corresponde al corte indicado, no a una consulta en vivo. Consultar COSTOS.md para cargos fechados.

## Relación con los criterios del profesor

| Criterio | Evidencia descrita | Verificación complementaria |
|---|---|---|
| Análisis · 20 % | Problema y decisión (11), alternativas (13), alcance (3–4), costo aproximado (15) | Informe técnico y COSTOS.md |
| Diseño · 25 % | Arquitectura completa (14), componentes y flujo (15) | ARQUITECTURA.md y configuración del pipeline |
| Demo · 30 % | Inicio (1–2), fechas (3–4), registro guardado (5), guía (6–8), resultados (9–10) | Pruebas automatizadas y registro HTTPS con reinicio |
| Presentación · 25 % | Correspondencia y acceso a Canva (12) | Presentación de 15 minutos; requiere ensayo y exposición real |

**Diferencias frente a la interfaz histórica:** seis vistas, calendario de creación/llegada/salida, recorrido por pasos, guardado compartido, estados y filtros de reservas, ayuda guiada, arquitectura con App Service y Blob privado. Entrenamiento e inferencia siguen separados; guardar reservas no altera las métricas.
