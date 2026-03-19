# Technical Methodology: Full-Scale GPU Audit (253,680 Records)

This document details the high-fidelity experimental setup and technical parameters used to generate the final audit results for the MedShare-FL project on the `cdc_diabetes_012` dataset.

## 1. Experimental Environment (vLab GPU)
The experiments were executed in a high-performance cloud environment (vLab) specifically configured to handle massive tabular datasets with Privacy-Preserving Machine Learning (PPML) overhead.

*   **Compute (GPU)**: NVIDIA Tesla T4 (15GB GDDR6 VRAM).
*   **Memory (System)**: High-capacity System RAM utilized for host-side SMOTE balancing of the 253k record set.
*   **Operating System**: Amazon Linux 2 (x86_64).
*   **Portable Node Stack**: Due to system-level `glibc 2.26` constraints, a portable **Node.js v14.21.3** binary was utilized to host the Ganache-based audit blockchain.

## 2. Core Software Stack
| Dependency | Version | Purpose |
| :--- | :--- | :--- |
| **PyTorch** | 2.4.1+cu121 | GPU-accelerated deep learning and gradient computation. |
| **Flower (FLWR)** | 1.11.1 | Federated Simulation Engine and Client/Server orchestration. |
| **Opacus** | 1.5.4 | Differential Privacy (DP) engine for gradient clipping and noise addition. |
| **Web3.py** | 7.14.1 | Blockchain integration for the immutable audit trail. |
| **Imbalanced-Learn** | 0.12.4 | SMOTE implementation for multi-class balancing of clinical indicators. |
| **Scikit-Learn** | 1.3.2 | Evaluation metrics (Accuracy, AUC-ROC) and data preprocessing. |

## 3. Massive Dataset Configuration (`cdc_diabetes_012`)
The audit targets the definitive CDC Indicators dataset, consisting of **253,680 unique patient records**.

### Hyperparameter Tuning (Multi-Class 0/1/2)
To ensure convergence on a quarter-million rows without GPU "Out of Memory" (OOM) errors, the following "Golden Parameters" were utilized:
*   **Global Rounds**: 30 (Ensures cross-hospital consensus).
*   **Local Epochs**: 20 (High-density learning per hospital).
*   **Batch Size**: **2,048** (Optimized for Tesla T4 CUDA core saturation and stable DP gradients).
*   **SMOTE Balancing**: Performed on the CPU host to preserve GPU VRAM for the 253k-row backpropagation.

## 4. Privacy & Security Matrix
### Differential Privacy (DP) Sweep
A 5-point privacy-utility curve was generated using the following noise multipliers ($\sigma$):
*   **$\sigma = 0.0$**: Baseline (No Privacy) for utility benchmarking.
*   **$\sigma = 0.5, 1.0, 2.0, 5.0$**: Progressive privacy scaling to map the Epsilon ($\epsilon$) budget vs. Accuracy tradeoff.

### Robustness & Security
The system was audited against adversarial interference using:
*   **Attacks**: 30% malicious hospital participation (Label Flipping and Gradient Scaling).
*   **Defense**: **Robust-MAD** (Median Absolute Deviation) strategy implemented at the server level to filter out malicious gradient updates before aggregation.

## 5. Audit Trail & Reproducibility
Every round of the experiment is cryptographically secured:
1.  **Commitment**: Each hospital posts a SHA-256 hash of its model update to the `CommitmentRegistry` smart contract.
2.  **Reputation**: Hospital reliability scores are updated on-chain based on the `Robust-MAD` filtering results.
3.  **Logs**: Real-time gas costs (~121k-138k Gas per round) and round latencies are recorded in `test/exp_gas_log.csv` and `test/exp_latency_log.csv`.

## 6. Execution Summary (Feb 28, 2026)
The full-scale audit of the `cdc_diabetes_012` dataset was successfully completed on Feb 28, 2026. 

*   **Result Status**: All 4 experimental phases finished without runtime errors.
*   **Data Integrity**: 100% verified with UTC timestamps and matching visual plots.
*   **Final Repository State**: Audit logs, 5 verified CSVs, 5 generated plots, and the final trained model weights (`best_model.pth`) are fully committed to the repository.

**SIGN-OFF**: *FINAL AUDIT COMPLETED AND VALIDATED.*
