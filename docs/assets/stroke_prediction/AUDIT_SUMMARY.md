# Audit Summary: Stroke Prediction (Gold Standard)

This document provides a comprehensive overview of the Federated Learning Audit conducted on the **Stroke Prediction** dataset. The audit verifies the privacy, utility, robustness, and performance metrics of the decentralized training process.

## 📊 Performance Overview

The system achieved a high-performance profile while maintaining rigorous privacy protections.

| Metric | Result | Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Max Accuracy** | **84.50%** | > 80% | **PASSED** ✅ |
| **Model AUC** | **0.9289** | > 0.85 | **PASSED** ✅ |
| **Privacy Budget ($\varepsilon$)** | **7.53** | $\le$ 10.0 | **PASSED** ✅ |
| **MI Leakage (AUC Gap)** | **0.0051** | $\le$ 0.05 | **PASSED** ✅ |
| **Robustness Score** | **100%** | Attack Blocked | **PASSED** ✅ |

## 🛡️ Security & Privacy Audit

### 1. Membership Inference (MI) Protection
The MI Audit confirmed that the model exhibits virtually zero privacy leakage. Even after 100 rounds of training, the advantage an attacker would gain to determine if a patient was in the training set is statistically insignificant (**MI-Gap: 0.0051**).

### 2. Differential Privacy (DP) Trade-off
The optimal balance was found at **$\sigma = 1.5$**, yielding an **$\varepsilon$ of 7.53**. This ensures that individual patient records are protected by mathematical noise without significantly degrading the model's ability to predict strokes accurately.

### 3. Robustness & Gatekeeping
During the audit, a **Label Flip** attack was simulated. The blockchain-integrated **Gatekeeper** successfully:
- Detected anomalous updates from a malicious node.
- Temporarily blacklisted the offending hospital.
- Maintained global model accuracy despite the adversarial presence.

## ⛓️ Blockchain Transparency
All **100 training rounds** were recorded on the decentralized registry.
- **Gas Costs**: Verified and optimized for high-frequency medical research.
- **Incentives**: 0.05 ETH bounty distributed to participating hospitals based on contribution quality.
- **Latency**: Blockchain transaction overhead accounted for less than **12%** of total training time, maintaining clinical real-time viability.

## 📂 Artifacts Registry
The results and visualizations generated during this audit are archived in this directory:
- **Plots**: `fig_mi.png`, `fig_dp_tradeoff.png`, `fig_robustness.png`, `fig_gas_costs.png`, `fig_latency.png`
- **Logs**: `exp_mi_results.csv`, `exp_dp_results.csv`, `exp_robustness_results.csv`
- **Metadata**: `training_history.json`, `baseline.json`, `comparison_stats.json`
- **Model**: `best_model.pth` (Final Audited Weights)

---
*Generated on: 2026-03-17*
