"""Resolución de rutas de recursos, válida en desarrollo y en el ejecutable de PyInstaller."""
from __future__ import annotations

import os
import sys
from pathlib import Path

MODEL_ENV_VAR = "PROTEINFUNC_MODEL_DIR"


def resource_root() -> Path:
    """Carpeta que contiene ``model/`` y ``examples/``.

    En un ejecutable de PyInstaller los datos se extraen en ``sys._MEIPASS``; en
    desarrollo es la raíz del repositorio. No depende del directorio actual.
    """
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parent.parent


def model_dir() -> Path:
    """Carpeta del paquete de modelo (la que contiene ``manifest.json``)."""
    override = os.environ.get(MODEL_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    return resource_root() / "model"


def examples_dir() -> Path:
    return resource_root() / "examples"
