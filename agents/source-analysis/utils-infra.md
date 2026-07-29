> 返回：[源码总览](overview.md) · [算法总览](../algorithms/overview.md) · [索引](../AGENTS.md)

# 基础设施：设置、语言、字体、IO、回放与视频

本文覆盖 `reinforcetactics/utils/` 中与全局配置、本地化、存档回放相关的模块。

---

## 位置

| 路径 | 角色 |
|------|------|
| `reinforcetactics/utils/settings.py` | `Settings` / `settings.json` |
| `reinforcetactics/utils/language.py` | `TRANSLATIONS` 与当前语言 |
| `reinforcetactics/utils/fonts.py` | 跨平台字体（含 CJK 回退） |
| `reinforcetactics/utils/file_io.py` | 地图 / 存档 / 回放文件 |
| `reinforcetactics/utils/replay_player.py` | GUI 回放器 |
| `reinforcetactics/utils/replay_actions.py` | 按 schema 回放动作到 `GameState` |
| `reinforcetactics/utils/video.py` | 无头 MP4 录制 |
| `reinforcetactics/utils/clipboard.py` | 剪贴板（菜单粘贴） |
| `reinforcetactics/utils/run_config.py` | 运行时配置辅助 |
| `reinforcetactics/utils/dependency_checker.py` | 可选依赖检查 |

---

## 文件清单

| 符号 | 说明 |
|------|------|
| `Settings` | 默认值合并、读写 `settings.json` |
| `get_settings` | 进程内单例访问 |
| `TRANSLATIONS` | `english` / `chinese` / 其他语言大字典 |
| `get_language` / `set_language` / `t(...)` | 当前语言与取词 |
| `get_font` / `get_display_font` | 正文 Noto Sans / 标题 Pixelify；CJK 系统字体 |
| `FileIO.load_map` / `save_game` / `load_replay` 等 | 统一 IO |
| `ReplayPlayer` | 播放控制条与逐步状态 |
| `execute_replay_action` / `get_schema_version` | v1–v3 回放兼容 |
| `record_game_to_video` 等 | Colab/CI 无显示录屏 |

---

## 职责

1. **持久化用户偏好**：语言、分辨率、精灵路径、启用单位、LLM API Key。
2. **UI 文案本地化**：所有菜单键走翻译表。
3. **字体正确显示**：打包字体覆盖拉丁；中文/韩文直读系统 TTF/TTC。
4. **地图与存档**：CSV 地图、JSON 存档/回放。
5. **确定性回放**：用记录的结果字段改状态，避免重算引擎 RNG 漂移。
6. **无头视频**：训练/笔记可视化。

---

## 数据结构

### `settings.json` 主要节

| 节 | 内容 |
|----|------|
| `language` | `"english"` / `"chinese"` / … |
| `paths` | maps, videos, replays, saves, models |
| `video` | fullscreen, resolution, fps |
| `audio` | 音量开关 |
| `graphics` | 精灵路径、是否用 tile sprites、动画开关 |
| `llm_api_keys` | openai / anthropic / google |
| `game.enabled_units` | 默认八兵种代码列表 |

`Settings._merge_with_defaults`：文件缺键时补默认，避免旧配置崩溃。

### 翻译

`TRANSLATIONS[lang][key] -> str`。键风格混用 `main_menu.title` 与历史扁平键；UI 侧按所用键查询。

### 回放 schema

| 版本 | 特征 |
|------|------|
| v1 | 基础动作重放（可能重入引擎） |
| v2 | 结果字段（HP after、击杀、反击）直接改状态 |
| v3 | 在 v2 上增加 `actor_unit_id` / `target_unit_id` 稳定引用 |

`get_schema_version(game_info)` 缺省为 1。

### 地图加载

`FileIO.load_map(path, for_ui=False)`：
- 训练：原始 CSV 网格。
- UI：可加海洋边框与最小尺寸填充（`for_ui=True`）。

---

## 核心逻辑

### 字体选择（摘要）

1. 非 CJK：`assets/fonts/NotoSans-Regular.ttf`（正文）、`PixelifySans-Regular.ttf`（标题）。
2. CJK（`chinese` / `korean`）：**优先**直接路径加载（Windows 如 `C:\Windows\Fonts\msyh.ttc`），避免 pygame-ce `SysFont` 扫注册表崩溃。
3. 失败再回退候选族名列表（微软雅黑、苹方、Noto CJK 等）。

详见排查文档链接。

### 回放路径

```text
ReplayPlayer / video.record_*
    → get_schema_version
    → execute_replay_action(game_state, action_record)
    → 可选 Renderer 帧 → MP4
```

`replay_actions` 与 `video` 共用执行逻辑，保证两条播放路径一致。

### Settings 生命周期

应用启动加载 → 设置菜单修改 → `save()` → 渲染/Bot/路径读取 `get_settings()`。

---

## 与需求关系

| 需求 | 落点 |
|------|------|
| 中文界面 | `language.py` + 设置菜单 |
| 中文不显示方框 | `fonts.py` 直读 TTC |
| 训练与 GUI 同一地图 | `FileIO.load_map` |
| 录像复现对局 | 回放 schema v2/v3 |
| Notebook 导出 MP4 | `video.py` + dummy SDL |
| LLM 密钥不进代码 | `settings.json` / 环境变量 |

---

## 相关算法

无直接 RL 算法。回放确定性影响评估视频与人眼验收，与 [evaluation-and-elo.md](../algorithms/evaluation-and-elo.md) 的「可复现评估」互补。

---

## 延伸阅读

- 中文字体问题：[`troubleshooting/chinese-font-display.md`](../troubleshooting/chinese-font-display.md)
- 汉化覆盖清单：[`usage/chinese-i18n-coverage.md`](../usage/chinese-i18n-coverage.md)
- UI 菜单导航：[ui-and-menus.md](ui-and-menus.md)
- 测试：`tests/test_settings.py`、`test_fonts.py`、`test_save_replay.py`、`test_replay_determinism.py`
- 字体资产：`assets/fonts/README.md`
