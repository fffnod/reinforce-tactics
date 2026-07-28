# Reinforce Tactics 本地部署说明

本文记录在 **Windows + Anaconda/Miniconda** 上成功部署本仓库（Fork）的完整过程，并说明如何 **一键重装** 与 **迁移到另一台电脑**。

> 对应开发分支建议：`feature/local-deploy`  
> 上游项目：https://github.com/kuds/reinforce-tactics  
> 本文档路径：`docs/LOCAL_DEPLOY.md`  
> 一键脚本目录：`deploy/`

---

## 1. 环境要求

| 项目 | 要求 | 备注 |
|------|------|------|
| 操作系统 | Windows 10/11（x64）已验证 | Linux/macOS 可用相同 pip 流程，脚本以 Windows 为主 |
| Python | **3.11–3.13**（推荐 **3.12**） | 项目已放弃 3.10 |
| Conda | Miniconda 或 Anaconda | 用于隔离环境 |
| 磁盘 | 建议 ≥ **10 GB** 可用 | torch 等体积较大 |
| 网络 | 首次安装需访问 PyPI / conda | 可配合代理 / 镜像 |
| GPU | **可选** | 默认按 CPU 版 PyTorch 安装即可 |

### 参考机器配置（首次部署成功）

| 组件 | 配置 |
|------|------|
| CPU | Intel Core i7-10750H（6C/12T） |
| GPU | NVIDIA Quadro P620 4GB（训练时非必须） |
| Python 环境 | conda `reinforce-tactics`，Python **3.12.13** |
| 包模式 | `pip install -e ".[gui]"`（可编辑 + GUI） |

---

## 2. 推荐 Git 工作流（简要）

不要在 `main` 上直接堆本地改动；保持与上游可同步：

```text
upstream (kuds/reinforce-tactics)
        │
        ▼
origin/main  (你的 Fork，尽量干净)
        │
        └── feature/local-deploy  ← 本地部署与实验
```

```powershell
# 首次（若尚未做）
gh repo fork kuds/reinforce-tactics --clone=false
gh repo clone <你的用户名>/reinforce-tactics
cd reinforce-tactics
git remote add upstream https://github.com/kuds/reinforce-tactics.git   # 若 clone fork 时未自动加
git checkout -b feature/local-deploy
```

同步上游：

```powershell
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
git checkout feature/local-deploy
git merge main
```

---

## 3. 首次手动安装过程（已验证）

以下为在参考机器上实际执行、并验证通过的步骤。

### 3.1 创建 Conda 环境

```powershell
conda create -n reinforce-tactics python=3.12 -y
conda activate reinforce-tactics
python -V
# 期望: Python 3.12.x
```

### 3.2 进入仓库并安装

```powershell
cd D:\path\to\reinforce-tactics

# 官方推荐：可编辑安装 + GUI（含 pygame、opencv、matplotlib 等）
pip install -e ".[gui]"
```

说明：

| 命令 | 内容 |
|------|------|
| `pip install -e .` | 仅 base：gymnasium、SB3、torch、tensorboard 等 |
| `pip install -e ".[gui]"` | base + **pygame-ce**、opencv、matplotlib、Pillow、imageio… |
| `pip install -e ".[all]"` | GUI + LLM + cloud + dev |
| `pip install -e ".[dev]"` | pytest、ruff、mypy、pre-commit |

首次安装可能耗时 **10–30+ 分钟**（主要下载 `torch`）。

### 3.3 冒烟验证（已通过项）

```powershell
# C1 导入
python -c "import reinforcetactics, gymnasium, torch, pygame; print(torch.__version__, torch.cuda.is_available())"

# C2 CLI
python main.py --help

# C3 GUI 能力（能开窗口即可）
python -c "import pygame; pygame.init(); s=pygame.display.set_mode((640,480)); print(s.get_size()); pygame.quit()"

# 可选：Gym 环境一步
python -c "from reinforcetactics.rl.gym_env import StrategyGameEnv; e=StrategyGameEnv(map_file='maps/1v1/beginner.csv', opponent='bot', render_mode=None); e.reset(); e.step(e.action_space.sample()); e.close(); print('ok')"
```

首次运行 `main.py` 可能生成本地 `settings.json`（已在 `.gitignore`，勿提交）。

### 3.4 启动游戏

```powershell
conda activate reinforce-tactics
cd <repo-root>
python main.py
# 或
python main.py --mode play
```

### 3.5 训练示例（可选）

```powershell
# 极短试跑
python main.py --mode train --algorithm ppo --timesteps 1000 --opponent bot

# 较正式（耗时长）
python main.py --mode train --algorithm ppo --timesteps 100000 --opponent bot
```

产物目录（默认 gitignore）：`models/`、`checkpoints/`、`tensorboard/`、`logs/`。

### 3.6 实测关键版本（锁定参考）

部署成功时第三方栈见 `deploy/requirements-lock.txt`，包括但不限于：

