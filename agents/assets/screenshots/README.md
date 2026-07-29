# 文档截图资源

本目录存放知识库 / 说明文档用的界面截图。由脚本生成，默认 **中文** UI。

## 生成方式

在仓库根目录、已激活 `reinforce-tactics` 环境时：

```powershell
cd D:\Grok\project2\reinforce-tactics
conda activate reinforce-tactics
python scripts/_capture_doc_screenshots.py
```

脚本会打开 pygame 窗口（短暂）、绘制各菜单并保存 PNG，无需人工点选。

## 当前文件

| 文件 | 内容 |
|------|------|
| `01-main-menu-zh.png` | 主菜单 |
| `02-settings-zh.png` | 设置 |
| `03-graphics-zh.png` | 图形设置 |
| `04-replay-select-zh.png` | 选择回放 |
| `05-game-mode-zh.png` | 选择游戏模式 |
| `06-map-select-1v1-zh.png` | 1v1 选图 |
| `07-game-board-beginner.png` | Beginner 地图对局画面（含示例单位，pixel_art） |

## 在 Markdown 中引用

相对路径示例（从 `agents/troubleshooting/`）：

```markdown
![主菜单](../assets/screenshots/01-main-menu-zh.png)
```

从 `agents/usage/`：

```markdown
![图形设置](../assets/screenshots/03-graphics-zh.png)
```

## 说明

- **可以**用脚本批量截菜单，适合写文档插图。
- 完整「交互式」整局录像仍需你本机手动操作；脚本覆盖的是静态界面帧。
- 若本机无显示器 / CI，可尝试设置 `SDL_VIDEODRIVER=dummy` 再改脚本为纯 Surface（当前 Windows 使用真实 display）。
