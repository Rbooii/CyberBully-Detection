"""Muat model sekali dan prediksi teks bully/non-bully."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .config import LABEL_NAMES, MAX_LENGTH
from .preprocess import normalize_text
from .runtime import resolve_device, warn_if_mps_without_fallback


class Predictor:
    """Wrapper inference: normalisasi teks, tokenisasi batch, dan softmax."""

    def __init__(
        self,
        model_dir: str | Path,
        device: str = "auto",
        max_length: int = MAX_LENGTH,
        threshold: float = 0.5,
        batch_size: int = 32,
    ) -> None:
        model_path = Path(model_dir)
        if not model_path.exists():
            raise FileNotFoundError(
                f"model tidak ditemukan di {model_path}; jalankan training dulu"
            )
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
