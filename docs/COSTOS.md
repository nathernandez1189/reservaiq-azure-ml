# Costos y control de consumo

Se propone un clúster CPU **Standard_DS2_v2** con mínimo 0, máximo 1 nodo y liberación después de 120 segundos inactivo. Es suficiente para este experimento tabular y reduce la tarifa frente al tamaño DS3 v2 de la primera estimación. La aplicación usa el modelo descargado y no mantiene un endpoint en línea.

## Escenario mínimo de una ejecución

| Concepto | Supuesto | USD |
| --- | --- | ---: |
| CPU DS2 v2 | 1 hora × 0,146 | 0,146 |
| Recursos auxiliares | Reserva supuesta para una práctica breve | 0,500 |
| Margen | Imprevistos dentro del escenario | 0,354 |
| **Total presupuestado** | **Escenario de 1 hora CPU** | **1,000** |

Tarifa pública consultada el 25/09/2026 UTC: Linux, East US, consumo bajo demanda, 0,146 USD/h. La respuesta de la API se conserva en `artifacts/azure-price-reference.json`. El total es una estimación, no una factura ni un tope automático. La región, cuota y tarifa efectiva deben verificarse antes de crear cómputo.

La reserva auxiliar de 0,50 USD es un supuesto, no una cotización desglosada de Storage, Key Vault, Container Registry o Application Insights. Mantener esos recursos durante más tiempo puede superar el escenario. El clúster en cero nodos no elimina todos los cargos.

## Controles

- Un solo nodo CPU; sin GPU ni endpoint permanente.
- Límites por etapa: 15 minutos para preparación, 30 para entrenamiento y 15 para evaluación. El máximo de las etapas no incluye toda la espera, creación de imagen ni aprovisionamiento.
- Descargar y verificar resultados antes de liberar infraestructura.
- Comprobar el número de nodos después del trabajo y consultar Cost Management con fecha.
- Las alertas de presupuesto avisan; no bloquean automáticamente el gasto.

## Estado de facturación

No hay una ejecución de Azure ML registrada en las evidencias de esta revisión. No se presenta un costo real consolidado. El registro del proveedor y la instalación de la extensión son preparación, no entrenamiento ni consumo de un nodo.

Fuentes: [tarifas de Azure ML](https://azure.microsoft.com/en-us/pricing/details/machine-learning/), [API de precios](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), [gestión de costos](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-optimize-cost?view=azureml-api-2).
