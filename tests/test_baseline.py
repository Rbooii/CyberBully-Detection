import pandas as pd

from cyberbully.baseline import top_features, train_baseline
from cyberbully.config import LABEL_COLUMN, TEXT_COLUMN


def make_frame(n: int = 80, offset: int = 0) -> pd.DataFrame:
    rows = []
    for index in range(n):
        number = offset + index
        if index % 2 == 0:
            rows.append(
                {
                    TEXT_COLUMN: f"dasar bodoh benci nomor {number}",
                    LABEL_COLUMN: 1,
                }
            )
        else:
            rows.append(
                {
                    TEXT_COLUMN: f"semangat bagus keren nomor {number}",
                    LABEL_COLUMN: 0,
                }
            )
    return pd.DataFrame(rows)


def test_baseline_trains_and_tunes_threshold() -> None:
    pipeline, payload, features = train_baseline(
        make_frame(), make_frame(offset=100), c_grid=(1.0,)
    )

    assert payload["best_c"] == 1.0
    assert 0.0 < float(payload["threshold"]) < 1.0
    assert payload["val"]["f1_bully"] > 0.5
    assert 0.0 <= float(payload["val"]["accuracy"]) <= 1.0
    assert features["bully"]
    assert features["non_bully"]

    probabilities = pipeline.predict_proba(make_frame(offset=500)[TEXT_COLUMN])[:, 1]
    assert probabilities.shape == (80,)
    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_top_features_returns_requested_limit() -> None:
    pipeline, _, _ = train_baseline(make_frame(), make_frame(offset=100), c_grid=(1.0,))
    features = top_features(pipeline, limit=3)
    assert len(features["bully"]) <= 3
    assert len(features["non_bully"]) <= 3
