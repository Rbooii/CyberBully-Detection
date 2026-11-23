"""Muat, petakan label, deduplikasi, dan split dataset tanpa leakage."""

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd
from sklearn.model_selection import train_test_split

from .config import DATA_PROCESSED, LABEL_COLUMN, SEED, SPLIT_RATIOS, TEXT_COLUMN
from .preprocess import normalize_text


def load_csv(path: Path, text_col: str, label_col: str) -> pd.DataFrame:
    """Baca CSV dan sisakan hanya kolom teks serta label, tanpa baris kosong."""
    df = pd.read_csv(path)
    missing = {text_col, label_col} - set(df.columns)
    if missing:
        raise ValueError(f"Kolom tidak ditemukan: {', '.join(sorted(missing))}")

    df = df[[text_col, label_col]].dropna()
    return df.rename(columns={text_col: TEXT_COLUMN, label_col: LABEL_COLUMN})


def map_labels(df: pd.DataFrame, positive: Sequence[str]) -> pd.DataFrame:
    """Petakan nilai label ke 0/1; semua nilai di `positive` menjadi kelas bully."""
    if not positive:
        raise ValueError("minimal satu nilai --positive wajib diberikan")

    result = df.copy()
    labels = result[LABEL_COLUMN].astype(str).str.strip().str.casefold()
    positive_values = {str(value).strip().casefold() for value in positive}

    unknown = set(labels.unique()) - positive_values
    if len(unknown) > 1:
        raise ValueError(
            "lebih dari dua nilai label ditemukan "
            f"({', '.join(sorted(unknown | positive_values))}); "
            "petakan eksplisit sebelum melanjutkan"
        )

    result[LABEL_COLUMN] = labels.isin(positive_values).astype(int)
    return result


def dedup(df: pd.DataFrame) -> pd.DataFrame:
    """Normalisasi teks lalu buang duplikat persis setelah normalisasi.

    Deduplikasi harus terjadi sebelum split supaya teks yang sama tidak
    muncul sekaligus di train dan test.
    """
    result = df.copy()
    result[TEXT_COLUMN] = result[TEXT_COLUMN].map(normalize_text)
    result = result[result[TEXT_COLUMN].str.len() > 0]
    result = result.drop_duplicates(subset=TEXT_COLUMN, keep="first")
    return result.reset_index(drop=True)


def validate_splits(splits: Mapping[str, pd.DataFrame]) -> None:
    """Pastikan tiap split terisi, punya kedua kelas, dan tidak beririsan."""
    expected = {"train", "val", "test"}
    if set(splits) != expected:
        raise ValueError(f"split harus {sorted(expected)}, bukan {sorted(splits)}")

    texts: dict[str, set[str]] = {}
    for name, part in splits.items():
        if part.empty:
            raise ValueError(f"split '{name}' kosong")
        if set(part[LABEL_COLUMN].unique()) != {0, 1}:
            raise ValueError(f"split '{name}' tidak memuat kedua kelas")
        texts[name] = set(part[TEXT_COLUMN])

    for first, second in combinations(sorted(texts), 2):
        overlap = texts[first] & texts[second]
        if overlap:
            sample = next(iter(overlap))
            raise ValueError(
                f"data leakage: {len(overlap)} teks muncul di "
                f"{first} dan {second} (contoh: {sample!r})"
            )


def split_dataset(
    df: pd.DataFrame,
    seed: int = SEED,
    ratios: tuple[float, float, float] = SPLIT_RATIOS,
) -> dict[str, pd.DataFrame]:
    """Split stratifikasi deterministik menjadi train/val/test."""
    train_ratio, val_ratio, test_ratio = ratios
    if round(train_ratio + val_ratio + test_ratio, 6) != 1.0:
        raise ValueError("total rasio split harus 1.0")
    if df[LABEL_COLUMN].value_counts().min() < 2:
        raise ValueError("tiap kelas butuh minimal 2 contoh agar bisa distratifikasi")

    train, rest = train_test_split(
        df,
        train_size=train_ratio,
        random_state=seed,
        stratify=df[LABEL_COLUMN],
    )
    val_share = val_ratio / (val_ratio + test_ratio)
    val, test = train_test_split(
        rest,
        train_size=val_share,
        random_state=seed,
        stratify=rest[LABEL_COLUMN],
    )

    splits = {
        "train": train.reset_index(drop=True),
        "val": val.reset_index(drop=True),
        "test": test.reset_index(drop=True),
    }
    validate_splits(splits)
    return splits


def save_splits(
    splits: Mapping[str, pd.DataFrame], out_dir: Path = DATA_PROCESSED
) -> dict[str, Path]:
    """Tulis tiap split ke CSV dan kembalikan path hasilnya."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, part in splits.items():
        path = out_dir / f"{name}.csv"
        part.to_csv(path, index=False)
        paths[name] = path
    return paths


def prepare(
    input_path: Path,
    text_col: str,
    label_col: str,
    positive: Sequence[str],
    out_dir: Path = DATA_PROCESSED,
    seed: int = SEED,
) -> dict[str, pd.DataFrame]:
    """Jalankan seluruh alur data: load, map label, dedup, split, simpan."""
    raw = load_csv(input_path, text_col, label_col)
    mapped = map_labels(raw, positive)
    cleaned = dedup(mapped)
    splits = split_dataset(cleaned, seed=seed)
    save_splits(splits, out_dir=out_dir)
    return splits


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV dataset mentah")
    parser.add_argument("--text-col", required=True, help="nama kolom teks")
    parser.add_argument("--label-col", required=True, help="nama kolom label")
    parser.add_argument(
        "--positive",
        nargs="+",
        required=True,
        help="satu atau beberapa nilai label yang berarti bully",
    )
    parser.add_argument("--out-dir", type=Path, default=DATA_PROCESSED)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point CLI `python -m cyberbully.data`."""
    args = _parse_args(argv)
    splits = prepare(
        input_path=args.input,
        text_col=args.text_col,
        label_col=args.label_col,
        positive=args.positive,
        out_dir=args.out_dir,
        seed=args.seed,
    )

    print(f"dataset bersih: {sum(len(part) for part in splits.values())} baris")
    for name, part in splits.items():
        counts = part[LABEL_COLUMN].value_counts().sort_index().to_dict()
        print(f"  {name:5s} {len(part):4d} baris  label={counts}")
    print(f"output: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
