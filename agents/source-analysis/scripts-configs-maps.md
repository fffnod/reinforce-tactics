> 返回：[源码总览](overview.md) · [算法总览](../algorithms/overview.md) · [索引](../AGENTS.md)

# 脚本、配置、地图与 Notebooks

本文说明仓库内**训练/评测资产与入口脚本**如何组织，以及脚本 → 算法文档的映射。

---

## 位置

| 路径 | 角色 |
|------|------|
| `scripts/train/` | 进阶训练 CLI |
| `scripts/tournament.py` | 锦标赛 CLI |
| `scripts/cloud/` | Vertex / 容器训练辅助 |
| `scripts/build_bc_warmstart.py` | 行为克隆热启动 |
| `scripts/eval_agent.py` | 独立评估 |
| `configs/` | YAML 超参与课程 |
| `maps/` | CSV 地图 |
| `notebooks/` | 交互实验与分析 |
| `main.py` + `cli/commands.py` | 通用 play / 简易 train / evaluate / stats |

---

## 文件清单

### `scripts/train/*`

| 脚本 | 调用核心 | 典型配置 |
|------|----------|----------|
| `train_bootstrap.py` | `run_curriculum` | `configs/ppo/bootstrap.yaml` |
| `train_self_play.py` | self-play + MaskablePPO | `configs/self_play/self_play.yaml` |
| `train_feudal_rl.py` | `FeudalRLAgent` | `configs/feudal/feudal_rl.yaml` |
| `train_alphazero.py` | AlphaZero trainer | `configs/alphazero/alphazero.yaml` |

### 其他常用脚本

| 脚本 | 用途 |
|------|------|
| `scripts/tournament.py` | 循环赛 |
| `scripts/build_bc_warmstart.py` | BC → `.zip` 供 warm_start |
| `scripts/eval_agent.py` | 加载模型评估 |
| `scripts/ab_feudal_ar.py` | Feudal AR 对照 |
| `scripts/cloud/vertex_train.py` | 云训练入口 |
| `scripts/cloud/build_image.sh` / `submit_vertex_job.sh` | 镜像与提交 |
| `scripts/generate_map_previews.py` / `generate_unit_gifs.py` | 文档/站点资源 |
| `scripts/run_tournament.sh` / `monitor_training.sh` | Shell 包装 |

### `configs/` 布局

```text
configs/
  README.md
  ppo/
    maskable_ppo.yaml
    ppo_baseline.yaml
    bootstrap.yaml              # 生产课程入口
    bootstrap_validation.yaml
    skirmish_bc_selfplay.yaml
    bootstrap_sweep/v*.yaml     # 扫参变体
  feudal/
    feudal_rl.yaml
  self_play/
    self_play.yaml
  alphazero/
    alphazero.yaml
  imitation/
    bc_scenarios.yaml
    bc_beginner_warmstart.yaml
    bc_skirmish_warmstart.yaml
```

加载：`reinforcetactics.rl.config.load_config` + `apply_overrides`（点号键）。未知键严格报错。

### `maps/` 布局

```text
maps/
  1v1/          # 主力训练与 GUI（starter, beginner, skirmish, …）
  1v1v1/        # 三人混战（主要 GUI）
  2v2/          # 组队（主要 GUI）
```

- 格式：CSV 字符地形（`p/w/m/f/r/b/h/t` 等，与 `TILE_TYPE_ORDER` / `FileIO` 一致）。
- RL Env **仅保证 1v1** 观察编码；课程地图应来自 `maps/1v1/`。
- 场景存档可参考 `saves/*_scenario.json`。

### `notebooks/` 角色

| Notebook | 角色 |
|----------|------|
| `ppo_bootstrap.ipynb` | 课程训练交互 / 曲线 |
| `ppo_training.ipynb` | 通用 PPO 实验 |
| `feudal_rl_training.ipynb` | Feudal 训练 |
| `bootstrap_run_analysis.ipynb` | 多 run 对比 |
| `balance_analysis.ipynb` | 数值平衡 |
| `bot_tournament.ipynb` / `llm_bot_tournament.ipynb` | 赛事后处理 |
| `kaggle_environments_smoke_test.ipynb` | 环境冒烟 |

Notebook 调用与 CLI 相同的 Python API，不另立训练实现。

