"""Generate original diagrams and charts used by the learning guide."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "figures"
BLUE = "#1f5d8f"
LIGHT = "#eaf3f9"
INK = "#172033"
ORANGE = "#d97706"
GREEN = "#1f8a70"
RED = "#c2413b"


def setup() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.dpi": 160,
            "savefig.dpi": 180,
            "axes.edgecolor": "#94a3b8",
            "axes.labelcolor": INK,
            "text.color": INK,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def box(ax, xy, width, height, text, color=LIGHT, edge=BLUE, size=11):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.03,rounding_size=0.04",
        linewidth=1.5,
        edgecolor=edge,
        facecolor=color,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text, ha="center", va="center", fontsize=size)
    return patch


def arrow(ax, start, end, text=""):
    patch = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15, linewidth=1.4, color=BLUE)
    ax.add_patch(patch)
    if text:
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.04, text, ha="center", fontsize=9)


def diagram(name: str, title: str, nodes: list[tuple[float, float, float, float, str]], edges: list[tuple]) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", pad=12)
    for x, y, w, h, text in nodes:
        box(ax, (x, y), w, h, text)
    for start, end, *label in edges:
        arrow(ax, start, end, label[0] if label else "")
    save(fig, name)


def agent_environment_loop() -> None:
    diagram(
        "agent-environment-loop.png",
        "强化学习的闭环",
        [(0.8, 1.8, 2.4, 1.1, "智能体\n策略 π(a|o)"), (6.8, 1.8, 2.4, 1.1, "环境\n游戏规则 + 对手")],
        [
            ((3.2, 2.55), (6.8, 2.55), "动作 a_t"),
            ((6.8, 2.05), (3.2, 2.05), "观察 o_(t+1)、奖励 r_(t+1)"),
        ],
    )


def project_dataflow() -> None:
    diagram(
        "project-dataflow.png",
        "从训练算法到游戏状态的数据流",
        [
            (0.2, 2.0, 1.6, 0.9, "PPO / A2C\nDQN / Feudal"),
            (2.3, 2.0, 1.6, 0.9, "SB3 / 自研\n训练循环"),
            (4.4, 2.0, 1.7, 0.9, "StrategyGameEnv\nreset / step"),
            (6.7, 2.0, 1.3, 0.9, "GameState\n规则真源"),
            (8.5, 2.0, 1.3, 0.9, "Bot\n对手回合"),
        ],
        [
            ((1.8, 2.45), (2.3, 2.45)),
            ((3.9, 2.45), (4.4, 2.45)),
            ((6.1, 2.45), (6.7, 2.45)),
            ((8.0, 2.6), (8.5, 2.6), "对手回合"),
            ((8.5, 2.2), (8.0, 2.2), "局面变化"),
        ],
    )


def actor_critic() -> None:
    diagram(
        "actor-critic.png",
        "Actor-Critic：共享观察、两类输出",
        [
            (0.4, 2.0, 1.5, 0.9, "观察 o_t"),
            (2.6, 2.0, 2.0, 0.9, "特征提取器\nMLP / CNN"),
            (6.1, 3.1, 2.3, 0.9, "Actor\n动作概率 π(a|o)"),
            (6.1, 0.9, 2.3, 0.9, "Critic\n状态价值 V(o)"),
        ],
        [
            ((1.9, 2.45), (2.6, 2.45)),
            ((4.6, 2.55), (6.1, 3.55)),
            ((4.6, 2.35), (6.1, 1.35)),
        ],
    )


def self_play() -> None:
    diagram(
        "self-play-pool.png",
        "带历史快照池的自对弈",
        [
            (0.4, 2.0, 1.8, 0.9, "当前策略 π_t"),
            (3.0, 2.0, 2.2, 0.9, "对手池\nπ_(t-1), π_(t-k), ..."),
            (6.0, 2.0, 1.6, 0.9, "采样对局"),
            (8.2, 2.0, 1.4, 0.9, "PPO 更新"),
        ],
        [
            ((2.2, 2.65), (3.0, 2.65), "定期快照"),
            ((5.2, 2.45), (6.0, 2.45), "采样对手"),
            ((7.6, 2.45), (8.2, 2.45), "轨迹"),
            ((8.9, 2.0), (1.3, 1.2), "得到 π_(t+1)"),
        ],
    )


def feudal() -> None:
    diagram(
        "feudal-architecture.png",
        "Feudal RL 的经理—工人结构",
        [
            (0.3, 2.0, 1.6, 0.9, "观察 o_t"),
            (2.5, 3.2, 2.0, 0.9, "Manager\n目标 g_k"),
            (2.5, 0.8, 2.0, 0.9, "特征提取器"),
            (5.4, 2.0, 2.0, 0.9, "Worker\n动作 a_t | g_k"),
            (8.2, 2.0, 1.4, 0.9, "环境"),
        ],
        [
            ((1.9, 2.55), (2.5, 3.65)),
            ((1.9, 2.25), (2.5, 1.25)),
            ((4.5, 3.55), (5.4, 2.65), "每 H 步"),
            ((4.5, 1.25), (5.4, 2.25)),
            ((7.4, 2.45), (8.2, 2.45)),
        ],
    )


def mcts() -> None:
    diagram(
        "mcts-cycle.png",
        "蒙特卡洛树搜索的一次模拟",
        [
            (0.3, 2.0, 1.5, 0.9, "1 选择\nSelection"),
            (2.6, 2.0, 1.5, 0.9, "2 扩展\nExpansion"),
            (4.9, 2.0, 1.5, 0.9, "3 评估\nEvaluation"),
            (7.2, 2.0, 1.7, 0.9, "4 回传\nBackup"),
        ],
        [
            ((1.8, 2.45), (2.6, 2.45)),
            ((4.1, 2.45), (4.9, 2.45)),
            ((6.4, 2.45), (7.2, 2.45)),
            ((8.05, 2.0), (1.05, 1.15), "重复 N 次"),
        ],
    )


def alphazero() -> None:
    diagram(
        "alphazero-loop.png",
        "AlphaZero 的训练外环",
        [
            (0.2, 2.0, 1.7, 0.9, "当前网络 fθ"),
            (2.5, 2.0, 1.6, 0.9, "MCTS 自对弈"),
            (4.7, 2.0, 1.7, 0.9, "数据 (s, π, z)"),
            (7.0, 2.0, 1.3, 0.9, "联合损失"),
            (8.8, 2.0, 1.0, 0.9, "新网络"),
        ],
        [
            ((1.9, 2.45), (2.5, 2.45)),
            ((4.1, 2.45), (4.7, 2.45)),
            ((6.4, 2.45), (7.0, 2.45)),
            ((8.3, 2.45), (8.8, 2.45)),
            ((9.3, 2.0), (1.05, 1.2), "评估通过后替换"),
        ],
    )


def llm_pipeline() -> None:
    diagram(
        "llm-pipeline.png",
        "LLM Bot 的推理流水线（不是 RL 训练）",
        [
            (0.2, 2.0, 1.5, 0.9, "GameState"),
            (2.2, 2.0, 1.6, 0.9, "序列化 +\n合法动作"),
            (4.5, 2.0, 1.4, 0.9, "Prompt"),
            (6.5, 2.0, 1.2, 0.9, "LLM"),
            (8.3, 2.0, 1.4, 0.9, "解析、校验\n执行"),
        ],
        [
            ((1.7, 2.45), (2.2, 2.45)),
            ((3.8, 2.45), (4.5, 2.45)),
            ((5.9, 2.45), (6.5, 2.45)),
            ((7.7, 2.45), (8.3, 2.45)),
        ],
    )


def discount_chart() -> None:
    steps = np.arange(0, 501)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for gamma, color in [(0.95, RED), (0.99, ORANGE), (0.997, GREEN)]:
        ax.plot(steps, gamma**steps, label=f"γ={gamma}", color=color, linewidth=2)
    ax.axhline(0.5, color="#94a3b8", linestyle="--", linewidth=1)
    ax.set(xlabel="距离当前的环境步数", ylabel="终局奖励在当前的折扣权重", title="折扣因子与有效时间范围")
    ax.legend()
    ax.grid(alpha=0.25)
    save(fig, "discount-horizon.png")


def ppo_clip_chart() -> None:
    ratio = np.linspace(0.4, 1.6, 400)
    eps = 0.2
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharex=True)
    for ax, advantage, title in [(axes[0], 1.0, "优势 A > 0"), (axes[1], -1.0, "优势 A < 0")]:
        unclipped = ratio * advantage
        clipped = np.clip(ratio, 1 - eps, 1 + eps) * advantage
        objective = np.minimum(unclipped, clipped)
        ax.plot(ratio, unclipped, "--", color="#94a3b8", label="未裁剪")
        ax.plot(ratio, objective, color=BLUE, linewidth=2, label="PPO 目标")
        ax.axvspan(1 - eps, 1 + eps, color=LIGHT)
        ax.axvline(1.0, color=INK, linewidth=1)
        ax.set_title(title)
        ax.set_xlabel("新旧策略概率比 r")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("代理目标")
    axes[0].legend()
    save(fig, "ppo-clip.png")


def mask_failure_chart() -> None:
    labels = ["真正合法", "逐维掩码后\n看似合法", "完整组合空间"]
    values = [3, 384, 103680]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(labels, values, color=[GREEN, ORANGE, RED])
    ax.set_yscale("log")
    ax.set_ylabel("动作组合数量（对数坐标）")
    ax.set_title("逐维掩码无法表达字段之间的依赖")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value * 1.18, f"{value:,}", ha="center")
    ax.grid(axis="y", alpha=0.2)
    save(fig, "mask-overapproximation.png")


def benchmark_chart() -> None:
    steps = np.array([10_000, 50_000, 200_000, 1_000_000])
    win_rate = np.array([0, 0, 0, 0])
    reward = np.array([-4965.1, -4965.1, -4978.1, -1066.9])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].plot(steps, win_rate, marker="o", color=RED)
    axes[0].set(xscale="log", ylim=(-2, 100), xlabel="训练步数", ylabel="胜率 (%)", title="历史基准：胜率始终为 0")
    axes[1].plot(steps, reward, marker="o", color=ORANGE)
    axes[1].set(xscale="log", xlabel="训练步数", ylabel="平均回报", title="历史基准：无效动作惩罚主导")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.suptitle("PPO vs SimpleBot（历史数据，6×6 beginner）", fontsize=14, fontweight="bold")
    save(fig, "historical-ppo-mask-failure.png")


def evaluation_ci_chart() -> None:
    p = 0.7
    n = np.arange(10, 501)
    half = 1.96 * np.sqrt(p * (1 - p) / n)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(n, half * 100, color=BLUE, linewidth=2)
    ax.scatter([20, 80, 100, 400], 1.96 * np.sqrt(p * (1 - p) / np.array([20, 80, 100, 400])) * 100, color=ORANGE)
    ax.set(xlabel="评估局数 n", ylabel="95% 正态近似半宽（百分点）", title="评估局数与胜率不确定性（假设真实胜率 70%）")
    ax.grid(alpha=0.25)
    save(fig, "evaluation-confidence.png")


def elo_chart() -> None:
    diff = np.linspace(-600, 600, 400)
    expected = 1 / (1 + 10 ** (-diff / 400))
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(diff, expected, color=BLUE, linewidth=2)
    ax.axhline(0.5, color="#94a3b8", linestyle="--")
    ax.axvline(0, color="#94a3b8", linestyle="--")
    ax.set(xlabel="己方 Elo - 对手 Elo", ylabel="期望得分", title="Elo 分差与期望得分")
    ax.grid(alpha=0.25)
    save(fig, "elo-expectation.png")


def curriculum_chart() -> None:
    stages = ["starter", "beginner", "intermediate", "skirmish", "corner_points"]
    board_area = [20, 36, 49, 64, 120]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(stages, board_area, marker="o", linewidth=2, color=BLUE)
    ax.fill_between(stages, board_area, alpha=0.15, color=BLUE)
    ax.set(ylabel="地图格数", title="课程主线中的空间复杂度增长")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "curriculum-map-growth.png")


def main() -> None:
    setup()
    agent_environment_loop()
    project_dataflow()
    actor_critic()
    self_play()
    feudal()
    mcts()
    alphazero()
    llm_pipeline()
    discount_chart()
    ppo_clip_chart()
    mask_failure_chart()
    benchmark_chart()
    evaluation_ci_chart()
    elo_chart()
    curriculum_chart()
    print(f"Generated figures in {OUT}")


if __name__ == "__main__":
    main()
