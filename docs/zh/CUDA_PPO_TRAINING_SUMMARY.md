# CUDA PPO 训练过程总结

> 日期：2026-08-06  
> 机器：Windows + NVIDIA GeForce RTX 5090  
> 仓库分支：`feature/local-deploy`  
> 目标：在 CUDA 上训练 MaskablePPO，验证能否学会击败规则 AI（SimpleBot）

本文记录从环境配置、算法选择、课程训练到离线评估的完整过程，包含实际执行的指令、各阶段含义、关键指标变化，以及“学习是否有效”的判定方法。

---

## 1. 目标与结论（先看结果）

| 问题 | 结论 |
|------|------|
| 能否用 CUDA 训练？ | **能**。`torch 2.11.0+cu128`，设备 RTX 5090 |
| PPO 是否在学？ | **是**。对 random 胜率 0% → 峰值 72.5% |
| 能否击败规则 AI？ | **能**。best 模型 vs SimpleBot：**96%**（50 局：48 胜 / 0 负 / 2 平） |

**最终可用模型：**

```text
benchmarks/bootstrap/cuda_short_curriculum/checkpoints/starter_random_best.zip
```

对应训练步数约 **700,000**（阶段内评估峰值胜率 72.5%）。

---

## 2. 环境准备

### 2.1 软件栈

| 组件 | 版本 / 说明 |
|------|-------------|
| Conda 环境 | `reinforce-tactics`（Python 3.12） |
| PyTorch | `2.11.0+cu128`（RTX 50 系需要 CUDA 12.8 / sm_120） |
| 算法库 | `stable-baselines3 2.9.0` + `sb3-contrib 2.9.0`（MaskablePPO） |
| 项目 | 可编辑安装 `reinforcetactics 0.3.3` |

### 2.2 为何不用 lock 里的默认 torch？

`deploy/requirements-lock.txt` 锁定的是 **CPU 版** `torch==2.13.0`（参考机默认配置）。  
RTX 5090 属于 Blackwell（`sm_120`），需要带 **CUDA 12.8** 的 wheel，否则无法在 GPU 上跑。

### 2.3 安装指令（本机实际执行）

```powershell
# 进入仓库根目录
cd D:\grok\reinforce-tactics

# PATH 中加入 Anaconda（若 conda 不在 PATH）
$env:Path = "C:\ProgramData\anaconda3;C:\ProgramData\anaconda3\Scripts;" + $env:Path

# 1) 安装 lock 中除 torch 以外的依赖
#    （先生成 requirements-no-torch.txt，去掉 torch== 行）
conda run -n reinforce-tactics python -m pip install -r deploy\requirements-no-torch.txt

# 2) 安装 CUDA 12.8 版 PyTorch（RTX 5090）
conda run -n reinforce-tactics python -m pip uninstall -y torch
conda run -n reinforce-tactics python -m pip install torch --index-url https://download.pytorch.org/whl/cu128

# 3) 可编辑安装本仓库（GUI extras 的依赖已由 lock 装好，用 --no-deps）
conda run -n reinforce-tactics python -m pip install -e ".[gui]" --no-deps

# 4) 训练进度条依赖
conda run -n reinforce-tactics python -m pip install tqdm rich
```

### 2.4 CUDA 冒烟验证

```powershell
# 使用环境内 python 更稳妥
$py = "C:\ProgramData\anaconda3\envs\reinforce-tactics\python.exe"

& $py -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0)); x=torch.randn(2,3,device='cuda'); print(x@x.T)"
```

**期望输出要点：**

- `2.11.0+cu128`
- `True`
- `NVIDIA GeForce RTX 5090`
- 矩阵乘法无报错

仓库内也有脚本：

```powershell
& $py scripts\smoke_cuda_ppo.py
```

---

## 3. 算法与训练设计选择

### 3.1 为什么是 MaskablePPO + `flat_discrete`？

项目基准文档（`benchmarks/ppo_vs_simplebot/`）说明：

| 动作空间 | 问题 | 结果 |
|----------|------|------|
| `MultiDiscrete` + 分维 mask | 掩码是各维合法值的**并集**，约 99% 采样动作实际非法 | 难学，奖励被 invalid 惩罚淹没 |
| `flat_discrete` + 精确 mask | 每步枚举合法动作，mask 与规则一致 | 可学到可玩策略 |

