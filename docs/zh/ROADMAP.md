# Reinforce Tactics — 开发路线图

一份按优先级划分的分阶段计划，将 Reinforce Tactics 从扎实的 alpha 打造成
完整的强化学习教育平台。每个阶段都建立在前一阶段之上。

> **最近更新：** 2026 年 5 月
> 状态图例：✅ 已完成 | 🟡 部分完成 | ⬚ 未开始

---

## 进度总览

| 阶段 | 描述 | 进度 |
|-------|-------------|----------|
| **Phase 1** | 夯实基础与快速收益 | **75%** — 4 项中 3 项完成 |
| **Phase 2** | 教育脚手架 | **0%** — 4 项中 0 项完成 |
| **Phase 3** | RL 深度与模型动物园 | **~25%** — 7 项中 0 项完成，2 项部分完成（3.2 的 6 个子任务中 4 项完成） |
| **Phase 4** | LLM 与基准打磨 | **12%** — 4 项中 0 项完成，2 项部分完成 |
| **Phase 5** | 平台扩展 | **10%** — 5 项中 0 项完成，2 项部分完成 |

---

## 算法与系统状态

各训练器 / Bot 类型的当前快照。「进入锦标赛」表示已出现在最新的
`tournament_results/` 目录中。

### 训练器（学习权重）

| | 代码 | 配置 | 训练 notebook | 进入锦标赛 | 状态 / 最大缺口 |
|---|---|---|---|---|---|
| **PPO (MaskablePPO)** | ✅ `make_maskable_env`, `masking.py` | ✅ `maskable_ppo.yaml`, `ppo_baseline.yaml`, `self_play.yaml` | ✅ `ppo_training.ipynb` | ❌ | 已训练 checkpoint 尚未进入天梯 |
| **Feudal RL** | ✅ `feudal_rl.py`，action masking + AR head 可选开启 | ✅ `feudal_rl.yaml` | ✅ `feudal_rl_training.ipynb` | ❌ | 已训练 checkpoint 未进入；尚未做独立 worker 与 AR worker 的 A/B |
| **AlphaZero** | ✅ `alphazero_net.py`，MCTS | ✅ `alphazero.yaml` | ❌ | ❌ | 无训练 notebook、无 checkpoint；策略头写死了网格尺寸（`alphazero_net.py:90`），因此无法与 PPO/feudal 共享权重或 AR head |
| **Autoregressive head**（AlphaStar 风格） | ✅ 在 feudal worker 内（`AutoregressiveActionHead`、`StructuredMaskProvider`、mask 贯通的 PPO 更新） | 通过 `--autoregressive-worker` 标志共享 `feudal_rl.yaml` | 共享 feudal notebook | ❌ | 架构已就位 + 42 项测试；从未真正训练过，尚无 PPO 或 AlphaZero 变体 |

### Bots（仅推理）

| | 状态 | 备注 |
|---|---|---|
| **LLM bots**（Claude、ChatGPT、Gemini） | ✅ 在 `bot_tournament.ipynb`、`llm_bot_tournament.ipynb` 中 | 已在天梯上；`Gemini 3.0 Flash` 第 2 名，其余低于 `MediumBot` |
| **脚本 bots**（Random/Noop/Simple/Medium/Advanced） | ✅ 完成 | `AdvancedBot` 目前为锦标赛榜首 |

### 顶层缺口（横切）

1. **三个训练器都没有 checkpoint 登上锦标赛天梯。** 天梯显示 AdvancedBot 能打败 LLM，但对 PPO/Feudal/AlphaZero 相对 AdvancedBot 毫无信息——而这正是本项目的核心问题。
2. **AlphaZero 是验证最少的训练器：** 无训练 notebook、无 checkpoint，且扁平策略头需要像 feudal 那样做 AR-head 改造，才能扩展到小地图之外。
3. **AR head 目前只存在于 feudal 内部。** 独立 PPO 与 AlphaZero 变体（Phase 3.2）仍待完成。

---

## 已完成工作（原路线图之外）

路线图创建之后交付、但原先未在此跟踪的重要功能：

### 精灵与动画系统 ✅
- 基于坐标的精灵动画与移动路径过渡
- 按队伍的调色板替换：单位精灵与队伍着色的建筑地块
- 地块变体自动发现，增加地形视觉多样性
- 精灵表拆分工具与统一的 `sprites_path` 自动发现

