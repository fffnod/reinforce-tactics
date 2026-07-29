# 可维护性与代码质量评审

**日期：** 2026-03-06
**范围：** 整个仓库——架构、代码质量、整合机会与体验改进。

---

## 执行摘要

Reinforce Tactics 架构良好，核心游戏逻辑、RL 环境、UI 与 tournament 系统分离清晰。近期 PR 已处理 linting（ruff/mypy）、部分代码整合，以及 50% 覆盖率底线。本评审识别**下一层级**改进：系统性重复、数据完整性缺陷，以及随代码库增长会日益痛苦的结构模式。

**按严重性分类的发现：**

| 严重性 | 数量 | 摘要 |
|----------|-------|---------|
| Critical | 2 | Settings 中数据损坏缺陷；ModelBot 中损坏的 action mask |
| High | 8 | 核心逻辑重复（观测、动作分发、mask）；RL 环境间逻辑不一致 |
| Medium | 12 | 魔法数字、缺失枚举、竞争路径系统、print vs logging |
| Low | 10 | 死代码、次要不一致、风格问题 |

---

## 严重问题

### 1. Settings 浅拷贝在运行时污染默认值

**文件：** `reinforcetactics/utils/settings.py:54,57,180`

`DEFAULT_SETTINGS.copy()` 是嵌套字典的浅拷贝。任何对嵌套值的运行时修改（例如 `settings["graphics"]["sprites_path"] = "new"`）会永久污染类级 `DEFAULT_SETTINGS`，影响所有未来实例与 `reset_to_defaults()` 调用。

**修复：** 在全部三处使用 `copy.deepcopy(self.DEFAULT_SETTINGS)`。

### 2. ModelBot action mask 始终全零，再被覆盖为全一

**文件：** `reinforcetactics/game/model_bot.py:184-245`

`_compute_action_mask` 用 `.get("targets", [])` 与 `.get("positions", [])`（字典风格）访问合法动作，但 `get_legal_actions()` 返回的动作使用直接键访问（例如 `action["target"].x`）。mask 循环遍历空列表，产生全零。第 244-245 行的回退再设 `mask[:] = 1.0`，使每个动作看起来都合法——完全击败 action masking。

**修复：** 将数据访问模式与 `get_legal_actions()` 返回格式对齐，匹配 `gym_env.py` 的 mask 构建代码。

---

## 高优先级问题

### 3. 观测构建重复 4 次，玩家视角逻辑已分叉

**文件：**
- `reinforcetactics/rl/gym_env.py:219-277`（正确——尊重 `agent_player`）
- `reinforcetactics/rl/mcts.py:281-339`（缺陷——始终把 player 1 金币放在前面）
- `reinforcetactics/game/model_bot.py`（缺陷——与 MCTS 相同）
- `reinforcetactics/rl/feudal_rl.py`（独立再实现）

**建议：** 在新模块 `reinforcetactics/rl/observation.py` 中提取共享的 `build_observation(game_state, perspective_player, grid)` 函数。四个消费者均应调用这一实现。

### 4. 动作分发链重复 4 次且已在分叉

**文件：**
- `gym_env.py:510-662`（152 行，10 分支 if/elif）
- `self_play.py:455-543`（88 行，上述副本）
- `mcts.py:250-278`（精简版）
- `model_bot.py:255-304`（另一变体）

四者均实现相同的"解码扁平动作 → 调用 game_state 方法"逻辑，略有差异。已在分叉（例如 paralyze 在 gym_env 允许 M+S，在 self_play 仅允许 M）。

**建议：** 提取共享的 `execute_action(game_state, action_type, params)` 分发器。各消费者将自身输入格式映射到共享分发器接口。

### 5. Action mask 构建重复 3 次且实现不一致

**文件：**
- `gym_env.py:295-385`
- `mcts.py:304-337`
- `model_bot.py:161-253`（损坏，见严重 #2）

**建议：** 提取共享的 `build_action_mask(game_state, player, grid_dims)` 函数，供三者使用。

### 6. Paralyze 单位类型检查不一致

- `gym_env.py:607` — 允许 Mage（`M`）**与** Sorcerer（`S`）
- `self_play.py:514` — 仅允许 Mage（`M`）
- `model_bot.py:439` — 仅允许 Mage（`M`）

一侧存在逻辑缺陷。应定义一次并处处引用。

### 7. GameMechanics 中 8 个几乎相同的"范围内找单位"方法

**文件：** `reinforcetactics/game/mechanics.py`

`get_adjacent_enemies`、`get_adjacent_allies`、`get_adjacent_paralyzed_allies`、`get_healable_allies`、`get_curable_allies`、`get_hasteable_allies`、`get_defence_buffable_allies`、`get_attack_buffable_allies`——全部遵循相同模式：遍历单位、检查玩家/生命、计算曼哈顿距离、应用过滤谓词。

