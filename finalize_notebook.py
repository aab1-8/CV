import json
import os

path = 'c:/Users/bhuva/bxp267/MedShare_FINAL_new.ipynb'

def finalize_all():
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # 1. Update/Inject Phase 2 (Experiment Suite)
    exp_code = [
        "## 🛸 PHASE 2: SYSTEM EXPERIMENTS (Maternal Health Gold Standard)\n",
        "# This run executes the definitive audit for the dissertation.\n",
        "\n",
        "import subprocess\n",
        "\n",
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

    # 2. Update/Inject Phase 4 (Visualization)
    viz_code = [
        "## 📈 PHASE 4: GOLD STANDARD AUDIT VISUALIZATION\n",
        "import pandas as pd, matplotlib.pyplot as plt, os\n",
        "\n",
        "results_path = 'test/exp_mi_results.csv'\n",
        "if not os.path.exists(results_path):\n",
        "    print(\"❌ ERROR: Results not found!\")\n",
        "else:\n",
        "    df = pd.read_csv(results_path).sort_values('noise')\n",
        "    plt.style.use('seaborn-v0_8-whitegrid')\n",
        "    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))\n",
        "    \n",
        "    ax1.plot(df['noise'], df['leakage_acc'], 'o-', label='MI Gap (ACC)', color='#e74c3c', linewidth=2.5)\n",
        "    ax1.plot(df['noise'], df['leakage_auc'], 's--', label='MI Gap (AUC)', color='#3498db', linewidth=2.5)\n",
        "    ax1.set_title(\"🛡️ Privacy Audit: MI Mitigation Efficiency\", fontsize=14, fontweight='bold')\n",
        "    ax1.set_xlabel(\"Privacy Protection Level (Sigma)\")\n",
        "    ax1.legend()\n",
        "    \n",
        "    ax2.plot(df['noise'], df['accuracy'] * 100, 'D-', label='System Accuracy', color='#2ecc71', linewidth=2.5)\n",
        "    ax2.set_title(\"📊 Utility Analysis: Model Accuracy vs Security\", fontsize=14, fontweight='bold')\n",
        "    ax2.set_ylabel(\"Global Federated Accuracy (%)\")\n",
        "    ax2.legend()\n",
        "    \n",
        "    plt.tight_layout()\n",
        "    os.makedirs('docs/assets/maternal_health/', exist_ok=True)\n",
        "    plt.savefig('docs/assets/maternal_health/fig_gold_standard_audit.png', dpi=300)\n",
        "    plt.show()"
    ]

    # Apply changes
    for cell in nb['cells']:
        c_id = cell.get('metadata', {}).get('id')
        if c_id == 'experiment_suite':
            cell['source'] = exp_code
            cell['outputs'] = []
            cell['execution_count'] = None

    # Remove old plot cell if it exists and add fresh at the end
    nb['cells'] = [c for c in nb['cells'] if c.get('metadata', {}).get('id') != 'gold_standard_plotting']
    nb['cells'].append({
        'cell_type': 'code',
        'metadata': {'id': 'gold_standard_plotting'},
        'outputs': [],
        'source': viz_code
    })

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("SUCCESS: Notebook finalized with Gold Standard Audit & Side-by-Side Plots.")

if __name__ == '__main__':
    finalize_all()
