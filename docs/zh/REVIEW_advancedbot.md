# 代码库评审：Reinforce Tactics（advancedbot）

## 严重缺陷

### 1. `max_turns` 从未被强制执行 ✅ 已修复
- **文件：** `reinforcetactics/core/game_state.py:95, 779-842`
- `max_turns` 被存储并序列化，但从未在 `end_turn()` 中检查。游戏可无限运行。`from_dict()` 中也未从存档数据恢复（第 1259 行）。
- **修复：** 在 `end_turn()` 中加入 `max_turns` 强制执行。

### 2. 缓存交错错误 ✅ 已修复
- **文件：** `reinforcetactics/core/game_state.py:293-300, 868-1013`
- 单个 `_cache_valid` 标志在 `get_unit_count()` 与 `get_legal_actions()` 之间共享。一方设为 `True` 时，另一方返回陈旧结果。
- **修复：** 为 `unit_count` 与 `legal_actions` 使用独立缓存标志。

### 3. 已死亡攻击者的状态仍被修改 ✅ 已修复
- **文件：** `reinforcetactics/core/game_state.py:502-522`
- 攻击者被击杀并从 `self.units` 移除后，代码无条件设置 `attacker.can_move = False`。应使用 `if result['attacker_alive']` 防护。
- **修复：** 仅当 `result['attacker_alive']` 为 True 时设置 `can_move`/`can_attack`。

### 4. 合法动作 BFS 中缺少 `moving_unit` ✅ 已修复
- **文件：** `reinforcetactics/core/game_state.py:906`
- `get_legal_actions()` 省略 `moving_unit=unit`，导致单位在寻路时挡住自己。
- **修复：** 现向 `get_legal_actions()` 传入 `moving_unit=unit`。

### 5. Action mask 与动作空间不对齐
- **文件：** `reinforcetactics/rl/gym_env.py:181-185, 234-340`
- MultiDiscrete 动作空间是组合式的，但 mask 是扁平 union 式。Agent 经常选到无效组合并被惩罚。
- **说明：** 这是 MultiDiscrete 空间 per-dimension masking 的已知限制。正确修复需要 Phase 3.2 规划的 auto-regressive action head。

### 6. Random 对手是空操作 ✅ 已修复
- **文件：** `reinforcetactics/rl/gym_env.py:669-681`
- `'random'` 对手获取合法动作后执行 `pass`。
- **修复：** `_random_opponent_turn()` 现完整实现随机动作执行。

### 7. 对 `'random'`/`'self'` 从未调用对手回合 ✅ 已修复
- **文件：** `reinforcetactics/rl/gym_env.py:86, 611`
- 这些模式下 `self.opponent` 保持 `None`，因此从不调用 `_opponent_turn()`。
- **修复：** `_opponent_turn()` 按 `opponent_type` 字符串分发，而非 `opponent` 对象。

### 8. max_tokens 为 None 时 ClaudeBot 崩溃 ✅ 已修复
- **文件：** `reinforcetactics/game/llm_bot.py:1370-1380`
- Anthropic API 要求 `max_tokens`。为 None 时省略该参数导致校验错误。
- **修复：** `max_tokens` 为 None 时默认 4096，以满足 Anthropic API 要求。

## 高严重性设计问题

