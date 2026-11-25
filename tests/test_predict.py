import json
from pathlib import Path

import pytest

from cyberbully.predict import load_threshold


def test_load_threshold_from_model_dir(tmp_path: Path) -> None:
    (tmp_path / "threshold.json").write_text(json.dumps({"threshold": 0.42}))
    assert load_threshold(tmp_path) == pytest.approx(0.42)


def test_load_threshold_defaults_to_half(tmp_path: Path) -> None:
    assert load_threshold(tmp_path) == 0.5


def test_load_threshold_rejects_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "threshold.json").write_text("{not json")
    with pytest.warns(RuntimeWarning):
        assert load_threshold(tmp_path) == 0.5


def test_load_threshold_rejects_out_of_range(tmp_path: Path) -> None:
    (tmp_path / "threshold.json").write_text(json.dumps({"threshold": 1.5}))
    with pytest.warns(RuntimeWarning):
        assert load_threshold(tmp_path) == 0.5
