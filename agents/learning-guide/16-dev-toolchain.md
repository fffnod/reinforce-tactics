> 返回：[指南目录](README.md) · [上一章](15-llm-bots.md) · [下一章](17-capstone-projects.md) · [索引](../AGENTS.md)

# 第 16 章：开发与测试工具链

本章面向「不仅跑训练、还要改代码」的读者：如何装 dev 依赖、跑测试、用 linter / 类型检查 / pre-commit，以及 **为什么 RL 代码特别需要测试**。读完后你应能在本机执行一轮「测一下再提交」的最短闭环。

提交作者环境（本机常无 global git user）见：
[`../usage/git-commit-push.md`](../usage/git-commit-push.md)。

---

## 1. 安装开发依赖

仓库根目录：

```powershell
cd D:\Grok\project2\reinforce-tactics
conda activate reinforce-tactics
pip install -e ".[dev]"
```

`pyproject.toml` 中 `dev` extra 包含：

| 包 | 用途 |
|----|------|
| `pytest` / `pytest-cov` | 单元测试与覆盖率 |
| `ruff` |  lint + 格式化 |
| `mypy` | 静态类型检查 |
| `pre-commit` | Git 提交前钩子 |

可选组合：

```powershell
# 只要 GUI
pip install -e ".[gui]"
# LLM Bot
pip install -e ".[llm]"
# 本地常见：gui + llm + dev（本机快照常如此；cloud 一般不装）
pip install -e ".[gui,llm,dev]"
```

覆盖率门槛（`pyproject.toml`）：`pytest` 默认 `--cov=reinforcetactics --cov-fail-under=65`。只跑少量文件时若触发全局 cov 失败，可临时：

```powershell
python -m pytest tests/test_fonts.py -q --no-cov
```

---

## 2. pytest 示例

### 2.1 与 Gym / 环境相关

```powershell
# 环境 step / reset / 动作空间等
python -m pytest tests/test_gym_env.py -q --no-cov

# 动作掩码
python -m pytest tests/test_rl_masking.py -q --no-cov

# 观察构造
python -m pytest tests/test_observation.py -q --no-cov
```

### 2.2 与字体 / i18n 相关

中文 UI 曾踩过 Windows SysFont 崩溃问题（见排查文档）。相关测试：

```powershell
python -m pytest tests/test_fonts.py -q --no-cov
python -m pytest tests/test_language_menu.py -q --no-cov
```

### 2.3 Bot / 锦标赛 / 回放确定性

```powershell
python -m pytest tests/test_bot_base.py tests/test_random_bot.py tests/test_noop_bot.py -q --no-cov
python -m pytest tests/test_tournament.py -q --no-cov
python -m pytest tests/test_replay_determinism.py -q --no-cov
```

### 2.4 全量（提交前推荐）

```powershell
python -m pytest -q
```

首次全量会较慢；失败时读断言与失败用例名，优先修 **确定性 / 掩码 / 奖励符号** 类问题。

---

## 3. ruff、mypy、pre-commit

### 3.1 ruff

配置在 `pyproject.toml` 的 `[tool.ruff]`：Python 3.11+、行宽 127 等。

```powershell
# 检查
ruff check .
# 自动修复可修项
ruff check --fix .
# 格式化
ruff format .
```

### 3.2 mypy

```powershell
mypy .
```

项目对部分模块开启了 `ignore_errors`（历史债），全树仍可能有噪声；**以 CI 与 pre-commit 配置为准**。本地解释器需已安装项目依赖（mypy 用 system 环境解析 numpy/torch 等）。

### 3.3 pre-commit

配置文件：`.pre-commit-config.yaml`。

钩子包括：

- 通用：尾随空白、EOF、YAML/JSON、大文件、合并冲突标记
- **ruff** + **ruff-format**
- **mypy**（对整棵树，`pass_filenames: false`）

一次性安装钩子：

```powershell
pre-commit install
```

对全部文件试跑（首次会下 hook 环境，较慢）：

```powershell
pre-commit run --all-files
```

提交时钩子失败 → **先修再 commit**，不要 `--no-verify` 除非你明确知道在做什么。

### 3.4 与本机 Git 作者的关系

pre-commit 通过后，`git commit` 仍可能因 **Author identity unknown** 失败。本机约定：

- **不要**改 global `user.name` / `user.email`
- 用环境变量 `GIT_AUTHOR_*` / `GIT_COMMITTER_*`

完整命令与踩坑：[`../usage/git-commit-push.md`](../usage/git-commit-push.md)。

---

## 4. 为什么 RL 代码特别需要测试

| 风险 | 没有测试时会发生什么 | 测试能钉住什么 |
|------|----------------------|----------------|
| **非确定性** | 同 seed 训练结果对不上；「修了 bug」其实是运气 | `seed`、回放轨迹、rng 平局决胜 |
| **动作掩码错误** | 采样非法动作 → 环境惩罚或静默失败 → 策略学歪 | `test_rl_masking`、合法动作集合一致性 |
| **观察与空间形状** | checkpoint 与地图尺寸 / FOW 通道不一致，加载才炸 | obs 通道数、pad、visibility 键 |
| **奖励符号/量级** | 赢棋给负分、塑形爆炸、value 网络学崩 | 终局奖励符号、简单 episode 回报范围 |
| **合同破坏** | Bot 不 `end_turn` 卡死循环；env 不换边 | `take_turn` 后 `current_player`、`game_over` |
| **回归** | 改 SimpleBot 购买逻辑拖垮课程阶段 | Bot 单元测试 + 小型锦标赛 smoke |

RL 的失败常常是 **静默变差**（胜率从 60% 掉到 40%），而不是立刻异常。自动化测试至少守住 **接口与不变量**；胜率回归还要靠固定评估协议（第 13 章）。

---

## 5. 建议的日常节奏

```text
改代码
  → ruff check --fix . && ruff format .
  → 相关 pytest（gym / bot / 你改的模块）
  → 需要提交时：pre-commit + 作者环境变量 commit
  → 确认 commit 成功后再 push
```

训练实验本身的产物（`models/`、长日志、大回放）不要误提交；以 `.gitignore` 为准。

---

## 6. 自检

- [ ] 已 `pip install -e ".[dev]"` 且 `pytest` / `ruff` 可运行
- [ ] 能单独跑 `test_gym_env` 与 `test_fonts` 一类冒烟
- [ ] 知道 pre-commit 会跑 ruff 与 mypy
- [ ] 知道提交作者 env 文档路径
- [ ] 能解释「掩码 + 确定性」为何对 RL 测试关键

---

## 7. 延伸阅读

| 文档 | 内容 |
|------|------|
| [`../usage/git-commit-push.md`](../usage/git-commit-push.md) | commit 作者、钩子失败重试、push 顺序 |
| [`../usage/local-run-guide.md`](../usage/local-run-guide.md) | 环境激活与 GUI / 训练 |
| [`../troubleshooting/chinese-font-display.md`](../troubleshooting/chinese-font-display.md) | 中文字体问题 |
| [`../../docs/zh/LOCAL_DEPLOY.md`](../../docs/zh/LOCAL_DEPLOY.md) | 完整本地部署 |
| `pyproject.toml` | ruff / mypy / pytest / extras 权威配置 |
