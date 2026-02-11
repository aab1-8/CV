import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

sns.set_theme(style="whitegrid", palette="muted")

# Ensure we are in the script's directory so relative paths for data and figures work
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir:
    os.chdir(script_dir)
    print(f"Working directory set to: {os.getcwd()}")


def load_and_dedup(csv_path, subset_cols):
    """Helper to read CSV and remove duplicate rows from previous runs (keep last)."""
    # Check if file exists, if not, try to look in parent directory
    if not os.path.exists(csv_path):
        parent_dir = os.path.dirname(os.path.dirname(csv_path))
        filename = os.path.basename(csv_path)
        fallback_path = os.path.join(parent_dir, filename)
        
        # Also check for "root_" prefixed files in parent
        root_prefixed_path = os.path.join(parent_dir, "root_" + filename)
        
        if os.path.exists(fallback_path):
            print(f"DEBUG: Found fallback file at {fallback_path}")
            csv_path = fallback_path
        elif os.path.exists(root_prefixed_path):
             print(f"DEBUG: Found fallback file at {root_prefixed_path}")
             csv_path = root_prefixed_path
        else:
            print(f"DEBUG: File not found: {csv_path}")
            return None

    try:
        df = pd.read_csv(csv_path)
        # Drop duplicates based on the key columns, keeping the LAST entry (newest run)
        df = df.drop_duplicates(subset=subset_cols, keep='last')
        print(f"DEBUG: Loaded {len(df)} rows from {os.path.basename(csv_path)}")
        return df
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None



def plot_save(name, func):
    """Wrapper for consistent plotting boilerplate."""
    print(f"--- Attempting to plot {name} ---")
    try:
        plt.figure(figsize=(12, 7))
        if func():
            plt.tight_layout()
            output_path = os.path.join(script_dir, name)
            plt.savefig(output_path, dpi=150)
            print(f"[OK] Generated {output_path}")
        else:
            print(f"[FAIL] Skipped {name} (func returned False)")
        plt.close()
    except Exception as e:
        print(f"[FAIL] Failed to generate {name}: {e}")


def plot_dp():
    csv_path = os.path.join(script_dir, "exp_dp_results.csv")
    mi_path = os.path.join(script_dir, "exp_mi_results.csv")
    
    print(f"DEBUG: Checking for DP results at: {csv_path}")
    
    df = None
    
    # Try loading DP results first
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, na_filter=False)
        df = df.drop_duplicates(subset=['noise'], keep='last').sort_values("noise")
    elif os.path.exists(mi_path):
        # Fallback to MI results which contain the same info (Accuracy vs Sigma)
        print(f"DEBUG: using MI results for DP plot at: {mi_path}")
        df_mi = pd.read_csv(mi_path, na_filter=False)
        
        def extract_noise(mode_str):
            if "sigma=" in str(mode_str):
                try: return float(str(mode_str).split("sigma=")[1].rstrip(")"))
                except: return 0.0
            return 0.0
            
        df_mi['noise'] = df_mi['Mode'].apply(extract_noise)
        df_mi = df_mi[['noise', 'accuracy']] # Keep only relevant cols
        df = df_mi.drop_duplicates(subset=['noise'], keep='last').sort_values("noise")
    else: 
        print(f"DEBUG: File does not exist!")
        # Fallback to root
        root_path = os.path.join(os.path.dirname(script_dir), "root_exp_dp_results.csv")
        if os.path.exists(root_path):
            csv_path = root_path
            print(f"DEBUG: Found in root: {csv_path}")
            df = pd.read_csv(csv_path, na_filter=False)
            df = df.drop_duplicates(subset=['noise'], keep='last').sort_values("noise")
        else:
            return False

    if df is None or df.empty: return False

    # Plot accuracy only
    plt.plot(df["noise"], df["accuracy"], marker="o", markersize=12, linewidth=4, color="#bc8cff", label="Model Accuracy")
    plt.xlabel("DP Noise Multiplier ($\\sigma$)", fontsize=14)
    plt.ylabel("Global Accuracy", fontsize=14)
    plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(loc='best', frameon=True, facecolor='white', framealpha=0.9, fontsize=12)
    
    plt.title("Privacy-Accuracy Tradeoff: Global Model Accuracy vs. Noise", fontsize=18, fontweight='bold', pad=20)
    return True

