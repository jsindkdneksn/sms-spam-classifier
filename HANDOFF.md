# B → A 已核实交接

2026-10-17 从用户已认证的桌面克隆读取，基于 B main：
`89b3625` — release: model-v1 (E3, dataset-v2) with metadata and DVC pointer。

本地 A 功能分支保留了全部 B 提交历史。尚未推送任何远端。B 的桌面克隆未修改。

## 已有

- train.py、数据处理脚本、三份实验配置、requirements-train.txt。
- data/v1.dvc、data/v2.dvc、models/release.dvc。
- DVC HTTP remote 名称 dagshub 和 origin，均指向 B 的 DagsHub DVC 存储。
- README_experiments：三次 run 与选定 E3 的报告。该文档报告 test spam F1=0.931、Accuracy=0.981；尚未从真实模型和数据独立复核。

## 待完成

- 实际数据和模型不在 Git clone 内，需读取 DVC 工件。
- Azure remote 尚未配置，与原课程要求不符；DagsHub MLflow 可继续保留。
- 缺 README_data、PROVENANCE、registry/current_model 等最终来源文档。
- 当前训练代码未自动记录 DVC 哈希；需要 B 后续补齐日志来源信息。
- 模型发布脚本已支持 --git-sha；应提供 MLflow run 中真实的完整训练 SHA。
- B 原元数据示例无 artifact_kind；正式工件与 A 发布契约需核对。

## A 已进行的训练代码调整

Ruff 格式化、整理导入，把 data_pipeline 中变量 l 改为 label、把 make_v2 的 shutil 导入移到顶部。未重训、未改变训练参数、未改数据划分或评估指标。原训练提交 SHA 继续指向 B 原历史，不改成格式调整后的 A 提交。

## 无需暴露令牌的当前拉取

在项目根目录手动运行 `python -m scripts.download_handoff`，用户名和访问令牌只在本地交互输入，不保存。工具使用已有 DVC 指针读取 B 的远端对象，校验目录和文件 MD5，不覆盖已更改的本地文件。

该工具只为当前交接提供轻量下载，不替代 DVC/Azure 验收。正式 CI 使用 scripts.pull_artifacts 调用 DVC。
