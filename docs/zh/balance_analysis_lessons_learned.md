# 平衡分析 — 经验总结

对 bot-tournament 平衡分析管线的复盘
（`notebooks/balance_analysis.ipynb`、`reinforcetactics/tournament/`、
`reinforcetactics/game/bot.py` 中的脚本 bot）。记录当
`baseline_20260524_034403` 运行显示前三 bot 挤在 12% 胜率带宽内，
而底层信号远弱于样本量所暗示时浮现的问题。

在从平衡运行下结论、按 tournament 结果调单位成本，或扩展脚本 bot
层次之前，请先阅读本文。

## 要点速览

1. **确定性 bot + 确定性引擎 = 重复轨迹。**
   对固定对阵与地图设 `games_per_side > 1` 会写出同一局的 N 份副本，
   而非 N 个独立样本。在 N 上计算的 Wilson CI 看起来合理，但实际
   只反映 `unique / N` 个数据点。基线运行的 96 局实际是 ~12 局唯一
   对局 × 8 份重复。
2. **随机平局决胜（`rng_seed`）恢复有效样本量。**
   无需改动任何评分逻辑——每个 bot 仍在其最高分选项中选择。只需在
   sort/max/min 前打乱平局，使等价决策在不同 episode 解析为不同选择。
3. **能力遥测比终局诊断更适合回答"为何 bot X 赢了 bot Y"。**
   `endstate_per_game` 记录的是 *游戏状态中发生了什么*（建造、金币、占领）。
   它不告诉你 *bot 触发了哪条启发式*。每局能力计数器
   （`knight_charge`、`sorcerer_haste`、`retreat_to_heal` 等）填补该缺口。
4. **优先级 + 成本排序产生单一文化。** SimpleBot 的
   "购买最高优先级可负担单位"循环总是选 Warrior（priority=1，cost=200 —
   严格占优）并在生产中 100% 造 W。任何使用严格优先级排序的购买逻辑
   都需要组成上限，否则 bot 会用自身属性检查把游戏阵容多样性淘汰掉。
5. **基于分数的攻击评估仍可能推荐自杀。**
   `value = damage_dealt - counter_damage + cost_term` 函数在致命但净
   有利的交换上仍为正（200g Warrior 造成 100 伤害、承受 80 反击 *并死亡*
   仍得 +4）。需要与评分函数分离的显式自杀防护——"若你会死却杀不掉对方，
   则中止"。
6. **PR #371 的随机平局决胜只有在每个排名点都 shuffle 时才有用。**
   覆盖不全意味着部分决策类型保持确定性，另一些变随机，从而偏置
   各 bot 的能力计数。审计发现 9 个遗漏点；命中最多的是
   `find_best_move_position`。
7. **Tournament 基础设施有潜伏缺陷，在确定性模式下被隐藏。**
   回放文件名冲突（仅时间戳、秒级精度）会静默覆盖同一秒内完成的
   相同对阵回放。直到随机模式开始为每对阵产生不同对局才显形；
   在文件名中加入 `game_id` 即可轻松修复。

## 重复轨迹问题

`baseline_20260524_034403` 中最大的测量误差来源。

### 症状

`bot_winrate_by_bucket.csv` 显示每桶 N=12 时 Wilson 95% CI 为 ±0.20。
前三 bot 挤在 12% 胜率内（MasterBot 70.8%，AdvancedBot 60.4%，
MediumBot 58.3%）。自然解读："需要更多游戏——样本量太小。"

### 实际发生了什么

默认配置（`games_per_side=1`）为每个对阵方向、每张地图写一局。
但 bot 与游戏引擎 *都是* 确定性的——相同起始状态 + 相同 bot 策略 →
字节级相同轨迹。提高到 `games_per_side=4` 也无济于事：
`MediumBot vs SimpleBot on starter.csv` 的 4 局产生相同动作流、
相同胜者、相同终态。Wilson CI 公式假定 N 个独立样本；它无法知道
自己被喂了重复。

### 定量证据

MediumBot vs SimpleBot 在 `starter.csv` 上 4 局/侧 smoke 运行，
在任何其他修复之前：

