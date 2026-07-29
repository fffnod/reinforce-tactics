> 返回：[指南目录](README.md) · [上一章](17-capstone-projects.md) · [索引](../AGENTS.md)

# 术语表与延伸阅读

本表汇总学习指南中出现的 **中英对照** 术语，按主题分组。符号以正文常见写法为准；细节以对应章节为准。

---

## 1. 强化学习基础

| 中文 | 英文 / 符号 | 白话 |
|------|-------------|------|
| 强化学习 | Reinforcement Learning (RL) | 通过与环境交互、最大化累计奖励来学习 |
| 智能体 | agent | 做决策的程序或策略 |
| 环境 | environment | 游戏规则 + 状态转移 +（常含）对手 |
| 状态 | state \(s\) | 环境完整描述 |
| 观察 | observation \(o\) | 智能体看到的信息（可含战争迷雾） |
| 动作 | action \(a\) | 一次决策输出 |
| 奖励 | reward \(r\) | 即时标量反馈 |
| 回报 | return \(G_t\) | 从 \(t\) 起折扣累计奖励 |
| 折扣因子 | discount \(\gamma\) | 未来奖励的衰减（常 0.99） |
| 轨迹 | trajectory / episode rollout | \(o_0,a_0,r_1,\ldots\) 序列 |
| 策略 | policy \(\pi(a\|o)\) | 观察下如何选动作（可随机） |
| 价值函数 | value function \(V(o)\) | 从观察出发的期望回报 |
| 动作价值 | action-value \(Q(o,a)\) | 在观察下采取动作 \(a\) 的期望回报 |
| 优势 | advantage \(A_t\) | 某动作比「平均水平」好多少 |
| 马尔可夫决策过程 | Markov Decision Process (MDP) | \((S,A,P,R,\gamma)\) 形式化 |
| 转移 | transition \(P\) | \(s,a \mapsto s'\) 的规律 |
| 回合结束 | terminated | 按规则结束（胜/负/和） |
| 截断 | truncated | 外部原因停止（步数上限等） |
| 探索 | exploration | 尝试非常规动作以发现更好策略 |
| 利用 | exploitation | 选当前认为最优的动作 |
| 信用分配 | credit assignment | 哪个动作该对延迟奖励负责 |
| 在策略 | on-policy | 用当前策略采的数据更新（如 PPO） |
| 离策略 | off-policy | 可用行为策略与目标策略不同的数据（如 DQN） |
| 监督学习 | supervised learning | 有标签拟合；对比 RL 常无逐步标签 |
| 行为克隆 | Behavior Cloning (BC) | 模仿专家动作分布的监督式初始化 |

---

## 2. 本项目中的「步」与「回合」

| 中文 | 英文 | 白话 |
|------|------|------|
| 环境步 / 微动作 | env step / micro-action | `StrategyGameEnv.step` 一次调用 |
| 游戏回合 | game turn | 当前玩家操作阶段，以 `end_turn` 结束 |
| 对手回合 | opponent turn | 环境内调用对手 `take_turn()` |
| 合法动作 | legal actions | 规则允许的操作集合 |
| 动作掩码 | action mask | 把非法动作概率压掉的布尔/向量掩码 |
| 平坦离散动作 | flat discrete | 一个整数索引进动作表 |
| 多离散动作 | MultiDiscrete | 多维整数向量（本项目常见六元组） |
| 战争迷雾 | fog of war (FOW) | 只能看见部分地图/单位 |
| 引擎覆盖 | engine_overrides | YAML 覆盖单位数值等经济/规则常量 |

---

## 3. PPO 与训练框架

| 中文 | 英文 / 符号 | 白话 |
|------|-------------|------|
| 近端策略优化 | Proximal Policy Optimization (PPO) | 用 clip 限制策略更新幅度的 Actor-Critic 算法 |
| 可掩码 PPO | MaskablePPO | sb3-contrib 中支持动作掩码的 PPO |
| 演员 | Actor | 策略网络 \(\pi\) |
| 评论家 | Critic | 价值网络 \(V\) |
| 演员—评论家 | Actor-Critic | 二者配合更新 |
| 裁剪 | clip \(\epsilon\) | 限制重要性比率偏离 1 |
| 重要性比率 | probability ratio \(r_t(\theta)\) | 新/旧策略概率比 |
| 广义优势估计 | GAE \(\lambda\) | 多步 TD 折中估计优势 |
| 熵系数 | entropy coefficient | 鼓励探索的损失权重 |
| 学习率 | learning rate | 梯度更新步长 |
| 并行环境数 | `n_envs` | 同时采样的环境副本数 |
| 总时间步 | `total_timesteps` | 训练预算（环境步累计） |
| 检查点 | checkpoint | 保存的模型权重快照 |
| Stable-Baselines3 | SB3 | 常用 RL 算法库 |
| Gymnasium | Gymnasium | 环境 `reset/step` API 标准 |
| 向量化环境 | VecEnv | 并行封装多个 env |
| 回调 | callback | 训练循环中插入评估、保存等逻辑 |

---

## 4. 课程、自对弈与进阶算法

| 中文 | 英文 | 白话 |
|------|------|------|
| 课程学习 | curriculum learning | 由易到难安排任务 |
| Bootstrap 课程 | bootstrap curriculum | 本仓库分阶段升对手/地图的训练管线 |
| 晋级 | promotion | 达胜率等门槛进入下一阶段 |
| 课程停滞 | CurriculumStalled | 阶段预算耗尽仍未晋级时抛出的失败 |
| 混合对手 | MixedBot | 按概率在 easy/hard 规则 Bot 间切换 |
| 自对弈 | self-play | 与自身或历史快照对战以提升 |
| 对手池 | opponent pool | 自对弈中采样的历史策略集合 |
| 封建 / 分层 RL | Feudal RL | Manager 定目标、Worker 执行 |
| 内在奖励 | intrinsic reward | 对达成子目标的额外奖励 |
| AlphaZero | AlphaZero | 策略价值网 + MCTS + 自对弈数据 |
| 蒙特卡洛树搜索 | MCTS | 用模拟扩展的博弈树搜索 |
| PUCT | PUCT | MCTS 选节点时的探索公式族 |
| 热启动 | warm start | 用 BC 等先初始化再 PPO |

---

## 5. 奖励与评估

| 中文 | 英文 | 白话 |
|------|------|------|
| 稀疏奖励 | sparse reward | 只在终局等少数时刻给分 |
| 稠密奖励 | dense reward | 逐步给塑形信号 |
| 奖励塑形 | reward shaping | 手工加中间信号引导学习 |
| 基于势能的塑形 | potential-based shaping | 用势差形式、理论上不改变最优策略（折扣意义下） |
| 奖励配置 | `reward_config` | env 中各项奖励权重字典 |
| 胜率 | win rate | 对指定对手的获胜比例 |
| 埃洛评分 | Elo rating | 用期望胜率模型更新的相对实力分 |
| 评估 | evaluation | 固定协议下测策略，通常不开探索噪声 |
| 威尔逊区间 | Wilson CI | 二项比例置信区间（样本量解释需谨慎） |

---

## 6. 脚本 Bot 与平衡

| 中文 | 英文 | 白话 |
|------|------|------|
| 规则 / 脚本 Bot | scripted bot | 启发式代码，不学权重 |
| 回合合同 | `take_turn` contract | 有限步内行动并 `end_turn` |
| 空操作 Bot | NoopBot | 直接结束回合 |
| 随机 Bot | RandomBot | 随机合法动作 |
| 均衡随机 Bot | BalancedRandomBot | 有限随机，压力随兵力缩放 |
| 简单 / 中级 / 高级 / 大师 | Simple / Medium / Advanced / Master | 递增启发式强度 |
| 随机平局决胜 | stochastic tiebreak | 同分候选 shuffle 后再选 |
| 自杀防护 | suicide guard | 禁止必死且杀不死敌的攻击 |
| 能力遥测 | capability telemetry | 记录启发式触发次数 |
| 单一文化 | monoculture | 购买策略塌缩为单一兵种 |
| 锦标赛 | tournament | 多 Bot 循环赛 |
| 回放 | replay | 对局过程记录文件 |

---

## 7. LLM 与模型 Bot

| 中文 | 英文 | 白话 |
|------|------|------|
| 大语言模型 | Large Language Model (LLM) | 文本生成模型 |
| 提示 / 提示词 | prompt | 送给 LLM 的系统与用户文本 |
| 应用编程接口 | API | 调用云端模型的接口 |
| 解析 | parse | 从模型输出提取 JSON 动作 |
| 温度 | temperature | 采样随机性；高则更发散 |
| 模型 Bot | ModelBot | 加载 SB3/Feudal 等本地权重对战 |
| AlphaZero Bot | AlphaZeroBot | 本地网络 + MCTS 对战 |

---

## 8. 工程与工具

| 中文 | 英文 | 白话 |
|------|------|------|
| 可编辑安装 | editable install (`pip install -e`) | 改源码立即生效的安装方式 |
| 可选依赖 | extras (`[dev]`, `[llm]`, `[gui]`) | pyproject 中分组依赖 |
| 单元测试 | unit test (pytest) | 自动检验函数/模块行为 |
| 覆盖率 | coverage | 测试执行到的代码比例 |
| 静态检查 | lint (ruff) | 风格与常见错误扫描 |
| 类型检查 | type check (mypy) | 静态类型分析 |
| 提交前钩子 | pre-commit | commit 前自动跑检查 |
| 连续集成 | CI | 远端自动测试构建 |
| 种子 | seed | 伪随机数初值，利复现 |
| 确定性 | determinism | 同输入同输出的程度 |

---

## 9. 游戏领域用语（简表）

| 中文 | 英文 | 白话 |
|------|------|------|
| 总部 | headquarters (HQ) | 关键关键建筑；占领敌方 HQ 可胜 |
| 占领 / 夺取 | seize / capture | 对建筑推进占领进度 |
| 单位 | unit | 战士、弓手、骑士等 |
| 金币 / 经济 | gold / economy | 购买单位与收入 |
| 回合制策略 | turn-based strategy | 分回合行动的策略玩法 |
| 克制 | counter | 兵种相生相克关系 |

---

## 10. 延伸阅读

### 10.1 经典与框架（概念级）

| 资源 | 说明 |
|------|------|
| [Sutton & Barto, *Reinforcement Learning: An Introduction*](http://incompleteideas.net/book/the-book-2nd.html) | RL 圣经；先抓直觉与符号，不必一次读完 |
| [Gymnasium 文档](https://gymnasium.farama.org/) | `Env`、`reset`、`step`、spaces 官方说明 |
| [Stable-Baselines3 文档](https://stable-baselines3.readthedocs.io/) | PPO 等算法用法与自定义 env |
| [Spinning Up — PPO](https://spinningup.openai.com/en/latest/algorithms/ppo.html) | OpenAI 对 PPO 的清晰算法说明 |
| [AlphaZero 论文（高层次）](https://www.science.org/doi/10.1126/science.aar6404) | Silver et al., *Mastering Chess and Shogi by Self-Play…*；先读摘要与方法框图即可 |
| [sb3-contrib MaskablePPO](https://sb3-contrib.readthedocs.io/) | 带动作掩码的 PPO 扩展 |

### 10.2 本仓库文档

| 路径 | 说明 |
|------|------|
| [本指南目录](README.md) | 00–17 章学习路径 |
| [`../algorithms/`](../algorithms/) | 算法速查卡 |
| [`../source-analysis/`](../source-analysis/) | 源码分层深潜 |
| [`../usage/local-run-guide.md`](../usage/local-run-guide.md) | 本地运行与短训 |
| [`../usage/git-commit-push.md`](../usage/git-commit-push.md) | 本机 Git 作者与提交 |
| [`../../docs/zh/`](../../docs/zh/) | 中文贡献者笔记（训练日记、平衡教训等） |
| [`../../docs/zh/README.md`](../../docs/zh/README.md) | `docs/zh` 索引 |
| [`../../docs/zh/balance_analysis_lessons_learned.md`](../../docs/zh/balance_analysis_lessons_learned.md) | 平衡分析教训 |
| [`../../docs/zh/bootstrap_lessons_learned.md`](../../docs/zh/bootstrap_lessons_learned.md) | Bootstrap 训练教训 |
| [reinforcetactics.com](https://reinforcetactics.com) | 用户向安装、规则、功能说明 |

### 10.3 明确不在本指南范围

| 主题 | 何处可选阅读 |
|------|----------------|
| Google Cloud / Vertex 云训练 | `docs/vertex_training.md` / `docs/zh/vertex_training.md` |
| 生产级超参扫荡与长时训练运维 | `docs/zh/` 下 REVIEW / bootstrap 笔记 |

---

## 11. 符号速查

| 符号 | 含义 |
|------|------|
| \(s, o, a, r\) | 状态、观察、动作、奖励 |
| \(\pi_\theta\) | 参数为 \(\theta\) 的策略 |
| \(V_\phi\) | 参数为 \(\phi\) 的价值 |
| \(G_t\) | 从 \(t\) 起的折扣回报 |
| \(\gamma\) | 折扣因子 |
| \(A_t\) | 优势 |
| \(r_t(\theta)\) | PPO 重要性比率 |
| \(\epsilon\) | PPO clip 范围 |
| \(\lambda\) | GAE 参数 |

---

返回完整目录：[README.md](README.md) · 知识库索引：[../AGENTS.md](../AGENTS.md)
