"""Local reservation copies. Historical model artifacts are never modified."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sqlite3
import uuid

class ConflictError(ValueError):
    pass

class MissingReservation(ValueError):
    pass

def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)

def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def reference(value):
    if not isinstance(value, str) or len(value.strip()) > 80 or any(ord(c) < 32 for c in value):
        raise ValueError('La referencia debe tener hasta 80 caracteres, sin saltos de línea.')
    return value.strip()

def revision(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError('Falta la versión de la reserva. Actualiza la lista e inténtalo de nuevo.')
    return value

class ReservationStore:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            version = con.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise ValueError('Esta base de reservas requiere una versión más reciente de ReservaIQ.')
            con.execute('''CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY, reference TEXT NOT NULL, inputs TEXT NOT NULL,
                result TEXT NOT NULL, model_sha256 TEXT NOT NULL, source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', revision INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')
            con.execute('''CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, response TEXT NOT NULL)''')
            con.execute('PRAGMA user_version = 1')
            con.commit()
            with con:
                yield con
        finally:
            con.close()

    @staticmethod
    def record(row):
        data = dict(row)
        data['inputs'] = json.loads(data['inputs'])
        data['result'] = json.loads(data['result'])
        return data

    def list(self):
        with self.connect() as con:
            return [self.record(row) for row in con.execute('SELECT * FROM reservations ORDER BY created_at DESC, id')]

    def create(self, entries, request_id):
        if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}', request_id):
            raise ValueError('No se pudo identificar el guardado. Recarga la página y vuelve a intentarlo.')
        if not 1 <= len(entries) <= 500:
            raise ValueError('Guarda entre 1 y 500 reservas por operación.')
        payload_hash = hashlib.sha256(encode(entries).encode('utf-8')).hexdigest()
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            prior = con.execute('SELECT * FROM requests WHERE request_id=?', (request_id,)).fetchone()
            if prior:
                if prior['payload_hash'] != payload_hash:
                    raise ConflictError('Este intento de guardado ya se usó con otros datos. Recarga la lista.')
                return json.loads(prior['response'])
            saved = []
            for entry in entries:
                ref = reference(entry['reference'])
                if entry['source'] not in ('manual', 'example', 'csv'):
                    raise ValueError('Origen de la reserva no admitido.')
                rid = 'RI-' + uuid.uuid4().hex[:12].upper()
                now = timestamp()
                con.execute('''INSERT INTO reservations
                    (id,reference,inputs,result,model_sha256,source,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?)''', (
                    rid, ref or rid, encode(entry['inputs']), encode(entry['result']),
                    entry['model_sha256'], entry['source'], now, now))
                saved.append(self.record(con.execute('SELECT * FROM reservations WHERE id=?', (rid,)).fetchone()))
            con.execute('INSERT INTO requests VALUES (?,?,?)', (request_id, payload_hash, encode(saved)))
            return saved

    def update(self, rid, expected_revision, entry):
        ref = reference(entry['reference'])
        expected_revision = revision(expected_revision)
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM reservations WHERE id=?', (rid,)).fetchone()
            if row is None:
                raise MissingReservation('La reserva ya no está disponible en esta copia.')
            if row['revision'] != expected_revision:
                raise ConflictError('La reserva cambió en otra ventana. Vuelve a abrirla desde Mis reservas.')
            if row['status'] == 'archived':
                raise ConflictError('Primero restaura la reserva archivada desde Mis reservas.')
            con.execute('''UPDATE reservations SET reference=?, inputs=?, result=?,
                model_sha256=?, status='pending', revision=revision+1, updated_at=? WHERE id=?''', (
                ref or rid, encode(entry['inputs']), encode(entry['result']), entry['model_sha256'], timestamp(), rid))
            return self.record(con.execute('SELECT * FROM reservations WHERE id=?', (rid,)).fetchone())

    def set_status(self, rid, expected_revision, status):
        if status not in ('pending', 'reviewed', 'archived'):
            raise ValueError('Estado de revisión no admitido.')
        expected_revision = revision(expected_revision)
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM reservations WHERE id=?', (rid,)).fetchone()
            if row is None:
                raise MissingReservation('La reserva ya no está disponible en esta copia.')
            if row['revision'] != expected_revision:
                raise ConflictError('La reserva cambió en otra ventana. Actualiza la lista para continuar.')
            con.execute('UPDATE reservations SET status=?, revision=revision+1, updated_at=? WHERE id=?', (status, timestamp(), rid))
            return self.record(con.execute('SELECT * FROM reservations WHERE id=?', (rid,)).fetchone())
