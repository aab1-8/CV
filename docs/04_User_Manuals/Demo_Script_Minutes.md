# MedShare-FL: Minute-by-Minute Demo Script (Outstanding 80-100% Target)

## Phase 1: The Vision & The "Reliability Gap" (Minutes 1-2)
*   **Action**: Open the **Dashboard** (`localhost:5173`) and the **Final Report** (`MEng_Final_Report_v2.tex`).
*   **Narrative**: "My project, **MedShare-FL**, addresses the **Reliability Gap** in medical AI. While Federated Learning is theoretically private, real-world implementations suffer from two things: **Byzantine Corruption** (malicious hospitals) and **Privacy-Utility Trade-offs** (accuracy loss)."
*   **Key Phrase**: *"I didn't just build a model; I built a decentralized marketplace with an immutable audit trail."*

## Phase 2: Live Metrics & "Privacy-Utility Harmony" (Minutes 3-4)
*   **Action**: Show the Dashboard’s **Accuracy vs. Baseline** chart. Highlight the **38.9% Federated Accuracy** vs. **39.7% Centralized**.
*   **Narrative**: "As you can see on the dashboard, we achieve nearly centralized-level performance. However, we do so with a **Privacy Epsilon of 0.72**. This is possible because I utilized the **Moments Accountant** for tighter privacy tracking than the standard composition theorem."
*   **Key Section**: Point to **Section 1.3** in the report (Summary of Contributions).

## Phase 3: The Defensive Defense (Byzantine Robustness) (Minutes 5-7)
*   **Action**: Open `medshare/strategy.py` at **Line 60**. 
*   **Narrative**: "A core innovation is my **Robust-MAD** defense. Standard FedAvg averages everything, meaning one malicious hospital can ruin the global model. My **Hampel Filter** (Line 60) calculates the **Median Absolute Deviation** of the updates. If a node's gradient norm is beyond **Median + 3*MAD**, we reject it and dock its reputation on-chain."
*   **Key Interaction**: Show the **Reputation penalty (-10 points)** logic on **Line 83**.

## Phase 4: Clinical Fairness & Technical Depth (Minutes 8-9)
*   **Action**: Open the **MASTER_FILE_MANIFEST.md** and point to the **SMOTE** logic.
*   **Narrative**: "Medical data is often imbalanced. If a disease is rare, the model will ignore it. I implemented **SMOTE** (Synthetic Minority Over-sampling) in `data.py` to synthetically balance minority diagnostic classes, increasing my recall on the **Thyroid dataset** from **72% to 92.1%**."
*   **Key Term**: *"This ensures clinical fairness across the marketplace."*

## Phase 5: The "Birmingham" Ownership Defense (Minute 10)
*   **Action**: Show the **10-page report**'s Bibliography and the **Verifiable DOI links**.
*   **Narrative**: "Finally, this project includes a complete **Ethereum-based Audit Trail**. Every update is hashed and committed on-chain. My report maps every technical claim to a specific file in my repository, ensuring complete auditability and ownership."
*   **Final Word**: *"I'm ready for your technical questions."*

---

## 🛑 Inspector "Trap" Questions (And how to answer them):
1.  **"Why didn't you use CNNs?"**: *"CNNs are for images. My core audit focused on **survival and prognosis prediction** using tabular hospital data (SUPPORT2, CDC), where MLPs and FedProx are the state-of-the-art for tabular interpretability."*
2.  **"Is this GDPR compliant?"**: *"Yes. By utilizing Differential Privacy (DP), I ensure **Membership Inference Resilience**, satisfying GDPR Article 32 regarding the security of personal data processing."*
3.  **"What happens if the Blockchain is down?"**: *"The system operates in **Autonomous Mode**. It continues training locally, but model rewards and reputation are queued until the network synchronizes, ensuring no loss of diagnostic progress."*
