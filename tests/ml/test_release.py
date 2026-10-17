"""Trusted CI must materialize the B handoff before running these tests."""

import csv
import hashlib
import re
from pathlib import Path

import pytest

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
