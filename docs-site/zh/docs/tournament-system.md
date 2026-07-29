---
sidebar_position: 5
id: tournament-system
title: 锦标赛系统
---

# 锦标赛系统

本文档描述 Reinforce Tactics 的锦标赛系统，可用于在不同类型的 Bot 之间运行循环赛。

:::tip
想看锦标赛结果？请查看 [Bot 锦标赛](./tournaments) 页面！
:::

## 概述

锦标赛系统会自动发现并运行以下 Bot 之间的竞赛：
- **SimpleBot**：内置基础规则 Bot（始终包含）
- **MediumBot**：内置改进型规则 Bot，具有高级策略（始终包含）
- **AdvancedBot**：内置高阶 Bot，扩展 MediumBot，具备地图分析、增强单位编成、山脉站位、远程战斗优先级与特殊能力使用（始终包含）
- **MasterBot**：大师级 Bot，扩展 AdvancedBot，具备威胁图、按 HP 升序集火、HQ 狙击优先级与加速跟进行动
- **MixedBot**：仅用于课程训练的 Bot，每个 episode 采样两个内部 Bot 之一（用于 bootstrap 训练，不参与积分榜）
- **LLM Bot**：OpenAI、Claude 与 Gemini Bot（若已配置 API 密钥）
- **Model Bot**：已训练的 Stable-Baselines3 模型（来自 `models/` 目录）

## 快速开始

使用默认设置运行锦标赛：

```bash
python3 scripts/tournament.py
```

这将：
- 使用 `maps/1v1/beginner.csv` 地图
- 发现所有可用 Bot
- 每组对阵运行 4 局（每方 2 局）
- 将结果保存到 `tournament_results/`

## 命令行选项

```bash
python3 scripts/tournament.py [OPTIONS]
```

### 选项

- `--map PATH`：单个地图文件路径（用于向后兼容）
- `--maps PATH [PATH ...]`：评估中使用的地图文件路径列表
- `--map-dir PATH`：从目录加载所有地图（替代逐个列出地图）
- `--map-pool-mode {cycle,random,all}`：地图选择方式：`cycle`（默认）、`random` 或 `all`
- `--models-dir PATH`：包含已训练模型的目录（默认：`models/`）
- `--output-dir PATH`：结果与回放的输出目录（默认：`tournament_results/`）
- `--games-per-side INT`：每组对阵中每方的对局数（默认：2）
- `--max-turns INT`：每局最大回合数（默认：500）
- `--test`：测试模式 - 添加重复的 SimpleBot 用于测试
- `--log-conversations`：启用 LLM 对话日志记录到 JSON 文件
- `--conversation-log-dir PATH`：对话日志目录（默认：`output_dir/llm_conversations/`）
- `--concurrent INT`：并发对局数（默认：1，顺序执行）
- `--no-llm`：跳过 LLM Bot 发现
- `--no-models`：跳过已训练模型 Bot 发现

### 示例

在指定地图上运行锦标赛：
```bash
python3 scripts/tournament.py --map maps/1v1/beginner.csv
```

跨多张地图运行锦标赛：
```bash
python3 scripts/tournament.py --maps maps/1v1/beginner.csv maps/1v1/funnel_point.csv
```

在目录中的所有地图上运行锦标赛：
```bash
python3 scripts/tournament.py --map-dir maps/1v1/ --map-pool-mode all
```

增加每组对阵的对局数：
```bash
python3 scripts/tournament.py --games-per-side 5
```

将结果保存到自定义目录：
```bash
python3 scripts/tournament.py --output-dir my_tournament
```

并发运行对局（不含 LLM Bot）：
```bash
python3 scripts/tournament.py --no-llm --concurrent 4
```

测试锦标赛系统：
```bash
python3 scripts/tournament.py --test --games-per-side 1
```

## Bot 发现

### SimpleBot、MediumBot、AdvancedBot 与 MasterBot
内置脚本 Bot 始终可用，无需配置。

- **SimpleBot**：基础策略，单单位购买与简单目标选择
- **MediumBot**：高级策略，协调攻击与最大化单位生产
- **AdvancedBot**：扩展 MediumBot，具备地图分析、优化单位编成（Warriors 25%、Archers 20%、Mages 15%、Knights 10%、Rogues 10%、Barbarians 8%、Clerics 7%、Sorcerers 5%）、Archer 山脉站位、远程战斗优先级以及特殊能力使用（Mage 麻痹、Cleric 治疗）
- **MasterBot**：扩展 AdvancedBot，具备每回合威胁图（用于撤退格子与 Knight 冲锋落点）、按 HP 升序集火、征服阶段的 HQ 狙击优先级，以及加速跟进（已加速单位在占领/攻击/冲锋后仍可执行第二次行动）

