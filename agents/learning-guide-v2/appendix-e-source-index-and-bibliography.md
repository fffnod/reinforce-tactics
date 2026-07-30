# 附录 E　源码符号索引与原始文献

## E.1 索引使用原则

正文已经包含理解概念所需的解释。本附录中的路径用于：

- 核验当前实现；
- 定位调试入口；
- 继续阅读完整上下文；
- 追踪论文和框架定义。

路径不承担“请读者自行查看源码才能理解正文”的责任。行号会随代码变化，所以索引以稳定的模块与符号名为主。

## E.2 游戏领域层

### `reinforcetactics/core/game_state.py`

`GameState` 是规则状态的核心聚合对象，负责：

- 地图、玩家、金币、单位与当前回合；
- 创建单位；
- 移动、攻击、占领；
- heal、cure、paralyze、haste、buff；
- 合法动作枚举；
- 回合推进、胜负与和局；
- 动作历史和 replay 相关状态。

阅读规则时从 `get_legal_actions` 与各动作执行方法成对核对：前者定义“可以提议什么”，后者定义“执行后怎样变化”。

### `reinforcetactics/constants.py`

集中保存单位数据、经济和战斗常量。实验的 `engine_overrides` 会在运行时稀疏覆盖其中一部分语义。分析历史平衡时必须记录覆盖后的有效值，而不只看源文件默认。

### `reinforcetactics/game/mechanics.py`

放置战斗或移动的共享规则辅助函数。若 Bot、GUI 与 RL 环境出现规则不一致，应检查它们是否都通过同一领域入口执行。

## E.3 规则 Bot

### `reinforcetactics/game/bot_base.py`

- `BaseBot`：Bot 共同接口；
- `BotUnitMixin`：距离、tie-break、动作辅助和诊断记录。

### `reinforcetactics/game/bot.py`

- `NoopBot`：只结束回合；
- `RandomBot`：均匀采样合法非结束动作，受 `max_actions` 限制；
- `BalancedRandomBot`：先尝试生产，再让每个单位随机行动一次；
- `SimpleBot`：局部启发式、单位能力和目标优先；
- `MediumBot`、`AdvancedBot`、`MasterBot`：逐级丰富威胁、组合和战术；
- `MixedBot`：每 episode 抽取一个内部对手。

Bot 名称是实现层级，不是数学保证的严格实力顺序。

### `reinforcetactics/game/model_bot.py`

把训练模型包装为游戏 Bot。核验点包括 observation 玩家视角、动作解码、动作掩码、设备与 `eval/no_grad` 推理。

### `reinforcetactics/game/alphazero_bot.py`

把策略价值网络与 MCTS 接到游戏 Bot 接口；评估时应明确 simulation 数、温度和根噪声。

## E.4 Gymnasium 环境

### `reinforcetactics/rl/gym_env.py`

关键符号：

- `StrategyGameEnv`：主 Gymnasium 环境；
- `StructuredActionMasks`：自回归动作条件掩码容器；
- `build_per_dim_masks`：MultiDiscrete 逐维掩码；
- `build_structured_masks`：阶段条件掩码；
- `build_flat_actions`：Flat Discrete 合法动作映射。

`StrategyGameEnv.reset` 负责新建局面与对手，`step` 负责解码当前玩家微动作、执行、奖励、必要时推进对手回合，并返回 Gymnasium 五元组。

### `reinforcetactics/rl/observation.py`

- `build_observation`：把 `GameState` 转换为 Dict observation；
- `GRID_CHANNELS`、`UNIT_CHANNELS`、`GLOBAL_FEATURES_DIM`：网络输入契约；
- 玩家相对所有者编码；
- padding、战争迷雾与尺度处理。

观察通道改动会影响所有保存模型和 AlphaZero 网络输入，属于公共训练契约变化。

### `reinforcetactics/rl/masking.py`

- `ActionMaskedEnv`：向 sb3-contrib 暴露掩码；
- `make_maskable_env`：单环境工厂；
- `make_maskable_vec_env`：向量环境工厂；
- `validate_action_mask`：掩码诊断。

SubprocVecEnv 使用时，掩码方法必须在子进程环境内可调用。

## E.5 特征提取与策略网络

`SpatialFeatureExtractor` 的实际定义可用：

```powershell
rg -n "class SpatialFeatureExtractor" reinforcetactics
```

它接收 `grid`、`units` 与 `global_features`，用卷积保存空间局部关系，再融合全局向量。核验：

