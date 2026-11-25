"""Muat model sekali dan prediksi teks bully/non-bully."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Sequence

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .config import LABEL_NAMES, MAX_LENGTH
from .preprocess import normalize_text
from .runtime import resolve_device, warn_if_mps_without_fallback


def load_threshold(model_dir: Path) -> float:
    """Baca threshold beku dari folder model, fallback ke 0,5."""
    path = model_dir / "threshold.json"
    if not path.exists():
        return 0.5
    try:
        payload = json.loads(path.read_text())
        threshold = float(payload["threshold"])
    except (OSError, KeyError, TypeError, ValueError) as error:
        warnings.warn(
            f"threshold.json tidak valid ({error}); memakai 0.5",
            RuntimeWarning,
            stacklevel=2,
        )
        return 0.5
    if not 0.0 < threshold < 1.0:
        warnings.warn(
            "threshold.json di luar 0-1; memakai 0.5",
            RuntimeWarning,
            stacklevel=2,
        )
        return 0.5
    return threshold


class Predictor:
    """Wrapper inference: normalisasi teks, tokenisasi batch, dan softmax."""

    def __init__(
        self,
        model_dir: str | Path,
        device: str = "auto",
        max_length: int = MAX_LENGTH,
        threshold: float | None = None,
        batch_size: int = 32,
    ) -> None:
        model_path = Path(model_dir)
        if not model_path.exists():
            raise FileNotFoundError(
                f"model tidak ditemukan di {model_path}; jalankan training dulu"
            )
        if threshold is None:
            threshold = load_threshold(model_path)
        if not 0.0 < threshold < 1.0:
            raise ValueError("threshold harus di antara 0 dan 1")

        self.device = resolve_device(device)
        warn_if_mps_without_fallback(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = (
            AutoModelForSequenceClassification.from_pretrained(model_path)
            .to(self.device)
            .eval()
        )
        self.max_length = max_length
        self.threshold = threshold
        self.batch_size = batch_size

    @torch.inference_mode()
    def predict_proba(self, texts: Sequence[str]) -> list[float]:
        """Kembalikan probabilitas kelas bully untuk setiap teks."""
        cleaned = [normalize_text(text) for text in texts]
        probabilities: list[float] = []

        for start in range(0, len(cleaned), self.batch_size):
            batch = cleaned[start : start + self.batch_size]
            encoded = self.tokenizer(
                batch,
                truncation=True,
                max_length=self.max_length,
                padding=True,
                return_tensors="pt",
            )
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            logits = self.model(**encoded).logits
            batch_probs = torch.softmax(logits.float(), dim=-1)[:, 1]
            probabilities.extend(batch_probs.cpu().tolist())

        return probabilities

    def predict(self, text: str) -> dict[str, float | str]:
        """Prediksi satu teks dengan threshold yang tersimpan di instance."""
        if not text.strip():
            raise ValueError("teks tidak boleh kosong")

        probability = self.predict_proba([text])[0]
        label_id = int(probability >= self.threshold)
        return {
            "label": LABEL_NAMES[label_id],
            "score": float(max(probability, 1.0 - probability)),
            "bully_probability": float(probability),
        }
