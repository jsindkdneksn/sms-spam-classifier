# SMS Spam Classifier

## 启动与网页地址

打开 Docker Desktop，启动已有容器：

```bash
docker start sms-spam-local
```

网页：http://127.0.0.1:8080/

## 模型和数据

模型：TF-IDF + 逻辑回归，版本 `model-v1`。测试集 spam F1 为 **0.931**，准确率为 **0.981**。

数据由 DVC 管理，存放在 Azure。v2 在 v1 基础上去重 308 条训练样本，验证集和测试集保持不变。

[数据说明](ml/README_data.md) · [实验记录](ml/README_experiments.md)

## 发布

改动按 `feature → dev → staging → main` 合并。PR 自动运行测试、代码检查和 Docker 构建；合并到 staging 或 main 后，重新验证并发布对应镜像到 Docker Hub。

镜像：`kzy217/sms-spam-classifier:staging`、`kzy217/sms-spam-classifier:production`。

当前已完成镜像发布，尚未接入主机自动部署。配置和运行方法见 [DEPLOYMENT.md](DEPLOYMENT.md)。