**建议：** 替换为单一 `get_units_in_range(center, units, min_range, max_range, predicate)` 函数。消除约 150 行重复。

### 8. `attack_unit()` 中反击伤害计算两次

**文件：** `reinforcetactics/game/mechanics.py:412-428 vs 431-447`

实际反击伤害施加与 response 字典中的反击伤害用同一公式独立计算。若只修一块不修另一块，会静默分叉。

**修复：** 反击伤害计算一次，存入变量，同时用于施加与 response。

### 9. AlphaZero checkpoint 缺少架构参数

**文件：** `reinforcetactics/rl/alphazero_trainer.py:487-491, 556-575`

`_save_checkpoint` 从配置字典中省略 `num_res_blocks` 与 `channels`。`_evaluation_phase` 用默认架构参数创建对手网络。若训练使用非默认值，`load_state_dict` 会因形状不匹配失败。

**修复：** 在保存的配置中包含 `num_res_blocks` 与 `channels`；加载时使用它们。

### 10. `generate_random_map` 基底填充缺陷

**文件：** `reinforcetactics/utils/file_io.py:301,347`

第 301 行：`np.full((height, width), "o")` 用海洋填充，但注释说是"grass"。由于塔放置（第 347 行）检查草地格子（`"p"`），随机生成地图上永远不会放置塔。

**修复：** 第 301 行将 `"o"` 改为 `"p"`，或更新塔放置逻辑。

---

## 中优先级问题

### 11. 无 `UnitType` 枚举——处处使用原始单字符字符串

单位类型（`"W"`、`"M"`、`"C"`、`"A"`、`"K"`、`"R"`、`"S"`、`"B"`）作为原始字符串比较散落在 15+ 文件中。格子有 `TileType`，单位没有等价物。

**建议：** 在 `constants.py` 中创建镜像 `TileType` 的 `UnitType` 枚举。检查单位类型处全部引用它。

### 12. `TileType` 枚举使用不一致

`constants.py` 定义 `TileType`。`game_state.py` 部分比较使用它（`TileType.TOWER.value`）。但 `tile.py`、`mechanics.py` 与 `grid.py` 专门使用原始字符串（`"m"`、`"f"`、`"h"`）。代码库应选定一种方式。

### 13. 重复的 tile-type 编码映射

- `grid.py:60` 本地定义 `tile_type_encoding`（缺少海洋 `"o"`）
- `game_state.py:1051` 本地定义 `unit_type_encoding`

这些应为 `constants.py` 中的共享常量，并应包含海洋。

### 14. 两套竞争的路径系统

`FileIO` 使用硬编码相对路径（`"saves"`、`"replays"`、`"maps/..."`），而 `Settings` 管理可配置路径。彼此不引用。经 `FileIO` 保存的游戏会忽略用户在 `Settings` 中配置的路径。

### 15. `print()` vs `logging` 分裂

Tournament 系统正确使用 `logging`。其他一切（`FileIO`、`Settings`、`Language`、`Tile`）使用带 emoji 的 `print()`。这妨碍输出控制并破坏可测试性。

**建议：** 全面采用 `logging`。库代码中的所有 `print()` 替换为适当日志级别。

### 16. 重复的地图 padding 逻辑

`FileIO._pad_map` + `FileIO.add_water_border` 与 `ReplayPlayer._pad_map_for_replay` 独立实现同一算法。

### 17. `UNIT_COLORS` 字典多余

**文件：** `reinforcetactics/constants.py:162-171`

`UNIT_COLORS` 中每项都重复 `UNIT_DATA[key]["color"]`。这是可静默分叉的死数据。

### 18. Reward shaping 与游戏规则中的魔法数字

| 位置 | 值 | 含义 |
|----------|-------|---------|
| `mechanics.py:236` | `0.9` | 防御减伤上限 |
| `game_state.py:717-724` | `1`，`2` | 塔/建筑治疗量 |
| `feudal_rl.py:457` | `10` | Manager horizon |
| `feudal_rl.py:857-863` | `0.1`，`5.0`，`-10.0` | Intrinsic reward 权重 |
| `self_play.py:414-417` | `50`，`5` | 最大动作数、最大连续无效 |
| `gym_env.py:86` | `20, 20` | 默认地图尺寸 |
| `llm_bot.py:632` | `150`，`100`，`50` | 建筑收入值 |

**建议：** 在 `constants.py` 中为玩法数值定义命名常量，并将 RL 超参作为构造参数（带文档化默认值）。

### 19. LLM bot 每次调用创建新的 API 客户端

