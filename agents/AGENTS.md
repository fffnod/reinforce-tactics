# Agents 项目知识索引

本目录存放面向开发者 / AI 助手的**长期知识库**：把对话与排查中沉淀的重要信息分类成文，避免全部堆在单一文件里。

**维护约定**

1. **本文件（`agents/AGENTS.md`）只做索引与概述**，不写长文。
2. 详细内容写在同目录（或子目录）的独立 Markdown 中。
3. 新增记录时：先在本索引登记「路径 + 概述」，再写正文。
4. 修改记录时：按索引找到对应文件，改完后如概述变化则同步更新本表。
5. 文中路径默认相对仓库根目录 `reinforce-tactics/`。

---

## 文档分类

| 分类 | 子目录 / 前缀 | 用途 |
|------|----------------|------|
| **使用类** | `usage/` | 安装、启动、GUI 操作、训练命令、部署迁移等「怎么用」 |
| **问题排查类** | `troubleshooting/` | 故障现象、根因、修复步骤、验证方法 |
| **源代码分析类** | `source-analysis/` | 模块结构、关键调用链、设计取舍 |
| **智能算法分析类** | `algorithms/` | RL 算法、奖励、对手体系、训练管线分析 |

---

## 索引表

### 使用类（usage）

| 文件 | 概述 | 状态 |
|------|------|------|
| [`usage/local-run-guide.md`](usage/local-run-guide.md) | Windows + Conda 下如何激活环境、启动 GUI、配置人机/AI、进行简单 PPO 训练与评估 | 已写 |
| [`usage/chinese-i18n-coverage.md`](usage/chinese-i18n-coverage.md) | 中文汉化覆盖范围：单位行动/购买/HUD/设置/地图编辑器；如何继续补词条 | 已写 |
| [`../docs/LOCAL_DEPLOY.md`](../docs/LOCAL_DEPLOY.md) | 完整本地部署说明（在线/离线包、一键脚本、迁移）；偏工程部署 | 已写（在 `docs/`） |
| [`../deploy/README.md`](../deploy/README.md) | 一键安装 / 离线打包脚本索引 | 已写（在 `deploy/`） |

### 问题排查类（troubleshooting）

| 文件 | 概述 | 状态 |
|------|------|------|
| [`troubleshooting/chinese-font-display.md`](troubleshooting/chinese-font-display.md) | 切换中文后菜单乱码/方框：pygame-ce Windows SysFont 崩溃、改为直读 `msyh.ttc` 等字体文件的原因与修复 | 已写 |

### 源代码分析类（source-analysis）

| 文件 | 概述 | 状态 |
|------|------|------|
| （待补充） | 例如：`main.py` 路由、菜单状态机、`gym_env` 动作空间、bot 工厂 | 占位 |

### 智能算法分析类（algorithms）

| 文件 | 概述 | 状态 |
|------|------|------|
| （待补充） | 例如：PPO 默认超参、对手 curriculum、MaskablePPO、AlphaZero/Feudal | 占位 |

---

## 本地环境快照（便于续写）

| 项 | 值 |
|----|-----|
| Fork | `https://github.com/fffnod/reinforce-tactics` |
| 开发分支 | `feature/local-deploy` |
| Conda 环境名 | `reinforce-tactics`（Python 3.12） |
| 已装 extras | `base` + `gui` + `llm` + `dev`（**未装** `cloud`） |
| PyTorch | CPU 版（`cuda=False`） |
| 项目路径（源机） | `D:\Grok\project2\reinforce-tactics` |

更细的部署与离线包说明见 `docs/LOCAL_DEPLOY.md`。

---

## 建议的后续条目（尚未成文）

- 使用类：LLM Bot API Key 配置与菜单路径
- 使用类：离线包在目标机的验收清单
- 源码：`reinforcetactics/utils/fonts.py` 字体选择流程
- 算法：`--opponent bot|random|noop|self` 与 gym 内对手构造
- 排查：训练产物目录与 `.gitignore` 关系
