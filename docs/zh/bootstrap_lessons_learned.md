# PPO Bootstrap — 经验教训

针对 `notebooks/ppo_bootstrap.ipynb` 与 `reinforcetactics/rl/bootstrap.py`
的课程式 bootstrap 工作回顾。记录我们在这款策略游戏上冷启动 PPO 时
踩过的坑，尤其是长时间试图教会智能体攻占敌方 HQ 的那条主线。

这些教训来自多次长时间 Colab 训练：训练会以各种方式卡住，而“显而易见”
的修法往往无效。在你改动 10→课程、或想换成“更简单”的对手之前先读本文——
许多看起来更容易的做法，对 PPO 反而更难。

## TL;DR

1. **不要用确定性对手做 PPO 课程训练。** NoopBot 产生零状态方差 → 零回报
   方差 → 零优势信号。PPO 无法从常数奖励中学习。
2. **“更简单”的对手对算法未必更简单。** 随机对手才是真正容易的训练目标，
   因为其动作注入了 PPO 所需的方差。
3. **HQ 占领很难直接学。** 它需要 7+ 步承诺序列（建造 → 走位 → seize ×4），
   且地形奖励稀疏。更稳妥的做法是通过课程阶段，使歼灭也成为可行胜径。
4. **奖励形状要匹配地图几何。** 在小地图（`starter.csv`）上有效的
   “5×歼灭 vs HQ 占领”加分，在更大地图（`beginner.csv`）上会变成扭曲激励，
   因为 HQ 占领在几何上不现实。
5. **盯紧评估 episode 上的 `std=0.0`。** 这是最有诊断价值的单一信号——
   几乎总是表示策略被锁死，而不是环境“本质上确定”。
6. **把峰值向前传递，但不要强制过训。** PPO 会在阶段内漂移；内存中的
   阶段末策略往往弱于该阶段的 `best_model.zip`——因此在阶段之间恢复最佳
   （`restore_best_checkpoint_between_stages`，默认开启）。但在带
   draw-with-shaping 吸引子的随机阶段上，*越过策略自然峰值的额外训练会
   侵蚀致胜行为*。v31 通过 `min_timesteps_before_promotion` 强制更多训练，
   结果比 v28 更早卡在一个阶段。该门控保留为代码中的 opt-in 功能，但
   **不会**在生产的 `*_random_N` 阶段上设置；在漂移吸引子阶段上，PPO
   的自然晋级节奏优于强制过训。
7. **BC 数据集质量 > 数据集规模。** 完全确定性 bot-vs-bot 对局的 N 个
   episode，产生的是 **1 条唯一轨迹复制 N 次**，而不是 N 条不同演示。
   没有新的 `stochastic_tiebreak` 选项（或随机对手），BC 数据集大部分是
   重复，策略会背下三套对局脚本而不是学到分布。见文末
   “BC 热启动：我们学到了什么”。
8. **确定性 bot-vs-bot 中观察到的玩家侧不对称，通常是伪影，不是结构。**
   skirmish.csv 上 AdvancedBot-vs-AdvancedBot 看起来像玩家 2 的 0/60 横扫——
   从玩家 2 录演示似乎是显然修复。开启 stochastic tiebreak 后，同一对局
   是玩家 1 的 40/60（即大致对称）。不要从“平局按数据结构迭代顺序解决”
   的运行里得出“地图偏袒 X 侧”的结论。
9. **临时评估环境必须转发生产环境使用的每一个 kwarg——不只是明显的那些。**
   尤其是 `reward_config` 和 `max_actions_per_turn`。环境内置默认值相对
   调好的 YAML 偏差 10–1000×；缺少 `max_actions_per_turn` 会关掉生产训练
   依赖的 never-end-turn 安全网。我们在 20260524_225835 撞上过，差点误诊
   “BC 坏了”，实际是评估环境一行 bug。见 “BC 热启动” → 失败模式 G。
10. **更好的 BC 训练指标 ≠ 不同的对局表现。** 运行 20260525_015401 把
    `end_turn_weight` 从 10× 提到 30×（3× 自动平衡），BC 训练明显更好
    （loss 2.73 → 1.21，action_type_acc 0.78 → 0.83，full_action_acc
    0.21 → 0.27）——但 BC 对 SimpleBot 的 sanity-eval 结果 *字节级相同*。
    类别重加权抬高了 end_turn 样本的梯度贡献，使策略在 end_turn 是
    *正确演示动作* 时预测更准，但不会改变其他状态上的 argmax 先验
    （那些状态上演示者会做有产出的动作）。Loss / 准确率曲线可以改善，
    而游戏表现不变。在信任训练指标之前，先用 bot 阶梯做 BC sanity-eval。
    见失败模式 H。
11. **单策略吸引子是环境结构问题，不是课程可调问题。** v34–v37 独立拉动
    四根杠杆——战斗 shaping 奖励、轻度 Warrior 属性削弱（atk 10→8，def 6→4）、
    卡关阶段 2× 预算、MixedBot 中期桥梁、更高晋级阈值——结果所有通过阶段
    上 **100% 单 Warrior 策略**。v37b 以每阶段 100% WR 通过 15 个阶段，
    全部 mono-W，零技能使用、零 HQ 占领。若默认单位平衡在最便宜档同时
    赢 HP/$、Atk/$ 和防御优势，PPO 会找到它并永不离开。修复在代价曲线
    几何（v38/v39 改了 Warrior 价格），不在课程压力。
12. **不要在最紧时钟的地图上做平衡实验。** v38（结构属性 nerf）和 v39
    （仅成本 nerf）都卡在 `starter_random`（51% / 35% WR）——*不是* nerf
    错了，而是 starter 的 $250 起始金 + max_turns=20 没有空间让 nerf
    要教的战略权衡发生。同一 nerf 在 beginner（max_turns=75，$400 起始）
    上 200k 步就以 100% WR 通过第一阶段。Starter 是导航热身；当实验
    关于平衡而非导航时，从课程中拿掉它。
13. **阵容跟踪应进入评估流水线。** 每阶段 `units_built` 告诉你策略学到了
    战略，还是只是剥削最便宜的性价比单位。仅有 WR + W/L/D 时，
    “靠 mono-Warrior 歼灭获胜”与“靠多元阵容 + HQ 突袭获胜”看起来一样。
    `viz.plot_curriculum_composition_summary`（本分支新增）一眼可见——
    没有它，四次迭代在 WR 曲线上会无法区分。

## 本环境上的冷启动问题

PPO 以近均匀策略起步（正交初始化缩放 0.01）。智能体尚不能做任何有用事，
因此 rollout 大多是失败轨迹。出现了三种具体失败模式：

### 失败模式 1：死策略陷阱（dead-policy trap）

**症状**：每个评估 episode 产生 *完全相同* 的奖励、长度和 W/L/D 分解。
在数十万步上，30 个 episode 的 `std_reward = 0.0`。TensorBoard 中
`approx_kl ≈ 0`。

**原因**：所有 rollout 回报恒定 → 价值函数拟合该常数 → 优势塌缩到 ≈ 0 →
策略梯度 ≈ 0 → 无更新 → 无探索 → 无新训练数据 → 循环。策略永久卡在
初始化 argmax 碰巧落在的地方。

**修复**：引入 *任何* 能给回报带来方差的东西。最简单来源是随机对手。
单独加大熵奖励无济于事——若无论选什么动作奖励都塌成常数。

### 失败模式 2：换图时价值函数灾难性错位

**症状**：智能体在 `starter.csv` 上达到 100% WR（评估 `reward std=0.0`——
完全确定、严重过拟合），首次接触 `beginner.csv` 时塌到 0% WR，策略狂刷
`end_turn`。过渡时训练侧 `train/explained_variance` 从 ~0.9 掉到 ~0.05。

**原因**：价值头学到了“starter 地图状态价值”。beginner 地图状态维度相似，
但实际回报天差地别，预测灾难性错误。PPO 的梯度信号在试图修正一个预测
完全不同分布的价值函数时失控；同时策略在噪声下退回“安全”选择（结束回合）。

**修复**：不要让 starter 策略结晶过硬。starter 阶段用 `patience: 1`，
首次达到阈值就晋级，而不是第二次评估再确认。仍能得到合格策略，但收敛
不那么完美，迁移更好。同时在第一个 beginner 阶段提高 `ent_coef`
（例如 0.05 → 0.10），在过渡期注入探索噪声。

### 失败模式 3：对 `end_turn` 的结构性奖励偏差

**症状**：在 noop 阶段，PPO 梯度漂移随时间把策略推向 `end_turn`。
end_turn 采样概率从 ~20% 均匀先验升到 50k 步后的 ~26%，并继续爬升。
即便策略短暂采样 `create_unit` 或 `move`，低 explained-variance 更新的
梯度噪声也会把它推回 `end_turn`。

**原因**：`turn_penalty = -20` 每回合无条件施加，对每个状态的 V(s)
产生恒定负拖拽。智能体不会把它体验为“end_turn 代价”——而是每个状态
V(s) 的一部分，使“更快推进回合”在结构上有吸引力。在多次缓慢更新中
这会累积，尽管 end_turn 并不会真正缩短固定长度 episode。

**修复**：去掉结构性偏差。在没有真实对手施压的阶段，设 `turn_penalty: 0`，
依赖正向逐动作 shaping（例如 `create_unit: +30`，`move: +5`）建立严格序：
`seize_progress > capture > create_unit > move > end_turn`。或者更稳健：
根本不要跑 noop 阶段（见下）。

## 为什么我们去掉了 `noop` 阶段

纸面想法合理：第 0 阶段对字面无操作对手，让智能体孤立学习导航与 HQ 占领，
再引入战斗动态。实践中它制造了我们遇到的最糟 PPO 失败模式。

`NoopBot.take_turn()` 调用 `end_turn()` 即退出——零对手动作、零状态扰动。
加上确定性评估（`MaskablePPO.predict(deterministic=True)` 取 argmax），
意味着 *每个* 评估 episode 产生相同轨迹、相同奖励、相同长度。30 个 episode
上 `std=0.0`。

后果链：

```
deterministic opponent
    ↓ no state variance across episodes
constant return distribution
    ↓ value function fits the constant
advantages collapse to ≈ 0
    ↓ policy gradient ≈ 0
no policy updates
    ↓ no exploration of new actions
training rollouts stay near initialisation
    ↓ same constant returns
[loop: stuck]
```

智能体最终会移动 *一个* 状态的 argmax（episode 开始时的空棋盘状态，
正的 `create_unit` 奖励每次采样建造都会触发），但从不移动建造后状态的
argmax。结果：1 次建造，然后 20 次 `end_turn`。在 250k 步中策略众数
字面没变。

Random / SimpleBot / MediumBot 对手能避免这一点，因为它们的动作使游戏
状态在 episode 间不同，回报有方差，PPO 才有优势信号可更新。**“更简单”
的对手反而是更难的学习目标。**

若将来再引入 noop 式训练，必须搭配非 RL 热身（从脚本演示行为克隆），
使策略进入 PPO 时已知道建造-并-占领模式。纯 RL 无法在确定性对手阶段
bootstrap。

## 为什么我们保留（且未改）原始 6 阶段布局

*有效* 的 pre-bootstrap 配置是：

```
starter map:  random → simple → medium
beginner map: random → simple → medium
```

我们加了每阶段覆盖（`max_turns`、`max_steps`、`ent_coef`、`reward_config`）
以处理 starter→beginner 换图，并在 beginner 上加了 `balanced_random`
作为稍易的对手动态垫脚石。但全程仍以对手随机性作为主要探索驱动。

具体来说，*不要* 跳过：

- **Random 作为第一个对手。** PPO 需要方差。
- **starter 阶段 `patience: 1`。** 防止不迁移的过拟合。
- **第一个 beginner 阶段的熵提升。** 换图是危险过渡；后续阶段再冷却回 0.05。
- **有对手的 beginner 阶段奖励重塑。** 大地图上 HQ 占领几何不现实；
  将 HQ 占领与歼灭终局奖励拉平（原 5000/1000，现 3000/3000），并把
  `seize_progress` 从 300 降到 50，避免智能体在争抢空间里被付费去
  开始完不成的 seize。

## 一路上有用的改动

即便去掉 noop，仍有若干干预保留：

- **更大 MLP**：SB3 默认 `net_arch=[64, 64]` 对 ~734 维 Dict 观测 +
  512 维 flat-discrete 动作头偏小。隐层维度少于动作选择数。提到
  `[256, 256]`，总约 ~640K 参数。尚无空间提取器——在 grid/units 通道上
  的小 CNN 可能进一步有帮助，但非严格必需。
- **`PPOConfig` 上的 `policy_kwargs` 字段**：使 net_arch 等策略定制可从
  YAML 配置，而不是埋在 `_default_model_factory` 里。
- **每阶段 `reset_num_timesteps=False`**：为跨阶段 WR 图保留全局时间轴。
  注意：`model.learn(total_timesteps=N, reset_num_timesteps=False)` 实际
  训练到 `num_timesteps >= num_timesteps + N`，即 SB3 在设置时把当前计数
  加到请求总量上。每阶段打印的预算是“额外 N 步”，不是绝对值。
- **带 patience 的 `PromotionCallback`**：推进阶段的正确方式是
  “WR ≥ 阈值连续 `patience` 次评估”，不是“第一次打到阈值就晋级”。
  避免一次幸运评估晋级。
- **带清晰信息的 `CurriculumStalled` 异常**：阶段预算用尽仍未晋级时
  大声失败，而不是静默把未晋级 checkpoint 交给下一阶段。

## 有效的诊断手段

阶段卡住时，按此顺序：

1. **看 W/L/D 分解。** `0/0/30`（全平）表示 episode 超时。`0/30/0` 表示
   对手杀了智能体。修复不同。
2. **查 `std_reward`。** `0.0` = 确定性环境上的锁死策略。任何 > 0 = 策略
   在不同 episode 做不同事（好，即使 WR 低）。
3. **分解奖励。** `mean − terminal_baseline` 告诉你智能体是否在收集 shaping
   奖励。若 shaping ~0，智能体没做任何有产出的事（不建造、不移动、不 seize）。
   若 shaping 大但终局差，说明在探索但完不成。
4. **看随时间的 `action_counts`。** 平坦的 100% `end_turn` 带是模式崩溃。
   健康训练是早期 `create_unit`，过渡到 `move`，最终 `seize`。
5. **看 TensorBoard 的 `train/explained_variance`。** 低于 0.1 表示价值函数
   几乎没拟合；低于 0.0 表示主动错误。会阻断所有 PPO 梯度信号。

## 当 PPO 确实学不会任务时

若在退回到“仅随机对手”之后，智能体在几十万步内仍碰不到获胜轨迹，
下一步升级 *不是* 更多熵或更花哨的奖励 shaping——而是从脚本演示做
**行为克隆（behaviour cloning）**。

