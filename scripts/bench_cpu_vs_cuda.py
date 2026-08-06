"""Fair short-run benchmark: MaskablePPO on CPU vs CUDA.

Runs the same env/model hyperparams for a fixed number of timesteps on each
device and reports wall-clock time + SB3-reported FPS.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from sb3_contrib import MaskablePPO

from reinforcetactics.rl.masking import make_maskable_vec_env


def run_once(
    device: str,
    timesteps: int,
    n_envs: int,
    n_steps: int,
    batch_size: int,
    map_file: str,
    seed: int,
) -> dict:
    print(f"\n{'=' * 60}")
    print(f"Benchmark device={device}  timesteps={timesteps}  n_envs={n_envs}")
    print(f"{'=' * 60}")

    env = make_maskable_vec_env(
        n_envs=n_envs,
        seed=seed,
        use_subprocess=(n_envs > 1),
        map_file=map_file,
        opponent="random",
        max_steps=500,
        max_turns=40,
        action_space_type="flat_discrete",
        max_flat_actions=512,
        max_actions_per_turn=40,
    )

    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        learning_rate=3e-4,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.05,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs={"net_arch": {"pi": [256, 256], "vf": [256, 256]}},
        device=device,
        verbose=1,
        seed=seed,
    )

    # Warmup one tiny learn to pay subprocess / CUDA init costs separately if desired
    t0 = time.perf_counter()
    model.learn(total_timesteps=timesteps, progress_bar=False)
    wall = time.perf_counter() - t0

    # SB3 stores num_timesteps after learn
    fps = timesteps / wall if wall > 0 else 0.0
    param_device = str(next(model.policy.parameters()).device)

    result = {
        "device_arg": device,
        "param_device": param_device,
        "timesteps": timesteps,
        "n_envs": n_envs,
        "n_steps": n_steps,
        "batch_size": batch_size,
        "map_file": map_file,
        "wall_seconds": round(wall, 3),
        "fps_wall": round(fps, 1),
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }

    env.close()
    del model
    if device.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.empty_cache()

    print(f"\n→ wall={wall:.2f}s  fps={fps:.1f}  params_on={param_device}")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--timesteps", type=int, default=65536, help="Env steps per device run")
    p.add_argument("--n-envs", type=int, default=8)
    p.add_argument("--n-steps", type=int, default=2048)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--map-file", default="maps/1v1/starter.csv")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--devices", default="cuda,cpu", help="Comma-separated: cuda,cpu")
    p.add_argument("--out", default="benchmarks/cpu_vs_cuda/bench_result.json")
    args = p.parse_args()

    devices = [d.strip() for d in args.devices.split(",") if d.strip()]
    results = []
    for d in devices:
        if d.startswith("cuda") and not torch.cuda.is_available():
            print(f"Skip {d}: CUDA not available")
            continue
        results.append(
            run_once(
                device=d,
                timesteps=args.timesteps,
                n_envs=args.n_envs,
                n_steps=args.n_steps,
                batch_size=args.batch_size,
                map_file=args.map_file,
                seed=args.seed,
            )
        )

    # Summary
    summary: dict = {"runs": results}
    by = {r["device_arg"]: r for r in results}
    if "cpu" in by and "cuda" in by:
        cpu, gpu = by["cpu"], by["cuda"]
        speedup = cpu["wall_seconds"] / gpu["wall_seconds"] if gpu["wall_seconds"] > 0 else None
        summary["comparison"] = {
            "cpu_wall_s": cpu["wall_seconds"],
            "cuda_wall_s": gpu["wall_seconds"],
            "cpu_fps": cpu["fps_wall"],
            "cuda_fps": gpu["fps_wall"],
            "speedup_cuda_over_cpu": round(speedup, 3) if speedup else None,
            "note": (
                "For this game env, rollouts are CPU-heavy; GPU mainly accelerates "
                "the PPO network update. Speedup is often modest unless batch is large."
            ),
        }
        print("\n" + "=" * 60)
        print("COMPARISON")
        print("=" * 60)
        print(f"CPU : {cpu['wall_seconds']:.2f}s  ({cpu['fps_wall']:.0f} FPS)")
        print(f"CUDA: {gpu['wall_seconds']:.2f}s  ({gpu['fps_wall']:.0f} FPS)")
        if speedup:
            print(f"CUDA speedup: {speedup:.2f}x  (higher is better for GPU)")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
