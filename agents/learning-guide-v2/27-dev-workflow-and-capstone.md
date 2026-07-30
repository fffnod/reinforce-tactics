# 第 27 章　DEV 工具链与综合研究实践

## 27.1 从“能运行”到“可研究”

强化学习项目同时包含游戏规则、环境适配、算法、配置、评估与可视化。某一层悄悄变化，最终表现可能完全不同。DEV 工具链的职责是把这些层的契约固定下来，使问题能够复现、定位和回归验证。

本项目在 `pyproject.toml` 中把开发依赖列为：

- pytest、pytest-cov；
- pre-commit；
- Ruff；
- mypy。

这些工具不提高策略网络的表达能力，却决定实验结论是否建立在稳定实现之上。

## 27.2 测试金字塔

### 单元测试

验证纯函数或局部契约：

- flat 动作编码/解码；
- 掩码形状与至少一个合法动作；
- GAE 数值；
- Elo 更新；
- JSON 提取；
- 配置验证。

### 集成测试

跨模块验证：

- `StrategyGameEnv.reset/step`；
- MaskablePPO 与 wrapper；
- BC checkpoint 加载到 PPO；
- Feudal rollout 与两层 update；
- MCTS 深复制后执行动作；
- replay 保存与重放。

### 冒烟测试

用极小预算跑完整路径：

- 64 个环境步；
- 1 次训练迭代；
- 1 局短自对弈；
- 1 个 checkpoint；
- 1 次导出。

冒烟成功表示接口贯通，不表示算法效果。

### 统计回归

固定小任务和种子，允许合理波动地检查：

- Noop 最低胜率；
- 无效动作率不超过上限；
- episode 不全部截断；
- loss 为有限数；
- 性能没有数量级退化。

统计回归不能写成要求每次 reward 完全相同，除非环境和算法路径确实确定性。

## 27.3 质量检查命令

项目级检查可依次运行：

```powershell
ruff check .
mypy reinforcetactics
pytest
```

`pyproject.toml` 当前配置 pytest 覆盖率门槛为 65%。只运行少量测试时，全局覆盖率门槛可能导致“测试本身通过，但命令因覆盖率不足退出”。局部调试可明确使用：

```powershell
pytest -q tests/test_alphazero.py --no-cov
```

最终提交前仍应运行项目规定的完整测试与覆盖率检查，不能把 `--no-cov` 当作验收结果。

## 27.4 配置优先级

一个可靠的配置系统应明确：

```text
代码默认值
  < 配置文件
  < 命令行显式参数
```

项目训练脚本先从 YAML/JSON 读取配置并设置 argparse 默认值，再由 CLI 覆盖。嵌套的 `reward_config`、`engine_overrides`、`opponent_kwargs` 等不能简单靠标量参数表达，因此需要显式传入环境工厂。

诊断配置时保存三份证据：

1. 原始配置文件；
2. 命令行；
3. 程序实际解析后的完整配置。

只看 YAML 不足以证明训练环境真正收到了字段。

## 27.5 诊断顺序

当训练失败时，按由低到高的顺序排查：

```text
规则层
  -> 环境契约
  -> 观察与动作
  -> 奖励与终止
  -> 算法数值
  -> 对手与课程
  -> 统计评估
```

### 规则层

用固定动作或规则 Bot 确认胜负、伤害、占领和经济。

### 环境契约

检查空间包含 observation/action，`terminated` 与 `truncated` 正确。

### 观察与动作

检查玩家相对视角、padding、掩码与真实合法动作一致。

### 奖励与终止

打印 breakdown，确认终局脉冲、势能差分和截断 bootstrap。

### 算法数值

检查 NaN、梯度范数、value loss、entropy、KL 与 clip fraction。

### 对手与课程

确认当前实际对手、地图、阶段、checkpoint 交接和晋级门。

### 统计评估

最后才判断算法是否真的更强。

这个顺序避免在环境动作编码错误时先调整学习率。

## 27.6 最小可复现问题

一个训练问题通常可以缩小为：

- 单地图；
- 单环境；
- CPU；
- 固定种子；
- 64–2048 步；
- 无渲染；
- 最少 callback；
- 输出观察形状、掩码数、奖励分解和终止原因。

若问题在最小版本消失，再逐个恢复 VecEnv、多地图、自对弈、课程和大网络。一次恢复一个因素，才能定位触发条件。

## 27.7 日志与 checkpoint

训练产物应形成一个不可歧义的 run 目录：

```text
run/
  resolved-config.yaml
  metadata.json
  tensorboard/
  checkpoints/
  eval/
  traces/
  final_model.zip
```

checkpoint 不只是网络参数。要可继续训练，还可能需要：

- 优化器状态；
- 当前环境步数；
- 学习率日程；
- replay/rollout 相关状态；
- 当前课程阶段；
- 最佳评估指标；
- 自对弈快照池；
- 随机数状态。

缺少这些状态时，“resume”可能只是从权重重新开始一个不同实验。

## 27.8 综合实践：从短训练到研究报告

下面给出一条不依赖旧知识文件的完整路线。

### 阶段 A：环境验收

运行：

```powershell
python agents/learning-guide-v2/tools/smoke_labs.py --only env
python agents/learning-guide-v2/tools/smoke_labs.py --only masks
```

保存 observation 形状、合法动作数、随机合法动作的 step 结果，以及 MultiDiscrete 各维掩码。

