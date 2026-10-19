# 来源链记录（PROVENANCE）

本文件记录"代码 → 数据 → 实验 → 模型 → 交付"的准确对应关系，所有值均为真实值，可用所列命令复核。

## 当前正式模型 model-v1

| 环节 | 标识 | 复核方式 |
|---|---|---|
| 训练代码提交 | `6b515f1c7b3bb1031aad13b70b92532ae4c35601`（ml: add train.py and experiment configs） | `git log --oneline 6b515f1` |
| 数据版本 | `dataset-v2`，指针 md5 `b8c47cc402e3773f024a3a8c3d26dc48.dir` | `git show dataset-v2:data/v2.dvc` |
| MLflow 实验 run | `2728e5419ad34a3a880d8cf35598837e`（E3 improved） | DagsHub 仓库 Experiments 页 |
| 模型文件 SHA256 | `8ae71127dc5c3c2d5436c09773ea4a38690d5b9ce42482133d5eb5368d8f6705` | `sha256sum models/release/model.joblib` |
| 交付代码提交 | `89b3625`（release: model-v1 ...，标签 `model-v1` = `89b3625019794037fde12f93b2579f1fd33d6f2a`） | `git rev-parse model-v1` |
| 模型 DVC 指针 | `models/release.dvc`（随 model-v1 提交） | `git show model-v1:models/release.dvc` |

## 追溯图

```text
应用镜像（成员 A 构建，digest 待 A 交付后补充）
        │
        ▼
交付代码提交 model-v1 = 89b3625 ── models/release.dvc ──► 模型文件 SHA256 8ae71127…
        │                                                        │
        │                                                        ▼
        └── 训练代码提交 6b515f1 ◄── MLflow run 2728e541（E3）
                     │
                     └── 数据 dataset-v2（b8c47cc4…）◄── 原始 SMS Spam Collection（Kaggle/UCI, CC BY 4.0）
```

## 全部实验 run 一览（实验 sms-spam，均可在 DagsHub Experiments 页打开）

| run | 训练代码 | 数据 | 验证 spam F1 |
|---|---|---|---|
| `29ffd4a17b7a42d89b9c4995d90ee5cf`（E1 baseline） | `6b515f1` | dataset-v1 | 0.879 |
| `65bed535b8fa4b548715fe9c92165766`（E2 e2_v2） | `6b515f1` | dataset-v2 | 0.879 |
| `2728e5419ad34a3a880d8cf35598837e`（E3 improved，选定） | `6b515f1` | dataset-v2 | 0.943 / 测试 0.931 |

## 口径说明

- 训练 SHA、交付 SHA 是两个不同提交，分别记录（训练时无法预知未来提交，故由 promote 时显式传入 `--git-sha`）。
- 模型 SHA256 只针对 `model.joblib` 文件本身，不包含 metadata.json，避免自引用。
- 评估口径（验证集选型、测试集一次）见 `ml/README_experiments.md`；数据版本差异见 `ml/README_data.md`。
