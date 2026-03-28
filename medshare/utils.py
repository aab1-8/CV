import os, json, numpy as np, time # Core libraries for logging, math and time-tracking

# GLOBAL SESSION STORAGE (ORIGINAL COMMENT PRESERVED)
# These variables maintain cross-round state to provide accurate MI leakage metrics
_START_TIME = time.time()
_LAST_LOGGED_ROUND = -1
_ROUND_CACHE = {} # Used to bridge 'Fit' metrics (train acc) to 'Evaluate' phase (test acc)

def reset_logging():
    """Resets the timing and cache for a brand new Federated Experiment."""
    global _LAST_LOGGED_ROUND, _START_TIME, _ROUND_CACHE
    _LAST_LOGGED_ROUND, _START_TIME = -1, time.time()
    _ROUND_CACHE.clear()
    print("[Logging] Experiment session state reset.")

def weighted_average(metrics, server_round=None, log_to_csv=True):
    """
    The aggregator: combines reports from all hospitals into a single Global Outcome.
    Calculates Accuracy, AUC, and Privacy Leakage (MI Scores).

    Design Note: Logging uses simple atomic 'append' modes. While suitable for this 
    single-threaded orchestration, a distributed production scale-up would require 
    an asynchronous thread-safe logging service or a dedicated DB.
    """
    global _START_TIME, _LAST_LOGGED_ROUND
    
    # Path Setup: Locate where the dashboard and audit logs live
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_test_dir = os.path.join(base_dir, "test")
    os.makedirs(target_test_dir, exist_ok=True)
    
    # Calculate weighted average: Weight = (Node_Data_Size) / (Total_Data_Size)
    total = sum([n for n, _ in metrics])
    if total == 0: return {"accuracy": 0.0, "auc": 0.5, "mi_score": 0.0, "mi_auc_score": 0.0}
    
    # Aggregating Primary Metrics (Accuracy & Area Under the Curve)
    agg_acc = sum([n * m["accuracy"] for n, m in metrics]) / total
    agg_auc = sum([n * m.get("auc", 0.5) for n, m in metrics]) / total
    agg_train_acc = sum([n * m.get("train_accuracy", m["accuracy"]) for n, m in metrics]) / total
    agg_train_auc = sum([n * m.get("train_auc", m.get("auc", 0.5)) for n, m in metrics]) / total

    # Step 1: MEMERSHIP INFERENCE (MI) ESTIMATION (Privacy Leakage)
    # MI proxy 1: Accuracy Gap (Yeom et al.) — measures how much better the model is at 'remembering' seen data.
    mi_score = max(0, agg_train_acc - agg_acc)
    # MI proxy 2: AUC Gap (Nasr et al.) — more robust against medical data imbalance.
    mi_auc_score = max(0, agg_train_auc - agg_auc)

    # Step 2: Privacy Extraction (Epsilon Accounting)
    # The 'Privacy Spent' is the maximum epsilon reported by any hospital (Worst-case scenario)
    eps_list = [m.get("privacy_spent", 0.0) for n, m in metrics if m.get("privacy_spent", 0.0) > 0]
    eps = max(eps_list) if eps_list else 0.0

    # Step 3: Round Bridging
    # In Flower, 'Fit' (Training) and 'Evaluate' (Testing) are separate callbacks. 
    # We cache training snapshots to make sure the evaluation phase shows the Correct Privacy metrics.
    current_round = server_round
    if current_round is not None:
        is_fit_phase = any("train_accuracy" in m for _, m in metrics)
        if is_fit_phase:
            fit_loss = sum([n * m.get("loss", 0.0) for n, m in metrics]) / total if total > 0 else 0.0
            _ROUND_CACHE[current_round] = {"epsilon": eps, "mi_score": mi_score, "mi_auc_score": mi_auc_score, "loss": fit_loss}
        if current_round in _ROUND_CACHE:
            # Synchronize cached privacy data into the final evaluation report
            eps = _ROUND_CACHE[current_round]["epsilon"]
            mi_score = _ROUND_CACHE[current_round]["mi_score"]
            mi_auc_score = _ROUND_CACHE[current_round].get("mi_auc_score", mi_auc_score)
    
    if current_round is None: return {"accuracy": float(agg_acc), "auc": float(agg_auc), "mi_score": float(mi_score), "mi_auc_score": float(mi_auc_score)}
    _LAST_LOGGED_ROUND = current_round

    # Metadata extraction for labeling logs
    first_m = metrics[0][1]
    exp_type, atk_type, dfns_name, total_rounds = first_m.get("experiment", "none"), first_m.get("attack_type", "None"), first_m.get("defense_name", "FedAvg"), first_m.get("total_rounds", 1)
    ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # --- Logging experimental results to CSVs for various audits (ORIGINAL COMMENT PRESERVED) ---
    # --- 4. GAS LOGGING (Blockchain Efficiency) (ORIGINAL COMMENT PRESERVED) ---
    # Captures exactly how much ETH/Gas each hospital node consumed during the train update
    gas_file = os.path.join(target_test_dir, "exp_gas_log.csv")
    if not os.path.exists(gas_file):
        with open(gas_file, "w", encoding='utf-8') as f: f.write("timestamp_utc,Round,Client,GasUsed\n") 
    with open(gas_file, "a", encoding='utf-8') as f:
        for n, m in metrics:
            if m.get("gas_used", 0) > 0:
                h_name = m.get("node_name", f"Hospital_{m.get('client_id', 'unknown')}")
                f.write(f"{ts_now},{current_round},{h_name},{int(m['gas_used'])}\n")

    # --- 5. LATENCY LOGGING (Compute Speed) (ORIGINAL COMMENT PRESERVED) ---
    if log_to_csv and exp_type == "latency":
        lat_file = os.path.join(target_test_dir, "exp_latency_log.csv")
        if not os.path.exists(lat_file):
            with open(lat_file, "w", encoding='utf-8') as f:
                f.write("timestamp_utc,rounds,duration_sec\n")
        with open(lat_file, "a", encoding='utf-8') as f:
            f.write(f"{ts_now},{current_round},{time.time() - _START_TIME:.2f}\n")

    # --- 6. ROBUSTNESS & ATTACK LOGGING (ORIGINAL COMMENT PRESERVED) ---
    if log_to_csv and exp_type == "robustness" and current_round == total_rounds:
        rob_file = os.path.join(target_test_dir, "exp_robustness_results.csv")
        if not os.path.exists(rob_file):
            with open(rob_file, "w", encoding='utf-8') as f:
                f.write("timestamp_utc,dataset,attack,defense,rounds,accuracy\n")
        with open(rob_file, "a", encoding='utf-8') as f:
            f.write(f"{ts_now},{first_m.get('dataset_name', 'unknown')},{atk_type},{dfns_name},{total_rounds},{agg_acc:.4f}\n")

    # --- 7. DP & MI PRIVACY LOGGING (The Audit Record) (ORIGINAL COMMENT PRESERVED) ---
    noise = first_m.get("noise_multiplier", 1.0)
    if log_to_csv and current_round == total_rounds:
        # DP results: Noise vs Accuracy vs Privacy Leakage (Epsilon)
        if exp_type == "dp":
            dp_file = os.path.join(target_test_dir, "exp_dp_results.csv")
            if not os.path.exists(dp_file):
                with open(dp_file, "w", encoding='utf-8') as f: f.write("timestamp_utc,dataset,noise,rounds,accuracy,epsilon,leakage_acc,leakage_auc\n")
            with open(dp_file, "a", encoding='utf-8') as f:
                f.write(f"{ts_now},{first_m.get('dataset_name', 'unknown')},{noise},{total_rounds},{agg_acc:.4f},{eps:.2f},{mi_score:.4f},{mi_auc_score:.4f}\n")
        
        # Membership Inference (MI) Audit: Specifically log attacks on baseline vs privacy-protected models
        if exp_type in ["mi", "mi_step"]:
            mi_file = os.path.join(target_test_dir, "exp_mi_results.csv")
            if not os.path.exists(mi_file):
                with open(mi_file, "w", encoding='utf-8') as f: f.write("timestamp_utc,dataset,noise,rounds,mode,leakage_acc,leakage_auc,accuracy\n")
            mode = f"With DP (sigma={noise})" if eps > 0 or noise > 0 else "No Privacy (Baseline)"
            with open(mi_file, "a", encoding='utf-8') as f:
                f.write(f"{ts_now},{first_m.get('dataset_name', 'unknown')},{noise},{total_rounds},{mode},{mi_score:.4f},{mi_auc_score:.4f},{agg_acc:.4f}\n")

    # Final Weighted Loss Calculation
    agg_loss = sum([n * m.get("loss", 0.0) for n, m in metrics]) / total if total > 0 else 0.0
    if agg_loss == 0.0 and current_round in _ROUND_CACHE: agg_loss = _ROUND_CACHE[current_round].get("loss", 0.0)

    # Step 8: Frontend Dashboard Synchronization
    # Updates the 'training_history.json' file which the React dashboard reads to plot the accuracy curves
    hist_file = os.path.join(base_dir, "frontend", "src", "data", "training_history.json")
    os.makedirs(os.path.dirname(hist_file), exist_ok=True)
    history = []
    if os.path.exists(hist_file):
        try:
            with open(hist_file, 'r', encoding='utf-8') as f: history = json.load(f)
        except: pass
    
    updated = False
    for entry in history:
        if entry["round"] == current_round:
            entry.update({"accuracy": float(agg_acc), "auc": float(agg_auc), "loss": float(agg_loss), "mi_score": float(mi_score), "mi_auc_score": float(mi_auc_score), "epsilon": float(eps)})
            updated = True; break
    if not updated:
        history.append({"round": current_round, "accuracy": float(agg_acc), "auc": float(agg_auc), "loss": float(agg_loss), "mi_score": float(mi_score), "mi_auc_score": float(mi_auc_score), "epsilon": float(eps)})
    with open(hist_file, "w", encoding='utf-8') as f: json.dump(history, f, indent=2)

    return {"accuracy": float(agg_acc), "auc": float(agg_auc), "mi_score": float(mi_score), "mi_auc_score": float(mi_auc_score)}

def generate_pairwise_masks(num_clients, net_template, scale=1e4, seed=42):
    """
    Secure Aggregation utility: Generates symmetric additive and subtractive noise.
    Hospitals i and j share a secret mask. One adds it, the other subtracts it. 
    They cancel out precisely at the server, revealing ONLY the sum perfectly.
    """
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
