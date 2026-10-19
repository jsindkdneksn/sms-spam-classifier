"""ml/train.py --config ml/configs/baseline.yaml

从 YAML 配置读取路径、随机种子、TF-IDF 与分类器参数；
TF-IDF 只在训练集 fit；仅用验证集输出选择指标；
自动向 MLflow 记录参数、指标、报告与模型工件。
"""

import argparse
import json
import subprocess
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


def build_pipeline(cfg):
    tfidf = TfidfVectorizer(
        ngram_range=tuple(cfg["tfidf"]["ngram_range"]), min_df=cfg["tfidf"]["min_df"]
    )
    c = cfg["classifier"]
    if c["type"] == "naive_bayes":
        clf = MultinomialNB(alpha=c.get("alpha", 1.0))
    elif c["type"] == "logistic_regression":
        clf = LogisticRegression(
            C=c.get("C", 1.0),
            class_weight=c.get("class_weight"),
            max_iter=c.get("max_iter", 1000),
            random_state=cfg["seed"],
        )
    else:
        raise ValueError(f"未知分类器类型: {c['type']}")
    return Pipeline([("tfidf", tfidf), ("clf", clf)])


def git_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def dataset_dvc_md5(data_dir: str):
    """读取 data/<版本>.dvc 指针中的 md5，作为数据版本哈希记录到 run。"""
    import yaml as _yaml

    pointer = Path(f"{data_dir}.dvc")
    if not pointer.exists():
        return None
    info = _yaml.safe_load(open(pointer, encoding="utf-8"))
    return info["outs"][0]["md5"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="models/experiments/model.joblib")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))

    train = pd.read_csv(Path(cfg["data_dir"]) / "train.csv")
    val = pd.read_csv(Path(cfg["data_dir"]) / "val.csv")

    mlflow.set_experiment(cfg["experiment_name"])
    with mlflow.start_run(run_name=Path(args.config).stem) as run:
        mlflow.log_params({"config": json.dumps(cfg, sort_keys=True)})
        mlflow.log_param("git_sha", git_sha())
        mlflow.log_param("dataset_dir", cfg["data_dir"])
        mlflow.log_param("dataset_dvc_md5", dataset_dvc_md5(cfg["data_dir"]))

        pipe = build_pipeline(cfg)
        pipe.fit(train["text"], train["label"])  # TF-IDF 只在训练集 fit

        pred = pipe.predict(val["text"])
        p, r, f1, _ = precision_recall_fscore_support(
            val["label"], pred, labels=["spam"], zero_division=0
        )
        acc = accuracy_score(val["label"], pred)
        metrics = {
            "val_spam_precision": p[0],
            "val_spam_recall": r[0],
            "val_spam_f1": f1[0],
            "val_accuracy": acc,
        }
        mlflow.log_metrics(metrics)
        mlflow.log_text(classification_report(val["label"], pred), "classification_report.txt")
        mlflow.log_text(
            json.dumps(confusion_matrix(val["label"], pred, labels=["ham", "spam"]).tolist()),
            "confusion_matrix.json",
        )

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipe, out)
        mlflow.log_artifact(str(out), artifact_path="model")
        mlflow.sklearn.log_model(pipe, "sklearn_model")
        print("run_id:", run.info.run_id)
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
