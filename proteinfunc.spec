# -*- mode: python ; coding: utf-8 -*-
# Empaquetado de ProteinFunc AI Desktop con PyInstaller (modo carpeta).
#   pyinstaller proteinfunc.spec --noconfirm
# Debe ejecutarse en cada sistema destino (Windows genera .exe; Linux, un binario).
# Usa PyTorch CPU para que la distribución no incluya CUDA.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("transformers.models.esm") + ["transformers.models.bert"]
datas = [("model", "model"), ("examples", "examples")]
datas += collect_data_files("transformers", include_py_files=False)

a = Analysis(
    ["run_app.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "IPython", "jupyter", "pandas", "sklearn", "scipy",
              "tensorboard", "torchvision", "torchaudio", "triton", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ProteinFuncAI",
    console=False,
    icon=None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="ProteinFuncAI")
