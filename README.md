# SMS Spam Classifier

输入一段英文短信，判断它是否是垃圾信息。网页用 FastAPI 提供服务，模型是 TF-IDF + 逻辑回归。

## 启动

已有 `sms-spam-local` 容器时，打开 Docker Desktop，再启动容器：

```bash
docker start sms-spam-local
```

打开 http://127.0.0.1:8080 。

从源码运行需要 Python 3.12。先安装依赖，并准备好 `models/release/` 中的正式模型：

```bash
python -m pip install -r requirements-app.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 。模型和数据通过 DVC 从 Azure 下载，配置见 [部署说明](DEPLOYMENT.md)。仓库不包含模型二进制和原始数据。

## 测试

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

完整测试需要正式模型和 v1、v2 数据。只检查应用代码时，可运行 `python -m pytest -q -m "not requires_remote"`。

## 模型和数据

正式模型为 `model-v1`，使用去重后的 v2 数据训练。测试集 spam F1 为 **0.931**，准确率为 **0.981**。

- [数据版本](ml/README_data.md)：v2 训练集去重 308 条，验证集和测试集保持不变。
- [实验记录](ml/README_experiments.md)：三次实验的参数、指标和 MLflow run。
- 页面用于英文短信辅助判断，显示的垃圾概率不是准确率。

## 协作和发布

改动按 `feature → dev → staging → main` 合并，经过同伴审查和 CI 检查。GitHub Actions 自动测试、构建并验证 Docker 镜像，再发布到 Docker Hub。

Azure 下载与 staging、production 镜像发布已验证通过。长期运行主机的自动部署尚未接入，数据原始来源和许可仍需补齐。

成员 A 负责应用、测试和 DevOps，成员 B 负责数据、训练和 MLflow。

API 文档在 `/docs`，健康检查在 `/health`，预测接口为 `POST /predict`。环境配置和镜像运行方法见 [DEPLOYMENT.md](DEPLOYMENT.md)。

不要提交令牌、`.env`、`.dvc/config.local` 或模型文件。
