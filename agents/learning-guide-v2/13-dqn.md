# 第 13 章　DQN：从动作价值到深度 Q 网络

## 13.1 DQN 解决什么问题

DQN（Deep Q-Network）用神经网络近似最优动作价值：

\[
Q_\theta(s,a)\approx Q^*(s,a)
\]

在离散动作空间中，若能估计每个动作的长期价值，就可以选择：

\[
a_t=\arg\max_a Q_\theta(s_t,a)
\]

DQN 适合动作集合固定且可枚举的离散任务。它不是本项目主线算法，但 `main.py` 暴露了 `--algorithm dqn`，因此必须说明真实兼容边界。

## 13.2 从 Q-learning 开始

表格 Q-learning 更新：

\[
Q(s_t,a_t)\leftarrow Q(s_t,a_t)+\alpha\left[
r_{t+1}+\gamma\max_{a'}Q(s_{t+1},a')-Q(s_t,a_t)
\right]
\]

方括号是 TD 误差。定义目标：

\[
y_t=r_{t+1}+\gamma(1-d_t)\max_{a'}Q_{\theta^-}(s_{t+1},a')
\]

- \(d_t=1\) 表示规则终止；
- \(\theta^-\) 是目标网络参数；
- \(Q_\theta(s_t,a_t)\) 是在线网络当前预测。

DQN 最小化：

\[
L(\theta)=\mathbb{E}\left[(y_t-Q_\theta(s_t,a_t))^2\right]
\]

数字例：奖励 2，\(\gamma=0.9\)，下一状态最大目标 Q 为 5，当前 Q 为 4：

\[
y=2+0.9\times5=6.5,\qquad y-Q=2.5
\]

网络应提高已执行动作的 Q 预测。

## 13.3 经验回放

连续游戏转移高度相关。DQN 把转移存入 replay buffer：

\[
(s_t,a_t,r_{t+1},s_{t+1},d_t)
\]

训练时随机抽取小批。作用：

- 打破相邻样本相关性；
- 同一昂贵转移可重复使用；
- 使数据分布比单条当前轨迹更平滑。

代价是样本来自旧策略。环境和动作语义必须稳定；若 Flat Discrete 索引在每个状态按列表位置重建，索引 17 不具有固定语义，网络学习难度显著增加。

## 13.4 目标网络

若用同一网络同时预测当前 Q 和目标最大 Q，更新目标会随参数同时移动，可能形成正反馈。DQN 使用延迟目标网络 \(\theta^-\)，每隔若干步从在线网络复制或缓慢更新：

\[
\theta^-\leftarrow\theta
\]

这不是让目标绝对正确，而是让优化期间目标变化更慢。

## 13.5 ε-greedy

\[
a_t=
\begin{cases}
\text{随机动作},&\text{概率 }\epsilon\\
\arg\max_aQ_\theta(s_t,a),&\text{概率 }1-\epsilon
\end{cases}
\]

训练早期 \(\epsilon\) 较高以探索，之后衰减。若随机动作不使用合法掩码，探索会浪费在非法动作。Flat Discrete 精确掩码可限制随机索引；普通 SB3 DQN 本身不接受 sb3-contrib MaskablePPO 的掩码接口，因此需要环境保证动作集合或定制策略。

## 13.6 与策略梯度的区别

| DQN | PPO/A2C |
|---|---|
| 输出每个离散动作 Q 值 | 输出动作概率和价值 |
| Off-policy，可重放旧数据 | On-policy，主要用新 rollout |
| ε-greedy 探索 | 随机策略与熵 |
| 只支持 Discrete（SB3 实现） | 支持 Discrete/MultiDiscrete 等 |
| 动作很多时输出头变大 | 结构化分布可拆多头 |

## 13.7 本项目的兼容性事实

当前环境默认：

```text
MultiDiscrete([10, 8, W, H, W, H])
```

SB3 2.9.0 的 DQN 只支持 `spaces.Discrete`。实测构造会抛出断言错误。因此：

```powershell
python main.py --mode train --algorithm dqn
```

在当前默认环境下不是可用训练路径。基础 CLI 创建环境时没有切换 `action_space_type="flat_discrete"`。

Flat Discrete 环境可以构造 DQN：

```python
from stable_baselines3 import DQN
from reinforcetactics.rl.gym_env import StrategyGameEnv

env = StrategyGameEnv(
    map_file="maps/1v1/starter.csv",
    opponent="noop",
    action_space_type="flat_discrete",
    max_flat_actions=128,
)
model = DQN(
    "MultiInputPolicy",
    env,
    buffer_size=10_000,
    learning_starts=1_000,
    batch_size=64,
    device="cpu",
)
```

“可构造”不等于“适合”。动态位置索引、动作上限和对手非平稳仍是实质限制。

## 13.8 为什么项目不以 DQN 为主线

1. 默认动作天然由多个条件字段组成；
2. 小地图 Flat 输出尚可，大地图动作上限迅速增长；
3. Flat 索引的语义随合法列表变化；
4. 自对弈使数据分布和对手同时变化；
5. 项目已建立 MaskablePPO 课程、评估和模型加载工具链。

DQN 仍有教学价值：它清楚展示 value-based、off-policy、经验回放和目标网络。

## 13.9 常见失败

| 现象 | 原因 |
|---|---|
| 构造即报动作空间不支持 | 使用默认 MultiDiscrete |
| Q 值持续增大 | 目标过估计、奖励尺度或终止处理错误 |
| 只选列表前部动作 | Flat 排序偏差、探索不足 |
| replay 中旧动作无法解释 | 动作索引语义不稳定 |
| 训练 loss 降但胜率不升 | 拟合 TD 目标不代表任务策略改善 |

## 13.10 CPU 兼容性验证

```powershell
python agents/learning-guide-v2/tools/smoke_labs.py
```

查看 JSON 中 `action_space_compatibility`：DQN 在 `multi_discrete` 下记录断言失败，在 `flat_discrete` 下记录 `construct_ok`。

## 13.11 本章练习

1. 计算 \(r=1,\gamma=0.99,\max Q^-=8,Q=6\) 时的 TD 目标和误差。
2. 目标网络为什么能提高稳定性？
3. 为什么 Flat Discrete 可构造 DQN 仍不表示它是本项目最佳算法？
4. 当前 `main.py --algorithm dqn` 的具体不兼容点是什么？

