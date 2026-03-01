import pandas as pd
import matplotlib
matplotlib.use('Agg')
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
        # Support both old schema (noise,...) and new timestamped schema
        if 'noise' not in df.columns and 'timestamp_utc' in df.columns:
            df = df.rename(columns={'noise': 'noise'})  # already correct
        df = df.drop_duplicates(subset=['noise'], keep='last').sort_values("noise")
    elif os.path.exists(mi_path):
        # Fallback to MI results which contain the same info (Accuracy vs Sigma)
        print(f"DEBUG: using MI results for DP plot at: {mi_path}")
        df_mi = pd.read_csv(mi_path, na_filter=False)
        
        # Consistent case for 'mode'
        if 'mode' in df_mi.columns: df_mi = df_mi.rename(columns={'mode': 'Mode'})
        
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
    print("DEBUG: Entered plot_robustness")
    csv_path = os.path.join(script_dir, "exp_robustness_results.csv")
    if not os.path.exists(csv_path): 
        print(f"DEBUG: File not found: {csv_path}")
        return False
    df = pd.read_csv(csv_path, na_filter=False)
    # Support new schema with timestamp/dataset columns - only keep what we need
    df = df[['attack', 'defense', 'accuracy']].drop_duplicates(subset=['attack', 'defense'], keep='last')
    print(f"DEBUG: Loaded {len(df)} rows from {csv_path}")
    
    attack_map = {"None": "No Attack", "label_flip": "Label Flip", "gradient_scale": "Grad Scale"}
    df['attack'] = df['attack'].map(lambda x: attack_map.get(x, x))
    df['attack'] = pd.Categorical(df['attack'], categories=['No Attack', 'Label Flip', 'Grad Scale'], ordered=True)
    
    colors = {"FedAvg": "#ff7b7b", "Robust-MAD": "#00d1ff"}
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
    # Support new timestamped schema
    if 'Round' not in df.columns and 'timestamp_utc' in df.columns:
        df = df.rename(columns={df.columns[1]: 'Round', df.columns[2]: 'Client', df.columns[3]: 'GasUsed'})
    if df.empty: return False

    agg_df = df.groupby('Round')['GasUsed'].agg(['mean', 'std']).reset_index()
    if agg_df.empty: return False

    plt.bar(agg_df['Round'].astype(str), agg_df['mean'], yerr=agg_df['std'], 
            capsize=3, color='#62efab', alpha=0.3, label="Network Avg",
            error_kw={'elinewidth': 0.8, 'markeredgewidth': 0.8})
    
    # 1. Clean names: "Hospital_1" -> "Hospital 1"
    df['Client'] = df['Client'].str.replace('_', ' ')
    
    # 2. Sort by hospital ID (number) for clean legend order
    df['sort_key'] = df['Client'].str.extract(r'(\d+)').fillna(0).astype(int)
    df = df.sort_values('sort_key')
    
    # Enhanced visibility for individual dots
    sns.stripplot(data=df, x="Round", y="GasUsed", hue="Client", 
                 palette="viridis", size=6, alpha=0.9, jitter=0.25, edgecolor="black", linewidth=1.0)
    
    # Optimize Y-axis to focus on usage range, accounting for error bars
    # We want to see from (mean - std) to (mean + std) plus a margin
    agg_df['low'] = agg_df['mean'] - agg_df['std'].fillna(0)
    agg_df['high'] = agg_df['mean'] + agg_df['std'].fillna(0)
    
    abs_min = min(df['GasUsed'].min(), agg_df['low'].min())
    abs_max = max(df['GasUsed'].max(), agg_df['high'].max())
    
    margin = (abs_max - abs_min) * 0.15 if abs_max > abs_min else abs_max * 0.1
    plt.ylim(bottom=max(0, abs_min - margin), top=abs_max + margin)
    
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
    df = pd.read_csv(csv_path, na_filter=False)
    # Support new timestamped schema
    if 'rounds' not in df.columns and 'timestamp_utc' in df.columns:
        df = df.rename(columns={df.columns[1]: 'rounds', df.columns[2]: 'duration_sec'})
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
    
    def extract_noise(mode_str):
        if "sigma=" in str(mode_str):
            try: return float(str(mode_str).split("sigma=")[1].rstrip(")"))
            except: return 0.0
        return 0.0

    if os.path.exists(mi_path):
        df_mi = pd.read_csv(mi_path, na_filter=False)
        if not df_mi.empty:
            # Consistent case for 'mode'
            if 'mode' in df_mi.columns: df_mi = df_mi.rename(columns={'mode': 'Mode'})
            # Backward compat: old CSVs had a single 'leakage' column
            if 'leakage' in df_mi.columns and 'leakage_acc' not in df_mi.columns:
                df_mi = df_mi.rename(columns={'leakage': 'leakage_acc'})
                df_mi['leakage_auc'] = df_mi['leakage_acc']  # Duplicate as best guess
            df_mi['noise'] = df_mi['Mode'].apply(extract_noise)
            df_mi['source'] = 'mi'
            dfs.append(df_mi)

    if os.path.exists(dp_path):
        df_dp = pd.read_csv(dp_path, na_filter=False)
        if not df_dp.empty:
            # Backward compat: old DP CSVs had 'leakage' instead of 'leakage_acc'
            if 'leakage' in df_dp.columns and 'leakage_acc' not in df_dp.columns:
                df_dp = df_dp.rename(columns={'leakage': 'leakage_acc'})
                df_dp['leakage_auc'] = df_dp['leakage_acc']
            if 'leakage_acc' in df_dp.columns:
                df_dp['Mode'] = df_dp['noise'].apply(lambda x: f"With DP (sigma={x})" if x > 0 else "No Privacy (Baseline)")
                df_dp['source'] = 'dp'
                dfs.append(df_dp)

    if not dfs: return False
    
    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values(by=['noise', 'source'], ascending=[True, False])
    df = df.drop_duplicates(subset=['noise'], keep='first')

    def clean_label(row):
        return f"σ={row['noise']}" if row['noise'] > 0 else "Baseline\n(No DP)"
    
    df['label'] = df.apply(clean_label, axis=1)
    df = df.sort_values('noise').reset_index(drop=True)

    if len(df) == 0:
        return False

    # --- Grouped bar chart: Accuracy Gap vs AUC Gap side by side ---
    n = len(df)
    x = np.arange(n)
    bar_w = 0.35

    bars_acc = plt.bar(x - bar_w/2, df['leakage_acc'], bar_w,
                       label='Accuracy Gap (Yeom 2018)',
                       color='#ff7b7b', edgecolor='black', linewidth=1.2, alpha=0.88)
    bars_auc = plt.bar(x + bar_w/2, df['leakage_auc'], bar_w,
                       label='AUC Gap — Primary (Nasr 2019)',
                       color='#8c6fff', edgecolor='black', linewidth=1.2, alpha=0.88,
                       hatch='//')

    # Annotate each bar with its percentage value
    for bar in bars_acc:
        h = bar.get_height()
        if h > 0.001:
            plt.text(bar.get_x() + bar.get_width()/2., h + 0.003,
                     f'{h*100:.1f}%', ha='center', va='bottom',
                     fontsize=8.5, fontweight='bold', color='#cc0000')

    for bar in bars_auc:
        h = bar.get_height()
        if h > 0.001:
            plt.text(bar.get_x() + bar.get_width()/2., h + 0.003,
                     f'{h*100:.1f}%', ha='center', va='bottom',
                     fontsize=8.5, fontweight='bold', color='#5500cc')

    # Annotate each group with model accuracy from the primary (mi) source
    for i, (_, row) in enumerate(df.iterrows()):
        acc = row.get('accuracy', 0)
        plt.text(i, -0.012, f'Acc: {acc*100:.1f}%',
                 ha='center', va='top', fontsize=8, color='#333333', fontstyle='italic')

    plt.title("Privacy Audit: Information Leakage vs. DP Noise Level (σ)",
              fontsize=17, fontweight='bold', pad=20)
    plt.ylabel("Measured Leakage (Proxy Score)", fontsize=13)
    plt.xlabel("Privacy Protection Level", fontsize=13)
    plt.xticks(x, df['label'], fontsize=11)

    max_leak = max(df['leakage_acc'].max(), df['leakage_auc'].max())
    plt.ylim(-0.025, max(0.15, max_leak * 1.40))

    plt.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    return True

if __name__ == "__main__":
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.facecolor'] = '#f8f9fa'
    plot_save("fig_dp_tradeoff.png", plot_dp)
    plot_save("fig_robustness.png", plot_robustness)
    plot_save("fig_gas_costs.png", plot_gas)
    plot_save("fig_latency.png", plot_latency)
    plot_save("fig_mi.png", plot_mi)