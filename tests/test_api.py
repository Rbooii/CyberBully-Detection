from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app


class FakePredictor:
    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir

    def predict(self, text: str) -> dict[str, float | str]:
        return {"label": "bully", "score": 0.92, "bully_probability": 0.92}


def test_health_without_model(tmp_path) -> None:
    app = create_app(model_dir=tmp_path / "missing")
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "model_loaded": False}


def test_predict_without_model_returns_503(tmp_path) -> None:
    app = create_app(model_dir=tmp_path / "missing")
    with TestClient(app) as client:
        response = client.post("/predict", json={"text": "dasar bodoh"})
        assert response.status_code == 503


def test_predict_with_fake_model(tmp_path) -> None:
    app = create_app(model_dir=tmp_path, predictor_factory=FakePredictor)
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["model_loaded"] is True

        response = client.post("/predict", json={"text": "dasar bodoh"})
        assert response.status_code == 200
        assert response.json()["label"] == "bully"
        assert 0.0 <= response.json()["bully_probability"] <= 1.0


def test_invalid_payload_returns_422(tmp_path) -> None:
    app = create_app(model_dir=tmp_path, predictor_factory=FakePredictor)
    with TestClient(app) as client:
        assert client.post("/predict", json={}).status_code == 422
        assert client.post("/predict", json={"text": "   "}).status_code == 422
        assert client.post("/predict", json={"text": "x" * 2_001}).status_code == 422


def test_cors_only_allows_dev_origin(tmp_path) -> None:
    app = create_app(model_dir=tmp_path, predictor_factory=FakePredictor)
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
