"""Hapus artefak turunan (model, metrik, split, sintetis, node_modules).

Default adalah dry-run. Gunakan `--yes` untuk benar-benar menghapus. Data asli
(`data/raw`) dan eval set manual (`data/eval`) tidak pernah disentuh.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

# Isi folder yang dihapus, kecuali nama yang dipertahankan.
CONTENT_TARGETS: dict[str, set[str]] = {
    "models": {".gitkeep"},
    "out": {".gitkeep"},
    "data/processed": {".gitkeep"},
    "data/synthetic": {".gitkeep", "README.md"},
}

# Folder yang dihapus seluruhnya.
WHOLE_DIR_TARGETS = ("interface/node_modules", "interface/dist")


def _ensure_within(path: Path, root: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise RuntimeError(f"path di luar repo: {path}") from error


def _size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def collect_targets(root: Path = ROOT) -> list[Path]:
    """Kumpulkan path yang akan dihapus tanpa menyentuh data asli/eval."""
    targets: list[Path] = []

    for relative, keep in CONTENT_TARGETS.items():
        directory = root / relative
        if not directory.exists():
            continue
        if directory.is_symlink():
            raise RuntimeError(f"folder target berupa symlink: {directory}")
        for entry in sorted(directory.iterdir()):
            if entry.name in keep:
                continue
            if entry.is_symlink():
                raise RuntimeError(f"target berupa symlink: {entry}")
            _ensure_within(entry, root)
            targets.append(entry)

    for relative in WHOLE_DIR_TARGETS:
        directory = root / relative
        if not directory.exists():
            continue
        if directory.is_symlink():
            raise RuntimeError(f"folder target berupa symlink: {directory}")
        _ensure_within(directory, root)
        targets.append(directory)

    return targets


def remove_targets(targets: Sequence[Path], root: Path = ROOT) -> None:
    """Hapus path yang sudah dikumpulkan, tetap dengan pengecekan batas repo."""
    for path in targets:
        _ensure_within(path, root)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def _format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="benar-benar hapus")
    args = parser.parse_args(argv)

    targets = collect_targets()
    total = sum(_size(path) for path in targets)

    print(f"target: {len(targets)} path, {_format_size(total)}")
    for path in targets:
        print(f"  {path.relative_to(ROOT)} ({_format_size(_size(path))})")

    if not targets:
        print("tidak ada artefak yang perlu dihapus")
        return 0

    if not args.yes:
        print("\ndry-run: tidak ada yang dihapus. Tambahkan --yes untuk eksekusi.")
        return 0

    remove_targets(targets)
    print(f"\nselesai: {len(targets)} path dihapus")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"GAGAL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
