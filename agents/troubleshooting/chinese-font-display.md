# 中文界面显示为异常字符 / 方框

**分类**：问题排查类
**现象**：进入游戏后，在设置中切换语言为「中文」，菜单与按钮出现乱码、方框（tofu）或无法正确显示汉字。
**状态**：已在源码中修复（`reinforcetactics/utils/fonts.py` + `language.py`）
**验证环境**：Windows 10/11，pygame-ce 2.5.7，Python 3.12，系统存在 `C:\Windows\Fonts\msyh.ttc`

---

## 1. 现象

- 英文界面正常。
- 切换到 **chinese** 后，UI 字符串变为空白框、问号或不可读字符。
- 部分环境在切换时还可能因字体子系统异常而间接失败（见根因）。

---

## 2. 根因分析

### 2.1 设计预期

项目自带字体（`assets/fonts/`）：

- `NotoSans-Regular.ttf` — 拉丁文 UI
- `PixelifySans-Regular.ttf` — 标题像素风

二者 **不含完整 CJK 字形**。
因此 `fonts.py` 在语言为 `chinese` / `korean` 时，应回退到 **系统 CJK 字体**。

### 2.2 实际故障（Windows + pygame-ce）

`pygame.font.get_fonts()` 与 `pygame.font.SysFont(...)` 在扫描 Windows 注册表字体时，可能遇到 **字体路径类型不是 str** 的条目，从而在 `ntpath.splitext` 处抛出：

```text
TypeError: expected str, bytes or os.PathLike object, not int
```

影响：

1. **无法枚举**系统字体列表。
2. **SysFont 全线失败**（包括 `Microsoft YaHei` 等）。
3. 旧逻辑在异常处理上不够宽（未捕获 `TypeError`），或最终落到 `Font(None)` / 无 CJK 的默认字体。
4. 界面用无 CJK 字形的字体去 `render("中文...")` → **方框/异常字符**。

对照实验（修复前）：

| 方式 | 结果 |
|------|------|
| `pygame.font.SysFont("Microsoft YaHei", 24)` | TypeError |
| `pygame.font.get_fonts()` | TypeError |
| `pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 24).render("中文")` | **成功** |

结论：系统上 **微软雅黑文件可用**，问题在 pygame 的 **SysFont/注册表扫描**，不是系统没装中文字体。

### 2.3 次要问题：语言切换未清字体缓存

字体缓存键仅为 `(kind, size)`，不含语言。切换语言后若不清理缓存，可能继续使用切换前的 Latin 字体实例。
修复时在 `Language.set_language` 中调用 `clear_font_cache()`。

### 2.4 主菜单仍乱码、设置却正常（第二阶段）

**现象（第一阶段修复后）**：设置页中文正常，返回主界面标题/选项仍是方框。

**原因**：`Menu` 基类在 `__init__` 时把 `title_font` / `option_font` **存成实例属性**。主菜单在英文下创建后一直存活；切换中文后 `_refresh_options()` 只换了文案字符串，**没有换字体对象**，仍用 Noto/Pixelify 画汉字 → 方框。
设置子菜单里部分界面在语言切换后会 `refresh` 或重新 `get_font()`，或用户主观上主要看了已能正确渲染的部分，因此表现为「设置正常、主界面不行」。

**修复**：

- `Menu.refresh_fonts()` / `_ensure_fonts_for_language()`：绘制前若语言变化则重载字体
- `MainMenu._refresh_options`、`SettingsMenu._refresh_options`、`LanguageMenu._set_language` 中显式 `refresh_fonts()`

---

## 3. 解决方案（已实现）

### 3.1 代码改动

| 文件 | 改动 |
|------|------|
| `reinforcetactics/utils/fonts.py` | CJK 优先 **按文件路径** 加载（Windows：`msyh.ttc`、`simhei.ttf` 等）；`get_fonts`/`SysFont` 失败时捕获更广异常；新增 `clear_font_cache()` |
| `reinforcetactics/utils/language.py` | `set_language` 成功/回退后清理字体缓存 |
| `tests/test_fonts.py` | 放宽 `get_fonts` 断言；新增中文渲染测试 |

加载优先级（CJK）：

1. 直接打开系统字体文件（如 `C:\Windows\Fonts\msyh.ttc`）
2. 再尝试 `SysFont` 候选名（在 SysFont 可用的平台上）
3. 最后 `Font(None)`（可能仍无 CJK，仅兜底）

### 3.2 用户侧操作

1. 更新到包含上述修复的代码（当前开发分支）。
2. 重新启动游戏：

```powershell
conda activate reinforce-tactics
cd <repo-root>
python main.py
```

3. 设置 → 语言 → **中文**。
4. 菜单应显示正常汉字。

若仍异常，检查系统是否存在：

```text
C:\Windows\Fonts\msyh.ttc
C:\Windows\Fonts\simhei.ttf
```

可用则几乎总能直读成功。极简系统若无任何中文字体，需安装「中文语言包 / 微软雅黑」或把 Noto CJK 字体放进 `assets/fonts/`（代码已预留若干文件名探测）。

### 3.3 开发验证命令

```powershell
python -c "import pygame; pygame.init(); from reinforcetactics.utils.language import get_language; from reinforcetactics.utils.fonts import get_font, clear_font_cache, _resolve_cjk_font_file; get_language().set_language('chinese'); clear_font_cache(); print(_resolve_cjk_font_file()); print(get_font(28).render('中文设置', True, (255,255,255)).get_size())"

pytest tests/test_fonts.py -v --cov-fail-under=0
```

期望：打印出 `...\msyh.ttc`（或其它 CJK 路径），render 尺寸宽高均 > 0；测试全绿。

---

## 4. 经验小结

| 点 | 说明 |
|----|------|
| 不要只依赖 `SysFont`/`get_fonts` 做 CJK | Windows 上 pygame-ce 可能坏 |
| 优先 **Font(绝对路径)** | 稳定、可测 |
| 语言切换必须 **清字体缓存** | 缓存键未含语言 |
| 打包离线包时 | 目标机一般也有 `msyh.ttc`；若无，需附带 CJK 字体文件 |

---

## 5. 相关索引

- 字体实现：`reinforcetactics/utils/fonts.py`
- 语言切换：`reinforcetactics/utils/language.py`
- 使用说明：`agents/usage/local-run-guide.md`
- 总索引：`agents/AGENTS.md`
