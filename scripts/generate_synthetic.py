"""Buat data sintetis untuk augmentasi train (bukan eval/test)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from cyberbully.config import DATA_EVAL, DATA_PROCESSED, DATA_SYNTHETIC, SEED
from cyberbully.data import read_frame, read_split
from cyberbully.synthetic import check_synthetic, generate_synthetic


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DATA_SYNTHETIC / "synthetic_train.csv",
    )
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--skip-check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    frame = generate_synthetic(seed=args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    print(f"dataset sintetis: {len(frame)} baris -> {args.out}")
    print(frame["category"].value_counts().to_string())

    if not args.skip_check:
        real_frames = {}
        for name in ("train", "val", "test"):
            try:
                real_frames[name] = read_split(DATA_PROCESSED, name)
            except FileNotFoundError:
                print(f"split {name} belum ada; cek overlap dilewati untuk split itu")
        eval_frame = None
        eval_path = DATA_EVAL / "implicit_eval.csv"
        if eval_path.exists():
            eval_frame = read_frame(eval_path)
        report = check_synthetic(frame, real_frames, eval_frame)
        print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
