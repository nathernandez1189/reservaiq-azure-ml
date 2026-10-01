# Experiencia de usuario de ReservaIQ

## Necesidad y objetivo

El usuario debe entender que ReservaIQ ayuda a priorizar revisiones y conservar reservas ficticias compartidas en la web, o copias independientes en modo local. El recorrido principal debe permitir elegir una estancia, revisar los detalles y guardar sin calcular manualmente noches o anticipación.

Se tomó como referencia la [explicación de experiencia de usuario de IBM](https://www.ibm.com/es-es/think/topics/user-experience): la utilidad, facilidad de uso y percepción dependen de la interacción completa. Las decisiones siguientes son una aplicación al proyecto; no constituyen una certificación ni sustituyen observar a personas usando la demo.

## Decisiones implementadas

| Fricción anterior | Cambio | Cómo se comprueba |
| --- | --- | --- |
| No saber dónde empezar | Inicio explica propósito y ofrece una acción principal: elegir fechas | Se puede identificar el primer paso sin leer métricas del modelo |
| Calcular cuatro variables temporales | Calendario compartido para creación, llegada y salida; las tres fechas siempre visibles y creación por defecto hoy | Las noches, su distribución, mes y anticipación se calculan automáticamente |
| Demasiados campos al mismo tiempo | Fechas → Detalles → Revisar y guardar | Indicador de paso, botones Atrás/Continuar y revisión antes de guardar |
| Contadores que no permiten consultar registros | Tarjetas Guardadas, Pendientes, Revisadas y Archivadas pulsables | Filtran la lista, resaltan la categoría y explican los estados vacíos |
| Calendario grande después de elegir la estancia | Botón Mostrar/Ocultar y cierre al seleccionar salida | Las fechas y el resumen permanecen; ocultar no vuelve a analizar ni modifica registros |
| No recordar lo elegido | Resumen de estancia durante el recorrido y revisión de todos los datos | Se muestran llegada, salida, noches y contexto |
| Confundir analizar con guardar | Acciones y estados explícitos; confirmación con código y acceso a Mis reservas | Solo analizar no crea un registro; guardar confirma una escritura correcta |
| Confundir el registro de demo con compra | Texto al guardar y en Inicio | Se explica que no se consulta disponibilidad ni se confirma una habitación |
| Usar un resultado desactualizado | Retirar el resultado al editar | Debe analizarse de nuevo antes de usar el índice |
| Confundir datos nuevos y evidencia | Métricas históricas agrupadas aparte; ejemplos identificados | Guardar no modifica entrenamiento ni resultados históricos |
| No entender un error | Validación junto a fechas y mensajes con una acción de recuperación | Fechas incompletas o fuera de alcance impiden continuar sin perder el resto |

## Calendario y accesibilidad implementada

Se muestran dos meses en pantallas amplias y uno en pantallas pequeñas. Llegada, salida y rango tienen estilos diferenciados. Los botones incluyen la fecha completa en su nombre accesible; hay foco visible, navegación por teclado y campos de fecha como alternativa. Los cambios importantes tienen mensajes de estado y los errores se asocian a los campos. El enlace para saltar al contenido evita recorrer todo el menú con el teclado.

Estos elementos están implementados. La validación visual en dispositivos, zoom y lectores de pantalla requiere una sesión manual; no se afirma conformidad WCAG completa.

## Datos, persistencia y límites

El calendario admite 0–60 días de anticipación y 1–30 noches. Una estancia incluye la noche de llegada y excluye la fecha de salida. Sábado y domingo se cuentan como fin de semana. Se utilizan fechas civiles, sin depender de cambios de hora del sistema.

El servidor vuelve a validar las fechas y exige correspondencia con las variables del modelo. La base conserva las fechas y el resultado juntos. Los registros anteriores y los CSV sin fechas permanecen utilizables en su modo original. No se inventan fechas para explicar un dato histórico.

El sistema no reserva inventario, cobra, contacta huéspedes ni sincroniza registros entre computadores. El índice no es una probabilidad calibrada. El modelo sigue siendo el artefacto histórico de Azure; las nuevas reservas no lo reentrenan.

## Validación y siguiente comprobación con personas

Las pruebas automáticas verifican aritmética, límites, cambios de año, recuperación de datos, consistencia entre cliente y servidor, teclado y pasos del formulario con componentes simulados. Los comandos y resultados están en [Evidencias](EVIDENCIAS.md). El acceso de navegador quedó bloqueado por una comprobación administrativa indisponible; no se generaron capturas automatizadas ni se afirmó una prueba visual de extremo a extremo. Se revisó visualmente el recorte de calendario aportado en la conversación. El archivo temporal no pudo leerse por restricciones del sistema, por lo que no se añadió una copia al repositorio.

Una prueba breve con cada integrante puede usar estas tareas, sin explicar primero dónde pulsar:

1. Explicar con sus palabras para qué sirve ReservaIQ y si guardar confirma una habitación.
2. Crear una estancia de tres noches y encontrar cuántas corresponden a fin de semana.
3. Guardarla, volver a abrirla y cambiar la salida manteniendo el mismo código.
4. Probar una fecha incorrecta y recuperarse usando el mensaje mostrado.
5. Explicar qué significa el índice y qué acción humana propone.

Registrar por tarea: completada sin ayuda, dificultad, mensaje que causó confusión y cambio sugerido. Probar también teclado y pantalla pequeña. Esta lista es un protocolo pendiente de ejecutar con personas; no se presenta como investigación ya realizada.
