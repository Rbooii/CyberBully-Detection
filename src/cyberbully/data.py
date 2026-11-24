"""Muat, petakan label, deduplikasi, dan split dataset tanpa leakage."""

from __future__ import annotations

import argparse
import warnings
from functools import reduce
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd
from sklearn.model_selection import train_test_split

from .config import DATA_PROCESSED, LABEL_COLUMN, SEED, SPLIT_RATIOS, TEXT_COLUMN
from .preprocess import normalize_text

_REPLACEMENT_CHAR = "\ufffd"


def read_csv_auto(path: Path, encoding: str = "auto") -> pd.DataFrame:
    """Baca CSV dengan encoding eksplisit atau deteksi aman UTF-8.

    Mode ``auto`` mencoba UTF-8 strict, lalu UTF-8 dengan karakter rusak
    diganti. Tidak jatuh ke latin-1 karena itu membuat teks UTF-8 yang valid
    justru menjadi mojibake.
    """
    if encoding != "auto":
        return pd.read_csv(path, encoding=encoding)

    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        pass

    df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    broken = int(df.astype(str).apply(lambda col: col.str.count(_REPLACEMENT_CHAR)).sum().sum())
    warnings.warn(
        f"{path.name}: {broken} karakter bukan UTF-8 valid diganti '?' "
        "(encoding='auto'). Periksa sumber data bila jumlahnya besar.",
        RuntimeWarning,
        stacklevel=2,
    )
    return df


def load_csv(
    path: Path,
    text_col: str,
    label_col: str | Sequence[str],
    *,
    keep_cols: Sequence[str] = (),
    encoding: str = "auto",
) -> pd.DataFrame:
    """Baca CSV dan sisakan kolom teks, kolom label, serta kolom pendukung."""
    label_cols = [label_col] if isinstance(label_col, str) else list(label_col)
    df = read_csv_auto(path, encoding)

    columns = list(dict.fromkeys([text_col, *label_cols, *keep_cols]))
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Kolom tidak ditemukan: {', '.join(missing)}")

    df = df[columns].dropna(subset=[text_col, *label_cols])
    df[text_col] = df[text_col].astype(str)
    return df.rename(columns={text_col: TEXT_COLUMN})


def map_labels(
    df: pd.DataFrame,
    positive: Sequence[str],
    label_cols: Sequence[str] | None = None,
    mode: str = "any",
) -> pd.DataFrame:
    """Gabungkan kolom label menjadi 0/1; nilai di `positive` dianggap bully."""
    if not positive:
        raise ValueError("minimal satu nilai --positive wajib diberikan")
    if mode not in {"any", "all"}:
        raise ValueError("mode label harus 'any' atau 'all'")

    label_cols = list(label_cols) if label_cols is not None else [LABEL_COLUMN]
    positive_values = {str(value).strip().casefold() for value in positive}
    matches: list[pd.Series] = []

    for column in label_cols:
        if column not in df.columns:
            raise ValueError(f"Kolom label tidak ditemukan: {column}")
        values = df[column].astype(str).str.strip().str.casefold()
        unknown = set(values.unique()) - positive_values
        if len(unknown) > 1:
            raise ValueError(
                f"kolom '{column}' memuat lebih dari dua nilai "
                f"({', '.join(sorted(unknown | positive_values))}); "
                "petakan eksplisit sebelum melanjutkan"
            )
        matches.append(values.isin(positive_values))

    combined = reduce(lambda left, right: left & right, matches) if mode == "all" else reduce(
        lambda left, right: left | right, matches
    )

    result = df.copy()
    result[LABEL_COLUMN] = combined.astype(int)
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
            raise ValueError(
                f"data leakage: {len(overlap)} teks muncul di {first} dan {second}"
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


def read_frame(path: Path) -> pd.DataFrame:
    """Baca CSV berlabel dan pastikan kolom teks serta label ada."""
    if not path.exists():
        raise FileNotFoundError(f"{path} tidak ada")

    frame = pd.read_csv(path)
    missing = {TEXT_COLUMN, LABEL_COLUMN} - set(frame.columns)
    if missing:
        raise ValueError(f"{path} kehilangan kolom: {', '.join(sorted(missing))}")
    return frame


def read_split(data_dir: Path, name: str) -> pd.DataFrame:
    """Baca salah satu split hasil `prepare` dan pastikan kolomnya lengkap."""
    path = data_dir / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} tidak ada; jalankan `python -m cyberbully.data` dulu"
        )
    return read_frame(path)


def stratified_subset(
    frame: pd.DataFrame,
    size: int | None,
    seed: int = SEED,
) -> pd.DataFrame:
    """Ambil subset stratifikasi untuk smoke test tanpa mengubah split asli."""
    if size is None or size >= len(frame):
        return frame
    if LABEL_COLUMN not in frame or frame[LABEL_COLUMN].value_counts().min() < 2:
        return frame.sample(n=size, random_state=seed).reset_index(drop=True)

    try:
        sampled, _ = train_test_split(
            frame,
            train_size=size,
            random_state=seed,
            stratify=frame[LABEL_COLUMN],
        )
    except ValueError:
        sampled = frame.sample(n=size, random_state=seed)
    return sampled.reset_index(drop=True)


def prepare(
    input_path: Path,
    text_col: str,
    label_col: str | Sequence[str],
    positive: Sequence[str],
    out_dir: Path = DATA_PROCESSED,
    seed: int = SEED,
    *,
    keep_cols: Sequence[str] = (),
    encoding: str = "auto",
    label_mode: str = "any",
) -> dict[str, pd.DataFrame]:
    """Jalankan seluruh alur data: load, map label, dedup, split, simpan."""
    label_cols = [label_col] if isinstance(label_col, str) else list(label_col)
    raw = load_csv(
        input_path,
        text_col,
        label_cols,
        keep_cols=keep_cols,
        encoding=encoding,
    )
    mapped = map_labels(raw, positive, label_cols=label_cols, mode=label_mode)
    cleaned = dedup(mapped)

    final_columns = [TEXT_COLUMN, LABEL_COLUMN]
    final_columns += [column for column in keep_cols if column not in final_columns]
    cleaned = cleaned[final_columns]

    splits = split_dataset(cleaned, seed=seed)
    save_splits(splits, out_dir=out_dir)
    return splits


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV dataset mentah")
    parser.add_argument("--text-col", required=True, help="nama kolom teks")
    parser.add_argument(
        "--label-col",
        nargs="+",
        required=True,
        help="satu atau beberapa kolom label (digabung sesuai --label-mode)",
    )
    parser.add_argument(
        "--positive",
        nargs="+",
        required=True,
        help="satu atau beberapa nilai label yang berarti bully",
    )
    parser.add_argument("--label-mode", choices=("any", "all"), default="any")
    parser.add_argument(
        "--keep-cols",
        nargs="*",
        default=[],
        help="kolom tambahan yang disimpan untuk analisis (mis. HS Abusive)",
    )
    parser.add_argument(
        "--encoding",
        default="auto",
        help="encoding CSV; default auto (UTF-8, ganti byte rusak)",
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
        keep_cols=args.keep_cols,
        encoding=args.encoding,
        label_mode=args.label_mode,
    )

    print(f"dataset bersih: {sum(len(part) for part in splits.values())} baris")
    for name, part in splits.items():
        counts = part[LABEL_COLUMN].value_counts().sort_index().to_dict()
        print(f"  {name:5s} {len(part):4d} baris  label={counts}")
    print(f"output: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
