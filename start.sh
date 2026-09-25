#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python app.py --port 8765
fi
printf '%s\n' 'Primero sigue los pasos de instalación de README.md para crear .venv.'
exit 1
