# PPO Bootstrap 训练评审 — 为何 runs 过不了课程（2026-07-12）

范围：`notebooks/ppo_bootstrap.ipynb`、`notebooks/ppo_training.ipynb`、
`reinforcetactics/rl/`（环境、callbacks、bootstrap 运行器）、`configs/ppo/`
（bootstrap.yaml + 全部 58 个 sweep 变体）、`reinforcetactics/game/bot.py` 中的
bot 天梯，以及 Drive 上的完整 run 历史
（`benchmarks/bootstrap/runs_summary.csv` / `runs_per_stage.csv` /
`runs_detail.json`：109 个 run 目录，2026-05-07 → 2026-06-02，56 个可用 runs，44
个不同配置，274 次尝试的 stage 行）。下文每条论断均对照 HEAD 代码（`5178e57`）
验证，并从 CSV 重新计算；若干条用新鲜的 bot-vs-bot 模拟核对。

## TL;DR — 按重要性排序的原因

1. **策略坍缩进「奖励为正的和局吸引子」** 是主要观察到的停滞机制 —
   不是打不过 bots。24/32 次卡墙停滞*峰值曾达到或超过晋级阈值*，随后
   崩溃到中位最终 WR 约 0.06–0.14，对局钉在约 73/75 回合，且**在输的同时
   平均奖励为正**（29/41 次停滞）。稠密 shaping 在你从不赢时仍然付钱。
2. **`configs/ppo/bootstrap.yaml` 仍自带 v27 消融已证明会独立造成该墙的两项
   奖励**（`win_speed_bonus: 50`、`enemy_owned_capture: -15`），外加
   `turn_penalty: 0`。产出每次深 run 的 v28/v49/v52a 修复从未回写到规范配置。
3. **若干晋级门槛位于或高于脚本 bot 天花板。**
   从 agent 座位（P1，阶段 `max_turns`）的新鲜模拟：在
   `beginner_random_15`（门槛 0.70/75 回合）上，仓库内任何 bot 最好是
   AdvancedBot 0.63（SimpleBot 0.00，90% 和局 — 重建经济的肉墙是和局机器，
   且 `win_rate` 把和局计为失败，`evaluation.py:357`）。`intermediate_medium`
   的 0.65 门槛约为最佳脚本 WR（0.30）的 ~2×。PPO *曾经* 清过这些门槛，
   但只是短暂 — 门槛坐在 ±10pp 评估噪声下的统计刀刃上。
4. **信用分配看不见终局奖励。** 一步 env = 一次单位微动作，因此 episode 跑
   ~700–2400 步；γ=0.99 时，±50 终局从早期决策折现到 ~1e-3，GAE 窗口
   （1/(1−γλ) ≈ 17 步）只跨 1–2 个游戏回合。稠密事件经济是事实上的目标。
   γ、lr、n_steps、batch、clip 在**全部 59 个配置中完全相同** — 坍缩的
   优化侧从未被攻击。
5. **墙钟时间 + 无 resume 限制了最深 runs。** 33 阶段预算合计 87.5M env 步；
   最深 run 仅到 7.9M。两次 20 阶段 runs（v50、v52a）都结束在**刚清完、
   仍在晋级的阶段**，被会话杀掉，且 `run_curriculum` 没有从 stage-K 恢复。
   33 阶段中 13 个（skirmish_random_20 起 + 全部 corner_points）从未被任何
   run 尝试。另外，首次 `CurriculumStalled` 会中止整个 run — 即使该阶段的
   `best_model.zip` 曾高于阈值，也没有从最佳 checkpoint 重试。
6. **潜在的表示天花板**（目前尚非绑定约束，但在前沿等待）：位置式
   `flat_discrete` 动作索引，每步重建语义；512 动作上限截断 728–744 动作的
   skirmish 状态，*丢掉全部 attack/heal/cast 动作*（move 先枚举）；
   `masked_avg` 池化把地图压成 64 个数再进动作头；`max_steps: 3000` 在
   `corner_points` 的 200 回合时钟前绑定，把长对局变成 −50 截断和局。

