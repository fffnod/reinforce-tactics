# Feudal RL 设置评审

## 总体评估
架构状态良好：干净的 Manager/Worker 拆分，共享 encoder 由单一 optimizer 驱动（manager 梯度从 encoder detach），感知 segment 长度的 GAE，对遗留 6-head 与 AlphaStar 风格自回归 worker 的完整 mask 贯通，以及暴露 `FeudalRLAgent` 全套特性的 YAML/CLI 界面。

本轮关闭了上一轮评审标出的缺口。下文是当前状态——已修复项、仍开放项，以及剩余工作的优先级。

---

## 本轮已修复

| 问题 | 位置 | 说明 |
|---|---|---|
| `compute_intrinsic_reward` 中未使用的 `state` 参数 | `feudal_rl.py:1599` | 签名现为 `(next_state, goal)`；已移除 `agent_player`（obs 相对 agent）。 |
| `_last_obs` 未安全初始化 | `feudal_rl.py:1219` | 当 `_last_obs is None` 时，`collect_rollout` 首次调用会自动 reset 环境。 |
| `evaluate` 可能引用未绑定的 `info` | `feudal_rl.py:1605` | 在 `while not done` 循环前初始化 `info = {}`。 |
| `n_worker <= 1` 时 worker advantage 归一化 | `feudal_rl.py:1418` | 现与 `m_adv` 采用相同防护。 |
| 环境缺少 `structured_action_masks` 时 AR worker 静默 | `feudal_rl.py:1226` | 一次性 `RuntimeWarning`；显式回退到无 mask 的 AR 采样。 |
| AR 模式下无意义的 per-dim mask 捕获 | `feudal_rl.py:1248` | `env_supports_masks` 现与 `not use_ar_masks` 做 AND。 |
| Checkpoint 丢失运行时配置（`manager_horizon`、`agent_player`） | `feudal_rl.py:1525` | `save_checkpoint` 写入 `hyperparams` 字典；`load_checkpoint` 恢复 `manager_horizon`/`agent_player`，grid 维度不匹配时拒绝加载。 |
| `load_checkpoint` 中陈旧的向后兼容分支 | `feudal_rl.py` | 已删除无效的 `optimizer` 回退。 |
| 训练脚本无法到达 `autoregressive_worker` | `train_feudal_rl.py:401`，`configs/feudal/feudal_rl.yaml:30` | 新增 `--autoregressive-worker` CLI 标志与 `feudal.autoregressive_worker` YAML 键，接入 `FeudalRLAgent(...)`。 |
| feudal 训练路径缺少 seeding | `train_feudal_rl.py:198-205` | 对 python `random`、numpy、torch、CUDA 以及两次 env reset 做 seed。 |
| feudal 模式下 W&B 已配置但未使用 | `train_feudal_rl.py:255-265` | 新 `_log()` 辅助函数将每项指标写入 TensorBoard *以及* W&B（启用时）。 |
| `reward_breakdown` / `end_reasons` 未暴露 | `train_feudal_rl.py:282-291` | 每次 update 记录各分量 reward 总和与 per-rollout end-reason 计数。 |
| `max_steps` 硬编码 | `train_feudal_rl.py` | 新增 `--max-steps` CLI 标志，YAML 中镜像为 `env.max_steps`。 |

`tests/test_feudal_rl_integration.py` 中新增测试：
- `test_checkpoint_restores_manager_horizon`
- `test_checkpoint_rejects_grid_dim_mismatch`
- `test_collect_rollout_auto_initializes_last_obs`
- `test_ar_worker_warns_without_structured_masks`
- 现有 `test_feature_extractor_*` 测试重命名，以反映 encoder 仅由 worker 拥有。

Notebook `notebooks/feudal_rl_training.ipynb` 已更新以匹配新 API（无需手动 priming `_last_obs`，新的 `compute_intrinsic_reward` 签名，checkpoint 往返校验现也断言 `manager_horizon` 得以保留）。

---

## 第 3 轮：系统集成（Tier 1 #1 + Tier 2）

