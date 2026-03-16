# vLab High-Performance Execution Guide (Zero-Loss Protocol)

Use this guide to ensure that results from long-running (2.5hr+) vLab experiments are never lost.

## 1. Fresh Session Setup (The "One-Shot" Protocol)
Whenever you start a new vLab instance, copy and paste this **Mega-Command** to restore everything (Libraries, Node 16, GPU, and Blockchain) in one go:

```bash
cd /jupyter/work/bxp267 && \
source venv/bin/activate && \
pip install -r requirements.txt && \
wget -nc https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz && \
tar -xJf node-v16.20.2-linux-x64.tar.xz --skip-old-files && \
export PATH=$(pwd)/node-v16.20.2-linux-x64/bin:\$PATH && \
npm install hardhat@2.19.4 --save-dev && \
npx hardhat compile && \
mkdir -p build && cp artifacts/contracts/*/*.json build/ 2>/dev/null && \
python -c "import torch, flwr; print('✅ System: READY')" && \
python -c "import torch; print('✅ GPU: ' + torch.cuda.get_device_name(0))" && \
echo "🚀 VLAB ENVIRONMENT FULLY RESTORED"
```

---

### Alternate: Step-by-Step Manual Setup

### Step A: Enter Project & Activate
```bash
cd ~/bxp267
source venv/bin/activate

# Ensure Git is configured for the session
git config --global user.email "your-email@example.com"
git config --global user.name "Bh"

# Install dependencies (If fresh session)
pip install -r requirements.txt
```
vLab's default Node is too old. We use Node 16 for stability:
```bash
# 1. Download & Extract Node 16 (Only needed once per session)
wget -nc https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz
tar -xJf node-v16.20.2-linux-x64.tar.xz
export PATH=$(pwd)/node-v16.20.2-linux-x64/bin:$PATH

# 2. Sync Configuration (CommonJS for Node 16 compatibility)
cat <<EOF > hardhat.config.cjs
module.exports = {
    solidity: "0.8.20",
    paths: { sources: "./contracts", artifacts: "./artifacts" }
};
EOF

# 3. Build & Sync Artifacts (Creates 'build/' folder for deployment)
npm install hardhat@2.19.4 --save-dev
npx hardhat compile
mkdir -p build
cp artifacts/contracts/MedShareTask.sol/MedShareTask.json build/
cp artifacts/contracts/CommitmentRegistry.sol/CommitmentRegistry.json build/
cp artifacts/contracts/Reputation.sol/Reputation.json build/
echo "✅ Infrastructure Ready"
```

## 1.1 System Health Check (The Integrity Protocol)
Run these commands to verify the vLab environment before launching tests:

### A. Process & Memory Check
Check for "zombie" processes from previous sessions:
```bash
ps aux | grep -E "python|ganache|ray"
# If old sessions exist, clear them:
pkill -9 -f "ray|ganache"
```

### B. Dependency Verification
Verify Python libraries, GPU acceleration, and Blockchain engine:
```bash
# Combined check command
python -c "import torch, flwr, opacus, web3; print('✅ Python Libraries: OK')" && \
python -c "import torch; print('✅ GPU Detection: ' + torch.cuda.get_device_name(0))" && \
npx ganache --version && echo "✅ Blockchain Engine: OK"
```

## 1.2 Monitoring Progress (The "Live View")
Use these commands while an experiment is running to ensure it's healthy:

### A. Watch the GPU
```bash
# Updates every 1 second (Look for 'python' using memory)
watch -n 1 nvidia-smi
```

### B. Watch the Logs
```bash
# Stream the audit results as they happen
tail -f admin_billing_test.log
```

## 2. Running Experiments (Background Mode)
Use `nohup` so the experiment continues even if your browser/internet crashes.

### Step A: Start & Deploy Blockchain
```bash
# 1. Start Ganache
npx ganache --wallet.seed federated --port 8545 --gasLimit 10000000 > ganache.log 2>&1 &

# 2. Deploy Contracts
python scripts/deploy_colab.py
```

### Step B: Launch Audit (Single Category)
```bash
# Example: MI Audit for Admin Billing
nohup python federated_survival.py --experiment mi --dataset admin_billing --enable_blockchain True --enable_dp True > admin_billing_mi.log 2>&1 &
```

## 2.1 The "Master Dataset Audit" (Full 5-Test Suite)
Use this command to run **everything** (MI, DP, Robustness, Latency, and Plotting) in one go. Ideal for finalizing a dataset for your report.

```bash
# 1. Reset & Start Blockchain
pkill -9 -f "ganache"
npx ganache --wallet.seed federated --port 8545 --gasLimit 10000000 > ganache.log 2>&1 &
sleep 5 && python scripts/deploy_colab.py

# 2. Launch Sequentially (approx 2-3 hours)
nohup bash -c " \
python federated_survival.py --experiment mi --dataset admin_billing --enable_blockchain True --enable_dp True && \
python federated_survival.py --experiment dp --dataset admin_billing --enable_blockchain True && \
python federated_survival.py --experiment robustness --dataset admin_billing --enable_blockchain True && \
python federated_survival.py --experiment latency --dataset admin_billing --enable_blockchain True && \
python test/plot_results.py " > full_audit.log 2>&1 &
```

## 3. The "Zero-Loss" Shutdown Sequence (CRITICAL)
NEVER close the vLab without running these 4 steps:

### Step A: Final Plotting
Generate the figures while the data is fresh on the vLab disk:
```bash
python test/plot_results.py
```

### Step B: The "Nuclear" Git Add
Force Git to see every result, bypassing any potential ignore rules:
```bash
git add -f test/*.csv test/*.png test/*.json
```

### Step C: The Scientific Commit
```bash
git commit -m "feat: Completed vLab experiment [Dataset Name] [Records Count]"
git push origin main
```

### Step D: Kill Background Processes
Clean up the blockchain/ganache node:
```bash
ps aux | grep ganache | awk '{print $2}' | xargs kill -9
```

## 4. Local Recovery
On your laptop, simply run:
```bash
git pull origin main
# Then regenerate plots locally to verify
python test/plot_results.py
```

---
*Created automatically to protect Bh's 100k-record research milestones.*
