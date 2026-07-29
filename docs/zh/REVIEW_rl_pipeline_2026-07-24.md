# RL 流水线评审 — 2026-07-24

范围：`reinforcetactics/rl/` 于 `faac8c8`、`configs/` 下全部 65 个 YAML 配置，
以及 Drive run 归档（`benchmarks/bootstrap/runs_summary.csv`、
`runs_per_stage.csv`、各 run 的 `eval_results.json`）。下文每个数字均从归档
重新计算；每条代码论断都带 `file:line`。

本文建立在 [`REVIEW_ppo_training.md`](REVIEW_ppo_training.md)（2026-07-12）之上，而非重复它。
第 5 节明确说明该评审中哪些建议已落地、哪些未落地。

---

## TL;DR

流水线周围的工程确实很好 — 每阶段配置捕获、增量评估落盘、run 元数据、
停滞轨迹、75 项 bootstrap 测试。阻塞点不在代码卫生。而是 **59 个 sweep
配置变化了奖励 shaping、课程形状与熵，却从未一次变化优化器或表示。**
`gamma`、`learning_rate`、`n_steps`、`batch_size`、`clip_range`、`pool` 与
动作头设计在每一次已记录的 run 中字节级相同。

在再跑任何 sweep 变体之前，我会先处理的五条发现：

1. **基于势的 shaping 在领先时每 episode 向 agent 收费约 190，而胜利只付 50。**
   每个微动作 `(gamma-1)*Phi`，每 episode 约 1900 个微动作。归档测得的
   `shaping_delta` 与算术在 0.3% 内吻合。对称地，*落后* 的 agent 被付钱去拖时间。
   这是双稳态激励，归档精确显示了这种双稳态。
2. **每个门槛决策都测在错误对象上。** 评估以 `deterministic=True` 运行
   （PPO 优化的是随机策略），对阵**每次评估都重抽**的 80-episode 基准。
   因此 `patience` 次连续过线比较的是两套不同问题集，而 `best_model.zip` 是
   对约 100 个噪声估计的 argmax — 最幸运的一次抽样，不是最好的策略。
3. **agent 从未通过占领 HQ 获胜。** 最深 run 的 480 次评估 episode：
   每次评估 `captures_by_type.hq == 0`，100% 胜利为 `by_elimination`。
   自 v49 起奖励对 HQ 胜付 80、对歼灭付 50。对策略从不做的事付更多，
   不是奖励调参问题 — 是能力问题。
4. **`pool: masked_avg` 在策略头之前把整盘压缩成 64 个数**
   （`extractors.py:189-195`）。再叠加 `flat_discrete` 的位置式动作索引，
   策略无法表达「把*这个*单位移到*那*一格」。仓库中每个配置都用 `masked_avg`。
5. **`gamma: 0.99` 在约 2000 步的 episode 上使终局奖励在算术上不可见**
   （`0.99^2000 = 1.9e-9`）。这在 7 月 12 日评审中已记录，却从未应用到
   任何一个配置，包括 v54。

---

## 1. 归档数据重算后显示了什么

| 指标 | 值 |
| --- | --- |
| 可用 runs | 109 个 run 目录中的 56 个 |
| 停滞阶段 | 41 |
| 烧尽 **>=95%** 预算的停滞阶段 | **41 / 41** |
| **峰值先达到或超过门槛** 的停滞阶段 | **28 / 41** |
| 这 28 个的中位最终 WR | **0.106** |
| 以 **WR <= 0.2 且平均奖励为正** 结束的停滞 | 18 / 41 |
| 33 阶段课程预算 | **108M env 步** |
| 有史以来最深 run | **7.9M 步（7%）** |
| 使用 `seed: 42`、n=1 的 runs | 50 / 56 |
| `multi_discrete` runs，峰值 WR | 3 / 3 均为 **0.00** |

标为 `completed_curriculum` 的四行全是 1/5/6 阶段探针课程。
**没有任何 run 完成过真正的 33 阶段天梯**，且 33 阶段中有 13 个从未被任何
东西尝试过。

### 坍缩有可测的形状

来自最深 run 的 `eval_results.json`（连续六次 50k 步评估）：

| step | WR | avg_len | W built | M built | hq caps | truncated |
| --- | --- | --- | --- | --- | --- | --- |
| 5.25M | 1.00 | 1965 | 6650 | 0 | 0 | 0/80 |
| 5.30M | 0.60 | 2639 | 6877 | 2225 | 0 | 27/80 |
| 5.35M | 0.45 | 2698 | 3246 | 5773 | 0 | 38/80 |
| 5.40M | 0.21 | 2812 | **407** | **8989** | 0 | 42/80 |
| 5.45M | 0.75 | 2474 | 7984 | 4 | 0 | 17/80 |
| 5.50M | 0.99 | 1773 | 6791 | 0 | 0 | 1/80 |

这不是渐进漂移。这是 **建造顺序的双稳态翻转** — Warriors 到 Mages 再回来 —
在 150k 步内完成，胜率跟随。策略有两种模式，优化器不断在它们之间敲。

每 80-episode 评估的奖励质量：`action` **+26,011**，`shaping_delta`
**-15,162**，`terminal` **+4,000**。即使在折现前，终局信号也不足总幅度的 10%。

---

## 2. 发现，按优先级排序

### 2.1 shaping 项付钱让 agent 落后，并对领先收税

`reinforcetactics/rl/gym_env.py:1446-1456`

```python
if not terminal:
    current_potential = self._compute_potential()
    delta = self.gamma * current_potential - self._prev_potential
    reward += delta
```