此前阻碍 feudal 成为项目一等训练器的功能缺口——tournament/GUI 集成、self-play、多环境 rollout、AR 校验，以及 intrinsic-reward 可见性——现已全部关闭。

| 问题 | 位置 | 说明 |
|---|---|---|
| ModelBot 无法加载 feudal `.pt` | `reinforcetactics/game/model_bot.py:51-174` | `_load_model` 按 `.zip` vs `.pt` 分发。Feudal 路径从 checkpoint 的 `hyperparams` blob 重建 `FeudalRLAgent`，grid 维度不匹配时拒绝。`take_turn` 经 stage-conditional / per-dim mask（由实时 `game_state` 构建）路由。 |
| Tournament 看不到 feudal checkpoint | `reinforcetactics/tournament/bots.py:389-416` | `discover_model_bots` 在 glob `*.zip` 之外同时 glob `*.pt`；`_test_model_file` 接受 `bot.model` 或 `bot.is_feudal`。同时修复了长期损坏的硬编码 `6x6_beginner.csv` 路径。 |
| Mask 构建与 env 耦合 | `reinforcetactics/rl/gym_env.py:60-203` | `build_per_dim_masks` 与 `build_structured_masks` 抽成纯函数，入参为 `(game_state, grid_w, grid_h, ...)`。Env 方法变为薄包装；ModelBot 使用同一规范布局。 |
| feudal 无 self-play | `gym_env.py:262-279`（env），`train_feudal_rl.py:248-322`（脚本） | `set_self_play_opponent_factory` 让 trainer 在每次 reset 时重新绑定 env 对手。Trainer 增加 `--opponent self`、`--opponent-snapshot-freq`、`--opponent-pool-size`、`--eval-opponent`。Snapshot 在固定大小池中滚动；对手以 `ModelBot` 实例加载。Eval 使用固定对手，避免分数漂移。 |
| 单环境 rollout 是吞吐瓶颈 | `feudal_rl.py:1438-1612`（`collect_rollout_vec`），`feudal_rl.py:1002-1062`（`merge_finalized_buffers`） | 在 N 个 env 上向量化 rollout，维护 per-env goal / segment 状态，每步一次批量化 feature-extractor 前向。Per-env GAE；finalize 后拼接合并。`--n-envs > 1` 时 trainer 使用该路径。 |
| AR worker 无校验 harness | `scripts/ab_feudal_ar.py` | A/B harness 从同一 seed、相同超参训练 legacy + AR 变体。打印并排 eval 表（win-rate、mean reward、goal-reached rate）与最终 verdict。ROADMAP Phase 3.7。 |
| Intrinsic-reward 校准是盲的 | `feudal_rl.py:837-902`（buffer 字段），`train_feudal_rl.py:434-465`（日志） | Buffer 现存储 per-step `w_intrinsic`、`w_extrinsic`、`w_reached_goal`。Trainer 记录 `train/worker_intrinsic_mean`、`train/worker_extrinsic_mean`、`train/goal_reached_rate`——可判断 worker 由 manager 还是 env 塑形，以及实际达成 goal 的步数比例。 |

新增测试：feudal `.pt` 加载器（扩展名分发、AR vs legacy、grid 不匹配防护、take_turn smoke）、tournament 发现（`*.pt` 拾取 + 伪造 checkpoint 拒绝）、self-play factory hook（每次 reset 调用 factory；无 factory 时安全 no-op）。feudal 相关套件中 398 项测试通过。

---

## 第 2 轮：训练循环功能

本轮关闭了阻塞实际训练运行的操作缺口（value-loss 爆炸、无法 resume、脆弱的 eval 调度、无 LR schedule、无 grad-norm 可见性）。