```
rng_seed=None  (deterministic, baseline behaviour)
  4 replays saved, 4 byte-identical trajectories
  → 1 unique game, recorded 4 times

rng_seed=42  (stochastic tiebreak enabled)
  4 replays saved, 4 distinct trajectories
  Winners:    p1, p2, p1, p1
  Actions:    40, 144, 102, 126
  → 4 unique games

rng_seed=42, re-run
  Same 4 trajectories as the first stochastic run (reproducible)
```

因此 `baseline_20260524_034403` 的"96 局"实际是 12 局唯一对局 × 8 副本。
CI 偏窄是因为样本看起来大；*信息量* 仅为每桶 12 个结果。

### 机制

每个脚本 bot 决策点都是对候选（可达格、可攻击敌人、可负担购买）
做 sort/max/min。当两个候选同分时，Python 的 `sort`/`max`/`min`
返回第一个——插入顺序，而非平局决胜。确定性引擎在同一起始状态的
每次回放中以相同插入顺序提供候选。净效果：bot 每次做相同选择。

PR #371 引入 `BotUnitMixin._maybe_shuffle` 作为基础设施原语：
`_rng is None` 时 no-op，设置后为 `rng.shuffle(items)`。在每次
sort/max/min 前调用，平局即随机解析。但 PR 只加了 rng *管道*；
tournament runner 中 *没有使用* 它。`rng_seed=None` 仍是隐式默认。

### 修复

三部分，单独都不够：

1. **`TournamentConfig.rng_seed: Optional[int] = None`**，默认为
   None 以保留既有行为。
2. **Runner 通过
   `SHA-256(rng_seed, game_id, map_stem, bot1_name, bot2_name, player, bot_name)`
   派生每局每侧 seed。** 必须是稳定哈希——Python 内置 `hash()` 每进程
   加盐，同一 tournament 重跑会产生不同 seed。
3. **`create_bot_instance` 将 `rng` 传入每个脚本 bot 构造函数。**
   Simple/Medium/Advanced/Master 在 PR #371 中已接受 `rng=None`；
   缺的是 runner 传入非 None 值。

有了这些，`rng_seed=42, games_per_side=4` 在默认 8 图池上产生 96 局
唯一对局——真正 96 个独立样本——且相同 seed 重跑复现同一集合。

### 对过往结果的含义

`baseline_20260524_034403` 的数字作为每个对阵 × 地图上
*单一确定性轨迹* 的测量是正确的，但不应解释为统计样本。
AdvancedBot 与 MediumBot 的聚拢可能真实，也可能是碰巧产生接近
胜率的某一特定轨迹对——从现有数据无法判断。关于 *哪些* bot
需要平衡调整的结论，须等待随机模式重跑。

## Wilson CI 展示陷阱

修复前，`bot_winrate_by_bucket.csv` 仍会打印

```
AdvancedBot, large,  12, 8, 4, 0, 0.667, [0.39, 0.86]
```

对实际为 4 唯一 × 3 重复的 12 局运行。CI 公式不知道自己被骗了关于 N。

已上线缓解：当 `RNG_SEED is None and GAMES_PER_SIDE > 1` 时在运行 cell
中一次性警告打印。不修复底层 CI 展示（那需要按局去重唯一性并重算
Wilson 区间），但至少在有人基于误导性窄条下结论前把问题暴露出来。

更原则的修复：notebook 计算每对阵的
`unique_trajectory_hashes / N` 比率，显示在 CI 列旁。开放工作项。

## SimpleBot 单一文化（优先级排序失效模式）

`baseline_20260524_034403` 中的 `bot_unit_gold_share.csv`：

```
SimpleBot, W, Warrior, 1.000, 1.000, 34.27, 48
SimpleBot, A, Archer,  0.000
SimpleBot, K, Knight,  0.000
SimpleBot, M, Mage,    0.000
... all other unit types: 0.000
```

SimpleBot 在全部 48 局中 **只造 Warrior**。

### 机制