shaping **按每个微动作**应用，且 `Phi` 是*水平*，不是速率：

```python
potential += (structures_agent - structures_opp) * self.reward_config["structure_control"]
```
（`:1406-1409`；v52a 设 `structure_control: 1.0`、`income_diff: 0.05`、
`unit_diff: 0.0`）

当盘面安静时，`Phi(s') == Phi(s)`，delta 为
`(gamma - 1) * Phi = -0.01 * Phi`，**每一步**。因此：

- **Agent 领先 10 个结构** -> `Phi = +10` -> **每步 -0.1**。
  在测得的约 1900 步/episode 上：**每 episode -190**。
- **Agent 落后 10 个结构** -> `Phi = -10` -> **每步 +0.1**，即
  **在输掉时拖到时钟结束可得 +190。**

对比 `win: 50.0`。**守住赢面的代价约为胜利报酬的 ~3.8 倍。**

这不是粗算。归档中最深 run 的 WR-1.00 评估的 `reward_components` 显示
`shaping_delta: -15,162.5` 覆盖 80 episodes = **每 episode -189.5**。
预测 -190 与实测 -189.5 在 0.3% 内一致。

两件事让它咬人而不是相互抵消：

- **终局 `-Phi(s_T)` 从未被收取。** 在终局步跳过 shaping（`if not terminal:`）
  *不等于* `Phi(terminal) = 0`；望远镜和留下悬空的 `+gamma^(T-1) * Phi(s_(T-1))`。
  Ng 等人的策略不变性保证在形式上不适用。
- **GAE 看不见补偿。** 在 `gamma=0.99, lambda=0.95` 下优势窗口约 17 步
  （见 2.3）。补偿终局项在约 1900 步之外。局部上，优化器只看到
  「卸掉物质领先 -> 奖励上升」。

这是归档中每个症状的干净机制解释：和局机器吸引子、WR <= 0.2 时平均奖励为正
（18/41 停滞），以及上表中的 Warrior->Mage->Warrior 双稳态 — 领先的策略被
往下推，落后的策略被推向拖延。

**修复**，从最便宜的开始：
1. 收取终局步：在 `terminal` 上加 `-self._prev_potential`
   （即 `F = gamma*0 - Phi(s_prev)`）而非跳过。恢复不变性。
2. shaping **每游戏回合一次**，而非每微动作 — 漏损与步数成正比，而步数约为
   回合数的 ~25 倍。
3. 或使 `Phi` 有界/归一化，使大领先无法支配终局奖励。

### 2.2 每个门槛决策都针对 PPO 从不优化的策略，对阵每次重采样的基准

`PeriodicEvalCallback._do_eval`（`callbacks.py:235-254`）中两个独立问题，
二者都直接落在晋级、`best_model.zip` 与停滞上。

**(a) 评估测的是确定性 argmax 策略。**

```python
m = evaluate_model(
    self.model,
    self.eval_env,
    n_episodes=self.n_eval_episodes,
    seed=eval_seed,
    track_breakdown=self.track_breakdown,
    **eval_kwargs,
)
```

未传 `deterministic` 参数，而 `evaluate_model` 的默认是
`deterministic: bool = True`（`evaluation.py:97`）。PPO 优化的是*随机*
策略；当阶段大部分时间 `ent_coef` 保持在 0.05-0.10 时，这两个策略相距很远。
因此每次晋级、每次 `best_model.zip` 保存、每次停滞判定，都是在测优化器
并不在改进的对象。

它也使指标以观测到的方式变脆：对位置打乱动作列表的 argmax（2.6）可在小权重
变化下整体翻转，而随机策略会平均过去。

**(b) 80-episode 基准在每次评估时重抽。**

```python
eval_seed = self.eval_seed_base + 1000 * self._last_eval_block
```

其中 `_last_eval_block = num_timesteps // eval_freq`（`:229`），每 episode
种子为 `seed + ep_idx`（`evaluation.py:217`）。因此连续评估抽到
**完全不相交** 的 80-seed 问题集。两个后果：

- `patience` 统计连续过线时，*问题集在两次测量之间变化* — 把基准噪声当
  作策略变化来测。
- `best_model.zip` 是在不同基准上对约 30-100 个噪声估计的 `argmax`。这是
  教科书式的赢家诅咒：保存的「最佳」系统性是最幸运的抽样，不是最佳策略 —
  而 2.8 随后把这个幸运 checkpoint 传到下一阶段。

**修复**：对晋级指标传 `deterministic=False`（或两者都报）；
并在整个阶段内**固定**评估 seed 集（仅 `eval_seed_base`，或仅每阶段轮换的
固定 seed 块），使连续评估可比较。两者都是一行改动，合起来让门槛名副其实。

### 2.3 `gamma: 0.99` 把终局放到视界之外 — 从未变化

`configs/**/*.yaml` — **全部 65 个配置**，包括最新的
`v54_uncapped_frontier.yaml:593`。

- 一步 env = 一次单位微动作。测得的 `avg_length` 为 **1965-2812
  env 步**（`max_steps: 3000`）。
- 有效视界 `1/(1-gamma)` = **100 步 ~ 5 个游戏回合**。
  `0.99^2000 = 1.9e-9`。
- GAE `lambda: 0.95` 给出优势窗口 `1/(1-gamma*lambda)` =
  **17 步** — 约一个游戏回合。

