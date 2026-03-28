import torch, flwr  # The powerhouse: PyTorch for AI, Flower for Federated connectivity
from torch.utils.data import DataLoader, TensorDataset  # Utilities for efficient data batching
from .models import get_parameters, set_parameters  # Translates between Python and AI weights
from .engine import train, test  # The shared engine: train for local update, test for evaluation
from .blockchain import BlockchainManager  # The "Truth Layer": logs every audit to Ethereum
import numpy as np  # Essential for mathematical weight manipulation

class FlowerSurvivalClient(flwr.client.NumPyClient):
    """
    Each hospital node runs an instance of this client.
    It encapsulates the logic for training securely on local records.
    """
    def __init__(self, net, trainloader, valloader, num_classes=1, mask_add=None, mask_sub=None, is_malicious=False, client_id=0, task_id=0, attack_type="label_flip", enable_dp=False, noise_multiplier=1.0, max_grad_norm=1.5, attack_scale_factor=100.0, local_epochs=1, enable_blockchain=False, node_name=None):
        # Store all local data, model, and configuration for this specific hospital
        self.net, self.trainloader, self.valloader = net, trainloader, valloader
        self.num_classes, self.mask_add, self.mask_sub = num_classes, mask_add, mask_sub
        self.is_malicious, self.client_id, self.task_id = is_malicious, client_id, task_id
        self.attack_type, self.enable_dp = attack_type, enable_dp
        self.noise_multiplier, self.max_grad_norm, self.attack_scale_factor = noise_multiplier, max_grad_norm, attack_scale_factor
        self.local_epochs, self.enable_blockchain = local_epochs, enable_blockchain
        self.node_name = node_name or f"Hospital_{client_id}"  # Human-readable label for dashboards
        
        # GPU Detection: If vLab has a NVIDIA GPU, we use it for a 10x speed boost
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.net.to(self.device)  # Move the model architecture to the specialized hardware

        # ADVERSARIAL MODE: Label Flipping Attack
        # Malicious nodes intentionally lie about patient outcomes to degrade global accuracy
        if self.is_malicious and self.attack_type == "label_flip":
            new_data = []
            for X, y in self.trainloader.dataset:
                # Flips class 1 to 0 and 0 to 1, or shifts multi-class labels by 1
                if self.num_classes > 1:
                    y_flipped = (float(y) + 1) % self.num_classes
                else:
                    y_flipped = 1.0 - float(y)
                new_data.append((X, torch.tensor(y_flipped).float()))
            
            # Replace the healthy dataset with the tampered (poisoned) one
            self.trainloader = DataLoader(
                new_data, 
                batch_size=self.trainloader.batch_size, 
                shuffle=True
            )

    def fit(self, parameters, config):
        """
        The main FL Handshake: The server sends current global weights, and we tune them locally.
        """
        print(f"[Client {self.client_id}] Starting local training on {self.device}...")
        # Step 1: Update local model with latest "Global Knowledge" from the server
        set_parameters(self.net, parameters)
        pe = None
        # Step 2: Initialize Differential Privacy (DP) via Opacus if enabled
        if self.enable_dp:
            from opacus import PrivacyEngine
            try:
                # Modern Opacus uses accountant="rdp"
                pe = PrivacyEngine(accountant="rdp")
            except:
                # Fallback for older versions or custom shims
                pe = PrivacyEngine()
        
        # Extract hyperparameters (learning rate) from the server's control message
        lr_val = config.get("learning_rate", 0.001)
        # Step 3: Run the local training loop (located in engine.py)
        # Returns: Privacy spent (epsilon) and current loss
        eps, train_loss = train(self.net, self.trainloader, epochs=self.local_epochs, privacy_engine=pe, 
                              num_classes=self.num_classes, noise_multiplier=self.noise_multiplier, 
                              max_grad_norm=self.max_grad_norm, lr=lr_val, device=self.device)
        
        # Weights must be moved back to the CPU to be serialized over the network back to the server
        weights = get_parameters(self.net.cpu())
        self.net.to(self.device)  # Return to GPU for immediate evaluation

        # Step 4: Blockchain Audit (Gas & Hash Logging)
        gas_used = 0
        if self.enable_blockchain:
            bcm = BlockchainManager.get_instance()
            if bcm:
                try: 
                    # Record a SHA-256 hash of our weights to the Ethereum contract to prove we participated
                    gas_used = bcm.post_commitment(self.task_id, int(config.get("server_round", 0)), weights, self.client_id)
                except Exception as e:
                    print(f"[Client {self.client_id}] Blockchain audit log failed: {e}")
        
        # ADVERSARIAL MODE: Gradient Scaling Attack
        # The malicious node inflates its update by 100x to overwhelm healthy hospitals
        if self.is_malicious and self.attack_type == "gradient_scale":
            weights = [w * self.attack_scale_factor for w in weights]
        
        # Step 5: Secure Aggregation (Double Masking)
        # We add/subtract secret masks so the server sees the aggregate but never the individual weights
        if self.mask_add is not None:
            weights = [float(w) + float(m) if np.isscalar(w) else w + m for w, m in zip(weights, self.mask_add)]
        if self.mask_sub is not None:
            weights = [float(w) - float(m) if np.isscalar(w) else w - m for w, m in zip(weights, self.mask_sub)]
        
        # Step 6: Post-Training Telemetry
        # We calculate metrics (accuracy, AUC) on ourselves before sending updates back
        _, train_acc, train_auc = test(self.net, self.trainloader, num_classes=self.num_classes, device=self.device)
        _, val_acc, val_auc = test(self.net, self.valloader, num_classes=self.num_classes, device=self.device)
        
        # Step 7: Final Report Generation
        # This metadata allows the server to track privacy leakage (Epsilon) and aggregate the Global accuracy
        metrics = {
            "accuracy": float(val_acc), 
            "auc": float(val_auc),
            "loss": float(train_loss),
            "privacy_spent": float(eps) if eps is not None else 0.0,
            "train_accuracy": float(train_acc),
            "train_auc": float(train_auc),
            "test_accuracy": float(val_acc),
            "test_auc": float(val_auc),
            "gas_used": int(gas_used) if gas_used else 0,
            "client_id": int(self.client_id),
            "noise_multiplier": float(self.noise_multiplier),
            "attack_type": str(self.attack_type),
            "is_malicious": bool(self.is_malicious),
            "node_name": str(self.node_name),
            "experiment": str(config.get("experiment", "none"))
        }
        
        # Inject any additional server-side parameters into our report
        for k, v in config.items():
            metrics[k] = v
            
        # Return local knowledge (weights), data size (for FedAvg weightings), and metrics
        return weights, len(self.trainloader.dataset), metrics

    def evaluate(self, parameters, config):
        """
        Server calls this to see how the Global model performs on this hospital's local test data.
        """
        # Update our architecture with the latest global averages
        set_parameters(self.net, parameters)
        # Run standard test loop
        loss, accuracy, auc = test(self.net, self.valloader, num_classes=self.num_classes, device=self.device)
        
        metrics = {"accuracy": float(accuracy), "auc": float(auc)}
        # Merge server metadata to ensure consistent logging across rounds
        for k, v in config.items():
            metrics[k] = v
            
        return float(loss), len(self.valloader.dataset), metrics