`SimpleBot.purchase_units` 循环：
1. 获取可负担单位（cost ≤ 可用金币）。
2. 按 `(UNIT_PRIORITIES[unit_type], cost)` 排序。
3. 买第一个。
4. 直到金币耗尽。

`UNIT_PRIORITIES` 把 Warrior 放在 priority 1（最高）。Warrior 花费
200，最便宜。因此排序键为 (1, 200)——*严格占优*于其他所有单位，
不论 bot 积攒了多少金币。循环就一直买 Warrior。

没有反占优机制：无"收益递减"权重、无军队组成目标、无手头金币
的阶梯门槛。直觉"bot 现在钱多了应该多样化"从不成立——
Warrior 每次都赢排序。

MediumBot 有相同缺陷（W priority 0）。AdvancedBot 使用不同的
（基于目标比例的）购买函数，自然多样化；不受影响。

### 修复

组成上限，按最小军队规模门控以保留前期节奏：

```python
WARRIOR_SHARE_CAP = 0.5  # SimpleBot; 0.6 on MediumBot
WARRIOR_CAP_MIN_UNITS = 3  # 4 on MediumBot

if total_units >= WARRIOR_CAP_MIN_UNITS:
    w_share = w_count / total_units
    if w_share >= WARRIOR_SHARE_CAP:
        affordable = [a for a in affordable if a["unit_type"] != "W"]
```

上限触发时，Warrior 从可负担集合中退出，下一优先级单位
（Barbarian，然后 Archer）填槽。Bot 在前 2–3 次购买以及
无非 Warrior 选项时仍默认 Warrior。

### Smoke 证据

修复前：
```
SimpleBot: cap_buy_W ≈ 7/game, cap_buy_B=0, cap_buy_A=0
MediumBot: cap_buy_W ≈ 7/game, cap_buy_B=0, cap_buy_A=0.5
```

修复后：
```
SimpleBot: cap_buy_W ≈ 6.5, cap_buy_B = 0.5, warrior_cap_hit = 0.5
MediumBot: cap_buy_W ≈ 6.3, cap_buy_B = 0.5, warrior_cap_hit = 0.5
```

上限平均每局长局触发一次；触感轻但足以打破单一文化。若新基线
仍显示 bot 打 W 群，可能需要收紧（`WARRIOR_SHARE_CAP=0.4`?）。

### 一般化教训

任何"按 N 个标准排序候选、取最高"的循环，若某一选项在全部 N 个
标准上 *联合* 占优，就易受此影响。修复不是"更多标准"（占优选项
仍会赢）——而是上限、配额，或按分数比例的随机选择。对平衡工具
而言，下次添加新单位时，审计脚本 bot 层次中每一个
`while True: sort → take[0] → buy` 循环。

## 自杀防护漏洞

`AdvancedBot.calculate_attack_value`（及其在 MediumBot 中的调用者）
按如下给攻击打分：

```python
value = damage_dealt - counter_damage
value += target_cost / 100.0
value -= (counter_damage * attacker_cost) / 1000.0
```

顶部有短路：若 `damage_dealt >= target.health`（确认击杀），
返回 `1000 + damage_dealt`。

### 失效情形

考虑 100 HP 的 200g Warrior 攻击 110 HP 的 300g Knight，
Warrior 造成 100 伤害、承受 80 反击。

- `damage_dealt = 100`，`target.health = 110`——不触发击杀确认。
- `counter_damage = 80`，`attacker.health = 100`——Warrior 以 20 HP
  存活。目前还好。

现在同样的 Warrior 在 70 HP 攻击同样的 110 HP Knight，
造成 100 伤害、承受 80 反击：

- `damage_dealt = 100 < 110`，无击杀确认。
- `counter_damage = 80 ≥ 70`，攻击者 **死亡**。
- `value = 100 - 80 + 3.0 - 16.0 = +7.0`——为正。

调用方门控是 `if best_value > 0: attack`。于是 bot **攻击并死亡**，
对存活的 300g 单位造成 100 伤害——用 200g 换 80 点未击杀任何东西的伤害。
从成本加权评分函数看这是略正的交换。从真实游戏看是"白扔 200g 单位"。

