import json
import os

path = 'c:/Users/bhuva/bxp267/MedShare_FINAL_new.ipynb'

def update_notebook():
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        try:
            nb = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to parse JSON: {e}")
            return

    found = False
    for cell in nb['cells']:
        cell_id = cell.get('metadata', {}).get('id')
        if cell_id == 'experiment_suite':
            cell['source'] = [
                "## 🛸 PHASE 2: SYSTEM EXPERIMENTS (Maternal Health Gold Standard)\n",
                "# This run executes the definitive audit for the dissertation.\n",
                "\n",
                "import subprocess\n",
                "\n",
                "# Gold Standard configuration for 50 Rounds / 50 Epochs / Multiple Sigmas\n",
                "configs = [\n",
                "    {\"sigma\": 0.0, \"rounds\": 50, \"epochs\": 50, \"batch\": 128, \"dataset\": \"maternal_health\", \"tag\": \"Baseline (No Privacy)\"},\n",
                "    {\"sigma\": 0.05, \"rounds\": 50, \"epochs\": 50, \"batch\": 128, \"dataset\": \"maternal_health\", \"tag\": \"DP (0.05 Sigma)\"},\n",
                "    {\"sigma\": 0.1, \"rounds\": 50, \"epochs\": 50, \"batch\": 128, \"dataset\": \"maternal_health\", \"tag\": \"DP (0.1 Sigma)\"},\n",
                "    {\"sigma\": 0.2, \"rounds\": 50, \"epochs\": 50, \"batch\": 128, \"dataset\": \"maternal_health\", \"tag\": \"DP (0.2 Sigma)\"},\n",
                "    {\"sigma\": 0.3, \"rounds\": 50, \"epochs\": 50, \"batch\": 128, \"dataset\": \"maternal_health\", \"tag\": \"DP (0.3 Sigma)\"},\n",
                "    {\"sigma\": 0.5, \"rounds\": 50, \"epochs\": 50, \"batch\": 128, \"dataset\": \"maternal_health\", \"tag\": \"DP (0.5 Sigma)\"}\n",
                "]\n",
                "\n",
                "print(\"🚀 STARTING GOLD STANDARD AUDIT: Maternal Health Benchmark\")\n",
                "print(\"=\"*70)\n",
                "\n",
                "for cfg in configs:\n",
                "    print(f\"\\n[AUDIT] Running: {cfg['tag']} | Sigma: {cfg['sigma']}\")\n",
                "    cmd = [\n",
                "        \"python\", \"federated_survival.py\",\n",
                "        \"--experiment\", \"mi\",\n",
                "        \"--dataset\", cfg['dataset'],\n",
                "        \"--rounds\", str(cfg['rounds']),\n",
                "        \"--epochs\", str(cfg['epochs']),\n",
                "        \"--batch_size\", str(cfg['batch']),\n",
                "        \"--sigma\", str(cfg['sigma']),\n",
                "        \"--enable_blockchain\", \"True\"\n",
                "    ]\n",
                "    subprocess.run(cmd)\n",
                "\n",
                "print(\"\\n\" + \"=\"*70)\n",
                "print(\"🏆 GOLD STANDARD AUDIT COMPLETE: Check docs/assets/maternal_health/ for final results.\")\n",
                "print(\"=\"*70)"
            ]
            cell['outputs'] = []
            cell['execution_count'] = None
            found = True
            break

    if found:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("SUCCESS: Experiment Suite cell updated with Blockchain functionality.")
    else:
        print("ERROR: Cell ID 'experiment_suite' not found.")

if __name__ == '__main__':
    update_notebook()
