import pytest
import torch

from cyberbully.runtime import (
    dataloader_workers,
    resolve_device,
    seed_everything,
    supports_fp16,
)


def test_resolve_explicit_cpu() -> None:
    assert resolve_device("cpu").type == "cpu"


def test_resolve_auto_picks_available_device() -> None:
    assert resolve_device("auto").type in {"cuda", "mps", "cpu"}


def test_resolve_missing_cuda_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="CUDA"):
        resolve_device("cuda")


def test_fp16_only_on_cuda() -> None:
    assert supports_fp16(torch.device("cuda")) is True
    assert supports_fp16(torch.device("mps")) is False
    assert supports_fp16(torch.device("cpu")) is False


def test_workers_zero_on_non_cuda() -> None:
    assert dataloader_workers(torch.device("mps")) == 0
    assert dataloader_workers(torch.device("cpu")) == 0
    assert dataloader_workers(torch.device("cuda")) == 2


def test_seed_everything_is_deterministic() -> None:
    seed_everything(123)
    first = torch.rand(3)
    seed_everything(123)
    assert torch.equal(first, torch.rand(3))
