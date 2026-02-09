print("[Module] Loading medshare.strategy")
import numpy as np, flwr, os, json, traceback
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

    def aggregate_fit(self, server_round, results, failures):
        try:
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
            
            # Anomaly Detection Logic (only if defense is Trimmed-Avg)
            if defense_name == "Trimmed-Avg":
                norms = [np.linalg.norm(np.concatenate([p.flatten() for p in parameters_to_ndarrays(r.parameters)])) for _, r in results]
                mu, sigma = np.mean(norms), np.std(norms)
                threshold = mu + 2.0 * sigma
                
                filtered_results = []
                for i, (proxy, res) in enumerate(results):
                    is_malicious = norms[i] > threshold and norms[i] > 10.0
                    if bcm:
                        if is_malicious: bcm.update_reputation(int(proxy.node_id), -10, "Anomaly")
                        else: bcm.update_reputation(int(proxy.node_id), 1, "Participation")
                    
                    if not is_malicious:
                        filtered_results.append((proxy, res))
                    else:
                        print(f"[Defense] Dropping malicious update from client {proxy.node_id} (norm: {norms[i]:.2f})")
                
                results = filtered_results

            agg_weights, _ = super().aggregate_fit(server_round, results, failures)
            if agg_weights:
                self.latest_weights = parameters_to_ndarrays(agg_weights)
                if self.enable_blockchain and bcm:
                    # Register model hash for audit trail every round
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
            loss, _ = super().aggregate_evaluate(server_round, results, failures)
            return loss, metrics_aggregated
        except Exception as e:
            print(f"[Strategy] Evaluate Error in Round {server_round}: {str(e)}")
            return None, {}
