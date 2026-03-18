import json

notebook_path = r'c:\Users\bhuva\bxp267\MedShare_FINAL_new.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The cell we want to target has the metadata id "experiment_suite" or similar
# Based on previous view_file, it was the cell at index 2 (Phase 2)
# Let's search for the cell containing "PHASE 2: RIGOROUS SCIENTIFIC SWEEP"

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "PHASE 2: RIGOROUS SCIENTIFIC SWEEP" in source or "admin_category" in source:
            new_source = [
                "## 🔬 PHASE 2: GOLD STANDARD SCIENTIFIC SWEEP (Admin-Category)\n",
                "import os\n",
                "print(\"🔥 STARTING 100-ROUND GLOBAL AUDIT (Admin-Category)\")\n",
                "print(\"=\"*70 + \"\\n\")\n",
                "\n",
                "experiments = [\n",
                "    (\"Privacy Audit (Audit Sweep)\", \"mi\", \"admin_category\", 100, 40),\n",
                "    (\"DP Utility Frontier\", \"dp\", \"admin_category\", 100, 20),\n",
                "    (\"Adversarial Robustness\", \"robustness\", \"admin_category\", 100, 20),\n",
                "    (\"System Telemetry (Gas/Latency)\", \"latency\", \"admin_category\", 20, 10)\n",
                "]\n",
                "\n",
                "for label, mode, dataset, rounds, epochs in experiments:\n",
                "    print(f\"\\n🚀 Phase: {label} ({mode}) on {dataset}...\")\n",
                "    !python federated_survival.py --experiment {mode} --dataset {dataset} --rounds {rounds} --epochs {epochs} --enable_dp True --enable_blockchain True\n",
                "\n",
                "print(\"\\n\" + \"=\"*70)\n",
                "print(\"✅ ADMIN-CATEGORY AUDIT COMPLETE\")\n",
                "print(\"=\"*70)"
            ]
            cell['source'] = new_source
            print("Successfully updated experiment config in notebook.")
            break

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
