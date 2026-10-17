# 当前正式模型登记（current_model）

## model-v1（当前交付版本）

- **模型**：TF-IDF(1-2gram, min_df=2) + LogisticRegression(C=1.0, class_weight=balanced, max_iter=1000, seed=42) 完整 scikit-learn Pipeline（提供 predict / predict_proba，labels = [ham, spam]）
- **获取方式**：`git checkout model-v1 && dvc pull` → `models/release/model.joblib` + `metadata.json`（无需训练数据）
- **来源链**（详见 `ml/PROVENANCE.md`）：
  - 训练代码 `6b515f1` · 数据 `dataset-v2`（`b8c47cc4…dir`）· run `2728e5419ad34a3a880d8cf35598837e`
  - 模型 SHA256 `8ae71127dc5c3c2d5436c09773ea4a38690d5b9ce42482133d5eb5368d8f6705`
  - 交付提交 `model-v1` = `89b3625019794037fde12f93b2579f1fd33d6f2a`
- **指标**：验证集 spam F1 0.943 / P 0.917 / R 0.971 / Acc 0.986；测试集（仅评估一次）spam F1 0.931 / P 0.947 / R 0.915 / Acc 0.981

## 选择原因

1. 主指标（验证集 spam F1）在三组实验中最高：0.943 vs MNB 的 0.879；
2. 类别权重 balanced 使 spam 召回从 0.784 提升到 0.971，漏放垃圾短信代价高于误杀正常短信，权衡方向符合场景；
3. 测试集 F1（0.931）与验证集接近，泛化正常；
4. 完整 Pipeline 交付（TF-IDF 在训练集内 fit），应用侧加载即可用，概率列按 `classes_` 定位。

## 应用对接（成员 A）

- 模型路径：`models/release/model.joblib`（环境变量 `MODEL_PATH`）
- 元数据路径：`models/release/metadata.json`（环境变量 `MODEL_METADATA_PATH`）
- 应用镜像 digest：待成员 A 的交付流水线构建后回填至 `ml/PROVENANCE.md`

## 变更历史

| 版本 | 日期 | 说明 |
|---|---|---|
| model-v1 | 2026-10-17 | E3（dataset-v2）首次正式交付 |
