import json
import threading

import pytest
from conftest import DATA

from proteinfunc_app.core.results import SCORE_FLOOR
from proteinfunc_app.services import run_prediction


def test_matches_reference_prediction_from_kaggle(predictor):
    """RNF-04: la app reproduce el example_prediction.json exportado por el notebook."""
    reference = json.loads((DATA / "reference_prediction.json").read_text(encoding="utf-8"))
    result = predictor.predict(reference["input"])
    expected = reference["results"][0]
    got = result["results"][0]
    assert got["status"] == expected["status"] and got["truncated"] == expected["truncated"]
    assert [p["go_term"] for p in got["predictions"]] == [p["go_term"] for p in expected["predictions"]]
    for a, b in zip(got["predictions"], expected["predictions"]):
        assert a["score"] == pytest.approx(b["score"], abs=1e-5)


def test_direct_and_propagated_scores(predictor):
    result = predictor.predict(">x\nMALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT", threshold=0.0)
    preds = result["results"][0]["predictions"]
    assert len(preds) == len(predictor.classes)
    for p in preds:
        assert p["direct_score"] <= p["score"] + 1e-7
        assert p["origin"] == ("propagated" if p["score"] > p["direct_score"] else "direct")
    by_term = {p["go_term"]: p["score"] for p in preds}
    for p in preds:  # Consistencia ontológica: ancestro ≥ descendiente.
        for parent in predictor.metadata[p["go_term"]]["ancestors"]:
            assert by_term[parent] >= p["score"] - 1e-7


def test_chunked_prediction_equals_single_call(predictor):
    records = [(f"p{i}", "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEG"[: 10 + i]) for i in range(20)]
    chunked = run_prediction(predictor, records, chunk_size=3)
    whole = predictor.predict_records(records, threshold=SCORE_FLOOR)
    assert [r["id"] for r in chunked] == [r["id"] for r in whole]
    for a, b in zip(chunked, whole):
        assert [p["go_term"] for p in a["predictions"]] == [p["go_term"] for p in b["predictions"]]
        assert [p["score"] for p in a["predictions"]] == pytest.approx([p["score"] for p in b["predictions"]], abs=1e-5)


def test_cancel_returns_none_not_partial(predictor):
    cancel = threading.Event()
    records = [(f"p{i}", "MKTAYIAKQR") for i in range(10)]
    seen = []

    def progress(done, total):
        seen.append(done)
        cancel.set()

    assert run_prediction(predictor, records, cancel, progress, chunk_size=2) is None
    assert seen == [2]


def test_truncation_flag(predictor):
    result = predictor.predict(">largo\n" + "M" * 700)["results"][0]
    assert result["truncated"] and result["residues_used"] == 512 and result["length"] == 700
