"""Create a deterministic toy artifact. This is never a production model."""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


def make_model(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    texts = [
        "free win prize call now",
        "claim your reward winner",
        "urgent selected cash prize",
        "see you at dinner tonight",
        "ok call me later meeting",
        "meeting moved to three tomorrow",
    ]
    model = Pipeline([("tfidf", TfidfVectorizer()), ("clf", MultinomialNB())])
    model.fit(texts, ["spam", "spam", "spam", "ham", "ham", "ham"])
    target = output / "model.joblib"
    joblib.dump(model, target)
    metadata = {
        "model_version": "ci-test-v1",
        "artifact_kind": "ci-test",
        "model_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "labels": list(model.classes_),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    make_model(parser.parse_args().out_dir)
