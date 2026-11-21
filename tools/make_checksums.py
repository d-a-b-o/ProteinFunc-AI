"""Genera model/SHA256SUMS con las huellas del paquete de modelo.

Ejecutar solo al incorporar una nueva versión del modelo:
    python tools/make_checksums.py [carpeta_modelo]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from proteinfunc_app.core.integrity import write_checksums  # noqa: E402

bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "model"
print(write_checksums(bundle).read_text(encoding="utf-8"))
