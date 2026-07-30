# 附录 C　历史实验索引与因果证据表

## C.1 怎样阅读本附录

本附录整理仓库保留的 Bootstrap 实验配置和两次 2026 年 7 月审查。所有数值与结论均标记为**历史记录**，其含义是：

- 当时的代码、配置、硬件与随机轨迹产生过该现象；
- 当前仓库可能已经修复、重构或改变默认值；
- 除非教材冒烟或独立复现实验明确说明，不能把历史结果当作 2026-07-29 当前代码的重复验证。

证据分为五栏：

1. **当时现象**：日志或结果中看到了什么；
2. **调查证据**：支持某个解释的指标、回放或消融；
3. **已排除原因**：至少有对照证据反对的解释；
4. **已落地变化**：代码或配置中已经存在的修正；
5. **开放问题**：仍需新的独立实验。

配置文件名是溯源坐标，不代替本附录中的解释。

## C.2 v15–v23：课程门槛与熵调度阶段

| 版本 | 主要变更 | 历史现象 | 后续证据如何修正理解 |
|---|---|---|---|
| v15 | 降低后段 entropy floor | 在 random_10 附近停滞 | 不能只归因于对手；使用五单位 roster 和当时奖励/经济 |
| v16 | 加入 turn penalty 等多项变化 | 形成新的课程墙 | 同时改 roster、奖励与经济，混杂严重 |
| v17 | random 阶段 patience 调整 | 仍在 random_15 附近停滞 | 延长/耐心不是充分修复 |
| v18 | 全局推广 random patience | 与 v17 相近 | 说明局部门槛波动并非唯一根因 |
| v19 | random_10 consolidation | 当时记录为较深高水位 | 后续发现“最佳配置”判断受混杂影响 |
| v20 | 降低 balanced-random entropy | 更早退化 | 熵太低可使探索提前收缩 |
| v21 | 拆分 consolidation 的 entropy 变化 | 未突破 | 同种子重复阶段也显示 CUDA/评估噪声 |
| v22 | 缩减单位 roster | 当时表现差，曾被解释为 roster 失败 | 后续 v26 等证明“缩减 roster 必败”是错误结论；v22 还缺 Cleric 并叠加其他变化 |
| v23 | 降低 random_15/20 晋级门 | 仍未解决根因 | 放松门槛只能改变晋级判定，不能创造稳定策略 |

### 这一阶段最重要的方法论结论

当时曾形成三类过早结论：

- 缩减单位集合会灾难性失败；
- random_15 是单纯容量墙；
- 调整 patience/threshold 可能解决。

后续 v24–v27 的配置复现与单变量消融表明，奖励项和版本不一致才是关键混杂。这个案例说明：在没有逐字段配置 diff 之前，不能把“版本号相邻”当作“只有一个变量不同”。

## C.3 v24–v28：复现与奖励项隔离

### v24：看似忠实、实际不忠实的复现

`v24_reproduce_deep_config` 试图复现历史深进度配置，却仍在较早阶段停滞。最初由此怀疑现代引擎或经济变化。

后续调查发现，v24 仍携带三个与真正深配置不同的奖励项：

- `win_speed_bonus`;
- `enemy_neutral_capture`;
- `enemy_owned_capture`.

因此 v24 不是严格的忠实复现。

### v25：random_10 二分诊断

v25 用更窄阶段缩小问题位置。它的价值主要是定位，而不是提供最终训练方案：单阶段探针可以回答“checkpoint 在这个对手上是否仍有能力”，却不能替代完整课程的分布迁移。

### v26：真正对齐奖励后的复现

`v26_faithful_deep_reward_on_head` 在现代代码上把上述三个项归零，并重现更深进度。由此排除“现代引擎必然导致课程失败”这一宽泛解释，确认关键差异可由配置表达。

历史对照的核心关系：

| 配置 | 代码时代 | 三个奖励项 | 历史结果 |
|---|---|---|---|
| v24 | 现代 | 开启/含惩罚 | 较早停滞 |
| v26 | 现代 | 全部归零 | 清过对应课程块 |

### v27a/b/c：单项回加

| 版本 | 仅回加的项 | 历史结果 | 因果判断 |
|---|---|---|---|
| v27a | `win_speed_bonus: 50` | 停滞，峰值约 0.80 | 独立有害证据 |
| v27b | `enemy_neutral_capture: -8` | 5/5 清除，约 0.9875 | 在该条件下相对无害 |
| v27c | `enemy_owned_capture: -15` | 停滞，峰值约 0.90 | 独立有害证据 |

