# MedShare-FL: Original Project Proposal

## 1. Title
**MedShare-FL** - A decentralized marketplace where hospitals (data custodians) collaboratively train and provide ML models (not raw data) for research. Privacy is preserved via Federated Learning (FL), Secure Aggregation, and Differential Privacy; an AI security layer detects Sybils and privacy risks.

---

## 2. Motivation and Justification
Centralized health-data brokers raise privacy, transparency, and compensation issues. Researchers need diverse real-world models; patients/hospitals require data confidentiality. MedShare-FL lets hospitals retain data while collectively training models for researchers—making the process auditable and robust to attacks. The project combines distributed systems and ML security.

---

## 3. Aims and Learning Objectives
**Main Aim**: Build a prototype MedShare-FL platform and evaluate its privacy/robustness/utility trade-offs.

### Objectives:
1. Implement a federated learning pipeline (Flower) with simulated hospital clients and a central aggregator.
2. Add privacy guarantees: secure aggregation and client-side differential privacy (DP).
3. Provide a React frontend for researchers/hospitals and demonstrate a full purchase-and-deliver workflow.
4. Evaluate the system: ML utility vs DP, latency/costs, and gas/communication overheads.

---

## 4. Scope (Must-Have vs. Optional)
**Must-Have (Deliver by Inspection):**
* FL simulation with 3–7 hospital clients (Flower + PyTorch).
* Secure aggregation (library or simple secret-sharing prototype).
* Differential Privacy on client updates (Opacus or TF Privacy).
* Node.js service to interact with smart contracts and orchestrate a simple off-chain aggregator.
* React dashboard showing task lifecycle, commitments, and model metrics.
* Synthetic/public non-sensitive datasets only (approx. 1000 rows).
* 10-page inspection report and demo.

---

## 5. High-Level Architecture
1. **Researcher** creates a `ModelTask` in the platform’s database.
2. **Hospitals** register and opt-in to the task. Each hospital keeps raw data locally.
3. **FL Round**: Aggregator broadcasts global model; hospitals run local training and compute updates.
4. **On-Chain Commitment**: Each hospital posts a commitment (hash of update + nonce) on-chain (`CommitmentRegistry`).
5. **Update Transfer**: Hospitals send encrypted updates off-chain to aggregator (secure aggregation protocol).
6. **Aggregation**: Aggregator produces aggregated model; publishes model hash/signature. Hospitals validate locally and report metrics.
7. **Settlement**: If validation criteria satisfied, `Reputation` contract updated.
8. **Delivery**: Researcher receives final aggregated model (download link + verification via on-chain model hash).

---

## 6. Technical & Non-Functional Requirements
### Functional Requirements:
* **R1**: Create and fund ModelTask (on-chain).
* **R2**: Register hospitals/nodes (permissioned identities).
* **R3**: Run FL rounds (configurable rounds, local epochs).
* **R4**: Post commitments (hashes) to chain prior to aggregation.
* **R5**: Secure aggregation of encrypted updates.
* **R6**: Deploy robust aggregation strategies.
* **R8**: UI for creating tasks, viewing progress, and managing reputations.

### Non-Functional Requirements:
* **N1**: Raw data never leaves hospital nodes.
* **N2**: Privacy budget (ε) recorded for DP and reported in experiments.
* **N3**: System handle simulated 3–7 clients with reasonable latency (round < 2 minutes).
* **N4**: Smart-contract gas usage minimized (only small hashes/metadata on-chain).
* **N5**: Reproducibility: Reproducible setup and GitLab with clear commit history.

---

## 7. Technical Stack
* **Federated Learning**: Python 3.10+, Flower (flwr), PyTorch, Opacus.
* **Backend**: Node.js (Express), Python microservice for aggregation.
* **Frontend**: React.js (Vite), MetaMask integration, Chart.js.
* **Dev Tooling**: GitLab, Ganache/Hardhat for Ethereum simulation.

---

## 8. Implementation Plan (15 Weeks)
* **Weeks 1–2**: Design & Setup.
* **Weeks 3–5**: FL Baseline (FedAvg) and convergence plots.
* **Weeks 6–7**: Privacy Primitives (DP & Secure Aggregation prototype).
* **Weeks 8–9**: Robustness (Krum, Trimmed Mean, Poisoning Attacks).
* **Weeks 10–11**: Smart Contracts & Marketplace (Solidity/Ganache).
* **Week 12**: Integration (E2E Pipeline).
* **Week 13**: Frontend Dashboard.
* **Week 14**: Final Evaluation & Scaling Tests.
* **Week 15**: Final 10-page Report & Demo.

---

## 9. Evaluation & Success Criteria
* **ML & Privacy**: Final accuracy vs. centralized baseline; Privacy ε value and Membership Inference (MI) scores.
* **Security**: Model degradation under poisoning (FedAvg vs. Robust); Detection/False-Positive rates.
* **Performance**: Round latency, communication overhead (MB), and gas costs per commitment.

---

## 10. Ethics & Legal
* Use only synthetic or openly licensed datasets.
* Document DP parameters and provide rationale for privacy levels.
* Include an Ethics section in the report detailing data handling protections.

---

## 11. Risks & Mitigation
* **Complexity**: Fallback to simple secret-sharing if libraries fail.
* **Utility Loss**: Tune ε carefully and report trade-offs honestly.
* **Contract Risks**: Keep on-chain logic minimal and test heavily in Ganache.

---

## 12. Deliverables
1. GitLab repo with code and commit history.
2. Deployed smart contracts + interaction scripts.
3. FL scripts and model artifacts.
4. React UI Dashboard.
5. Evaluation results & plots.
6. 10-page inspection report.

---

## 13. Plan-vs-Execution Audit (Outcome Defense)
*Note: This section documents how the project evolved from the initial proposal to the final high-fidelity system submitted in March 2026.*

| Proposal Item | Final Outcome (MedShare-FL) | Thesis Rationale |
| :--- | :--- | :--- |
| **Datasets**: Synthetic 1,000 rows | **Real-World 253,680 records** (CDC) | Escalated complexity to test true GPU scalability and 'Large Data' noise cancellation. |
| **Defense**: Simple Krum / Trimmed Mean | **Robust-MAD (Hampel Influence)** | Krum requires a fixed $f$ (attacker count); Robust-MAD handles unknown $f$ levels. |
| **Report**: 10 Pages (Minimum) | **22+ Technical Pages** | Expanded to include "SHAP Explainability" and "Membership Inference" privacy audits. |
| **Aggregation**: Simple Prototype | **Differential Privacy Equilibrium** | Implemented true noise-robustness boundaries rather than a toy average. |

**The "Outcome" Defense Script:**
> *"We originally planned for a toy prototype with 1,000 rows, but the final MedShare-FL system scaled to a 253,000-record clinical dataset and implemented a high-breakdown-point Robust-MAD (Hampel) filter. This transition from proof-of-concept to a scientifically robust marketplace is my primary technical contribution."*
