# Evidencias del microproyecto

Las evidencias enlazan resultados con archivos verificables. Las métricas corresponden a una ejecución local; la configuración de Azure se documenta por separado hasta disponer de un trabajo completado y sus artefactos.

| Evidencia | Archivo | Qué demuestra |
| --- | --- | --- |
| Fuente y huella | `data/source.json` | Procedencia del CSV y comprobación de integridad |
| Manifiesto | `artifacts/splits/data_manifest.json` | Alcance, exclusiones, fechas y tamaños |
| Comparación | `artifacts/trained/selection.json` | Selección de modelo y umbral en validación |
| Modelo serializado | `artifacts/trained/model.joblib` | Artefacto utilizado para inferencia |
| Prueba reservada | `artifacts/test_predictions.csv` | Cada predicción y desenlace usados en métricas |
| Resultados | `artifacts/summary.json` | Métricas, casos, matriz e importancia |
| Comprobación local | `docs/verificacion.json` | Resultado y alcance de las pruebas |
| Ejecución automática | GitHub Actions | Resultado de la ejecución correspondiente al commit |
| CSV de carga | `ejemplos-csv/reservas-listas.csv` | Ocho registros con el contrato exacto |

## Reproducir las comprobaciones

```bash
python -m unittest discover -s tests -v
```

Las pruebas comprueban catorce aspectos del modelo, datos y API. Incluyen el CSV entregado y la concordancia entre resultados individuales y por lote. La prueba de procedencia exige trabajo Completed y SHA256 coincidente antes de afirmar un modelo de Azure.

## Revisión de interfaz y capturas

En esta revisión no se pudieron obtener capturas reales porque la herramienta de navegador no pudo verificar su política de seguridad. No se sustituyen por imágenes que aparenten una ejecución. Las pruebas del servidor no prueban la navegación visual del cliente.

Para completar esa evidencia deben comprobarse las cuatro vistas, la inferencia, la carga del CSV y las descargas en un navegador. Las capturas deben mostrar el estado real, acompañarse de fecha y de una explicación de qué verifican. No deben incluir identificadores de suscripción, credenciales ni información privada.

## Evidencia de Azure

La aceptación de la ejecución requiere: workspace y región, trabajo Completed con sus tres etapas, entorno resuelto, salidas descargadas, modelo registrado, SHA256 de la copia usada en la aplicación y estado final de los nodos. Un archivo YAML válido no demuestra que el trabajo se haya ejecutado.