这组消融比“v24 对 v26”更强，因为每次只回加一个候选项。结果还说明，有害项不一定使胜率归零；它们可能让策略偶尔越过门槛，却不能维持 patience 所需的连续评估。

### v28：生产奖励修正版

v28 把 v26/v27 的结论合入较完整课程，并改进阶段 handoff。它成为后续多项实验的基线之一。其深度不应被简化为“奖励已经全部解决”，因为 random_15 的策略漂移、评估噪声和后续阶段仍存在。

## C.4 v29–v32：时间上限、warm start 与晋级噪声

| 版本 | 变更 | 历史观察 | 结论 |
|---|---|---|---|
| v29 | random_15 的 `max_turns` 探针 | 从更长前缀进入仍可停滞 | 仅增加游戏回合上限不是充分条件 |
| v30 | 从 random_10 峰值 checkpoint 单阶段 warm start | 能清 random_15 | checkpoint 质量与交接点重要；不是“给同一 stage 更多任意训练” |
| v31 | 加 `min_timesteps_before_promotion=500k` | 比 v28 更早停在 random_10 | 强制等待可错过暂时但真实的可晋级窗口 |
| v32 | 去掉强制门，random_15 评估局数 80→160 | 目标是降低门判噪声 | 更多评估降低方差，但不修复策略本身 |

v31 的具体历史轨迹中，350k 与 400k 的评估曾达到约 0.925 和 0.8375，却因最小步数门不能晋级，之后能力下降。这说明“训练更久”不是单调改进；on-policy 策略会继续漂移。

v30 与 v31 不矛盾：前者从特定峰值 checkpoint 开始单阶段训练，后者改变完整课程中的晋级时机。实验问题不同。

## C.5 v33：BC warm start

v33 使用规则示范训练 BC 初始策略，再进入 PPO。历史上它帮助跨过 random_15 墙，并暴露新的问题：

- 示范动作类别严重不均衡；
- `end_turn` 在每回合只出现一次，非结束动作很多；
- 未加权交叉熵会形成“永不结束回合”倾向；
- BC checkpoint 与下游 PPO 的 observation/action space、extractor、net architecture 必须精确匹配。

已落地机制包括结束回合样本权重、按下游配置构造同结构模型和 BC→PPO 加载检查。BC 解决的是探索与初始技能，不自动解决后续奖励吸引子。

## C.6 v34–v40：单一单位构成吸引子

### v34：深进度不等于策略多样

v34 开启更积极的战斗塑形，历史上清过多个阶段，但单位构成几乎完全是 Warrior。这证明：

- 课程深度和胜率不能充分描述策略；
- shaped reward 可以加速已有行为，却不一定创造多样战略；
- 应记录 `units_built` 和构成比例。

### v35–v37：四类杠杆

| 版本 | 主要杠杆 | 历史结果摘要 |
|---|---|---|
| v35 | Warrior 攻防削弱，加入 intermediate r10/r15，放宽回合 | 在 beginner r10 附近漂移 |
| v36 | v35 + r10 预算 1.5M→3M | 仍不能证明构成问题解决 |
| v37a | 撤销削弱 + MixedBot 桥接 | 能通过桥接，构成仍可能单一 |
| v37b | 撤销削弱 + 更高门槛 | 清 15 个阶段且每段曾达 100%，仍为单一 Warrior |

v37b 是关键反例：更高晋级门和更深课程没有自动产生单位多样性。

### v38 与 v39：结构削弱和成本削弱

- v38 把 Warrior 攻击、防御、HP 一起降低；
- v39 保留战斗数值，只把成本 200 提到 300。

两者都在紧时钟 starter 地图遇到新墙。它说明平衡改动会改变学习可达性，尤其在地图时间预算很短时。不能只根据目标构成判断 nerf 是否合理。

### v40：跳过 starter

v40 从 beginner 开始课程，使成本 nerf 有足够经济与时间空间发挥。它把“学习通用能力”和“在极短 starter 时钟下适应成本变化”分开。

开放问题是：跳过 starter 后的模型是否仍在 starter 上可靠。课程不训练某分布，就不能假定泛化。

## C.7 v41–v46：击杀刷分、和局与对手多样性

### v41：kill-farm draw plateau

v41 在 r10 使用多项稳定杠杆，较快清除部分阶段，却在 r15 形成高战斗、低终结的和局平台。历史行为证据表现为：