**文件：** `reinforcetactics/game/llm_bot.py:1248` 及子类等价处

每次 `_call_llm` 调用都构造新 API 客户端，浪费连接建立时间并阻止 HTTP 连接池。

**修复：** 在 `__init__` 中创建一次客户端并复用。

### 20. Renderer 在热循环中分配 surface

**文件：** `reinforcetactics/ui/renderer.py:383-385, 674, 692-693, 710-711`

迷雾叠加、移动叠加、目标叠加与攻击范围叠加均每帧每格创建新 `pygame.Surface`。`_get_overlay` 缓存模式存在（第 531 行）但未一致应用。

### 21. 硬编码 random 对手玩家

**文件：** `reinforcetactics/rl/gym_env.py:678`

`_random_opponent_turn` 硬编码 `player=2`。若 agent 为 player 2，random 对手应为 player 1。应使用 `3 - self.agent_player`。

### 22. `_merge_with_defaults` 仅处理一层嵌套

**文件：** `reinforcetactics/utils/settings.py:63-72`

若加载的设置文件某子字典缺少部分键，合并后这些默认值会丢失。应使用递归合并。

---

## 低优先级 / 体验

### 23. `GameMechanics` 是纯静态类
所有方法均为 `@staticmethod`。普通函数模块会更简单。同理，`FileIO` 无状态——全部 `@staticmethod`。

### 24. `get_legal_actions()` 有 127 行
**文件：** `game_state.py:885-1011`。应分解为 per-action-type 辅助方法。

### 25. 可见性系统每次更新做 3 次全网格扫描
**文件：** `visibility.py:127-192`。可改用 `grid.get_capturable_tiles(player)`。

### 26. `TILE_COLORS` 有重复键
**文件：** `constants.py:46-66`。`TileType.GRASS.value` 与 `"p"` 均作为键使用且值相同。

### 27. 语言系统存储 770 行 Python 字典字面量
**文件：** `language.py:7-773`。添加翻译需编辑 Python 源码。应使用外部 JSON/TOML 文件。

### 28. 翻译覆盖不完整
西班牙语与中文缺少 `map_editor.*` 键。无警告发出。

### 29. CSV 导出不转义值
**文件：** `tournament/results.py:389-407`。应使用 `csv` 模块。

### 30. 死代码
- `file_io.py:556-584` — `export_replay_video` 是桩
- `masking.py:236-240` — 未使用 import 用 noqa 压制
- `feudal_rl.py:838` — `goal_type` 计算后从未使用
- `gym_env.py:47` — `ALL_UNIT_TYPES = ALL_UNIT_TYPES` 多余遮蔽

### 31. Bot API 密钥测试不一致
**文件：** `tournament/bots.py:451-506`。OpenAI 做真实 API 调用；Anthropic 仅实例化客户端；Google 调用 list_models。各提供商严格程度不一。

### 32. 菜单基类 `_populate_option_rects` / `_draw_content` 重复
**文件：** `ui/menus/base.py:183-323`。Rect 几何计算两次——一次命中测试，一次渲染。

---

## 建议行动计划

### 阶段 1 — 修复缺陷与数据损坏（1-2 天）
1. 修复 `Settings` 浅拷贝 → `deepcopy`（严重 #1）
2. 修复 `ModelBot` action mask 数据访问（严重 #2）
3. 修复 `generate_random_map` 海洋/草地缺陷（高 #10）
4. 修复 paralyze 单位类型不一致（高 #6）
5. 修复反击伤害双重计算（高 #8）
6. 修复 random 对手硬编码玩家（中 #21）
7. 修复 AlphaZero checkpoint 架构参数（高 #9）

### 阶段 2 — 整合重复的 RL 逻辑（3-5 天）
1. 提取共享 `build_observation()` 函数
2. 提取共享 `execute_action()` 分发器
3. 提取共享 `build_action_mask()` 函数
4. 创建 `UnitType` 枚举并处处使用
5. 将 tile-type 编码映射统一到 `constants.py`

### 阶段 3 — 代码质量改进（2-3 天）
1. 在 mechanics 中提取 `get_units_in_range()` 通用辅助
2. 全面采用 `logging`（替换 `print()`）
3. 统一路径管理（Settings ↔ FileIO）
4. 一致缓存 renderer overlay surface
5. 分解过长方法（`get_legal_actions`、`_execute_action`、`_serialize_game_state`）

### 阶段 4 — 体验改进（持续）
1. 将语言翻译外置到 JSON
2. 增加 `UnitType` 与 `TileType` 枚举使用一致性
3. 移除死代码与桩
4. 跨调用复用 LLM API 客户端
5. 将 `_merge_with_defaults` 加固为递归合并
