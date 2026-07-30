# 第 10 章　观察编码与空间特征

## 10.1 观察设计决定可学信息

神经网络只能使用观察中出现的信息。奖励再合理、算法再先进，也无法弥补关键状态缺失。反过来，把无关或泄漏的信息加入观察，会让训练指标虚高、部署失败。

项目观察为字典：

\[
o_t=\{\text{grid},\text{units},\text{global\_features},[\text{visibility}]\}
\]

字典观察允许分别处理空间平面和全局向量。

## 10.2 `grid`

`grid` 的形状为：

```text
(H, W, GRID_CHANNELS)
```

通道表达地形、建筑类别、相对归属和结构生命等。使用 one-hot 或归一化通道而不是把所有类别压成一个整数，有两个优点：

- 数字大小不暗示不存在的顺序关系；
- 卷积可以分别学习“水域”“总部”“敌方归属”等检测器。

若用地形编号 1、2、3，网络会把编号 3 当作比 1“大”；one-hot 不引入这种错误几何。

## 10.3 `units`

`units` 也是 `(H,W,C)`，包含：

- 单位类型 one-hot；
- 自己/对手相对归属；
- 是否已行动；
- 生命比例；
- 麻痹、加速、防御和攻击增益等状态。

“是否已行动”是马尔可夫状态的重要部分。若只编码单位位置和类型，相同画面下合法动作可能不同。

## 10.4 `global_features`

五维全局摘要包括双方金币、回合与双方单位数。原始数值量级差异很大，因此构造观察时按 `gold_scale`、`turn_scale` 和 `unit_count_scale` 缩放，再通过 `tanh` 映射到稳定范围。

例如金币特征可写为：

\[
x_{\mathrm{gold}}=\tanh\left(\frac{\mathrm{gold}}{c_{\mathrm{gold}}}\right)
\]

若缩放常数为 1000，金币 100 的输入约 0.10，金币 5000 接近饱和。缩放常数应覆盖课程中的典型经济范围；太小会让大量状态挤在 1 附近，太大则差异过小。

## 10.5 玩家相对视角

观察不是固定用“玩家 1/玩家 2”通道，而是“自己/对手”。这使同一策略可以控制不同座次：

```text
绝对 player 1 / player 2
          ↓ perspective_player
相对 self / opponent
```

自对弈翻转视角时，还要交换金币、归属、可见性和当前玩家含义。只交换单位 owner 而不交换全局特征会产生内部矛盾。

## 10.6 战争迷雾

启用 `fog_of_war` 后增加可见性平面，并隐藏不可见敌军。需要同时检查：

- 隐藏单位是否从 `units` 移除；
- 合法动作是否泄漏隐藏目标；
- LLM 序列化是否泄漏；
- 自对弈翻转后是否用正确玩家可见性；
- `info` 中的诊断是否被策略误用。

普通无记忆策略面对同一观察无法区分不同隐藏局面。若研究战争迷雾，应考虑循环策略、观察历史或信念建模，而不是只打开布尔开关后沿用所有结论。

## 10.7 跨地图 padding

同一个神经网络要求固定输入形状。课程从 6×6 到 10×12 时，可把小地图补零到最大尺寸：

```text
真实 6×6 区域 + 其余 padding
```

`pad_to_size=(pad_h,pad_w)` 不能小于当前地图。当前实现只对 Flat Discrete 模式完整支持，因为 MultiDiscrete 的动作维度本身包含 \(W,H\)，仅填充观察仍不能统一动作空间。

padding 需要配套：

- 空间通道填零；
- 坐标通道按统一规则生成；
- 池化忽略填充格；
- 合法动作只指向真实地图；
- LLM 或 GUI 坐标转换保持原地图坐标。

## 10.8 默认展平的代价

SB3 的普通组合提取器会将空间张量展平，再送入线性层。输入维度随地图面积增长：

\[
D=H\times W\times(C_{\mathrm{grid}}+C_{\mathrm{units}})
\]

第一层参数约为 \(D\times d_{\mathrm{hidden}}\)。地图扩大时参数数量增长，且相邻关系没有显式结构。

## 10.9 `SpatialFeatureExtractor`

空间提取器的概念流程：

```text
grid + units
→ 通道拼接
→ (B,H,W,C) 转 (B,C,H,W)
→ 可选坐标通道
→ 多层 3×3 卷积
→ masked average / average / flatten
→ 拼接 global_features
→ 线性投影到 features_dim
```

坐标卷积解决“卷积平移共享但总部角落具有绝对意义”的矛盾。额外卷积扩大感受野，使高层特征能覆盖更大邻域。掩码平均使小地图的特征不被零填充稀释。

## 10.10 观察检查

```powershell
python -c "from reinforcetactics.rl.gym_env import StrategyGameEnv; e=StrategyGameEnv(map_file='maps/1v1/beginner.csv',opponent='noop'); o,_=e.reset(seed=42); print({k:(v.shape,v.dtype,float(v.min()),float(v.max())) for k,v in o.items()}); e.close()"
```

应检查每个键的形状、dtype、最小最大值以及 `observation_space.contains(obs)`。只检查 shape 不足以发现越界或 NaN。

## 10.11 历史问题：空间盲性

2026-07-24 的管线审查指出，早期生产配置使用默认展平网络，策略需要从头学习地图邻接关系。后续配置引入 `SpatialFeatureExtractor`、坐标通道、更深卷积和掩码池化。

这个修复提高了表示能力，但不能单独证明胜率提升。正确实验需要保持动作空间、奖励、对手、种子和训练预算不变，只替换特征提取器，并进行多种子对比。

## 10.12 本章练习

1. 为什么单位“是否已行动”必须进入观察？
2. one-hot 地形相比单整数编码避免了什么错误假设？
3. 为什么 padding 观察不能自动解决 MultiDiscrete 跨地图动作空间变化？
4. 设计一个检查战争迷雾信息泄漏的测试。