### 为何成本惩罚抓不住

`(counter_damage * attacker_cost) / 1000.0` 项为 *风险* 校准
（每次攻击坏结果的小概率），而非 *确定性*（攻击者数学上必死）。
成本惩罚随 attacker_cost/1000 缩放，对常见单位很小（0.2 到 0.4），
对比原始伤害交换（50–100 点）。

### 修复

与评分函数分离的显式防护：

```python
if counter_damage >= attacker.health and damage_dealt < target.health:
    self._record("suicide_eval_rejected")
    return -1000.0 - counter_damage
```

返回严格低于调用方 `> 0` 门控的值，使 bot 将此选项视为比任何其他
动作更差——包括本回合什么都不做。

### 指标语义陷阱

计数器的朴素名称是 `suicide_blocked`。但记录发生在
`calculate_attack_value` 内，该函数被 *每次评估* 调用，而非每次
实际选定攻击。Bot 考虑五个攻击候选时可能对其中三个触发防护，
然后攻击第四个（非自杀）目标——`suicide_blocked: 3` 会夸大防护的
行为影响（"我们拒绝了三次攻击"），实际只是从候选池拒绝了三个选项。

重命名为 `suicide_eval_rejected` 以匹配实际计数内容。不修复语义
（指标仍计评估次数，非被拒攻击）；只是让名称诚实。更准确的
"被拒攻击"计数器需要在目标选择后于调用方记录，而非在 per-candidate
评估器内部。

## 能力遥测 vs 终局诊断

既有 `endstate_per_game.csv` 记录每局 *游戏状态增量*：

| 列 | 记录内容 |
|---|---|
| builds_p1, gold_spent_p1 | 玩家建造了什么 |
| captures_p1, attacks_p1, damage_p1 | 发生了什么 |
| structures_p1_final | 最终局面 |

这些是描述性的——告诉你 *发生了什么*。不告诉你 *为什么*。
若 MasterBot 以 10-6 击败 AdvancedBot，是因为：

- MasterBot 的威胁感知撤退保存了更多单位？
- MasterBot 的 HQ-snipe 优先级在 CONQUER 阶段先到？
- MasterBot 的 HP 升序集火让残血单位继续挥砍？
- MasterBot 的 Sorcerer haste 跟进链式占领？

从建造/金币/伤害数字无法判断。它们是效果，不是原因。

### 修复

每个脚本 bot 上的每局计数器，惰性创建，使绕过 `BaseBot.__init__`
的子类仍能工作：

```python
class BaseBot(ABC):
    def _record(self, name: str, n: int = 1) -> None:
        counters = getattr(self, "capabilities_fired", None)
        if counters is None:
            counters = {}
            self.capabilities_fired = counters
        counters[name] = counters.get(name, 0) + n
```

每个 bot 决策点记录命名事件：

```python
# AdvancedBot._try_knight_charge
if best_charge and best_value > 0:
    ...
    self._record("knight_charge")
    return True
```

Tournament runner 将 `bot.capabilities_fired` 快照写入回放的
`game_info`。Notebook 摄入，构建 `capabilities_per_game.csv`
（长格式，每玩家-局一行）与 `capabilities_per_bot.csv`
（每局平均触发次数）。

### 这能暴露什么（smoke 运行，12 局）

```
bot         | knight_charge | hq_snipe | retreat_to_heal | sorcerer_haste
AdvancedBot | 2.17          | 0.00     | 0.50            | 0.00
MasterBot   | 3.00          | 1.50     | 1.17            | (varies)
MediumBot   | 0.00          | 0.00     | 0.33            | 0.00
SimpleBot   | 0.00          | 0.00     | 0.00            | 0.00
```

AdvancedBot 与 MasterBot 之间 10% Elo 差距现有机制故事：
约 3× 更多 retreats-to-heal、独占 HQ-snipe 优先级、更多 Knight charges。
这是否 *导致* 胜率差距是另一问题（相关非因果），但至少差异化行为可见。

### 教训

任何需要调试 *行为*（而非状态）的系统，应在决策点插桩，而非仅
在结果上。数据量成本小（计数器字典），分析价值大。

