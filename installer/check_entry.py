"""Ejecutable de consola: verifica el paquete del modelo y predice un FASTA de ejemplo.
Uso: proteinfunc-check [ruta.fasta]"""
import sys

from proteinfunc_app.app import main

if __name__ == "__main__":
    sys.exit(main(["--check", *sys.argv[1:2]]))
