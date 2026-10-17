# 实验记录（README_experiments）

项目：英文短信垃圾信息识别系统 · 成员 B 维护
评估口径：**主指标为 spam 类 F1**，同时报告 Precision / Recall / Accuracy；准确率不单独代表效果。
流程纪律：**验证集用于模型选择，固定测试集只在选定模型后评估一次**，未参与任何调参。

## 实验总览（均为验证集指标）

| 实验 | MLflow run ID | 数据版本 | 模型 | spam P | spam R | spam F1 | Accuracy |
|---|---|---|---|---|---|---|---|
| E1 baseline | `29ffd4a17b7a42d89b9c4995d90ee5cf` | dataset-v1 | TF-IDF(1-gram, min_df=2) + MultinomialNB(α=1.0) | 1.000 | 0.784 | 0.879 | 0.974 |
| E2 e2_v2 | `65bed535b8fa4b548715fe9c92165766` | dataset-v2 | 同 E1（参数完全一致） | 1.000 | 0.784 | 0.879 | 0.974 |
| E3 improved | `2728e5419ad34a3a880d8cf35598837e` | dataset-v2 | TF-IDF(1-2gram, min_df=2) + LogisticRegression(C=1.0, class_weight=balanced, max_iter=1000) | 0.917 | 0.971 | **0.943** | **0.986** |

三次 run 均可于 DagsHub 仓库 Experiments 页打开（实验 `sms-spam`），参数、分类报告、混淆矩阵、模型工件齐全；三次训练代码 git SHA 均为 `6b515f1`，训练时工作区已提交。

## 观察与解释

1. **E1 → E2（去重 308 条训练样本）指标逐位相同**：MNB 的多项式计数容忍重复样本，去重没有翻转任何验证集预测。v2 的价值在于训练数据更干净、来源可审计，**不是**性能提升；不将 E1→E2 记为改进。
2. **E3 换用 LogisticRegression + balanced 类别权重后 spam 召回从 0.784 升至 0.971**，F1 0.879 → 0.943；代价是精确率 1.000 → 0.917（误报略增）。对垃圾短信场景，漏放垃圾短信的代价通常高于误杀正常短信，此权衡方向合理。

## 模型选择

按主指标 **验证集 spam F1** 选定 **E3**（F1 = 0.943，高于 E1/E2 的 0.879）。

## 最终测试集评估（仅一次，评估对象仅 E3）

数据：`data/v2/test.csv`（dataset-v2，835 条：ham 717 / spam 118，与 v1 的测试集字节级一致）

| 指标 | 数值 |
|---|---|
| spam Precision | 0.947 |
| spam Recall | 0.915 |
| **spam F1** | **0.931** |
| Accuracy | 0.981 |

混淆矩阵（行 = 真实标签 ham/spam，列 = 预测 ham/spam）：

| | 预测 ham | 预测 spam |
|---|---|---|
| 真实 ham | 711 | 6 |
| 真实 spam | 10 | 108 |

测试集 F1（0.931）与验证集（0.943）接近，无明显过拟合 gap；模型泛化正常。

## 复现方式

```bash
python ml/train.py --config ml/configs/improved.yaml --out models/experiments/E3.joblib
# 测试集评估：对 models/experiments/E3.joblib 在 data/v2/test.csv 上计算上表指标
```

随机种子 42（配置内），训练依赖见 `requirements-train.txt`。
