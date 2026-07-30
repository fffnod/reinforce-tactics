# 附录 B　命令、配置与参数参考

## B.1 统一执行环境

本书验收基线：

```text
日期                  2026-07-29
Conda 环境            reinforce-tactics
Python                3.12.13
Gymnasium             1.3.0
Stable-Baselines3     2.9.0
sb3-contrib           2.9.0
PyTorch               2.13.0+cpu
```

在未激活环境时，所有命令可加前缀：

```powershell
conda run -n reinforce-tactics python <script> <arguments>
```

先确认版本：

```powershell
conda run -n reinforce-tactics python -c `
  "import sys,gymnasium,stable_baselines3,sb3_contrib,torch; print(sys.version); print(gymnasium.__version__,stable_baselines3.__version__,sb3_contrib.__version__,torch.__version__)"
```

本书不包含 Cloud/Vertex 执行命令，也不要求任何 LLM API key。

## B.2 教材构建

生成静态图：

```powershell
conda run -n reinforce-tactics python `
  agents/learning-guide-v2/tools/generate_figures.py
```

运行所有教材冒烟：

```powershell
conda run -n reinforce-tactics python `
  agents/learning-guide-v2/tools/smoke_labs.py
```

只运行一个项目：

```powershell
conda run -n reinforce-tactics python `
  agents/learning-guide-v2/tools/smoke_labs.py --only masks
```

允许的 `--only` 值由脚本固定，发布版包括环境、掩码、算法兼容、MaskablePPO、MCTS/AlphaZero 等低成本检查。

构建同源 HTML 与 PDF：

```powershell
conda run -n reinforce-tactics python `
  agents/learning-guide-v2/tools/build_book.py
```

PDF 构建阶段使用 Chromium/Edge 打印同源 HTML，使 MathML 公式在 PDF 中保留真正的上下标、分式、根号和希腊字母。构建器自动查找系统 Chrome/Edge；非标准安装位置可通过 `GUIDE_BROWSER` 指定。还需保证 Node.js 能解析 Playwright，Codex 工作区运行时已内置该依赖。

验证章节、链接、图片、算法覆盖、HTML、PDF 文本与书签：

```powershell
conda run -n reinforce-tactics python `
  agents/learning-guide-v2/tools/verify_book.py
```

输出位置：

```text
agents/learning-guide-v2/export/Reinforce-Tactics-RL-Learning-Guide-combined.md
agents/learning-guide-v2/export/Reinforce-Tactics-RL-Learning-Guide.html
output/pdf/Reinforce-Tactics-RL-Learning-Guide-v2.pdf
```

## B.3 测试命令

完整测试和覆盖率：

```powershell
conda run -n reinforce-tactics pytest
```

环境、观察和动作：

```powershell
conda run -n reinforce-tactics pytest -q `
  tests/test_rl_env.py `
  tests/test_rl_observation.py `
  tests/test_rl_action_mask.py `
  --no-cov
```

具体测试文件名以仓库当前文件为准。本教材验证器会检查正文引用路径是否存在；若测试重命名，应同步更新教材命令。

Feudal：

```powershell
conda run -n reinforce-tactics pytest -q `
  tests/test_feudal_rl.py `
  tests/test_feudal_rl_integration.py `
  --no-cov
```

AlphaZero：

```powershell
conda run -n reinforce-tactics pytest -q `
  tests/test_alphazero.py `
  --no-cov
```

LLM mock：

```powershell
conda run -n reinforce-tactics pytest -q `
  tests/test_llm_bot.py `
  tests/test_llm_prompts.py `
  --no-cov
```

Tournament 与 replay：

```powershell
conda run -n reinforce-tactics pytest -q `
  tests/test_tournament_library.py `
  tests/test_tournament_config.py `
  tests/test_tournament.py `
  tests/test_save_replay.py `
  tests/test_replay_determinism.py `
  --no-cov
```