- 能击杀、能获得战斗塑形；
- 夺取比例低；
- 大量对局到达回合或微动作上限；
- episode reward 与胜率脱钩。

这比“容量不足”更符合奖励吸引子。

### v42：去掉战斗刷分

v42 仅把 `damage_scale` 与 `kill` 归零。方向上减少了击杀刷分，却仍停在相近墙，并出现训练更稀疏、廉价支持单位偏好等新表现。

因而“加战斗奖励”和“完全去掉战斗奖励”都不是完整解。需要考虑对称代价、终局、占领可达性和对手分布。

### v43a/b：对手多样性与容量配对

| 版本 | 变更 | 历史峰值/阶段 | 解释 |
|---|---|---|---|
| v43a | Mixed 对手多样性，网络 [256,256] | r15 峰值约 0.8375，较深 |
| v43b | v43a + [512,512] | 反而早一阶段停 | 容量不是当时主要瓶颈 |

v43a 能通过更难的 mixed r10，支持“对手多样性减轻策略漂移”。但它仍没有单独消除可获利和局。

### v44–v46

- v44 调整 HQ 收入，考察经济肉墙与治疗循环；
- v45 调整 r15 entropy floor，考察探索收缩；
- v46 去掉 unit-difference 奖励，考察屯兵与单位数塑形。

这些版本继续从经济、探索和奖励三条轴隔离问题。它们必须结合各自配置 diff 与 run 结果阅读，不能把后续版本号视为单调改进。

## C.8 v48–v54：动作空间、对称战斗、截断与可占结构

仓库没有 v47 配置。版本号缺口不是文档错误；实验索引应忠实保留。

| 版本 | 主要实验轴 | 需要回答的问题 |
|---|---|---|
| v48 | MultiDiscrete + opponent diversity | flat 路径容量/截断是否是主因 |
| v49 | 对称战斗代价、负和局、强化 HQ 胜利 | 让受伤也付代价、和局不再是安全港后是否终结 |
| v50 | HP-scaled damage model | 机制层伤害与奖励尺度是否更一致 |
| v51 | 预算、entropy floor、patience | 在新奖励下是否需要更稳阶段节奏 |
| v52a | 按 `max_turns` 缩放 draw | 不同地图时间上限下和局惩罚是否可比 |
| v52b | v52a + 更高 `max_flat_actions` | flat 合法动作容量是否截断 |
| v53 | 可占结构相关变化 | 夺取瓶颈是“不能夺”还是“不愿夺” |
| v53b | v53 + HQ income | HQ 经济是否造成防守/恢复吸引子 |
| v53c | entropy stability | 全局熵设置是否造成 100% 和局平台 |
| v54 | 放宽微动作上限与前沿配置 | `max_steps` 是否提前截断深局，同时检查关闭 guard 的风险 |

### v49 的奖励几何

历史配置的核心意图：

- `win_by_hq_capture` 提高；
- draw 改为明显负值；
- `unit_diff` 归零；
- 增加承受伤害的对称代价；
- 提高 HQ capture 的即时价值。

这不是简单“奖励更大”，而是试图让战斗奖励接近净交换，并让结束游戏优于持续安全刷分。

### v52a 与 v52b

v52a 针对不同阶段 `max_turns` 缩放和局惩罚。v52b 在此基础上提高 flat 动作容量，用于排除大军队局面的合法动作截断。若 `max_legal_actions` 接近上限，只有提高容量后仍观察相同瓶颈，才能较有力排除截断。

### v53 系列

该系列把注意力从“策略为什么不选 seize”推进到：

- 当前决策点是否真的出现 seize；
- 哪类结构可占；
- HQ 收入和恢复是否让对手形成肉墙；
- entropy 是否使策略永远保持过度随机。

这也是当前 `evaluate_model` 保留 `seize_available_rate`、`captures_by_type`、治疗经济与军队/金币指标的背景。

### v54

v54 提高 `max_steps`，给长对局更多微动作空间。2026-07-24 审查提醒：提高上限只减少“被提前截断”，也可能关闭防止“永不结束回合”策略无限拖延的护栏。必须同时看：

- `max_steps_truncate` 比例；
- `max_turns_draw`；
- 每回合微动作数；
- end-turn 频率；
- 终局类型。

## C.9 2026-07-12 训练审查

该次审查集中于“为什么 Bootstrap run 不能稳定清课”。主要历史发现：

