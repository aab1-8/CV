# MedShare-FL: Documentation Index 📚

Welcome to the official documentation for **MedShare-FL**, a decentralized, privacy-preserving health data marketplace. This index provides a clean structure to explore the project's architecture, security protocols, and experimental results.

---

## 🏛️ [System Architecture](./architecture/)
Discover the high-level design, class structures, and technical workflow of the MedShare ecosystem.
*   **[Core Architecture](./architecture/architecture.md)**: Main design document explaining the Hub-and-Spoke FL model.
*   **[Diagrams](./architecture/)**: Visual representations including Sequence, Class, and Use Case diagrams.
*   **[Dataset Inventory](./architecture/dataset_inventory.md)**: Details on the 4+ clinical datasets supported.
*   **[File Structure Guide](./guides/file_structure_guide.md)**: Navigating the codebase folders.

## 📊 [Experimental Reports](./reports/)
Detailed performance audits across multiple medical tasks.
*   **[MSc Thesis: Final Report](./reports/MSc_Final_Project_Report.md)**: **START HERE.** The comprehensive summary of all findings.
*   **[Verified Audit Summaries](./reports/)**:
    *   [Maternal Health](./reports/RESULTS_MATERNAL_HEALTH_AUDIT_SUMMARY.md)
    *   [Stroke Prediction](./reports/RESULTS_STROKE_AUDIT_SUMMARY.md)
    *   [Support2 (Mortality & Disease)](./reports/RESULTS_SUPPORT2_AUDIT_SUMMARY.md)
    *   [Thyroid Disease](./reports/RESULTS_THYROID_AUDIT_SUMMARY.md)
    *   [Admin Category Audit](./reports/RESULTS_ADMIN_CATEGORY_AUDIT_SUMMARY.md)
    *   [Admin Billing Audit](./reports/RESULTS_ADMIN_BILLING_SUMMARY.md)
*   **[Performance Guide](./guides/MODEL_PERFORMANCE_GUIDE.md)**: Understanding AUC, Accuracy, and Convergence metrics.

## 🛡️ [Security & Privacy](./security/)
In-depth analysis of the system's "Defense-in-Depth" strategy.
*   **[MI Privacy Audit](./security/MI_PRIVACY_AUDIT_ANALYSIS.md)**: Analyzing Membership Inference leakage risk.
*   **[SecAgg vs. Robustness](./security/secagg_vs_robustness_tradeoff.md)**: Scientific rationale for our architectural choices.
*   **[Technical Audit](./architecture/Technical_Methodology_Audit.md)**: Verified methodology for the 30% malicious-node tests.
*   **[Data Transmission](./security/data_transmission_audit.md)**: Verifying the hashing and blockchain audit trail.

## 🛠️ [Operational Guides](./guides/)
How to run, configure, and reproduce the experiments.
*   **[Colab Setup](./guides/colab_setup.md)**: Running the system on free cloud hardware.
*   **[Config Guide](./guides/config_guide.md)**: Tuning Rounds, Epochs, and Privacy Multipliers.
*   **[Reproducibility](./guides/REPRODUCIBILITY.md)**: Ensuring consistent results across environments.
*   **[VLab Persistence](./guides/VLAB_PERSISTENT_RECOVERY.md)**: Managing long-running simulations on remote servers.
*   **[SSL Patch Reference](./guides/SSL_CERTIFICATE_THYROID_PATCH_REFERENCE.md)**: Fixes for SSL/Dataset issues.

## 📋 [Audit Logs & Archives](./audit_logs/)
Traceability records for development and large-scale runs.
*   **[Problem Resolution Log](./audit_logs/Problem_Resolution_Log.md)**: Historical fixes and bug tracking.
*   **[CDC Diabetes Archive](./audit_logs/CDC_DIABETES_012_DATA_ARCHIVE.md)**: Audit trail for the 253k record multiclass dataset run.
*   **[Final Audit Report](./reports/Final_Experimental_Audit_Report.md)**: Verification of the final simulation sweeps.

---
*Created by Antigravity for the MedShare-FL Project.*
