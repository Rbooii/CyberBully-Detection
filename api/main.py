"""FastAPI: bandingkan model A (real-only) dan B (real + sintetis)."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Literal, Mapping, Protocol

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from cyberbully.config import MODELS_DIR
from cyberbully.predict import Predictor

from .schemas import CompareResponse, HealthResponse, PredictRequest, PredictResponse

DEFAULT_MODEL_DIRS = {
    "a": Path(
        os.environ.get(
            "CYBERBULLY_MODEL_A",
            os.environ.get("CYBERBULLY_MODEL_DIR", MODELS_DIR / "indobert_real"),
        )
    ),
    "b": Path(os.environ.get("CYBERBULLY_MODEL_B", MODELS_DIR / "indobert_aug")),
}
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


class PredictorLike(Protocol):
    def predict(self, text: str) -> dict[str, float | str]: ...


def create_app(
    model_dirs: Mapping[str, Path] | None = None,
    predictor_factory: Callable[[Path], PredictorLike] = Predictor,
) -> FastAPI:
    """Buat aplikasi; factory dipakai test agar tidak memuat model asli."""
    resolved_dirs = {
        key: Path(path)
        for key, path in (model_dirs or DEFAULT_MODEL_DIRS).items()
    }
    unknown = set(resolved_dirs) - {"a", "b"}
    if unknown:
        raise ValueError(f"model key tidak dikenal: {', '.join(sorted(unknown))}")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.predictors: dict[str, PredictorLike] = {}
        app.state.thresholds: dict[str, float | None] = {}
        app.state.model_errors: dict[str, str] = {}
        for key, path in resolved_dirs.items():
            try:
                predictor = predictor_factory(path)
                app.state.predictors[key] = predictor
                app.state.thresholds[key] = getattr(predictor, "threshold", None)
            except (FileNotFoundError, OSError, ValueError, RuntimeError) as exc:
                app.state.model_errors[key] = str(exc)
        yield

    app = FastAPI(
        title="CyberBully Detection API",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    def _predictor(key: str) -> PredictorLike:
        predictor = app.state.predictors.get(key)
        if predictor is None:
            raise HTTPException(
                status_code=503,
                detail=f"Model {key.upper()} belum tersedia; latih model terlebih dahulu.",
            )
        return predictor

    def _response(key: str, text: str) -> PredictResponse:
        predictor = _predictor(key)
        result = predictor.predict(text)
        threshold = app.state.thresholds.get(key)
        return PredictResponse(
            **result,
            threshold=0.5 if threshold is None else float(threshold),
        )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        models = {key: key in app.state.predictors for key in resolved_dirs}
        thresholds = {
            key: app.state.thresholds.get(key) for key in resolved_dirs
        }
        return HealthResponse(
            status="ok",
            model_loaded=any(models.values()),
            models=models,
            thresholds=thresholds,
        )

    @app.post("/predict", response_model=PredictResponse)
    def predict(
        payload: PredictRequest,
        model: Literal["a", "b"] = Query(default="a"),
    ) -> PredictResponse:
        return _response(model, payload.text)

    @app.post("/compare", response_model=CompareResponse)
    def compare(payload: PredictRequest) -> CompareResponse:
        missing = [key for key in ("a", "b") if key not in app.state.predictors]
        if missing:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Model belum lengkap untuk perbandingan: "
                    + ", ".join(key.upper() for key in missing)
                ),
            )
        return CompareResponse(
            a=_response("a", payload.text),
            b=_response("b", payload.text),
        )

    return app


app = create_app()