模式：写一个演示生成器，程序化打一局胜局（造 Warrior，走到敌 HQ，
seize ×4），记录 (obs, action) 对，在启动 PPO 前对策略网络做若干 epoch
监督学习。BC 后策略已“知道” build → move → seize 模式；PPO 再在奖励信号下
精炼。`imitation` 库（sb3 配套）与 SB3 策略集成干净。

我们没交付这条——更便宜的替代（去掉 noop、用随机对手）就够了。但若
稀疏奖励探索真的失败，这是下一根杠杆。

## 不值得再追的方向

- **更大熵** 作为主修复。我们试过 `ent_coef=0.10`（以及更高原型）。
  对换图有用的一次性 bump，对死策略陷阱无用。问题不是“策略分布太尖”，
  而是“完全没有梯度信号”。
- **更大逐动作奖励** 作为主修复。我们把 `create_unit` 10 → 30 → 30、
  `move` 0.5 → 5。智能体从不响应。问题不是奖励幅度，而是 rollout 间
  奖励 *差异*（需要对手方差）。
- **负的 `end_turn` 奖励。** 在相反方向重新引入恒定基线偏差，无助于
  底层冷启动问题。
- **更多训练步数。** 卡住不会靠等待解开。若策略 250k 步没动，2.5M 也不会。

## ⚠️ 更正 — 下文 v15–v23 结论曾被混淆

**读 sweep 小节前先读这段。** “课程调参 sweep（v15–v23）” 中的分析建立在
`runs_summary.csv` 上，其中 `enabled_units` 列是错的。分析 notebook 从
run 根 YAML 取阵容，没有就回退到“全部 8 个”——几乎每个 run 都这样。
修正审计读取权威的 `config.json:env_config.enabled_units` 后，推翻了两条
头条结论：

1. **“缩小单位阵容会灾难性失败”（来自 v22）是错的。** v22 用了 `[W,K,A,M]`
   （Knight，*无 Cleric*）+ `tp=-0.5` + v16 后引擎。*整个历史中进展最深的
   run* 用的是 **受限** 阵容：
   - `20260511_132922`：阵容 `[W,M,C,A,K]`，`tp=-0.2`，rt 0.2.5 →
     **到达 `skirmish_simple`——17 个课程阶段**，比所谓“高水位”v19 深约 3×。
   - `20260512_163309` / `_195716`：阵容 `[W,M,C,A,K]`，`tp=0.0` →
     以 **50k 步 100% WR** 通过 `beginner_random_15`（v17–v23 在这上面
     耗了数百万步卡住）。
   - 深的 `[W,M,C,A]`（4 单位，*含* Cleric）run 到达 `beginner_advanced`
     （12 阶段）。
   受限阵容是记录上 *最好* 的配置。v22 失败是因为丢掉 Cleric 并叠了
   v16 经济，不是因为单位更少。

2. **“单独 `turn_penalty=-0.5` 引入了 random_15 墙”不完整。** v16 同时改了
   *三件事*：阵容（受限 → 全 8）、`turn_penalty`（0 → -0.5）、引擎经济
   （Knight 防御 5→7，HQ 收入 150→100）。每个 all-8 + tp=-0.5 的 run 都卡住；
   每个深 run 都是受限阵容 + tp≤0 + pre-v16 经济。墙与 *三重* 变更相关，
   不是孤立的 turn_penalty。

诚实保留的 caveat：阵容 + tp 不 *充分*——`20260513_033055`（v15）用了
`[W,M,C,A,K]` + `tp=0.0` 仍卡在 random_10（其 v15 熵地板变更是区分点）。
且深 run 在 6–17 阶段 *停了*（Colab 断连 / 短会话），无法证明它们不会
稍后卡住。但“自 v17 起每个 run 都卡在 random_15”只描述 all-8 + tp=-0.5
分支——修正数据表明那是对可工作配置的回归。

**v24（`v24_reproduce_deep_config.yaml`）复现 17 阶段配置**：阵容
`[W,M,C,A,K]`，`turn_penalty=-0.2`，引擎回退到 Knight def=5 / HQ income=150
（constants.py，一并提交），基于 v18（标准课程 + 已验证的 patience=2 修复，
无 consolidate 实验）。若 v24 进展深，整个 v17–v23 熵/patience/阈值绕路
是在治疗自伤回归。

原 sweep 小节 **未编辑** 保留，因其 *机制性* 观察（draw-with-shaping 吸引子、
漂移 vs 平台诊断、GPU 非确定性、热启动不可复现）仍然有效有用——只有
对阵容盲目的比较结论被本更正取代。

## ✅ 实验 A 结果 — 深配置是真的；回归在代码路径上

运行 `20260515_213159` 是忠实复现：检出 commit `6eb0566`（rt 0.2.5）
未编辑，`ppo_bootstrap.ipynb` 从该 commit Run-All，安装时验证经济
（`STARTING_GOLD=250 HQ_INCOME=150 Warrior_atk=10 Knight_def=5`），
阵容 `[W,M,C,A,K]` 经活动 cell-11 覆盖，`turn_penalty=-0.2`，24 阶段
rt-0.2.5 课程。**它复现了深进展，甚至更多：**

- `starter_random/simple/medium` → `beginner_balanced_random` →
  **`beginner_random_10` 在前两次评估就通过（WR 1.0, 1.0）**——正是每个
  v16–v24 run 死掉的阶段。
- `beginner_random_15`（0.99/1.0），`beginner_random_20`（0.89/0.90），
  `beginner_simple/mixed/medium/advanced`——全部通过。
- `skirmish_balanced_random` → `skirmish_random_10/15/20` 通过
  （各自经 collapse→recover 穿过 draw 吸引子——策略在此 commit *能逃出*）。
- 卡在 **`skirmish_simple`（阶段 17）**，从 5.8M 到 8.8M timesteps WR 0.0
  （会话结束）——与历史深 run 的恢复签名完全一致。

这是 **决定性的**。排除剩余假设：

1. **不是经济。** v24 回退了经济仍卡在阶段 5。此处独立轴确认。
2. **不是幻影 / 不是课程长度伪影。** 深进展真实、端到端、可重复——
   通过 16 阶段，不是 Colab 停止计数。
3. **是 rt 0.2.5 → 0.2.7 代码路径。** 使 `beginner_random_10` 在当前代码
   上不可通过的回归，活在 `6eb0566` 与 HEAD 之间漂移的引擎/训练代码里——
   *不是* 配置、*不是* 经济、*不是* 阵容。

机制注：skirmish 阶段都出现了 draw-with-shaping 塌缩（1.0 → 0.0 平局约
1M 步 → 弹回 1.0）。在 `6eb0566` 智能体 **逃出** 该吸引子；在当前代码的
`beginner_random_10` 上则永不逃出。回归很可能没有加硬性破坏——它使
draw 均衡吸引子 *不可逃出*。首要嫌疑：`c7001bf`（“用终局速度奖励替换
逐 end_turn 代价”）——直接作用在深配置 `turn_penalty=-0.2` 所 shaping 的
平/胜激励上的奖励景观变更。

下一步本是对 `6eb0566..HEAD` 做 **代码二分**——但结果 **根本不是代码回归**。
见紧接的 RESOLVED 小节。

## ✅ 已解决 — 回归是 `6eb0566` 之后的奖励添加（代码脱罪）

上文“0.2.5 → 0.2.7 代码路径”框架是 **错的**，错的原因有教益：v24 被假设
为忠实配置移植，却静默携带了深 run **从未有过** 的三项奖励——
`win_speed_bonus: 50`（`c7001bf` 添加）以及 `enemy_neutral_capture: -8` /
`enemy_owned_capture: -15`（`922aa29` 添加）。其他每个奖励键与 `6eb0566`
字节相同。

`v26_faithful_deep_reward_on_head.yaml` 定了论（运行 `20260516_194038`）：
**现代 HEAD 代码**（rt 0.2.7，现代 obs/extractor/masking）+ 字节忠实的
`6eb0566` 奖励形状（那 3 项置零）+ 经 `engine_overrides` 的忠实经济 →
**通过 `beginner_random_10`**（`promoted: true`，`best_win_rate 0.9625`，
WR 96.25%/83.75%；`run_status: completed_curriculum 5/5`）。与实验 A
非比特相同（奖励/回合有差异——配置真正落地，不像惰性实验 B 测试 #1），
因此是真实、独立的通过。

| Run | 代码 | 奖励形状 | `beginner_random_10` |
|-----|------|----------|----------------------|
| 实验 A | 6eb0566 | 深（忠实） | 通过，16 阶段 |
| v24 | modern | 深经济 **+ win_speed_bonus 50 + 占领惩罚** | **卡在阶段 5** |
| **v26** | **modern** | **深，那 3 项置零** | **通过** |

v24 卡住与 v26 通过之间 *唯一* 的 delta 就是那三项奖励。**那就是回归。**
它 **不是** 代码回归——现代 obs 瘦身 / CNN 提取器 / masking / RandomBot /
课程在奖励形状忠实时都能顺利过 `random_10`。修复是 **仅配置**。整个
v17–v23 熵/patience/阈值 sweep 以及计划中的代码二分，都在追自伤的
*奖励* 回归——从不需要代码二分。

### 最终隔离 — 两个独立元凶项（`v27a/b/c`）

`v27a/b/c` 在已证明的 v26 基线上各自重新启用三项中的 **恰好一项**
（现代代码，经 `engine_overrides` 的忠实经济，仅一项奖励变化——三个 run
均验证 `git b1926c2`，rt 0.2.7）：

| Run | 重新启用的项 | `beginner_random_10` | best WR |
|-----|--------------|----------------------|---------|
| `20260516_202350` v27a | `win_speed_bonus: 50` | **卡住**（`curriculum_stalled`） | 0.80 |
| `20260516_222009` v27b | `enemy_neutral_capture: -8` | **通过**（`completed_curriculum 5/5`） | 0.9875 |
| `20260516_230751` v27c | `enemy_owned_capture: -15` | **卡住**（`curriculum_stalled`） | 0.90 |

**两项独立重现墙：`win_speed_bonus`（`c7001bf`）与 `enemy_owned_capture`
（`922aa29`）。** `enemy_neutral_capture` **无害**（v27b 以 98.75% 通过）。

机制注：v27a/c 并未硬塌到 0%——它们峰值 *高于* 0.75 门控（0.80 / 0.90），
但预算内无法连续两次评估守住。这就是上文记录的 draw-with-shaping
**策略漂移不稳定性**：每一项都扰动奖励景观，足以阻止在 `random_10` 上
*稳定* 收敛，即便策略短暂达到能力。与 v26（三项全零 → 稳定通过）和
v24（三项都在 → 硬 0% 卡住）一致。

**交付修复：** 在现代代码上，生产奖励配置必须设 `win_speed_bonus: 0`、
`enemy_owned_capture: 0` 和 `turn_penalty: -0.2`（深 run 值，有效）；
`enemy_neutral_capture` 若在中立争抢地图上有设计价值可保持 `-8`，或
为零以极简。这是
`configs/ppo/bootstrap_sweep/v28_production_reward_fixed.yaml` 的基础
（完整 33 阶段生产课程，现代意图平衡——见其头注释的平衡 vs 可训练性说明）。

强化的教训：“忠实复现”必须逐键对照原版验证，不能从“同一经济 + 阵容”
假设。相差三项加性奖励的配置是不同实验——并耗费了两周代码回归考古。

## ✅ 引擎常数混淆类 — 现已通过 `env.engine_overrides` 关闭

两周复现线程的根因不是某一个配置：而是 **平衡住在 `constants.py`
（`UNIT_DATA`、`STARTING_GOLD`、`*_INCOME`）——完全在配置面之外。**
任何 YAML 编辑或 `apply_overrides` 调用都够不着；它跨 commit 静默漂移
（`a596c15` Warrior/Barbarian/gold，`f4dc50e` Knight 防御 5→7，`6f64745`
HQ 收入 150→100），且不记入任何 run 产物。每次历史比较都被一个只能通过
`git show <sha>:constants.py` 恢复的不可见变量混淆。

现已在结构上关闭：

1. **`env.engine_overrides`** — 稀疏、可选的 YAML 覆盖
   （`starting_gold`、`*_income`、`unit_data: {CODE: {field: val}}`）。
   `GameState` 将其深度合并到模块常数之上，成为 `self.unit_data` /
   `self.income_rates` / `self.starting_gold`；单位与收入读这些解析后的表，
   永不读全局，因此覆盖不会泄漏或半应用（模块常数保持原样；未知
   code/field 大声失败）。缺省 ⇒ 与之前字节相同。
2. **自动记录** — `config.json` 现在记录 `engine_overrides`、解析后的
   `effective_engine_economy`、`effective_balance_profile_hash`，以及
   覆盖 *完整* `UNIT_DATA` 的逐字 `engine_constants_hash`（捕获 5 键投影
   漏掉的字段漂移）。
3. **忠实复现现为纯配置。** `v26_faithful_deep_reward_on_head.yaml`
   以 `engine_overrides` 块携带字节忠实的 `6eb0566` `[W,M,C,A,K]` 属性块
   + 经济——无需 `git checkout constants.py` 钉死，无需 notebook 手术，
   在现代 HEAD 上运行。

教训：**任何影响结果的东西必须活在配置面上，并快照进 `config.json`。**
`enabled_units`、`reward_config`，以及现在的引擎经济/属性都已关闭。
此类剩余需警惕的成员：地图内容（经 `map_sha256` 关闭）、课程结构
（`curriculum_hash`）、库/代码漂移（`git.commit` + `libraries`）。若将来
添加影响结果的旋钮，同一变更中进入 dataclass 与 `config.json` meta 块——
不要放在模块常数里。

## ✅ 课程交接 + 跳过学习 — 两个耦合的课程 bug，均已修复

奖励与经济类关闭后，v28（完整 33 阶段生产配置：经 `engine_overrides` 的
现代意图平衡、字节忠实 6eb0566 奖励、阵容 `[W,M,C,A,K]`）仍卡在
`beginner_random_15`。课程 runner 本身又浮现两个机制 bug——都不是配置问题，
而是 *runner 如何在阶段间移动策略*。均已修复（默认保留旧行为）。

### Bug 1 — 阶段内漂移传播到下一阶段

课程循环经 `model.set_env(...)` 把 **内存中的阶段末** 模型带到下一阶段。
PPO 在阶段内首次过阈值后会从获胜吸引子 *漂移*（已记录的 draw-with-shaping
策略漂移）；到阶段晋级（patience-2）或预算耗尽时，内存策略常常是漂移后的
后峰值版本，而非峰值本身。与此同时评估回调 *确实* 保存了
`<stage>/best_model.zip`，但阶段之间 **从未重新加载**。

