"""Gabungkan train asli dengan data sintetis, tanpa menyentuh val/test."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from cyberbully.config import DATA_EVAL, DATA_PROCESSED, DATA_SYNTHETIC, SEED
from cyberbully.data import read_frame, read_split
from cyberbully.synthetic import build_augmented_train, check_synthetic


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--synthetic",
        type=Path,
        default=DATA_SYNTHETIC / "synthetic_train.csv",
    )
    parser.add_argument("--out", type=Path, default=DATA_PROCESSED / "train_augmented.csv")
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    real_train = read_split(DATA_PROCESSED, "train")
    real_val = read_split(DATA_PROCESSED, "val")
    real_test = read_split(DATA_PROCESSED, "test")
    synthetic = read_frame(args.synthetic)

    eval_frame = None
    eval_path = DATA_EVAL / "implicit_eval.csv"
    if eval_path.exists():
        eval_frame = read_frame(eval_path)

    check_synthetic(synthetic, {"train": real_train, "val": real_val, "test": real_test}, eval_frame)

    augmented = build_augmented_train(
        real_train,
        synthetic,
        real_val,
        real_test,
        eval_frame=eval_frame,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    augmented.to_csv(args.out, index=False)

    print(f"train augmented: {len(augmented)} baris -> {args.out}")
    print(augmented["source"].value_counts().to_string())
    print(augmented["label"].value_counts().sort_index().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
