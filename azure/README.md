# Pipeline de Azure Machine Learning

Tres componentes CLI v2 ejecutan el mismo código del experimento: preparación, entrenamiento y evaluación. `pipeline.yml` define sus dependencias y salidas. El diseño usa un nodo CPU DS2 v2 como máximo y escala a cero; no necesita un endpoint de inferencia permanente.

La ejecución `mango_wire_5f09pdg4m3` completó las tres etapas y produjo el modelo registrado `reservaiq:1`. Las salidas verificadas están incluidas en el repositorio; el grupo de infraestructura es temporal. [Evidencias](../docs/EVIDENCIAS.md) · [Costos y supuestos](../docs/COSTOS.md).

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

No continúes si falta cuota, la región no está permitida o el costo previsto supera el presupuesto de la práctica. El workspace crea recursos asociados; documenta sus nombres y el digest del entorno resuelto. `environment-lock.json` conserva el digest de la imagen base y de la imagen construida. La primera ejecución resolvió `latest`; para reconstruir con la misma base se puede usar `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04@sha256:7481fbfbbc1c7d7ab0e9e4633180c809413bd77e108b605d6e4d3a60aa35bf67`. El archivo también registra los paquetes y Python observados.

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

## 6. Salidas y eliminación del grupo temporal

Las salidas de los pasos se almacenan en el datastore de Blob Storage, separadas de los registros. `job download --all` puede descargar solo registros para un paso del pipeline. Comprueba explícitamente la presencia de `model.joblib`, `selection.json`, las predicciones, el manifiesto y las particiones. En Blob Storage, ignora marcadores de carpeta de cero bytes al descargar: una carpeta como `trained` no es un archivo de modelo.

Después de verificar las diez salidas, descargar la versión registrada y comparar sus huellas, comprueba que el grupo contiene exclusivamente recursos de esta práctica. El siguiente comando elimina ese grupo completo, incluidas sus copias remotas; debe ejecutarse solo después de conservar los artefactos necesarios:

```bash
az resource list --resource-group rg-reservaiq -o table
az group delete --name rg-reservaiq --yes --no-wait
az group exists --name rg-reservaiq
```

Un resultado `false` confirma que el grupo ya no existe. Conserva esa comprobación con fecha. El modelo incluido permite seguir ejecutando la aplicación sin mantener el workspace o el registro de contenedores. La facturación se consolida con retraso y se consulta por separado.