因此和局吸引子不是奖励表里的 bug；它是 *PPO 实际能看见的目标的正确最优*。
九个 sweep 变体（v16、v27a-c、v34、v42、v44、v46、v49、v52a）从奖励侧攻击它。
没有一个动过折扣。

**修复**：把 `gamma` 提到 0.997-0.999（视界 330-1000 步）*并*减少每 episode
步数 — `max_actions_per_turn: 20-30` 会把 75 回合对局从 ~2000 步降到 ~1500。
两者都做；单提 gamma 要求价值头在未归一化奖励上表示 1000 步回报。

### 2.4 截断既收取和局惩罚，又获得时限 bootstrap

`gym_env.py:1504-1506, 1573-1577`

```python
terminated = self.game_state.game_over
truncated  = self.current_step >= self.max_steps
...
elif truncated:
    # Truncation penalty: agent hit step limit without finishing the game.
    terminal_bonus = self.reward_config.get("draw", 0.0)      # -50
```

返回 `truncated=True` 是正确的 Gymnasium 信号，SB3 的 on-policy rollout
收集器对此的响应是在该步奖励上加 `gamma * V(terminal_obs)`（`collect_rollouts`
中的 `TimeLimit.truncated` 路径）。环境已经在同一转移上加了 `draw: -50`。

因此截断步的价值目标是 `-50 + gamma*V(s_T)` — agent 同时被告知「这是终局
和局，吃惩罚」与「这是人工截止，保留未来价值」。两者矛盾，且该 bug 在
每 80 次评估 episode 中的 **27-42 次**触发（2.10），因此不是边角情况。

**修复**：选定一种语义。
- 若步数耗尽*按规则*是和局，镜像 `max_turns` 处理 — 设 `terminated=True`
  （`:1529-1532` 已对 max-turns 和局这样处理），从而不做 bootstrap。
- 若是真正的时限，从 `elif truncated` 分支去掉 `draw` 奖励，让 bootstrap
  携带价值。

### 2.5 策略在空间上是盲的 — 从未变化

`reinforcetactics/rl/extractors.py:189-195`

```python
elif self.pool == "masked_avg":
    live = self._live_cell_mask(grid)
    features = (features * live).sum(dim=(2, 3), keepdim=True) / denom
    features = features.flatten(1)
```

CNN 的 `(B, 64, H, W)` 输出在活格上平均成 **64 个数**，与 5 个全局特征拼接，
再投影到 256。10x12 棋盘上每个单位位置、HP、地形格与所有权 bit 到达策略头
时，只是 69 个空间平均标量。

`extractors.py:46-50` 已说明 `flatten`「保留位置信息」且「当下游头消费 per-cell
特征时必需」。`masked_avg` 为 pad 不变性而选 — 但 `pad_to_size` 在每个课程中
只解析一次（`bootstrap.py:626-629`），因此填充形状*固定*，`flatten` 是安全的。
在 (10, 12) 上是 `64*10*12 + 5 = 7685` 输入，第一层约 1.97M 参数。便宜。

**这是桌上对 `hq: 0` 的最佳解释。** HQ 占领要求把特定单位路由到特定格子并
夺取。歼灭是与位置无关的消耗。策略恰好做它能表示的那一种。

**修复**：在其它一切保持 v52a 的情况下，跑一个 `pool: flatten` 变体。
这是一行配置改动，测试从未测过的轴。

### 2.6 `flat_discrete` 动作索引是位置式的，且每步重建

`gym_env.py:1065-1069` 与 `_build_flat_actions`（`gym_env.py:247-302`）

索引 `i` 是「本步重建的合法动作列表的第 i 项」。该列表通过迭代
`self.units`（`core/game_state.py:1334`）与 `grid.get_capturable_tiles`
（`:1327`）构建。单位死亡时 `self.units.remove()` 使之后每个索引平移；
金币跨过某单位成本时，整个 `create_unit` 前缀长度变化并平移一切。

因此 logit-到-动作映射依赖状态，且在 episode *内部* 易变。结合 2.5，策略
无法从观测推断枚举 — 只能学粗粒度规律（「低索引是 create_unit，最后一个是
end_turn」）。这是确定性-argmax 评估在相邻评估间 1.00 -> 0.21 -> 0.99 摆动
的机械解释。

**修复（更大）**：pointer/per-cell 动作头 — 从各自空间特征向量为每个
（单位, 目标）对打分 — 同时消除 2.5 与 2.6。`pool: flatten` 是前提。

### 2.7 没有任何学习率调度真正到达 PPO

`reinforcetactics/rl/config.py:116` 声明 `lr_schedule: str = "constant"`，
但 `:137` 丢掉了它：

```python
skip = {"use_action_masking", "lr_schedule", "purchase_explore_eps"}
```

注释写「feudal-only (`lr_schedule`)」。因此 bootstrap/PPO 路径在全部 22M
计划步上跑 **恒定 3e-4**，且没有从配置支持的改法。全部 56 个归档 runs
确认 `learning_rate: 0.0003`。

鉴于 2.1 的双稳态，后期阶段 LR 退火是最便宜的干预之一 — 代码库已有可直接
复制的精确模式（`callbacks.py:434-520`，`EntropyScheduleCallback`，它每阶段
修改存活模型属性，并经 `_on_training_start` 正确处理 `reset_num_timesteps=False`）。

**修复**：增加镜像 `EntropyScheduleCallback` 的 `LRScheduleCallback`，并在
`as_sb3_kwargs` 中兑现 `lr_schedule`，或增加
`CurriculumStage.learning_rate_schedule`。

