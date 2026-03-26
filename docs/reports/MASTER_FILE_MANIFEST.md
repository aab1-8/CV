# MedShare-FL: Master File Manifest (Inspection Guide)

| File Path | Description | Key Variable/Function | Why it's Awesome |
| :--- | :--- | :--- | :--- |
| `medshare/strategy.py` | **Byzantine Strategy** | `aggregate_fit` | Implements the MAD outlier rejection. |
| `medshare/engine.py` | **ML Engine** | `train` | Handles FedProx and Opacus DP-SGD. |
| `medshare/blockchain.py` | **Blockchain Bridge** | `post_commitment` | Connects Python to the Solidity contract. |
| `medshare/data.py` | **Clinical Preprocessing** | `apply_smote` | Solves the medical "Minority Class" skew. |
| `medshare/utils.py` | **Telemetry Layer** | `weighted_average` | Tracks real-time Privacy Leakage (MI). |
| `contracts/CommitmentRegistry.sol` | **Smart Contract** | `postCommitment` | Immutable audit trail for hospital trust. |
| `medshare/client.py` | **Adversary Logic** | `is_malicious` | Simulates flips and scaling attacks. |
| `test/plot_results.py` | **Visualization** | `plot_accuracy` | Generates the performance proof graphs. |

### The "Golden Line Numbers" for Inspection:
*   **Hampel Filter (Robust-MAD)**: `medshare/strategy.py`, Line **60** (Calculation) & **69** (Threshold).
*   **DP-SGD (Opacus)**: `medshare/engine.py`, Line **29** (Privacy wrapping).
*   **FedProx Logic**: `medshare/engine.py`, Line **69** (Consensus stability).
*   **On-Chain Commitment**: `medshare/client.py`, Line **80** (Handshake logic).
*   **Label Poisoning Attack**: `medshare/client.py`, Line **29** (The Flip logic).
*   **Reputation Penalty Logic**: `medshare/strategy.py`, Line **83** (Docking points).