## PR #371 审计教训

PR #371（"在每个 sort / max / best-tracking 点可选随机平局决胜"）
在 21 个排名点加入 `_maybe_shuffle`。审计又发现 9 个遗漏：

- `find_best_move_position`（命中最多——每个 bot 每次
  move-toward-target 调用）
- `try_cleric_abilities` 治疗目标 `min(HP)`
- `try_mage_paralyze` 麻痹目标 `max(cost)` 两条路径
- `try_use_special_ability` mage `for enemy in self.game_state.units`
- `_try_sorcerer_abilities` Priority 3 attack_buff、Priority 4
  defence_buff、Priority 5 defence_buff
- `try_ranged_attack` 最低 HP 目标选择（两个分支）
- `_try_sorcerer_abilities` MasterBot 双 capture combo

### 机制性担忧

对面向遥测的目标，部分覆盖比无覆盖更糟。若 21 点随机化、9 点保持
确定性，随机分布的 *形状* 取决于 bot 做了哪个决策——频繁触发的
确定性点（如 `find_best_move`）产生一致模式，偏置每个下游指标的
表观能力率。朴素解读"MasterBot 每局 charge 3× 对 Advanced 的 2.17×"
可能被确定性 move-toward-target 选择夸大，这些选择持续把 MasterBot
的 Knight 放到可 charge 位置。

### 为何发生

PR 按 `git grep "max\(|min\(|sort"` 划范围，漏掉了
`for x in collection` 先匹配获胜循环（`try_use_special_ability`
mage）、通过严格 `<` 的 best-tracking（`find_best_move_position`——
根本没有 `max`/`min`/`sort` 调用），以及 `bot_base.py` 中的辅助函数
（PR 聚焦于 `bot.py`）。

### 一般化教训

引入横切基础设施变更（"每个 X 应做 Y"）时，范围查询须匹配语义意图，
而非语法表面。对"每个排名点"：grep 输出模式（`best_*`、`*_target`、
`*_best`），而非输入模式（`max`、`min`、`sort`）。更好的是：加代码
评审清单或 CI lint 规则，标记 bot 文件中新的 sort/max/min/严格比较
排名点。否则一旦有人加新启发式，审计缺口会重开。

## 回放文件名冲突

`games_per_side > 1` 整个生命周期中的潜伏缺陷，但在确定性模式下
不可见（重复轨迹回放以相同内容覆盖——无功能影响）。一旦随机模式
为每对阵产生不同对局而文件名无法消歧，就硬性暴露。

### 机制

```python
replay_filename = (
    f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{bot1_desc.name}_vs_{bot2_desc.name}_{map_config.stem}.json"
)
```

秒级时间戳。同一秒内完成的同一对阵两局产生相同文件名。
`FileIO.save_replay` 直接写入；无冲突检测。

### 修复

在文件名中包含 `game_id`（`ScheduledGame` 上已有）：

```python
replay_filename = (
    f"game_{...timestamp...}_id{game_id:04d}_{bot1}_vs_{bot2}_{map_stem}.json"
)
```

### 教训

因无关属性"碰巧能用"的默认值（确定性回放产生相同字节）是定时炸弹。
任何从非唯一源（时间戳、默认 `random()` 的随机整数、哈希截断）
派生唯一标识的东西，都需要 *证明* 唯一性或在写入点 *处理* 冲突。

此模式在代码库其他处也有——例如 runner 中的 `game_session_id` 使用
`datetime.now()` 无消歧。下次有人改 tournament-runner 写入路径时
值得扫一遍。

## 横切：今后如何做平衡运行

任何平衡分析运行的发货默认清单：

1. **将 `RNG_SEED` 设为固定整数。** `42` 即可；任何整数均可，只要记录。
   Notebook 现会在其为 None 且 `GAMES_PER_SIDE > 1` 时警告。
2. **`GAMES_PER_SIDE = 4` 作为最低值**（默认为 1，适合抽查，但每桶
   N=12——对超出顶线积分榜的任何分析都太窄）。
