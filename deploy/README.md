# Deploy tools（一键部署 / 迁移）

本目录提供 **Windows 本机一键安装** 与 **跨电脑迁移打包** 工具。

完整说明见：[`docs/LOCAL_DEPLOY.md`](../docs/LOCAL_DEPLOY.md)

## 文件一览

| 文件 | 作用 |
|------|------|
| `install.bat` | 双击安装入口（**在线**，推荐联网机） |
| `install.ps1` | 在线安装逻辑（conda 环境 + 依赖 + 可编辑安装） |
| `install-offline.bat` / `install-offline.ps1` | **离线**安装入口（解压 conda-pack 环境） |
| `verify.ps1` | 冒烟测试（导入 / CLI / pygame / Gym env） |
| `requirements-lock.txt` | 已验证可工作的第三方包版本锁定 |
| `environment.yml` | Conda 环境描述（可选，手动 `conda env create`） |
| `pack-for-migration.ps1` | 打**轻量**迁移 zip（仅源码，目标机需联网） |
| `pack-offline.ps1` | 打**完整离线**包（源码 + 环境 tar.gz + wheels） |

## 本机安装

```powershell
cd <repo-root>
.\deploy\install.ps1
```

或双击 `deploy\install.bat`。

## 打迁移包（轻量，目标机需联网）

```powershell
cd <repo-root>
.\deploy\pack-for-migration.ps1
```

产物：`dist/reinforce-tactics-deploy-*.zip`

## 打完整离线包（目标机无需联网）

前提：本机已存在可用的 conda 环境 `reinforce-tactics`。

```powershell
cd <repo-root>
.\deploy\pack-offline.ps1
# 体积更大、更快打包时可跳过 wheels 镜像：
.\deploy\pack-offline.ps1 -SkipWheels
```

产物：`dist/reinforce-tactics-offline-*.zip`（通常约 1–2+ GB）

目标机：

1. 解压到英文路径  
2. 双击 `install-offline.bat`  
3. 使用生成的 `Activate-ReinforceTactics.bat` 后运行 `python main.py`  

> 离线包 **内含** 完整 Python 运行时与依赖，**不需要** 预装 Anaconda。  
> 目标机仍需 Windows x64 + 自带 `tar.exe`。