v29（深经济 + 奖励修复 + `max_turns=100` + 现代代码，所有混淆受控）
以漂移后的 post-`random_10` 策略进入 `random_15`，与 v28 一样卡住。v30
（单阶段 `random_15`，经 `set_parameters` 从 v29 的 *峰值* `random_10`
checkpoint 热启动）约 50k 步通过 `random_15`。同一代码、同一阶段、同一
对手——唯一差异是进入的是哪个 `random_10` 策略。结论性证据：漂移交接
是 bug，不是阶段本身。

**修复：** `CurriculumConfig.restore_best_checkpoint_between_stages`
（默认 `True`）。阶段晋级后，runner 把 `<stage>/best_model.zip` 重载进
内存模型（`set_parameters(..., exact_match=True)`），再进下一阶段。
向前传递峰值，不是漂移。也改善最终阶段：`final_model.zip` 变成末阶段
最佳，而不是漂移的运行末策略。

### Bug 2 — 强交接导致阶段“跳过”自身学习

交接修复必要但不充分。v28 运行 `20260522_163958`（交接修复已上线 +
现代平衡 + 奖励修复，均经 `config.json` 验证）仍卡在
`beginner_random_15`。CSV 揭示机制：

| stage | timesteps | WR | note |
|--|--|--|--|
| `beginner_balanced_random` | end | promoted | 最佳交给下一阶段 |
| **`beginner_random_10`** | **@250,008**（首次评估，进入阶段约 8 步） | **1.0** | 带入策略轻易赢 random_10 |
| `beginner_random_10` | 300,000 | 0.01 | PPO 更新使策略漂移 |
| `beginner_random_10` | 350,000 / 400,000 | 0.925 / 0.84 | 恢复 → 晋级 |
| `beginner_random_15` | 首次评估 | 0.91 | 继承 *@250,008 快照*（阶段内历史最佳） |
| `beginner_random_15` | 下次评估 | 0.0 → 3M 步混乱 | 塌缩 |

`random_10` 的 `best_model.zip` 是 *@250,008* 快照——random_10 刚开始、
尚无任何 random_10 特定学习的时刻。因此进入 `random_15` 的交接实际上是
`balanced_random` 的最佳策略，约 0 的 random_10 精炼。强到能靠迁移赢
random_10 的策略，未必强到对付更难的 `random_15` 对手，且对 random_15
奖励信号的 PPO 更新立刻使其失稳。

**当带入策略已经很强时，阶段可以“跳过”自身学习。** 晋级门控（patience=2）
防不住——它只要求持续能力，强交接可以立刻产出而无任何阶段特定训练。

**修复：** `CurriculumStage.min_timesteps_before_promotion: int = 0`
（默认 0；旧行为）。当 `> 0` 时，`PromotionCallback` 忽略评估结果——
并拒绝晋级——直到 `model.num_timesteps >= min_timesteps_before_promotion`。
连胜计数重置，窗口前评估全部丢弃，因此晋级只能建立在门控后评估上。
在 `v31_production_minsteps_gate.yaml` 的噪声随机 `*_random_N` 阶段上
设为 `500_000`（v28 的继任；v28 保持不动作为激发门控的 bug 历史记录）。

### 教训

1. **交接 ≠ 进展。** 只有每个阶段在交接前 *真正训练过*，传递峰值策略才
   有帮助。晋级门控量的是持续能力，不是学习量——二者不同，课程正确性
   依赖两者。
2. **检查 `best_model.zip` 的 *内容*，不只是存在。** 交接修复看似有效
   （下一阶段以 91% 起步——看起来很棒）。它只在更难阶段的持续训练下失败，
   该对手未充分训练的策略撑不住。不要把早期评估 WR 迁移当作稳健学习
   的证据。
3. **强带入是双刃剑。** 出色的交接使 *当前* 阶段首次评估就轻易通过，
   从而短路 *下一阶段* 的学习。`min_timesteps_before_promotion` 门控使
   “阶段特定学习量”成为一等、可配置的课程属性——与阈值和 patience 并列。
4. **每个隔离变量一个 v 号。** v28（仅交接，无门控）与 v31（交接 + 门控）
   保留为独立 sweep 配置，使实验叙事可读：每个 v 号对应一组 run 记录与
   相对前驱的一个变量变更。

### ⚠️ 对“跳过学习”诊断的更正 — 门控弊大于利

上文“Bug 2”小节保留为 *我们测试的假设*。v31
（在 `beginner_random_{10,15,20}` 上 `min_timesteps_before_promotion: 500_000`）
于 2026-05-23 运行验证，**比 v28 更早卡在一个阶段——就在
`beginner_random_10` 本身。** 跳过学习前提是错的。

**数据（运行 `20260523_042220`，`beginner_random_10`）：**

| timesteps | WR | note |
|--|--|--|
| 250,008 | **1.00** | 门控前（回调丢弃） |
| 300,000 | 0.01 | 门控前（丢弃） |
| 350,000 | **0.925** | 门控前（v28 会晋级） |
| 400,000 | **0.8375** | 门控前（v28 会晋级） |
| 450,000 | 0.0375 | 门控前；策略开始漂移 |
| 500,000 | 0.5875 | 门控打开；策略已退化 |
| → 1.75M | 0.0 – 0.5，从未连续两次 ≥ 0.75 | 门控后混乱 |

在 v28 的自然节奏（无门控）下，`random_10` 在 `@350k / @400k` 对
（0.925 + 0.8375）上晋级。v31 把该对当门控前丢弃，并 **在策略峰值之后
继续训练**，经 draw-with-shaping 吸引子 **退化** 了工作策略——文档一直
警告的同一机制，但发生在 `random_10` *内部* 而非交接处。策略早早达峰，
额外训练抹掉了它。

**与 v30（有效诊断）的调和：** v30 从 **v29 的** `random_10` 最佳热启动，
该最佳处于累积 ~600k env-steps（v29 更长的探测前缀）。v28 的 `random_10`
最佳在累积 ~250k。“撑住 `random_15`”与“在 `random_15` 上塌缩”的差异是
**课程上的总累积训练**，不是阶段特定的 `random_10` 训练。跳过学习诊断
把门控对准了错误的轴。

**也揭示了：一个实现缺陷，留作记录。** `PromotionCallback.min_timesteps`
与 `model.num_timesteps` 比较，而后者是累积的（因 `reset_num_timesteps=False`）。
因此 `random_10` 上的 500k 值只强制了约 250k 阶段特定训练，而非意图的
500k。把它改成阶段相对不会有帮助（事实上会更糟——经验信号是 *更少*
峰值后训练更好，不是更多）。

**更新后的教训（取代上文第 3–4 点）：**

3. **在有漂移吸引子的阶段上，PPO 的自然晋级节奏优于强制额外训练。**
   一旦策略在 `*_random_N` 阶段跨过能力阈值，继续 PPO 更新往往侵蚀
   致胜行为而非改进。不要人为拉长这些阶段。
4. **所需训练量轴是 *累积* 的，不是每阶段的。** v30 通过 `random_15`
   不是因为有更多 `random_10` 训练，而是因为进入 `random_15` 的策略
   在课程上有更多总经验。若后续阶段需要更稳健的进入策略，杠杆是
   *更早* 的阶段或单独的 BC 热启动——不是强迫紧邻前一阶段越过峰值过训。
5. **`min_timesteps_before_promotion` 保留在代码中作为 opt-in 功能，
   默认 0，任何生产配置都不设置。** 对非随机阶段（过训不冒漂移吸引子
   风险）可能有用——但 `*_random_N` 阶段不应使用。

**当前生产目标（`v32_drop_gate_higher_eval.yaml`）：** v28 无门控，加上
长期推迟的评估噪声杠杆，应用于 `beginner_random_15`
（`n_eval_episodes: 80 → 160`，每阶段覆盖）。WR 估计的 σ 减半，使
有能力但噪声大的 random_15 策略能维持 patience-2 连胜。v28 与 v31
均保留为历史记录（分别为“无门控”与“有门控”实验）。

## 课程调参 sweep（v15–v23）：9 个变体教会我们什么

原始 6 阶段布局交付后，一次长 sweep（`configs/ppo/bootstrap_sweep/v15…v23`）
试图在更长课程上把智能体推过 `beginner_random_*` 阶段——该课程加入
`balanced_random` 垫脚石、`consolidate` 阶段，以及 intermediate / skirmish /
corner_points 地图尾部。**自 v17 起每个 run 都卡在 `beginner_random_15`。**
v19 是高水位：通过 6 阶段，卡在 random_15，峰值 WR 0.74。v20、v21、v22
全部回归。下文教训与上文冷启动教训同样昂贵——再动课程前先读。

### TL;DR（sweep 版）

1. **v19 是最佳配置。每个“简化”变更都回归了。** v20（更低熵）、v21
   （分步熵 consolidate）、v22（缩小单位阵容）各自去掉了智能体隐式依赖
   的东西，通过的阶段都 *少于* v19。仔细的平衡是承重的；不要假设简化免费。
2. **熵对 *泛化* 是承重的，不只是探索。** 把 `beginner_balanced_random`
   起始熵 0.07 → 0.05（v20）导致 random_10 灾难性回归（一次评估 90% → 0%，
   全平）。高熵产生的是对对手类别变更稳健的策略，不只是“噪声”。
3. **阶段边界的熵 *台阶* 不是 consolidate 冲击原因。** v21 把 v19 的单个
   0.05→0.003 consolidate 拆成两个更小台阶（≈无边界跳变），策略跌得 *更狠*
   （86% → 8.75%）。干净证伪了边界台阶假设。
4. **缩小单位阵容与对手强度混淆。** v22（`enabled_units: [W,K,A,M]`）使
   *最易* 阶段 `starter_random` 变得不可学。去掉 Cleric/Sorcerer/Rogue/
   Barbarian 阻止 RandomBot 把约 25% 建造浪费在随机用不上的单位上，把
   “随机”对手变成强得多的对手。早期课程的容易部分来自对手用弱单位
   自我削弱的伪影。
5. **对随机对手的 `patience` 必须低。** patience=4 要求对噪声 RandomBot
   连续 4 次评估 ≥ 阈值——实际上要求技能 *和* 运气。v17/v18 把 random_N
   阶段降到 patience=2；这修好了 random_10（50k 步通过，而 v16 卡满
   1.5M 预算）。它没修好 random_15（策略在那里从未守住门槛）。
6. **降低门控 ≠ 修复策略，但回答不同问题。** v23 把 random_15/20 晋级
   0.70 → 0.60（v19 明确守住过的水平），纯粹是为了了解 post-random_15
   课程是否 *根本可达*，还是卡住是真正的能力天花板。它明确是最后一个
   课程配置实验。

### draw-with-shaping 均衡（random_15 卡住机制）

跨 v17/v18/v19/v21，random_15 卡住有一个一致签名：策略达到获胜阵容
（Warrior+Knight，有时 +Mage），然后在约数十万步上 **从其上漂移**
进入 max-turns 平局吸引子，并在阶段预算内永不恢复。

机制：对 *静态随机* 对手，阶段 *内部* 没有课程梯度。一旦 PPO 找到
获胜策略，若它游荡，没有东西把它拉回，因为价值函数正确估计在当前权重下
“拖到 max_turns”比“冒险尝试获胜”有更高的方差调整回报。`turn_penalty = -0.5`
（v16 加入）把平局从 ≈+45 期望重定价到 ≈−40，*部分* 对抗这一点——但策略
仍会漂到那里，因为其 *替代*（承诺获胜）在它还不是合格赢家时得分更差。
惩罚改变了价值，没有改变行为。

### 决定性诊断：漂移 vs 平台

本 sweep 发现的最有用判别器：

| 信号 | random_15 卡住（我们看到的） | 容量受限（会是什么） |
|--------|-------------------------------|-------------------------------|
| `explained_variance` | ~0.85–0.95 | 低，~0.3–0.5 |
| `value_loss` | 低，稳定 | 高，可能上升 |
| `approx_kl` | ~0.005–0.01（几乎不更新） | 更高（抖动） |
| WR 轨迹 | **从** 获胜策略 **漂移** | **平台** 于次优 |

观察到的签名是“价值函数很好拟合回报，策略几乎不更新，但策略在 *游荡*”。
这是 **优化 / 吸引子** 问题，不是表示容量问题。更大网络会拟合同样回报，
得出同样“平局最好”的结论。这就是我们在 sweep 期间 *没有* 跳到架构变更
的原因——数据不支持容量受限。（v23 后课程调参耗尽时，判别对照是：
单独在 random_15 上训练新策略，无课程，3M 步。若通过，random_15 在此容量
可解，课程失败是干扰/遗忘；若不能，是真正天花板，网络必须变大。）

### GPU 非确定性放大分歧

v19 与 v21 在 `beginner_random_10` 之前共享相同配置（同一 seed）。v19 的
r10 晋级评估打到 100%；v21 打到 90%。约 50k 训练步 + 约 24 次 PPO 更新上的
CUDA atomic-add 非确定性，足以把本应相同的 run 送进不同盆地。比较 run 时，
把晋级评估上的 ±10% 当噪声而非信号——且不要过度解读单次 run。这是已知的
深度 RL 可复现性限制，不是配置 bug。

### 热启动不可共享

我们给 `TrainingConfig` / `run_curriculum` 加了休眠的 `warm_start_path`
（在阶段 1 前经 `set_parameters` 加载策略+优化器）。它能工作，但指向
*特定先前 run* checkpoint 的配置无法从干净检出复现——别人跑不了。把
热启动保持为 opt-in 基础设施；不要构建 *依赖* 它的 sweep 变体。这就是
v23 从“把 post-consolidate 策略热启动进 random_15”转向自包含门控放宽的
原因。

### Knight 强化：脚本 bot 看不见，RL 看得见

平衡工作的一个相关发现：把 Knight 防御 5→7 产生了 *字节相同* 的 bot
锦标赛结果（脚本 bot 用静态启发式优先级，从不感知属性变化），但回放
分析中 Knight 存活率可测 +3.6pt，且 RL 智能体强化后 *确实* 造更多 Knight
（梯度发现耐久）。**`balance_analysis`（bot 锦标赛）无法验证 RL 相关的
属性变更。** 用回放级指标或 RL 训练 delta，而不是 bot 胜负，来评估
单位属性调参。

**更新（`rng_seed` 接入后）：** 上文“字节相同”框架 *部分* 是确定性回放
伪影，不只是静态优先级 bot 的函数。`games_per_side=1` 且无 rng 时，
整场锦标赛是 12 局唯一游戏 × 8 副本，因此任何不翻转确定性决策分支的
属性变更都产生字面相同字节。在随机模式下 bot 锦标赛 *输出*（胜率、
占领计数）现在有真实统计内容——但静态优先级论点仍成立：不改变任何
排序键的属性变更不会移动脚本 bot 行为，无论收集多少独立样本。新贡献是
回放级指标（金币份额、建造计数、存活率）现在在每局层面有统计意义，
可用于属性调参信号。完整平衡分析回顾见
[`balance_analysis_lessons_learned.md`](balance_analysis_lessons_learned.md)。

