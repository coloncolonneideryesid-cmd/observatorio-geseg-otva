@echo off
cd /d "%~dp0"
pip install -r requirements.txt
if not exist data\db\otva.db (
  echo Cargando los eventos de la v0 al Observatorio...
  python -m etl.cargar inicial --usuario instalacion
)
pause
