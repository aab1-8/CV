import json
import os

notebook_path = r'c:\Users\bhuva\bxp267\MedShare_FINAL_new.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Define the new cells
new_cells = [
    {
        "cell_type": "markdown",
        "metadata": {"id": "phase2_header"},
        "source": [
            "## 🚀 PHASE 2: REMAINING AUDITS (DP, Robustness, Latency)\n",
            "\n",
            "This phase executes the remaining 3 experimental tests to complete the full 5-test data audit for **admin_billing**.\n",
            "\n",
            "| Test | Description | Efficiency |\n",
            "| :--- | :--- | :--- |\n",
            "| **Test 2: DP Sweep** | Accuracy vs Privacy Trade-off | 100 Rounds |\n",
            "| **Test 3: Robustness** | Defense against Malicious Attacks | 100 Rounds |\n",
            "| **Test 4: Latency & Gas** | Blockchain Economy | 10 Rounds |\n"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "test2_dp"},
        "outputs": [],
        "source": [
            "# TEST 2: DP SWEEP (Privacy-Utility Tradeoff)\n",
            "!python federated_survival.py --experiment dp --dataset admin_billing --rounds 100 --batch_size 256 --lr 0.0005 --enable_blockchain True"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "test3_robustness"},
        "outputs": [],
        "source": [
            "# TEST 3: ROBUSTNESS (Defense Audit)\n",
            "!python federated_survival.py --experiment robustness --dataset admin_billing --rounds 100 --batch_size 256 --lr 0.0005 --enable_blockchain True"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "test4_latency"},
        "outputs": [],
        "source": [
            "# TEST 4: LATENCY & GAS (Blockchain Efficiency)\n",
            "!python federated_survival.py --experiment latency --dataset admin_billing --rounds 10 --batch_size 256 --lr 0.0005 --enable_blockchain True"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {"id": "phase3_header"},
        "source": [
            "## 📊 PHASE 3: FINAL PLOTTING & VERIFICATION\n",
            "\n",
            "Once all CSV files are ready (MI, DP, Robustness, Latency), run this to generate the final 5 verification plots."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "test5_plotting"},
        "outputs": [],
        "source": [
            "# TEST 5: FINAL PLOTTING\n",
            "!python test/plot_results.py"
        ]
    }
]

# Append new cells
nb['cells'].extend(new_cells)

# Write back
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("✅ Successfully appended 4 tests to MedShare_FINAL_new.ipynb")
