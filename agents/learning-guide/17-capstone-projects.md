> 返回：[指南目录](README.md) · [上一章](16-dev-toolchain.md) · [下一章](glossary.md) · [索引](../AGENTS.md)

# 第 17 章：综合练习课题

本章是指南的 **收束实战**：五个课题由浅到深，验收标准写清楚，方便自学或作为课程作业。不必全做；按时间选 1–2 个做完并留下简短报告即可。

**默认环境**

```powershell
cd D:\Grok\project2\reinforce-tactics
conda activate reinforce-tactics
python -c "import reinforcetactics, gymnasium, torch; print('ok')"
```

命令以当前仓库 CLI / 脚本为准；若参数名有微调，以 `--help` 与 [`../usage/local-run-guide.md`](../usage/local-run-guide.md) 为准。

---

## 课题 1：短 PPO 训练 + 评估报告

### 目标

跑通「训练 → 保存 → 评估」主线，写一页纸结论（中文即可）。

### 建议步骤

1. 用 **短步数** 配置或 CLI 覆盖（CPU 友好），例如总步数 \(10^4\sim5\times10^4\) 量级（能出 checkpoint 即可，不求强）。
2. 训练：

   ```powershell
   python main.py --mode train --algorithm ppo --help
   # 按 help 与 local-run-guide 选择短配置 / 覆盖 total_timesteps
   ```

3. 评估：对 `noop` / `random` / `simple` 中至少 **一种** 对手多局评估。
4. 记录：地图、步数、种子、对手、胜率或平均回报、训练墙钟时间。

### 验收标准

- [ ] 训练过程无崩溃，磁盘上有可加载的模型产物（如 `.zip`）
- [ ] 至少完成一次自动化评估并记下数字
- [ ] 书面说明：你认为结果「有没有学到东西」——例如是否优于随机瞎点（允许结论为「步数太短没学到」）
- [ ] 点出 **一个** 你对照过的代码位置（如 `rl/gym_env.py` 的 `step` 或 CLI train 入口）

### 对应章节

04、05、13；算法卡 [`../algorithms/ppo.md`](../algorithms/ppo.md)

---

## 课题 2：改一项 `reward_config` 并定性对比

### 目标

理解奖励塑形对行为的影响，而不是只调学习率。

### 建议步骤

1. 找到 `reward_config`（训练 YAML 如 `configs/ppo/ppo_baseline.yaml` / `bootstrap.yaml` 的 `env.reward_config`，或 env 默认值）。
2. **只改一个标量**，例如：
   - 提高 / 降低 `win_by_hq_capture` 或 `win_by_elimination`；或
   - 调整某项塑形（占领进度、回合惩罚等——以配置里真实键名为准）。
3. 用 **相同种子、相同短步数、相同对手** 各训一小段（或用固定脚本策略 + 打印 episode 回报做更轻的对比）。
4. 定性观察：是否更爱冲 HQ、是否拖回合、是否只杀单位不占建筑等。

### 验收标准

- [ ] 写明改动前后的 **键名与数值**
- [ ] 控制变量：至少种子与对手协议一致
- [ ] 用 3–5 句描述行为差异（允许「看不出差异，因为步数太短」）
- [ ] 联系第 07 章：稀疏终局 vs 稠密塑形、潜在风险（杀敌刷分、量级压垮 value）

### 对应章节

07；[`../algorithms/reward-shaping.md`](../algorithms/reward-shaping.md)；源码 [`../source-analysis/rl-gym-env.md`](../source-analysis/rl-gym-env.md)

---

## 课题 3：微型 Bootstrap 或精读阶段 YAML

### 目标

搞清课程学习「阶段」长什么样，以及晋级在说什么。

### 路径 A — 真跑一个极短课程（可选，耗时）

1. 复制 `configs/ppo/bootstrap.yaml` 为本地临时配置。
2. 删到只剩 **1–2 个最简单阶段**（如 starter + random/simple），把 `max_timesteps`、评估频率降到可接受。
3. 跑 `scripts/train/train_bootstrap.py` 或文档推荐入口，观察是否晋级 / 是否 `CurriculumStalled`。

### 路径 B — 只读不训（推荐 CPU 紧张时）

1. 打开 `configs/ppo/bootstrap.yaml`。
2. 列出至少 **4 个** `curriculum.stages` 条目：`name`、`opponent`（及 `opponent_kwargs` 若有）、地图相关字段、晋升门槛（若有）。
3. 用自己的话解释：为什么 Simple 之后要接 MixedBot，而不是直接 Advanced。

### 验收标准

- [ ] 能画出「弱 → 强」的阶段箭头（文字版即可）
- [ ] 正确解释 `MixedBot` 的 `easy` / `hard` / `p_hard` 至少一处实例
- [ ] 说明 `CurriculumStalled` 大致在什么情况下出现（阶段预算用尽仍未达胜率）
- [ ] 若跑了训练：贴阶段目录或日志中晋级相关一行证据

### 对应章节

08、14；[`../algorithms/curriculum-bootstrap.md`](../algorithms/curriculum-bootstrap.md)；[`../../docs/zh/bootstrap_lessons_learned.md`](../../docs/zh/bootstrap_lessons_learned.md)

---

## 课题 4：两个脚本 Bot 的锦标赛

### 目标

用锦标赛管线比较规则 Bot，巩固第 14 章。

### 建议步骤

```powershell
python scripts/tournament.py `
  --test `
  --no-llm `
  --no-models `
  --map maps/1v1/starter.csv `
  --games-per-side 1 `
  --max-turns 100 `
  --output-dir tournament_results/capstone_bots
