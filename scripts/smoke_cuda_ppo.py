"""Quick CUDA + MaskablePPO smoke test."""
import torch
from sb3_contrib import MaskablePPO

from reinforcetactics.rl.masking import make_maskable_env

print("cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
env = make_maskable_env(
    map_file="maps/1v1/beginner.csv",
    opponent="bot",
    max_steps=200,
    action_space_type="flat_discrete",
    render_mode=None,
)
model = MaskablePPO(
    "MultiInputPolicy",
    env,
    n_steps=64,
    batch_size=32,
    n_epochs=1,
    device="cuda",
    verbose=0,
)
model.learn(total_timesteps=128)
print("device", model.device)
print("policy_device", next(model.policy.parameters()).device)
print("smoke_ok")
env.close()
