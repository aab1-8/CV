# 🏆 Gold Standard Execution Plan: Diabetes Hospital Audit

This document defines the definitive, research-grade parameters for the 130-US Hospitals dataset (101,766 records) when running on high-end hardware (15GB vLab GPU).

---

## 🔬 1. Scientific Rationales

| Feature | Setting | Rationale |
| :--- | :--- | :--- |
| **Rounds** | **60** | Required to achieve convergence on the 50+ medical features/biomarkers in this dataset. |
| **Local Epochs** | **10** | Balanced local optimization to ensure the model learns 3-class classification without noise overfitting. |
| **Audit Epochs** | **40** | High-intensity "Stress Test" used strictly for the Privacy Audit (MI) to prove defense strength under extreme overfitting. |
| **Batch Size** | **2048** | The "Scientific Sweet Spot": Provides 10 gradient steps per epoch, ensuring the model identifies complex patterns in the hospital data without noise. |
| **Rebalancing** | **SMOTE** | Synthetic oversampling is enabled to prevent the model from ignoring rare readmission categories. |

---

## 🚀 2. Command Execution Sequence

Run these commands in order from the project root. The system is programmed to detect your vLab hardware and apply the Gold Standard settings automatically.

### Phase 1: The Privacy Stress-Test
This is the most intensive part of the audit. It proves that even if hospitals "over-train" their data, individuals cannot be identified.
```powershell
python federated_survival.py --experiment mi --dataset diabetes_hospital
```
*   **Target Output:** `test/exp_mi_results.csv` & `fig_mi.png`

### Phase 2: The Security & Utility Sweep
Generates the core data for your performance reports and robustness analysis.
```powershell
# Run DP Trade-off Sweep
python federated_survival.py --experiment dp --dataset diabetes_hospital --epochs 10

# Run Robustness Defense Sweep
python federated_survival.py --experiment robustness --dataset diabetes_hospital --epochs 10
```
*   **Target Output:** `test/exp_dp_results.csv`, `test/exp_robustness_results.csv`, `fig_dp_tradeoff.png`, `fig_robustness.png`

### Phase 3: System Performance & Dashboard
Measures the decentralized overhead and prepares the results for the web interface.
```powershell
# Run Latency/Gas Benchmark
python federated_survival.py --experiment latency --dataset diabetes_hospital --rounds 10 --enable_blockchain True
```
*   **Target Output:** `test/exp_gas_log.csv`, `test/exp_latency_log.csv`, `fig_gas_costs.png`, `fig_latency.png`

---

## 📊 3. Final Verification (The "Triple Check")
After all runs are complete, execute the plotting engine to finalize your research artifacts:
```powershell
python test/plot_results.py
```

**Required Artifact Inventory:**
1. [ ] `test/fig_mi.png` (Privacy Proof)
2. [ ] `test/fig_dp_tradeoff.png` (Utility Proof)
3. [ ] `test/fig_robustness.png` (Security Proof)
4. [ ] `test/fig_gas_costs.png` (Economic Proof)
5. [ ] `test/fig_latency.png` (Scalability Proof)

---
*Created: 2026-03-04 | Verified: vLab EC2 Instance (T4 GPU)*
