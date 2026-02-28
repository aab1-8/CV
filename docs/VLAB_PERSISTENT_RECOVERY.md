# vLab Persistent Recovery & Environment Guide

This guide provides the "Zero-Intervention" setup to restore the research environment on vLab after a system reset or IP change. It leverages the persistent `/jupyter/work/bxp267` storage to avoid re-installing dependencies.

## 1. The "One-Click" Recovery Script
Copy and paste this entire block into your vLab terminal following any reset:

```bash
# A. Restore Environment Paths
export PATH=/jupyter/work/bxp267/node-v14.21.3-linux-x64/bin:$PATH
cd /jupyter/work/bxp267
source venv/bin/activate

# B. Start the Audit Blockchain (Ganache)
# Port 8546 is reserved for the MedShare Audit
ganache --port 8546 --mnemonic "exit taxi picnic regret brush gold vacant dignity book enable left divorce" > ganache.log 2>&1 &

# C. Deploy Audit Contracts
# Wait 2 seconds for Ganache to warm up
sleep 2 && python scripts/deploy_colab.py
```

## 2. Environment Verification (Scientific Audit)
To prove the environment is research-ready, run this check:
```bash
echo "--- ENVIRONMENT AUDIT ---"
node -v | xargs echo "Node (Glibc-safe):"
pip list | grep -E "torch|flwr|opacus|web3|ray|imbalanced-learn"
nvidia-smi | grep -E "Tesla T4|Driver Version"
```

## 3. Persistent File Locations
To survive vLab host resets, all critical binaries are stored in the work directory:
*   **Runtime**: `/jupyter/work/bxp267/venv` (Python Virtual Env)
*   **Node.js**: `/jupyter/work/bxp267/node-v14.21.3-linux-x64` (Portable Binary)
*   **Audit Chain**: Ganache is installed globally in the persistent Node folder.

## 4. Master Audit Command (253,680 Records)
Once recovery is complete, launch the final security audit:
```bash
nohup python federated_survival.py \
    --dataset cdc_diabetes_012 \
    --experiment robustness \
    --rounds 30 \
    --epochs 20 \
    --sample_size 253680 \
    --enable_blockchain True \
    --enable_dp True \
    > master_audit_security.log 2>&1 &
```

## 5. Summary of Permanent Fixes
| Feature | Strategy | Benefit |
| :--- | :--- | :--- |
| **Glibc Conflict** | Portable Node v14 | Bypass OS library limitations. |
| **Session Reset** | Persistent Storage | Move Node/Ganache into the project folder. |
| **GPU OOM** | Batch Size 2048 | Optimized for 15GB Tesla T4 VRAM. |
| **Data Loss** | Background (`nohup`) | Ensures completion across network drops. |
