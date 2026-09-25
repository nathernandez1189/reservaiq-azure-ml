# Ficha del modelo

| Campo | Descripción |
| --- | --- |
| Uso | Priorizar revisión humana de reservas |
| Cliente | Hotel Brisa del Valle, ficticio, Cali |
| Fuente | Dos hoteles portugueses, llegadas 2015–2017 |
| Objetivo | `is_canceled`, convertido a `target` |
| Modelo seleccionado | HistGradientBoostingClassifier de scikit-learn |
| Selección | Mayor average precision en validación |
| Umbral | 0,17 por máximo F1 en validación |
| Entradas | Diez campos definidos en `core.py` |
| Alcance | 0–60 días de anticipación; 1–30 noches; categorías conocidas |
| Salida | Índice del clasificador y alerta, no probabilidad calibrada |
| Acción | Prioridad para revisión; no decisiones automáticas sobre huéspedes |

## Evaluación reservada

| Resultado real | Con alerta | Sin alerta |
| --- | ---: | ---: |
| Canceló | 1.467 | 364 |
| No canceló | 2.715 | 3.444 |

AP: 0,4134. ROC AUC: 0,7307. F1: 0,4879. Brier: 0,1560. Al umbral de 0,17 se detecta 80,1 % de cancelaciones y la precisión es 35,1 %. El total de alertas es 4.182, por eso la lista de tamaño K resulta operativamente distinta.

La importancia por permutación se calcula sobre 2.500 registros de validación, tres repeticiones y semilla 42. No explica causalmente cada predicción. El intervalo Wilson de detección supone observaciones independientes y no corrige dependencia entre reservas.

## Límites y validación futura

La fecha de creación es aproximada y los campos no tienen versiones históricas. Puede permanecer fuga temporal residual. No se dispone de identificador de huésped para separar recurrencia y grupos. La deduplicación exacta también puede quitar reservas legítimas indistinguibles.

La población, país y período son limitados. Para utilizarlo con el cliente se necesitan datos locales, una auditoría de disponibilidad de variables en el momento de decisión, evaluación por hotel y período y seguimiento de cambios en la distribución. Medir beneficios requiere un experimento de intervención, no solo métricas predictivas.

La aplicación restringe el contrato de entrada. No debe utilizarse para negar alojamiento, cobrar penalidades o atribuir intención a personas. Los datos de entrada no incluyen identidad, nacionalidad ni contactos.
