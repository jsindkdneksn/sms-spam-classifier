# SMS Spam Classifier

英文短信识别应用：FastAPI + 单页 HTML + scikit-learn Pipeline。

## 当前阶段

项目保留 B 的 Git 历史，应用已沿 feature → dev → staging → main 集成，staging/production 镜像发布已通过。model-v1 与两版数据已完成课程 Azure Blob Storage 上传及独立空缓存下载，8 个文件 SHA256 全部匹配。本次 Azure 接入含 55 项通过的本地测试；远端 CI 是否使用 Azure，仍需以环境配置及实际运行记录为准。交接核查见 HANDOFF.md，数据版本与配置见 ml/README_data.md。

- A：应用、测试、Docker、GitHub Actions 和交付文档。
- B：数据、DVC/Azure、训练、MLflow、模型及来源信息。
- 待完成：GitHub 环境切换 Azure 并验证、staging 持续部署，以及 B 补充原始数据下载来源与许可。

## 本地运行（PowerShell）

Python 3.12 已在本机测试；scikit-learn=1.5.2、joblib=1.4.2 与 B 手册一致，但仍需核对其真实模型环境。

```powershell
py -3.12 -m venv .venv
$ProjectPython = '.venv\Scripts\python.exe'
& $ProjectPython -m pip install -r requirements-app.txt -r requirements-dev.txt
& $ProjectPython -m scripts.make_ci_model --out-dir work/ci-model
$env:MODEL_PATH = (Resolve-Path 'work/ci-model/model.joblib').Path
$env:MODEL_METADATA_PATH = (Resolve-Path 'work/ci-model/metadata.json').Path
$env:APP_ENV = 'development'
& $ProjectPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000/。停止服务按 Ctrl+C。若 py 不可用，可使用已安装 Python 的绝对路径建立虚拟环境，不需要修改系统执行策略。

Git Bash 激活方式为 `source .venv/Scripts/activate`，环境变量使用 `export NAME=value`，不能原样执行 PowerShell 的 `$env:NAME`。

## 测试

```powershell
& $ProjectPython -m ruff check .
& $ProjectPython -m ruff format --check .
& $ProjectPython -m pytest -q -m 'not requires_remote'
```

测试覆盖输入校验、预测接口/异常工件、文本边界/模型契约。正式远端数据模型准备好后运行 `python -m pytest -q`，不跳过 requires_remote。

## 接口

`POST /predict` 接收 `{"text":"Free prize call now"}`，返回 label、spam_probability、model_version。严格字符串，去空白后长度 1～5000。非法输入返回 422；模型不可用返回 503。

`GET /health` 返回状态、模型版本、工件类型和环境。staging、production 拒绝 ci-test 模型。`/docs` 提供交互接口文档。

## 正式模型

B 交付 `.dvc/config`、`data/v1.dvc`、`data/v2.dvc`、`models/release.dvc`，实际数据和模型留在 DVC 远端。

模型目录 `models/release/` 包含 model.joblib、metadata.json。正式元数据必须包含：model_version、model_sha256、40 位 training_git_sha、dataset_hash、dataset_version、mlflow_run_id、非空 metrics。可额外标记 artifact_kind=release。

B 原工件没有 artifact_kind，加载器在完整来源校验后兼容此格式，仅在内存标记 release，不修改原文件或 DVC 指针。显式 ci-test/未知标记和不完整来源记录仍被拒绝。training_git_sha 必须来自训练 run，不能填写交付时的 HEAD。

运行 `python -m scripts.verify_release --require-release` 验证。校验值不能证明来源可信，joblib 只加载团队可信存储的工件。

## Git 和自动化

功能分支 → dev → staging → main。A 提交、B 审查，反之亦然。先接入 B 现有历史，之后再创建团队 GitHub 仓库，不把本独立包的 Git 历史覆盖 B 历史。

CI：PR 到 dev/staging/main，或这些分支收到 push，执行静态检查、应用测试、Docker 构建与烟雾检查。可信代码的远端集成任务运行完整测试，需要 `integration` 环境审批和只读 DVC 凭证。

Delivery：staging/main 的 push 重新验证该提交，依次拉取正式数据与模型、全量测试、生成环境文件、构建正式镜像、烟雾检查、推送 Docker Hub。staging/main 分别使用 staging/production 环境。失败不会发布。

完整环境配置、镜像运行和回滚见 DEPLOYMENT.md。GitHub 的离线应用测试、Docker 构建与容器检查已成功运行；真实工件 job 仍需配置远端只读权限。尚未发布或部署正式环境。

## 课程要求

DagsHub 用于协作/实验不替代原要求的 Azure DVC 存储。由 B 补齐 Azure，或取得老师明确替代许可。Azure、DagsHub、Docker Hub 分别是不同职责，不混用凭证。

请勿将原始数据、模型二进制、课件、令牌、.env 或虚拟环境提交 Git。