---

## 职责

| 资产 | 职责 |
|------|------|
| **scripts** | 可复现的一键入口；解析 `--config` 与 CLI 覆盖 |
| **configs** | 超参、课程阶段、奖励与对手阶梯的版本化来源 |
| **maps** | 关卡几何与出生点；影响难度与观察形状 |
| **notebooks** | 探索、绘图、断线后续分析；非生产唯一路径 |

---

## 数据结构

### 配置顶层分区（`TrainingConfig`）

`env` · `ppo` · `feudal` · `self_play` · `alphazero` · `curriculum` · `eval` · `logging` · `seed` · `warm_start_path`

详见 [rl-training-pipelines.md](rl-training-pipelines.md) 与 `configs/README.md`。

### 地图

- 磁盘：CSV。
- 内存：`pandas.DataFrame` / `GameState` 内部网格。
- 课程跨尺寸：bootstrap 解析 `pad_to_size`（需 `flat_discrete`）。

---

## 核心逻辑

### 脚本 → 目的 → 算法文档

| 脚本 | 目的 | 算法文档 |
|------|------|----------|
| `main.py --mode train` | 简易 SB3 PPO/A2C/DQN | [ppo.md](../algorithms/ppo.md) |
| `scripts/train/train_bootstrap.py` | MaskablePPO 多阶段课程 | [curriculum-bootstrap.md](../algorithms/curriculum-bootstrap.md) · [ppo.md](../algorithms/ppo.md) |
| `scripts/train/train_self_play.py` | 自对弈 / 对手池 | [self-play.md](../algorithms/self-play.md) |
| `scripts/train/train_feudal_rl.py` | Manager-Worker | [feudal-rl.md](../algorithms/feudal-rl.md) |
| `scripts/train/train_alphazero.py` | MCTS + 策略价值网 | [alphazero-mcts.md](../algorithms/alphazero-mcts.md) |
| `scripts/build_bc_warmstart.py` | 示教克隆热启动 | [behavior-cloning.md](../algorithms/behavior-cloning.md) |
| `scripts/eval_agent.py` | 固定对手评估 | [evaluation-and-elo.md](../algorithms/evaluation-and-elo.md) |
| `scripts/tournament.py` | 多 Bot Elo 循环赛 | [evaluation-and-elo.md](../algorithms/evaluation-and-elo.md) · [game-bots.md](game-bots.md) |
| `scripts/cloud/vertex_train.py` | 云上跑上述训练 | 部署见 `docs/vertex_training.md` |

### 推荐调用模式

```bash
# 生产课程
python scripts/train/train_bootstrap.py --config configs/ppo/bootstrap.yaml

# 覆盖示例
python scripts/train/train_bootstrap.py --config configs/ppo/bootstrap.yaml \
  --override ppo.learning_rate=1e-4

# 锦标赛
python scripts/tournament.py --map-dir maps/1v1/ --map-pool-mode cycle --no-llm
```

（具体 CLI 标志以各脚本 `argparse` 为准。）

### 云路径

`scripts/cloud/`：构建训练镜像 → `submit_vertex_job.sh` 提交 → `vertex_train.py` 内调 bootstrap/feudal 等。依赖可选 extra `cloud`。

---

## 与需求关系

| 需求 | 落点 |
|------|------|
| 可复现实验 | 固定 YAML + seed + 版本化 bootstrap_sweep |
| 换地图难度 | 改 `curriculum.stages[].map_file` 或 `env.map_file` |
| 不改代码扫参 | `configs/ppo/bootstrap_sweep/` |
| 离线对比模型 | `eval_agent` / `tournament` |
| 文档与演示素材 | `generate_*` + `notebooks` |

---

## 相关算法

见上表。环境约束（1v1、动作空间）见 [rl-gym-env.md](rl-gym-env.md)；总览见 [overview.md](overview.md) §3。

---

## 延伸阅读

- `configs/README.md`
- `docs/vertex_training.md`、`docs/LOCAL_DEPLOY.md`
- 地图用户说明：`docs-site/docs/maps.mdx`
- 源码管线：[rl-training-pipelines.md](rl-training-pipelines.md) · [rl-advanced-trainers.md](rl-advanced-trainers.md) · [tournament-system.md](tournament-system.md)
