"""Trusted CI must materialize the B handoff before running these tests."""

import csv
import hashlib
import re
import subprocess
from pathlib import Path

import pytest
import yaml
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from app.predictor import Predictor

pytestmark = pytest.mark.requires_remote


def key(text):
    text = re.sub(r"https?://\S+|www\.\S+", "<URL>", text.lower())
    return " ".join(re.sub(r"[\W_]+", " ", text).split())


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_real_data(version):
    sets = []
    for split in ("train", "val", "test"):
        path = Path("data") / version / f"{split}.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert rows
        assert all(row["label"] in {"ham", "spam"} and row["text"].strip() for row in rows)
        sets.append({key(row["text"]) for row in rows})
    assert not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    if version == "v2":
        with Path("data/v2/train.csv").open(encoding="utf-8-sig", newline="") as stream:
            train = list(csv.DictReader(stream))
        assert len(train) == len(sets[0])


@pytest.mark.parametrize("split", ["val", "test"])
def test_evaluation_sets_unchanged(split):
    assert (
        hashlib.sha256(Path(f"data/v1/{split}.csv").read_bytes()).digest()
        == hashlib.sha256(Path(f"data/v2/{split}.csv").read_bytes()).digest()
    )


def test_real_release():
    model = Predictor(
        Path("models/release/model.joblib"), Path("models/release/metadata.json"), True
    )
    assert model.predict("!!!???")["label"] in {"ham", "spam"}


def test_release_provenance_matches_committed_data():
    model = Predictor(
        Path("models/release/model.joblib"), Path("models/release/metadata.json"), True
    )
    pointer = yaml.safe_load(Path("data/v2.dvc").read_text())
    assert model.metadata["dataset_hash"] == pointer["outs"][0]["md5"]
    result = subprocess.run(
        ["git", "cat-file", "-e", model.metadata["training_git_sha"] + "^{commit}"],
        capture_output=True,
    )
    assert result.returncode == 0, "Actual training commit must be in repository history"


@pytest.mark.parametrize("split,prefix", [("val", "validation"), ("test", "test")])
def test_reported_metrics_match_frozen_release(split, prefix):
    # Audit the frozen artifact; never fit, tune or select a model against this test.
    model = Predictor(
        Path("models/release/model.joblib"), Path("models/release/metadata.json"), True
    )
    with Path(f"data/v2/{split}.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    labels = [row["label"] for row in rows]
    predictions = model.model.predict([row["text"] for row in rows])
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, labels=["spam"], zero_division=0
    )
    actual = {
        "spam_precision": precision[0],
        "spam_recall": recall[0],
        "spam_f1": f1[0],
        "accuracy": accuracy_score(labels, predictions),
    }
    for name, value in actual.items():
        assert value == pytest.approx(model.metadata["metrics"][f"{prefix}_{name}"])
