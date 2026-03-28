print("[Module] Loading medshare.strategy") # Debug info for process monitoring
import numpy as np, flwr, os, json, traceback, torch # Federated and data utilities
from flwr.common import parameters_to_ndarrays # Translates bytes to NumPy weights
from .blockchain import BlockchainManager # The decentralized trust ledger

class AnomalyMonitoringStrategy(flwr.server.strategy.FedAvg):
    """
    A Secure & Robust Strategy that monitors hospitals for malicious updates.
    Extends standard FedAvg with Robust-MAD (Median Absolute Deviation).
    """
    def __init__(self, task_id=0, total_rounds=3, enable_blockchain=False, net=None, fit_metrics_aggregation_fn=None, evaluate_metrics_aggregation_fn=None, *args, **kwargs):
        # Initialize standard Flower FedAvg parameters
        super().__init__(
            fit_metrics_aggregation_fn=fit_metrics_aggregation_fn, 
            evaluate_metrics_aggregation_fn=evaluate_metrics_aggregation_fn,
            *args, **kwargs
        )
        self.task_id = task_id # Used to link results to the Blockchain study
        self.total_rounds = total_rounds # When to finalize the Ethereum Bounty
        self.enable_blockchain = enable_blockchain # Toggle for decentralized audit mode
        self.net = net # Reference to the model architecture for state_dict checkpointing
        self.latest_weights = None # Keeps best global model in memory for checkpointing
        self.best_acc = 0.0 # Track best accuracy for checkpointing logic

    def aggregate_fit(self, server_round, results, failures):
        """
        Gathers updates from all hospitals and performs Robust Averaging.
        """
        try:
            # Step 1: UNIVERSAL SANITY CHECK (Protecting server from NaN/Inf crashes)
            # sanity check: exclude nodes with NaN/Inf updates (ORIGINAL COMMENT PRESERVED)
            valid_results = []
            for proxy, res in results:
                # Extract numerical weights from the client's packet
                arrays = parameters_to_ndarrays(res.parameters)
                # If any hospital sends a 'NaN' (Not-A-Number) weight, we drop them immediately
                if any(np.isnan(a).any() or np.isinf(a).any() for a in arrays):
                    print(f"[Sanity] Warning: Client {proxy.node_id} sent NaN/Inf weights. Excluding.")
                else:
                    valid_results.append((proxy, res))
            results = valid_results

            # Step 2: Blockchain Initialization
            bcm = BlockchainManager.get_instance()
            agg_weights = None
            metrics_aggregated = {}
            if not results: return None, {} # Return if zero nodes participated

            # Step 3: Global Metric Aggregation (Calls weighted_average in utils.py)
            if self.fit_metrics_aggregation_fn:
                metrics = [(res.num_examples, res.metrics) for _, res in results]
                metrics_aggregated = self.fit_metrics_aggregation_fn(metrics, server_round=server_round)

            # Step 4: Defense Mechanism: Robust-MAD (Median Absolute Deviation)
            # This identifies 'Gradient Scaling' and 'Poisoning' attacks
            # Anomaly Detection Logic (only if defense is Robust-MAD) (ORIGINAL COMMENT PRESERVED)
            defense_name = results[0][1].metrics.get("defense_name", "FedAvg")
            
            if defense_name == "Robust-MAD":
                # A. Calculate the 'Norm' (Size) of every hospital's weight update
                norms = [np.linalg.norm(np.concatenate([p.flatten() for p in parameters_to_ndarrays(r.parameters)])) for _, r in results]
                
                # B. Find the 'Median Update' - extremely robust against outliers
                med_norm = np.median(norms)
                # C. Calculate the Median Absolute Deviation (MAD): how much do hospitals vary?
                mad = np.median([abs(n - med_norm) for n in norms]) 
                
                # D. Set an Anomaly Threshold: Median + 3.0 * MAD
                # This is a standard robust statistical limit for outliers (3 Sigmas)
                threshold = med_norm + 3.0 * (mad + 0.1 * med_norm)
                
                filtered_results = []
                for i, (proxy, res) in enumerate(results):
                    c_id = int(res.metrics.get("client_id", proxy.node_id))
                    norm = norms[i]
                    # E. An update is malicious if it's way outside the median norm 
                    # and significantly larger (>2.5x) than the healthy baseline.
                    is_malicious = norm > threshold and norm > (med_norm * 2.5)
                    
                    # F. Update Reputation on the Ethereum Smart Contract
                    if bcm:
                        if is_malicious: 
                            # Dock points from the hospital's reputation (SLSH)
                            bcm.update_reputation(c_id, -10, "Anomaly")
                        else: 
                            # Award points for honest participation
                            bcm.update_reputation(c_id, 1, "Participation")
                    
                    if not is_malicious:
                        # Only keep healthy, non-poisoned nodes for the global average
                        filtered_results.append((proxy, res))
                    else:
                        print(f"[Defense] Catching outlier client {c_id} (norm: {norm:.2f}, limit: {threshold:.2f})")
                
                # G. Fallback: If everyone is suspicious, keep the one closest to 'average behavior'
                if filtered_results: results = filtered_results
                else:
                    closest_idx = np.argmin([abs(n - med_norm) for n in norms])
                    print(f"[Defense] Warning: All clients flagged as outliers. Using client {closest_idx} (closest to median norm {med_norm:.2f}).")
                    results = [results[closest_idx]]

            # Step 5: Perform the actual FedAvg (Weighting updates by dataset size)
            agg_weights, _ = super().aggregate_fit(server_round, results, failures)
            
            # Step 6: Post-Aggregation Blockchain Commitments
            if agg_weights:
                self.latest_weights = parameters_to_ndarrays(agg_weights)
                if self.enable_blockchain and bcm:
                    # Record the final "Global Knowledge" hash to Ethereum
                    bcm.post_model_hash(self.task_id, self.latest_weights)
                    # FINAL ROUND: Trigger the Smart Contract to distribute the Bounty
                    if server_round >= self.total_rounds:
                        bcm.finalize_task(self.task_id, self.latest_weights)
            
            return agg_weights, metrics_aggregated
        except Exception as e:
            # Comprehensive crash reporting for vLab stability
            print(f"[Strategy] CRASH in Round {server_round}: {str(e)}")
            traceback.print_exc()
            raise e

    def aggregate_evaluate(self, server_round, results, failures):
        """
        Gathers evaluation metrics (Accuracy, AUC) from all nodes and saves the best model.
        """
        try:
            metrics_aggregated = {}
            if results and self.evaluate_metrics_aggregation_fn:
                # Step 7: Final Global Accuracy Calculation
                metrics = [(res.num_examples, res.metrics) for _, res in results]
                metrics_aggregated = self.evaluate_metrics_aggregation_fn(metrics, server_round=server_round)
                
                # Step 8: Model Checkpointing (Auto-saving the "Best Model")
                current_acc = metrics_aggregated.get("accuracy", 0.0)
                if current_acc >= self.best_acc or self.best_acc == 0.0:
                    try:
                        self.best_acc = current_acc
                        if self.latest_weights is not None:
                            # Save to persistent storage for dashboard access (.pth format)
                            checkpoint_dir = os.path.join(os.getcwd(), "test")
                            os.makedirs(checkpoint_dir, exist_ok=True)
                            checkpoint_path = os.path.join(checkpoint_dir, "best_model.pth")
                            
                            # Standardised state_dict saving 
                            if self.net is not None:
                                # Map the List[np.ndarray] back to the model's named parameters
                                params_dict = zip(self.net.state_dict().keys(), self.latest_weights)
                                state_dict = {k: torch.tensor(v) for k, v in params_dict}
                                torch.save(state_dict, checkpoint_path)
                            else:
                                torch.save(self.latest_weights, checkpoint_path) # Fallback to raw weights
                            
                            print(f"[Strategy] New BEST Evaluation model saved (Acc: {current_acc:.4f})")
                    except Exception as e:
                        print(f"[Strategy] Checkpoint failed: {e}")
            
            # Inherit standard loss aggregation from FedAvg
            loss, _ = super().aggregate_evaluate(server_round, results, failures)
            return loss, metrics_aggregated
        except Exception as e:
            print(f"[Strategy] Evaluate Error in Round {server_round}: {str(e)}")
            return None, {}