此外：已提交 notebook 的默认值在 Run-All 下当前是坏的
（`BUILD_BC_WARMSTART = True` 在训练开始前就对默认 flat_discrete 配置抛
`RuntimeError`），PPO 训练诊断（approx_kl、clip_fraction、explained_variance）
被收集但从不落盘，且 59 个 sweep 变体每个都用 `seed: 42`、n=1 —
 相同配置重跑会在通过与停滞间翻转，因此多数单旋钮 sweep 结论落在噪声带内。

---

## 1. run 数据实际显示了什么

### 漏斗（attempted = evals_run > 0；56 个可用 runs）

| stage | att | clear | stall | clear% | med peak WR | med final WR |
|---|---|---|---|---|---|---|
| starter_random | 38 | 32 | 6 | 84% | .975 | .956 |
| starter_simple / starter_medium | 32 | 32 | 0 | 100% | 1.0 | 1.0 |
| beginner_balanced_random | 47 | 47 | 0 | 100% | 1.0 | 1.0 |
| **beginner_random_10** | **43** | **28** | **15** | **65%** | 1.0 | .838 |
| **beginner_random_15** | **23** | **10** | **13** | **43%** | .888 | .488 |
| beginner_random_20 | 6 | 4 | 2 | 67% | .819 | .769 |
| beginner_simple/mixed/medium/advanced | 各 4 | 全部 | 0 | 100% | .94–1.0 | .94–1.0 |
| intermediate_*（至 random_15） | 3–4 | 全部 | 0 | 100% | 1.0 | 1.0 |
| **intermediate_random_20** | 4 | 2 | 2 | 50% | .913 | .469 |
| intermediate_simple/medium/mixed | 2 | 2 | 0 | 100% | .80–.83 | .77–.81 |
| skirmish（至 random_15） | 2 | 2 | 0 | 100% | ~1.0 | ~1.0 |
| skirmish_random_20 → corner_points_medium（13 阶段） | **0** | — | — | — | — | — |

- `random_10` / `random_15` 这一对贡献了 **41 次停滞中的 28 次**。6 次
  starter_random 停滞全是自我折腾的配置（战士削弱、减单位、BC 热启动、
  patience=4）。
- 越过墙的 runs 会清掉它们碰到的一切 — 包括 medium 与 advanced bots
  （38/38 medium 阶段通过，4/5 advanced）— 直到会话死亡。后期课程不是
  「太难」；而是**未探索**。
- 最深 runs：`20260601_172412`（v52a）与 `20260531_165459`（v50），均为
  20/33 阶段、5.5–5.85M 步，都以 `skirmish_random_15`
  **以 ~1.0 WR CLEARED** 结束 — 墙钟死亡，非停滞。

### 停滞取证 — 坍缩，而非无能

| stalled stage | n | peak WR q25/50/75 | med final WR | peak ≥ gate | med avg_turns | med avg_reward |
|---|---|---|---|---|---|---|
| beginner_random_10 | 15 | .79/.90/.99 | **.06** | 14/15 | **72.8** / 75 | **+18.2** |
| beginner_random_15 | 13 | .71/.75/.90 | **.14** | 10/13 | **73.1** / 75 | **+23.6** |
| intermediate_random_20 | 2 | .69/.79/.88 | .02 | 1/2 | 67.1 | +10.5 |

- 每次停滞阶段都消耗了**其步数预算的 100%**：「停滞」意味着策略在阈值附近
  振荡，从未拿到 `patience=2` *连续* 80-episode 评估过线，随后 PPO 更新
  最终把它推进和局吸引子。
- **29/41 次停滞以正平均奖励结束，且 WR ≤ 0.2。** 极端：
  v40_skip_starter 以 WR .0375、avg_reward **+58.5** 结束；
  v53c 把 avg_turns 钉在精确 75.0（100% 和局）达 5M 步。
