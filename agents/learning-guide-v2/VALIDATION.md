# 第二版教材验证记录

## 1. 验证基线

```text
日期                  2026-07-29
仓库提交              69a085d（教材修改前基线）
系统                  Windows / PowerShell
Python                3.12.13
Gymnasium             1.3.0
Stable-Baselines3     2.9.0
sb3-contrib           2.9.0
PyTorch               2.13.0+cpu
设备                  CPU
```

本文件区分“完成”“部分完成”和“发现当前问题”。冒烟只验证接口和数据流，不作为策略能力结论。

## 2. 用户原始八项要求覆盖矩阵

| 原始要求 | 主要章节 | 实验/验证 | 教材内图 |
|---|---|---|---|
| 1. 以项目建立完整 RL 理解并可实践 | 00–27 全书 | env、MaskablePPO、Bootstrap、进阶冒烟 | 项目数据流、智能体闭环 |
| 2. 零 RL/数学背景，详细公式 | 03–05、13–23、附录 A | 逐章数值练习与附录 D | 折扣范围、PPO clip、置信区间 |
| 3. 循序渐进讲算法、代码与框架 | 06–12、各算法章 | PyTorch/Gymnasium/SB3 接口与短训 | Actor-Critic、动作掩码 |
| 4. 用原始论文和官方文档补充 | 附录 E | 链接与书目检查 | 正文原创图为主 |
| 5. 每种项目算法独立专章与历史困难 | 13–22、附录 C | 兼容矩阵、BC、Feudal、MCTS/AlphaZero | 历史 PPO 失败、课程、层级、搜索 |
| 6. 结合游戏、LLM、DEV，不含 Cloud | 01、09–12、24、26、27 | Bot/LLM mock/DEV 测试 | 游戏截图、LLM 管线 |
| 7. 流程图、示意图、截图与运行结果 | 全书 assets | 15 张原创图、2 张本地截图、JSON 结果 | assets 内独立保存 |
| 8. 正式入门读物与详细实操 | README、00–27、附录 B/D | 同源构建、链接/PDF/HTML 验证 | 连续阅读 HTML/PDF |

## 3. 算法覆盖

| 算法/训练策略 | 独立章节 | 当前状态表述 | 实际验证 |
|---|---:|---|---|
| DQN | 13 | 默认 MultiDiscrete 不兼容；Flat 可构造 | 与当前 SB3 构造结果一致 |
| A2C | 14 | 可构造，但普通 A2C 不消费掩码 | 构造通过 |
| PPO | 15 | 基础算法；无遮罩路径有组合动作局限 | 构造通过 |
| MaskablePPO | 16 | 主训练路径 | CPU 64 步通过 |
| Bootstrap | 17 | 课程控制器 | 1 阶段短流程完成 |
| 行为克隆 | 18 | warm start，价值头留给 PPO | 29 条示范、1 epoch、checkpoint |
| 自对弈 | 19 | 历史池实验路径 | 组件与 128 项相关测试通过；完整 CLI 见问题记录 |
| Feudal RL | 20 | 实验路径，两层 PPO | 64 步训练与评估完成；结束保存见问题记录 |
| MCTS | 21 | AlphaZero 搜索组件 | 2 simulations，概率和 1 |
| AlphaZero | 22 | 实验路径 | 1 局、4 样本、1 次联合更新、checkpoint |

## 4. CPU 冒烟结果

### 4.1 动作空间兼容

```text
MultiDiscrete([10, 8, 6, 6, 6, 6])
  PPO           construct_ok
  A2C           construct_ok
  DQN           AssertionError：只支持 Discrete
  MaskablePPO   construct_ok

Flat Discrete(512)
  PPO / A2C / DQN / MaskablePPO 均 construct_ok
```

### 4.2 掩码

在 `beginner.csv`、seed 42 初态：

```text
逐维 true 数          [2, 3, 2, 2, 2, 2]
笛卡尔积组合数        96
领域层合法动作数      7
过度近似比例          13.714
```

这是一条当前短探针，不是正文所述历史“约 99% 无效组合”基准的复现。历史图已明确标“历史数据”。

### 4.3 MaskablePPO

```text
训练步数              64
预测动作              5
后续 step reward      0.797
terminated            false
truncated             false
```

### 4.4 Bootstrap

`labs/bootstrap-smoke.yaml`：

```text
run status            completed_curriculum
stages completed      1 / 1
训练步数              32（另有初始评估）
对手                  Noop
评估结果              0 胜 / 0 负 / 1 和
```

门槛为 0，验收目标仅是阶段迁移、评估、checkpoint 与 resolved config。

### 4.5 行为克隆

