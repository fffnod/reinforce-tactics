# Bootstrap 运行评审 — 2026-05-08 → 2026-05-10

来自 `benchmarks/bootstrap/` 中最近四次已完成 `ppo_bootstrap` 运行的发现。四次均在 `maps/1v1/beginner.csv` 上对 random 对手跑完完整 6 阶段 curriculum，核心 PPO 超参与 seed（42）相同。它们之间有意改动的是逐步 combat reward shaping（运行 1 → 2/3）与 structure-capture reward shaping（运行 3 → 4）。更广的背景见 [`bootstrap_lessons_learned.md`](bootstrap_lessons_learned.md)（英文原文：[`docs/bootstrap_lessons_learned.md`](../bootstrap_lessons_learned.md)）。

## 覆盖的运行

| # | 运行目录 | git | Reward-shape 变更 | 最终阶段最佳胜率 |
| --- | --- | --- | --- | --- |
| 1 | `20260508_222916` | `2dbb19a` | `damage_scale: 0.5`，`kill: 50.0` | **76.7%** ✅ 已晋升 |
| 2 | `20260509_024930` | `ef2d8a3` | 移除 combat shaping（`damage_scale: 0`，`kill: 0`） | 66.7% ❌ 停滞 |
| 3 | `20260509_153111` | `5abbcbf` | 移除 combat shaping（重复） | 71.7% ❌ 停滞 |
| 4 | `20260509_201218` | `8f821b5` | 增加 `tower_capture: 1500`，`building_capture: 4000`，`hq_capture: 2500` | 61.7% ❌ 停滞 |

"最终阶段" = `beginner_random_20`（`max_actions=20` 的 random 对手，六个 bootstrap 阶段中最难）。晋升阈值为 75%，`patience: 2`。四次运行硬件相同（NVIDIA L4，sb3 2.8.0，torch 2.10）。

## 共享设置

四次运行中以下设置未变：

- **PPO**：lr `3e-4`，`n_steps 2048`，`batch_size 64`，`n_epochs 10`，
  γ `0.99`，λ `0.95`，clip `0.2`，`vf_coef 0.5`，`max_grad_norm 0.5`。
- **网络**：独立 pi/vf MLP `[256, 256]`。
- **Entropy**：每阶段线性调度 `0.10 → 0.03`。
- **Action masking**：启用。
- **Curriculum 控制**：6 阶段，每阶段 `max_timesteps: 2_000_000`
  （`beginner_random_20` 在 commit `d3a272b` 中已提至 3M），
  `n_envs: 4`，`eval_freq: 50_000`，`n_eval_episodes: 60`，
  `promotion_win_rate: 0.75`，`patience: 2`。
- **Beginner 对手**：`random`，`opponent_kwargs.max_actions: 20`
  （对比 starter 阶段使用的更弱默认动作 random）。
- **Reward（始终存在）**：`win 5000`，`loss -5000`，`draw -5000`，
  `win_by_hq_capture 3000`，`win_by_elimination 3000`，`capture 2000`，
  `seize_progress 50`，`structure_control 10`，`unit_diff 1.0`，
  `income_diff 0.5`，`invalid_action -10`，`turn_penalty -20`。

## 各阶段轨迹（四次运行一致）

较早的 curriculum 阶段收敛干净，每次运行看起来相同。来自运行 4 汇总的 `bootstrap_results.csv`（与运行 2–3 使用相同 curriculum）：

| 阶段 | 对手 | 通过于 | 最终胜率 |
| --- | --- | --- | --- |
| `starter_random` | random | ~50–100k | 88–93% |
| `starter_simple` | simple | 首次 eval（100k） | 100% |
| `starter_medium` | medium | 200k（100k 与 150k 时为 0%） | 100% |
| `beginner_balanced_random` | balanced_random | 200k | 100% |
| `beginner_random_10` | random（max_actions=10） | 250–300k | 97–98% |
| `beginner_random_20` | random（max_actions=20） | （见下文） | 各异 |

每次运行都出现两个轨迹特征：

- **`starter_medium` 是阶跃函数。** 前 150k 步胜率停在 0.0，episode 触达时限（avg reward ≈ -5000），然后在 200k 跳到 1.0。Agent 必须先发现 HQ capture 才能对 `medium` 获胜；稠密 reward 中没有任何东西逐渐逼近解。
- **每阶段首次 eval 在 `t = stage_steps + 4`**（curriculum runner 的 4 步 warm-eval）。对 `starter_simple` 与 `beginner_balanced_random`，agent 一进阶段就立即获胜，表明阶段间正向迁移。