- 坍缩由训练诱发的重启证明：v21 的 `consolidate_a` 重跑*刚清完*的
  random_10 阶段，在相同设置下从已通过退化到 peak .8625 / final **.0125**。
- 晋级呈双峰：已通过阶段的中位清关时间是 **50k 步**（一个评估间隔 —
  策略到达时已足够强）；不能几乎立刻通过的阶段通常永远过不了。

### 两次 20 阶段 runs 的共同点（及其停滞兄弟所缺）

1. **对手多样性**：random_10/15/20 阶段对战
   `mixed(easy=random, hard=random_harder, p_hard=0.5)`（v43a+ 族），
   而非单一对手。
2. **反和局奖励几何**：`draw: -50`（v52a：按已用回合缩放）、
   `win_speed_bonus: 0`、`enemy_owned_capture: 0`、`turn_penalty: -0.5/-1.0`。
3. `ent_coef` 0.10 → 0.01 线性（全部 10 次 random_15 通过都有 ent_start
   0.10；0.025–0.05 配置挤满停滞列表；v53c 全局 0.05 是 sweep 中最差的
   run）。
4. 更大的 random_10 预算（5M）。

PPO 旋钮相同但 shaping 更多或熵更少的兄弟
（v43b/v44/v46/v51/v52b/v53c）仍以经典 peak-then-collapse 签名停滞 —
  起作用的是奖励几何与对手混合，因为其它都未变。

---

## 2. 代码与配置中的根因

### 2.1 规范配置仍含已被证明有罪的奖励

[`bootstrap_lessons_learned.md`](bootstrap_lessons_learned.md)（§"RESOLVED"，v26/v27 表）给出二分：
将 {win_speed_bonus, enemy_owned_capture, turn_penalty} 置零可清 beginner 块
（v26）；单独恢复 `win_speed_bonus: 50`（v27a）或单独恢复
`enemy_owned_capture: -15`（v27c）各自独立重现 random_10/15 停滞；
`v28_production_reward_fixed.yaml` 固化了修复。然而 `configs/ppo/bootstrap.yaml`
— 在该决议*之后*仍被改过，且是 `scripts/train/train_bootstrap.py` 的默认 —
仍自带 `win_speed_bonus: 50.0`（第 150 行）、`enemy_neutral_capture: -8.0` /
`enemy_owned_capture: -15.0`（第 163–164 行）、`turn_penalty: 0.0`（第
142 行）。**今天对规范配置的新鲜 run 会重跑 sweep 已证明会停滞的配置。**

### 2.2 和局吸引子是奖励几何定理，不是坏运气

每步事件收入（战斗 shaping、占领、`seize_progress: 3`、
收入/单位/结构势）随 `max_turns` 缩放，而和局终局是固定 −50，且终局步跳过
shaping（`gym_env.py:1488–1496`）。在 75 回合 beginner 和局上，可耕作的
非终局收入（停滞 runs 中约 +60–95/episode）超过 |−50|，因此存在「安全付费
港湾」（v49 自己的头注释：和局收取 +28..+55 —「和局被*正向*奖励」）。每个
地图块因 `max_turns` 增大（75 → 120 → 200）而终局固定，重新打开吸引子；
v52a 的按回合缩放和局惩罚是结构性对策，应成为默认。由于 draw == loss == −50
而 `turn_penalty` 为负，快速失败可以在回报上支配长和局，并与慢赢匹敌 —
 净每回合税后，`win > draw > loss` 的奖励排序实际上并未被强制。

### 2.3 晋级机制：噪声门槛、无地板、赢家诅咒、无重试

- `PromotionCallback`（`callbacks.py:309–344`）在 `patience` 次连续评估
  ≥ 阈值时晋级；`min_timesteps_before_promotion` 默认为 0（`config.py:254`）
  且 bootstrap.yaml 未设置，首次评估在阶段入口后一个 vec-step 内触发
  （`callbacks.py:160–169` + `reset_num_timesteps=False`），因此 117/233
  次通过发生在 ≤2 次评估内。多数快速通过是真实的（86/117 约 1.0 WR），
  但门槛对晋级后遇崖的策略没有保护。