因此本次验证统一使用：

- **算法**：`MaskablePPO`（`sb3-contrib`）
- **动作空间**：`env.action_space_type: flat_discrete`
- **设备**：`device: cuda`

### 3.2 为什么用课程（curriculum）而不是一上来打 SimpleBot？

先做了一次 **直接打规则 bot** 的短训（见第 4 节），出现“高回报、零胜率、全平局”的虚假学习。  
课程思路（与官方 `configs/ppo/bootstrap.yaml` 一致）：

1. **先打弱对手（random）** → 容易拿到真正的胜负信号  
2. **再打规则 bot（simple）** → 验证是否可迁移 / 击败脚本 AI  

### 3.3 课程配置文件

路径：`configs/ppo/cuda_short_curriculum.yaml`

| 字段 | 取值 | 含义 |
|------|------|------|
| `algorithm` | `maskable_ppo` | 带动作掩码的 PPO |
| `env.n_envs` | 8 | 8 个并行环境（SubprocVecEnv） |
| `env.action_space_type` | `flat_discrete` | 精确合法动作索引 |
| `env.max_turns` | 40 | 到回合上限判平（并给 draw 惩罚） |
| `ppo.device` | `cuda` | GPU 训练 |
| `ppo.batch_size` | 256 | 适配 GPU 的较大 batch |
| `ppo.policy_kwargs.net_arch` | `[256,256]` | 策略/价值网络宽度 |

**奖励设计要点（相对“伪学习”配置的修正）：**

| 奖励项 | 作用 |
|--------|------|
| `win / loss / draw = ±50` | 明确终局胜负 |
| `win_speed_bonus = 50` | 鼓励更快结束比赛 |
| `tower/building/hq_capture` | 鼓励占领而非只磨血 |
| `haste/buff/... = 0` | 避免刷增益动作骗 shaping |
| `invalid_action = -0.1` | 有 mask 时仅作轻微兜底 |

---

## 4. 阶段一览：计划中的两个阶段

配置里设计了两阶段；**实际只跑完阶段 1**（因晋升条件未连续满足而 stall）。

### 4.1 阶段 A：`starter_random`（已执行）

| 项目 | 内容 |
|------|------|
| 地图 | `maps/1v1/starter.csv`（小图，决策空间小，好学） |
| 对手 | `random`：随机合法动作，强度低、方差大 |
| 预算 | 最多 **800,000** env steps |
| 晋升门槛 | 评估胜率 **≥ 70%** |
| `patience` | **2**（需在评估中**连续**达标才会晋升；峰值一次 70% 不够） |
| `ent_coef` | **0.10**（更高熵，鼓励探索） |
| 评估 | 每 50k 步左右评估 40 局 |

**阶段涵义：**  
建立“能赢”的基本策略——造兵、推进、歼灭/占领——而不是在复杂规则 bot 上卡死。

### 4.2 阶段 B：`starter_simple`（配置了但未执行）

| 项目 | 内容 |
|------|------|
| 地图 | 同 `starter` |
| 对手 | `simple`：规则 AI **SimpleBot**（脚本启发式） |
| 预算 | 最多 **1,500,000** steps |
| 晋升门槛 | 胜率 **≥ 60%**，`patience=3` |
| `ent_coef` | **0.05**（对手更强时降低随机探索） |

**阶段涵义：**  
在已会赢的基础上，专门适应规则 bot 的行为模式。  
本次因阶段 A stall，**没有进入本阶段正式训练**；但用阶段 A 的 best 模型做了 **离线 vs SimpleBot** 评估（见第 7 节），已足够验证“能打赢规则 AI”。

### 4.3 对照实验：直接 vs bot（失败路径，已执行）

| 项目 | 内容 |
|------|------|
| 配置 | `configs/ppo/cuda_verify_vs_bot.yaml` |
| 地图 | `maps/1v1/beginner.csv` |
| 对手 | `bot`（SimpleBot 别名） |
| 步数 | **300,000** |
| 训练命令 | 见下节 |
| 结果 | 训练 reward 上升，但 **50 局评估全是 max_turns 平局，胜率 0%** |

