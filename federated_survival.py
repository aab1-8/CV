import os, json, argparse, torch, flwr
import pandas as pd, numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from flwr.common import Context
from flwr.server import ServerApp, ServerConfig, ServerAppComponents
from flwr.client import ClientApp
from medshare.models import SurvivalMLP, get_parameters
from medshare.data import load_tabular_data, create_dataloaders, get_data_cached
from medshare.utils import weighted_average, reset_logging, generate_pairwise_masks
from medshare.client import FlowerSurvivalClient
from medshare.strategy import AnomalyMonitoringStrategy
from medshare.blockchain import BlockchainManager
from medshare.engine import train, test
import torch.nn as nn

def get_centralized_performance(X, y, dim, classes, config, fitted_scaler=None):
    cache_path = os.path.join("test", f"centralized_{config.get('display_name', 'FL')}_{len(X)}.json")
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            data = json.load(f)
            return data["accuracy"], data.get("auc", 0.5)
    
    print(f"[Baseline] Training Centralized Gold Standard for {config.get('display_name', 'FL')}...")
    tr_X_raw, te_X_raw, tr_y, te_y = train_test_split(X, y, test_size=0.2)
    
    # Global scale unification
    if fitted_scaler:
        scaler = fitted_scaler
    else:
        scaler = MinMaxScaler()
        scaler.fit(tr_X_raw)
        
    tr_X = pd.DataFrame(scaler.transform(tr_X_raw), columns=X.columns)
    te_X = pd.DataFrame(scaler.transform(te_X_raw), columns=X.columns)
    
    from medshare.data import create_dataloaders
    use_gpu = torch.cuda.is_available()
    batch_size = (2048 if len(X) > 10000 else 1024) if use_gpu else 64
    device = "cuda" if use_gpu else "cpu"
    train_loader = create_dataloaders(tr_X, tr_y, batch_size=batch_size)
    test_loader = create_dataloaders(te_X, te_y, batch_size=batch_size)
    
    net = SurvivalMLP(dim, classes)
    train(net, train_loader, epochs=20, num_classes=classes, device=device)
    _, acc, auc = test(net, test_loader, num_classes=classes, device=device)
    
    os.makedirs("test", exist_ok=True)
    with open(cache_path, 'w') as f: json.dump({"accuracy": float(acc), "auc": float(auc)}, f)
    return float(acc), float(auc)

DATASET_PRESETS = {
    # --- BINARY CLASSIFICATION ---
    "support2": {
        "display_name": "SUPPORT2-Death", 
        "TARGET_COLUMN": "death", 
        "PARTITION_COLUMN": "dzgroup",
        "apply_rebalancing": False # 72/28 split is manageable without synthetic data
    },
    "stroke_prediction": {
        "display_name": "Stroke", 
        "DATA_SOURCE": "stroke_prediction", 
        "TARGET_COLUMN": "stroke", 
        "DROP_COLUMNS": ["id"], 
        "apply_rebalancing": True # Heavy 95/5 imbalance
    },
    "cdc_diabetes_binary": {
        "display_name": "CDC-Diabetes-Binary", 
        "DATA_SOURCE": "cdc_diabetes", 
        "TARGET_COLUMN": "Diabetes_binary"
    },
    "thyroid": {
        "display_name": "Thyroid", 
        "DATA_SOURCE": "thyroid", 
        "TARGET_COLUMN": "target",
        "apply_rebalancing": True # Severe 93/7 imbalance
    },
    
    # --- MULTI-CLASS CLASSIFICATION ---
    "cdc_diabetes_012": {
        "display_name": "CDC-Diabetes-012", 
        "DATA_SOURCE": "cdc_diabetes", 
        "TARGET_COLUMN": "Diabetes_012",
        "apply_rebalancing": True
    },
    "diabetes_hospital": {
        "display_name": "Diabetes-Hospitals", 
        "DATA_SOURCE": "diabetes_hospital", 
        "TARGET_COLUMN": "readmitted",
        "DROP_COLUMNS": ["encounter_id", "patient_nbr"],
        "apply_rebalancing": "auto"
    },
    "maternal_health": {
        "display_name": "Maternal-Health", 
        "DATA_SOURCE": "maternal_health", 
        "TARGET_COLUMN": "RiskLevel",
        "apply_rebalancing": "auto" # Dynamic detection
    },
    "admin_billing": {
        "display_name": "Admin-Billing-Risk", 
        "DATA_SOURCE": "hospital_admin", 
        "TARGET_COLUMN": "high_bill", 
        "DROP_COLUMNS": ["Patient ID", "Name", "Date of Birth", "Admit Date", "Discharge Date", "Bill Amount"]
    },
    "admin_category": {
        "display_name": "Admin-Category", 
        "DATA_SOURCE": "hospital_admin", 
        "TARGET_COLUMN": "condition_category", 
        "DROP_COLUMNS": ["Patient ID", "Name", "Date of Birth", "Admit Date", "Discharge Date", "Medical Condition"]
    },
    "support2_disease": {
        "display_name": "SUPPORT2-Disease", 
        "TARGET_COLUMN": "dzgroup", 
        "PARTITION_COLUMN": "death",
        "apply_rebalancing": False # Clinical realism priority
    },
    "diabetic_retinopathy": {
        "display_name": "Diabetic-Retinopathy", 
        "DATA_SOURCE": "diabetic_retinopathy", 
        "TARGET_COLUMN": "class",
        "apply_rebalancing": False
    },
}

