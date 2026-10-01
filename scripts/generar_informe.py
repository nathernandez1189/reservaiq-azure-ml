"""Informe técnico generado desde los artefactos verificados."""
from pathlib import Path
import json,html,re,hashlib,datetime,sys
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Flowable,Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics import renderPDF
from diagrama_arquitectura import architecture, WIDTH, HEIGHT

ROOT=Path(__file__).resolve().parents[1];PROJ=ROOT;OUT=ROOT/'docs';OUT.mkdir(parents=True,exist_ok=True)
S=json.loads((PROJ/'artifacts/summary.json').read_text(encoding='utf-8'));M=S['test'];D=S['data'];V=S['selection']
R=json.loads((PROJ/'artifacts/runtime.json').read_text(encoding='utf-8'));AZURE=R.get('origin')=='azure_ml' and R.get('job_status')=='Completed' and R.get('model_sha256')==hashlib.sha256((PROJ/'artifacts/trained/model.joblib').read_bytes()).hexdigest()
if Path('/System/Library/Fonts/Supplemental/Arial.ttf').exists():
 pdfmetrics.registerFont(TTFont('Arial','/System/Library/Fonts/Supplemental/Arial.ttf'))
 pdfmetrics.registerFont(TTFont('ArialBold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
else:
 pdfmetrics.registerFont(pdfmetrics.Font('Arial','Helvetica','WinAnsiEncoding'))
 pdfmetrics.registerFont(pdfmetrics.Font('ArialBold','Helvetica-Bold','WinAnsiEncoding'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
C=colors.HexColor;navy=C('#102631');teal=C('#087e80');ink=C('#17252d');muted=C('#546772');pale=C('#eaf3f3')
styles={
 'title':ParagraphStyle('title',fontName='ArialBold',fontSize=27,leading=32,textColor=ink,spaceAfter=16),
 'subtitle':ParagraphStyle('subtitle',fontName='Arial',fontSize=14,leading=20,textColor=muted,spaceAfter=18),
 'h2':ParagraphStyle('h2',fontName='ArialBold',fontSize=13,leading=18,textColor=ink,spaceBefore=15,spaceAfter=7),
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10.2,leading=15,textColor=ink,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=8.7,leading=12.5,textColor=muted,spaceAfter=7),
 'cell':ParagraphStyle('cell',fontName='Arial',fontSize=9.1,leading=12.5,textColor=ink),
 'head':ParagraphStyle('head',fontName='ArialBold',fontSize=9.1,leading=12.5,textColor=colors.white),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=8.5,leading=12,textColor=ink,spaceBefore=7,spaceAfter=10)}
story=[];md=[]
def markdown(t):
 t=re.sub(r'<br\s*/?>','\n',t)
 t=re.sub(r'<link href="([^"]+)"[^>]*>(.*?)</link>',r'[\2](\1)',t)
 t=t.replace('<b>','**').replace('</b>','**')
 return html.unescape(re.sub('<[^>]+>','',t))
def p(t,style='body'):
 story.append(Paragraph(t,styles[style]));md.append(markdown(t)+'\n')
def title(t):p(t,'title');md[-1]='# '+md[-1]
def h(t):p(t,'h2');md[-1]='## '+md[-1]
def table(rows,widths):
 formatted=[[Paragraph(str(v),styles['head' if i==0 else 'cell']) for v in row] for i,row in enumerate(rows)]
 t=Table(formatted,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,pale]),('GRID',(0,0),(-1,-1),.4,C('#d4dfe1')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]));story.extend([t,Spacer(1,10)])
 md.append('\n'.join(['| '+' | '.join(markdown(str(v)).replace('\n','<br>') for v in rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |']+['| '+' | '.join(markdown(str(v)).replace('\n','<br>') for v in r)+' |' for r in rows[1:]])+'\n')
def page():story.append(PageBreak());md.append('\n---\n')
def pct(v):return f'{v*100:.1f} %'.replace('.',',')
def num(v):return f'{v:,}'.replace(',','.')
def code(t):
 p(html.escape(t).replace('\n','<br/>'),'code');md[-1]='```bash\n'+t+'\n```\n'

class Architecture(Flowable):
 def __init__(self):
  Flowable.__init__(self);self.width=480;self.height=HEIGHT*480/WIDTH
 def draw(self):
  diagram=architecture();diagram.scale(480/WIDTH,480/WIDTH)
  renderPDF.draw(diagram,self.canv,0,0)


title('ReservaIQ')
p('Priorización de reservas hoteleras con aprendizaje automático','subtitle')
p('Microproyecto 3 · Computación en la Nube · UAO<br/>Prof. Oscar Mondragón')
h('Equipo')
p('Juan Ospina Tenorio<br/>Natalia Hernández Piedrahita<br/>Miguel Ángel Diuza')
h('Problema de negocio')
p('Hotel Brisa del Valle es un cliente ficticio de Cali. Su equipo de reservas dispone de tiempo limitado para revisar confirmaciones. ReservaIQ ordena las reservas según un índice asociado a cancelación y selecciona una lista de tamaño K, ajustada a esa capacidad. El personal decide qué acciones realizar.')
table([['Resultado retrospectivo','Valor'],['Reservas de prueba',num(M['n'])],['Precisión del 20 % prioritario',pct(M['top20']['precision'])],['Cancelaciones capturadas en ese 20 %',pct(M['top20']['recall'])],['Concentración frente a selección aleatoria esperada',f"{M['top20']['lift']:.2f} veces"]],[365,115])
p('Los datos son reales e históricos, de dos hoteles de Portugal. No pertenecen al cliente ficticio. Estas métricas no prueban ahorros, cancelaciones evitadas ni generalización a Colombia.','small')
h('Estado de la evidencia')
p(f"Pipeline de Azure ML completado: {R['job_name']}. Modelo descargado, registrado y verificado en la aplicación; pruebas de datos, API y guardado local verificadas. Las evidencias conservan estados, huellas y comparación entre ejecuciones. El anexo incluye cuatro capturas aportadas por el equipo de una sesión con indicador de modelo local; la ejecución Azure se acredita mediante registros independientes." if AZURE else 'Entrenamiento, evaluación, inferencia y pruebas verificados localmente. Componentes de Azure ML configurados; ejecución remota por verificar.','small')

page();title('1. Requerimientos y alternativas')
p('La necesidad se traduce en una decisión verificable: qué reservas revisar primero cuando existe una capacidad K. La alerta por umbral es un análisis complementario y no obliga a contactar a todos los registros señalados.')
table([['ID','Requerimiento','Criterio de aceptación'],['R1','Analizar una reserva','Validar diez variables y devolver índice, decisión y versión.'],['R2','Priorizar revisión','Seleccionar exactamente K registros y exportar la lista.'],['R3','Analizar un lote','CSV con 1-500 filas, máximo 150 KB y el mismo contrato.'],['R4','Evaluar sin usar el futuro','Particiones temporales disjuntas y madurez de etiquetas.'],['R5','Comparar y explicar','Candidatos, métricas, matriz y ejemplos de aciertos y errores.'],['R6','Ejecutar en Azure ML','Tres componentes, trabajo Completed y artefactos verificables.'],['R7','Limitar consumo','CPU, mínimo cero, máximo un nodo y límites de duración.'],['R8','Conservar reservas locales','Guardar, recuperar y editar después de reiniciar; archivo reversible.']],[35,145,300])
h('Alternativas consideradas')
table([['Alternativa','Ventaja','Limitación'],['Reglas manuales','Simplicidad y explicación','Umbrales rígidos y mantenimiento manual.'],['Clasificador y lista','Comparación y prioridad medible','Necesita datos y seguimiento de errores.'],['AutoML','Exploración automatizada','Más ensayos y consumo variable.']],[130,160,190])
p('Se elige clasificación supervisada con revisión humana. No hay integración con un sistema hotelero productivo, envío de mensajes, modificación de reservas ni cobros automáticos.','small')

page();title('2. Datos, alcance y variables')
p('Antonio, Almeida y Nunes publicaron 119.390 reservas de dos hoteles portugueses con llegadas en 2015-2017. Se conserva la distribución de TidyTuesday y su huella SHA256. Licencia de los datos originales: CC BY 4.0. [1, 2]')
table([['Tratamiento','Registros'],['Archivo original','119.390'],['Alcance antes de deduplicar','55.053'],['Duplicados exactos retirados','7.603'],['Después de deduplicar','47.450'],['Incluidos en las tres particiones','35.387'],['Fuera de períodos o madurez','12.063']],[350,130])
h('Contrato de diez variables')
p('<b>Numéricas:</b> lead_time, arrival_month, stays_in_weekend_nights y stays_in_week_nights.<br/><b>Categóricas:</b> hotel, meal, market_segment, distribution_channel, reserved_room_type y customer_type.')
p('Se admiten reservas con 0-60 días de anticipación, 1-30 noches totales, mes 1-12 y categorías conocidas. El diccionario completo está en ejemplos-csv/LEEME.md. No se usan identificadores de huéspedes ni contactos.')
h('Exclusiones para reducir fuga de información')
p('Estado final, fecha de estado, habitación asignada y cambios pueden reflejar hechos posteriores. ADR y depósitos no garantizan disponibilidad al crear la reserva. Se excluyen también país e identificadores de agencia o empresa.')
h('Limitaciones del origen')
p('La fecha de creación se deriva de llegada menos anticipación. No hay versiones históricas de los campos. La deduplicación puede eliminar reservas legítimas indistinguibles y no se puede excluir toda dependencia entre huéspedes recurrentes o grupos. El alcance no representa todos los hoteles ni todos los horizontes de reserva.','small')

page();title('3. Método y selección')
table([['Partición','Creación de reserva','Resultado antes de','n / cancelaciones'],['Entrenamiento','Jul 2015-jun 2016','01/09/2016','21.236 / 3.933'],['Validación','Sep-nov 2016','01/02/2017','6.161 / 1.346'],['Prueba','Feb-may 2017','01/09/2017','7.990 / 1.831']],[95,130,125,130])
p('Los espacios entre períodos permiten que los desenlaces anteriores sean conocidos antes de la evaluación siguiente. Las particiones no se mezclan aleatoriamente. El manifiesto conserva los límites exactos y la prueba comprueba que no se comparten registros.')
h('Protocolo reproducible')
p('1. Fijar alcance, fechas y semilla 42.<br/>2. Ajustar escalado, codificación y modelos solo en entrenamiento.<br/>3. Elegir el mayor average precision en validación.<br/>4. Fijar umbral por máximo F1 en una cuadrícula de 0,05 a 0,95.<br/>5. Evaluar la prueba reservada y conservar todas las predicciones.')
table([['Modelo','AP validación','ROC AUC validación']]+[[x['name'],f"{x['average_precision']:.4f}",f"{x['roc_auc']:.4f}"] for x in V['candidates']],[260,110,110])
h('Modelo elegido')
p(f"{S['model']}, con umbral {S['threshold']:.2f}. La diferencia frente a regresión logística es modesta; no se afirma superioridad universal. Las configuraciones se limitan a una comparación manejable y no se ajustan usando la prueba.")
p('Se fijan versiones de Python y librerías. selection.json documenta candidatos, barrido de umbral, duración de entrenamiento y entorno. model.joblib conserva transformaciones y clasificador juntos para evitar diferencias entre preparación e inferencia.','small')

page();title('4. Arquitectura y flujo')
story.append(Architecture());story.append(Spacer(1,8))
md.append('![Flujo de datos y artefactos, con Azure y entorno local separados](figuras/arquitectura.svg)\n')
table([['Componente','Responsabilidad'],['Workspace y Blob','Organizar trabajos, conservar entradas y artefactos.'],['Clúster CPU DS2 v2','Ejecutar con mínimo 0, máximo 1 nodo e inactividad de 120 s.'],['Preparación','Aplicar alcance, deduplicación, fechas y particiones.'],['Entrenamiento','Comparar candidatos y fijar modelo y umbral.'],['Evaluación','Calcular métricas sobre prueba y exportar evidencia.'],['Registro y descarga','Versionar el modelo y comprobar su huella.'],['Aplicación local y SQLite','Inferencia, lotes, prioridad y guardado local de reservas.']],[155,325])
p('Preparación entrega entrenamiento y validación al componente de entrenamiento, y prueba al de evaluación. Entrenamiento produce el modelo; evaluación recibe ese modelo y produce métricas y predicciones. Las flechas representan datos y artefactos. [3]','small')
p('Registro y descarga son pasos posteriores al trabajo Completed, no componentes adicionales del pipeline. El registro pertenece a Azure; la aplicación usa los archivos descargados en el entorno local.','small')
p('Las copias nuevas se guardan en SQLite con resultado y estado de revisión. No se sincronizan entre equipos, no se envían a Azure y no cambian el entrenamiento ni las métricas históricas.','small')
p('El modelo descargado evita mantener un endpoint de inferencia. artifacts/runtime.json vincula la aplicación con trabajo, estado Completed, versión y SHA256. La etiqueta de origen Azure exige coincidencia con el archivo cargado. El estado histórico del trabajo y el cierre de recursos se documentan por separado.','small')

page();title('5. Resultados y decisión')
table([['Métrica de prueba','Resultado'],['Average precision',f"{M['average_precision']:.4f}"],['ROC AUC',f"{M['roc_auc']:.4f}"],[f"Detección al umbral {S['threshold']:.2f}",pct(M['recall'])],[f"Precisión al umbral {S['threshold']:.2f}",pct(M['precision'])],['F1',f"{M['f1']:.4f}"],['Brier del índice sin calibrar',f"{M['brier']:.4f}"]],[340,140])
table([['Desenlace real','Con alerta','Sin alerta'],['Canceló',num(M['tp']),num(M['fn'])],['No canceló',num(M['fp']),num(M['tn'])]],[240,120,120])
p(f"El umbral captura muchas cancelaciones y genera {num(M['fp'])} falsas alertas. El hotel no tiene que revisar automáticamente todas las alertas: puede definir K según su capacidad.")
h('Revisar el 20 % prioritario')
p(f"Se seleccionan {num(M['top20']['k'])} registros y {num(M['top20']['hits'])} cancelaron. La precisión es {pct(M['top20']['precision'])} y se captura {pct(M['top20']['recall'])} de las cancelaciones. Frente a la frecuencia base de {pct(M['positives']/M['n'])}, la concentración es {M['top20']['lift']:.2f} veces la esperada con selección aleatoria. Es una comparación retrospectiva, no un experimento de intervención.")
h('Explicación y límites')
p('La importancia por permutación utiliza 2.500 reservas de validación y tres repeticiones. Describe sensibilidad global, no causalidad individual. El intervalo Wilson de detección es aproximado y no corrige dependencia entre reservas. Los índices no son probabilidades calibradas.','small')

page();title('6. Implementación y comprobación')
p('El servidor local carga el modelo y escucha en 127.0.0.1. Las seis vistas son Inicio, Nueva reserva, Mis reservas, Cómo probarlo, Resultados del modelo y Diseño y Azure. El recorrido distingue analizar, guardar y revisar.')
table([['Ruta','Comportamiento'],['GET /api/summary','Métricas, ejemplos y procedencia comprobada.'],['GET /api/health','Estado del servicio, modelo y huella.'],['GET /api/sample.csv','Ocho reservas listas para cargar.'],['POST /api/predict','Una reserva validada: inferencia sin guardar.'],['POST /api/batch','Entre 1 y 500 reservas: inferencia sin guardar.'],['GET /api/reservations','Consultar las copias locales guardadas.'],['POST /api/reservations','Analizar y guardar una nueva reserva.'],['POST /api/reservations/batch','Guardar todo el lote o ninguna fila.'],['POST /api/reservations/update','Editar y recalcular con control de revisión.'],['POST /api/reservations/status','Revisar, archivar o restaurar.']],[195,285])
h('Iniciar y usar')
code('py -3.12 iniciar.py  # Windows\npython3.12 iniciar.py  # macOS / Linux')
p('Ejecutar únicamente la línea del sistema utilizado. El lanzador prepara el entorno y las dependencias. Abrir http://127.0.0.1:8765 y mantener la terminal abierta. En Nueva reserva, elegir llegada y salida en el calendario, completar Detalles y pasar a Revisar y guardar. Las noches y la anticipación se calculan automáticamente. Mis reservas permite recuperar el registro.','small')
p('El CSV se selecciona en Nueva reserva, se analiza y muestra una vista previa. Guardar lote conserva todas las filas; Descargar resultados genera el JSON. La guía y las pruebas paso a paso están en docs/GUIA-DE-USO.md y docs/PRUEBAS-GUIADAS.md.','small')

page();title('6.1. Calendario y guardado local')
h('Tres pasos con resumen de estancia')
p('Fechas, Detalles y Revisar y guardar separan las decisiones. El calendario calcula cuatro variables del modelo: anticipación, mes de llegada y noches entre semana/de fin de semana. La salida no cuenta como noche. El servidor valida la misma regla: 0 a 60 días de anticipación y 1 a 30 noches. Los ejemplos históricos sin fechas completas conservan sus variables originales.','small')
h('Qué se guarda y por qué')
p('SQLite conserva una copia local con referencia, diez variables, resultado, huella del modelo, fechas de creación/llegada/salida cuando se conocen y estado de revisión. La migración conserva los registros previos. El archivo .runtime/reservaiq.sqlite3 no se publica en GitHub; permite recuperar los registros tras reiniciar sin infraestructura de nube.')
p('Solo analizar no modifica la base. Guardar cambios mantiene el identificador y exige la revisión vigente para evitar sobrescrituras entre ventanas. Los reintentos de una misma creación devuelven el mismo registro. Un fallo en un lote revierte todas sus escrituras. Archivar es reversible.')
h('Comprobar el recorrido')
p('Con creación 01/10/2026, llegada 02/10 y salida 05/10 se obtienen 3 noches: 1 entre semana y 2 de fin de semana; anticipación de 1 día. Analizar y guardar conserva el registro con código RI-. Mis reservas permite recuperarlo, editarlo y organizarlo. Sus tarjetas Guardadas, Pendientes, Revisadas y Archivadas filtran los registros al pulsarlas. La guía incluye además el caso histórico 12301, el CSV y errores esperados.','small')
h('Comprobaciones automáticas y límites')
p('Las pruebas Python cubren integridad del dataset y modelo, separación temporal, métricas, las 7.990 predicciones, UTF-8 en Windows, API y persistencia real. Incluyen reiniciar el servidor, reintentos concurrentes sin duplicación, conflictos de edición y transacciones de lote. También se prueban fechas, cambio de año, año bisiesto y migración de la base. JavaScript verifica calendario, tarjetas de estado y recorrido guiado con una API simulada.')
code('python -m unittest discover -s tests -v\nnpm ci\nnpm test')
p('GitHub Actions ejecuta las comprobaciones en Windows y Linux. La evidencia fechada registra el resultado de cada suite. Las capturas del anexo documentan la interfaz anterior de cuatro vistas: no acreditan visualmente el guardado nuevo. La navegación de la nueva versión en un navegador real queda pendiente de comprobación cuando el control de acceso permita abrirlo.','small')
p('Las reservas nuevas no tienen una etiqueta real de cancelación conocida. No alimentan el entrenamiento ni alteran las métricas. Cada computador conserva su propia base. Para trasladarla, se cierra la aplicación y se copia .runtime. La exportación JSON permite consultar los datos, pero esta versión no incluye importación de esas copias.','small')

page();title('7. Costos, evidencia y conclusiones')
table([['Concepto','Supuesto','USD'],['CPU DS2 v2','1 hora × 0,146','0,146'],['Servicios auxiliares','Reserva supuesta de práctica breve','0,500'],['Margen','Imprevistos del escenario','0,354'],['Total presupuestado','Una ejecución acotada','1,000']],[145,255,80])
p('Referencia Linux North Central US consultada el 25/09/2026 UTC. La reserva auxiliar no es una cotización de todos los servicios y puede ser insuficiente si se conservan durante más tiempo. El total es un escenario, no factura ni bloqueo automático del gasto. La factura puede aparecer con retraso; el detalle fechado se conserva en docs/COSTOS.md. [4, 5]','small')
h('Controles y evidencia de aceptación')
p('Se usó un clúster de 0 a 1 nodos, con inactividad de 120 segundos y límites por etapa. Se descargaron diez salidas y se verificó la copia del modelo registrado. Después se eliminó el grupo temporal rg-reservaiq; Azure confirmó que ya no existe. Los cargos anteriores pueden consolidarse con retraso.')
p('La aceptación en Azure exige trabajo Completed, etapas, entorno resuelto, modelo registrado, salidas descargadas y huella coincidente con la aplicación. El repositorio conserva la configuración, las salidas del trabajo y su procedencia en docs/EVIDENCIAS.md. El cierre de recursos temporales evita mantener servicios de esta práctica después de descargar los resultados.')
h('Conclusión')
p('El experimento demuestra una priorización histórica con capacidad limitada y expone sus errores. Para utilizarlo en el hotel se requieren datos locales, auditoría de disponibilidad temporal de las variables y un experimento que mida el efecto de las acciones. La evidencia disponible no demuestra beneficios financieros.')
h('Fuentes')
for label,url in [('1. Antonio, Almeida y Nunes: datos hoteleros','https://doi.org/10.1016/j.dib.2018.11.126'),('2. TidyTuesday: CSV y diccionario','https://github.com/rfordatascience/tidytuesday/tree/main/data/2020/2020-02-11'),('3. Microsoft: componentes de Azure ML','https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-component-command?view=azureml-api-2'),('4. Microsoft: API de precios','https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices'),('5. Microsoft: control de costos','https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-optimize-cost?view=azureml-api-2')]:
 p(f'<link href="{html.escape(url,quote=True)}" color="#087e80">{label}</link>','small')


# Se incrustan los PNG originales completos: el estado visible nunca se retoca.
captures=json.loads((OUT/'capturas/manifest.json').read_text(encoding='utf-8'))
for item in captures['images']:
 page();title(item['pdf_title'])
 p('Captura aportada por el equipo · '+item['captured_at_from_filename']+' (según el nombre del archivo).','small')
 p('Captura de la interfaz anterior de cuatro vistas, sin guardado local. La sesión capturada muestra un indicador de modelo local. La ejecución en Azure se acredita por separado en los registros de evidencia.','small')
 image_path=OUT/'capturas'/item['file']
 if hashlib.sha256(image_path.read_bytes()).hexdigest()!=item['sha256']:
  raise ValueError('La captura no coincide con su manifiesto: '+item['file'])
 story.append(Image(str(image_path),width=480,height=480*item['height']/item['width']))
 story.append(Spacer(1,8))
 md.append('!['+item['title']+'](capturas/'+item['file']+')\n')
 p('<b>Qué se observa.</b> '+html.escape(item['observed']),'small')
 p('<b>Por qué importa.</b> '+html.escape(item['explanation']),'small')
 p('<b>Alcance.</b> '+html.escape(item['scope']),'small')
 url='https://github.com/nathernandez1189/reservaiq-azure-ml/blob/main/docs/capturas/'+item['file']
 p('<link href="'+url+'" color="#087e80">Abrir la captura original a resolución completa</link> · docs/CAPTURAS.md amplía la explicación.','small')

def footer(c,doc):
 c.saveState();w,height=doc.pagesize;c.setFont('ArialBold',9);c.setFillColor(teal);c.drawString(56,height-33,'RESERVAIQ')
 c.setFont('Arial',8);c.setFillColor(muted);c.drawRightString(w-56,height-33,'INFORME TÉCNICO  /  UAO');c.setStrokeColor(C('#d9e2e5'));c.line(56,42,w-56,42);c.drawString(56,27,'Microproyecto 3 · Computación en la Nube');c.drawRightString(w-56,27,str(doc.page));c.restoreState()
pdf=OUT/'ReservaIQ-Informe-tecnico.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),leftMargin=56,rightMargin=56,topMargin=60,bottomMargin=59,title='ReservaIQ Informe técnico',author='Juan Ospina Tenorio; Natalia Hernández Piedrahita; Miguel Ángel Diuza').build(story,onFirstPage=footer,onLaterPages=footer)
(PROJ/'docs/Informe-tecnico.md').write_text('\n'.join(md),encoding='utf-8')
print(pdf)
