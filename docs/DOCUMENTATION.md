# 🏥 MedShare: Federated Learning Clinical Dashboard
### **Master Technical Demonstrator & User Guide (MSc Thesis Edition)**

The **MedShare Dashboard** is a high-fidelity interactive demonstrator designed to visualize the entire lifecycle of a **Privacy-Preserving Federated Learning (FL)** study. It bridges the gap between complex cryptographic training and real-world clinical governance.

---

## **🎯 I. Why This Dashboard Context Matters**
In traditional medical research, data is pooled centrally, creating **massive privacy risks.** 
**The MedShare Solution:** This dashboard proves that we can train high-accuracy models (e.g., our **38.9% Accuracy Diabetes Run**) without the data ever leaving the hospital’s firewall.

### **Core Pillars:**
1.  **Data Sovereignty**: Prove that hospitals maintain 100% control of their records.
2.  **Economic Incentive**: Use the **Ethereum Bounty System** to reward participation.
3.  **Auditable Science**: Provide real-time accuracy and "Epsilon" (Privacy Leakage) metrics to satisfy clinical auditors.

---

## **🏗️ II. The Three-View Architecture**

### **1. 📊 The Researcher Marketplace**
The hub where studies are commissioned with specific **Bounties** and **Model Requirements.**

### **2. 🏥 The Hospital View**
The secure portal where nodes link local clinical datasets and perform **Local Training Handshakes.**

### **3. 📈 The Global Analytics Audit**
The scoreboard showing real-world results, **Differential Privacy (DP)** metrics, and **Security Grid** data.

---

## **🎯 III. THE USER JOURNEYS (Step-by-Step)**

### **A. Researcher Creation (Marketplace)**
1.  **Data Topic**: Selects the specific dataset requirement (e.g., "Diabetes Study").
2.  **Hospital Requirement**: Specifies the minimum number of medical centers (nodes) needed.
3.  **Model Selection**: Chooses the architecture (e.g., **MLP**, **CNN**, or **XGBoost**).
4.  **Incentivization (The Bounty)**: 
    *   The researcher inputs a **Total ETH Bounty** (e.g., 15 ETH).
    *   The system automatically splits this bounty among successful nodes.
    *   **Logic**: Each hospital receives `Total Bounty / Hospitals Needed` upon delivery.

### **B. Hospital Participation & Security**
1.  **Secure Linking**:
    *   The hospital selects its **Local Dataset** (Diabetes, Stroke, Heart) from the dropdown.
    *   **Privacy Guarantee**: The dashboard performs a **local-only handshake.** The raw dataset **stays behind the hospital firewall** and is never uploaded.
2.  **Local Training (The Handshake)**:
    *   Triggered by the **"Link & Participate"** button.
    *   Observation: **"🧪 Training Securely..."** animation (1.5s delay).
3.  **Model Submission**: Only the resulting weights & accuracy are sent to the aggregator—patient records remain inaccessible to the researcher.

### **C. Audit & Asset Retrieval**
1.  **Historical Audit Switcher**: Auditors can switch between old audit JSONs (Thyroid, Maternal Health) to verify historical integrity.
2.  **Asset Portal**: Once 100% full, the researcher retrieves the **Aggregated Weights (.pth)** and the **38.9% Accuracy Ceremony.**

---

## **💻 IV. Technical "Special Sauce" Highlights**

### **⚡ Chart Destruction (Anti-Ghosting)**
To prevent "Ghosting" (stuck data points), the **`renderWithCleanup`** helper kills the previous Chart.js instance before drawing new data, ensuring perfectly crisp updates.

### **⛓️ "Demonstrator Mode" Fail-Safe**
During the demo, if the blockchain is offline, the dashboard enters **Demonstrator Mode**, generating **MOCKED** Transaction hashes to prevent presentation interruptions.

### **🛡️ Security Validation**
The dashboard enforces guardrails: Participation is **blocked** if no local dataset is linked, enforcing the "Data locality" narrative during the viva.

---

**This system confirms the project's commitment to Data Locality and Secure Clinical Research.** 🎓📊🚀
