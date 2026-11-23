"""Deteksi device dan pengaturan runtime untuk Mac (MPS) dan Colab (CUDA)."""

from __future__ import annotations

import os
import random
import warnings

import numpy as np
import torch


def resolve_device(choice: str = "auto") -> torch.device:
    """Pilih device: CUDA (Colab) > MPS (Mac) > CPU, atau paksa lewat `choice`."""
    if choice != "auto":
        device = torch.device(choice)
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("device cuda diminta, tapi CUDA tidak tersedia")
        if device.type == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("device mps diminta, tapi MPS tidak tersedia")
        return device

    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def seed_everything(seed: int) -> None:
    """Set seed Python, NumPy, dan PyTorch agar run bisa direproduksi."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def supports_fp16(device: torch.device) -> bool:
    """fp16 hanya untuk CUDA; MPS dan CPU memakai float32."""
    return device.type == "cuda"


def dataloader_workers(device: torch.device) -> int:
    """MPS butuh 0 worker; CUDA boleh paralel."""
    return 2 if device.type == "cuda" else 0


def warn_if_mps_without_fallback(device: torch.device) -> None:
    """Ingatkan fallback MPS sebelum operasi yang tidak didukung muncul."""
    if device.type == "mps" and os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") != "1":
        warnings.warn(
            "MPS aktif tanpa PYTORCH_ENABLE_MPS_FALLBACK=1; "
            "jalankan `export PYTORCH_ENABLE_MPS_FALLBACK=1` sebelum training.",
            RuntimeWarning,
            stacklevel=3,
        )
