# MedShare-FL: Live Demonstration Script

*This document outlines the exact, step-by-step procedure to execute a flawless live demonstration of the MedShare-FL platform for your MEng examiners. Keep this sheet open alongside your terminals.*

---

## **Phase 1: Environment Initialization (Pre-Demo)**
Before the examiners arrive, ensure your backend infrastructure is fully booted and wiped clean.

1. **Start the Ganache Blockchain Server:**
   Open a new terminal in your project directory (e.g., `bxp267`) and run:
   ```bash
   npx -y ganache --port 8545 --accounts 10 --gasLimit 6721975 --mnemonic "test test test test test test test test test test test junk"
   ```
   *(Leave this terminal visible on the side. The examiners will love seeing the Ethereum transactions stream in real-time.)*

2. **Deploy the Smart Contracts:**
   Open a **second** terminal and run the deployment script to push your Solidity code to Ganache:
   ```bash
   python scripts/deploy_colab.py
   ```

3. **Start the Dashboard:**
   In the **same second terminal** (or a third), start the Vite UI server:
   ```bash
   cd frontend
   npm run dev
   ```

4. **Wipe Browser Memory (Safety Check):**
   * Open `http://localhost:5173/` in your browser.
   * Scroll to the very bottom and click: **"Developer: Clear Local Simulation Progress"**
   * Click **"Reset Everything"** on the popup.
   * Your dashboard will reload and be 100% mathematically clean.

---

## **Phase 2: The Live Demonstration (Examiner Present)**

### **Step 1: Launch the Federated AI Engine**
Tell the examiners: *"I am now going to launch a federated training run across 8 isolated nodes, secured by an Ethereum Smart Contract."*
* Open a terminal containing your python environment and run:
  ```bash
  python federated_survival.py --enable_blockchain True --rounds 3 --epochs 1
  ```
* **What happens:** The script will initialize your dataset, post the Escrow Transaction of **0.05 ETH** to the blockchain, securely join 7 of the 8 nodes autonomously, and print a massive `🚨 DEMO PAUSE 🚨` message. 
* Tell the examiners: *"The AI engine has intentionally frozen itself. It is waiting for the 8th participant (our Hospital Dashboard) to manually sign the legal Smart Contract using the UI."*

### **Step 2: Execute the Dashboard Handshake**
* Navigate to your **Frontend Dashboard window**.
* You will instantly see the new **"TRAIN SUPPORT2-DEATH"** Study task appear dynamically from the blockchain.
* Expand the **Active Dataset Link** dropdown under "Your Hospital" and select: **"Heart Disease / SUPPORT2 (Survival)"**.
* Click the green **`🔗 Link & Participate`** button on the `SUPPORT2` task card.
* Click **OK** on the handshake confirmation.
* Tell the examiners: *"I have just cryptographically signed the data commitment. Let’s look back at the terminal."*

### **Step 3: Watch the Engine Evaluate**
* Immediately open your Python Terminal.
* You will see that the script has automatically detected your handshake and **resumed training!** 
* Tell the examiners: *"Because this is the official evaluation set, my engine has dynamically overridden the default 3 rounds and escalated to 50 mathematical rounds to ensure strict convergence. It takes about 45 seconds."*
* Let the 50 rounds complete. At Round 50, you will see it execute `completeTask()` and close itself.

### **Step 4: Claim the 0.0063 ETH Reward**
* Navigate back to the **Frontend Dashboard**.
* Click **`↻ Refresh`** on your browser.
* Point to your Hospital Earnings. The `0.000` balance has instantly skyrocketed to **`0.0063 ETH`**.
* The **`🔗 Claim Reward`** button is now unlocked!
* Explain the math: *"The contract held a rigid 0.05 ETH. Because 8 nodes contributed honestly, 0.05 split 8 ways equals 0.00625. Our dashboard perfectly detected the 0.0063 ETH allocation directly from the Ethereum state."*

### **Step 5: Inspect Final Assets**
* Point to the Request Card. It now proudly displays **"FINALIZED"** and **"STUDY FULFILLED"**.
* Click the blue **"📊 View Study Assets"** button to proudly show the final Global Model weights and audit parameters!

**End of Demo!** 🎉
