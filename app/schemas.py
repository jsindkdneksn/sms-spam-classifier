from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: StrictStr

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not 1 <= len(cleaned) <= 5000:
            raise ValueError("Text must contain 1 to 5000 characters after trimming")
        return cleaned


class PredictionResponse(BaseModel):
    label: Literal["ham", "spam"]
    spam_probability: float = Field(ge=0, le=1, allow_inf_nan=False)
    model_version: str
