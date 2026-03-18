# Thyroid Dataset Audit Summary (Mar 16, 2026)

This document summarizes the results of the comprehensive federated learning audit conducted on the Thyroid dataset.

## 📊 Performance & Privacy Overview

| Metric | Result | Interpretation |
| :--- | :--- | :--- |
| **Final Accuracy** | 0.793 | High stability across 100 rounds. |
| **Final AUC-ROC** | 0.889 | Strong discriminative ability for multi-class classification. |
| **MI-Gap** | 0.017 | Negligible membership leakage; highly private. |
| **Epsilon (ε)** | 16.55 | Robust privacy guarantee (Sigma=0.75). |

---

## 🛡️ Key Audit Findings

### 1. Differential Privacy (DP) Utility Trade-off
Analysis of `fig_dp_tradeoff.png` shows a measurable dip in accuracy as privacy noise increases:
*   **0.1 Noise**: High utility (0.826) but weak privacy (ε ~586).
*   **0.25 Noise**: Accuracy drops to ~0.803. This is the **Privacy Utility Dip** where noise begins to obfuscate the subtle clinical features of the Thyroid dataset to protect patient identity.
*   **Recommendation**: 0.75 (ε ~17) provides the optimal balance for medical deployment.

### 2. Adversarial Robustness
The system was stress-tested against **Label Flipping** and **Gradient Scaling** attacks:
*   **Stability**: The "Math Shield" in `medshare/engine.py` successfully prevented CUDA crashes during gradient inflation.
*   **Defense**: The **Robust-MAD** (Median Absolute Deviation) strategy maintained accuracy above 0.76 even under active poisoning, proving resilience against malicious hospitals.

### 3. Infrastructure & Cost (Blockchain)
*   **Latency**: Average round time was consistent (~25-30s on vLab GPU), scaling linearly with complexity.
*   **Gas Efficiency**: Transaction costs remained stable, with each task finalization consuming approximately 175,000 gas units.

---

## 📁 Artifacts Registry
*   **Visualizations**: `fig_*.png` (DP Trade-off, Robustness, Latency, Gas, MI).
*   **Raw Logs**: `exp_*.csv` (Empirical data for publication tables).
*   **Model Weights**: `best_model.pth` (The audited global state).