典型行为统计（eval）：

- `captures = 0`（从不占建筑）  
- 大量 `attack` / buff 类动作，刷 shaping 回报  
- `avg_turns = 60`（打到回合上限）  

**涵义：** 回报曲线上升 ≠ 学会胜利；必须用 **胜率 / 终局原因 / 占领次数** 交叉验证。

---

## 5. 实际使用的指令

以下均在仓库根目录 `D:\grok\reinforce-tactics` 执行。  
`$py` 表示：

```powershell
$py = "C:\ProgramData\anaconda3\envs\reinforce-tactics\python.exe"
$env:PYTHONUNBUFFERED = "1"
$env:SDL_VIDEODRIVER = "dummy"   # 无头训练，避免 pygame 抢显示
$env:MPLBACKEND = "Agg"
```

### 5.1 对照短训（直接 vs bot，约 30 万步）

```powershell
& $py scripts\train\train_feudal_rl.py `
  --config configs\ppo\cuda_verify_vs_bot.yaml `
  --mode flat `
  --use-action-masking `
  --device cuda
```

- 日志目录示例：`logs\maskable_ppo_20260806_223044\`  
- 模型：`final_model.zip`、`best_model\best_model.zip`

### 5.2 课程训练（主实验）

```powershell
& $py scripts\train\train_bootstrap.py `
  --config configs\ppo\cuda_short_curriculum.yaml `
  --device cuda `
  --skip-plots `
  --skip-videos `
  --sanity-episodes 50 `
  --output-dir benchmarks\bootstrap\cuda_short_curriculum
```

**参数涵义：**

| 参数 | 涵义 |
|------|------|
| `--config` | 课程 + 超参 YAML |
| `--device cuda` | 强制 GPU（`auto` 时也会在有 CUDA 时选 GPU） |
| `--skip-plots / --skip-videos` | 跳过图表/录像，加快收尾 |
| `--sanity-episodes 50` | 结束后再做一轮快速评估 |
| `--output-dir` | 所有 checkpoint / 指标写到该目录 |

**输出目录结构：**

```text
benchmarks/bootstrap/cuda_short_curriculum/
  cuda_short_curriculum.yaml      # 配置快照
  resolved_config.yaml
  policy_summary.json
  train_metrics.csv               # 训练过程指标
  bootstrap_results.csv           # 每轮评估汇总
  run_status.json                 # 结束状态（stall/完成）
  final_model.zip
  checkpoints/
    starter_random.zip
    starter_random_best.zip       # ★ 推荐使用
  starter_random/
    best_model.zip
    eval_results.jsonl
    stage_final.zip
  tensorboard/MaskablePPO_0/
```

### 5.3 离线评估（验证是否打得过规则 AI）

```powershell
# vs SimpleBot（规则 AI）
& $py scripts\eval_cuda_ppo_vs_bot.py `
  --model benchmarks\bootstrap\cuda_short_curriculum\checkpoints\starter_random_best.zip `
  --episodes 50 `
  --map-file maps/1v1/starter.csv `
  --opponent simple `
  --device cuda `
  --out benchmarks\bootstrap\cuda_short_curriculum\eval_best_vs_simple.json

# vs random（对照）
& $py scripts\eval_cuda_ppo_vs_bot.py `
  --model benchmarks\bootstrap\cuda_short_curriculum\checkpoints\starter_random_best.zip `
  --episodes 50 `
  --map-file maps/1v1/starter.csv `
  --opponent random `
  --device cuda `
  --out benchmarks\bootstrap\cuda_short_curriculum\eval_best_vs_random.json
