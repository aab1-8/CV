
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Load only the completed rows (drop any empty trailing rows)
df = pd.read_csv("test/exp_mi_results.csv").dropna()
print(df)

labels = df["Mode"]
accuracy = df["accuracy"] * 100
leakage_auc = df["leakage_auc"] * 100

x = np.arange(len(labels))
width = 0.38

fig, ax1 = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("#0f1117")
ax1.set_facecolor("#0f1117")

# Bar 1: FL Accuracy
bars1 = ax1.bar(x - width/2, accuracy, width, label="FL Accuracy (%)",
                color="#4f8ef7", alpha=0.9, zorder=3)

# Bar 2: MI Leakage AUC
bars2 = ax1.bar(x + width/2, leakage_auc, width, label="MI Leakage AUC (%)",
                color="#f76c6c", alpha=0.9, zorder=3)

# Value labels on bars
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
             f"{bar.get_height():.1f}%", ha='center', va='bottom',
             color='white', fontsize=8.5, fontweight='bold')

for bar in bars2:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, h + 0.8,
             f"{h:.2f}%", ha='center', va='bottom',
             color='#f76c6c', fontsize=8.5, fontweight='bold')

# Styling
ax1.set_xticks(x)
ax1.set_xticklabels(labels, rotation=15, ha='right', color='white', fontsize=9)
ax1.set_ylim(0, 115)
ax1.set_ylabel("Percentage (%)", color='white', fontsize=11)
ax1.tick_params(axis='y', colors='white')
ax1.spines['bottom'].set_color('#444')
ax1.spines['left'].set_color('#444')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.grid(axis='y', color='#333', linestyle='--', linewidth=0.6, zorder=0)

ax1.set_title("🩺 Thyroid Dataset — Membership Inference Attack Audit\n"
              "Privacy vs. Accuracy Trade-off across Differential Privacy Noise Levels",
              color='white', fontsize=13, fontweight='bold', pad=16)

legend = ax1.legend(facecolor='#1e2130', edgecolor='#444', labelcolor='white',
                    fontsize=10, loc='upper right')

# Annotation: highlight the baseline
ax1.axhline(y=accuracy.iloc[0], color='#4f8ef7', linestyle=':', linewidth=1, alpha=0.5)
ax1.text(len(labels) - 0.5, accuracy.iloc[0] + 1.5,
         f"Baseline: {accuracy.iloc[0]:.1f}%", color='#4f8ef7', fontsize=8, ha='right')

plt.tight_layout()
out_path = "test/fig_thyroid_mi.png"
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f"\nSaved: {out_path}")
plt.show()
