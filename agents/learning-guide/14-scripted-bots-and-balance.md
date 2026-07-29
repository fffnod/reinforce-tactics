> 返回：[指南目录](README.md) · [上一章](13-evaluation-elo-tournament.md) · [下一章](15-llm-bots.md) · [索引](../AGENTS.md)

# 第 14 章：规则 Bot 与平衡分析

本章把 **脚本启发式对手**（scripted bots）讲清楚：它们是课程学习的「梯子」、评估的「标尺」，也是平衡分析最容易踩坑的地方。读完后你应能：

1. 说出 Bot 难度阶梯上每一层大致在干什么；
2. 背出 `take_turn` 合同；
3. 解释为何「确定性 Bot + 多局重复」会骗你对样本量的直觉；
4. 跑一次可选的短锦标赛冒烟命令。

更细的源码说明见 [`../source-analysis/game-bots.md`](../source-analysis/game-bots.md)、[`../source-analysis/tournament-system.md`](../source-analysis/tournament-system.md)；作者原始笔记见 [`../../docs/zh/balance_analysis_lessons_learned.md`](../../docs/zh/balance_analysis_lessons_learned.md)。

---

## 1. 为什么脚本 Bot 对 RL 很重要

| 用途 | 说明 |
|------|------|
| **课程对手** | Bootstrap 阶段从 Noop / Random 一路升到 Simple → Medium → …，让策略「先学会赢弱对手再学打强的」 |
| **评估标尺** | 「对 Simple 胜率 70%」比「平均奖励 12.3」更好懂、更可比 |
| **可复现基线** | 规则固定、无网络权重，换机器重跑行为可对齐（配合 `rng` 时则是可复现的随机） |
| **奖励 sanity** | 若连 `NoopBot` 都打不赢，问题多半在策略/奖励/掩码，而不是「对手太强」 |
| **平衡与设计** | 单位成本、技能、地图改动后，用 Bot 锦标赛看强弱是否塌缩成单一文化 |

神经网络策略在训练早期很弱且不稳定；脚本 Bot 提供 **可控难度曲线** 和 **不依赖 checkpoint 的评测锚点**。

---

## 2. Bot 难度阶梯

实现主要在：

| 模块 | 路径 |
|------|------|
| 抽象合同与 mixin | `reinforcetactics/game/bot_base.py` |
| 规则 Bot 实现 | `reinforcetactics/game/bot.py` |
| 锦标赛发现与工厂 | `reinforcetactics/tournament/bots.py`、`runner.py` |
| CLI | `scripts/tournament.py` |

### 2.1 一览表

| 类 | 角色（白话） |
|----|----------------|
| **NoopBot** | 直接结束回合；零压力。课程 stage-0 / 奖励自检 |
| **RandomBot** | 在合法动作上均匀随机，最多 `max_actions` 次后 `end_turn` |
| **BalancedRandomBot** | 可选造 1 个兵 + 每单位最多 1 个随机动作；压力随兵力缩放，介于 Noop 与「狂乱 Random」之间 |
| **SimpleBot** | 固定购买优先级 + 贪心接近 / 攻击 / 占领 |
| **MediumBot** | 集火、低血撤退治疗、占领去重、简单克制购买 |
| **AdvancedBot** | 地图分析、阶段机、编制目标、技能特化（冲锋、侧袭等） |
| **MasterBot** | 威胁图、更聪明的撤退 / 集火 / 占领优先级 |
| **MixedBot** | 每局掷硬币选 easy / hard 内层 Bot；课程「桥接阶段」专用 |

继承关系（概念）：

```text
BaseBot + BotUnitMixin
  ├─ NoopBot
  ├─ RandomBot
  │    └─ BalancedRandomBot
  ├─ SimpleBot
  ├─ MediumBot
  │    └─ AdvancedBot
  │         └─ MasterBot
  └─ MixedBot  （内部再构造 simple/medium/…）
```

### 2.2 各层策略直觉

**NoopBot**
什么都不做就 `end_turn()`。若智能体胜率仍接近 0，先查奖励与动作掩码。

**RandomBot**
从「除 end_turn 外的合法动作」里 `choice`，执行最多约 20 次。噪声大，适合早期探索压力，不适合当「公平强敌」。

**BalancedRandomBot**
先有机会造一个单位，再按单位分桶各做一次随机动作。比 Noop 有威胁，又不会像 Random 那样在一回合内乱点几十下。

**SimpleBot**
`purchase_units → move_and_act_units → end_turn`。购买按优先级表（Warrior 最高）；行动贪心打残血、靠近、占领。需要 **Warrior 占比上限**，否则会「只造勇士」的单一文化（见第 5 节）。

