# 🏁 MedShare-FL: Final Demonstration Guide (MSc Inspection)

This guide provides the exact steps to demonstrate the **MedShare-FL Federated Learning Marketplace** to your project markers. It highlights all the advanced "Platinum" security and privacy features you've implemented.

---

## 🛠️ Phase 1. The Marketplace Backbone (Blockchain)
**Goal**: Launch the Ethereum blockchain where all hospitals and researchers will register their audit trails.

1.  Open a terminal and start the **Ganache** local blockchain:
    ```bash
    npx ganache --port 8546 --mnemonic "exit taxi picnic regret brush gold vacant dignity book enable left divorce"
    ```
    *Keep this terminal running.*

---

## 🔬 Phase 2. The Heart of the Project (FL Simulation)
**Goal**: Conduct a federated training session across multiple simulated hospitals.

1.  Open a second terminal and run a standard federated training:
    ```bash
    python federated_survival.py --dataset stroke_prediction --rounds 5 --epochs 2
    ```
2.  **To Demonstrate Secure Aggregation (Requirement R5)**:
    Run the same simulation with cryptographic masking enabled:
    ```bash
    python federated_survival.py --dataset support2 --rounds 3 --enable_secagg True
    ```
3.  **To Demonstrate Byzantine Robustness (Requirement R6)**:
    Run a simulation with 30% malicious clients and the `Robust-MAD` defense:
    ```bash
    python federated_survival.py --experiment robustness --dataset support2 --epochs 2
    ```

---

## 📊 Phase 3. The Security Audit (Analysis)
**Goal**: Generate the professional scientific plots for your report.

1.  Run the plotting suite:
    ```bash
    python test/plot_results.py
    ```
2.  Inspect the outputs in the `test/` folder:
    *   `stress_robustness_chart.png`: Proves that your **Robust-MAD** defense neutralized the attacker.
    *   `stress_dp_tradeoff_chart.png`: Shows the high utility of your **Differential Privacy** implementation.
    *   `stress_mi_audit_chart.png`: Scientifically verifies the privacy protection via **Membership Inference Gap**.

---

## 🖥️ Phase 4. The Final Marketplace Dashboard (UI)
**Goal**: Visualize the hospital reputations and rewards earned on the blockchain.

1.  Navigate to the `frontend/` folder in a new terminal:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
2.  Open the URL provided (e.g., `http://localhost:5173`) in your browser.
3.  **Inspect**:
    *   **The Reputation Scorecard**: See which hospitals gained reputation for high-quality contributions.
    *   **The Reward Summary**: View the ETH bounties distributed to the participating hospitals.

---

## 📄 Final Tip: The Inspection Report
Your full technical and security audit report is available at:
`docs/reports/audit_mar_2026.md`