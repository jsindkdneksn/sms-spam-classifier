# 数据说明（README_data）

## 来源与许可

- **直接来源**：Kaggle 镜像 <https://www.kaggle.com/datasets/abhishek14398/sms-spam-collection>（下载日期：2026-10-17）
- **上游来源**：UCI Machine Learning Repository, SMS Spam Collection, <https://archive.ics.uci.edu/dataset/228/sms+spam+collection>（Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A.）
- **许可**：CC BY 4.0（署名 4.0 国际），允许共享与改编，需适当署名 [UCI 页面](https://archive.ics.uci.edu/ml/datasets/sms+spam+collection)
- 建议引用：`Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A. (2011). Contributions to the Study of SMS Spam Filtering: New Collection and Results. ACM DocEng 2011.`

## 原始文件特征（已核实）

- 文件：`SMSSpamCollection.csv`，UTF-8 编码，无表头
- **每行整体被一对双引号包裹**，行内为 `label<TAB>text` 两字段（解析时先剥外层引号）
- 有效样本 **5574 条**：ham 4827（86.6%）/ spam 747（13.4%），无非法标签、无空文本
- 文本长度 2～910 字符；按"小写 + URL 归一 + 去标点"生成内容分组键后有 306 组重复内容（涉及 751 条），**无标签冲突**

## 字段与统一格式

统一为 `text,label` 两列 CSV（`data/processed/` 及 v1/v2 均为此格式），label 仅取 `ham`/`spam`。

## 清洗与防泄漏原则

- 内容分组键**仅用于识别重复和防泄漏划分**，不对文本做激进清洗（URL、数字可能携带分类信息，原样保留给 TF-IDF）
- 训练/验证/测试 = 70/15/15，**先按分组键分组再划分**，随机种子 42，相同短信内容不会跨集合出现
- 冲突标签（同一分组键不同 label，实测 0 组）如发生将整组剔除并记录

## 两个数据版本

| | dataset-v1 | dataset-v2 |
|---|---|---|
| 训练集 | 3898 条（含重复） | 3590 条（去重 308 条） |
| 验证集 | 841（ham 739 / spam 102） | 与 v1 **字节级一致** |
| 测试集 | 835（ham 717 / spam 118） | 与 v1 **字节级一致** |
| DVC 指针 md5 | `df9fa08c8b03b8dde68db5f1d4480563.dir` | `b8c47cc402e3773f024a3a8c3d26dc48.dir` |
| Git 标签 | `dataset-v1` = `ae2571861f8728016d199de9a8e22a4ccb2f7fbd` | `dataset-v2` = `acd94fa45b35d2fedc64a99d7531969945d8ed67` |
| 说明 | 首个可训练版本 | 仅训练集去重；验证/测试不动，v1→v2 的指标差异才可归因于训练数据变化 |

**v1→v2 指标影响**：MNB 验证集指标两版逐位相同（见 README_experiments），去重未翻转任何预测；v2 的价值在于训练数据更干净、来源可审计。

## 如何恢复

```bash
# 恢复到 v1 或 v2（需 DagsHub 认证，远端：https://dagshub.com/hanss0090/sms-spam-classifier.dvc）
git checkout dataset-v1 && dvc pull   # 或 dataset-v2
```

原始数据文件不进入 Git 历史（由 `data/raw/` 在 .gitignore 排除 + DVC 管理 `data/v1`、`data/v2` 保证）。
