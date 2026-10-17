import joblib
import numpy as np
import pytest

from app.predictor import Predictor


@pytest.mark.parametrize(
    "text",
    [
        "FREE CALL NOW",
        "www.example.com https://example.com",
        "123456789",
        "!!!???",
        "zzqvx unseenwords",
        " See you tomorrow ",
        "Email me at x@example.org",
        "🙂",
    ],
)
def test_edge_texts(client, text):
    response = client.post("/predict", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in {"ham", "spam"}
    assert 0 <= data["spam_probability"] <= 1


def test_save_load_consistency(model_dir, tmp_path):
    original = joblib.load(model_dir / "model.joblib")
    joblib.dump(original, tmp_path / "copy.joblib")
    restored = joblib.load(tmp_path / "copy.joblib")
    texts = ["free prize", "dinner meeting", "!!!", "new tokens"]
    np.testing.assert_allclose(original.predict_proba(texts), restored.predict_proba(texts))


def test_spam_probability_uses_classes(model_dir):
    predictor = Predictor(model_dir / "model.joblib", model_dir / "metadata.json")
    text = "free win prize"
    expected = predictor.model.predict_proba([text])[0][
        list(predictor.model.classes_).index("spam")
    ]
    assert predictor.predict(text)["spam_probability"] == pytest.approx(expected)


def test_reverse_class_order(model_dir, monkeypatch):
    class ReversedModel:
        classes_ = ["spam", "ham"]

        def predict(self, texts):
            return ["spam"] * len(texts)

        def predict_proba(self, texts):
            return [[0.9, 0.1]] * len(texts)

    monkeypatch.setattr("app.predictor.joblib.load", lambda _: ReversedModel())
    predictor = Predictor(model_dir / "model.joblib", model_dir / "metadata.json")
    assert predictor.predict("message")["spam_probability"] == pytest.approx(0.9)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_probability_rejected(model_dir, monkeypatch, invalid):
    predictor = Predictor(model_dir / "model.joblib", model_dir / "metadata.json")
    monkeypatch.setattr(predictor.model, "predict_proba", lambda _: [[1 - invalid, invalid]])
    with pytest.raises(ValueError):
        predictor.predict("message")
