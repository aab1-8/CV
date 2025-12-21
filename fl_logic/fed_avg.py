import numpy as np

class FederatedServer:
    """
    Manages the Global Model and the Federated Averaging (FedAvg) algorithm.
    This class simulates the Central Server functions if we were running a manual simulation
    separate from the Flower framework's default strategy.
    
    NOTE: In the main `federated_survival.py`, we use Flower's built-in `FedAvg` strategy.
    This class is provided either as a standalone educational implementation or a custom utility
    for manual simulation loops.
    """
    def __init__(self):
        """
        Initializes the Global Model weights for the Federated Learning server.
        """
        # Global weights (W) initialized to None.
        # They will be set when the first client connects or explicitly initialized later.
        self.weights = None
        
        # History log to track how weights evolve over time
        self.history = []

    def aggregate_fedavg(self, client_results):
        """
        Performs the core Federated Averaging (FedAvg) aggregation algorithm.
        
        Equation: W_global = Sum(W_local * (N_local / N_total))
        
        Args:
            client_results: List of dicts containing:
                - 'weights': The local model weights from a client.
                - 'bias': The local model bias.
                - 'n_samples': The number of training samples that client used.
                
        Returns:
            The simplified global weights and bias.
        """
        # Calculate N_total: The sum of training samples across all participating clients
        total_samples = sum(res['n_samples'] for res in client_results)
        
        # Initialize accumulators for the new weighted sum
        # We need to handle a LIST of parameters (one for each layer in the neural net)
        # Take the first client's weights as a template for shape
        first_weights = client_results[0]['weights']
        new_weights = [np.zeros_like(w) for w in first_weights]
        
        # Iterate over each client's update
        for res in client_results:
            # Calculate the weight contribution factor for this client
            # Clients with MORE data get a HIGHER influence on the global model
            weight_factor = res['n_samples'] / total_samples
            
            # Accumulate the weighted contribution for EACH layer
            for i, layer_weights in enumerate(res['weights']):
                new_weights[i] += layer_weights * weight_factor
            
        # Update the Global Model state with the new averages
        self.weights = new_weights
        
        # Store a snapshot of the model state for historical analysis
        self.history.append({
            'weights': [w.copy() for w in self.weights]
        })
        
        print(f"📡 Server: Aggregated updates from {len(client_results)} nodes (Total Samples: {total_samples})")
        return self.weights

    def get_global_model(self):
        """
        Returns the current state of the global model.
        Used by clients to synchronize their local models before training.
        """
        return self.weights
