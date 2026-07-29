# 动作掩码（Action Masking）

> 返回：[算法总览](overview.md) · [源码总览](../source-analysis/overview.md) · [索引](../AGENTS.md)

---

## 1. 一句话直觉

棋盘上**很多格子的「攻击/移动」根本不合法**；掩码像考卷上的涂黑选项——**不许选**，策略只在合法动作上分配概率。

---

## 2. 要解决的问题

- 动作空间组合爆炸：`action_type × unit_type × from_x × from_y × to_x × to_y`。
- 绝大多数组合非法（例如从空格移动、打不存在的敌人）。
- 若只靠「非法 −10」惩罚，早期几乎全是惩罚，**信用分配极差**。
- `MultiDiscrete` 各维独立掩码是**过近似**：各维都「可能合法」，笛卡尔积仍可能非法。

---

## 3. 核心概念

### 3.1 合法动作 vs 掩码

| 概念 | 含义 |
|------|------|
| 合法动作集 | `GameState.get_legal_actions(player)` 返回的结构化列表 |
| 动作掩码 | 布尔/0-1 向量，告诉策略「哪些 logit 可参与 softmax」 |
| 非法动作 | 掩码为 0；采样与 log-prob 时排除 |

### 3.2 两种空间

| 类型 | 代码值 | 掩码粒度 |
|------|--------|----------|
| 多维离散 | `multi_discrete` | **按维**掩码：`at, ut, fx, fy, tx, ty` |
| 扁平离散 | `flat_discrete` | **精确到每个候选动作**；列表长度 ≤ `max_flat_actions` |

### 3.3 MultiDiscrete 过近似问题

例：`from` 维允许坐标 A，`to` 维允许坐标 B，但「从 A 走到 B」可能仍非法。
各维 mask 的**外积** ⊇ 真合法集 → 策略仍可能采到 env 判非法的动作。

### 3.4 结构化 / 自回归头（Autoregressive）

采样顺序：

\[
\text{atype} \rightarrow \text{source} \rightarrow (\text{unit\_type}) \rightarrow \text{target}
\]

每一步用**条件掩码**（给定前面选择后合法的后续维度）。
本项目：`StructuredActionMasks` + Feudal 的 `AutoregressiveActionHead`。

---

## 4. 算法步骤

```mermaid
flowchart LR
  GS[GameState.get_legal_actions] --> B[build_per_dim_masks 或 build_structured_masks]
  B --> M[action_masks]
  M --> P[MaskablePPO / AR head 采样]
  P --> E[env.step]
  E -->|非法兜底| Pen[invalid_action 惩罚]
```

1. 从规则引擎枚举合法微动作。
2. 编码为 mask（flat 或 per-dim 或 structured）。
3. 策略在 mask 下采样。
4. 执行；若仍非法（过近似泄漏），记 `invalid_action` 并常视为空操作/惩罚。

---

## 5. 公式与数字例子

### 5.1 带掩码的分类分布

未掩码 logits \(z_i\)，掩码 \(m_i\in\{0,1\}\)：

\[
\pi(a=i\|o) = \frac{m_i\, e^{z_i}}{\sum_j m_j\, e^{z_j}}
\]

| 符号 | 含义 |
|------|------|
| \(z_i\) | 第 \(i\) 个动作的 logit |
| \(m_i\) | 1=合法，0=非法 |
| \(\pi(a=i\|o)\) | 掩码后概率 |

**玩具例**：3 个动作 logits \(z=(0, 1, 2)\)，掩码 \(m=(1,0,1)\)（中间非法）：

\[
e^0=1,\; e^2\approx 7.39,\quad
\pi(0)=\frac{1}{1+7.39}\approx 0.119,\quad
\pi(2)\approx 0.881,\quad
\pi(1)=0
\]

### 5.2 Flat 索引（本项目约定）

\[
\text{flat\_idx} = \text{atype}\cdot (H\cdot W) + y\cdot W + x
\]

（空间索引 \((y,x)=(\text{row},\text{col})\)。）

**例子**：\(W=3,H=2\)，`attack`(atype=2) 打 \((x,y)=(1,0)\)：

\[
\text{flat\_idx} = 2\cdot 6 + 0\cdot 3 + 1 = 13
\]

### 5.3 过近似计数

设各维合法数：atype 3、from 2、to 4，笛卡尔积 \(3\times2\times4=24\)，
真合法仅 5 个 → 最多 **19** 个「维合法但整体非法」组合。
Flat/AR 的目标就是把可采样集压回真合法集。

---

## 6. 在本项目中的实现

| 组件 | 位置 |
|------|------|
| 环境与 mask API | `rl/gym_env.StrategyGameEnv.action_masks` |
| 按维 mask 纯函数 | `rl/gym_env.build_per_dim_masks` |
| 结构化 mask | `rl/gym_env.build_structured_masks`、`StructuredActionMasks` |
| Flat 候选列表 | `rl/gym_env.build_flat_actions` |
| SB3 包装 | `rl/masking.ActionMaskedEnv`、`make_maskable_env`、`make_maskable_vec_env` |
| 校验工具 | `rl/masking.validate_action_mask` |
| AR 头 | `rl/feudal_rl.AutoregressiveActionHead`、`AutoregressiveWorkerNetwork` |
| GUI/锦标赛推理复用 | `ModelBot` 调用 `build_per_dim_masks` / structured 构建 |

`end_turn` 在 mask 中几乎总合法（atype=5，flat 规范索引等）。

源码导读：[../source-analysis/rl-gym-env.md](../source-analysis/rl-gym-env.md) · [../source-analysis/rl-advanced-trainers.md](../source-analysis/rl-advanced-trainers.md)

示例脚本：`examples/train_with_action_masking.py`。

---

## 7. 配置与超参（简）

| 参数 | 说明 |
|------|------|
| `env.action_space_type` | `multi_discrete` / `flat_discrete` |
| `env.max_flat_actions` | flat 列表上限（默认 512） |
| `env.max_actions_per_turn` | 单游戏回合动作过多时**强制只允许 end_turn**（防永不结束回合） |
| `ppo.use_action_masking` | 是否用 MaskablePPO |
| `feudal.autoregressive_worker` | Feudal worker 是否 AR |

Bootstrap 生产配置常用 **`flat_discrete`**，以消除 MultiDiscrete 过近似。

---

## 8. 常见误解

1. **「有了 per-dim mask 就永远不会非法」**
   否。过近似仍可能；需 flat 或 AR。

2. **「把非法动作概率设为 0 等于删掉动作空间」**
   空间定义仍在；只是分布支撑集变小。切换地图时合法集变化，mask 动态变。

3. **「mask 是观察的一部分」**
   本项目 mask **不进** policy 的 Dict obs；由 `action_masks()` 另供 MaskablePPO。

4. **「flat 截断 `max_flat_actions` 没事」**
   合法动作极多时截断会丢动作；评估里有 `max_legal_actions` 诊断。

5. **「惩罚非法就够了，不必 mask」**
   在本游戏合法比极低时，几乎学不会；项目实践强烈依赖 mask。

---

## 9. 延伸阅读

- Huang & Ontañón, *A Closer Look at Invalid Action Masking in Policy Gradient Algorithms*
- 本目录：[ppo.md](ppo.md) · [feudal-rl.md](feudal-rl.md) · [mdp-gymnasium-basics.md](mdp-gymnasium-basics.md)
- 测试：`tests/test_rl_masking.py`、`tests/test_structured_masks.py`、`tests/test_autoregressive_head.py`
