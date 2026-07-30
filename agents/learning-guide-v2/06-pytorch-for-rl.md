# 第 06 章　用于强化学习的 PyTorch

## 6.1 张量与形状

PyTorch 的核心对象是 `torch.Tensor`。张量同时保存数值、数据类型、设备和可选梯度信息。

```python
import torch

x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
print(x.shape)   # torch.Size([2, 2])
print(x.dtype)   # torch.float32
print(x.device)  # cpu
```

强化学习中最常见的错误不是公式，而是形状：

- 环境返回 `(H,W,C)`，CNN 需要 `(B,C,H,W)`；
- 单个动作是 `(6,)`，批动作是 `(B,6)`；
- 布尔掩码长度必须与对应 logits 完全一致；
- 价值输出通常是 `(B,1)`，优势可能是 `(B,)`。

项目特征提取器会把批维和通道维整理为卷积所需格式。阅读 `permute`、`reshape`、`unsqueeze` 时，应在注释旁写出变换前后的形状。

## 6.2 自动求导

```python
x = torch.tensor(3.0, requires_grad=True)
y = x**2
y.backward()
print(x.grad)  # 6
```

PyTorch 在前向计算时记录运算图；`backward()` 从输出向参数应用链式法则。只有参与图且 `requires_grad=True` 的叶张量会积累梯度。

梯度默认累积，因此训练循环必须在每次更新前清零：

```python
optimizer.zero_grad()
loss.backward()
optimizer.step()
```

忘记清零会把多批梯度意外相加；在有意做梯度累积时才保留。

## 6.3 `nn.Module`

网络继承 `torch.nn.Module`：

```python
from torch import nn

class ValueNet(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
        )

    def forward(self, x):
        return self.net(x)
```

`model.parameters()` 返回优化器要更新的参数；`state_dict()` 保存具名权重。checkpoint 若只保存 `state_dict`，可能遗漏优化器、训练步数、地图尺寸和架构超参数。本项目的 Feudal 与 AlphaZero checkpoint 因此还要保存 hyperparameters 和训练状态。

## 6.4 训练模式与评估模式

```python
model.train()
# 更新参数

model.eval()
with torch.no_grad():
    prediction = model(x)
```

`eval()` 会改变 dropout、batch normalization 等层的行为；`torch.no_grad()` 则关闭梯度记录以减少内存。二者作用不同，评估时通常都需要。

## 6.5 优化器

Adam 为每个参数维护一阶和二阶矩估计，常用于深度强化学习：

```python
optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
```

学习率仍是最重要的尺度之一。PPO 一次 rollout 会重复训练多个 epoch；学习率、epoch 数、batch size 和 clip range共同决定一次采样数据引起多大变化。

梯度裁剪：

```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
```

它限制整体梯度范数，缓解异常批次造成的巨大更新，但不能修复错误奖励尺度或 NaN 输入。

## 6.6 概率分布

离散策略常用 `torch.distributions.Categorical`：

```python
from torch.distributions import Categorical

logits = torch.tensor([[2.0, 1.0, 0.0]])
dist = Categorical(logits=logits)
action = dist.sample()
log_prob = dist.log_prob(action)
entropy = dist.entropy()
```

PPO 需要保存旧策略对已执行动作的 `log_prob`，更新时再用新策略计算同一动作的 `log_prob`。二者相减后取指数即可得到概率比：

\[
\frac{\pi_{\mathrm{new}}(a|s)}{\pi_{\mathrm{old}}(a|s)}
=\exp(\log\pi_{\mathrm{new}}-\log\pi_{\mathrm{old}})
\]

## 6.7 动作掩码在 logits 层生效

非法动作应在 softmax 前赋极小 logit：

```python
masked_logits = logits.masked_fill(~mask, -1e8)
dist = Categorical(logits=masked_logits)
```

这样非法动作概率近似为 0，合法动作重新归一化。若所有掩码均为 False，分布没有可选动作，因此项目保证 `end_turn` 始终可用。

逐维 MultiDiscrete 会为六个维度创建六个独立分布。即使每个维度值合法，组合仍可能非法；这是第十一章的核心问题。

## 6.8 项目的空间特征提取

`reinforcetactics/rl/extractors.py` 中的 `SpatialFeatureExtractor` 接收：

- `grid`：地形、建筑和归属通道；
- `units`：单位类型、归属、生命和状态通道；
- `global_features`：金币、回合和单位数量等摘要。

空间通道拼接后转为 `(B,C,H,W)`，经多层卷积提取局部关系。可选设计包括：

- `coord_conv`：加入归一化横纵坐标，使网络区分绝对位置；
- `extra_conv`：扩大感受野；
- `masked_avg`：跨地图 padding 时忽略填充格；
- 固定 `features_dim`：向策略和价值头提供稳定维度。

普通平均池化在 6×6 地图填充到 10×12 时，会把大量零填充纳入平均。掩码平均只统计真实地图区域，减少阶段切换造成的尺度变化。

## 6.9 数值稳定性

需要重点监控：

- logits 是否出现 `inf` 或 `nan`；
- value loss 是否被大终局奖励放大；
- `log(0)` 是否通过稳定分布实现避免；
- 观察是否归一化到合理范围；
- 掩码后是否至少有一个动作；
- 梯度范数是否持续撞上裁剪上限。

项目全局特征使用缩放和 `tanh`，避免金币数千而单位数量个位数造成输入尺度悬殊。归一化是表示设计的一部分，不是单纯“让网络更快”。

## 6.10 CPU 冒烟

```powershell
python -c "import torch; from reinforcetactics.rl.extractors import SpatialFeatureExtractor; print(torch.__version__, torch.cuda.is_available())"
```

本书基准输出为 CPU 版本且 `cuda=False`。所有短实验应显式允许 CPU；生产长训才需要结合硬件选择批大小和并行环境数。

## 6.11 本章练习

1. `(8,10,12,32)` 若代表 `(B,H,W,C)`，怎样变成 CNN 常用形状？
2. `model.eval()` 与 `torch.no_grad()` 有何不同？
3. 为什么梯度裁剪不能修复奖励正负号错误？
4. 为什么跨地图 padding 时掩码平均优于普通平均？

