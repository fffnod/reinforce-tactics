# 第 07 章　Gymnasium 环境契约

## 7.1 环境的最小接口

Gymnasium 将算法与领域规则隔离。算法只需要空间定义以及 `reset`、`step`：

```python
obs, info = env.reset(seed=42)
obs, reward, terminated, truncated, info = env.step(action)
```

`StrategyGameEnv` 继承 `gymnasium.Env`。创建后应满足：

- `obs` 属于 `observation_space`；
- `action` 属于 `action_space`；
- `reward` 可转换为标量浮点数；
- `terminated`、`truncated` 是布尔值；
- `info` 是诊断字典，不应被策略依赖为隐藏观察。

## 7.2 `reset`

`reset(seed=...)` 开始新 episode，重建游戏状态、对手、计数器和奖励势能基线。第一次重置通常应调用父类种子逻辑，以创建环境自己的随机数生成器。

```python
obs, info = env.reset(seed=7)
```

同一种子可帮助重现环境随机序列，但不能保证 GPU 并行训练逐位一致。项目还包含游戏引擎 RNG、Bot RNG、NumPy、Python 和 PyTorch 随机源，完整复现必须统一记录。

## 7.3 `step`

一次环境步的顺序可概括为：

1. 解码动作；
2. 按规则执行或判定无效；
3. 更新动作统计和即时奖励；
4. 若智能体结束回合，让对手完成回合；
5. 检查规则终局和外部步数上限；
6. 构造下一观察、奖励分解和诊断信息。

调用方循环：

```python
obs, info = env.reset(seed=42)
while True:
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
```

随机采样没有使用合法动作掩码，因此可能产生无效动作；它只能验证接口，不是合理基线。

## 7.4 观察空间

默认观察是 `spaces.Dict`：

```text
grid              (H, W, GRID_CHANNELS)
units             (H, W, UNIT_CHANNELS)
global_features   (5,)
visibility        (H, W)  # 仅战争迷雾
```

空间声明是契约。若 `Box` 声明范围 `[0,1]`，实际观察就不应出现未缩放金币 5000。`gymnasium.utils.env_checker.check_env` 可以发现形状、dtype 和返回值错误。

## 7.5 动作空间

默认：

```text
MultiDiscrete([10, 8, W, H, W, H])
```

六个字段依次表示动作类型、单位类型、起点横纵坐标、目标横纵坐标。

Flat Discrete 模式：

```text
Discrete(max_flat_actions)
```

每个索引在当前步骤映射到一条完整合法动作。两种模式的网络输出形状不同，模型不可互换。

## 7.6 终止与截断

Gymnasium 明确区分：

- `terminated=True`：任务定义内的终局；
- `truncated=True`：任务外条件提前停止，常见为时间限制。

价值目标在规则终止处不 bootstrap，在纯截断处通常要 bootstrap。官方 Gymnasium 文档专门强调这一差别，因为旧版 `done` 无法直接表达。

项目中：

| 原因 | 标志 | 含义 |
|---|---|---|
| 总部占领、消灭 | `terminated` | 规则终局 |
| `max_turns` 和局 | `terminated` | 规则定义的和局 |
| `max_steps` | `truncated` | 收集器截断 |

将 `max_steps` 截断再额外施加 `draw` 惩罚，可能与算法的时间限制 bootstrap 同时作用，形成双重边界效应。当前环境把截断奖励设为显式可选项。

## 7.7 `info` 的作用

`info` 应保存诊断信息，例如：

- `winner`、`game_over`、`end_reason`；
- `reward_breakdown`；
- `n_legal_actions`；
- 单位创建、伤害、治疗和占领统计；
- episode 长度和累计奖励。

训练策略不应把只存在于 `info` 的隐藏敌方信息作为输入，否则训练和部署接口不一致。评估器可以使用它分解结果。

## 7.8 Wrapper

Wrapper 在不改领域环境的情况下增加行为。项目中的 `ActionMaskedEnv` 和自对弈环境都是 wrapper 或类似包装层。常见用途：

- 统一动作掩码接口；
- 记录 episode 指标；
- 向量化多个环境；
- 翻转玩家相对观察；
- 注入对手快照。

Wrapper 必须正确转发属性和 `reset/step`。多层 wrapper 下直接访问 `env.game_state` 可能失败，应通过框架提供的属性转发或 `unwrapped` 谨慎访问。

## 7.9 向量环境

VecEnv 同时推进多个独立环境，收集形状为 `(n_envs, ...)` 的批数据。若 PPO 的 `n_steps=2048,n_envs=8`，每次 rollout 收集：

\[
2048\times8=16384
\]

条转移。配置中的 `eval_freq`、callback 调用次数和实际总环境步之间可能因此出现倍数关系。解释训练日志必须知道指标按“算法调用”还是“总环境步”计数。

## 7.10 PettingZoo 边界

PettingZoo 为多智能体环境定义 AEC 和 Parallel API。当前项目虽依赖该包，但主环境仍是 Gymnasium 单智能体包装：对手回合发生在环境内部。若未来实现真正多智能体训练，需要新环境接口，而不是仅把 `opponent="self"` 称为 PettingZoo。

## 7.11 验证命令

```powershell
python -c "from gymnasium.utils.env_checker import check_env; from reinforcetactics.rl.gym_env import StrategyGameEnv; e=StrategyGameEnv(map_file='maps/1v1/starter.csv',opponent='noop',max_steps=16); check_env(e); print('check_env passed'); e.close()"
```

`check_env` 通过只说明 Gymnasium 契约基本一致，不验证奖励是否合理、掩码是否精确或 Bot 是否有竞争力。

## 7.12 本章练习

1. 写出当前 Gymnasium `step` 的五个返回值。
2. 为什么 `max_turns` 和 `max_steps` 在项目中采用不同结束标志？
3. `n_steps=512,n_envs=4` 时每次 PPO rollout 有多少条转移？
4. 为什么环境契约通过仍不能证明训练问题建模正确？