1. 默认 `bootstrap.yaml` 与深 run 的奖励修正不完全一致；
2. 多个深 run 在仍晋级时因外部停止结束，不能简单写成算法停滞；
3. 高正回报可与 100% 和局并存；
4. Mixed 对手、多样性、负和局和 entropy floor 是相关杠杆；
5. 许多结论基于单种子，证据强度不足；
6. 需要把奖励、终止、动作空间和观察尺度的最终解析值落盘。

这次审查的重要贡献不是提出一个万能新配置，而是把“训练停滞”拆成外部终止、评估噪声、奖励吸引子和配置漂移。

## C.10 2026-07-24 全管线审查

第二次审查扩展到 RL pipeline：

- self-play RNG 与对手推理热路径；
- flatten 与空间 extractor；
- `lr_schedule` 等配置字段是否真正传到 SB3；
- 最大合法动作数与 flat 容量；
- reward 默认值与实验最佳值漂移；
- auto-heal、收入、军队规模等诊断；
- 50/56 run 使用同一种子，无法支持强泛化结论；
- 历史 run 与当前代码的比较边界。

审查还强调：修复观察、动作或奖励语义后，修复前后的数字不再严格可比。此时应重跑一个明确基线，而不是把旧曲线继续拼在新曲线上。

## C.11 跨版本因果链

### 奖励吸引子链

```text
终局回报稀疏
  -> 加入战斗/单位/占领塑形
  -> 早期学习变快
  -> 策略发现可重复获得塑形但不终局
  -> 高 reward + 高和局
  -> 对称代价、负和局、HQ 目标与行为诊断
```

### 课程交接链

```text
短评估偶然越门
  -> checkpoint 交到更难阶段
  -> 能力漂移或崩溃
  -> patience / 最小步数 / 更多评估
  -> 发现强制训练也会错过能力峰值
  -> 保留 best、固定锚与交接审计
```

### 单位构成链

```text
便宜单位在多个轴占优
  -> PPO 收敛到单一单位
  -> 课程胜率仍很高
  -> 战斗塑形进一步强化
  -> 统计 units_built 暴露问题
  -> 成本/属性/地图时钟消融
```

### 对手分布链

```text
固定对手轨迹窄
  -> 策略学会特定节奏
  -> 切换阶段时分布跃迁
  -> MixedBot / 历史池
  -> 提高多样性但引入非平稳
  -> 固定锚点评估
```

## C.12 当前应如何复现历史结论

推荐顺序：

1. 固定当前代码 revision；
2. 选择一个结论，不一次复现全部 v15–v54；
3. 找到最小成对配置；
4. 用配置 diff 确认只有目标变量不同；
5. 至少 3–5 个种子；
6. 使用独立固定评估集；
7. 保存 resolved config；
8. 报告胜/和/负、终局、奖励与行为；
9. 将结果写为“当前复现”并与“历史记录”分栏；
10. 若不能复现，先检查版本、默认值与数据管线，不直接判定旧记录错误。

## C.13 版本总索引

```text
v15  lower_entropy_floors
v16  turn_penalty
v17  random_patience
v18  random_patience_global
v19  consolidate_random10
v20  lower_balanced_random_entropy
v21  split_consolidate
v22  reduced_units
v23  lower_random_threshold
v24  reproduce_deep_config
v25  bisect_random10_repro
v26  faithful_deep_reward_on_head
v27a ablate_win_speed_bonus
v27b ablate_enemy_neutral_capture
v27c ablate_enemy_owned_capture
v28  production_reward_fixed
v29  random15_maxturns_probe
v30  random15_warmstart_probe
v31  production_minsteps_gate
v32  drop_gate_higher_eval
v33  production_bc_warmstart
v34  aggressive_combat
v35  warrior_nerf
v36  warrior_nerf_more_budget
v37a revert_nerf_mixed_bridge
v37b revert_nerf_higher_thresholds
v38  structural_warrior_nerf
v39  cost_only_nerf
v40  skip_starter
v41  r10_stability
v42  remove_combat_farm
v43a opponent_diversity
v43b opponent_diversity_capacity
v44  opp_diversity_hq_income_cut
v45  opp_diversity_r15_entropy_floor
v46  opp_diversity_no_unit_diff
v47  仓库无对应配置
v48  multidiscrete_opp_diversity
v49  symmetric_combat_negative_draw
v50  hp_scaled_damage
v51  budget_floor_patience2
v52a maxturn_scaled_draw
v52b maxturn_scaled_draw_plus_maxflat
v53  capturable_structures
v53b capturable_structures_hq_income
v53c entropy_stability
v54  uncapped_frontier
```

