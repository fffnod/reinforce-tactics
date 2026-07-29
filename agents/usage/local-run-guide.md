# 本地运行与基础操作指南

**分类**：使用类
**适用**：Windows + Conda 环境 `reinforce-tactics`
**相关**：`docs/LOCAL_DEPLOY.md`（部署）、`main.py`（入口）

---

## 1. 启动前准备

```powershell
cd D:\Grok\project2\reinforce-tactics   # 按本机路径调整
conda activate reinforce-tactics
python -V    # 期望 3.12.x
```

确认在项目根目录（存在 `main.py`、`maps/`、`reinforcetactics/`）。

---

## 2. 启动游戏界面（GUI）

```powershell
python main.py
# 或显式：
python main.py --mode play
```

默认 `--mode` 为 `play`，会打开 pygame 窗口进入主菜单。

### 2.1 主菜单常见项

| 含义 | 作用 |
|------|------|
| 新游戏 / New Game | 选模式、地图、玩家后开局 |
| 读档 / Load Game | 继续存档 |
| 回放 / Watch Replay | 观看录像 |
| 设置 / Settings | 语言、图形、API Keys 等 |
| 退出 / Exit | 退出 |

### 2.2 推荐第一局（人机）

1. **新游戏**
2. 模式选 **1v1**
3. 地图选 **beginner / starter**（`maps/1v1/` 下）
4. **玩家配置**：
   - Player 1 → **Human**
   - Player 2 → **Computer**，Bot 选 **SimpleBot**（最弱规则 AI）
5. **Start Game / 开始游戏**

### 2.3 选择 AI 类型

在玩家配置界面：

- 切换 **Human / Computer**
- 电脑行点击 Bot 类型循环切换：

| 类型 | 说明 |
|------|------|
| SimpleBot | 弱，适合学操作 |
| MediumBot | 中等 |
| AdvancedBot | 较强 |
| OpenAI / Claude / Gemini Bot | 需 `[llm]` + API Key |
| ModelBot | 使用训练好的 `.zip` 模型（若菜单提供） |

LLM 需在 **设置 → API Keys** 或环境变量中配置：

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

### 2.4 局内操作（摘要）

| 操作 | 方式 |
|------|------|
| 选单位 | 左键点击己方单位 |
| 移动 / 攻击 | 点击高亮格子或目标；按菜单提示 |
| 产兵 | 点击己方 HQ/建筑，用金币购买 |
| 结束回合 | 点击 **End Turn** |
| 取消 | **Esc** |

胜利：占领敌方 HQ，或消灭对方全部单位。

### 2.5 中文界面

设置中切换语言为 **中文**。若出现乱码/方框，见：

`agents/troubleshooting/chinese-font-display.md`

---

## 3. 简单训练（命令行）

训练在终端 headless 运行，不经过完整主菜单对战 UI。

### 3.1 冒烟（确认能训）

```powershell
python main.py --mode train --algorithm ppo --timesteps 2000 --opponent bot
```

### 3.2 常用训练示例

```powershell
# 默认 PPO，规则 bot，10 万步
python main.py --mode train --algorithm ppo --timesteps 100000 --opponent bot

# 固定简单地图
python main.py --mode train --algorithm ppo --timesteps 50000 --opponent bot --map-file maps/1v1/beginner.csv

# 自定义模型名
python main.py --mode train --algorithm ppo --timesteps 50000 --opponent bot --model-name my_first_ppo
```

| 参数 | 含义 |
|------|------|
| `--algorithm` | `ppo` / `a2c` / `dqn` |
| `--timesteps` | 总步数 |
| `--opponent` | `bot` / `random` / `noop` / `self` |
| `--map-file` | 地图 CSV 路径 |
| `--model-name` | 保存名 |

### 3.3 产物目录

| 路径 | 内容 |
|------|------|
| `models/` | 最终模型 zip |
| `checkpoints/` | 中途检查点 |
| `tensorboard/` | 日志 |

```powershell
tensorboard --logdir ./tensorboard
```

### 3.4 评估

```powershell
python main.py --mode evaluate --model models/ppo_final.zip --episodes 5
python main.py --mode evaluate --model models/ppo_final.zip --episodes 3 --render
```

### 3.5 其它

```powershell
python main.py --help
python main.py --mode stats
```

高级脚本见 `scripts/train/`（AlphaZero、Feudal、Self-play 等）。

---

## 4. 依赖档位速查

| Extra | 用途 | 本机参考状态 |
|-------|------|----------------|
| base | RL 核心 | 已装 |
| gui | 游戏界面 | 已装 |
| llm | LLM bot | 已装 |
| dev | pytest/ruff/mypy | 已装 |
| cloud | GCS 上传 | 未装（本地一般不需要） |

```powershell
pip install -e ".[gui,llm,dev]"
```

---

## 5. 建议的第一次路径

```text
1. conda activate reinforce-tactics
2. python main.py
3. 新游戏 → 1v1 → beginner → Human vs SimpleBot
4. 打完一局熟悉 End Turn
5. python main.py --mode train --algorithm ppo --timesteps 2000 --opponent bot
6. 确认 models/ 下生成 zip
```
