# 贡献者与开发文档

本目录存放与源码同仓的 **面向贡献者** 文档：路线图、内部代码评审、开发者指南等，**不属于** 对外发布的用户手册。

> **用户向文档**（安装、游戏规则、API、锦标赛等）发布于 **[reinforcetactics.com](https://reinforcetactics.com)**，源文件在 [`docs-site/`](../../docs-site/)。

## 双语说明

| 目录 | 语言 |
|------|------|
| [`docs/`](../) | 英文原文 |
| [`docs/zh/`](./) | 中文译本（本目录） |

对应的用户站文档见 [`docs-site/zh/`](../../docs-site/zh/)。

## 本目录内容

| 文件 | 读者 | 用途 |
|---|---|---|
| [`LOCAL_DEPLOY.md`](LOCAL_DEPLOY.md) | 贡献者 / 本地用户 | Windows + Conda 本地安装、一键脚本、跨机迁移 |
| [`ROADMAP.md`](ROADMAP.md) | 贡献者 | 计划功能、里程碑与待办 |
| [`vertex_training.md`](vertex_training.md) | 贡献者 | 通过 Vertex AI 自定义任务在 Google Cloud 上训练（Docker + GCS） |
| [`MAP_EDITOR.md`](MAP_EDITOR.md) | 贡献者 | 游戏内地图编辑器内部工作方式 |
| [`REVIEW_maintainability.md`](REVIEW_maintainability.md) | 贡献者 | 代码质量评审：重复、缺陷、重构优先级 |
| [`REVIEW_advancedbot.md`](REVIEW_advancedbot.md) | 贡献者 | 高级规则 Bot 代码评审 |
| [`feudal_rl_review.md`](feudal_rl_review.md) | 贡献者 | Feudal RL 实现代码评审 |
| [`bootstrap_runs_review.md`](bootstrap_runs_review.md) | 贡献者 | PPO Bootstrap 训练 run 回顾 |
| [`bootstrap_lessons_learned.md`](bootstrap_lessons_learned.md) | 贡献者 | Bootstrap 训练经验总结 |
| [`balance_analysis_lessons_learned.md`](balance_analysis_lessons_learned.md) | 贡献者 | 平衡性分析流水线经验 |
| [`REVIEW_ppo_training.md`](REVIEW_ppo_training.md) | 贡献者 | PPO Bootstrap 训练为何卡关 |
| [`REVIEW_rl_pipeline_2026-07-24.md`](REVIEW_rl_pipeline_2026-07-24.md) | 贡献者 | RL 流水线评审（2026-07-24） |

## 何时写在 `docs/` vs `docs-site/`

- **此处（`docs/`）** — 内部笔记、评审结论、路线图、随代码频繁变更的开发指南。不对外发布。
- **[`docs-site/docs/`](../../docs-site/docs/)** — 用户会读的内容：安装、游玩、训练、Bot 配置、锦标赛。经 Docusaurus 发布到 [reinforcetactics.com](https://reinforcetactics.com)。

若 `docs/` 中的贡献者笔记成熟为对用户有用的内容，应提升到 `docs-site/docs/`，并删除（或改为桩）原文。
