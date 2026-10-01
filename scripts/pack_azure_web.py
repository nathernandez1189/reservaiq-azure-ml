"""Create an allowlisted Azure package without credentials or local databases."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def pack(artifacts,output):
    artifacts=Path(artifacts).resolve();output=Path(output).resolve()
    runtime=json.loads((artifacts/'runtime.json').read_text(encoding='utf-8'))
    model=artifacts/'trained/model.joblib'
    if not (runtime.get('origin')=='azure_ml' and runtime.get('job_status')=='Completed'
            and runtime.get('model_sha256')==hashlib.sha256(model.read_bytes()).hexdigest()):
        raise ValueError('Falta procedencia de una ejecución Azure completada y un modelo coincidente.')
    sources=['app.py','core.py','booking_dates.py','storage.py','cloud_storage.py','cloud_wsgi.py',
             'docs/figuras/arquitectura-canva.svg','docs/figuras/arquitectura-azure-web.svg',
             'ejemplos-csv/reservas-listas.csv']
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'web').glob('*')) if p.suffix in ('.js','.css','.html')]
    requirements=(ROOT/'requirements.txt').read_text(encoding='utf-8')+'\n'+''.join(
        line+'\n' for line in (ROOT/'requirements-azure.txt').read_text(encoding='utf-8').splitlines()
        if not line.startswith('-r '))
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for rel in sources:z.write(ROOT/rel,rel)
        for rel in ['trained/model.joblib','summary.json','runtime.json']:z.write(artifacts/rel,'cloud-artifacts/'+rel)
        z.writestr('requirements.txt',requirements)
    with zipfile.ZipFile(output) as z:
        if z.testzip():raise ValueError('El paquete no pasó la verificación de integridad.')
        assert not any(part in name.split('/') for name in z.namelist() for part in ['.azure','.venv','.runtime','.git'])
    return {'package':output.name,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'job':runtime['job_name']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--artifacts-dir',default='cloud-artifacts');parser.add_argument('--output',default='deploy.zip')
    args=parser.parse_args();print(json.dumps(pack(args.artifacts_dir,args.output),ensure_ascii=False))
