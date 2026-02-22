# MedShare-FL Issue Tracker

## 🟢 Resolved / Completed
- [x] **Synthetic Data Generator**: Added `generate_synthetic_data` to augment real clinical data. (Implemented: `federated_survival.py`)
- [x] **Missing Loss Metric in Dashboard**: Fixed `evaluate` method to return loss in metrics dictionary. (Fixed: `federated_survival.py`)
- [x] **Colab Artifact Cleanup**: Removed `survival_federated.ipynb` and `fl_logic/` directory.
- [x] **Results Visibility**: Added Comparison Statistics and Training History JSON exports for frontend dashboard.
- [x] **Federated Performance Gap**: Tuned hyperparameters (10 rounds, 10 epochs) to reach 99.1% of centralized accuracy.
- [x] **Privacy Mechanisms**: Added Differential Privacy (DP) noise to weights using `opacus` (Sigma=1.0).
- [x] **Model Checkpointing**: Save the best global model to disk (`test/best_model.pth`).

- [x] **Data Heterogeneity**: Performance variability handled by disease-group partitioning and global feature scaling. Use of FedProx minimizes drift.
- [x] **Windows Ray Warnings**: Simulation stability verified on Windows; resource throttling prevents OOM. (Status: Experimental but Stable).
- [x] **Hardware-Aware Acceleration**: Implemented dynamic resource allocation for Colab (15GB GPU) vs Local (6GB GPU).
- [x] **Data & Baseline Caching**: Implemented JSON caching for datasets and local model baselines to skip redundant training.

## 🔴 Open Issues / Future Work
- [ ] **Dynamic Client Scaling**: Simulate variable number of clients or dropouts.
- [ ] **Secure Aggregation**: Evaluate impact of masking on non-linear strategies.