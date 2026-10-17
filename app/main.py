import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.predictor import Predictor
from app.schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)


def create_app(
    model_path: Path | None = None,
    metadata_path: Path | None = None,
    environment: str | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(api: FastAPI):
        api.state.predictor = None
        env = environment or os.getenv("APP_ENV", "development")
        api.state.environment = env
        try:
            api.state.predictor = Predictor(
                model_path or Path(os.getenv("MODEL_PATH", "models/release/model.joblib")),
                metadata_path
                or Path(os.getenv("MODEL_METADATA_PATH", "models/release/metadata.json")),
                require_release=env in {"staging", "production"},
            )
        except Exception as exc:
            # Avoid leaking filesystem details or credentials through API responses.
            logger.error("Model unavailable (%s)", type(exc).__name__)
        yield

    api = FastAPI(title="SMS Spam Classifier", version="0.1.0", lifespan=lifespan)

    @api.get("/", include_in_schema=False)
    def index():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @api.get("/health")
    def health():
        predictor = api.state.predictor
        if predictor is None:
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return {
            "status": "ok",
            "model_version": predictor.metadata["model_version"],
            "artifact_kind": predictor.metadata.get("artifact_kind", "unspecified"),
            "environment": api.state.environment,
        }

    @api.post("/predict", response_model=PredictionResponse)
    def predict(request: PredictionRequest):
        predictor = api.state.predictor
        if predictor is None:
            raise HTTPException(status_code=503, detail="Model is unavailable")
        try:
            return predictor.predict(request.text)
        except Exception as exc:
            logger.error("Prediction failed (%s)", type(exc).__name__)
            raise HTTPException(status_code=503, detail="Prediction is unavailable") from None

    return api


app = create_app()
