"""Model request/response API agar kontraknya eksplisit."""

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("teks tidak boleh kosong")
        return stripped


class PredictResponse(BaseModel):
    label: str
    score: float
    bully_probability: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
