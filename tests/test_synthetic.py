import pandas as pd
import pytest

from cyberbully.synthetic import (
    DEFAULT_COUNTS,
    build_augmented_train,
    check_synthetic,
    generate_synthetic,
)


def test_default_counts_total_15k() -> None:
    assert sum(count for _, count in DEFAULT_COUNTS.values()) == 15_000
    assert sum(label * count for label, count in DEFAULT_COUNTS.values()) == 9_000


def test_generate_is_deterministic_and_unique() -> None:
    counts = {"sindiran": 40, "kasar_akrab": 40, "kritik": 40}
    first = generate_synthetic(counts=counts, seed=7)
    second = generate_synthetic(counts=counts, seed=7)

    assert len(first) == 120
    assert first["text"].is_unique
    assert first.equals(second)
    assert set(first["label"]) == {0, 1}
    assert set(first["category"]) == set(counts)


def test_generate_has_no_pii() -> None:
    import re

    frame = generate_synthetic(counts={"sindiran": 80, "netral": 80}, seed=3)
    texts = " ".join(frame["text"].astype(str))
    assert not re.search(r"https?://|@\w+|\b08\d{7,11}\b", texts)


def test_check_rejects_eval_overlap() -> None:
    synthetic = generate_synthetic(counts={"sindiran": 30}, seed=1)
    eval_frame = pd.DataFrame(
        {"text": [synthetic["text"].iloc[0]], "label": [1]}
    )
    with pytest.raises(ValueError, match="eval"):
        check_synthetic(synthetic, eval_frame=eval_frame)


def test_check_rejects_pii() -> None:
    frame = generate_synthetic(counts={"netral": 20}, seed=1)
    frame.loc[frame.index[0], "text"] = "hubungi saya di @akun atau 081234567890"
    with pytest.raises(ValueError, match="PII"):
        check_synthetic(frame)


def test_augmented_train_keeps_val_test_out() -> None:
    synthetic = generate_synthetic(counts={"sindiran": 30, "netral": 30}, seed=5)
    real_train = pd.DataFrame(
        {"text": [f"train asli {i}" for i in range(10)], "label": [1, 0] * 5}
    )
    real_val = pd.DataFrame({"text": ["val khusus"], "label": [1]})
    real_test = pd.DataFrame({"text": ["test khusus"], "label": [0]})

    combined = build_augmented_train(real_train, synthetic, real_val, real_test, seed=5)

    assert len(combined) == 70
    assert set(combined["source"]) == {"real", "synthetic"}
    assert "val khusus" not in set(combined["text"])
    assert "test khusus" not in set(combined["text"])
    assert combined["text"].is_unique