`--no-cov` 只用于局部快速反馈。最终验收运行完整 `pytest`，接受 `pyproject.toml` 中 65% 覆盖率门槛。

## B.4 环境构造参数

`StrategyGameEnv` 的关键概念字段：

| 参数 | 类型 | 用途 |
|---|---|---|
| `map_file` | 路径或 `None` | 固定 CSV 地图或随机地图 |
| `opponent` | 字符串 | 规则 Bot / 模型对手类型 |
| `opponent_kwargs` | 字典 | 对手构造参数 |
| `max_steps` | 整数 | 环境微动作截断上限 |
| `max_turns` | 整数或 `None` | 游戏回合上限 |
| `max_actions_per_turn` | 整数或 `None` | 单游戏回合的智能体微动作上限 |
| `action_space_type` | 字符串 | `multi_discrete` 或 `flat_discrete` |
| `max_flat_actions` | 整数 | Flat 路径合法动作容量/防护参数 |
| `fog_of_war` | 布尔 | 是否启用局部可见性 |
| `enabled_units` | 列表或 `None` | 允许单位代码 |
| `pad_to_size` | 二元组或 `None` | 跨地图统一观察尺寸 |
| `reward_config` | 字典或 `None` | 奖励分量 |
| `engine_overrides` | 字典或 `None` | 经济、单位数据等稀疏覆盖 |
| `gold_scale` | 浮点 | 全局金币特征归一化尺度 |
| `turn_scale` | 浮点 | 回合特征尺度 |
| `unit_count_scale` | 浮点 | 单位数量尺度 |
| `render_mode` | 字符串或 `None` | 训练通常为 `None` |

最小交互：

```python
from reinforcetactics.rl.gym_env import StrategyGameEnv

env = StrategyGameEnv(
    map_file="maps/1v1/starter.csv",
    opponent="noop",
    max_steps=64,
    action_space_type="multi_discrete",
    render_mode=None,
)

obs, info = env.reset(seed=0)
action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
env.close()
```

若使用掩码，随机采样必须从合法分布产生；直接 `action_space.sample()` 主要用于接口压力测试，会产生大量无效组合。

## B.5 PPO 与 MaskablePPO 参数

| 参数 | 含义 | 影响 |
|---|---|---|
| `learning_rate` | 优化器步长 | 过大不稳，过小学习慢 |
| `n_steps` | 每环境每次 rollout 步数 | 越大回报统计更长、更新更慢 |
| `batch_size` | minibatch 大小 | 必须适配 rollout 样本数 |
| `n_epochs` | 同一 rollout 重用轮数 | 过大可能使策略偏离旧策略 |
| `gamma` | 折扣 | 越高重视更远回报 |
| `gae_lambda` | GAE 参数 | 调节偏差—方差 |
| `clip_range` | PPO 裁剪宽度 | 限制有利方向更新收益 |
| `ent_coef` | 熵系数 | 鼓励探索 |
| `vf_coef` | 价值损失系数 | 平衡 critic 与 actor |
| `max_grad_norm` | 梯度范数上限 | 防止单次极端更新 |
| `policy_kwargs` | 网络与 extractor | 决定表示能力 |
| `device` | `cpu/cuda/auto` | 运行设备 |

rollout 大小：

\[
N_{\text{rollout}}=n_{\text{steps}}\times n_{\text{envs}}
\]

例如 4 个环境、`n_steps=256`，一次更新收集 1024 个样本。`batch_size=64` 时每 epoch 约 16 个 minibatch。

MaskablePPO 要求：

- 环境暴露 `action_masks()`；
- 训练采样使用 MaskablePPO；
- 评估使用 `MaskableEvalCallback` 或显式向 `predict` 传 `action_masks`；
- 自定义 SubprocVecEnv 场景中，掩码方法要存在于子环境内部。

## B.6 MaskablePPO 最小配置

