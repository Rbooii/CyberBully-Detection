"""FastAPI: POST /predict dan GET /health dengan model dimuat sekali saat startup."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Protocol

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from cyberbully.config import MODELS_DIR
from cyberbully.predict import Predictor

from .schemas import HealthResponse, PredictRequest, PredictResponse

DEFAULT_MODEL_DIR = Path(
    os.environ.get("CYBERBULLY_MODEL_DIR", MODELS_DIR / "indobert")
)
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


class PredictorLike(Protocol):
    def predict(self, text: str) -> dict[str, float | str]: ...


def create_app(
    model_dir: Path | None = None,
    predictor_factory: Callable[[Path], PredictorLike] = Predictor,
) -> FastAPI:
    """Buat aplikasi; factory dipakai test agar tidak memuat model asli."""
    resolved_model_dir = Path(model_dir) if model_dir is not None else DEFAULT_MODEL_DIR

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.predictor = None
        app.state.model_error = None
        try:
            app.state.predictor = predictor_factory(resolved_model_dir)
        except (FileNotFoundError, OSError) as exc:
            app.state.model_error = str(exc)
        yield

    app = FastAPI(
        title="CyberBully Detection API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            model_loaded=app.state.predictor is not None,
        )

    @app.post("/predict", response_model=PredictResponse)
    def predict(payload: PredictRequest) -> PredictResponse:
        if app.state.predictor is None:
            raise HTTPException(
                status_code=503,
                detail="Model belum tersedia; latih model terlebih dahulu.",
            )
        result = app.state.predictor.predict(payload.text)
        return PredictResponse(**result)

    return app


app = create_app()
