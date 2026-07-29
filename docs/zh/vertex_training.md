# 在 Vertex AI 上进行云端训练

使用项目的 Docker 镜像与 Vertex AI **自定义任务（custom jobs）**，在 Google Cloud 上跑长时间训练。流程是：镜像构建一次并推送到 Artifact Registry，再用一条 CLI 提交任务。Vertex 会拉起 GPU 机器、执行训练命令（可能数小时到数天）、流式日志，结束后销毁机器。

机器是临时的，因此镜像入口（[`scripts/cloud/vertex_train.py`](../../scripts/cloud/vertex_train.py)）会把输出目录（`models/`、`checkpoints/`、`tensorboard/`、`logs/`）**周期性且在退出时** 上传到 Google Cloud Storage，这样任务结束（或被抢占/取消）后模型仍可保留。

> 优先使用下文的托管方案，而不是旧版 GCE VM 启动脚本（`scripts/gcp_launch.sh`）手动管裸实例。

## 前置条件

- 已开通计费的 GCP 项目。
- 已安装并登录 [`gcloud` CLI](https://cloud.google.com/sdk/docs/install)（`gcloud auth login`、`gcloud config set project PROJECT_ID`）。
- 启用这些 API：
  ```bash
  gcloud services enable aiplatform.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
  ```
- 用于输出的 GCS 桶（与任务同区域性能更好）：
  ```bash
  gcloud storage buckets create gs://YOUR_BUCKET --location=us-central1
  ```
- 该区域有 GPU 配额（例如 `us-central1` 的 `NVIDIA_TESLA_T4`）。在 *IAM 与管理 → 配额* 中查看，不足则申请。

## 1. 构建并推送镜像

```bash
PROJECT_ID=your-project REGION=us-central1 ./scripts/cloud/build_image.sh
```

使用 **Cloud Build**（本地不必装 Docker），首次运行会创建 Artifact Registry 仓库 `reinforce-tactics`，并推送：

```
us-central1-docker.pkg.dev/your-project/reinforce-tactics/rl-trainer:latest
```

可通过环境变量覆盖 `AR_REPO`、`IMAGE_NAME`、`TAG`、`BUILD_TIMEOUT`。本地构建：

```bash
docker build -t us-central1-docker.pkg.dev/your-project/reinforce-tactics/rl-trainer:latest .
docker push   us-central1-docker.pkg.dev/your-project/reinforce-tactics/rl-trainer:latest
```

## 2. 提交训练任务

脚本名之后的参数即为容器内执行的训练命令。镜像入口会包一层 GCS 同步。

```bash
# 通过 main.py 跑 PPO
BUCKET=YOUR_BUCKET ./scripts/cloud/submit_vertex_job.sh \
  python3 main.py --mode train --algorithm ppo --timesteps 10000000 --opponent bot

# Feudal RL 高级脚本，带 action masking 与 W&B
WANDB_API_KEY=$WANDB_API_KEY BUCKET=YOUR_BUCKET \
  ./scripts/cloud/submit_vertex_job.sh \
  python3 scripts/train/train_feudal_rl.py --mode feudal --total-timesteps 20000000 \
    --n-envs 8 --device cuda --use-action-masking --wandb

# 使用 configs/ 下 YAML
BUCKET=YOUR_BUCKET ./scripts/cloud/submit_vertex_job.sh \
  python3 scripts/train/train_feudal_rl.py --config configs/feudal/feudal_rl.yaml --device cuda
```

`BUCKET` 必填。产物路径：`gs://BUCKET/jobs/<JOB_NAME>/{models,checkpoints,tensorboard,logs}/`。

### 在 CLI 上选择配置

通过提交脚本透传训练命令自身的参数。支持 `--config <yaml>` 的入口：

| 入口 | 支持 `--config`？ |
|---|---|
| `scripts/train/train_bootstrap.py`（课程） | ✅ |
| `scripts/train/train_feudal_rl.py` | ✅ |
| `scripts/train/train_alphazero.py` | ✅ |
| `scripts/train/train_self_play.py` | ✅ |
| `main.py`（`--mode train`） | ❌ — 仅独立参数（`--algorithm`、`--timesteps` 等） |

### Curriculum bootstrap — 图表与视频

`scripts/train/train_bootstrap.py` 是 `notebooks/ppo_bootstrap.ipynb` 的 headless CLI 镜像：跑课程（`run_curriculum`）、写诊断图（`viz.plot_*`）、每阶段录回放视频（`.mp4`）——与 notebook 相同产物，去掉 Colab/Drive 部分。镜像已带 matplotlib、pygame、opencv、imageio+ffmpeg，并强制 headless（`SDL_VIDEODRIVER=dummy`、`MPLBACKEND=Agg`），可无人值守。

```bash
# 在 Vertex 上复现 ppo_bootstrap 流水线
BUCKET=YOUR_BUCKET ./scripts/cloud/submit_vertex_job.sh \
  python3 scripts/train/train_bootstrap.py \
    --config configs/ppo/bootstrap.yaml --device cuda

# 带 BC warm-start（需 multi_discrete 配置），例如 v33 sweep
BUCKET=YOUR_BUCKET ./scripts/cloud/submit_vertex_job.sh \
  python3 scripts/train/train_bootstrap.py \
    --config configs/ppo/bootstrap_sweep/v33_production_bc_warmstart.yaml \
    --build-bc --device cuda
```

脚本把所有内容写到一个 run 目录（默认 `benchmarks/bootstrap/<timestamp>/`）——`charts/`、`videos/`、`checkpoints/`、配置快照、`bootstrap_results.csv`、`final_model.zip`——结束时（含卡死）整树上传到 `gs://BUCKET/jobs/<JOB_NAME>/<timestamp>/`。常用标志：`--skip-videos`、`--skip-plots`、`--sanity-episodes N`、`--set dotted.key=value`、`--gcs-output gs://...`。完整列表见 `python3 scripts/train/train_bootstrap.py --help`。拉取结果：

```bash
gcloud storage cp -r gs://YOUR_BUCKET/jobs/JOB_NAME ./bootstrap_run
```

### 配置（环境变量）

| 变量 | 默认 | 用途 |
|---|---|---|
| `PROJECT_ID` | 当前 gcloud 项目 | GCP 项目 |
| `REGION` | `us-central1` | 任务与镜像区域 |
| `BUCKET` | *（必填）* | 输出 GCS 桶（名称或 `gs://` URI） |
| `JOB_NAME` | `rt-train-<timestamp>` | 显示名与输出子目录 |
| `IMAGE_URI` | 推导 | 完整镜像 URI（覆盖 `AR_REPO`/`IMAGE_NAME`/`TAG`） |
| `MACHINE_TYPE` | `n1-highmem-8` | Worker 机型 |
| `ACCELERATOR_TYPE` | `NVIDIA_TESLA_T4` | GPU 类型 |
| `ACCELERATOR_COUNT` | `1` | 每副本 GPU 数（`0` = 仅 CPU） |
| `REPLICA_COUNT` | `1` | Worker 副本数 |
| `SYNC_INTERVAL` | `300` | GCS 同步间隔秒（`0` = 仅退出时） |
| `SERVICE_ACCOUNT` | *（未设）* | 以该服务账号运行任务 |
| `WANDB_API_KEY` | *（未设）* | 若设置则传入容器 |

## 3. 监控任务

```bash
gcloud ai custom-jobs list --region=us-central1
gcloud ai custom-jobs stream-logs JOB_ID --region=us-central1
```

也可在 Cloud Console *Vertex AI → 训练 → 自定义任务* 中查看。

## 4. 取回训练好的模型

```bash
gcloud storage ls   gs://YOUR_BUCKET/jobs/JOB_NAME/
gcloud storage cp -r gs://YOUR_BUCKET/jobs/JOB_NAME/models ./models
```

本地评估：

```bash
python main.py --mode evaluate --model models/ppo_final.zip --episodes 20
```

## 产物持久化如何工作

容器入口是包装器，不是直接训练命令：

```dockerfile
ENTRYPOINT ["python3", "scripts/cloud/vertex_train.py"]
CMD ["python3", "main.py", "--mode", "train"]
```

包装器会：

1. 从 `GCS_OUTPUT_URI`（提交脚本设置）解析 GCS 目标，否则回退 `AIP_MODEL_DIR`。都没有则只本地跑——同一镜像也可在笔记本上用。
2. 以子进程运行训练命令。
3. 每 `GCS_SYNC_INTERVAL` 秒上传 `models/`、`checkpoints/`、`tensorboard/`、`logs/` 到 `gs://.../jobs/<name>/<dir>/`。
4. 将 `SIGTERM`/`SIGINT`（Vertex 取消/抢占发 `SIGTERM`）转发给训练进程以便 checkpoint，退出前做 **最终同步**。

上传为尽力而为：短暂存储故障只记日志，不导致任务失败。

## IAM / 权限

默认自定义任务以 **Vertex AI Custom Code Service Agent** 运行。GCS 上传成功需要该身份（或你传入的 `SERVICE_ACCOUNT`）对桶有写权限：

```bash
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/storage.objectAdmin"
```

## 故障排查

| 现象 | 可能原因 / 处理 |
|---|---|
| `google-cloud-storage not installed; skipping GCS sync` | 镜像未装 `[cloud]` extra。用 `build_image.sh` 重建（`Dockerfile` 会安装）。 |
| 任务在跑但桶仍空 | 服务账号缺少桶上的 `storage.objectAdmin`（见上文 IAM）。 |
| 提交时 `Quota exceeded` | 申请该区域 GPU 配额，或 `ACCELERATOR_COUNT=0` 做 CPU 冒烟。 |
| Cloud Build 超时 | 提高 `BUILD_TIMEOUT`（如 `BUILD_TIMEOUT=7200s`）。 |
| 想在镜像里开 shell | `docker run --entrypoint bash -it IMAGE_URI`（绕过包装器）。 |
