# 附录 A　数学符号、公式与术语速查

本附录供连续阅读时回查。它不是对正文的外部依赖：每个核心概念在正文首次出现时仍有完整解释。

## A.1 记号约定

| 符号 | 读法 | 含义 | 常见范围 |
|---|---|---|---|
| \(t\) | t | 环境微动作时间下标 | \(0,1,2,\ldots\) |
| \(s_t\) | s 下标 t | 时刻 \(t\) 的状态 | 状态空间 \(\mathcal S\) |
| \(o_t\) | o 下标 t | 智能体实际观察 | 观察空间 \(\mathcal O\) |
| \(a_t\) | a 下标 t | 智能体动作 | 动作空间 \(\mathcal A\) |
| \(r_t\) | r 下标 t | 一步奖励 | 实数 |
| \(\pi(a\mid s)\) | pi | 状态下的动作概率 | \([0,1]\)，对动作求和为 1 |
| \(\theta\) | theta | 神经网络参数 | 实向量 |
| \(\gamma\) | gamma | 折扣因子 | 通常 \([0,1)\) |
| \(\lambda\) | lambda | GAE 偏差—方差参数 | \([0,1]\) |
| \(\alpha\) | alpha | 学习率或其他权重 | 由上下文决定 |
| \(\epsilon\) | epsilon | PPO 裁剪宽度或探索率 | 由上下文决定 |
| \(V^\pi(s)\) | V | 状态价值 | 期望折扣回报 |
| \(Q^\pi(s,a)\) | Q | 动作价值 | 执行动作后的期望折扣回报 |
| \(A^\pi(s,a)\) | A | 优势 | \(Q^\pi-V^\pi\) |
| \(G_t\) | G | 从 \(t\) 开始的回报 | 奖励的折扣和 |
| \(\delta_t\) | delta | TD 残差 | 实数 |
| \(\mathbb E[X]\) | E | 随机变量的期望 | 实数 |
| \(\operatorname{Var}(X)\) | Var | 方差 | 非负 |
| \(\nabla_\theta\) | nabla | 对参数的梯度 | 与 \(\theta\) 同形 |
| \(H(\pi)\) | H | 策略熵 | 非负 |
| \(D_{\mathrm{KL}}\) | KL | 分布差异 | 非负 |
| \(N(s,a)\) | N | MCTS 访问次数 | 非负整数 |
| \(P(s,a)\) | P | MCTS 网络先验 | \([0,1]\) |
| \(W(s,a)\) | W | MCTS 累计价值 | 实数 |

同一希腊字母在不同算法中可能有不同含义。比如 \(\alpha\) 在 DQN 中常指学习率，在 Feudal 章节中又表示 Worker 外在奖励权重。判断含义必须看公式定义，不能只看字母。

## A.2 集合、下标与条件

\(\mathcal S\) 表示所有可能状态的集合，单个状态写作 \(s\in\mathcal S\)。花体大写通常表示空间或集合。

\[
\pi(a\mid s)
\]

竖线读作“在……条件下”。它表示已知状态 \(s\) 时选择动作 \(a\) 的概率，不是除法。

\[
x_{1:T}=(x_1,x_2,\ldots,x_T)
\]

表示从 1 到 \(T\) 的一段序列。

\[
\mathbf 1[C]
\]

是指示函数：条件 \(C\) 成立取 1，否则取 0。它常用于终局、合法性或到达目标奖励。

\[
\arg\max_a f(a)
\]

返回使 \(f(a)\) 最大的动作，而 \(\max_a f(a)\) 返回最大数值。两者不要混淆。

## A.3 概率与统计

### 概率分布

离散动作策略满足：

\[
\pi(a\mid s)\ge0,\qquad
\sum_{a\in\mathcal A}\pi(a\mid s)=1
\]

动作掩码后，求和只在合法集合上进行。

### 期望

离散随机变量：

\[
\mathbb E[X]=\sum_xp(x)x
\]

若一次攻击 70% 造成 10 点、30% 造成 0 点，期望伤害为 \(0.7\times10+0.3\times0=7\)。期望 7 不表示某次一定造成 7 点。

### 方差与标准差

\[
\operatorname{Var}(X)
=\mathbb E[(X-\mathbb E[X])^2]
\]

\[
\operatorname{SD}(X)=\sqrt{\operatorname{Var}(X)}
\]

平方保证正负偏差不会抵消；开根号使标准差恢复到原变量单位。

### 协方差

\[
\operatorname{Cov}(X,Y)
=\mathbb E[(X-\mathbb E[X])(Y-\mathbb E[Y])]
\]