### 不值得再追的方向（sweep 版）

- **熵日程变体。** 两个干净负结果（v20、v21）。问题不是熵形状。更低熵
  降低泛化；更小熵台阶不软化 consolidate 冲击。
- **单位阵容缩减作为“简化”。** 它改变对手强度（v22）。若必须测试单位复杂度，
  需要 *非对称* 阵容（仅限制智能体），这需要 env-factory 代码变更，不是
  YAML 开关。
- **v23 之后更多 `patience` / 阈值排列。** random_N 上 patience 已是 2；
  v23 是最后一个有意义的门控动作。v23 后课程配置搜索空间耗尽。
- **为运气重跑。** 与冷启动教训相同：撑约 1M 步的卡住不会靠延长预算解开。
  v17 的 random_15 跑满 3M 从未恢复。

## 未来工作

- **根据 v23 + 单阶段对照决定网络变更。** v23 是终端课程实验。若卡住
  （或通过 random_15 但下游阶段以同样漂移签名撞墙），先加宽 MLP
  `net_arch [256,256] → [512,512]`（最便宜有意义的容量提升，约 1.3M 参数，
  约 1.5–2× 墙钟），再 `features_dim` + CNN 宽度，再 unit-attention 块。
  并行跑单阶段 random_15-only 对照，在提交前区分容量受限与干扰/遗忘。
- **随机阶段的对手多样性（选项 C）。** 已诊断的 draw 吸引子机制是
  “静态对手 → 无阶段内梯度 → 漂移”。每 episode *混合* RandomBot
  （例如 max_actions 从 {10,15,20} 采样）会给出抗塌缩的多模态梯度。
  需要扩展 `MixedBot._build_inner` 以支持带 kwargs 的 `random`/
  `balanced_random` 子 bot（当前仅支持 simple/medium/advanced）。中等工作量；
  若 v23 + 更大网络打不开 random_15，是最有原则的剩余杠杆。
- **在 `grid` 和 `units` 通道上的 CNN 特征提取器** 可能加速收敛，尤其
  移到更大地图时。中等工作量（约 80 LOC）。*（注：`SpatialFeatureExtractor`
  随后已交付——本项大体完成；开放部分是其上的 unit-attention。）*
- **经小型自定义特征提取器从 MaskablePPO 的观测 dict 中去掉 `action_mask`。**
  它与 MaskablePPO 的 masking 流水线冗余，目前消耗网络输入维度约 70%。
  注意：AZ 与 Feudal RL 流水线 *确实* 使用 obs-mask，全局移除会破坏——
  必须是每策略特征提取器，不是环境变更。
- **行为克隆热身** 现已构建（`reinforcetactics/rl/imitation.py` +
  `ppo_bootstrap.ipynb` 第 3c 节），并在 beginner 课程上验证（v33 用 BC
  通过 random_15）。验证期间浮现的失败模式见下文“BC 热启动：我们学到了什么”。
  开放后续：多尺寸地图 BC 的 pad_to_size 穿线，以及 BC 数据集配置与课程
  第一阶段地图解耦。
- **`CurriculumStage` 上的 `start_fresh` 标志**，可选在阶段边界重新初始化
  模型而不是总是复用权重——当换图对 starter 策略过陡时有用。

## BC 热启动：我们学到了什么

行为克隆（BC）原列在未来工作；我们在 v33 周期构建它以打破 random_15 墙，
然后在单地图 skirmish 探测上精炼，再面对第二堵墙（BC → AdvancedBot 直接，
750k 步 0% WR）。验证工作浮现了若干失败模式——从“只需克隆 bot 动作”的
直觉看并不明显，且若诊断未内建会复发。

### 失败模式 A：确定性 bot 每 N 个 episode 产生 1 条唯一轨迹

**症状**：BC 数据集某场景有 60 个演示，但每场景 `avg_turns` 回来是
*精确整数*（18.0、21.0、14.0）。60 个 episode 是同一局游戏的 60 份
字节相同回放。对比有随机对手的场景（random、balanced_random），
`avg_turns` 是分数（21.9、10.6）——那些产生了 60 局真正不同的游戏。

**原因**：`SimpleBot` / `MediumBot` / `AdvancedBot` / `MasterBot` 在游戏状态上
完全确定。它们的 sort / max / best-tracking 位点按数据结构迭代顺序解平局
（Python 稳定排序、平局时最左 `max()`）。同一起始状态的两局在每一步
产生相同决策。`_make_bot` 给它们种子 `rng`，但它们不消费它。

**诊断**：每场景 `ScenarioStats` 表（本分支新增，从 notebook 第 3d 节打印）——
W/L/D + avg_turns 列通过精确整数 avg_turns 签名一眼揭示重复游戏场景。

**修复：** 每个 `DemonstrationScenario` 上 opt-in `stochastic_tiebreak: true`。
bot 收到每 episode 的 rng，并在确定性比较前对每个 sort / best-tracking
位点的输入做 `_maybe_shuffle()`。评分逻辑不变——bot 仍在其最高评分选项中
挑选——但平局随机解决，因此 N 个 episode 给出约 N 条唯一轨迹。

**对 BC 为何重要**：重复密集的数据集让监督策略 *背下* 少数对局脚本。
动作类型准确率看起来很好（首次运行 81%）但反映的是模式匹配，不是泛化。
有 stochastic-tiebreak 多样性后，动作类型准确率降到 76%——那是代表性
分布上的 *真实* 天花板。

### 失败模式 B：确定性平局解法伪影看起来像结构性地图偏差

第一次 skirmish BC 构建显示 `advanced_vs_advanced` 对玩家 1 是 **0 胜 /
60 负**。我们诊断为“skirmish 地图偏袒玩家 2”，并翻转
`demonstrator_player: 2` 从获胜侧录制。

下一构建启用 stochastic tiebreak 后，同一对局变成玩家 2 的 **20 胜 /
40 负**——即 **玩家 1 约 67% 胜率**。原 0/60 不是结构地图偏差；是一个
固定的平局解序列碰巧确定性地惩罚玩家 1 的移动顺序。微小扰动就整体
翻转对局。

**教训**：不要从确定性 bot-vs-确定性 bot 结果推断“地图 X 偏袒 Y 侧”。
确定性平局是未建模的对抗参数，改变它可以反转结论。

### 失败模式 C：`make_warm_started_model` 单源路径静默忽略 `stochastic_tiebreak`

BC 基础设施初次接线时，`stochastic_tiebreak` 活在 `DemonstrationScenario` 上，
但 **不** 在 `make_warm_started_model` 的单源 kwargs 上。调用
`make_warm_started_model(env, demonstrator='advanced', opponent='advanced',
n_episodes=50)` 且不传 `scenarios=` 时，静默产生 50 局字节相同游戏，
无论标志如何——正是该标志要修的失败，且无法 opt-in。notebook 用
`scenarios=` 所以没事，但任何临时调用者都会掉进重复陷阱。

**修复：** 把 `stochastic_tiebreak` 穿到每个 BC 入口。处处默认 `False`
保留向后兼容，但标志必须从每个调用者可达。

### 失败模式 D：MixedBot 的内部 bot 曾是确定性的

`MixedBot(easy=medium, hard=advanced)` 每 episode 重采样 easy-vs-hard
（`self.use_hard = self._rng.random() < p_hard`），但
`MixedBot._build_inner` 最初构建所选内部 bot 时不转发 `rng`。因此即便
`stochastic_tiebreak=True`，每个“Medium episode”与其他“Medium episode”
打法相同——总共约 2 条唯一轨迹（每个内部选择一条），不是 N。PPO 课程的
`skirmish_mixed_medium_advanced` 桥梁阶段也受影响（MixedBot 的每一“侧”
都是确定性的）。

**修复：** `_build_inner` 现在接受并转发 `rng`。仅因在我们“修了”别处
确定性 bot 问题后，每场景统计仍显示 MixedBot 场景上相同的 `avg_turns`
才被发现。

### 失败模式 E：动作循环超时静默膨胀“平局”计数

`_play_episode` 的外层步预算上限（`max_turns * 4 + 50`）是防止 bot 在
回合内动作循环中卡住的防御。触发时 `game_state.game_over` 仍为 False 且
`winner is None`——`EpisodeOutcome.is_draw` 正确将其当作平局。但这把
“对局在 `max_turns` 上限合法结束无胜者”（对局属性）与“bot 卡在动作循环”
（bot bug）混为一谈。每场景平局列膨胀，用户分不清是哪一种。

**修复：** 当步预算上限在 `end_game` 运行前触发时，设
`end_reason = "step_budget_exhausted"`，并在 `ScenarioStats` 上单独增加
`step_budget_exhausted` 计数。格式化器的 `T` 列使超时与 W/L/D 并列可见，
重复游戏场景或 bot bug 立刻浮现。

### 失败模式 F：共享 rng 在切换 `stochastic_tiebreak` 时使随机 bot 轨迹失同步

当 `stochastic_tiebreak=True` 时，同一每 episode rng 同时驱动确定性 bot
的平局洗牌与随机 bot 的动作抽取（RandomBot/BalancedRandomBot/MixedBot 的
抛硬币）。在同一 seed 上切换标志会改变 RandomBot 的 `.choice()` 抽取，
因为 AdvancedBot 先前的 `_maybe_shuffle` 消费了 rng 状态。两种模式
不可复现比较。

**修复：** `_play_episode` 为确定性 bot 平局派生单独的
`tiebreak_rng = random.Random(seed ^ 0xC0FFEEBAD)`。随机 bot 流无论标志
如何不变。

### 失败模式 G：sanity-eval 环境构造遗漏生产 env kwargs → 测量伪影看起来像 BC 失败

这个几乎让我们误诊一整轮迭代。`ppo_bootstrap.ipynb` 新加的第 3e 节
（“BC sanity eval”）这样构建评估环境：

```python
sanity_env = make_maskable_env(
    map_file=first_stage.map_file,
    opponent=opp,
    max_turns=first_stage.resolve_max_turns(cfg.env),
    max_steps=first_stage.resolve_max_steps(cfg.env),
    enabled_units=cfg.env.enabled_units,
    action_space_type=cfg.env.action_space_type,
    seed=cfg.seed + 7777,
)
```

注意缺了什么：**`reward_config` 和 `max_actions_per_turn`**。不传时，
`make_maskable_env` → `StrategyGameEnv.__init__` 回退到环境 *内置默认*
（`gym_env.py:406-454`）：

| 旋钮 | YAML（skirmish_bc_selfplay） | 环境默认 | 比率 |
|---|---|---|---|
| `invalid_action` | -0.01 | **-10.0** | 惩罚 1000× 更重 |
| `draw` | -50 | **-200** | 惩罚 4× 更重 |
| `loss` | -50 | **-1000** | 惩罚 20× 更重 |
| `max_actions_per_turn` | 60 | **None**（禁用） | 安全网消失 |

前三项使奖励幅度不可解释。第四项造成结构性评估失败：没有
`max_actions_per_turn`，没有东西在 N 个智能体动作后强制 end_turn。BC 策略
在贪心解码下欠预测 end_turn，并产生每维合法但联合非法的动作元组
（智能体审计失败模式 4——每维 MaskablePPO masking 是过近似）。智能体在
这些非法动作上循环，用满 `max_steps=3000` 预算却从不推进一个游戏回合，
然后以 `max_steps_truncate` 截断（归类为平局）。

**运行 20260524_225835 观察到的症状**：
```
BC vs simple   WR= 0.0%   reward=-30169.0   W/L/D=0/0/30
```

算术核对：`3000 invalid_actions × -10 = -30,000` 加上默认平局终局 `-200`
加上小的 potential-shaping 偏差 ≈ `-30,200`，与观测 `-30,169` 在 shaping
噪声内匹配。0/0/30 结果是每个 episode 在非法动作上循环直到 `max_steps`，
不是“BC 打不过 SimpleBot”。

**我们差点交付的误诊**：输出的显然读法是“BC 从根本上坏了；把
`end_turn_weight` 从自动平衡提到 30 以强制更多 end_turn 预测。”那是
完全错误的修复——BC 策略 *确实* 欠预测 end_turn，但在生产环境的
`max_actions_per_turn=60` 安全网下，上限会在 60 次非法后强制 end_turn，
智能体会真正打游戏。在 sanity eval 中禁用安全网反转了诊断。

**修复：** 第 3e 节现在镜像第 6 节课程后 sanity eval 与 `run_curriculum`
训练中评估已正确做的——转发
`reward_config = first_stage.resolve_reward_config(cfg.env)`、
`max_actions_per_turn = cfg.env.max_actions_per_turn`、
`pad_to_size = cfg.env.pad_to_size`。还把 `avg_length`、`avg_turns`、
`end_reasons` 加进打印输出，使 never-end-turn 失败模式内联可见，而不是
埋在奖励幅度里。

**一般教训**：任何在 `run_curriculum` 之外的“临时”环境构造（sanity eval、
回放视频、手写调试探针）必须转发生产环境使用的 *相同* kwargs，不只是
明显的（map / opponent / max_turns）。`reward_config` 容易忘，因为它不改变
*行为*，只改变 *测量*——但环境内置默认在多数键上相对 YAML 偏差 10–1000×，
因此未转发环境的任何奖励数字都不可解释。`max_actions_per_turn` 是危险的
遗漏，因为它 *确实* 以伪装成另一种失败模式的方式改变行为。

为保证测量一致性必须转发的 kwargs：

```python
make_maskable_env(
    map_file=stage.map_file,
    opponent=opp,
    max_steps=stage.resolve_max_steps(cfg.env),
    max_turns=stage.resolve_max_turns(cfg.env),
    reward_config=stage.resolve_reward_config(cfg.env),  # essential
    enabled_units=cfg.env.enabled_units,
    action_space_type=cfg.env.action_space_type,
    max_actions_per_turn=cfg.env.max_actions_per_turn,    # essential
    pad_to_size=cfg.env.pad_to_size,
    opponent_kwargs=stage.opponent_kwargs,                # if applicable
    seed=cfg.seed + <fresh offset>,
)
```

### 失败模式 H：end_turn_weight 加重的是 loss，不是 argmax 先验

`behavior_clone` 中的类别不平衡自动重平衡（默认
`end_turn_weight = n_non_end / n_end ≈ 10`）最初用于对抗 non-end_turn 与
end_turn 演示约 10:1 的不平衡。v33 笔记把 BC 的“never-end-turn 吸引子”
描述为不平衡后果，自动重平衡意在中和。Skirmish 运行 20260525_015401
测试 *显式* 把权重提到 30（3× 自动平衡值）是否会把 BC 策略推出吸引子。

**没有。** 同一地图、同一 seed、同一场景，仅改 `end_turn_weight=30.0`。
对 SimpleBot 的 sanity-eval 结果与自动平衡运行 **字节相同**：