### 2.8 `best_model.zip` 通常是*带入*策略，因此晋级可撤销该阶段

`callbacks.py:224, 229-232, 324-331` 与 `bootstrap.py:997-1013` 的交互

`PeriodicEvalCallback` 每阶段全新构造，`self._last_eval_block = -1`，但门槛
看的是**累计**计数器：

```python
block = self.num_timesteps // self.eval_freq
if block > self._last_eval_block:
```

运行器传 `reset_num_timesteps=False`（`bootstrap.py:841`），因此阶段入口时
`num_timesteps` 已是数百万，`block` 是大正数。**每个阶段第一次 `_on_step`
立即触发评估** — 即 `docs/bootstrap_runs_review.md:67-70` 已指出的
「每阶段首次评估在 `t = stage_steps + 4`」。

该评估测的是**带入策略**，且完全有资格成为阶段最佳（`best_win_rate` 从
`-1.0` 开始，`:214`）。因此当阶段后来晋级且运行器执行

```python
model.set_parameters(str(best_ckpt), exact_match=True)  # :1011
```

时，它可能恢复*阶段入口时*的策略，丢弃该阶段训练的一切。这不是假设：
7 月 12 日评审测得中位清关时间为 **50k 步 — 单个评估间隔**。在评估 #1 与
#2 上以带入策略得分最高而通过的阶段，会回退到带入权重。

在 20 阶段 run 上叠加，策略可推进天梯的大部分，却吸收远少于步数计数器暗示
的训练 — 然后在首个真正困难的阶段欠训。运行器已经*测量*到这一点
（`best_checkpoint_stage_steps`，`bootstrap.py:845-851`，以及 `:1000-1003`
的「skip-ahead」注释）；测量加了，修复没有。

**修复**：向 `PeriodicEvalCallback` 增加 `best_eligible_after`（相对阶段步数，
默认 `eval_freq`）— 把阶段入口评估记为*基线*行，但对其跳过 `model.save`。
两行，且让 `restore_best_checkpoint_between_stages` 名副其实。

### 2.9 停滞对 run 致命，而好的 checkpoint 留在磁盘上

`bootstrap.py:934-981`

停滞时运行器写 `run_status.json`、保存坍缩后的策略，并抛出
`CurriculumStalled` — 杀死整个 run。该阶段的 `best_model.zip` 在 41 例中的
**28 例**曾达到或超过门槛，并在异常中被引用（`:956-957`，由 `7fedf3e` 添加），
但从未有东西加载它。

与此同时 `restore_best_checkpoint_between_stages`（`:997-1013`）只在
**晋级**路径运行：

```python
if not promote_cb.promoted:
    ...
    raise CurriculumStalled(...)
# Stage promoted (the stall branch above raises).
if cfg.curriculum.restore_best_checkpoint_between_stages:
```

因此唯一能修复漂移的机制，在恰恰需要它的情况下不可达。也没有从 stage-K
启动：在 108M 步预算对 ~6M 每 Colab 会话下，无论奖励调多少都跑不完天梯。

**修复，按顺序**：
1. 停滞时，`model.set_parameters(best_model.zip)`，重新预热熵，并在抛出前
   重试该阶段一次。
2. 增加**阶段内**回归保护：若 WR 连续 N 次评估比阶段最佳低超过 X，恢复
   `best_model.zip` 并继续。直接把 28 次 peak-then-collapse 停滞变成晋级。
3. `run_curriculum(start_stage=K)` + run 清单，使被杀会话恢复而非重启。

### 2.10 `max_steps: 3000` 是指标看不见的截断悬崖

`gym_env.py:1505` `truncated = self.current_step >= self.max_steps`；
`:1573-1577` 用**和局**奖励给截断打分；`evaluation.py:366` 计算
`win_rate = wins / n_episodes`，因此截断像失败一样计入门槛。

实测：最深 run 的正常评估中 **80 中 27-42** 个评估 episode 被截断。
`v52a_maxturn_scaled_draw.yaml:11-13` 仍断言「3000 远高于任何现实对局长度
… 因此正常游玩下截断从不触发」。它在三分之一到一半的 episode 上触发。

雪上加霜，`bootstrap.yaml:49` 与 `v54:474` 中的 `max_actions_per_turn: null`
禁用了对抗永不 end-turn 吸引子的唯一护栏 — 其自身 docstring（`gym_env.py:501`）
描述的正是正在观测到的失败模式。

**修复**：从 `max_turns` 缩放 `max_steps`（`max_turns * max_actions_per_turn
* 1.5`）而非钉死常数；给 `max_actions_per_turn` 设真实值；并在晋级指标中
将 `truncated` 与 `max_turns_draw` 分开记录，使门槛不再把「慢」与「差」混为一谈。

### 2.11 晋级门槛在阈值附近是抛硬币

`callbacks.py:415-430` 要求 `patience` **连续**评估过门槛。
在 WR 0.75、80 episodes 时标准误为 4.8pp，因此对真正 0.75 的策略，连续两次
越过 0.75 门槛大致是抛硬币 — 而 41/41 次停滞烧尽全部预算等待它。

**修复**：对胜率的 Wilson 下界门控，或对最近 K 次评估的滚动均值门控，
而非原始连续点估计。

### 2.12 BC / 模仿子系统瞄准无法学习的动作空间

`gym_env.py:1059-1060` 将 multi_discrete masks 文档化为
「按维度布尔掩码（**并集过近似**）」— 按维 masking 无法表达联合合法性，
因此会采样非法联合动作。

