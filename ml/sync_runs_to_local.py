"""把 DagsHub 上的 sms-spam 实验 run 同步到本地 mlruns，供 mlflow ui 离线查看。

用法: python ml/sync_runs_to_local.py [本地存储目录，默认 ./mlruns]
说明: 只读取远端并写入本地，不修改 DagsHub 上的任何 run。
"""
import shutil
import sys
import tempfile
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient

REMOTE_URI = "https://dagshub.com/hanss0090/sms-spam-classifier.mlflow"
EXPERIMENT = "sms-spam"


def main():
    local_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "mlruns").resolve()
    local_uri = "file:///" + local_dir.as_posix().lstrip("/")  # 三斜杠 file URI
    # DagsHub 的 run 工件是 mlflow-artifacts:// 方案，下载时要求全局
    # tracking URI 为远端 http(s)，否则本地 file store 校验会拒绝
    mlflow.set_tracking_uri(REMOTE_URI)
    src = MlflowClient(tracking_uri=REMOTE_URI)
    dst = MlflowClient(tracking_uri=local_uri)

    exp = src.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        raise SystemExit(f"远端不存在实验 {EXPERIMENT}")
    dst_exp = dst.create_experiment(EXPERIMENT)

    runs = src.search_runs(experiment_ids=[exp.experiment_id])
    print(f"远端共 {len(runs)} 个 run，开始同步到 {local_dir}")
    for r in runs:
        data = r.data
        new_run = dst.create_run(
            experiment_id=dst_exp,
            run_name=r.info.run_name,
            tags={k: v for k, v in r.data.tags.items()
                  if not k.startswith("mlflow.")},
        )
        for k, v in data.params.items():
            dst.log_param(new_run.info.run_id, k, v)
        for k, v in data.metrics.items():
            dst.log_metric(new_run.info.run_id, k, v)
        # 工件：分类报告 / 混淆矩阵 / model.joblib / sklearn_model
        tmp = Path(tempfile.mkdtemp(prefix="mlflow-sync-"))
        try:
            local_path = src.download_artifacts(r.info.run_id, "", tmp)
            for artifact in sorted(Path(local_path).rglob("*")):
                if artifact.is_file():
                    rel = artifact.relative_to(local_path)
                    parent = str(rel.parent)
                    dst.log_artifact(new_run.info.run_id, str(artifact),
                                     artifact_path=None if parent == "." else parent)
                    print(f"  [{r.info.run_name}] artifact {rel}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(f"  [{r.info.run_name}] {r.info.run_id[:8]} 同步完成")
    print("完成。运行: mlflow ui --backend-store-uri", local_uri)


if __name__ == "__main__":
    main()
