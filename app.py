"""Local demo API and persistent reservation copies. Bind only to localhost."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import argparse
import hashlib
import json
import os
import sqlite3
import joblib
from core import infer, validate_input
from booking_dates import validate_stay, features_from_stay
from storage import ReservationStore, ConflictError, MissingReservation, reference

ROOT = Path(__file__).resolve().parent
BUNDLE = joblib.load(ROOT/'artifacts/trained/model.joblib')
MODEL_SHA256 = hashlib.sha256((ROOT/'artifacts/trained/model.joblib').read_bytes()).hexdigest()
PROVENANCE_PATH = ROOT/'artifacts/runtime.json'
PROVENANCE = json.loads(PROVENANCE_PATH.read_text(encoding='utf-8')) if PROVENANCE_PATH.exists() else {'origin':'local','job_status':'not_run'}
AZURE_VERIFIED = (PROVENANCE.get('origin') == 'azure_ml' and PROVENANCE.get('job_status') == 'Completed' and PROVENANCE.get('model_sha256') == MODEL_SHA256)
STORE = ReservationStore(os.environ.get('RESERVAIQ_DB_PATH', ROOT/'.runtime/reservaiq.sqlite3'))


def public_summary():
    summary = json.loads((ROOT/'artifacts/summary.json').read_text(encoding='utf-8'))
    summary['azure_verified'] = AZURE_VERIFIED
    summary['deployment'] = {**PROVENANCE, 'model_sha256': MODEL_SHA256, 'verified': AZURE_VERIFIED}
    return summary


def reservation_entry(payload, source='manual'):
    if not isinstance(payload, dict):
        raise ValueError('Envía los datos de una reserva.')
    clean = validate_input(payload.get('inputs'))
    stay = validate_stay(payload.get('stay'))
    if stay is not None and any(clean[k] != v for k, v in features_from_stay(stay).items()):
        raise ValueError('Las fechas no coinciden con los días y noches del análisis. Vuelve a elegir la estancia.')
    return {'inputs': clean, 'result': infer(BUNDLE, clean),
            'reference': reference(payload.get('reference', '')),
            'source': source, 'model_sha256': MODEL_SHA256, 'stay': stay}


def batch_results(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise ValueError('El lote debe contener entre 1 y 500 registros.')
    results = []
    for i, row in enumerate(rows, 1):
        try:
            results.append(infer(BUNDLE, row))
        except ValueError as error:
            raise ValueError(f'Fila {i}: {error}') from error
    return results


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, mime='application/json; charset=utf-8'):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        try:
            static = {'/': ('web/index.html', 'text/html'), '/index.html': ('web/index.html', 'text/html'),
                      '/style.css': ('web/style.css', 'text/css'), '/app.js': ('web/app.js', 'text/javascript'),
                      '/csv.js': ('web/csv.js', 'text/javascript'),
                      '/dates.js': ('web/dates.js', 'text/javascript'),
                      '/booking.js': ('web/booking.js', 'text/javascript'),
                      '/arquitectura.svg': ('docs/figuras/arquitectura-canva.svg', 'image/svg+xml'),
                      '/api/sample.csv': ('ejemplos-csv/reservas-listas.csv', 'text/csv')}
            if route in static:
                path, mime = static[route]
                return self.respond(200, (ROOT/path).read_bytes(), mime+'; charset=utf-8')
            if route == '/api/summary':
                return self.respond(200, public_summary())
            if route == '/api/health':
                return self.respond(200, {'status': 'ok', 'model': BUNDLE['name'], 'azure_verified': AZURE_VERIFIED,
                                          'model_sha256': MODEL_SHA256, 'storage': 'local_sqlite'})
            if route == '/api/reservations':
                records = STORE.list()
                return self.respond(200, {'reservations': records, 'count': len(records), 'storage': 'local'})
            self.respond(404, {'error': 'Recurso no encontrado'})
        except (OSError, sqlite3.Error):
            self.respond(503, {'error': 'No se pudieron leer los archivos o las reservas. Revisa los permisos de la carpeta del proyecto y vuelve a intentar.'})
        except (ValueError, TypeError, KeyError):
            self.respond(500, {'error': 'No se pudieron leer los datos guardados. Conserva tus archivos y revisa que la copia del proyecto esté completa.'})

    def do_POST(self):
        route = urlparse(self.path).path
        routes = ['/api/predict', '/api/batch', '/api/reservations', '/api/reservations/batch',
                  '/api/reservations/update', '/api/reservations/status']
        if route not in routes:
            return self.respond(404, {'error': 'Ruta no encontrada'})
        origin = self.headers.get('Origin')
        if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}']:
            return self.respond(403, {'error': 'Origen no permitido'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1_000_000:
                raise ValueError('La solicitud es demasiado grande. Divide el archivo en lotes más pequeños.')
            payload = json.loads(self.rfile.read(length))
            if route == '/api/predict':
                result = reservation_entry(payload)['result'] if isinstance(payload, dict) and 'inputs' in payload else infer(BUNDLE, payload)
                return self.respond(200, result)
            if route == '/api/batch':
                results = batch_results(payload)
                return self.respond(200, {'count': len(results), 'flagged': sum(x['flagged'] for x in results), 'results': results})
            if not isinstance(payload, dict):
                raise ValueError('Envía una reserva o un lote válido.')
            if route == '/api/reservations':
                entry = reservation_entry(payload, payload.get('source', 'manual'))
                records = STORE.create([entry], payload.get('request_id'))
                return self.respond(200, {'reservation': records[0]})
            if route == '/api/reservations/batch':
                rows = payload.get('rows')
                results = batch_results(rows)
                entries = [{'inputs': validate_input(row), 'result': result, 'reference': '', 'source': 'csv',
                            'model_sha256': MODEL_SHA256} for row, result in zip(rows, results)]
                records = STORE.create(entries, payload.get('request_id'))
                return self.respond(200, {'reservations': records, 'count': len(records)})
            if route == '/api/reservations/update':
                entry = reservation_entry(payload)
                record = STORE.update(payload.get('id'), payload.get('revision'), entry)
            else:
                record = STORE.set_status(payload.get('id'), payload.get('revision'), payload.get('status'))
            self.respond(200, {'reservation': record})
        except ConflictError as error:
            self.respond(409, {'error': str(error)})
        except MissingReservation as error:
            self.respond(404, {'error': str(error)})
        except (ValueError, TypeError, KeyError) as error:
            self.respond(400, {'error': str(error)})
        except (OSError, sqlite3.Error):
            self.respond(503, {'error': 'No se pudo guardar. Comprueba el espacio y los permisos de la carpeta del proyecto. Tus reservas anteriores se conservan.'})

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError:
        parser.exit(1, f'No se pudo abrir el puerto {args.port}. Cierra la otra copia o utiliza --port 8766.\n')
    print(f'ReservaIQ: http://127.0.0.1:{args.port}\nMantén esta terminal abierta. Para cerrar, pulsa Ctrl+C.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nReservaIQ se cerró. Tus reservas guardadas se conservan.')
    finally:
        server.server_close()