在 run `20260525_050151` 上测得：`invalid_penalty` = **每次评估 -2358**，
`invalid_action: -0.1`，即 **每 240,000 步约 23,580 次非法动作（~10%）**，
且 **80/80** episodes 命中 `max_steps_truncate`，WR 整 run 钉在 0.00。

`imitation.py:25` 与 `scripts/build_bc_warmstart.py:160` 仅支持
**multi_discrete**。那是约 1,600 行 BC 基础设施加三个接到实证无法学习的
动作空间的配置，而每个生产 run 用 `flat_discrete`。

**修复**：把 BC 移植到 `flat_discrete` — 标签只是演示动作在
`build_flat_actions(...)` 中的索引，该函数已是与 `ModelBot` 共享的模块级
纯函数（`gym_env.py:230-302`）。或退役子系统并删除配置，以免继续成陷阱。

即使移植后 BC 热启动仍会表现不佳的另外两个原因：

- **价值头在 BC 偏移的共享 trunk 上保持随机初始化。**
  `imitation.py:1331` 选择 `bc_params = [p for n, p in
  policy.named_parameters() if not n.startswith("value_net")]`，因此 BC 训练
  `features_extractor` 但不训练最终价值头。SB3 的
  `MaskableActorCriticPolicy` 默认 `share_features_extractor=True` 且无配置
  覆盖，因此 PPO 的首次更新看到巨大价值损失，并以 `vf_coef: 0.5` 把它
  推回共享提取器 — 在几次更新内撤销克隆。对前 N 次更新冻结提取器，或在
  交接前对演示回报回归价值头。
- **演示在不同引擎上收集。** `imitation.py:707-713` 构造
  `GameState(map_data, num_players=2, max_turns=..., enabled_units=...,
  fog_of_war=...)`，并省略 `engine_overrides` 与 `rng`。因此 v50 起的任何
  配置（`damage_model: hp_scaled`、`W: {cost: 300}`）都在克隆一个玩着不同
  游戏的 bot。

### 2.13 自对弈 RNG 未播种；对手推理在热路径上

`self_play.py:542`

```python
if self.swap_players and random.random() < 0.5:
```

模块全局 `random`，因此 `reset(seed=...)` 控制不了它。同样在
`:355` / `:365`（`np.random.randint`、`np.random.choice`）。在 fork 的
`SubprocVecEnv` 下，每个 worker 继承相同的全局 RNG 状态，因此座位交换决策
在全部 8 个 env 间**相关**，自对弈评估不可复现。这正是环境已为战斗 RNG 在
`gym_env.py:1663-1669` 修复的那类 bug — 修复只是从未到达包装器。

`self_play.py:317-340` 把完整策略 `state_dict` 拷到 numpy，
`load_state_dict` 到对手，预测一个动作，再 `load_state_dict` 回原策略 —
  **每个对手动作两次完整参数加载**。改为持有两个策略实例。

`self_play.py:533-548`：`self.env.reset()` 在 `:533` 运行（从 `agent_player`
座位设置 `_prev_potential`，`gym_env.py:1692`），而 `agent_player` 仅在
`:544` 翻转。交换 episode 的第一个 shaping delta 对照另一座位的势计算。
严重性低但修复免费。

同一文件中另外三个缺陷比 RNG 问题更严重，每个都独立让自对弈不成自对弈。
我对照源码验证了全部三个：

**(a) 对手从未获得 action masks。** `self_play.py:332`：

```python
action, _ = self.opponent_model.predict(obs, deterministic=self.opponent_deterministic)
```

`MaskablePPO.predict` 把缺失的 `action_masks` 当作「无 masking」，因此对手
在完整 `MultiDiscrete([10, 8, W, H, W, H])` 上自由采样。几乎每个此类联合
动作都非法（2.12），因此对手实际上是 pass-bot。「自对弈」agent 在对噪声训练。

**(b) `swap_players` 从未到达游戏。** `make_self_play_env` 组合
`SelfPlayEnv(ActionMaskedEnv(StrategyGameEnv(...)))`（`:751-754`），因此
`self.env` 是包装器。`SelfPlayEnv.reset` 随后做：

```python
self.agent_player = 2
self.env.agent_player = 2  # :545
```

`gymnasium.Wrapper` 覆盖 `__getattr__` 但**不**覆盖 `__setattr__`，因此这
在*包装器*上创建新属性，遮蔽委托。`StrategyGameEnv.agent_player` 仍为 `1`。
在每个交换 episode 上，基础环境为错误座位计奖励、算势并选终局奖励，而
`SelfPlayEnv` 相信 agent 是玩家 2。

**(c) `SubprocVecEnv` 静默完全禁用对手更新。**
`_SelfPlayCallback._get_self_play_envs`（`:627-643`）仅通过
`hasattr(self.env, "envs")` 到达 env。`SubprocVecEnv` 没有 `.envs` — env 在
子进程中 — 且 `isinstance(self.env, SelfPlayEnv)` 回退也不匹配 VecEnv，
因此方法返回 `[]`，`_update_opponents` / `_add_to_pool` 是空操作。每个
bootstrap 配置设 `use_subprocess: true`。

鉴于 (a)-(c)，归档中任何自对弈结果都不应信任，且课程中 `opponent: "self"`
进一步退化：`gym_env.py:1751-1760` 在未注册自对弈工厂时回退到
`self.opponent = None`，而 bootstrap 路径从不注册 — 静默无作为的对手，配置
验证却接受（`"self"` 在 `_BOT_OPPONENT_TYPES` 中，`:76`）。

