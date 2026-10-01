"""Una misma arquitectura vectorial para el informe, el repositorio y Canva."""
from pathlib import Path
import math
from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Polygon
from reportlab.graphics import renderSVG, renderPDF
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

WIDTH, HEIGHT = 1800, 950


def architecture(dark=False):
    """Las flechas expresan datos/artefactos; el registro es un paso posterior."""
    p = ({'bg': '#14232d', 'zone': '#192f3b', 'pipeline': '#10212b',
          'card': '#203d49', 'ink': '#edf7f7', 'muted': '#b9d0d5',
          'line': '#66dfcf', 'border': '#45616c', 'local': '#1b343b'} if dark else
         {'bg': '#ffffff', 'zone': '#eff6fa', 'pipeline': '#ffffff',
          'card': '#ffffff', 'ink': '#142e3c', 'muted': '#42616d',
          'line': '#087f80', 'border': '#abc4ce', 'local': '#edf7f3'})
    d = Drawing(WIDTH, HEIGHT)

    def rect(x, y, w, h, fill, stroke=None, radius=15, thickness=2):
        d.add(Rect(x, HEIGHT-y-h, w, h, rx=radius, ry=radius,
                   fillColor=HexColor(fill), strokeColor=HexColor(stroke) if stroke else None,
                   strokeWidth=thickness))

    def text(x, y, value, size=28, bold=False, color=None, anchor='start'):
        d.add(String(x, HEIGHT-y-size, value, fontName='Helvetica-Bold' if bold else 'Helvetica',
                     fontSize=size, fillColor=HexColor(color or p['ink']), textAnchor=anchor))

    def node(x, y, w, h, title, lines):
        rect(x, y, w, h, p['card'], p['border'], 12)
        rect(x, y+15, 5, h-30, p['line'], radius=2)
        title_size=min(30,30*(w-42)/max(1,stringWidth(title,'Helvetica-Bold',30)))
        text(x+21, y+13, title, title_size, True)
        for i, line in enumerate(lines):
            body_size=min(25,25*(w-42)/max(1,stringWidth(line,'Helvetica',25)))
            text(x+21, y+53+i*28, line, body_size, color=p['muted'])

    def arrow(points, label=None, label_pos=None, label_fill=None):
        coords = [(x, HEIGHT-y) for x, y in points]
        d.add(PolyLine([v for xy in coords for v in xy], strokeColor=HexColor(p['line']),
                       strokeWidth=3.3, strokeLineJoin=1, fillColor=None))
        (x0,y0),(x,y) = coords[-2:]
        angle=math.atan2(y-y0,x-x0)
        length, half=12, 5.5
        bx,by=x-length*math.cos(angle), y-length*math.sin(angle)
        tip=[x,y,bx+half*math.sin(angle),by-half*math.cos(angle),
             bx-half*math.sin(angle),by+half*math.cos(angle)]
        d.add(Polygon(tip, fillColor=HexColor(p['line']), strokeColor=None))
        if label:
            lx, ly=label_pos
            w=stringWidth(label,'Helvetica',24)+20
            rect(lx-w/2,ly-3,w,32,label_fill or p['pipeline'],radius=5)
            text(lx,ly,label,24,color=p['muted'],anchor='middle')

    rect(0,0,WIDTH,HEIGHT,p['bg'],radius=0)
    rect(20,20,1760,465,p['zone'],p['border'],20)
    text(50,40,'AZURE  /  Workspace, almacenamiento y registro del modelo',31,True)
    rect(340,95,1010,350,p['pipeline'],p['border'],16)
    text(370,111,'PIPELINE CLI v2  ·  3 componentes  ·  CPU de 0 a 1 nodo',27,True)
    rect(20,525,1760,360,p['local'],p['border'],20)
    text(50,542,'ENTORNO LOCAL',27,True)
    text(50,590,'Modelo descargado.',25,color=p['muted'])
    text(50,625,'Sin endpoint permanente.',25,color=p['muted'])

    node(60,170,230,105,'Datos / Blob',['CSV versionado'])
    node(380,170,260,105,'1. Preparación',['Limpieza y particiones'])
    node(710,170,270,105,'2. Entrenamiento',['Comparar + umbral'])
    node(1050,320,260,105,'3. Evaluación',['Prueba reservada'])
    node(1420,170,310,133,'Registro del modelo',['reservaiq:1','Paso posterior al job'])
    node(1090,560,640,126,'Aplicación de reservas',['Formulario / CSV → API → índice del modelo',
                                               'Análisis, guardado, lista K y exportación'])
    node(455,587,410,95,'Personal del hotel',['Revisión y decisión final'])
    node(1090,735,640,126,'SQLite local',['Datos, índice, referencia y estado de revisión', '.runtime/reservaiq.sqlite3'])
    arrow([(1380,686),(1380,735)])
    arrow([(1420,735),(1420,686)],'guardar / recuperar',(1590,693),p['local'])
    text(50,766,'Cada computador conserva su propia base.',25,color=p['muted'])
    text(50,802,'No se reentrena ni se envían reservas a Azure.',25,color=p['muted'])

    arrow([(290,222),(380,222)])
    arrow([(640,222),(710,222)],'train + validación',(675,142))
    arrow([(510,275),(510,372),(1050,372)],'datos de prueba',(757,351))
    arrow([(845,275),(845,300),(1180,300),(1180,320)],'modelo',(1010,283))
    arrow([(980,222),(1420,222)],'model.joblib',(1195,183))
    arrow([(1180,425),(1180,560)],'métricas + predicciones',(1160,491),p['bg'])
    arrow([(1575,303),(1575,560)],'descarga + SHA-256',(1575,491),p['bg'])
    arrow([(1090,628),(865,628)],'lista K / resultados',(978,595),p['local'])
    text(35,911,'Flechas: datos y artefactos. Registro y descarga son pasos posteriores; no son componentes del pipeline.',25,color=p['muted'])
    return d


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview-dir',type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    folder=root/'docs/figuras'
    folder.mkdir(parents=True,exist_ok=True)
    for suffix,dark in [('arquitectura',False),('arquitectura-canva',True)]:
        diagram=architecture(dark)
        renderSVG.drawToFile(diagram,str(folder/f'{suffix}.svg'))
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True,exist_ok=True)
            renderPDF.drawToFile(diagram,str(args.preview_dir/f'{suffix}.pdf'))
    print('Diagramas SVG generados desde una fuente común.')
