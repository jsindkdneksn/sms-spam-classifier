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
