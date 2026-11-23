"""Metrik biner kelas bully dan pemilihan threshold dari validation set."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def probabilities_from_logits(logits: np.ndarray) -> np.ndarray:
    """Ubah logits [n, 2] menjadi probabilitas kelas bully (kolom 1)."""
    logits = np.asarray(logits, dtype=np.float64)
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return (exp / exp.sum(axis=1, keepdims=True))[:, 1]


def binary_metrics(
    labels: Sequence[int],
    probabilities: Sequence[float],
    threshold: float = 0.5,
) -> dict[str, float | int | list[list[int]]]:
    """Hitung accuracy, precision, recall, F1, dan confusion matrix kelas bully."""
    labels_array = np.asarray(labels, dtype=int)
    probs_array = np.asarray(probabilities, dtype=float)
    if labels_array.shape != probs_array.shape:
        raise ValueError("jumlah label dan probabilitas harus sama")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold harus di antara 0 dan 1")

    predictions = (probs_array >= threshold).astype(int)
    matrix = confusion_matrix(labels_array, predictions, labels=[0, 1])

    return {
        "threshold": float(threshold),
        "n": int(labels_array.size),
        "positives": int(labels_array.sum()),
        "accuracy": float(accuracy_score(labels_array, predictions)),
        "precision_bully": float(
            precision_score(labels_array, predictions, pos_label=1, zero_division=0)
        ),
        "recall_bully": float(
            recall_score(labels_array, predictions, pos_label=1, zero_division=0)
        ),
        "f1_bully": float(
            f1_score(labels_array, predictions, pos_label=1, zero_division=0)
        ),
        "confusion_matrix": matrix.tolist(),
    }


def choose_threshold(
    labels: Sequence[int],
    probabilities: Sequence[float],
    start: float = 0.05,
    stop: float = 0.95,
    step: float = 0.01,
) -> dict[str, float | dict[str, float | int | list[list[int]]]]:
    """Cari threshold dengan F1 bully terbaik pada validation set."""
    best_threshold = start
    best_metrics = binary_metrics(labels, probabilities, threshold=start)

    for threshold in np.arange(start, stop + step / 2, step):
        metrics = binary_metrics(labels, probabilities, threshold=float(threshold))
        if metrics["f1_bully"] > best_metrics["f1_bully"]:
            best_threshold = float(threshold)
            best_metrics = metrics

    return {"threshold": best_threshold, "metrics": best_metrics}