### AlphaZero 实现 ✅
- 完整 AlphaZero + MCTS（`alphazero_net.py`、`alphazero_trainer.py`、`mcts.py`）
- 双头 CNN：残差块 + 策略头与价值头
- MCTS 使用 PUCT 选择、Dirichlet 噪声、神经网络评估、action masking
- 自对弈数据生成、回放缓冲、学习率调度、checkpoint
- 与游戏兼容的 `AlphaZeroBot`，可用于锦标赛
- `test_alphazero.py` 中 22 项综合测试
- 训练脚本：`scripts/train/train_alphazero.py`

### Feudal RL（分层）实现 ✅
- Manager-Worker PPO，支持可变步长 GAE 与内在奖励
- `FeudalRolloutBuffer`，manager/worker 分开存储
- 完整训练循环 + TensorBoard 日志（`scripts/train/train_feudal_rl.py`）
- CLI 参数：`--manager-horizon`、`--worker-reward-alpha`、`--manager-lr-scale`

### AdvancedBot 与 RL 缺陷修复 ✅
- `game_state.py` 中强制 `max_turns`（对局不再无限进行）
- BFS 寻路修复：将 `moving_unit` 传入 `get_legal_actions()`
- 缓存交错修复：`unit_count` 与 `legal_actions` 使用独立标志
- Bot 递归保护（`MAX_RECURSION_DEPTH=10`），防止 haste 栈溢出
- 模型 bot 掩码：使用真实合法动作掩码，而非 `np.ones`
- 自对弈权重交换：`try/finally` 保护，安全恢复权重
- 改进异常处理与结构化日志

### 关键缺陷修复第二轮 ✅
- 死亡攻击者状态突变：用 `attacker_alive` 保护 `can_move`/`can_attack`
- ClaudeBot `max_tokens` 崩溃：Anthropic API 要求 `max_tokens`；为 None 时默认 4096
- `_execute_action` 中裸异常捕获：`TypeError`/`AttributeError` 现在重新抛出，不再被吞掉
- 山地视野加成：`calculate_vision_radius()` 现已接入 `PlayerVisibility.update()`（山地 +1 射程生效）
- 自对弈 `swap_players` 修复：在 `StrategyGameEnv` 上增加 `agent_player` 属性；`_execute_action`、`_get_obs`、`_compute_potential` 与 `step()` 使用它，而非硬编码玩家 1；`SelfPlayEnv` 在 reset 时把 `agent_player` 传到基础环境

### 存档 / 读档 / 回放改进 ✅
- 退出进行中的对局时提示先保存
- 对局结束后自动保存回放
- 加载菜单显示状态、时间戳与对局信息

### 锦标赛改进 ✅
- `enabled_units` 配置，可按锦标赛限制单位类型
- `ClaudeBot` JSON 序列化支持（`to_dict()` / `from_dict()`）
- `LLMBot` 中的 token 统计（`total_input_tokens`、`total_output_tokens`、`get_token_usage()`）

### 包与基础设施 ✅
- `pyproject.toml` 支持 pip 安装（版本 0.2.0）
- 依赖拆分：无头基础、`[gui]`、`[llm]`、`[dev]`、`[all]` extras
- 战争迷雾：HQ 始终可见，建筑/塔在侦察前隐藏
- 2v2 FoW 视角支持
- 文档站点与当前代码库同步

---

## Phase 1：夯实基础与快速收益（1–2 周）

高影响、低成本的项目，可解锁后续一切工作。

### 1.1 修复 `SelfPlayCallback` 的 SB3 兼容性 ✅
**优先级：** 关键
- `SelfPlayCallback` 现通过 `_make_callback_class()` 中的动态类创建
  继承 `BaseCallback`。
- 按 SB3 API 实现 `_on_step()` 与 `_init_callback()`。
- 在 `test_self_play.py` 中测试了与 `MaskablePPO` 的 callback 集成。

### 1.2 添加基线训练基准 ⬚
**优先级：** 高 — 用户目前无法判断训练是否有效。
- 在 `maps/1v1/beginner.csv` 上，用带 action masking 的 PPO 对战 `SimpleBot`，
  分别跑 10K、50K、200K、1M timesteps。记录胜率、平均奖励、平均 episode 长度。
