"""Baseline TF-IDF + Logistic Regression sebagai pembanding IndoBERT."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .config import DATA_PROCESSED, LABEL_COLUMN, MODELS_DIR, OUT_DIR, SEED, TEXT_COLUMN
from .data import read_split, stratified_subset
from .metrics import binary_metrics, choose_threshold


def build_pipeline(c_value: float, seed: int) -> Pipeline:
    """Bangun pipeline TF-IDF 1–2 gram + Logistic Regression berbobot kelas."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=100_000,
                    sublinear_tf=True,
                    lowercase=False,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=c_value,
                    class_weight="balanced",
                    solver="liblinear",
                    max_iter=2_000,
                    random_state=seed,
                ),
            ),
        ]
    )


def top_features(pipeline: Pipeline, limit: int = 25) -> dict[str, list[str]]:
    """Ambil fitur dengan koefisien paling positif dan paling negatif."""
    vectorizer: TfidfVectorizer = pipeline.named_steps["tfidf"]
    classifier: LogisticRegression = pipeline.named_steps["classifier"]
    names = vectorizer.get_feature_names_out()
    coefficients = classifier.coef_[0]
    order = np.argsort(coefficients)

    return {
        "bully": [str(names[index]) for index in order[::-1][:limit]],
        "non_bully": [str(names[index]) for index in order[:limit]],
    }


def train_baseline(
    train_frame: pd.DataFrame,
    val_frame: pd.DataFrame,
    c_grid: Sequence[float] = (0.1, 0.5, 1.0, 2.0, 5.0),
    seed: int = SEED,
) -> tuple[Pipeline, dict[str, object], dict[str, list[str]]]:
    """Latih kandidat C, pilih F1 terbaik dari validation, lalu tuning threshold."""
    if not c_grid:
        raise ValueError("c_grid tidak boleh kosong")

    candidates: dict[str, dict[str, float | int | list[list[int]]]] = {}
    best_pipeline: Pipeline | None = None
    best_c = float(c_grid[0])
    best_f1 = -1.0

    for c_value in c_grid:
        pipeline = build_pipeline(float(c_value), seed)
        pipeline.fit(train_frame[TEXT_COLUMN], train_frame[LABEL_COLUMN])
        probabilities = pipeline.predict_proba(val_frame[TEXT_COLUMN])[:, 1]
        metrics = binary_metrics(
            val_frame[LABEL_COLUMN].to_numpy(), probabilities, threshold=0.5
        )
        candidates[str(c_value)] = metrics
        if metrics["f1_bully"] > best_f1:
            best_c = float(c_value)
            best_f1 = float(metrics["f1_bully"])
            best_pipeline = pipeline

    if best_pipeline is None:
        raise RuntimeError("tidak ada kandidat baseline yang berhasil dilatih")

    val_probabilities = best_pipeline.predict_proba(val_frame[TEXT_COLUMN])[:, 1]
    tuned = choose_threshold(val_frame[LABEL_COLUMN].to_numpy(), val_probabilities)
    threshold = float(tuned["threshold"])

    payload: dict[str, object] = {
        "model": "tfidf+logreg",
        "seed": seed,
        "rows": {"train": len(train_frame), "val": len(val_frame)},
        "c_grid": [float(value) for value in c_grid],
        "candidates_at_0.5": candidates,
        "best_c": best_c,
        "threshold": threshold,
        "val": tuned["metrics"],
        "val_predictions": val_probabilities,
    }
    return best_pipeline, payload, top_features(best_pipeline)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_PROCESSED)
    parser.add_argument(
        "--model-out", type=Path, default=MODELS_DIR / "baseline_tfidf.joblib"
    )
    parser.add_argument("--metrics-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--subset", type=int, default=None)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--c-grid",
        nargs="+",
        type=float,
        default=[0.1, 0.5, 1.0, 2.0, 5.0],
    )
    parser.add_argument("--eval-test", action="store_true")
    parser.add_argument("--confirm-test", action="store_true")
    parser.add_argument("--allow-rerun-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point CLI `python -m cyberbully.baseline`."""
    args = _parse_args(argv)

    test_path = args.metrics_dir / "baseline_test.json"
    if args.eval_test:
        if not args.confirm_test:
            print("test butuh --confirm-test; evaluasi test hanya sekali untuk laporan.")
            return 2
        if test_path.exists() and not args.allow_rerun_test:
            print(f"{test_path} sudah ada; butuh --allow-rerun-test dan alasan jelas.")
            return 2

    train_frame = stratified_subset(read_split(args.data_dir, "train"), args.subset, args.seed)
    val_frame = read_split(args.data_dir, "val")

    pipeline, payload, features = train_baseline(
        train_frame, val_frame, c_grid=args.c_grid, seed=args.seed
    )
    probabilities = np.asarray(payload.pop("val_predictions"))

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, args.model_out)
    _write_json(args.metrics_dir / "baseline_val.json", payload)
    _write_json(args.metrics_dir / "baseline_top_features.json", features)

    predictions = val_frame.copy()
    predictions["probability"] = probabilities
    predictions["prediction"] = (probabilities >= float(payload["threshold"])).astype(int)
    predictions.to_csv(args.metrics_dir / "baseline_val_predictions.csv", index=False)

    print(json.dumps(payload, indent=2))
    print(f"model: {args.model_out}")
    print(f"metrik: {args.metrics_dir / 'baseline_val.json'}")

    if args.eval_test:
        test_frame = read_split(args.data_dir, "test")
        test_probabilities = pipeline.predict_proba(test_frame[TEXT_COLUMN])[:, 1]
        test_metrics = binary_metrics(
            test_frame[LABEL_COLUMN].to_numpy(),
            test_probabilities,
            threshold=float(payload["threshold"]),
        )
        test_payload = {
            "threshold": float(payload["threshold"]),
            "metrics": test_metrics,
            "model": "tfidf+logreg",
        }
        _write_json(test_path, test_payload)
        test_predictions = test_frame.copy()
        test_predictions["probability"] = test_probabilities
        test_predictions["prediction"] = (
            test_probabilities >= float(payload["threshold"])
        ).astype(int)
        test_predictions.to_csv(
            args.metrics_dir / "baseline_test_predictions.csv", index=False
        )
        print(json.dumps(test_payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
