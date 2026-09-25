"""Gráfica reproducible desde las métricas; requiere reportlab==4.4.9."""
import json
from pathlib import Path
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics import renderSVG
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT / 'artifacts/summary.json').read_text())['test']
d = Drawing(960, 450)
navy, text, muted, aqua = map(HexColor, ['#10202b', '#edf6f8', '#a8bac6', '#51d3bf'])
d.add(Rect(0, 0, 960, 450, fillColor=navy, strokeColor=navy))
d.add(String(40, 406, 'RESERVAIQ  /  RESULTADO RETROSPECTIVO', fontName='Helvetica-Bold', fontSize=13, fillColor=aqua))
d.add(String(40, 365, '¿Qué concentra una lista de revisión del 20 %?', fontName='Helvetica-Bold', fontSize=25, fillColor=text))
d.add(String(40, 336, f"Prueba temporal: {m['n']:,} reservas de dos hoteles de Portugal (2017).".replace(',', '.'), fontName='Helvetica', fontSize=13, fillColor=muted))
chart = HorizontalBarChart()
chart.x, chart.y, chart.width, chart.height = 272, 130, 550, 152
chart.data = [[m['positives'] / m['n'] * 100, m['top20']['precision'] * 100]]
chart.categoryAxis.categoryNames = ['Selección aleatoria esperada', '20 % de mayor índice']
chart.categoryAxis.labels.fontName = 'Helvetica'
chart.categoryAxis.labels.fontSize = 12
chart.categoryAxis.labels.fillColor = text
chart.categoryAxis.strokeColor = muted
chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 50, 10
chart.valueAxis.labels.fillColor = muted
chart.valueAxis.labels.fontSize = 11
chart.valueAxis.labelTextFormat = '%d %%'
chart.valueAxis.strokeColor = muted
chart.bars[0].fillColor = aqua
chart.bars[0].strokeColor = aqua
chart.bars[(0, 0)].fillColor = HexColor('#547586')
chart.barLabelFormat = '%.1f %%'
chart.barLabels.fontName = 'Helvetica'
chart.valueAxis.labels.fontName = 'Helvetica'
chart.barLabels.fontSize = 13
chart.barLabels.fillColor = text
chart.barLabels.dx = 24
chart.barLabels.boxAnchor = 'w'
d.add(chart)
d.add(String(40, 72, f"{m['top20']['hits']} cancelaciones en {m['top20']['k']:,} reservas priorizadas  ·  {m['top20']['lift']:.2f} veces la concentración base".replace(',', '.'), fontName='Helvetica-Bold', fontSize=16, fillColor=text))
d.add(String(40, 40, 'Comparación histórica. No demuestra cancelaciones evitadas ni ingresos recuperados.', fontName='Helvetica', fontSize=12, fillColor=muted))
renderSVG.drawToFile(d, str(ROOT / 'docs/figuras/priorizacion.svg'))
print('docs/figuras/priorizacion.svg')
