# 第 08 章　Stable-Baselines3 训练框架

## 8.1 框架负责什么

Stable-Baselines3（SB3）实现常用深度强化学习算法和训练基础设施。它负责：

- 策略、价值或 Q 网络；
- rollout buffer 或 replay buffer；
- 批处理、反向传播和优化器；
- 模型保存与加载；
- callback、日志与向量环境；
- `learn` 和 `predict` 的统一接口。

项目仍需负责环境、观察、动作、奖励、对手与评估。框架不会判断奖励是否鼓励真实胜利，也不会自动修复非法动作表示。

## 8.2 模型构造

```python
from stable_baselines3 import PPO

model = PPO(
    "MultiInputPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    verbose=1,
)
```

`MultiInputPolicy` 用于 `spaces.Dict` 观察。它不是算法名称，而是策略类选择。`policy_kwargs` 可以指定网络结构和自定义特征提取器。

## 8.3 `learn`

```python
model.learn(total_timesteps=100_000, callback=callbacks)
```

对 on-policy 算法，`learn` 循环收集 rollout、计算优势、进行多轮小批优化，再收集新数据。`total_timesteps` 是目标环境步数；向量环境和固定 rollout 长度可能使最终计数略超过目标。

PPO 的每次更新数据量：

\[
N_{\mathrm{rollout}}=n_{\mathrm{steps}}\times n_{\mathrm{envs}}
\]

若 batch size 不能整除该值，最后出现较小批次并产生警告。短实验应把 `batch_size` 设为 rollout 大小的因数。

## 8.4 `predict`

```python
action, state = model.predict(obs, deterministic=True)
```

`deterministic=True` 通常选择分布众数或最大 Q 动作，适合稳定评估；训练时算法会自行采样。对于 MaskablePPO，预测还需提供当前掩码：

```python
action, state = model.predict(
    obs,
    action_masks=env.action_masks(),
    deterministic=True,
)
```

若训练使用掩码而评估忘记传掩码，模型可能在评估时选择非法动作，造成“训练正常、评估很差”的测量错误。

## 8.5 On-policy rollout buffer

PPO/A2C 的 buffer 保存一段当前策略数据：

```text
observation, action, reward, done,
value, log_probability, advantage, return
```

更新后通常清空，继续用新策略收集。旧 `log_probability` 用于计算 PPO 新旧概率比；value 用于 GAE。

## 8.6 DQN replay buffer

DQN 保存：

```text
(observation, action, reward, next_observation, done)
```

训练时随机采样旧转移，打破相邻样本相关性并重复利用数据。由于数据来自旧策略，DQN 是 off-policy。经验回放不适用于普通 PPO，因为 PPO 目标假设数据来自旧策略的已知快照且只进行受限更新。

## 8.7 Monitor 与日志

`Monitor` 记录 episode 回报、长度和额外信息。TensorBoard 展示：

- `rollout/ep_rew_mean`、`ep_len_mean`；
- `train/policy_gradient_loss`；
- `train/value_loss`；
- `train/entropy_loss`；
- `train/approx_kl`；
- `train/clip_fraction`；
- `time/fps` 和步数。

这些指标必须结合环境结果解释。价值损失下降不等于胜率上升；平均回报上涨可能来自塑形刷分；熵降低可能是合理收敛，也可能是过早坍缩。

## 8.8 Callback

Callback 在训练事件上执行逻辑：

- 周期评估；
- checkpoint 保存；
- 课程晋级；
- 熵系数调度；
- 指标记录；
- 早停或停滞异常。

回调频率容易受 `n_envs` 影响。应在代码中确认 `n_calls`、`num_timesteps` 和实际环境步的关系，而不是只看配置名。

项目的 `PeriodicEvalCallback` 和 `PromotionCallback` 进一步记录胜负、终局原因、动作分布和晋级状态。

## 8.9 模型保存与环境兼容

SB3 `.zip` 通常保存策略参数、算法超参数和空间信息。加载时环境必须兼容：

- 观察键、形状和 dtype；
- 动作空间类型与尺寸；
- 自定义特征提取器导入路径；
- 掩码接口；
- 地图 padding 与单位集合。

MultiDiscrete 模型不能直接放到 Flat Discrete 环境，因为输出头完全不同。仅文件能加载不代表环境语义相同；奖励和对手变化也会影响评估。

## 8.10 `sb3-contrib`

实验性或扩展算法位于 `sb3-contrib`。项目主线使用 `MaskablePPO`。官方接口要求环境暴露 `action_masks()`；在 `SubprocVecEnv` 下，掩码必须在环境内部实现，不能只靠主进程包装函数。

项目提供 `make_maskable_env` 和 `make_maskable_vec_env` 统一构建环境，避免不同训练脚本漏传参数。

## 8.11 配置优先级

项目高级训练脚本通常采用：

1. dataclass 默认；
2. YAML/JSON 配置；
3. CLI 显式覆盖。

最终运行配置必须落盘。只保存原始 YAML 不够，因为 CLI 可能改过值；只保存命令也不够，因为默认值可能随版本变化。`run_config` 一类工具应记录合并后的配置、版本、Git 提交、设备和种子。

## 8.12 最小接口检查

```powershell
python -c "from sb3_contrib import MaskablePPO; from reinforcetactics.rl.masking import make_maskable_env; e=make_maskable_env(map_file='maps/1v1/starter.csv',opponent='noop',action_space_type='flat_discrete',max_flat_actions=128); m=MaskablePPO('MultiInputPolicy',e,n_steps=32,batch_size=32,n_epochs=1,device='cpu',verbose=0); m.learn(64); print('learn passed'); e.close()"
```

这条命令验证 64 步训练循环，不评价策略强度。

## 8.13 本章练习

1. `MultiInputPolicy` 与 PPO 的关系是什么？
2. 为什么 PPO 不能像 DQN 一样任意重复使用很久以前的数据？
3. 训练使用动作掩码时，评估为何也必须传掩码？
4. 模型文件能加载时，还需要检查哪些环境兼容项？

