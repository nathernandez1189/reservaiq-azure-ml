# Pruebas guiadas de ReservaIQ

Estas acciones permiten comprobar el funcionamiento de la aplicación. Los resultados esperados se distinguen de las comprobaciones automáticas; esta tabla no afirma que el lector ya las haya realizado.

Usa datos de ejemplo. Las reservas que guardes permanecerán en tu computador. Puedes archivarlas al terminar.

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | Iniciar la aplicación y entrar a Cómo probarlo → Comprobar conexión | Servidor/modelo, evidencias y acceso al guardado aparecen disponibles. No prueba entrenamiento remoto nuevo. |
| 2 | Cargar ejemplo de prueba | Registro histórico 12301, anticipación 28 días, estancia de 3 noches; estado Sin guardar. |
| 3 | Pulsar Solo analizar | Índice aproximado 39,8 y sugerencia Priorizar revisión. No aparece en Mis reservas. |
| 4 | Pulsar Analizar y guardar | Código RI-…, mensaje de guardado y registro en Mis reservas. |
| 5 | Recargar la página, cerrar el servidor y volver a iniciarlo | La misma referencia y código siguen disponibles. |
| 6 | Abrir la reserva y cambiar anticipación de 28 a 7; Solo analizar | Índice aproximado 13,6 y seguimiento habitual. La copia guardada todavía conserva el dato anterior. El desenlace del escenario editado es desconocido. |
| 7 | Pulsar Guardar cambios y volver a abrir | Mismo código, nuevos datos y resultado, estado pendiente. No crea una segunda reserva. |
| 8 | Marcar revisada; archivar; filtrar Archivadas y restaurar | Cambios reversibles de estado, sin borrar la reserva ni contactar huéspedes. |
| 9 | Seleccionar el CSV de ejemplo y Analizar lote | 8 filas analizadas, 0 por encima del umbral, vista previa. Todavía no guardadas. |
| 10 | Guardar lote y visitar Mis reservas | Se añaden 8 reservas identificadas como Importada de CSV. |
| 11 | Escribir 61 días de anticipación o 0 noches totales | Se impide el envío o se explica el error; no se guarda una entrada inválida. |
| 12 | Crear una copia del CSV con una celda vacía o una fila fuera de alcance | Se rechaza todo el lote, sin un guardado parcial. |
| 13 | Modificar la misma reserva desde dos ventanas | La segunda edición con una versión antigua se rechaza. Actualizar y reabrir recupera la versión vigente. |
| 14 | Cambiar capacidad a 2 con al menos 3 pendientes | Se marcan las 2 pendientes de mayor índice. La lista histórica de Inicio permanece independiente. |
| 15 | Descargar copia de todas | Archivo JSON con referencias, diez variables, resultados, estados, fechas y procedencia del modelo. No hay importador JSON en esta versión. |

## Qué comprueban los tests automáticos

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
