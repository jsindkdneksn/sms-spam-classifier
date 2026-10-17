# 交付和部署

## 当前限制

GitHub 与 PR 已接通，离线 CI 及测试镜像运行通过；正式 DVC 工件已在本机验证。GitHub 远端只读凭证、Azure、Docker Hub 与 staging 主机仍待配置；没有发布正式镜像或部署外部服务。

## GitHub 环境

创建 integration、staging、production。integration 需设置审查者，PR 代码审查后才能释放只读远端凭证；staging/production 限对应受保护分支。

每个环境设置：

| 类别 | 名称 | 含义 |
|---|---|---|
| Variable | DVC_REMOTE | 实际已提交的 DVC remote 名 |
| Variable | AZURE_STORAGE_ACCOUNT | 采用 Azure 时的账户名 |
| Secret | AZURE_SAS_TOKEN | 采用 Azure 时的最小必要权限令牌 |
| Variable | DAGSHUB_USERNAME | 使用 DagsHub HTTP 远端时的用户名 |
| Secret | DAGSHUB_TOKEN | 使用 DagsHub 远端时的只读令牌 |
| Secret | DOCKERHUB_USERNAME | staging/production 的镜像 namespace |
| Secret | DOCKERHUB_TOKEN | staging/production 的镜像推送令牌 |
| Secret | APP_ENV_FILE | staging/production 的多行运行配置 |

Azure 与 DagsHub 凭证只设置所选方案需要的一组。当前 pull_artifacts 若同时发现两者，会优先使用 DagsHub；因此不要为 Azure remote 同时设置 DagsHub 凭证。B 的实际 remote 名和路径必须先核对。

APP_ENV_FILE 示例（没有密码）：

```dotenv
MODEL_PATH=/app/models/release/model.joblib
MODEL_METADATA_PATH=/app/models/release/metadata.json
```

APP_ENV 由流水线根据分支设置为 staging/production，不能用它绕过正式模型校验。文件在 RUNNER_TEMP 生成、按文件要求使用环境配置、不进入镜像或 artifact，任务结束清理。

## 首次接入

1. 导入 B 源码并保留其 Git 历史，核对本应用与其模型契约。
2. 补齐 DVC 指针和远端，安装固定交付依赖并完成真实数据/模型测试。
3. 创建或接入 GitHub，创建 dev/staging/main。
4. 配置三个环境及凭证，明确只允许团队成员向功能分支写入。
5. 提交 feature → dev PR，先跑出 app-checks、real-artifacts 的真实结果。
6. 在保护规则中要求 PR、另一人审查、trust-gate/app-checks/real-artifacts 三项检查通过、禁止强制推送。
7. fork PR 不提供凭证；审查后将修改转到团队分支，运行完整检查后才合并。
8. dev → staging，检查 Delivery，查看镜像与模型校验信息。
9. staging → main，再验证 production 镜像。

两条工作流独立触发；Delivery 自己有 verify → publish 依赖，不能仅凭另一个工作流的旧绿勾发布。没有数据/模型指针时 real-artifacts 和 Delivery 会明确失败，不能静默降级为测试模型。

## 本地 Docker

```powershell
docker build -t sms-spam:local .
docker run -d --name sms-spam-a-local -p 127.0.0.1:8001:8000 -e APP_ENV=production sms-spam:local
python -m scripts.smoke_test --url http://127.0.0.1:8001
docker logs sms-spam-a-local
```

上述默认要求正式模型。仅测试时先生成 work/ci-model，用 `--build-arg MODEL_DIR=work/ci-model` 构建，并设置 APP_ENV=development。测试镜像不能加正式发布标签。

Dockerfile 默认 python:3.12-slim，支持 BASE_IMAGE 参数。若 B 模型确实要求另一 Python 版本，虚拟环境、Docker、CI 应同步修改并重测。原课程的代理路径需要单独核实，不预设可用。

## 镜像追踪

推送 namespace/sms-spam-classifier:staging-完整SHA 或 :production-完整SHA，另保留 staging/production 浮动标签。流水线摘要记录 RepoDigests 和模型 SHA256。运行或回滚优先使用 digest，避免浮动标签发生变化。

## staging 自动部署（尚待主机接入）

CI 内短暂启动容器仅为烟雾检查，不是持续部署。原要求对部署表述存在歧义；默认应完成至少 staging 的真实自动部署。

需要已有 Docker 主机及团队授权。确认后再增加受保护部署任务，流程为：保存旧 digest → 拉取新 digest → 停止旧容器并启动新容器 → 有时限健康检查 → 成功保留；失败则使用旧 digest 恢复。

初始方案允许短暂停机，不能称为零停机。无部署主机时先完成交付，记录待办并向老师确认；不购买新服务、不改动无关容器。

## 排查

- Docker CLI 存在但引擎连接失败：启动 Docker Desktop，确认 Linux 容器引擎，再检查当前 context。
- WindowsApps python/py 无法运行：使用真实解释器绝对路径，创建独立 .venv。
- 模型 503：检查路径、checksum、依赖版本、元数据、artifact_kind；不要关闭 release 校验。
- DVC 认证失败：核对 remote 类型和显式配置；仅 export 任意名称令牌不代表 DVC 自动使用。
- Ruff 扫描 B 代码失败：统一格式或在 PR 分别修复，不关闭全部检查。
- 推送权限失败：核对 Docker namespace 和令牌权限，不把密码传为 Docker build-arg。
- 远端完整测试失败：检查 B 的 v1/v2 实际路径、数据报告和评估集不变约定，不删除断言凑通过。

## 技术依据

Action 标签在实现时按官方 release 页面核对：

- https://github.com/actions/checkout/releases/tag/v7.0.1
- https://github.com/actions/setup-python/releases/tag/v7.0.0
- https://github.com/docker/login-action/releases/tag/v4.6.0

后续更新需要重新验证，不把工作流文件存在等同于远端运行成功。
