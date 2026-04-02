# MedShare-FL: Documentation Index 📚

Welcome to the official documentation for **MedShare-FL**, a decentralized, privacy-preserving health data marketplace. This index provides a clean, hierarchical structure to explore the project's architecture, security protocols, and experimental results.

---

## 🏛️ [01. Project Foundation](./)
The "Big Picture" documents and the final academic submission materials.
*   **[Final Project Report (Markdown)](./Final_Project_Markdown_Report.md)**: **START HERE.** The comprehensive summary of all findings.
*   **[LaTeX Dissertation Source](./MEng_Final_Report_v2.tex)**: The formal academic submission file.
*   **[System Overview](./System_Overview.md)**: High-level technical demonstrator guide.
*   **[Master File Manifest](./Master_File_Manifest.md)**: Index of all project assets.

## 🏗️ [02. System Architecture](../02_Architecture/)
The engineering blueprints and codebase documentation.
*   **[Architecture Design](../02_Architecture/Architecture_Design.md)**: Main design document for the Hub-and-Spoke FL model.
*   **[Codebase Documentation](../02_Architecture/Codebase_Documentation.md)**: Detailed mapping of Python and Solidity logic.
*   **[Dataset Inventory](../02_Architecture/Dataset_Inventory.md)**: Details on the 7+ clinical datasets supported.
*   **[Visual Gallery](../02_Architecture/Diagrams/)**: Project diagrams (Sequence, Class, and Use Case).
*   **[Technical Methodology Audit](../02_Architecture/Methodology_Audit.md)**: Verified methodology for the 30% malicious-node tests.

## 📊 [03. Case Studies](../03_Case_Studies/)
Empirical results and audit summaries for specific clinical tasks.
*   **[CDC Diabetes Audit (250k+ records)](../03_Case_Studies/Final_Experimental_Audit.md)**: Our largest scalability benchmark.
*   **[Thyroid Disease Summary](../03_Case_Studies/Thyroid_Audit_Summary.md)**: Multi-class imbalanced classification.
*   **[Stroke Prediction Summary](../03_Case_Studies/Stroke_Audit_Summary.md)**: Lifestyle risk factor analysis.
*   **[Support2 Mortality Audit](../03_Case_Studies/Support2_Audit_Summary.md)**: Real-world clinical survival records.

## 🛠️ [04. User Manuals](../04_User_Manuals/)
How to run, configure, and reproduce the experiments.
*   **[VLab Execution Guide](../04_User_Manuals/VLab_Execution_Guide.md)**: Running the system on high-performance vLab servers.
*   **[Colab Setup Reference](../04_User_Manuals/Colab_Execution_Guide.md)**: Running on free cloud hardware.
*   **[Reproducibility Guide](../04_User_Manuals/Reproducibility_Guide.md)**: Ensuring consistent results.
*   **[Performance Evaluation](../04_User_Manuals/Performance_Evaluation_Guide.md)**: Understanding DP and Utility metrics.
*   **[Viva Demo Script](../04_User_Manuals/Viva_Demo_Script.md)**: A step-by-step guide for project presentation.

## 📋 [05. Audit Logs & Forensic Traceability](../05_Audit_Logs/)
The "Black Box" records of historical bug fixes and large-scale runs.
*   **[System Audit Trail](../05_Audit_Logs/System_Full_Audit_Trail.md)**: Complete log for the final Gold Standard rounds.
*   **[Problem Resolution Log](../05_Audit_Logs/Problem_Resolution_Log.md)**: Tracking the "Dataset Paradoxes" and their fixes.
*   **[CDC Replication Log](../05_Audit_Logs/CDC_Diabetes_Replication_Log.md)**: Forensic verification of the CDC run results.
*   **[SSL Patch Reference](../05_Audit_Logs/SSL_Thyroid_Patch_Reference.md)**: Fixes for historical dataset fetch issues.

## 🛡️ [06. Security & Privacy](../06_Security/)
In-depth analysis of the "Defense-in-Depth" strategy.
*   **[SecAgg vs. Robustness](../06_Security/SecAgg_vs_Robustness_Tradeoff.md)**: Scientific rationale for our architectural choices.
*   **[MI Privacy Analysis](../06_Security/MI_Privacy_Audit_Analysis.md)**: Analyzing Membership Inference leakage risk.
*   **[Data Transmission Audit](../06_Security/Data_Transmission_Audit.md)**: Verifying the hashing and blockchain audit trail.
*   **[Platinum Security Audit](../06_Security/Platinum_Security_Audit.md)**: Comprehensive hardening review.
---
*Created by Antigravity for the MedShare-FL Project.*
