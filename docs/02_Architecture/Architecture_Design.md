# MedShare System Architecture

MedShare is a **Privacy-Preserving Federated Learning Marketplace** designed for healthcare datasets. It ensures that medical models can be trained across multiple hospitals without ever sharing sensitive patient records.

## 🏗️ Core Components

- **`medshare/` (The Core Engine)**: A modularized Python package containing:
    - `models.py`: Neural Network definitions (MLP for Survival Analysis & Classification).
    - `data.py`: Secure data loaders with rebalancing and clinical schema matching.
    - `engine.py`: Training and evaluation loops with **Differential Privacy (Opacus)**.
    - `client.py`: The **Flower (FL)** client that handles local training and security hooks.
    - `strategy.py`: Custom server aggregation logic featuring **Anomaly Detection** and **Blockchain Audit Logs**.
    - `blockchain.py`: Manager class for coordinating on-chain interactions.

- **`contracts/` (Solidity)**: Smart contracts deployed on Ethereum (or Ganache) to provide:
    - **Task Registry**: Managing training jobs.
    - **Commitment Registry**: Locking in model update hashes for auditability.
    - **Reputation System**: Tracking and rewarding node honesty.

- **`frontend/` (Web Dashboard)**: A modern UI built with Vite/Chart.js to:
    - **Marketplace**: Create model requests and monitor hospital contributions.
    - **Analytics**: Visualize training accuracy, data distribution, and security audits.

- **`federated_survival.py`**: The primary entry point for running simulations and benchmarks.

## 🔄 The MedShare Workflow

1.  **Task Creation**: A researcher uses the **Marketplace** to broadcast a model training request to the Blockchain.
2.  **Local Training**: Participating hospitals fetch the global model and train it on their **Local Private Data**.
3.  **Privacy Protection**: **Differential Privacy (DP)** adds mathematical noise to the updates, ensuring individual patient data cannot be reverse-engineered.
4.  **Blockchain Audit**: Hospitals post a hash of their trained weights to the **Commitment Registry** before sharing them.
5.  **Robust Aggregation**: The server collects updates, uses **Anomaly Detection** to filter out poisoning attacks, and updates the global model.
6.  **Trust Scoring**: Honesty is rewarded with **Blockchain Reputation**, while malicious behavior (poisoning) results in credit deductions.

## 🛡️ Privacy & Auditing (Technical Specs)

- **MIA Advantage (Information Leakage)**: Our Privacy Audit plot calculates empirical leakage using the **AUC-Gap metric (Nasr et al., 2019)**. It measures the discrepancy between **Training AUC** and **Testing AUC** across the hospital network.

### 🧠 Understanding the "Generalization Gap"
In the context of Membership Inference Attacks (MIA), the model acts as a "witness" to the data. If a model behaves differently when it sees data it has been trained on versus new data, it leaks a **Membership Signature**.

*   **Small/No Gap = Low Leakage**: If the model discriminates equally well on training patients AND strangers, an attacker cannot distinguish between them. The model has learned general medical rules.
*   **Large Gap = High Leakage**: If the model has a significantly higher AUC on training patients than on strangers, it has **memorized** specific details. This allows an attacker to identify training participants with high confidence.

#### 🏥 A Clinical Example:
Imagine a model trained to predict a rare lung disease:
1.  **Attacker Input**: Patient X (who has a unique genetic marker).
2.  **High-Leakage Model**: Predicts the disease for Patient X with 99.9% confidence because it "remembers" that exact DNA pattern from the training set. However, it only predicts 60% confidence for a stranger with the same symptoms.
3.  **The Result**: The attacker knows: *"Because the model is uniquely over-confident on Patient X, they were definitely in the training database."* Their clinical history is now exposed.

- **Noise Multiplier ($\sigma$)**: In the audits, $\sigma$ represents the volume of Gaussian noise added to model updates. Higher $\sigma$ values physically prevent the model from memorizing unique patient details, thereby closing the Generalization Gap.

### 📊 Dataset-Specific Patterns (Clinical Audits)

1.  **High Stability Baseline**: In standard federated runs with 5 hospitals, you may observe low baseline leakage without privacy. This occurs because the institutional cohort sizes are sufficient to allow the model to learn general medical patterns without immediate overfitting.
2.  **The Instability Spike**: At very low noise levels, empirical leakage can occasionally fluctuate. This is not because the model is "less safe", but because the noise causes **generalization jitter**.
3.  **The Privacy Gain Curve**: As $\sigma$ increases, you will observe a consistent **narrowing of the AUC-Gap**. This is the intended effect of Differential Privacy: it physically erases the "Membership Signature" until the training and testing performance are indistinguishable.

## 💾 Data Storage

- **Local Storage**: MedShare uses **CSV-based flat files** for portability and ease of mount/sync in environments like Google Colab.
- **Distributed Ledger**: The **Ethereum (Ganache)** blockchain acts as the project's immutable database for:
    - **Audit Trails**: Every training step is hashed and registered on-chain.
    - **Reputation**: Node history is stored in the `Reputation.sol` smart contract.
    - **Bounties**: ETH balances are managed via the `MedShareTask.sol` contract.