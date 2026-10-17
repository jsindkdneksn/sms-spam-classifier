"""ml/promote_model.py —— 把选定实验的模型提升为正式 release 工件

用法:
  python ml/promote_model.py --src models/experiments/E3.joblib \
      --version model-v1 --metrics models/experiments/E3_metrics_all.json \
      --run-id 2728e5419ad34a3a880d8cf35598837e \
      --data-hash b8c47cc402e3773f024a3a8c3d26dc48.dir
"""

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True)
ap.add_argument("--version", required=True)
ap.add_argument("--metrics", required=True, help="含 val/test 指标的 json 文件")
ap.add_argument("--run-id", required=True)
ap.add_argument("--data-hash", required=True, help="dvc 数据指针 md5，如 cat data/v2.dvc")
ap.add_argument(
    "--git-sha",
    default=None,
    help="训练时代码的提交 SHA（默认取当前 HEAD，正式交付应填实际训练所用的提交）",
)
args = ap.parse_args()

release = Path("models/release")
release.mkdir(parents=True, exist_ok=True)
shutil.copy2(args.src, release / "model.joblib")

meta = {
    "model_version": args.version,
    "training_git_sha": args.git_sha
    or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "dataset_hash": args.data_hash,
    "dataset_version": "dataset-v2",
    "mlflow_run_id": args.run_id,
    "model_sha256": sha256(release / "model.joblib"),
    "labels": ["ham", "spam"],
    "metrics": json.load(open(args.metrics, encoding="utf-8")),
}
with open(release / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)
print(json.dumps(meta, indent=2, ensure_ascii=False))
