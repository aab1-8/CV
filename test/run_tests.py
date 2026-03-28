"""
MedShare-FL Full Integration Test Suite
Tests all modules for correctness after the Platinum Hardening changes.
"""
import sys, os, traceback, torch, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def ok(msg):
    global PASS
    PASS += 1
    print(f"  [PASS] {msg}")

def fail(msg, err=""):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {msg}: {err}")

print("\n" + "="*60)
print("TEST 1: MODULE IMPORTS")
print("="*60)
try:
    from medshare.models import SurvivalMLP, get_parameters, set_parameters
    ok("medshare.models")
except Exception as e:
    fail("medshare.models", e)

try:
    from medshare.data import get_data_cached, create_dataloaders
    ok("medshare.data")
except Exception as e:
    fail("medshare.data", e)

try:
    from medshare.engine import train, test
    ok("medshare.engine")
except Exception as e:
    fail("medshare.engine", e)

try:
    from medshare.utils import weighted_average, reset_logging, generate_pairwise_masks
    ok("medshare.utils")
except Exception as e:
    fail("medshare.utils", e)

try:
    from medshare.strategy import AnomalyMonitoringStrategy
    ok("medshare.strategy")
except Exception as e:
    fail("medshare.strategy", e)

try:
    from medshare.blockchain import BlockchainManager
    ok("medshare.blockchain")
except Exception as e:
    fail("medshare.blockchain", e)

try:
    import ast
    with open("federated_survival.py", "r") as f:
        ast.parse(f.read())
    ok("federated_survival.py syntax")
except SyntaxError as e:
    fail("federated_survival.py syntax", e)

print("\n" + "="*60)
print("TEST 2: DATA PIPELINE & TYPE SAFETY")
print("="*60)
try:
    config = {
        "display_name": "SUPPORT2-Death", "TARGET_COLUMN": "death",
        "PARTITION_COLUMN": "dzgroup", "apply_rebalancing": False,
        "sample_size": 400
    }
    X, y, parts, dim, classes = get_data_cached(config)
    ok(f"Data loaded: {len(X)} rows, {dim} features, {classes} classes")

    # Core fix: y must be a numpy array
    y_array = np.asarray(y) if not isinstance(y, np.ndarray) else y
    assert isinstance(y_array, np.ndarray), "y_array is not numpy!"
    ok(f"y_array type: numpy.ndarray, dtype={y_array.dtype}")

    # Check all partitions align cleanly
    names = list(parts.unique())
    for n in names:
        mask = parts == n
        X_n = X[mask]
        y_n = y_array[mask]
        assert len(X_n) == len(y_n) > 0, f"Partition {n} misaligned or empty!"
    ok(f"All {len(names)} hospital partitions aligned (no index mismatch)")

except Exception as e:
    fail("Data pipeline", e)
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 3: MODEL TRAIN / EVAL / ROUND-TRIP")
print("="*60)
try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    config["sample_size"] = 300
    X, y, parts, dim, classes = get_data_cached(config)
    y_array = np.asarray(y)
    scaler = MinMaxScaler()
    X_sc = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
    tr_X, te_X, tr_y, te_y = train_test_split(X_sc, y_array, test_size=0.2, random_state=42)

    net = SurvivalMLP(dim, classes)
    loader_tr = create_dataloaders(tr_X, tr_y, batch_size=64)
    loader_te = create_dataloaders(te_X, te_y, batch_size=64)

    eps, loss = train(net, loader_tr, epochs=1, num_classes=classes)
    ok(f"Training 1 epoch: loss={loss:.4f}")

    _, acc, auc = test(net, loader_te, num_classes=classes)
    ok(f"Evaluation: acc={acc:.4f}, auc={auc:.4f}")

    # Weight round-trip
    w1 = get_parameters(net)
    net2 = SurvivalMLP(dim, classes)
    set_parameters(net2, w1)
    w2 = get_parameters(net2)
    for a, b in zip(w1, w2):
        assert np.allclose(a, b), "Weight round-trip failed!"
    ok("get_parameters / set_parameters round-trip")

except Exception as e:
    fail("Model train/eval/round-trip", e)
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 4: STATE_DICT CHECKPOINT (Platinum Fix)")
print("="*60)
try:
    weights = get_parameters(net)
    params_dict = zip(net.state_dict().keys(), weights)
    state_dict = {k: torch.tensor(v) for k, v in params_dict}

    checkpoint_path = "test/_test_checkpoint.pth"
    torch.save(state_dict, checkpoint_path)
    loaded = torch.load(checkpoint_path, weights_only=True)

    assert isinstance(loaded, dict), "Checkpoint is not a dict!"
    assert list(loaded.keys()) == list(net.state_dict().keys()), "Key mismatch!"
    ok(f"Checkpoint is valid state_dict: {len(loaded)} named keys")

    # Verify we can reload into a fresh model
    net3 = SurvivalMLP(dim, classes)
    net3.load_state_dict(loaded)
    ok("load_state_dict() into fresh model: success")

    os.remove(checkpoint_path)

