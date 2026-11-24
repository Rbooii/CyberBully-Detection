from pathlib import Path

import pytest

from scripts.reset_generated import _ensure_within, collect_targets, remove_targets


def make_root(tmp_path: Path) -> Path:
    for relative in ("models", "out", "data/processed", "data/synthetic"):
        (tmp_path / relative).mkdir(parents=True)
    (tmp_path / "data/raw").mkdir(parents=True)
    (tmp_path / "data/eval").mkdir(parents=True)
    (tmp_path / "interface/node_modules/pkg").mkdir(parents=True)
    (tmp_path / "interface/dist").mkdir(parents=True)

    (tmp_path / "models/model.bin").write_text("model")
    (tmp_path / "models/.gitkeep").write_text("")
    (tmp_path / "out/metrics.json").write_text("{}")
    (tmp_path / "out/.gitkeep").write_text("")
    (tmp_path / "data/processed/train.csv").write_text("text,label\n")
    (tmp_path / "data/processed/.gitkeep").write_text("")
    (tmp_path / "data/synthetic/synthetic.csv").write_text("text,label\n")
    (tmp_path / "data/synthetic/README.md").write_text("readme")
    (tmp_path / "data/synthetic/.gitkeep").write_text("")
    (tmp_path / "data/raw/re_dataset.csv").write_text("raw")
    (tmp_path / "data/eval/implicit_eval.csv").write_text("eval")
    (tmp_path / "interface/node_modules/pkg/index.js").write_text("js")
    (tmp_path / "interface/dist/index.html").write_text("html")
    return tmp_path


def test_collect_only_generated_artifacts(tmp_path) -> None:
    root = make_root(tmp_path)
    names = {path.relative_to(root).as_posix() for path in collect_targets(root)}

    assert names == {
        "models/model.bin",
        "out/metrics.json",
        "data/processed/train.csv",
        "data/synthetic/synthetic.csv",
        "interface/node_modules",
        "interface/dist",
    }


def test_remove_keeps_raw_eval_and_gitkeep(tmp_path) -> None:
    root = make_root(tmp_path)
    remove_targets(collect_targets(root), root)

    assert not (root / "models/model.bin").exists()
    assert not (root / "data/synthetic/synthetic.csv").exists()
    assert not (root / "interface/node_modules").exists()
    assert not (root / "interface/dist").exists()

    assert (root / "models/.gitkeep").exists()
    assert (root / "data/processed/.gitkeep").exists()
    assert (root / "data/synthetic/README.md").exists()
    assert (root / "data/raw/re_dataset.csv").exists()
    assert (root / "data/eval/implicit_eval.csv").exists()


def test_empty_root_has_no_targets(tmp_path) -> None:
    assert collect_targets(tmp_path) == []


def test_refuses_path_outside_root(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="di luar repo"):
        _ensure_within(tmp_path.parent / "outside.txt", tmp_path)