正值表示二者倾向同向变化，负值表示反向变化。相关不等于因果。

### 样本均值

\[
\bar x=\frac1n\sum_{i=1}^{n}x_i
\]

训练曲线若只有一个种子，曲线上的多个时间点不是独立样本，不能用它们代替多种子均值。

### 样本方差

\[
s^2=\frac1{n-1}\sum_i(x_i-\bar x)^2
\]

分母使用 \(n-1\) 是对有限样本估计总体方差的校正。

### 标准误

\[
\operatorname{SE}(\bar x)=\frac{s}{\sqrt n}
\]

增加独立种子能降低均值估计误差，但收益按平方根增长：把标准误减半，约需四倍样本。

### 置信区间

大样本正态近似：

\[
\bar x\pm1.96\operatorname{SE}(\bar x)
\]

95% 置信区间的频率学解释是：若重复相同抽样过程，约 95% 的此类区间覆盖真实参数；不是“参数有 95% 概率落在本次区间”。

## A.4 向量与矩阵

向量：

\[
\mathbf x=
\begin{bmatrix}
x_1\\x_2\\\vdots\\x_d
\end{bmatrix}
\]

可表示全局特征或网络隐藏状态。

点积：

\[
\mathbf w^\top\mathbf x
=\sum_{i=1}^{d}w_ix_i
\]

每个输入乘权重再求和。线性层：

\[
\mathbf y=W\mathbf x+\mathbf b
\]

若 \(\mathbf x\in\mathbb R^d\)、输出 \(\mathbf y\in\mathbb R^k\)，则 \(W\in\mathbb R^{k\times d}\)、\(\mathbf b\in\mathbb R^k\)。

形状检查是调试神经网络的第一工具。矩阵乘法 \(AB\) 只有在 A 的列数等于 B 的行数时成立。

## A.5 导数、梯度与链式法则

一元导数：

\[
f'(x)=\lim_{h\to0}\frac{f(x+h)-f(x)}h
\]

它描述局部斜率。若损失随参数增加而上升，导数为正，梯度下降会减小参数。

多参数梯度：

\[
\nabla_\theta L=
\begin{bmatrix}
\partial L/\partial\theta_1\\
\vdots\\
\partial L/\partial\theta_d
\end{bmatrix}
\]

梯度下降：

\[
\theta\leftarrow\theta-\alpha\nabla_\theta L
\]

链式法则：

\[
\frac{\partial L}{\partial x}
=\frac{\partial L}{\partial y}
\frac{\partial y}{\partial x}
\]

深度网络的反向传播就是把这个规则从输出层反复应用到输入层。PyTorch `loss.backward()` 计算梯度，`optimizer.step()` 才更新参数，`optimizer.zero_grad()` 清除默认累积的旧梯度。

## A.6 激活、softmax 与对数概率

ReLU：

\[
\operatorname{ReLU}(x)=\max(0,x)
\]

Tanh：

\[
\tanh(x)=\frac{e^x-e^{-x}}{e^x+e^{-x}}\in(-1,1)
\]

Softmax：

\[
p_i=\frac{e^{z_i}}{\sum_j e^{z_j}}
\]

为了数值稳定，实际实现会减去最大 logit：

\[
p_i=\frac{e^{z_i-z_{\max}}}
{\sum_j e^{z_j-z_{\max}}}
\]

概率乘积在长序列中容易下溢，因此策略梯度使用对数概率：

\[
\log\prod_t\pi(a_t\mid s_t)
=\sum_t\log\pi(a_t\mid s_t)
\]

对数不会改变概率大小次序，并把乘积变为求和。

## A.7 监督学习损失

均方误差：

\[
L_{\mathrm{MSE}}
=\frac1B\sum_i(\hat y_i-y_i)^2
\]

项目价值网络、Q 网络和 AlphaZero 价值头都会使用平方误差。

交叉熵：

\[
L_{\mathrm{CE}}
=-\sum_k y_k\log p_k
\]

one-hot 标签时只保留正确类别的 \(-\log p\)。BC 用它学习专家动作；AlphaZero 则以软目标 \(\pi\) 对完整动作分布求和。

类别加权交叉熵：

\[
L=-w_y\log p_y
\]

可提高少数动作类别的贡献，但不能创造数据中从未出现的状态—动作关系。

## A.8 回报与折扣

有限 episode 回报：

\[
G_t=r_t+\gamma r_{t+1}+\gamma^2r_{t+2}+\cdots
\]

递推形式：

\[
G_t=r_t+\gamma G_{t+1}
\]

有效时间尺度粗略为：

