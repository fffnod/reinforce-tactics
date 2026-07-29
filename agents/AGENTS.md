# Agents 项目知识索引

本目录存放面向开发者 / AI 助手的**长期知识库**：把对话与排查中沉淀的重要信息分类成文，避免全部堆在单一文件里。

**维护约定**

1. **本文件（`agents/AGENTS.md`）只做索引与概述**，不写长文。
2. 详细内容写在同目录（或子目录）的独立 Markdown 中。
3. 新增记录时：先在本索引登记「路径 + 概述」，再写正文。
4. 修改记录时：按索引找到对应文件，改完后如概述变化则同步更新本表。
5. 文中路径默认相对仓库根目录 `reinforce-tactics/`。

---

## 文档分类

| 分类 | 子目录 / 前缀 | 用途 |
|------|----------------|------|
| **使用类** | `usage/` | 安装、启动、GUI 操作、训练命令、部署迁移等「怎么用」 |
| **问题排查类** | `troubleshooting/` | 故障现象、根因、修复步骤、验证方法 |
| **源代码分析类** | `source-analysis/` | 模块结构、关键调用链、设计取舍 |
| **智能算法分析类** | `algorithms/` | RL 算法、奖励、对手体系、训练管线分析 |

---

## 索引表

### 使用类（usage）

| 文件 | 概述 | 状态 |
|------|------|------|
| [`usage/git-commit-push.md`](usage/git-commit-push.md) | **必读**：本机无 git author 时如何用环境变量提交；pre-commit 失败重试；origin/分支；commit message 风格 | 已写 |
| [`usage/local-run-guide.md`](usage/local-run-guide.md) | Windows + Conda 下如何激活环境、启动 GUI、配置人机/AI、进行简单 PPO 训练与评估 | 已写 |
| [`usage/chinese-i18n-coverage.md`](usage/chinese-i18n-coverage.md) | 中文汉化覆盖范围：单位行动/购买/HUD/设置/地图编辑器；如何继续补词条 | 已写 |
| [`../docs/LOCAL_DEPLOY.md`](../docs/LOCAL_DEPLOY.md) | 完整本地部署说明（在线/离线包、一键脚本、迁移）；偏工程部署 | 已写（在 `docs/`） |
| [`../deploy/README.md`](../deploy/README.md) | 一键安装 / 离线打包脚本索引 | 已写（在 `deploy/`） |

### 问题排查类（troubleshooting）

| 文件 | 概述 | 状态 |
|------|------|------|
| [`troubleshooting/chinese-font-display.md`](troubleshooting/chinese-font-display.md) | 切换中文后菜单乱码/方框：pygame-ce Windows SysFont 崩溃、改为直读 `msyh.ttc` 等字体文件的原因与修复 | 已写 |

### 源代码分析类（source-analysis）

| 文件 | 概述 | 状态 |
|------|------|------|
| [`source-analysis/overview.md`](source-analysis/overview.md) | 源码分层总览、主控制流、分文档索引 | 已写 |
| [`source-analysis/entrypoints-and-cli.md`](source-analysis/entrypoints-and-cli.md) | `main.py` 与 CLI 四模式 train/evaluate/play/stats | 已写 |
| [`source-analysis/core-game-engine.md`](source-analysis/core-game-engine.md) | `GameState` SSOT、合法动作、end_turn、胜负、engine_overrides | 已写 |
| [`source-analysis/app-runtime.md`](source-analysis/app-runtime.md) | GUI 会话、InputHandler、Bot 工厂、人机回合 | 已写 |
| [`source-analysis/game-bots.md`](source-analysis/game-bots.md) | 规则 Bot 层级、MixedBot 课程桥、rng 决胜 | 已写 |
| [`source-analysis/game-llm-and-model-bots.md`](source-analysis/game-llm-and-model-bots.md) | LLM / ModelBot(.zip·.pt) / AlphaZeroBot | 已写 |
| [`source-analysis/rl-gym-env.md`](source-analysis/rl-gym-env.md) | `StrategyGameEnv`、六维/flat 动作、观察、掩码、势函数奖励、`step` 流程 | 已写 |
| [`source-analysis/rl-training-pipelines.md`](source-analysis/rl-training-pipelines.md) | Bootstrap 课程、自对弈、config、回调、评估、CLI train ↔ SB3 | 已写 |
| [`source-analysis/rl-advanced-trainers.md`](source-analysis/rl-advanced-trainers.md) | Feudal Manager/Worker/AR、AlphaZero、MCTS、BC、特征提取器 | 已写 |
| [`source-analysis/tournament-system.md`](source-analysis/tournament-system.md) | 循环赛调度、Bot 发现、Elo、`scripts/tournament.py` | 已写 |
| [`source-analysis/ui-and-menus.md`](source-analysis/ui-and-menus.md) | 菜单树、Renderer/widgets 高层导航 | 已写 |
| [`source-analysis/utils-infra.md`](source-analysis/utils-infra.md) | 设置、i18n、字体、FileIO、回放 schema、无头视频 | 已写 |
| [`source-analysis/scripts-configs-maps.md`](source-analysis/scripts-configs-maps.md) | 训练脚本、configs/maps 布局、脚本→算法文档表 | 已写 |

