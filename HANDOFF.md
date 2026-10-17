# B → A 已核实交接

2026-10-17 从用户已认证的桌面克隆读取，基于 B main：
`89b3625` — release: model-v1 (E3, dataset-v2) with metadata and DVC pointer。

本地 A 功能分支保留了全部 B 提交历史，已推送 GitHub 并创建草稿 PR #1。B 的桌面克隆未修改。

## 已有

- train.py、数据处理脚本、三份实验配置、requirements-train.txt。
- data/v1.dvc、data/v2.dvc、models/release.dvc。
- DVC HTTP remote 名称 dagshub 和 origin，均指向 B 的 DagsHub DVC 存储。
- README_experiments：三次 run 与选定 E3 的报告。该文档报告 test spam F1=0.931、Accuracy=0.981；尚未从真实模型和数据独立复核。

## 待完成

- 实际数据和模型已通过用户交互认证读取，全部 DVC MD5 校验通过；仍不提交二进制或原始数据到 Git。
- Azure remote 尚未配置，与原课程要求不符；DagsHub MLflow 可继续保留。
- 缺 README_data、PROVENANCE、registry/current_model 等最终来源文档。
- 当前训练代码未自动记录 DVC 哈希；需要 B 后续补齐日志来源信息。
- 模型发布脚本已支持 --git-sha；应提供 MLflow run 中真实的完整训练 SHA。
- B 原元数据无 artifact_kind，A 已兼容完整来源信息的原格式，不修改已被 DVC 校验的工件。

## 正式模型本地验收

51 项测试通过，含防泄漏、v2 去重、固定评估集、来源指针匹配、训练提交可追踪、正式模型加载和指标独立复核。读取已冻结的测试集仅做工件报告审计，没有重训或调参。

- 模型：model-v1；训练 SHA：6b515f1c7b3bb1031aad13b70b92532ae4c35601。
- 数据 DVC 哈希：b8c47cc402e3773f024a3a8c3d26dc48.dir。
- 模型 SHA256：8ae71127dc5c3c2d5436c09773ea4a38690d5b9ce42482133d5eb5368d8f6705。
- 验证集 spam F1：0.9428571428571428；测试集 spam F1：0.9310344827586207，Accuracy：0.9808383233532935，与 B 元数据一致。

## A 已进行的训练代码调整

Ruff 格式化、整理导入，把 data_pipeline 中变量 l 改为 label、把 make_v2 的 shutil 导入移到顶部。未重训、未改变训练参数、未改数据划分或评估指标。原训练提交 SHA 继续指向 B 原历史，不改成格式调整后的 A 提交。

## 无需暴露令牌的当前拉取

在项目根目录手动运行 `python -m scripts.download_handoff`，用户名和访问令牌只在本地交互输入，不保存。工具使用已有 DVC 指针读取 B 的远端对象，校验目录和文件 MD5，不覆盖已更改的本地文件。

该工具只为当前交接提供轻量下载，不替代 DVC/Azure 验收。正式 CI 使用 scripts.pull_artifacts 调用 DVC。
