"""Fine-tuning IndoBERT untuk klasifikasi bully/non-bully di MPS atau CUDA."""

from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import torch
import transformers
from sklearn.utils.class_weight import compute_class_weight
from torch import nn
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

from .config import (
    BASE_MODEL,
    DATA_PROCESSED,
    LABEL_COLUMN,
    LABEL_NAMES,
    MAX_LENGTH,
    MODELS_DIR,
    ROOT,
    SEED,
    TEXT_COLUMN,
)
from .data import read_frame, read_split, stratified_subset
from .metrics import binary_metrics, probabilities_from_logits
from .runtime import (
    dataloader_workers,
    resolve_device,
    seed_everything,
    supports_fp16,
    warn_if_mps_without_fallback,
)


class TextClassificationDataset(Dataset):
    """Dataset PyTorch berisi input_ids, attention_mask, dan label."""

    def __init__(self, frame: pd.DataFrame, tokenizer, max_length: int) -> None:
        encoded = tokenizer(
            frame[TEXT_COLUMN].tolist(),
            truncation=True,
            max_length=max_length,
        )
        self.input_ids = encoded["input_ids"]
        self.attention_mask = encoded["attention_mask"]
        self.labels = frame[LABEL_COLUMN].astype(int).tolist()

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        return {
            "input_ids": torch.tensor(self.input_ids[index], dtype=torch.long),
            "attention_mask": torch.tensor(self.attention_mask[index], dtype=torch.long),
            "labels": torch.tensor(self.labels[index], dtype=torch.long),
        }


class WeightedLossTrainer(Trainer):
    """Trainer dengan cross-entropy berbobot untuk data imbalanced."""

    def __init__(self, class_weights: torch.Tensor, **kwargs) -> None:
        super().__init__(**kwargs)
        self.class_weights = class_weights

    def compute_loss(
        self, model, inputs, return_outputs=False, num_items_in_batch=None
    ):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        weights = self.class_weights.to(outputs.logits.device)
        loss = nn.functional.cross_entropy(outputs.logits, labels, weight=weights)
        return (loss, outputs) if return_outputs else loss


