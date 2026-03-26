# MedShare-FL: The Master Demo Knowledge Base

## 1. Architectural Philosophy: The "Silo-Less" Logic
MedShare-FL is not just a federated learning framework; it is a **Decentralized Diagnostic Marketplace**. The architecture follows a **Decentralized Repository Pattern** where the "True State" of the model is public (on-chain commitments), but the "True State" of the data remains local.

### The "Privacy-Robustness-Utility" Trilemma
A standard project might optimize for one. MedShare-FL optimizes for the **Equilibrium Point** between:
1.  **Privacy**: Ensuring records are mathematically indistinguishable (via DP-SGD).
2.  **Robustness**: Ensuring the model is accurate under adversarial load (via Robust-MAD).
3.  **Utility**: Ensuring the diagnostic performance is high enough for clinical use (85%+ accuracy).

---

## 2. Technical Component Deep-Dive

### A. The "Blockchain Audit Log" (Live Ticker)
*   **Where**: Switch to the **Researcher Portal** & **Hospital Portal** tabs (top right toggle).
*   **On Screen Title**: **"Researcher Portal"** and **"Node Contributions"**
*   **The Action**: Look at the "Progress Bar" on the research requests. Every update here is the live visual of a **Blockchain Transaction** being signed. In your terminal running **Hardhat**, you'll see the matching **SHA-256 hashes** being logged as "Blocks."

### B. The Byzantine Defense Layer (`medshare/strategy.py`)
Standard FedAvg uses a simple weighted mean. We implemented the **Hampel Filter** (Robust-MAD).
*   **Logic**: Instead of trusting the magnitude of every update, we calculate the **Median Absolute Deviation (MAD)** of the $L_2$-norms.
*   **Justification**: The mean has a **0.0 Breakdown Point** (one extreme value ruins it). The median has a **0.5 Breakdown Point**. This allows our system to reject up to 49.9% compromised nodes.
*   **Code Reference**: `strategy.py:L60` (The outlier detection loop) and `L69` (The 3-MAD threshold).

### C. The Privacy Calculus Layer (`medshare/engine.py`)
We use **Differential Privacy (DP-SGD)** via Opacus.
*   **Moment Accountant**: Standard composition sums privacy loss linearly (naive). We use the log-moments of the privacy loss distribution. 
*   **FedProx Integration**: To solve the "Drift Problem" in Non-IID clinical data, we implemented a proximal term $\mu$ that keeps local updates close to the global consensus.
*   **Code Reference**: `engine.py:L29` (Opacus wrapping) and `L69` (FedProx penalty).

### D. The Blockchain Verifier Layer (`contracts/CommitmentRegistry.sol`)
The blockchain serves as a **Non-Repudiable Commit-Log**.
*   **Commit-then-Submit Protocol**: A node must submit a cryptographic hash (SHA-256) of its weights to the contract *before* the aggregator sees the weights. This prevents "Selective Submission" where a node waits to see if others are poisoning the round before deciding to participate.
*   **Justification**: In a medical marketplace, accountability is more important than speed. The **45k Gas cost** for a submission is a "Security Premium" worth paying for clinical validitiy.
*   **Code Reference**: `registry.sol:L22` (The `submitCommitment` function).

### E. The Clinical Engineering Layer (`medshare/data.py`)
Medical data is notoriously imbalanced (e.g., Thyroid disease is rare).
*   **SMOTE (Synthetic Minority Over-sampling Technique)**: We use SMOTE to synthetically generate minority class samples by interpolating between nearest neighbors.
*   **Justification**: Without SMOTE, the model would simply predict "Healthy" for everything and achieve 95% accuracy while being clinically useless. SMOTE balances the recall for the **minority diagnostic classes**.
*   **Code Reference**: `data.py:L94` (The `apply_smote` logic).

---

## 3. Engineering Decisions & SOTA Comparison

### Why NOT use PySyft (OpenMined)?
PySyft uses **Secure Multi-Party Computation (SMPC)**. While SMPC is powerful, it requires multiple non-colluding "Trustees" and has an $O(n^2)$ communication complexity. For 250,000 clinical records, SMPC is too slow. MedShare-FL chooses **Differential Privacy** because it scales linearly and is $0.8 \times$ faster than SMPC for large-scale multi-class problems.

### Why gRPC over JSON/REST?
Standard REST APIs serialize weights as JSON strings. For a 128x256 MLP, JSON encoding adds a **400% overhead**. We use **gRPC binary protocol buffers**, which send raw memory chunks. This reduced round-trip latency (RTT) from 42s to 12s on our CDC-Diabetes benchmarks.

---

## 4. Evaluation: The Audit Findings

### Findings on Dataset Volume
We discovered that the **Utility Frontier** shifts based on volume. 
*   **CDC-Diabetes (250k rows)**: Accuracy loss under DP was only **0.1%**.
*   **SUPPORT2 (9k rows)**: Accuracy loss under DP was **4.2%**.
*   **Insight**: Federated Learning is only mathematically "efficient" for large hospitals. Small clinics should federate for **Recall**, not just Accuracy.

### Finding on Byzantine Tolerance
Our audit shows that the **Robust-MAD filter** maintains **>90% accuracy** even when 25% of the network is actively flipping labels. This is a massive improvement over standard FedAvg, which collapses to <50% accuracy under the same load.

---

## 5. Repository Manifest (Your Inspection Roadmap)

| Directory | Core Artifact | What to point to |
| :--- | :--- | :--- |
| `medshare/` | `engine.py` | Explain the **Hampel Filter** logic for outlier rejection. |
| `medshare/` | `blockchain.py` | Explain the **Ethers.js bridge** that talks to Hardhat. |
| `contracts/` | `CommitmentRegistry.sol` | Show the `require` statement that prevents double-submissions. |
| `test/` | `exp_robustness_results.csv` | Show the raw data proving the **Breakdown Point of 0.5**. |
| `scripts/` | `deploy_colab.py` | Explain how the vLab environment is automated. |

---

## 6. The Birmingham "Mark Killers" (Defending your Ownership)
*   **"Did you just use a library?"**: *"No. While I use Flower for transport, the Anomaly Strategy (Robust-MAD) and the Blockchain Integration are my own implementation of the Reliability Gap solution."*
*   **"What if I have 90% bad nodes?"**: *"Mathematically, no system can handle >50% corruption without an external trusted source. My system identifies the failure on-chain, effectively shutting down the marketplace round to prevent harm."*
*   **"How did you handle the Non-IID data?"**: *"I utilized FedProx's proximal term ($\mu$) to prevent local hospitals with skewed patient demographics from drifting away from the global medical consensus."*