```
                end_turn=auto (~10×)    end_turn_weight=30.0
BC vs simple    +796.6 / 50 turns       +796.5 / 50 turns
                W/L/D 0/0/30            W/L/D 0/0/30
                end=max_steps_truncate  end=max_steps_truncate
```

但同一 60 epochs 上 BC *训练* 指标大幅改善：

```
                Loss        action_type_acc   full_action_acc
auto-balance    5.0 → 2.73  0.60 → 0.78       0.08 → 0.21
weight=30.0     3.0 → 1.21  0.57 → 0.83       0.09 → 0.27
```

更低 loss，每个轴上更高准确率。监督策略在 `end_turn_weight=30` 下
**客观上训练得更好**。它只是在对被动对手的贪心解码下玩得没有任何不同。

**差距为何**：loss 权重增加了 `end_turn` 为正确标签的样本的梯度贡献，
因此策略在 *面对 end_turn 是演示中正确答案的状态* 时更准确预测 end_turn。
它 **不会** 在没有特定演示动作强烈正确的状态上移动 argmax 先验。
sanity-eval 时，BC 策略遇到演示者会做 move/attack/capture 的游戏状态
（因为脚本 bot 有侵略性）；那些高 logit 的 non-end_turn 动作上 argmax
仍胜出，智能体从不自愿结束回合。

不对称是结构性的：**对样本加重 ≠ 在无关状态上移动 argmax 先验**。类别
不平衡论证假设策略必须“学会 end_turn 是可能动作”；但策略已经知道——
它只是在多数状态把 end_turn 排在最可能的 non-end_turn 动作之下，仅缩放
权重不会在演示者做有产出动作的状态上翻转该排序。

可能真正移动 argmax 的方向（未测试，按侵入性排序）：

1. **高得多的权重（100、500、1000）。** 预期收益递减——loss 最终饱和，
   对 non-end_turn 样本的梯度消失，但推理时相对 logit 排序仍可能偏向
   演示最多的 non-end_turn 动作。快速可试（超参 sweep），低风险回退。
2. **非对称 / 基于 margin 的 loss。** 对错误 end_turn 预测的惩罚重于
   错误 non-end_turn 预测，或加 margin 项，在 end_turn 正确时把 end_turn
   的 logit 至少推高 δ 超过次佳 non-end_turn。`behavior_clone` 中更大
   代码变更。
3. **不同推理规则。** 评估时，若 `max(non_end_turn_logit) - end_turn_logit < threshold`
   则选 end_turn——即“没有高置信有产出动作，就结束回合”。这完全绕过
   BC 训练问题，但是事后行为 hack，不是模型修复。
4. **`flat_discrete` 动作空间。** End_turn 成为 N 个等权动作 token 之一；
   每动作 masking 而非每维 masking；交叉熵在平坦分布上良定义。可能是
   最干净的模型级修复，但需要扩展 `imitation.py` 以记录 flat_discrete
   演示。

**教训**：不要仅从监督指标断定超参“没用”——也不要仅从监督指标断定它
“有用”。训练曲线视图（loss 下降、准确率上升）可以在指标与对局策略
分叉时隐藏未变的 argmax 行为。`evaluate_bc_against_bot_ladder` sanity
eval 是抓住这一点的诊断——没有它，我们会高兴地交付 `end_turn_weight=30`，
并在下一课程 run 的 PPO 评估第 8 步发现同样的 0% WR。

**本代码库未来 BC 迭代的具体顺序**：先 sanity eval（便宜，约 1 分钟），
再训练指标（加载 JSON），再课程 run（昂贵）。若超参调整后对 Simple 的
sanity-eval WR 不变，在课程 run 前中止——额外 PPO 算力修不好 BC 没修好的。

### 诊断纪律：在 PPO 之前打印每场景统计

上述六个失败模式中的三个（A、B、E）被 notebook 第 3d 节的
`format_scenario_stats_table` 打印抓住，而它存在 *只因为我们构建了它*。
错误演示侧、12% 重复游戏标签、或多数“平局”实际是 bot 卡住超时的 BC
checkpoint，都会无错训练并产生表面正常的 checkpoint。诊断列
（`W/L/D/T` 加 `avg_turns`）是我们在多小时 PPO 运行前抓住这些的最便宜信号。

**经验法则**：任何全确定性 bot 场景上精确整数 `avg_turns` 意味着 N 份
同一局游戏。`T` 列中的动作循环超时意味着 bot bug，不是地图属性。
同 bot 对局（`X vs X`）上演示者 WR 显著低于 50% 意味着你从失败视角录制。

### BC 训练指标实际告诉你什么

每 epoch BC 统计（`bc_training_stats.json` + `bc_training_curves.png`）
有我们现在理解的特定形状：

- **`loss`** 干净下降。总是。若不下降，数据集 / 模型配置在 BC 特定问题
  之前就坏了。
- **`action_type_acc`** 前 3–4 个 epoch 急剧上升，然后在多样化数据上
  **平台在约 70–80%**。更多 epoch 对该指标帮助不大。它是数据集动作分布上
  动作类型分类器的天花板，不是欠训练信号。
- **`full_action_acc`** 全程缓慢上升。(from, to) 坐标预测比类型分类
  收敛更久。严格匹配指标，因此绝对数字低（epoch 8 约 14%）——*不要读成坏*；
  即便近最优策略也可能选与演示者不同但有效的目标。

**对 `BC_EPOCHS` 的含义**：停止用 action_type_acc 调参——它在多样化数据上
很快封顶。8 epochs 够用；16 主要帮助 full_action_acc 且收益递减。

### BC 的价值头学不到什么

`behavior_clone` 更新策略网络（特征提取器 + 共享 MLP + 动作头）但
**不** 更新价值头。BC 有动作的监督标签但没有状态价值标签；我们可以从
终局结果估计价值，但会噪声且会偏置 PPO 的 bootstrapping。价值头从零开始，
PPO 在前几次更新中拟合它。

**后果**：期望前 1–2 次 PPO 更新有 `value_loss` 尖峰，随 critic 追上而衰减。
健康。诊断是当尖峰 *不* 衰减——那信号奖励尺度问题或价值头容量天花板。

### 单地图探测模式（每次都这样做）

在新地图 / 新 BC 混合上做任何多小时课程 run 之前：

1. 把 `total_timesteps` 和阶段 `max_timesteps` 降到总计约 1M。
   在我们的超参下约 60 次 PPO 更新、约 20 个评估点。
2. 在前 3–5 次评估内确认 `WR > 0` 且 `std > 0`。
3. 确认奖励不在下降（黄旗），且 avg_turns 不是单调爬向 `max_turns`
   （v15–v23 sweep 的 stall 吸引子签名）。
4. 仅在探测显示上升信号后，把预算调回生产规模。

第一次 skirmish 运行是 10M 预算 run，在我们停止前 750k 步保持 WR=0.0%、
std=0.0。探测模式在约 15 分钟墙钟内抓住该签名，而不是数小时；保存的
诊断产物（`scenario_stats.txt`、`bc_training_curves.png`、
`bc_demo_outcomes.png`）在 Drive 上，能扛 Colab 断连，并跨迭代可比。

## 阵容多样性：mono-Warrior 吸引子（v34–v40）

BC 流水线通过 `beginner_random_15`（v33）后，下一目标是教智能体
**用阵容打球**——使用 Mage/Cleric/Knight、占领 HQ、行使 PR #383 新增的
状态效果通道。v34 改为冷启动，浮现不同问题：PPO 可以几乎通过整门课程
而从不学习阵容。v34–v40 追修复；下文是那七个配置的代价。

### v34 发现：通过 14 阶段，零战略学到

`v34_aggressive_combat.yaml` 以文档建议的重缩放幅度重新启用战斗 shaping
奖励（`damage_scale=0.002`，`kill=0.2`，`turn_penalty=-0.5`，`draw=-10`）。
运行 `20260526_145412` 冷启动通过 **14 阶段**——经 `beginner_advanced`
进入 intermediate——然后以 60% WR 卡在 `intermediate_random_20`。头条数字
不错。阵容数据不行：

- 在 **每个** 通过阶段上，`units_built["W"]` 占总建造的 **95–100%**。
  M/C/A/K/R/S/B 是个位数或零。
- 每个阶段 `captures_by_type.hq = 0`。策略仅靠歼灭获胜，从不 HQ 突袭。
- 状态效果观测通道（麻痹/加速/增益）零信号，因为策略从不建造产生它们的单位。
- 卡住阶段上 `avg_turns` 钉在 60 回合上限：intermediate 的 7×7 地图
  max_turns=60（比 6×6 beginner 的 75 更短时钟）以平局耗尽（卡住时
  80/80 max_turns_draw）。

策略学到了有效但琐碎的战略——“刷出 HP/$ + Atk/$ 最好的最便宜单位，
在时钟跑完前歼灭对手”——在小地图、非侵略对手上有效，几何或对手强度
一变立刻失效。

### 为什么默认平衡是单单位局部最优

v34 之前，默认 Warrior 属性使其在每金币上帕累托主导：cost=200（最便宜）、
HP=15（并列最高）、atk=10（并列最高）、def=6（任意单位最高）。PPO 立刻
找到并永不探索。性价比表状态很重要：

```
  W: cost 200  HP/$ 0.075  Atk/$ 0.050  Def 6   <- top of every axis
  K: cost 350  HP/$ 0.051  Atk/$ 0.023  Def 5
  M: cost 300  HP/$ 0.033  Atk/$ 0.033  Def 4
  A: cost 250  HP/$ 0.060  Atk/$ 0.020  Def 1
```

一旦单个单位在最便宜档赢下每个性价比轴，就没有分布内策略梯度指向多样性。
熵奖励产生随机 *探索*，不是随机 *剥削*——策略偶尔会采样 Mage，Mage 相对
同样金币造更多 Warrior 表现更差，梯度推回 W。

### 我们试过的四根杠杆（v35–v37）

| Config | 杠杆 | 首次卡住 | 通过阶段上的 Mono-W |
|---|---|---|---|
| v35 | Warrior nerf atk 10→8，def 6→4；加入 intermediate r10/r15；intermediate max_turns 60→75 | `beginner_random_10`（阵容在多样化） | 漂移进行中 |
| v36 | v35 + `beginner_random_10` 预算 1.5M → 3M（恢复时间） | `beginner_random_10`（通过 7 阶段） | 100%（5479/5479 = r10 上 W） |
| v37a | 回退 nerf + r15 与 r20 间 MixedBot 桥梁阶段 | `beginner_random_15`（CUDA 非确定卡住） | 100% |
| v37b | 回退 nerf + 更高晋级阈值（r10:0.75→0.90，r15:0.70→0.85，r20:0.70→0.75） | `intermediate_random_20`，在 **每阶段 100% WR 通过 15 阶段后** | 每个通过阶段 100% |

**v37b 是决定性负结果。** 以 100% WR 通过 15 阶段的策略——比 v34 深 run 更好——
却 0% 阵容多样性，确认 mono-W 吸引子 **不是** 课程问题。任何中期课程压力
（MixedBot 桥梁）、阈值收紧（强制更多阶段特定训练）、软属性 nerf 都逃不出。
默认平衡是原因。

### v38（结构 nerf）与 v39（仅成本 nerf）撞上新墙

`v38_structural_warrior_nerf.yaml`：atk 10→7，def 6→3，HP 15→13。
这使 Knight 在每个战斗轴上严格优于 Warrior。运行 `20260527_200511`
以相对 0.90 阈值 **51% 峰值 WR** 卡在 `starter_random`。诊断：最小尺度上
战斗数学坏了。Warrior atk=7 面对 def=4 单位，每次击杀需 3–4 回合，
starter 的 max_turns=20 在任一方解决战斗前耗尽——每 80 episode 评估
50–70 平局。nerf 过于激进，*且* 测试地图太小，无法支撑它要教的战略权衡。

`v39_cost_only_nerf.yaml`：Warrior 属性不变，cost 200→300。动机是手术式——
只改价格（Warrior 最后一个优势轴），保持战斗数学完整。运行
`20260528_005831` 以 **35% 峰值 WR——比 v38 更差** 卡在 `starter_random`。
诊断不同且更根本：starter 有 $250 起始金与 max_turns=20。W cost=300 时，
策略字面 **无法在第 1 回合造 Warrior**，之后约每 2 回合收入造 1 单位。
无论策略是否在“赢”早期，对局都以平局结束。

### 诊断：平衡实验与 starter 不兼容

两次卡住同一根因：**starter 太紧，测不了平衡**。Starter 在课程中的角色是
便宜地教导航——仅此而已。默认平衡下 PPO 可以速通 starter（v34 各阶段
50–100k 通过），因此 starter 的经济结构从未重要。一旦改变代价曲线或战斗数学，
starter 的硬限制（20 回合，$250 金）在策略能表达课程要引出的战略转变之前
就与新机制碰撞。

失败形状是一般的：**在某一平衡设置下有效的课程阶段，在另一设置下可能
不可行，且失败看起来像策略 bug**（低 WR、大量平局），实际是环境时钟 bug。
区分它们的诊断：看卡住时的 *金币花费 / 单位建造* 比率——若显示策略几乎
把一切花在单位上但游戏仍平局拖完，时钟是问题；若金币累积未花，策略
从未学会建造。v38/v39 都显示前者。

### v40 的解决

`v40_skip_starter.yaml` 完全去掉 `starter_random` / `starter_simple` /
`starter_medium`。课程在 `beginner_balanced_random`（6×6 地图，max_turns=75，
$400 起始金）上打开，保留 v39 的 W cost=300 nerf，其余继承 v39 不变。
运行 `20260528_020718` 在 200k env-steps 以 100% WR（W/L/D=80/0/0）
通过阶段 1——在早期探索下探后的首次评估上——代价曲线假设在这里可测，
在 starter 上则不能。剩余阶段随 run 进展仍 TBD；诊断问题是阵容是否在
`beginner_random_{10,15,20}` 尤其是 `beginner_mixed_r15_simple` 上多样化。

### 可推广教训

1. **默认平衡阵容是策略的先验。** 若默认单位表有明确性价比赢家，本环境上
   每次 PPO run 都收敛到 mono-该单位阵容。课程不反击——patience 门控与阶段
   阈值奖励获胜，不是 *用阵容* 获胜。若要多样性，代价曲线必须打破每轴垄断。
   （三个单位赢不同轴是 v39 设计：Knight HP/$、Mage Atk/$、Archer 便宜档 HP/$。
   这是否真打破吸引子是 v40 测试。）

2. **属性 nerf 与成本 nerf 失败方式不同。** 属性 nerf（v38）破坏战斗 *数学*，
   在紧时钟地图上传播为“策略根本赢不了”。成本 nerf（v39）保留战斗数学，
   但在低金币地图上破坏 *经济*。成本 nerf 可以更细粒度回退（300 → 275 → 250），
   且不与战斗动态交互；当目标是阵容 shaping 而非每单位重平衡时优先用它们。

