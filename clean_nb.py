
import json
import os

def cleanup_notebook(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # We want to replace Cell 7 with a merged version, and remove Cell 8.
    # New source for Cell 7 (Indices are 0-based)
    new_source = [
        "# @title 🎨 Results Visualization (Live Update)\n",
        "import os\n",
        "import matplotlib.pyplot as plt\n",
        "import matplotlib.image as mpimg\n",
        "\n",
        "# 1. Run the plotter to update PNGs in the test folder\n",
        "if os.path.exists(\"test/plot_results.py\"):\n",
        "    print(\"📊 Syncing experiment results...\")\n",
        "    !python test/plot_results.py\n",
        "\n",
        "# 2. List of expected plots\n",
        "plots = [\n",
        "    \"test/fig_dp_tradeoff.png\",\n",
        "    \"test/fig_robustness.png\",\n",
        "    \"test/fig_latency.png\",\n",
        "    \"test/fig_mi.png\",\n",
        "    \"test/fig_gas_costs.png\"\n",
        "]\n",
        "\n",
        "# 3. Display everything with professional formatting\n",
        "for path in plots:\n",
        "    if os.path.exists(path):\n",
        "        plt.figure(figsize=(12, 7))\n",
        "        plt.imshow(mpimg.imread(path))\n",
        "        plt.axis('off')\n",
        "        plt.title(f\"Scientific Visualization: {os.path.basename(path)}\", fontsize=14, color='#bc8cff')\n",
        "        plt.show()\n",
        "    else:\n",
        "        print(f\"⌛ {path} not ready yet (Run the benchmark for this type first!)\")\n"
    ]
    
    # Update Cell 7
    nb['cells'][7]['source'] = new_source
    nb['cells'][7]['metadata']['cellView'] = 'form' # This makes it a 'hidden' or 'form' cell in Colab
    
    # Remove Cell 8
    # Be careful not to remove the wrong thing if indices changed, but based on inspection it is at index 8.
    if len(nb['cells']) > 8:
        del nb['cells'][8]
        print("Successfully merged and removed redundant visualization cell.")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

if __name__ == "__main__":
    cleanup_notebook(r'c:\Users\bhuva\bxp267\MedShare_FINAL.ipynb')