- 将结果保存为 markdown 表与 TensorBoard 日志。
- 提交为 `docs-site/docs/training-benchmarks.md` 以及带训练脚本与日志的
  `benchmarks/` 目录。
- 目标：用户可运行同一脚本，将自己的曲线与参考对比。

### 1.3 统一 Action Mask 逻辑 ✅
**优先级：** 中
- `gym_env.py` 中的 `_build_masks()` 只调用一次 `get_legal_actions()`，
  并从共享中间结构导出扁平与按维度掩码。
- `_get_action_mask()`（扁平）与 `action_masks()`（元组）都使用该统一方法。

### 1.4 添加 RL 专用测试 ✅
**优先级：** 中
- `test_gym_env.py` 中 73+ 项测试，覆盖：
  - `reset()` 与 `step()` 后 observation 形状与 `observation_space` 一致
  - `action_masks()` 任意维度都不会返回全零
  - 奖励落在预期范围内
  - 自对弈环境正确交替玩家

**里程碑：** ~~Phase 1 结束时，RL 训练流水线正确、有测试，并~~
~~有文档化的预期结果。~~ **状态：4 项中 3 项完成。** RL 流水线已正确且有测试。
基线基准仍是最后缺口——发布后用户将有参考点来验证自己的训练运行。

---

## Phase 2：教育脚手架（2–4 周）

这是杠杆最高的工作。代码已存在，只需要让人用得上。

### 2.1 初学者 RL 环境 ⬚
**优先级：** 高 — 对新人影响最大的单项改动。
- 创建 `StrategyGameEnvSimple`（或配置预设）：6x6 地图（现有
  `maps/1v1/beginner.csv`）、2 种单位（Warrior + Archer）、无特殊能力、
  更小的动作空间。
- 在此环境上，PPO 应在 <50K 步内对 `SimpleBot` 收敛到 >70% 胜率。
- 附带脚本：`examples/train_beginner.py`，在 CPU 上约 5 分钟跑完。
- 在文档站点中记录预期输出。

### 2.2 核心 RL 文档页面 ⬚
**优先级：** 高 — 文档站点几乎没有 RL 内容。
向 `docs-site/docs/` 添加这些页面：
- **「训练你的第一个 Agent」** — 逐步 PPO 教程、预期现象、如何阅读
  TensorBoard 输出。
- **「理解环境」** — observation space 图解、action space 拆解、
  reward config 说明。
- **「Action Masking 详解」** — 为何重要、在本游戏中如何工作、
  过近似（over-approximation）权衡。
- **「奖励工程指南」** — 稀疏 vs 稠密、基于势的 shaping（引用
  Ng et al. 1999）、直接动作加分的风险、如何调 `reward_config`。
- **「自对弈训练指南」** — 对手池、选择策略、检测策略循环、推荐超参。

### 2.3 学习路径 / 课程页面 ⬚
**优先级：** 高 — 给项目清晰的叙事弧线。
- 在文档站点增加「Learning Path」页面，渐进课程：
  1. 手动游玩以理解机制
  2. 在初学者环境上训练 PPO
  3. 理解并调优 reward shaping
  4. 加入 action masking
  5. 自对弈训练
  6. AlphaZero 深入
  7. Feudal RL（分层）
  8. LLM bots 与 RL-vs-LLM 对比
- 每一步链接到相关文档页、示例脚本与预期结果。

### 2.4 扩展示例脚本 ⬚
**优先级：** 中
- `examples/train_self_play.py` — 端到端自对弈 + 对手池
- `examples/train_alphazero.py` — AlphaZero + MCTS 可视化
- `examples/evaluate_and_compare.py` — 用训练模型对战 bots 并打印统计
- `examples/reward_shaping_experiment.py` — 用不同 reward 配置训练并画对比图

> **注意：** `train/` 中已有训练脚本（train_self_play.py、train_alphazero.py、
> train_feudal_rl.py），但它们是完整训练流水线，不是简化的教学示例。
> `examples/` 目录仍需要面向初学者的版本。