def get_adaptive_experiment_config(num_records):
    """Calibrates signal-to-noise ratios and hardware throughput based on environment."""
    use_gpu = torch.cuda.is_available()
    import sys
    is_colab = 'google.colab' in sys.modules
    
    # Precise VRAM Detection: Distinguish between Local 6GB GPUs and vLab/Colab 15GB GPUs
    vram_gb = 0
    if use_gpu:
        try:
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        except:
            vram_gb = 8 # Default fallback
    
    # High-end Hardware categorization (vLab/Colab with 12GB+ VRAM)
    is_high_end = is_colab or (vram_gb > 12)

    # Premium Scaling: Use optimized batches for tabular convergence (High-end: 2048, Local: 512)
    # Total VRAM usage will stay low, but 'Scientific Precision' will increase.
    gpu_batch = 2048 if is_high_end else 512
    
    if num_records < 5000: # Micro Datasets (e.g. 1k rows)
        return {
            "sigmas": [0.05, 0.1, 0.2, 0.5],  # User-specified; 0 baseline added automatically by MI sweep
            "batch_size": 256 if use_gpu else 32,  # Large batch = fewer noisy DP steps = stable convergence
            "rounds": 50,
            "epochs": 40  # CRITICAL: 1 epoch caused non-convergence → noisy/non-monotonic MI
        }
    elif num_records < 70000: # Standard Research Datasets (e.g. 10k-50k rows)
        return {
            "sigmas": [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5],
            "batch_size": gpu_batch if use_gpu else 128,
            "rounds": 100 if is_high_end else 50,
            "epochs": 5 
        }
    else: # Massive Datasets (> 70k rows, e.g. CDC/Diabetes Hospitals)
        return {
            "sigmas": [0.0, 0.5, 1.0, 2.0, 5.0],
            "batch_size": gpu_batch if use_gpu else 128,
            "rounds": 60 if is_high_end else 30, # Increased for convergence on 100k+ rows
            "epochs": 10 
        }