- NHWC 到 NCHW 的转换；
- padding 是否参与 pooling；
- 输出 `features_dim`；
- `policy_kwargs` 是否在训练与加载时一致。

普通 `MultiInputPolicy` 的默认 CombinedExtractor 会分别展平/处理 Dict 字段，不等于项目自定义空间 CNN。

## E.6 配置

### `reinforcetactics/rl/config.py`

包含环境、PPO、课程阶段与总训练配置的数据结构，负责 YAML/JSON 解析、默认值和验证。

关键审计问题：

- CLI 是否覆盖配置；
- 嵌套字典是否传给环境工厂；
- 未识别字段是否报错或静默丢弃；
- resolved config 是否落盘。

### `reinforcetactics/utils/run_config.py`

提供运行配置的辅助处理。配置文件是输入，真正生效的是脚本解析后的对象。

## E.7 Bootstrap

### `reinforcetactics/rl/bootstrap.py`

- `CurriculumStalled`：阶段预算耗尽异常；
- `_resolve_curriculum_pad_size`：跨地图统一观察；
- `_default_model_factory`：MaskablePPO 等模型构造；
- `_write_stage_config`、`_write_run_status`：审计产物；
- `run_curriculum`：阶段训练、评估、晋级、checkpoint 交接；
- `make_stage_env`：按阶段创建环境；
- `record_curriculum_replays`：回放。

### `scripts/train/train_bootstrap.py`

headless CLI，支持配置、点路径覆盖、BC 预训练、本地输出、绘图/视频开关和本地禁用 GCS。教材不涉及 Cloud。

## E.8 行为克隆

### `reinforcetactics/rl/imitation.py`

- `Demonstration`：单个观察—动作—掩码样本；
- `DemonstrationDataset`：数据集；
- `_ActionRecorder`：规则 Bot 动作拦截；
- `record_episode`、`collect_demonstrations`：采集；
- `DemonstrationScenario`：多场景定义；
- `collect_demonstrations_multi`：场景混合；
- `behavior_clone`：masked cross-entropy；
- `make_warm_started_model`：构造与加载；
- `evaluate_bc_against_bot_ladder`：部署评估。

### `scripts/build_bc_warmstart.py`

独立 BC 构建入口。其帮助文本明确说明：价值头不由 BC 拟合，空间与下游 curriculum 必须精确匹配。

## E.9 自对弈

### `reinforcetactics/rl/self_play.py`

- `OpponentPool`：历史策略池；
- `SelfPlayEnv`：环境 wrapper；
- `make_self_play_env`、`make_self_play_vec_env`：工厂；
- callback 类：更新对手、添加快照、记录评估。

核验 RNG 来源、池采样策略、player swap、对手模型设备、`eval()` 与 `no_grad()`。

### `scripts/train/train_self_play.py`

CLI 支持 self-play/mixed、历史池、规则 Bot 比例、换边、VecEnv、resume 与 PPO 超参数。

## E.10 Feudal RL

### `reinforcetactics/rl/feudal_rl.py`

- `ManagerNetwork`：高层目标；
- `WorkerNetwork`：传统多头 Worker；
- `AutoregressiveActionHead`、`AutoregressiveWorkerNetwork`：阶段条件动作；
- `_compute_gae`：支持 `segment_lengths`；
- `FeudalRolloutBuffer`：两层轨迹、掩码与奖励分量；
- `FeudalRLAgent`：采样与两层 PPO update；
- `compute_intrinsic_reward`：目标进展奖励。

当前 Worker 奖励的权威语义在 `FeudalRolloutBuffer.add_worker_step`：

```python
intrinsic_reward + worker_reward_alpha * extrinsic_reward
```

Manager GAE 的段折扣在 `_compute_gae`：

```python
gamma ** segment_lengths[t]
```

### `scripts/train/train_feudal_rl.py`

包括 flat PPO 对照与真正 Manager—Worker 训练路径。文件顶部旧注释若提到特定部署环境，不改变本书仅使用本地 CPU 的范围。

## E.11 MCTS 与 AlphaZero

### `reinforcetactics/rl/alphazero_net.py`

- `ResidualBlock`；
- `AlphaZeroNet`；
- 策略头大小 \(10WH\)；
- tanh 价值头；
- `predict` 中合法动作 masked softmax。

### `reinforcetactics/rl/mcts.py`