### 随机平局决胜（Stochastic Tiebreak）

所有脚本 Bot 接受可选的 `rng`（`random.Random` 实例）。提供时，Bot 在每个排序 / max / 最优跟踪处用它决胜，使同一场景的两次运行不会产生字节级完全相同的对局。未提供 `rng` 时，Bot 保持确定性。该机制通过 `MixedBot` 传递给其内部 Bot，使课程桥接 Bot 的随机决胜真正生效。

### 课程桥接（MixedBot）

`MixedBot` 不是独立策略——它是训练时的课程桥接。构造时以概率 `p_hard` 采样两个内部 Bot 之一，并在整个 episode 生命周期内将 `take_turn()` 委托给该实例（环境在每次 `reset()` 时重建对手，因此选择实际上每个 episode 重新采样）。通过 `configs/ppo/bootstrap.yaml` 中的 `opponent_kwargs` 配置，例如 `{easy: simple, hard: medium, p_hard: 0.5}` 用于 simple→medium 桥接。

### LLM Bot
在以下条件满足时自动包含：
1. 在 `settings.json` 中配置了 API 密钥
2. 安装了所需包（`openai`、`anthropic` 或 `google-genai`）
3. API 连接测试通过

#### 支持的模型

**OpenAI（默认：gpt-5-mini-2025-08-07）**
- GPT-5：`gpt-5-mini-2025-08-07`（推荐，性价比高）
- GPT-4o 系列：`gpt-4o`、`gpt-4o-mini`
- O 系列：`o1`、`o1-mini`、`o3-mini`

**Anthropic Claude（默认：claude-haiku-4-5-20251001）**
- Claude 4.5：`claude-haiku-4-5-20251001`（推荐）、`claude-sonnet-4-5-20250929`
- Claude 4：`claude-sonnet-4-20250514`
- Claude 3.5：`claude-3-5-sonnet-20241022`、`claude-3-5-haiku-20241022`

**Google Gemini（默认：gemini-2.5-flash）**
- Gemini 2.5：`gemini-2.5-flash`（推荐）
- Gemini 2.0：`gemini-2.0-flash`
- Gemini 1.5：`gemini-1.5-pro`、`gemini-1.5-flash`

在 `settings.json` 中配置 API 密钥：
```json
{
  "llm_api_keys": {
    "openai": "sk-...",
    "anthropic": "sk-ant-...",
    "google": "AIza..."
  }
}
```

你也可以通过设置环境变量或修改 Bot 初始化代码来指定自定义模型。

### Model Bot
自动从 `models/` 目录发现：
1. 将已训练的 `.zip` 模型文件放入 `models/`
2. 模型必须兼容 Stable-Baselines3（PPO、A2C 或 DQN）
3. 模型必须在 Reinforce Tactics 环境上训练

示例模型文件：`models/ppo_best_model.zip`

## 锦标赛格式

### 循环赛结构
每个 Bot 与每个其他 Bot 恰好对战一次。

### 对阵结构
每组对阵包含 `2 × games-per-side` 局：
- Bot A 作为玩家 1 进行 `games-per-side` 局
- Bot B 作为玩家 1 进行 `games-per-side` 局

这可抵消先手优势。

使用 `--games-per-side 2` 的示例：
- 第 1 局：Bot A（P1）vs Bot B（P2）
- 第 2 局：Bot A（P1）vs Bot B（P2）
- 第 3 局：Bot B（P1）vs Bot A（P2）
- 第 4 局：Bot B（P1）vs Bot A（P2）

### 对局执行
- 所有对局以 **无头模式**（不渲染）运行以提高速度
- 每局最多 500 回合（防止无限对局）
- 对局在以下情况结束：
  - 一方获胜（占领敌方 HQ 或消灭所有敌方单位）
  - 达到回合上限（计为平局）

### ELO 评分系统
锦标赛跟踪所有 Bot 的 ELO 评分：
- **起始评分**：所有 Bot 为 1500
- **K 因子**：32（标准国际象棋评分调整）
- 每局结束后根据期望结果与实际结果更新评分
- 最终排名包含 ELO 评分及相对初始评分的变化

## 输出文件

锦标赛生成以下输出：

### `tournament_results/tournament_results.json`
完整锦标赛数据的 JSON 格式：
```json
{
  "timestamp": "2025-12-10T22:09:52.145889",
  "map": "maps/1v1/beginner.csv",
  "games_per_side": 2,
  "rankings": [
    {
      "bot": "SimpleBot",
      "wins": 5,
      "losses": 1,
      "draws": 2,
      "total_games": 8,
      "win_rate": 0.625,
      "elo": 1564,
      "elo_change": 64
    }
  ],
  "matchups": [...],
  "elo_history": {...}
}
```

