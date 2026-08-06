"""Evaluate a trained MaskablePPO checkpoint vs rule-based bot (win rate)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sb3_contrib import MaskablePPO

from reinforcetactics.rl.evaluation import evaluate_model
from reinforcetactics.rl.masking import make_maskable_env


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="Path to .zip model")
    p.add_argument("--episodes", type=int, default=50)
    p.add_argument("--map-file", default="maps/1v1/beginner.csv")
    p.add_argument("--opponent", default="bot")
    p.add_argument("--device", default="cuda")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default=None, help="Optional JSON results path")
    args = p.parse_args()

    model_path = Path(args.model)
    print(f"Loading {model_path} on {args.device}...")
    model = MaskablePPO.load(str(model_path), device=args.device)

    env = make_maskable_env(
        map_file=args.map_file,
        opponent=args.opponent,
        max_steps=500,
        max_turns=60,
        action_space_type="flat_discrete",
        max_flat_actions=512,
        max_actions_per_turn=40,
        render_mode=None,
    )

    print(f"Evaluating {args.episodes} episodes vs opponent={args.opponent} on {args.map_file}")
    results = evaluate_model(
        model,
        env,
        n_episodes=args.episodes,
        deterministic=True,
        seed=args.seed,
        track_breakdown=True,
    )
    env.close()

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    for k in (
        "n_episodes",
        "win_rate",
        "wins",
        "losses",
        "draws",
        "mean_reward",
        "std_reward",
        "mean_length",
        "mean_invalid",
    ):
        if k in results:
            v = results[k]
            if k == "win_rate":
                print(f"{k:16s}: {v:.1%} ({results.get('wins', '?')}/{results.get('n_episodes', '?')})")
            elif isinstance(v, float):
                print(f"{k:16s}: {v:.3f}")
            else:
                print(f"{k:16s}: {v}")

    if "end_reason_counts" in results:
        print("end_reasons     :", results["end_reason_counts"])
    if "action_type_counts" in results:
        print("action_types    :", results["action_type_counts"])

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        serializable = {k: (float(v) if hasattr(v, "item") else v) for k, v in results.items()}
        # numpy types / nested
        def _clean(obj):
            if isinstance(obj, dict):
                return {str(k): _clean(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_clean(x) for x in obj]
            if hasattr(obj, "item"):
                return obj.item()
            if isinstance(obj, (int, float, str, bool)) or obj is None:
                return obj
            return str(obj)

        out.write_text(json.dumps(_clean(serializable), indent=2), encoding="utf-8")
        print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
