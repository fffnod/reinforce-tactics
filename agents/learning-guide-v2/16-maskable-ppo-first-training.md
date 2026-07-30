# 第 16 章　MaskablePPO 与第一次可验证训练

## 16.1 MaskablePPO 改变什么

MaskablePPO 保留 PPO 的 rollout、GAE 和裁剪更新，只把策略分布限制在合法动作上。它解决的是“动作合法性”，不是奖励、观察或信用分配。

对合法集合 \(\mathcal{A}(s)\)：

\[
\pi'(a|s)=
\begin{cases}
\dfrac{\pi(a|s)}{\sum_{b\in\mathcal{A}(s)}\pi(b|s)},
&a\in\mathcal{A}(s)\\
0,&a\notin\mathcal{A}(s)
\end{cases}
\]

合法动作重新归一化，策略梯度只在可执行选择之间比较。

## 16.2 环境构造

推荐从小地图、noop 对手、Flat Discrete 开始验证：

```python
from reinforcetactics.rl.masking import make_maskable_env

env = make_maskable_env(
    map_file="maps/1v1/starter.csv",
    opponent="noop",
    action_space_type="flat_discrete",
    max_flat_actions=128,
    max_steps=32,
)
```

Flat 模式使掩码精确。noop 对手只用于接口与冷启动检查，不代表合理长期教师。

## 16.3 模型构造

```python
from sb3_contrib import MaskablePPO

model = MaskablePPO(
    "MultiInputPolicy",
    env,
    learning_rate=3e-4,
    n_steps=32,
    batch_size=32,
    n_epochs=1,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    seed=42,
    device="cpu",
    verbose=1,
)
```

这里的数值专为 64 步冒烟。生产配置通常使用更大 rollout、更多 epoch、并行环境和空间特征提取器。

## 16.4 训练与预测

```python
model.learn(total_timesteps=64)

obs, info = env.reset(seed=43)
mask = env.action_masks()
action, _ = model.predict(
    obs,
    action_masks=mask,
    deterministic=True,
)
obs, reward, terminated, truncated, info = env.step(action)
```

若忘记 `action_masks`，`predict` 不知道当前合法集合。训练 callback 也应使用 MaskablePPO 专用评估逻辑。

## 16.5 可直接运行的 CPU 冒烟

```powershell
python agents/learning-guide-v2/tools/smoke_labs.py
```

脚本会：

1. 构造 MultiDiscrete 与 Flat 环境；
2. 验证 PPO、A2C、DQN、MaskablePPO 的空间兼容性；
3. 比较逐维掩码组合数与领域合法动作数；
4. 运行 64 步 Flat MaskablePPO；
5. 运行两次模拟的 MCTS 接口检查；
6. 写出 `assets/data/smoke-results.json`。

成功标准是脚本退出码 0、数值有限、预测动作可执行。不是胜率标准。

## 16.6 第一次正式训练应怎样定义

第一次训练的合理验收分三层：

### 管线层

- 环境、模型和 callback 能创建；
- rollout 完成；
- 无 NaN、动作越界或掩码全空；
- checkpoint 与日志产生。

### 学习信号层

- episode 回报存在方差；
- 动作分布不是只剩 `end_turn`；
- value loss 有限；
- 终局原因不全为相同截断。

### 能力层

- 固定对手和地图上胜率高于随机波动；
- 多种子方向一致；
- 回放显示目标行为；
- 对未用于训练的固定锚仍有效。

64 步只覆盖第一层。

## 16.7 为什么不是直接运行基础 CLI

`main.py --algorithm ppo` 构造普通 `stable_baselines3.PPO`，不使用 MaskablePPO 工厂。因此教学主线显式使用 `sb3_contrib.MaskablePPO` 或 Bootstrap 脚本。

基础 CLI 仍可用于说明 SB3 接口，但不应作为本项目复杂动作空间的推荐长训命令。

## 16.8 MultiDiscrete 与 Flat 选择

| 项目 | MultiDiscrete | Flat Discrete |
|---|---|---|
| 输出 | 六个分类头 | 一个索引头 |
| 掩码 | 逐维过度近似 | 完整动作精确 |
| 跨地图 | 维度随 W/H 变化 | 固定上限可统一 |
| 大地图 | 头较紧凑 | 上限可能很大 |
| 动作语义 | 字段稳定 | 索引位置动态 |

初学实操先用 Flat 验证合法性；研究大地图时应评估自回归或合法动作评分网络。

## 16.9 向量环境注意

SubprocVecEnv 在子进程中计算掩码，环境类必须原生实现 `action_masks`。不能把只存在主进程的闭包当作唯一掩码来源。

评估环境必须复用训练时的：

- 动作空间类型和上限；
- 地图 padding；
- 特征提取器；
- enabled units；
- gamma 与奖励配置；
- 对手参数与最大回合。

## 16.10 失败诊断

| 现象 | 优先检查 |
|---|---|
| `ValueError` 无合法动作 | `end_turn` 掩码与领域合法动作 |
| 训练合法、评估非法 | 评估漏传掩码 |
| Flat 索引越界 | `_current_actions` 重建时序与上限 |
| 只结束回合 | 奖励、对手、探索、动作列表排序 |
| 小图可训、大图加载失败 | observation/action shape 与 padding |
| 回报涨、胜率 0 | 奖励分解和终局原因 |

## 16.11 结果记录模板

```text
提交：
环境版本：
地图 / 对手：
动作空间 / 上限：
观察提取器：
奖励配置哈希：
PPO 超参数：
训练种子：
总步数与运行时间：
评估地图 / 对手 / 局数 / 座次：
胜负和、置信区间、终局原因：
回放结论：
```

## 16.12 本章练习

1. MaskablePPO 相比 PPO 改变了哪个概率分布？
2. 为什么 64 步冒烟不能说明模型会赢？
3. 为什么训练和评估环境的 `max_flat_actions` 必须一致？
4. 设计三个从“管线可运行”到“能力有效”的递进验收条件。

