import argparse, sys, os
from types import SimpleNamespace
import federated_survival

# Manual configuration for a "Showcase" audit
args = SimpleNamespace(
    dataset="support2",
    rounds=2,
    epochs=1,
    sample_size=1000,
    batch_size=32,
    lr=0.001,
    task_id=0,
    experiment="audit_showcase",
    enable_blockchain=True,
    sigma=0.0,
    enable_dp=False,
    enable_secagg=False
)

config = federated_survival.DATASET_PRESETS["support2"].copy()
config["attack_type"] = "gradient_scale"
config["defense_name"] = "Robust-MAD"
config["display_name"] = "Byzantine Audit Demo"

print(f"[Quick Audit] Starting targeted simulation...")
print(f"[Quick Audit] Attack: {config['attack_type']}, Defense: {config['defense_name']}")
federated_survival.run_simulation(args, config)