### 阶段 B：接口边界

验证：

- DQN + 默认 MultiDiscrete 必须得到清晰的不兼容结果；
- DQN + Flat Discrete 可以构造；
- A2C 可以构造，但普通 A2C 不消费掩码；
- MaskablePPO 构造并学习 64 步。

这一步的结果是软件能力矩阵，不是算法排名。

### 阶段 C：第一条训练曲线

使用 `labs/maskable-ppo-smoke.yaml` 在 CPU 上训练短预算。确认：

- TensorBoard 有 rollout 和 train 指标；
- 模型能保存；
- 固定 5 局评估能运行；
- 结果中有终局原因和奖励分解。

### 阶段 D：课程训练

运行 `labs/bootstrap-smoke.yaml`，门槛设为 0 只验证阶段迁移。正式实验再恢复合理门槛、最小阶段步数、耐心和多局评估。

### 阶段 E：进阶路径

依次执行：

- BC 数据管线与一次交叉熵更新；
- BC 权重加载到 PPO；
- 自对弈快照池采样；
- Feudal 两层 rollout；
- MCTS 2 次 simulation；
- AlphaZero 一个自对弈样本与一次更新。

不要同时调试全部路径。每项先在单独报告中通过，再组合。

### 阶段 F：正式研究问题

选择一个可证伪问题，例如：

> 在 5 个种子、每个 50 万环境步的预算下，Bootstrap 是否比固定 BalancedRandom 训练提高对 MediumBot 的独立测试胜率？

建立两组配置，固定其余变量，预先确定主要指标与测试种子。

### 阶段 G：报告

报告至少包括：

1. 问题与假设；
2. 代码 revision 和环境版本；
3. 完整配置；
4. 训练预算；
5. 多种子曲线；
6. 最终原始结果和置信区间；
7. 终局、动作、奖励分解；
8. 失败 run；
9. 典型回放；
10. 限制与下一实验。

## 27.9 教材构建与验证

新版教材提供四类命令：

```powershell
python agents/learning-guide-v2/tools/generate_figures.py
python agents/learning-guide-v2/tools/smoke_labs.py
python agents/learning-guide-v2/tools/build_book.py
python agents/learning-guide-v2/tools/verify_book.py
```

它们分别：

- 重绘教材静态图；
- 运行低成本接口冒烟；
- 从 `book.json` 的同一章节清单生成连续 HTML 与 PDF；
- 检查章节、链接、图片、算法覆盖、PDF 文本和书签。

PDF 还需通过 Poppler 渲染为逐页 PNG，在 `tmp/pdfs/` 中检查：

- 中文字体缺字；
- 表格或代码越界；
- 公式被截断；
- 标题孤行；
- 图片模糊；
- 空白页；
- 页眉页码冲突。

自动检查不能代替视觉检查。

## 27.10 DEV 中的常见错误

**修复训练问题却没有测试环境契约。**  
算法层可能只是掩盖底层错误。

**复制配置后只改文件名。**  
必须验证解析值真的不同。

**用冒烟结果宣称性能。**  
冒烟只验证路径。

**忽略工作树已有改动。**  
实验和文档修改应保持范围清晰，不覆盖无关用户文件。

**只保存 final model。**  
无法恢复训练上下文，也无法解释 best 与 final 差异。

**测试用 mock，最终却从未做集成测试。**  
mock 隔离外部依赖；真实组件边界仍需本地、免费、可控的集成验证。

## 27.11 研究伦理与结果表述

报告应明确：

- 未运行的实验不能写成已验证；
- 历史结果不能冒充当前代码复现；
- 单种子结果不能表述为一般结论；
- 失败版本不能从实验索引中消失；
- LLM mock 不能冒充真实供应商性能；
- 教材示意数字要标注“算例”，历史数据要标注“历史数据”。

严格表述不会削弱研究价值，反而使下一位读者能准确接续工作。

## 27.12 全书实践终点

完成本章后，读者应能够：

- 从游戏机制定义 MDP/POMDP；
- 推导并解释回报、价值、GAE 和 PPO；
- 理解 PyTorch、Gymnasium、SB3/sb3-contrib 的职责；
- 追踪观察、动作、掩码、奖励和终止的数据链；
- 运行 MaskablePPO 主线；
- 分析 DQN、A2C 的适用边界；
- 使用课程、BC 与自对弈；
- 理解 Feudal、MCTS 和 AlphaZero 的实验实现；
- 设计带置信区间和消融的研究；
- 使用 Bot、Tournament、Elo、回放和 trace 评估；
- 在不调用外部 API 的条件下测试 LLM Bot 管线；
- 构建并验证整本教材。

## 27.13 本章小结

DEV 工具链把游戏、环境、算法和研究结论连接成可验证系统。最有效的排障方式是从规则与契约逐层上升；最可靠的研究流程是先用冒烟确认软件，再以多种子、独立评估和完整记录回答性能问题。

## 27.14 练习

1. 为什么局部 pytest 可能在测试都通过后仍因覆盖率门槛退出？
2. 写出一个训练配置的三层优先级，并说明如何保存解析结果。
3. 把“模型不学习”缩小成一个最小可复现问题。
4. 设计一个 checkpoint 恢复一致性测试。
5. 按本章模板提出一个关于奖励塑形的可证伪研究问题。