**里程碑：** Phase 2 结束时，零 RL 经验的用户可沿学习路径从「什么是 RL？」
走到「我训练了一个 AlphaZero agent」。

---

## Phase 3：RL 深度与模型动物园（3–6 周）

加深 RL 能力并交付预训练产物。

### 3.1 预训练模型动物园 ⬚
**优先级：** 高 — 无需等待训练即可上手体验。
- 交付模型：随机基线、50K 步、200K 步、1M 步、自对弈冠军。
- 以可下载 `.zip` 存储（或 Git LFS / release 产物）。
- 增加 `examples/play_against_model.py`：加载模型并渲染一局。
- 用户可立刻看到不同训练预算的效果。

### 3.2 自回归动作分解 🟡
**优先级：** **高 — 在 10x14+ 与 20x20 地图上训练前的前置条件。**

当前 MultiDiscrete 空间（10 × 8 × W × H × W × H）配合独立按维 masking，
在大地图上会遭遇组合爆炸：

| 地图尺寸 | 组合数 | 按维 mask 过近似 |
|----------|-------------|--------------------------|
| 6×6      | 288K        | 可管理                   |
| 10×14    | 1.6M        | 显著                     |
| 20×20    | 12.8M       | 严重                     |

自回归分解使每一步选择保持较小（≤H·W），与地图大小无关，
并支持*精确*条件 masking，消除所有非法动作组合。

**分解顺序（已交付 — 联合空间头，比原规格更简单）：**
```
action_type(A) → src_xy(H·W) → unit_type(U) → tgt_xy(H·W)
```
每阶段在所有先前选择条件下采样：
`P(at) → P(src|at) → P(ut|at, src) → P(tgt|at, src)`。
`src_xy → tgt_xy` 联合头替代原 `from_x → from_y → to_x → to_y`
4 阶段规格，因为底层合法性数据已经按 (x, y) 成对。

**实现步骤：**

1. ✅ **条件 mask 构建器**（`gym_env.py`）— `StructuredActionMasks` dataclass +
   `StrategyGameEnv.structured_action_masks()` 从单次 `get_legal_actions()`
   构建 atype/source/target/unit_type。`test_structured_masks.py` 验证与现有
   扁平枚举精确等价。

2. ✅ **自回归策略网络** — `feudal_rl.py` 中的 `AutoregressiveActionHead`
   （而非独立模块——目前可以，因为只有 feudal 消费它）。
   分阶段 logits + 可选每阶段 masks；`sample`、`sample_with_provider`、
   `evaluate` 镜像联合因式分解。源位置嵌入送入 unit_type 与 target 头，
   使二者真正以所选源为条件。

3. ✅ **Feudal RL 集成** — `FeudalRLAgent` 上的 `autoregressive_worker=True` 标志。
   `AutoregressiveWorkerNetwork` 可直接替换 `WorkerNetwork`。采样时应用的
   条件 masks 存入 buffer（`FeudalRolloutBuffer(store_masks=True)`），
   并在 PPO 更新时经 `evaluate_action` 回放，使新旧 log-prob 在相同 mask
   支撑下计算。

4. ⬚ **独立 PPO 模式** — `StrategyGameEnv` 上的 `action_space_type='autoregressive'`，
   以及 SB3 兼容的策略包装，使 AR head 无需 feudal 层级也能工作。
   *仍开放。*

5. ⬚ **训练 CLI** — `scripts/train/train_feudal_rl.py` 上的 `--autoregressive-worker`，
   以及 3.2.4 落地后的 `--mode autoregressive`。*仍开放。*

6. ✅ **测试** — 跨 `test_structured_masks.py`、
   `test_autoregressive_head.py`、`test_autoregressive_rollout.py` 共 42 项新测试。
   端到端检查确认真实 rollout 中记录的每个动作，其 bit 都在采样时实际应用的
   mask 中置位（即策略在训练期间可证明只采样合法动作）。

**本工作内的开放后续：**
- 上文 3.2.4 + 3.2.5（独立 PPO + CLI 标志）。
- AR worker 的 `select_action` 推理时 masking — 当前未掩码，因为
  `select_action` 没有 env 引用；若传入 `action_masks` 参数或 env 句柄，
  可作为小后续处理。
