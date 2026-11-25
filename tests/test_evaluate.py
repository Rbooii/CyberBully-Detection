import pandas as pd

from cyberbully.evaluate import _drop_proposals


def test_drop_proposals_filters_unreviewed_rows() -> None:
    frame = pd.DataFrame(
        {
            "text": ["a", "b", "c"],
            "label": [1, 0, 1],
            "status": ["usulan", "final", "Usulan"],
        }
    )
    result = _drop_proposals(frame)
    assert len(result) == 1
    assert result["status"].iloc[0] == "final"


def test_drop_proposals_without_status_keeps_frame() -> None:
    frame = pd.DataFrame({"text": ["a"], "label": [1]})
    assert _drop_proposals(frame).equals(frame)


def test_evaluate_uses_threshold_from_model(monkeypatch, tmp_path) -> None:
    import json

    import cyberbully.evaluate as evaluate

    class FakePredictor:
        def __init__(self, model_dir, device, max_length, threshold=None):
            self.threshold = 0.42 if threshold is None else threshold

        def predict_proba(self, texts):
            return [0.6 for _ in texts]

    monkeypatch.setattr(evaluate, "Predictor", FakePredictor)
    monkeypatch.setattr(
        evaluate,
        "_read_frame",
        lambda path: pd.DataFrame({"text": ["a", "b"], "label": [1, 0]}),
    )

    code = evaluate.main(
        [
            "--model-dir",
            str(tmp_path / "model"),
            "--split",
            "val",
            "--out-dir",
            str(tmp_path / "out"),
        ]
    )

    assert code == 0
    payload = json.loads((tmp_path / "out" / "val_metrics.json").read_text())
    assert payload["threshold"] == 0.42