| 包 | 版本（示例） |
|----|----------------|
| reinforcetactics | 0.3.3（editable 源码） |
| torch | 2.13.0+cpu |
| gymnasium | 1.3.0 |
| stable-baselines3 | 2.9.0 |
| sb3-contrib | 2.9.0 |
| pygame-ce | 2.5.7 |
| numpy | 2.5.1 |
| pettingzoo | 1.26.1 |

`cuda=False` 表示当前为 **CPU 版 PyTorch**，对本项目默认小网络 PPO 通常足够；GPU 加速见下文。

---

## 4. 一键部署（推荐复现方式）

仓库已内置脚本，**新机器 / 重装** 时优先使用。

### 4.1 前置

1. 已安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda  
2. 已拿到本仓库源码（git clone 或解压迁移包）  
3. 终端能执行 `conda`（必要时「Anaconda Prompt」或重新打开 PowerShell）

### 4.2 安装

**方式 A — 双击**

```text
deploy\install.bat
```

**方式 B — PowerShell**

```powershell
cd <repo-root>
.\deploy\install.ps1
```

常用参数：

```powershell
.\deploy\install.ps1                  # 默认：env=reinforce-tactics, extras=gui, 用 lock
.\deploy\install.ps1 -Extras all      # 装全部 extras
.\deploy\install.ps1 -SkipVerify      # 跳过冒烟
.\deploy\install.ps1 -EnvName rt-dev  # 自定义环境名
```

脚本会：

1. 检查 conda  
2. 创建/复用环境 `reinforce-tactics`（Python 3.12）  
3. `pip install -r deploy/requirements-lock.txt`  
4. `pip install -e ".[gui]"`（可编辑，改源码立即生效）  
5. 调用 `deploy/verify.ps1` 做冒烟测试  

### 4.3 单独验证

```powershell
.\deploy\verify.ps1
.\deploy\verify.ps1 -EnvName reinforce-tactics
```

### 4.4 手动 Conda 文件（可选）

```powershell
conda env create -f deploy/environment.yml
conda activate reinforce-tactics
pip install -e ".[gui]"
```

> `environment.yml` 通过 pip 引用 `requirements-lock.txt`；若 `conda env create` 对相对路径解析异常，请改用 `install.ps1`。

---

## 5. 迁移到另一台电脑

### 5.1 能做成「一键」的是什么？

| 内容 | 是否进迁移包 | 原因 |
|------|----------------|------|
| 源码 + maps + configs | ✅ | 体积可控 |
| `deploy/*` 脚本与 lock | ✅ | 一键复现 |
| 部署文档 | ✅ | 说明 |
| 完整 conda 环境 / site-packages | ❌ 默认不做 | 数 GB～十几 GB，且难跨机路径兼容 |
| models / checkpoints / tensorboard | ❌ 默认排除 | 体积大且属产物 |
| settings.json、密钥 | ❌ | 本地隐私 |

因此「一键部署包」= **源码迁移包 + 目标机一键安装脚本**。  
目标机仍需：**Conda + 首次联网下载依赖**（版本由 lock 固定，尽量一致）。

