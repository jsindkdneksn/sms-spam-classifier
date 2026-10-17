"""Only load model artifacts from a trusted team-controlled source."""

import hashlib
import json
import math
import re
from pathlib import Path

import joblib


def verify_metadata(model_path: Path, metadata_path: Path, require_release: bool = False) -> dict:
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict) or not isinstance(meta.get("model_version"), str):
        raise ValueError("Invalid metadata")
    if not meta["model_version"].strip():
        raise ValueError("Empty model version")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if meta.get("model_sha256") != digest:
        raise ValueError("Model checksum mismatch")
    if require_release:
        # B's original DVC release predates artifact_kind. Accept that schema only
        # after the same full provenance checks, without changing the hashed files.
        if meta.get("artifact_kind") not in (None, "release") or meta["model_version"].startswith(
            "ci-test"
        ):
            raise ValueError("Production rejects test or unknown artifacts")
        if not re.fullmatch(r"[0-9a-f]{40}", str(meta.get("training_git_sha", ""))):
            raise ValueError("Missing actual training commit SHA")
        for key in ("dataset_hash", "dataset_version", "mlflow_run_id"):
            value = meta.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Missing provenance: {key}")
        if not isinstance(meta.get("metrics"), dict) or not meta["metrics"]:
            raise ValueError("Missing evaluation metrics")
        meta.setdefault("artifact_kind", "release")
    return meta


class Predictor:
    def __init__(self, model_path: Path, metadata_path: Path, require_release: bool = False):
        self.metadata = verify_metadata(model_path, metadata_path, require_release)
        self.model = joblib.load(model_path)
        if not callable(getattr(self.model, "predict", None)) or not callable(
            getattr(self.model, "predict_proba", None)
        ):
            raise ValueError("Model must support prediction and probabilities")
        classes = list(self.model.classes_)
        if len(classes) != 2 or set(classes) != {"ham", "spam"}:
            raise ValueError("Model classes must be ham and spam")
        self.spam_index = classes.index("spam")
        self.predict("startup readiness check")

    def predict(self, text: str) -> dict:
        label = str(self.model.predict([text])[0])
        probabilities = self.model.predict_proba([text])[0]
        probability = float(probabilities[self.spam_index])
        if label not in {"ham", "spam"} or not math.isfinite(probability):
            raise ValueError("Invalid model output")
        if not 0 <= probability <= 1:
            raise ValueError("Invalid probability")
        return {
            "label": label,
            "spam_probability": probability,
            "model_version": self.metadata["model_version"],
        }
