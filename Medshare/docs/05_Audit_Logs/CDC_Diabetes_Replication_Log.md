# 📑 Replicating the CDC-Diabetes-012 Privacy Audit
**Release Date:** February 28, 2026  
**Target Dataset:** `cdc_diabetes_012` (253,680 records / 641,109 resampled)  
**Hardware Requirement:** NVIDIA Tesla T4 GPU (or equivalent with >8GB VRAM)

---

## 1. Environment Preparation
Before running the audit, ensure the blockchain engine and contract deployments are active.

### A. Start the Blockchain (Ganache)
Execute this command in a dedicated terminal to host the audit trail:
```bash
# Ensure Node.js v14+ is in your PATH
ganache --port 8546 --mnemonic "exit taxi picnic regret brush gold vacant dignity book enable left divorce" --accounts 10
```

### B. Deploy Audit Contracts
In a second terminal, deploy the `MedShareTask`, `CommitmentRegistry`, and `Reputation` contracts:
```bash
python scripts/deploy_colab.py
```

---

## 2. Definitive Audit Commands
Executing the following commands in sequence replicates the four critical research phases.

### Phase 1: Adversarial Robustness Sweep
Evaluates the `Robust-MAD` defense against label-flipping and gradient-scaling attacks.
```bash
python federated_survival.py --dataset cdc_diabetes_012 --experiment robustness --rounds 30 --epochs 20 --enable_blockchain True --enable_dp False
```

### Phase 2: Privacy-Utility Tradeoff (DP Sweep)
Generates the Accuracy vs. Noise ($\sigma$) curve.
```bash
python federated_survival.py --dataset cdc_diabetes_012 --experiment dp --rounds 30 --epochs 20 --enable_blockchain True --enable_dp True
```

### Phase 3: Membership Inference (MI) Privacy Audit
The flagship "Stress Test" using SMOTE resampled data to audit for information leakage.
```bash
python federated_survival.py --dataset cdc_diabetes_012 --experiment mi --rounds 30 --epochs 20 --enable_blockchain True --enable_dp True
```

### Phase 4: System Scalability (Latency)
Measures the real-world wall-clock overhead of the entire federated chain.
```bash
python federated_survival.py --dataset cdc_diabetes_012 --experiment latency --rounds 30 --epochs 20 --enable_blockchain True --enable_dp False
```

---

## 3. Data Integrity & Verification Markers
To ensure the system is working correctly during the run, look for these "Integrity Fingerprints":

| Marker | Expected Behavior | Verification Command |
| :--- | :--- | :--- |
| **GPU Saturation** | CUDA VRAM should hit ~7.7 GB for CDC records. | `nvidia-smi` |
| **SMOTE Balance** | Logs should state "[Data] Multi-class SMOTE applied". | Check `final_paper_audit.log` |
| **Blockchain Trail** | `exp_gas_log.csv` should record ~121k-138k gas per round. | `tail -n 10 test/exp_gas_log.csv` |
| **Privacy Elasticity** | Accuracy should drop from ~63% to ~54% as noise increases. | `cat test/exp_mi_results.csv` |

---

## 4. Visualizing the Evidence
Once all phases are complete, generate the 5 research-grade plots for your report:
```bash
python test/plot_results.py
```
**Output Files:** `fig_mi.png`, `fig_latency.png`, `fig_gas_costs.png`, `fig_dp_tradeoff.png`, `fig_robustness.png`.

---

## 5. Repository Check-in
To capture the audit for the final submission:
```bash
git add test/exp_*.csv test/fig_*.png final_paper_audit.log test/best_model.pth build/deploy_info.json
git commit -m "RESEARCH COMPLETE: Final 5-stage audit and all validated plots"
git push origin main
```