### 2.14 单 seed sweeps

50/56 runs 使用 `seed: 42`、n=1。v21 在相同设置上重跑*刚清完*的阶段，从
通过变为 peak 0.86 / final 0.0125。`bootstrap_lessons_learned.md` 中记录的
多数单旋钮结论落在它们本要消解的噪声带内。

---

### 2.15 最终健全性评估未使用该阶段的 env

`scripts/train/train_bootstrap.py:301-312` 手搓其 env：

```python
env = make_maskable_env(
    map_file=...,
    opponent=...,
    max_steps=...,
    max_turns=...,
    reward_config=...,
    enabled_units=...,
    action_space_type=...,
    seed=cfg.seed + 9999,
    opponent_kwargs=...,
    pad_to_size=cfg.env.pad_to_size,
)
```

它丢掉了 `engine_overrides`、`max_flat_actions`、`max_actions_per_turn`、
`gamma` 与三个 tanh 缩放因子。对 v50 起的每个配置，这意味着健全性评估跑在
**默认引擎规则**上 — 无 `damage_model: hp_scaled`、无 `W: {cost: 300}` —
 因此其胜率与它本要交叉核对的训练内评估不可比。

`bootstrap.py:1036-1053` 记录了正是这类 bug，且 `make_stage_env`（`:1055`）
存在就是为了防止它。修复是一行：

```python
from reinforcetactics.rl.bootstrap import make_stage_env

env = make_stage_env(stage, cfg.env, seed=cfg.seed + 9999)
```

（`make_stage_env` 还应转发 `gamma`；目前没有 — 见第 3 节。）

### 2.16 替代算法有各自的正确性 bug

这些不在 bootstrap 关键路径上，但对任何运行 `train_feudal_rl.py` 或
`train_alphazero.py` 的人是承重的，且每个都会静默产出看起来合理但错误的
训练曲线。

**Feudal RL**
- `feudal_rl.py:1258-1262` vs `:1295-1296` — `manager_segment_open`、
  `manager_reward_accum` 与 `manager_step_count` 是每次 `collect_rollout()`
  调用重置的**局部变量**，但 `self.current_goal` / `self.goal_step_counter`
  在 agent 上持久。在目标 `g_k` 下赚到的奖励跨每个 rollout 边界记到
  `g_(k+1)` 上。
- `feudal_rl.py:1324-1325` — `done = terminated or truncated` 同时存为
  `w_dones` 与 `m_dones`，且 `_compute_gae` 把它当终局指示器。每个时限
  episode 的价值 bootstrap 被置零。
- `feudal_rl.py:1358` — manager critic 对**未折现**的段内奖励和回归，而
  GAE 对 bootstrap 应用 `gamma^k`；两者不一致。
- `feudal_rl.py:823, 1983-2003` — worker 奖励把大致 `[-10, +15]` 的内在项
  与原始 env 奖励混合，未归一化；且两个目标奖金按附近单位数线性缩放无上限。

**AlphaZero**
- `alphazero_trainer.py:315-326` — 在 `_training_phase()` 前设
  `self.network.train()`，在 `_evaluation_phase` 前从未切回。
  BatchNorm 运行统计随后被评估中 batch-size-1 的 MCTS 前向覆盖。
- `alphazero_trainer.py:522-525` — 当 `total_decided == 0` 时
  `_evaluation_phase` 返回 `0.5`，且 `_play_eval_game` 构建其 `GameState`
  时**没有 `max_turns`**，因此全截断评估正好返回保证永久拒绝每个候选网络
  的值。拒绝还回退权重但不回退 Adam/scheduler 状态。
- `alphazero_trainer.py:98-139` — `self_play_game` 以按*单个动作*计数的
  `max_steps=400` 封顶，`GameState` 上无 `max_turns`。鉴于 PPO 测得约 2000
  步的 episode，实质上每个自对弈局被截断并标为和局，训练价值头处处预测 0。
- `alphazero_trainer.py:574, 612` — `_save_checkpoint` 持久化五个配置键，
  `load_checkpoint` 做 `cls(**config)`，因此 resume 时 `map_file`、
  `enabled_units` 与 `lr` 被静默丢掉。

---

## 3. 值得修的较小事项

- `configs/ppo/bootstrap.yaml` — **规范**配置 — 仍自带
  `win_speed_bonus: 50.0`（`:157`）、`enemy_owned_capture: -15.0`（`:171`）与
  `turn_penalty: 0.0`（`:149`）：正是 v27 消融隔离为造成墙的项。v54 有
  修正值；任何人跑的默认没有。三行回写。
- `callbacks.py:324-331` — `best_win_rate` 仅在 `if self.save_dir is not None`
  内更新。`save_dir=None` 时它停在 `-1.0`，`CurriculumStalled.achieved_win_rate`
  会报 `-1.0`。在 bootstrap 中未生效（它总是传阶段目录），但对其它调用者
  是陷阱。
- `bootstrap.py:866-896`、`:918-921` — 元数据写入周围三处 `except Exception: pass`。
  对 checkpoint 是承重参数的论证合理，但它们目前吞掉*原因*；一行
  `logger.warning` 就能让 Drive 配额失败可见。
- PPO 路径上没有任何 `VecNormalize`。在未归一化回报与 `vf_coef: 0.5` 下，
  价值损失幅度由奖励尺度设定。5000 -> 50 的重标定修了最糟的情况；
  `norm_reward=True`（或 `clip_range_vf`）将永久解耦两者。