3. **战斗 shaping 奖励（v34）*不是* 多样性杠杆。** `damage_scale + kill`
   奖励结束战斗。每金币赢得战斗的单位是最便宜的合格战斗者——即未 shaping
   策略已在收敛的同一单位。战斗 shaping 解锁了 v34 的深度（14 阶段 vs 先前约 7），
   但没改变策略 *造什么*；只是让策略更激进地那样做。

4. **收紧晋级阈值不强制阵容。** v37b 把 r10 提到 0.90、r15 到 0.85，希望
   门槛强制更多阶段特定学习。策略通过 **在同一对手上把 mono-Warrior 做得更好**
   达到更高门槛，而不是多样化。Patience 与阈值量 WR；WR 无需阵容多样性
   即可测；因此更紧门控不施压阵容多样性。

5. **MixedBot 桥梁对对手过渡有用，对阵容过渡无用。** `beginner_mixed_r15_simple`
   阶段（50% max_actions=15 的 RandomBot，50% SimpleBot）设计用 SimpleBot 的
   占领贪婪节奏惩罚 mono 歼灭玩法。v37a 干净通过它 *仍 mono-W*——SimpleBot 对
   争抢建筑的压力不足以使阵容比更多 Warrior 更有价值。桥梁仍有对手难度
   台阶价值；它只是不独立强制多样性。

6. **阵容摘要可视化是最便宜的抓手。** 加入 `plot_curriculum_composition_summary`
   （每阶段水平堆叠条：建造单位 + HQ 占领 + 技能使用）在 v37b 上一眼浮现
   “每个通过阶段 100% mono-W”。同样数据一直在 `eval_log.csv` 中
   （`units_built` 是每阶段 JSON 列）但没人解析。**构建总结每阶段 *战略*
   而不只是结果的诊断**——并在每次 run 后查看，尤其是“成功”的 run。

7. **`units_built` 形状决定新特征是否被行使。** PR #383 为状态效果 debuff
   （paralyze、haste、defence_buff、attack_buff）加了 4 个新观测通道。
   在 mono-Warrior 策略上那些通道在观测流中永久为零——Mage/Sorcerer/Cleric
   从不建造，因此技能从不释放。新观测特征只有在 *策略* 最终产生它们编码的
   数据时才有回报。若代价曲线激励忽略那些单位，通道是惰性的。跟踪这种
   耦合：策略从不行使的“改进观测空间”是死重量。

### v40+ 的开放问题

- **W cost=300 是否真在 beginner 上打破吸引子？** v39 测不了——它死在
  starter 上，未到达成本变更有空间起作用的任何阶段。v40 的 beginner
  阶梯是第一次真实测试。观察 `beginner_random_{10,15,20}` 的 units_built
  分布。
- **若 v40 仍以 mono-W 通过 beginner/intermediate 阶梯**，则代价曲线几何
  也不是绑定杠杆，下一步是 (a) 显式多样性奖励（每 episode 每第 N 种
  不同单位类型小正奖励）或 (b) 从使用阵容的演示者 BC 热启动。两者都比
  平衡调参工作量大。
- **容量尚未测试。** 每个 v34–v40 run 用 `net_arch=[256, 256]`。若多样性
  *需要* 更宽隐层来表示多单位阵容规划，平衡/课程杠杆都修不了。在其他
  方面到达 `intermediate_random_20` 墙的配置上跑 `[512, 512]` 对照，
  可区分“平衡瓶颈”与“容量瓶颈”。
- **starter 阶梯当前未训练。** v40 的策略冷进入 `beginner_balanced_random`。
  若未来迭代需要 starter 做导航预训练（例如 beginner 更大地图拖慢冷启动
  收敛），更干净的模式可能是 *单独* 的仅 starter 前课程 run 交付 checkpoint，
  而不是把 starter 拼回为平衡实验调好的配置。

## `beginner_random_15` 上的 kill-farm 平局平台（v41，运行 `20260528_135412`）

`v41_r10_stability.yaml` 对 `beginner_random_10` 应用了文档化的三重修复
（门控 0.75→0.65，预算 3M→5M，熵地板 0.03→0.01）。**对所述目标有效**——
r10 以 100% / 93.75% 通过——但课程在一阶段后卡在 **`beginner_random_15`
（33 阶段中的第 3）**，相对 0.70 门控的 best WR 0.65，耗尽约 3M 步
（`run_status: curriculum_stalled`）。这是迄今仪器最全的 r15 卡住
（五张诊断图），比 v15–v32 sweep 更精确地钉住机制。

### 这是已知的 draw-with-shaping 漂移——已确认，不是新 bug

`eval_curves` 与“漂移 vs 平台”表完全匹配：**explained_variance ≈ 0.85，
value_loss 低且稳定，approx_kl ≈ 0.005。** 价值头拟合回报；策略每步几乎
不更新却游荡。因此这是 **优化/吸引子** 问题，不是容量——且 **也不是**
v27a/v27c 奖励回归：v41 已交付 `win_speed_bonus: 0` 与
`enemy_owned_capture: 0`。原因在奖励形状的别处。

### 新细节：这是战斗 farm，占领行为死在 random_10

早期 sweep 缺乏的三张图：

- **阵容跨阶段剧烈漂移；占领早死。** `balanced_random`：W55%，占领 HQ:4 /
  B:21（seizing 是计划的一部分）。`random_10`：**W81%，HQ:0 / B:0——以 100%
  纯歼灭通过。** `random_15`：重新规格到 **约 70% Knight + 约 20% Barbarian**，
  每评估击杀 10,324（所有阶段最高）但仅 HQ:1 / B:5。占领取胜行为在
  **balanced_random → random_10 过渡** 蒸发，不是在 r15。
- **r15 上的动作混合是 kill-farm。** 约 50% move，约 22% attack，约 10%
  create，约 10% end_turn，约 9% heal，**seize 仅约 2–3%**——且 seize 在
  r10 已约 1–2%。智能体移动并交换攻击；几乎从不推进占领。
- **奖励分解显示 farm 为何稳定。** 每 80-ep 评估求和：`action`（战斗）
  +2000–5000，`shaping_delta` +1000–2000，`terminal` 慢性 −500 到 −3500
  （平局惩罚）。卡住的 75 回合平局因此净 **≈ +19/episode**：密集战斗+potential
  farm 超过平局惩罚。获胜结束 farm 且很少达到（HQ:1/评估），因此梯度指向
  战斗并拖延，不是结束。W/L/D ≈ 3/1/76，回合钉在 75 回合上限。

这是环境奖励 docstring 自己的警告（“从不结束游戏的 kill-farm 局部最优”）
以及 v34–v40 小节 **教训 #3**（“战斗 shaping 不是多样性杠杆——它奖励结束
战斗，因此策略只是对最便宜战斗者更激进”）。v34 战斗 shaping 通过在易阶段
歼灭解锁深度；在 r15 上更活跃的对手（max_actions 10→15）无法在 75 回合内
歼灭，同一侵略性变成平局。

### 三重修复副作用：r10 通过时比 v40 *更少* 多样性

值得标记：v40 的 r10 *卡住* 但 **28% Warrior**（多样）；v41 的 r10
**以 81% Warrior、纯歼灭通过**。更低熵地板（0.01）+ 额外预算让策略承诺
mono-W 歼灭并通过——用晋级换掉 v40 曾有的阵容。通过 `*_random_N` 阶段与
*用阵容* 通过仍是不同事（教训 #4）。

### v42：移除战斗 farm（单变量测试）

`v42_remove_combat_farm.yaml` 将 `damage_scale` 与 `kill` 置零（相对 v41 的
*唯一* delta，经配置 diff 验证）。没有逐步战斗 farm 时，平局明确净负
（`turn_penalty −0.5 × ~73 回合` + `draw −10`，无东西抵消），因此占领/获胜
是唯一正回报路径。本 run 之外的支持证据：深配置（实验 A / v26）在无战斗
shaping 下通过 *超过* r15，配置内注释记录置零战斗的 run 到达 `random_20`
（过 r15）——战斗 shaping 仅对最终 r20 推进重要。若 v42 *仍* 以 seize ≈ 2%
卡在 r15，瓶颈是占领 **探索**（稀疏、承诺的多步 seize 序列），不是奖励比率——
此时奖励微调耗尽，升级是已在账上的更高置信杠杆：**从使用占领的演示者 BC
热启动**（v33 以此通过 r15）与 **未测试的 `net_arch [256,256]→[512,512]`
容量对照**。

### 教训

1. **有利可图的平局是奖励 bug，不是策略 bug。** 若逐步 shaping（战斗 + potential）
   能超过平局终局，PPO 发现 farm-and-stall 均衡，draw-with-shaping 吸引子成为
   理性休止点，不是瞬态。检查奖励分解：若平局上 `action + shaping_delta`
   超过 `|terminal|`，平局 *付钱*。
2. **“通过”隐藏学到了哪种胜利条件。** r10 以 100% 通过、零 HQ/建筑占领——
   纯歼灭。课程然后把纯歼灭策略交给歼灭来不及完成的阶段。读通过阶段上的
   `captures_by_type`，不只是 WR。
3. **三重修复搬迁卡住；它不移除机制。** 门控/预算/熵让 r10 过了门槛（通过
   承诺 mono-W 歼灭），相同漂移一阶段后重现。机制是奖励景观，它随策略
   沿课程下行。
4. **Seize 饥荒是贯穿线。** 跨 r10 与 r15 智能体 seize 约 2% 时间。beginner
   阶梯上每个“无法收官”的卡住都归结为“策略从未学会承诺的 seize 序列”。
   那把持久修复指向占领探索（BC，或更密/更早的占领课程），而不是对手/
   门控/熵调参。

## v42（运行 `20260528_212658`）：移除战斗 farm — 方向对，同一堵墙

`v42_remove_combat_farm.yaml` 将战斗 shaping 置零（`damage_scale` 0.002→0，
`kill` 0.2→0）——上文 v42 条目预测的单变量测试。它 **再次卡在
`beginner_random_15`**，best WR **0.7125**（相对 v41 的 0.65——它 *曾* 越过
0.70 门控一次但无法维持 patience-2）。三个发现：

1. **它使早期阶梯过度稀疏。** 密集战斗奖励消失后，`random_10` 首次评估
   **塌到 0% / 约 1 动作每回合 / 奖励 −47.6**（纯平局惩罚——阶段切换的
   end-turn 塌缩，没有战斗梯度爬回），然后用 **约 2.9M 步** 的剧烈振荡
   才勉强通过（约 3.0M 的 0.65/0.75 对）——而 v41 在 **150k** 通过。v41 的
   战斗 shaping 策略是立刻迁移的歼灭机器；v42 的占领导向策略不迁移，
   也没有后备侵略。

2. **它把一个退化吸引子换成另一个：Cleric-spam。** r15 漂移到 **约 74% Cleric**
   （W21% / C74% / K5%），HQ:0 / B:0。机制是代价曲线：v39/v40 nerf 使 Warrior
   成本 300，因此 **Cleric（200）现在是最便宜单位**，移除战斗 shaping 移除了
   偏好战士而非便宜辅助单位的唯一理由 → **刷最便宜单位吸引子**（v34–v40 教训）
   以 *新* 的最便宜单位重现。Cleric 重军队无法可靠占领或歼灭 → 平局。

3. **漂移本身未动。** 同样健康但在漂移的 PPO 签名（explained_variance ~0.8，
   approx_kl 低，value_loss 稳定）。r15 在 3.9M 达峰 0.7125 然后 *真正*
   塌缩（0.46、0.60，→ 长时间 ~0）。占领行为从未活过阶段 1：
   `balanced_random` 达到 **HQ:11** 占领（相对 v41 的 HQ:4——移除 farm *确实*
   在易阶段多样化 + 占领），但 r10 与 r15 都是 **HQ:0**。

**结论：战斗奖励轴耗尽。** v41 *加入* 战斗 shaping → Knight kill-farm，
卡在 r15。v42 *移除* 它 → Cleric spam，卡在 r15。两个方向在同一阶段以
同一漂移撞墙。累积证据（v15→v42）现在横跨 **加入与移除** 奖励杠杆——
全部卡在 r15。**奖励 shaping 不是杠杆。** 这落在 v42 配置自己的决策树分支：
“以 seize ~2% 卡在 r15 → 奖励微调耗尽，升级到非奖励杠杆。”

### 可推广教训

**移除密集 shaping 项不会把行为重定向到稀疏目标——它只是搬迁最便宜单位
吸引子。** 希望是杀死战斗 farm 会把策略推向占领。结果它把策略推到 *新的*
最低摩擦行为（刷现在最便宜的单位 Cleric，并平局）。占领序列稀疏且承诺；
不是靠 *移除* 激励到达，只有靠 *添加* 体验它的路径（更密占领课程或 BC）。
推论：**代价曲线 nerf 改变“刷最便宜”吸引子落在哪个单位**——nerf Warrior
价格使 Cleric 最便宜，吸引子移到 Cleric。若保持 W=300 nerf，最便宜单位
身份（Cleric）现在本身是问题。

## v43a / v43b：对手多样性 ± 容量（测试非奖励杠杆）

奖励轴已耗尽，v43 把奖励保持在 **v41 的** 设置（战斗 shaping 开——*快的*
早期阶梯；v42 的战斗关奖励把 r10 过度稀疏到约 2.9M，会在到达 r15 墙前
成为并行 run 瓶颈），只变非奖励杠杆，作为并行 A/B：

- **`v43a_opponent_diversity.yaml`** = v41 + beginner `random_{10,15,20}`
  簇上的 **对手多样性**。每个静态 RandomBot 替换为每 episode
  `MixedBot(random@A, random@B)`（仅配置——MixedBot 已向
  `RandomBot(max_actions)` 转发 `easy_kwargs`/`hard_kwargs`）：
  r10→{10,15}，r15→{10,20}（括住它卡住的 15），r20→{15,20}。
  这是文档的 **“选项 C”** 抗漂移杠杆：*静态* 随机对手不给阶段内梯度，
  因此 PPO 从任何获胜策略漂移；每 episode 变化对手提供一个。`net_arch`
  不变 `[256,256]`。
- **`v43b_opponent_diversity_capacity.yaml`** = v43a + `net_arch`
  `[256,256]→[512,512]`（相对 v43a 的 *唯一* delta）。容量与对手多样性
  配对而非单独测试，因为“漂移 vs 平台”诊断说 r15 是吸引子问题，不是
  容量受限——因此单独容量是弱实验。更窄赌注：若多样多单位阵容需要更多
  宽度表示，更大网络可利用多样性提供的稳定性。

