"""Serve the existing HTTP handlers through a production WSGI server.

Gunicorn controls sockets, timeouts and workers; both deployments retain one API
implementation. Only explicit static routes are exposed, never filesystem paths.
"""
from email.message import Message
from http import HTTPStatus
from io import BytesIO
from types import SimpleNamespace
import json
import app


def application(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET').upper()
    if method not in ('GET', 'HEAD', 'POST'):
        start_response('405 Method Not Allowed', [('Allow', 'GET, HEAD, POST'), ('Content-Length', '0')])
        return [b'']
    handler = app.Handler.__new__(app.Handler)
    handler.path = environ.get('PATH_INFO', '/')
    handler.server = SimpleNamespace(server_port=8000)
    handler.headers = Message()
    for name, value in environ.items():
        if name.startswith('HTTP_'):
            handler.headers[name[5:].replace('_', '-')] = str(value)
    handler.headers['Content-Length'] = environ.get('CONTENT_LENGTH', '0') or '0'
    handler.rfile = environ.get('wsgi.input', BytesIO())
    response = {}

    def respond(status, data, mime='application/json; charset=utf-8'):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
        response.update(status=status, body=body, mime=mime)

    handler.respond = respond
    if method == 'POST':
        handler.do_POST()
    else:
        handler.do_GET()
    status = response['status']
    headers = [('Content-Type', response['mime']), ('Content-Length', str(len(response['body']))),
               ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'),
               ('Referrer-Policy', 'same-origin'), ('X-Frame-Options', 'DENY')]
    if app.PUBLIC_ORIGIN:
        headers.append(('Strict-Transport-Security', 'max-age=86400'))
    start_response(f'{status} {HTTPStatus(status).phrase}', headers)
    return [b'' if method == 'HEAD' else response['body']]
