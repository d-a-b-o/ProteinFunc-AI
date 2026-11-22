"""Genera THIRD_PARTY_LICENSES.txt con las licencias de las dependencias instaladas (RNF-10).
Se ejecuta en CI antes de PyInstaller:  python tools/make_licenses.py
Requiere pip-licenses en el entorno de compilación."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE = ["pip", "setuptools", "wheel", "pip-licenses", "prettytable", "wcwidth", "pyinstaller",
           "pyinstaller-hooks-contrib", "altgraph", "pefile", "pywin32-ctypes", "macholib", "packaging",
           "pytest", "pytest-qt", "pluggy", "iniconfig", "pygments", "colorama", "tomli"]

HEADER = """ProteinFunc AI Desktop — licencias de terceros
==============================================

Componentes que no son paquetes de Python:
- ESM-2 (esm2_t6_8M_UR50D), Meta AI — licencia MIT. https://github.com/facebookresearch/esm
- Gene Ontology (nombres y relaciones de términos) — CC BY 4.0. https://geneontology.org
- Datos de entrenamiento: CAFA 6 (Kaggle), sujetos a las reglas de la competencia.
- PySide6/Qt se distribuye bajo LGPL-3.0 como librerías dinámicas reemplazables.

Paquetes de Python incluidos (versión y licencia), seguidos de sus textos de licencia:

"""

out = subprocess.run([sys.executable, "-m", "piplicenses", "--format=plain-vertical", "--with-license-file",
                      "--no-license-path", "--with-urls", "--ignore-packages", *EXCLUDE],
                     check=True, capture_output=True, text=True, encoding="utf-8").stdout
target = ROOT / "THIRD_PARTY_LICENSES.txt"
target.write_text(HEADER + out, encoding="utf-8")
print(f"{target} ({len(out.splitlines())} líneas)")
