import pandas as pd

from cyberbully.evaluate import _drop_proposals


def test_drop_proposals_filters_unreviewed_rows() -> None:
    frame = pd.DataFrame(
        {
            "text": ["a", "b", "c"],
            "label": [1, 0, 1],
            "status": ["usulan", "final", "Usulan"],
        }
    )
    result = _drop_proposals(frame)
    assert len(result) == 1
    assert result["status"].iloc[0] == "final"


def test_drop_proposals_without_status_keeps_frame() -> None:
    frame = pd.DataFrame({"text": ["a"], "label": [1]})
    assert _drop_proposals(frame).equals(frame)