```

评估脚本会：

1. 用 `MaskablePPO.load(..., device=cuda)` 加载  
2. 构造带 mask 的 `make_maskable_env`  
3. 调用 `reinforcetactics.rl.evaluation.evaluate_model`（预测时传入 `action_masks`）  
4. 统计胜率、终局原因、造兵与占领等

---

## 6. 数据变化：阶段 `starter_random` 全过程

来源：`benchmarks/bootstrap/cuda_short_curriculum/bootstrap_results.csv`  
评估：每点约 **40 局**，对手 `random`，地图 `starter`。

### 6.1 胜率 / 战绩表

| 步数 | 胜率 | 胜 | 负 | 平 | 平均回报 | 平均长度 | 平均回合 |
|------|------|----|----|-----|----------|----------|----------|
| 8 | **0.0%** | 0 | 26 | 14 | -51.1 | 49 | 19.7 |
| 50,000 | 30.0% | 12 | 12 | 16 | +8.3 | 170 | 27.7 |
| 100,000 | 65.0% | 26 | 3 | 11 | +67.6 | 180 | 23.5 |
| 150,000 | 65.0% | 26 | 1 | 13 | +73.3 | 186 | 25.2 |
| 200,000 | 60.0% | 24 | 2 | 14 | +61.9 | 154 | 24.4 |
| 250,000 | 57.5% | 23 | 1 | 16 | +63.5 | 159 | 26.2 |
| 300,000 | 65.0% | 26 | 1 | 13 | +70.9 | 167 | 24.1 |
| 350,000 | 57.5% | 23 | 4 | 13 | +54.3 | 167 | 25.2 |
| 400,000 | **70.0%** | 28 | 3 | 9 | +72.0 | 151 | 22.1 |
| 450,000 | 55.0% | 22 | 1 | 17 | +53.3 | 152 | 26.5 |
| 500,000 | 67.5% | 27 | 0 | 13 | +68.3 | 149 | 24.1 |
| 550,000 | 65.0% | 26 | 0 | 14 | +65.3 | 133 | 22.9 |
| 600,000 | 62.5% | 25 | 0 | 15 | +59.3 | 118 | 23.8 |
| 650,000 | 65.0% | 26 | 0 | 14 | +69.2 | 131 | 24.9 |
| **700,000** | **72.5%** | **29** | **0** | **11** | **+77.9** | **125** | **22.7** |
| 750,000 | 60.0% | 24 | 0 | 16 | +63.2 | 135 | 25.2 |
| 800,000 | 52.5% | 21 | 0 | 19 | +59.4 | 147 | 27.8 |

### 6.2 趋势解读

```text
胜率
  ^
70%|              * (400k)           * (700k 峰值 72.5%)
65%|      * *         *     *   * *
60%|        *               *
50%|  *                              * (800k 回落)
 0%| *
   +----------------------------------------> steps
     0   100k  200k  300k  400k  500k  600k  700k  800k
