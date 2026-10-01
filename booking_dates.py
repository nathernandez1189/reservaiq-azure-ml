"""Date-only stays; checkout is excluded and no timezone offsets are used."""
from datetime import date, timedelta
import re

STAY_KEYS = {'booked_on', 'check_in', 'check_out'}


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Elige una fecha válida para creación, llegada y salida.')
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError('Una de las fechas no existe. Revisa el calendario.') from error
    if not 1900 <= parsed.year <= 2100:
        raise ValueError('Utiliza fechas entre 1900 y 2100.')
    return parsed


def validate_stay(stay):
    if stay is None:
        return None
    if not isinstance(stay, dict) or set(stay) != STAY_KEYS:
        raise ValueError('La estancia necesita fecha de creación, llegada y salida.')
    booked, arrival, departure = (parse_date(stay[k]) for k in ('booked_on', 'check_in', 'check_out'))
    lead = (arrival-booked).days
    nights = (departure-arrival).days
    if not 0 <= lead <= 60:
        raise ValueError('La llegada debe ser entre 0 y 60 días después de crear la reserva.')
    if not 1 <= nights <= 30:
        raise ValueError('La salida debe ser posterior a la llegada y la estancia debe tener entre 1 y 30 noches.')
    return {key: stay[key] for key in ('booked_on', 'check_in', 'check_out')}


def features_from_stay(stay):
    clean = validate_stay(stay)
    if clean is None:
        raise ValueError('Elige las fechas de tu estancia.')
    booked, arrival, departure = (parse_date(clean[k]) for k in ('booked_on', 'check_in', 'check_out'))
    total = (departure-arrival).days
    weekend = sum((arrival+timedelta(days=i)).weekday() >= 5 for i in range(total))
    return {'lead_time': (arrival-booked).days, 'arrival_month': arrival.month,
            'stays_in_weekend_nights': weekend, 'stays_in_week_nights': total-weekend}