- `viz.py:262` 已有关于缩放奖励 / 增加 `clip_range_vf` 的注释 — 诊断存在，
  旋钮从未接上。
- `bootstrap.py:1055` 的 `make_stage_env` 不转发 `gamma`，因此任何回放或
  重评估 env 用默认 0.99 算 `shaping_delta`，即使 run 以不同折扣训练。一旦
  应用建议 2.3 这就错了。
- `bootstrap.py:752` 读 `stage.n_eval_episodes`，默认 `30`（`config.py:255`）。
  课程运行器**从不读** `cfg.eval.n_eval_episodes`。今天每个交付阶段都设了
  覆盖，因此没坏 — 但忘记设的新阶段会静默用 30 episodes 评估，而配置写 80。
  把阶段字段做成 `int | None` 并对 `cfg.eval` 解析。
- `bootstrap.py:836` — `model.ep_info_buffer` 在阶段边界不清空，因此每阶段
  `train_metrics.csv` 前约 100 行描述的是*上一*阶段，却带着新阶段的
  `context` 标签。
- `scripts/train/train_bootstrap.py:399-415` — 捕获 `CurriculumStalled`、
  打印，然后脚本打印 `✅ Done` 并返回 **0**。任何把退出码当真相的 CI 或
  调度器会把失败 run 记为成功。停滞时返回非零码。
- `callbacks.py:390-409` — `min_timesteps_before_promotion` 现为阶段相对；
  过去对照累计计数器。这是更好的语义，但 `v31_production_minsteps_gate.yaml`
  的归档 run 不再能从其自身配置复现。值得在 `_write_stage_config` 输出中
  打上 `promotion_gate_version`。
- `bootstrap.py:699-703` — 购买探索 hook 从**全局**
  `cfg.ppo.purchase_explore_eps` 安装一次。阶段级覆盖通过写存活属性应用，
  但若全局在 `flat_discrete` 上为 `0.0`，安装提前返回
  （`purchase_exploration.py:207-211`），每阶段值成为静默空操作。
- `bootstrap.py:469-480` — 每阶段 `config.json` 省略 `pad_to_size`、
  `gold_scale`、`turn_scale`、`unit_count_scale` 与 `n_envs`。`pad_to_size`
  是运行器*推导*的字段（`:626-629`），因此无法从 run 记录重建 observation
  space。
- `bootstrap.py:97-101` — `CurriculumStalled` 消息总是读作「最佳 win_rate X
  未达阈值 Y」，即使峰值超过了阈值（28/41 例）。「峰值 100%，从未连续 2 次
  评估守住」是不同失败，应有不同读法。
- `scripts/train/train_bootstrap.py:373-384` — run 目录得到
  `shutil.copy2(config_path, ...)`，即**源** YAML，*在*
  `_apply_set_overrides` 与设备解析已经突变 `cfg` 之后。用
  `--set ppo.gamma=0.997` 启动的 run 记录 `gamma: 0.99`。改为转储
  解析后的配置 — 一旦开始用 `--set` 做 sweep，这就重要。
- `bootstrap.py:764` — 每步评估追踪硬编码开启
  （`trace_dir=stage_dir / "traces"`），无配置旋钮、无大小上限，且
  `evaluation.py:223` 为*每个* episode 分配每步缓冲，而非仅匹配的。停滞
  阶段写到 Drive 支持的 run 目录时，可为 2000+ 步的 episode 产生大量 JSONL。
- `evaluation.py:215-235` — 评估是严格串行单 env 循环，每步一次推理。
  80 episodes × ~2000 步是每次评估 160k 次串行 GPU 往返，对间隔中的 50k
  *向量化*训练步。评估而非训练很可能是墙钟瓶颈 — 这直接相关，因为墙钟
  死亡是两种 run 致命模式之一。向量化它，或在晋级之间降低 `n_eval_episodes`。
- `gym_env.py:420` — `map_file: null` 在 `__init__` 中经模块全局 numpy RNG
  抽一次随机地图，在任何播种之前，因此 `reset(seed=...)` 无法复现它，每个
  vec worker 得到不同棋盘。bootstrap 配置未用，但是活陷阱。
- 抢占：`train_bootstrap.py` 写到 `benchmarks/bootstrap/<run_id>` 并在
  `finally` 块中上传一次，而容器的周期上传器同步不同的硬编码目录列表。
  没有 SIGTERM 处理器。在 Vertex/Colab 抢占上整个 run 目录丢失 — 对最深
  run 死于墙钟的项目，这值得一小时工作。

---

## 4. 建议的工作顺序

先正确性，再两条从未测试的轴，再让 run 能活下来的管道。每个实验相对 v52a
只改一个变体，以便归因干净。

> **状态：** 项目 1-5 已实现。见本节底部「已落地」了解确切改动及其*未*修复
> 的内容。

**正确性（在任何新 sweep 之前做 — 这些改变数字的含义）：**

1. **收取终局 `-Phi(s_prev)`**（2.1）。`_calculate_reward` 中约 3 行。
   去掉归档以 0.3% 确认的「领先被征税」梯度。
2. **选定一种截断语义**（2.4）。要么在 `max_steps` 上 `terminated=True`，
   要么从截断分支去掉 `draw` 奖励。约 2 行。
3. **修复评估方法论**（2.2）：在整个阶段固定评估 seed 集，并对随机策略
   （`deterministic=False`）门控，或两者都报。两行，之后每个数字可比较。