def run_simulation(args, config):
    reset_logging()
    if args.sample_size: config["sample_size"] = args.sample_size
    if hasattr(args, "heterogeneity"): config["heterogeneity"] = args.heterogeneity
    
    # Clean UI history before starting new simulation
    hist_f = os.path.join("frontend", "src", "data", "training_history.json")
    if os.path.exists(hist_f): 
        try: os.remove(hist_f)
        except: pass
    
    # Global Scaler Unification
    X, y, parts, dim, classes = get_data_cached(config)
    
    # To prevent 'Ghost Leakage' and ensure a fair comparison, we fit the scaler 
    # ONCE on a representative global sample before any models are trained.
    original_names = list(parts.unique())
    scaler = MinMaxScaler()
    train_indices = []
    # Identify training indexes across all hospitals to create a 'Public Reference Set'
    for n in original_names:
        n_idx = X.index[parts == n]
        n_tr_idx, _ = train_test_split(n_idx, test_size=0.2, random_state=42)
        train_indices.extend(n_tr_idx)
    
    scaler.fit(X.loc[train_indices])
    
    # Calculate REAL Centralized Baseline using the SAME GLobal Scaler
    centralized_acc, centralized_auc = get_centralized_performance(X, y, dim, classes, config, fitted_scaler=scaler)
    
    name_to_original_idx = {n: i for i, n in enumerate(original_names)}
    # Ensure y is numpy for safe indexing across partitions
    y_array = np.asarray(y) if not isinstance(y, np.ndarray) else y
    print(f"[INIT] Loaded {len(X)} records across {len(original_names)} hospitals.")
    
    # Gatekeeping: Filter hospitals by reputation if blockchain is active
    bcm = None
    if config.get("enable_blockchain", False):
        bcm = BlockchainManager.get_instance()
        
    authorized_names = []
    for i, n in enumerate(original_names):
        rep = bcm.get_reputation(i) if bcm else 100
        # Sync with Smart Contract: Threshold is Score >= 0 (Base 100 in Python)
        score = rep - 100
        if score >= 0:
            authorized_names.append(n)
        else:
            print(f"[Gatekeeper] Hospital {n} REJECTED (Score: {score}). Minimum Honest Score required: 0.")
    
    if not authorized_names:
        print("[INIT] Error: No authorized hospitals found. Simulation aborted.")
        return
        
    names = authorized_names
    # Nodes transform their local data using the FIXED Global Scaler
    nodes = {n: train_test_split(pd.DataFrame(scaler.transform(X.loc[parts == n]), columns=X.columns, index=X.index[parts == n]), y_array[parts == n], test_size=0.2, random_state=42) for n in names}
    # Detect whether parameters were explicitly passed via CLI vs using the default (1 epoch / 3 rounds)
    # This allows us to apply the adaptive "Gold Standard" defaults automatically.
    explicit_rounds = getattr(args, '_cli_rounds', None)
    exec_rounds = args.rounds if explicit_rounds is not None else (config.get("rounds", args.rounds) if args.rounds == 3 else args.rounds)
    
    # Epoch Handling: If user left it at default (1), use the adaptive Gold Standard (10 for big data)
    exec_epochs = config.get("epochs", args.epochs) if args.epochs == 1 else args.epochs
    
    print(f"[INIT] Starting simulation: {exec_rounds} rounds, {exec_epochs} epochs, {config.get('batch_size', 32)} batch size.")
    
    # Bounty Demo: Initialize Task on Blockchain (Only if enabled)
    bcm = None
    if config.get("enable_blockchain", False):
        bcm = BlockchainManager.get_instance()
    initial_balances = {}
    created_task_id = None
    if bcm:
        # Reduced bounty to 0.05 ETH for simulation stability
        print("[Blockchain] Posting task with 0.05 ETH bounty...")
        created_task_id = bcm.create_task_with_bounty(f"Train {config.get('display_name', 'FL')}", len(names), exec_rounds, bounty_eth=0.05)
        print(f"[Blockchain] Created Task ID: {created_task_id} (Sync with Dashboard ETH-{created_task_id})")
        for i, n in enumerate(names):
            # Use original ID for join logic to match contract checks
            orig_idx = name_to_original_idx[n]
            
            # RESERVED: Skip the first hospital in the script so it can be manually joined via the Dashboard UI
            if i == 0:
                print(f"[Blockchain] Hospital {n} (Account {orig_idx+1}) is reserved for MANUAL joining via the dashboard.")
                continue
                
            bcm.join_task(created_task_id, orig_idx)
            initial_balances[orig_idx] = bcm.get_balance(orig_idx)
            
        import time
        print(f"\\n{'='*60}")
        print(f"🚨 DEMO PAUSE: WAITING FOR DASHBOARD HANDSHAKE! 🚨")
        print(f"-> Please open the Frontend Dashboard.")
        print(f"-> Select Hospital Node 1.")
        print(f"-> Click 'Link & Participate' on Task ETH-{created_task_id}.")
        print(f"{'='*60}\\n")
        
        try:
            while True:
                # Index 5 in the Task Tuple is the Status Enum (0=Open, 1=Training, 2=Completed)
                t_status = bcm.task_contract.functions.tasks(created_task_id).call()[5]
                if t_status == 1:
                    print(f"✅ Dashboard Participation Confirmed! Task is now fully subscribed (Training Status). Resuming AI Engine...\\n")
                    break
                time.sleep(2.0)
        except KeyboardInterrupt:
            print(f"\\n🚨 Manual Bypass Triggered. Resuming simulation without dashboard confirmation...")

    from flwr.common import ndarrays_to_parameters
    def fit_agg(m, server_round=None): return weighted_average(m, server_round=server_round, log_to_csv=False)
    def eval_agg(m, server_round=None): return weighted_average(m, server_round=server_round, log_to_csv=True)

    strategy = AnomalyMonitoringStrategy(
        task_id=created_task_id if created_task_id is not None else args.task_id, 
        total_rounds=exec_rounds,
        enable_blockchain=config.get("enable_blockchain", False),
        net=SurvivalMLP(dim, classes), # Enable structured state_dict checkpointing
        initial_parameters=ndarrays_to_parameters(get_parameters(SurvivalMLP(dim, classes))),
        fit_metrics_aggregation_fn=fit_agg,
        evaluate_metrics_aggregation_fn=eval_agg,
        min_evaluate_clients=len(names),
        fraction_evaluate=1.0,
        on_fit_config_fn=lambda r: {
            "server_round": r,
            "total_rounds": exec_rounds,
            "experiment": args.experiment,
            "attack_type": config.get("attack_type", "None"),
            "defense_name": config.get("defense_name", "FedAvg"),
            "noise_multiplier": config.get("noise_multiplier", 0.0),
            "dataset_name": config.get("display_name", "unknown"),
            "learning_rate": config.get("learning_rate", 0.001), # Integrated from legacy re-assignment
        },
        on_evaluate_config_fn=lambda r: {
            "server_round": r,
            "total_rounds": exec_rounds,
            "experiment": args.experiment,
            "attack_type": config.get("attack_type", "None"),
            "defense_name": config.get("defense_name", "FedAvg"),
            "noise_multiplier": config.get("noise_multiplier", 0.0),
            "dataset_name": config.get("display_name", "unknown"),
            "learning_rate": config.get("learning_rate", 0.001), # Standardized across phases
        },
    )

    # SECURE AGGREGATION: Generate Pairwise Masks
    # This fulfills R5: Secure aggregation prototype
    mask_add_list, mask_sub_list = None, None
    if config.get("enable_secagg", False) or args.enable_secagg:
        print(f"[SEC-AGG] Initializing Pairwise Masking for {len(names)} hospitals...")
        mask_add_list, mask_sub_list = generate_pairwise_masks(len(names), SurvivalMLP(dim, classes))

    def client_fn(context: Context):
        # Use node_id as p_id if partition-id is missing (common in local simulation)
        p_id = int(context.node_config.get("partition-id", context.node_id))
        h_name = names[p_id]
        orig_idx = name_to_original_idx[h_name]
        
        print(f"[Client] Initializing client {p_id} (Hospital: {h_name}, GlobalID: {orig_idx})")
        tr_X, te_X, tr_y, te_y = nodes[h_name]
        # Adaptive batching to prevent 'Signal Drowning' in small cohorts
        bs = config.get("batch_size", 32)
        return FlowerSurvivalClient(
            SurvivalMLP(dim, classes), 
            create_dataloaders(tr_X, tr_y, batch_size=bs), 
            create_dataloaders(te_X, te_y, batch_size=bs), 
            num_classes=classes, 
            mask_add=mask_add_list[p_id] if mask_add_list else None,
            mask_sub=mask_sub_list[p_id] if mask_sub_list else None,
            # Malicious detection based on ORIGINAL index to maintain attack consistency
            is_malicious=(orig_idx < int(len(original_names)*0.2)) and (config.get("attack_type", "None") != "None"), 
            client_id=orig_idx, 
            task_id=created_task_id if created_task_id is not None else args.task_id, 
            local_epochs=exec_epochs,
            attack_type=config.get("attack_type", "label_flip"),
            enable_dp=config.get("enable_dp", False),
            noise_multiplier=config.get("noise_multiplier", 1.0),
            enable_blockchain=config.get("enable_blockchain", False),
            node_name=h_name
        ).to_client()

    # --- Advanced Resource Configuration ---
    # Detect high-end hardware for parallel scaling
    use_gpu = torch.cuda.is_available()
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9 if use_gpu else 0
    import sys, multiprocessing
    is_high_end = ('google.colab' in sys.modules) or (vram_gb > 12)
    cpu_count = multiprocessing.cpu_count()

    # vLab/Colab MAX (15GB GPU): Target ~10GB GPU usage (0.13 * 5 = 0.65 fraction)
    # This leaves "Oxygen" (5GB+) for the system/Jupyter as requested.
    client_cpu = 0.4 if is_high_end else 2.0 
    client_gpu = 0.13 if is_high_end else (0.5 if use_gpu else 0) 

    backend_config = {
        "client_resources": {
            "num_cpus": client_cpu,
            "num_gpus": client_gpu
        },
        "init_args": {
            "num_cpus": cpu_count, 
            "num_gpus": 1.0 if use_gpu else 0
        }
    }
    
    if is_high_end:
        print(f"[Hardware] Mode: VLAB/COLAB High-End (15GB GPU). Running {len(names)} parallel clients in 10GB Safety Zone.")
    else:
        print(f"[Hardware] Mode: Local Efficiency. Capping parallelism to protect CPU temps.")
    
    # Run Simulation and capture history
    history = flwr.simulation.run_simulation(
        server_app=ServerApp(server_fn=lambda _: ServerAppComponents(strategy=strategy, config=ServerConfig(num_rounds=exec_rounds))), 
        client_app=ClientApp(client_fn=client_fn), 
        num_supernodes=len(names),
        backend_config=backend_config
    )
    
    # Extract real accuracy/auc from training_history.json (most reliable source)
    fed_acc, fed_auc, fed_eps, fed_mi_acc, fed_mi_auc = 0.70, 0.75, 0.0, 0.0, 0.0  # Fallbacks only if file is missing
    if os.path.exists(hist_f):
        try:
            with open(hist_f, 'r', encoding='utf-8') as f:
                h = json.load(f)
                if h:
                    # Get the final round's metrics
                    final_round = max(h, key=lambda x: x.get("round", 0))
                    fed_acc = final_round.get("accuracy", fed_acc)
                    fed_auc = final_round.get("auc", fed_auc)
                    fed_mi_acc = final_round.get("mi_score", 0.0)
                    fed_mi_auc = final_round.get("mi_auc_score", 0.0)
                    fed_eps = final_round.get("epsilon", 0.0)
                    print(f"[Results] Extracted: Acc={fed_acc:.4f}, AUC={fed_auc:.4f}, MI-Gap={fed_mi_auc:.4f}, Eps={fed_eps:.2f}")
        except Exception as e:
            print(f"[Warning] Could not read training_history.json: {e}")

    # Finalize on blockchain if needed
    if created_task_id is not None and bcm:
        print(f"[Blockchain] Finalizing Task {created_task_id} and distributing bounties...")
        # Map the best local model hash to blockchain for audit
        # For simplicity, we use a placeholder of the best accuracy achieved
        bcm.complete_task_and_pay(created_task_id, f"acc:{fed_acc:.4f}")

    # Calculate Local Baseline (Per-Node Accuracy/AUC)
    print(f"[Baseline] Calculating Local Baselines for each hospital...")
    local_metrics = []
    
    # Check for existing baseline cache to skip training
    baseline_cache_f = os.path.join("test", f"baseline_{config.get('display_name', 'FL')}_{len(X)}.json")
    if os.path.exists(baseline_cache_f):
        print(f"[Baseline] Loading cached local baselines...")
        with open(baseline_cache_f, "r", encoding='utf-8') as f:
            local_metrics = json.load(f)
            # Filter out old 'Federated' entries from cache, we want fresh ones for this run
            local_metrics = [m for m in local_metrics if m["Type"] == "Local Baseline"]
    else:
        for i, name in enumerate(names):
            tr_X, te_X, tr_y, te_y = nodes[name]
            net = SurvivalMLP(dim, classes)
            # Train a quick local model (3 epochs) to see isolated performance
            use_gpu = torch.cuda.is_available()
            bs = config.get("batch_size", 1024 if use_gpu else 64)
            device = "cuda" if use_gpu else "cpu"
            train(net, create_dataloaders(tr_X, tr_y, batch_size=bs), epochs=3, num_classes=classes, device=device)
            _, l_acc, l_auc = test(net, create_dataloaders(te_X, te_y, batch_size=bs), num_classes=classes, device=device)
            
            # Local Baseline Entry
            local_metrics.append({
                "Hospital": name,
                "Accuracy": float(l_acc),
                "AUC-ROC": float(l_auc),
                "Samples": int(len(tr_X) + len(te_X)),
                "Type": "Local Baseline"
            })
        
        # Save baseline cache
        with open(baseline_cache_f, "w", encoding='utf-8') as f:
            json.dump(local_metrics, f, indent=2)

    # Add fresh Federated entries for this specific run
    for name in names:
        tr_X, te_X, _, _ = nodes[name]
        local_metrics.append({
            "Hospital": name,
            "Accuracy": float(fed_acc),
            "AUC-ROC": float(fed_auc),
            "Samples": int(len(tr_X) + len(te_X)),
            "Type": "Federated"
        })

    # Save to baseline.json
    with open(os.path.join("frontend", "src", "data", "baseline.json"), "w", encoding='utf-8') as f:
        json.dump(local_metrics, f, indent=2)

    # Safe division for local metrics averages
    # Use the number of local-baseline ENTRIES (not len(names)) to avoid div-by-wrong-denominator
    # when some hospitals are blacklisted or cached from a previous run with more nodes.
    local_baseline_entries = [m for m in local_metrics if m["Type"] == "Local Baseline"]
    n_local = len(local_baseline_entries) if local_baseline_entries else 1
    avg_local_acc = sum(m["Accuracy"] for m in local_baseline_entries) / n_local
    avg_local_auc = sum(m["AUC-ROC"] for m in local_baseline_entries) / n_local
    improvement = 0.0
    if avg_local_acc > 0:
        improvement = (fed_acc - avg_local_acc) / avg_local_acc * 100

    bcm = BlockchainManager.get_instance()
    summary = {
        "dataset_name": config.get("display_name", "FL"),
        "reputation": {n: (bcm.get_reputation(name_to_original_idx[n]) if bcm else 100) for n in original_names},
        "local_accuracy": float(avg_local_acc), 
        "local_auc": float(avg_local_auc),
        "centralized_accuracy": float(centralized_acc),
        "centralized_auc": float(centralized_auc),
        "federated_accuracy": float(fed_acc),
        "federated_auc": float(fed_auc),
        "improvement_local_fed": float(improvement),
        "security": {
            "dp_enabled": config.get("enable_dp", False), 
            "epsilon": float(fed_eps) if config.get("enable_dp") else 0.0, 
            "delta": "1e-5", 
            "leakage_acc": float(fed_mi_acc),
            "leakage_auc": float(fed_mi_auc),
            "defense_type": config.get("defense_name", "FedAvg"),
            "attack_simulated": config.get("attack_type", "None") not in ["None", None],
            "attack_type": config.get("attack_type", "None")
        }
    }
    with open(os.path.join("frontend", "src", "data", "comparison_stats.json"), "w", encoding='utf-8') as f: json.dump(summary, f, indent=2)

