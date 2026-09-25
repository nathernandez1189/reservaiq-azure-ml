"""Local demo server. Bind only to localhost; not a production web server."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, argparse, joblib, hashlib
from core import infer

ROOT=Path(__file__).resolve().parent
BUNDLE=joblib.load(ROOT/'artifacts/trained/model.joblib')
MODEL_SHA256=hashlib.sha256((ROOT/'artifacts/trained/model.joblib').read_bytes()).hexdigest()
PROVENANCE_PATH=ROOT/'artifacts/runtime.json'
PROVENANCE=json.loads(PROVENANCE_PATH.read_text()) if PROVENANCE_PATH.exists() else {'origin':'local','job_status':'not_run'}
AZURE_VERIFIED=(PROVENANCE.get('origin')=='azure_ml' and PROVENANCE.get('job_status')=='Completed' and PROVENANCE.get('model_sha256')==MODEL_SHA256)

def public_summary():
    summary=json.loads((ROOT/'artifacts/summary.json').read_text())
    summary['azure_verified']=AZURE_VERIFIED
    summary['deployment']={**PROVENANCE,'model_sha256':MODEL_SHA256,'verified':AZURE_VERIFIED}
    return summary
class Handler(BaseHTTPRequestHandler):
    def respond(self,status,data,mime='application/json; charset=utf-8'):
        body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        route=urlparse(self.path).path
        if route in ['/','/index.html']:
            return self.respond(200,(ROOT/'web/index.html').read_bytes(),'text/html; charset=utf-8')
        if route in ['/style.css','/app.js']:
            return self.respond(200,(ROOT/'web'/route[1:]).read_bytes(),'text/css; charset=utf-8' if route.endswith('css') else 'text/javascript; charset=utf-8')
        if route=='/api/summary':return self.respond(200,public_summary())
        if route=='/api/health':return self.respond(200,{'status':'ok','model':BUNDLE['name'],'azure_verified':AZURE_VERIFIED,'model_sha256':MODEL_SHA256})
        if route=='/api/sample.csv':
            return self.respond(200,(ROOT/'artifacts/demo-input.csv').read_bytes(),'text/csv; charset=utf-8')
        self.respond(404,{'error':'Recurso no encontrado'})
    def do_POST(self):
        route=urlparse(self.path).path
        if route not in ['/api/predict','/api/batch']:return self.respond(404,{'error':'Ruta no encontrada'})
        # Reject cross-origin browser requests to the local model.
        origin=self.headers.get('Origin')
        if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:
            return self.respond(403,{'error':'Origen no permitido'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=150000:raise ValueError('Tamaño de solicitud no permitido.')
            payload=json.loads(self.rfile.read(length))
            if route=='/api/predict':return self.respond(200,infer(BUNDLE,payload))
            if not isinstance(payload,list) or not 1<=len(payload)<=500:raise ValueError('El lote debe contener entre 1 y 500 registros.')
            results=[infer(BUNDLE,row) for row in payload]
            self.respond(200,{'count':len(results),'flagged':sum(x['flagged'] for x in results),'results':results})
        except (ValueError,TypeError,KeyError) as error:self.respond(400,{'error':str(error)})
    def log_message(self,format,*args): pass

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);a=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'ReservaIQ: http://127.0.0.1:{a.port} · modelo real · procedencia verificada en /api/health',flush=True)
    server.serve_forever()
