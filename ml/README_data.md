# 数据说明（README_data）

## 来源与许可

- **直接来源**：Kaggle 镜像 <https://www.kaggle.com/datasets/abhishek14398/sms-spam-collection>（下载日期：2026-10-17）
- **上游来源**：UCI Machine Learning Repository, SMS Spam Collection, <https://archive.ics.uci.edu/dataset/228/sms+spam+collection>（Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A.）
- **许可**：CC BY 4.0（署名 4.0 国际），允许共享与改编，需适当署名
- 建议引用：`Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A. (2011). Contributions to the Study of SMS Spam Filtering: New Collection and Results. ACM DocEng 2011.`

## 原始文件特征（已核实）

- 文件：`SMSSpamCollection.csv`，UTF-8 编码，无表头
- **每行整体被一对双引号包裹**，行内为 `label<TAB>text` 两字段（解析时先剥外层引号）
- 有效样本 **5574 条**：ham 4827（86.6%）/ spam 747（13.4%），无非法标签、无空文本
- 文本长度 2～910 字符；按"小写 + URL 归一 + 去标点"生成内容分组键后有 306 组重复内容（涉及 751 条），**无标签冲突**

## 清洗与防泄漏原则

- 统一字段为 `text,label`，label 仅取 `ham`/`spam`
- 内容分组键**仅用于识别重复和防泄漏划分**，不对文本做激进清洗（URL、数字可能携带分类信息，原样保留给 TF-IDF）
- 训练/验证/测试 = 70/15/15，**先按分组键分组再划分**，随机种子 42，相同短信内容不会跨集合出现
- 冲突标签（同一分组键不同 label，实测 0 组）如发生将整组剔除并记录

## 数据版本

| 版本 | train | val | test | DVC 目录 MD5 | 首次记录的 Git 提交 |
|---|---:|---:|---|---|---|
| v1 | 3898 | 841 | 835 | `df9fa08c8b03b8dde68db5f1d4480563.dir` | `ae2571861f8728016d199de9a8e22a4ccb2f7fbd` |
| v2 | 3590 | 841 | 835 | `b8c47cc402e3773f024a3a8c3d26dc48.dir` | `acd94fa45b35d2fedc64a99d7531969945d8ed67` |

- v2 在训练集中去重 308 条；验证集、测试集与 v1 **字节级一致**，v1→v2 的指标差异才可归因于训练数据变化
- **v1→v2 指标影响**：MNB 验证集指标两版逐位相同（见 README_experiments）；v2 的价值在于训练数据更干净、来源可审计，而非分数提升
- 正式模型使用 dataset-v2；两个版本存放在不同目录，当前 Git 提交同时引用两版数据，无须切换工作区即可下载

## Azure 接入（DVC 远端）

- 课程存储账户：`wut2026`；容器：`dvc`。
- 本组远程：`myazure`，URL `azure://dvc/sms-spam-jsindkdneksn`。
- DagsHub 远程保留（实验追踪与协作用途）。2026-10-17 已验证 Azure 上传及独立空缓存下载，8 个文件 SHA256 全部一致；证据见 `ml/azure-verification.json`。
- 安装：`python -m pip install -r requirements-delivery.txt`。
- 上传及独立下载验收：`python -m scripts.azure_handoff`（交互式隐藏输入 SAS）。
- SAS 仅保存在被忽略的 `.dvc/config.local`，不提交 Git；成功报告写入 `work/azure-verification.json`，不含凭证。

GitHub 的 integration、staging、production 环境分别设置：
`DVC_REMOTE=myazure`、`AZURE_STORAGE_ACCOUNT=wut2026`（Variables）与 `AZURE_SAS_TOKEN`（Secret）。
本机上传需写权限；CI 只需下载权限。现有认证脚本依据远程 URL 选择认证方式，可保留原 DagsHub Secrets。

## 如何恢复

```bash
# 恢复到 v1 或 v2（数据内容在 Azure/DagsHub 远端，Git 只有指针）
git checkout dataset-v1 && dvc pull   # 或 dataset-v2；DVC_REMOTE 决定从哪个远端拉取
```

原始数据文件不进入 Git 历史（`data/raw/` 等在 .gitignore 排除，数据内容全部由 DVC 管理）。
