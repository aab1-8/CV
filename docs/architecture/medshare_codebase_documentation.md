# MedShare Codebase Documentation

This document serves as the exhaustive taxonomy and technical manual for the MedShare project. It covers all moving parts including the Python Flower federated learning implementation, the Ethereum blockchain smart contracts, the frontend dashboard, and the data telemetry systems.

## 1. Root Orchestration & Execution

*   **`federated_survival.py`**: The 582-line master simulation script. It controls the `flwr` (Flower) server/client orchestration, detects high-end GPUs (15GB VRAM) to scale batch sizes (up to 2048), handles `experiment` parameters (`dp`, `mi`, `robustness`, `latency`), and executes adaptive training loops across 7 different datasets. It outputs telemetry data directly to the `/test/` directory and frontend JSONs.
*   **`MedShare_FINAL_new.ipynb` & `MedShare_FINAL.ipynb`**: The primary Jupyter Notebooks for execution on Google Colab. They orchestrate environment setup, dependency installation, blockchain deployment (via Ganache in the background), and cell-by-cell execution of the various `federated_survival.py` experimental suites.
*   **`test_data_health.py`**: A diagnostic script that validates the "Diamond Standard" for datasets before they hit the FL pipeline, checking for missing values (NaNs), ensuring identifiers are dropped, and checking categorical encoding formats.

## 2. Core Machine Learning Engine (`medshare/`)

*   **`engine.py`**: Handles local `train()` and `test()` loops on the clients. Crucially, it integrates PyTorch and `opacus` to inject Differential Privacy (DP) Gaussian noise directly into the stochastic gradient descent optimizer, and applies `FedProx` temporal regularization.
*   **`models.py`**: Defines `SurvivalMLP`, a dynamic neural network architecture. It structurally adapts its final activation layers (Sigmoid vs Logic) based on whether the incoming task is binary or multi-class classification.
*   **`strategy.py`**: Implements `AnomalyMonitoringStrategy` (an extension of Flower’s `FedAvg`). It is the central nervous system of the server: aggregating weights, running `Robust-MAD` statistical anomaly detection to identify and ban malicious (Byzantine) updates, logging telemetry, and reporting to the blockchain.
*   **`client.py`**: Defines `FlowerSurvivalClient`. It coordinates client-side training rounds. If a client is flagged as `is_malicious`, it conducts active adversarial poisoning (`label_flip` and `gradient_scale` attacks) before updating. It also pushes model weight commitments to the blockchain prior to submitting updates to the server.
*   **`data.py`**: The universal ETL pipeline. It fetches data from the UCI ML repository (using an SSL-certificate-bypassing patch), Kaggle, and local CSVs. It conducts on-the-fly `SMOTE` oversampling to handle severe clinical imbalances.
*   **`utils.py`**: The telemetry and aggregation module. Calculates weighted averages for accuracy/AUC, computes the Membership Inference (MI) privacy leak proxy scores, and streams data directly to `exp_*_results.csv` files and JSON files (`training_history.json`) for the frontend.
*   **`blockchain.py`**: The Python-to-Web3 bridge. Contains the `MedShareBlockchain` class, connecting dynamically to Ganache (127.0.0.1:8545). It constructs tasks, manages the reputation ledger, and signs commitment hashes using the ABIs compiled from Solidity.

## 3. Smart Contracts (`contracts/`)

*   **`MedShareTask.sol`**: The task lifecycle contract. Researchers fund tasks with ETH bounties. It tracks state machines (Open, Training, Completed). Only approved hospitals evaluated by their reputation scores can join and get paid.
*   **`Reputation.sol`**: The global network trust ledger. If a hospital triggers the server's Anomaly Detection (Robust-MAD), their reputation score is slashed by the admin, disqualifying them from future task payouts.
*   **`CommitmentRegistry.sol`**: The cryptographic security layer. Enforces a "Commit-then-Submit" protocol. Hospitals submit `keccak256` hashes of their model weights *before* sending physical weights, ensuring that the aggregator server cannot tamper with federated updates post-submission.

## 4. Telemetry & Verification Framework (`test/`)

*   **`plot_results.py`**: A robust 324-line Python script utilizing Matplotlib and Seaborn to parse `/test/*.csv` logs into high-resolution, publication-ready PNGs:
    *   `fig_dp_tradeoff.png`: Accuracy degradation vs. Differential Privacy Noise ($\sigma$).
    *   `fig_robustness.png`: Resiliency of Robust-MAD vs. standard FedAvg under adversarial attacks.
    *   `fig_mi.png`: Membership Inference gap mapping (Information Leakage).
    *   `fig_gas_costs.png`: Scatter/Bar composite plotting EVM token expenditures for on-chain audits.
    *   `fig_latency.png`: Network scaling wall-clock measurements.
*   **`plot_thyroid_mi.py`**: A specialized override plotter utilized specifically for edge-case imbalances present in the Thyroid dataset.

## 5. Web Dashboard (`frontend/`)

*   **`index.html`**: The UI skeleton. A lightweight, modern Single Page Application (SPA) offering three toggleable views: Analytics Dashboard, Researcher Marketplace, and Hospital Portal.
*   **`main.js`**: Connects JSON telemetry (e.g., `baseline.json`, `comparison_stats.json`) into the DOM, driving the reactive display of sample sizes, global AUC metrics, and real-time Hospital trust scores.
*   **`blockchain.js`**: Ethers.js integration that pulls contract addresses from `deploy_info.json`. Allows researchers to create real blockchain tasks directly from the web browser.
*   **`marketplace.js`**: Handles the local state logic for the Research Marketplace, matching data requests from researchers to hospital node capabilities.
*   **`charts.js`**: Leverages `Chart.js` to render dynamic data visualizations in the browser: Triple Baseline Benchmarks, Training Loss tracking, and Hospital Data Distribution bar charts.

## 6. Project Architecture & Maintenance

*   **`scripts/deploy_colab.py`**: Fully automates the compilation and deployment of Solidity contracts to the local Ganache network, linking them together, and seamlessly dropping the resulting ABIs and addresses into the `/frontend/src/data/` folder.
*   **`scripts/patch_notebook_gold.py` & `scripts/clean_nb.py` & `update_notebook.py`**: A suite of automated Python scripts used to surgically alter the JSON structure of your Jupyter Notebooks—bypassing caching errors, altering column schemas, and dynamically swapping experimental targets without requiring manual rewriting.
*   **`add_tests.py` & `run_master.sh`**: Wrappers for automated background execution of rigorous multi-phase sweeps.
*   **`docs/`**: The permanent repository containing final exported SVGs/PNGs (in `/assets/`), PlantUML architecture diagrams, execution guides, and your final experimental audit reports.
