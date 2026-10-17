# 数据版本与 Azure 存储

原始输入为成员 B 交接的英文短信文件 `SMSSpamCollection.csv`（ham/spam）。
本仓库不提交原始文件；原始公开下载地址及许可仍需成员 B 补充确认，
不将未经核实的下载来源作为已验证事实。

| 版本 | train | val | test | DVC 目录 MD5 | 首次记录的 Git 提交 |
|---|---:|---:|---:|---|---|
| v1 | 3898 | 841 | 835 | df9fa08c8b03b8dde68db5f1d4480563.dir | ae2571861f8728016d199de9a8e22a4ccb2f7fbd |
| v2 | 3590 | 841 | 835 | b8c47cc402e3773f024a3a8c3d26dc48.dir | acd94fa45b35d2fedc64a99d7531969945d8ed67 |

v2 在训练集中去重 308 条；验证集、测试集保持与 v1 字节一致。
划分脚本使用归一化内容键分组，随机种子为 42，防止同组内容跨集合泄漏。
正式模型使用 dataset-v2；详见 `ml/README_experiments.md`。
两个版本分别存放在不同目录，因此当前 Git 提交同时引用两版数据，无须切换工作区才能下载。

## Azure 接入

- 课程存储账户：`wut2026`；容器：`dvc`。
- 本组远程：`myazure`，URL `azure://dvc/sms-spam-jsindkdneksn`。
- DagsHub 远程保留作为原交接来源。2026-10-17 已验证 Azure 上传及独立空缓存下载，8 个文件 SHA256 全部一致；证据见 `ml/azure-verification.json`。GitHub CI 切换仍需环境配置和实际运行验收。
- 安装：`python -m pip install -r requirements-delivery.txt`。
- 上传及独立下载验收：`python -m scripts.azure_handoff`，交互式隐藏输入 SAS。
- SAS 仅保存在忽略的 `.dvc/config.local`，不提交 Git；临时验收目录中的凭证自动清除。
- 成功报告写入 `work/azure-verification.json`，不含凭证。

GitHub 的 integration、staging、production 环境分别设置：
`DVC_REMOTE=myazure`、`AZURE_STORAGE_ACCOUNT=wut2026`（Variables），
以及 `AZURE_SAS_TOKEN`（Secret）。本机上传需写入权限；CI 只需下载所需权限。
现有认证脚本依据远程 URL 选择认证方式，可保留原 DagsHub Secrets。
先完成 Azure 上传与独立下载验收，再切换环境变量并按 feature → dev → staging → main 合并。
