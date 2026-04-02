# MedShare: Elite Privacy-Preserving Federated Learning for Healthcare (MEng Final Audit)

**Status: 🏆 PLATINUM / FULLY VERIFIED (2026)**
A blockchain-audited, Byzantine-robust federated learning system for collaborative medical AI training across hospitals without sharing raw patient data.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for Ganache blockchain)

### Installation
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running a Simulation
```bash
# Start local blockchain (required for audit logging)
npx ganache --port 8546 --mnemonic "exit taxi picnic regret brush gold vacant dignity book enable left divorce"

# Run federated learning simulation
python federated_survival.py --dataset support2 --rounds 5 --epochs 2
```

### Running Benchmark Experiments
```bash
# Differential Privacy trade-off
python federated_survival.py --experiment dp --dataset support2 --epochs 2 --sample_size 2000

# Robustness against poisoning attacks
python federated_survival.py --experiment robustness --dataset support2 --epochs 2 --sample_size 2000

# Latency scaling
python federated_survival.py --experiment latency --dataset support2 --epochs 2 --sample_size 2000

# Membership Inference (Privacy)
python federated_survival.py --experiment mi --dataset support2 --epochs 2 --sample_size 2000

# Blockchain Gas Cost Analysis
python federated_survival.py --experiment gas --dataset support2 --epochs 2 --sample_size 2000

# Generate plots
python test/plot_results.py
```

## 📊 Project Structure

```
bxp267/
├── federated_survival.py     # Main FL simulation engine
├── medshare/                 # Core logic module (Modernized)
│   ├── blockchain.py         # Smart contract interface
│   ├── strategy.py           # Anomaly monitoring & defenses
│   ├── engine.py             # PyTorch training/testing loops
│   ├── client.py             # Flower client implementation
│   └── data.py               # Dataset handlers & partitioning
│
├── contracts/                # Solidity smart contracts
├── build/                    # Compiled artifacts & deploy addresses
├── frontend/                 # Vite dashboard for visualization
├── test/                     # Benchmark results & plotting
├── docs/                     # Documentation & diagrams
│   └── MEng_Final_Report_v2.tex      # 📄 MASTER INSPECTION REPORT (LaTeX)
│
└── MedShare_FINAL_new.ipynb  # Google Colab notebook
```

## 🔐 Security Features

| Feature | Description |
|---------|-------------|
| **Differential Privacy** | Opacus-based gradient clipping and noise injection (RDP) |
| **FedProx Stability** | Proximal term (mu=0.01) to prevent client drift under noise |
| **Byzantine Robustness** | `Robust-MAD` defense against poisonous outliers |
| **Blockchain Audit** | Immutable SHA-256 commitment registry (Commit-then-Submit) |
| **Secure Aggregation** | Symmetric Pairwise Masking (SOTA Protocol) |

## 📈 Available Datasets

- `support2` - SUPPORT2 Clinical Study (mortality)
- `support2_disease` - SUPPORT2 Multi-class (disease group prediction)
- `cdc_diabetes_binary` - CDC Diabetes Health Indicators (Binary)
- `cdc_diabetes_012` - CDC Diabetes Multi-class (0/1/2)
- `thyroid` - Thyroid Disease (Multi-class)
- `diabetes_hospital` - Diabetes 130-US Hospitals (Readmission risk)
- `maternal_health` - Maternal Health Risk (Multi-class)
- `stroke_prediction` - Stroke Prediction (with SMOTE rebalancing)
- `admin_billing` - Synthetic Admin Risk (Billing level)
- `admin_category` - Hospital Administrative Categories

## 🖥️ Dashboard

Start the visualization dashboard:
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` to view training metrics, gas costs, and security audits.

## 📚 Documentation

- [**MEng Final Project Report (Master)**](docs/01_Foundation/MEng_Final_Report_v2.tex)
- [Architecture Overview](docs/01_Foundation/Discovery_And_Drafts/System_Overview.md)
- [Configuration Guide](docs/01_Foundation/Discovery_And_Drafts/Master_File_Manifest.md)
- [Project Verification (Final Audit)](docs/01_Foundation/Discovery_And_Drafts/Project_State_Verification.md)
- [Security Trade-offs & Critical Decisions](docs/01_Foundation/MEng_Final_Report_v2.tex#L344)

## 🛠️ Technologies

- **Federated Learning**: Flower (flwr)
- **Deep Learning**: PyTorch
- **Privacy**: Opacus (Differential Privacy)
- **Blockchain**: Solidity, Web3.py, Ganache (Local Ethereum)
- **Frontend**: Vite, Vanilla JS, CSS3, Chart.js

## 📝 Credits & Development
Developed as part of an MEng Computer Science Final Project (2025-26).