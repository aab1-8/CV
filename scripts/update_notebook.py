import json
import os

notebook_path = r'c:\Users\bhuva\bxp267\MedShare_FINAL.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Define the new cells
header_cell = {
    "cell_type": "markdown",
    "metadata": {"id": "high_fidelity_header"},
    "source": [
        "## 🚀 4. High-Fidelity Master Sweep (Support2 Multi-class)\n",
        "\n",
        "This run uses the **FedProx stabilizer** and **Adaptive Calibration** (50 rounds, increased training intensity).\n",
        "It focuses on the multi-class `support2_disease` dataset to recover ~70% accuracy under DP."
    ]
}

run_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {"id": "high_fidelity_run"},
    "outputs": [],
    "source": [
        "# Run the High-Fidelity Master Sweep for Multi-class Disease Prediction\n",
        "!python federated_survival.py --dataset support2_disease --rounds 50 --epochs 5 --experiment dp"
    ]
}

plot_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {"id": "high_fidelity_plot"},
    "outputs": [],
    "source": [
        "## 📊 5. Generate High-Fidelity Plots\n",
        "!python test/plot_results.py\n",
        "\n",
        "import matplotlib.pyplot as plt\n",
        "import matplotlib.image as mpimg\n",
        "import os\n",
        "\n",
        "fig_paths = ['test/fig_dp_tradeoff.png', 'test/fig_mi.png']\n",
        "for path in fig_paths:\n",
        "    if os.path.exists(path):\n",
        "        plt.figure(figsize=(12, 8))\n",
        "        img = mpimg.imread(path)\n",
        "        plt.imshow(img)\n",
        "        plt.axis('off')\n",
        "        plt.show()\n",
        "    else:\n",
        "        print(f\"Plot not found: {path}\")"
    ]
}

# Append the new cells
nb['cells'].extend([header_cell, run_cell, plot_cell])

# Save the notebook back
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f)

print("Successfully updated MedShare_FINAL.ipynb with High-Fidelity sweep cells.")
