import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from cyberbully.config import LABEL_COLUMN, TEXT_COLUMN
from cyberbully.data import (
    dedup,
    map_labels,
    prepare,
    read_csv_auto,
    read_frame,
    split_dataset,
    stratified_subset,
    validate_splits,
)


def make_frame(n: int = 60) -> pd.DataFrame:
    rows = []
    for i in range(n):
        if i % 2 == 0:
            rows.append({"tweet": f"dasar bodoh nomor {i}!!!", "kategori": "bully"})
        else:
            rows.append({"tweet": f"semangat ya nomor {i}", "kategori": "non-bully"})
    return pd.DataFrame(rows)


def test_map_labels_to_binary() -> None:
    df = pd.DataFrame(
        {"text": ["a", "b", "c"], "label": ["Bully", "non-bully", "BULLY"]}
    )
    mapped = map_labels(df, ["bully"])
    assert mapped[LABEL_COLUMN].tolist() == [1, 0, 1]


def test_map_labels_rejects_multiple_unknown_classes() -> None:
    df = pd.DataFrame({"text": ["a", "b", "c"], "label": ["bully", "netral", "sayang"]})
    with pytest.raises(ValueError, match="lebih dari dua"):
        map_labels(df, ["bully"])


def test_map_labels_union_of_columns() -> None:
    df = pd.DataFrame(
        {
            "text": ["a", "b", "c", "d"],
            "HS": [1, 0, 1, 0],
            "Abusive": [0, 1, 1, 0],
        }
    )
    union = map_labels(df, ["1"], label_cols=["HS", "Abusive"], mode="any")
    both = map_labels(df, ["1"], label_cols=["HS", "Abusive"], mode="all")
    assert union[LABEL_COLUMN].tolist() == [1, 1, 1, 0]
    assert both[LABEL_COLUMN].tolist() == [0, 0, 1, 0]


def test_map_labels_rejects_unknown_mode() -> None:
    df = pd.DataFrame({"text": ["a"], "label": ["bully"]})
    with pytest.raises(ValueError, match="mode label"):
        map_labels(df, ["bully"], mode="xor")


def test_read_csv_auto_replaces_invalid_utf8(tmp_path) -> None:
    path = tmp_path / "rusak.csv"
    path.write_bytes(b"text,label\nhalo \xf0,1\nbaik,0\n")
    with pytest.warns(RuntimeWarning, match="bukan UTF-8 valid"):
        df = read_csv_auto(path)
    assert "\ufffd" in df["text"].iloc[0]


def test_dedup_uses_normalized_text() -> None:
    df = pd.DataFrame(
        {
            "text": ["Halo   Dunia", "halo dunia", "Halo Dunia!!!", "   "],
            "label": [1, 1, 0, 0],
        }
    )
    result = dedup(df)
    assert len(result) == 2
    assert set(result[TEXT_COLUMN]) == {"halo dunia", "halo dunia!!!"}


def binary_frame(n: int = 60) -> pd.DataFrame:
    raw = make_frame(n).rename(columns={"tweet": TEXT_COLUMN, "kategori": LABEL_COLUMN})
    return dedup(map_labels(raw, ["bully"]))


def test_split_is_deterministic_and_disjoint() -> None:
    df = binary_frame()
    first = split_dataset(df)
    second = split_dataset(df)

    for name in ("train", "val", "test"):
        assert_frame_equal(first[name], second[name])

    validate_splits(first)
    assert (len(first["train"]), len(first["val"]), len(first["test"])) == (48, 6, 6)


def test_validate_splits_detects_leakage() -> None:
    df = binary_frame()
    splits = {
        "train": df.iloc[:40].reset_index(drop=True),
        "val": df.iloc[40:50].reset_index(drop=True),
        "test": pd.concat([df.iloc[50:], df.iloc[:2]]).reset_index(drop=True),
    }
    with pytest.raises(ValueError, match="data leakage"):
        validate_splits(splits)


def test_prepare_dedups_before_split_and_writes_csv(tmp_path) -> None:
    raw = make_frame()
    duplicated = pd.concat([raw, raw.head(4)], ignore_index=True)
    source = tmp_path / "raw.csv"
    duplicated.to_csv(source, index=False)

    out_dir = tmp_path / "processed"
    splits = prepare(source, "tweet", "kategori", ["bully"], out_dir=out_dir)

    total = sum(len(part) for part in splits.values())
    assert total == len(raw)

    for name in ("train", "val", "test"):
        path = out_dir / f"{name}.csv"
        assert path.exists()
        loaded = pd.read_csv(path)
        assert list(loaded.columns) == [TEXT_COLUMN, LABEL_COLUMN]
        assert len(loaded) == len(splits[name])


def test_prepare_keeps_support_columns(tmp_path) -> None:
    rows = []
    for i in range(40):
        rows.append(
            {
                "tweet": f"contoh tweet {i}",
                "HS": i % 2,
                "Abusive": 1 if i % 3 == 0 else 0,
            }
        )
    source = tmp_path / "raw.csv"
    pd.DataFrame(rows).to_csv(source, index=False)

    splits = prepare(
        source,
        "tweet",
        ["HS", "Abusive"],
        ["1"],
        out_dir=tmp_path / "processed",
        keep_cols=["HS", "Abusive"],
    )

    for part in splits.values():
        assert list(part.columns) == [TEXT_COLUMN, LABEL_COLUMN, "HS", "Abusive"]


def test_stratified_subset_keeps_classes_and_is_deterministic() -> None:
    df = binary_frame()
    first = stratified_subset(df, 20, seed=42)
    second = stratified_subset(df, 20, seed=42)

    assert len(first) == 20
    assert set(first[LABEL_COLUMN].unique()) == {0, 1}
    assert_frame_equal(first, second)


def test_stratified_subset_returns_full_frame_when_size_too_large() -> None:
    df = binary_frame()
    assert stratified_subset(df, 10_000) is df


def test_read_frame_requires_text_and_label(tmp_path) -> None:
    path = tmp_path / "missing_label.csv"
    path.write_text("text\nhalo\n", encoding="utf-8")
    with pytest.raises(ValueError, match="label"):
        read_frame(path)
