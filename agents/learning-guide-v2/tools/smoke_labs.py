"""Run short, CPU-only integration probes used by the guide.

This script is deliberately small. It checks interfaces and data flow; it does
not claim that an agent has learned a competitive strategy.
"""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any

import gymnasium
import numpy as np
import sb3_contrib
import stable_baselines3
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3 import A2C, DQN, PPO

from reinforcetactics.rl.alphazero_net import AlphaZeroNet
from reinforcetactics.rl.gym_env import StrategyGameEnv
from reinforcetactics.rl.masking import make_maskable_env
from reinforcetactics.rl.mcts import MCTS
from reinforcetactics.rl.self_play import OpponentPool, make_self_play_env


ROOT = Path(__file__).resolve().parents[1]


def action_space_probe() -> dict[str, Any]:
    result: dict[str, Any] = {}
    algorithms = (PPO, A2C, DQN, MaskablePPO)
    for mode in ("multi_discrete", "flat_discrete"):
        env = StrategyGameEnv(
            map_file="maps/1v1/starter.csv",
            opponent="noop",
            max_steps=16,
            action_space_type=mode,
        )
        mode_result: dict[str, str] = {"space": str(env.action_space)}
        for algorithm in algorithms:
            try:
                if algorithm is DQN:
                    kwargs = {"buffer_size": 32, "learning_starts": 1, "batch_size": 4}
                elif algorithm is A2C:
                    kwargs = {"n_steps": 8}
                else:
                    kwargs = {"n_steps": 8, "batch_size": 8}
                algorithm("MultiInputPolicy", env, verbose=0, device="cpu", **kwargs)
                mode_result[algorithm.__name__] = "construct_ok"
            except Exception as exc:
                mode_result[algorithm.__name__] = f"{type(exc).__name__}: {exc}"
        result[mode] = mode_result
        env.close()
    return result


def mask_probe() -> dict[str, Any]:
    env = StrategyGameEnv(
        map_file="maps/1v1/beginner.csv",
        opponent="noop",
        action_space_type="multi_discrete",
        max_steps=16,
    )
    env.reset(seed=42)
    masks = env.action_masks()
    product = int(np.prod([np.count_nonzero(mask) for mask in masks]))
    legal_actions = env.game_state.get_legal_actions(player=env.agent_player)
    legal = int(
        sum(
            len(actions) if isinstance(actions, list) else int(bool(actions))
            for actions in legal_actions.values()
        )
    )
    env.close()
    return {
        "per_dimension_true_counts": [int(np.count_nonzero(mask)) for mask in masks],
        "mask_cross_product": product,
        "domain_legal_actions": legal,
        "overapproximation_ratio": product / max(legal, 1),
    }


def maskable_ppo_probe() -> dict[str, Any]:
    env = make_maskable_env(
        map_file="maps/1v1/starter.csv",
        opponent="noop",
        action_space_type="flat_discrete",
        max_steps=32,
        max_flat_actions=128,
    )
    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        n_steps=32,
        batch_size=32,
        n_epochs=1,
        learning_rate=3e-4,
        device="cpu",
        seed=42,
        verbose=0,
    )
    model.learn(total_timesteps=64)
    obs, _ = env.reset(seed=43)
    action, _ = model.predict(obs, action_masks=env.action_masks(), deterministic=True)
    _, reward, terminated, truncated, info = env.step(action)
    env.close()
    return {
        "timesteps": 64,
        "predicted_action": int(np.asarray(action).item()),
        "step_reward": float(reward),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "end_reason": info.get("end_reason"),
    }


def mcts_probe() -> dict[str, Any]:
    env = StrategyGameEnv(map_file="maps/1v1/starter.csv", opponent=None, max_steps=16)
    obs, _ = env.reset(seed=7)
    net = AlphaZeroNet(
        grid_height=env.grid_height,
        grid_width=env.grid_width,
        num_action_types=10,
        num_res_blocks=1,
        channels=16,
    )
    net.eval()
    search = MCTS(
        net,
        grid_width=env.grid_width,
        grid_height=env.grid_height,
        num_simulations=2,
        c_puct=1.5,
        device="cpu",
    )
    probabilities, root_value = search.search(env.game_state, add_noise=False)
    env.close()
    return {
        "simulations": 2,
        "policy_entries": int(len(probabilities)),
        "probability_sum": float(probabilities.sum()),
        "nonzero_actions": int(np.count_nonzero(probabilities)),
        "root_value": float(root_value),
        "observation_keys": list(obs),
    }


def self_play_probe() -> dict[str, Any]:
    pool = OpponentPool(max_size=2, selection_strategy="recent")
    for index in range(3):
        pool.models.append({"snapshot": np.asarray([index], dtype=np.float32)})
        pool.metadata.append({"timestep": index * 10, "win_rate": 0.5, "index": index})
    pool._update_selection_weights()

    env = make_self_play_env(
        max_steps=16,
        swap_players=False,
        opponent_pool=pool,
    )
    obs, info = env.reset(seed=11)
    masks = env.action_masks()
    result = env.step(np.asarray([5, 0, 0, 0, 0, 0], dtype=np.int64))
    env.close()
    return {
        "pool_size_after_overflow": pool.size,
        "selection_weights": [float(value) for value in pool._selection_weights],
        "observation_keys": list(obs),
        "mask_dimensions": len(masks),
        "step_tuple_length": len(result),
        "reset_info_type": type(info).__name__,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        choices=("env", "actions", "masks", "maskable-ppo", "self-play", "mcts"),
        default=None,
        help="Run one named probe instead of the complete suite",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "assets" / "data" / "smoke-results.json",
        help="JSON output path",
    )
    args = parser.parse_args()
    probes = {
        "actions": ("action_space_compatibility", action_space_probe),
        "masks": ("mask_probe", mask_probe),
        "maskable-ppo": ("maskable_ppo_probe", maskable_ppo_probe),
        "self-play": ("self_play_probe", self_play_probe),
        "mcts": ("mcts_probe", mcts_probe),
    }
    environment = {
        "python": platform.python_version(),
        "gymnasium": gymnasium.__version__,
        "stable_baselines3": stable_baselines3.__version__,
        "sb3_contrib": sb3_contrib.__version__,
        "torch": torch.__version__,
        "device": "cpu",
    }
    results: dict[str, Any] = {"environment": environment}
    if args.only and args.only != "env":
        result_name, probe = probes[args.only]
        results[result_name] = probe()
    elif args.only is None:
        for result_name, probe in probes.values():
            results[result_name] = probe()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
