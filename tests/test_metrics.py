import pytest

from cyberbully.metrics import (
    binary_metrics,
    choose_threshold,
    probabilities_from_logits,
)


def test_binary_metrics_perfect() -> None:
    metrics = binary_metrics([0, 1, 1, 0], [0.1, 0.9, 0.8, 0.2])
    assert metrics["accuracy"] == 1.0
    assert metrics["precision_bully"] == 1.0
    assert metrics["recall_bully"] == 1.0
    assert metrics["f1_bully"] == 1.0
    assert metrics["confusion_matrix"] == [[2, 0], [0, 2]]


def test_binary_metrics_threshold_changes_predictions() -> None:
    labels = [1, 0]
    probabilities = [0.6, 0.4]
    assert binary_metrics(labels, probabilities, 0.5)["accuracy"] == 1.0
    assert binary_metrics(labels, probabilities, 0.7)["recall_bully"] == 0.0


def test_binary_metrics_handles_missing_predictions() -> None:
    metrics = binary_metrics([0, 0], [0.1, 0.2])
    assert metrics["f1_bully"] == 0.0
    assert metrics["precision_bully"] == 0.0


def test_probabilities_from_logits_matches_softmax() -> None:
    probs = probabilities_from_logits([[0.0, 0.0], [1000.0, 0.0]])
    assert probs[0] == pytest.approx(0.5)
    assert probs[1] == pytest.approx(0.0)


def test_choose_threshold_improves_over_default() -> None:
    labels = [1, 1, 0, 0]
    probabilities = [0.7, 0.6, 0.55, 0.3]
    result = choose_threshold(labels, probabilities)
    assert result["metrics"]["f1_bully"] > 0.9
    assert 0.5 < result["threshold"] < 0.7
    assert result["fallback"] is None


def test_choose_threshold_falls_back_at_grid_boundary() -> None:
    labels = [1, 1, 0, 0]
    probabilities = [0.02, 0.03, 0.0, 0.01]
    result = choose_threshold(labels, probabilities)
    assert result["threshold"] == 0.5
    assert result["fallback"] == "boundary"