## `beginner_random_20` 上的差异

四次运行在此分道扬镳。

### 运行 1 — `20260508_222916`（含 combat shaping）

`damage_scale: 0.5`，`kill: 50.0`。`eval_curves.png` 显示 avg-reward y 轴顶端约 **15,000**——稠密 combat 项贡献了真实量级。

- 最佳胜率 **76.7%** → 越过 75% 门槛。
- `combat_summary` 显示 **captures 与 kills 均随训练上升**
  （结束时约 40–60 captures、40+ kills / 局，造成伤害显著超过承受伤害——净 dealt 为正）。
- `outcome_breakdown` 含 `losses_by_hq_capture` 切片——random 对手偶尔会占领 agent 的 HQ。

### 运行 2 — `20260509_024930`（移除 combat shaping）

`damage_scale: 0.0`，`kill: 0.0`。Avg-reward 轴顶端约 **10,000**（与稠密 combat 项为零一致）。

- 最佳胜率 **66.7%**——远低于 75% 门槛；预算耗尽。
- `outcome_breakdown` 仍含 `losses_by_hq_capture`，agent 仍易被 HQ rush。
- avg-reward 曲线比运行 1 *量级更低且更噪*——策略可跟随的稠密梯度更少。

### 运行 3 — `20260509_153111`（移除 combat shaping，重复）

与运行 2 相同 reward 配置、相同 seed。

- 最佳胜率 **71.7%**——比运行 2 更接近阈值但仍低于。
- `outcome_breakdown` 图例 **省略 `losses_by_hq_capture`**——本运行 eval 中 agent 从未因 HQ capture 落败，只有 elimination/draws。防守扎实；缺口在于收官取胜。
- 无配置差异下比运行 2 高约 5pp，突显在此性能水平下 60-episode 评估的噪声。

### 运行 4 — `20260509_201218`（加入 structure-capture rewards）

在运行 2–3 的无 combat 基线上增加三项新 reward：`tower_capture: 1500`，`building_capture: 4000`，`hq_capture: 2500`。Combat shaping（`damage_scale`、`kill`）仍为零。训练在 2M `max_timesteps` 上限后继续约 300k（runner 完成了进行中的 collection 周期），从 300k → 2.3M 共 41 次 eval。

- 最佳胜率 **61.7%** 于 step 2.2M——四次中最终数字最差，*但预算耗尽时轨迹仍在爬升*：

  | 步数区间 | 平均胜率 | 窗口内最大 |
  | --- | --- | --- |
  | 0.3–0.5M | 0.343 | 0.400 |
  | 0.5–0.75M | 0.300 | 0.317 |
  | 0.75–1.0M | 0.350 | 0.383 |
  | 1.0–1.25M | 0.373 | 0.450 |
  | 1.25–1.5M | 0.420 | 0.467 |
  | 1.5–1.75M | 0.450 | 0.517 |
  | 1.75–2.0M | 0.527 | 0.600 |
  | 2.0–2.3M | 0.537 | 0.617 |

- **防守在 ~1.1M 完全解决。** 阶段前约 1M 中，agent 每 60-episode eval 输掉 5–10 局（多为 elimination）。自 step **1.1M 起，此后每次 eval *零* 败**——到 2.3M 连续 24 次 eval 无败。1.1M 后策略对 random_20 无法击破，但转胜缓慢。
- **真正瓶颈 = 收官。** 全阶段合计：1026 胜 / 96 负 / **1338 平**（54% episode 为平局）。Agent 多数平局，不败，但只有时能 capture。
- **平均 episode 长度 ~1100–1300 步**（接近但低于 1500 上限）并贯穿始终——对局很长，每回合累积 `turn_penalty: -20`。
- **`eval_curves.png` 上 `approx_kl` 轴达 ~0.14**（运行 1–3 为 ≤0.05）。本运行 PPO 更新明显更大——很可能是新 `building_capture: 4000` 远超既有稠密项、产生更高方差 advantage 的副作用。
- **`value_loss` 轴跨 10⁵–10⁶**，也高于先前运行，与更大 reward 量级一致。
- `combat_summary` 显示 captures 与 attacks 上升；`outcome_breakdown` 显示阶段后半损失类别塌缩为零，平局吸收了差额。

## 趋势与弱点