### 智能算法分析类（algorithms）

| 文件 | 概述 | 状态 |
|------|------|------|
| [`algorithms/overview.md`](algorithms/overview.md) | RL 零基础总览、算法地图、推荐学习顺序 | 已写 |
| [`algorithms/mdp-gymnasium-basics.md`](algorithms/mdp-gymnasium-basics.md) | MDP、回报 \(G_t\)、Gymnasium `reset/step`、terminated vs truncated | 已写 |
| [`algorithms/ppo.md`](algorithms/ppo.md) | 策略梯度、Actor-Critic、PPO clip、GAE；SB3 / MaskablePPO | 已写 |
| [`algorithms/action-masking.md`](algorithms/action-masking.md) | 非法动作、per-dim vs flat 掩码、AR 头 | 已写 |
| [`algorithms/reward-shaping.md`](algorithms/reward-shaping.md) | 稀疏/稠密、势能塑形、杀敌刷分陷阱 | 已写 |
| [`algorithms/curriculum-bootstrap.md`](algorithms/curriculum-bootstrap.md) | 课程阶段、晋级、patience、MixedBot、CurriculumStalled | 已写 |
| [`algorithms/self-play.md`](algorithms/self-play.md) | 自对弈、对手池、`set_self_play_opponent_factory` | 已写 |
| [`algorithms/behavior-cloning.md`](algorithms/behavior-cloning.md) | 行为克隆、BC→PPO、演示重复轨迹问题 | 已写 |
| [`algorithms/feudal-rl.md`](algorithms/feudal-rl.md) | Manager/Worker、内在奖励、段 GAE | 已写 |
| [`algorithms/alphazero-mcts.md`](algorithms/alphazero-mcts.md) | MCTS/PUCT、策略价值网、自对弈数据 | 已写 |
| [`algorithms/evaluation-and-elo.md`](algorithms/evaluation-and-elo.md) | 胜率噪声、Elo 期望与更新 | 已写 |

---

## 本地环境快照（便于续写）

| 项 | 值 |
|----|-----|
| Fork / `origin` | `https://github.com/fffnod/reinforce-tactics` |
| 上游 / `upstream` | `https://github.com/kuds/reinforce-tactics` |
| 开发分支 | `feature/local-deploy` |
| Conda 环境名 | `reinforce-tactics`（Python 3.12） |
| 已装 extras | `base` + `gui` + `llm` + `dev`（**未装** `cloud`） |
| PyTorch | CPU 版（`cuda=False`） |
| 项目路径（源机） | `D:\Grok\project2\reinforce-tactics` |
| Git 作者（提交用） | `fffnod <33726281+fffnod@users.noreply.github.com>`（**仅 env，勿改 global**；详见 [`usage/git-commit-push.md`](usage/git-commit-push.md)） |

更细的部署与离线包说明见 `docs/LOCAL_DEPLOY.md`。

### AI 助手开场应加载的约定

1. 读本索引；按任务打开对应子文档。
2. 任何 **git commit / push**：先读 [`usage/git-commit-push.md`](usage/git-commit-push.md)，用环境变量设置 author，确认 commit 成功后再 push。
3. 本地运行 / 训练：[`usage/local-run-guide.md`](usage/local-run-guide.md)。
4. 中文 UI / 字体：[`usage/chinese-i18n-coverage.md`](usage/chinese-i18n-coverage.md)、[`troubleshooting/chinese-font-display.md`](troubleshooting/chinese-font-display.md)。
5. **熟悉架构 / 读代码**：从 [`source-analysis/overview.md`](source-analysis/overview.md) 进入。
6. **学 RL 概念**：从 [`algorithms/overview.md`](algorithms/overview.md) 进入（零基础友好）。

---

## 推荐阅读路径

| 目标 | 顺序 |
|------|------|
| 建立项目整体概念 | [`source-analysis/overview.md`](source-analysis/overview.md) → core → app 或 bots → rl-gym-env |
| 从零学本项目 RL | [`algorithms/overview.md`](algorithms/overview.md) → mdp → ppo → masking → reward → curriculum |
| 进阶训练器 | feudal / alphazero 算法文 + [`source-analysis/rl-advanced-trainers.md`](source-analysis/rl-advanced-trainers.md) |
| 评测梯子 | [`algorithms/evaluation-and-elo.md`](algorithms/evaluation-and-elo.md) + [`source-analysis/tournament-system.md`](source-analysis/tournament-system.md) |

链接一律使用**相对路径**（可在目录间移动后仍可跳转）。源码文与算法文双向链接；复杂逻辑含 Mermaid 流程图。

---

## 建议的后续条目（尚未成文）

- 使用类：LLM Bot API Key 配置与菜单路径
- 使用类：离线包在目标机的验收清单
- 排查：训练产物目录与 `.gitignore` 关系
