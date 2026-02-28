import os
import json
import numpy as np
import time

# Global variable to track session state
_START_TIME = time.time()
_LAST_LOGGED_ROUND = -1

def reset_logging():
    global _LAST_LOGGED_ROUND, _START_TIME, _ROUND_CACHE
    _LAST_LOGGED_ROUND = -1
    _START_TIME = time.time()
    _ROUND_CACHE.clear()
    print("[Logging] Session state reset.")

# Global cache to bridge metrics between Fit and Evaluate phases within a round
_ROUND_CACHE = {}

def weighted_average(metrics, server_round=None, log_to_csv=True):
    """Aggregates metrics and logs ACTUAL system data for visualizations."""
    global _START_TIME, _LAST_LOGGED_ROUND
    
    # Paths setup
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_test_dir = os.path.join(base_dir, "test")
    os.makedirs(target_test_dir, exist_ok=True)
    
    # current_round will be determined later to ensure session consistency
    if server_round is not None:
         print(f"[Metrics] Aggregating {len(metrics)} clients for Round {server_round}")
    
    total = sum([n for n, _ in metrics])
    if total == 0: return {"accuracy": 0.0, "auc": 0.5, "mi_score": 0.0, "mi_auc_score": 0.0}
    
    # Step 1: Base Averages
    agg_acc = sum([n * m["accuracy"] for n, m in metrics]) / total
    agg_auc = sum([n * m.get("auc", 0.5) for n, m in metrics]) / total
    agg_train_acc = sum([n * m.get("train_accuracy", m["accuracy"]) for n, m in metrics]) / total
    agg_train_auc = sum([n * m.get("train_auc", m.get("auc", 0.5)) for n, m in metrics]) / total

    # MI proxy 1: Accuracy Gap (Yeom et al. 2018) — simple, fast, less robust on imbalanced data
    mi_score = max(0, agg_train_acc - agg_acc)
    # MI proxy 2: AUC Gap (Nasr et al. 2019) — threshold-free, imbalance-robust, recommended for medical data
    mi_auc_score = max(0, agg_train_auc - agg_auc)

    # Step 2: Privacy Extraction
    eps_list = [m.get("privacy_spent", 0.0) for n, m in metrics if m.get("privacy_spent", 0.0) > 0]
    eps = max(eps_list) if eps_list else 0.0

    # Step 3: Round Bridging
    current_round = server_round
    if current_round is not None:
        # We cache during the Fit phase (where train_accuracy is present)
        # to carry over MI scores and Epsilon to the Evaluate phase.
        is_fit_phase = any("train_accuracy" in m for _, m in metrics)
        
        if is_fit_phase:
            fit_loss = sum([n * m.get("loss", 0.0) for n, m in metrics]) / total if total > 0 else 0.0
            _ROUND_CACHE[current_round] = {"epsilon": eps, "mi_score": mi_score, "mi_auc_score": mi_auc_score, "loss": fit_loss}
        # Evaluation phase always tries to inherit from its corresponding Fit phase
        if current_round in _ROUND_CACHE:
            eps = _ROUND_CACHE[current_round]["epsilon"]
            mi_score = _ROUND_CACHE[current_round]["mi_score"]
            mi_auc_score = _ROUND_CACHE[current_round].get("mi_auc_score", mi_auc_score)
    
    # Tracking for dashboard
    hist_file = os.path.join(base_dir, "frontend", "src", "data", "training_history.json")
    os.makedirs(os.path.dirname(hist_file), exist_ok=True)
    history = []
    if os.path.exists(hist_file):
        try:
            with open(hist_file, 'r', encoding='utf-8') as f: history = json.load(f)
        except: pass
    
    if current_round is None:
        return {"accuracy": float(agg_acc), "auc": float(agg_auc), "mi_score": float(mi_score), "mi_auc_score": float(mi_auc_score)}
    
    # Track last round logged for console visibility
    _LAST_LOGGED_ROUND = current_round

    # Extract Metadata
    first_m = metrics[0][1]
    exp_type = first_m.get("experiment", "none")
    atk_type = first_m.get("attack_type", "None")
    dfns_name = first_m.get("defense_name", "FedAvg")
    total_rounds = first_m.get("total_rounds", 1)
    
    # --- 1. GAS LOGGING ---
    # We check for gas_used regardless of log_to_csv because gas is only reported 
    # during the Fit phase (where log_to_csv might be False to avoid dual-logging accuracy).
    gas_file = os.path.join(target_test_dir, "exp_gas_log.csv")
    ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if not os.path.exists(gas_file):
        with open(gas_file, "w", encoding='utf-8') as f: 
            f.write("timestamp_utc,Round,Client,GasUsed\n") 
    
    with open(gas_file, "a", encoding='utf-8') as f:
        for n, m in metrics:
            g = m.get("gas_used", 0)
            if g > 0:
                # Use node_name for clean reporting, fallback to legacy index
                h_name = m.get("node_name", f"Hospital_{m.get('client_id', 'unknown')}")
                f.write(f"{ts_now},{current_round},{h_name},{g}\n")

    # --- 2. LATENCY LOGGING ---
    if log_to_csv and exp_type == "latency":
        lat_file = os.path.join(target_test_dir, "exp_latency_log.csv")
        if not os.path.exists(lat_file):
            with open(lat_file, "w", encoding='utf-8') as f: 
                f.write("timestamp_utc,rounds,duration_sec\n")
        with open(lat_file, "a", encoding='utf-8') as f:
            dur = time.time() - _START_TIME
            f.write(f"{ts_now},{current_round},{dur:.2f}\n")

    # --- 3. ROBUSTNESS LOGGING ---
    if log_to_csv and exp_type == "robustness" and current_round == total_rounds:
        rob_file = os.path.join(target_test_dir, "exp_robustness_results.csv")
        if not os.path.exists(rob_file):
            with open(rob_file, "w", encoding='utf-8') as f: 
                f.write("timestamp_utc,dataset,attack,defense,rounds,accuracy\n")
        with open(rob_file, "a", encoding='utf-8') as f:
            dataset_name = first_m.get("dataset_name", "unknown")
            f.write(f"{ts_now},{dataset_name},{atk_type},{dfns_name},{total_rounds},{agg_acc:.4f}\n")

    # --- 4. DP & MI ---
    noise = first_m.get("noise_multiplier", 1.0)

    # We log to CSV only on the last round. Preference is given to Evaluation accuracy
    # over Fit accuracy for the long-term benchmarks (DP and MI CSVs).
    if log_to_csv and current_round == total_rounds:
        # Log to DP results file
        if exp_type == "dp":
            dp_file = os.path.join(target_test_dir, "exp_dp_results.csv")
            header = "timestamp_utc,dataset,noise,rounds,accuracy,epsilon,leakage_acc,leakage_auc\n"
            
            # Self-healing: Reset file if header is old (backward compatibility guard)
            if os.path.exists(dp_file):
                with open(dp_file, "r") as f:
                    first_line = f.readline()
                    if "timestamp_utc" not in first_line:
                        print(f"[Logging] Rotating old DP results file (detected legacy schema)...")
                        os.remove(dp_file)

            if not os.path.exists(dp_file):
                with open(dp_file, "w", encoding='utf-8') as f:
                    f.write(header)
            
            # Prevent duplicate sigma entries in the same file
            exists = False
            if os.path.exists(dp_file):
                with open(dp_file, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.split(",")
                        if len(parts) > 2 and parts[2].strip() == str(noise):
                            exists = True
                            break
            
            if not exists:
                dataset_name = first_m.get("dataset_name", "unknown")
                with open(dp_file, "a", encoding='utf-8') as f:
                    f.write(f"{ts_now},{dataset_name},{noise},{total_rounds},{agg_acc:.4f},{eps:.2f},{mi_score:.4f},{mi_auc_score:.4f}\n")
        
        # Log to MI results file (Only log if specific MI experiment or DP experiment requested it)
        # This prevents the 'DP' experiment from cluttering the 'MI Audit' plot if they are run separately.
        if exp_type in ["mi", "mi_step"]:
            mi_file = os.path.join(target_test_dir, "exp_mi_results.csv")
            header = "timestamp_utc,dataset,noise,rounds,mode,leakage_acc,leakage_auc,accuracy\n"
            
            # Self-healing: Reset file if header is old
            if os.path.exists(mi_file):
                with open(mi_file, "r") as f:
                    first_line = f.readline()
                    if "timestamp_utc" not in first_line:
                        print(f"[Logging] Rotating old MI results file (detected legacy schema)...")
                        os.remove(mi_file)

            if not os.path.exists(mi_file):
                with open(mi_file, "w", encoding='utf-8') as f:
                    f.write(header)
            
            mode = f"With DP (sigma={noise})" if eps > 0 or noise > 0 else "No Privacy (Baseline)"
            
            # Prevent duplicate entries
            exists = False
            if os.path.exists(mi_file):
                with open(mi_file, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.split(",")
                        if len(parts) > 4 and parts[4].strip() == mode:
                            exists = True
                            break
                
            if not exists:
                dataset_name = first_m.get("dataset_name", "unknown")
                with open(mi_file, "a", encoding='utf-8') as f:
                    f.write(f"{ts_now},{dataset_name},{noise},{total_rounds},{mode},{mi_score:.4f},{mi_auc_score:.4f},{agg_acc:.4f}\n")

    # Compute weighted loss — inherit from fit-phase cache if this is the evaluate phase
    agg_loss = sum([n * m.get("loss", 0.0) for n, m in metrics]) / total if total > 0 else 0.0
    if agg_loss == 0.0 and current_round in _ROUND_CACHE:
        agg_loss = _ROUND_CACHE[current_round].get("loss", 0.0)

    # Update history for frontend
    updated = False
    for entry in history:
        if entry["round"] == current_round:
            update_data = {
                "accuracy": float(agg_acc), 
                "auc": float(agg_auc),
                "loss": float(agg_loss),
                "mi_score": float(mi_score),
                "mi_auc_score": float(mi_auc_score)
            }
            if eps > 0: update_data["epsilon"] = float(eps)
            entry.update(update_data)
            updated = True
            break
    if not updated:
        entry_data = {
            "round": current_round, 
            "accuracy": float(agg_acc), 
            "auc": float(agg_auc),
            "loss": float(agg_loss),
            "mi_score": float(mi_score),
            "mi_auc_score": float(mi_auc_score),
            "epsilon": float(eps)
        }
        history.append(entry_data)
    with open(hist_file, "w", encoding='utf-8') as f: json.dump(history, f, indent=2)

    return {"accuracy": float(agg_acc), "auc": float(agg_auc), "mi_score": float(mi_score), "mi_auc_score": float(mi_auc_score)}

def generate_pairwise_masks(num_clients, net_template, scale=1e4, seed=42):
    """Generates symmetric pairwise masks for secure aggregation."""
    np.random.seed(seed)
    shapes = [p.shape for p in net_template.parameters()]
    mask_adds = [[np.zeros(s) for s in shapes] for _ in range(num_clients)]
    mask_subs = [[np.zeros(s) for s in shapes] for _ in range(num_clients)]
    for i in range(num_clients):
        for j in range(i + 1, num_clients):
            for p_idx, shape in enumerate(shapes):
                mask = np.random.uniform(-scale, scale, shape)
                mask_adds[i][p_idx] += mask
                mask_subs[j][p_idx] += mask
    return mask_adds, mask_subs
