import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL_DIR = ROOT / "model"
EXAMPLES = ROOT / "examples"
DATA = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="session")
def loaded_model():
    from proteinfunc_app.services import load_predictor

    return load_predictor(MODEL_DIR)


@pytest.fixture(scope="session")
def predictor(loaded_model):
    return loaded_model.predictor