```

1. **0 → 100k：快速爬升**  
   - 0% → 65%，回报从 -51 到 +68  
   - 说明 mask + 奖励尺度正确，策略迅速找到“能赢”的方向  

2. **100k → 700k：高位震荡**  
   - 胜率 55%–72.5% 波动，**败场逐渐趋近 0**（后期多为平局而不是输）  
   - 峰值 **700k / 72.5%** → 保存为 best checkpoint  

3. **700k → 800k：回落**  
   - 胜率掉到 52.5%，平局变多  
   - 可能原因：持续高熵探索（`ent_coef=0.10`）、过拟合近期轨迹、或评估噪声  

4. **课程 stall 原因**  
   - 门槛 70%，`patience=2` 要求**连续**达标  
   - 仅出现过 **单次** ≥70%（400k、700k），从未连续两次  
   - `run_status.json`：`status = curriculum_stalled`，`achieved_win_rate = 0.725`  

### 6.3 行为层面的“学到了什么”（相对对照实验）

在 200k 左右的评估快照中已可见健康行为（示例字段来自 `eval_results.jsonl`）：

| 信号 | 对照实验（直接 vs bot） | 课程 200k vs random |
|------|------------------------|---------------------|
| 胜率 | 0% | 60% |
| 占领 `captures` | 0 | 有（塔/建筑） |
| 终局 | 全 `max_turns_draw` | 歼灭 + 部分平局 |
| 造兵 | 几乎全是法师系刷战 | 以战士 `W` 等为主力 |

说明策略从“刷 shaping”转向“结束比赛 / 占领 / 歼灭”。

### 6.4 训练过程其它指标（定性）

来自 `train_metrics.csv` 与日志：

| 指标 | 变化方向 | 含义 |
|------|----------|------|
| `explained_variance` | 由接近 0 升到 ~0.8+ | 价值网络在拟合回报 |
| `entropy_loss`（绝对值） | 有所下降 | 策略从更随机到更自信 |
| `approx_kl` | 维持较小 | PPO 更新未剧烈发散 |
| 吞吐 | ~1500–2200 FPS（8 env） | 瓶颈主要在 CPU 环境步进；GPU 仍用于网络更新 |

---

## 7. 如何验证“学习是有效的”

单看 `ep_rew_mean` 不够。本次采用 **多层证据**：

### 7.1 训练中评估（in-training eval）

- 固定间隔评估 40 局  
- 主指标：**胜率**，辅以 W/L/D、平均回报、回合数  
- 课程晋升门槛绑在胜率上，避免“高分平局”

### 7.2 终局原因（end_reason）

| 终局 | 含义 | 健康表现 |
|------|------|----------|
| `elimination` | 歼灭对方单位获胜 | 课程后期应增多 |
| `hq_capture` | 占领总部 | 可选胜利方式 |
| `max_turns_draw` | 回合上限平局 | 过多则策略偏保守 |
| `max_steps_truncate` | 环境步数截断 | 过多可能卡在“不结束回合” |

**对照实验失败标志：** 50/50 `max_turns_draw`，0 胜 0 负。  
**课程成功标志：** 出现大量 `elimination`，败场接近 0。

### 7.3 行为统计

有效学习通常伴随：

- `captures` / `seize` > 0  
- 合理 `create_unit`（有兵可打）  
- 不是只刷 `haste` / buff  

### 7.4 离线固定评估（最关键）

对 **best 模型** 做独立 50 局评估（与训练晋升逻辑解耦）：

| 对手 | 地图 | 局数 | 胜率 | 胜/负/平 | 平均回报 | 主要终局 |
|------|------|------|------|----------|----------|----------|
| **simple（规则 AI）** | starter | 50 | **96%** | 48 / 0 / 2 | ~1214 | 48 次歼灭 |
| random | starter | 50 | 58% | 29 / 1 / 20 | ~738 | 30 次歼灭，20 平 |

结果文件：

- `benchmarks/bootstrap/cuda_short_curriculum/eval_best_vs_simple.json`  
- `benchmarks/bootstrap/cuda_short_curriculum/eval_best_vs_random.json`  

**解读：**

1. vs SimpleBot **96%** → **可以有效击败规则 AI**（在 starter 图设定下）。  
2. vs random **58%**、平局较多 → random 行为更发散，best 策略对“可预测的规则 bot”利用更充分；也说明 58% 仍显著优于随机开局的 0%。  
3. 评估用 mask 正确预测；若忘记 mask，MaskablePPO 结果会失真。

### 7.5 对照实验对比（证明验证方法必要）

| 实验 | 训练回报趋势 | 离线胜率 vs 规则 bot | 判定 |
|------|--------------|----------------------|------|
| 直接 beginner + bot，30 万步 | 上升 | **0%**（全平） | **无效/假学习** |
| 课程 starter + random，80 万步 + best | 上升且胜率上升 | **96%** | **有效学习** |

---

## 8. 运行状态与产物清单

### 8.1 `run_status.json` 摘要

```json
{
  "status": "curriculum_stalled",
  "stalled_stage": "starter_random",
  "achieved_win_rate": 0.725,
  "threshold": 0.7,
  "best_checkpoint_timestep": 700000
}
```

含义：阶段 1 用尽预算未**连续**跨过晋升线；但 best 模型已具备实战能力。

### 8.2 关键路径

| 路径 | 说明 |
|------|------|
| `configs/ppo/cuda_short_curriculum.yaml` | 课程配置 |
| `configs/ppo/cuda_verify_vs_bot.yaml` | 对照短训配置 |
| `scripts/train/train_bootstrap.py` | 课程训练入口 |
| `scripts/train/train_feudal_rl.py` | 平面 MaskablePPO 入口 |
| `scripts/eval_cuda_ppo_vs_bot.py` | 带 mask 的评估脚本 |
| `scripts/smoke_cuda_ppo.py` | CUDA 冒烟 |
| `benchmarks/bootstrap/cuda_short_curriculum/` | 本次主实验全部产物 |
| `logs/maskable_ppo_20260806_223044/` | 对照短训产物 |

---

## 9. CPU vs CUDA 训练效率对比（本机实测）

> 测试日期：2026-08-06  
> GPU：NVIDIA GeForce RTX 5090 · `torch 2.11.0+cu128`  
> 原始数据：`benchmarks/cpu_vs_cuda/bench_result.json`、`update_only.json`  
> 复现脚本：`scripts/bench_cpu_vs_cuda.py`

### 9.1 测试设定（公平对照）

| 项目 | 取值 |
|------|------|
| 算法 | MaskablePPO + `flat_discrete` |
| 网络 | `net_arch = [256, 256]`（约 0.76M 参数，与课程训练一致） |
| 并行环境 | `n_envs = 8`（SubprocVecEnv） |
| `n_steps` / `batch_size` | 2048 / 256 |
| 地图 / 对手 | `maps/1v1/starter.csv` / `random` |
| 端到端步数 | **65,536** env steps |
| 仅更新测试 | 对约 16,384 transitions 调用 `model.train()` × 10 epochs |

```powershell
$py = "C:\ProgramData\anaconda3\envs\reinforce-tactics\python.exe"
& $py scripts\bench_cpu_vs_cuda.py `
  --timesteps 65536 --n-envs 8 --n-steps 2048 --batch-size 256 `
  --devices cuda,cpu `
  --out benchmarks\cpu_vs_cuda\bench_result.json
```