def plot_robustness():
    csv_path = os.path.join(script_dir, "exp_robustness_results.csv")
    if not os.path.exists(csv_path): return False
    df = pd.read_csv(csv_path, na_filter=False).drop_duplicates(subset=['attack', 'defense'], keep='last')
    
    attack_map = {"None": "No Attack", "label_flip": "Label Flip", "gradient_scale": "Grad Scale"}
    df['attack'] = df['attack'].map(lambda x: attack_map.get(x, x))
    df['attack'] = pd.Categorical(df['attack'], categories=['No Attack', 'Label Flip', 'Grad Scale'], ordered=True)
    
    colors = {"FedAvg": "#ff7b7b", "Trimmed-Avg": "#00d1ff"}
    sns.barplot(data=df, x="attack", y="accuracy", hue="defense", palette=colors, edgecolor='black', alpha=0.9)
    plt.title("Adversarial Robustness: Defense Strategy Comparison", fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Simulated Attack Vector", fontsize=14)
    plt.ylabel("Resilience (Accuracy)", fontsize=14)
    plt.legend(title="Defense Engine", loc='lower left')
    plt.ylim(0.0, 1.0)
    return True

def plot_gas():
    csv_path = os.path.join(script_dir, "exp_gas_log.csv")
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0: return False
    df = pd.read_csv(csv_path).drop_duplicates(subset=['Round', 'Client'], keep='last')
    if df.empty: return False

    agg_df = df.groupby('Round')['GasUsed'].agg(['mean', 'std']).reset_index()
    if agg_df.empty: return False

    plt.bar(agg_df['Round'].astype(str), agg_df['mean'], yerr=agg_df['std'], capsize=7, color='#62efab', alpha=0.3, label="Network Avg")
    
    # 1. Clean names: "Hospital_1" -> "Hospital 1"
    df['Client'] = df['Client'].str.replace('_', ' ')
    
    # 2. Sort by hospital ID (number) for clean legend order
    df['sort_key'] = df['Client'].str.extract(r'(\d+)').astype(int)
    df = df.sort_values('sort_key')
    
    # Enhanced visibility for individual dots
    sns.stripplot(data=df, x="Round", y="GasUsed", hue="Client", 
                 palette="viridis", size=6, alpha=0.9, jitter=0.25, edgecolor="black", linewidth=1.0)
    
    # Optimize Y-axis to focus on usage range
    # Optimize Y-axis to focus on usage range, accounting for error bars
    min_gas = df['GasUsed'].min()
    
    # Calculate the absolute max height including the error bar (mean + std)
    max_with_error = (agg_df['mean'] + agg_df['std']).max()
    max_data = df['GasUsed'].max()
    true_max = max(max_with_error, max_data)
    
    margin = (true_max - min_gas) * 0.15 if true_max > min_gas else min_gas * 0.1
    plt.ylim(bottom=max(0, min_gas - margin), top=true_max + margin)
    
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.title("Blockchain Verification: Gas Cost Analysis", fontsize=18, fontweight='bold', pad=20)
    plt.ylabel("Gas Units (EVM)", fontsize=14)
    # Force Y-axis to plain integers (no scientific notation)
    plt.ticklabel_format(style='plain', axis='y')
    # CRITICAL: Disable the offset (the "+1.211e5" part)
    plt.gca().yaxis.get_major_formatter().set_useOffset(False)
    
    # Ensure tick marks are WHOLE NUMBERS only
    from matplotlib.ticker import MaxNLocator
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    
    plt.legend(title="Hospital Node", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    return True

def plot_latency():
    csv_path = os.path.join(script_dir, "exp_latency_log.csv")
    df = load_and_dedup(csv_path, subset_cols=['rounds'])
    if df is None or df.empty: return False
    plt.plot(df["rounds"], df["duration_sec"], marker="s", markersize=10, linewidth=3, color="teal")
    plt.title("System Scaling: Latency Benchmark", fontsize=18, fontweight='bold', pad=20)
    plt.ylabel("Wall-clock Time (Seconds)", fontsize=14)
    plt.xlabel("Communication Rounds", fontsize=14)
    return True

def plot_mi():
    mi_path = os.path.join(script_dir, "exp_mi_results.csv")
    dp_path = os.path.join(script_dir, "exp_dp_results.csv")
    
    dfs = []
    
    # helper to parse noise from Mode string
    def extract_noise(mode_str):
        if "sigma=" in str(mode_str):
            try: return float(str(mode_str).split("sigma=")[1].rstrip(")"))
            except: return 0.0
        return 0.0

    if os.path.exists(mi_path):
        df_mi = pd.read_csv(mi_path, na_filter=False)
        if not df_mi.empty:
            df_mi['noise'] = df_mi['Mode'].apply(extract_noise)
            df_mi['source'] = 'mi'
            dfs.append(df_mi)

    if os.path.exists(dp_path):
        df_dp = pd.read_csv(dp_path, na_filter=False)
        if not df_dp.empty and 'leakage' in df_dp.columns:
            df_dp['Mode'] = df_dp['noise'].apply(lambda x: f"With DP (sigma={x})" if x > 0 else "No Privacy (Baseline)")
            df_dp['source'] = 'dp'
            dfs.append(df_dp)

    if not dfs: return False
    
    # Merge and prioritize MI results
    df = pd.concat(dfs, ignore_index=True)
    
    # Sort by source (mi > dp) so we can keep 'first' or 'last' reliably
    # We want 'mi' results to override 'dp' results if they exist for the same noise level
    # 'mi' comes after 'dp' alphabetically, so descending sort puts 'mi' first
    df = df.sort_values(by=['noise', 'source'], ascending=[True, False])
    
    # Drop duplicates by NOISE level, keeping the one from 'mi' (the first one due to sort)
    df = df.drop_duplicates(subset=['noise'], keep='first')
        
    def clean_label(row):
        mode_str = str(row['Mode'])
        if "sigma=" in mode_str:
            return f"Sigma={row['noise']}"
        return "Baseline"
    
    df['label'] = df.apply(clean_label, axis=1)
    
    # Force sort by noise level
    df = df.sort_values('noise')
    
    # Ensure we have at least some data points
    if len(df) == 0:
        return False
    
    # plot_save already created the figure
    
    # Create bar chart with color gradient
    colors = plt.cm.magma(np.linspace(0.3, 0.8, len(df)))
    bars = plt.bar(df['label'], df['leakage'], color=colors, edgecolor='black', linewidth=1.5, alpha=0.85)
    
    # Add labels for full visibility
    for bar, (_, row) in zip(bars, df.iterrows()):
        height = bar.get_height()
        acc = row.get('accuracy', 0)
        
        # 1. Leakage label on TOP (The Privacy Proof)
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                f'Leak: {height*100:.1f}%', ha='center', va='bottom', 
                fontweight='bold', fontsize=10, color='darkred')
        
        # 2. Accuracy label INSIDE (The Utility Metric)
        # Position it slightly below the top of the bar for readability
        plt.text(bar.get_x() + bar.get_width()/2., height / 2 if height > 0.05 else height + 0.02,
                f'Acc:\n{acc*100:.1f}%', ha='center', va='center', 
                fontweight='bold', fontsize=9, color='white' if height > 0.05 else 'black')
    
    plt.title("Privacy Audit: Information Leakage vs. Sigma (\u03c3)", fontsize=18, fontweight='bold', pad=20)
    plt.ylabel("Measured Leakage (Generalization Gap)", fontsize=14)
    plt.xlabel("Privacy Protection Level", fontsize=14)
    
    # Dynamic Y-axis scaling to make small differences visible
    max_leak = df['leakage'].max()
    plt.ylim(0, max(0.15, max_leak * 1.35)) 
    
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add explanatory annotation
    plt.annotate("Baseline (High Risk)", xy=(0, df['leakage'].iloc[0]), xytext=(0.5, max_leak*1.2),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
    
    plt.tight_layout()
    return True

def plot_robustness():
    csv_path = os.path.join(script_dir, "exp_robustness_results.csv")
    df = load_and_dedup(csv_path, subset_cols=['attack', 'defense'])
    if df is None or df.empty: return False
    
    attack_map = {"None": "No Attack", "label_flip": "Label Flip", "gradient_scale": "Grad Scale"}
    df['attack'] = df['attack'].map(lambda x: attack_map.get(x, x))
    df['attack'] = pd.Categorical(df['attack'], categories=['No Attack', 'Label Flip', 'Grad Scale'], ordered=True)
    
    colors = {"FedAvg": "#ff7b7b", "Trimmed-Avg": "#00d1ff"}
    sns.barplot(data=df, x="attack", y="accuracy", hue="defense", palette=colors, edgecolor='black', alpha=0.9)
    plt.title("Adversarial Robustness: Defense Strategy Comparison", fontsize=18, fontweight='bold', pad=20)
    plt.ylabel("Global Model Accuracy", fontsize=14)
    plt.xlabel("Attack Scenario", fontsize=14)
    plt.ylim(0, 1.0)
    plt.legend(title="Defense Method", loc='lower right')
    return True

if __name__ == "__main__":
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.facecolor'] = '#f8f9fa'
    plot_save("fig_dp_tradeoff.png", plot_dp)
    plot_save("fig_robustness.png", plot_robustness)
    plot_save("fig_gas_costs.png", plot_gas)
    plot_save("fig_latency.png", plot_latency)
    plot_save("fig_mi.png", plot_mi)