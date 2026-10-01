# Arquitectura y flujo de ReservaIQ

## Versión actual: MICROPROYECTO3 y demo web

![Azure ML, modelo registrado, App Service y reservas compartidas](figuras/arquitectura-azure-web.svg)

La ejecución `microproyecto3-reejecucion-20261001` completó las etapas `prepare`, `train` y `evaluate` en `ml-microproyecto3`. La demo pública carga una copia verificada de `reservaiq:1` y conserva reservas ficticias compartidas. [Ejecución](../azure/evidence/microproyecto3/execution.json) · [Captura real](CAPTURAS.md#captura-real-de-azure-ml) · [Abrir la demo](https://reservaiq-microproyecto3-20261001.azurewebsites.net/).

**Las flechas representan datos y artefactos transferidos.** El modelo procede de entrenamiento; evaluación produce el informe. Registrar, descargar y publicar son pasos posteriores a revisar el trabajo Completed, no tres etapas adicionales del pipeline ni tareas automáticas desencadenadas por cada reserva.

## Componentes y responsabilidades

| Componente | Qué hace | Motivo de la elección |
| --- | --- | --- |
| Workspace Azure ML | Organiza datos, componentes, entorno, trabajos y registro del modelo | Procedencia y versiones consultables |
| Blob asociado a Azure ML | Conserva CSV, particiones y salidas de las etapas | Archivos separados del cómputo |
| Clúster `microproyecto3-cpu` | Ejecuta el pipeline con `Standard_DS2_v2`, mínimo 0, máximo 1 nodo e inactividad de 120 s | CPU suficiente y capacidad acotada |
| `prepare` | Valida alcance, deduplica, deriva fechas y fija particiones temporales | Reducir contaminación entre entrenamiento y prueba |
| `train` | Ajusta transformaciones y candidatos con entrenamiento; selecciona modelo y umbral con validación | Comparación controlada sin utilizar la prueba |
| `evaluate` | Aplica el modelo fijo a prueba; calcula métricas, ejemplos y predicciones | Medir desempeño retrospectivo sin reentrenar |
| Registro del modelo | Versiona el archivo de entrenamiento como `reservaiq:1` | Identificar el artefacto elegido |
| Descarga y verificación | Conserva modelo, selección, informe y huella; compara las 7.990 predicciones | Vincular ejecución y aplicación |
| App Service Linux F1 | Sirve interfaz y API HTTPS; valida, infiere y gestiona reservas | Acceso web sin instalar Python y sin endpoint permanente de Azure ML |
| Blob privado `reservaiq-demo` | Conserva `reservas.sqlite3`, una instantánea SQLite procesada en memoria | Persistencia compartida del prototipo entre reinicios |
| Navegador y personal del hotel | Eligen fechas, consultan señales, priorizan hasta K pendientes y revisan estados | Mantener la decisión en manos de una persona |

## Transferencias del pipeline y publicación

| Origen → destino | Archivo o contenido | Correspondencia con la implementación |
| --- | --- | --- |
| Datos / Blob → prepare | `hotels.csv`, activo `reservaiq-hotels:1` | Entrada `raw` del [pipeline ejecutado](../azure/evidence/microproyecto3/pipeline.yml) |
| prepare → train | Carpeta `splits`; lee `train.csv` y `validation.csv` | `pipeline.py: train()` |
| prepare → evaluate | Carpeta `splits`; lee `test.csv` y validación para importancia global | `pipeline.py: evaluate()`; validación no reajusta modelo ni umbral |
| train → evaluate | `model.joblib` y `selection.json` | Entrada `trained`; modelo y decisión ya fijados |
| train → registro | Archivo de modelo de la salida `trained` | Se registra después de comprobar el trabajo; no sale de evaluación |
| evaluate → paquete web | Informe, métricas, ejemplos y predicciones descargados | Salida `report`; alimenta las vistas de resultados y la cohorte histórica |
| registro → paquete web | Copia descargada de `reservaiq:1` | SHA-256 y `runtime.json` verifican la procedencia |
| paquete web → App Service | Código y `cloud-artifacts/` de la nueva ejecución | `scripts/pack_azure_web.py`; el original `artifacts/` permanece intacto |

Las tres etapas intercambian archivos almacenados en Blob; las líneas no son conexiones de red directas entre procesos. La preparación produce una carpeta común, pero cada función lee solamente los archivos descritos. La prueba se reserva para la evaluación final. [Método y límites](MODELO.md).

## Flujo operativo: fechas o CSV hasta revisión

![Flujo actual de análisis, guardado y revisión](figuras/flujo-reserva.svg)

1. **Capturar:** la persona elige creación, llegada y salida y revisa seis categorías. El calendario puede ocultarse sin perder la selección. Como alternativa, importa un CSV con diez columnas y 1–500 filas.
2. **Derivar y validar:** las fechas producen anticipación, mes de llegada y noches entre semana y de fin de semana. El servidor comprueba nuevamente las diez variables y, si existen fechas completas, su consistencia. Se admiten 0–60 días de anticipación y 1–30 noches; la salida no añade una noche.
3. **Inferir:** se aplica el modelo fijo y se devuelve índice, alerta por umbral y versión. **Solo analizar no escribe reservas.** El índice no es una probabilidad calibrada.
4. **Guardar expresamente:** Analizar y guardar confirma un código RI. Para CSV, Analizar lote genera vista previa y Guardar lote confirma el conjunto completo. Una entrada inválida rechaza el lote sin guardado parcial.
5. **Recuperar y seguir:** Mis reservas permite buscar, pulsar contadores de estado, abrir, editar, priorizar hasta K pendientes, marcar revisada, archivar y restaurar. Editar recalcula el resultado y exige la revisión vigente.
6. **Decidir y exportar:** una persona interpreta la señal y decide una acción. Guardar no confirma habitaciones, contacta huéspedes, cobra ni demuestra que se evitó una cancelación.

Los CSV y ejemplos históricos sin fechas completas conservan sus diez variables; no se inventan fechas. Las nuevas reservas no contienen etiquetas reales conocidas de cancelación, no entran al entrenamiento y no alteran las métricas ni la cohorte histórica de Inicio. [Pruebas paso a paso](PRUEBAS-GUIADAS.md).

## Guardado web y consistencia

La aplicación lee la instantánea de Blob y su ETag, realiza la transacción SQLite en memoria y publica la nueva instantánea condicionada a que el ETag siga vigente. Si otro cliente guardó primero, rechaza el conflicto en vez de sobrescribirlo. La revisión de cada registro evita ediciones antiguas y la clave del intento evita duplicar una misma solicitud repetida. El éxito se confirma después de escribir.

La identidad administrada de App Service accede únicamente al contenedor privado autorizado. El navegador nunca recibe claves de almacenamiento. No se monta SQLite sobre un sistema de archivos de red. La instantánea completa está limitada a 16 MiB; es un diseño acotado de demostración, no una base de datos productiva para alta concurrencia.

**La demo es pública y compartida, sin autenticación por usuario:** se usan exclusivamente reservas ficticias. Se verificaron 31 comprobaciones HTTPS y la conservación de nueve registros tras reiniciar App Service. El detalle y el alcance de la evidencia están en [web-verification.json](../azure/evidence/microproyecto3/web-verification.json). Recargar una página durante la exposición no equivale a reiniciar el servidor.

## Variante local e historia de las ejecuciones

![Variante local: modelo descargado y SQLite independiente](figuras/arquitectura.svg)

`python iniciar.py` abre la aplicación en cada computador. Usa `artifacts/` y `.runtime/reservaiq.sqlite3`, independientes de la web. GitHub no sincroniza reservas. El mismo calendario, contrato y estados están disponibles; la diferencia es dónde se ejecuta la aplicación y se conserva la base.

El grupo original `rg-reservaiq` se eliminó el 25 de septiembre. La ejecución nueva MICROPROYECTO3 y su demo se conservan hasta el 5 de octubre inclusive, hora de Colombia, según el plazo autorizado. Esa eliminación histórica no describe el estado del nuevo grupo. Los costos de ambas ejecuciones se documentan separados en [Costos](COSTOS.md).

## Fuente de los diagramas y alcance de la revisión

`scripts/diagrama_arquitectura.py` genera la arquitectura actual, la variante local y el flujo operativo en SVG. Las variantes oscuras conservan la misma topología para las diapositivas. El informe y el README utilizan `arquitectura-azure-web.svg`; el modo local de la aplicación utiliza `arquitectura-canva.svg`.

```bash
python -m pip install -r requirements-docs.txt
python scripts/diagrama_arquitectura.py
python scripts/generar_informe.py
```

La revisión compara cada transferencia con `pipeline.py`, el YAML del trabajo ejecutado, `app.py`, `storage.py` y `cloud_storage.py`. Los recursos auxiliares, como Container Registry y Key Vault, están descritos en [Costos](COSTOS.md): no son etapas adicionales del pipeline. La figura explica el flujo funcional solicitado por el microproyecto; no representa una topología productiva de redes.
