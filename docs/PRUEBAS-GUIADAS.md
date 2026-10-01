# Pruebas guiadas de ReservaIQ

## Entorno de la demostración

Realiza el recorrido en [la demo web](https://reservaiq-microproyecto3-20261001.azurewebsites.net/) con datos ficticios. Los registros son compartidos. La alternativa `127.0.0.1:8765` requiere iniciar la app y utiliza una base independiente.

La prueba de reinicio del servicio web ya se documentó en [web-verification.json](../azure/evidence/microproyecto3/web-verification.json): nueve registros conservaron sus datos. Durante la exposición basta guardar, recargar y volver a abrir el registro; recargar una página no demuestra por sí solo un reinicio del servidor. No reinicies ni reentrenes Azure como parte del recorrido normal.

Suite actual: 41 pruebas Python y 26 JavaScript, ejecutadas en Windows y Ubuntu. Además hubo 31 comprobaciones reales HTTPS. El ensayo completo con navegador y cronómetro se realiza aparte.

Estas acciones permiten comprobar el funcionamiento de la aplicación. Los resultados esperados se distinguen de las comprobaciones automáticas; esta tabla no afirma que el lector ya las haya realizado.

Usa datos de ejemplo. En la web, los registros quedan compartidos en Azure; en modo local, permanecen en el computador que ejecuta el servidor. Puedes archivarlos al terminar.

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | Iniciar la aplicación y entrar a Cómo probarlo → Comprobar conexión | Servidor/modelo, evidencias y acceso al guardado aparecen disponibles. No prueba entrenamiento remoto nuevo. |
| 2 | Cargar ejemplo de prueba | Registro histórico 12301, anticipación 28 días, estancia de 3 noches; estado Sin guardar. |
| 3 | Pulsar Solo analizar | Índice aproximado 39,8 y sugerencia Priorizar revisión. No aparece en Mis reservas. |
| 4 | Pulsar Analizar y guardar | Código RI-…, mensaje de guardado y registro en Mis reservas. |
| 5 | En la web: recargar y abrir desde otra ventana; en local: cerrar y reiniciar el servidor | La misma referencia y código siguen disponibles. |
| 6 | Abrir la reserva, ir a Fechas y cambiar anticipación de 28 a 7; volver a Revisar y guardar → Solo analizar | Índice aproximado 13,6 y seguimiento habitual. La copia guardada todavía conserva el dato anterior. El desenlace del escenario editado es desconocido. |
| 7 | Pulsar Guardar cambios y volver a abrir | Mismo código, nuevos datos y resultado, estado pendiente. No crea una segunda reserva. |
| 8 | Marcar revisada; archivar; filtrar Archivadas y restaurar | Cambios reversibles de estado, sin borrar la reserva ni contactar huéspedes. |
| 9 | Seleccionar el CSV de ejemplo y Analizar lote | 8 filas analizadas, 0 por encima del umbral, vista previa. Todavía no guardadas. |
| 10 | Guardar lote y visitar Mis reservas | Se añaden 8 reservas identificadas como Importada de CSV. |
| 11 | En el modo de ejemplo histórico, escribir 61 días de anticipación o 0 noches totales | Se impide el envío o se explica el error; no se guarda una entrada inválida. |
| 12 | Crear una copia del CSV con una celda vacía o una fila fuera de alcance | Se rechaza todo el lote, sin un guardado parcial. |
| 13 | Modificar la misma reserva desde dos ventanas | La segunda edición con una versión antigua se rechaza. Actualizar y reabrir recupera la versión vigente. |
| 14 | Cambiar capacidad a 2 con al menos 3 pendientes | Se marcan las 2 pendientes de mayor índice. La lista histórica de Inicio permanece independiente. |
| 15 | Descargar copia de todas | Archivo JSON con referencias, diez variables, resultados, estados, marcas de guardado, fechas de estancia cuando se conocen y procedencia del modelo. No hay importador JSON en esta versión. |

## Probar el calendario de principio a fin

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| C1 | Abrir Nueva reserva y Continuar sin elegir fechas | Explicación junto a los campos; se mantiene el paso Fechas y no se guarda nada. |
| C2 | En Fecha de creación de la reserva, escribir 01/10/2026 | El calendario se sitúa en octubre. Esta fecha es solo un caso de práctica reproducible. |
| C2b | Pulsar Creación de la reserva en el calendario, elegir 30/09/2026 y después llegada 02/10 y salida 05/10 | Creación visible, 2 días de anticipación y 3 noches. Cambiar la creación al 01/10 conserva la estancia y recalcula a 1 día. Las tres fechas se recuperan al abrir la reserva. |
| C3 | Pulsar Llegada en el selector del calendario, elegir 02/10/2026 y después salida 05/10/2026 | 3 noches: viernes, sábado y domingo. 1 entre semana, 2 de fin de semana; 1 día de anticipación. El lunes de salida no cuenta. |
| C3b | Después de elegir la salida, pulsar Mostrar calendario y luego Ocultar calendario | El panel se despliega y recoge sin cambiar fechas, noches, índice ni guardado. Los campos y resumen siguen visibles. |
| C4 | Continuar con los detalles; referencia `Prueba calendario`; revisar los seis campos | Ayudas junto a cada opción; el resumen muestra el contexto de la estancia. |
| C5 | Revisar mi reserva → Solo analizar | Índice y recomendación reales del modelo para ese escenario; no hay registro guardado todavía. No se presupone una puntuación ni cancelación. |
| C6 | Analizar y guardar; ir a Mis reservas | Código RI-… y tarjeta con las fechas de llegada y salida. |
| C7 | Recargar y abrir Prueba calendario; reiniciar el servidor solo en modo local | Mismo código, mismas fechas y mismo resultado. |
| C8 | Volver al paso Fechas; cambiar salida al 06/10; revisar y guardar cambios | 4 noches (2 entre semana, 2 de fin de semana); mismo código, resultado recalculado. |
| C9 | Elegir una salida anterior a la llegada o superior a 30 noches | Mensaje comprensible; no se guarda una entrada inválida. Los días fuera de alcance están deshabilitados en el calendario. |
| C10 | Navegar usando Tab, flechas y Enter; probar una pantalla pequeña y zoom al 200 % | Controles visibles, foco perceptible y recorrido completo. Es una comprobación manual pendiente, no un resultado certificado. |
| C11 | Abrir un registro anterior o Cargar ejemplo de prueba | Se conservan sus variables; no aparecen fechas ficticias. Puede elegirse explícitamente el modo calendario para crear un escenario editado. |

## Comprobar las tarjetas de estado

Pulsa Guardadas, Pendientes, Revisadas y Archivadas en Mis reservas. El título y los registros deben corresponder a la tarjeta; Guardadas incluye todos los estados. Con una reserva revisada y ninguna pendiente, Revisadas muestra ese registro y Pendientes muestra un estado vacío explicado. La búsqueda se limpia al pulsar una tarjeta, la paginación vuelve a la primera página y el selector de estado se sincroniza.

## Qué comprueban los tests automáticos

- Cálculo de anticipación y noches, exclusión de la salida, cambio de año, año bisiesto y fechas independientes de la zona horaria.
- Migración de las reservas anteriores sin perder sus campos; rechazo de fechas inconsistentes en el servidor, persistencia de fechas y recuperación tras reiniciar.
- Recorrido de tres pasos, elección con calendario y teclado, revisión, edición y separación del modo histórico mediante pruebas de componentes.
- Integridad de datos y modelo, separación temporal, métricas y coincidencia de las 7.990 predicciones.
- Contrato de entradas, límites de lote y rechazo de peticiones de otro origen.
- Persistencia real en SQLite y recuperación después de reiniciar el servidor HTTP.
- Reintentos concurrentes sin duplicación, edición sin crear otra reserva, bloqueo de versiones antiguas y archivo/restauración.
- Guardado de lote completo o ninguno; los artefactos históricos conservan sus huellas antes y después.
- CSV con BOM, comillas, comas/punto y coma, celdas inválidas y límite de filas.
- Componentes de interfaz con una API simulada: separación de análisis/guardado, invalidación de resultados editados, protección frente a HTML en referencias, archivo/restauración, vista previa de lotes y recuperación tras un fallo de conexión.

Desde el entorno Python del proyecto:

```bash
python -m unittest discover -s tests -v
```

Las comprobaciones del cliente para desarrollo utilizan Node.js (no se necesita para usar la aplicación):

```bash
npm ci
npm test
```

El estado y los límites de la verificación de esta versión están en [Evidencias](EVIDENCIAS.md). Las pruebas automáticas no equivalen a una revisión visual en todos los dispositivos.
