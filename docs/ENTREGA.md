# Entrega académica de ReservaIQ

Microproyecto 3 · Computación en la Nube · Prof. Oscar Mondragón.

**Integrantes:** Juan Ospina Tenorio, Natalia Hernández Piedrahita y Miguel Ángel Diuza.

La vista **Diseño y Azure** de la aplicación contiene una correspondencia con los cuatro criterios, accesos a evidencias, alternativas y una lectura del flujo paso a paso. **Cómo probarlo** guía la demostración.

## Material para la revisión

- [Informe técnico en PDF](ReservaIQ-Informe-tecnico.pdf): análisis, alternativas, diseño, implementación, resultados, costos, fuentes y capturas comentadas.
- [Presentación ampliada en Canva](https://www.canva.com/d/20i32hmvo0gpTiA): 12 diapositivas para una exposición de 15 minutos.
- [Contenido de las 12 diapositivas](PRESENTACION.md): copia de consulta dentro del repositorio, disponible sin una cuenta de Canva.
- [Guía de uso y guardado local](GUIA-DE-USO.md) y [pruebas guiadas](PRUEBAS-GUIADAS.md).
- [Instrucciones para ejecutar la demo](../README.md#ejecutar-la-aplicación) y [CSV listo para cargar](../ejemplos-csv/reservas-listas.csv).
- [Evidencias de ejecución y verificación](EVIDENCIAS.md), [capturas comentadas](CAPTURAS.md) y [ejecución en Azure](../azure/evidence/run.json).

El enlace de Canva proporcionado por la integración solicitó iniciar sesión en la comprobación del 29/09/2026. No se ha confirmado acceso anónimo al diseño. La copia de contenido permite revisar la presentación desde GitHub; conserva la información, tablas y flujo, pero no reproduce la maquetación gráfica de Canva.

## Correspondencia con los criterios del profesor

Esta tabla se basa en las instrucciones del microproyecto facilitadas por el curso. Indica dónde está la evidencia; no constituye una calificación.

| Criterio | Peso | Qué se pide | Cómo lo desarrolla ReservaIQ | Dónde revisarlo |
| --- | ---: | --- | --- | --- |
| Análisis de requerimientos | 20 % | Empresa, necesidades, requerimientos y restricciones; alternativas; pipeline, componentes o algoritmos; costos aproximados | Hotel ficticio Brisa del Valle; priorización por capacidad K; contrato de diez variables; comparación de reglas, clasificación y AutoML; evaluación de cuatro candidatos; escenario de US$1 con supuestos | [Informe](Informe-tecnico.md), [modelo y datos](MODELO.md), [costos](COSTOS.md); diapositivas 2–4 y 6–8 |
| Propuesta de diseño | 25 % | Diagrama, relación y flujo entre componentes, descripción | Datos y Blob, componentes de preparación/entrenamiento/evaluación en Azure ML, modelo versionado y aplicación local con revisión humana | [Arquitectura](ARQUITECTURA.md), [pipeline](../azure/pipeline.yml), [preparación](../azure/prepare.yml), [entrenamiento](../azure/train.yml) y [evaluación](../azure/evaluate.yml); diapositivas 5 y 8 |
| Implementación del demo | 30 % | Implementar la solución diseñada | Inferencia individual, guardado local, estados de revisión, priorización por K, procesamiento de CSV y exportación; modelo entrenado en Azure, descargado y comprobado; demostración de aciertos y errores | [Aplicación e instrucciones](../README.md), [modelo](../artifacts/), [pruebas](../tests/), [registros Azure](../azure/evidence/); diapositivas 9–11 |
| Presentación de la solución | 25 % | Exposición de 15 minutos que explique requerimientos, diseño y demo | Presentación ampliada de 12 diapositivas; distribución objetivo de cinco minutos por integrante, con demo dentro del último bloque | [Canva](https://www.canva.com/d/20i32hmvo0gpTiA) y [contenido consultable](PRESENTACION.md) |

El material cubre los temas solicitados. El criterio de presentación también requiere realizar la exposición y mostrar la demo: disponer del archivo no demuestra que esa actividad ya se haya cumplido.

## Alcance de la evidencia

- El pipeline y sus tres componentes terminaron en **Completed**. Se descargó el modelo registrado `reservaiq:1` y se comprobó la coincidencia de 7.990 predicciones con los resultados locales.
- Las capturas documentan una sesión local. Los registros de Azure acreditan por separado la ejecución en la nube.
- **US$1 es un escenario estimado**, no una factura. La consulta de facturación del 25/09/2026 no tenía cargos consolidados. La rúbrica solicita costos aproximados.
- El cierre de los recursos temporales quedó verificado. La aplicación se evalúa con el modelo descargado; abrirla no requiere reconstruir Azure.
- Los resultados son retrospectivos sobre datos de Portugal. No prueban cancelaciones evitadas, ingresos recuperados ni validez operativa en Colombia.

## Repositorio, ZIP y formato de entrega

Las instrucciones facilitadas enumeran el contenido del trabajo y la presentación de 15 minutos. **No especifican expresamente que deba entregarse un ZIP, un PDF o un enlace de GitHub como único formato.** Los campos de la actividad en el campus pueden establecer condiciones adicionales. El informe se conserva como soporte organizado del análisis y el diseño; no se presenta como un archivo independiente obligatorio en las instrucciones facilitadas.

El repositorio centraliza el informe, la referencia a Canva, la copia consultable de las diapositivas, el código, el modelo, los CSV y las evidencias. El ZIP para el profesor es una copia de los archivos versionados en la misma revisión. No incorpora entregables técnicos exclusivos.

| Aspecto | Repositorio en GitHub | ZIP de la misma revisión |
| --- | --- | --- |
| Código, datos, modelo, informe, capturas y documentación | Incluidos | Los mismos archivos |
| Enlace a Canva y contenido consultable de las diapositivas | Incluidos | Incluidos |
| Diseño editable alojado en Canva | Se abre mediante enlace; requiere permisos de Canva | No está incrustado; se abre mediante el mismo enlace |
| Historial de commits y ejecuciones de GitHub Actions | Consultables en GitHub | No incluye la carpeta `.git` ni la interfaz de Actions |
| Actualizaciones posteriores | Pueden publicarse en nuevas revisiones | Es una copia fija |

Para entregar, utiliza el repositorio como punto de entrada si la actividad admite enlaces. Si exige un archivo, adjunta el ZIP de esa misma revisión y agrega el enlace cuando el formulario lo permita. No es necesario adjuntar duplicados salvo que el campus o el profesor los solicite.

La publicación en GitHub, la disponibilidad del ZIP y la edición de Canva **no equivalen a una entrega formal en el campus**.
