#!/bin/bash
cd "$(dirname "$0")" || exit 1
if ! command -v python3.12 >/dev/null 2>&1; then
  printf '%s\n' 'Instala Python 3.12 y vuelve a abrir este archivo.'
  read -r -p 'Pulsa Enter para cerrar.'
  exit 1
fi
exec python3.12 iniciar.py
