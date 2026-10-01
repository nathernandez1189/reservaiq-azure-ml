@echo off
cd /d "%~dp0"
py -3.12 iniciar.py
if errorlevel 1 (
  echo.
  echo Revisa el mensaje anterior. Se requiere Python 3.12 con el lanzador py.
  pause
)
