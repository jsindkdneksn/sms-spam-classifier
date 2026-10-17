"""tests/test_model_artifact.py —— 模型工件契约检查（B 负责）"""

import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pytest

RELEASE = Path("models/release")


@pytest.mark.requires_remote  # 依赖 models/release 正式工件（DVC 拉取）
def test_release_files_exist_and_valid():
    assert (RELEASE / "model.joblib").exists()
    meta = json.load(open(RELEASE / "metadata.json", encoding="utf-8"))
    assert meta["model_version"] and meta["mlflow_run_id"]
    import hashlib

    assert (
        hashlib.sha256((RELEASE / "model.joblib").read_bytes()).hexdigest() == meta["model_sha256"]
    )


@pytest.mark.requires_remote
def test_pipeline_contract():
    pipe = joblib.load(RELEASE / "model.joblib")
    assert hasattr(pipe, "predict") and hasattr(pipe, "predict_proba")
    idx = list(pipe.classes_).index("spam")  # 按 classes_ 找列，不假设索引
    for text in [
        "Free entry! Call now!!!",
        "zzqvx unseen words 12345",
        "See you at dinner at 7?",
        "!!!???",
        "www.free-prize.com",
    ]:
        proba = pipe.predict_proba([text])[0]
        assert 0.0 <= proba[idx] <= 1.0


@pytest.mark.requires_remote
def test_save_load_consistency(tmp_path):
    pipe = joblib.load(RELEASE / "model.joblib")
    p = tmp_path / "m.joblib"
    joblib.dump(pipe, p)
    texts = ["Free entry! Call now", "ok see you", "WINNER claim prize 400"]
    assert np.allclose(pipe.predict_proba(texts), joblib.load(p).predict_proba(texts))


def test_offline_test_model(tmp_path):
    # 供 CI 离线使用的小型确定性测试模型：结构合法即可，不代表模型质量
    out = tmp_path / "test_model.joblib"
    subprocess.run([sys.executable, "ml/make_test_model.py", str(out)], check=True)
    pipe = joblib.load(out)
    idx = list(pipe.classes_).index("spam")
    proba = pipe.predict_proba(["free win prize now"])[0]
    assert 0.0 <= proba[idx] <= 1.0
