import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.predictor import Predictor


def test_prediction_contract(client):
    response = client.post("/predict", json={"text": "see you at dinner"})
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"label", "spam_probability", "model_version"}
    assert data["label"] in {"ham", "spam"}
    assert 0 <= data["spam_probability"] <= 1
    assert data["model_version"] == client.get("/health").json()["model_version"]


@pytest.mark.parametrize("failure", ["missing", "corrupt", "checksum", "metadata"])
def test_bad_artifact_is_unavailable(model_dir, failure):
    model, metadata = model_dir / "model.joblib", model_dir / "metadata.json"
    if failure == "missing":
        model.unlink()
    elif failure == "corrupt":
        import hashlib

        model.write_bytes(b"not a joblib file")
        meta = json.loads(metadata.read_text())
        meta["model_sha256"] = hashlib.sha256(model.read_bytes()).hexdigest()
        metadata.write_text(json.dumps(meta))
    elif failure == "checksum":
        model.write_bytes(model.read_bytes() + b"unexpected")
    else:
        metadata.write_text("invalid json")
    with TestClient(create_app(model, metadata, "development")) as client:
        assert client.get("/health").status_code == 503
        response = client.post("/predict", json={"text": "hello"})
        assert response.status_code == 503
        assert str(model_dir) not in response.text


@pytest.mark.parametrize("env", ["staging", "production"])
def test_release_environments_reject_test_model(model_dir, env):
    with TestClient(create_app(model_dir / "model.joblib", model_dir / "metadata.json", env)) as c:
        assert c.get("/health").status_code == 503


def test_prediction_failure_returns_503(client, monkeypatch):
    def fail(_self, _text):
        raise ValueError("private internal detail")

    monkeypatch.setattr(Predictor, "predict", fail)
    response = client.post("/predict", json={"text": "hello"})
    assert response.status_code == 503
    assert "private internal" not in response.text


def test_page_and_docs(client):
    assert client.get("/").status_code == 200
    assert "英文短信" in client.get("/").text
    assert client.get("/docs").status_code == 200


@pytest.mark.parametrize("marker", [None, "release"])
def test_complete_legacy_and_current_release_metadata(model_dir, marker):
    path = model_dir / "metadata.json"
    metadata = json.loads(path.read_text())
    metadata.update(
        model_version="release-contract-fixture",
        training_git_sha="a" * 40,
        dataset_hash="b" * 32 + ".dir",
        dataset_version="dataset-v2",
        mlflow_run_id="c" * 32,
        metrics={"test_spam_f1": 0.9},
    )
    if marker is None:
        metadata.pop("artifact_kind")
    else:
        metadata["artifact_kind"] = marker
    path.write_text(json.dumps(metadata))
    original = path.read_bytes()
    predictor = Predictor(model_dir / "model.joblib", path, require_release=True)
    assert predictor.metadata["artifact_kind"] == "release"
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "missing", ["training_git_sha", "dataset_hash", "mlflow_run_id", "metrics"]
)
def test_legacy_metadata_cannot_bypass_provenance(model_dir, missing):
    path = model_dir / "metadata.json"
    metadata = json.loads(path.read_text())
    metadata.pop("artifact_kind")
    metadata.update(
        model_version="release-contract-fixture",
        training_git_sha="a" * 40,
        dataset_hash="b" * 32 + ".dir",
        dataset_version="dataset-v2",
        mlflow_run_id="c" * 32,
        metrics={"test_spam_f1": 0.9},
    )
    metadata.pop(missing)
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        Predictor(model_dir / "model.joblib", path, require_release=True)
