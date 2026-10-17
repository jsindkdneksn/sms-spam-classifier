import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from scripts.make_ci_model import make_model


@pytest.fixture
def model_dir(tmp_path):
    make_model(tmp_path)
    return tmp_path


@pytest.fixture
def client(model_dir):
    with TestClient(
        create_app(model_dir / "model.joblib", model_dir / "metadata.json", "development")
    ) as instance:
        yield instance
