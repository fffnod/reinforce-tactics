# Deploy tools（一键部署 / 迁移）

本目录提供 **Windows 本机一键安装** 与 **跨电脑迁移打包** 工具。

完整说明见：[`docs/LOCAL_DEPLOY.md`](../docs/LOCAL_DEPLOY.md)

## 文件一览

| 文件 | 作用 |
|------|------|
| `install.bat` | 双击安装入口（推荐） |
| `install.ps1` | 实际安装逻辑（conda 环境 + 依赖 + 可编辑安装） |
| `verify.ps1` | 冒烟测试（导入 / CLI / pygame / Gym env） |
| `requirements-lock.txt` | 已验证可工作的第三方包版本锁定 |
| `environment.yml` | Conda 环境描述（可选，手动 `conda env create`） |
| `pack-for-migration.ps1` | 打迁移 zip（不含 models/缓存） |

## 本机安装

```powershell
cd <repo-root>
.\deploy\install.ps1
```

或双击 `deploy\install.bat`。

## 打迁移包

```powershell
cd <repo-root>
.\deploy\pack-for-migration.ps1
```

产物在 `dist/reinforce-tactics-deploy-*.zip`。

## 目标机

1. 安装 Miniconda/Anaconda  
2. 解压 zip  
3. 运行 `deploy\install.bat`  

> 迁移包 **不含** 已编译的 conda 环境与 PyTorch 二进制（体积过大）。  
> 目标机需联网，由安装脚本重新下载依赖（版本由 lock 文件固定）。
