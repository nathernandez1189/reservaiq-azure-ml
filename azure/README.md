# Pipeline de Azure Machine Learning

Tres componentes CLI v2 ejecutan el mismo código del experimento: preparación, entrenamiento y evaluación. `pipeline.yml` define sus dependencias y salidas. El diseño usa un nodo CPU DS2 v2 como máximo y escala a cero; no necesita un endpoint de inferencia permanente.

Esta revisión contiene la configuración y validación local. El estado de una ejecución remota debe comprobarse con el trabajo y sus artefactos. [Costos y supuestos](../docs/COSTOS.md).

## 1. Requisitos y comprobación de cuenta

```bash
az account show --query '{subscription:name,state:state}' -o table
az extension add --name ml --yes
az provider show --namespace Microsoft.MachineLearningServices --query registrationState -o tsv
```

Si el proveedor no está registrado:

```bash
az provider register --namespace Microsoft.MachineLearningServices --wait
```

Verifica la cuenta, permisos, región y presupuesto antes de continuar. El registro del proveedor no crea un nodo. No publiques tokens, archivos `.azure` ni identificadores personales.

## 2. Workspace y cómputo

Estos comandos crean recursos potencialmente facturables. Usa un grupo separado del resto de prácticas y revisa su contenido antes de modificarlo:

```bash
az group create --name rg-reservaiq --location northcentralus
az ml workspace create --file azure/workspace.yml --resource-group rg-reservaiq
az ml compute list-usage --location northcentralus --resource-group rg-reservaiq --workspace-name ml-reservaiq -o table
az ml compute create --file azure/compute.yml --resource-group rg-reservaiq --workspace-name ml-reservaiq
```

No continúes si falta cuota, la región no está permitida o el costo previsto supera el presupuesto de la práctica. El workspace crea recursos asociados; documenta sus nombres y el digest del entorno resuelto. La imagen base usa una etiqueta mutable y el digest es necesario para identificar exactamente la imagen ejecutada.

### Acceso a datos mediante identidad

El workspace usa `system_datastores_auth_mode: identity` y el clúster declara una identidad administrada. Ser propietario de la suscripción no concede por sí mismo acceso al contenido de Blob Storage. Se necesita `Storage Blob Data Contributor` para cargar entradas y guardar o descargar resultados. Limita las asignaciones a la cuenta de almacenamiento de esta práctica.

```bash
RESERVAIQ_STORAGE=$(az ml workspace show -g rg-reservaiq -n ml-reservaiq --query storage_account -o tsv)
RESERVAIQ_USER=$(az ad signed-in-user show --query id -o tsv)
RESERVAIQ_WORKSPACE=$(az ml workspace show -g rg-reservaiq -n ml-reservaiq --query identity.principal_id -o tsv)
RESERVAIQ_COMPUTE=$(az ml compute show -g rg-reservaiq -w ml-reservaiq -n reservaiq-cpu --query identity.principal_id -o tsv)
az role assignment create --assignee-object-id "$RESERVAIQ_USER" --assignee-principal-type User --role "Storage Blob Data Contributor" --scope "$RESERVAIQ_STORAGE"
az role assignment create --assignee-object-id "$RESERVAIQ_WORKSPACE" --assignee-principal-type ServicePrincipal --role "Storage Blob Data Contributor" --scope "$RESERVAIQ_STORAGE"
az role assignment create --assignee-object-id "$RESERVAIQ_COMPUTE" --assignee-principal-type ServicePrincipal --role "Storage Blob Data Contributor" --scope "$RESERVAIQ_STORAGE"
az ml workspace update -g rg-reservaiq -n ml-reservaiq --image-build-compute reservaiq-cpu
```

Las asignaciones pueden tardar en propagarse. Verifica el acceso antes de reenviar un trabajo y consulta la lista para evitar ejecuciones duplicadas. La construcción del entorno usa el mismo clúster limitado a un nodo. No se publican identidades ni credenciales. [Autenticación entre servicios](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-identity-based-service-authentication?view=azureml-api-2).

## 3. Trabajo y salidas

Desde la raíz del repositorio:

```bash
az ml job create --file azure/pipeline.yml --resource-group rg-reservaiq --workspace-name ml-reservaiq --query name -o tsv
```

Guarda el nombre del trabajo devuelto en `RESERVAIQ_JOB`. Comprueba y descarga:

```bash
az ml job show --name "$RESERVAIQ_JOB" --resource-group rg-reservaiq --workspace-name ml-reservaiq --query '{name:name,status:status}'
az ml job stream --name "$RESERVAIQ_JOB" --resource-group rg-reservaiq --workspace-name ml-reservaiq
az ml job download --name "$RESERVAIQ_JOB" --all --download-path azure/evidence-private --resource-group rg-reservaiq --workspace-name ml-reservaiq
```

Se espera `Completed` y salidas `trained` y `report`. Verifica modelo, predicciones y métricas. La API pública de la aplicación debe reflejar el origen del artefacto que realmente está cargado.

## 4. Registro y descarga para inferencia

```bash
az ml model create --name reservaiq --type custom_model --path "azureml://jobs/$RESERVAIQ_JOB/outputs/trained/paths/model.joblib" --resource-group rg-reservaiq --workspace-name ml-reservaiq
```

Conserva el número de versión. Guarda una copia del modelo local, verifica la procedencia del modelo descargado y compara predicciones antes de sustituir los artefactos de la aplicación. `artifacts/runtime.json` debe registrar trabajo, estado Completed, versión y SHA256. Nunca cambies solo la etiqueta de la interfaz para afirmar ejecución en nube.

## 5. Cierre y verificación del consumo

```bash
az ml compute show --name reservaiq-cpu --resource-group rg-reservaiq --workspace-name ml-reservaiq
```

Comprueba el recuento de nodos y espera su liberación. Conserva las salidas antes de eliminar recursos. Consulta Cost Management con fecha; los cargos pueden aparecer con retraso. Cero nodos no implica cero cargos de almacenamiento o registro de contenedores.

Fuentes: [componentes CLI v2](https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-component-command?view=azureml-api-2), [clústeres](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-attach-compute-cluster?view=azureml-api-2), [control de costos](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-optimize-cost?view=azureml-api-2).