教材 `labs/maskable-ppo-smoke.yaml` 的目标是短训练，不是推荐正式超参数：

```yaml
algorithm: maskable_ppo
total_timesteps: 64
seed: 0
env:
  map_file: maps/1v1/starter.csv
  opponent: noop
  max_steps: 64
  max_turns: 12
  action_space_type: multi_discrete
  n_envs: 1
ppo:
  learning_rate: 0.0003
  n_steps: 32
  batch_size: 16
  n_epochs: 1
  gamma: 0.99
  gae_lambda: 0.95
  clip_range: 0.2
  ent_coef: 0.01
  vf_coef: 0.5
  max_grad_norm: 0.5
  device: cpu
```

短预算把 `n_epochs` 降为 1 以减少 CPU 时间；不能据此比较最终性能。

## B.7 Bootstrap

运行教材最小课程：

```powershell
conda run -n reinforce-tactics python `
  scripts/train/train_bootstrap.py `
  --config agents/learning-guide-v2/labs/bootstrap-smoke.yaml `
  --output-dir tmp/learning-guide-v2/bootstrap `
  --device cpu `
  --skip-plots `
  --skip-videos `
  --sanity-episodes 0 `
  --no-gcs
```

通用入口：

```powershell
conda run -n reinforce-tactics python `
  scripts/train/train_bootstrap.py `
  --config configs/ppo/bootstrap.yaml `
  --output-dir benchmarks/bootstrap/local-run `
  --device cpu `
  --set ppo.learning_rate=0.0003 `
  --skip-videos `
  --no-gcs
```

重要 CLI：

| 参数 | 作用 |
|---|---|
| `--config` | Bootstrap YAML |
| `--output-dir` | run 目录 |
| `--device` | `cpu/cuda/auto` |
| `--set KEY=VALUE` | 可重复的点路径覆盖 |
| `--build-bc` | 课程前创建 BC warm start |
| `--bc-scenarios` | 示范场景 YAML |
| `--bc-epochs` | BC epoch |
| `--skip-plots` | 跳过图 |
| `--skip-videos` | 跳过 replay 视频 |
| `--sanity-episodes` | 最终 sanity eval 局数，0 跳过 |
| `--no-gcs` | 强制不上传；本书本地实验使用 |

阶段配置常见字段：

```yaml
curriculum:
  stages:
    - name: starter_noop
      map_file: maps/1v1/starter.csv
      opponent: noop
      promotion_win_rate: 0.0
      n_eval_episodes: 2
      eval_freq: 32
      max_timesteps: 64
      patience: 1
```

正式训练需要合理的 `promotion_win_rate`、`min_timesteps_before_promotion`、`patience`、`eval_freq`、评估局数和阶段预算。门槛为 0 只验证控制流。

## B.8 行为克隆

构建 checkpoint：

```powershell
conda run -n reinforce-tactics python `
  scripts/build_bc_warmstart.py `
  --scenarios configs/imitation/bc_beginner_warmstart.yaml `
  --curriculum-config configs/ppo/bootstrap_sweep/v33_production_bc_warmstart.yaml `
  --output tmp/learning-guide-v2/bc/bc_warmstart.zip `
  --epochs 1 `
  --batch-size 32 `
  --learning-rate 0.0003 `
  --seed 0 `
  --map-file maps/1v1/beginner.csv `
  --enabled-units W M C A K `
  --max-turns 75 `
  --end-turn-weight 30
