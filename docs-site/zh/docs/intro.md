---
sidebar_position: 1
id: intro
title: 欢迎使用 Reinforce Tactics
slug: /
---

# 欢迎使用 Reinforce Tactics

![Reinforce Tactics Logo](/img/logo.svg)

**Reinforce Tactics** 是一款专为强化学习研究与实验打造的模块化回合制策略游戏。本项目将经典战术玩法与现代 RL 能力相结合，为开发与测试强化学习算法提供丰富的环境。

## 🎮 什么是 Reinforce Tactics？

Reinforce Tactics 是一款 2D 回合制策略游戏，具有以下特点：

- **回合制战术玩法**，多种单位类型
- **8 种单位类型**：Warrior、Mage、Cleric、Archer、Knight、Rogue、Sorcerer 与 Barbarian（各有独特能力）
- **战斗系统**，包含攻击、反击、麻痹与治疗
- **经济系统**，通过控制建筑获得收入
- **建筑占领**：塔楼、建筑与总部
- **存档/读档系统**，可继续游戏
- **回放系统**，可观看过往对局
- **AI 对手**：SimpleBot、MediumBot、AdvancedBot、MasterBot 以及由 LLM 驱动的 Bot（GPT、Claude、Gemini）
- **完整的 Gymnasium 集成**，用于 RL 训练
- **无头模式**，可在不渲染的情况下快速训练
- **多种训练算法**：通过 Stable-Baselines3 支持 PPO、A2C、DQN，以及带 MCTS 的 AlphaZero、Feudal RL 和 Behavior Cloning 预热（用于 MaskablePPO）
- **课程训练**：MixedBot 在脚本 Bot 难度层级之间桥接（例如 simple → medium → advanced），实现分阶段对手进阶
- **动作掩码**：MaskablePPO 以及所有 Bot 类型的合法动作掩码
- **自对弈**：让智能体与自身副本对战进行训练
- **战争迷雾**：带地形加成的视线可见性
- **地图编辑器**：用于创建和修改地图的游戏内编辑器
- **多人模式**：1v1、1v1v1（混战）与 2v2（团队）地图
- **锦标赛系统**：带 ELO 评分与 Docker 支持的循环赛
- **精灵动画**：按队伍调色板替换与移动路径过渡
- **多语言**：英语、韩语、西班牙语、法语、中文
- **Docker 支持**，便于部署

## 🤖 为什么选择 Reinforce Tactics？

本项目的设计目标是：

- **研究友好**：模块化架构便于扩展与定制
- **RL 就绪**：标准 Gymnasium 接口，可无缝集成各类 RL 库
- **教育价值**：清晰的代码结构，适合学习 RL 与游戏开发
- **性能出色**：无头模式可在无渲染开销下快速训练

## 🚀 快速入门

### 安装

```bash
# Clone the repository
git clone https://github.com/kuds/reinforce-tactics.git
cd reinforce-tactics

# Basic Installation (core + RL dependencies)
pip install .

# With GUI support
pip install ".[gui]"

# With LLM bot support
pip install ".[llm]"

# Full Installation (all extras)
pip install ".[all]"
```

### 游玩游戏

```bash
python main.py --mode play
```

### 训练 RL 智能体

```bash
python main.py --mode train --algorithm ppo --timesteps 1000000 --opponent bot
```

### 作为 Gymnasium 环境使用

```python
from reinforcetactics.rl.gym_env import StrategyGameEnv

# Create environment
env = StrategyGameEnv(map_file="maps/1v1/beginner.csv", opponent="bot", render_mode=None)

# Standard Gym API
obs, info = env.reset()
action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
```

## 📚 文档结构

本文档分为以下几个部分：

- **入门指南**（本页）：概述与快速入门
- **游戏机制**：单位、战斗系统、建筑与地形
- **Bot 锦标赛**：官方锦标赛结果与分析
- **地图**：可用地图预览与说明
- **锦标赛系统**：运行锦标赛的技术指南
- **实现状态**：项目当前状态与已完成功能

## 🔗 有用链接

- [GitHub 仓库](https://github.com/kuds/reinforce-tactics)
- [主 README](https://github.com/kuds/reinforce-tactics#readme)
- [问题反馈](https://github.com/kuds/reinforce-tactics/issues)
- [许可证（Apache 2.0）](https://github.com/kuds/reinforce-tactics/blob/main/LICENSE)

## 💡 贡献

欢迎贡献！无论你感兴趣的是：
- 改进 RL 算法
- 添加新单位类型或游戏机制
- 完善文档
- 修复 Bug

欢迎在 GitHub 上提交 issue 或 pull request。

## 📜 许可证

本项目采用 Apache License 2.0 授权——欢迎使用与修改！