**读并行对：** v43a 通过 → 多样性单独修好漂移（不需容量，省约 1.5–2× 算力）；
v43b 通过但 v43a 不通过 → 容量在漂移修复上增加真实价值；都不通过 → 升级到
**BC 热启动**（唯一曾通过 r15 的杠杆，v33）。**Caveat：** v41 的奖励使卡住
平局边际净正（战斗+potential farm 约 +57/ep vs 约 −47 平局惩罚），因此对手
多样性修 *无阶段内梯度* 根因，但不修 *有利可图平局* 根因；若 v43a/b 仍在
r15 平局，后续是对手多样性 **+ v42 的战斗关奖励**（平局净负）。

### 结果（v43a `20260529_142749`，v43b `20260529_144521`）

干净、决定性的 A/B。

| Run | 杠杆 | 卡住于 | 通过阶段 | Best WR |
|---|---|---|---|---|
| **v43a** | 对手多样性，`[256,256]` | `beginner_random_15` | **3** | **0.8375** |
| **v43b** | 对手多样性 + `[512,512]` | `beginner_random_10` | **2** | 0.8375 |

1. **容量出局。** v43b 走得 *更少*——早整整一阶段卡住（r10 vs r15）。两者
   峰值都 0.8375，因此 `[512,512]` 不是无能；它 **以同样方式漂移，并卡在
   漂移抓住它的地方**，正是“非容量受限”诊断所预测。无收益，约 1.5–2× 算力，
   且此处少一阶段。别用它。（阶段差距部分是 run 间噪声，但信号——“容量
   无收益”——清晰。）

2. **对手多样性是整个 sweep 中最有效的单一杠杆。** v43a (a) **通过了现在
   *更难* 的混合 r10**——`MixedBot(random@10, random@15)`，比 v41 的静态 r10
   更难，也是 v42 几乎死掉的阶段——且 (b) 把 r15 推到 **0.8375，现代冷启动
   线最高 r15 WR**（v41 0.65，v42 0.71；只有旧代码/旧奖励深配置更好）。
   阶段内梯度假设得到验证：每 episode 变化对手使策略在远更高水平上保持能力。
   **保留它。**

3. **它仍未攻破 *维持*。** 尽管 0.84 天花板，v43a 卡住——策略在评估间振荡
   （峰值约 0.84，下探低于 0.70），从未连成 **两次连续 ≥0.70**。漂移被
   *减弱*（更高均值，能力更久）但未 *消除*。约 0.20 的评估间摆动对采样噪声
   太大（80-ep σ≈0.05），因此是真实残余漂移——且 W/L/D 列显示 **它在 *获胜*
   与 *平局* 间振荡，不是失败**（0.8375 评估是 67W/1L/12D；低评估约
   0W/1L/79D）。它游荡进有利可图的平局，正是 v43 caveat 标记的第二根因。

**结论 + 下一步（v44）。** 对手多样性杀死了 *无阶段内梯度* 根因；*有利可图
平局* 根因（v41 奖励使卡住平局净正）仍在。因此自然后续组合各自杀死不同
根因的两根杠杆：

> **v44 = v43a（对手多样性，`[256,256]`）+ 使平局无利可图。**

最干净的单加变量是 **HQ 收入削减**（`headquarters_income: 150 → 100`）：
它缩小策略可躺的保证基地收入，使卡住平局在经济上更差，同时提高争抢建筑/
塔的 *相对* 价值（推向占领）。作为相对 v43a 的单变量 delta 留下，以便归因。
（若交付不足，叠 v42 的战斗关奖励，或升级到 BC 热启动——仍是唯一曾通过
r15 的杠杆。）从 v38/v39 教训带前的 caveat：不要过度收紧经济，优先削减
HQ 收入而非建筑/塔收入（削减后者会 *抑制* 我们想要的占领）。

### 结果：v44 + v45（运行 `20260530_034840` = v44，`20260530_034656` = v45）

两者都基于 v43a 基线（对手多样性，`[256,256]`）；各为单变量 delta。
**都没有改进 v43a，且 v44 回归。**

| Run | 相对 v43a 的单一 delta | 卡住于 | 通过 | Best WR |
|---|---|---|---|---|
| v43a（基线） | — | `random_15` | 3 | **0.8375** |
| **v44** | `headquarters_income 150→100` | **`random_10`** | **2** | 0.65 |
| **v45** | r15 `ent_coef end 0.03→0.01` | `random_15` | 3 | 0.7375 |

**v44（HQ 收入削减）适得其反——v38/v39 经济过紧失败，正是上文 caveat 警告的。**
它早一阶段卡住（r10，从未到达 r15）。智能体的胜径是大规模歼灭，因此更瘦
经济 → 更小军队 → 无法对混合对手收官 r10。CSV 显示下探处真实 **失败**
（0W/18L/62D，11W/16L/53D），不只是平局——对称收入削减伤害依赖经济的智能体
策略 *多于* 与金币无关的随机对手玩法。“更少金 → 更多占领”的希望未实现；
更少收入只是使早期更弱。**HQ 收入削减出局。**

**v45（熵地板 0.01）是洗牌。** 它像 v43a 一样到达 r15，以同样方式卡住
（峰值 0.7375 vs v43a 的 0.8375——在 CUDA 噪声范围内，因此不可归因于变更）。
后期更硬承诺 **没有** 停止胜↔平振荡。与文档“更低熵降低探索”一致——
可能用承诺换天花板而未获得稳定性。

**收敛信号（v43a/b、v44、v45）。** 卡在哪一阶段（r10 vs r15）部分是噪声——
策略刚好在 0.70 门控处 *边际*。对手多样性确实抬高了天花板（0.84 可达），
但 **其上每个便宜配置杠杆现在都失败：容量（v43b，更差）、经济（v44，更差）、
熵（v45，洗牌）。** v43a 仍是高水位。这强烈表明奖励/经济/熵/容量微调不会
使该策略 *可靠* 收官胜利——缺失的是稳健、可重复的 **占领** 胜，而不是脆弱的
大规模歼灭，那些微调一直教不会。

**下一步：** v46（`unit_diff 0.3→0.0`，最后未测的便宜杠杆——停止为数量付钱）
排队以收尾便宜杠杆 sweep，但期望不高。指示的升级是 **从使用占领的演示者
BC 热启动**（保留对手多样性）——唯一曾通过 r15 的杠杆（v33），且能直接
教占领胜。

## ✅ 突破 — v49→v50：奖励景观才是根因；冷启动现可达 skirmish

这是 v15–v45 sweep 一直在绕的章节。便宜配置杠杆耗尽（熵、patience、容量、
对手多样性、经济）后，本分支构建的一组 **诊断** 钉住实际机制，**组合奖励
修复（v49）+ 决定性战斗引擎变更（v50）** 把现代冷启动线从“卡在
`beginner_random_15`”（自 v17 起每个配置）带到 **约 20 阶段，到达
`skirmish_random_20`**——从冷启动匹配历史深配置的前沿。

### 破解它的诊断

sweep 一直在猜策略 *为何* 卡住。三处添加使其可观测（评估日志 + TensorBoard
+ 逐步 info）：

- **`seize_available_rate`** — 占领动作合法的决策点比例。这分离“策略从未
  到达可占领格”（导航/探索）与“到达却拒绝”（奖励）。在
  `beginner_random_15` 卡住时即使 0% WR 仍坐在 **40–57%** → 智能体 *能*
  占领却 *不愿*。那排除了 BC/导航作为下一杠杆，直指奖励景观。
- **`max_legal_actions`** — 峰值合法动作集大小。`flat_discrete` 的
  `max_flat_actions` 上限护栏；后来抓住 skirmish 上真实的 512 溢出
  （见 v52）。
- **`best_checkpoint_timestep` / 阶段相对步数** — 向前交接的最佳 checkpoint
  实际在阶段多远（跳过学习交接的征兆）。

同时浮现 **潜在截断 bug**：`_build_flat_actions` 在 `max_flat_actions` 上限
*之前* 追加 `end_turn` 并头截断溢出——静默丢掉 `end_turn`（最后追加）和
`seize`（action_type 3，在 create/move/attack 之后构建）。修复为始终保留
两者。在 6×6 上潜在；**在 skirmish 上承重**（v50 撞上限）。

### v49（运行 `20260531_051101`）：组合奖励修复打破 r15 墙

从 v43a run 的决定性读法：0% WR 时策略以 78–80/80 局平局拖到 75 回合上限，
同时收集 **+28..+55 奖励**——*平局被正向奖励*。安全付费港湾。v49 是单轴
sweep 从未试过的组合修复（全部基于 v43a 的对手多样性基线）：

1. **`draw: −10 → −50`** — 移除正向安全港平局（== 失败，因此永不偏好失败
   而非平局）。
2. **`damage_taken_scale: −0.002`（新环境项）** — 对承受伤害收费，使战斗
   shaping 净零和；互相交易净 ~0，只有决定性战斗付钱。杀死拖到时钟的
   交易 farm，而不把战斗置零（v42 的战斗关使 r10 过度稀疏）。
3. **`unit_diff: 0.3 → 0.0`** — 停止按单位 *数量* 付钱（已确认的最便宜单位
   spam 补贴）。
4. **`hq_capture: 25 → 60`，`win_by_hq_capture: 50 → 80`** — HQ 原先付费
   *少于* 建筑（40）；使它成为最佳目标并偏好可迁移的胜。

结果：平局翻为 **负**（0%-WR 评估现 −20..−48），mono-Warrior spam 消失
（Warrior 份额 23–65%，不是 95–100%），且 **通过 `random_10`、`random_15`、
`mixed_r15_simple`** 并到达 `beginner_random_20`（5 阶段，best 0.7875）——
第一个越过 r15 墙的现代配置。胜是靠 **歼灭**（阶段 1 后 HQ 占领 0）；
负平局强制 *结束*，不是 *占领*。

### v50（运行 `20260531_165459`）：hp_scaled 决定性战斗 → 突破

`v50 = v49 + damage_model: hp_scaled`（引擎：出伤与反击随攻击者当前 HP
分数缩放——与 seize 一致，后者一直是 HP 基；经 `engine_overrides` 配置面，
记入 `config.json`）。

平坦伤害模型是 **消耗** 模型——1-HP 单位打得和满血一样硬，因此军队均匀
磨掉，对局在 *机制层面* 漂向 max-turn 平局。HP 缩放使战斗 **决定性**
（集火复合，战斗解决）。它本身也缩小 farm。

结果——现代最深 run，大幅领先：

