# -*- mode: python ; coding: utf-8 -*-
# Empaquetado de ProteinFunc AI Desktop con PyInstaller (modo carpeta).
#   pyinstaller proteinfunc.spec --noconfirm
# Debe ejecutarse en cada sistema destino (Windows genera .exe; Linux, un binario).
# Instala PyTorch CPU antes de empaquetar para no incluir CUDA.
#
# Genera dos ejecutables que comparten las librerías:
#   ProteinFuncAI        aplicación gráfica (sin consola en Windows)
#   proteinfunc-check    verificación por consola: paquete + predicción de ejemplo
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("transformers.models.esm") + ["transformers.models.bert"]
datas = [("model", "model"), ("examples", "examples"),
         ("proteinfunc_app/icon.png", "proteinfunc_app")]
datas += collect_data_files("transformers", include_py_files=False)
if os.path.isfile("THIRD_PARTY_LICENSES.txt"):  # Generado por tools/make_licenses.py (CI).
    datas.append(("THIRD_PARTY_LICENSES.txt", "."))
icon = "installer/icon.ico" if sys.platform == "win32" else None

a = Analysis(
    ["run_app.py", "installer/check_entry.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "IPython", "jupyter", "pandas", "sklearn", "scipy",
              "tensorboard", "torchvision", "torchaudio", "triton", "pytest"],
    noarchive=False,
    # transformers inspecciona la ruta de sus propios .py (auto_docstring): se incluyen como archivos.
    module_collection_mode={"transformers": "py"},
)
pyz = PYZ(a.pure)
gui = EXE(pyz, [s for s in a.scripts if s[0] == "run_app"], [], exclude_binaries=True,
          name="ProteinFuncAI", console=False, icon=icon, upx=False)
cli = EXE(pyz, [s for s in a.scripts if s[0] == "check_entry"], [], exclude_binaries=True,
          name="proteinfunc-check", console=True, icon=icon, upx=False)
coll = COLLECT(gui, cli, a.binaries, a.datas, name="ProteinFuncAI", upx=False)
