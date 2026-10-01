# ReservaIQ en MICROPROYECTO3

La nueva ejecución conserva en Azure el dataset, los componentes, el trabajo terminado y el modelo registrado. La aplicación web incorpora el mismo modelo para analizar reservas individuales o lotes CSV y guardar ejemplos compartidos. La ejecución original del 25 de septiembre y sus archivos en `artifacts/` permanecen separados.

[Abrir la demo web de ReservaIQ](https://reservaiq-microproyecto3-20261001.azurewebsites.net/)

## Cómo revisar lo cargado

1. Abrir [Azure Portal](https://portal.azure.com/) con la cuenta del proyecto y seleccionar **Azure for Students**.
2. **Grupos de recursos → MICROPROYECTO3 → ml-microproyecto3 → Iniciar Studio**.
3. En **Trabajos**, buscar `microproyecto3-reejecucion-20261001`. Abrir el gráfico: `prepare`, `train` y `evaluate` deben indicar **Completed**. Esta ejecución corresponde al **1 de octubre UTC / noche del 30 de septiembre de 2026 en Colombia**.
4. En **Modelos**, abrir `reservaiq`, versión `1`. En **Datos**, revisar `reservaiq-hotels` (dataset) y `reservaiq-entrega` (código y documentación). En **Componentes**, están `reservaiq_prepare`, `reservaiq_train` y `reservaiq_evaluate`.
5. En **Proceso / Compute → Clústeres de proceso**, abrir `microproyecto3-cpu`. Configuración: `Standard_DS2_v2`, mínimo 0 y máximo 1 nodo; inactividad 120 segundos. Después del trabajo se verificaron **0 nodos actuales y 0 deseados**.
6. Para la demo, abrir **Azure Portal → MICROPROYECTO3 → reservaiq-microproyecto3-20261001 → Examinar**. El usuario final no necesita instalar Python ni iniciar sesión en Studio.

Studio requiere acceso autorizado a la suscripción; compartir un enlace de Studio no concede permisos al profesor. El enlace público de la aplicación muestra el producto, pero no concede acceso al portal ni al contenedor privado.

## Flujo y almacenamiento

![Arquitectura del despliegue web](figuras/arquitectura-azure-web.svg)

- **Entrenamiento:** el CSV versionado entra en `prepare`. Las particiones de entrenamiento y validación alimentan `train`. La prueba reservada llega directamente a `evaluate` junto al modelo fijado. Después de verificar la evaluación se registra el modelo.
- **Publicación:** se descargan los artefactos de esta nueva ejecución a `cloud-artifacts/`, una carpeta excluida de Git. Se verifica la huella del modelo y se incorpora la procedencia en `runtime.json`. No se reemplaza `artifacts/`.
- **Aplicación:** Azure App Service Linux F1 ejecuta el modelo a través de Gunicorn y la misma API de la demo local. No utiliza un endpoint de inferencia de Azure ML encendido permanentemente.
- **Reservas de prueba:** la identidad administrada de App Service tiene `Storage Blob Data Contributor` únicamente sobre el contenedor privado `reservaiq-demo`. No se distribuyen claves ni SAS. SQLite realiza cada transacción en memoria; Blob conserva la copia resultante. Una escritura condicionada por ETag impide que dos clientes sobrescriban silenciosamente sus cambios. La revisión del registro y la clave del intento protegen frente a ediciones antiguas y reintentos duplicados.
- **Separación:** las reservas de la demo no reentrenan el modelo ni modifican sus métricas. El modo local sigue usando su archivo SQLite independiente.

Esta estrategia de almacenamiento es apropiada para una demostración pequeña: copia completa limitada a 16 MiB, importaciones de hasta 500 filas y reintento explícito si otro cliente guarda primero. Una aplicación de producción necesitaría autenticación por usuario, aislamiento de clientes, una base de datos transaccional de servicio y pruebas de carga. No se monta SQLite sobre un sistema de archivos de red.

## Cómo comprobar la demo

1. Elegir **Nueva reserva** y usar únicamente datos ficticios, sin nombres, correos ni teléfonos.
2. Seleccionar fecha de creación, llegada y salida. Continuar hasta **Analizar y guardar**.
3. Comprobar el índice, el código `RI-…` y **Guardada en Azure**. Abrir **Mis reservas** y recargar.
4. Abrir el mismo enlace en otro computador y pulsar **Actualizar lista**: debe aparecer la misma reserva.
5. Editar la reserva, guardar, marcar revisada, archivar y restaurar. Una edición antigua debe rechazarse y pedir actualizar.
6. Descargar el CSV de ejemplo, analizarlo, revisar la vista previa y guardar sus ocho filas. Analizar sin guardar no crea reservas.
7. Probar datos fuera del alcance: anticipación mayor que 60 días o cero noches. Se deben rechazar sin guardar parcialmente el lote.

La demo es **pública y compartida**: quienes tengan el enlace pueden ver y modificar las reservas ficticias. El contenedor no es público; las operaciones pasan por la aplicación. El índice no es una probabilidad calibrada ni demuestra que una acción evitará cancelaciones.

## Disponibilidad y costos

Disponibilidad solicitada: hasta el **lunes 5 de octubre de 2026, inclusive, hora de Colombia**, con límite autorizado de **US$3** para esta nueva ejecución y conservación. Antes del cierre deben descargarse las evidencias y cualquier reserva ficticia que se quiera conservar.

Presupuesto orientativo: **US$2**, no factura. App Service usa el nivel gratuito F1 (la API puede representarlo como `LinuxFree / U13`). La tarifa pública consultada para el clúster fue US$0,146 por hora de nodo y el registro Basic US$0,1666 por día. Para seis días, el registro suma aproximadamente US$1; se reserva margen para entrenamiento, almacenamiento, operaciones y recursos asociados. El tiempo real de uso y los cargos consolidados se revisan en Cost Management. Al verificar el 1 de octubre UTC aún no había filas de costo para MICROPROYECTO3: esto no significa costo cero.

F1 comparte capacidad, tiene cuota diaria de CPU, puede dormirse y no ofrece SLA. La primera apertura puede tardar; no se habilita un plan de pago para evitar ese límite. Cero nodos en Azure ML detiene el cómputo del clúster, pero no elimina cargos de almacenamiento y registro.

## Capturas recomendadas

1. `azure-01-microproyecto3.png`: Portal → grupo MICROPROYECTO3; mostrar nombres, tipos y región de recursos.
2. `azure-02-pipeline-completed.png`: Studio → Trabajos → nueva ejecución; mostrar nombre, estado y gráfico con sus tres etapas Completed.
3. `azure-03-modelo-registrado.png`: Studio → Modelos → reservaiq → versión 1; mostrar nombre, versión y vínculo al trabajo.
4. `azure-04-compute-cero.png`: Studio → Proceso → clúster; mostrar 0 nodos y límites 0–1.
5. `azure-05-datos-entrega.png`: Studio → Datos; mostrar dataset y activo de código/documentación con sus versiones.
6. `azure-06-demo-web.png`: aplicación web → Mis reservas; mostrar URL HTTPS y una reserva ficticia guardada.
7. `azure-07-costo-real.png`: Cost Management → Análisis de costos, ámbito suscripción, desde 30/09 hasta la fecha de consulta, filtro MICROPROYECTO3, agrupar por nombre de servicio. Mostrar período, total, moneda y servicios; si no hay datos, conservar ese estado y repetir después.

En **todas** las capturas revisar y ocultar ID de suscripción, tenant, correo y nombre de usuario; recortar el perfil y cualquier URL que los incluya. No capturar claves, tokens, SAS ni opciones para mostrarlos. Rotular las capturas de entrenamiento como **re-ejecución del 30/09/2026 Colombia (01/10 UTC)**; no atribuirlas al trabajo original `mango_wire_5f09pdg4m3`.

## Reproducción técnica

```sh
python -m pip install -r requirements-azure.txt
python -m unittest discover -s tests -v
npm ci
npm test
```

El modo local sigue iniciándose con `python iniciar.py`. El despliegue web requiere Python 3.12, HTTPS, `RESERVAIQ_STORAGE=azure_blob`, cuenta y contenedor, origen HTTPS exacto, `RESERVAIQ_ARTIFACTS_DIR=cloud-artifacts` y permiso de identidad en ese contenedor. Preparar el paquete sin credenciales ni reservas locales:

```sh
python scripts/pack_azure_web.py --artifacts-dir cloud-artifacts --output deploy.zip
```

El paquete expande las dependencias de nube en `requirements.txt`; habilitar `SCM_DO_BUILD_DURING_DEPLOYMENT=true` para que Azure las instale. Inicio del servidor:

```sh
gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:8000 cloud_wsgi:application
```

Los resultados de pruebas de transporte en memoria no reemplazan la comprobación real de guardado en Azure. La evidencia de despliegue distingue ambos tipos de verificación.

Referencias oficiales: [Python en App Service](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python), [planes de alojamiento](https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans), [restricciones de almacenamiento montado y SQLite](https://learn.microsoft.com/en-us/azure/app-service/configure-connect-to-azure-storage), [análisis de costos](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/customize-cost-analysis-views), [API pública de precios](https://prices.azure.com/api/retail/prices).

## Comprobación de la publicación

La verificación separa 67 pruebas locales (41 Python y 26 de interfaz/datos), comprobaciones reales por HTTPS y persistencia tras reiniciar App Service. Los resultados están en [web-verification.json](../azure/evidence/microproyecto3/web-verification.json). El [pipeline ejecutado](../azure/evidence/microproyecto3/pipeline.yml) referencia los activos registrados en este workspace; su nombre identifica una ejecución ya realizada y no debe reutilizarse para crear un trabajo distinto.
