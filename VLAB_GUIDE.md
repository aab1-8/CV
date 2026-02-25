# vLab High-Performance Execution Guide (Zero-Loss Protocol)

Use this guide to ensure that results from long-running (2.5hr+) vLab experiments are never lost.

## 1. The Startup Sequence
Before starting any experiment, ensure your environment is ready:
```bash
source venv/bin/activate
# Ensure Git knows who you are
git config --global user.email "your-email@example.com"
git config --global user.name "Bhuvan"
```

## 2. Running Experiments (Background Mode)
Use `nohup` so the experiment continues even if your browser/internet crashes:
```bash
# Example: MI Audit for 100k records
nohup python federated_survival.py --experiment mi --dataset diabetes_hospital --rounds 30 --epochs 5 --enable_blockchain True --enable_dp True > simulation.log 2>&1 &
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
*Created automatically to protect Bhuvan's 100k-record research milestones.*