- 将 AR head 改造应用到 AlphaZero（`alphazero_net.py:90` 是与 feudal 相同的扁平
  `Linear(32·H·W, A·H·W)` 形状，3.2 已为 feudal 修复）。

**前置于：** 在大于 6×6 的地图上以有竞争力的样本效率训练。
应在 Phase 5.1 的大地图课程阶段之前完成。

### 3.5 从 `AdvancedBot` 做行为克隆 Bootstrap ⬚
**优先级：** 中 — 本地替代 AlphaStar 的人类回放 SL 阶段。

AlphaStar 依赖人类回放的监督预训练，在 RL 前给策略强先验。我们没有回放，
但有最强脚本 bot `AdvancedBot`。短 BC 阶段应能给三个训练器合理热启动，
对 AR worker 尤其有价值（其联合分布比旧版 6 头独立 worker 更宽，冷启动探索更难）。

**步骤：**
1. **轨迹收集器** — `scripts/collect_advancedbot_trajectories.py` 跑
   AdvancedBot vs AdvancedBot，将 `(obs, structured_masks, action)` 三元组
   落盘。
2. **BC 预训练循环** — 在记录的 masks 下，最小化 `AutoregressiveActionHead.evaluate`
   相对记录动作的交叉熵。复用 head 现有
   `evaluate(features, action, masks)` 签名，无需新网络代码。
3. **动作先验辅助损失** — 在 PPO 中加入小系数 `-log p_policy(bot_action | s)`，
   系数随训练衰减。本地类比 AlphaStar 的 z-conditioning 衰减；减轻 RL 接管后的
   BC 分布偏移。
4. **A/B 支架** — 相同 seed 与配置，`BC + RL` vs `RL only`。相对
   `AdvancedBot` 的胜率与首次获胜时间是头条指标。

### 3.6 将自回归头扩展到 PPO 与 AlphaZero ⬚
**优先级：** 中 — 收口 3.2.4 并解锁 AlphaZero 扩展。

目前 `AutoregressiveActionHead` 住在 `feudal_rl.py` 内。两个自然扩展：

- **MaskablePPO + AR head。** 将 `AutoregressiveActionHead` 抽到
  `reinforcetactics/rl/autoregressive.py`，构建使用它的 SB3 兼容策略，
  把 structured-mask 路径接到 PPO rollout buffer。
- **AlphaZero + AR head。** `alphazero_net.py` 中的 `Linear(32·H·W, A·H·W)`
  策略头是与 feudal worker 相同的形状问题。用 AR head 替换，经链式法则
  计算联合先验以兼容 MCTS。让 AlphaZero 扩展到更大地图，并与另两个训练器
  共享架构工作。

### 3.7 验证 AR Worker（A/B vs 旧版 Feudal） ⬚
**优先级：** 高 — 对 3.2 工作是否值得交付的决策级测试。

从相同 seed、相同超参训练两次 feudal，唯一差异：
`autoregressive_worker=False` vs `=True`。预期结果：

- **非法动作率** 在 AR 下降至 ~0（masking 精确）。
- **相对 `AdvancedBot` 的胜率** 提升，或至少匹配样本效率。
- **专家动作的联合对数似然**（来自 3.5 的 BC 轨迹）在 AR 下应显著更高 —
  旧版 worker 无法表示依赖关系。

若胜率不提升，说明 AR head 正确但受探索约束，下一步应尝试 3.5
（BC bootstrap）。无论结果如何，都能决定是否默认 `autoregressive_worker=True`。

### 3.3 AlphaZero 与 Feudal RL 文档 🟡
**优先级：** 中 — 这些很亮眼但不可见。
- **「Reinforce Tactics 的 AlphaZero」** 文档页：架构图、结合本游戏讲解 MCTS、
  训练循环走读、结果。
- **「用 Feudal 网络做分层 RL」** 文档页：Manager-Worker 层级、何时/为何有帮助、
  空间特征提取、训练指南。
- 增加逐步交互式 Jupyter notebooks。

> **注意：** AlphaZero 与 Feudal RL 均**已完整实现并测试**（见上文
> 「已完成工作」）。剩余工作是写文档与交互 notebook，使它们可被使用。