- `random_10` **快 3× 通过**（750k vs v49 的约 2.3M）——决定性在行动。
- 通过 **整条 beginner 阶梯** 包括击败 Simple/Medium/**Advanced** bot，
  然后 **迁移到 intermediate（7×7）** 与 **skirmish（8×8）**，通过
  `skirmish_random_15` 并卡在 `skirmish_random_20`（约 20 阶段），
  Colab 在约 8M 步超时。

**hp_scaled 是保留项。** 它是 v49 奖励修复的引擎侧孪生：v49 移除安全平局，
v50 使智能体赢下它现在必须打的战斗。

### v51（运行 `20260601_031012`）：预算地板 + patience-2 — 以及方差炸弹

`v51 = v50 + 每阶段 3M 预算地板 + 统一 patience-2`。动机：v50 的
`intermediate_random_20` 预算 **1.5M/patience-3**——比 `beginner_random_20`
（3M/patience-2，同类漂移吸引子阶段）一半预算且更严门控——且仅在预算边缘
靠晚期恢复通过。地板是 **天花板** 提升（允许恢复），*不是* 适得其反的
`min_timesteps_before_promotion` 门控（那强制过训）；易阶段仍早晋级并忽略它。

**但 v51 卡在 `beginner_random_15`（3 阶段，0.6625）**——远差于 v50。
这 **不是修复的回归**，原因是整篇文档中最重要的方法论教训：

> **本课程上 run 间方差巨大：同一配置、同一 seed 产生 14 阶段（v50）vs
> 3 阶段（v51）。**

证明是方差不是变更：(a) `random_15` 在两者中有 *相同* 预算（3M）和 patience
（2）——修复没碰它；(b) v50 与 v51 的 **首次评估（@ step 8）字节相同**
（WR 0.5，reward 91.8589625）——同一 seed，同一权重初始化；(c) 它们在
`@ 50k` 分叉。一切都有种子——**对手 bot**（来自 `np_random` 的每 episode
`random.Random(bot_seed)`）、**权重初始化**（`MaskablePPO(seed=cfg.seed)` →
策略构建前 `set_random_seed`）、**评估 RNG**——因此 *唯一* 不受控变量是
**CUDA 浮点非确定性**（非结合 atomic add），`random_10/15` 漂移吸引子把它
放大成完全不同的轨迹。

**后果：**
1. **跨配置的单次 run 比较不可靠。** v49 的 5 阶段卡住、v50 的 20 阶段
   run、v51 的 3 阶段卡住是高方差过程的样本。结论需要 **每配置 2–3 个
   seed**。
2. 文档旧的“把晋级评估 ±10% 当噪声”严重低估——这里是卡住与突破之差。
3. 若需要精确复现，还要设 `torch.use_deterministic_algorithms(True)` +
   `CUBLAS_WORKSPACE_CONFIG` + 禁用 cuDNN autotune（更慢，复现 *一条*
   路径）。为 *比较*，做相反——变化 seed。
4. 一个残余全局 RNG 泄漏：**Rogue 闪避在 `mechanics.attack_unit` 中用
   `random.random()`**（不是 env/bot rng）。次要（很少造 Rogue）但对干净
   多种子工作值得关闭。

### v52a / v52b（排队）：skirmish 卡住是平局经济 + 截断，不是占领

v50 的 `skirmish_random_20` 卡住暴露两个 skirmish 特定（`max_turns=120`）
阻塞——且值得注意 **skirmish 上 `seize_avail` *很高*（75–82%）**，因此
*不是* 歼灭无法迁移的占领墙：

1. **负平局修复不缩放到更长时钟。** 在 skirmish 上逐步战斗/seize farm 随
   `max_turns` 与更大建筑数缩放，而 `draw:-50` 固定——因此 0/0/80 平局回到
   盈亏平衡/正向（+19..+54）。v49 的平局修复为 `max_turns=75` 校准。
2. **截断触发** — 合法动作超过 `max_flat_actions=512`（警告在 517/526/528；
   `max_legal` 钉在 512），丢掉合法 move/attack。诊断 + 截断修复抓住并
   控制了它，但上限对 8×8 确实太小。

两者都基于 v51（把预算/patience 修复带前）：
- **v52a** = `turn_penalty −0.5 → −1.0`。`turn_penalty` 是自然的 *max-turns
  缩放器*（每 `end_turn` 收费，因此卡住累积 `turn_penalty × max_turns`）：
  120 回合 skirmish 卡住现耗 −120（曾 −60），把期望平局回报明确移到负，
  而快速胜提前结束（+100..+220 奖励）保持正。隔离奖励修复。
- **v52b** = v52a + `max_flat_actions 512 → 1024`。加上截断修复。
- 读 A/B：v52a 通过 → 平局经济是阻塞；v52b 通过但 v52a 不通过 → 截断有贡献；
  都不 → 更深能力墙 → 结构 v53。
- 若 `−1.0` 交付不足的升级：`turn_penalty −1.5`（胜有充足余量）。

### 现已在配置面的可复用杠杆（默认惰性）

全部快照进 `config.json`，未设置时与旧版字节相同：
- `reward_config.damage_taken_scale` — 对称战斗（杀死交易 farm）。
- `engine_overrides.damage_model: flat|hp_scaled` — 决定性战斗。
- `engine_overrides.{tower,building,headquarters}_health` — 占领难度杠杆
  （例如 HQ@30 = 2 个 Warrior 回合 vs 4）。当占领成为绑定墙时的直接旋钮。

### 仍开放的（→ v53 结构）

整条弧线上，**胜靠歼灭；HQ 占领在第一个易阶段后保持约 0。** 奖励现在
*指向* 占领（hq_capture 60，win 80），平局不再付钱——但 **占领关卡** 在
机制上仍难：seize 伤害 = seizer 的 *当前* HP（开火下衰减），被防守的 HQ
需 3–4 个不间断回合占领，驻军单位 **物理阻挡** 格子（你不能踏入被占格）
并在其上 **基地治疗**，被杀的 seizer 让建筑每回合回复 50%。因此占领
只在战斗已赢后发生——即塌缩为歼灭，而歼灭不迁移到更大地图（歼灭来不及
收官）。

结构杠杆（当占领成为绑定墙时，可能在 v52 后的 skirmish+）：
**`headquarters_health` 降低**（使 HQ 成为 1–2 回合动作以便探索可达）和/或
**从使用占领的演示者 BC 热启动**（唯一曾教会占领的东西，v33）。两者现在
与最终奖励结束-靠占领、平局不再付钱的奖励组合。

### 教训（本章）

1. **在调杠杆前构建诊断。** `seize_available_rate` 把多年“是到不了还是
   不愿结束？”的猜测变成一个数字答案（不愿），把努力从 BC 重定向到奖励。
2. **有利可图的平局一直是根因。** 每个便宜杠杆（熵、patience、容量、
   对手多样性）失败，因为它们在奖励使正的吸引子 *周围* 轻推策略。把平局
   定价为负（v49）+ 决定性战斗（v50）移除吸引子，4× 课程深度随之而来。
3. **为某一 `max_turns` 校准的平局修复不迁移到更长时钟。** farm 随时钟
   缩放；惩罚也必须（`turn_penalty` 自然做这件事——在多 `max_turns` 课程上
   优先于平坦 `draw` 常数）。
4. **Run 间方差淹没多数配置 delta。** 同一 seed → 仅 CUDA 非确定性就 3 vs 14
   阶段。跨 **多个 seed** 比较配置，不是单次 run。这重新语境化 *整个*
   v15–v48 单 run sweep：一些“卡住”和“通过”是运气。
5. **预算是天花板，不是地板。** 提高 `max_timesteps` 让易卡阶段恢复，
   而不强制过训（不像 `min_timesteps` 门控）。把 random_N / 漂移吸引子
   阶段保持在 ≥3M。
6. **引擎平衡属于配置面。** `damage_model`、建筑 HP 与 `damage_taken_scale`
   关闭最后硬编码混淆——平衡变更现在是记录的配置 delta，不是 `constants.py`
   编辑。

## v52a 完整运行 + 动作空间 / 经济工作（skirmish_random_20 墙）

v52a 运行（`20260601_172412`，`turn_penalty −1.0`，`max_flat_actions 512`）
跑到 Colab 超时，给出决定性的 *负* 结果，重塑剩余工作：
**skirmish_random_20 是硬结构墙，且在 512 上限上是截断饱和的。**

### 完成的运行显示了什么

- **迄今最深前沿**：通过整条 beginner + intermediate 阶梯与 skirmish 至
  `skirmish_random_15`，然后卡在 `skirmish_random_20`。
- **不是计时卡住**：策略从约 5.85M 到约 8.05M 超时坐在 `skirmish_random_20`
  上——**约 2.2M 步**——从未维持 ≥70%。WR 无限在 0%↔37% 振荡。完整阶段
  预算都打不开，因此阻塞是结构的（占领/经济），不是预算。
- **截断饱和**：每条警告读 `max_flat_actions (512)`；卡住时需求 **持续
  513–744**，因此约 30–45% 的合法集（move/attack）在多数决策、每局游戏上
  被丢掉。这是迄今最干净的证明：**512 是 8×8 地图上真实的绑定约束**——
  也是 `max_flat_actions: 1024`（v52b/v53/v53b）的直接理由。
- **策略塌缩签名**：评估 @ 7.75M = `WR 0% / len 121 / turns 120 /
  seize_avail 0% / max_legal 20`——智能体造约 1 单位并拖平，几轮评估后又
  摆回 max_legal=512。剧烈的 mass↔nothing 摆动 = 晚期熵/漂移不稳定性
  （保持熵再尖刺杠杆存活）。
- **系统级漂移确认**：若干阶段记录 `restoring best checkpoint … peak @ 8
  stage steps`——该阶段最佳策略是 *迁移点*，训练从其上漂移
  （beginner_random_10 需要约 850k 步 100%↔2% 振荡；intermediate_random_15
  完全到 0% 约 800k 后恢复）。

### 动作空间膨胀：已诊断，不是猜测

审阅 `get_legal_actions`，膨胀是 **移动主导**，不是技能/攻击主导：移动
枚举为 **每个（单位，可达格）一个**，因此合法集大小缩放为
`units × 每单位足迹`。值得记录的更正：Mage/Sorcerer 的 `{"adjacent","range"}`
数字是距离 1 / 2 的 **伤害**，*不是* 12 格射程——远程攻击射程仅 ≤2
（Archer 2–3/4）。因此远程多目标是次要贡献；**军队规模 × 移动扇** 是
全部故事。744 合法 ≈ skirmish 上约 24 单位。

### 棋盘密度是单位上限的正确镜头

`每侧 20 单位` 对每图 **可行走** 格：

| map | walkable | 20 = 1 侧 | 两侧都 20 |
|-----|------|------|------|
| beginner 6×6 | 36 | 56% | 111%（不可能） |
| intermediate 7×7 | 43 | 47% | 93%（堵死） |
| skirmish 8×8 | 62 | 32%（约 ⅓） | 65% |
| corner_points 12×10 | 114 | 18% | 35% |

因此 **20 的上限在小地图上宽松到免费**（它们物理上装不下约 40 单位——
自我封顶约 15–18/侧），**只在真正的 skirmish 堵死时咬合**（卡住所在的
约 24 单位峰值）或 **在 corner_points 上强制精度**（20 是主动向下约束的
唯一地图，即便那里也只是 18% 密度——可玩）。测得的约 24 单位 skirmish
峰值因此是 *病理*，不是要为保留余量而保护的正常玩法。

### 本会话交付的内容（全部默认惰性 / 配置面）

- **合法动作正确性修复**（`get_legal_actions`）：对已麻痹敌人不再提供
  paralyze（匹配 heal/cure/buff 守卫）；源单位循环与远程攻击目标循环上的
  `health > 0` 守卫（今天经同步移除安全，否则脆弱）。
- **军队经济遥测**：每 episode `peak_own_units` / `mean_own_units` /
  `peak_gold_banked` / `mean_gold_banked`，浮现在评估结果、tensorboard
  （`eval/*`）与评估打印行（`army(pk/mn)=… gold(pk/mn)=…`）。分离
  “经济资助 mass”（高峰值军队 + 约 0 囤金）与“奖励资助 mass”——且本谱系
  奖励对单位 **什么都不付**（`create_unit 0`，`unit_diff 0`，伤害净零，
  `kill 0.2`），因此持续大军牵涉 **经济**（无上限每回合收入、无维护、
  免费建筑治疗），不是奖励。
- **每玩家单位上限**（`constants.MAX_UNITS_PER_PLAYER = 50`，覆盖
  `engine_overrides.max_units_per_player`）：在 **`create_unit` 与
  `get_legal_actions` 两者** 中强制，使上限出现在动作 mask 中（无
  提供-后-拒绝的 create）。同时约束动作空间膨胀与把所有金转为单位的经济。
- **v53b 配置** = v53 建筑 HP **+ 经济杠杆**：`headquarters_income 150 → 120`
  （修剪最大金水龙头而不碰相对单位价值）与 `max_units_per_player 20`
  （主动杠杆；代码默认保持 50 作为永不绑定护栏）。v53（经 `max_flat 1024`
  容纳军队）vs v53b（经经济缩小军队）是干净 A/B。

### 教训（本章）

1. **钉在上限的饱和 `max_legal` 是删失测量。** 评估 `max_legal_actions` 是
   `len(_current_actions)`，本身以 `max_flat` 封顶，因此钉在 512 并 *隐藏*
   真实需求——必须读截断 **警告**（原始计数，可达 744）才能看到真实大小。
   不要从（删失的）评估标量推断军队规模。
2. **动作空间膨胀是 `units × move-footprint`，由移动主导。** 削弱单位的
   *技能* 或 *攻击射程* 几乎碰不到它；只有军队规模（经济）或每单位移动
   枚举（动作表示）移动指针。
3. **密度，不是原始计数，确定单位上限大小。** 同一上限在 6×6 棋盘上免费，
   在 12×10 上绑定。相对 **每图可行走格** 定上限；约 ⅓ 棋盘单侧覆盖是
   堵死起点。
4. **当奖励已去补贴 mass 但智能体仍 mass 时，看经济，不看奖励。** 无上限
   收入 + 无维护 + 免费治疗使单位成为免费持有的工具品；策略把所有金转为
   身体，即便没有东西为身体付钱。修 *供给*（收入/维护/上限），不是奖励权重。
5. **从未维持的完整预算卡住是结构的，不是预算不足。** `skirmish_random_20`
   上 2.2M 步无持续晋级排除“需要更多步”——升级到结构杠杆（占领 HP / 经济），
   不是更大天花板。
6. **完整阶梯 run 是成本单位。** 到达 skirmish 消耗整次 Colab 会话，因此
   仅引擎变更（建筑 HP、收入、上限、伤害模型）可从近 skirmish checkpoint
   热启动友好，但 `max_flat` 变更会调整 `Discrete` 动作头大小，需要全新 run。

## 调参路线图 — 值得下一步拉的杠杆（及其优先级）

v52a skirmish_random_20 墙之后，开放旋钮分为标量 *调参*、结构 *重构* 与
*方法论*。按期望杠杆排序：

### 1. `gamma` / 有效视界 — 被低估的标量（近优先做这个）

`gamma` 按 **env-step**，不是按游戏回合。Episode 跑到 `max_steps=3000`
（skirmish ≈ 20 env-steps/回合 × 120 回合 ≈ 2400 步）。在 `gamma=0.99` 时
有效视界是 `1/(1−0.99)=100` env-steps ≈ **约 5 游戏回合**。因此在占领推进
约第 50 回合赚到的终局 `hq_capture (+60)` / `win (+80)` 奖励，在到达铺垫
它们的机动时已被折扣到 **近零**——这是 **“靠歼灭获胜、HQ 占领 ≈ 0、无法
在时钟内收官 skirmish”** 最干净的机制解释。密集 potential 项
（income/structure_control）携带局部信号，但大的 *终局* 占领激励几乎不传播。

- 杠杆：`ppo.gamma 0.99 → 0.995–0.997`（视界约 200–330 步 ≈ 10–17 回合），
  可选 `gae_lambda → ~0.97`。一行；可从近 skirmish checkpoint 热启动，
  效果显示快。
- Caveat：更高 gamma 提高价值函数方差 → 与漂移不稳定性交互（§ @ 7.75M 塌缩）。
  观察 `explained_variance`/`value_loss`。
- 把这排在起始熵 **之上**：它是占领失败的根因杠杆，不是稳定器。

### 2. 多种子 — 方法论，不是参数（信任 3–4 的前提）

Run 间方差（CUDA 非确定性）淹没多数配置 delta（同一 seed → 3 vs 14 阶段）。
在经济 / 熵 / HP / gamma 跨 **≥3 个 seed** 比较之前，任何单 run “这有帮助”
都可疑。不是旋钮——是使每个其他旋钮结果可信的东西。

### 3. 占领可达性包（使推进能够 *完成*）

占领是两部分关卡；两者都调，不只是 HP：
- **建筑 HP**（v53，配置面）：HQ@30 = 约 2 个 Warrior 回合 vs 4。
- **回复率**（尚未上表面——`mechanics` 中硬编码 50%/回合）：孤独 seizer 的
  伤害 = 其 *当前* HP（开火下衰减），因此 50%/回合回复往往超过单个 seizer——
  占领只在战斗已赢后落地。降低回复（≈25%/回合）或 **敌方占据格子时暂停
  回复** 可以说比 HP 更对症。需要结构 HP 得到的同样 `engine_overrides` 处理。
- **经济**（v53b，配置面）：`headquarters_income 150→120` + 单位上限
  把军队从堵死峰值缩下。

### 4. 起始熵再尖刺（稳定器，不是根修复）

7.75M 塌缩（`max_legal=20`，造约 1 单位，拖平）与系统级
`peak @ transfer-point` 漂移说明晚期不稳定性真实。进入新阶段时温和的
ent_coef 再尖刺可能阻止策略从迁移能力漂移——但它治 *症状*；排在 gamma
与占领包之下。

### 5. 动作表示重构（从源头杀死膨胀）

`max_flat 1024` 是对 `units × move-footprint` 膨胀的创可贴。持久修复是
改变移动如何表示——选单位再方向、每格移动头、或每单位 top-K 目的地剪枝——
永久移除截断混淆，并使精确多单位玩法 *可学*（策略能看到所有选项）。是
重构，不是标量，但是板上最高杠杆的非调参变更。

### 荣誉提名（更低优先级）

- **`win_speed_bonus` vs `turn_penalty`**：速度压力目前全在
  `turn_penalty −1.0`（密集，每回合）。`win_speed_bonus` 仅终局且 *不能*
  被 farm；它可能是更干净的“快速赢”信号，且不惩罚合法的长占领。便宜 A/B。
- **驻军 / seize 机制**：防守者物理阻挡格子 *并* 在其上基地治疗，强制
  先杀后占领（→ 歼灭）。允许相邻时推进占领，或多单位部分 seize，在机制层
  攻击关卡——侵入式；仅当 HP+回复不够时。
- **墙上的对手强度**：skirmish_random_20 对 `random@20`；现在不是绑定问题
  （截断/经济/视界才是）——先放着。

### 建议顺序

`gamma`/视界 → 多种子 harness →（经济 + 建筑 HP + 回复）包 → 熵再尖刺 →
动作表示重构。