**MediumBot**
在 Simple 之上加：集火可击杀目标、低血撤到治疗建筑、占领目标不重复抢、购买看克制关系。

**AdvancedBot**
分析地图（HQ、山地、森林），用阶段机（扩张 / 交战 / 征服等）+ 编制目标 + 单位技能（骑士冲锋、盗贼侧袭、术士加速等）。

**MasterBot**
每回合建威胁图（敌方下一步能打到的格），撤退与集火更「怕死」也更敢集火。

**MixedBot**
构造时指定 `easy` / `hard` / `p_hard`（例如 50% Simple + 50% Medium）。环境每次 `reset` 会重建对手，于是不同 episode 难度不同——适合 **课程桥接**（刚打过 easy，预习 hard）。

---

## 3. `take_turn` 合同

所有 Bot（规则、LLM、ModelBot、AlphaZeroBot）都实现同一接口，因此可塞进 GUI、Gym 对手位或锦标赛。

```text
take_turn() 必须：
  1. 在有限步骤内返回（禁止死循环）
  2. 代表 self.bot_player 执行 0..N 个领域动作
     （create_unit / move / attack / seize / 技能…）
  3. 调用 game_state.end_turn()
     （若已经 game_over 可直接返回）
```

`BaseBot` 只保证持有：

- `self.game_state` — 共享的 `GameState`
- `self.bot_player` — 自己的玩家编号

可选遥测：`_record("knight_charge")` 等，锦标赛 / 平衡分析可从回放 `game_info` 读能力触发次数。

**和 RL env 步的区别（复习）**：

| 概念 | 含义 |
|------|------|
| Env 的 `step` | 智能体一个 **微动作** |
| Bot 的 `take_turn` | 一整 **游戏回合**（内部可含很多领域动作，最后 `end_turn`） |

对手在 env 里走完一整回合时，智能体那边可能已经过去很多 `step`（见第 02 / 04 章）。

---

## 4. 在课程与评估中的用法

### 4.1 课程（Bootstrap）

`configs/ppo/bootstrap.yaml` 的 `curriculum.stages` 里，阶段字段类似：

```yaml
- name: starter_simple
  opponent: simple
  # map、胜率门槛、max_timesteps …
```

常见对手名：`noop`、`random`、`balanced_random`、`simple`、`medium`、`advanced`、`mixed`。

桥接示例（概念）：

```yaml
- name: beginner_mixed_simple_medium
  opponent: mixed
  opponent_kwargs:
    easy: simple
    hard: medium
    p_hard: 0.5
```

直觉：**一半局仍像刚打过的 Simple，一半局预习 Medium**，避免难度断崖导致 `CurriculumStalled`。

### 4.2 评估与锦标赛

- 短评估：CLI / `scripts/eval_agent.py` 对指定 Bot 打多局算胜率
- 全梯子：`scripts/tournament.py` 循环赛 + Elo
- 消费方还包括 `app/bot_factory`（GUI 选人机对手）

评估时建议固定地图、`max_turns`，并想清楚是否启用 **随机平局决胜**（下一节）。

---

## 5. 平衡分析教训（白话版）

以下主题来自 `docs/zh/balance_analysis_lessons_learned.md`，改写成入门语言。

### 5.1 确定性重复局：看起来有 N 个样本，其实只有 1 个

**现象**
`games_per_side=4`，Medium vs Simple 在同一张图上打 4 局，回放 **字节级相同**，胜负完全一样。你却把 N=4 当成 4 个独立样本去算置信区间——区间会 **虚窄**。

**原因**
脚本 Bot 在候选列表上做 `sort` / `max` / `min`。平分时 Python 总取「插入顺序的第一个」。引擎也是确定性的 → 同一开局永远同一轨迹。

**教训**
- 没有随机性时，`games_per_side > 1` **不会**增加信息量，只会复制同一局。
- 旧基线里「96 局」可能实际是「12 个唯一对局 × 8 份拷贝」。

### 5.2 随机平局决胜（stochastic tiebreak）

**做法**
每个 Bot 仍只在 **最高分候选** 里选，但在排序前用 `_maybe_shuffle` 打乱平局项。`rng_seed` 固定时可复现。

**效果**
同样 4 局会走出不同动作流、不同胜负——**有效样本量恢复**。锦标赛 runner 用稳定哈希从全局 seed 派生每局每侧的 `rng`，避免 Python 内置 `hash()` 跨进程不稳定。