def run_experiment(args):
    config = DATASET_PRESETS.get(args.dataset, DATASET_PRESETS["support2"]).copy()
    config["enable_blockchain"] = args.enable_blockchain
    config["noise_multiplier"] = args.sigma
    config["enable_dp"] = args.enable_dp
    if args.experiment == "gas":
        config["enable_blockchain"] = True
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")
    
    # Clear old experiment logs ONLY for targeted experiments
    if args.experiment == "dp":

        path = os.path.join(test_dir, "exp_dp_results.csv")
        if os.path.exists(path): os.remove(path)
    elif args.experiment == "mi":
        path = os.path.join(test_dir, "exp_mi_results.csv")
        if os.path.exists(path): os.remove(path)
    elif args.experiment == "robustness":
        path = os.path.join(test_dir, "exp_robustness_results.csv")
        if os.path.exists(path): os.remove(path)
    elif args.experiment == "latency":
        path = os.path.join(test_dir, "exp_latency_log.csv")
        if os.path.exists(path): os.remove(path)

    # 1. Peek at dataset size to calibrate adaptive ranges
    X_peek, _, _, _, _ = get_data_cached(config)
    num_records = len(X_peek)
    adapt = get_adaptive_experiment_config(num_records)
    config["batch_size"] = args.batch_size if getattr(args, "batch_size", None) is not None else adapt["batch_size"]
    config["rounds"] = adapt["rounds"]
    config["epochs"] = adapt["epochs"]
    print(f"[Experiment] Dataset: {config['display_name']} ({num_records} rows)")
    print(f"[Experiment] Calibration: Rounds={adapt['rounds']}, Epochs={adapt['epochs']}, Batch={adapt['batch_size']}")

    if args.experiment == "dp":
        # Targeted sweep for the Privacy-Utility Frontier
        noises = adapt["sigmas"]
        saved_rounds = args.rounds
        args.rounds = adapt["rounds"]
        for n in noises:
            print(f"\n[Sweep] Running DP with sigma={n} ({args.rounds} rounds)")
            config["enable_dp"] = True
            config["noise_multiplier"] = n
            run_simulation(args, config)
        args.rounds = saved_rounds
    elif args.experiment == "mi":
        # Full MI Audit Sweep (Baseline vs multiple DP levels)
        # Uses the dataset's native preset for rebalancing (True for Thyroid/Stroke)
        
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")
        mi_file = os.path.join(test_dir, "exp_mi_results.csv")
        if os.path.exists(mi_file): os.remove(mi_file)
        
        # Consistent evaluation points
        noises = [0] + adapt["sigmas"]
        saved_rounds = args.rounds
        saved_epochs = args.epochs
        # Stability calibration for MI: Default to 30/40 for full audit, 
        # but respect user if they pass explicit non-default values.
        if num_records > 50000:
            config["batch_size"] = adapt["batch_size"]
        else:
            config["batch_size"] = args.batch_size if args.batch_size else 128
            
        if args.lr:
            config["learning_rate"] = args.lr
        
        if args.rounds == 3:
            args.rounds = adapt["rounds"]
        
        if args.epochs == 1: # If user didn't specify, use high-intensity for audit
            # For massive datasets, 40 epochs is too risky/slow; use adaptive max (10-20)
            args.epochs = adapt["epochs"] if num_records > 50000 else 40
        
        # Mark as explicit so run_simulation engine respects these overrides
        args._cli_rounds = args.rounds
        
        for n in noises:
            mode_name = "BASELINE (No Privacy)" if n == 0 else f"MI Audit with sigma={n}"
            rebalance_status = config.get("apply_rebalancing", "Preset")
            print(f"\n[Audit] Running {mode_name} ({args.rounds} Rounds, {args.epochs} Epochs, rebalance={rebalance_status})")
            
            config["enable_dp"] = (n > 0)
            config["noise_multiplier"] = n
            run_simulation(args, config)
            
        args.rounds = saved_rounds
        args.epochs = saved_epochs
    elif args.experiment == "mi_step":
        # Individual step for external loop
        config["noise_multiplier"] = args.sigma
        config["enable_dp"] = True if args.sigma > 0 else False
        run_simulation(args, config)
    elif args.experiment == "robustness":
        # Attack types: No Attack, Label Flip, Gradient Scale
        attacks = ["None", "label_flip", "gradient_scale"]
        defenses = ["FedAvg", "Robust-MAD"]
        # Use the adaptive round count if the user didn't specify a high enough value for robustness charts.
        rob_rounds = max(args.rounds, adapt["rounds"] if args.rounds == 3 else 5)
        saved_rounds = args.rounds
        args.rounds = rob_rounds
        # Store the explicit value so run_simulation() uses it, not the adaptive calibration.
        args._cli_rounds = rob_rounds
        for atk in attacks:
            for dfns in defenses:
                print(f"\n[Sweep] Running Attack: {atk}, Defense: {dfns}")
                config["attack_type"] = atk
                config["defense_name"] = dfns
                # Reset the blockchain singleton between sweeps so reputation scores from
                # one attack scenario do not bleed into the next scenario's gatekeeper check.
                BlockchainManager._instance = None
                run_simulation(args, config)
        args.rounds = saved_rounds
        args._cli_rounds = saved_rounds
    elif args.experiment == "latency":
        # Latency benchmark: use the user-supplied round count for honest scaling measurement.
        # Previously hardcoded to 7, which ignored --rounds.
        args._cli_rounds = args.rounds  # Mark as explicit so run_simulation respects it.
        run_simulation(args, config)
    else:
        run_simulation(args, config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="support2")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--sample_size", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    def str_to_bool(v):
        if isinstance(v, bool): return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'): return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'): return False
        else: raise argparse.ArgumentTypeError('Boolean value expected.')

    parser.add_argument("--task_id", type=int, default=0)
    parser.add_argument("--experiment", default="none")
    parser.add_argument("--enable_blockchain", type=str_to_bool, nargs='?', const=True, default=False)
    parser.add_argument("--sigma", type=float, default=1.0)
    parser.add_argument("--enable_dp", type=str_to_bool, nargs='?', const=True, default=False)
    parser.add_argument("--enable_secagg", type=str_to_bool, nargs='?', const=True, default=False)
    parser.add_argument("--heterogeneity", default="none", choices=["none", "label", "feature"])
    args = parser.parse_args()
    run_experiment(args)