### 3.4 训练调试叠加层 ⬚
**优先级：** 中 — 可视化学习辅助。
- 用 `render_mode='human'` 评估训练模型时，显示可选面板：
  - 概率最高的 5 个动作
  - 当前累计奖励
  - 合法动作数量
  - 价值函数估计（若可用）
- 评估中用键盘快捷键切换。

**里程碑：** Phase 3 结束时，项目拥有模型动物园、自回归动作分解贯通 PPO 与
AlphaZero（不仅 feudal）、经 A/B 相对旧 worker 验证、以及高级主题文档。
PPO、Feudal 与 AlphaZero 各自至少有一个训练 checkpoint 登上锦标赛天梯并击败
`AdvancedBot`。

---

## Phase 4：LLM 与基准打磨（4–8 周）

形式化使本项目独特的 RL-vs-LLM 对比。

### 4.1 RL vs LLM 基准套件 ⬚
**优先级：** 中高 — 独特价值主张。
- 定义标准化基准：固定地图、固定起始条件、每对阵 N 局。
- 指标：胜率、平均对局长度、金币效率（每击杀花费金币）、
  单位存活率、结构控制随时间变化。
- 自动化：`python -m reinforcetactics.benchmark run` 产出 JSON 结果文件。
- 在文档站点发布为「战术推理排行榜」。

### 4.2 本地 LLM 支持（Ollama） ⬚
**优先级：** 中 — 消除实验成本门槛。
- 增加 `OllamaBot`（`LLMBot` 子类），对接本地 Ollama 服务器。
- 支持 Llama 3、Mistral 等模型。
- 适合负担不起 API 费用的学生。

### 4.3 LLM 成本跟踪 🟡
**优先级：** 低–中
- 跟踪 token（输入 + 输出）与每局估算费用。
- 记入已有的对话 JSON 文件。
- 增加汇总命令：`python main.py --mode stats --llm-costs`

> **注意：** Token 跟踪已部分实现 — `LLMBot` 已跟踪
> `total_input_tokens` 与 `total_output_tokens`，并有 `get_token_usage()` 方法。
> 剩余工作是按模型估算美元成本与 CLI 汇总命令。

### 4.4 锦标赛 CI 自动化 🟡
**优先级：** 低–中
- 每次 release 运行锦标赛的 GitHub Actions 工作流。
- 将更新后的 ELO 与 RL-vs-LLM 结果发布到文档站点。

> **注意：** CI 基础设施已存在（deploy-docusaurus.yml、python-package.yml、
> pylint.yml），但尚无锦标赛专用自动化。

**里程碑：** Phase 4 结束时，「GPT-5 与 1M 步 PPO agent 在战术推理上如何比较？」
有可量化、可复现的答案。

---

## Phase 5：平台扩展（8+ 周，更长期）

扩大项目覆盖面与研究价值的更大努力。

### 5.1 课程学习系统 🟡
**优先级：** 中 — 使项目可用于课程。
- 将 Phase 2 的渐进环境形式化为 `CurriculumEnv`，当 agent 达到胜率阈值时
  自动提升难度。
- 阶段：6×6 地图 → 10×14 地图 → 20×20 地图；仅战士 → 全部单位；无迷雾 → 战争迷雾。
- 跟踪并可视化跨阶段进度。

> **状态：** 已实现为 bootstrap 阶段运行器
> （`reinforcetactics/rl/bootstrap.py` + `configs/ppo/bootstrap.yaml`）。
> 胜率门控自动晋级已上线；扫描变体在
> `configs/ppo/bootstrap_sweep/`。先前的 `make_curriculum_env()`
> 三预设 API 已移除，改用更丰富的流水线。
>
> **依赖：** 10×14 与 20×20 地图阶段需要先完成 Phase 3.2（自回归动作分解）。
> 没有它，组合动作空间使大地图训练不切实际。

### 5.2 多智能体 RL（3+ 玩家） 🟡
**优先级：** 中 — 打开 MARL 研究。
- 1v1v1 与 2v2 地图已存在，但 `StrategyGameEnv` 硬编码为 2 玩家。
- 扩展为兼容 PettingZoo 的多智能体环境。
- 支持联盟形成、对手建模等研究。

> **注意：** PettingZoo 已列为依赖但尚未使用。2v2 FoW 视角已实现，
> 为多智能体支持打下基础。