3. **运行后检查 `capabilities_per_bot.csv`。** 若 bot 的特征能力
   （例如 MasterBot 的 `hq_snipe`、`haste_followthrough`）未以预期
   速率触发，在从胜负数字下结论前先调查。
4. **用 `bot_unit_gold_share.csv` 交叉对照积分榜。** 若 bot 的
   单位金币份额像单一文化模式（一单位 ≥0.9），你在测量退化策略，
   而非 bot 的设计。
5. **跨代码 commit 比较运行时，务必检查 `engine_constants_hash`。**
   活在 `constants.py` 中的平衡变更（单位属性、起始金币、结构收入）
   会静默混淆平衡比较。Bootstrap 文档的"engine-constant confound class"
   一节是相关先例——同样教训适用于此。

## 不值得再追的

- **"更多局会修好 CI。"** 不——没有 `rng_seed`，更多局就是重复。
  修复是 seed，不是数量。
- **在跑随机基线前把 Medium↔Advanced 聚拢当设计问题追。**
  `baseline_20260524_034403` 数据无法区分"它们实际接近"与
  "每桶只有 3 局唯一对局"。等待 post-`rng_seed` 数字。
- **在优先级排序中加更多标准以修单一文化。** SimpleBot 有 2 个标准
  （priority、cost）；对 Warrior 都占优。加第 3 个对 Warrior 占优的
  标准无济于事。上限、配额或比例采样是唯一修复。
- **降低自杀防护阈值以"保留激进打法"。** 防护仅在攻击者 *确定死亡*
  且目标 *确定存活* 时触发。两个条件都是致命交换诊断，不是偏好信号。
  没有可拧的"更激进"旋钮——只有"忽略防护并接受单位损失"，
  这正是 bot 此前在做的。

## 未来工作

- **积分榜表中的 CI 准确度列。** 计算并显示 `unique_trajectory_count / N`
  与 Wilson CI 并列，使读者能看到展示的 CI 何时夸大了信息量。
- **技能消融 tournament。** 每轮禁用一项能力重跑（MasterBot 关闭
  `_threat_map`、MasterBot 关闭 `haste_followthrough`、AdvancedBot
  关闭 `counter_matrix`）。每次消融的 Elo 差给出"什么区分 bot N 与
  bot N+1"的定量答案。能力遥测已提供 *观测* 版本；消融是 *因果*
  版本。昂贵（每次消融一场 tournament）但决定性。
- **威胁感知撤退作为独立能力计数器。** MasterBot 的 `find_retreat_tile`
  选与 AdvancedBot 不同的（更安全）格。当前两者都记 `retreat_to_heal`。
  增加 `retreat_threat_avoided`（威胁图分数与父级选择不同时递增）
  会给"MasterBot 撤退比 Advanced 更安全"的论断直接证据。
- **非对称质量 bot 阶梯。** 若设计目标是"Medium 应明显弱于 Advanced"，
  当前实现主要靠 *阵容限制* 达成（MediumBot 不能造
  Cleric/Sorcerer/Rogue/Barbarian/Mage）。有了随机模式与新能力遥测，
  现在可以设计阵容相同但 *启发式更差* 的 MediumBot（例如更短威胁
  视野、无 charge-bonus 利用、朴素治疗目标）。那会是比
  "enabled_units 不同"更有趣的设计空间。

## 交叉引用

PPO bootstrap 文档
（[`bootstrap_lessons_learned.md`](bootstrap_lessons_learned.md)）
有一则"Knight 强化：脚本 bot 看不见、RL 看得见"的旁注，预示了部分
这些发现——特别是脚本 bot 的静态启发式优先级使它们对 RL 会发现的
属性变更视而不见。随机模式现已可用，bot-tournament 输出的 *统计*
  可靠性得以恢复，但 *对属性变更盲目* 的论断仍然成立：打乱平局
不会让固定优先级 bot 开始偏好被强化的单位。对 RL 相关的属性调优，
回放级指标（建造计数、金币份额、存活率）仍是正确信号，而非 bot
胜负。随机模式使这些回放级指标具有统计意义，这是新贡献。
