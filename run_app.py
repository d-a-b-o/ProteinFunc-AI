"""Lanzador para PyInstaller y para doble clic: equivale a ``python -m proteinfunc_app``."""
import sys

from proteinfunc_app.app import main

if __name__ == "__main__":
    sys.exit(main())
