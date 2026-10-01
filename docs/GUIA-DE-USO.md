# Usar ReservaIQ paso a paso

ReservaIQ ayuda a decidir qué reservas revisar primero. Puedes **analizar, guardar, volver a abrir y organizar copias locales**. Guardar aquí no confirma una habitación ni envía datos a un hotel.

## 1. Actualizar e iniciar

Si ya clonaste el repositorio, detén la aplicación con `Ctrl+C` en su terminal. En la carpeta del proyecto ejecuta:

```bash
git pull --ff-only
```

Si Git avisa que tienes cambios locales en conflicto, consérvalos antes de continuar; no los borres para forzar la actualización.

Necesitas **Python 3.12**. En Windows, abre `iniciar-windows.cmd` con doble clic o ejecuta:

```powershell
py -3.12 iniciar.py
```

En macOS, abre `iniciar-mac.command` o ejecuta:

```bash
python3.12 iniciar.py
```

El lanzador prepara `.venv`, instala las versiones de `requirements.txt` cuando hacen falta e inicia el servidor con ese mismo Python. La primera instalación requiere internet. No necesitas activar manualmente el entorno ni cambiar las políticas de PowerShell. Si falta `joblib`, usa este lanzador para que instalación y ejecución compartan el entorno.

Abre **http://127.0.0.1:8765**. Mantén la terminal abierta. No abras `web/index.html` como archivo. Para salir, pulsa `Ctrl+C`; las reservas guardadas permanecen. Si el puerto está ocupado, inicia con `--port 8766` y abre la dirección que muestra la terminal.

## 2. Crear tu primera reserva

1. Entra en **Nueva reserva**.
2. Escribe una referencia opcional, por ejemplo `Prueba del grupo`. No necesitas datos personales.
3. Ajusta los diez campos a tu caso. Cada uno incluye una explicación. La anticipación va de 0 a 60 días y las noches deben sumar de 1 a 30.
4. Pulsa **Analizar y guardar**.
5. Comprueba el índice, la sugerencia y el mensaje **Guardada en este computador**, con un código `RI-…`.
6. Entra en **Mis reservas**. Tu registro ya debe aparecer.

**Solo analizar** calcula el resultado sin guardar ni modificar la copia existente. Descargar un resultado crea un archivo para consultarlo; tampoco sustituye al botón de guardado.

## 3. Entender el resultado

- **Índice / 100:** una señal del clasificador. Un valor alto concentra más señales históricas de cancelación. No es una probabilidad calibrada.
- **Priorizar revisión:** alcanzó el umbral de 17/100 elegido en validación. Sugiere revisar la información; no significa que vaya a cancelar con certeza.
- **Seguimiento habitual:** está por debajo del umbral. También puede ocurrir una cancelación.
- **Prioritaria en Mis reservas:** está entre las K pendientes con mayor índice según tu capacidad. Esta selección y la alerta por umbral son decisiones distintas.

No se envían mensajes ni se realizan cobros o cancelaciones. Los estados de revisión los cambia el usuario.

## 4. Volver a abrir y editar

1. Busca la referencia en **Mis reservas** y pulsa **Abrir**.
2. Cambia un dato. Verás **Cambios sin guardar** y el resultado anterior se retirará para no confundirlo con el nuevo.
3. Puedes pulsar **Solo analizar** para comparar sin modificar la copia guardada.
4. Pulsa **Guardar cambios** para conservar la edición. Se mantiene el código, se recalcula el resultado y vuelve a quedar pendiente de revisión.
5. Si otra ventana modificó la reserva, actualiza la lista y vuelve a abrirla: no se sobrescriben silenciosamente cambios ajenos.

Recargar la página conserva lo que ya se guardó. Los campos que todavía no hayas guardado no son una reserva persistida.

## 5. Organizar tus reservas

**Mis reservas** permite buscar por referencia o código y filtrar por activas, pendientes, revisadas o archivadas. Se ordenan por índice y se muestran hasta 20 por página.

Indica cuántas puedes revisar. Las primeras K pendientes quedan marcadas como **Prioritarias**. Si hay menos de K pendientes, se seleccionan las disponibles. La búsqueda y los filtros no cambian la prioridad global de tus pendientes.

- **Marcar revisada:** registra que examinaste sus datos; no confirma un contacto ni un desenlace.
- **Volver a pendiente:** permite revisarla de nuevo.
- **Archivar:** la retira de las activas sin borrarla.
- **Restaurar:** se encuentra al filtrar por Archivadas y devuelve la reserva a pendientes.

## 6. Subir un lote CSV

1. En **Nueva reserva → Importar un archivo CSV**, descarga el ejemplo o utiliza `ejemplos-csv/reservas-listas.csv`.
2. Selecciona el archivo y pulsa **Analizar lote**.
3. Revisa el resumen y las primeras ocho filas. Todavía no están guardadas.
4. Pulsa **Guardar lote** para conservar todas las reservas. Una fila inválida impide guardar el lote completo.
5. Abre **Mis reservas** o descarga los resultados con su botón explícito.

Se admiten comas o punto y coma, comillas de CSV y archivos UTF-8 de hasta 150 KB y 500 reservas. Mantén las diez columnas del ejemplo y no dejes celdas vacías. [Diccionario completo](../ejemplos-csv/LEEME.md).

Reintentar la misma operación no duplica el guardado. **Importar y analizar otra vez el mismo archivo constituye un lote nuevo**: esta versión no identifica automáticamente reservas duplicadas a partir de diez variables, porque dos reservas legítimas pueden compartir esos datos.

## 7. Dónde se guarda y cómo conservarlo

La base está en `.runtime/reservaiq.sqlite3` dentro de la carpeta del proyecto. Cada computador tiene su propia copia, que no se sube a GitHub ni se sincroniza con Azure. `git pull` no reemplaza esa base ignorada por Git.

Para trasladar o respaldar la base completa, **cierra primero la aplicación** y copia la carpeta `.runtime` junto con el proyecto. No elimines esa carpeta si quieres conservar las reservas. En **Mis reservas → Descargar copia de todas**, también puedes obtener los datos en JSON para consultarlos; esta versión no tiene un importador de copias JSON.

Los datos guardados son independientes del dataset histórico, el modelo y sus métricas. Guardar una nueva reserva no reentrena el modelo y no añade una etiqueta de cancelación conocida.

## 8. Probar y solucionar problemas

Entra en **Cómo probarlo** para seguir seis pasos con resultados esperados y comprobar la conexión. La [matriz de pruebas guiadas](PRUEBAS-GUIADAS.md) permite registrar qué comprobaste.

| Mensaje o situación | Qué hacer |
| --- | --- |
| No conecta / Failed to fetch | Verifica que la terminal del servidor siga abierta. Reinicia con el lanzador y recarga la página. |
| No module named joblib | Ejecuta `iniciar.py` con Python 3.12 para instalar las dependencias en el entorno correcto. |
| UnicodeDecodeError: charmap | Actualiza el repositorio y reinicia; esta versión lee los archivos explícitamente como UTF-8. |
| La reserva cambió en otra ventana | Actualiza Mis reservas y abre de nuevo el registro antes de editarlo. |
| No se pudo guardar | Comprueba espacio y permisos de la carpeta. Conserva la base existente. |
| No veo reservas de un compañero | El almacenamiento es local a cada computador; el repositorio no contiene bases personales. |
| Veo cifras históricas en Inicio | Corresponden a la prueba del modelo, no a las reservas recién ingresadas. |

Abrir y usar la demo local no requiere encender recursos de Azure.
