# Costos y control de consumo

Se utilizó un clúster CPU **Standard_DS2_v2** con mínimo 0, máximo 1 nodo y liberación después de 120 segundos inactivo. El tamaño permite ejecutar este experimento tabular con CPU. La aplicación usa el modelo descargado y no mantiene un endpoint en línea.

## Escenario mínimo de una ejecución

| Concepto | Supuesto | USD |
| --- | --- | ---: |
| CPU DS2 v2 | 1 hora × 0,146 | 0,146 |
| Recursos auxiliares | Reserva supuesta para una práctica breve | 0,500 |
| Margen | Imprevistos dentro del escenario | 0,354 |
| **Total presupuestado** | **Escenario de 1 hora CPU** | **1,000** |

Tarifa pública consultada el 25/09/2026 UTC: Linux, North Central US, consumo bajo demanda, 0,146 USD/h. La respuesta de la API se conserva en `artifacts/azure-price-reference.json`. El total es una estimación, no una factura ni un tope automático. La región, cuota y tarifa efectiva deben verificarse antes de crear cómputo.

La reserva auxiliar de 0,50 USD es un supuesto, no una cotización desglosada de Storage, Key Vault, Container Registry o Application Insights. Mantener esos recursos durante más tiempo puede superar el escenario. El clúster en cero nodos no elimina todos los cargos.

## Controles

- Un solo nodo CPU; sin GPU ni endpoint permanente.
- Límites por etapa: 15 minutos para preparación, 30 para entrenamiento y 15 para evaluación. El máximo de las etapas no incluye toda la espera, creación de imagen ni aprovisionamiento.
- Descargar y verificar resultados antes de liberar infraestructura.
- Comprobar el número de nodos después del trabajo y consultar Cost Management con fecha.
- Las alertas de presupuesto avisan; no bloquean automáticamente el gasto.

## Estado de facturación

El pipeline `mango_wire_5f09pdg4m3` y sus tres etapas terminaron en estado Completed. La imagen se construyó en el mismo clúster. Se conservaron diez salidas y se verificó la versión registrada antes de solicitar el cierre del grupo temporal.

El límite operativo autorizado fue **US$3**. El presupuesto de **US$1** de la tabla es un escenario conservador para una práctica breve; no es una factura. La consulta de Cost Management del 25/09/2026 UTC no devolvió filas para `rg-reservaiq`. Esto significa que no había cargos consolidados en esa consulta, no que la ejecución fuera gratuita. El resultado fechado está en `azure/evidence/billing.json`.

El cierre y la comprobación del grupo se conservan en `azure/evidence/closure.json`. Los estados y el modelo son evidencia histórica; para otro entrenamiento se deben recrear los recursos y revisar tarifa, cuota y presupuesto.

Fuentes: [tarifas de Azure ML](https://azure.microsoft.com/en-us/pricing/details/machine-learning/), [API de precios](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), [gestión de costos](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-optimize-cost?view=azureml-api-2).

## Cierre verificado

El 25/09/2026 UTC se confirmó `az group exists --name rg-reservaiq` → `false`. Se eliminaron el workspace, el clúster y sus recursos asociados después de conservar modelo, resultados y registros. No queda un endpoint ni un clúster de esta práctica en ejecución. Las copias incluidas permiten evaluar la demo sin Azure; la factura puede reflejar cargos anteriores con retraso.