- `MCTSNode`：`prior`、`visit_count`、`value_sum`、children；
- `_resolve_action_refs`：深复制后的对象解析；
- `_execute_action_on_state`：模拟转移；
- `_obs_from_game_state`：网络观察与 flat mask；
- `MCTS.search`：返回 `(action_probs, root_value)`；
- `MCTS.select_action`：温度采样；
- PUCT、根噪声与回传。

### `reinforcetactics/rl/alphazero_trainer.py`

- `ReplayBuffer`；
- `self_play_game`；
- `AlphaZeroTrainer`；
- 自对弈、联合损失、候选评估、checkpoint。

当前联合损失代码为策略交叉熵加价值 MSE，L2 由 optimizer `weight_decay` 实现。

### `scripts/train/train_alphazero.py`

提供网络、搜索、自对弈、评估、设备与恢复参数。

## E.12 评估、Tournament 与 Replay

### `reinforcetactics/rl/evaluation.py`

- `_model_accepts_action_masks`：识别 predict 接口；
- `evaluate_model`：胜/和/负、回报、长度、终局、动作、奖励、单位、战斗、经济、可夺取和 trace。

### `reinforcetactics/tournament/`

- `config.py`：`TournamentConfig`；
- `schedule.py`：地图与换边赛程；
- `runner.py`：比赛执行；
- `bots.py`：参赛者描述与 Bot 构造；
- `elo.py`：期望得分与 rating 更新；
- `results.py`：聚合与输出。

### `reinforcetactics/utils/replay_actions.py`

动作记录与序列化。

### `reinforcetactics/utils/replay_player.py`

回放读取与逐动作重建。Replay determinism 测试用于防止记录能写却不能重现。

## E.13 LLM Bot

### `reinforcetactics/game/llm_bot.py`

- `LLMBot`：通用状态、提示、重试、解析、执行与日志；
- `_serialize_game_state`；
- `_run_planning_phase`；
- `_format_prompt`；
- `_execute_actions`；
- `_extract_json`；
- 按动作类型的 `_execute_*`；
- `OpenAIBot`、`ClaudeBot`、`GeminiBot`：供应商适配。

本教材只测试 `LLMBot` 的本地 mock 数据管线，不调用这些供应商。

### `reinforcetactics/game/llm_prompts.py`

basic、strategic、two-phase planning/execution 的提示模板。提示中规则数值应与当前常量做一致性测试。

## E.14 DEV 与测试索引

| 领域 | 代表测试 |
|---|---|
| 环境与观察 | `tests/test_rl_*.py` |
| Bot | `tests/test_*_bot.py` |
| Masking | 掩码与环境相关测试 |
| Bootstrap | 课程/配置/评估相关测试 |
| BC | imitation 相关测试 |
| Self-play | self-play 相关测试 |
| Feudal | `test_feudal_rl.py`、`test_feudal_rl_integration.py` |
| AlphaZero | `test_alphazero.py` |
| LLM mock | `test_llm_bot.py`、`test_llm_prompts.py` |
| Tournament | `test_tournament*.py` |
| Replay | `test_save_replay.py`、`test_replay_determinism.py` |

精确文件清单可运行：

```powershell
rg --files tests
```

## E.15 原始论文与教材

以下只列原始论文、作者教材或框架官方文档。

### 强化学习基础

1. Richard S. Sutton, Andrew G. Barto. *Reinforcement Learning: An Introduction, Second Edition*. 2018.  
   https://incompleteideas.net/book/the-book-2nd.html

2. Richard Bellman. *A Markovian Decision Process*. Journal of Mathematics and Mechanics, 1957.  
   https://www.jstor.org/stable/24900506

3. Ronald J. Williams. *Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning*. Machine Learning, 1992.  
   https://doi.org/10.1007/BF00992696

### DQN

4. Volodymyr Mnih et al. *Human-level control through deep reinforcement learning*. Nature, 2015.  
   https://doi.org/10.1038/nature14236

5. Hado van Hasselt, Arthur Guez, David Silver. *Deep Reinforcement Learning with Double Q-learning*. 2015.  
   https://arxiv.org/abs/1509.06461

### Actor-Critic、GAE 与 PPO

6. Volodymyr Mnih et al. *Asynchronous Methods for Deep Reinforcement Learning*. 2016.  
   https://arxiv.org/abs/1602.01783

7. John Schulman et al. *High-Dimensional Continuous Control Using Generalized Advantage Estimation*. 2015.  
   https://arxiv.org/abs/1506.02438