```

1. 确认输出目录中有结果文件。
2. 阅读胜负表：内置 Simple / Medium / … 与 `--test` 的 SimpleBot2 谁赢。
3. **思考题**：若 `games_per-side` 提到 4 且 **不** 开随机平局决胜，统计上可能有什么问题？（第 14 章 5.1）

进阶（可选）：在 notebook 或小脚本里只实例化 `SimpleBot` vs `MediumBot` 多局，手动统计胜率。

### 验收标准

- [ ] 命令成功跑完，结果目录非空
- [ ] 用表格或列表写出至少一对 matchup 的胜负
- [ ] 书面回答：确定性重复局为何会让「N 局」的置信区间骗人
- [ ] 指出 `take_turn` 合同中「必须 end_turn」一条

### 对应章节

13、14；[`../source-analysis/tournament-system.md`](../source-analysis/tournament-system.md)

---

## 课题 5：LLM 一回合 Demo **或** 精读 Prompt 结构

任选一条路径。

### 路径 A — 真调用 API（需 Key 与 `[llm]`）

```powershell
pip install -e ".[llm]"
$env:OPENAI_API_KEY = '...'   # 或 Claude / Gemini 对应变量
python examples/llm_bot_demo.py
```

验收：

- [ ] Demo 至少成功完成 **1 次** `take_turn`（日志中有成功标记）
- [ ] 记录供应商、是否报错重试、体感延迟
- [ ] 用三句话对比 LLM Bot 与 PPO ModelBot（第 15 章表）

### 路径 B — 不调用 API，只读代码

1. 阅读 `reinforcetactics/game/llm_prompts.py` 中 `PROMPT_BASIC` 或 `PROMPT_STRATEGIC`。
2. 阅读 `llm_bot.py` 中 `take_turn`：序列化 → 调用 → 解析 → 执行。
3. 写出：
   - system prompt 里规定了哪些动作类型；
   - 非法 JSON / 非法动作时 Bot 如何兜底；
   - 为何默认 **不会** 用回报更新 LLM 权重。

### 验收标准（路径 B）

- [ ] 列出至少 4 种动作类型字段（如 CREATE_UNIT、MOVE、ATTACK、END_TURN）
- [ ] 说明失败时为何仍应 `end_turn`（合同）
- [ ] 明确：本课题 **不是** 云训练

### 对应章节

15；[`../source-analysis/game-llm-and-model-bots.md`](../source-analysis/game-llm-and-model-bots.md)

---

## 学习清单：章节回映

用此表自检是否达到指南目标。全部勾完 ≈ 走完主线。

### Part A — 地基

| 能力 | 章 | 自检 |
|------|----|------|
| 能激活环境并指向仓库地图 | 00 | [ ] |
| 能解释为何用 RL 做这款策略游戏 | 01 | [ ] |
| 能把规则对应到 MDP 要素 \(S,A,R,P,\gamma\) | 02 | [ ] |
| 能读懂折扣回报与简单期望式 | 03 | [ ] |

### Part B — 框架与首训

| 能力 | 章 | 自检 |
|------|----|------|
| 能说明 Gymnasium `reset/step` 与 SB3 角色 | 04 | [ ] |
| 能完成一次短训并找到产物 | 05 | [ ] |
| 能区分观察、动作空间、掩码 | 06 | [ ] |
| 能举一例稀疏奖励 vs 塑形 | 07 | [ ] |

### Part C — 算法专章

| 能力 | 章 | 自检 |
|------|----|------|
| 能解释课程阶段与晋级 / stalled | 08 | [ ] |
| 知道 BC 是模仿演示而非回报最大化 | 09 | [ ] |
| 知道自对弈为何需要对手池 / 快照 | 10 | [ ] |
| 知道 Feudal 的 Manager/Worker 分工 | 11 | [ ] |
| 知道 AlphaZero = 网络 + MCTS 自对弈数据 | 12 | [ ] |
| 能解释胜率噪声与 Elo 直觉 | 13 | [ ] |

### Part D — 扩展与工程

| 能力 | 章 | 自检 |
|------|----|------|
| 能排序 Bot 梯子并复述 `take_turn` 合同 | 14 | [ ] |
| 能描述 LLM 流水线与主要限制 | 15 | [ ] |
| 能跑 pytest / ruff，并知道 commit 作者 env | 16 | [ ] |
| 至少完成 **一个** 本章课题并留下笔记 | 17 | [ ] |
| 能用术语表查中英对照 | [glossary.md](glossary.md) | [ ] |

### 综合目标（指南开头承诺）

| 目标 | 自检 |
|------|------|
| 能向他人用游戏语言讲清 agent / env / reward / policy | [ ] |
| 知道本项目主线：玩 → 短训 PPO → 评估 → Bot / 锦标赛 | [ ] |
| 知道算法速查在 `agents/algorithms/`，源码深潜在 `agents/source-analysis/` | [ ] |
| **不做** 默认路径上的云训练（Vertex） | [ ] |

---

## 报告模板（可选）

```text
课题编号与标题：
日期与环境（CPU/GPU、commit 哈希可选）：
做了什么（命令 / 改动文件）：
关键数字或观察：
结论（3–8 句）：
卡点与下一步：
对应章节：
```

---

## 下一步去哪

| 你想… | 去向 |
|--------|------|
| 查术语 | [glossary.md](glossary.md) |
| 继续抠算法 | [`../algorithms/overview.md`](../algorithms/overview.md) |
| 继续抠源码 | [`../source-analysis/overview.md`](../source-analysis/overview.md) |
| 读作者训练日记 | [`../../docs/zh/`](../../docs/zh/) |
| 玩家向安装与规则 | [reinforcetactics.com](https://reinforcetactics.com) |

恭喜读到这里。把课题笔记留下，比「只收藏文档」有效得多。