**注意**
只有 **每一个** 排名点都 shuffle 才有用；漏掉 `find_best_move_position` 一类热点，会让部分决策仍确定性、能力统计偏斜。

### 5.3 自杀防护（suicide guards）

**现象**
攻击评分 `value = 伤害 - 反击 + 成本项` 在「自己必死、也杀不死对方」时仍可能 **为正**。调用方 `if value > 0: 攻击` → 白送单位。

**修复直觉**
评分函数之外加硬规则：

```text
若 反击伤害 ≥ 自己当前 HP 且 自己造成的伤害 < 目标当前 HP：
    记 suicide_eval_rejected，返回极负分
```

**指标命名**
计数发生在「评估候选」时，不是「最终选定攻击」时，所以叫 `suicide_eval_rejected` 比 `suicide_blocked` 更诚实。

### 5.4 其它相关教训（简记）

| 主题 | 一句话 |
|------|--------|
| 购买单一文化 | 严格优先级 + Warrior 最便宜 → 100% 造 W；需要组成上限 |
| 能力遥测 | 终局统计只说「发生了什么」；`knight_charge` 等才说「启发式为何触发」 |
| 回放文件名 | 仅时间戳秒级会在并发/随机模式下互相覆盖；应带 `game_id` |

---

## 6. 代码地图

| 你想找… | 去哪 |
|---------|------|
| `BaseBot` / `take_turn` 合同 | `reinforcetactics/game/bot_base.py` |
| Noop…Master、MixedBot | `reinforcetactics/game/bot.py` |
| `_maybe_shuffle` / 距离 / 技能辅助 | `BotUnitMixin`（同 `bot_base.py`） |
| 锦标赛调度、Elo、导出 | `reinforcetactics/tournament/` |
| CLI 入口 | `scripts/tournament.py` |
| GUI 如何 new Bot | `reinforcetactics/app/bot_factory.py` |
| 平衡 notebook | `notebooks/balance_analysis.ipynb`、`bot_tournament.ipynb` |

---

## 7. 实操：可选短锦标赛

目标：**验证锦标赛管线能跑**，不是认真排行榜。

```powershell
cd D:\Grok\project2\reinforce-tactics   # 换成你的仓库根
conda activate reinforce-tactics

# --test：额外塞一个 SimpleBot2，保证至少 2 个参赛者（无模型/无 LLM 时也够）
# --no-llm --no-models：跳过 API 与 models/ 扫描，启动更快
# 单图 + 每侧 1 局 + 回合上限收紧：几分钟内结束（视 CPU 而定）
python scripts/tournament.py `
  --test `
  --no-llm `
  --no-models `
  --map maps/1v1/starter.csv `
  --games-per-side 1 `
  --max-turns 80 `
  --output-dir tournament_results/learning_guide_smoke
```

预期：

- 日志里出现参赛 Bot 与对局进度；
- `tournament_results/learning_guide_smoke/` 下有结果 JSON/CSV（具体文件名以 `ResultsExporter` 为准）。

若报「Need at least 2 bots」，确认加了 `--test`。默认地图路径若与你分支不一致，换成 `maps/1v1/` 下任意存在的 `.csv`。

想对比 **两条规则 Bot** 的定性强弱，可在课题章（第 17 章）做更小范围的配对实验，或读 `notebooks/bot_tournament.ipynb`。

---

## 8. 自检

- [ ] 能按强度大致排序：Noop < Random/BalancedRandom < Simple < Medium < Advanced < Master
- [ ] 能默写 `take_turn` 三条合同
- [ ] 知道为何确定性 Bot 下 `N` 局可能不是 `N` 个独立样本
- [ ] 知道 `rng` 平局决胜与自杀硬防护各解决什么问题
- [ ] 知道 MixedBot 在课程里扮演「桥」

---

## 9. 延伸阅读

| 文档 | 内容 |
|------|------|
| [`../source-analysis/game-bots.md`](../source-analysis/game-bots.md) | 规则 Bot 源码深潜 |
| [`../source-analysis/tournament-system.md`](../source-analysis/tournament-system.md) | 赛程 / Elo / CLI |
| [`../algorithms/evaluation-and-elo.md`](../algorithms/evaluation-and-elo.md) | 胜率噪声与 Elo 公式 |
| [`../../docs/zh/balance_analysis_lessons_learned.md`](../../docs/zh/balance_analysis_lessons_learned.md) | 完整平衡教训 |
| 第 13 章 | 评估、ELO、锦标赛总览 |
| 第 15 章 | LLM Bot（同一 `take_turn` 合同） |