```

参数解释：

- `--scenarios`：示范对手、地图和采样组合；
- `--curriculum-config`：读取下游 PPO 的 extractor 与 net architecture，保证精确加载；
- `--output`：生成的 MaskablePPO checkpoint；
- `--epochs`、`--batch-size`、`--learning-rate`：监督训练；
- `--seed`：示范与训练随机种子；
- `--end-turn-weight`：结束回合样本权重，修正示范类别不均衡；
- `--enabled-units`、`--map-file`、`--max-turns`：必须与下游空间匹配。

`--end-turn-weight=1` 关闭额外加权。自动值或较大权重用于对抗“永不结束回合”的类别不平衡吸引子，但必须用 held-out expert action accuracy 和实际 rollout 共同验证。

## B.9 自对弈

下列命令是完整 mixed 训练入口。`n_envs` 必须至少为 2，因为脚本会把环境分别分配给规则 Bot 与自对弈对手。当前基准环境还需要安装 SB3 进度条的可选依赖 `rich` 与 `tqdm`；若没有这两个包，脚本会在创建进度条时退出，而不是进入训练：

```powershell
conda run -n reinforce-tactics python `
  scripts/train/train_self_play.py `
  --config agents/learning-guide-v2/labs/self-play-smoke.yaml `
  --mode mixed `
  --use-opponent-pool `
  --pool-size 2 `
  --pool-strategy uniform `
  --n-envs 2 `
  --no-subprocess `
  --total-timesteps 64 `
  --n-steps 32 `
  --batch-size 16 `
  --n-epochs 1 `
  --eval-freq 64 `
  --n-eval-episodes 1 `
  --checkpoint-freq 64 `
  --device cpu `
  --log-dir tmp/learning-guide-v2/self-play
```

教材的零依赖冒烟验证不安装额外软件，而是直接检查历史池、采样权重、换边环境、动作掩码以及一步交互：

```powershell
conda run -n reinforce-tactics python `
  agents/learning-guide-v2/tools/smoke_labs.py `
  --only self-play
```

这一组件级命令不等价于完成一次策略更新；它的目的，是把“自对弈数据管线可用”和“完整 CLI 在当前依赖集下可以运行”区分开来。

池参数：

| 参数 | 含义 |
|---|---|
| `--opponent-update-freq` | 当前对手更新间隔 |
| `--use-opponent-pool` | 启用历史池 |
| `--pool-size` | 最大快照数 |
| `--pool-strategy` | `uniform/recent/prioritized` |
| `--add-to-pool-freq` | 添加候选快照间隔 |
| `--min-win-rate-for-pool` | 加入池的门槛 |
| `--bot-ratio` | mixed 模式规则 Bot 比例 |
| `--swap-players` | 随 episode 换边；当前帮助显示默认开启 |

只有 64 步时，池可能还没到添加周期。教材冒烟会直接测试池对象，不能把“训练命令退出成功”当成已验证历史采样。

## B.10 Feudal

运行：

```powershell
conda run -n reinforce-tactics python `
  scripts/train/train_feudal_rl.py `
  --mode feudal `
  --config agents/learning-guide-v2/labs/feudal-smoke.yaml
```

关键参数：

| 参数 | 含义 |
|---|---|
| `manager_horizon` | 一个目标持续的最大微动作数 |
| `worker_reward_alpha` | 外在奖励在 Worker 合成奖励中的乘数 |
| `manager_lr_scale` | Manager 相对基础学习率 |
| `worker_lr_scale` | Worker 相对基础学习率 |
| `autoregressive_worker` | 使用阶段条件 Worker |
| `reward_scale` | 外在奖励进入层级 buffer 前的缩放 |

当前 Worker 公式：

\[
r^W=r^{int}
+\texttt{worker\_reward\_alpha}\times
\texttt{reward\_scale}\times r^{env}
\]

不要把 alpha 当作 \((1-\alpha,\alpha)\) 插值。

## B.11 AlphaZero

完整脚本入口：

```powershell
conda run -n reinforce-tactics python `
  scripts/train/train_alphazero.py `
  --map-file maps/1v1/starter.csv `
  --res-blocks 1 `
  --channels 16 `
  --num-simulations 1 `
  --c-puct 1.5 `
  --dirichlet-alpha 0.3 `
  --iterations 1 `
  --games-per-iter 1 `
  --epochs-per-iter 1 `
  --batch-size 2 `
  --buffer-size 128 `
  --max-game-steps 4 `
  --temperature-threshold 2 `
  --eval-games 0 `
  --eval-threshold 0.55 `
  --lr 0.001 `
  --weight-decay 0.0001 `
  --checkpoint-dir tmp/learning-guide-v2/alphazero `
  --device cpu
