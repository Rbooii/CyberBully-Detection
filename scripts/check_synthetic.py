"""Validasi data sintetis sebelum dipakai training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from cyberbully.config import DATA_EVAL, DATA_PROCESSED, DATA_SYNTHETIC
from cyberbully.data import read_frame, read_split
from cyberbully.synthetic import check_synthetic


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_SYNTHETIC / "synthetic_train.csv",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    frame = read_frame(args.input)
    if "category" not in frame.columns:
        raise ValueError(f"{args.input} tidak punya kolom category")

    real_frames = {}
    for name in ("train", "val", "test"):
        try:
            real_frames[name] = read_split(DATA_PROCESSED, name)
        except FileNotFoundError:
            print(f"split {name} belum ada; dilewati")

    eval_frame = None
    eval_path = DATA_EVAL / "implicit_eval.csv"
    if eval_path.exists():
        eval_frame = read_frame(eval_path)

    try:
        report = check_synthetic(frame, real_frames, eval_frame)
    except ValueError as error:
        print(f"GAGAL: {error}")
        return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
