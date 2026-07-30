# Agents knowledge base

项目知识库索引与约定见：

**[agents/AGENTS.md](agents/AGENTS.md)**

详细文档按分类放在 `agents/` 目录下（使用 / 排查 / 源码分析 / 算法）。

## 开场必读（防止对话重启后重复踩坑）

| 主题 | 文档 |
|------|------|
| **Git commit/push 作者信息、pre-commit、分支** | [`agents/usage/git-commit-push.md`](agents/usage/git-commit-push.md) |
| 本地环境快照与完整索引 | [`agents/AGENTS.md`](agents/AGENTS.md) |
| **项目整体架构（源码）** | [`agents/source-analysis/overview.md`](agents/source-analysis/overview.md) |
| **强化学习学习指南 v2（推荐，00–27）** | [`agents/learning-guide-v2/README.md`](agents/learning-guide-v2/README.md) |
| **学习指南 v2 离线 PDF** | [`output/pdf/Reinforce-Tactics-RL-Learning-Guide-v2.pdf`](output/pdf/Reinforce-Tactics-RL-Learning-Guide-v2.pdf) |
| **强化学习学习指南 v1（旧版 00–17）** | [`agents/learning-guide/README.md`](agents/learning-guide/README.md) |
| **强化学习算法总览（速查）** | [`agents/algorithms/overview.md`](agents/algorithms/overview.md) |

在本机提交时：本机常**没有**可用的 `user.name`/`user.email`。必须用环境变量
`GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_*` =
`fffnod` / `33726281+fffnod@users.noreply.github.com`，**不要**改 global git config。
commit 失败后不要误以为 push 已成功。

熟悉代码时：先读源码总览，再按分层打开 `agents/source-analysis/` 分篇；系统学 RL 优先走 `agents/learning-guide-v2/`，算法速查走 `agents/algorithms/`，文档用相对路径互链。