\[
H_{\mathrm{eff}}\approx\frac1{1-\gamma}
\]

\(\gamma=0.99\) 时约 100 步。这不是硬截止线，而是理解折扣衰减的尺度。

## A.9 价值、Q 与优势

\[
V^\pi(s)=\mathbb E_\pi[G_t\mid s_t=s]
\]

\[
Q^\pi(s,a)
=\mathbb E_\pi[G_t\mid s_t=s,a_t=a]
\]

\[
A^\pi(s,a)=Q^\pi(s,a)-V^\pi(s)
\]

优势为正表示该动作优于状态下的平均策略，负值表示较差。它不是“会赢的概率”，单位与回报相同。

## A.10 Bellman 方程

状态价值：

\[
V^\pi(s)
=\sum_a\pi(a\mid s)
\sum_{s',r}p(s',r\mid s,a)
[r+\gamma V^\pi(s')]
\]

最优动作价值：

\[
Q^*(s,a)
=\mathbb E[
r+\gamma\max_{a'}Q^*(s',a')
\mid s,a]
\]

Bellman 方程把长期量分为“一步奖励 + 下一状态的长期量”，是 TD、DQN 和 Actor-Critic 的共同基础。

## A.11 MC、TD 与 GAE

Monte Carlo 目标使用完整回报：

\[
y_t^{MC}=G_t
\]

无 bootstrap，偏差低但方差高，必须等待 episode 或片段结束。

一步 TD 目标：

\[
y_t^{TD}=r_t+\gamma(1-d_t)V(s_{t+1})
\]

TD 残差：

\[
\delta_t
=r_t+\gamma(1-d_t)V(s_{t+1})-V(s_t)
\]

GAE：

\[
\hat A_t^{GAE(\gamma,\lambda)}
=\sum_{l=0}^{\infty}
(\gamma\lambda)^l\delta_{t+l}
\]

\(\lambda=0\) 接近一步 TD，\(\lambda=1\) 接近长回报。对时间限制截断，只要底层 MDP 未终局，就通常应保留下一状态 bootstrap。

## A.12 策略梯度

基本策略梯度：

\[
\nabla_\theta J(\theta)
=\mathbb E[
\nabla_\theta\log\pi_\theta(a_t\mid s_t)
G_t]
\]

用优势替代回报：

\[
\nabla_\theta J(\theta)
\approx\mathbb E[
\nabla_\theta\log\pi_\theta(a_t\mid s_t)
\hat A_t]
\]

若优势为正，提高该动作概率；若优势为负，降低概率。baseline \(V(s)\) 在不依赖当前动作时不会改变期望梯度方向，却能降低方差。

## A.13 熵与 KL

离散策略熵：

\[
H(\pi)=-\sum_a\pi(a)\log\pi(a)
\]

均匀分布熵高，确定性分布熵低。熵奖励鼓励探索，但熵过高可能使策略长期随机。

KL 散度：

\[
D_{\mathrm{KL}}(p\Vert q)
=\sum_xp(x)\log\frac{p(x)}{q(x)}
\]

它不对称，不是严格距离。PPO 日志的 approximate KL 用于监控新旧策略变化幅度。

## A.14 DQN 公式

目标：

\[
y_t=r_t+\gamma(1-d_t)
\max_{a'}Q_{\theta^-}(s_{t+1},a')
\]

损失：

\[
L(\theta)
=\mathbb E[
(Q_\theta(s_t,a_t)-y_t)^2]
\]

\(\theta^-\) 是目标网络参数，在一段更新期间保持较慢变化；replay buffer 打乱相邻样本相关性。DQN 要枚举单一离散动作的 Q 值，因此不直接兼容项目默认 MultiDiscrete CLI。

## A.15 A2C 公式

A2C 使用同步 rollout，常用 \(n\)-step 回报：

\[
G_t^{(n)}
=\sum_{k=0}^{n-1}\gamma^kr_{t+k}
+\gamma^nV(s_{t+n})
\]

Actor 损失：

\[
L_{\text{actor}}
=-\log\pi(a_t\mid s_t)\hat A_t
\]

Critic 损失：

\[
L_{\text{critic}}
=(V(s_t)-\hat G_t)^2
\]

总损失加入价值系数和熵项。项目普通 A2C 构造路径不消费动作掩码，这是接口限制而非公式限制。

## A.16 PPO 公式

概率比：

\[
r_t(\theta)
=\frac{\pi_\theta(a_t\mid s_t)}
{\pi_{\theta_{\mathrm{old}}}(a_t\mid s_t)}
=\exp[
\log\pi_\theta-\log\pi_{\theta_{\mathrm{old}}}]
\]

裁剪目标：

\[
L^{CLIP}
=\mathbb E[
\min(
r_t\hat A_t,
\operatorname{clip}(r_t,1-\epsilon,1+\epsilon)\hat A_t)]
\]

最小值会在有利于目标、但变化过大的方向上限制收益。它不是把所有概率比强行裁到区间内，也不能单独保证参数距离很小。

总损失：

\[
L=-L^{CLIP}+c_vL^V-c_eH
\]

实现通常最小化 \(L\)，所以策略目标前有负号，熵奖励前也有负号。

## A.17 动作掩码

给合法性 \(m_i\in\{0,1\}\)，masked logits：

\[
\tilde z_i=
\begin{cases}
z_i,&m_i=1\\
-M,&m_i=0
\end{cases}
\]

\(M\) 为很大正数。softmax 后非法概率接近 0。

MaskablePPO 必须在采样和更新时对同一状态使用一致掩码；评估时也必须调用支持掩码的预测接口。

逐维 MultiDiscrete 掩码保证各维取值分别出现过，但不保证笛卡尔积组合合法。自回归条件掩码解决的是组合依赖。

## A.18 奖励塑形

势能塑形：

\[
F(s,a,s')=\gamma\Phi(s')-\Phi(s)
\]

塑形后奖励：

\[
r'=r+F
\]

在标准条件下，这种形式保持最优策略不变。任意事件奖励不一定具有该性质。项目中伤害、击杀、占领等分量必须通过 reward breakdown 和终局结果共同诊断。

## A.19 BC

行为克隆最大化专家动作似然：

\[
\max_\theta
\sum_i\log\pi_\theta(a_i\mid s_i)
\]

等价最小化交叉熵。BC 的核心问题是分布偏移：部署时一次错误进入专家数据很少覆盖的状态，后续错误会累积。BC→PPO 用示范建立初始技能，再以环境交互修正。

## A.20 自对弈

对手从历史池采样：

\[
\pi_{\text{opp}}\sim P_{\text{pool}}
\]

如果只对当前最新模型训练，对手随自己同步变化，容易循环与遗忘。历史快照、规则锚点和多样采样能减轻非平稳。

## A.21 Feudal

Manager：

\[
g_k\sim\pi_M(g\mid s_{kc})
\]

Worker：

\[
a_t\sim\pi_W(a\mid s_t,g_k)
\]

项目 Worker 奖励：

\[
r_t^W=r_t^{int}
+\alpha r_t^{ext}
\]

Manager 段折扣：

\[
\gamma^{k_t}
\]

不要把 `worker_reward_alpha` 误读成内外奖励凸组合。

## A.22 MCTS

PUCT：

\[
Q(s,a)
+c_{\mathrm{puct}}P(s,a)
\frac{\sqrt{N(s)+1}}{1+N(s,a)}
\]

访问策略：

\[
\pi(a\mid s)
=\frac{N(s,a)^{1/\tau}}
{\sum_bN(s,b)^{1/\tau}}
\]

玩家视角翻号、合法 flat 索引与深复制后的动作引用是项目实现的关键正确性点。

## A.23 AlphaZero

样本：

\[
(s,\pi,z)
\]

联合损失：

\[
L=(z-v)^2-\pi^\top\log p+c\|\theta\|^2
\]

\(\pi\) 来自 MCTS，不是实际单一动作；\(z\) 是玩家相对终局标签。

## A.24 项目术语

**环境微动作（env step）**：一次 `env.step(action)`。  
**游戏回合（game turn）**：一名玩家的一组单位行动与结束回合。  
**episode**：从 reset 到 terminated 或 truncated 的一局。  
**stage**：Bootstrap 中固定地图、对手、奖励与门槛的一段训练。  
**rollout**：on-policy 算法采集的一段连续交互。  
**buffer**：保存训练样本的数据结构；不同算法语义不同。  
**wrapper**：包裹环境并修改接口或行为的对象。  
**VecEnv**：让 SB3 同时管理一个或多个环境的接口。  
**checkpoint**：训练中间状态；是否能完整恢复取决于保存内容。  
**snapshot**：自对弈历史策略的冻结副本。  
**anchor**：长期固定、用于跨阶段比较的评估对手。  
**shaping attractor**：高 shaped reward 但不完成真实目标的策略区域。  
**invalid combination**：MultiDiscrete 每维看似可选、组合后违反规则的动作。  
**exact mask**：相对当前条件精确描述合法选择的掩码。  
**historical result**：旧代码、旧配置或旧环境得到的记录，未自动代表当前复现。