- 80-episode 评估在 p≈0.7 时给出 ±10pp CI。门槛距可达天花板约 5pp 内
  （random_15 的 0.70 vs 0.63 脚本天花板）使晋级变成运气彩票；
  `patience: 4`（v13/v15/v16）甚至让 starter_random 的 0.90 门槛不可达
  （v16 peak .9125 后停滞）。
- 阶段之间运行器恢复按评估 WR 最佳的 checkpoint
  （`bootstrap.py:957–971`）— 对噪声评估的 argmax，赢家诅咒选择。但在
  **停滞**时它抛出 `CurriculumStalled`（`bootstrap.py:908–941`）*且不使用*
  同一 `best_model.zip` — 28/41 次停滞阶段磁盘上有 peak ≥ 阈值，run 直接
  死亡。notebook 随后 `runtime.unassign()`（cell 40）。
- `win_rate` 中和局计为失败（`evaluation.py:357`）。在肉墙 random 阶段，
  多数非胜是和局；按排除和局的胜率门控是最严格的读法。

### 2.4 视界：γ=0.99 覆盖微动作 episode

一步 env = 一次单位动作；`end_turn` 在该步内执行整段对手回合
（`gym_env.py:1280–1309`）。Beginner episode 约 700–1500 env 步
（75 回合 × ~20 步/回合），skirmish 可达 ~2400。
有效视界 1/(1−γ) = 100 步 ≈ **5 个游戏回合**；0.99^800 ≈ 3e-4。
长视界后果（经济雪球、HQ 护送、*不*和局的价值）对早期状态的回报不可见；
在此视界下只有稠密事件奖励是可学信号。这就是为何奖励重权（v50/v52a）
能起作用，而其它不能：**γ、gae_lambda、lr、n_steps、batch_size、clip_range、
n_epochs、vf_coef、网络规模在全部 59 个配置中字面相同**（仅 ent_coef，以及
有一次 net_arch 不同）。从未试过 γ≈0.997–0.999 并重标定终局，或按回合
（而非按动作）的决策粒度。

### 2.5 会话经济与缺失的 resume 路径

- 课程最坏情况总预算：87.5M 步。观测最大：7.9M（中位 2.1M）。串行单环境
  评估吃掉约 30–50% 会话墙钟（80 episodes × 每 50k 步 × 33 阶段）。
- 15/56 可用 runs 结束在刚清完的阶段（其中 13 个总步数 ≤750k —
  早期 Colab 切断）。两次 20 阶段 runs 都如此死亡。
- `run_curriculum`（`bootstrap.py:637`）总是从 stage 0 开始；
  `warm_start_path` 只播种初始模型。没有从 stage-K 恢复，因此每个会话都
  从零还债整条天梯 — 在到达前沿前约 1–2M 步已解决阶段。

### 2.6 当前前沿的潜在天花板（skirmish_random_20+）

- **512 动作截断**：skirmish 状态测得 728–744 合法动作；`_build_flat_actions`
  在 `max_flat_actions=512` 截断，枚举顺序（create → move → attack → …，
  `gym_env.py:82–93`）意味着大军上 **attack/heal/cast 动作被静默先丢掉**。
  足够大到能赢的军队无法攻击。
- **位置式动作语义**：`Discrete(512)` 索引 i =「每步重建列表的第 i 项」
  （`gym_env.py:1461–1468`）；映射每步变化，并依赖不可观测的单位插入顺序
  （`game_state.py:1319, 1351`）— 真观测别名。策略仍在小地图上对
  medium/advanced 达到 1.0 WR，因此今天是样本效率税，但随军队规模恶化。
- **`masked_avg` 池化**（`extractors.py:189–195`）把 CNN 地图压到 64 维
  （+5 全局 → Linear(69, 256)）再进动作头 — 精确空间目标选择必须挤过全局
  平均。全部 sweep 配置都用它（`pool: flatten` 未用）。
