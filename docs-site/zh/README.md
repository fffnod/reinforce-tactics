# Reinforce Tactics 文档站点

> **说明**：本文档为简体中文翻译。英文原文位于 `docs-site/`，中文版本位于 `docs-site/zh/`。

这是 Reinforce Tactics 的**面向用户**的文档网站，使用 [Docusaurus](https://docusaurus.io/)（现代静态网站生成器）构建。部署地址为 [reinforcetactics.com](https://reinforcetactics.com)。

> 面向贡献者的说明（路线图、内部代码审查、开发指南）位于仓库级 [`docs/`](../../docs/) 目录——请参阅 [`docs/zh/README.md`](../../docs/zh/README.md)（中文）或 [`docs/README.md`](../../docs/README.md)（英文）。

## 双语目录

| 路径 | 语言 |
|------|------|
| [`docs-site/docs/`](../docs/) | 用户文档英文原文（Docusaurus 源） |
| [`docs-site/zh/`](./) | 用户文档简体中文（本树） |
| [`docs/`](../../docs/) | 贡献者文档英文 |
| [`docs/zh/`](../../docs/zh/) | 贡献者文档中文 |

`zh/` 与英文 markdown/mdx 平行，便于双语阅读。**尚未**接入 Docusaurus i18n 语言切换；若要在线上站点提供语言切换，需另行配置。

## 安装

```bash
cd docs-site
npm install
```

## 本地开发

```bash
cd docs-site
npm start
```

该命令会启动本地开发服务器，并在浏览器中打开 `http://localhost:3000`。大多数更改会实时反映，无需重启服务器。

## 构建

```bash
cd docs-site
npm run build
```

该命令会将静态内容生成到 `build` 目录，可使用任何静态内容托管服务进行部署。

## 文档结构

文档包含：
- **入门指南**（`intro.md`）：概述、功能特性与快速入门
- **游戏机制**（`game-mechanics.md`）：单位、战斗系统、建筑与地形
- **Bot 锦标赛**（`tournaments.mdx`）：官方锦标赛结果与分析
- **地图**（`maps.mdx`）：可用地图预览与说明
- **锦标赛系统**（`tournament-system.md`）：运行锦标赛的技术指南
- **实现状态**（`implementation-status.md`）：功能当前状态与开发路线图

## 部署

当更改推送到 main 分支时，站点会通过 GitHub Actions 自动部署到 GitHub Pages。

## 贡献文档

添加或更新文档：

1. 编辑 `docs/` 目录中的 markdown 文件
2. 使用 `npm start` 进行本地测试
3. 提交并推送更改
4. 站点将自动部署

有关 Docusaurus 的更多信息，请访问[官方文档](https://docusaurus.io/)。