### 5.3 基于 Web 的界面 ⬚
**优先级：** 较低 — 工作量最大，覆盖面最广。
- 浏览器版本：使用 Pyodide（浏览器内 Python）或 React 前端 + WebSocket 接
  Python 后端。
- 无头模式已将逻辑与渲染分离，架构支持这一点。
- 让人无需安装即可试用游戏。

### 5.4 音效与音乐 ⬚
**优先级：** 对 RL 使用较低，对游戏打磨较高。
- 在 implementation-status.md 中列为「High Priority」。
- 为战斗、单位创建、结构占领添加音效。
- 背景音乐。
- 对演示与「游戏」体验重要。

> **注意：** 设置基础设施已存在（`settings.py` 中的音频音量配置、
> `settings.sound` 的语言键），但尚无实际音频文件或 `pygame.mixer` 集成。

### 5.5 战役 / 故事模式 ⬚
**优先级：** 较低 — 锦上添花。
- 脚本化场景，通过引导游玩教授游戏机制。
- 可兼作 RL 课程：每个战役任务是一个训练场景。

---

## 可视化时间线

```
Week  1-2   ████ Phase 1: Fix Foundations        [██████████████░░░░░░] 75%
Week  3-6   ████████ Phase 2: Educational         [░░░░░░░░░░░░░░░░░░░░]  0%
Week  7-12  ████████████ Phase 3: RL Depth         [█████░░░░░░░░░░░░░░░] 25%
Week 13-20  ████████████████ Phase 4: LLM Polish   [██░░░░░░░░░░░░░░░░░░] 12%
Week 21+    ████████████████████ Phase 5: Platform  [██░░░░░░░░░░░░░░░░░░] 10%
```

阶段可重叠 — Phase 2 文档可在 Phase 1 修复落地时开始。
阶段内项目可在贡献者之间并行。

---

## 推荐的下一步

基于当前进度，下一步最高影响的工作：

1. **把训练好的 checkpoint 送上锦标赛天梯**（覆盖 PPO 与 Feudal 的 Phase 3.1，
   以及作为扩展的 AlphaZero 训练 notebook）。目前天梯只有 `AdvancedBot` 与 LLM，
   对三个训练器是否真能击败 `AdvancedBot` 毫无信息——而这是项目的头条问题。

2. **Phase 3.7 — 验证 AR worker（A/B vs 旧版 feudal）**。决定 3.2 落地的 AR head
   是否应成为默认。一旦有 feudal 训练脚本，运行成本很低。

3. **Phase 3.5 — 从 `AdvancedBot` 做 BC bootstrap**。本地替代 AlphaStar 的
   基于回放的 SL 预训练；对第 2 步中 AR worker 的热启动特别有用。

4. **Phase 1.2 — 基线训练基准**：Phase 1 最后一项。
   发布参考训练曲线后，用户才能验证自己的运行。

5. **Phase 2.1 — 初学者 RL 环境**：对新人影响最大的单项改动。
   简化的 6×6 环境 + 快速收敛，大幅降低入门门槛。

6. **Phase 2.2 — 核心 RL 文档**：五篇文档页，让现有 RL 基础设施可被使用。
   代码扎实；缺口在文档。

7. **Phase 3.6 — 将 AR head 扩展到 PPO 与 AlphaZero**：收口 3.2 的独立 PPO
   子任务，并让 AlphaZero 扩展到 6×6 之外（其策略头是 3.2 为 feudal 修复的
   同一扁平 `Linear(32·H·W, A·H·W)` 形状）。

8. **Phase 3.3 — AlphaZero 与 Feudal RL 文档**：两种算法均已完整实现并测试，
   但零文档。写这些页面会把已完成的工作呈现出来。

---

## 如何使用本路线图

1. **独立开发者？** 按 Phase 1 → 2 → 3 顺序推进。Phase 2 的每小时影响最高。
2. **小团队？** 一人做 Phase 1 修复，另一人并行开始 Phase 2 文档。
3. **寻找贡献者？** Phase 2 文档页与 Phase 3 示例脚本是很好的首次贡献任务 —
   范围清晰、影响大，且不要求对代码库非常熟悉。
4. **学术用途？** 优先 Phase 2.3（学习路径）— 把项目变成课程模块。
