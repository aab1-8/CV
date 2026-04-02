# Model Performance Evaluation Guide

This document outlines how the MedShare project measures the success and medical utility of the Federated Global Model. We use a "Triple-Verification" approach to ensure the model is scientifically sound and superior to isolated training.

## 🥇 1. The Success Metric: "The Performance Gap"

We evaluate the federated model by comparing it against two extreme benchmarks to calculate the **Federated Gain**.

| Benchmark | Definition | Role |
| :--- | :--- | :--- |
| **Local Baselines** | Each hospital trains a model **only** on its own small dataset (e.g., 200 records). | Represents the status quo (isolated data). |
| **Centralized Gold Standard** | A theoretical "perfect" model trained as if all hospitals pooled all data into one server. | Represents the upper limit of what is mathematically possible. |
| **Federated Global Model** | The collaboration model produced by MedShare without sharing raw data. | **The Goal**: Must outperform Local Baselines and match the Gold Standard as closely as possible. |

*   **Evidence**: Check `frontend/src/data/comparison_stats.json` or the **Dashboard Analytics** tab. A successful run usually shows the Federated model matching ~95-98% of the Centralized Gold Standard.

## 🔬 2. Server-Side Evaluation (Evaluation Phase)

The performance is not just "reported" by clients; it is verified by the server in every communication round.

### The Evaluation Workflow:
1.  **Fit Phase**: Hospitals train locally and send updates to the server.
2.  **Aggregation**: The server creates a new **Global Model** using the custom `AnomalyMonitoringStrategy`.
3.  **Validation**: The server sends this Global Model back to all hospitals.
4.  **Hold-out Testing**: Each hospital tests the global model on its **private test set** (unseen data).
5.  **Average AUC/Accuracy**: These scores are averaged globally to determine the "true" medical utility of that round.
6.  **Checkpointing**: The system automatically identifies the best performing model across all rounds and saves it to `test/best_model.pth`.

## 📈 3. Visual & Raw Data Evidence

Auditors can verify the model's learning curve through the following files:

*   **`test/fig_latency.png`**: Shows how the model scales over time.
*   **`test/fig_dp_tradeoff.png`**: Proves that the model remains useful even when privacy noise is added.
*   **`test/exp_robustness_results.csv`**: Proves the model can maintain 60%+ accuracy even when 30% of the network is actively trying to poison it.
*   **`frontend/src/data/training_history.json`**: Contains a round-by-round log of Accuracy, Loss, and AUC. In a healthy run, you will see Loss **decreasing** and Accuracy **increasing** until they plateau.

## 🏥 Why We Use AUC-ROC (Area Under Curve)

In medical survival analysis (like our datasets), **Accuracy can be misleading**. For example, if 90% of patients survive, a "dumb" model that always predicts "Survive" would be 90% accurate but useless for identifying high-risk patients.

**AUC-ROC** measures the model's ability to **rank** patients correctly (e.g., does the model assign a higher risk score to the patient who actually needs intervention?).
*   **0.5**: Random chance (useless).
*   **0.7 - 0.8**: Good medical predictive power.
*   **0.9+**: Exceptional performance.

---
**Audit Note**: All performance metrics are calculated using `scikit-learn` in `medshare/engine.py` to ensure standard clinical consistency.