| 问题 | 位置 | 说明 |
|---|---|---|
| 原始 reward 量级导致 value-loss 爆炸 | `feudal_rl.py:1278`，`train_feudal_rl.py:401` | `collect_rollout` 接受 `reward_scale`；新增 `--reward-scale` CLI 标志（及 `feudal.reward_scale` YAML 键）。在 Direction-A `±5000` 终局下，`reward_scale=0.001` 使 `vf_coef * value_loss` 与 policy/entropy 项量级相当。 |
| 未接入从 checkpoint resume | `train_feudal_rl.py:248-256`，`feudal_rl.py:1525,1583` | `save_checkpoint` 接受 `training_state` 字典；`load_checkpoint` 返回它。训练脚本的 `--resume PATH` 恢复 weights、optimizer state、`total_timesteps`、`best_eval_*` 以及 eval/checkpoint 高水位，使节奏干净续上。 |
| 脆弱的 eval/checkpoint 调度（`% eval_freq < n_steps`） | `train_feudal_rl.py:354,392` | 改为高水位门控（`total_timesteps - last_eval_step >= eval_freq`），并在最终 update 强制 eval。对任意不能整除 `eval_freq` 的 `n_steps` 都稳健。 |
| 无 LR 调度 | `train_feudal_rl.py:268-289`，`configs/feudal/feudal_rl.yaml:24` | 新增 `--lr-schedule {constant,linear}`，在 `total_timesteps` 上线性退火至零。乘数记为 `train/lr_mult`。 |
| 无 per-network 梯度范数可见性 | `feudal_rl.py:1479,1503` | `update()` 现返回 `worker_grad_norm` 与 `manager_grad_norm`（`clip_grad_norm_` 返回的裁剪前总范数）。暴露到 TensorBoard / W&B，并打印在每次 update 进度行中。 |
| 最佳 checkpoint 判据仅看 reward | `train_feudal_rl.py:367-385` | 最佳模型现按 `(win_rate, mean_reward)` 元组选取——在本环境 reward 形态下 win 优先；mean-reward 作平局决胜。 |

`tests/test_feudal_rl_integration.py` 中新增测试：
- `test_checkpoint_training_state_roundtrip`
- `test_checkpoint_without_training_state_returns_none`
- `test_reward_scale_shrinks_extrinsic_signal`
- `test_update_reports_gradient_norms`

Notebook 现暴露 `REWARD_SCALE = 0.001`，贯穿 sanity-check 与训练 rollout，metrics 图同时绘制两种梯度范数（log 刻度）与 value loss（log 刻度），使 value-target 范围一目了然。

---

## 仍开放

这些是研究 / 探索项，不是阻塞项。上一轮的全部系统集成缺口均已关闭。

### 功能

1. **规模化运行 AR A/B。** `scripts/ab_feudal_ar.py` 已接线，但尚未产生 verdict。同样适用于使用新 `train/goal_reached_rate` 诊断的 `--worker-reward-alpha` 扫描，以寻找 intrinsic-vs-extrinsic 甜点。
2. **Subprocess vec envs。** 当前向量化 rollout 在进程内顺序运行 env。对 env 受限的运行，`SubprocVecEnv` 风格包装可带来真实 wall-clock 加速；`FeudalRLAgent` 内 per-env 状态已支持。
3. **无 goal-coverage 探索奖励。** Manager 探索仅靠 entropy；没有奖励覆盖 goal 空间。
4. **无 `manager_horizon` curriculum。** 训练全程固定；早期较短、后期较长是合理方向。
5. **无 plateau 早停。** 可在长跑上节省算力。

### 体验（Quality-of-life）

1. **无 goal 分布热力图。** Goal-type 直方图已进入 TensorBoard，但空间覆盖（manager 选择哪些 `(x, y)` 格子）未可视化。
2. **`FeudalRLAgent` 无 `from_config` / `to_config`。** Checkpoint 现携带运行时子集，但完整配置序列化器会简化超参扫描。

---

## 优先级摘要

| 优先级 | 问题 | 类型 |
|----------|-------|------|
| Medium | 运行 AR A/B + intrinsic-reward 扫描 | Validation |
| Low | Subprocess vec envs | Perf |
| Low | Goal-coverage 探索 / 热力图 | Gap / QoL |
| Low | manager_horizon curriculum | Gap |
| Low | 早停 | Gap |
| Low | `from_config` / `to_config` 序列化器 | QoL |