### `tournament_results/tournament_results.csv`
便于导入电子表格的简单 CSV 格式：
```csv
Bot,Wins,Losses,Draws,Total Games,Win Rate,Elo,Elo Change
SimpleBot,5,1,2,8,0.625,1564,+64
OpenAIBot,3,3,2,8,0.375,1436,-64
```

### `tournament_results/replays/`
每局对局的回放文件：
- 格式：`matchup{N}_game{M}_{BotA}_vs_{BotB}.json`
- 示例：`matchup001_game01_SimpleBot_vs_OpenAIBot.json`
- 可使用游戏的回放系统播放

## ModelBot 集成

`ModelBot` 类允许已训练的 Stable-Baselines3 模型参加锦标赛。

### 创建兼容模型

使用强化学习环境训练模型：

```python
from stable_baselines3 import PPO
from reinforcetactics.rl.gym_env import StrategyGameEnv

# Create environment
env = StrategyGameEnv(map_file="maps/1v1/beginner.csv", opponent="bot", render_mode=None)

# Train model
model = PPO("MultiInputPolicy", env, verbose=1)
model.learn(total_timesteps=100000)

# Save model
model.save("models/my_trained_bot")
```

保存的模型将自动被发现并用于锦标赛。

### 动作转换

ModelBot 自动在以下格式之间转换：
- 模型动作（MultiDiscrete 格式）
- 游戏动作（create_unit、move、attack、seize、heal）

动作格式：`[action_type, unit_type, from_x, from_y, to_x, to_y]`

## 故障排除

### "Need at least 2 bots for a tournament"
- 仅发现了 SimpleBot
- 添加 LLM API 密钥或训练一些模型
- 或使用 `--test` 标志添加重复的 SimpleBot

### LLM Bot 未被发现
- 检查 `settings.json` 中的 API 密钥
- 安装所需包：`pip install openai`（或 `anthropic`、`google-genai`）
- 验证 API 密钥有效且有额度

### Model Bot 未被发现
- 确保 `.zip` 文件位于 `models/` 目录
- 验证模型兼容 Stable-Baselines3
- 检查已安装 `stable-baselines3`：`pip install stable-baselines3`

### 对局以平局结束
- 地图可能过大或防守阵地过强
- 尝试更小的地图或在代码中提高回合上限
- 检查 Bot 逻辑是否足够激进

## 测试

运行测试套件：
```bash
python3 -m pytest tests/test_tournament.py -v
```

快速锦标赛测试：
```bash
python3 scripts/tournament.py --test --games-per-side 1 --output-dir /tmp/test
```

## 架构

### 关键组件

1. **BotDescriptor**：描述 Bot 并知道如何实例化
2. **TournamentRunner**：管理锦标赛执行
3. **TournamentConfig**：锦标赛设置的统一配置
4. **ELO Rating**：带可配置 K 因子的评分系统
5. **TournamentSchedule**：带恢复支持的循环赛排程
6. **ModelBot**：Stable-Baselines3 模型的封装
7. **Bot discovery**：自动检测可用 Bot（内置、LLM、模型）
8. **Results tracking**：胜/负/平统计，支持 CSV/JSON 导出

### 代码结构

```
scripts/
  tournament.py              # Main tournament CLI script
reinforcetactics/
  game/
    bot.py                   # SimpleBot, MediumBot, AdvancedBot, MasterBot, MixedBot
    llm_bot.py               # LLM bot implementations (OpenAI, Claude, Gemini)
    model_bot.py             # ModelBot for trained models
  tournament/
    bots.py                  # Bot descriptors and discovery
    runner.py                # Tournament execution engine
    config.py                # Tournament configuration
    schedule.py              # Round-robin scheduling with resume support
    results.py               # Results tracking and export
    elo.py                   # ELO rating system
tests/
  test_tournament.py         # Tournament system tests
  test_tournament_library.py # Tournament library tests
```

## Docker 锦标赛运行器

更多高级锦标赛功能，请参阅 `docker/tournament/` 中基于 Docker 的锦标赛运行器：

```bash
cd docker/tournament
docker-compose up --build
```

Docker 锦标赛运行器包括：
- **ELO 评分系统**：在整个锦标赛中跟踪 Bot 技能评分
- **并发对局执行**：并行运行多局（可配置 1-32）
- **恢复能力**：从中断处继续锦标赛
- **Google Cloud Storage**：将结果上传到 GCS 以用于云部署
- **多地图锦标赛**：跨多张地图对战，支持按地图配置
- **LLM API 速率限制**：API 调用之间可配置延迟

详见 `docker/tournament/README.md` 了解详细配置选项。

## 未来增强

可能的改进：
- 瑞士轮锦标赛格式
- 实时进度可视化
- 淘汰赛制的锦标赛对阵表
- 交手统计
- 每个 Bot 的性能分析
