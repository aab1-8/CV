# MedShare: Privacy-Preserving Federated Learning for Healthcare

A blockchain-audited federated learning system for collaborative medical AI training across hospitals without sharing raw patient data.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for Ganache blockchain)

### Installation
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

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
├── blockchain_service.py     # Smart contract interface
├── deploy_colab.py           # Contract deployment script
├── requirements.txt          # Python dependencies
│
├── contracts/                # Solidity smart contracts
│   ├── MedShareTask.sol      # Research task & bounty management
│   └── CommitmentRegistry.sol # Audit trail for model updates
│
├── build/                    # Compiled contracts & deployment info
│   └── deploy_info.json      # Contract addresses
│
├── frontend/                 # Vite dashboard for visualization
│   ├── index.html
│   └── src/
│
├── test/                     # Benchmark results & plotting
│   ├── plot_results.py       # Generate visualization charts
│   ├── exp_*.csv             # Experiment results (generated)
│   └── fig_*.png             # Plots (generated)
│
├── docs/                     # Documentation & diagrams
│   ├── medshare_use_case.md
│   ├── secagg_vs_robustness_tradeoff.md
│   └── *.png                 # Architecture diagrams
│
└── MedShare_FINAL.ipynb      # Google Colab notebook
```

## 🔐 Security Features

| Feature | Description |
|---------|-------------|
| **Differential Privacy** | Opacus-based gradient clipping and noise injection |
| **Secure Aggregation** | Pairwise masking to hide individual updates |
| **Byzantine Robustness** | TrimmedMean, FedMedian, Krum defenses |
| **Blockchain Audit** | Immutable commitment registry for all updates |
| **Anomaly Detection** | Real-time monitoring for poisoning attacks |

## 📈 Available Datasets

- `support2` - SUPPORT2 Clinical Study (mortality prediction)
- `cdc_diabetes` - CDC Diabetes Health Indicators
- `stroke_prediction` - Stroke Prediction Dataset
- `diabetes_hospital` - Diabetes 130-US Hospitals

## 🖥️ Dashboard

Start the visualization dashboard:
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` to view training metrics and security audits.

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Configuration Guide](docs/config_guide.md)
- [Security Trade-offs](docs/secagg_vs_robustness_tradeoff.md)
- [Colab Setup](docs/colab_setup.md)

## 🛠️ Technologies

- **Federated Learning**: Flower (flwr)
- **Deep Learning**: PyTorch
- **Privacy**: Opacus (Differential Privacy)
- **Blockchain**: Solidity, Web3.py, Ganache
- **Frontend**: Vite, Chart.js

## 📝 License

MIT License - See LICENSE file for details.