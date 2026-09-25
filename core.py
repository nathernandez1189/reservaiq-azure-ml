"""Feature contract for ReservaIQ. No guest identifiers or outcome variables."""
import math
import pandas as pd

NUMERIC=['lead_time','arrival_month','stays_in_weekend_nights','stays_in_week_nights']
CATEGORICAL=['hotel','meal','market_segment','distribution_channel','reserved_room_type','customer_type']
FEATURES=NUMERIC+CATEGORICAL
BOUNDS={'lead_time':(0,60),'arrival_month':(1,12),'stays_in_weekend_nights':(0,15),'stays_in_week_nights':(0,30)}
CATEGORIES={
 'hotel':['City Hotel','Resort Hotel'],
 'meal':['BB','HB','FB','SC','Undefined'],
 'market_segment':['Direct','Corporate','Online TA','Offline TA/TO','Complementary','Groups','Aviation'],
 'distribution_channel':['Direct','Corporate','TA/TO','GDS'],
 'reserved_room_type':['A','B','C','D','E','F','G','H','L','P'],
 'customer_type':['Transient','Transient-Party','Contract','Group']}
SPANISH={'lead_time':'Anticipación','arrival_month':'Mes de llegada','stays_in_weekend_nights':'Noches de fin de semana','stays_in_week_nights':'Noches entre semana','hotel':'Tipo de hotel','meal':'Alimentación','market_segment':'Segmento de mercado','distribution_channel':'Canal de distribución','reserved_room_type':'Categoría de habitación','customer_type':'Tipo de reserva'}

def validate_input(payload):
    if not isinstance(payload,dict) or set(payload)!=set(FEATURES):
        raise ValueError('Se requieren exactamente las diez variables del formulario o del CSV de ejemplo.')
    clean={}
    for name,(lo,hi) in BOUNDS.items():
        v=payload[name]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v!=int(v) or not lo<=v<=hi:
            raise ValueError(f'{SPANISH[name]}: ingresa un entero entre {lo} y {hi}.')
        clean[name]=int(v)
    if not 1<=clean['stays_in_weekend_nights']+clean['stays_in_week_nights']<=30:
        raise ValueError('La estancia total debe ser de 1 a 30 noches.')
    for name,values in CATEGORIES.items():
        if not isinstance(payload[name],str) or payload[name] not in values:
            raise ValueError(f'{SPANISH[name]}: categoría no admitida.')
        clean[name]=payload[name]
    return clean

def infer(bundle,payload):
    clean=validate_input(payload)
    score=float(bundle['model'].predict_proba(pd.DataFrame([clean])[FEATURES])[0,1])
    flagged=score>=bundle['threshold']
    return {'score':score,'threshold':bundle['threshold'],'flagged':flagged,
      'decision':'Priorizar revisión' if flagged else 'Seguimiento habitual',
      'model':bundle['name'],'model_version':bundle['version'],
      'note':'Índice no calibrado; no es certeza de cancelación. La revisión no cancela ni modifica reservas.',
      'scope':'Reservas con anticipación de 0 a 60 días y estancia de 1 a 30 noches. Datos históricos de Portugal.'}