`labs/bc-smoke.yaml`：

```text
示范 episode          1
示范样本              29
训练 epoch            1
final loss            5.0814
action-type accuracy  0.724
full-action accuracy  0.172
checkpoint            写出成功
```

这是软件管线检查，不是 BC 能力基准。

### 4.6 自对弈组件

```text
历史池 max size       2
插入 3 项后 size      2
recent 权重           [1/3, 2/3]
SelfPlayEnv reset     Dict observation + info
动作掩码维数          6
step 返回             五元组
```

### 4.7 Feudal

```text
总步数                64
manager horizon       4
reward scale          0.001
autoregressive        false
两次 rollout/update   完成
64 步评估             完成
```

训练核心完成后，脚本在最终 `config.json` 序列化时因 `args._cfg` 为 `TrainingConfig` 而抛出 `TypeError`。本教材没有修改训练公共实现；该问题作为当前开放工程缺陷保留。

### 4.8 MCTS 与 AlphaZero

MCTS：

```text
simulations           2
policy entries        360（10 × 6 × 6）
probability sum       1.0
nonzero actions       2
```

AlphaZero：

```text
iterations            1
self-play games       1
max game steps        4
examples              4
policy loss           0.2344
value loss            0.0023
checkpoint            iteration + final 均成功
```

## 5. 测试结果

### 通过

```text
self-play + LLM mock                  128 passed
Feudal + AlphaZero                    120 passed
Bot + evaluation + tournament/replay 305 passed
```

### 当前单项失败

同一 Bot/evaluation/tournament/replay 组有 1 项失败：

```text
tests/test_tournament.py::
  TestTournamentSystem::
  test_tournament_runner_with_logging_parameters
```

原因是 Windows `Path` 将 `/tmp/test_tournament/llm_conversations` 规范化为反斜杠，而测试断言 POSIX 斜杠字符串。其余 305 项通过。这是跨平台测试期望问题，不是本教材修改造成。

## 6. 完整 CLI 当前问题

### Self-play mixed

`n_envs=1` 时脚本按 `n_envs // 2` 创建 0 个环境，产生 `IndexError`。教材已把 mixed 配置改为 `n_envs=2`。

在基准环境继续运行时，SB3 的硬编码 `progress_bar=True` 要求未安装的可选 `rich`/`tqdm`，训练开始前产生 `ImportError`。组件路径和 self-play 测试已经通过；本书不为此修改项目训练 API，也不在验收中安装额外包。

### Feudal

核心短训和评估完成，最终保存配置时 `TrainingConfig` 不可 JSON 序列化。教材把这一现象写入验证记录，不把脚本退出码误报为全流程成功。

## 7. 素材检查

```text
原创静态图            15
游戏截图              2
图表缺字警告          已通过 ASCII 下标替换消除
付费 LLM 调用         0
Cloud 命令            0
```

历史训练图使用仓库记录重绘，并在标题中标注“历史数据”或“历史基准”。

## 8. 构建与视觉检查

2026-07-30 使用 `tools/build_book.py` 与 `tools/verify_book.py` 完成同源构建和验证：

- `book.json` 是 HTML/PDF 的共同章节清单；
- 33 个正文与附录文件全部进入连续阅读版本；
- HTML 由 Pandoc 生成 self-contained 文档，大小约 2.15 MB；
- HTML 审计确认目录存在、678 个 MathML 公式、130 个代码块和 18 个内嵌图片实例；1099 个内部锚点引用无失效目标；
- PDF 由 Chromium/Edge 直接打印同源 HTML，共 251 页、约 7.52 MB，保留 MathML 数学排版，含目录、书签、页眉、页码、中文字体回退和代码样式；
- 用 pdfplumber/pypdf 检查了文本可提取性和 outline；
- 用 Poppler 将 251 页全部渲染为 PNG，组合为 9 张联系表逐页检查；
- 另外以原始分辨率检查了游戏截图页、PPO 数值推演页、图表密集页和末页。

2026-07-30 的复核修复了三个同源问题：

- 0.5 节长命令改为在代码框内自动换行，首尾字符均完整可见；
- 1.4 节回合示意改用具有中文字体回退的浏览器代码排版，“创建单位—移动—攻击—占领—结束回合”完整显示；
- PDF 不再把 LaTeX 降级为纯文本，策略、价值函数、PPO 等公式中的上下标、分式、根号与希腊字母均按 MathML 排版。

验证器会检查 HTML 至少包含 500 个 MathML 公式、PDF 包含目标中文和完整长命令，并拒绝仍含 `\theta`、`\frac`、`_{...}` 等原始 LaTeX 痕迹的输出。