### 9.2 端到端结果（采样 + PPO 更新）

| 设备 | 墙钟时间 | 吞吐 (FPS) | 相对加速 |
|------|----------|------------|----------|
| **CUDA** | **37.7 s** | **1739** | **1.32×** |
| **CPU** | 49.8 s | 1316 | 1.0×（基准） |

含义：同样跑完 65,536 步，**CUDA 大约快 32%**。

按此吞吐粗算 **80 万步**（接近课程阶段 1 预算，不含评估开销）：

| 设备 | 估时 |
|------|------|
| CUDA | ~7.7 分钟 |
| CPU | ~10.1 分钟 |

SB3 日志中的瞬时 FPS（含更新后）：

| 迭代 | CUDA FPS | CPU FPS |
|------|----------|---------|
| 1（几乎全是采样） | 2316 | 2046 |
| 4（采样 + 多次 train） | 1867 | 1447 |

课程长训时 CUDA 日志约在 **1500–2200 FPS**，与本次 bench 一致。

### 9.3 仅 PPO 网络更新（`model.train()`）

| 设备 | 平均耗时 | 加速比 |
|------|----------|--------|
| **CUDA** | **2.49 s** | **1.79×** |
| **CPU** | 4.45 s | 1.0× |

纯更新阶段 GPU 优势大于端到端（约 **1.8×**），但仍不是数量级差距。

### 9.4 为什么 CUDA 没有快很多？

本项目一步训练大致是：

```text
┌─────────────────────────────────┐
│ 环境 rollout（游戏逻辑）          │  ← 主要在 CPU
│ 并行 8 个 env.step               │  ← 往往占大部分墙钟
└─────────────────────────────────┘
                ↓
┌─────────────────────────────────┐
│ PPO 前向 / 反向 / 优化           │  ← CUDA 或 CPU
│ 网络较小（~0.76M 参数）          │  ← 5090 算力吃不饱
└─────────────────────────────────┘
```

1. **瓶颈在环境仿真**，不在 GPU 算力。  
2. 策略网络相对较小，GPU 无法充分发挥。  
3. 每次更新有 **CPU↔GPU 数据搬运**，会吃掉一部分收益。  
4. 端到端 ~**1.3×**、纯 `train()` ~**1.8×**，说明 CUDA 主要省“更新网络”那一段。

### 9.5 怎么选设备？

| 场景 | 建议 |
|------|------|
| 本机有 RTX / 已装 cu128 torch | 用 **`device=cuda`**，略快且不吃亏 |
| 无 GPU / 服务器纯 CPU | **CPU 完全可行**，大约慢三成 |
| 想更大 CUDA 收益 | 加大 `batch_size` / 网络（如 Spatial CNN），或优化 env 并行 |
| 部署文档默认 CPU torch | 小网络 PPO 可接受；有 50 系 GPU 时仍建议换 cu128 |