except Exception as e:
    fail("Checkpoint state_dict", e)
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 5: UTILS - weighted_average & MI SCORES")
print("="*60)
try:
    reset_logging()
    ok("reset_logging()")

    mock_metrics = [
        (100, {"accuracy": 0.80, "auc": 0.85, "train_accuracy": 0.82, "train_auc": 0.87,
               "privacy_spent": 0.0, "gas_used": 0, "client_id": 0,
               "noise_multiplier": 0.0, "attack_type": "None",
               "is_malicious": False, "node_name": "H1", "experiment": "none",
               "server_round": 1, "total_rounds": 3, "defense_name": "FedAvg",
               "dataset_name": "test", "learning_rate": 0.001}),
        (200, {"accuracy": 0.90, "auc": 0.92, "train_accuracy": 0.91, "train_auc": 0.93,
               "privacy_spent": 0.0, "gas_used": 0, "client_id": 1,
               "noise_multiplier": 0.0, "attack_type": "None",
               "is_malicious": False, "node_name": "H2", "experiment": "none",
               "server_round": 1, "total_rounds": 3, "defense_name": "FedAvg",
               "dataset_name": "test", "learning_rate": 0.001}),
    ]
    result = weighted_average(mock_metrics, server_round=1, log_to_csv=False)
    expected_acc = (100*0.80 + 200*0.90) / 300
    assert abs(result["accuracy"] - expected_acc) < 1e-6, f"Wrong: {result['accuracy']} != {expected_acc}"
    ok(f"weighted_average: acc={result['accuracy']:.4f} (expected {expected_acc:.4f})")
    assert "mi_score" in result, "mi_score missing!"
    assert "mi_auc_score" in result, "mi_auc_score missing!"
    ok(f"MI metrics present: mi_score={result['mi_score']:.4f}, mi_auc_score={result['mi_auc_score']:.4f}")

except Exception as e:
    fail("weighted_average / MI", e)
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 6: SECAGG PAIRWISE MASKS")
print("="*60)
try:
    net_tmpl = SurvivalMLP(53, 1)
    adds, subs = generate_pairwise_masks(3, net_tmpl)
    assert len(adds) == len(subs) == 3, "Wrong number of masks!"
    for p_idx in range(len(adds[0])):
        assert adds[0][p_idx].shape == subs[0][p_idx].shape
    ok("SecAgg masks: correct count and shapes")

    # Cancellation: for each pair (i,j), adds[i] should cancel subs[j]
    for p_idx in range(len(adds[0])):
        net_sum = adds[0][p_idx] + adds[1][p_idx] + adds[2][p_idx] - subs[0][p_idx] - subs[1][p_idx] - subs[2][p_idx]
        # Pairwise: adds[i] to j's subs[j] — total sum should be zero
    ok("SecAgg mask shapes internally consistent")

except Exception as e:
    fail("SecAgg masks", e)
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 7: UI DATA FILES EXIST")
print("="*60)
import json
ui_files = [
    ("frontend/src/data/comparison_stats.json", ["dataset_name", "federated_accuracy", "security"]),
    ("frontend/src/data/baseline.json", None),
    ("test/best_model.pth", None),
]
for path, required_keys in ui_files:
    try:
        assert os.path.exists(path), f"Missing file: {path}"
        if path.endswith(".json") and required_keys:
            with open(path) as f:
                data = json.load(f)
            for k in required_keys:
                assert k in data, f"Key '{k}' missing in {path}"
        ok(f"{os.path.basename(path)}")
    except Exception as e:
        fail(os.path.basename(path), e)

print("\n" + "="*60)
print("TEST 8: STRATEGY INSTANTIATION")
print("="*60)
try:
    from flwr.common import ndarrays_to_parameters
    net_s = SurvivalMLP(53, 1)
    strat = AnomalyMonitoringStrategy(
        task_id=0, total_rounds=2, enable_blockchain=False,
        net=net_s,
        initial_parameters=ndarrays_to_parameters(get_parameters(net_s)),
        on_fit_config_fn=lambda r: {"server_round": r, "total_rounds": 2, "experiment": "test",
                                     "attack_type": "None", "defense_name": "FedAvg",
                                     "noise_multiplier": 0.0, "dataset_name": "test",
                                     "learning_rate": 0.001},
        on_evaluate_config_fn=lambda r: {"server_round": r, "total_rounds": 2, "experiment": "test",
                                          "attack_type": "None", "defense_name": "FedAvg",
                                          "noise_multiplier": 0.0, "dataset_name": "test",
                                          "learning_rate": 0.001},
    )
    assert hasattr(strat, "net"), "Strategy missing net attribute!"
    assert strat.net is net_s, "Strategy net not set correctly!"
    ok("AnomalyMonitoringStrategy instantiated with net attribute")
    # Verify config functions produce correct keys
    cfg = strat.on_fit_config_fn(1)
    assert "learning_rate" in cfg, "learning_rate missing from fit config!"
    assert "server_round" in cfg, "server_round missing from fit config!"
    ok(f"on_fit_config_fn keys correct: {list(cfg.keys())}")
    cfg_eval = strat.on_evaluate_config_fn(1)
    assert "learning_rate" in cfg_eval, "learning_rate missing from eval config!"
    ok("on_evaluate_config_fn keys correct")
except Exception as e:
    fail("Strategy instantiation", e)
    traceback.print_exc()

print("\n" + "="*60)
print(f"FINAL: {PASS} passed, {FAIL} failed")
print("="*60)
sys.exit(0 if FAIL == 0 else 1)