```

如果只验证搜索而不希望候选比赛耗时，使用：

```powershell
conda run -n reinforce-tactics python `
  agents/learning-guide-v2/tools/smoke_labs.py --only mcts
```

关键参数：

| 参数 | 作用 |
|---|---|
| `--res-blocks`、`--channels` | 网络容量 |
| `--num-simulations` | 每真实动作搜索次数 |
| `--c-puct` | PUCT 探索 |
| `--dirichlet-alpha` | 根噪声形态 |
| `--games-per-iter` | 每轮自对弈局数 |
| `--epochs-per-iter` | buffer 训练轮数 |
| `--buffer-size` | 历史样本容量 |
| `--temperature-threshold` | 一局内从采样转向贪心的步数 |
| `--eval-games` | 候选对最佳对局数 |
| `--eval-threshold` | 接受候选胜率 |

## B.12 评估

查看精确接口：

```powershell
conda run -n reinforce-tactics python scripts/eval_agent.py --help
```

库接口：

```python
from reinforcetactics.rl.evaluation import evaluate_model

result = evaluate_model(
    model,
    env,
    n_episodes=100,
    deterministic=True,
    seed=10_000,
    track_breakdown=True,
    trace_dir="tmp/eval/traces",
    trace_end_reasons=("max_steps_truncate",),
)
```

正式报告保存 `rewards`、`lengths` 原始数组，而不只保留均值。

## B.13 Tournament

查看入口：

```powershell
conda run -n reinforce-tactics python scripts/tournament.py --help
```

配置核心：

```json
{
  "name": "local-bot-ladder",
  "maps": [
    {"path": "maps/1v1/starter.csv", "max_turns": 50}
  ],
  "games_per_side": 2,
  "map_pool_mode": "all",
  "output_dir": "tmp/learning-guide-v2/tournament",
  "save_replays": true,
  "rng_seed": 20260729,
  "concurrent_games": 1
}
```

`rng_seed` 使整体可复现，同时让同一对阵的多局在 tie-break 上产生差异。没有 RNG 的确定性 Bot 可能重复完全相同轨迹。

## B.14 TensorBoard

从 run 根目录启动：

```powershell
conda run -n reinforce-tactics tensorboard `
  --logdir tmp/learning-guide-v2 `
  --port 6006
```

重点指标：

- `rollout/ep_rew_mean`、`ep_len_mean`；
- `train/entropy_loss`；
- `train/value_loss`；
- `train/approx_kl`；
- `train/clip_fraction`；
- `train/explained_variance`；
- 课程阶段胜率、终局原因；
- Feudal 两层 loss 与奖励分量；
- AlphaZero policy/value loss。

不同奖励配置的 `ep_rew_mean` 不能直接横向比较。

## B.15 配置覆盖与审计

Bootstrap `--set` 示例：

```powershell
--set ppo.learning_rate=0.0001
--set env.enabled_units='[W,M,C,A,K]'
--set env.reward_config.draw=-50
```

PowerShell 中列表和字符串的引号要保留给 Python 解析。运行后检查 resolved config，而不是仅相信命令行输出。

配置审计清单：

1. 地图存在；
2. 所有阶段空间形状一致，或正确 padding；
3. warm start 的网络与空间完全匹配；
4. reward 字段进入环境；
5. engine override 已应用；
6. 评估对手与训练对手按设计分离；
7. `max_steps` 与 `max_turns` 的单位没有混淆；
8. 掩码训练与评估均开启；
9. 输出目录不覆盖旧 run；
10. 版本、种子和完整解析配置落盘。