1. **移除 combat shaping 在最难阶段损失约 5–10 个百分点。** 这仍是四次运行中最大的单一信号。运行 1（`damage_scale: 0.5`，`kill: 50`）是唯一越过 75% 的。用 structure-capture shaping 替换 combat shaping（运行 4）未能填补差距。
2. **`beginner_random_20` 的瓶颈从防守转向进攻。** 早期运行（1–3）偶有 `losses_by_hq_capture` 或 `losses_by_elimination`。运行 4 在 ~1.1M 步后 *完全消灭损失*，但并未代之以胜利——变成平局。新 structure-capture rewards 很可能教会防守式地图控制，却没有足够梯度去推动终结。
3. **`max_timesteps: 2M` 预算不足。** 运行 4 的胜率曲线在上限前单调改善（阶段末 0.34 → 0.54 → 0.62）。commit `d3a272b` 中提至 3M 是合理的——线性外推，运行 4 风格策略在 3M 有望达到 70%+。
4. **平局与负一样严惩（-5000）。** 再加 `max_turns: 100` 上的 `turn_penalty: -20`，强烈抑制任何谨慎的"拖延并稳住"打法，但讽刺的是运行 4 策略正收敛于此（54% 平局率，无败）。Reward 形态在与实际学到的策略对抗。
5. **接近阈值时 eval 噪声不可忽视。** 运行 2 与 3（配置相同）之间 5pp 差距约为 1 个标准误（`sqrt(0.7*0.3/60) ≈ 5.9%`）。`patience: 2` 要求连续两次越过 75%，因此真实胜率约 74% 的策略多数时候会晋升失败，即使策略确实接近。
6. **0.03 的 entropy 下限对收敛策略偏高。** 调度结束于 0.03，不论阶段跑多久。`max_timesteps` 现为 3M，agent 在 step 3M 仍被要求注入有意义的探索噪声——恰恰是应承诺的时候。
7. **Reward 量级不平衡，可能诱发高 `approx_kl`。** `building_capture: 4000` 与 `win: 5000` 同量级，但触发频繁得多，比 `unit_diff: 1.0` / `income_diff: 0.5` 稠密项大 4 个数量级。运行 4 的 `approx_kl` 峰值 ~0.14（运行 1–3 ≤0.05），暗示策略被这些大稠密 reward 猛拽。

## 各运行观察到的行为

- **全部四次运行**：相同的 `starter_medium` 阶跃（200k 时 0% → 100%）；进入 `starter_simple` 与 `beginner_balanced_random` 的正向迁移（首次 eval 胜率 1.0）；快速穿越 `beginner_random_10`（进阶段 50–100k 内 ≥97%）。
- **运行 1（含 combat shaping）**：`beginner_random_20` 上 captures *与* kills 双升；净伤害为正；以 combat 收官。76.7% 通过晋升。
- **运行 2（无 shaping）**：停滞于 66.7%，仍有部分局输给 HQ capture，reward 曲线量级更低。
- **运行 3（无 shaping）**：停滞于 71.7%，eval 切片中无 HQ capture 败——学会防守但未学会收官。
- **运行 4（structure-capture rewards）**：停滞于 61.7% 但仍在爬升。策略清晰分为 1.1M 前"仍会输"与 1.1M 后"从不败、多数平"两个区间。`approx_kl` 为各运行最高（~0.14）。受预算限制，非性能上限。

## 建议

按预期影响大致排序：

1. **以较低量级重新启用 combat shaping，并叠加 structure-capture rewards。** 尝试在运行 4 的 reward 配置上叠加 `damage_scale: 0.2`，`kill: 20.0`。数据表明 combat shaping 产生 *结束* 对局的梯度，而新 capture rewards 产生 *控制* 地图的梯度。运行 1 只有前者并获胜；运行 4 只有后者并打平。
2. **已完成**：`beginner_random_20.max_timesteps` 从 2M 提至 3M（commit `d3a272b`）。运行 4 单调上升的轨迹使这明显是正确决定。
3. **降低 `beginner_random_20` 的 entropy 下限**至 `end: 0.01`，使策略能在新 3M 预算的最后 ~1M 变锐。
4. **软化平局惩罚。** 让 `draw` 比 `loss` 负得少（例如 `draw: -1000`）——运行 4 已收敛但爱平的策略正被从它学到的唯一稳定策略推开。
5. **若下次运行仍出现 `approx_kl > 0.1`，考虑仅在本阶段降低学习率或 clip range。** 新 capture rewards 产生更大 advantage，可能需要更小更新以保持稳定。
6. **仅当未来运行落在 73–77% 区间时，考虑将 `n_eval_episodes` 提至 100**——100 episode 时标准误从 ~5.9% 降至 ~4.3%，实质性减少假阴性晋升检查。不要预先改。
7. **变换 seed 一次**（例如 seed=43、44），以确认 reward-shaping 回归是结构性的，而非单次倒霉抽签。
