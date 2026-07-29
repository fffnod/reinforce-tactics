# GUI 回放：终局自动保存导致重复条目与按钮语义混乱

**分类**：问题排查
**相关代码**：

- `reinforcetactics/app/game_loop.py`（`GameSession.run` / `_handle_game_over`）
- `reinforcetactics/ui/menus/in_game/game_over_menu.py`（「保存回放」）
- `reinforcetactics/ui/menus/save_load/replay_selection_menu.py`（回放列表）
- 对照：锦标赛 `tournament/runner.py` 的 `save_replays`（**另一条路径**）

**状态**：已改为 **仅用户确认后保存**（GUI）

---

## 1. 现象

1. 人机对战只打了一局，回放列表里出现 **两条** 同日、同对阵、同地图、同回合数的记录。
2. 结算界面有「保存回放」，但即使用户不点，磁盘上也可能已经有文件。
3. 用户点了「保存回放」后，更容易出现 **双文件**（差几秒、内容几乎相同，仅时间戳不同）。
4. （相关）列表曾混入 `tournament_results/**/llm_logs/game_*.json`，显示 Incomplete / Unknown Map，无法播放——已另做过滤，见 §5。

---

## 2. 根因

### 2.1 双重写入（重复 7.29 类记录）

旧逻辑：

```text
对局 game_over
  → GameSession._handle_game_over()
      → save_replay_to_file()          # 自动，无条件
      → GameOverMenu
            → 用户再点「保存回放」
                → 再次 save_replay_to_file()  # 新文件名（带新时间戳）
```

两份 JSON 动作序列相同，只差 `timestamp` / `game_info.end_time`。

中途退出旧逻辑还会在 `action_history` 非空时 **自动存未完成回放**，进一步增加「意外文件」。

### 2.2 按钮语义与自动保存冲突

- 自动保存 → 「不点也会存」
- 菜单仍写「保存回放」→ 用户以为只有确认才存

两条路径叠在一起，**不是**为锦标赛批量回放设计的（锦标赛见下）。

### 2.3 与「批量自动对弈」的关系

| 场景 | 是否自动存回放 | 入口 |
|------|----------------|------|
| GUI 人机/本地对局 | **现已否**；仅「保存回放」 | `game_loop` + `GameOverMenu` |
| 锦标赛 / Docker | 由配置 `save_replays` 控制（默认常为 true） | `tournament/runner.py` |
| 评估脚本等 | 各自 CLI/参数 | `scripts/eval_agent.py` 等 |

GUI 旧自动保存 **不是** 锦标赛批量管线；批量走 runner 配置。

---

## 3. 修改后的逻辑（当前约定）

### 3.1 GUI

| 事件 | 行为 |
|------|------|
| 对局正常结束 | **不**自动写 `replays/`；弹出结算菜单 |
| 用户点「保存回放」 | 调用 `save_replay_to_file()`；同一结算界面再次点击则复用 `last_replay_path`，不写第二份 |
| 用户只点「主菜单 / 退出」 | **不**保存回放 |
| 中途退出（暂停→回菜单等） | **不**自动保存回放 |

### 3.2 锦标赛 / 评估

**不变**：仍由 `save_replays` 等配置决定是否批量落盘，与 GUI 结算菜单无关。

---

## 4. 代码改动要点

### `game_loop.py`

- `_handle_game_over`：去掉 `save_replay_to_file()` 自动调用。
- `run` 在非 `game_over` 退出时：去掉「有 `action_history` 就自动存」的分支。

### `game_over_menu.py`

- `_save_replay`：用户确认时才写入；用 `last_replay_path` 做同屏幂等，避免连点重复文件。

### 验证建议

1. 新开一局打完，**不点**「保存回放」→ `replays/` 不应新增文件。
2. 再打一局，点「保存回放」→ 出现 **一个** `replay_*.json`。
3. 同一结算界面再点一次「保存回放」→ 仍只有一个文件。
4. 锦标赛（`save_replays: true`）仍应按配置写回放。

---

## 5. 相关：回放列表误收录 LLM 日志

**现象**：列表底部出现 Incomplete / Unknown Map（如 `game_20251223_...`）。

**原因**：扫描 `tournament_results` 时把 `llm_logs/game_*.json`（对话日志，无 `game_info`/`actions`）当成回放。

**处理**（`replay_selection_menu.py`）：

- 跳过 `llm_logs` 目录；
- 仅收录具备 `game_info` + `actions`（或 `action_history`）的 JSON；
- 锦标赛回放优先 `replays/` 下的 `game_*.json` / 文件名含 `replay`。

---

## 6. 用户侧清理建议

- 已产生的重复 `replay_YYYYMMDD_*.json`：可人工删除内容重复的一份。
- 无法播放的 `llm_logs` 下文件：**不要**当回放删业务数据前先确认；过滤后列表应不再显示它们。

---

## 7. 延伸阅读

- 源码会话流：[`../source-analysis/app-runtime.md`](../source-analysis/app-runtime.md)
- 回放 IO / schema：[`../source-analysis/utils-infra.md`](../source-analysis/utils-infra.md)
- 锦标赛：[`../source-analysis/tournament-system.md`](../source-analysis/tournament-system.md)
