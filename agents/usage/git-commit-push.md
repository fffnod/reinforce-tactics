# Git 提交与推送（本机 / AI 助手必读）

在本仓库做 `commit` / `push` 时，**必须**遵循本节，否则会重复踩坑。
对话重启后仍以本文件为准，不要假设全局 `git config` 已配置。

---

## 1. 作者身份（高频失败点）

### 现象

```text
Author identity unknown
*** Please tell me who you are.
fatal: unable to auto-detect email address (got 'CEPREI@DXPER.(none)')
```

`git add` 可能已成功，但 **`git commit` 失败**；若脚本里 commit 失败后仍执行 `push`，会显示 `Everything up-to-date`，**改动其实没推上去**。

### 原因

本机未配置可用的 `user.name` / `user.email`（或 AI 会话不应依赖用户的 global config）。

### 正确做法（仅环境变量，不要改 global config）

与历史提交保持一致，使用 GitHub noreply：

| 字段 | 值 |
|------|-----|
| name | `fffnod` |
| email | `33726281+fffnod@users.noreply.github.com` |

**PowerShell（本机默认 shell）示例：**

```powershell
cd D:\Grok\project2\reinforce-tactics

$env:GIT_AUTHOR_NAME = 'fffnod'
$env:GIT_AUTHOR_EMAIL = '33726281+fffnod@users.noreply.github.com'
$env:GIT_COMMITTER_NAME = 'fffnod'
$env:GIT_COMMITTER_EMAIL = '33726281+fffnod@users.noreply.github.com'

git add <paths>
git commit -m @"
Short summary of the change.

Optional body explaining why, not just what.
"@

if ($LASTEXITCODE -ne 0) {
  Write-Host 'COMMIT FAILED — do not push'
  git status
  exit $LASTEXITCODE
}

git push -u origin HEAD
```

**禁止（除非用户明确要求）：**

- `git config --global user.name/email`
- 用随机假邮箱提交
- commit 失败后不检查就当 push 成功

### 验证

```powershell
git log -1 --format='%h %an <%ae>%n%s'
git status   # 应为 clean，且分支与 origin 同步
```

---

## 2. 远程与分支

| 项 | 值 |
|----|-----|
| `origin` | `https://github.com/fffnod/reinforce-tactics.git`（用户 Fork） |
| `upstream` | `https://github.com/kuds/reinforce-tactics.git`（上游） |
| 常用开发分支 | `feature/local-deploy` |
| 干净主干 | `main` — 本地实验不要直接堆在 `main` |

默认 **push 到 `origin` 当前分支**。未经用户确认不要 force-push，不要改 `upstream`。

---

## 3. pre-commit 钩子

仓库启用了 pre-commit（trailing-whitespace、EOF、ruff、mypy 等）。

### 现象

```text
trim trailing whitespace.................................................Failed
- files were modified by this hook
```

钩子会**改文件并拒绝本次 commit**。

### 处理

```powershell
# 把钩子自动修复后的文件重新 stage，再 commit 一次
git add -u
# 仍需带上第 1 节的 AUTHOR/COMMITTER 环境变量
git commit -m "..."
```

不要用 `--no-verify` 跳过钩子，除非用户明确要求。

---

## 4. 提交前检查清单（AI 助手）

1. `git status` / `git diff` / `git log -5 --oneline` 了解改动与 message 风格
2. 只 stage 相关文件；不提交密钥、`settings.json`、大体量 `dist/*.zip`、训练产物
3. 设置 `GIT_AUTHOR_*` / `GIT_COMMITTER_*`（见 §1）
4. `git commit`，检查 **exit code = 0**
5. 若 pre-commit 改文件 → 回到 §3 再 commit
6. `git push -u origin HEAD`
7. 再 `git status`：应 clean，且 `Your branch is up to date with 'origin/...'`

---

## 5. Commit message 风格（本仓库近期）

参考现有提交：

- `Add Windows local deploy docs and one-click migration tooling.`
- `Add full offline deploy packaging via conda-pack.`
- `Fix Chinese UI fonts and complete major in-game localization.`
- `Add Simplified Chinese translations for docs and docs-site.`

约定：

- 首行：祈使句、说明「做了什么」，可带简短 why
- 正文（可选）：补充范围、布局、注意点
- 英文即可（与现有 log 一致）；用户若指定中文 message 则从其要求

---

## 6. 相关文档

- 本地部署：`docs/LOCAL_DEPLOY.md` / `docs/zh/LOCAL_DEPLOY.md`
- 分支与工作流简述：同上 §2
- 知识库索引：`agents/AGENTS.md`
