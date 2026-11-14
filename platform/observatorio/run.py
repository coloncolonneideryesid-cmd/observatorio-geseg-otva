"""Inicia el Observatorio OTVA:  python run.py [--puerto 8000] [--abrir]
Requiere la carga inicial:  python -m etl.cargar inicial"""
import argparse, os, sys, threading, webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--abrir", action="store_true")
    a = ap.parse_args()
    import uvicorn
    from backend import config as C
    if not C.EVENTS_DB.exists():
        sys.exit("Falta la carga inicial. Ejecute primero:  python -m etl.cargar inicial")
    if a.abrir:
        threading.Timer(2.5, lambda: webbrowser.open(f"http://{a.host}:{a.puerto}")).start()
    print(f"\nObservatorio OTVA en http://{a.host}:{a.puerto}")
    print("Primer ingreso: usuario 'admin'; la clave inicial está en", C.CREDENCIALES)
    uvicorn.run("backend.main:app", host=a.host, port=a.puerto, log_level="info")
