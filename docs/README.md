# MedShare-FL: Documentation Index 📚

Welcome to the official documentation for **MedShare-FL**, a decentralized, privacy-preserving health data marketplace. This index provides a clean structure to explore the project's architecture, security protocols, and experimental results.

---

## 🏛️ [System Architecture](./architecture/)
Discover the high-level design, class structures, and technical workflow of the MedShare ecosystem.
*   **[Core Architecture](./architecture/architecture.md)**: Main design document explaining the Hub-and-Spoke FL model.
*   **[Diagrams](./architecture/)**: Visual representations including Sequence, Class, and Use Case diagrams.
*   **[Dataset Inventory](./architecture/dataset_inventory.md)**: Details on the 4+ clinical datasets supported.
*   **[File Structure Guide](./architecture/file_structure_guide.md)**: Navigating the codebase folders.

## 📊 [Experimental Reports](./reports/)
Detailed performance audits across multiple medical tasks.
*   **[Final Project Report](./reports/Final_Project_Report_Combined.md)**: **START HERE.** The comprehensive summary of all findings.
*   **[Dataset Deep-Dives](./reports/)**:
    *   [Maternal Health](./reports/RESULTS_MATERNAL_HEALTH.md)
    *   [Stroke Prediction](./reports/RESULTS_STROKE_PREDICTION.md)
    *   [Support2 Disease Prediction](./reports/RESULTS_SUPPORT2_DISEASE.md)
    *   [Thyroid Disease](./reports/RESULTS_THYROID.md)
*   **[Performance Guide](./reports/MODEL_PERFORMANCE_GUIDE.md)**: Understanding AUC, Accuracy, and Convergence metrics.

## 🛡️ [Security & Privacy](./security/)
In-depth analysis of the system's "Defense-in-Depth" strategy.
*   **[MI Privacy Audit](./security/MI_PRIVACY_AUDIT_ANALYSIS.md)**: Analyzing Membership Inference leakage risk.
*   **[SecAgg vs. Robustness](./security/secagg_vs_robustness_tradeoff.md)**: Scientific rationale for our architectural choices.
*   **[Technical Audit](./security/Technical_Methodology_Audit.md)**: Verified methodology for the 30% malicious-node tests.
*   **[Data Transmission](./security/data_transmission_audit.md)**: Verifying the hashing and blockchain audit trail.

## 🛠️ [Operational Guides](./guides/)
How to run, configure, and reproduce the experiments.
*   **[Colab Setup](./guides/colab_setup.md)**: Running the system on free cloud hardware.
*   **[Config Guide](./guides/config_guide.md)**: Tuning Rounds, Epochs, and Privacy Multipliers.
*   **[Reproducibility](./guides/REPRODUCIBILITY.md)**: Ensuring consistent results across environments.
*   **[VLab Persistence](./guides/VLAB_PERSISTENT_RECOVERY.md)**: Managing long-running simulations on remote servers.

## 📋 [Audit Logs & Archives](./audit_logs/)
Traceability records for development and large-scale runs.
*   **[Problem Resolution Log](./audit_logs/Problem_Resolution_Log.md)**: Historical fixes and bug tracking.
*   **[CDC Diabetes Archive](./audit_logs/CDC_DIABETES_012_DATA_ARCHIVE.md)**: Audit trail for the 253k record multiclass dataset run.
*   **[Final Audit Report](./audit_logs/Final_Experimental_Audit_Report.md)**: Verification of the final simulation sweeps.

---
*Created by Antigravity for the MedShare-FL Project.*
