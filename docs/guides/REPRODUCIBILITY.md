# MedShare Reproducibility Guide

This guide ensures that all stress tests and scientific experiments in the MedShare project can be reproduced with 100% accuracy on local hardware (Windows/Linux/Mac) or Google Colab.

## ⚙️ 1. Environment Requirements
- **Hardware**: Minimum 4GB RAM. NVIDIA GPU (6GB+ VRAM) recommended for acceleration.
- **Python**: 3.9 - 3.11
- **Blockchain**: Ganache (CLI or Desktop)
- **Key Libraries**: `flwr`, `torch`, `opacus`, `web3`, `pandas`, `scikit-learn`

## 🚀 2. Ground-Up Execution Steps

### Step A: Initialize the Blockchain
Start a deterministic local blockchain with sufficient gas for federated rounds.
```bash
npx ganache --wallet.seed federated --port 8545 --gasLimit 10000000
```

### Step B: Compile & Deploy Smart Contracts
Ensure your smart contracts are ready to manage hospital reputations and model hashes.
```bash
# Compile (if needed)
npx hardhat compile

# Deploy to local Ganache
python scripts/deploy_colab.py
```

### Step C: Run Scientific Sweeps
The system uses adaptive configuration. You can run individual experiments or full sweeps.

**Option 1: Full Comprehensive Sweep (Recommended)**
```bash
# Replace 'maternal_health' with 'support2', 'stroke_prediction', etc.
python federated_survival.py --experiment robustness --dataset maternal_health
python federated_survival.py --experiment latency --dataset maternal_health
python federated_survival.py --experiment gas --dataset maternal_health
python federated_survival.py --experiment dp --dataset maternal_health
python federated_survival.py --experiment mi --dataset maternal_health
```

**Option 2: Targeted Experiment**
```bash
# Run a specific security audit
python federated_survival.py --experiment mi --dataset maternal_health --rounds 10 --epochs 25
```

## 📈 3. Generating Visualizations
Once the CSV logs are generated in the `test/` directory, run the plotting engine:
```bash
python test/plot_results.py
```
This will produce:
- `fig_robustness.png`
- `fig_latency.png`
- `fig_gas_costs.png`
- `fig_dp_tradeoff.png`
- `fig_mi.png`

## 🧪 4. Optimized Hyperparameters (Verified)
For maximum stability on small-to-medium datasets (e.g., Maternal Health, SUPPORT2), use these settings:

| Setting | Value | Why? |
| :--- | :--- | :--- |
| **Local Epochs** | 10 (DP) / 25 (MI) | Allows model to recover from privacy noise. |
| **GPU Parallelism** | 2 Workers (Local 6GB) / 5 Workers (Colab) | Calibrated for VRAM stability vs. Cloud Speed. |
| **DP LR Decay** | 0.25 (75% reduction) | Keeps the Adam optimizer stable under noise. |
| **Batch Size** | 2048 (Local GPU) / 8192 (Colab) | Optimized for environment-aware throughput. |
| **Caching** | Enabled (.json) | Skips redundant SMOTE and baseline training. |

## 📁 5. Archiving Results
To save current results before testing a new dataset:
```bash
mkdir -p docs/assets/[dataset_name]
cp test/*.png docs/assets/[dataset_name]/
cp test/*.csv docs/assets/[dataset_name]/
cp test/*.json docs/assets/[dataset_name]/
```

---
**Audit Note**: This reproducibility path was manually verified on 2026-02-15 on local NVIDIA hardware.