4. **让阶段入口评估仅作基线**（2.8）。`PeriodicEvalCallback` 中约 5 行。
   阻止 `restore_best_checkpoint_between_stages` 撤销阶段自身的训练。
5. **让 `_final_sanity_eval` 指向 `make_stage_env`**（2.15），并从
   `make_stage_env` 转发 `gamma`。约 3 行。在任何 `--set` sweep 前转储
   *解析后* 配置而非源 YAML（第 3 节）。

**然后是没人扫过的两条轴：**

6. **`pool: flatten`**（一行）。观察 `captures_by_type.hq` — 若仍为 0，
   那就是归档中最大开放问题的答案。
7. **`gamma: 0.997` + `max_actions_per_turn: 25`**（两行）。同时把终局拉进
   视界并缩短 episode。
8. **阶段相对 LR 退火**（约 40 行，复制 `EntropyScheduleCallback`）。
   双稳态修复的另一半。

**然后是决定 run 能否完成的管道：**

9. **阶段内回归时恢复最佳 checkpoint**（约 30 行）。用已在磁盘上的
   checkpoint 把主导停滞模式变成晋级。
10. **停滞时从最佳重试，以及从 stage-K 恢复**（约 60 行）。没有它，108M
    步课程在约 6M 步/会话下无法到达，无论其它修了什么。
11. **`PromotionCallback` 中的 Wilson 下界**（约 10 行）。

**然后是卫生：**

12. 把 v49/v52a 奖励值回写进 `configs/ppo/bootstrap.yaml`。
13. `train_bootstrap.py` 中停滞时非零退出。
14. 把 BC 移植到 `flat_discrete`，或退役并删除三个配置。
15. 在信任任何自对弈结果前，修复 2.13 中的三个自对弈缺陷 — 对手 masks、
    落在包装器上的 `agent_player` 写入，以及 `SubprocVecEnv` 返回无 envs —
    然后从 `np_random` 播种包装器 RNG，并持有两个策略对象而非每对手动作
    交换 `state_dict`。
16. 任何打算保留的结论用 **3 个 seed** 重跑。

### 已落地（项目 1-5）

| 改动 | 文件 |
| --- | --- |
| 终局步收取 `F = gamma*0 - Phi(s_prev)`，而非跳过 shaping 项。步数限制截断保留普通 delta — 其后继状态是真实的并得到 bootstrap。 | `gym_env.py` `_calculate_reward`（`terminal` -> `terminated`） |
| 截断不再收取 `draw` 终局。新增可选 `reward_config['truncation']`（默认 0.0），若需要显式惩罚。 | `gym_env.py` step |
| 评估每阶段重放一套固定问题集。`EvalConfig.resample_eval_seeds` 恢复旧的每次评估轮换行为。 | `callbacks.py`、`config.py` |
| `best_eligible_after` 阶段相对步数内的评估被记录但不能认领 `best_model.zip`。Bootstrap 传 `eval_freq`；`EvalConfig.best_eligible_after` 覆盖。每个评估行现带 `stage_steps` 与 `best_eligible`。 | `callbacks.py`、`bootstrap.py`、`config.py` |
| `make_stage_env` 转发 `gamma`；`_final_sanity_eval` 经它走，而非手搓 env。 | `bootstrap.py`、`train_bootstrap.py`、`imitation.py` |
| `resolved_config.yaml` 写在源 YAML 旁，使 `--set` 覆盖进入 run 记录。 | `train_bootstrap.py` |

增加了八项测试，每项都对照先前行为验证会失败 — 包括望远镜检查：折现
shaping 回报精确等于 `-Phi(s_0)`，在故意不对称的起点上，以免空过。

**这*没有*修复什么。** 终局收取恢复了 Ng 等人的不变性，但**没有**去掉 2.1
中测得的约 190/episode 漏损。该漏损是在约 1900 个微动作上累积的
`(1 - gamma) * Phi`，其大小由 `gamma` 与每 episode 步数设定 — 而非终局项，
其在 `gamma=0.99, T=1900` 时的折现权重约 1e-9。去掉漏损需要项目 7
（提高 `gamma`、降低 episode 长度）或按游戏回合的 shaping 节奏。把项目 1
当作使提高 `gamma` 安全的正确性前提，而非单独修复和局吸引子。

**可比性。** 这些改变了奖励函数与评估协议，因此此后的数字与归档 runs
不可比。在解读任何处理效应前，原样重跑 v52a 作为新锚点。

---

## 5. 2026-07-12 评审建议的状态

**已落地**（提交 `026b8a0`、`7fedf3e`、`a552bc1`、`0587759`）：
可观测性 — `train_metrics.csv`、`eval_results.jsonl`、`run_status.json` 中的
最佳 checkpoint 字段；`BUILD_BC_WARMSTART` 默认；评估环境漂移修复；
自动治疗诊断；带 `max_steps: 4500` 与 `max_flat_actions: 1024` 的
`v54_uncapped_frontier`。

**未落地** — 且这是决定 run 能否完成的两条：

- **建议 #2，checkpoint/resume。** 无 `start_stage`，无停滞时从最佳重试。
  两种观测到的死亡模式（墙钟、停滞）仍对 run 致命。
- **建议 #5，优化器轴。** `gamma`、`learning_rate`、`n_steps`、
  `batch_size` 与 `clip_range` 在仓库每个配置中仍相同，包括 v54。
  `lr_schedule` 在到达 SB3 前仍被丢掉（`config.py:137`）。

本评审再增加第三条从未触碰的轴：**表示**（`pool`，以及扁平位置式动作头）。
