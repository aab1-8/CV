# Problem Resolution & Technical Debugging Log

## 🟢 2026-03-18: vLab PATH Corruption Fix
*   **The Problem**: The user encountered `bash: ls: command not found` and `npm ERR! code ENOENT` after running the environment setup. This happened because the "Mega-Command" in the guide incorrectly escaped the search path (`\$PATH`), causing the shell to lose all system command locations.
*   **The Solution**: 
    1.  Restored the session PATH manually: `export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin`.
    2.  Fixed the `VLAB_GUIDE.md` (Line 12) to use `$PATH` properly.
*   **Verification**: All system tools (`ls`, `cat`, `hardhat`) are now functional in the interactive terminal.

This document chronicles the technical challenges encountered during the setup of the 253,680-record CDC Diabetes audit on the vLab GPU environment and the specific engineering solutions implemented to resolve them.

## 1. Environment: Incompatible System Libraries (Glibc Error)
*   **The Problem**: The vLab (Amazon Linux 2) uses `glibc 2.26`. Modern Node.js versions (v18, v20+) and the standard `yum` installers require `glibc 2.28+`, causing a fatal "Library not found" error during the blockchain setup.
*   **The Solution**: We bypassed the system package manager entirely by downloading a **Portable Node.js v14.21.3 Binary**. By extracting this to the home directory and manually updating the session `$PATH`, we successfully enabled the `ganache` audit chain without requiring a system-level OS upgrade.

## 2. Infrastructure: Virtual Environment & Pathing Conflicts
*   **The Problem**: The initial background sweep was launched from the parent `work/` directory without the Python virtual environment (`venv`) activated. This led to immediate crashes (PID 17479) because the system-level Python lacked the required MedShare dependencies (`flwr`, `opacus`, `torch`).
*   **The Solution**: We utilized `ps aux` to identify the faulty process, terminated it with `kill`, and performed a **"Deep Context Switch"**:
    1.  Navigated specifically into the project root (`cd bxp267`).
    2.  Explicitly activated the isolated research environment (`source venv/bin/activate`).
    3.  Restarted the sweep (PID 17913), which then successfully found all clinical data and GPU libraries.

## 3. Stability: GPU Memory Management (OOM Prevention)
*   **The Problem**: Training a multi-class model on 253,680 records with Differential Privacy (DP) creates a massive memory footprint. DP "Gradient Clipping" tracks individual patient gradients, which typically doubles the required VRAM, risking an "Out of Memory" (OOM) crash on the 15GB Tesla T4.
*   **The Solution**: We implemented a **"Safety Barrier" configuration**:
    *   **Batch Size Scaling**: Locked the batch size to **2,048**. This is small enough to fit within a 6GB "Active Buffer" but large enough to provide a stable medical "Signal."
    *   **Host-Side SMOTE**: Moved the dataset rebalancing (SMOTE) to the system RAM to preserve the GPU's memory exclusively for active backpropagation.

## 4. Research Alignment: Adaptive Configuration Mismatch
*   **The Problem**: The project's `get_adaptive_experiment_config` logic was using a 50,000-row threshold and a standard set of sigmas ($\sigma = [0.25, 1.0, 1.5, ...]$), which did not match the user's specific research requirements for the massive CDC dataset audit.
*   **The Solution**: We permanently modified the `federated_survival.py` file to:
    1.  Increase the "Massive" threshold to **70,000 rows**.
    2.  Hard-code the exact research range: **$\sigma = [0.0, 0.5, 1.0, 2.0, 5.0]$**.
    3.  Set the epochs to **20** to ensure high-fidelity convergence on the CDC data.

## 5. Data Access: Missing Clinical API Libraries
*   **The Problem**: The vLab was missing the specific APIs needed to pull real-world data from the UCI and Kaggle repositories.
*   **The Solution**: We performed a targeted dependency patch, installing `ucimlrepo`, `kagglehub`, and `imbalanced-learn`. This ensured the audit uses **real patient data**, not simulated "dummy" records.