- **`max_steps: 3000` vs corner_points 的 `max_turns: 200`**：模拟显示
  重军队对局在约 90–135 回合累积 3000 agent 步，因此 yaml 的
  「截断从不触发」注释（第 22–24 行，仍引用「max_turns 20/60/120」）已过时 —
  corner_points 对局将以 −50 截断和局结束，无论盘面如何，且 `win_speed_bonus`
  按 episode 达不到的 200 回合视界标定。
- **前方门槛-vs-天花板违规**：从 agent 座位模拟（新鲜，每对阵 30–40 局）：
  `intermediate_medium` 门槛 0.65 vs 最佳脚本 0.30；`skirmish_medium` 门槛
  0.70 vs AdvancedBot 正好 0.70；bot 层级按地图非单调（AdvancedBot 在
  intermediate 上 *输给* MediumBot 0.30，但在 skirmish 上赢 0.70）。先手优势
  巨大（MediumBot 镜像：P1 赢 93–97%），且 P2 多一拍收入
  （`game_state.py:1246`）— agent 总是打 P1，训练静默依赖座位优势。

### 2.7 Notebook 与工具缺陷

- **Run-All 当前损坏**：cell "3c" 自带 `BUILD_BC_WARMSTART = True`，在训练
  开始前对默认 `bootstrap.yaml`（flat_discrete）抛
  `RuntimeError("BC warm-start requires action_space_type=multi_discrete…")`。
  （run 数据也同意 BC 热启动应保持关闭：v33 与 skirmish_bc_selfplay 得 0.000 WR。）
  成功的 BC 构建还会覆盖任何手动设置的 `cfg.warm_start_path`。
- **训练诊断从不落盘**：`TrainingMetricsCallback` 把 approx_kl / clip_fraction /
  explained_variance / value_loss（`callbacks.py:53–62`）收集到内存；
  `bootstrap.py` 写评估 JSON/CSV 但从不写训练记录，notebook 只实时画图 —
  随 Colab VM 消失。因此坍缩动态（KL 爆炸？价值发散？熵坍缩？）无法从归档
  runs 诊断，59 个变体在对此盲目的情况下设计。
- **`run_status.json` 被写但从不被读**：分析 notebook 纯从
  `bootstrap_results.csv` 尾部分类阶段。（这不腐蚀停滞统计 — 中途中止的阶段
  只显示 `not_started` — 但截断-vs-停滞必须从 `total_env_steps` 推断，且
  汇总 CSV 会把清完后被杀的 run 误标为「以 cleared 结束」。）
- **训练环境无 `Monitor` 包装** → 所有训练图中 `rollout/ep_rew_mean`、
  `ep_len_mean` 静默缺失。
- **处处单 seed**：全部 59 配置用 `seed: 42`，每变体一次 run。配置重跑时
  结果翻转（bootstrap：random_10 上 4 通过 / 1 停滞；v43a：1/1；v16：1 通过 /
  2 停滞；相同配置+阶段清关步数可差 3×）。多数单旋钮 sweep 结论在 run-to-run
  噪声内。
- **`ppo_training.ipynb` 已分叉**：重标定前的 ±5000 奖励、训练全新模型，
  名义上的「从 bootstrap checkpoint 自对弈」交接从未实现 — 成功的 bootstrap
  目前没有可用的下游消费者。
- 值得知道的机制怪癖：最小 1 伤害钳制让不能合法反击的单位获得幻影反击；
  停在己方结构上的受伤单位自动治疗并静默花费 agent 金币。

---

## 3. 建议，按预期价值排序

1. **把已验证的奖励几何回写进 `bootstrap.yaml`**（每个新 run 继承它）：
   `win_speed_bonus: 0`、`enemy_owned_capture: 0`、`turn_penalty: -0.5..-1.0`、
   按已用回合缩放的和局惩罚（v52a），保持净回合税后 `draw` ≤ `loss`，使
   win > draw > loss 在回报层面成立。对所有 random_N 阶段采用 v43+ 混合
   random 对手。
