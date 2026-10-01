"""One local entry point. Creates a Python 3.12 environment without activation."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description='Prepara y abre ReservaIQ. No utiliza Azure.')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    if sys.version_info[:2] != (3,12):
        print('ReservaIQ utiliza Python 3.12. En Windows: py -3.12 iniciar.py. En macOS: python3.12 iniciar.py.')
        return 1
    env=dict(os.environ,PYTHONUTF8='1')
    executable=ROOT/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')
    if not executable.exists():
        print('Primera ejecución: creando el entorno de ReservaIQ…',flush=True)
        subprocess.run([sys.executable,'-m','venv',str(ROOT/'.venv')],check=True,env=env)
    # Use the environment's interpreter for BOTH installation and application.
    check="import sys; assert sys.version_info[:2] == (3,12); from importlib.metadata import version; from pathlib import Path; pairs=[line.split('==') for line in Path('requirements.txt').read_text(encoding='utf-8').splitlines() if '==' in line]; assert all(version(name)==expected for name,expected in pairs)"
    valid=subprocess.run([str(executable),'-c',check],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if valid.returncode:
        version_check=subprocess.run([str(executable),'-c','import sys; sys.exit(sys.version_info[:2] != (3,12))'],env=env)
        if version_check.returncode:
            print('La carpeta .venv pertenece a otra versión de Python. Renómbrala y vuelve a iniciar. Conserva la carpeta .runtime: contiene las reservas.')
            return 1
        print('Instalando las dependencias del proyecto. Este paso requiere internet y puede tardar unos minutos…',flush=True)
        subprocess.run([str(executable),'-m','pip','install','-r',str(ROOT/'requirements.txt')],cwd=ROOT,env=env,check=True)
    print(f'Abre http://127.0.0.1:{args.port} en tu navegador. Mantén esta ventana abierta.',flush=True)
    try:
        return subprocess.call([str(executable),str(ROOT/'app.py'),'--port',str(args.port)],cwd=ROOT,env=env)
    except KeyboardInterrupt:
        return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError) as error:
        print(f'No fue posible iniciar ReservaIQ: {error}. Revisa Python 3.12 y la conexión de la instalación.')
        raise SystemExit(1)
