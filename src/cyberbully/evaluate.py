"""Evaluasi model pada validation, test (sekali), dan eval set manual."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import pandas as pd

from .config import (
    DATA_EVAL,
    DATA_PROCESSED,
    LABEL_COLUMN,
    MAX_LENGTH,
    MODELS_DIR,
    OUT_DIR,
    TEXT_COLUMN,
)
from .metrics import binary_metrics
from .predict import Predictor


def _read_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} tidak ada; jalankan `python -m cyberbully.data` dulu"
        )
    frame = pd.read_csv(path)
    missing = {TEXT_COLUMN, LABEL_COLUMN} - set(frame.columns)
    if missing:
        raise ValueError(f"{path} kehilangan kolom: {', '.join(sorted(missing))}")
    labels = set(frame[LABEL_COLUMN].unique())
    if not labels <= {0, 1}:
        raise ValueError(
            f"{path} memuat label selain 0/1: {sorted(labels)}; petakan dulu"
        )
    return frame.reset_index(drop=True)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _evaluate_implicit(
    predictor: Predictor,
    path: Path,
    threshold: float,
) -> dict[str, object] | None:
    if not path.exists():
        print(f"eval set manual tidak ada ({path}); dilewati")
        return None

    frame = pd.read_csv(path)
    missing = {TEXT_COLUMN, LABEL_COLUMN} - set(frame.columns)
    if missing:
        raise ValueError(f"{path} kehilangan kolom: {', '.join(sorted(missing))}")

    labels = set(frame[LABEL_COLUMN].unique())
    if not labels <= {0, 1}:
        raise ValueError(f"{path} memuat label selain 0/1: {sorted(labels)}")

    frame = frame.reset_index(drop=True)
    probabilities = predictor.predict_proba(frame[TEXT_COLUMN].tolist())
    result: dict[str, object] = {
        "overall": binary_metrics(frame[LABEL_COLUMN].to_numpy(), probabilities, threshold)
    }

    if "category" in frame.columns:
        per_category = {}
        for category, group in frame.groupby("category"):
            group_probs = [
                probabilities[index] for index in group.index.to_numpy()
            ]
            per_category[str(category)] = binary_metrics(
                group[LABEL_COLUMN].to_numpy(), group_probs, threshold
            )
        result["per_category"] = per_category

    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=MODELS_DIR / "indobert")
    parser.add_argument("--data-dir", type=Path, default=DATA_PROCESSED)
    parser.add_argument("--split", choices=("val", "test"), default="val")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    parser.add_argument("--max-length", type=int, default=MAX_LENGTH)
    parser.add_argument("--confirm-test", action="store_true")
    parser.add_argument("--allow-rerun-test", action="store_true")
    parser.add_argument("--implicit-eval", type=Path, default=DATA_EVAL / "implicit_eval.csv")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point CLI `python -m cyberbully.evaluate`."""
    args = _parse_args(argv)
    if args.threshold is not None and not 0.0 < args.threshold < 1.0:
        print("threshold harus di antara 0 dan 1.")
        return 2

    metrics_path = args.out_dir / f"{args.split}_metrics.json"
    if args.split == "test":
        if not args.confirm_test:
            print(
                "test set hanya boleh dievaluasi sekali untuk laporan. "
                "Tambahkan --confirm-test bila ini evaluasi final."
            )
            return 2
        if metrics_path.exists() and not args.allow_rerun_test:
            print(
                f"{metrics_path} sudah ada. Evaluasi test berikutnya butuh "
                "--allow-rerun-test dan alasan yang jelas di laporan."
            )
            return 2
        if args.threshold is None:
            print("test butuh --threshold dari validation, bukan 0.5 default.")
            return 2

    threshold = 0.5 if args.threshold is None else args.threshold
    frame = _read_frame(args.data_dir / f"{args.split}.csv")

    predictor = Predictor(
        args.model_dir,
        device=args.device,
        max_length=args.max_length,
        threshold=threshold,
    )
    probabilities = predictor.predict_proba(frame[TEXT_COLUMN].tolist())
    metrics = binary_metrics(frame[LABEL_COLUMN].to_numpy(), probabilities, threshold)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            TEXT_COLUMN: frame[TEXT_COLUMN].to_numpy(),
            LABEL_COLUMN: frame[LABEL_COLUMN].to_numpy(),
            "probability": probabilities,
            "prediction": (pd.Series(probabilities) >= threshold).astype(int),
        }
    ).to_csv(args.out_dir / f"{args.split}_predictions.csv", index=False)
    _write_json(metrics_path, metrics)

    print(json.dumps(metrics, indent=2))
    print(f"metrik disimpan di: {metrics_path}")

    implicit = _evaluate_implicit(predictor, args.implicit_eval, threshold)
    if implicit is not None:
        implicit_path = args.out_dir / "implicit_metrics.json"
        _write_json(implicit_path, implicit)
        print(f"eval set manual disimpan di: {implicit_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
