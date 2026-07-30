# 基于 Reinforce Tactics 的策略类强化学习学习指南

> 第二版完整教材。面向具有编程基础、但没有强化学习和高等数学背景的读者。

本书从一局回合制策略游戏开始，依次建立概率、梯度、价值函数和策略优化的基础，再进入 Gymnasium、PyTorch、Stable-Baselines3 以及本项目的真实代码。PPO、MaskablePPO、DQN、A2C、课程学习、行为克隆、自对弈、Feudal RL、MCTS 和 AlphaZero 均有独立章节。作者长期训练过程中出现的动作掩码失真、奖励投机、课程漂移、评估噪声和行为克隆数据退化，也被重写为可复用的研究案例。

## 阅读基准

| 项目 | 本书验证环境 |
|---|---|
| 仓库基准 | `69a085d` 附近，2026-07-29 |
| Python | 3.12.13 |
| Gymnasium | 1.3.0 |
| Stable-Baselines3 | 2.9.0 |
| sb3-contrib | 2.9.0 |
| PyTorch | 2.13.0 CPU |
| 操作系统 | Windows + PowerShell + Conda |

项目依赖没有锁定精确版本，因此未来安装得到的新版本可能在警告文本、默认参数或输出格式上有所变化。本书把“算法原理”“项目当前实现”和“本机验证结果”明确分开；前两者可长期阅读，第三者用于复现实验。

## 五篇阅读路线

1. **第一篇（00-05）**：游戏、MDP、概率、梯度与强化学习基础。
2. **第二篇（06-12）**：PyTorch、Gymnasium、SB3 和项目环境实现。
3. **第三篇（13-16）**：DQN、A2C、PPO 与 MaskablePPO。
4. **第四篇（17-22）**：课程、模仿、自对弈、Feudal、MCTS、AlphaZero。
5. **第五篇（23-27）**：实验方法、Bot、Elo、LLM 与工程实践。

若只想先跑通一条训练线，可以按 `00 → 01 → 02 → 05 → 07 → 09 → 10 → 11 → 12 → 15 → 16 → 23` 阅读。完整学习建议严格按编号推进。

## 本书如何做到自包含

- 数学概念在正文内从定义讲起，不要求打开外部教材。
- 关键源码以精简片段、伪代码和数据流图解释；路径只用于核验。
- 历史实验结论在对应章节给出证据和推理过程；附录 C 提供完整索引。
- 所有截图、图表、短实验结果和最小配置均保存在本目录。
- 论文与框架文档仅作出处引用，不代替正文解释。

## 目录

### 第一篇　从策略游戏进入强化学习

- [00　序言、学习目标与实践路线](00-preface-and-roadmap.md)
- [01　游戏规则与策略问题](01-game-rules-and-strategy.md)
- [02　智能体、环境与 MDP](02-agent-environment-and-mdp.md)
- [03　概率与统计基础](03-probability-and-statistics.md)
- [04　微积分、梯度与神经网络](04-calculus-and-neural-networks.md)
- [05　强化学习基础](05-rl-foundations.md)

### 第二篇　框架与项目实现

- [06　用于强化学习的 PyTorch](06-pytorch-for-rl.md)
- [07　Gymnasium 环境契约](07-gymnasium-contract.md)
- [08　Stable-Baselines3 训练框架](08-sb3-training-framework.md)
- [09　项目运行时与数据流](09-project-runtime-and-dataflow.md)
- [10　观察编码与空间特征](10-observation-and-spatial-features.md)
- [11　动作空间与动作掩码](11-action-space-and-masking.md)
- [12　奖励塑形、终止与截断](12-reward-shaping-and-termination.md)

### 第三篇　基础算法专章

- [13　DQN](13-dqn.md)
- [14　A2C](14-a2c.md)
- [15　PPO](15-ppo.md)
- [16　MaskablePPO 与第一次训练](16-maskable-ppo-first-training.md)

### 第四篇　训练策略与进阶算法

- [17　课程学习与 Bootstrap](17-curriculum-bootstrap.md)
- [18　行为克隆](18-behavior-cloning.md)
- [19　自对弈](19-self-play.md)
- [20　Feudal RL](20-feudal-rl.md)
- [21　蒙特卡洛树搜索](21-mcts.md)
- [22　AlphaZero](22-alphazero.md)

### 第五篇　研究、评估与工程实践

- [23　实验设计与可复现性](23-experiment-design.md)
- [24　规则 Bot 与平衡分析](24-scripted-bots-and-balance.md)
- [25　评估、Elo 与锦标赛](25-evaluation-elo-tournament.md)
- [26　LLM Bot](26-llm-bots.md)
- [27　开发工作流与综合实践](27-dev-workflow-and-capstone.md)

### 附录

- [附录 A　符号与术语](appendix-a-symbols-and-glossary.md)
- [附录 B　命令与参数](appendix-b-commands-and-parameters.md)
- [附录 C　实验编年索引](appendix-c-experiment-chronology.md)
- [附录 D　练习参考答案](appendix-d-exercise-answers.md)
- [附录 E　源码索引与参考文献](appendix-e-source-index-and-bibliography.md)

## 实操约定

所有命令均从仓库根目录执行：

```powershell
cd D:\Grok\project2\reinforce-tactics
conda activate reinforce-tactics
python -c "import gymnasium, stable_baselines3, sb3_contrib, torch; print('environment ready')"
```

带有“CPU 冒烟实验”标记的命令只验证数据流和接口，不证明模型已经学会策略。需要数十万乃至数百万步的结论，正文会明确标记为“历史长训结果”，并说明数据出处与局限。

## 连续阅读版本

- HTML：[`export/Reinforce-Tactics-RL-Learning-Guide.html`](export/Reinforce-Tactics-RL-Learning-Guide.html)
- PDF：[`../../output/pdf/Reinforce-Tactics-RL-Learning-Guide-v2.pdf`](../../output/pdf/Reinforce-Tactics-RL-Learning-Guide-v2.pdf)
- 验证记录与八项覆盖矩阵：[`VALIDATION.md`](VALIDATION.md)

重新生成：

```powershell
conda activate reinforce-tactics
python agents/learning-guide-v2/tools/generate_figures.py
python agents/learning-guide-v2/tools/build_book.py
python agents/learning-guide-v2/tools/verify_book.py
```

PDF 由同一份 self-contained HTML 通过 Chromium/Edge 排版生成，因此 MathML 公式会保留真正的上下标、分式和根号。构建器会自动查找 Chrome 或 Edge；若浏览器位于其他位置，可设置 `GUIDE_BROWSER`。PDF 构建还需要 Node.js 与 Playwright，Codex 工作区运行时已经提供这两项依赖。

## 范围边界

本书讨论项目中的本地游戏、RL、LLM Bot 和开发工具链，不涉及 Vertex AI、GCS 或其他 Cloud 训练部署。LLM 章节使用 mock 测试和静态示例，不调用付费 API。
