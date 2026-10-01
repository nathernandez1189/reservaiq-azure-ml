# Costos y control de consumo

Consulta de Cost Management del **1 de octubre de 2026, 03:20 UTC** (30 de septiembre, 22:20 en Colombia). Período consultado: 24 de septiembre al 1 de octubre. Cada ejecución se informa por separado.

## Consumo registrado y estimación

| Ejecución | Grupo | Consumo registrado antes de impuestos | Situación |
| --- | --- | ---: | --- |
| Original del 25 de septiembre UTC | `rg-reservaiq` | **US$0,0620879781** | Consumo reportado; grupo eliminado |
| Nueva del 1 de octubre UTC | `MICROPROYECTO3` | **Sin datos todavía** | La consulta devolvió cero filas, no costo cero |

El primer valor equivale aproximadamente a **6,21 centavos de dólar**. Es consumo registrado antes de impuestos, no una factura final ni un pago en efectivo: los créditos educativos pueden cubrir el consumo. La ausencia de filas de la segunda ejecución no permite informar un total real todavía.

## Desglose real de la ejecución original

| Servicio | USD antes de impuestos |
| --- | ---: |
| Virtual Machines | 0,0462341120 |
| Storage | 0,0085738500 |
| Virtual Network | 0,0039041667 |
| Container Registry | 0,0032918494 |
| Key Vault | 0,0000840000 |
| Load Balancer | 0,0000000000 |
| **Total** | **0,0620879781** |

Respuestas fechadas, sin identificadores de cuenta: [original](../azure/evidence/microproyecto3/cost-original-20261001.json) y [MICROPROYECTO3](../azure/evidence/microproyecto3/cost-microproyecto3-20261001.json). La consulta antigua de [billing.json](../azure/evidence/billing.json) conserva el estado sin cargos observado el 25 de septiembre y no se sobrescribe.

## Presupuesto de conservación de MICROPROYECTO3

Disponibilidad autorizada hasta el **5 de octubre de 2026 inclusive, hora de Colombia**, con límite autorizado de **US$3**. El escenario orientativo actual es **US$2**, separado del consumo real todavía no reportado.

| Concepto | Supuesto del escenario | USD aproximados |
| --- | --- | ---: |
| CPU Standard_DS2_v2 | Hasta 1 hora a US$0,146 por hora de nodo | 0,1460 |
| Container Registry Basic | 6 días a US$0,1666 por día | 0,9996 |
| App Service F1 | Nivel gratuito, sujeto a sus cuotas | 0,0000 |
| Storage, operaciones, Key Vault y margen | Reserva presupuestaria, no cotización ni medición | 0,8544 |
| **Total estimado** | **Conservación temporal del proyecto** | **2,0000** |

Las tarifas públicas consultadas son para North Central US. El cargo efectivo depende de duración, uso y contrato. El clúster tiene mínimo 0, máximo 1 nodo y liberación tras 120 segundos de inactividad. Se verificaron cero nodos tras la ejecución. La aplicación sirve el modelo desde App Service y no requiere un endpoint de inferencia de Azure ML. Cero nodos no elimina los cargos de los servicios conservados.

El escenario original de US$1 contemplaba una práctica breve y cierre inmediato: CPU 0,146 + auxiliares supuestos 0,500 + margen 0,354. Se conserva como antecedente, no como presupuesto de varios días.

## Control y comprobación

- Consultar Cost Management con ámbito de suscripción, período personalizado y filtro de grupo exacto. Agrupar por nombre de servicio.
- Conservar el presupuesto US$3. Las alertas y la revisión programada no son un bloqueo automático de cargos.
- Mantener el plan F1 y el clúster en cero nodos mientras no se entrena. No volver a ejecutar el pipeline para abrir la demo.
- Antes del cierre, respaldar modelo, informes y reservas ficticias, comprobar sus huellas y eliminar solo el grupo del proyecto después del plazo autorizado.
- F1 puede dormirse, comparte recursos y no ofrece SLA. No se ha contratado capacidad de producción.

Azure incorpora cargos con retraso; no es posible forzar su aparición. Los costos pueden ajustarse antes de cerrar la factura. [Actualización de costos y uso de Microsoft](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-cost-mgt-data#cost-and-usage-data-updates-and-retention).

Fuentes: [precios de Azure ML](https://azure.microsoft.com/en-us/pricing/details/machine-learning/), [API de precios](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), [control de costos](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-optimize-cost?view=azureml-api-2).