def _compute_metrics(eval_pred) -> dict[str, float | int | list[list[int]]]:
    logits = np.asarray(eval_pred.predictions)
    labels = np.asarray(eval_pred.label_ids)
    return binary_metrics(labels, probabilities_from_logits(logits), threshold=0.5)


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=BASE_MODEL)
    parser.add_argument("--data-dir", type=Path, default=DATA_PROCESSED)
    parser.add_argument(
        "--train-file",
        type=Path,
        default=None,
        help="CSV train alternatif, mis. data/processed/train_augmented.csv",
    )
    parser.add_argument("--out", type=Path, default=MODELS_DIR / "indobert")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--eval-batch-size", type=int, default=32)
    parser.add_argument("--grad-accum", type=int, default=1)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=MAX_LENGTH)
    parser.add_argument("--subset", type=int, default=None)
    parser.add_argument("--class-weights", action="store_true")
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    parser.add_argument(
        "--fp16",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="default: aktif hanya di CUDA",
    )
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--logging-steps", type=int, default=25)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point CLI `python -m cyberbully.train`."""
    args = _parse_args(argv)
    seed_everything(args.seed)

    device = resolve_device(args.device)
    warn_if_mps_without_fallback(device)

    use_fp16 = supports_fp16(device) if args.fp16 is None else args.fp16
    if use_fp16 and not supports_fp16(device):
        raise ValueError("fp16 hanya didukung di CUDA, bukan MPS/CPU")

    train_source = read_frame(args.train_file) if args.train_file else read_split(args.data_dir, "train")
    train_frame = stratified_subset(train_source, args.subset, args.seed)
    val_frame = read_split(args.data_dir, "val")
    if train_frame.empty or val_frame.empty:
        raise ValueError("train atau val kosong; periksa hasil split")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model, num_labels=2)
    model.config.id2label = dict(LABEL_NAMES)
    model.config.label2id = {name: index for index, name in LABEL_NAMES.items()}

    train_dataset = TextClassificationDataset(train_frame, tokenizer, args.max_length)
    val_dataset = TextClassificationDataset(val_frame, tokenizer, args.max_length)

    class_weights = None
    if args.class_weights:
        weights = compute_class_weight(
            "balanced",
            classes=np.array([0, 1]),
            y=train_frame[LABEL_COLUMN].to_numpy(),
        )
        class_weights = torch.tensor(weights, dtype=torch.float32)

    steps_per_epoch = math.ceil(
        len(train_dataset) / (args.batch_size * args.grad_accum)
    )
    total_steps = max(1, int(steps_per_epoch * args.epochs))
    warmup_steps = max(1, int(total_steps * args.warmup_ratio))

    output_dir = args.out
    checkpoint_dir = output_dir / "checkpoints"
    training_args = TrainingArguments(
        output_dir=str(checkpoint_dir),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        warmup_steps=warmup_steps,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=args.logging_steps,
        load_best_model_at_end=True,
        metric_for_best_model="f1_bully",
        greater_is_better=True,
        save_total_limit=2,
        fp16=use_fp16,
        dataloader_num_workers=dataloader_workers(device),
        dataloader_pin_memory=device.type == "cuda",
        seed=args.seed,
        data_seed=args.seed,
        report_to=[],
        disable_tqdm=False,
    )

    trainer_class = WeightedLossTrainer if class_weights is not None else Trainer
    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": train_dataset,
        "eval_dataset": val_dataset,
        "data_collator": DataCollatorWithPadding(tokenizer),
        "processing_class": tokenizer,
        "compute_metrics": _compute_metrics,
    }
    if class_weights is not None:
        trainer = trainer_class(class_weights=class_weights, **trainer_kwargs)
    else:
        trainer = trainer_class(**trainer_kwargs)

    checkpoints = sorted(checkpoint_dir.glob("checkpoint-*"))
    resume_from = checkpoints[-1] if args.resume and checkpoints else None
    if args.resume and resume_from is None:
        print("--resume diberikan, tetapi tidak ada checkpoint; mulai dari awal")

    trainer.train(resume_from_checkpoint=resume_from)

    prediction = trainer.predict(val_dataset)
    probabilities = probabilities_from_logits(np.asarray(prediction.predictions))
    val_metrics = binary_metrics(
        val_frame[LABEL_COLUMN].to_numpy(), probabilities, threshold=0.5
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    predictions = val_frame.copy()
    predictions["probability"] = probabilities
    predictions["prediction"] = (probabilities >= 0.5).astype(int)
    predictions.to_csv(output_dir / "val_predictions.csv", index=False)

    _write_json(output_dir / "val_metrics.json", val_metrics)
    _write_json(output_dir / "train_log.json", {"log_history": trainer.state.log_history})

    run_meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "device": str(trainer.args.device),
        "fp16": use_fp16,
        "seed": args.seed,
        "max_length": args.max_length,
        "batch_size": args.batch_size,
        "train_file": str(args.train_file) if args.train_file else None,
        "grad_accum": args.grad_accum,
        "epochs": args.epochs,
        "learning_rate": args.lr,
        "class_weights": class_weights.tolist() if class_weights is not None else None,
        "subset": args.subset,
        "rows": {"train": len(train_frame), "val": len(val_frame)},
        "label_counts": {
            "train": train_frame[LABEL_COLUMN].value_counts().sort_index().to_dict(),
            "val": val_frame[LABEL_COLUMN].value_counts().sort_index().to_dict(),
        },
        "git_commit": _git_commit(),
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
    }
    _write_json(output_dir / "run_meta.json", run_meta)

    print(f"device: {trainer.args.device} | fp16: {use_fp16}")
    print(f"train: {len(train_frame)} baris | val: {len(val_frame)} baris")
    print(json.dumps(val_metrics, indent=2))
    print(f"model & metrik disimpan di: {output_dir}")
    print("test set belum disentuh; gunakan evaluate.py dengan threshold dari validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