### 9. 非 potential-based reward shaping 压过终局信号 ✅ 已修复
- **文件：** `reinforcetactics/rl/gym_env.py:691-708`
- 基于状态的 reward 每步施加。`structure_control=5.0` 且 500 步保持 2 结构领先时，shaping 产生 5,000 reward，对比 1,000 胜利 reward。
- **修复：** Reward shaping 改为 potential-based（Phi(s') - Phi(s)），只奖励优势变化，而非维持领先。

### 10. 硬编码 rewards 绕过 reward_config ✅ 已修复
- **文件：** `reinforcetactics/rl/gym_env.py:534-661`
- 12+ 个硬编码 reward 值不受 `reward_config` 控制。
- **修复：** 所有 reward 值现从 `reward_config` 字典读取，并带合理默认值。

### 11. 裸 except 吞掉真实 bug ✅ 已修复
- **文件：** `reinforcetactics/rl/gym_env.py:663-665`
- `_execute_action` 中所有异常被转为 "invalid action" 惩罚。真实 bug 变得不可见。
- **修复：** `TypeError` 与 `AttributeError` 作为编程错误重新抛出。游戏逻辑异常仍优雅捕获。

### 12. bot act 方法中无界递归 ✅ 已修复
- **文件：** `reinforcetactics/game/bot.py`（20+ 调用点）
- `act_with_unit` 在 haste 时递归调用自身。若 `can_move` 永不变为 False，会栈溢出。
- **修复：** 加入 `MAX_RECURSION_DEPTH=10` 防护，防止 haste 栈溢出。

### 13. 山地视野加成是死代码 ✅ 已修复
- **文件：** `reinforcetactics/core/visibility.py:302-326`
- `calculate_vision_radius()` 实现了山地 +1 范围，但从未被调用。
- **修复：** `PlayerVisibility.update()` 现对单位与结构均使用 `calculate_vision_radius()`，启用基于地形的视野加成。

### 14. Model bot 的 action mask 全为 1 ✅ 已修复
- **文件：** `reinforcetactics/game/model_bot.py:149-152`
- 返回 `np.ones(...)`，模型对合法动作无任何指导。
- **修复：** 从合法动作计算真实 mask。

### 15. Self-play 权重交换无 finally 防护 ✅ 已修复
- **文件：** `reinforcetactics/rl/self_play.py:346-373`
- 每次对手动作两次 `load_state_dict` 调用，无异常安全。
- **修复：** `try/finally` 确保始终恢复原始参数。

### 16. self-play 中 swap_players 损坏 ✅ 已修复
- **文件：** `reinforcetactics/rl/self_play.py:453, 629`
- 对手回合始终假设为 player 2，不论交换状态。
- **修复：** 向 `StrategyGameEnv` 添加 `agent_player` 属性。`_execute_action`、`_get_obs`、`_compute_potential` 与 `step()` 均使用 `agent_player` 而非硬编码 player 1。`SelfPlayEnv` 在 reset 时将 `agent_player` 传播到基础 env。

### 17. Feudal RL 首次调用时 `_last_obs` 为 None
- **文件：** `reinforcetactics/rl/feudal_rl.py:596`

### 18. Tournament 竞态条件
- **文件：** `reinforcetactics/tournament/runner.py:251`
- 错误路径上 `completed_count` 在锁外递增。

## 架构关注点

### 19. GameState 是上帝对象（~50KB）
- 处理状态、CRUD、战斗、技能、回合、收入、合法动作、战争迷雾、坐标、录制、序列化、玩家配置。

### 20. bot.py 中大量重复
- `manhattan_distance`、`find_best_move_position`、`__init__` 在 SimpleBot/MediumBot 间全部重复。
- Haste 检查模式重复 17 次。

### 21. 技能方法是样板复制
- **文件：** `reinforcetactics/core/game_state.py:526-633`
- 六个 7 行方法结构完全相同。

### 22-23. 无 UnitType 枚举；TileType 枚举使用不一致
- 单位类型全程为原始字符串。TileType 存在，但多数代码使用 `'m'`、`'f'`、`'h'` 字面量。

## 性能关注点

### 24. 按位置 O(n) 查找单位
- **文件：** `reinforcetactics/core/game_state.py:302-307`
- 循环内线性扫描。应使用位置索引字典。

### 25. 用 Python 循环做 numpy masking
- **文件：** `reinforcetactics/core/game_state.py:1077-1085`
- 应向量化为 numpy 操作。

### 26-27. 每回合重复 BFS 与网格扫描
- `get_reachable_positions` 与 `find_our_hq` 被冗余调用。

## 安全关注点

### 28. 文件 I/O 无路径净化
- `save_game`、`save_replay`、`save_map` 接受任意路径并 `mkdir(parents=True)`。

### 29. API 密钥以全局可读明文存放
- **文件：** `reinforcetactics/utils/settings.py`

### 30. 浅拷贝污染 DEFAULT_SETTINGS
- **文件：** `reinforcetactics/utils/settings.py:74-85`

## 五大建议

1. **修复 RL action masking 架构** - 切换到 auto-regressive action head（Phase 3.2），以获得正确的 per-sub-action masking。
2. **分解 GameState** - 将合法动作、战斗、技能、序列化提取到专注类中。
3. ~~**修复缓存与 max_turns 缺陷**~~ ✅ 已完成 — 独立缓存标志，回合上限已强制执行。
4. ~~**整合 bot 层次**~~ ✅ 部分完成 — 已加递归防护；完整 BotBase 重构仍待做。
5. **添加 UnitType 枚举，一致使用 TileType** - 防止拼写/重构类 bug。

## 解决情况摘要

| 类别 | 总计 | 已修复 | 剩余 |
|----------|-------|-------|-----------|
| 严重缺陷（#1-8） | 8 | 7 | 1（#5 — 架构性，计划于 Phase 3.2） |
| 高严重性（#9-18） | 10 | 8 | 2（#17、#18） |
| 架构（#19-23） | 5 | 0 | 5 |
| 性能（#24-27） | 4 | 0 | 4 |
| 安全（#28-30） | 3 | 0 | 3 |