---

## 10. 经验与后续建议

### 10.1 已验证的有效做法

1. **CUDA**：RTX 5090 使用 `pip install torch --index-url https://download.pytorch.org/whl/cu128`  
2. **动作空间**：`flat_discrete` + MaskablePPO  
3. **课程**：先 random 再 simple；奖励强调胜负与占领  
4. **验证**：胜率 + 终局原因 + 占领统计 + 离线评估，缺一不可  
5. **设备**：CUDA 端到端约 **1.3×** CPU；网络更新约 **1.8×**（本项目小网络）

### 10.2 可改进点

| 问题 | 建议 |
|------|------|
| 晋升 `patience=2` 导致 stall | 降到 1，或降低门槛到 0.65，或拉长预算 |
| 后期胜率回落 | 峰值后降低 `ent_coef`；或 early-stop 用 best 进下一阶段 |
| 未训练阶段 B | 从 `starter_random_best.zip` warm-start，直接训 `opponent=simple` |
| 更大地图 / MediumBot | 继续官方 `configs/ppo/bootstrap.yaml` 全课程（百万～千万步级） |
| CUDA 加速有限 | 加大网络/batch，或提升 env 吞吐（更多并行、减评估频率） |

### 10.3 续训示例（从 best 继续打 SimpleBot）

可在配置中设 warm-start / 或使用项目 resume 机制；也可新建仅含 `starter_simple` 的 YAML，加载：

```text
benchmarks/bootstrap/cuda_short_curriculum/checkpoints/starter_random_best.zip
```

（具体 resume 字段以 `train_bootstrap.py` / `TrainingConfig.resume` 为准。）

---

## 11. 一句话总结

在 **RTX 5090 + CUDA 12.8 PyTorch** 上，用 **MaskablePPO + flat_discrete**，经 **starter 图 vs random 的课程训练（约 80 万步）**，best 模型在 **starter 图 vs SimpleBot 上达到约 96% 胜率**；  
对照“直接打 bot 却只刷回报”的实验说明：**必须以胜率与终局质量，而不是仅以回报曲线，来判定强化学习是否有效。**  
同设定下 **CUDA 端到端约比 CPU 快 1.3 倍**（环境步进仍是主瓶颈）。

---

## 附录 A：快速复现检查清单

```powershell
cd D:\grok\reinforce-tactics
$py = "C:\ProgramData\anaconda3\envs\reinforce-tactics\python.exe"

# CUDA
& $py -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"

# 评估现有 best（无需重训）
& $py scripts\eval_cuda_ppo_vs_bot.py `
  --model benchmarks\bootstrap\cuda_short_curriculum\checkpoints\starter_random_best.zip `
  --episodes 50 --map-file maps/1v1/starter.csv --opponent simple --device cuda

# CPU vs CUDA 吞吐对比
& $py scripts\bench_cpu_vs_cuda.py --timesteps 65536 --n-envs 8 --devices cuda,cpu

# 重跑课程（可选）
& $py scripts\train\train_bootstrap.py `
  --config configs\ppo\cuda_short_curriculum.yaml `
  --device cuda --skip-plots --skip-videos `
  --output-dir benchmarks\bootstrap\cuda_short_curriculum_rerun
```

## 附录 B：名词表

| 名词 | 含义 |
|------|------|
| MaskablePPO | 支持动作掩码的 PPO，非法动作采样概率为 0 |
| flat_discrete | 把合法动作摊平成 Discrete(N) 索引 |
| SimpleBot / simple / bot | 项目内规则脚本 AI（`bot` 为 simple 别名） |
| random | 均匀随机合法动作的对手 |
| env step | 一次环境 `step`；并行 8 环境时吞吐更高 |
| promotion / patience | 课程晋升：胜率达标需连续出现 patience 次 |
| stall | 阶段预算用尽仍未晋升 |
| shaping | 中间奖励塑形；过强可导致假学习 |
| FPS（训练） | 每秒完成的环境步数；越高训练越快 |