8. John Schulman et al. *Proximal Policy Optimization Algorithms*. 2017.  
   https://arxiv.org/abs/1707.06347

9. John Schulman et al. *Trust Region Policy Optimization*. 2015.  
   https://arxiv.org/abs/1502.05477

### 奖励塑形

10. Andrew Y. Ng, Daishi Harada, Stuart Russell. *Policy Invariance Under Reward Transformations: Theory and Application to Reward Shaping*. ICML, 1999.  
    https://people.eecs.berkeley.edu/~russell/papers/icml99-shaping.pdf

### 行为克隆与数据聚合

11. Stéphane Ross, Geoffrey Gordon, Drew Bagnell. *A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning*. AISTATS, 2011.  
    https://proceedings.mlr.press/v15/ross11a.html

### 层级强化学习

12. Peter Dayan, Geoffrey E. Hinton. *Feudal Reinforcement Learning*. NeurIPS, 1992.  
    https://proceedings.neurips.cc/paper/1992/hash/d14220ee66aeec73c49038385428ec4c-Abstract.html

13. Alexander Vezhnevets et al. *FeUdal Networks for Hierarchical Reinforcement Learning*. 2017.  
    https://arxiv.org/abs/1703.01161

### MCTS 与 AlphaZero

14. Levente Kocsis, Csaba Szepesvári. *Bandit Based Monte-Carlo Planning*. ECML, 2006.  
    https://doi.org/10.1007/11871842_29

15. David Silver et al. *Mastering the game of Go without human knowledge*. Nature, 2017.  
    https://doi.org/10.1038/nature24270

16. David Silver et al. *A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play*. Science, 2018.  
    https://arxiv.org/abs/1712.01815

### 无效动作掩码

17. Shengyi Huang, Santiago Ontañón. *A Closer Look at Invalid Action Masking in Policy Gradient Algorithms*. 2020.  
    https://arxiv.org/abs/2006.14171

## E.16 框架官方文档

### PyTorch

- 张量： https://pytorch.org/docs/stable/tensors.html
- 自动求导： https://pytorch.org/docs/stable/autograd.html
- `nn.Module`： https://pytorch.org/docs/stable/generated/torch.nn.Module.html
- Optimizer： https://pytorch.org/docs/stable/optim.html
- Conv2d： https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html

### Gymnasium

- Env API： https://gymnasium.farama.org/api/env/
- Spaces： https://gymnasium.farama.org/api/spaces/
- 处理 time limits： https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/
- Wrapper： https://gymnasium.farama.org/api/wrappers/

Gymnasium 官方 API 的 `step` 返回 observation、reward、terminated、truncated、info。`terminated` 表示 MDP 终局，`truncated` 表示在 MDP 外部条件下结束采样。

### Stable-Baselines3

- 总览： https://stable-baselines3.readthedocs.io/
- PPO： https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
- A2C： https://stable-baselines3.readthedocs.io/en/master/modules/a2c.html
- DQN： https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html
- 自定义策略/特征提取： https://stable-baselines3.readthedocs.io/en/master/guide/custom_policy.html
- VecEnv： https://stable-baselines3.readthedocs.io/en/master/guide/vec_envs.html
- Callback： https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html

### sb3-contrib

- MaskablePPO： https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html

官方文档明确要求评估使用 mask-aware 接口；使用 `SubprocVecEnv` 时 `action_masks` 必须在环境内部实现。

### PettingZoo

- API： https://pettingzoo.farama.org/api/
- AEC API： https://pettingzoo.farama.org/api/aec/
- Parallel API： https://pettingzoo.farama.org/api/parallel/

本项目安装 PettingZoo，但当前主 RL 路径是内部推进对手的 Gymnasium 单智能体环境。

## E.17 历史材料与当前事实的分界

仓库中的历史训练评论用于重建研究过程，但引用时遵守：

- 配置文件说明实验意图；
- 日志/结果说明当时观察；
- 成对消融才提供较强因果证据；
- 当前源码定义当前行为；
- 当前本机冒烟定义当前接口是否可运行；
- 大规模能力仍需新的多种子实验。

当四者冲突时，不应把最旧的评论提升为当前事实。

## E.18 建议阅读顺序

1. 正文 00–12，建立任务与框架；
2. 根据主线读 15–17；
3. 实际跑 MaskablePPO；
4. 再读 18–22 的进阶方法；
5. 用 23–27 设计实验；
6. 需要核验时查本附录对应符号；
7. 最后阅读原始论文，对照项目取舍。

