print("[Module] Loading medshare.strategy")
import numpy as np, flwr, os, json, traceback, torch
from flwr.common import parameters_to_ndarrays
from .blockchain import BlockchainManager

class AnomalyMonitoringStrategy(flwr.server.strategy.FedAvg):
    def __init__(self, task_id=0, total_rounds=3, enable_blockchain=False, fit_metrics_aggregation_fn=None, evaluate_metrics_aggregation_fn=None, *args, **kwargs):
        super().__init__(
            fit_metrics_aggregation_fn=fit_metrics_aggregation_fn, 
            evaluate_metrics_aggregation_fn=evaluate_metrics_aggregation_fn,
            *args, **kwargs
        )
        self.task_id = task_id
        self.total_rounds = total_rounds
        self.enable_blockchain = enable_blockchain
        self.latest_weights = None
        self.best_acc = 0.0 # Track best accuracy across rounds

    def aggregate_fit(self, server_round, results, failures):
        try:
            # 0. Universal Sanity Check (Prevents NaN crashes across all strategies)
            valid_results = []
            for proxy, res in results:
                arrays = parameters_to_ndarrays(res.parameters)
                if any(np.isnan(a).any() or np.isinf(a).any() for a in arrays):
                    print(f"[Sanity] Warning: Client {proxy.node_id} sent NaN/Inf weights. Excluding client from aggregation.")
                    # Do not append to valid_results, effectively excluding it
                else:
                    valid_results.append((proxy, res))
            results = valid_results

            bcm = BlockchainManager.get_instance()
            # Initialize default returns to prevent UnboundLocalError
            agg_weights = None
            metrics_aggregated = {}
            if not results:
                return None, {}

            # Call aggregation function with explicit round number (triggers utils.weighted_average)
            if self.fit_metrics_aggregation_fn:
                metrics = [(res.num_examples, res.metrics) for _, res in results]
                metrics_aggregated = self.fit_metrics_aggregation_fn(metrics, server_round=server_round)

            # Get defense name from first client's metrics if available
            defense_name = results[0][1].metrics.get("defense_name", "FedAvg")
            
            # Anomaly Detection Logic (only if defense is Robust-MAD)
            if defense_name == "Robust-MAD":
                norms = [np.linalg.norm(np.concatenate([p.flatten() for p in parameters_to_ndarrays(r.parameters)])) for _, r in results]
                
                # Robust Median-based filtering (Resistant to Outlier Masking)
                med_norm = np.median(norms)
                mad = np.median([abs(n - med_norm) for n in norms]) # Median Absolute Deviation
                
                # We drop updates that are significantly larger than the median.
                # Threshold: Median + 3.0 * MAD (standard robust statistical limit)
                # We also add a small safety epsilon (0.1 * med_norm) to MAD to prevent 
                # dropping healthy clients when the group is perfectly uniform.
                threshold = med_norm + 3.0 * (mad + 0.1 * med_norm)
                
                filtered_results = []
                for i, (proxy, res) in enumerate(results):
                    c_id = int(res.metrics.get("client_id", proxy.node_id))
                    norm = norms[i]
                    # An update is malicious if it's way outside the median norm
                    # AND is large enough to be a threat (>10.0 scale)
                    is_malicious = norm > threshold and norm > (med_norm * 2.5)
                    
                    if bcm:
                        if is_malicious: bcm.update_reputation(c_id, -10, "Anomaly")
                        else: bcm.update_reputation(c_id, 1, "Participation")
                    
                    if not is_malicious:
                        filtered_results.append((proxy, res))
                    else:
                        print(f"[Defense] Catching outlier client {c_id} (norm: {norm:.2f}, median_baseline: {med_norm:.2f}, limit: {threshold:.2f})")
                
                # Ensure we have at least one client left
                if filtered_results:
                    results = filtered_results
                else:
                    print("[Defense] All clients flagged. Keeping the one closest to median.")
                    closest_idx = np.argmin([abs(n - med_norm) for n in norms])
                    results = [results[closest_idx]]

            agg_weights, _ = super().aggregate_fit(server_round, results, failures)
            if agg_weights:
                self.latest_weights = parameters_to_ndarrays(agg_weights)
                if self.enable_blockchain and bcm:
                    bcm.post_model_hash(self.task_id, self.latest_weights)
                    
                    # Finalize task ONLY in the final round to distribute bounty
                    if server_round >= self.total_rounds:
                        bcm.finalize_task(self.task_id, self.latest_weights)
            
            return agg_weights, metrics_aggregated
        except Exception as e:
            print(f"[Strategy] CRASH in Round {server_round}: {str(e)}")
            traceback.print_exc()
            raise e

    def aggregate_evaluate(self, server_round, results, failures):
        try:
            metrics_aggregated = {}
            if results and self.evaluate_metrics_aggregation_fn:
                metrics = [(res.num_examples, res.metrics) for _, res in results]
                metrics_aggregated = self.evaluate_metrics_aggregation_fn(metrics, server_round=server_round)
                
                # Model Checkpointing: Save the model if it's the best evaluated so far
                current_acc = metrics_aggregated.get("accuracy", 0.0)
                if current_acc >= self.best_acc or self.best_acc == 0.0:
                    try:
                        self.best_acc = current_acc
                        if self.latest_weights is not None:
                            checkpoint_dir = os.path.join(os.getcwd(), "test")
                            os.makedirs(checkpoint_dir, exist_ok=True)
                            checkpoint_path = os.path.join(checkpoint_dir, "best_model.pth")
                            torch.save(self.latest_weights, checkpoint_path)
                            print(f"[Strategy] New BEST Evaluation model saved (Acc: {current_acc:.4f})")
                    except Exception as e:
                        print(f"[Strategy] Checkpoint failed: {e}")
            
            loss, _ = super().aggregate_evaluate(server_round, results, failures)
            return loss, metrics_aggregated
        except Exception as e:
            print(f"[Strategy] Evaluate Error in Round {server_round}: {str(e)}")
            return None, {}
