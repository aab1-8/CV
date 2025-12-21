from fl_logic.fed_avg import FederatedServer
from fl_logic.client import FlowerSurvivalClient
from fl_logic.model import SurvivalMLP, get_parameters
from sklearn.metrics import accuracy_score, roc_auc_score
import pandas as pd
import numpy as np

def run_federated_simulation(cleaned_nodes, rounds=10, local_epochs=3):
    """
    Orchestrates the Federated Learning simulation across multiple nodes (Hospitals).
    This function manually runs the FL loop:
    Server sends weights -> Clients train -> Clients return updates -> Server aggregates.
    
    Args:
        cleaned_nodes: Dictionary containing preprocessed data for each hospital.
            Each node should have 'train' and 'test' DataLoaders.
        rounds: Total number of communication rounds (Server <-> Client cycles).
        local_epochs: How many training passes each client does per round.
        
    Returns:
        The final FederatedServer object containing the global model.
    """
    # 1. Setup - Determine input dimension from the first node's data
    first_node_name = list(cleaned_nodes.keys())[0]
    # Get a sample batch to determine input dimension
    sample_batch = next(iter(cleaned_nodes[first_node_name]['train']))
    input_dim = sample_batch[0].shape[1]
    
    # Initialize the Central Server
    server = FederatedServer()
    
    # Initialize Clients (Hospitals) - each gets its own model and data
    clients = {}
    for name, data in cleaned_nodes.items():
        # Create a fresh model for this client
        net = SurvivalMLP(input_dim)
        # Wrap it in a FlowerSurvivalClient
        clients[name] = FlowerSurvivalClient(net, data['train'], data['test'])
        
    print(f"🚀 Starting Federated Learning Simulation: {len(clients)} nodes, {rounds} rounds.\n")
    
    # 2. Communication Rounds Loop
    for r in range(1, rounds + 1):
        print(f"--- Round {r} ---")
        
        # Step A: Server Broadcast
        # Get the current global model parameters (or None for first round)
        global_params = server.get_global_model()
        
        # If this is the first round and server has no weights yet,
        # initialize from the first client
        if global_params is None:
            first_client = list(clients.values())[0]
            global_params = first_client.get_parameters({})
            server.weights = global_params
        
        local_updates = []
        
        # Step B: Model Training on Clients
        for name, client in clients.items():
            # Client receives global weights, trains on private data, 
            # and returns the updated weights and training stats.
            # fit() returns: (parameters, num_samples, metrics_dict)
            updated_params, num_samples, metrics = client.fit(global_params, {})
            
            # Format the update for server aggregation
            local_updates.append({
                'weights': updated_params,
                'n_samples': num_samples
            })
            
        # Step C: Server Aggregation
        # Server collects all updates and averages them to create the new Global Model
        server.aggregate_fedavg(local_updates)
        print("")
        
    return server