2. **增加阶段 resume + 停滞重试。** 每阶段持久化（阶段索引、模型、优化器、
   熵调度位置）；让 `run_curriculum` 从 stage K 开始；在 `CurriculumStalled`
   时重载该阶段 `best_model.zip`（28/41 停滞曾高于阈值）并以重新预热的熵
   重试一次再放弃。把两种观测到的死亡模式（墙钟与停滞）从 run 致命变为
   可恢复。在 87.5M 步预算 vs ~6M 步/会话下，单靠奖励修复无法跑完天梯。
3. **修正超过可达天花板的门槛。** 单独统计和局（对 win+draw 或 Elo 式分数
   门控），或在肉墙 random 阶段提高 `max_turns` / 加入打破增援的机制；按
   现配置，`beginner_random_15/20` 的 0.70 高于 agent 座位上任何脚本 bot 的
   WR（最佳 0.63），`intermediate_medium` 的 0.65 约为脚本天花板（0.30）的
   ~2×。把 `min_timesteps_before_promotion`（v31 风格）加入生产，并对
   Wilson 下界而非原始 WR 门控，以杀死 ±10pp 彩票。
4. **持久化训练诊断**（metrics_callback.records → 每阶段 CSV，随每次评估
   刷新），以便最终归因 peak-then-collapse（KL/clip/熵/价值）。便宜，且每个
   未来 sweep 变体都可诊断。
5. **从优化器侧攻击坍缩** — 唯一从未触碰的轴：阶段后期降低/退火 LR、更紧
   clip_range、更大 batch，以及 γ 0.997–0.999（或按回合宏动作）把终局拉进
   视界。另外，当阶段在 50k 晋级时，停止在 `max_timesteps` 上退火熵 —
   按预期晋级步数退火或设地板。
6. **对 skirmish/corner_points 提高 `max_flat_actions`（≥1024）并重排枚举
   使攻击在截断中存活**；对 corner_points 提高 `max_steps`（≥4500）或随
   `max_turns` 缩放。更长期地，用 pointer/per-cell 动作头与 `pool: flatten`
   替换位置扁平头，一次去掉两个表示天花板。
7. **任何打算保留的结论都跑 ≥3 个 seed**，并在每次晋级时对固定对手电池
   （例如当前地图上的 random_15 + simple + medium）重评，以测量而非假设
   保留/遗忘。
8. 小卫生：默认 `BUILD_BC_WARMSTART = False`（当前对 flat_discrete 配置破坏
   Run-All）、用 Monitor 包装训练环境、让分析 notebook 读 `run_status.json`、
   刷新 bootstrap.yaml 中过时的 `max_turns` 注释，并要么接通
   `ppo_training.ipynb` 的自对弈交接，要么退役该 notebook。

## 附录：最深 run 轨迹

- **20260601_172412 / v52a** — 20/33，5.85M 步，以 CLEARED 结束
  （会话切断）：balanced_random 100k@1.0 → r10 850k (1.0/.99) → r15 350k
  (.96/.76) → mixed 50k@1.0 → r20 1.45M (.85/.79) → simple→advanced
  各 50–100k @.85–1.0 → intermediate 块通过（r15 1.1M .98/.89，
  r20 850k .93/.91）→ skirmish balanced/r10 50k@1.0 → skirmish_r15
  150k@1.0。**END（墙钟）。**
- **20260531_165459 / v50** — 20/33，5.5M 步，形状相同；r20 最慢
  （2.1M，.75/.75）；在 skirmish_random_15 以 CLEARED 结束（1.0/.99）。
- **20260527_150915 / v37b** — 15 个阶段以 .85–.90 阈值通过，几乎全在
  1.0 WR，然后 intermediate_random_20：peak .975 → final .0375，
  avg_turns 74.2/75，烧尽全部预算。单对手训练 + 旧 shaping：坍缩被推迟，
  未被修复。
