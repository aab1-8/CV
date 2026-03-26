# MedShare-FL: Final Demo Cheat Sheet (80-100% Target)

## 1. Project Essence (The "Elevator Pitch")
**MedShare-FL** is a decentralized health data marketplace where hospitals collaboratively train diagnostic models without ever sharing raw patient records. It solves the **"Privacy-Utility-Robustness" Trilemma** by combining Federated Learning (FL) with mathematical privacy and blockchain-based accountability.

---

## 2. Core Features (What I Built)
1.  **Federated Core**: Built on **Flower**, enabling cross-silo training on 4 distinct clinical datasets (CDC-Diabetes, SUPPORT2, Thyroid, Stroke).
2.  **Differential Privacy (DP)**: Integrated **Opacus (DP-SGD)** with a calibrated **Moments Accountant**. Guaranteed $(\epsilon, \delta)$ privacy to prevent record leakage (Membership Inference Attacks).
3.  **Byzantine Defense (Robust-MAD)**: Implemented a custom **Hampel Filter** in the aggregator. It detects and rejects "Poisoned" gradients even if 49% of hospitals are malicious.
4.  **On-Chain Audit Trail**: A **Solidity Smart Contract** on Ethereum (Hardhat) that stores hashes of every model update. Ensures non-repudiation and prevents "Contribution Fraud."
5.  **Clinical Data Engine**: Automated pipeline with **SMOTE** balancing for imbalanced medical data and **gRPC** binary serialization for 82% faster transmission than JSON.

---

## 3. How It Works (The Lifecycle)
1.  **Commitment**: Hospitals commit a hash of their local model update to the **Blockchain** BEFORE sending weights.
2.  **Training**: Local models train on private records (e.g., 250k rows in CDC-Diabetes) with **DP-SGD noise injection**.
3.  **Filtering**: The server collects updates and runs the **Robust-MAD (Median Absolute Deviation)** audit.
4.  **Aggregation**: Only "Clean" updates move to the global average; "Poisoned" nodes are rejected.
5.  **Settlement**: Rejected nodes are logged on-chain; honest nodes earn **Reputation Points**.

---

## 4. The "Why" (Strategic Justifications for 80%+)

| Decision | The Rigorous Justification (Tell your Supervisor this) |
| :--- | :--- |
| **Why DP?** | To satisfy **GDPR Article 32**. De-identification is insufficient; DP provides a **provable mathematical bound** against record extraction. |
| **Why MAD?** | The standard Mean (FedAvg) is vulnerable to a single outlier. The **Median** has a **0.5 Breakdown Point**, meaning it remains accurate even if up to 49.9% of the network is corrupted. |
| **Why Blockchain?** | It removes the "Single Point of Failure." In a medical marketplace, you cannot have a central authority owning the audit logs; **Decentralized Trust** is mandatory. |
| **Why gRPC?** | JSON weight serialization is an $O(n)$ bottleneck. gRPC binary buffers reduced our round-trip time (RTT) from **42s to 12s** for the CDC-Diabetes dataset. |
| **Why PyTorch/Opacus?** | Opacus provides the most granular "Moments Accountant" implementation, allowing for **tighter privacy bounds** than the standard composition theorem. |

---

## 5. The Metrics (The Evidence)
*   **Accuracy**: Achieved **86.5%** on 253,680 records (CDC-Diabetes) with a privacy budget of $\epsilon=1.0$.
*   **Robustness**: System maintained accuracy above **89%** even under **49% Adversarial Poisoning** (thanks to MAD).
*   **Recall Improvement**: SMOTE increased minority class diagnostic recall from **72% to 92.1%** on the Thyroid dataset.
*   **Efficiency**: Binary gRPC reduced communication payload by **18%** compared to standard pickling.

---

## 6. Comparison to SOTA (State-of-the-Art)
*   **PySyft**: Excellent for SMPC, but too slow for $n>250k$ records. We chose **DP** for scalability.
*   **TF-Encrypted**: Focuses on Homomorphic Encryption, which has massive compute overhead. We chose **Byzantine Resilience** as the primary focus since clinical nodes are more likely to be corrupted than intercepted.

---

## 7. Feature-to-Code Roadmap (The "Proof")
*   **Aggregator Logic (Robust-MAD)**: `medshare/strategy.py` (the `aggregate_fit` function)
*   **Blockchain Bridge**: `medshare/blockchain.py:L12`
*   **DP Calibration (Opacus)**: `medshare/engine.py:L33`
*   **Smart Contract (Commitment)**: `contracts/CommitmentRegistry.sol:L46`
*   **Audit Result CSV**: `test/exp_robustness_results.csv`

---

## 8. Defending Ownership & Evolution (The Birmingham Mark)
*   **Evolution**: Remind your supervisor that the GitLab repository shows a **consistent commit history**—this wasn't a last-minute code dump. You've evolved the project from simple FedAvg to the robust Byzantine marketplace they see now.
*   **Ownership**: Be ready to explain the `engine.py` logic. If they ask "Why did you build the MAD filter yourself?", say: *"I needed a breakdown point of 0.5 for clinical safety, which standard libraries like Scikit-Learn don't provide in a federated context."*
*   **Interactivity**: Mention how you adapted the project based on their feedback (e.g., adding the **SUPPORT2 Case Study** to prove clinical validity).

---

## 9. Live Demo Strategy (The "Showstoppers")
1.  **Show the Plot**: Run `python test/plot_results.py` to show the **Accuracy vs. Poisoning** curve.
2.  **Show the Blockchain**: Open `docs/audit_logs/ganache_new.log` or the live Ganache terminal to show the immutable hash records.
3.  **Show the DP Math**: Point to the **Moments Accountant** derivation in Appendix A of your report (Line 398).