若需要 **完全离线**（U 盘拷贝已装好的环境），见 [§5.4](#54-可选完全离线conda-pack进阶)。

### 5.2 在源机器打迁移包

```powershell
cd <repo-root>
.\deploy\pack-for-migration.ps1
```

产物示例：

```text
dist/reinforce-tactics-deploy-YYYYMMDD-HHMM.zip
```

包内含 `START_HERE.txt`、完整源码（排除缓存与训练产物）、`deploy/` 脚本。

### 5.3 在目标机器安装

1. 安装 Miniconda/Anaconda  
2. 解压 zip（路径尽量 **英文、无空格**）  
3. 双击 `deploy\install.bat`，或：

```powershell
cd <解压目录>
.\deploy\install.ps1
```

4. 启动：

```powershell
conda activate reinforce-tactics
python main.py
```

### 5.4 完整离线部署包（推荐离线场景）

一键脚本会打包：**源码 + conda-pack 完整环境 +（可选）wheels 镜像 + 离线安装脚本**。

#### 源机器打包

前提：已存在可用环境 `reinforce-tactics`（见 §3 / §4）。

```powershell
cd <repo-root>
.\deploy\pack-offline.ps1
# 更快、略小（不额外导出 wheels）：
.\deploy\pack-offline.ps1 -SkipWheels
```

产物示例：

```text
dist/reinforce-tactics-offline-YYYYMMDD-HHMM.zip   # 通常约 1–2+ GB
dist/reinforce-tactics-offline-YYYYMMDD-HHMM.manifest.txt
```

包内结构：

| 路径 | 说明 |
|------|------|
| `env/reinforce-tactics-env.tar.gz` | 完整 Python 环境（含 torch、SB3、pygame 等） |
| `source/` | 项目源码 |
| `wheels/` | pip 轮子备用镜像（未加 `-SkipWheels` 时） |
| `deploy/install-offline.ps1` | 离线安装逻辑 |
| `install-offline.bat` | 双击入口 |
| `START_HERE.txt` | 目标机说明 |

#### 目标机器安装（无需联网、无需预装 Anaconda）

1. 解压到 **英文路径**（避免空格/中文），例如 `D:\rt-offline`  
2. 双击 `install-offline.bat`，或：

```powershell
cd D:\rt-offline
.\deploy\install-offline.ps1
```

3. 安装脚本会：解压环境 → `conda-unpack` → 通过 `.pth` 将 `source/` 链入 `sys.path`（完全离线，无需 pip 联网构建）→ 冒烟测试  
4. 使用生成的激活脚本：

```text
Activate-ReinforceTactics.bat
```

然后：

```powershell
python main.py
```

#### 注意

| 项 | 说明 |
|----|------|
| 体积 | 明显大于轻量迁移包；请预留数 GB 磁盘 |
| 平台 | 仅适用于 **同类 Windows x64**；不要拷到 Linux/macOS |
| GPU | 包内一般为 **CPU 版 torch**；不会自动变成 CUDA 版 |
| 路径 | 安装后环境在包内 `runtime\reinforce-tactics`（可用 `-Prefix` 改） |
| 重装 | 删除 `runtime\` 后再次运行 `install-offline.bat` 即可 |

手工 `conda-pack`（不推荐，除非调试）：

```powershell
conda run -n reinforce-tactics python -m pip install conda-pack
conda run -n reinforce-tactics python -m conda_pack -n reinforce-tactics -o dist\env.tar.gz
```

---

## 6. CPU / GPU 说明（训练）

| 方式 | 适用 |
|------|------|
| **CPU（默认）** | 学流程、小步数试训、本机开发 |
| **GPU** | 大批量更新、更大网络、长训；受显卡算力限制 |

参考机上默认 `torch 2.13.0+cpu`，`cuda=False`。  
本项目默认 PPO 为小网络 + 单环境仿真，**瓶颈多在 CPU 环境 step**，P620 类入门 GPU 往往只有有限加速。

若要 CUDA 版 PyTorch，在激活环境后按 [pytorch.org](https://pytorch.org) 选择命令重装 `torch`，再：

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

---

## 7. 常见问题

### 7.1 `conda` 不是内部或外部命令

- 使用 **Anaconda Prompt**，或把 conda 加入 PATH  
- 或先执行：`%USERPROFILE%\anaconda3\Scripts\conda.exe`（路径按本机安装位置）

### 7.2 `pip install` 很慢 / 超时

可临时使用国内镜像（示例）：

```powershell
pip install -e ".[gui]" -i https://pypi.tuna.tsinghua.edu.cn/simple
```

使用 lock 时：

```powershell
pip install -r deploy/requirements-lock.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 7.3 与系统 Python 冲突

始终：

```powershell
conda activate reinforce-tactics
where python
# 应指向 ...\envs\reinforce-tactics\python.exe
```

### 7.4 GUI 无法显示

- 确认装了 `.[gui]`（含 pygame-ce）  
- 远程桌面 / 无显示器环境可能失败；训练请用 headless（`render_mode=None`）  
- 运行 `.\deploy\verify.ps1` 查看 `pygame_display` 项  

### 7.5 想删掉环境重来

```powershell
conda deactivate
conda env remove -n reinforce-tactics -y
.\deploy\install.ps1
```

### 7.6 可编辑安装与迁移

`pip install -e .` 把环境指到 **当前磁盘上的源码路径**。  
换电脑或移动目录后，请在新路径下 **重新执行** `install.ps1` 或 `pip install -e ".[gui]"`。

---

## 8. 目录与产物约定

| 路径 | 说明 |
|------|------|
| `deploy/` | 一键安装 / 验证 / 迁移打包 |
| `docs/LOCAL_DEPLOY.md` | 本文 |
| `settings.json` | 本地设置（gitignore） |
| `models/`、`checkpoints/`、`tensorboard/`、`logs/` | 训练产物（gitignore） |
| `dist/*.zip` | 迁移包输出（建议不提交或自行决定） |

---

## 9. 验收清单（部署完成标准）

- [ ] `conda activate reinforce-tactics` 成功  
- [ ] `python -c "import reinforcetactics, torch, pygame"` 无报错  
- [ ] `python main.py --help` 有完整帮助  
- [ ] `python main.py` 能进入游戏菜单（有图形界面时）  
- [ ] （可选）Gym `reset`/`step` 成功  
- [ ] 开发在 `feature/*` 分支，不污染干净 `main`  

---

## 10. 相关链接

- 上游 README 安装说明：仓库根目录 `README.md`  
- 用户文档站：https://reinforcetactics.com  
- 贡献者文档索引：`docs/README.md`  
- 部署脚本说明：`deploy/README.md`  
- Vertex 云训练（进阶）：`docs/vertex_training.md`  
