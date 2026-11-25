from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app


class FakePredictor:
    def __init__(self, model_dir: Path) -> None:
        if not model_dir.exists():
            raise FileNotFoundError(model_dir)
        self.model_dir = model_dir
        self.probability = 0.9 if "real" in model_dir.name else 0.2
        self.threshold = 0.42 if "real" in model_dir.name else 0.17

    def predict(self, text: str) -> dict[str, float | str]:
        label = "bully" if self.probability >= 0.5 else "non-bully"
        return {
            "label": label,
            "score": max(self.probability, 1 - self.probability),
            "bully_probability": self.probability,
        }


def test_health_without_models(tmp_path) -> None:
    app = create_app(
        model_dirs={
            "a": tmp_path / "missing_real",
            "b": tmp_path / "missing_aug",
        }
    )
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "model_loaded": False,
            "models": {"a": False, "b": False},
            "thresholds": {"a": None, "b": None},
        }


def test_predict_without_model_returns_503(tmp_path) -> None:
    app = create_app(
        model_dirs={
            "a": tmp_path / "missing_real",
            "b": tmp_path / "missing_aug",
        }
    )
    with TestClient(app) as client:
        response = client.post("/predict", json={"text": "dasar bodoh"})
        assert response.status_code == 503


def test_compare_returns_both_models(tmp_path) -> None:
    (tmp_path / "indobert_real").mkdir()
    (tmp_path / "indobert_aug").mkdir()
    app = create_app(
        model_dirs={
            "a": tmp_path / "indobert_real",
            "b": tmp_path / "indobert_aug",
        },
        predictor_factory=FakePredictor,
    )
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["model_loaded"] is True
        assert health["models"] == {"a": True, "b": True}
        assert health["thresholds"] == {"a": 0.42, "b": 0.17}

        response = client.post("/compare", json={"text": "dasar bodoh"})
        assert response.status_code == 200
        body = response.json()
        assert body["a"]["label"] == "bully"
        assert body["b"]["label"] == "non-bully"
        assert body["a"]["bully_probability"] == 0.9
        assert body["b"]["bully_probability"] == 0.2
        assert body["a"]["threshold"] == 0.42
        assert body["b"]["threshold"] == 0.17

        single = client.post("/predict?model=b", json={"text": "dasar bodoh"})
        assert single.status_code == 200
        assert single.json()["bully_probability"] == 0.2


def test_compare_requires_both_models(tmp_path) -> None:
    (tmp_path / "indobert_real").mkdir()
    app = create_app(
        model_dirs={
            "a": tmp_path / "indobert_real",
            "b": tmp_path / "missing_aug",
        },
        predictor_factory=FakePredictor,
    )
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["models"] == {"a": True, "b": False}
        assert health["thresholds"] == {"a": 0.42, "b": None}

        assert client.post("/predict?model=b", json={"text": "halo"}).status_code == 503
        assert client.post("/compare", json={"text": "halo"}).status_code == 503


def test_invalid_model_key_returns_422(tmp_path) -> None:
    (tmp_path / "indobert_real").mkdir()
    (tmp_path / "indobert_aug").mkdir()
    app = create_app(
        model_dirs={"a": tmp_path / "indobert_real", "b": tmp_path / "indobert_aug"},
        predictor_factory=FakePredictor,
    )
    with TestClient(app) as client:
        assert client.post("/predict?model=c", json={"text": "halo"}).status_code == 422


def test_invalid_payload_returns_422(tmp_path) -> None:
    (tmp_path / "indobert_real").mkdir()
    (tmp_path / "indobert_aug").mkdir()
    app = create_app(
        model_dirs={"a": tmp_path / "indobert_real", "b": tmp_path / "indobert_aug"},
        predictor_factory=FakePredictor,
    )
    with TestClient(app) as client:
        assert client.post("/predict", json={}).status_code == 422
        assert client.post("/predict", json={"text": "   "}).status_code == 422
        assert client.post("/predict", json={"text": "x" * 2_001}).status_code == 422


def test_cors_only_allows_dev_origin(tmp_path) -> None:
    (tmp_path / "indobert_real").mkdir()
    (tmp_path / "indobert_aug").mkdir()
    app = create_app(
        model_dirs={"a": tmp_path / "indobert_real", "b": tmp_path / "indobert_aug"},
        predictor_factory=FakePredictor,
    )
    with TestClient(app) as client:
        allowed = client.options(
            "/predict",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

        blocked = client.options(
            "/predict",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert blocked.headers.get("access-control-allow-origin") is None
